#!/usr/bin/env python3
"""Validate corpus/exercises/conjugation — the form-discrimination drill bank (roadmap item C).

Every answer here is DERIVED from corpus/conjugations, so the thing that can rot is the derivation
drifting from its source: a rebuild of the conjugation bank that changes a surface, or an item whose
options stop being answerable.

WHY THE DISTRACTOR AND READING CHECKS WERE ADDED
------------------------------------------------
The original checks pinned the ANSWER to the bank and then said nothing at all about the other three
quarters of the item. `distractors` only had to be three strings distinct from each other and from the
answer — literally any three strings. A form-discrimination drill whose wrong answers are not forms of
the same word is not a discrimination drill: the learner picks the answer by recognising the stem, not
by knowing the form, and a rebuild that mis-keyed the distractor pool would ship silently. So a
distractor must now be a real surface of the SAME vocab record carried by at least one form label other
than the one being asked for (surfaces legitimately coincide — ichidan potential and passive are the
same string — so the test is on the label set, not on the string).

The same hole existed under the answer: `kana` and `romaji` ride along with every item and are what the
app shows when it reveals the reading, and nothing compared them to anything. They are now pinned to the
conjugation bank exactly as `correct` is, and then re-derived a second time from the kana itself with a
local Hepburn table (KANA_ROMAJI below), so a bank entry whose own romaji is wrong cannot launder itself
through the exercise. The comparison ignores the apostrophe in syllabic-n forms (kin'en vs kinen):
scripts/ingest/conjugate.py inserts it conditionally, so its presence is a spelling convention rather
than a fact about the reading, and 158 items legitimately go without it. Long-vowel ー romanises to a
literal hyphen, which is this corpus's convention (ko-chisuru), not a gap in the table.

`prompt` is likewise pinned: it must be the DICTIONARY form's surface, not the headword. For suru-nouns
those differ (headword 合図, prompt 合図する) and 9,050 items depend on the distinction; a prompt that
drifts to the headword asks the learner to conjugate a noun.

Checked:
  * every item's `correct` still matches the conjugation bank for that (vocab_id, form). This is the
    check that matters: it is what makes the bank Layer B rather than a frozen copy.
  * `kana` and `romaji` match the bank entry for that same (vocab_id, form), and romaji is what the
    kana romanises to.
  * `slug`, `headword`, `kind` and `class` agree with the conjugation record the item cites.
  * `prompt` is the dictionary-form surface of that record.
  * four DISTINCT option strings, and each distractor is a real form of the same vocab under a
    different form label.
  * `correct` is never equal to `prompt`, which would not be a question.
  * ids unique; level matches the file; `example`, where present, resolves to a real sentence AND that
    sentence actually contains the answer surface. An example that does not contain the form it is
    illustrating is worse than none.

Reads exported JSON only; never db/corpus.sqlite.
Usage: validate_conjugation_exercises.py [--root PATH] [--list]
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]

MAX_REPORT = 15

# Hepburn, matching the convention scripts/ingest/conjugate.py produces: ー is a literal hyphen and
# small-kana digraphs are single mora. Verified against all 18,524 items and all 19,784 bank forms.
DIGRAPH = {
    "きゃ": "kya", "きゅ": "kyu", "きょ": "kyo", "しゃ": "sha", "しゅ": "shu", "しょ": "sho",
    "ちゃ": "cha", "ちゅ": "chu", "ちょ": "cho", "にゃ": "nya", "にゅ": "nyu", "にょ": "nyo",
    "ひゃ": "hya", "ひゅ": "hyu", "ひょ": "hyo", "みゃ": "mya", "みゅ": "myu", "みょ": "myo",
    "りゃ": "rya", "りゅ": "ryu", "りょ": "ryo", "ぎゃ": "gya", "ぎゅ": "gyu", "ぎょ": "gyo",
    "じゃ": "ja", "じゅ": "ju", "じょ": "jo", "びゃ": "bya", "びゅ": "byu", "びょ": "byo",
    "ぴゃ": "pya", "ぴゅ": "pyu", "ぴょ": "pyo", "ぢゃ": "ja", "ぢゅ": "ju", "ぢょ": "jo",
    "てぃ": "ti", "でぃ": "di", "ふぁ": "fa", "ふぃ": "fi", "ふぇ": "fe", "ふぉ": "fo",
    "うぃ": "wi", "うぇ": "we", "しぇ": "she", "ちぇ": "che", "じぇ": "je",
    "とぅ": "tu", "どぅ": "du",
}
MONO = {
    "あ": "a", "い": "i", "う": "u", "え": "e", "お": "o",
    "か": "ka", "き": "ki", "く": "ku", "け": "ke", "こ": "ko",
    "が": "ga", "ぎ": "gi", "ぐ": "gu", "げ": "ge", "ご": "go",
    "さ": "sa", "し": "shi", "す": "su", "せ": "se", "そ": "so",
    "ざ": "za", "じ": "ji", "ず": "zu", "ぜ": "ze", "ぞ": "zo",
    "た": "ta", "ち": "chi", "つ": "tsu", "て": "te", "と": "to",
    "だ": "da", "ぢ": "ji", "づ": "zu", "で": "de", "ど": "do",
    "な": "na", "に": "ni", "ぬ": "nu", "ね": "ne", "の": "no",
    "は": "ha", "ひ": "hi", "ふ": "fu", "へ": "he", "ほ": "ho",
    "ば": "ba", "び": "bi", "ぶ": "bu", "べ": "be", "ぼ": "bo",
    "ぱ": "pa", "ぴ": "pi", "ぷ": "pu", "ぺ": "pe", "ぽ": "po",
    "ま": "ma", "み": "mi", "む": "mu", "め": "me", "も": "mo",
    "や": "ya", "ゆ": "yu", "よ": "yo",
    "ら": "ra", "り": "ri", "る": "ru", "れ": "re", "ろ": "ro",
    "わ": "wa", "ゐ": "i", "ゑ": "e", "を": "o", "ん": "n",
    "ぁ": "a", "ぃ": "i", "ぅ": "u", "ぇ": "e", "ぉ": "o",
    "ゃ": "ya", "ゅ": "yu", "ょ": "yo", "ゎ": "wa", "ー": "-",
}
VOWELISH = ("a", "i", "u", "e", "o", "y")


def kata2hira(s: str) -> str:
    return "".join(chr(ord(c) - 0x60) if "ァ" <= c <= "ヶ" else c for c in s)


def romanize(kana: str) -> str:
    """Kana -> Hepburn. っ doubles the next consonant; ん before a vowel or y takes an apostrophe."""
    s = kata2hira(kana)
    out: list[str] = []
    i = 0
    while i < len(s):
        ch = s[i]
        if ch == "っ":
            nxt = DIGRAPH.get(s[i + 1:i + 3]) or MONO.get(s[i + 1:i + 2], "") if i + 1 < len(s) else ""
            out.append(nxt[:1])
            i += 1
            continue
        two = s[i:i + 2]
        if two in DIGRAPH:
            out.append(DIGRAPH[two])
            i += 2
            continue
        if ch in MONO:
            r = MONO[ch]
            if ch == "ん" and i + 1 < len(s):
                nxt = DIGRAPH.get(s[i + 1:i + 3]) or MONO.get(s[i + 1], "")
                if nxt[:1] in VOWELISH:
                    r = "n'"
            out.append(r)
            i += 1
            continue
        out.append(ch)
        i += 1
    return "".join(out)


def same_reading(a: str, b: str) -> bool:
    """Compare romaji ignoring the optional syllabic-n apostrophe (see the module docstring)."""
    return a.replace("'", "") == b.replace("'", "")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[2],
                    help="repo root to validate (default: this checkout)")
    ap.add_argument("--list", action="store_true", help="print every failure, not the first 15")
    args = ap.parse_args()
    root = args.root.resolve()
    ex = root / "corpus" / "exercises" / "conjugation"
    if not ex.exists():
        print("validate_conjugation_exercises: bank not built - run build_conjugation_exercises.py")
        return 0

    # (vocab_id, form) -> conjugation entry, and vocab_id -> {surface: {form labels}} for distractors.
    key: dict[tuple[int, str], dict] = {}
    record: dict[int, dict] = {}
    labels: dict[int, dict[str, set[str]]] = {}
    for f in sorted((root / "corpus" / "conjugations").glob("*.json")):
        for e in json.loads(f.read_text(encoding="utf-8")):
            record[e["vocab_id"]] = e
            for x in e["conjugations"]:
                key[(e["vocab_id"], x["form"])] = x
                if x.get("surface"):
                    labels.setdefault(e["vocab_id"], {}).setdefault(x["surface"], set()).add(x["form"])

    jp_of: dict[str, str] = {}
    for f in sorted((root / "corpus" / "sentences").rglob("*.json")):
        try:
            data = json.loads(f.read_text(encoding="utf-8"))
        except Exception:
            continue
        for s in (data if isinstance(data, list) else [data]):
            if isinstance(s, dict) and s.get("slug") and s.get("jp"):
                jp_of[s["slug"]] = s["jp"]

    fails: list[str] = []
    seen: set[str] = set()
    total = 0
    romaji_checked = 0
    for f in sorted(ex.glob("*.json")):
        level = f.stem.split("_")[0]
        for it in json.loads(f.read_text(encoding="utf-8")):
            total += 1
            iid = it["id"]
            if iid in seen:
                fails.append(f"{iid}: duplicate id")
            seen.add(iid)
            if it["level"] != level:
                fails.append(f"{iid}: level {it['level']} in {level} file")
            entry = key.get((it["vocab_id"], it["form"]))
            if entry is None:
                fails.append(f"{iid}: no such (vocab_id, form) in the conjugation bank")
            elif entry.get("surface") != it["correct"]:
                fails.append(f"{iid}: answer drifted from the bank "
                             f"({it['correct']!r} vs {entry.get('surface')!r})")
            opts = [it["correct"], *it.get("distractors", [])]
            if len(opts) != 4 or len(set(opts)) != 4:
                fails.append(f"{iid}: options are not 4 distinct strings: {opts}")
            if it["correct"] == it["prompt"]:
                fails.append(f"{iid}: answer equals the prompt")
            ex_slug = it.get("example")
            if ex_slug:
                if ex_slug not in jp_of:
                    fails.append(f"{iid}: example {ex_slug} does not resolve")
                elif it["correct"] not in jp_of[ex_slug]:
                    fails.append(f"{iid}: example {ex_slug} does not contain the answer surface")

            # ---- the item is a real slice of its conjugation record ----------------------------
            rec = record.get(it["vocab_id"])
            if rec is None:
                fails.append(f"{iid}: vocab_id {it['vocab_id']} has no conjugation record")
                continue
            for field in ("slug", "headword", "kind", "class"):
                if it.get(field) != rec.get(field):
                    fails.append(f"{iid}: {field} {it.get(field)!r} disagrees with the conjugation "
                                 f"record ({rec.get(field)!r})")
            dic = key.get((it["vocab_id"], "dictionary"))
            if dic is None:
                fails.append(f"{iid}: its vocab has no dictionary form to prompt with")
            elif it["prompt"] != dic.get("surface"):
                fails.append(f"{iid}: prompt {it['prompt']!r} is not the dictionary form "
                             f"({dic.get('surface')!r})")

            # ---- the reading shown with the answer ---------------------------------------------
            if entry is not None:
                if it.get("kana") != entry.get("kana"):
                    fails.append(f"{iid}: kana {it.get('kana')!r} drifted from the bank "
                                 f"({entry.get('kana')!r})")
                if it.get("romaji") != entry.get("romaji"):
                    fails.append(f"{iid}: romaji {it.get('romaji')!r} drifted from the bank "
                                 f"({entry.get('romaji')!r})")
            if it.get("kana") and it.get("romaji"):
                romaji_checked += 1
                want = romanize(it["kana"])
                if not same_reading(want, it["romaji"]):
                    fails.append(f"{iid}: romaji {it['romaji']!r} is not what {it['kana']!r} "
                                 f"romanises to ({want!r})")

            # ---- the wrong answers are real forms of the same word ------------------------------
            surface_labels = labels.get(it["vocab_id"], {})
            for d in it.get("distractors", []):
                forms = surface_labels.get(d)
                if not forms:
                    fails.append(f"{iid}: distractor {d!r} is not any form of {it.get('headword')}")
                elif forms == {it["form"]}:
                    fails.append(f"{iid}: distractor {d!r} is only labelled {it['form']}, "
                                 f"the form being asked for")

    for line in (fails if args.list else fails[:MAX_REPORT]):
        print(f"  [FAIL] {line}")
    if not args.list and len(fails) > MAX_REPORT:
        print(f"  [FAIL] ... and {len(fails) - MAX_REPORT} more (re-run with --list)")
    print(f"validate_conjugation_exercises: {total} items, {romaji_checked} readings re-romanised, "
          + ("ALL OK" if not fails else f"{len(fails)} FAIL"))
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
