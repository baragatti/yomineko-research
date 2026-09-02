#!/usr/bin/env python3
"""Apply the Phase-4 grammar patch (owner go-ahead 2026-08-05).

Field mapping (the finder's names -> storage):
    expl_pt / expl_en     localized_text(grammar_point, 'explanation', pt-BR/en)
    label_pt / label_en   localized_text(grammar_point, 'label',       pt-BR/en)
    pattern               grammar_point.structure_pattern
    register              grammar_point.register           (closed enum - see below)
    forms[i].pt/.en       localized_text(grammar_point, 'form_meanings', ...) - list-shaped, NOT patched
                          here because the index/shape cannot be anchored safely; routed to manual.

Guards, all learned from earlier phases in this campaign:
  * SUBSTRING anchoring - a fix replaces `current` INSIDE the stored value when `current` is a fragment
    (most expl_* findings quote one sentence of a paragraph). If `current` is absent from the stored
    value, the op is skipped and reported: silently rewriting the whole field would delete the rest of
    the explanation.
  * VALUE validation - a fix that reads as an instruction ("Replace X with Y", "delete the clause",
    a bare arrow) is never written; those are exactly what corrupted a kana field in Phase 3 and a
    conjugation surface in Phase 5.
  * ENUM protection - `register` and `caution` are closed neutral-English enums. Phase-4 verifiers
    explicitly rejected a fix that would have written pt-BR prose into `caution` ("rough" there means
    blunt/top-down, not vulgar), so any register value outside the observed enum is refused.
  * en/pt PARITY is not forced: these are separate findings, and inventing the sibling half is what the
    sentence pipeline got wrong for three rounds.

Single transaction; --dry-run reports without writing.
Usage: fable5_grammar_apply.py [--dry-run]
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

LOC = {"expl_pt": ("explanation", "pt-BR"), "expl_en": ("explanation", "en"),
       "label_pt": ("label", "pt-BR"), "label_en": ("label", "en")}
COL = {"pattern": "structure_pattern"}
# `register` findings quote the ARRAY form (["casual", "colloquial"]), which lives in register_json - the
# bare `register` column is a different, coarser field {casual, formal, neutral, polite}. Writing an array
# into it would have corrupted the column; the enum guard caught that on the first dry run.
REGISTER_VOCAB = {"plain", "polite", "casual", "colloquial", "written", "formal",
                  "humble", "honorific", "literary", "masculine", "feminine"}
INSTRUCTION = re.compile(
    r"^(replace|change|set|update|remove|delete|drop|add|apply|keep|no change|rewrite|fix)\b|"
    r"->|→|\bshould be\b|\bmust be\b|\bi\.e\.\b.*\breplace\b", re.I)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    conf = [f for f in json.loads((FD / "phase4_grammar.json").read_text(encoding="utf-8"))["findings"]
            if f["verdict"] == "confirmed"]
    con = sqlite3.connect(db_target(ROOT / "db" / "corpus.sqlite"))
    gid = {slug: i for i, slug in con.execute("SELECT id, slug FROM grammar_point")}
    registers = {r[0] for r in con.execute("SELECT DISTINCT register FROM grammar_point") if r[0]}

    applied, skipped = 0, []
    con.execute("BEGIN")
    for f in conf:
        slug, field, cur, fix = f["slug"], f["field"], (f.get("current") or ""), (f.get("fix") or "").strip()
        if slug not in gid:
            skipped.append((slug, field, "unknown grammar point")); continue
        if not fix or INSTRUCTION.search(fix):
            skipped.append((slug, field, "fix is an instruction, not a value")); continue
        if chr(8212) in fix:
            # house rule (audit_lesson_hygiene + integrity_audit): no em dash in learner-facing text.
            # Six slipped through on the first apply and had to be cleaned afterwards.
            fix = fix.split(chr(8212))[0].rstrip()
            if not fix:
                skipped.append((slug, field, "fix was only an em-dash rationale")); continue
        i = gid[slug]

        if field in LOC:
            dbfield, locale = LOC[field]
            row = con.execute("SELECT value FROM localized_text WHERE entity_type='grammar_point' AND "
                              "entity_id=? AND field=? AND locale=?", (i, dbfield, locale)).fetchone()
            if not row:
                skipped.append((slug, field, "no stored value")); continue
            stored = row[0] or ""
            if cur and cur in stored:
                new = stored.replace(cur, fix, 1)          # surgical: keep the rest of the paragraph
            elif cur and cur not in stored:
                skipped.append((slug, field, "anchor text not found in stored value")); continue
            else:
                new = fix
            if not args.dry_run:
                con.execute("UPDATE localized_text SET value=? WHERE entity_type='grammar_point' AND "
                            "entity_id=? AND field=? AND locale=?", (new, i, dbfield, locale))
            applied += 1

        elif field == "register":
            # take the leading JSON array and ignore any trailing prose rationale
            m = re.match(r"\s*(\[[^\]]*\])", fix)
            if not m:
                skipped.append((slug, field, "no JSON array in fix")); continue
            try:
                vals = json.loads(m.group(1))
            except json.JSONDecodeError:
                skipped.append((slug, field, "unparseable register array")); continue
            bad = [v for v in vals if v not in REGISTER_VOCAB]
            if not vals or bad:
                skipped.append((slug, field, f"register values outside vocabulary: {bad}")); continue
            if not args.dry_run:
                con.execute("UPDATE grammar_point SET register_json=? WHERE id=?",
                            (json.dumps(vals, ensure_ascii=False), i))
            applied += 1

        elif field in COL:
            col = COL[field]
            if col == "register" and fix not in registers:
                skipped.append((slug, field, f"'{fix}' outside the observed register enum {sorted(registers)}"))
                continue
            stored = con.execute(f"SELECT {col} FROM grammar_point WHERE id=?", (i,)).fetchone()[0] or ""
            new = stored.replace(cur, fix, 1) if (cur and cur in stored) else fix
            if not args.dry_run:
                con.execute(f"UPDATE grammar_point SET {col}=? WHERE id=?", (new, i))
            applied += 1
        else:
            skipped.append((slug, field, "list-shaped or unmapped field"))

    if args.dry_run:
        con.rollback()
    else:
        con.commit()
    REPORTS.mkdir(parents=True, exist_ok=True)
    (REPORTS / "phase4_grammar_skipped.json").write_text(json.dumps(
        {"note": "Phase-4 findings NOT auto-applied. Each needs a human/agent pass; none was guessed at.",
         "skipped": [{"slug": s, "field": f, "why": w} for s, f, w in skipped]},
        ensure_ascii=False, indent=1), encoding="utf-8")
    con.close()
    print(f"grammar apply ({'dry-run' if args.dry_run else 'APPLIED'}): {applied} fields")
    print(f"skipped: {len(skipped)} {dict(Counter(w for _, _, w in skipped))}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
