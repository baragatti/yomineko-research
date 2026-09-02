#!/usr/bin/env python3
"""Attach exam-bank checkpoints to speaking-path units. Spec: design/speaking_path.md + design/learning_science.md.

The 6,166-item exam bank and the speaking path were built independently and had no connection: the bank
is JLPT-format, the path is scenario-ordered. But the bank items carry the same corpus IDs the path
does (`vocab_id`, `sentence` slug, `grammar` key), so they join cleanly, and reusing them means the
speaking path gets retrieval practice for free instead of needing a second authored exercise bank.

Three ways an item reaches a unit, in priority order:
  0. SAME SENTENCE  - the item is built from a phrase this unit just practised. Strongest link: it tests
                      exactly what the learner said out loud a minute ago.
  1. NEW WORD       - the item's vocab_id is one this unit introduces.
  2. KNOWN WORD     - the item's vocab_id is anywhere in the cumulative known set. This is the spaced
                      review channel: older words resurface in later units.

Types are filtered by what the PATH is for, not by what the bank offers:
  * orthography is excluded outright - it asks the learner to produce kanji, and this path is explicitly
    recognition-only for kanji (design/speaking_path.md section 1).
  * reading_comp and text_grammar are excluded - multi-paragraph reading is a different skill from speech.
  * listening_* are excluded until the audio exists (design/listening.md).
  * what remains is ordered production-first: sentence_order (assemble a sentence) before context_fill
    (cued recall in context) before recognition formats.

DISTRACTORS ARE REBUILT FROM THE LEARNER'S KNOWN SET, not taken from the bank. The bank draws its wrong
answers from the whole level, so requiring them all to be known yielded 134 checkpoint items against a
396 target and left 11 units with none. Rebuilding fixes that, and it is the better question anyway: a
distractor the learner has never seen is eliminated on sight as unfamiliar rather than on meaning, which
makes the item easier than it looks and tests recognition of novelty instead of the word. Every option a
checkpoint shows is therefore a word the learner has already met. The stem and the correct answer still
come from the audited bank item; only the wrong answers are re-drawn.

Ties among equally-close distractor candidates are broken by a hash of (item, candidate), never
alphabetically - the same mistake in build_exam_banks.py collapsed 400 items onto 31 distinct
distractors (see that file's `spread`).

Usage: build_speaking_checkpoints.py [--dry-run]
"""
from __future__ import annotations
import argparse, hashlib, json, re, sqlite3, sys
from collections import Counter
from pathlib import Path
sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
ROOT = Path(__file__).resolve().parents[2]
DB = ROOT / "db" / "corpus.sqlite"
SPEAK = ROOT / "course" / "speak"
BANKS = ROOT / "corpus" / "exam_banks"

# Production before recognition. The count and mix are the tunable part; the join above is not.
TYPE_ORDER = ["sentence_order", "context_fill", "usage", "paraphrase", "kanji_reading"]
EXCLUDED = {"orthography", "reading_comp", "text_grammar",
            "listening_task", "listening_point", "listening_gist", "listening_say", "listening_reply"}
PER_UNIT = 6
MAX_PER_TYPE = 2          # no unit may be all one format
# i+1 on the item's STEM. Every option a checkpoint shows is already forced inside the known set, but
# nothing constrained the sentence the question is asked ABOUT, so an item could pose a known choice
# over a stem carrying words the learner has never met. validate_speaking_path has enforced this budget
# since it was written; the builder merely happened to satisfy it, and the first reshuffle of the path
# broke that luck. Enforced here so the constraint is a rule instead of a coincidence.
MAX_UNKNOWN_IN_STEM = 3   # = validate_speaking_path.MAX_UNKNOWN_IN_STEM
# Which field of a known word can stand in as a wrong answer for each format.
DISTRACTOR_FIELD = {"kanji_reading": "kana", "context_fill": "hw", "paraphrase": "hw"}
KANJI = re.compile(r"[一-鿿㐀-䶿]")


def spread(anchor: str, value: str) -> str:
    return hashlib.sha1(f"{anchor}{value}".encode("utf-8")).hexdigest()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    con = sqlite3.connect(DB)
    vid_of = {slug: i for slug, i in con.execute("SELECT slug,id FROM vocab")}
    # every headword/kana we know, to test whether an item's visible strings are inside the known set
    forms = {i: (hw, kana) for i, hw, kana in con.execute("SELECT id,headword,kana FROM vocab")}

    # A stem sentence's vocabulary, under exactly build_speaking_path.link_ok — the same acceptance rule
    # the path used to build the known set, so "unknown" means the same thing in both files.
    kana_count: Counter = Counter(k for _, k in con.execute("SELECT id,kana FROM vocab"))
    slug_of = {i: s for i, s in con.execute("SELECT id,slug FROM sentence")}
    stem_vocab: dict[str, set[int]] = {}
    for sid, vid, surface, lemma in con.execute(
            "SELECT DISTINCT sentence_id,vocab_id,surface,lemma FROM token "
            "WHERE split_mode='C' AND vocab_id IS NOT NULL"):
        hw, kana = forms.get(vid, ("", ""))
        surface, lemma = surface or "", lemma or ""
        if not (hw in (lemma, surface)
                or any(ch in surface for ch in hw if KANJI.match(ch))
                or (kana == lemma and kana_count[kana] == 1)):
            continue
        s = slug_of.get(sid)
        if s:
            stem_vocab.setdefault(s, set()).add(vid)

    items: list[dict] = []
    # Banks are named <level>_<section>.json; sidecars (removed_items.json, INDEX.md) are not banks.
    for f in sorted(BANKS.glob("n[0-9]_*.json")):
        parts = f.stem.split("_", 1)
        if len(parts) != 2:
            continue
        level, typ = parts
        if typ in EXCLUDED:
            continue
        for it in json.loads(f.read_text(encoding="utf-8")):
            it["_type"], it["_level"] = typ, level
            items.append(it)

    by_sentence: dict[str, list[dict]] = {}
    by_vocab: dict[int, list[dict]] = {}
    for it in items:
        if it.get("sentence"):
            by_sentence.setdefault(it["sentence"], []).append(it)
        if it.get("vocab_id"):
            by_vocab.setdefault(it["vocab_id"], []).append(it)

    course = json.loads((SPEAK / "course.json").read_text(encoding="utf-8"))
    known: set[int] = set()
    known_str: set[str] = set()
    stats, used_ids = Counter(), set()
    empty: list[str] = []

    for stage in course["stages"]:
        d = SPEAK / stage["slug"].split(":", 1)[1]
        for uid in stage["unit_ids"]:
            n = int(uid.rsplit("-", 1)[1])
            p = d / f"unit-{n:02d}.json"
            u = json.loads(p.read_text(encoding="utf-8"))
            new = {vid_of[w] for w in u["words"] if w in vid_of}
            known |= new
            for v in new:
                hw, kana = forms.get(v, ("", ""))
                known_str.update(x for x in (hw, kana) if x)

            def visible_ok(it: dict) -> bool:
                """Every option shown must already be known, else the checkpoint teaches by distractor."""
                opts = [it.get("correct") or "", *(it.get("distractors") or it.get("wrong") or [])]
                return all((not o) or o in known_str for o in opts)

            def redraw(it: dict) -> list[str] | None:
                """Three wrong answers drawn from the KNOWN set, closest in length to the right one."""
                field = DISTRACTOR_FIELD.get(it["_type"])
                correct = it.get("correct") or ""
                if not field or not correct:
                    return None
                pool = []
                for v in known:
                    hw, kana = forms.get(v, ("", ""))
                    cand = kana if field == "kana" else hw
                    if cand and cand != correct:
                        pool.append((abs(len(cand) - len(correct)), spread(it["id"], cand), cand))
                pool.sort()
                out: list[str] = []
                for _, _, cand in pool:
                    if cand not in out:
                        out.append(cand)
                    if len(out) == 3:
                        return out
                return None

            pool: list[tuple[int, dict]] = []
            for slug in u["say_now"]:
                for it in by_sentence.get(slug, []):
                    pool.append((0, it))
            for v in new:
                for it in by_vocab.get(v, []):
                    pool.append((1, it))
            for v in known - new:
                for it in by_vocab.get(v, []):
                    pool.append((2, it))

            picked, seen, per_type = [], set(), Counter()
            pool.sort(key=lambda t: (t[0], TYPE_ORDER.index(t[1]["_type"])
                                     if t[1]["_type"] in TYPE_ORDER else 99, t[1]["id"]))
            for prio, it in pool:
                if len(picked) >= PER_UNIT:
                    break
                if it["id"] in seen or it["id"] in used_ids:
                    continue
                if per_type[it["_type"]] >= MAX_PER_TYPE:
                    continue
                stem = it.get("sentence")
                if stem and len(stem_vocab.get(stem, set()) - known) > MAX_UNKNOWN_IN_STEM:
                    continue                               # i+1 on the sentence the item asks about
                entry = {"id": it["id"], "type": it["_type"], "via":
                         ("phrase" if prio == 0 else "new-word" if prio == 1 else "review")}
                if it["_type"] == "sentence_order":
                    pass                                   # assembles from its own pieces, no options
                elif it["_type"] in DISTRACTOR_FIELD:
                    if (it.get("correct") or "") not in known_str:
                        continue                           # the ANSWER must be a word they know
                    opts = redraw(it)
                    if not opts:
                        continue
                    entry["distractors"] = opts            # overrides the bank's, all inside the known set
                elif not visible_ok(it):
                    continue                               # usage: options are whole sentences, cannot redraw
                seen.add(it["id"])
                per_type[it["_type"]] += 1
                picked.append(entry)
            used_ids.update(x["id"] for x in picked)

            u["checkpoint"] = picked
            stats.update(x["type"] for x in picked)
            stats.update([f"via:{x['via']}" for x in picked])
            if not picked:
                empty.append(uid)
            if not args.dry_run:
                p.write_text(json.dumps(u, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    total = sum(v for k, v in stats.items() if not k.startswith("via:"))
    course["totals"]["checkpoint_items"] = total
    if not args.dry_run:
        (SPEAK / "course.json").write_text(json.dumps(course, ensure_ascii=False, indent=2) + "\n",
                                           encoding="utf-8")
    print(f"checkpoints ({'dry-run' if args.dry_run else 'WRITTEN'}): {total} items over "
          f"{len(course['stages'])} stages")
    print("  by type:  " + "  ".join(f"{k}={v}" for k, v in sorted(stats.items())
                                     if not k.startswith("via:")))
    print("  by link:  " + "  ".join(f"{k}={v}" for k, v in sorted(stats.items())
                                     if k.startswith("via:")))
    if empty:
        print(f"  units with no checkpoint: {len(empty)} ({', '.join(empty[:6])})")
    con.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
