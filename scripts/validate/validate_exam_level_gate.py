#!/usr/bin/env python3
"""Exam-bank LEVEL gate: every item's learner-visible Japanese is inside its level's taught set.

WHY THIS EXISTS (readiness finding G3, `research/reports/readiness/jlpt_course_path.md`)
----------------------------------------------------------------------------------------
`validate_exam_banks.py` proves an item is ANSWERABLE — the key is right, the options are distinct,
the blank is intact, the refs resolve, the bank is deep enough. It never asks whether the item is
answerable BY A LEARNER AT THAT LEVEL, and neither did any of the other 39 validators. Measured on
this data the omission is not theoretical: `kr:n5:1` tests 嗚呼 (嗚 has no kanji record at all),
`or:n5:3` tests 青 which the course does not unlock until N4, and the N5 表記 bank holds **3
level-appropriate items out of 379** against a paper that draws 5 — the N5 orthography section
cannot produce one honest paper. N4 言い換え類義 is 1 of 60 against a paper that draws 4.

THE DEFINITION THIS FILE IMPLEMENTS
-----------------------------------
An exam item is **level-appropriate** when every kanji, every vocabulary item and every grammar
point that its LEARNER-VISIBLE Japanese requires is inside the taught set at the end of that level.

  * **Learner-visible Japanese** is everything the app prints or plays for that item: the stem, the
    question, the correct option, every distractor / wrong option, the `pieces` of an ordering item,
    the `target` of a paraphrase/usage item, the passage behind a `reading_comp` item, and every
    turn of a listening script. Options count: a learner cannot eliminate an orthography distractor
    whose kanji they have never met, so the kanji in an option must be taught too.
  * **The taught set at the end of a level** is the `cumulative_known_set` of the LAST lesson of
    that level's course module (last topic by `order`, last lesson by `order`). The course's cks is
    monotonic and cross-module cumulative — pre-N5 ⊂ N5 ⊂ N4 ⊂ N3 — so that one lesson is the whole
    level. Check T below asserts it rather than assuming it.
  * **What each dimension is derived from — the corpus's own dissection, never a re-guess:**
      - kanji: every CJK ideograph in the visible strings, looked up as `kanji:<char>`.
      - vocab: the item's own `vocab` slug (kr/or/cf/pp/us name their word), plus — for an item whose
        stem IS a bank sentence with a blank (cf/gf/so/pp/us/lr) — every `tokens[].vocab` slug of the
        sentence the item's `sentence` ref names.
      - grammar: the item's own `grammar` key (gf/tg), plus the `grammar[]` tags of that same source
        sentence. 「一人で行くしかない」 is an N5 sentence_order item built on しかない, which the
        course does not teach until N3; the sentence's own dissection is what says so.
    Reading passages carry tokens without vocab links, so a passage is checked on the kanji
    dimension only. That is a data limitation, stated rather than hidden.

WHY A RATCHET AND NOT A HARD FLOOR
----------------------------------
3,565 of 6,048 items are inappropriate today. The repair is not a data edit: it is the A2 builder
regeneration (`APP_PLAN.md` W17/W18) selecting from level-clean material in the first place. So the
per-(level, family) inappropriate counts are frozen in `exam_level_baseline.json`: a count may
SHRINK freely (lower the ceiling in the same commit), and if it GROWS this gate fails, because a
bank rebuild that puts MORE untaught Japanese in front of a learner must be a visible decision. A
ceiling naming a bank that no longer exists is a failure too, so the file cannot rot into decoration.

**The rule the A2 builder must implement to pass this gate at 0** is the definition above, applied at
SELECTION time: reject a candidate item unless every kanji in stem+options+passage+script has
`kanji:<c>` in the level's taught set, its own `vocab` slug is in the taught vocab, every
`tokens[].vocab` of its source sentence is in the taught vocab, and its own `grammar` key plus every
`grammar[]` tag of its source sentence is in the taught grammar. When a family's ceiling reaches 0,
sufficiency stops being a printed number and becomes a hard check (see check S).

Reads the exported JSON only — never db/corpus.sqlite.

Usage: validate_exam_level_gate.py [--root PATH] [--list]
"""
from __future__ import annotations

import argparse
import collections
import glob
import json
import re
import sys
from pathlib import Path
from typing import Any

sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
sys.path.insert(0, str(Path(__file__).resolve().parent))

# The paper table lives in ONE place. validate_exam_banks.py hardcodes it as a deliberate mirror of
# SECTIONS in prototype/app/lib/exam.server.ts; importing it here means the two gates can never
# disagree about how many questions a section draws.
from validate_exam_banks import (  # noqa: E402
    BANK_RE,
    MIN_RATIO,
    PAPER_COUNTS,
    PASSAGE_TYPES,
    TYPE_PREFIX,
)

DEFAULT_ROOT = Path(__file__).resolve().parents[2]
BASELINE = Path(__file__).resolve().parent / "exam_level_baseline.json"
MAX_SHOWN = 20          # failure lines printed without --list
MAX_ITEMS_PER_FAMILY = 8  # example inappropriate items printed for a family over its ceiling

LEVELS = ("n5", "n4", "n3")
# Course modules in teaching order. A level's taught set is the last lesson of ITS module; the
# earlier modules are listed so check T can prove nothing taught earlier fell out of it.
MODULE_ORDER = ("pre-n5", "n5", "n4", "n3")

# CJK ideographs: Unified, Extension A, and the compatibility block. Kana, punctuation, romaji and
# the iteration mark are not kanji and are not gated.
KANJI_RE = re.compile(r"[㐀-䶿一-鿿豈-﫿]")

# Listening counts from design/exam_simulator.md. REPORTED, never gated for sufficiency, for the
# same reason listening is absent from PAPER_COUNTS in validate_exam_banks.py: every listening item
# is audio "pending" and no paper draws from these banks yet. The level ratchet DOES cover them —
# an untaught kanji in a script is untaught whether or not a paper draws it today.
LISTENING_PAPER_COUNTS = {
    "listening_task": (7, 8, 6),
    "listening_point": (6, 7, 6),
    "listening_gist": (0, 0, 3),
    "listening_say": (5, 5, 4),
    "listening_reply": (6, 8, 9),
}
ALL_PAPER_COUNTS = {**PAPER_COUNTS, **LISTENING_PAPER_COUNTS}
GATED_FOR_SUFFICIENCY = set(PAPER_COUNTS)

# Field families whose stem is (or is built from) the sentence its `sentence` ref names.
VISIBLE_STR_FIELDS = ("stem", "question", "correct", "answer", "target")
VISIBLE_LIST_FIELDS = ("distractors", "wrong", "pieces")


def load_list(path: Path) -> list[dict[str, Any]]:
    data = json.loads(path.read_text(encoding="utf-8"))
    return data if isinstance(data, list) else []


def gram_slug(ref: str) -> str:
    """Exam items address grammar by the bare `key` ("tai"), the rest of the corpus by the slug
    ("gram:tai") — readiness G13. Normalize to slug space, which is what a cks holds."""
    return ref if ref.startswith("gram:") else "gram:" + ref


def module_lessons(root: Path, module: str) -> list[tuple[int, int, str, dict[str, Any]]]:
    """Every lesson of a course module, in teaching order: (topic order, lesson order, id, cks)."""
    cjson = root / "course" / module / "course.json"
    if not cjson.exists():
        return []
    course = json.loads(cjson.read_text(encoding="utf-8"))
    out: list[tuple[int, int, str, dict[str, Any]]] = []
    for topic in course.get("topics", []):
        tdir = (root / "course" / module / topic["path"]).parent
        for lf in sorted(tdir.glob("lesson-*.json")):
            les = json.loads(lf.read_text(encoding="utf-8"))
            out.append((int(topic.get("order", 0)), int(les.get("order", 0)),
                        les.get("id", lf.name), les.get("cumulative_known_set") or {}))
    out.sort(key=lambda r: (r[0], r[1]))
    return out


def cks_sets(cks: dict[str, Any]) -> dict[str, set[str]]:
    return {k: set(cks.get(k) or []) for k in ("kanji", "vocab", "grammar")}


def visible_jp(it: dict[str, Any], btype: str, read_jp: dict[str, str]) -> list[str]:
    """Every Japanese string this item puts in front of a learner."""
    out: list[str] = []
    for k in VISIBLE_STR_FIELDS:
        v = it.get(k)
        if isinstance(v, str) and v:
            out.append(v)
    for k in VISIBLE_LIST_FIELDS:
        for v in (it.get(k) or []):
            if isinstance(v, str):
                out.append(v)
    for turn in (it.get("script") or []):
        if isinstance(turn, dict) and turn.get("text"):
            out.append(str(turn["text"]))
    # reading_comp prints the passage above the question. text_grammar does NOT (its stem IS the
    # passage with one blank — validate_exam_banks check I is what makes that safe), so adding the
    # passage there would double-count the same characters.
    if btype == "reading_comp":
        out.append(read_jp.get(it.get("reading") or "", ""))
    return [s for s in out if s]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=str(DEFAULT_ROOT), help="tree to validate (default: repo root)")
    ap.add_argument("--list", action="store_true",
                    help="print every inappropriate item and what is untaught in it")
    args = ap.parse_args()
    root = Path(args.root).resolve()
    fails: list[str] = []

    banks_dir = root / "corpus" / "exam_banks"
    if not banks_dir.exists():
        print("FAIL validate_exam_level_gate: corpus/exam_banks is MISSING — a gate whose data "
              "vanished must FAIL, not certify nothing")
        return 1
    if not (root / "course").exists():
        print("FAIL validate_exam_level_gate: course/ is MISSING — with no course there is no "
              "taught set and nothing can be called level-appropriate")
        return 1

    # ---- the taught set per level, from the course export only --------------------------------
    print("taught set at the end of each level (cumulative_known_set of the module's last lesson):")
    taught: dict[str, dict[str, set[str]]] = {}
    seen_modules: list[tuple[str, list[tuple[int, int, str, dict[str, Any]]]]] = []
    for module in MODULE_ORDER:
        les = module_lessons(root, module)
        if not les:
            fails.append(f"T course/{module}: no lessons — the taught set for {module} cannot be built")
            continue
        seen_modules.append((module, les))
        if module in LEVELS:
            last = les[-1]
            sets = cks_sets(last[3])
            if not sets["vocab"]:
                fails.append(f"T {module}: the last lesson {last[2]} has an EMPTY taught vocab set")
            taught[module] = sets
            print(f"  {module:6s} {last[2]:26s} vocab {len(sets['vocab']):5d}  "
                  f"kanji {len(sets['kanji']):4d}  grammar {len(sets['grammar']):4d}")

    # --- T: the last lesson really is the level. Everything taught in this module or an earlier
    # one must be inside it, or "the end of N5" is not what the last N5 lesson knows.
    for i, module in enumerate(MODULE_ORDER):
        if module not in taught:
            continue
        end = taught[module]
        for earlier, lessons in seen_modules:
            if MODULE_ORDER.index(earlier) > i:
                continue
            for _, _, lid, cks in lessons:
                got = cks_sets(cks)
                for dim in ("kanji", "vocab", "grammar"):
                    missing = got[dim] - end[dim]
                    if missing:
                        fails.append(
                            f"T {module}: lesson {lid} teaches {dim} {sorted(missing)[:3]} that the "
                            f"last {module} lesson's cumulative_known_set does not contain — the "
                            f"course is no longer cumulative, so 'taught by the end of {module}' is "
                            f"undefined")

    # ---- corpus ground truth ------------------------------------------------------------------
    vocab_headword: dict[str, str] = {}
    for f in sorted(glob.glob(str(root / "corpus" / "vocab" / "*.json"))):
        for v in load_list(Path(f)):
            vocab_headword[v["slug"]] = v.get("headword", "")
    kanji_registry: set[str] = set()
    for f in sorted(glob.glob(str(root / "corpus" / "kanji" / "*.json"))):
        for k in load_list(Path(f)):
            kanji_registry.add(k["character"])
    if not kanji_registry:
        fails.append("T corpus/kanji is empty — 'no kanji record at all' could not be distinguished "
                     "from 'not taught'")

    sentences: dict[str, dict[str, Any]] = {}
    bank_json = root / "corpus" / "sentences" / "bank.json"
    if bank_json.exists():
        for s in load_list(bank_json):
            sentences[s["slug"]] = s
    if not sentences:
        fails.append("T corpus/sentences/bank.json is empty — no dissection, so the vocab and "
                     "grammar dimensions would silently pass")

    read_jp: dict[str, str] = {}
    for f in sorted(glob.glob(str(root / "corpus" / "readings" / "*.json"))):
        for r in load_list(Path(f)):
            read_jp[r["slug"]] = r.get("jp", "")

    # ---- per-item verdict ---------------------------------------------------------------------
    stats: dict[tuple[str, str], dict[str, Any]] = {}
    reasons: dict[tuple[str, str], list[tuple[str, list[str]]]] = collections.defaultdict(list)
    bank_files = 0

    for path in sorted(banks_dir.glob("*.json")):
        m = BANK_RE.match(path.name)
        if not m:
            continue  # sidecars (INDEX.md, removed_items.json) are not banks
        level, btype = m.group(1), m.group(2)
        if btype not in TYPE_PREFIX:
            continue  # unknown bank type is validate_exam_banks check A's failure, not this one's
        bank_files += 1
        items = load_list(path)
        if not items:
            fails.append(f"E {path.name}: EMPTY bank — a level gate over zero items certifies nothing")
            continue
        if level not in taught:
            fails.append(f"E {path.name}: no course module for level {level} — its taught set is unknown")
            continue
        T = taught[level]
        up = level.upper()
        st = stats.setdefault((level, btype), {"total": 0, "ok": 0, "bad": 0,
                                              "ok_passages": set(), "dims": collections.Counter()})

        for it in items:
            st["total"] += 1
            iid = it.get("id") or "<no id>"
            why: list[str] = []

            # --- kanji: every ideograph the learner sees --------------------------------------
            chars: set[str] = set()
            for s in visible_jp(it, btype, read_jp):
                chars.update(KANJI_RE.findall(s))
            for c in sorted(chars):
                if f"kanji:{c}" not in T["kanji"]:
                    tail = "" if c in kanji_registry else " (no kanji record at all)"
                    why.append(f"kanji {c} not taught by end of {up}{tail}")

            # --- vocab: the item's own word, plus the dissection of its source sentence -------
            src = None
            sslug = it.get("sentence")
            if sslug:
                src = sentences.get(sslug)
                if src is None:
                    # Resolution is validate_exam_banks check D's gate. It matters HERE because an
                    # unresolvable sentence would make the vocab and grammar dimensions vacuous.
                    why.append(f"sentence {sslug} does not resolve — its vocab and grammar cannot "
                               f"be proven taught")
            vslugs: set[str] = set()
            if it.get("vocab"):
                vslugs.add(str(it["vocab"]))
            if src:
                for tok in (src.get("tokens") or []):
                    if tok.get("vocab"):
                        vslugs.add(str(tok["vocab"]))
            for v in sorted(vslugs):
                if v not in T["vocab"]:
                    hw = vocab_headword.get(v)
                    why.append(f"vocab {v}{f' ({hw})' if hw else ''} not taught by end of {up}")

            # --- grammar: the item's own point, plus the source sentence's tags ---------------
            gslugs: set[str] = set()
            if it.get("grammar"):
                gslugs.add(gram_slug(str(it["grammar"])))
            if src:
                for g in (src.get("grammar") or []):
                    gslugs.add(gram_slug(str(g)))
            for g in sorted(gslugs):
                if g not in T["grammar"]:
                    why.append(f"grammar {g} not taught by end of {up}")

            # --- the passage a passage-backed item is drawn from must exist -------------------
            if btype in PASSAGE_TYPES:
                rslug = it.get("reading")
                if not rslug or rslug not in read_jp:
                    why.append(f"passage {rslug!r} does not resolve — the Japanese behind this item "
                               f"cannot be proven taught")

            if why:
                st["bad"] += 1
                for dim in ("kanji", "vocab", "grammar"):
                    if any(w.startswith(dim + " ") for w in why):
                        st["dims"][dim] += 1
                reasons[(level, btype)].append((iid, why))
            else:
                st["ok"] += 1
                if btype in PASSAGE_TYPES:
                    st["ok_passages"].add(it.get("reading"))

    if bank_files == 0:
        print("FAIL validate_exam_level_gate: no n*_*.json bank files under corpus/exam_banks")
        return 1

    # ---- the table: this is the input to the A2 builder's level gate --------------------------
    baseline: dict[str, Any] = {}
    if BASELINE.exists():
        baseline = json.loads(BASELINE.read_text(encoding="utf-8"))
    ceilings: dict[str, Any] = baseline.get("ceilings") or {}

    print("\nlevel-appropriateness per (level, family) — appropriate = every kanji, vocab and "
          "grammar\npoint of the item's learner-visible Japanese is in that level's taught set:")
    print(f"  {'family':16s} {'lvl':4s} {'total':>6s} {'appro':>6s} {'inappr':>7s} {'ceil':>6s} "
          f"{'paper':>6s} {'pool':>6s} {'ratio':>7s}  flag")
    order = list(PAPER_COUNTS) + list(LISTENING_PAPER_COUNTS)
    for btype in order:
        for idx, level in enumerate(LEVELS):
            st = stats.get((level, btype))
            if st is None:
                continue
            key = f"{level}_{btype}"
            req = ALL_PAPER_COUNTS.get(btype, (0, 0, 0))[idx]
            # exam.server.ts admits one item per passage per paper, so a passage-backed section's
            # real capacity is the number of DISTINCT passages behind its appropriate items.
            pool = len(st["ok_passages"]) if btype in PASSAGE_TYPES else st["ok"]
            ceil_val = ceilings.get(key)
            ratio = (pool / req) if req else float("inf")
            flag = ""
            if req:
                if pool < req:
                    flag = "SHORT"
                elif ratio < MIN_RATIO:
                    flag = "THIN"
            if btype not in GATED_FOR_SUFFICIENCY:
                flag = (flag + " (audio pending)").strip()
            ceil_s = "-" if ceil_val is None else str(ceil_val)
            ratio_s = "  inf" if req == 0 else f"{ratio:6.1f}x"
            print(f"  {btype:16s} {level:4s} {st['total']:6d} {st['ok']:6d} {st['bad']:7d} "
                  f"{ceil_s:>6s} {req:6d} {pool:6d} {ratio_s:>7s}  {flag}")

            # --- S: sufficiency is a printed number while the family still carries debt. The
            # moment its ceiling is 0 the bank claims to be fully level-clean, and a section that
            # cannot fill a level-appropriate paper from it becomes a hard failure.
            if ceil_val == 0 and req and btype in GATED_FOR_SUFFICIENCY:
                if pool < req:
                    fails.append(f"S {key}: {pool} level-appropriate usable, the paper draws {req} "
                                 f"— section short at ceiling 0")
                elif ratio < MIN_RATIO:
                    fails.append(f"S {key}: {pool} level-appropriate usable vs {req} per paper "
                                 f"({ratio:.1f}x, floor {MIN_RATIO}x) at ceiling 0")

    # ---- R: the ratchet ------------------------------------------------------------------------
    print(f"\nratchet (inappropriate items per (level, family); baseline {BASELINE.name} — "
          f"may shrink, never grow):")
    for (level, btype), st in sorted(stats.items()):
        key = f"{level}_{btype}"
        ceil_val = ceilings.get(key)
        if ceil_val is None:
            fails.append(f"R {key}: no ceiling in {BASELINE.name} — add one with today's count "
                         f"({st['bad']}) and a reason, or fix the items")
            print(f"  {key:24s} {st['bad']:5d}  (UNBASELINED)")
            continue
        if st["bad"] > ceil_val:
            fails.append(f"R {key} grew: {ceil_val} -> {st['bad']} inappropriate items "
                         f"(+{st['bad'] - ceil_val})")
            print(f"  {key:24s} {st['bad']:5d}  ceiling {ceil_val}  GREW")
            for iid, why in reasons[(level, btype)][:MAX_ITEMS_PER_FAMILY]:
                print(f"      {iid}: " + "; ".join(why[:4])
                      + (f" (+{len(why) - 4} more)" if len(why) > 4 else ""))
            if st["bad"] > MAX_ITEMS_PER_FAMILY:
                print(f"      ... {st['bad'] - MAX_ITEMS_PER_FAMILY} more inappropriate items in "
                      f"{key} — --list names every one of them and what is untaught in it")
        elif st["bad"] < ceil_val:
            print(f"  {key:24s} {st['bad']:5d}  ceiling {ceil_val}  SHRANK — lower the ceiling "
                  f"to {st['bad']} in {BASELINE.name}")
        else:
            print(f"  {key:24s} {st['bad']:5d}  ceiling {ceil_val}")
    for key in ceilings:
        if key.startswith("_"):
            continue
        lv, _, bt = key.partition("_")
        if (lv, bt) not in stats:
            fails.append(f"R ceiling {key} matches no bank in corpus/exam_banks — stale entry")

    total = sum(st["total"] for st in stats.values())
    ok = sum(st["ok"] for st in stats.values())
    dims: collections.Counter[str] = collections.Counter()
    for st in stats.values():
        dims.update(st["dims"])
    print(f"\n{total} items, {ok} level-appropriate, {total - ok} not "
          f"(failing dimension: kanji {dims['kanji']}, vocab {dims['vocab']}, "
          f"grammar {dims['grammar']}; an item can fail on more than one)")

    if args.list:
        print("\nevery inappropriate item and what is untaught in it:")
        for (level, btype) in sorted(reasons):
            for iid, why in reasons[(level, btype)]:
                print(f"  {level}_{btype} {iid}: " + "; ".join(why))

    shown = fails if args.list else fails[:MAX_SHOWN]
    for line in shown:
        print("  FAIL", line)
    if len(fails) > len(shown):
        print(f"  ... {len(fails) - len(shown)} more (--list for all)")
    print(f"\nvalidate_exam_level_gate: {total} items in {len(stats)} banks, "
          + ("ALL OK" if not fails else f"FAIL {len(fails)}"))
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
