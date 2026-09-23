#!/usr/bin/env python3
"""Shared selection rules for the exam-bank builders (W17).

`build_exam_banks.py` (the six deterministic families) and `build_reading_comp_bank.py` (読解) must
answer the same three questions the same way, or the level gate and the bank gate disagree with each
other about the same item. Those questions are:

  1. **Is this item inside its level?** — `TaughtSets` below is the ONE implementation of the rule
     `validate_exam_level_gate.py` measures: every kanji of the learner-visible Japanese, the item's
     own vocab, the source sentence's token vocab, and the item's + the sentence's grammar are all
     in the `cumulative_known_set` of the LAST lesson of that level's course module. The gate reads
     the exported course; so does this, for the same reason — the exported JSON is the source of
     truth (CLAUDE.md) and reading the DB's `lesson.cumulative_known_set` would not even work: the
     DB stores `vocab:<headword>` refs that only the exporter resolves to `vocab:<jmdict_id>`.

  2. **Does this token really name that word?** — `reading_link_ok`. The n3 linker matched on
     WRITTEN FORM and ignored reading (qa_sweep/exam_japanese_3.md F4), so 135 items point at the
     wrong lexeme: 空/から on six *sky* sentences, 時/とき on the じ counter 26 times, 金/きん where
     the sentence says かね. The rule here is W12's: a token links to a vocab record only when the
     lemma (surface, or a contiguous run of surfaces) AND the reading agree.

  3. **Is this string printable as an option?** — `option_ok`. 103 N4 items print a grammar-point
     label (自動詞, 命令形), a leaked sense index (`ずっと ①`) or a slot-stripped non-word
     (`よりほうが`, `とかとか`, `おになる`) as one of the four choices, which silently makes the item
     3-option (qa_sweep/exam_japanese_2.md S3/F07).

  4. **Would a distractor also be right?** — `interchangeable`, over design/exam_equivalents.json.

Imported by both builders; no side effects, no I/O beyond the course tree it is handed.
"""
from __future__ import annotations

import json
import re
import unicodedata
from pathlib import Path

# CJK ideographs — Unified, Extension A and the compatibility block, EXACTLY the class
# validate_exam_level_gate.KANJI_RE gates on. The builder used to test `"一" <= ch <= "鿿"`, which
# misses Extension A and the compatibility block entirely, so a 㐂 or a 﫿 in an option was invisible
# to the builder and visible to the gate.
KANJI_RE = re.compile(r"[㐀-䶿一-鿿豈-﫿]")

LEVELS = ("n5", "n4", "n3")
MODULE_ORDER = ("pre-n5", "n5", "n4", "n3")
ORD = {"pre-n5": -1, "n5": 0, "n4": 1, "n3": 2, "n2": 3, "n1": 4}


def has_kanji(s: str) -> bool:
    return bool(KANJI_RE.search(s))


def kanji_of(s: str) -> set[str]:
    return set(KANJI_RE.findall(s))


def kana_fold(s: str) -> str:
    """NFKC + katakana -> hiragana. Two readings that fold together are the same reading, which is
    what lets a token reading (カタカナ from the analyzer) be compared with a vocab `kana` field."""
    s = unicodedata.normalize("NFKC", s or "")
    return "".join(chr(ord(c) - 0x60) if 0x30A1 <= ord(c) <= 0x30F6 else c for c in s)


def gram_slug(ref: str) -> str:
    """Exam items address grammar by bare key, the rest of the corpus by slug — normalize to slug
    space, which is what a cumulative_known_set holds (readiness G13)."""
    return ref if ref.startswith("gram:") else "gram:" + ref


# --------------------------------------------------------------------------------------------
# 1. the taught set
# --------------------------------------------------------------------------------------------
class TaughtSets:
    """`cumulative_known_set` of the last lesson of each level's module, from the EXPORTED course.

    Last topic by `order`, last lesson by `order` — the same walk `validate_exam_level_gate.py`
    does. The course's cks is monotonic and cross-module cumulative, so that one lesson IS the
    level; the gate's check T asserts that rather than assuming it, and this class trusts the gate
    to keep doing so instead of re-deriving it.
    """

    def __init__(self, root: Path) -> None:
        self.by_level: dict[str, dict[str, set[str]]] = {}
        self.kanji_chars: dict[str, set[str]] = {}
        # Words a lesson TEACHES (a `vocab` unlock, exported refs), cumulative up to each level. Equal
        # to the cks vocab today (712 / 1,355 / 2,951); kept separate so a wider cks cannot let an
        # untaught word become the word under test.
        self.words: dict[str, set[str]] = {}
        unlocked: set[str] = set()
        for module in MODULE_ORDER:
            les = self._module_lessons(root, module)
            unlocked |= {u["ref"] for r in les for u in r[4] if u.get("type") == "vocab"}
            if module in LEVELS:
                self.words[module] = set(unlocked)
                if not les:
                    raise SystemExit(
                        f"exam_rules: course/{module} has no lessons, so the taught set for {module} "
                        f"cannot be built — a bank selected against an unknown level is not "
                        f"level-gated, and building it would silently defeat W03.")
                cks = les[-1][3]
                sets = {k: set(cks.get(k) or []) for k in ("kanji", "vocab", "grammar")}
                if not sets["vocab"]:
                    raise SystemExit(
                        f"exam_rules: the last {module} lesson {les[-1][2]} has an EMPTY taught "
                        f"vocab set")
                self.by_level[module] = sets
                self.kanji_chars[module] = {x.split(":", 1)[1] for x in sets["kanji"]}

    @staticmethod
    def _module_lessons(root: Path, module: str):
        cjson = root / "course" / module / "course.json"
        if not cjson.exists():
            return []
        course = json.loads(cjson.read_text(encoding="utf-8"))
        out = []
        for topic in course.get("topics", []):
            tdir = (root / "course" / module / topic["path"]).parent
            for lf in sorted(tdir.glob("lesson-*.json")):
                les = json.loads(lf.read_text(encoding="utf-8"))
                out.append((int(topic.get("order", 0)), int(les.get("order", 0)),
                            les.get("id", lf.name), les.get("cumulative_known_set") or {},
                            les.get("unlocks") or []))
        out.sort(key=lambda r: (r[0], r[1]))
        return out

    # -- the three dimensions, each named the way the gate names it ----------------------------
    def kanji_ok(self, text: str, lvl: str) -> bool:
        return kanji_of(text) <= self.kanji_chars[lvl]

    def strings_kanji_ok(self, strings, lvl: str) -> bool:
        return all(self.kanji_ok(s, lvl) for s in strings if s)

    def vocab_ok(self, slug: str, lvl: str) -> bool:
        return slug in self.by_level[lvl]["vocab"]

    def grammar_ok(self, ref: str, lvl: str) -> bool:
        return gram_slug(ref) in self.by_level[lvl]["grammar"]

    def word_taught(self, slug: str, lvl: str) -> bool:
        return slug in self.words[lvl]


# --------------------------------------------------------------------------------------------
# 2. the reading-aware link
# --------------------------------------------------------------------------------------------
def reading_link_ok(tokens: list[tuple[str, str | None, str | None]], headword: str,
                    kana: str) -> bool:
    """True when the sentence really uses THIS lexeme, judged by lemma AND reading (W12's rule).

    `tokens` is `[(surface, lemma, reading), ...]` for one sentence in analyzer order. A link is
    accepted when a single token, or a contiguous RUN of tokens, spells the headword and reads the
    record's kana. A token whose reading the analyzer left null cannot prove anything and is not
    accepted — "no evidence" is not "agreement", and treating it as agreement is exactly how 時/とき
    got attached to twenty-six clock readings.
    """
    want = kana_fold(kana)
    n = len(tokens)
    for i in range(n):
        surf, read = "", ""
        for j in range(i, n):
            s, _lemma, r = tokens[j]
            if not r:
                break
            surf += s
            read += r
            if len(surf) > len(headword):
                break
            if surf == headword:
                if kana_fold(read) == want:
                    return True
                break
    return False


# --------------------------------------------------------------------------------------------
# 3. what may be printed as an option
# --------------------------------------------------------------------------------------------
# Grammar METALANGUAGE. `grammar_point.forms_json` carries these as if they were forms, and the
# builder printed them as choices: gf:n4:3360 offers 命令形 ("imperative form") as a fill-in for
# 「その（　）どうすればいいでしょう？」. No learner picks a metalinguistic label, so the item is a
# 3-option item wearing four options.
METALANGUAGE = {
    "自動詞", "他動詞", "命令形", "意向形", "受身形", "使役形", "可能形", "過去形", "否定形",
    "連体形", "連用形", "終止形", "仮定形", "辞書形", "普通形", "丁寧形", "受動態", "使役受身",
    "名詞化", "助数詞", "接続詞", "副詞", "形容詞", "形容動詞", "動詞", "名詞", "助詞", "助動詞",
}
CIRCLED = re.compile(r"[①-⑳㉑-㉟]")   # ① … ⑳ — internal sense indices
SLOT = "～〜…‥"                                          # citation slot markers, BOTH tildes


def option_ok(form: str) -> bool:
    """Mechanical shape guards on a string about to be printed as a choice.

    Every rejection here is a measured leak, not a precaution:
      * a space of any width          — `くらい ①`, `でも でも` (S3(b), S3(c))
      * a circled numeral             — `ずっと ①`, `以上 ①` (S3(b))
      * a slot marker anywhere        — the U+FF5E filter missed U+301C, and `なん〜か` shipped as a
                                        distractor on 9 items (regen review §4)
      * grammar metalanguage          — 自動詞 / 命令形 / 受身形 (S3(a))
      * an exact doubling X+X         — `かか` (from gram:ka-ka's forms[0]), `しし`, `とと`,
                                        `たりたり`, `とかとか`, `でもでも`: the signature of a
                                        pattern whose 〜 slots were stripped instead of filled
    """
    if not form or len(form) < 2 or len(form) > 8:
        return False
    if any(c.isspace() or c in "　" for c in form):
        return False
    if CIRCLED.search(form):
        return False
    if any(c in SLOT for c in form):
        return False
    if "-" in form or "－" in form:
        return False
    if form in METALANGUAGE:
        return False
    if len(form) % 2 == 0 and form[: len(form) // 2] == form[len(form) // 2:]:
        return False
    return True


# --------------------------------------------------------------------------------------------
# 4. two options that are the same answer
# --------------------------------------------------------------------------------------------
# gf:n4:3535 「これはお茶（　）味だ。」 keyed のような and offered みたいな; gf:n4:3845 keyed
# なければいけない and offered なければならない. The same-point rule (fix 14) cannot see these: the
# forms belong to different grammar points. The classes live in design/exam_equivalents.json.
EQUIVALENTS = Path(__file__).resolve().parents[2] / "design" / "exam_equivalents.json"


def load_equivalents(path: Path = EQUIVALENTS) -> list[tuple[set[str], re.Pattern | None, re.Pattern | None]]:
    out = []
    for c in json.loads(path.read_text(encoding="utf-8"))["classes"]:
        before = re.compile("(?:" + c["before"] + r")\Z") if c.get("before") else None
        after = re.compile(c["after"]) if c.get("after") else None
        out.append((set(c["forms"]), before, after))
    return out


def interchangeable(a: str, b: str, before: str, after: str, classes) -> bool:
    """True when `b` printed in the blank would be as right as `a`: both in one class and the class
    context (the text around the blank) holds."""
    return any(a in forms and b in forms and a != b
               and (bre is None or bre.search(before)) and (are is None or are.match(after))
               for forms, bre, are in classes)


if __name__ == "__main__":
    eq = load_equivalents()
    assert interchangeable("のような", "みたいな", "これはお茶", "味だ。", eq)
    assert interchangeable("なければいけない", "なければならない", "待た", "。", eq)
    assert interchangeable("どれ", "どの", "", "くらい？", eq) and not interchangeable("どれ", "どの", "", "が安い？", eq)
    assert interchangeable("ごとに", "おきに", "この時計は１５分", "なる。", eq)
    assert not interchangeable("おきに", "ごとに", "一行", "書け。", eq)          # every other row != every row
    assert not interchangeable("けど", "でも", "ちょっと話があるんだ", "。", eq)   # でも is only 'but' sentence-initially
    assert not interchangeable("ずに", "ないで", "私は外出せ", "家にいた。", eq)   # せ + ないで is not a word
    assert not interchangeable("なきゃ", "ないと", "勉強し", "試験に落ちる。", eq)  # mid-sentence ないと is 'if not'
    print("exam_rules: equivalence self-check ok")
