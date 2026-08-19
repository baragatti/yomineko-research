#!/usr/bin/env python3
"""Apply the staged Phase-4 grammar findings to the corpus DB, then re-export.

44 rows from the QA-queues pass: 36 "fix", 8 "needs-human" (skipped here on purpose). All 25 originally
queued findings were real; the first applier skipped them because the anchor quoted an elided or
already-corrected string, or the target is list/array-shaped, or the fix was phrased as an instruction.

The dominant defect class is FALSE FORMATION RULES that license ungrammatical learner output, e.g.
gram:cha-ikenai-ja-ikenai giving ちゃ to all verbs and じゃ only to nouns, which licenses *読んちゃいけない.

Field routing, which is where earlier rounds went wrong:
  expl_pt/expl_en/label_pt/formation_pt/nuance_pt -> localized_text rows (pt-BR or en)
  pattern                                          -> grammar_point.structure_pattern
  register                                         -> grammar_point.register_json, a JSON ARRAY. A
                                                      previous round wrote a quoted array into the prose
                                                      `register` column instead.
  forms[i].form/.pt/.en                            -> grammar_point.forms_json, list of objects.
  caution is NEVER written here: it is a closed neutral-English enum (none/rough/offensive/sensitive)
  and pt-BR prose was once put into it. "rough" there means blunt, not vulgar.

Guards: instruction-as-value refused; anchors must be byte-exact; register must parse as a JSON list of
known register words; nothing is written to `caution`.

Usage: apply_phase4_grammar.py [--apply]
"""
from __future__ import annotations
import argparse, json, re, sqlite3, sys
from collections import Counter
from pathlib import Path
sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SRC = ROOT / "research" / "derived" / "qa_queues" / "phase4_grammar.json"
DB = ROOT / "db" / "corpus.sqlite"
INSTRUCTION = re.compile(
    r"^(replace|change|set|update|remove|delete|drop|apply|rewrite|trocar|corrigir|substituir)\b"
    r"|->|→|\bshould be\b|\bmust be\b|Substituir a frase", re.I)
LOC = {"expl_pt": ("explanation", "pt-BR"), "expl_en": ("explanation", "en"),
       "label_pt": ("label", "pt-BR"), "formation_pt": ("formation", "pt-BR"),
       "nuance_pt": ("nuance", "pt-BR"), "formation_en": ("formation", "en"),
       "nuance_en": ("nuance", "en")}
REGISTER_OK = {"plain", "casual", "polite", "formal", "humble", "honorific", "written",
               "spoken", "colloquial", "literary", "archaic", "neutral"}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--src", default=str(DEFAULT_SRC),
                    help="findings file; round-2 files share the same row shape")
    args = ap.parse_args()
    rows = [r for r in json.loads(Path(args.src).read_text(encoding="utf-8"))["rows"] if r["verdict"] == "fix"]
    print(f"{len(rows)} fix rows staged")
    con = sqlite3.connect(DB)
    gid = {s: i for s, i in con.execute("SELECT slug,id FROM grammar_point")}
    applied, skipped = Counter(), []

    # A forms[i].form rename moves the meaning-map key with it, so the rename MUST land before any
    # .pt/.en edit that looks the meaning up by that key. gram:gp-98's form is literally "なん    か"
    # with embedded spaces, and its meaning edits could not resolve until the form itself was fixed.
    rows.sort(key=lambda r: 0 if r["id"].endswith(".form") else 1)

    for r in rows:
        slug, _, field = r["id"].partition("#")
        cur, fix = r.get("current") or "", r.get("fix") or ""
        i = gid.get(slug)
        if not i:
            skipped.append((r["id"], "unknown grammar point")); continue
        # An EMPTY fix with a non-empty anchor is a DELETION, not a missing value: gram:you-da carried
        # three trailing volitional sentences under an evidential entry, and removing them is the fix.
        # Only a fix that is empty AND anchorless is "no value supplied"; that would blank the field.
        if not fix and not cur:
            skipped.append((r["id"], "empty fix with no anchor would blank the field")); continue
        if fix and INSTRUCTION.search(fix):
            skipped.append((r["id"], "fix is an instruction, not a value")); continue
        if field == "caution":
            skipped.append((r["id"], "refused: caution is a closed enum")); continue

        if field in LOC:
            f, loc = LOC[field]
            row = con.execute("SELECT value FROM localized_text WHERE entity_type='grammar_point' AND "
                              "entity_id=? AND field=? AND locale=?", (i, f, loc)).fetchone()
            if not row:
                skipped.append((r["id"], "no stored value")); continue
            stored = row[0] or ""
            if cur and cur not in stored:
                skipped.append((r["id"], "anchor not found")); continue
            new = stored.replace(cur, fix, 1) if cur else fix
            if args.apply:
                con.execute("UPDATE localized_text SET value=? WHERE entity_type='grammar_point' AND "
                            "entity_id=? AND field=? AND locale=?", (new, i, f, loc))
            applied.update([field])

        elif field == "pattern":
            stored = con.execute("SELECT structure_pattern FROM grammar_point WHERE id=?",
                                 (i,)).fetchone()[0] or ""
            if cur and cur not in stored:
                skipped.append((r["id"], "anchor not found")); continue
            new = stored.replace(cur, fix, 1) if cur else fix
            if args.apply:
                con.execute("UPDATE grammar_point SET structure_pattern=? WHERE id=?", (new, i))
            applied.update(["pattern"])

        elif field == "register":
            try:
                val = json.loads(fix)
            except Exception:
                skipped.append((r["id"], "register fix is not JSON")); continue
            if not isinstance(val, list) or not val or not all(
                    isinstance(x, str) and x in REGISTER_OK for x in val):
                skipped.append((r["id"], f"register not a list of known words: {fix[:40]}")); continue
            if args.apply:
                con.execute("UPDATE grammar_point SET register_json=? WHERE id=?",
                            (json.dumps(val, ensure_ascii=False), i))
            applied.update(["register"])

        elif field.startswith("forms["):
            # forms_json is a list of plain STRINGS. The {form, meaning} objects in the export are built
            # at export time by joining forms_json against localized_text field "form_meanings", which is
            # a JSON MAP keyed by the form string. So .form edits the list, .pt/.en edit that map — and
            # renaming a form must move its meaning key too, or the export silently drops the meaning.
            m = re.match(r"forms\[(\d+)\]\.(form|pt|en)$", field)
            if not m:
                skipped.append((r["id"], "unresolved forms path")); continue
            idx, sub = int(m.group(1)), m.group(2)
            raw = con.execute("SELECT forms_json FROM grammar_point WHERE id=?", (i,)).fetchone()[0]
            try:
                forms = json.loads(raw or "[]")
            except Exception:
                skipped.append((r["id"], "forms_json unparseable")); continue
            if idx >= len(forms) or not isinstance(forms[idx], str):
                skipped.append((r["id"], f"no form at index {idx}")); continue

            if sub == "form":
                if cur and forms[idx] != cur:
                    skipped.append((r["id"], f"form anchor mismatch (stored {forms[idx]!r})")); continue
                old_form, forms[idx] = forms[idx], fix
                if args.apply:
                    con.execute("UPDATE grammar_point SET forms_json=? WHERE id=?",
                                (json.dumps(forms, ensure_ascii=False), i))
                    # carry the meaning across, both locales, or the export loses it
                    for loc in ("pt-BR", "en"):
                        row = con.execute(
                            "SELECT value FROM localized_text WHERE entity_type='grammar_point' AND "
                            "entity_id=? AND field='form_meanings' AND locale=?", (i, loc)).fetchone()
                        if not row:
                            continue
                        try:
                            mp = json.loads(row[0] or "{}")
                        except Exception:
                            continue
                        if old_form in mp:
                            mp[fix] = mp.pop(old_form)
                            con.execute(
                                "UPDATE localized_text SET value=? WHERE entity_type='grammar_point' "
                                "AND entity_id=? AND field='form_meanings' AND locale=?",
                                (json.dumps(mp, ensure_ascii=False), i, loc))
                applied.update(["forms.form"])
            else:
                loc = "pt-BR" if sub == "pt" else "en"
                row = con.execute(
                    "SELECT value FROM localized_text WHERE entity_type='grammar_point' AND "
                    "entity_id=? AND field='form_meanings' AND locale=?", (i, loc)).fetchone()
                if not row:
                    skipped.append((r["id"], f"no form_meanings for {loc}")); continue
                try:
                    mp = json.loads(row[0] or "{}")
                except Exception:
                    skipped.append((r["id"], "form_meanings unparseable")); continue
                key = forms[idx]
                if key not in mp:
                    skipped.append((r["id"], f"no meaning entry for {key!r}")); continue
                if cur and mp[key] != cur:
                    skipped.append((r["id"], "meaning anchor mismatch")); continue
                mp[key] = fix
                if args.apply:
                    con.execute(
                        "UPDATE localized_text SET value=? WHERE entity_type='grammar_point' AND "
                        "entity_id=? AND field='form_meanings' AND locale=?",
                        (json.dumps(mp, ensure_ascii=False), i, loc))
                applied.update([f"forms.{sub}"])
        else:
            skipped.append((r["id"], f"unmapped field {field}"))

    if args.apply:
        con.commit()
    print(f"phase4 grammar apply ({'APPLIED' if args.apply else 'dry-run'}): "
          f"{sum(applied.values())} fields {dict(applied)}")
    if skipped:
        print(f"skipped {len(skipped)}: {dict(Counter(w for _, w in skipped).most_common(6))}")
        for k, w in skipped[:6]:
            print(f"   {k}: {w}")
    con.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
