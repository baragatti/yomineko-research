#!/usr/bin/env python3
"""W28/W26 — a card that cannot be shown or graded must not ship.

WHY THIS EXISTS
---------------
`validate_srs_decks.py` proves the card SET is right: the deck registry is respected, filing follows
the lesson's level, no item is enrolled twice. It says nothing about whether a card has any content,
because until W27 none of them did — `srs.introduces_cards[]` is derived from the unlock ledger and
carries a deck, an item and a list of kinds. For `recognition`, `cloze`, `handwriting` and
`listening` that is enough: the app renders the record the card names. For `production` it is not.
The learner is shown a pt-BR cue and has to write Japanese, so the cue and the accepted answers ARE
the card, and 2,951 vocabulary production cards shipped without either (G1 of
`research/reports/readiness/srs_fsrs.md`). W26 declared this gate and left it pending; W27 authored
the content it gates. `design/srs_design.md` §8 is the schema.

WHAT IT ASSERTS
---------------
Over the EXPORTED course tree (`course/**/lesson-*.json`), never the DB:

  A  Every card's `item` resolves to a live record in the registry its namespace names, and that
     record is not deprecated. A deprecated address is the failure nobody sees: the card still
     enrols, the scheduler still queues it, and the review screen has nothing to draw.
     `corpus/vocab_redirects.json`, `corpus/grammar_deprecated.json` and
     `corpus/families_deprecated.json` are the retirement ledgers; a card may not name a key in one.
  B  Every `production` card on a vocabulary item carries a `production_key` with a non-empty
     `prompt["pt-BR"]`. Ratcheted per namespace, so grammar/kanji/kana production cards (W28 and
     later) are held at today's counts and may only shrink — a NEW unkeyed vocabulary card fails.
  C  Where a key exists, its `accept` set contains the record's headword or its kana, and nothing
     outside that record's `forms[]`. Both halves matter and they fail differently: a set without
     the headword or the kana grades the ONE answer the learner is most likely to write as wrong,
     and a set with a surface that belongs to another entry grades a different word as right. NFKC
     twins count as the form they fold to (`5日` for `５日`, `FAX` for `ＦＡＸ`): those are the same
     surface typed on a different keyboard, and the speak bank already treats them so.
  D  A `production_key` may only sit on a card whose `card_types` contains `production`, and only
     one per card. A key on a recognition-only card is content nothing renders.
  E  Structural: `prompt` is a locale object whose keys are a subset of the declared locales and
     which carries `pt-BR` (design/i18n.md R5); `sense_index`, when present, points at a real sense
     of the record; `accept` has no duplicates and no blank entries.
  F  (W28) Where a card carries an `example`: the sentence is in the bank; `cloze.answer` is exactly
     `jp[start:end]` (a drifted sentence is caught, not blanked wrong); both ends sit on C-unit token
     boundaries; the span holds the item (the card's own vocab token, the kanji's character, or for
     grammar a form of the point or a sentence tagged with it); the sentence is not graded above the
     lesson unless the lesson renders it; a kana family card carries none. Cards with no example
     are ratcheted per namespace (NO_EXAMPLE_RATCHET). design/srs_design.md §9.

Empty input FAILS (scripts/validate/README.md, Conventions): a run that found no lesson, no card or
no production card has certified nothing, and the floors sit well below today's counts.

Exit 0 = OK. Exit 1 = FAIL, listing up to 20 offenders per check with a one-line reason each.

PLANT PROOF (recorded 2026-09-09, per scripts/validate/README.md)
------------------------------------------------------------------
Run on a COPY of the tree (the validator is copied into the fixture beside its own `corpus/` and
`course/`, because it resolves ROOT from its own path — a validator left in the repo would read the
repo and pass on a planted fixture). Verbatim, one line per plant:

  control          exit=0  [OK] 4136 card(s) over 322 lesson(s); 2951 production key(s) checked

  1-no-key         exit=1  ratchet: vocab: 1 production card(s) with no answer key, ratchet is 0 -
                           a new unkeyed card is a regression
  2-blank-prompt   exit=1  les:n5-perguntas-01 / vocab:1581310: empty prompt - the learner is shown
                           nothing to answer
  3-no-head        exit=1  les:n5-perguntas-01 / vocab:1581310: accepts neither the headword '側'
                           nor the kana 'がわ' (['ぬ'])
  4-alien          exit=1  les:n5-perguntas-01 / vocab:1581310: accepts ['月'], which is not a form
                           of 側/がわ
  5-ghost          exit=1  les:n5-perguntas-01 / vocab:9999999: does not resolve to a record in
                           corpus/vocab
  6-retired        exit=1  les:n5-perguntas-01 / vocab:1551240: names a retired address (a
                           redirect/deprecation ledger carries it), so the card renders nothing
  7-wrong-kind     exit=1  les:n5-perguntas-01 / gram:gp-10: carries a production_key but
                           card_types are ['recognition'] - nothing renders it
  8-bad-sense      exit=1  les:n5-perguntas-01 / vocab:1581310: sense_index 99 names no sense of the
                           record (2 sense(s))
  9-dup            exit=1  les:n5-perguntas-01 / vocab:1581310: accept carries a duplicate
  10-bare-prompt   exit=1  les:n5-perguntas-01 / vocab:1581310: prompt is not a locale object (str)
  11-empty-tree    exit=1  [FAIL] 0 lesson leaf/leaves under <fixture>/course, floor is 300

Plant 1 is caught by the RATCHET rather than by a per-card message, which is the design: a card with
no key is not a defect in general (1,185 grammar/kanji/kana cards have none and are held), it is a
defect when the count for that namespace grows.

PLANT PROOF, check F (recorded 2026-09-23, W28; same method, fresh fixture per plant):

  control          exit=0  [OK] 4136 card(s) over 322 lesson(s); 2951 production key(s) checked;
                           2242 example(s) checked
  F1-no-example    exit=1  ratchet: vocab: 1696 card(s) with no example, ratchet is 1695
  F2-ghost         exit=1  les:n3-conectores-01 / vocab:1013980: example sentence 'sent:nope' is not
                           in the bank
  F3-drift         exit=1  ... cloze answer 'X' is not jp[0:7] ('アイスクリーム'): the sentence drifted
  F4-cut-token     exit=1  ... cloze span 1-7 ('イスクリーム') cuts through a token
  F5-wrong-token   exit=1  ... cloze span 'を' does not hold the card's own token
  F6-kanji-off     exit=1  les:n3-conectores-01 / kanji:定: cloze span 'が' does not carry the character
  F7-gram-off      exit=1  les:n3-conectores-01 / gram:n3-sore-to: cloze span '明日' is not a form of
                           the point and the sentence is not tagged
  F8-above-level   exit=1  les:n5-desu-wa-01 / vocab:1223615: example sentence is graded n1, above
                           the lesson's n5, and the lesson does not render it
  F9-kana-example  exit=1  les:pre-n5-hiragana-01 / kana:hiragana-a: a kana family card carries an
                           example: five glyphs, not a word

W29 (2026-09-23): check C has a kana branch (a glyph key accepts exactly its `char`), the kana
unkeyed ratchet is 0 and kana cards leave the no-example ratchet. Plant-proved with the deck and
ledger changes, 20/20 caught: research/reports/w29_apply_report.md §3.

Usage: validate_card_content.py [--root PATH] [--all]
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import unicodedata
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]

REPO = Path(__file__).resolve().parents[2]
MAX_REPORT = 20
# Floors: today's tree carries 322 lessons, 4,137 cards and 2,951 production keys. Empty input must
# fail rather than certify nothing; the floors sit far enough below to survive normal growth and
# far enough above zero to catch a tree that did not load.
MIN_LESSONS, MIN_CARDS, MIN_KEYS = 300, 3_500, 2_500
LOCALES = {"pt-BR", "en"}
# Per-namespace ratchet for check B: production cards that carry no key yet. Vocabulary is at 0 and
# must stay there; grammar, kanji and kana are W28-and-later work and are held at today's counts.
# A number may only shrink. Raising one is a decision, not a fix.
# W29: kana 57 -> 0. Every kana card is a glyph card with a derived key (repairs/kana_cards.json).
UNKEYED_RATCHET = {"vocab": 0, "gram": 494, "kanji": 634, "kana": 0}
# W28, check F. Cards with no `example`, per namespace, as derived on 2026-09-23. Most are not a
# defect of the card: every bank sentence carrying the word is graded above the introducing lesson's
# level (research/reports/w28_card_examples_report.md). Kana cards are a glyph, not a word, carry
# none by design (check F rejects one) and are not counted here (W29). May only shrink.
NO_EXAMPLE_RATCHET = {"vocab": 1695, "gram": 90, "kanji": 52}
MIN_EXAMPLES = 2_000
LEVEL_ORDER = ("pre-n5", "n5", "n4", "n3", "n2", "n1")
SENT_TAG_RX = re.compile(r'<sentence\s+ref="([^"]+)"')


def nfkc(s: str) -> str:
    return unicodedata.normalize("NFKC", s)


def token_bounds(sent: dict) -> tuple[dict[int, dict], set[int]] | None:
    """Starts (-> token) and ends of the C-unit tokens tiled over `jp`; None if they do not tile.

    The same walk as `build_vocab_exercises.token_spans`, kept inline so a plant fixture needs no
    second file: split_mode A rows are sub-units of the C token that follows them.
    """
    jp = sent.get("jp") or ""
    starts: dict[int, dict] = {}
    ends: set[int] = set()
    i = 0
    for t in sent.get("tokens") or []:
        surf = t.get("surface") or ""
        if not surf or t.get("split_mode") == "A":
            continue
        j = jp.find(surf, i)
        if j < 0:
            return None
        starts[j] = t
        ends.add(j + len(surf))
        i = j + len(surf)
    return starts, ends


def check_example(ex: dict, ns: str, item: str, rec: dict, lesson: dict, bank: dict) -> str | None:
    """Check F: the example exists, is showable at this lesson, and its cloze blanks the item."""
    if not isinstance(ex, dict) or not isinstance(ex.get("cloze"), dict):
        return "example is not {sentence, cloze}"
    if ns == "kana":
        return "a kana card carries an example: a glyph, not a word"
    sent = bank.get(ex.get("sentence"))
    if sent is None:
        return f"example sentence {ex.get('sentence')!r} is not in the bank"
    jp = sent.get("jp") or ""
    c = ex["cloze"]
    a, b, ans = c.get("start"), c.get("end"), c.get("answer")
    if not (isinstance(a, int) and isinstance(b, int) and 0 <= a < b <= len(jp)):
        return f"cloze span {a!r}-{b!r} is not inside the sentence ({len(jp)} chars)"
    if jp[a:b] != ans:
        return f"cloze answer {ans!r} is not jp[{a}:{b}] ({jp[a:b]!r}): the sentence drifted"
    bounds = token_bounds(sent)
    if bounds is None:
        return "the sentence's tokens do not tile its text, so no span can be aligned"
    starts, ends = bounds
    if a not in starts or b not in ends:
        return f"cloze span {a}-{b} ({ans!r}) cuts through a token"
    if ns == "vocab" and not any(t.get("vocab") == item for s, t in starts.items() if a <= s < b):
        return f"cloze span {ans!r} does not hold the card's own token"
    if ns == "kanji" and item.split(":", 1)[1] not in ans:
        return f"cloze span {ans!r} does not carry the character"
    if ns == "gram":
        tagged = item.split(":", 1)[1] in (sent.get("grammar") or [])
        forms = [f.get("form") or "" for f in rec.get("forms") or [] if isinstance(f, dict)]
        forms.append(rec.get("structure_pattern") or "")
        if not tagged and not any(ans in f for f in forms):
            return f"cloze span {ans!r} is not a form of the point and the sentence is not tagged"
    rendered = set(SENT_TAG_RX.findall(lesson.get("body") or "")) | set(lesson.get("sentence_refs") or [])
    for e in lesson.get("exercises") or []:
        rendered |= set(e.get("sentence_refs") or [])
    slv, llv = sent.get("level"), lesson.get("level")
    if ex["sentence"] not in rendered and slv in LEVEL_ORDER and llv in LEVEL_ORDER \
            and LEVEL_ORDER.index(slv) > LEVEL_ORDER.index(llv):
        return f"example sentence is graded {slv}, above the lesson's {llv}, and the lesson does not render it"
    return None


def die(msg: str) -> None:
    print(f"[FAIL] {msg}")
    raise SystemExit(1)


def load_lessons(root: Path) -> list[dict]:
    out = []
    for path in sorted((root / "course").rglob("lesson-*.json")):
        rec = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(rec, dict) and isinstance(rec.get("id"), str):
            out.append(rec)
    return out


def load_registry(root: Path, sub: str) -> dict[str, dict]:
    out: dict[str, dict] = {}
    d = root / "corpus" / sub
    if not d.is_dir():
        return out
    for path in sorted(d.glob("*.json")):
        try:
            recs = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            continue
        if not isinstance(recs, list):
            continue
        for rec in recs:
            if isinstance(rec, dict) and isinstance(rec.get("slug"), str):
                out[rec["slug"]] = rec
            elif isinstance(rec, dict) and isinstance(rec.get("id"), str):
                out[rec["id"]] = rec
    return out


def load_kana(root: Path) -> dict[str, dict]:
    """Legal kana card targets, at BOTH granularities.

    `contracts/user_state/card.schema.json` accepts the family form `kana:hiragana-a` (57 cards
    today) and the glyph form `kana:hiragana-あ` (211 glyph records), because W29 migrates one to the
    other under decision D6 and the contract has to hold across that migration. The same rule is in
    `validate_srs_decks.load_kana_ids`; both gates consume the same files, per README Conventions.
    Kana records carry `id`, not `slug`, and no `forms[]` — no kana card carries an answer key yet.
    """
    out: dict[str, dict] = {}
    fam = root / "corpus" / "kana" / "families.json"
    if fam.exists():
        for group in json.loads(fam.read_text(encoding="utf-8")).values():
            for f in group:
                out[f["id"]] = f
                for m in f.get("members") or []:
                    out[m["id"]] = m
    for name in ("hiragana.json", "katakana.json"):
        p = root / "corpus" / "kana" / name
        if p.exists():
            for g in json.loads(p.read_text(encoding="utf-8")):
                out[g["id"]] = g
    return out


def load_retired(root: Path) -> set[str]:
    """Every address a card may not name: the retirement ledgers, keys only."""
    retired: set[str] = set()
    for name in ("vocab_redirects.json", "grammar_deprecated.json", "families_deprecated.json"):
        f = root / "corpus" / name
        if not f.exists():
            continue
        doc = json.loads(f.read_text(encoding="utf-8"))
        if isinstance(doc, dict):
            rows = doc.get("rows") if isinstance(doc.get("rows"), list) else None
            if rows is not None:
                for r in rows:
                    for k in ("from", "slug", "id", "deprecated"):
                        if isinstance(r, dict) and isinstance(r.get(k), str):
                            retired.add(r[k])
                            break
            else:
                retired.update(k for k in doc if isinstance(k, str) and ":" in k)
    return retired


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", type=Path, default=REPO, help="tree to validate (corpus/, course/)")
    ap.add_argument("--all", action="store_true", help="print every failure, not the first 20")
    args = ap.parse_args()
    root: Path = args.root.resolve()

    lessons = load_lessons(root)
    if len(lessons) < MIN_LESSONS:
        die(f"{len(lessons)} lesson leaf/leaves under {root}/course, floor is {MIN_LESSONS} — a "
            f"card gate that found no lessons has certified nothing")

    registries = {"vocab": load_registry(root, "vocab"),
                  "gram": load_registry(root, "grammar"),
                  "kanji": load_registry(root, "kanji"),
                  "kana": load_kana(root)}
    if not registries["kana"]:
        die(f"no kana ids under {root}/corpus/kana — a card gate that cannot resolve a kana target "
            f"would pass every kana card by failing to look")
    if not registries["vocab"]:
        die(f"no vocab records under {root}/corpus/vocab — the accept sets cannot be checked "
            f"against a registry that is not there")
    retired = load_retired(root)

    bank_path = root / "corpus" / "sentences" / "bank.json"
    bank = {s["slug"]: s for s in json.loads(bank_path.read_text(encoding="utf-8"))} \
        if bank_path.exists() else {}
    if not bank:
        die(f"no sentence bank at {bank_path} — an example cannot be checked against nothing")

    fails: dict[str, list[str]] = {k: [] for k in "ABCDEF"}
    n_cards = n_prod = n_keys = n_examples = 0
    unkeyed: dict[str, int] = {}
    no_example: dict[str, int] = {}

    for L in lessons:
        lid = L["id"]
        for card in (L.get("srs") or {}).get("introduces_cards") or []:
            n_cards += 1
            item = card.get("item")
            addr = f"{lid} / {item}"
            if not isinstance(item, str) or ":" not in item:
                fails["A"].append(f"{addr}: item is not a stable id")
                continue
            ns = item.split(":", 1)[0]
            # ---- A: the item resolves and is not retired -------------------------------------
            if item in retired:
                fails["A"].append(f"{addr}: names a retired address (a redirect/deprecation ledger "
                                  f"carries it), so the card renders nothing")
                continue
            reg = registries.get(ns)
            if reg is None:
                fails["A"].append(f"{addr}: namespace {ns!r} has no registry")
                continue
            rec = reg.get(item)
            if rec is None:
                fails["A"].append(f"{addr}: does not resolve to a record in corpus/{ns}")
                continue

            # ---- F: the example sentence and its cloze span (W28) ------------------------------
            ex = card.get("example")
            if ex is None:
                # Kana cards carry none by design (check F rejects one), so they are not a gap to
                # ratchet: W29 turned 57 family cards into 211 glyph cards without losing anything.
                if ns != "kana":
                    no_example[ns] = no_example.get(ns, 0) + 1
            else:
                n_examples += 1
                why = check_example(ex, ns, item, rec, L, bank)
                if why:
                    fails["F"].append(f"{addr}: {why}")

            key = card.get("production_key")
            kinds = card.get("card_types") or []
            is_prod = "production" in kinds
            # ---- D: a key only belongs on a production card ----------------------------------
            if key is not None and not is_prod:
                fails["D"].append(f"{addr}: carries a production_key but card_types are "
                                  f"{kinds!r} — nothing renders it")
                continue
            if not is_prod:
                continue
            n_prod += 1
            # ---- B: a production card needs a key (ratcheted per namespace) ------------------
            if key is None:
                unkeyed[ns] = unkeyed.get(ns, 0) + 1
                continue
            n_keys += 1
            prompt = key.get("prompt")
            # ---- E: structure ---------------------------------------------------------------
            if not isinstance(prompt, dict):
                fails["E"].append(f"{addr}: prompt is not a locale object ({type(prompt).__name__})")
                continue
            if not set(prompt) <= LOCALES:
                fails["E"].append(f"{addr}: prompt carries undeclared locale(s) "
                                  f"{sorted(set(prompt) - LOCALES)}")
                continue
            pt = prompt.get("pt-BR")
            if not isinstance(pt, str) or not pt.strip():
                fails["B"].append(f"{addr}: empty prompt — the learner is shown nothing to answer")
                continue
            accept = key.get("accept")
            if not isinstance(accept, list) or not accept:
                fails["B"].append(f"{addr}: empty accept set — nothing the learner types can be right")
                continue
            if any(not isinstance(a, str) or not a.strip() for a in accept):
                fails["E"].append(f"{addr}: accept carries a blank entry")
                continue
            if len(set(accept)) != len(accept):
                fails["E"].append(f"{addr}: accept carries a duplicate")
                continue
            senses = rec.get("senses") or []
            si = key.get("sense_index")
            if si is not None:
                if not isinstance(si, int) or si < 0 or si >= len(senses):
                    fails["E"].append(f"{addr}: sense_index {si!r} names no sense of the record "
                                      f"({len(senses)} sense(s))")
                    continue
            # ---- C: the accept set is this record's, and admits its own name -----------------
            if ns == "kana":
                # W29: a kana record has no headword, kana or forms[]; its name IS its glyph, and
                # that one surface is all a grader may take. A family record has no `char`, so a
                # key on a family card gets an empty form set and fails, which is right: W29
                # retired family cards.
                ch = rec.get("char")
                forms = {ch} if isinstance(ch, str) and ch else set()
                head = kana = ch
            else:
                forms = {f.get("form") for f in (rec.get("forms") or []) if isinstance(f, dict)}
                forms = {f for f in forms if isinstance(f, str)}
                head, kana = rec.get("headword"), rec.get("kana")
            nforms = {nfkc(f) for f in forms}
            if head not in accept and kana not in accept:
                fails["C"].append(f"{addr}: accepts neither the headword {head!r} nor the kana "
                                  f"{kana!r} ({accept!r})")
                continue
            outside = [a for a in accept if a not in forms and nfkc(a) not in nforms]
            if outside:
                fails["C"].append(f"{addr}: accepts {outside!r}, which is not a form of "
                                  f"{head}/{kana}")
                continue

    if n_cards < MIN_CARDS:
        die(f"{n_cards} card(s) across {len(lessons)} lessons, floor is {MIN_CARDS}")
    if n_keys < MIN_KEYS:
        die(f"{n_keys} production key(s), floor is {MIN_KEYS} — a run that found no keys would "
            f"pass every content check by having nothing to check")
    if n_examples < MIN_EXAMPLES:
        die(f"{n_examples} card example(s), floor is {MIN_EXAMPLES}")

    ratchet_fail = []
    for ns in sorted(set(no_example) | set(NO_EXAMPLE_RATCHET)):
        got, allowed = no_example.get(ns, 0), NO_EXAMPLE_RATCHET.get(ns)
        if allowed is None:
            ratchet_fail.append(f"{ns}: {got} card(s) with no example and no ratchet entry")
        elif got > allowed:
            ratchet_fail.append(f"{ns}: {got} card(s) with no example, ratchet is {allowed} — a card "
                                f"that lost its example is a regression")
    for ns, allowed in UNKEYED_RATCHET.items():
        got = unkeyed.get(ns, 0)
        if got > allowed:
            ratchet_fail.append(f"{ns}: {got} production card(s) with no answer key, ratchet is "
                                f"{allowed} — a new unkeyed card is a regression")
    for ns in sorted(set(unkeyed) - set(UNKEYED_RATCHET)):
        ratchet_fail.append(f"{ns}: {unkeyed[ns]} production card(s) with no answer key and no "
                            f"ratchet entry — add one with a reason or key them")

    total = sum(len(v) for v in fails.values()) + len(ratchet_fail)
    print(f"{n_cards} card(s) over {len(lessons)} lesson(s); {n_prod} production card(s), "
          f"{n_keys} key(s) checked")
    for ns, allowed in sorted(UNKEYED_RATCHET.items()):
        print(f"  unkeyed {ns:<6} {unkeyed.get(ns, 0):>4} / ratchet {allowed}")
    for ns, allowed in sorted(NO_EXAMPLE_RATCHET.items()):
        print(f"  no example {ns:<6} {no_example.get(ns, 0):>4} / ratchet {allowed}")
    if not total:
        print(f"[OK] {n_cards} card(s) over {len(lessons)} lesson(s); {n_keys} production key(s) "
              f"checked; {n_examples} example(s) checked")
        return 0
    print(f"[FAIL] {total} problem(s)")
    for check in "ABCDEF":
        rows = fails[check]
        if not rows:
            continue
        print(f"  check {check}: {len(rows)}")
        for r in (rows if args.all else rows[:MAX_REPORT]):
            print(f"    {r}")
        if not args.all and len(rows) > MAX_REPORT:
            print(f"    … and {len(rows) - MAX_REPORT} more")
    for r in ratchet_fail:
        print(f"  ratchet: {r}")
    return 1


if __name__ == "__main__":
    sys.exit(main())
