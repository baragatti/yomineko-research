#!/usr/bin/env python3
"""Gate: every item a lesson UNLOCKS is also PRACTISED by that same lesson's exercises.

WHY THIS EXISTS

`validate_exercise_contracts.py` enforces "a lesson that unlocks items renders >=1 retrieval and >=1
production exercise". That rule is satisfied by two exercises, whatever the lesson teaches. The two
readiness audits measured what the rule leaves uncovered
(`research/reports/readiness/jlpt_course_path.md` G2, `.../tests_exercises.md` G1): 1,560 exercises
against 4,133 unlocked items — 0.38 exercises per item — with vocab practised in its own lesson
39.9%, kanji 10.6%, grammar 86.1% by a surface-containment measure. The learner meets fifteen new
words, answers five questions about three of them, and the SRS then schedules all fifteen as though
they had been retrieved. Nothing in the suite could see it, because no gate ever asked "was THIS
item asked?".

This validator asks that question, per item, over the EXPORTED JSON under `course/` and `corpus/`
(the source of truth per CLAUDE.md), never `db/corpus.sqlite`.

THE DEFINITION OF "PRACTISED" (this is the contract; read it before changing a number)

An unlocked item I of lesson L is practised when at least one exercise of L **targets** I. An
exercise targets I when I is found in one of three places:

  1. ANSWER SURFACES — the strings the learner must produce, or that are marked correct:
     `answer.text`, `answer.full`, `answer.correct`, every `answer.accept[]`, every `answer.order[]`
     piece, and both members of every `answer.pairs[]` row (a matching grid has no wrong content).
  2. EXPLICIT TARGET MARKUP in the prompt — `<vocab ref="…">`, `<kanji ref="…">`,
     `<grammar ref="…">` naming I's slug. Zero exercises carry such markup today; the branch is here
     so the W20 authoring campaign and a future `tests[]` ref array are measured the moment they land.
  3. A CITED SENTENCE — a slug in `sentence_refs` that resolves in `corpus/sentences/bank.json`, via
     that sentence's own dissection: its tokens' `vocab` slugs (vocab), its `grammar[]` tags (grammar
     — the tag is the grammar `key`, so the slug is `gram:<tag>`), its tokens' `surface` characters
     (kanji).

Three surfaces are deliberately NOT practice, and each exclusion is the point of the gate:

  * DISTRACTORS. `answer.choices` minus `answer.correct` is excluded. A word that appears only as a
    wrong option is being discriminated against incidentally; the item is not about it. (Counting
    distractors is how a coverage number gets inflated without a single new question being asked.)
  * THE `explanation` FIELD. That text is shown after the answer — feedback, not the task. Including
    it moves vocab from 24.2% to 31.1% while adding no retrieval whatsoever.
  * INCIDENTAL JAPANESE IN THE `prompt`. The stem of "Complete: 私＿学生です。" is scaffolding; the
    item targets the particle the learner supplies, not 私 and not 学生. Only markup (2) counts from
    the prompt.

MATCHING, per kind — chosen so that "contains the characters" never passes for "asks about it":

  * vocab — longest-match tiling (MaxMatch) of each Japanese run against the FULL registry surface
    set (`headword`, `kana`, every `forms[].form`); only the tiled forms are credited, never a bare
    substring. Measured cost of the difference: plain containment credits 70 more vocab records than
    tiling, and the extra hits are い inside 寒いですから, か inside だから, 数 inside 数字, 表 inside
    ひょうばん — noise, every one. Tiling also correctly refuses to credit the word 本 for 日本.

    MaxMatch alone is still not enough, and a Fable random sample proved it: les:n4-potencial-02 was
    credited with 線 because its recognition answer ここで写真をとることができません。 segments as
    …でき|ま|せん and せん is 線's kana surface. 増す (kana ます) inside 任せます is the same defect. A
    kana-only surface swallowed by a longer kana run IS the incidental substring this gate claims to
    exclude, so two rules bound it:

      (a) When an exercise's answer string IS one of the sentences it cites (production, recognition
          and sentence_build answers are frequently bank sentences verbatim), that string is not
          tiled at all — the sentence's own token dissection, which is Layer-A ground truth, is the
          only reading of it. A tiler must never overrule a real morphological analysis.
      (b) Otherwise a surface is credited only when it carries at least one kanji, or it is the
          whole Japanese run of that answer, or — being kana-only — its matched span is delimited on
          BOTH sides by a run edge or by a character outside its own kana script. The MaxMatch
          segmentation itself is unchanged; only the crediting is filtered, so the tiling stays
          deterministic. The boundary is per-script, not "any kana": a katakana loanword beside a
          hiragana particle (タクシーで) is delimited, which is how Japanese writes word edges, while
          せん inside できません and ます inside 任せます are not. Collapsing both kana scripts into one
          class instead drops every katakana loanword in the course — 13 of them, measured.

    What (b) still cannot do is split a hiragana word from a hiragana suffix: きれい in きれいです is
    not credited, because nothing short of a morphological analyser can tell it from a substring.
    That is a false ABSENT, and false absents are the safe direction — the item lands on the W20
    work list, where an author sees the existing practice, instead of being silently written off.
  * kanji — plain character containment over the same surfaces. A kanji INSIDE the answer word is
    practice of that kanji: answering 医者 practises 医 and 者. This is the one place where being
    inside a longer string counts, because a kanji has no other unit.
  * grammar — probe segments cut from `forms[].form` + `structure_pattern` by splitting on the
    placeholder marks ～〜…‥ and whitespace and dropping brackets. A segment of 2+ characters matches
    by containment; a ONE-character segment (the particle points: も, の, は) matches only when a
    whole answer string IS that character, because otherwise の would match nearly every Japanese
    sentence in the course. Plus (2) and the cited sentence's grammar tags.

Known judgement calls, stated so the numbers can be argued with:
  * A surface shared by homograph siblings credits every record that spells it. The unlock ledger
    guarantees each sibling is taught by exactly one lesson, so the blast radius is the sibling's own
    lesson, and `course/coverage_exemptions.json` already tracks the known pairs.
  * A conjugated form in an answer (食べました) does not tile onto its dictionary record (食べる).
    Both this gate and the readiness audits under-credit inflected vocab identically; closing it
    needs the conjugation table, which is a different join and a later unit.
  * `sentence_refs` on an exercise is provenance and is NOT required to be displayed
    (`validate_sentence_manifest.py`). Crediting it is the generous reading, taken deliberately: it
    keeps the absent list — the W20 work list — free of items an author can show was already covered.
  * `kana-family` unlocks are counted and reported but not measured; kana practice lives in the kana
    registry, not in exercise answer keys. `conjugation-form` and `phrase` unlocks do not exist yet.

RATCHET. Today's absent counts per (level, kind) are frozen in
`scripts/validate/practice_coverage_baseline.json`. Growth FAILS. Shrinkage prints an advisory
naming the ceiling to lower. A baseline entry matching no (level, kind) in the data is itself a
failure, so the file cannot rot into decoration. A level the baseline does not know is a failure, so
a new course tier must be frozen deliberately.

EXEMPTIONS. `course/practice_exemptions.json` is read here, and its entries are checked to name real
lessons, but it does NOT exempt anything from this rule. That file documents one rule only — the
"renders >=1 retrieval + >=1 production exercise" rule in `validate_exercise_contracts.py`. Its eight
kanji-reinforcement lessons unlock 59 kanji and render no practice at all; those 59 are absent here
and stay in the work list, which is precisely the debt the exemption reasons describe.

OUTPUT. The per-lesson absent list is written to `research/reports/practice_coverage_review.json`
(the W20 campaign's work list), only when its content actually changed, so a validator never dirties
the tree it validates.

Exit 1 on any FAIL.
Usage: validate_practice_coverage.py [--root PATH] [--list] [--write-baseline] [--no-report]
"""
from __future__ import annotations

import argparse
import collections
import json
import re
import sys
import unicodedata
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]

DEFAULT_ROOT = Path(__file__).resolve().parents[2]
BASELINE = Path(__file__).resolve().parent / "practice_coverage_baseline.json"
BASELINE_REL = "scripts/validate/practice_coverage_baseline.json"
REVIEW_REL = "research/reports/practice_coverage_review.json"
LOC = "pt-BR"
MAX_SHOWN = 15

# Floors far below the real counts (322 lessons, 4,076 measured unlocks): growth never trips them,
# but a tree whose course/ or corpus/ was moved, renamed or shadowed fails instead of certifying
# nothing. "Empty input fails" — scripts/validate/README.md.
MIN_LESSONS = 250
MIN_UNLOCKS = 3000
MIN_SENTENCES = 4000

MEASURED_KINDS = ("vocab", "kanji", "grammar")
# Unlock types that teach an item but have no answer-key surface to look for (see the docstring).
UNMEASURED_ITEM_TYPES = ("kana-family", "conjugation-form", "phrase")

# One Japanese run: kana, kanji, halfwidth katakana, 々/〆 and the chōonpu.
JP_RUN_RX = re.compile(r"[぀-ヿ㐀-䶿一-鿿ｦ-ﾟ々〆ー]+")
# A surface with no kanji at all: only such a surface can be swallowed by a longer kana run
# (せん inside できません, ます inside 任せます), so only such a surface needs the boundary rule.
KANA_ONLY_RX = re.compile(r"^[぀-ヿｦ-ﾟー]+$")
HIRAGANA_RX = re.compile(r"[぀-ゟ]")
KATAKANA_RX = re.compile(r"[゠-ヿｦ-ﾟー]")


def kana_script(ch: str) -> str | None:
    """'hira', 'kata', or None for anything that breaks a kana run (kanji, digits, latin, edges).

    The two kana scripts are separate boundaries: a script change is how Japanese delimits a
    katakana loanword, so タクシー beside the particle で is a whole word, while せん inside できません
    is not. Treating all kana as one class would throw away every katakana loanword in the course.
    """
    if HIRAGANA_RX.match(ch):
        return "hira"
    if KATAKANA_RX.match(ch):
        return "kata"
    return None
# Folding used only to ask "is this answer string that cited sentence, verbatim?" — the same
# punctuation set LessonExercises.tsx normAnswer() drops, so a trailing 。 never hides the match.
SENTENCE_FOLD_RX = re.compile(r"[\s　。、・「」『』（）()！？!?]")
# Grammar patterns are written with placeholders: ～ば～ほど, どんなに～ことか, ～(ん)だもの.
PLACEHOLDER_RX = re.compile(r"[～〜…‥\s]+")
BRACKETS = str.maketrans("", "", "()（）[]｛｝{}")
# <vocab ref="…">, <kanji ref="…">, <grammar ref="…"> anywhere in the prompt locale object.
TARGET_REF_RX = re.compile(r'<(?:vocab|kanji|grammar)\s+[^>]*?ref="([^"]+)"')
TOPIC_NUM_RX = re.compile(r"topic-(\d+)")


# --------------------------------------------------------------------------- registries
def load_vocab(root: Path) -> tuple[dict[str, set[str]], int]:
    """surface form -> {slug}, and the longest surface, for the MaxMatch tiler."""
    surfaces: dict[str, set[str]] = collections.defaultdict(set)
    for path in sorted(root.glob("corpus/vocab/*.json")):
        for rec in json.loads(path.read_text(encoding="utf-8")):
            forms = {f for f in (rec.get("headword"), rec.get("kana")) if f}
            forms |= {f["form"] for f in (rec.get("forms") or []) if f.get("form")}
            for form in forms:
                surfaces[form].add(rec["slug"])
    return surfaces, (max((len(f) for f in surfaces), default=0))


def load_kanji(root: Path) -> dict[str, str]:
    out: dict[str, str] = {}
    for path in sorted(root.glob("corpus/kanji/*.json")):
        for rec in json.loads(path.read_text(encoding="utf-8")):
            out[rec["slug"]] = rec["character"]
    return out


def load_grammar(root: Path) -> tuple[dict[str, set[str]], dict[str, str]]:
    """slug -> probe segments, and slug -> pt-BR label (for the review file)."""
    probes: dict[str, set[str]] = {}
    labels: dict[str, str] = {}
    for path in sorted(root.glob("corpus/grammar/*.json")):
        for rec in json.loads(path.read_text(encoding="utf-8")):
            raw = {f["form"] for f in (rec.get("forms") or []) if f.get("form")}
            if rec.get("structure_pattern"):
                raw.add(rec["structure_pattern"])
            segs: set[str] = set()
            for form in raw:
                for seg in PLACEHOLDER_RX.split(form.translate(BRACKETS)):
                    seg = seg.strip()
                    if seg and JP_RUN_RX.fullmatch(seg):
                        segs.add(seg)
            probes[rec["slug"]] = segs
            lab = rec.get("label")
            labels[rec["slug"]] = (lab.get(LOC) if isinstance(lab, dict) else None) or rec.get("key") or ""
    return probes, labels


def fold_sentence(s: str) -> str:
    return SENTENCE_FOLD_RX.sub("", unicodedata.normalize("NFKC", s or ""))


def load_sentences(root: Path) -> dict[str, tuple[set[str], set[str], str, str]]:
    """slug -> (token vocab slugs, gram: slugs from the tags, token surfaces, folded jp)."""
    path = root / "corpus" / "sentences" / "bank.json"
    if not path.exists():
        return {}
    out: dict[str, tuple[set[str], set[str], str, str]] = {}
    for rec in json.loads(path.read_text(encoding="utf-8")):
        tokens = rec.get("tokens") or []
        out[rec["slug"]] = (
            {t["vocab"] for t in tokens if t.get("vocab")},
            {"gram:" + g for g in (rec.get("grammar") or []) if isinstance(g, str)},
            "".join(t.get("surface") or "" for t in tokens),
            fold_sentence(rec.get("jp") or ""),
        )
    return out


def load_vocab_display(root: Path) -> dict[str, str]:
    out: dict[str, str] = {}
    for path in sorted(root.glob("corpus/vocab/*.json")):
        for rec in json.loads(path.read_text(encoding="utf-8")):
            head, kana = rec.get("headword") or "", rec.get("kana") or ""
            out[rec["slug"]] = head if head == kana or not kana else f"{head}（{kana}）"
    return out


def load_exemptions(root: Path, lesson_ids: set[str], fails: list[str]) -> list[str]:
    """Read the exemption file this validator does NOT honour, and prove its entries still resolve."""
    path = root / "course" / "practice_exemptions.json"
    if not path.exists():
        return []
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        fails.append(f"practice_exemptions.json is not valid JSON: {exc}")
        return []
    out: list[str] = []
    for entry in data.get("lessons") or []:
        lid = entry.get("id") if isinstance(entry, dict) else None
        if not lid:
            fails.append(f"practice_exemptions.json: entry {entry!r} has no 'id'")
            continue
        if lid not in lesson_ids:
            fails.append(f"practice_exemptions.json: '{lid}' names no exported lesson — stale entry")
            continue
        out.append(lid)
    return out


# --------------------------------------------------------------------------- matching
def make_tiler(surfaces: dict[str, set[str]], max_len: int):
    """Longest-match (MaxMatch) segmentation, filtered so a kana surface cannot be swallowed.

    The segmentation is pure MaxMatch and always advances by the span it consumed, so the reading of
    a string is deterministic. Crediting is what the filter narrows: a matched surface is credited
    when it carries a kanji, or it IS the whole run, or — kana-only — a non-kana character (or a run
    edge) sits on both sides of its span. Without that last clause できません yields 線 (せん) and
    任せます yields 増す (ます): a real word, incidentally spelled, that no exercise ever asked about.
    """
    def tile(run: str, into: set[str]) -> None:
        i, n = 0, len(run)
        while i < n:
            for length in range(min(max_len, n - i), 0, -1):
                form = run[i:i + length]
                hit = surfaces.get(form)
                if not hit:
                    continue
                if not KANA_ONLY_RX.match(form):
                    into |= hit                                  # carries a kanji: unambiguous
                elif i == 0 and length == n:
                    into |= hit                                  # the answer IS the word
                else:
                    left_ok = i == 0 or kana_script(run[i - 1]) != kana_script(form[0])
                    right_ok = (i + length == n
                                or kana_script(run[i + length]) != kana_script(form[-1]))
                    if left_ok and right_ok:
                        into |= hit
                i += length
                break
            else:
                i += 1
    return tile


def answer_surfaces(answer: object) -> list[str]:
    """Every string of an answer key the learner must produce or that is marked correct.

    `choices` is read ONLY through `correct`: a distractor is not practice of the word it spells.
    """
    out: list[str] = []
    if not isinstance(answer, dict):
        return out
    for key in ("text", "full", "correct"):
        if isinstance(answer.get(key), str):
            out.append(answer[key])
    for key in ("accept", "order"):
        out += [x for x in (answer.get(key) or []) if isinstance(x, str)]
    for pair in (answer.get("pairs") or []):
        if isinstance(pair, list):
            out += [x for x in pair if isinstance(x, str)]
    return out


def lesson_sort_key(path: Path, lesson: dict, level_order: dict[str, int]) -> tuple:
    topic_num = int(m.group(1)) if (m := TOPIC_NUM_RX.search(path.parent.name)) else 0
    return (level_order.get(path.parts[-3], 99), topic_num, lesson.get("order", 0), path.name)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=str(DEFAULT_ROOT), help="tree to validate (default: repo root)")
    ap.add_argument("--list", action="store_true", help="print every FAIL instead of the first 15")
    ap.add_argument("--write-baseline", action="store_true",
                    help=f"re-freeze {BASELINE_REL} from this tree")
    ap.add_argument("--no-report", action="store_true", help=f"do not write {REVIEW_REL}")
    args = ap.parse_args()
    root = Path(args.root).resolve()
    fails: list[str] = []

    manifest_path = root / "course" / "manifest.json"
    if not manifest_path.exists():
        print(f"validate_practice_coverage: FAIL course/manifest.json missing under {root}")
        return 1
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    taught = [c["level"] for c in sorted(manifest["courses"], key=lambda c: c["order"])]
    level_order = {lv: i for i, lv in enumerate(taught)}

    vocab_surfaces, max_surface = load_vocab(root)
    kanji_char = load_kanji(root)
    gram_probes, gram_label = load_grammar(root)
    sentences = load_sentences(root)
    vocab_display = load_vocab_display(root)
    tile = make_tiler(vocab_surfaces, max_surface)

    for name, n, floor in (("vocab surfaces", len(vocab_surfaces), 5000),
                           ("kanji records", len(kanji_char), 1500),
                           ("grammar records", len(gram_probes), 400),
                           ("bank sentences", len(sentences), MIN_SENTENCES)):
        if n < floor:
            fails.append(f"registry '{name}' holds {n} records (floor {floor}) — the export this gate "
                         f"measures against is missing or moved; refusing to certify coverage")

    leaves = sorted(root.glob("course/*/topic-*/lesson-*.json"))
    per: dict[tuple[str, str], list[int]] = collections.defaultdict(lambda: [0, 0])
    per_topic: dict[str, list[int]] = collections.defaultdict(lambda: [0, 0])
    rows: list[dict] = []
    n_lessons = n_teaching = n_exercises = 0
    n_unmeasured = 0
    n_no_exercise_unlocks = 0
    n_answers_dissected = 0
    lesson_ids: set[str] = set()
    ordered: list[tuple[tuple, Path, dict]] = []

    for path in leaves:
        lesson = json.loads(path.read_text(encoding="utf-8"))
        lesson_ids.add(lesson.get("id", path.stem))
        ordered.append((lesson_sort_key(path, lesson, level_order), path, lesson))
    ordered.sort(key=lambda t: t[0])

    for _key, path, lesson in ordered:
        n_lessons += 1
        lid = lesson.get("id", path.stem)
        level = path.parts[-3]
        unlocks: dict[str, list[str]] = collections.defaultdict(list)
        for entry in lesson.get("unlocks") or []:
            utype, ref = entry.get("type"), entry.get("ref")
            if utype in MEASURED_KINDS and isinstance(ref, str):
                unlocks[utype].append(ref)
            elif utype in UNMEASURED_ITEM_TYPES:
                n_unmeasured += 1
        exercises = lesson.get("exercises") or []
        n_exercises += len(exercises)
        if not unlocks:
            continue
        n_teaching += 1
        if not exercises:
            n_no_exercise_unlocks += sum(len(v) for v in unlocks.values())

        # ---- gather the three target surfaces of this lesson's exercises -------------------
        answer_strings: list[str] = []
        marked_refs: set[str] = set()
        cited: set[str] = set()
        tiled: set[str] = set()
        n_dissected = 0
        for ex in exercises:
            mine = answer_surfaces(ex.get("answer"))
            answer_strings += mine
            prompt = ex.get("prompt")
            if prompt is not None:
                marked_refs |= set(TARGET_REF_RX.findall(json.dumps(prompt, ensure_ascii=False)))
            ex_cited = {s for s in (ex.get("sentence_refs") or [])
                        if isinstance(s, str) and s in sentences}
            cited |= ex_cited
            # (a) an answer that IS one of this exercise's cited sentences is read through that
            # sentence's Layer-A token dissection, never re-tiled by this gate's approximation.
            verbatim = {sentences[s][3] for s in ex_cited}
            for s in mine:
                if fold_sentence(s) in verbatim:
                    n_dissected += 1
                    continue
                for run in JP_RUN_RX.findall(s):
                    tile(run, tiled)

        runs: list[str] = []
        for s in answer_strings:
            runs += JP_RUN_RX.findall(s)
        answer_text = "".join(runs)          # kanji + grammar pools: every answer, dissected or not
        whole_answers = set(answer_strings)
        sent_vocab: set[str] = set()
        sent_gram: set[str] = set()
        sent_text = ""
        for sref in cited:
            v, g, surf, _folded = sentences[sref]
            sent_vocab |= v
            sent_gram |= g
            sent_text += surf
        kanji_pool = set(answer_text) | set(sent_text)
        n_answers_dissected += n_dissected

        absent: list[dict[str, str]] = []
        for kind in MEASURED_KINDS:
            for ref in unlocks[kind]:
                if kind == "vocab":
                    known = ref in vocab_display
                    hit = ref in tiled or ref in marked_refs or ref in sent_vocab
                    display = vocab_display.get(ref, "")
                elif kind == "kanji":
                    known = ref in kanji_char
                    hit = (kanji_char.get(ref, "\x00") in kanji_pool) or ref in marked_refs
                    display = kanji_char.get(ref, "")
                else:
                    known = ref in gram_probes
                    hit = ref in marked_refs or ref in sent_gram or any(
                        (len(seg) > 1 and seg in answer_text) or (len(seg) == 1 and seg in whole_answers)
                        for seg in (gram_probes.get(ref) or set()))
                    display = gram_label.get(ref, "")
                if not known:
                    # Duplicates validate_unlock_ledger check A on purpose: an unlock that resolves to
                    # nothing would otherwise leave this gate's denominator silently, and a shrinking
                    # denominator is how a ratchet passes by losing its data.
                    fails.append(f"{lid}: {kind} unlock {ref} resolves to no exported record — it would "
                                 f"vanish from this gate's counts (see validate_unlock_ledger check A)")
                per[(level, kind)][0] += 1
                per_topic[lesson.get("topic") or "?"][0] += 1
                if hit:
                    per[(level, kind)][1] += 1
                    per_topic[lesson.get("topic") or "?"][1] += 1
                else:
                    absent.append({"kind": kind, "ref": ref, "display": display})
        if absent:
            n_unlocked = sum(len(v) for v in unlocks.values())
            rows.append({
                "id": lid,
                "level": level,
                "topic": lesson.get("topic"),
                "path": path.relative_to(root).as_posix(),
                "title": (lesson.get("title") or {}).get(LOC) if isinstance(lesson.get("title"), dict)
                         else lesson.get("title"),
                "exercises": len(exercises),
                "unlocked": n_unlocked,
                "practised": n_unlocked - len(absent),
                "absent_count": len(absent),
                "absent": absent,
            })

    if n_lessons < MIN_LESSONS:
        fails.append(f"only {n_lessons} lesson leaves under course/*/topic-*/lesson-*.json "
                     f"(floor {MIN_LESSONS}) — an empty or moved course cannot pass this gate")
    total_unlocked = sum(u for u, _p in per.values())
    total_practised = sum(p for _u, p in per.values())
    if total_unlocked < MIN_UNLOCKS:
        fails.append(f"only {total_unlocked} measured unlocks (floor {MIN_UNLOCKS}) — nothing to gate")
    if n_teaching == 0 or n_exercises == 0:
        fails.append(f"{n_teaching} teaching lessons and {n_exercises} exercises — refusing to certify")

    exempt = load_exemptions(root, lesson_ids, fails)

    # ---- the ratchet ------------------------------------------------------------------
    current = {lv: {k: per[(lv, k)][0] - per[(lv, k)][1] for k in MEASURED_KINDS if (lv, k) in per}
               for lv in sorted({lv for lv, _k in per}, key=lambda lv: level_order.get(lv, 99))}
    unlocked_now = {lv: {k: per[(lv, k)][0] for k in MEASURED_KINDS if (lv, k) in per}
                    for lv in current}

    if args.write_baseline:
        BASELINE.write_text(json.dumps({
            "_why": "Frozen ceilings for validate_practice_coverage.py: the number of items each "
                    "course level unlocks that its own lesson never asks about. These are known "
                    "CONTENT debt (W04/W20 in research/reports/APP_PLAN.md), not passing checks. A "
                    "count may SHRINK freely — lower the ceiling in the same commit that authors the "
                    "practice — but GROWTH FAILS, because a lesson that gains an unlock without "
                    "gaining a question is exactly the regression this gate exists to catch. An entry "
                    "matching no (level, kind) in the data is itself a failure, so this file cannot "
                    "rot into decoration. `unlocked` is context, not a gated number.",
            "_definition": "See the module docstring of scripts/validate/validate_practice_coverage.py. "
                           "Changing the matching rules invalidates these ceilings on purpose: "
                           "re-freeze with --write-baseline in the same commit.",
            "absent": current,
            "unlocked": unlocked_now,
        }, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(f"  wrote {BASELINE_REL} (frozen at {total_unlocked - total_practised} absent)")

    drops: list[str] = []
    if not BASELINE.exists():
        fails.append(f"{BASELINE_REL} missing — re-freeze it with --write-baseline")
    else:
        base = json.loads(BASELINE.read_text(encoding="utf-8")).get("absent") or {}
        for level, kinds in current.items():
            for kind, now in kinds.items():
                was = (base.get(level) or {}).get(kind)
                if was is None:
                    fails.append(f"{BASELINE_REL}: no ceiling for ({level}, {kind}) — a new level or "
                                 f"unlock kind must be frozen deliberately")
                elif now > was:
                    fails.append(f"practice debt GREW: ({level}, {kind}) absent {was} -> {now}")
                elif now < was:
                    drops.append(f"({level}, {kind}) {was} -> {now}")
        for level, kinds in base.items():
            for kind, was in (kinds or {}).items():
                if kind not in current.get(level, {}):
                    fails.append(f"{BASELINE_REL}: ceiling ({level}, {kind}) = {was} matches nothing in "
                                 f"the course — stale entry")

    # ---- the W20 work list --------------------------------------------------------------
    if not args.no_report:
        payload = json.dumps({
            "why": "Every item a lesson unlocks that the same lesson's own exercises never ask about "
                   "— the per-item practice debt behind APP_PLAN W04, and the work list the W20 "
                   "per-item practice campaign consumes. Regenerated by "
                   "scripts/validate/validate_practice_coverage.py; the counts are ratcheted in "
                   + BASELINE_REL + " and may not grow.",
            "definition": "An unlocked item is practised when an exercise of its own lesson TARGETS "
                          "it: the item appears in an answer surface (text/full/correct/accept/order/"
                          "pairs), in <vocab|kanji|grammar ref> markup in the prompt, or in a sentence "
                          "the exercise cites via sentence_refs (token vocab slugs, grammar tags, "
                          "token surfaces for kanji). Distractors, the explanation field and incidental "
                          "Japanese in the prompt do not count. Vocab matches by longest-match tiling, "
                          "kanji by character containment, grammar by pattern-segment match.",
            "generated_by": "scripts/validate/validate_practice_coverage.py",
            "order": "course order (level, topic number, lesson order); re-sort by absent_count for "
                     "worst-first",
            "summary": {
                "unlocked": total_unlocked,
                "practised": total_practised,
                "absent": total_unlocked - total_practised,
                "lessons_with_absent_items": len(rows),
                "by_level_kind": {f"{lv}|{k}": {"unlocked": per[(lv, k)][0],
                                                "practised": per[(lv, k)][1],
                                                "absent": per[(lv, k)][0] - per[(lv, k)][1]}
                                  for lv, k in sorted(per, key=lambda t: (level_order.get(t[0], 99), t[1]))},
            },
            "count": len(rows),
            "lessons": rows,
        }, ensure_ascii=False, indent=2) + "\n"
        report = root / REVIEW_REL
        report.parent.mkdir(parents=True, exist_ok=True)
        # a validator must not dirty the tree it validates: write only on real change
        if not report.exists() or report.read_text(encoding="utf-8") != payload:
            report.write_text(payload, encoding="utf-8")

    # ---- report -------------------------------------------------------------------------
    print(f"  {'level':7s} {'kind':9s} {'unlocked':>9s} {'practised':>10s} {'absent':>7s}   share")
    for level, kind in sorted(per, key=lambda t: (level_order.get(t[0], 99), t[1])):
        u, p = per[(level, kind)]
        print(f"  {level:7s} {kind:9s} {u:9d} {p:10d} {u - p:7d}   {100 * p / u:5.1f}%")
    print(f"  {'TOTAL':7s} {'':9s} {total_unlocked:9d} {total_practised:10d} "
          f"{total_unlocked - total_practised:7d}   "
          f"{100 * total_practised / max(total_unlocked, 1):5.1f}%")

    worst = sorted(per_topic.items(), key=lambda kv: (kv[1][1] - kv[1][0], kv[0]))[:3]
    for topic, (u, p) in worst:
        print(f"  ADVISORY: {topic} is the thinnest — {u - p} of {u} unlocked items never asked "
              f"({100 * p / max(u, 1):.1f}% practised)")
    if exempt:
        held = sum(r["absent_count"] for r in rows if r["id"] in set(exempt))
        print(f"  ADVISORY: {len(exempt)} lessons carry a course/practice_exemptions.json entry; that "
              f"file exempts the render-a-retrieval-and-production rule only, so their {held} unlocked "
              f"items are counted absent here")
    if n_no_exercise_unlocks:
        print(f"  ADVISORY: {n_no_exercise_unlocks} items are unlocked by lessons with zero exercises")
    print(f"  ADVISORY: {n_answers_dissected} answer strings are one of their own exercise's cited "
          f"sentences verbatim and were read through that sentence's token dissection, not tiled")
    if n_unmeasured:
        print(f"  ADVISORY: {n_unmeasured} {'/'.join(UNMEASURED_ITEM_TYPES)} unlocks are reported but "
              f"not measured — they have no answer-key surface (see the docstring)")
    for drop in drops:
        print(f"  ADVISORY: debt shrank — {drop}; lower the ceiling with --write-baseline")

    shown = fails if args.list else fails[:MAX_SHOWN]
    for line in shown:
        print(f"  FAIL {line}")
    if len(fails) > len(shown):
        print(f"  … and {len(fails) - len(shown)} more (--list for all)")

    print(f"\nvalidate_practice_coverage: {n_lessons} lessons ({n_teaching} teaching), {n_exercises} "
          f"exercises, {total_unlocked} unlocked items | {total_practised} practised, "
          f"{total_unlocked - total_practised} absent in {len(rows)} lessons"
          f"{'' if args.no_report else ' -> ' + REVIEW_REL} | {len(fails)} FAIL")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
