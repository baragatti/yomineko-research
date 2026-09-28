#!/usr/bin/env python3
"""JLPT exam-simulator BANKS (roadmap B; owner-approved 2026-07-05). Generates per-level, per-question-type
item banks derived ONLY from verified corpus facts — no AI generation, so Japanese correctness is inherited:
  kanji_reading   (漢字読み)  headword -> pick the correct kana reading         [vocab facts]
  orthography     (表記)      kana -> pick the correct written form            [vocab facts]
  context_fill    (文脈規定)  bank sentence with the target word blanked        [sentence + vocab]
  grammar_form    (文法形式)  bank sentence with the grammar form blanked       [sentence + grammar]
  sentence_order  (並べ替え)  reorder the sentence's BUNSETSU                    [sentence tokens]
  text_grammar    (文章の文法) a reading passage with one grammar form blanked   [reading + grammar]
Distractors are built by RULE (same level + same lexeme class + similar length; never equal to the correct
answer; orthography distractors must not share the stem's reading — i.e. wrong by construction). Among
equally-close candidates the order is a hash of (item, candidate), NOT alphabetical — see `spread()`.
Deterministic (hashed sorts, no RNG) so re-runs are reproducible; the APP does the per-attempt random pick (see
design/exam_simulator.md). Real JLPT papers are © JEES — format reference only; zero copied text.
Output: corpus/exam_banks/{level}_{type}.json + INDEX.md. Usage: build_exam_banks.py [--out DIR]

W17 — WHAT CHANGED AND WHY (research/reports/w17_builder_report.md)
==================================================================
The A2 decision packet (`research/reports/exam_bank_regen_review.md` §5.1) measured that regenerating
with the builder as it stood was a NO-GO: it stripped provenance from 5,182 items, dropped 3,392 vocab
slugs, re-introduced all 93 answer leaks a migration had removed, and printed a citation placeholder as
a distractor. The two QA waves then added the defects the plan had to absorb. Every change below is one
of those findings; each is marked with the finding it closes.

  1  LEAK GUARD (EB-05). `cf` skips a candidate whose headword occurs more than once in the sentence
     (`continue`, i.e. try the next vocab — never drop the sentence); `gf`/`tg` select a form that
     occurs EXACTLY once. Blanking only the first occurrence left the answer printed further along on
     93 items.
  2  PROVENANCE. `layer` / `ai_generated` / `needs_review` on every item, derived exactly as the
     now-disabled `migrate_exam_banks_p7.py` derived them, so a rebuild carries what the migration used
     to stamp in afterwards (and `contracts/exam_item.schema.json` REQUIRES all four).
  3  PUBLISHED SLUGS. `vocab: vocab:<jmdict_id>` beside every `vocab_id`; `contracts/README.md` forbids
     a row number as an address.
  4  `reading_verified` PREFERENCE on the `cf` candidate order. A preference, never a filter:
     `reading_verified=0` means "not confirmed", not "wrong", and filtering would discard 180 items for
     no defect.
  5  OKURIGANA (EB-02). `kanji_reading` distractors are ranked by whether they share the stem's kana
     head/tail, so the item stops being solvable by matching okurigana shape.
  6  ORTHOGRAPHY RANKING (EB-06). Rank on `len(headword)` — the string actually printed — not on
     `len(kana)`, plus the same shape bonus and a penalty for a length longshot.
  7  DETERMINISM. Explicit `ORDER BY` on the `sentence_vocab` scan. The stability of the old scan
     depended on the query being answered from the PK covering index; adding one non-PK column to the
     SELECT silently reverts it and moves 223 items.
  8  WAVE DASH. The citation-placeholder filter tested U+FF5E only, so U+301C survived and `なん〜か`
     shipped as a learner-visible distractor on 9 items. Now in `exam_rules.option_ok`, with the rest of
     the option-shape rules.
  9  INDEX. `removed_items.json` matched the bank glob and was listed as a 3-item bank; excluded now.
 10  READING-AWARE LINKS (qa F4, 135 items). A `cf` candidate must be proved by the sentence's own
     dissection — lemma AND reading, W12's rule, in `exam_rules.reading_link_ok`. 空/から stood on six
     *sky* sentences, 時/とき on the じ counter 26 times, 金/きん where the sentence says かね.
 11  BUNSETSU (qa F15/S4/F8, 45 ambiguous items). `sentence_order` tiles are bunsetsu, not morphemes,
     and the item carries `accepted[]` — every meaning-preserving reordering — instead of one string.
     Items whose tiles admit a MEANING-CHANGING reordering are refused. See `bunsetsu.py`.
 12  HOMOPHONE-SET DEDUPE (qa F1, 37 items). One `orthography` item per (level, kana) and one
     `kanji_reading` item per (level, headword). あつい appeared as three byte-identical items keyed
     暑い / 熱い / 厚い; whichever the learner picked, one of the three marked them wrong.
 13  THE LEVEL RULE (W03). Selection now happens against the level's taught set — every kanji in
     stem/options/passage, the item's own vocab, the source sentence's token vocab and its grammar
     tags. This is the rule `validate_exam_level_gate.py` measures, implemented once in
     `exam_rules.TaughtSets` so the builder and the gate cannot disagree.
 14  FOUR REAL OPTIONS (qa S3, 103 items). Options are filtered by `exam_rules.option_ok`: no grammar
     metalanguage (自動詞 / 命令形), no leaked sense index (`ずっと ①`), no slot-stripped non-word
     (`とかとか`, `おになる`). A grammar distractor must also be ATTESTED in the level's own corpus, and
     may not come from the same grammar point as the key (んです vs のです was offered as a wrong answer
     to itself). `kanji_reading` distractors must be the same script class as the key — a katakana
     loanword reading is eliminated on sight and the item is a 3-option item wearing four.
 15  EXPLANATIONS. Auto-graded items carry a pt-BR `explanation` assembled from the RECORD — the vocab
     gloss and reading, the grammar point's label, the sentence's own translation — by a fixed template
     per family. It is Layer B for that reason: no model wrote it, and there is nothing in it a
     reviewer has to fact-check that is not already checked where it lives.

 16  ONE KEY PER PRINTED STEM (W18). `cf` / `gf` skip a candidate whose blanked stem, normalized the
     way `validate_exam_stem_collisions.py` normalizes it, is already an item at this level: two
     sentences that differ only in the blanked word printed どのくらい（　） keyed 大きい and 高い.

 17  NO SECOND RIGHT ANSWER. A distractor that is as right as the key is refused. Grammar forms by the
     classes in design/exam_equivalents.json (`exam_rules.interchangeable`): gf:n4:3535 keyed のような
     offered みたいな, seven N4 items keyed なければいけない offered なければならない or the reverse.
     Vocab by the record itself: every JMdict reading of a spelling joins `hw_readings` (or:n3:1553
     printed おん keyed 音 and offered 御, which also reads おん), and a `cf` candidate that shares a
     sense-0 gloss with the key is skipped (「（　）に行ってください。」 keyed 前 offered 先).
     Report: research/derived/pending/exam_equivalent_distractors.json.

 18  THE STEM MUST RULE THE DISTRACTOR OUT. A wrong answer that makes the stem a fine sentence is a
     second key even when it means something else: 「もう帰っ（　）。」 keyed たらどうですか offered
     たらいいですか. `gf` / `tg` refuse a distractor that (a) turns the stem into a bank sentence or
     (b) the corpus shows in the same slot — attached, token-aligned, to a word of the same POS and
     conjugation form (`slot_shape`). What is left does not attach there. `gf` also blanks at
     SudachiPy token boundaries only (W16's rule): 「あなたの（　）す。」 keyed おかげで.
 19  ENOUGH STEM TO JUDGE BY. A `gf` stem needs MIN_STEM_CONTENT content tokens outside the blank:
     「（　）？」 keyed なぜ is answered as well by なあ or まで. Measured, not guessed — 0 leaves
     those, 1 leaves inversions (「キツイ（　）。」 with これ), 3 halves n5_grammar_form.
     Report: research/reports/exam_builder_fixes_2.md.
 20  A TAUGHT WORD UNDER TEST. `kanji_reading` / `orthography` key on a word some lesson up to the
     level unlocks (`exam_rules.TaughtSets.word_taught`). Today the cks vocab IS that union, so this
     moves no item; it pins the rule should the cks ever widen. W24's "72 of 1,953" joined bank slugs
     to the DB's `vocab:<headword>` unlock refs; against the export all 1,953 test a taught word.
     Report: research/reports/exam_taught_word_rule.md.
 21  18 AND 19 FOR `cf`. The stem needs MIN_STEM_CONTENT content tokens: 「（　）だけ来た」 keyed 一人
     is answered as well by 先月. A word distractor is refused when (a) it makes the stem a sentence
     the bank or raw_tatoeba_sentence has, (b) the bank or Tatoeba shows it between the same
     neighbours as the blank (`word_frames`): 「いい（　）だけど」 keyed 人 offered 男, or (c) it
     shares the key's open group (`open_group`), read in the filled stem: 「りんごが（　）ある」 keyed
     九つ offered 六つ and 四つ. Report: research/reports/exam_builder_fixes_3.md.
 22  WITHDRAWAL LEDGER. research/derived/reauthor/exam_authored/_flagged_auto.json, read by default
     (`--flagged {}` builds without it): ids a review withdrew (a second key the rules cannot see, a
     defective key sentence). Applied after the cap, so a withdrawal shrinks the bank and never
     backfills an unchecked item. Report: research/reports/q1_exam_fixes_3_report.md.

RUN ORDER (W18): the authored, listening and reading_comp builders first, this one LAST — the
INDEX below is a glob over every bank file, so a bank written after it leaves a stale row.

DEPENDENCY THIS ADDS: the exported `course/` tree. The taught set is read from the course export, as
the gate reads it, because the DB's `lesson.cumulative_known_set` stores `vocab:<headword>` refs that
only the exporter resolves to `vocab:<jmdict_id>`. Run `export_course.py` before this.
"""
from __future__ import annotations
import argparse, hashlib, json, sqlite3, sys
from itertools import islice
from pathlib import Path
sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
# W01: honour --db / $YOMINEKO_DB so a rebuild can target a scratch DB (scripts/dbtarget.py).
import sys as _sys, pathlib as _pl  # noqa: E402
_sys.path.append(str(next(p for p in _pl.Path(__file__).resolve().parents if p.name == "scripts")))
_sys.path.append(str(_pl.Path(__file__).resolve().parent))
from dbtarget import db_target  # noqa: E402
from exam_rules import (  # noqa: E402
    KANJI_RE, TaughtSets, has_kanji, interchangeable, kana_fold, load_equivalents, option_ok,
    reading_link_ok,
)
import bunsetsu  # noqa: E402
_sys.path.append(str(_pl.Path(__file__).resolve().parents[1] / "validate"))
# W18: one definition of "the same printed stem" — the collision gate's own.
from validate_exam_stem_collisions import normalize as stem_key  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
DB = db_target(ROOT / "db" / "corpus.sqlite")
OUT = ROOT / "corpus" / "exam_banks"
LEVELS = ("n5", "n4", "n3")
ORD = {"n5": 0, "n4": 1, "n3": 2, "n2": 3, "n1": 4}
allowed = lambda slvl, lvl: slvl in ORD and ORD[slvl] <= ORD[lvl]
CAPS = {"kanji_reading": 400, "orthography": 400, "context_fill": 400, "grammar_form": 300, "sentence_order": 300, "text_grammar": 150}
HAS_KANJI = has_kanji

# Sidecars under corpus/exam_banks that are not banks. `removed_items.json` matched `*_*.json`, so the
# INDEX gained the line "- removed_items.json — 3 items" (len() over its {why,count,items} dict).
NOT_A_BANK = {"removed_items.json"}
# Fix 22: ids withdrawn by review, {bank: [{id, kind, why, ...}]}.
FLAGGED = ROOT / "research" / "derived" / "reauthor" / "exam_authored" / "_flagged_auto.json"

_TOK = None
_MODE_C = None


def _tok():
    """SudachiPy mode-C tokenizer, built on first use so a run that emits no text_grammar item never
    pays for the dictionary."""
    global _TOK, _MODE_C
    if _TOK is None:
        from sudachipy import dictionary, tokenizer
        _TOK = dictionary.Dictionary(dict="full").create()
        _MODE_C = tokenizer.Tokenizer.SplitMode.C
    return _TOK


def token_spans(tok, mode, text: str) -> tuple[set, set]:
    """Character offsets where a SudachiPy mode-C token starts and ends, for one string.

    W16. `text_grammar` used to blank a grammar form with `jp.replace(form, "（　）", 1)`, which cuts
    wherever the characters happen to line up — inside a word as readily as around one. `のに` is a
    form; it is also the tail of 読む**のに**時間 and the middle of たの**のに**… A stem blanked mid-word
    is not a grammar question, it is a typo the learner has to see through, and the distractor set
    (whole forms) can no longer fit the hole. The blank is now cut only where the form BEGINS at a
    token start and ENDS at a token end.
    """
    starts, ends = set(), set()
    for m in tok.tokenize(text, mode):
        starts.add(m.begin())
        ends.add(m.end())
    return starts, ends


def boundary_occurrence(text: str, form: str, starts: set, ends: set) -> int:
    """Index of the first occurrence of `form` in `text` that is token-aligned, or -1."""
    i = text.find(form)
    while i != -1:
        if i in starts and i + len(form) in ends:
            return i
        i = text.find(form, i + 1)
    return -1


# Fix 19: POS that carry no context of their own. A stem is only as informative as the content words
# printed around its blank; 「（　）？」 keyed なぜ has none, and する / もう / まだ fit it as well.
FUNCTION_POS = {"助詞", "助動詞", "補助記号", "記号", "空白"}
# Prefixes, prenominals and conjunctions give a stem no context either: お（　）だけ keyed 水, どの（　）が
# 安い keyed 店, また話し（　）だ keyed 中 each count only one real content word. The stem counter only;
# `word_frames` keeps FUNCTION_POS, since a prenominal (その試合) is a real frame neighbour.
STEM_FUNCTION_POS = FUNCTION_POS | {"接頭辞", "連体詞", "接続詞"}
MIN_STEM_CONTENT = 2
# Conjugation types whose 未然形 and 連用形 print the same string (食べ, し, 来, 入れられ).
SAME_MIZEN_RENYOU = ("上一段", "下一段", "カ行変格", "サ行変格",
                     "助動詞-レル", "助動詞-ラレル", "助動詞-セル", "助動詞-サセル")


def slot_shape(ms, at: int) -> frozenset[str]:
    """Fix 18: what a form printed at offset `at` of a tokenized text attaches to — the POS and
    conjugation form of the token ending there, `|` at the text edge or after punctuation.

    SudachiPy tags a conjugated word by what FOLLOWS it; the learner reads the string. So a string
    that can be several forms is all of them: 言う is 終止形 before べき and 連体形 before ように, and
    入れ is 未然形 before られる and 連用形 before ていた. 動詞 and 助動詞 are one class (an auxiliary
    conjugates like the verb it extends) and every 連用形 variant is one (帰り, 帰っ). Coarser only
    ever refuses more distractors, never admits one."""
    m = next((m for m in ms if m.end() == at), None)
    if m is None or m.part_of_speech()[0] in ("補助記号", "記号", "空白"):
        return frozenset({"|"})
    p = m.part_of_speech()
    pos = "用言" if p[0] in ("動詞", "助動詞") else p[0]
    c = p[5].split("-")[0]
    if c == "*":
        return frozenset({pos})
    if c in ("終止形", "連体形"):
        cs = ("終止形", "連体形")
    elif c in ("未然形", "連用形") and p[4].startswith(SAME_MIZEN_RENYOU):
        cs = ("未然形", "連用形")
    else:
        cs = (c,)
    return frozenset(f"{pos}/{x}" for x in cs)


def content_tokens(ms, at: int, end: int) -> int:
    """Fix 19: content tokens printed outside the blank [at, end)."""
    return sum(1 for m in ms if (m.end() <= at or m.begin() >= end)
               and m.part_of_speech()[0] not in STEM_FUNCTION_POS)


# Fix 21: SudachiPy subclasses that name a semantic group, not just a syntax. Members of one group stand
# in for each other wherever the group can stand: 「（　）だけ来た」 keyed 一人 is answered as well by
# 先月, 「りんごを（　）買った」 keyed 五つ by 九つ or 毎年. The stem cannot rule a same-group
# distractor out, so it is refused. Common nouns and verbs carry no such group and are left to the
# attestation test.
OPEN_GROUPS = (
    ("adverbial", ("名詞-普通名詞-副詞可能", "名詞-数詞", "副詞")),   # time / quantity / place; numerals
    ("adjectival", ("形容詞", "形状詞", "連体詞")),
    ("pronoun", ("代名詞",)),
    ("counter-noun", ("名詞-普通名詞-助数詞可能",)),
)


def open_group(ms, at: int, end: int) -> str | None:
    """Fix 21: the open group of the word printed at [at, end) of a tokenized text, read in place (千
    alone is a name, in 千人 a numeral), or None when it has none or does not stand as its own tokens."""
    span = [m for m in ms if m.begin() >= at and m.end() <= end]
    if not span or span[0].begin() != at or span[-1].end() != end:
        return None
    c = "-".join(x for x in span[0].part_of_speech()[:3] if x != "*")
    return next((g for g, prefixes in OPEN_GROUPS if c.startswith(prefixes)), None)


def word_frames(ms: list, i: int) -> list[tuple[str, str, str, str]]:
    """Fix 21: token i's frame on each side that has a content word, by normalized form: (content word
    before, the particles between, w) and (w, the particles between, content word after)."""
    out = []
    j = i + 1
    while j < len(ms) and ms[j].part_of_speech()[0] == "助詞":
        j += 1
    if j < len(ms) and ms[j].part_of_speech()[0] not in FUNCTION_POS:
        out.append(("R", ms[i].normalized_form(), "".join(m.surface() for m in ms[i + 1:j]),
                    ms[j].normalized_form()))
    j = i - 1
    while j >= 0 and ms[j].part_of_speech()[0] == "助詞":
        j -= 1
    if j >= 0 and ms[j].part_of_speech()[0] not in FUNCTION_POS:
        out.append(("L", ms[j].normalized_form(), "".join(m.surface() for m in ms[j + 1:i]),
                    ms[i].normalized_form()))
    return out


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


def is_hiragana_only(s: str) -> bool:
    return bool(s) and all(0x3041 <= ord(c) <= 0x309F or c == "ー" for c in s)


def spread(anchor: str, value: str) -> str:
    """Deterministic per-item tiebreak for equally-close candidates.

    Ties used to break ALPHABETICALLY, which meant the same alphabetically-first words won for every
    single target: 400 n4 kanji_reading items shared just 31 distinct distractors, あがる/あさい/あいだ
    appearing on ~133 questions each. A learner eliminates those from memory after two questions, which
    defeats the point of the bank. Hashing (anchor, value) spreads choices across the whole eligible pool
    while keeping the build reproducible — this file's contract is "deterministic, no RNG", and a hash is
    deterministic; only the *ordering* is arbitrary, which is exactly what a tiebreak should be.
    """
    return hashlib.sha1(f"{anchor}{value}".encode("utf-8")).hexdigest()


def pick_distractors(cands, correct_key, want=3):
    """cands: list of (sort_key, value) pre-ordered by closeness; returns first `want` unique values."""
    out, seen = [], {correct_key}
    for _, v in cands:
        if v in seen:
            continue
        seen.add(v)
        out.append(v)
        if len(out) == want:
            break
    return out


def group_order(cands: list[dict], lvl: str) -> list[dict]:
    """Which record represents a homophone / homograph group, best first (W17 fix 12).

    Deterministic and evidence-ordered: the record whose OWN level is this bank's level first — an
    N4 漢字読み item should test the N4 word, and 米 names both vocab:1132570 (メートル, N5) and
    vocab:1508750 (こめ, N4), which a cumulative known set puts in the same group — then a JMdict
    `common` spelling, then a better frequency rank, then the JMdict entry number so the choice
    never depends on row order. The caller walks this list and takes the first record that can
    actually be built into an item, rather than losing the whole group when the representative
    happens to have no usable distractors.
    """
    return sorted(cands, key=lambda v: (0 if v["lvl"] == lvl else 1,
                                        0 if v["common"] else 1,
                                        v["freq"] if v["freq"] is not None else 10 ** 9,
                                        v["slug"]))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=None,
                    help="write the banks here instead of corpus/exam_banks (prototype mode: "
                         "nothing under corpus/ is touched)")
    ap.add_argument("--root", default=None,
                    help="tree to read the course export from (default: the repo root)")
    ap.add_argument("--stats", default=None, help="write per-family selection counters here (JSON)")
    # Fix 22: the withdrawal ledger, read by default like build_listening_bank.py's
    # `_flagged_listen.json`, so a rebuild never re-admits a withdrawn item. `--flagged {}` builds
    # without it.
    ap.add_argument("--flagged", default=None, help="withdrawal ledger as a JSON string")
    args = ap.parse_args()
    raw = args.flagged if args.flagged is not None else (
        FLAGGED.read_text(encoding="utf-8") if FLAGGED.is_file() else "{}")
    withdrawn: dict[str, set[str]] = {bank: {r["id"] for r in rows}
                                      for bank, rows in json.loads(raw).items()}
    out_dir = Path(args.out) if args.out else OUT
    root = Path(args.root).resolve() if args.root else ROOT
    con = sqlite3.connect(DB)
    out_dir.mkdir(parents=True, exist_ok=True)
    counts = {}
    drops: dict[str, dict[str, int]] = {}

    def drop(fam: str, why: str) -> None:
        drops.setdefault(fam, {}).setdefault(why, 0)
        drops[fam][why] += 1

    # ---- the level rule (W03), from the course export -----------------------------------------
    taught = TaughtSets(root)
    equiv = load_equivalents()

    vocab = [dict(zip(("id", "slug", "hw", "kana", "lex", "lvl", "common", "freq"), r))
             for r in con.execute(
        "SELECT id,slug,headword,kana,lexeme_type,level,COALESCE(common,0),freq_rank FROM vocab "
        "WHERE kana!='' ORDER BY id")]
    vb_by_id = {v["id"]: v for v in vocab}
    # Uncollapsed spelling -> every reading it can take. A kanji_reading distractor that is ALSO a
    # reading of the stem is a second right answer; 93 headwords are shared by 193 records, so a
    # dict keyed by headword would have hidden exactly the collisions this guards.
    hw_readings: dict[str, set[str]] = {}
    for v in vocab:
        hw_readings.setdefault(v["hw"], set()).add(v["kana"])
    # Fix 17: and every reading JMdict gives the spelling, including readings no record here keeps —
    # 御 reads おん, and or:n3:1553 offered it against the key 音 for the stem おん.
    if con.execute("SELECT name FROM sqlite_master WHERE name='raw_jmdict_entry'").fetchone():
        for (data,) in con.execute("SELECT data FROM raw_jmdict_entry ORDER BY ent_seq"):
            e = json.loads(data)
            for r in e.get("kana", []):
                applies = r.get("appliesToKanji") or ["*"]
                for k in e.get("kanji", []):
                    if "*" in applies or k["text"] in applies:
                        hw_readings.setdefault(k["text"], set()).add(r["text"])

    # pt-BR text for the derived `explanation` (fix 15) comes from `localized_text`, the locale
    # module (design/i18n.md) — NOT from the legacy `*_pt` columns. `sentence.pt` is NULL on all
    # 5,889 rows and `grammar_point.label_pt` on all 496, because the pt-BR content moved to the
    # locale table; reading the columns produced an explanation that was empty or that just
    # repeated the answer.
    LOC = "pt-BR"
    gloss: dict[int, str] = {}          # vocab row id -> first gloss of sense 0
    gloss_set: dict[int, set[str]] = {}  # vocab row id -> every gloss of that sense (fix 17)
    for vid, val in con.execute(
            "SELECT vs.vocab_id, lt.value FROM vocab_sense vs "
            "JOIN localized_text lt ON lt.entity_type='vocab_sense' AND lt.entity_id=vs.id "
            "  AND lt.field='gloss' AND lt.locale=? "
            "WHERE vs.sense_order=0 ORDER BY vs.vocab_id, vs.id", (LOC,)):
        if vid in gloss:
            continue
        try:
            g = json.loads(val or "[]")
        except Exception:
            g = []
        if g:
            gloss[vid] = str(g[0])
            gloss_set[vid] = {str(x).strip().lower() for x in g}
    # ... keyed by the PRINTED spelling: 先 is both さき ('à frente') and さっき ('agora há pouco'), and
    # the learner reads the string, not the record the builder happened to draw it from.
    gloss_of_hw: dict[str, set[str]] = {}
    for v in vocab:
        gloss_of_hw.setdefault(v["hw"], set()).update(gloss_set.get(v["id"], ()))
    # grammar: the per-FORM meaning where the record has one, else the point's own label.
    form_meaning: dict[str, str] = {}   # grammar key -> {form: meaning}
    glabel: dict[str, str] = {}
    for key, field, val in con.execute(
            "SELECT g.key, lt.field, lt.value FROM localized_text lt "
            "JOIN grammar_point g ON g.id = lt.entity_id "
            "WHERE lt.entity_type='grammar_point' AND lt.locale=? "
            "  AND lt.field IN ('form_meanings','label') ORDER BY g.key", (LOC,)):
        if field == "label":
            glabel[key] = val or ""
        else:
            try:
                form_meaning[key] = json.loads(val or "{}")
            except Exception:
                pass
    sent_pt: dict[int, str] = {sid: (v or "") for sid, v in con.execute(
        "SELECT entity_id, value FROM localized_text WHERE entity_type='sentence' "
        "AND field='translation' AND locale=?", (LOC,))}

    # real sentences preferred; verified-generated (passed the §9 gen gates, needs_review) fill thin levels
    sents = {sid: (slug, jp, lvl, ai, pt) for sid, slug, jp, lvl, ai, pt in con.execute(
        "SELECT id,slug,jp,level,COALESCE(ai_generated,0),COALESCE(pt,'') FROM sentence ORDER BY id")}
    svocab: dict = {}
    # W17 fix 7: an explicit ORDER BY, so stability does not depend on this query happening to be
    # answered from the PK covering index. `reading_verified DESC` is fix 4's preference — a verified
    # anchor wins the `break` below when a sentence links more than one eligible word.
    for sid, vid in con.execute(
            "SELECT sentence_id,vocab_id FROM sentence_vocab "
            "ORDER BY sentence_id, COALESCE(reading_verified,0) DESC, vocab_id"):
        if sid in sents:
            svocab.setdefault(sid, []).append(vid)

    # The mode-C tokens, exactly as corpus/sentences/bank.json publishes `tokens[]` (W45: the mode-A
    # sub-units nest as `parts[]` there and carry no vocab) — that is what the level gate reads for
    # the vocab dimension, so the builder must select on the same set.
    slug_of_vid = {v["id"]: v["slug"] for v in vocab}
    tok_vocab: dict[int, set[str]] = {}
    toks_c: dict[int, list[dict]] = {}
    for sid, surf, lemma, read, pos, vid in con.execute(
            "SELECT sentence_id,surface,lemma,reading,pos,vocab_id FROM token "
            "WHERE split_mode='C' ORDER BY sentence_id, position, id"):
        if sid not in sents:
            continue
        if vid is not None and vid in slug_of_vid:
            tok_vocab.setdefault(sid, set()).add(slug_of_vid[vid])
        toks_c.setdefault(sid, []).append(
            {"surface": surf, "lemma": lemma, "reading": read, "pos": pos})

    def form_strs(forms_json):
        """forms_json entries are plain strings (or occasionally dicts) — normalize, then apply the
        option-shape guards (W17 fix 8/14, `exam_rules.option_ok`)."""
        out = []
        try:
            for f in json.loads(forms_json or "[]"):
                fm = (f if isinstance(f, str) else (f.get("form") or "")).strip()
                fm = fm.lstrip("～〜").strip()  # N3 forms are cited as ～うちに; the sentence contains うちに
                if option_ok(fm):
                    out.append(fm)
        except Exception:
            pass
        return out

    gp = {gid: (key, lvl, forms, label) for gid, key, lvl, forms, label in con.execute(
        "SELECT id,key,level,forms_json,COALESCE(label_pt,'') FROM grammar_point "
        "WHERE deprecated_by IS NULL ORDER BY id")}
    gforms = []            # (level, key, form)
    gkey_of_form: dict[tuple[str, str], str] = {}   # (level, form) -> the grammar key that owns it
    # W08b: merged-away rows keep their forms; a regeneration must not re-issue items on them.
    for key, lvl, forms in con.execute(
            "SELECT key,level,forms_json FROM grammar_point "
            "WHERE level IN ('n5','n4','n3') AND deprecated_by IS NULL ORDER BY key"):
        for fm in form_strs(forms):
            gforms.append((lvl, key, fm))
            gkey_of_form.setdefault((lvl, fm), key)
    sgram: dict = {}
    for sid, gid in con.execute(
            "SELECT sentence_id,grammar_id FROM sentence_grammar ORDER BY sentence_id, grammar_id"):
        if sid in sents:
            sgram.setdefault(sid, []).append(gid)
    sent_gram_slugs: dict[int, set[str]] = {}
    for sid, gids in sgram.items():
        sent_gram_slugs[sid] = {"gram:" + gp[g][0] for g in gids if g in gp}

    readings = [(slug, rlvl, jp) for slug, rlvl, jp in con.execute(
        "SELECT slug,level,jp FROM reading ORDER BY slug")] \
        if con.execute("SELECT name FROM sqlite_master WHERE name='reading'").fetchone() else []

    # W17 fix 14: a form may only be PRINTED if the level's own corpus attests it. A pattern label
    # whose 〜 slots were stripped (`よりほうが`, `の中でが一番`, `のはだ`) occurs in no real Japanese,
    # which is precisely what makes it eliminable on sight; a real form occurs in the sentences the
    # level is built from. Cheap to compute and it needs no new vocabulary of exceptions.
    attested: dict[str, set[str]] = {}
    for lvl in LEVELS:
        corpus_text = [jp for (_s, jp, slvl, _ai, _pt) in sents.values() if allowed(slvl, lvl)]
        corpus_text += [jp for (_s, rlvl, jp) in readings if allowed(rlvl, lvl)]
        blob = "\n".join(corpus_text)
        attested[lvl] = {fm for (l2, _k, fm) in gforms if l2 == lvl and fm in blob}

    # Fix 18: where each form is ATTESTED — every slot shape it fills, token-aligned, anywhere in the
    # bank or the readings (grammaticality does not depend on the level) — and every bank sentence, so
    # a distractor that makes the stem a real sentence, or that the corpus shows in the same slot as
    # the key, is refused: 「もう帰っ（　）。」 keyed たらどうですか offered たらいいですか.
    tk = _tok()
    all_forms = {fm for _l, _k, fm in gforms}
    slot_seen: dict[str, set[str]] = {}
    for text in [s[1] for s in sents.values()] + [r[2] for r in readings]:
        here = [x for x in all_forms if x in text]
        if not here:
            continue
        ms = tk.tokenize(text, _MODE_C)
        starts, ends = token_spans(tk, _MODE_C, text)
        for x in here:
            i = text.find(x)
            while i != -1:
                if i in starts and i + len(x) in ends:
                    slot_seen.setdefault(x, set()).update(slot_shape(ms, i))
                i = text.find(x, i + 1)
    bank_keys = {stem_key(s[1]) for s in sents.values()}

    def admissible(x: str, shape: frozenset[str], pre: str, post: str) -> bool:
        # `x not in pre + post` is validate_exam_banks check C, which `x not in jp` misses when the
        # blank itself splits the distractor: が（　）います offered がいます.
        return (x not in pre + post and not shape & slot_seen.get(x, set())
                and stem_key(pre + x + post) not in bank_keys)

    # Fix 21: the same rule for context_fill, where the options are words. A word distractor is refused
    # when it makes the stem a sentence the bank or Tatoeba has; when the bank or Tatoeba shows it
    # between the same neighbours as the blank (`word_frames`, every side that has a content word):
    # 「いい（　）だけど」 keyed 人 offered 男; or when it shares the key's open group (`open_group`).
    said = [s[1] for s in sents.values()]
    if con.execute("SELECT name FROM sqlite_master WHERE name='raw_tatoeba_sentence'").fetchone():
        said += [t for (t,) in con.execute("SELECT text FROM raw_tatoeba_sentence ORDER BY id")]
    said_keys = {stem_key(t) for t in said}
    frame_seen: set[tuple[str, str, str, str]] = set()
    for text in said:
        ms = list(tk.tokenize(text, _MODE_C))
        for i, m in enumerate(ms):
            if m.part_of_speech()[0] not in FUNCTION_POS:
                frame_seen.update(word_frames(ms, i))

    def cf_admissible(x: str, group: str | None, pre: str, post: str) -> bool:
        if x in pre + post or stem_key(pre + x + post) in said_keys:
            return False
        ms = list(tk.tokenize(pre + x + post, _MODE_C))
        i = next((k for k, m in enumerate(ms)
                  if m.begin() == len(pre) and m.end() == len(pre) + len(x)), None)
        fr = word_frames(ms, i) if i is not None else []
        if fr and all(f in frame_seen for f in fr):
            return False
        return group is None or open_group(ms, len(pre), len(pre) + len(x)) != group

    # ---- the taught, level-clean vocabulary pool ----------------------------------------------
    # A word may be the ANSWER or a DISTRACTOR at a level only when the course has taught the record
    # and every kanji it prints. This is the pool W03 measured (177 level-clean N5 words against an
    # orthography floor of 15), and it is what turns the level ceilings into 0.
    clean_pool: dict[str, list[dict]] = {}
    for lvl in LEVELS:
        clean_pool[lvl] = [v for v in vocab
                           if taught.vocab_ok(v["slug"], lvl)
                           and HAS_KANJI(v["hw"]) and v["hw"] != v["kana"]
                           and taught.kanji_ok(v["hw"], lvl)]
        clean_pool[lvl].sort(key=lambda v: (v["kana"], v["hw"], v["slug"]))

    for lvl in LEVELS:
        lv_vocab = clean_pool[lvl]
        pool_slugs = {v["slug"] for v in lv_vocab}

        # ---- kanji_reading + orthography -----------------------------------------------------
        # W17 fix 12: one item per printed STEM. 背 was two kanji_reading items keyed せ and せい;
        # あつい was three orthography items keyed 暑い / 熱い / 厚い over an identical option set.
        # Fix 20: the word under test is one a lesson teaches; distractors still come from the whole
        # level-clean pool, which is what the learner may meet.
        by_hw: dict[str, list[dict]] = {}
        by_kana: dict[str, list[dict]] = {}
        for v in lv_vocab:
            if not taught.word_taught(v["slug"], lvl):
                drop("kanji_reading", "target-word-not-taught")
                drop("orthography", "target-word-not-taught")
                continue
            by_hw.setdefault(v["hw"], []).append(v)
            by_kana.setdefault(v["kana"], []).append(v)
        kr_groups = sorted((group_order(g, lvl) for g in by_hw.values()),
                           key=lambda g: (g[0]["kana"], g[0]["hw"]))
        or_groups = sorted((group_order(g, lvl) for g in by_kana.values()),
                           key=lambda g: (g[0]["kana"], g[0]["hw"]))
        for hw, g in by_hw.items():
            if len(g) > 1:
                drop("kanji_reading", "homograph-group-deduped")
        for kana, g in by_kana.items():
            if len(g) > 1:
                drop("orthography", "homophone-group-deduped")

        kr, ort = [], []
        for group in kr_groups:
            # Walk the group best-first and keep the first record that yields four real options.
            for v in group:
                tail, head = hiragana_tail(v["hw"]), hiragana_head(v["hw"])

                def shaped(o: str, tail: str = tail, head: str = head) -> bool:
                    """EB-02: does this reading match the stem's okurigana shape? An option that does
                    not is eliminated without reading the kanji, which is what made 373 of 439 items
                    shape-solvable."""
                    return (not tail or o.endswith(tail)) and (not head or o.startswith(head))

                # kanji_reading distractors: a kana reading of another level-clean word, never a
                # reading the stem itself takes, and the same script class as the key — a katakana
                # loanword (グラム, コーヒー) can never read a kanji stem and drops the item to three
                # real options.
                kc = []
                for w in lv_vocab:
                    if w["id"] == v["id"] or w["kana"] == v["kana"]:
                        continue
                    if w["kana"] in hw_readings.get(v["hw"], ()):
                        continue
                    if is_hiragana_only(v["kana"]) != is_hiragana_only(w["kana"]):
                        continue
                    s = (0 if shaped(w["kana"]) else 100)                         + abs(len(w["kana"]) - len(v["kana"])) * 10                         + (0 if w["lex"] == v["lex"] else 5)
                    kc.append((s, w["kana"]))
                kc.sort(key=lambda t: (t[0], spread(v["hw"], t[1])))
                dk = pick_distractors(kc, v["kana"])
                if len(dk) == 3 and taught.strings_kanji_ok([v["hw"], v["kana"], *dk], lvl):
                    kr.append({"id": f"kr:{lvl}:{v['id']}", "level": lvl, "stem": v["hw"],
                               "correct": v["kana"], "distractors": dk, "vocab": v["slug"],
                               "vocab_id": v["id"], "source": "vocab",
                               "explanation": {"pt-BR": explain_vocab(v, gloss)},
                               "layer": "B", "ai_generated": False, "needs_review": False})
                    break
            else:
                drop("kanji_reading", "no-clean-distractor-set")

        for group in or_groups:
            for v in group:
                stem = v["kana"]

                def fits(o: str, stem: str = stem) -> bool:
                    """EB-06: the printed spelling's own kana head/tail has to be compatible with the
                    stem, or it is eliminated on shape."""
                    t, h = hiragana_tail(o), hiragana_head(o)
                    return (not t or stem.endswith(t)) and (not h or stem.startswith(h))

                hc = []
                for w in lv_vocab:
                    if w["id"] == v["id"] or w["kana"] == v["kana"]:
                        continue        # a homophone spelling would be a second right answer
                    if v["kana"] in hw_readings.get(w["hw"], ()):
                        continue        # ... and so would any other spelling that also reads the stem
                    s = (0 if fits(w["hw"]) else 40)                         + (30 if abs(len(w["hw"]) - len(v["hw"])) >= 2 else 0)                         + abs(len(w["hw"]) - len(v["hw"])) * 10                         + (0 if w["lex"] == v["lex"] else 5)
                    hc.append((s, w["hw"]))
                hc.sort(key=lambda t: (t[0], spread(v["kana"], t[1])))
                dh = pick_distractors(hc, v["hw"])
                if len(dh) == 3 and taught.strings_kanji_ok([v["hw"], *dh], lvl):
                    ort.append({"id": f"or:{lvl}:{v['id']}", "level": lvl, "stem": v["kana"],
                                "correct": v["hw"], "distractors": dh, "vocab": v["slug"],
                                "vocab_id": v["id"], "source": "vocab",
                                "explanation": {"pt-BR": explain_ortho(v, gloss)},
                                "layer": "B", "ai_generated": False, "needs_review": False})
                    break
            else:
                drop("orthography", "no-clean-distractor-set")

        # ---- context_fill --------------------------------------------------------------------
        cf, cf_stems = [], set()
        for sid in sorted(svocab, key=lambda x: (sents[x][3], x)):
            if len(cf) >= CAPS["context_fill"]:
                break
            slug, jp, slvl, ai, pt = sents[sid]
            if not allowed(slvl, lvl):
                continue
            # the level rule, on the sentence itself: its dissection is what the gate reads
            if not (tok_vocab.get(sid, set()) <= taught.by_level[lvl]["vocab"]):
                drop("context_fill", "sentence-vocab-above-level")
                continue
            if not (sent_gram_slugs.get(sid, set()) <= taught.by_level[lvl]["grammar"]):
                drop("context_fill", "sentence-grammar-above-level")
                continue
            if not taught.kanji_ok(jp, lvl):
                drop("context_fill", "sentence-kanji-above-level")
                continue
            for vid in svocab[sid]:
                v = vb_by_id.get(vid)
                if not v or v["slug"] not in pool_slugs or v["hw"] not in jp:
                    continue
                if jp.count(v["hw"]) > 1:
                    drop("context_fill", "leak-guard-multiple-occurrence")
                    continue        # EB-05: blanking one leaves the answer printed in the other
                if not reading_link_ok([(t["surface"], t["lemma"], t["reading"])
                                        for t in toks_c.get(sid, [])], v["hw"], v["kana"]):
                    drop("context_fill", "reading-does-not-agree")
                    continue        # qa F4: 空/から on a *sky* sentence, 時/とき on a clock reading
                at = jp.index(v["hw"])
                end = at + len(v["hw"])
                ms = tk.tokenize(jp, _MODE_C)
                if content_tokens(ms, at, end) < MIN_STEM_CONTENT:
                    drop("context_fill", "stem-too-short")          # fix 21 (19 for cf)
                    continue
                # W18: two sentences that differ only in the blanked word print the SAME question
                # with two keys (どのくらい（　） keyed 大きい and 高い); whichever the learner picks,
                # one item marks it wrong. The first stem wins; the sentence tries its next word.
                if stem_key(jp.replace(v["hw"], "（　）", 1)) in cf_stems:
                    drop("context_fill", "duplicate-printed-stem")
                    continue
                cands = []
                for w in lv_vocab:
                    if w["id"] == v["id"] or w["hw"] in jp:
                        continue
                    # fix 17: a word sharing a sense-0 gloss with the key fits the same blank —
                    # 「（　）に行ってください。」 keyed 前 offered 先 (both 'à frente').
                    if gloss_of_hw.get(w["hw"], set()) & gloss_set.get(v["id"], set()):
                        continue
                    cands.append((abs(len(w["hw"]) - len(v["hw"])) * 10
                                  + (0 if w["lex"] == v["lex"] else 20), w["hw"]))
                cands.sort(key=lambda t: (t[0], spread(f"{sid}:{v['hw']}", t[1])))
                # fix 21: walk the same order, keeping only what the stem rules out.
                base = pick_distractors(cands, v["hw"], want=len(cands))
                group = open_group(ms, at, end)
                dh = list(islice((x for x in base
                                  if cf_admissible(x, group, jp[:at], jp[end:])), 3))
                if len(dh) == 3:
                    cf_stems.add(stem_key(jp.replace(v["hw"], "（　）", 1)))
                    cf.append({"id": f"cf:{lvl}:{sid}:{vid}", "level": lvl,
                               "stem": jp.replace(v["hw"], "（　）", 1), "correct": v["hw"],
                               "distractors": dh, "sentence": slug, "vocab": v["slug"], "vocab_id": vid,
                               "explanation": {"pt-BR": explain_vocab(v, gloss)},
                               "layer": "B", "ai_generated": bool(ai), "needs_review": bool(ai),
                               "source": "sentence+vocab"})
                else:
                    drop("context_fill", "no-admissible-distractor" if len(base) >= 3
                         else "no-clean-distractor-set")
                break  # one item per sentence

        # ---- grammar_form --------------------------------------------------------------------
        gf, gf_stems = [], set()
        # The printable form pool for this level: attested in the level's own corpus, readable at
        # the level, and owned by a grammar point the course actually TEACHES. That last clause is
        # not decoration — `gram:gp-152` (the A3 duplicate of `gram:te-hoshii`, which no lesson
        # unlocks) owns a form that put an untaught grammar key on a live N4 item.
        lv_forms = sorted({fm for l2, k, fm in gforms
                           if l2 == lvl and fm in attested[lvl] and taught.kanji_ok(fm, lvl)
                           and taught.grammar_ok(k, lvl)})
        for sid in sorted(sgram, key=lambda x: (sents[x][3], x)):
            if len(gf) >= CAPS["grammar_form"]:
                break
            slug, jp, slvl, ai, pt = sents[sid]
            if not allowed(slvl, lvl):
                continue
            if not (tok_vocab.get(sid, set()) <= taught.by_level[lvl]["vocab"]):
                drop("grammar_form", "sentence-vocab-above-level")
                continue
            if not (sent_gram_slugs.get(sid, set()) <= taught.by_level[lvl]["grammar"]):
                drop("grammar_form", "sentence-grammar-above-level")
                continue
            if not taught.kanji_ok(jp, lvl):
                drop("grammar_form", "sentence-kanji-above-level")
                continue
            for gid in sgram[sid]:
                key, glvl, forms, _label = gp.get(gid, (None, None, None, ""))
                if glvl != lvl or not forms or not taught.grammar_ok(key, lvl):
                    continue
                # EB-05 for gf: the blanked form must occur EXACTLY ONCE, or the stem prints its own
                # answer further along.
                single = [x for x in form_strs(forms) if x in lv_forms and jp.count(x) == 1]
                if not single:
                    drop("grammar_form", "no-single-occurrence-form")
                    continue
                # fix 18: W16's token-boundary rule, which text_grammar already had. 「あなたの（　）す。」
                # keyed おかげで left the answer's own す printed after the blank.
                starts, ends = token_spans(tk, _MODE_C, jp)
                fm = next((x for x in single if boundary_occurrence(jp, x, starts, ends) >= 0), None)
                if not fm:
                    drop("grammar_form", "blank-cuts-a-word")
                    continue
                at, ms = jp.index(fm), tk.tokenize(jp, _MODE_C)
                if content_tokens(ms, at, at + len(fm)) < MIN_STEM_CONTENT:
                    drop("grammar_form", "stem-too-short")          # fix 19
                    continue
                if stem_key(jp.replace(fm, "（　）", 1)) in gf_stems:
                    drop("grammar_form", "duplicate-printed-stem")   # W18, as in context_fill
                    continue
                # NB: this used to slice [:40] BEFORE sorting, i.e. off an alphabetically-sorted
                # lv_forms — so the candidate set was the same 40 forms every time. Sort the full pool.
                # W17 fix 14: never offer another form of the SAME grammar point as a wrong answer —
                # んです was keyed with のです offered, and じゃない with ではない, on a point whose own
                # key is `janai-dewa-nai`.
                # fix 17: nor a form that is as right as the key in this blank (のような / みたいな).
                pre, post = jp.split(fm, 1)
                base = [x for x in lv_forms
                        if x != fm and x not in jp and gkey_of_form.get((lvl, x)) != key
                        and not interchangeable(fm, x, pre, post, equiv)]
                # fix 18: and never a form that fits the slot as the corpus shows it used.
                shape = slot_shape(ms, at)
                dis = [x for x in base if admissible(x, shape, pre, post)]
                dis.sort(key=lambda x: (abs(len(x) - len(fm)), spread(f"{sid}:{fm}", x)))
                if len(dis) >= 3:
                    gf_stems.add(stem_key(jp.replace(fm, "（　）", 1)))
                    gf.append({"id": f"gf:{lvl}:{sid}", "level": lvl,
                               "stem": jp.replace(fm, "（　）", 1), "correct": fm, "distractors": dis[:3],
                               "sentence": slug, "grammar": key,
                               "explanation": {"pt-BR": explain_grammar(fm, key, form_meaning, glabel)},
                               "layer": "B", "ai_generated": bool(ai), "needs_review": bool(ai),
                               "source": "sentence+grammar"})
                else:
                    drop("grammar_form", "no-admissible-distractor" if len(base) >= 3
                         else "no-clean-distractor-set")
                break

        # ---- sentence_order ------------------------------------------------------------------
        # qa F09: `so:n4:808` and `so:n4:809` were the same tiles and the same answer from two
        # different Tatoeba sentences, and sampling is without replacement BY ID, so one paper could
        # ask the same question twice out of its four 並べ替え slots. One item per answer string.
        so, so_answers = [], set()
        for sid in sorted(toks_c, key=lambda x: (sents[x][3], x)):
            if len(so) >= CAPS["sentence_order"]:
                break
            slug, jp, slvl, ai, pt = sents[sid]
            if not allowed(slvl, lvl):
                continue
            if not (tok_vocab.get(sid, set()) <= taught.by_level[lvl]["vocab"]):
                drop("sentence_order", "sentence-vocab-above-level")
                continue
            if not (sent_gram_slugs.get(sid, set()) <= taught.by_level[lvl]["grammar"]):
                drop("sentence_order", "sentence-grammar-above-level")
                continue
            if not taught.kanji_ok(jp, lvl):
                drop("sentence_order", "sentence-kanji-above-level")
                continue
            pieces = bunsetsu.chunk(toks_c[sid])
            if pieces is None:
                drop("sentence_order", "unchunkable")
                continue
            if not (4 <= len(pieces) <= 6):
                drop("sentence_order", f"chunk-count-{len(pieces)}")
                continue
            accepted, why = bunsetsu.scramble(pieces)
            if accepted is None:
                drop("sentence_order", why)
                continue
            answer = "".join(pieces)
            if answer in so_answers:
                drop("sentence_order", "duplicate-answer")
                continue
            so_answers.add(answer)
            so.append({"id": f"so:{lvl}:{sid}", "level": lvl, "pieces": pieces,
                       "answer": answer, "accepted": accepted, "sentence": slug,
                       "explanation": {"pt-BR": sent_pt.get(sid, "")},
                       "layer": "B", "ai_generated": bool(ai), "needs_review": bool(ai),
                       "source": "sentence-tokens"})

        # ---- text_grammar (文章の文法): blank a level-appropriate grammar form inside a READING passage ----
        tg = []
        tg_forms = lv_forms          # already attested + level-readable
        for slug, rlvl, jp in readings:
            if rlvl != lvl or len(tg) >= CAPS["text_grammar"]:
                continue
            if not taught.kanji_ok(jp, lvl):
                drop("text_grammar", "passage-kanji-above-level")
                continue
            # W16: the blank is cut at SudachiPy mode-C token boundaries, never inside a word.
            tk = _tok()
            starts, ends = token_spans(tk, _MODE_C, jp)
            fm, at = None, -1
            for cand in tg_forms:
                # The form must occur EXACTLY ONCE in the passage. A W15 passage is written
                # ABOUT its lesson's grammar target and therefore repeats it, so blanking the
                # first occurrence leaves the answer printed two lines down — which
                # validate_exam_banks check C ("stem prints its own answer outside the blank")
                # is there to catch. The old concatenations rarely repeated a form, so the rule
                # was never needed before the passages became real texts.
                if jp.count(cand) != 1:
                    continue
                at = boundary_occurrence(jp, cand, starts, ends)
                if at >= 0:
                    fm = cand
                    break
            if not fm:
                drop("text_grammar", "no-token-aligned-single-form")
                continue
            key = gkey_of_form.get((lvl, fm))
            if key and not taught.grammar_ok(key, lvl):
                drop("text_grammar", "form-owner-grammar-above-level")
                continue
            base = [x for x in tg_forms
                    if x != fm and x not in jp and gkey_of_form.get((lvl, x)) != key
                    and not interchangeable(fm, x, jp[:at], jp[at + len(fm):], equiv)]
            shape = slot_shape(tk.tokenize(jp, _MODE_C), at)      # fix 18
            dis = [x for x in base if admissible(x, shape, jp[:at], jp[at + len(fm):])]
            dis.sort(key=lambda x: (abs(len(x) - len(fm)), spread(f"{slug}:{fm}", x)))
            if len(dis) >= 3:
                tg.append({"id": f"tg:{lvl}:{slug.split(':',1)[1]}", "level": lvl,
                           "stem": jp[:at] + "（　）" + jp[at + len(fm):], "correct": fm,
                           "distractors": dis[:3], "reading": slug, "source": "reading+grammar",
                           "grammar": key or "",
                           "explanation": {"pt-BR": explain_grammar(fm, key or "", form_meaning, glabel)},
                           # Provenance the disabled migrate_exam_banks_p7.py used to stamp
                           # after the fact. A text_grammar stem is a REAL passage with one form
                           # blanked, so the Japanese the learner reads is not model-generated
                           # (ai_generated false) and the item is a derivation, not pedagogy
                           # (layer B). Emitted here so a regenerated bank carries it: the
                           # migration cannot run in a rebuild, and validate_provenance_json.py
                           # requires the fields on every item.
                           "layer": "B", "ai_generated": False, "needs_review": False})
                if not key:
                    tg[-1].pop("grammar")
            else:
                drop("text_grammar", "no-admissible-distractor" if len(base) >= 3
                     else "no-clean-distractor-set")

        for name, items in (("kanji_reading", kr), ("orthography", ort), ("context_fill", cf),
                            ("grammar_form", gf), ("sentence_order", so), ("text_grammar", tg)):
            items = items[:CAPS[name]]
            # Fix 22: withdraw AFTER the cap, so a withdrawal never backfills an unchecked item.
            out = withdrawn.get(f"{lvl}_{name}", set())
            if out:
                absent = sorted(out - {it["id"] for it in items})
                items = [it for it in items if it["id"] not in out]
                drops.setdefault(name, {})["withdrawn"] = (
                    drops.get(name, {}).get("withdrawn", 0) + len(out) - len(absent))
                if absent:
                    print(f"{lvl}_{name}: {len(absent)} ledger ids not built: {' '.join(absent)}")
            (out_dir / f"{lvl}_{name}.json").write_text(json.dumps(items, ensure_ascii=False), encoding="utf-8")
            counts[f"{lvl}_{name}"] = len(items)

    # INDEX covers ALL bank files (deterministic + authored) — glob, don't use only this run's counts,
    # so regenerating the deterministic banks never wipes the authored banks from the listing.
    # W17 fix 9: `removed_items.json` matches `*_*.json` and is NOT a bank — its top level is a
    # {why, count, items} dict, so it used to be listed as a 3-item bank.
    all_counts = {f.stem: len(json.loads(f.read_text(encoding="utf-8")))
                  for f in sorted(out_dir.glob("*_*.json")) if f.name not in NOT_A_BANK}
    (out_dir / "INDEX.md").write_text(
        "# corpus/exam_banks — JLPT-style question banks (our format)\n\n"
        "Per-level, per-type item banks DERIVED from verified corpus facts (vocab readings, real bank "
        "sentences, grammar forms) — deterministic types have no AI-generated Japanese; distractors are "
        "rule-built (same level/lexeme class, similar length, wrong by construction). Real JLPT papers are "
        "© JEES and were used only as FORMAT reference; zero copied text. The app's exam simulator randomly "
        "samples these per attempt — picker spec: `design/exam_simulator.md`. Item: {id, level, stem, "
        "correct, distractors|pieces, source refs}. Deterministic types are Layer B; the AUTHORED types "
        "(`paraphrase`, `usage`, `reading_comp`, `listening_*`) are Layer C (authored + adversarially "
        "verified, needs_review). `reading_comp` items reference their passage by `read:` slug — the app "
        "renders the passage from `corpus/readings` (single source of truth). `listening_*` items are "
        "voice-ready TEXT scripts (speaker-tagged turns, `audio: \"pending\"` — spec: `design/listening.md`); "
        "`listening_reply` prompts are REAL bank sentences verbatim (`sentence` ref).\n\n"
        "Every deterministic item is selected against its level's taught set (the `cumulative_known_set` "
        "of the last lesson of that level's module): every kanji it prints, its own vocabulary record, "
        "and the source sentence's token vocabulary and grammar tags are inside it — the rule "
        "`scripts/validate/validate_exam_level_gate.py` measures. `sentence_order` tiles are BUNSETSU and "
        "the item carries `accepted[]`, every reordering that means the same thing; the app grades "
        "against that list, not against one string. Auto-graded items carry a pt-BR `explanation` "
        "assembled from the record (gloss + reading, or the grammar point's label), never free prose.\n\n"
        "`removed_items.json` is a withdrawal ledger, not a bank, and is deliberately absent below.\n\n"
        + "".join(f"- `{k}.json` — {v} items\n" for k, v in sorted(all_counts.items())), encoding="utf-8")
    con.close()
    if args.stats:
        Path(args.stats).write_text(json.dumps({"counts": counts, "drops": drops},
                                               ensure_ascii=False, indent=1), encoding="utf-8")
    print("exam banks ->", counts)
    return 0


# --------------------------------------------------------------------------------------------
# W17 fix 15: explanations are TEMPLATES over record fields. No sentence here was written for a
# specific item; every variable is a Layer-A or Layer-B field that already has a gate of its own.
# --------------------------------------------------------------------------------------------
def explain_vocab(v: dict, gloss: dict[int, str]) -> str:
    # W18: learner-facing pt-BR carries no em dash (design/translation_style.md), so the templates
    # join with a colon / parentheses instead of the W17 draft's dash.
    g = gloss.get(v["id"], "")
    return f"{v['hw']}（{v['kana']}）: {g}" if g else f"{v['hw']}（{v['kana']}）"


def explain_ortho(v: dict, gloss: dict[int, str]) -> str:
    g = gloss.get(v["id"], "")
    return f"{v['kana']} escreve-se {v['hw']}" + (f" ({g})" if g else "")


def explain_grammar(fm: str, key: str, form_meaning: dict[str, dict], glabel: dict[str, str]) -> str:
    """The FORM's own pt-BR meaning where the record carries one (364 of 496 points do), else the
    point's pt-BR label. Never the point's Layer-C `explanation`: an item is Layer B and a
    didactic explanation belongs to the grammar record, which the item already references by key
    (spec 1.3 — fact and explanation never share a field)."""
    m = (form_meaning.get(key) or {}).get(fm) or ""
    if m:
        return f"{fm}: {m}"
    lb = glabel.get(key, "")
    return f"{fm}: {lb}" if lb else fm


if __name__ == "__main__":
    sys.exit(main())
