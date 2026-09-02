#!/usr/bin/env python3
"""Restore the Layer-A English anchor on the mined Tatoeba sentences whose ingestion dropped it.

342 bank records export with no `translation.en`. That anchor is what makes the Layer-B pt-BR
machine-validatable against a Layer-A source (spec 1.1), so a missing one silently downgrades a record
from "checkable" to "trust the author". Three different things produced those 342, and only one of them
is a defect:

  324  source='tatoeba', tags ["mined", "stage:"]  -- A REAL BUG. Repaired here.
   12  the sentences a verified Layer-A pairing audit DELIBERATELY unlinked. NOT touched. See below.
    6  source='generated', ai_generated=1          -- no human English exists. NOT touched.

THE BUG. scripts/ingest/mine_tatoeba_stages.py selects candidates and REQUIRES an English pairing
(`if ... rid not in eng: continue`), writing each one as {tatoeba_id, jp, en, stage} into
research/derived/tatoeba_mined_stages.json. The pt-BR authoring pass that followed used a narrower row
shape -- {tatoeba_id, jp, pt, pt_literal, register, reject, reject_reason} -- and `en` is simply not in
it. Those authored batches, not the mine output, became research/derived/mined_pt/_accepted.json. From
there `ingest_mined_stages.py` line 110 does `"en": r.get("en")` against a row that has never carried
the key, so every one of the 324 was persisted with en=None, and persist_dissection.persist()'s
`"en" if en else "dict"` recorded pt_validated_against='dict'. Nothing was corrupted -- a value was
dropped in a JSON round-trip and no one downstream noticed, because a missing optional field looks
exactly like a field that was never supposed to be there.

WHERE THE ENGLISH COMES FROM. Not from this script, and not from a model. tatoeba_mined_stages.json
still holds the exact pairing the miner recorded before it was dropped, so the repair is a replay of a
value this project already had, with no tie-break to make: 63 of the 324 have more than one directly
linked English row upstream, and the artifact says which one the pipeline picked. Every value is
re-verified here against raw_tatoeba_translation for that EXACT jp_id, so a string that is not a genuine
direct pairing cannot be written even if the artifact were wrong. All 324 were additionally confirmed
against the raw dumps themselves (jpn_sentences.tsv.bz2 + links.tar.bz2 + eng_sentences.tsv.bz2), not
just the ingested copy: 324/324 jp byte-identical, 324/324 English present verbatim among that jp id's
direct links.

THE 12 THAT STAY EMPTY, AND WHY THIS SCRIPT REFUSES THEM. research/derived/qa_queues/round3/
layer_a_pairing_verified.json is a two-round verified queue in which a reviewer confirmed, one by one,
that the upstream Tatoeba English attached to these records does not say what the Japanese says
(sent:tatoeba-77972: the Japanese is a partial negation on wake dewa nai, the English a total one) and
that no better upstream row exists. apply_layer_a_pairing.py then removed each pairing on purpose. They
are inside the gap because they were *fixed*, and re-linking them from the same upstream data would undo
a human-verified correction and put the exact defect back. They are refused loudly, by slug, rather than
filtered out quietly, so this reasoning is visible on every run.

WHAT IS NOT WRITTEN. pt_validated_against stays 'dict' on all 324. It records what the pt-BR was
actually checked against, and these translations were authored from the Japanese and reviewed by two
checkers who never saw this English. Flipping it to 'en' because an anchor now exists would assert a
validation that did not happen. The anchor makes that validation possible; it is not the validation.

DB ONLY -- writes sentence.en, the column the exporter reads first
(export_corpus.py: `en=s["en"] or SLen.get((sid, "translation"))`) and the column
persist_dissection.persist() would have filled had the value survived. Nothing under corpus/ is touched;
run the exporter afterwards.

Idempotent: targets are derived from the live DB using the exporter's own definition of "has no anchor",
so a second run finds nothing to do and reports 0. Every write is additionally guarded in its own WHERE
clause, so it cannot overwrite an anchor that appeared in between.

Usage: apply_en_anchor_backfill.py [--check]
"""
from __future__ import annotations

import argparse
import json
import re
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
MINE = ROOT / "research" / "derived" / "tatoeba_mined_stages.json"
PAIRING = ROOT / "research" / "derived" / "qa_queues" / "round3" / "layer_a_pairing_verified.json"

SLUG_RE = re.compile(r"^sent:tatoeba-(\d+)$")

# The gap, as the exporter sees it: neither the sentence.en column nor a localized_text en row.
GAP_SQL = """
SELECT s.id, s.slug, s.jp, s.source, s.jp_source, s.ai_generated, s.tags
  FROM sentence s
  LEFT JOIN localized_text lt
    ON lt.entity_type='sentence' AND lt.entity_id=s.id
   AND lt.field='translation' AND lt.locale='en'
 WHERE (s.en IS NULL OR trim(s.en)='')
   AND (lt.value IS NULL OR trim(lt.value)='')
 ORDER BY s.id
"""


def load_mine() -> dict[int, dict]:
    """The miner's own record of which English row it paired with each Japanese id."""
    doc = json.loads(MINE.read_text(encoding="utf-8"))
    out: dict[int, dict] = {}
    for candidates in doc["candidates"].values():
        for cand in candidates:
            out.setdefault(int(cand["tatoeba_id"]), cand)
    return out


def load_unlinked() -> dict[str, str]:
    """Slugs a verified audit deliberately unlinked -> the reviewer's reason, for the refusal message."""
    doc = json.loads(PAIRING.read_text(encoding="utf-8"))
    return {r["id"]: (r.get("why") or "").strip()
            for r in doc["rows"]
            if r.get("verdict") == "fix" and (r.get("endorsed_action") or "") == "unlink-en"}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true", help="report only; write nothing")
    args = ap.parse_args()

    for path in (DB, MINE, PAIRING):
        if not path.exists():
            print(f"missing required input: {path}")
            return 2

    mine = load_mine()
    unlinked = load_unlinked()
    con = sqlite3.connect(DB)
    con.execute("PRAGMA busy_timeout=60000")

    gap = con.execute(GAP_SQL).fetchall()
    applied = 0
    legit: list[str] = []      # expected, explained, not a defect
    refused: list[str] = []    # a precondition failed -- someone must look

    print(f"{len(gap)} record(s) currently export with no translation.en\n")

    for sid, slug, jp, source, jp_source, ai_generated, tags in gap:
        tag_list = json.loads(tags or "[]")

        # -- legitimately anchorless: an AI-generated sentence has no human English to point at, and
        #    authoring one would launder model output into a Layer-A slot (spec 1.1 / 1.3).
        if int(ai_generated or 0) or source == "generated" or jp_source in ("generated", "ai-generated"):
            legit.append(f"{slug}: ai_generated -- no human English source exists; en is optional "
                         f"(contracts/common.schema.json LocaleText requires only pt-BR)")
            continue

        # -- legitimately anchorless: a verified audit removed this pairing on purpose.
        if slug in unlinked:
            why = unlinked[slug]
            legit.append(f"{slug}: REFUSING to re-link -- apply_layer_a_pairing.py unlinked this on "
                         f"purpose after two rounds of verification. {why[:180]}")
            continue

        match = SLUG_RE.match(slug)
        if not match:
            refused.append(f"{slug}: not a sent:tatoeba-<id> slug, so no upstream id to look up")
            continue
        jp_id = int(match.group(1))

        cand = mine.get(jp_id)
        if cand is None:
            refused.append(f"{slug}: no candidate for jp_id {jp_id} in {MINE.name} -- this record did "
                           f"not come through the mined-stage path; not guessing an anchor for it")
            continue

        # Precondition: the Japanese is Layer A and must be byte-exact upstream, in BOTH the raw table
        # and the artifact. If it drifted, the recorded pairing is no longer known to belong to it.
        raw = con.execute("SELECT text FROM raw_tatoeba_sentence WHERE id=?", (jp_id,)).fetchone()
        if raw is None:
            refused.append(f"{slug}: jp_id {jp_id} is not in raw_tatoeba_sentence")
            continue
        if raw[0] != jp:
            refused.append(f"{slug}: stored jp does not match raw_tatoeba_sentence byte-for-byte -- "
                           f"refusing to attach an anchor to altered Layer-A Japanese")
            continue
        if cand.get("jp") != jp:
            refused.append(f"{slug}: stored jp does not match the mined candidate's jp")
            continue

        en = (cand.get("en") or "").strip()
        if not en:
            refused.append(f"{slug}: the mined candidate carries no English")
            continue

        # Precondition, and the one that matters most: the value must be a real English row DIRECTLY
        # linked to this exact Japanese id upstream. Not a translation of a translation, not authored.
        hit = con.execute(
            "SELECT 1 FROM raw_tatoeba_translation WHERE jp_id=? AND lang='eng' AND text=? LIMIT 1",
            (jp_id, en)).fetchone()
        if hit is None:
            refused.append(f"{slug}: the candidate English is not a direct eng pairing of jp_id "
                           f"{jp_id} in raw_tatoeba_translation -- refusing to write it")
            continue

        if "mined" not in tag_list:
            refused.append(f"{slug}: expected the 'mined' tag on a mined-stage record, found {tag_list}")
            continue

        print(f"  {slug}  (tatoeba jp_id {jp_id})")
        print(f"     en: {en}")
        if not args.check:
            # Guarded write: re-asserts the precondition inside the statement itself.
            cur = con.execute(
                "UPDATE sentence SET en=? WHERE id=? AND (en IS NULL OR trim(en)='')", (en, sid))
            if cur.rowcount != 1:
                refused.append(f"{slug}: guarded UPDATE matched {cur.rowcount} rows, expected 1")
                continue
        applied += 1

    if not args.check:
        con.commit()

    verb = "would backfill" if args.check else "backfilled"
    print(f"\n{verb} {applied} en anchor(s) from Tatoeba's own direct pairings")
    print(f"legitimately anchorless, left alone: {len(legit)}")
    for line in legit:
        print(f"  - {line}")
    if refused:
        print(f"\nREFUSED (a precondition failed -- look at these): {len(refused)}")
        for line in refused:
            print(f"  ! {line}")
    if not args.check and applied:
        print("\nnext: re-run the corpus exporter so corpus/sentences/bank.json carries the anchors.")
    con.close()
    return 1 if (args.check and applied) else (2 if refused else 0)


if __name__ == "__main__":
    sys.exit(main())
