#!/usr/bin/env python3
"""Exam-bank gate: every item is answerable, wrong-by-construction elsewhere, and still agrees with
the corpus record it was cut from.

WHY THIS EXISTS (review findings EB-01..EB-10, F3; proposals EB-V1..EB-V10)
--------------------------------------------------------------------------
The previous version of this file took its ground truth from `db/corpus.sqlite` — a git-ignored,
regenerable index. CLAUDE.md declares the exported JSON the source of truth, and the DB is not in the
tree, so on a fresh clone the gate over 6,073 committed items did not skip: it raised
`sqlite3.OperationalError: no such table: vocab` and exited 1, taking validate_all.py's whole run
down (EB-03). Worse, the one check that most needed a complete map built it as
`kana_by_hw = {hw: kana for _, (hw, kana) in vk.items()}`, collapsing the 93 headwords shared by 193
vocab records to whichever row SQLite happened to iterate last — so the "no homophone distractor"
invariant tested one reading per headword and could not have caught a real collision. This rewrite
reads corpus/vocab, corpus/sentences, corpus/readings and corpus/grammar only, and builds the full
uncollapsed headword -> {readings} map (18,388 headwords over 7,401 records plus their `forms`).

The defects the hard checks below were written against, each confirmed on this data at some point:

  EB-01  all 262 text_grammar items were the referenced passage with one span blanked, while the app
         rendered that same passage unblanked above the stem — 100% of 文章の文法 questions leaked
         their own answer. The app no longer renders a passage for text_grammar, and check I is what
         makes that safe: the tg stem must BE the passage with exactly one blank, so nothing is lost
         by not showing it, and an item whose stem drifts from its passage fails here.
  EB-05  93 cloze items printed their own answer elsewhere in the stem because the builder blanked
         only the first occurrence. Those 93 were removed (corpus/exam_banks/removed_items.json);
         check C keeps them out.
  F3     3,777 items addressed vocabulary by SQLite row number. They now carry a `vocab` slug too;
         check D asserts slug and row id name the SAME record, so a rebuild that renumbers vocab
         cannot silently re-point an item at a different word.
  EB-10  no section is short today, but nothing froze that. Check O mirrors the SECTIONS table the
         prototype's paper builder uses and fails if a bank drops under 3x what a paper draws.

Everything the old gate checked is kept (distractor-set shape, cloze blanks, sentence_order
reassembly, paraphrase/usage/listening shape, refs resolve) and re-derived from the corpus instead of
being taken on trust.

ADVISORY SECTION
----------------
Four counters measure item QUALITY rather than correctness — the items are individually right, but a
learner can shortcut them (EB-02 okurigana shape-matching, EB-06 orthography distractor shape, EB-07
reading_comp answerable by scanning, EB-09 an alternative chip ordering that also spells the answer).
Repairing them is a builder change, not a data edit, so they are frozen at their measured values in
scripts/validate/exam_banks_baseline.json: the count may shrink, never grow. An advisory that only
prints a number is not a gate, which is the failure mode this suite just spent a day removing.

Reads the exported JSON only — never db/corpus.sqlite.

Usage: validate_exam_banks.py [--root PATH] [--list]
"""
from __future__ import annotations

import argparse
import collections
import functools
import glob
import json
import re
import sys
import unicodedata
from pathlib import Path
from typing import Any

sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
DEFAULT_ROOT = Path(__file__).resolve().parents[2]
BASELINE = Path(__file__).resolve().parent / "exam_banks_baseline.json"
MAX_SHOWN = 15

# The blank marker, exactly: FULLWIDTH LEFT PAREN + IDEOGRAPHIC SPACE + FULLWIDTH RIGHT PAREN.
BLANK = "（　）"
BANK_RE = re.compile(r"^(n[0-9])_([a-z_]+)\.json$")

# id prefix -> bank type. A file whose items do not carry its prefix is a mis-filed item.
TYPE_PREFIX = {
    "kanji_reading": "kr", "orthography": "or", "context_fill": "cf", "grammar_form": "gf",
    "sentence_order": "so", "text_grammar": "tg", "paraphrase": "pp", "usage": "us",
    "reading_comp": "rc", "listening_task": "lt", "listening_point": "lp",
    "listening_gist": "lg", "listening_say": "ls", "listening_reply": "lr",
}
# 発話表現 (listening_say) and 即時応答 (listening_reply) are genuinely 3-option sections; every
# other choice section is 4-option. sentence_order has no option list at all.
OPTIONS = {t: 4 for t in TYPE_PREFIX}
OPTIONS.update({"listening_say": 3, "listening_reply": 3})
del OPTIONS["sentence_order"]

SPEAKERS = {"M1", "M2", "F1", "F2", "N"}
# Punctuation stripped before comparing an assembled sentence_order answer with its source sentence,
# and before comparing option strings for collisions.
PUNCT = "。、！？!?・ 　「」．，"

# MIRROR of SECTIONS in prototype/app/lib/exam.server.ts — (n5, n4, n3) questions per paper.
# Hardcoded on purpose: this validator must run on a corpus checkout with no prototype present. If
# the TS table changes, change this one in the same commit; check O is what makes a bank that can no
# longer fill its section a build failure instead of a silently shorter paper (EB-10).
PAPER_COUNTS = {
    "kanji_reading": (7, 7, 8),
    "orthography": (5, 5, 6),
    "context_fill": (6, 8, 11),
    "paraphrase": (3, 4, 5),
    "usage": (0, 4, 5),
    "grammar_form": (9, 8, 13),
    "sentence_order": (4, 4, 5),
    "text_grammar": (2, 3, 4),
    "reading_comp": (3, 4, 4),
}
# Listening is absent from PAPER_COUNTS for the same reason it is absent from SECTIONS: the banks are
# voice-ready scripts with audio "pending", so no paper draws from them yet.

# exam.server.ts admits at most ONE question per passage inside a section, so for passage-backed
# types the capacity is the number of DISTINCT passages, not the item count.
PASSAGE_TYPES = {"reading_comp", "text_grammar"}
MIN_RATIO = 3  # a learner should not meet the same item every third paper


def hiragana_tail(s: str) -> str:
    i = len(s)
    while i > 0 and 0x3041 <= ord(s[i - 1]) <= 0x309F:
        i -= 1
    return s[i:]


def hiragana_head(s: str) -> str:
    i = 0
    while i < len(s) and 0x3041 <= ord(s[i]) <= 0x309F:
        i += 1
    return s[:i]


def fold(s: str) -> str:
    """NFKC + katakana->hiragana + punctuation/space strip. Two options that fold together are two
    right answers however differently they are written (ブルー vs ぶるー, half-width vs full-width)."""
    s = unicodedata.normalize("NFKC", s)
    s = "".join(chr(ord(c) - 0x60) if 0x30A1 <= ord(c) <= 0x30F6 else c for c in s)
    return "".join(c for c in s if c not in PUNCT)


def strip_punct(s: str) -> str:
    return "".join(c for c in s if c not in PUNCT)


def count_orderings(pieces: tuple[str, ...], answer: str, cap: int = 2) -> int:
    """How many DISTINCT orderings of `pieces` (as sequences of strings, so repeated chips do not
    inflate the count) concatenate to `answer`. Stops at `cap`."""
    items = sorted(collections.Counter(pieces).items())
    keys = [k for k, _ in items]

    @functools.lru_cache(maxsize=None)
    def rec(state: tuple[int, ...], pos: int) -> int:
        if pos == len(answer):
            return 1 if not any(state) else 0
        n = 0
        for i, k in enumerate(keys):
            if state[i] and answer.startswith(k, pos):
                nxt = list(state)
                nxt[i] -= 1
                n += rec(tuple(nxt), pos + len(k))
                if n >= cap:
                    break
        return n

    out = rec(tuple(c for _, c in items), 0)
    rec.cache_clear()
    return out


def load_list(path: Path) -> list[dict[str, Any]]:
    data = json.loads(path.read_text(encoding="utf-8"))
    return data if isinstance(data, list) else []


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=str(DEFAULT_ROOT), help="tree to validate (default: repo root)")
    ap.add_argument("--list", action="store_true", help="print every failure instead of the first 15")
    args = ap.parse_args()
    root = Path(args.root).resolve()
    banks_dir = root / "corpus" / "exam_banks"
    if not banks_dir.exists():
        print("FAIL validate_exam_banks: corpus/exam_banks is MISSING — a gate whose data vanished must FAIL, not certify nothing")
        return 1

    # ---- ground truth, from the committed JSON only -------------------------------------------
    vocab: list[dict[str, Any]] = []
    for f in sorted(glob.glob(str(root / "corpus" / "vocab" / "*.json"))):
        vocab += load_list(Path(f))
    v_by_slug = {v["slug"]: v for v in vocab}
    v_by_id = {v["id"]: v for v in vocab}
    # UNCOLLAPSED headword -> every reading that spelling can take, including alternate `forms`.
    # The old dict comprehension kept one reading per headword; a homophone distractor is exactly the
    # case where a headword has more than one.
    hw_readings: dict[str, set[str]] = collections.defaultdict(set)
    for v in vocab:
        hw_readings[v["headword"]].add(v["kana"])
        for fm in (v.get("forms") or []):
            spelling = fm.get("form") or fm.get("headword")
            if spelling:
                hw_readings[spelling].add(fm.get("kana") or v["kana"])

    sent_jp: dict[str, str] = {}
    bank_json = root / "corpus" / "sentences" / "bank.json"
    if bank_json.exists():
        for s in load_list(bank_json):
            sent_jp[s["slug"]] = s["jp"]
    read_jp: dict[str, str] = {}
    for f in sorted(glob.glob(str(root / "corpus" / "readings" / "*.json"))):
        for r in load_list(Path(f)):
            read_jp[r["slug"]] = r["jp"]
    grammar_refs: set[str] = set()
    for f in sorted(glob.glob(str(root / "corpus" / "grammar" / "*.json"))):
        for g in load_list(Path(f)):
            grammar_refs.add(g["key"])       # exam items reference grammar by key ...
            grammar_refs.add(g["slug"])      # ... accept the slug too, so an exporter change is fine

    fails: list[str] = []
    total = 0
    seen_ids: dict[str, str] = {}
    per_bank: dict[tuple[str, str], list[dict[str, Any]]] = {}

    for path in sorted(banks_dir.glob("*.json")):
        m = BANK_RE.match(path.name)
        if not m:
            continue  # sidecars (removed_items.json) are not banks
        level, btype = m.group(1), m.group(2)
        if btype not in TYPE_PREFIX:
            fails.append(f"A {path.name}: unknown bank type {btype!r}")
            continue
        items = load_list(path)
        per_bank[(level, btype)] = items
        prefix = TYPE_PREFIX[btype]

        for it in items:
            total += 1
            iid = it.get("id")
            if not isinstance(iid, str) or not iid:
                fails.append(f"A {path.name}: item with no id")
                continue

            # --- A: identity ------------------------------------------------------------------
            if iid in seen_ids:
                fails.append(f"A {iid}: duplicate id (also in {seen_ids[iid]})")
            seen_ids[iid] = path.name
            parts = iid.split(":")
            if parts[0] != prefix:
                fails.append(f"A {iid}: id prefix is not {prefix!r} ({path.name})")
            if len(parts) < 2 or parts[1] != level:
                fails.append(f"A {iid}: id level disagrees with {path.name}")
            if it.get("level") != level:
                fails.append(f"A {iid}: level {it.get('level')!r} in a {level} file")

            # --- B: option set ----------------------------------------------------------------
            opts: list[str] | None = None
            if "distractors" in it:
                opts = [it.get("correct", ""), *it["distractors"]]
            elif "wrong" in it:
                opts = [it.get("correct", ""), *it["wrong"]]
            if opts is not None:
                want = OPTIONS.get(btype)
                if want is not None and len(opts) != want:
                    fails.append(f"B {iid}: {len(opts)} options, {btype} takes {want}")
                if any(not isinstance(o, str) or not o.strip() for o in opts):
                    fails.append(f"B {iid}: blank or non-string option")
                elif len({fold(o) for o in opts}) != len(opts):
                    fails.append(f"B {iid}: options collide under NFKC+kana fold: {opts}")

            # --- C: blank integrity (EB-05) ---------------------------------------------------
            stem = it.get("stem")
            if isinstance(stem, str) and BLANK in stem:
                if stem.count(BLANK) != 1:
                    fails.append(f"C {iid}: {stem.count(BLANK)} blanks in the stem")
                rest = stem.replace(BLANK, "")
                correct = it.get("correct") or ""
                if correct and correct in rest:
                    fails.append(f"C {iid}: stem prints its own answer {correct!r} outside the blank")
                for d in it.get("distractors", []):
                    if d and d in rest:
                        fails.append(f"C {iid}: stem contains distractor {d!r}")

            # --- D: references resolve, and the slug agrees with the row id (F3) --------------
            sslug = it.get("sentence")
            if sslug and sslug not in sent_jp:
                fails.append(f"D {iid}: sentence {sslug} does not resolve")
                sslug = None
            rslug = it.get("reading")
            if rslug and rslug not in read_jp:
                fails.append(f"D {iid}: reading {rslug} does not resolve")
                rslug = None
            gref = it.get("grammar")
            if gref and gref not in grammar_refs:
                fails.append(f"D {iid}: grammar {gref} does not resolve")
            vslug, vrec = it.get("vocab"), None
            if vslug:
                vrec = v_by_slug.get(vslug)
                if vrec is None:
                    fails.append(f"D {iid}: vocab {vslug} does not resolve")
            if "vocab_id" in it:
                if vslug is None:
                    fails.append(f"D {iid}: vocab_id {it['vocab_id']} with no `vocab` slug beside it")
                elif vrec is not None and vrec["id"] != it["vocab_id"]:
                    fails.append(f"D {iid}: vocab {vslug} is id {vrec['id']}, item says {it['vocab_id']}")
                elif it["vocab_id"] not in v_by_id:
                    fails.append(f"D {iid}: vocab_id {it['vocab_id']} is not a vocab row")

            # --- E..N: per-type derivation from the corpus record ----------------------------
            if btype == "kanji_reading":
                if vrec is None:
                    fails.append(f"E {iid}: no resolvable vocab to check the reading against")
                elif it.get("stem") != vrec["headword"] or it.get("correct") != vrec["kana"]:
                    fails.append(f"E {iid}: {it.get('stem')!r}/{it.get('correct')!r} != vocab "
                                 f"{vrec['headword']!r}/{vrec['kana']!r}")

            elif btype == "orthography":
                if vrec is None:
                    fails.append(f"F {iid}: no resolvable vocab to check the spelling against")
                elif it.get("stem") != vrec["kana"] or it.get("correct") != vrec["headword"]:
                    fails.append(f"F {iid}: {it.get('stem')!r}/{it.get('correct')!r} != vocab "
                                 f"{vrec['kana']!r}/{vrec['headword']!r}")
                for d in it.get("distractors", []):
                    if it.get("stem") in hw_readings.get(d, ()):
                        fails.append(f"F {iid}: distractor {d!r} also reads {it.get('stem')!r} "
                                     f"— two right answers")

            elif btype == "context_fill":
                if vrec is not None and it.get("correct") != vrec["headword"]:
                    fails.append(f"G {iid}: answer {it.get('correct')!r} != vocab {vrec['headword']!r}")
                if sslug and BLANK in (it.get("stem") or ""):
                    filled = it["stem"].replace(BLANK, it.get("correct") or "")
                    if filled != sent_jp[sslug]:
                        fails.append(f"G {iid}: filled stem is not the source sentence")
                elif BLANK not in (it.get("stem") or ""):
                    fails.append(f"G {iid}: no blank in the stem")

            elif btype == "grammar_form":
                if BLANK not in (it.get("stem") or ""):
                    fails.append(f"H {iid}: no blank in the stem")
                elif sslug:
                    filled = it["stem"].replace(BLANK, it.get("correct") or "")
                    if filled != sent_jp[sslug]:
                        fails.append(f"H {iid}: filled stem is not the source sentence")
                if sslug and (it.get("correct") or "") not in sent_jp[sslug]:
                    fails.append(f"H {iid}: answer {it.get('correct')!r} is not in the source sentence")

            elif btype == "text_grammar":
                # EB-01: the stem must BE the passage with one blank. That is what makes it safe for
                # the app not to render the passage separately, and it fails if either side drifts.
                if BLANK not in (it.get("stem") or ""):
                    fails.append(f"I {iid}: no blank in the stem")
                elif not rslug:
                    fails.append(f"I {iid}: no resolvable passage")
                elif it["stem"].replace(BLANK, it.get("correct") or "") != read_jp[rslug]:
                    fails.append(f"I {iid}: filled stem is not the passage {rslug}")

            elif btype == "sentence_order":
                pieces = it.get("pieces") or []
                if len(pieces) < 2 or any(not isinstance(p, str) or not p.strip() for p in pieces):
                    fails.append(f"J {iid}: piece list is empty, too short, or has a blank chip")
                elif "".join(pieces) != it.get("answer"):
                    fails.append(f"J {iid}: pieces do not reassemble the answer")
                if sslug and strip_punct(sent_jp[sslug]) != strip_punct(it.get("answer") or ""):
                    fails.append(f"J {iid}: answer is not the source sentence")

            elif btype == "paraphrase":
                target = it.get("target") or ""
                if vrec is not None and target != vrec["headword"]:
                    fails.append(f"K {iid}: target {target!r} != vocab {vrec['headword']!r}")
                if not target or target not in (it.get("stem") or ""):
                    fails.append(f"K {iid}: target {target!r} is not in the stem")
                if it.get("correct") == target:
                    fails.append(f"K {iid}: the paraphrase is the target itself")
                if sslug and it.get("stem") != sent_jp[sslug]:
                    fails.append(f"K {iid}: stem drifted from the source sentence")

            elif btype == "usage":
                target = it.get("target") or ""
                wrong = it.get("wrong") or []
                if vrec is not None and target != vrec["headword"]:
                    fails.append(f"L {iid}: target {target!r} != vocab {vrec['headword']!r}")
                if target not in (it.get("correct") or ""):
                    fails.append(f"L {iid}: the right sentence does not use {target!r}")
                if any(target not in w for w in wrong):
                    fails.append(f"L {iid}: a wrong option does not use {target!r} — not a usage item")
                if sslug and it.get("correct") != sent_jp[sslug]:
                    fails.append(f"L {iid}: right sentence drifted from the source sentence")

            elif btype == "reading_comp":
                if not (it.get("question") or "").strip():
                    fails.append(f"M {iid}: no question")
                if not rslug:
                    fails.append(f"M {iid}: no resolvable passage")

            elif btype.startswith("listening"):
                script = it.get("script") or []
                if not script or any(t.get("speaker") not in SPEAKERS
                                     or not (t.get("text") or "").strip() for t in script):
                    fails.append(f"N {iid}: script missing, or a turn has no speaker/text")
                if btype in ("listening_task", "listening_point", "listening_gist") \
                        and not (it.get("question") or "").strip():
                    fails.append(f"N {iid}: no question")

    # ---- O: sufficiency (EB-10) -------------------------------------------------------------
    print("bank capacity vs the paper (SECTIONS mirror; passage types count DISTINCT passages):")
    for btype, counts in PAPER_COUNTS.items():
        for level, req in zip(("n5", "n4", "n3"), counts):
            if req == 0:
                continue  # n5 usage: the real N5 paper has no 用法 section
            items = per_bank.get((level, btype))
            if items is None:
                fails.append(f"O {level}_{btype}.json: bank missing, paper needs {req}")
                continue
            eff = len({i.get("reading") for i in items}) if btype in PASSAGE_TYPES else len(items)
            ratio = eff / req
            mark = ""
            if eff < req:
                fails.append(f"O {level}_{btype}: {eff} usable, the paper draws {req} — section short")
                mark = "SHORT"
            elif ratio < MIN_RATIO:
                fails.append(f"O {level}_{btype}: {eff} usable vs {req} per paper "
                             f"({ratio:.1f}x, floor {MIN_RATIO}x)")
                mark = "THIN"
            print(f"  {btype:15s} {level}  {eff:4d} / {req:3d}  {ratio:5.1f}x {mark}")

    # ---- advisory counters, frozen against a baseline ---------------------------------------
    adv: dict[str, int] = collections.Counter()
    for (level, btype), items in per_bank.items():
        for it in items:
            if btype == "kanji_reading":
                stem = it.get("stem") or ""
                tail, head = hiragana_tail(stem), hiragana_head(stem)
                if not tail and not head:
                    continue

                def shaped(o: str, tail: str = tail, head: str = head) -> bool:
                    return (not tail or o.endswith(tail)) and (not head or o.startswith(head))

                if shaped(it.get("correct") or "") and \
                        not any(shaped(d) for d in it.get("distractors", [])):
                    adv["okurigana_giveaway"] += 1
            elif btype == "orthography":
                stem, correct = it.get("stem") or "", it.get("correct") or ""
                for d in it.get("distractors", []):
                    if abs(len(d) - len(correct)) >= 2:
                        adv["orthography_longshot_distractors"] += 1

                def fits(o: str, stem: str = stem) -> bool:
                    t, h = hiragana_tail(o), hiragana_head(o)
                    return (not t or stem.endswith(t)) and (not h or stem.startswith(h))

                if fits(correct) and sum(1 for d in it.get("distractors", []) if fits(d)) < 2:
                    adv["orthography_shape_solvable"] += 1
            elif btype == "reading_comp":
                passage = read_jp.get(it.get("reading") or "", "")
                if passage and (it.get("correct") or "") in passage \
                        and not any(d in passage for d in it.get("distractors", [])):
                    adv["reading_comp_string_match"] += 1
            elif btype == "sentence_order":
                if count_orderings(tuple(it.get("pieces") or []), it.get("answer") or "") > 1:
                    adv["sentence_order_ambiguous"] += 1

    base: dict[str, Any] = {}
    if BASELINE.exists():
        base = json.loads(BASELINE.read_text(encoding="utf-8"))
    print("advisory (item quality — may shrink, never grow; baseline "
          f"{BASELINE.name}):")
    for key in sorted(set(base) | set(adv)):
        if key.startswith("_"):
            continue
        now, was = adv.get(key, 0), base.get(key, {}).get("count")
        if was is None:
            fails.append(f"P advisory {key}: no baseline entry — add one with a reason")
            print(f"  {key:35s} {now:5d}  (UNBASELINED)")
            continue
        print(f"  {key:35s} {now:5d}  baseline {was}" + ("  GREW" if now > was else ""))
        if now > was:
            fails.append(f"P advisory {key} grew: {was} -> {now}")
    for key in base:
        if not key.startswith("_") and key not in adv and base[key].get("count", 0) > 0:
            fails.append(f"P baseline {key} matches nothing in the banks — stale entry")

    # Reported, not gated: all text_grammar passages are also reading_comp passages, and the app
    # resets its one-passage-per-section guard per section (EB-08). The repair is in exam.server.ts,
    # not in this data, so this line is a measurement rather than a rule.
    tg_p = {i.get("reading") for its in
            [v for (l, t), v in per_bank.items() if t == "text_grammar"] for i in its}
    rc_p = {i.get("reading") for its in
            [v for (l, t), v in per_bank.items() if t == "reading_comp"] for i in its}
    print(f"  passages used by both text_grammar and reading_comp: {len(tg_p & rc_p)} "
          f"(tg {len(tg_p)}, rc {len(rc_p)}) — app-side, see EB-08")

    shown = fails if args.list else fails[:MAX_SHOWN]
    for line in shown:
        print("  FAIL", line)
    if len(fails) > len(shown):
        print(f"  ... {len(fails) - len(shown)} more (--list for all)")
    print(f"\nvalidate_exam_banks: {total} items in {len(per_bank)} banks, "
          + ("ALL OK" if not fails else f"FAIL {len(fails)}"))
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
