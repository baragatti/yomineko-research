#!/usr/bin/env python3
"""Repair the INDIVIDUALLY NAMED translation defects the six QA auditors found in the sentence bank.

Six auditors read all 5,889 bank records (research/reports/qa_sweep/translation_accuracy_1.md ..
_6.md). Three of their findings were SYSTEMATIC classes, already repaired by earlier campaigns and
deliberately out of scope here: the "Quanto a" topic scaffold applied to non-topic chunks, the
こ/そ/あ demonstrative mis-mapping, and the missing `translation.en`. `structure_explanation` is
repaired separately too. What is left is the long tail this script applies -- every defect a report
named on its own:

  * `translation` [pt-BR] -- MEANING SHIFTS (tense/voice flips, 行ってきた losing the return leg,
    名前を呼ぶ read as addressing someone by first name, a dropped 少し, an invented superlative,
    orelha/ouvido, 交番 as "delegacia"), SCAFFOLDING left inside the natural-speech field
    (explanatory parentheses, slash-separated candidate renderings, "(a pessoa)" placeholders),
    UNNATURAL pt-BR and calques, ORTHOGRAPHY ("prático" for "pratico", "desde de", "da" for "dá"),
    and REGISTER (さようなら as the final-parting "Adeus").
  * `translation_literal` [pt-BR/en] -- the individually named scaffold defects: coined words
    ("gostável", "é gostado"), 上手 attributed to the instrument instead of the person, person and
    number disagreeing with the natural translation of the same record, garbled strings that do not
    parse as Portuguese, and 二度と read as "duas vezes mais".
  * token `gloss` / `role` / `conjugation_note` -- the two token-gloss errors, the two mislabelled
    の-possessor roles, and the editor-to-editor comments ("a glosa 'to print' está errada") that
    leaked into learner-facing conjugation notes, in both locales.

design/translation_style.md is the binding contract these rewrites answer to: `translation` is
NATURAL speech (§1, §5 -- no parentheses explaining grammar, no "Quanto a" mirror), and
`translation_literal` is the structural scaffold where the chunk-by-chunk gloss belongs.

DB ONLY. This writes `db/corpus.sqlite` localized_text and nothing else. `corpus/sentences/bank.json`
is exported from the DB by the orchestrator afterwards -- do not run an exporter from here.

Idempotent: every edit is matched on its EXACT current DB value, so a second run reports 0 changes
and `--check` after an apply exits clean. A row whose stored text is neither the expected defective
value nor the finished rewrite is SKIPPED and reported; it is never overwritten.

Usage: apply_translation_defect_repairs.py [--check] [--data PATH]
"""
from __future__ import annotations

import argparse
import json
import sqlite3
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]

ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / "db" / "corpus.sqlite"

# The verified rewrite table: [{entity, slug, field, locale, old, new, why, token_position?}, ...].
# TRACKED, not session-scoped, so the applied edits stay auditable and the script re-runnable.
# `slug` always names the SENTENCE; a token row adds `token_position` to address one of its tokens.
DATA = ROOT / "research" / "derived" / "repairs" / "translation_defect_repairs.json"

FIELDS = {
    "sentence": {"translation", "translation_literal"},
    "token": {"gloss", "role", "conjugation_note"},
}
LOCALES = {"pt-BR", "en"}


def load(path: Path) -> list[dict]:
    rows = json.loads(path.read_text(encoding="utf-8"))
    seen: set[tuple] = set()
    for i, r in enumerate(rows):
        missing = {"entity", "slug", "field", "locale", "old", "new"} - set(r)
        if missing:
            raise SystemExit(f"row {i}: missing key(s) {sorted(missing)}")
        ent = r["entity"]
        if ent not in FIELDS:
            raise SystemExit(f"row {i} ({r['slug']}): unexpected entity {ent!r}")
        if r["field"] not in FIELDS[ent]:
            raise SystemExit(f"row {i} ({r['slug']}): unexpected {ent} field {r['field']!r}")
        if r["locale"] not in LOCALES:
            raise SystemExit(f"row {i} ({r['slug']}): unexpected locale {r['locale']!r}")
        if not isinstance(r["old"], str) or not isinstance(r["new"], str):
            raise SystemExit(f"row {i} ({r['slug']}): `old`/`new` must be strings")
        # A row whose `new` equals its `old` would apply nothing while still counting as a repair in
        # the campaign ledger; that is a defect in the table, not a no-op to swallow silently.
        if r["old"] == r["new"]:
            raise SystemExit(f"row {i} ({r['slug']}): `new` is identical to `old`")
        pos = r.get("token_position")
        if ent == "token":
            if not isinstance(pos, int):
                raise SystemExit(f"row {i} ({r['slug']}): token row needs an integer token_position")
        elif pos is not None:
            raise SystemExit(f"row {i} ({r['slug']}): token_position on a sentence row")
        key = (ent, r["slug"], r["field"], r["locale"], pos)
        if key in seen:
            raise SystemExit(f"row {i}: duplicate target {key}")
        seen.add(key)
    return rows


def sentence_rows(con: sqlite3.Connection, r: dict) -> tuple[list[tuple[int, str, int]], str | None]:
    """localized_text rows for one sentence field, plus the sentence's Layer-A `en` column."""
    hit = con.execute(
        "SELECT lt.entity_id, lt.value, lt.is_list "
        "FROM localized_text lt JOIN sentence s ON s.id = lt.entity_id "
        "WHERE lt.entity_type='sentence' AND s.slug=? AND lt.field=? AND lt.locale=?",
        (r["slug"], r["field"], r["locale"])).fetchall()
    src_en = con.execute("SELECT en FROM sentence WHERE slug=?", (r["slug"],)).fetchone()
    return hit, (src_en[0] if src_en else None)


def token_rows(con: sqlite3.Connection, r: dict) -> list[tuple[int, str, int]]:
    """localized_text rows for one token field.

    `token.position` is NOT unique: Sudachi's C-mode compound and its A-mode parts share a position
    (夜食にインスタントラーメンを食べた has three tokens at position 2). So every token at the
    position is fetched and the caller disambiguates by value -- addressing the wrong split of a
    fused compound would silently rewrite a different word.
    """
    return con.execute(
        "SELECT lt.entity_id, lt.value, lt.is_list "
        "FROM localized_text lt JOIN token t ON t.id = lt.entity_id "
        "JOIN sentence s ON s.id = t.sentence_id "
        "WHERE lt.entity_type='token' AND s.slug=? AND t.position=? AND lt.field=? AND lt.locale=?",
        (r["slug"], r["token_position"], r["field"], r["locale"])).fetchall()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true",
                    help="report what would change; write nothing")
    ap.add_argument("--data", type=Path, default=DATA,
                    help="path to the verified rewrite table (JSON)")
    args = ap.parse_args()

    if not args.data.exists():
        raise SystemExit(f"rewrite table not found: {args.data}")
    rows = load(args.data)

    con = sqlite3.connect(DB)
    con.execute("PRAGMA busy_timeout=60000")

    changed = 0
    already = 0
    skipped: list[str] = []
    shadowed: list[str] = []

    for r in rows:
        ent, slug, field, locale = r["entity"], r["slug"], r["field"], r["locale"]
        pos = r.get("token_position")
        label = (f"{slug}.{field} [{locale}]" if ent == "sentence"
                 else f"{slug} token[{pos}].{field} [{locale}]")

        if ent == "sentence":
            hit, src_en = sentence_rows(con, r)
            # export_corpus.py reads `translation`/en as `sentence.en or localized_text`, so a
            # non-null Layer-A `en` would shadow this edit in the exported bank. Say so out loud
            # rather than reporting a repair the reader will never see.
            if field == "translation" and locale == "en" and src_en is not None:
                shadowed.append(f"{label}: sentence.en (Layer A) is set, so the exporter will use "
                                f"it instead of this row")
        else:
            hit = token_rows(con, r)

        if not hit:
            skipped.append(f"{label}: no localized_text row")
            continue
        if any(is_list for _, _, is_list in hit):
            skipped.append(f"{label}: stored as a list, expected scalar text")
            continue

        exact = [h for h in hit if h[1] == r["old"]]
        done = [h for h in hit if h[1] == r["new"]]
        if len(exact) > 1:
            skipped.append(f"{label}: {len(exact)} rows carry the expected text -- ambiguous, "
                           f"not touching it")
            continue
        if not exact:
            if done:
                already += 1                                   # already repaired; nothing to do
            else:
                skipped.append(f"{label}: current value matches neither the expected defective "
                               f"text nor the rewrite -- not touching it")
            continue
        if len(hit) > 1:
            print(f"  (note) {label}: {len(hit)} rows at this position; matched the one holding "
                  f"the expected text")

        entity_id = exact[0][0]
        print(f"  {label}")
        if r.get("why"):
            print(f"     why: {r['why']}")
        if not args.check:
            con.execute(
                "UPDATE localized_text SET value=? WHERE entity_type=? AND entity_id=? "
                "AND field=? AND locale=?", (r["new"], ent, entity_id, field, locale))
        changed += 1

    if not args.check:
        con.commit()
    con.close()

    verb = "would repair" if args.check else "repaired"
    print(f"\n{verb} {changed} field(s) of {len(rows)}; {already} already carried the rewrite")
    for s in shadowed:
        print(f"  ~ {s}")
    for s in skipped:
        print(f"  ! {s}")
    return 1 if (args.check and changed) else (2 if skipped else 0)


if __name__ == "__main__":
    sys.exit(main())
