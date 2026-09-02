#!/usr/bin/env python3
"""The small follow-up pass the translation-defect campaign asked for in its own skip list.

`scripts/apply_translation_defect_repairs.py` applied 231 fields and then wrote
`research/reports/qa_sweep/translation_repairs_skipped.md`, which records what it deliberately left
open. Four of those entries are not policy questions or out-of-reach schema problems -- they are
finishable defects the campaign simply did not own. This script finishes them:

  1. §4b -- THREE `translation_literal` [pt-BR] siblings that now DISAGREE with the natural field
     repaired beside them, so a single record teaches two different things:
       * `sent:gen-fb07d83b3e0c` orelha (outer ear) vs the repaired "ouvido" for 耳が…痛い
       * `sent:gen-790b6cf52284` "quente" vs the repaired "quentinho" for 暖かい (not 暑い)
       * `sent:tatoeba-10083431` "ramo" (branch) for つる, a climbing vine
     Each is re-derived from the Japanese. The scaffold is NOT dissolved: every `(が, sujeito)`,
     "Quanto a …" topic mirror and reversed genitive stays, because these are genuine topic は /
     genitive の and `translation_literal` is where the structure is the teaching point
     (design/translation_style.md §5). Only the mistaught word changes.

  2. §4 -- FIVE `translation` [en] anchors still reading as an imperative or a bare gerund while the
     pt-BR beside them was repaired to the 1st-person present the plain non-past Japanese has
     (`sent:gen-30b970cffa4a`, `gen-56d495bbcf16`, `gen-7ea63d9fd0ad`, `gen-c19dfc37c744`,
     `gen-db21e4d29aa3`). None of the five Japanese sentences carries imperative marking. All five
     are `gen-` records whose `sentence.en` is NULL, so the string is Layer-B derived and may be
     re-authored -- the script RE-CHECKS that at run time and skips loudly if a Layer-A `en` has
     appeared, because `export_corpus.py` renders `translation`/en as `sentence.en or localized_text`
     and spec §1.1 forbids editing a selected source pair.

  3. §6 -- `sent:gen-960d7cee0887` `translation` [pt-BR], which the campaign table shipped with
     `new` identical to `old` and its loader therefore rejected. 〜とみえて states an inference and
     then what follows from it; a て-clause can never mean "because of what comes next", so the
     stored "porque não responde" ran the sentence backwards. The record's own て particle note
     already read "e por isso".

  4. §2 -- `sent:gen-9f80f08cc644` `kana`, a `sentence` COLUMN and so unreachable by a
     `localized_text` campaign: 辛い is transcribed つらい (painful) in a sentence about miso, where
     it is からい. `romaji` rides along because it is a mechanical transliteration of `kana`.

The TOKEN reading for that last record is deliberately NOT touched -- see DEFERRED below.

DB ONLY. This writes `db/corpus.sqlite` (`localized_text`, and two `sentence` columns) and nothing
else. `corpus/sentences/bank.json` is exported from the DB by the orchestrator afterwards -- do not
run an exporter from here.

Idempotent: every edit is matched on its EXACT current stored value, so a second run reports 0
changes and `--check` after an apply exits clean. A field whose stored text is neither the expected
defective value nor the finished rewrite is SKIPPED and reported; it is never overwritten.

Usage: apply_translation_followups.py [--check] [--data PATH]
"""
from __future__ import annotations

import argparse
import json
import sqlite3
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]

# W01: honour --db / $YOMINEKO_DB so a rebuild can target a scratch DB (scripts/dbtarget.py).
import sys as _sys, pathlib as _pl  # noqa: E402
_sys.path.append(str(next(p for p in _pl.Path(__file__).resolve().parents if p.name == "scripts")))
from dbtarget import db_target  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
DB = db_target(ROOT / "db" / "corpus.sqlite")

# The verified rewrite table: [{store, entity, slug, field, locale?, old, new, why}, ...].
# TRACKED, not session-scoped, so the applied edits stay auditable and the script re-runnable.
DATA = ROOT / "research" / "derived" / "repairs" / "translation_followups.json"

# store -> the fields it may address. `localized_text` rows carry a locale; `column` rows write a
# scalar column on `sentence` and must NOT carry one.
LOCALIZED_FIELDS = {"translation", "translation_literal"}
COLUMN_FIELDS = {"kana", "romaji"}
LOCALES = {"pt-BR", "en"}

# Named, argued NON-changes. Printed on every run so the decision stays visible next to the repairs
# instead of living only in a report nobody re-reads.
DEFERRED: list[tuple[str, str]] = [
    (
        "sent:gen-9f80f08cc644 token[4] 辛い reading 'つらい'",
        "Left as the analyzer emits it. validate.py §7.2 re-derives every token reading from "
        "SudachiPy and any unregistered divergence is an ERROR, not a warning; SudachiPy returns "
        "つらい for 辛い here (confirmed by running Dissector().skeleton on this sentence), so "
        "rewriting the token to からい would fail the gate. The corpus has a sanctioned escape "
        "hatch -- research/derived/fable5_validation/verified_reading_overrides.json, which "
        "ALREADY registers exactly this override for sent:tatoeba-10901867 (i=4) and "
        "sent:tatoeba-11727272 (i=1) -- but that ledger's own note certifies every entry as "
        "confirmed by the Phase-3 QA 2-vote adversarial campaign, so this pass will not add a row "
        "to it under a provenance it does not have. The record self-documents the split: its "
        "structure_explanation states in both locales that the tokenizer misread 辛い, and the "
        "token's own gloss and conjugation_note both spell out からい. Owner call.",
    ),
    (
        "sent:tatoeba-10083431 translation_literal [en] 'As for this, it's a grapevine branch.'",
        "Carries the same つる/branch slip as the pt-BR literal repaired here. Out of this pass's "
        "brief, which scopes the en layer to the five plain-non-past anchors above; flagged so the "
        "two locales are not left disagreeing unnoticed.",
    ),
]


def load(path: Path) -> list[dict]:
    rows = json.loads(path.read_text(encoding="utf-8"))
    seen: set[tuple] = set()
    for i, r in enumerate(rows):
        missing = {"store", "entity", "slug", "field", "old", "new"} - set(r)
        if missing:
            raise SystemExit(f"row {i}: missing key(s) {sorted(missing)}")
        if r["entity"] != "sentence":
            raise SystemExit(f"row {i} ({r['slug']}): unexpected entity {r['entity']!r}")
        store, field, locale = r["store"], r["field"], r.get("locale")
        if store == "localized_text":
            if field not in LOCALIZED_FIELDS:
                raise SystemExit(f"row {i} ({r['slug']}): unexpected localized field {field!r}")
            if locale not in LOCALES:
                raise SystemExit(f"row {i} ({r['slug']}): unexpected locale {locale!r}")
        elif store == "column":
            if field not in COLUMN_FIELDS:
                raise SystemExit(f"row {i} ({r['slug']}): unexpected sentence column {field!r}")
            if locale is not None:
                raise SystemExit(f"row {i} ({r['slug']}): a column row must not carry a locale")
        else:
            raise SystemExit(f"row {i} ({r['slug']}): unexpected store {store!r}")
        if not isinstance(r["old"], str) or not isinstance(r["new"], str):
            raise SystemExit(f"row {i} ({r['slug']}): `old`/`new` must be strings")
        # A row whose `new` equals its `old` would apply nothing while still counting as a repair in
        # the campaign ledger. That is exactly the defect this follow-up exists to clean up after
        # (skip list §6, sent:gen-960d7cee0887), so reject it outright rather than swallow a no-op.
        if r["old"] == r["new"]:
            raise SystemExit(f"row {i} ({r['slug']}): `new` is identical to `old`")
        key = (store, r["slug"], field, locale)
        if key in seen:
            raise SystemExit(f"row {i}: duplicate target {key}")
        seen.add(key)
    return rows


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

    for r in rows:
        store, slug, field, locale = r["store"], r["slug"], r["field"], r.get("locale")
        label = f"{slug}.{field}" + (f" [{locale}]" if locale else " (sentence column)")

        sent = con.execute("SELECT id, en FROM sentence WHERE slug=?", (slug,)).fetchone()
        if sent is None:
            skipped.append(f"{label}: no such sentence")
            continue
        sid, src_en = sent

        # Layer-A guard. export_corpus.py renders `translation`/en as `sentence.en or
        # localized_text`, so on a mined record the English a reader sees is the immutable source
        # pair -- editing the localized row would be both invisible and a spec §1.1 violation.
        if field == "translation" and locale == "en" and src_en is not None:
            skipped.append(f"{label}: sentence.en (Layer A) is set to {src_en!r} -- this en is a "
                           f"selected source pair, not authored text; refusing to rewrite it")
            continue

        if store == "localized_text":
            hit = con.execute(
                "SELECT value, is_list FROM localized_text WHERE entity_type='sentence' "
                "AND entity_id=? AND field=? AND locale=?", (sid, field, locale)).fetchall()
            if not hit:
                skipped.append(f"{label}: no localized_text row")
                continue
            if len(hit) > 1:
                skipped.append(f"{label}: {len(hit)} rows for one (field, locale) -- ambiguous, "
                               f"not touching it")
                continue
            cur, is_list = hit[0]
            if is_list:
                skipped.append(f"{label}: stored as a list, expected scalar text")
                continue
        else:
            cur = con.execute(f"SELECT {field} FROM sentence WHERE id=?", (sid,)).fetchone()[0]

        if cur == r["new"]:
            already += 1                                       # already repaired; nothing to do
            continue
        if cur != r["old"]:
            skipped.append(f"{label}: current value matches neither the expected defective text "
                           f"nor the rewrite -- not touching it (stored: {cur!r})")
            continue

        print(f"  {label}")
        print(f"     old: {r['old']}")
        print(f"     new: {r['new']}")
        if r.get("why"):
            print(f"     why: {r['why']}")
        if not args.check:
            if store == "localized_text":
                con.execute(
                    "UPDATE localized_text SET value=? WHERE entity_type='sentence' "
                    "AND entity_id=? AND field=? AND locale=?", (r["new"], sid, field, locale))
            else:
                # `field` is constrained to COLUMN_FIELDS by load(), so this interpolation cannot
                # carry anything but a known column name.
                con.execute(f"UPDATE sentence SET {field}=? WHERE id=?", (r["new"], sid))
        changed += 1

    if not args.check:
        con.commit()
    con.close()

    verb = "would repair" if args.check else "repaired"
    print(f"\n{verb} {changed} field(s) of {len(rows)}; {already} already carried the rewrite")
    for s in skipped:
        print(f"  ! {s}")
    print("\ndeliberately NOT changed:")
    for what, why in DEFERRED:
        print(f"  - {what}\n      {why}")
    return 1 if (args.check and changed) else (2 if skipped else 0)


if __name__ == "__main__":
    sys.exit(main())
