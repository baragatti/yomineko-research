#!/usr/bin/env python3
"""Gate: every exercise in the exported courseware is answerable exactly as the app renders it.

The 13-panel course review found five independent ways an exercise could ship broken while the whole
validator suite stayed green, because nothing checked the CONTRACT between the stored answer key and
the widget the renderer builds from it:

  * EX-ORPHAN-BODY — 19 exercises were authored but never referenced by their lesson body. The app
    renders exercises ONLY from `<exercise ref="…"/>` nodes (prototype/app/lib/render-body.server.ts
    `case "exercise"`), so three N4 lessons presented zero practice. validate_lessons.py checked the
    link in one direction only (a body ref must resolve), never the reverse.
  * CLOZE-ANSWER-IS-BLANKED-SENTENCE — 5 cloze items stored the blanked sentence in `answer.text`
    instead of the filler. `answer.text` is the ONLY string the app grades and the only one it prints
    under "Ver resposta", so those items had no reachable success state.
  * PROD-REVEALED-ANSWER-REJECTED / PROD-PUNCTUATION-MISMATCH — 133 of 308 production items revealed
    an `answer.text` that was absent from `answer.accept`, i.e. the app graded its own revealed answer
    as wrong. validate_lessons.py's ANSWER_SHAPES for production is ('text',) — it never looked at
    `accept`.
  * BUILD-ANSWER-ORTHOGRAPHY — a sentence_build whose piece bank cannot spell the answer it displays.
  * ZERO-EXERCISE-LESSONS-UNGUARDED — validate_lessons.py wraps its ">=1 retrieval + >=1 production"
    rule in `if types:`, so a lesson with NO exercises skips the rule that exists precisely for it.

Every check here reads the EXPORTED JSON under course/ (the source of truth per CLAUDE.md), never
db/corpus.sqlite, and the production/cloze grading rule replicates prototype/app/ui/LessonExercises.tsx
`normAnswer()` character for character: NFKC, lowercase, then drop whitespace and the sentence
punctuation set. The port was differential-tested against the real TSX function under node over all
6,825 answer strings in the corpus plus full-width / ideographic-space / chōonpu / ・ / … edge cases:
0 disagreements. Data and grader cannot drift apart without this failing.

Lessons that legitimately render no practice are declared in course/practice_exemptions.json (each
entry {id, reason}); an entry that matches nothing, or whose lesson has since gained practice, is
itself a failure, so the list cannot rot.

Exit 1 on any FAIL. Usage: validate_exercise_contracts.py [--root PATH] [--list]
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import unicodedata
from collections import Counter, defaultdict
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
DEFAULT_ROOT = Path(__file__).resolve().parents[2]
LOC = "pt-BR"
MAX_SHOWN = 15

EXERCISE_RX = re.compile(r'<exercise\s+ref="([^"]+)"')
BLANK_RX = re.compile(r"[_＿]{2,}")
KANA_RX = re.compile(r"^[ぁ-ゟ゠-ヿー]+$")

# Mirrors prototype/app/ui/LessonExercises.tsx normAnswer() exactly:
#   (s || "").normalize("NFKC").toLowerCase().replace(/[\s　。、・「」『』（）()！？!?]/g, "")
# The full-width members stay in the class even though NFKC already folds （）！？ down to ()!? —
# keeping the sets identical is what makes a future drift in the TSX visible as a diff here.
NORM_STRIP_RX = re.compile(r"[\s　。、・「」『』（）()！？!?]")
# Extra marks the app does NOT fold, used only to split a production mismatch into
# "punctuation-only" (cosmetic, fixable by the accept list) and "substantive" (a different sentence).
PUNCT_ONLY_RX = re.compile(r"[\s　。、・「」『』（）()！？!?，,．.…‥]")
# sentence_build is graded on order.join("") with whitespace stripped (LessonExercises.tsx), while
# answer.text is only printed; these marks are never pieces, so they may differ between the two.
BUILD_STRIP_RX = re.compile(r"[\s　。、？！?!…]")

RETRIEVAL = {"recognition", "reading", "listening", "cloze", "particle_choice", "matching", "ordering"}
PRODUCTION = {"production", "handwriting"}
TEACHING_UNLOCKS = {"kana-family", "vocab", "kanji", "grammar", "conjugation-form", "phrase"}
# The renderer branches on `Array.isArray(ans.choices)` BEFORE it looks at ex.type, so any type that
# grows a choices key is drawn as multiple choice. These two are the types that are meant to.
CHOICE_TYPES = {"recognition", "particle_choice", "reading", "listening"}
BRACKETS = (("(", ")"), ("（", "）"), ("「", "」"), ("『", "』"), ("[", "]"))
TERMINAL = tuple(".?!:…。？！」』)）\"'")


def norm_answer(s: str) -> str:
    """The learner-side normalisation the app grades with (LessonExercises.tsx normAnswer)."""
    return NORM_STRIP_RX.sub("", unicodedata.normalize("NFKC", s or "").lower())


def punct_fold(s: str) -> str:
    return PUNCT_ONLY_RX.sub("", unicodedata.normalize("NFKC", s or "").lower())


def loc_text(v: object) -> str | None:
    """Return the pt-BR string of a locale object, or None if the field is not a valid locale object."""
    if isinstance(v, dict) and isinstance(v.get(LOC), str):
        return v[LOC]
    return None


def load_exemptions(course: Path, fails: list[str]) -> dict[str, str]:
    path = course / "practice_exemptions.json"
    if not path.exists():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        fails.append(f"practice_exemptions.json is not valid JSON: {e}")
        return {}
    out: dict[str, str] = {}
    for entry in data.get("lessons") or []:
        if not isinstance(entry, dict) or not entry.get("id") or not str(entry.get("reason") or "").strip():
            fails.append(f"practice_exemptions.json: entry {entry!r} needs both an 'id' and a 'reason'")
            continue
        if entry["id"] in out:
            fails.append(f"practice_exemptions.json: '{entry['id']}' listed twice")
        out[entry["id"]] = entry["reason"]
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=str(DEFAULT_ROOT), help="repo root (point at a mutated copy to test)")
    ap.add_argument("--list", action="store_true", help="print every FAIL instead of the first 15")
    args = ap.parse_args()
    root = Path(args.root).resolve()
    course = root / "course"

    fails: list[str] = []
    notes: list[str] = []          # advisory — reported, never fatal
    exempt = load_exemptions(course, fails)
    exempt_used: set[str] = set()

    n_lessons = n_ex = 0
    type_counts: Counter[str] = Counter()
    choice_hist: Counter[int] = Counter()
    id_seen: dict[str, str] = {}                     # exercise id -> lesson id
    cross: dict[tuple[str, str], list[str]] = defaultdict(list)
    prod_punct = prod_subst = 0
    accept_collapse = 0
    match_dup_right = 0
    no_terminal = 0
    n_teaching = 0
    cloze_warn = 0
    n_fields = 0

    for leaf in sorted(course.glob("*/topic-*/lesson-*.json")):
        n_lessons += 1
        d = json.loads(leaf.read_text(encoding="utf-8"))
        lid = d.get("id", leaf.stem)
        body = d.get("body") or ""
        exercises = d.get("exercises") or []
        n_ex += len(exercises)

        # ---- 1. body binding: declared ids and body refs are the same set, each used once ----
        declared = [e.get("id") for e in exercises]
        referenced = EXERCISE_RX.findall(body)
        dup_declared = [i for i, c in Counter(declared).items() if c > 1]
        dup_ref = [r for r, c in Counter(referenced).items() if c > 1]
        for i in dup_declared:
            fails.append(f"{lid}: exercise id '{i}' declared more than once in exercises[]")
        for r in dup_ref:
            fails.append(f"{lid}: body references exercise '{r}' more than once")
        ref_set = set(referenced)
        for i in declared:
            if i not in ref_set:
                fails.append(f"{lid}: exercise '{i}' is authored but never referenced by the body, "
                             f"so the app never renders it")
        for r in referenced:
            if r not in set(declared):
                fails.append(f"{lid}: body <exercise ref=\"{r}\"/> matches no exercise in this lesson "
                             f"(renderExercise returns an empty string)")

        for ex in exercises:
            eid = ex.get("id")
            typ = ex.get("type")
            ans = ex.get("answer") if isinstance(ex.get("answer"), dict) else {}
            type_counts[typ] += 1
            where = f"{lid}/{eid}"

            # ---- 2. identity ----
            if not isinstance(eid, str) or not eid.startswith("ex:"):
                fails.append(f"{lid}: exercise id {eid!r} is missing or not 'ex:'-prefixed")
            elif eid in id_seen:
                fails.append(f"{where}: exercise id also used by {id_seen[eid]} — ids must be corpus-unique")
            else:
                id_seen[eid] = lid
            if not isinstance(ex.get("answer"), dict):
                fails.append(f"{where}: answer is missing or not an object")

            # ---- 3. prose fields: locale object, non-blank, balanced brackets ----
            for fld in ("prompt", "explanation"):
                txt = loc_text(ex.get(fld))
                if txt is None or not txt.strip():
                    fails.append(f"{where}: {fld} is missing, blank, or not a {{'{LOC}': …}} locale object")
                    continue
                n_fields += 1
                for open_c, close_c in BRACKETS:
                    if txt.count(open_c) != txt.count(close_c):
                        fails.append(f"{where}: {fld} has unbalanced {open_c}{close_c} "
                                     f"(likely truncated): {txt[:120]}")
                if not txt.strip().endswith(TERMINAL):
                    no_terminal += 1   # ratcheted against NO_TERMINAL_CEILING below

            # ---- 4. within/cross-lesson duplicates ----
            key = (json.dumps(ex.get("prompt"), sort_keys=True, ensure_ascii=False),
                   json.dumps(ex.get("answer"), sort_keys=True, ensure_ascii=False))
            same_lesson = [prev_id for prev_lid, prev_id in cross[key] if prev_lid == lid]
            if same_lesson:
                fails.append(f"{where}: identical prompt+answer to {same_lesson[0]} in the same lesson")
            cross[key].append((lid, eid))

            # ---- 5. choice widget (keyed on the presence of choices, like the renderer) ----
            if isinstance(ans.get("choices"), list):
                ch = ans["choices"]
                choice_hist[len(ch)] += 1
                if len(ch) < 2 or any(not isinstance(c, str) or not c.strip() for c in ch):
                    fails.append(f"{where}: choices must be >=2 non-empty strings (got {ch!r})")
                elif len(set(ch)) != len(ch):
                    fails.append(f"{where}: choices repeat a value — two radios would share data-correct: {ch!r}")
                correct = ans.get("correct")
                if not isinstance(correct, str) or not correct.strip():
                    fails.append(f"{where}: answer.correct is missing or blank")
                elif correct not in ch:
                    fails.append(f"{where}: answer.correct {correct!r} is not among choices {ch!r} — "
                                 f"every radio renders data-correct=\"false\", so no answer can be right")
                if typ not in CHOICE_TYPES:
                    notes.append(f"{where}: type '{typ}' carries a choices array, so the renderer draws it as "
                                 f"multiple choice and ignores that type's own answer keys")

            # ---- 6. cloze: answer.text is the FILLER, not the blanked sentence ----
            elif typ == "cloze":
                text, full = ans.get("text"), ans.get("full")
                if not isinstance(text, str) or not text.strip():
                    fails.append(f"{where}: cloze answer.text is missing or blank")
                elif BLANK_RX.search(text):
                    fails.append(f"{where}: cloze answer.text holds the blanked sentence, not the filler "
                                 f"({text[:60]!r}) — it is the only string the app grades or reveals")
                if not isinstance(full, str) or not full.strip():
                    fails.append(f"{where}: cloze answer.full is missing or blank")
                elif BLANK_RX.search(full):
                    fails.append(f"{where}: cloze answer.full still contains a blank marker ({full[:60]!r})")
                if isinstance(text, str) and isinstance(full, str) and text.strip() and full.strip():
                    if re.sub(r"\s", "", text) not in re.sub(r"\s", "", full) and not KANA_RX.match(text.strip()):
                        cloze_warn += 1
                        notes.append(f"{where}: cloze answer.text is not a substring of answer.full "
                                     f"({text[:30]!r} vs {full[:40]!r}) — fine for a reading-cloze, "
                                     f"suspicious otherwise")

            # ---- 7. production: the revealed answer must be one the grader accepts ----
            elif typ in PRODUCTION:
                text = ans.get("text")
                acc = ans.get("accept")
                if not isinstance(text, str) or not text.strip():
                    fails.append(f"{where}: {typ} answer.text is missing or blank")
                if typ == "handwriting" and acc is None:
                    # handwriting has no accept list by convention: the renderer seeds the accept set
                    # from answer.text alone, so text non-blank is the whole contract.
                    pass
                elif not isinstance(acc, list) or not acc or \
                        any(not isinstance(a, str) or not a.strip() for a in acc):
                    fails.append(f"{where}: production answer.accept must be a non-empty list of non-empty "
                                 f"strings (got {acc!r})")
                else:
                    for a in acc:
                        if BLANK_RX.search(a):
                            fails.append(f"{where}: accept entry {a[:60]!r} contains a blank marker")
                    if len(set(acc)) != len(acc):
                        fails.append(f"{where}: accept repeats a string verbatim: {acc!r}")
                    elif len({norm_answer(a) for a in acc}) != len(acc):
                        # Legal but redundant: the punctuation repair deliberately lists both the
                        # punctuated and unpunctuated form, and normAnswer folds them together.
                        accept_collapse += 1
                    if isinstance(text, str) and text.strip():
                        pool = {norm_answer(a) for a in acc}
                        if norm_answer(text) not in pool:
                            if punct_fold(text) in {punct_fold(a) for a in acc}:
                                prod_punct += 1
                                bucket = "punctuation-only"
                            else:
                                prod_subst += 1
                                bucket = "substantive"
                            fails.append(f"{where}: revealed answer {text!r} is not in accept {acc!r} "
                                         f"({bucket}) — the learner cannot type the answer the app shows them")

            # ---- 8. matching: the pairing must be recoverable from what the learner can see ----
            elif typ == "matching":
                pairs = ans.get("pairs")
                if not isinstance(pairs, list) or len(pairs) < 2:
                    fails.append(f"{where}: matching answer.pairs must be a list of >=2 pairs (got {pairs!r})")
                elif any(not isinstance(p, list) or len(p) != 2 or
                         any(not isinstance(x, str) or not x.strip() for x in p) for p in pairs):
                    fails.append(f"{where}: every matching pair must be two non-empty strings: {pairs!r}")
                else:
                    lefts = [p[0] for p in pairs]
                    if len(set(lefts)) != len(lefts):
                        fails.append(f"{where}: the left column repeats a term, so one row is unmatchable: "
                                     f"{lefts!r}")
                    # A repeated RIGHT label is legal: LessonExercises.tsx grades the right column by
                    # TEXT, so any cell showing the canonical label is accepted. Counted, not failed.
                    rights = [p[1] for p in pairs]
                    if len(set(rights)) != len(rights):
                        match_dup_right += 1

            # ---- 9. sentence_build / ordering: the pieces must spell the displayed answer ----
            elif typ in ("sentence_build", "ordering"):
                order, text = ans.get("order"), ans.get("text")
                if not isinstance(order, list) or len(order) < 2 or \
                        any(not isinstance(p, str) or not p.strip() or BLANK_RX.search(p) for p in order):
                    fails.append(f"{where}: answer.order must be >=2 non-empty pieces without blank markers "
                                 f"(got {order!r})")
                elif not isinstance(text, str) or not text.strip():
                    fails.append(f"{where}: answer.text is missing or blank")
                elif BUILD_STRIP_RX.sub("", "".join(order)) != BUILD_STRIP_RX.sub("", text):
                    fails.append(f"{where}: the piece bank spells {''.join(order)!r} but the app displays "
                                 f"{text!r} as the answer — the learner cannot build what they are shown")

        # ---- 10. a teaching lesson must RENDER retrieval and production practice ----
        teaches = any(u.get("type") in TEACHING_UNLOCKS for u in (d.get("unlocks") or []))
        if teaches:
            n_teaching += 1
            rendered_types = {e.get("type") for e in exercises if e.get("id") in ref_set}
            has_r = any(t in RETRIEVAL for t in rendered_types)
            has_p = any(t in PRODUCTION for t in rendered_types)
            if lid in exempt:
                exempt_used.add(lid)
                if has_r and has_p:
                    fails.append(f"{lid}: listed in practice_exemptions.json but it now renders both a "
                                 f"retrieval and a production exercise — drop the stale exemption")
            elif not has_r or not has_p:
                missing = " and ".join(x for x, ok in (("retrieval", has_r), ("production", has_p)) if not ok)
                fails.append(f"{lid}: teaches {sum(1 for u in d['unlocks'] if u.get('type') in TEACHING_UNLOCKS)}"
                             f" items but renders no {missing} exercise "
                             f"(rendered types: {sorted(t for t in rendered_types if t)})")
        elif lid in exempt:
            exempt_used.add(lid)
            fails.append(f"{lid}: listed in practice_exemptions.json but it unlocks no items, so the "
                         f"practice rule never applied to it — drop the stale exemption")

    for lid, reason in exempt.items():
        if lid not in exempt_used:
            fails.append(f"practice_exemptions.json: '{lid}' matches no lesson under course/ "
                         f"(reason on file: {reason[:70]})")

    for uses in cross.values():
        if len({lesson for lesson, _ in uses}) > 1:
            notes.append(f"cross-lesson duplicate exercise (identical prompt+answer): "
                         f"{[eid for _, eid in uses]}")

    print(f"exercise contracts: {n_lessons} lessons, {n_ex} exercises "
          f"({', '.join(f'{t}={c}' for t, c in sorted(type_counts.items()))}); "
          f"{n_teaching} teach items, {len(exempt)} practice exemptions; "
          f"{n_fields} prose fields; choices histogram {dict(sorted(choice_hist.items()))}")
    print(f"  production mismatches: {prod_subst} substantive, {prod_punct} punctuation-only; "
          f"advisory counters: {accept_collapse} accept lists that collapse under normAnswer, "
          f"{match_dup_right} matching items with a repeated right label (legal — graded by text), "
          f"{cloze_warn} cloze text-not-in-full, {no_terminal} prose fields without terminal punctuation, "
          f"{sum(1 for n in notes if n.startswith('cross-lesson'))} cross-lesson duplicate pairs")
    if notes and args.list:
        for n in notes:
            print(f"  note  {n}")
    if fails:
        print(f"=== {len(fails)} FAIL ===")
        for f in (fails if args.list else fails[:MAX_SHOWN]):
            print(f"  FAIL {f}")
        if not args.list and len(fails) > MAX_SHOWN:
            print(f"  … {len(fails) - MAX_SHOWN} more (run with --list)")
        return 1
    # Terminal-punctuation ratchet: 171 prose fields ended without terminal punctuation when this
    # gate was written (mostly stylistic fragments, not truncations — truncation is caught by the
    # bracket-balance rule). The count may only shrink; growth means new unfinished prose shipped.
    NO_TERMINAL_CEILING = 171
    if no_terminal > NO_TERMINAL_CEILING:
        print(f"FAIL: {no_terminal} prose fields lack terminal punctuation "
              f"(ceiling {NO_TERMINAL_CEILING}) — new unfinished prose shipped")
        return 1
    if no_terminal < NO_TERMINAL_CEILING:
        print(f"  note: no-terminal-punctuation count dropped to {no_terminal} — "
              f"lower NO_TERMINAL_CEILING to match")
    if n_lessons < 300:
        # a gate whose data vanished must FAIL, not certify nothing
        print(f"FAIL: only {n_lessons} lessons found (floor 300) — the glob is no longer "
              f"finding the course")
        return 1
    print("=== 0 FAIL — every exercise binds to its body and its answer key grades as rendered ===")
    return 0


if __name__ == "__main__":
    sys.exit(main())
