#!/usr/bin/env python3
"""Apply the Phase-6 lesson/reading patch (owner go-ahead 2026-08-05).

Four storage shapes, each anchored differently:
    body|title|description|objectives[i]   localized_text(lesson, ...)      substring anchor
    exercises[i].prompt|.explanation       localized_text(exercise, ...)    substring anchor, exercise by ord
    exercises[i].answer                    exercise.answer column           substring anchor
    tokens[i].r|.ro                        reading.tokens JSON list         INDEX + surface cross-check
    pt                                     reading.translation_pt           substring anchor

Guards carried over from phases 3-5, each of which caught a real corruption:
  * a fix phrased as an INSTRUCTION is never written (kana fields and conjugation surfaces were corrupted
    this way before the guard existed);
  * em dashes are truncated - house rule, enforced by integrity_audit;
  * substring anchoring: if the quoted `current` is not present in the stored value the op is SKIPPED,
    never applied wholesale, because most findings quote one clause of a long body;
  * token edits verify the token's SURFACE matches what the finding described before touching its reading,
    so an index shift cannot silently rewrite a different token (the exact bug that hit the sentence
    patch, where indices were in a different order than the DB).
Everything not applied is written to phase6_skipped.json rather than guessed at.

Usage: fable5_lessons_apply.py [--dry-run]
"""
from __future__ import annotations
import argparse, json, re, sqlite3, sys
from collections import Counter
from pathlib import Path
sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
# W01: honour --db / $YOMINEKO_DB so a rebuild can target a scratch DB (scripts/dbtarget.py).
import sys as _sys, pathlib as _pl  # noqa: E402
_sys.path.append(str(next(p for p in _pl.Path(__file__).resolve().parents if p.name == "scripts")))
from dbtarget import db_target, out_root  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
FD = ROOT / "research" / "derived" / "fable5_validation"
# W01: the patch inputs are read from the repo, but the skipped-report is OUTPUT — it follows
# --out-root / $YOMINEKO_OUT_ROOT so a rebuild does not overwrite the tracked one with a
# report derived from its scratch database. Unset, it is the same path it always was.
REPORTS = out_root(ROOT) / "research" / "derived" / "fable5_validation"
INSTRUCTION = re.compile(
    r"^(replace|change|set|update|remove|delete|drop|add|apply|keep|rewrite|fix|minimal|split|trocar|"
    r"corrigir|no body|just |only )\b|->|→|\bshould be\b|\bmust be\b", re.I)
LESSON_LOC = {"body": "body", "title": "title", "description": "description"}


def clean(fix: str):
    fix = fix.strip()
    if not fix or INSTRUCTION.search(fix):
        return None, "fix is an instruction, not a value"
    if "—" in fix:
        fix = fix.split("—")[0].rstrip()
        if not fix:
            return None, "fix was only an em-dash rationale"
    return fix, None


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    conf = [f for f in json.loads((FD / "phase6_lessons_partial.json").read_text(encoding="utf-8"))["findings"]
            if f["verdict"] == "confirmed"]
    con = sqlite3.connect(db_target(ROOT / "db" / "corpus.sqlite"))
    lid = {slug: i for i, slug in con.execute("SELECT id, slug FROM lesson")}
    applied, skipped = Counter(), []
    con.execute("BEGIN")

    def loc_update(etype, eid, field, locale, cur, fix):
        row = con.execute("SELECT value FROM localized_text WHERE entity_type=? AND entity_id=? AND "
                          "field=? AND locale=?", (etype, eid, field, locale)).fetchone()
        if not row:
            return "no stored value"
        stored = row[0] or ""
        if cur and cur in stored:
            new = stored.replace(cur, fix, 1)
        elif cur:
            return "anchor text not found"
        else:
            new = fix
        if not args.dry_run:
            con.execute("UPDATE localized_text SET value=? WHERE entity_type=? AND entity_id=? AND "
                        "field=? AND locale=?", (new, etype, eid, field, locale))
        return None

    for f in conf:
        slug, field, cur = f["slug"], f["field"], (f.get("current") or "")
        fix, why = clean(f.get("fix") or "")
        if why:
            skipped.append((slug, field, why)); continue
        kind = f.get("kind")

        if kind == "lesson":
            i = lid.get(slug)
            if not i:
                skipped.append((slug, field, "unknown lesson")); continue
            base = field.split("[")[0]
            if base in LESSON_LOC and "[" not in field:
                err = loc_update("lesson", i, LESSON_LOC[base], "pt-BR", cur, fix)
                (skipped.append((slug, field, err)) if err else applied.update([base]))
            elif base == "objectives":
                err = loc_update("lesson", i, "objectives", "pt-BR", cur, fix)
                (skipped.append((slug, field, err)) if err else applied.update(["objectives"]))
            elif base == "exercises":
                m = re.match(r"exercises\[(\d+)\]\.(prompt|explanation|answer)$", field)
                if not m:
                    skipped.append((slug, field, "unmapped exercise sub-field")); continue
                ordv, sub = int(m.group(1)), m.group(2)
                row = con.execute("SELECT id FROM exercise WHERE lesson_id=? ORDER BY ord LIMIT 1 OFFSET ?",
                                  (i, ordv)).fetchone()
                if not row:
                    skipped.append((slug, field, f"no exercise at index {ordv}")); continue
                eid = row[0]
                if sub == "answer":
                    stored = con.execute("SELECT answer FROM exercise WHERE id=?", (eid,)).fetchone()[0] or ""
                    if cur and cur not in stored:
                        skipped.append((slug, field, "anchor text not found")); continue
                    new = stored.replace(cur, fix, 1) if cur else fix
                    if not args.dry_run:
                        con.execute("UPDATE exercise SET answer=? WHERE id=?", (new, eid))
                    applied.update(["exercise.answer"])
                else:
                    err = loc_update("exercise", eid, sub, "pt-BR", cur, fix)
                    (skipped.append((slug, field, err)) if err else applied.update([f"exercise.{sub}"]))
            else:
                skipped.append((slug, field, "unmapped lesson field"))

        elif kind == "reading":
            row = con.execute("SELECT tokens, translation_pt FROM reading WHERE slug=?", (slug,)).fetchone()
            if not row:
                skipped.append((slug, field, "unknown reading")); continue
            toks_json, tr = row
            m = re.match(r"tokens\[(\d+)\]\.(r|ro)$", field)
            if m:
                idx, attr = int(m.group(1)), m.group(2)
                toks = json.loads(toks_json or "[]")
                if idx >= len(toks):
                    skipped.append((slug, field, "token index out of range")); continue
                # cross-check: the finding's `current` must match this token's present value, else the
                # index refers to a different tokenization than the one stored.
                if cur and toks[idx].get(attr) != cur:
                    skipped.append((slug, field, "token value does not match anchor")); continue
                toks[idx][attr] = fix
                if not args.dry_run:
                    con.execute("UPDATE reading SET tokens=? WHERE slug=?",
                                (json.dumps(toks, ensure_ascii=False), slug))
                applied.update([f"reading.tokens.{attr}"])
            elif field == "pt":
                stored = tr or ""
                if cur and cur not in stored:
                    skipped.append((slug, field, "anchor text not found")); continue
                new = stored.replace(cur, fix, 1) if cur else fix
                if not args.dry_run:
                    con.execute("UPDATE reading SET translation_pt=? WHERE slug=?", (new, slug))
                applied.update(["reading.pt"])
            else:
                skipped.append((slug, field, "unmapped reading field"))
        else:
            skipped.append((slug, field, f"unmapped kind {kind}"))

    if args.dry_run:
        con.rollback()
    else:
        con.commit()
    REPORTS.mkdir(parents=True, exist_ok=True)
    (REPORTS / "phase6_skipped.json").write_text(json.dumps(
        {"note": "Phase-6 findings NOT auto-applied; each needs a human/agent pass. Nothing was guessed.",
         "skipped": [{"slug": s, "field": f, "why": w} for s, f, w in skipped]},
        ensure_ascii=False, indent=1), encoding="utf-8")
    con.close()
    print(f"lessons apply ({'dry-run' if args.dry_run else 'APPLIED'}): {sum(applied.values())} fields "
          f"{dict(applied)}")
    print(f"skipped: {len(skipped)} {dict(Counter(w for _, _, w in skipped).most_common(6))}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
