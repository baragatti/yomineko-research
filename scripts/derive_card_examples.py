#!/usr/bin/env python3
"""W28. An example sentence and a cloze span for every SRS card, selected from the bank. Table only.

WHY
---
`lesson.srs.introduces_cards[]` names a deck, an item and its kinds (and, since W27, a production
key on vocabulary cards). Nothing on a card said which sentence shows the item in use, so the review
screen had no example to print and no stored cloze for the `cloze` kind. W13 measured the data half
(2,901 of 2,951 vocabulary cards have the word as a token in some bank sentence); this is the other
half: the slot, the selection rule and the span. No sentence or prose is authored.

THE RULE (the lesson renderer's own, imported, not copied)
----------------------------------------------------------
A sentence may be a card's example when, at the card's lesson L (the lesson that issues the card):
  1. the bank labels its register as model text (derive_lesson_sentences.SHOWABLE_REGISTERS) and it
     has a pt-BR translation;
  2. L renders it; OR it passes the display test `validate_lesson_gating` check D applies to every
     sentence a lesson shows (`derive_lesson_sentences.fit`, the same arithmetic): graded at or
     below L's level, and at most BUDGET[level] kanji + words outside L's cumulative_known_set
     (pre-N5 0, N5 1, N4 2, N3 2), with no unlinked content token;
  3. it carries the card's item: the word as a token (vocab), the point as a tag or, failing any
     tagged sentence, a spelled form (grammar), the character in its text (kanji);
  4. a cloze span exists (below).
Ranking: rendered by L first, then i+0 (`build_vocab_exercises.sentence_ok`) before i+1, then fewer
unknowns, then a real sentence over a generated one (spec 1.2), then shorter, then a stable hash. The
first ranked sentence with a span wins. W14's `Mais exemplos` adds used i+0 only because check D
ratchets the COUNT of body links carrying a new item; a card is not a body link, so the budget
applies as written.

WHAT IT DOES NOT REACH
----------------------
W13's 2,901 / 2,951 counts a vocabulary card as able to show an example when the word is a token in
ANY bank sentence. Under the rule above far fewer can: the bank grades 3,405 of its 10,209 sentences
N2/N1 and 473 N5, so for most words every sentence that carries them is above the level of the lesson
that introduces them. Those cards get no example (`no_example[]`, reason
`none-passes-display-rule`) and `validate_card_content.py` holds the count as a ratchet. Showing an
above-level sentence to fill the slot is the decision this script refuses to take.

THE CLOZE SPAN (a Sudachi token boundary on both sides; the practice builder's rules)
------------------------------------------------------------------------------------
  vocab   the card's own token (reading and sense must fit the record), extended over its
          inflection to the whole form (`whole_form_end`: なり -> なりません)
  gram    a probe segment of the point's forms/structure_pattern aligned to token starts and ends; a
          one-character point is a particle token (taken from the end)
  kanji   the whole token (extended over its inflection) that carries the character
A span must leave at least 2 Japanese letters outside it; a vocab or kanji span must be 2 letters
long or hold a kanji. `start`/`end` are code-point offsets into the sentence's `jp`; `answer` is
`jp[start:end]`. Kana cards get no example: a family card is five glyphs, not a word.

Reads the EXPORTED tree (course/, corpus/). Writes research/derived/repairs/card_examples.json.
Deterministic. Usage: derive_card_examples.py [--out PATH]
"""
from __future__ import annotations

import argparse
import collections
import json
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "scripts" / "validate"))
import build_vocab_exercises as bve  # noqa: E402  (sentence_ok, rank_sentences, token_spans)
import derive_needs  # noqa: E402
import validate_lesson_gating as vlg  # noqa: E402  (LEVEL_ORDER)
import validate_practice_coverage as vpc  # noqa: E402  (grammar probe segments)
from derive_lesson_sentences import SHOWABLE_REGISTERS, fit  # noqa: E402

TABLE = ROOT / "research" / "derived" / "repairs" / "card_examples.json"
LOC = "pt-BR"


def letters(s: str) -> int:
    return len(bve.JP_LETTER_RX.findall(s))


def span_ok(jp: str, a: int, b: int, word: bool) -> bool:
    if letters(jp[:a] + jp[b:]) < bve.MIN_JP_LEFT or not jp[a:b].strip():
        return False
    return not word or letters(jp[a:b]) >= 2 or bool(bve.KANJI_RX.search(jp[a:b]))


def vocab_span(sent: dict, rec: dict, item: str) -> tuple[int, int] | None:
    spans = bve.token_spans(sent)
    jp = sent["jp"]
    for k, (a, _b, t) in enumerate(spans):
        if t.get("vocab") == item and bve.reading_fits(t, rec) and bve.sense_fits(t, rec):
            b = bve.whole_form_end(spans, k)
            if span_ok(jp, a, b, True):
                return a, b
    return None


def kanji_span(sent: dict, ch: str) -> tuple[int, int] | None:
    spans = bve.token_spans(sent)
    jp = sent["jp"]
    for k, (a, b, _t) in enumerate(spans):
        if ch in jp[a:b]:
            b = bve.whole_form_end(spans, k)
            if span_ok(jp, a, b, True):
                return a, b
    return None


def gram_span(sent: dict, segs: list[str], single: list[str], tagged: bool) -> tuple[int, int] | None:
    """`build_vocab_exercises.build_grammar_cloze`'s alignment, returning the offsets."""
    jp = sent["jp"]
    spans = bve.token_spans(sent)
    if not spans:
        return None
    starts = {a: t for a, _b, t in spans}
    ends = {b for _a, b, _t in spans}
    for seg in segs + (single if tagged else []):
        hits = [i for i in range(len(jp)) if jp.startswith(seg, i)]
        for at in (reversed(hits) if len(seg) == 1 else hits):
            tok = starts.get(at)
            if tok is None or at + len(seg) not in ends:
                continue
            if len(seg) == 1 and not (tok.get("surface") == seg and tok.get("pos") == "particle"
                                      and tok.get("pos_fine") != "接続助詞"):
                continue
            if span_ok(jp, at, at + len(seg), False):
                return at, at + len(seg)
    return None


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", help="write the table here instead of research/derived/repairs/")
    args = ap.parse_args()
    root = ROOT

    rows = bve.load_lessons(root)                      # fills bve.INTRO_POS, course order
    bve.SENT_REFS.update(derive_needs.load_sentence_index(root))
    by_slug, by_vocab, by_gram, need, _att = bve.index_bank(root)
    V = bve.load_vocab_records(root)
    probes, _labels = vpc.load_grammar(root)
    by_kanji: dict[str, list[str]] = collections.defaultdict(list)
    for slug, s in by_slug.items():
        for ch in dict.fromkeys(bve.KANJI_RX.findall(s.get("jp") or "")):
            by_kanji[ch].append(slug)
    order = vlg.LEVEL_ORDER

    kanji_chars = {k["character"] for kf in sorted(root.glob("corpus/kanji/*.json"))
                   for k in json.loads(kf.read_text(encoding="utf-8"))}
    vid2slug = {v["id"]: s for s, v in V.items()}

    def showable(slug: str, level: str) -> bool:
        s = by_slug[slug]
        if s.get("register") not in SHOWABLE_REGISTERS:
            return False
        return bool(((s.get("translation") or {}).get(LOC) or "").strip())

    def ranked(cands: list[str], row: dict, ref: str) -> list[str]:
        """The display rule, then the renderer's preference order.

        Admitted: a sentence L renders, or one that is not above L's level, carries no unlinked
        content token and no more unknown kanji + words than check D's i+1 budget for the level
        (`derive_lesson_sentences.fit`, the same arithmetic). Ranked: rendered by L, then i+0
        (`sentence_ok`) before i+1, then fewer unknowns, then real over generated, then shorter, then
        a stable hash.
        """
        les = row["lesson"]
        budget = vlg.BUDGET.get(les.get("level"), 2)
        keyed = []
        for s in cands:
            rec = by_slug[s]
            above, load = fit(rec, les, kanji_chars, vid2slug)
            rendered = s in row["rendered"]
            if not rendered and (above or load > budget or need[s][2]):
                continue
            prov = rec.get("provenance") or {}
            keyed.append(((0 if rendered else 1, 0 if bve.sentence_ok(s, row, need) else 1, load,
                           1 if prov.get("jp_source") == "ai-generated" else 0,
                           len(rec.get("jp") or ""), bve.h(ref, row["id"], s)), s))
        return [s for _k, s in sorted(keyed)]

    out: list[dict] = []
    missing: list[dict] = []
    counts: collections.Counter[str] = collections.Counter()
    for row in rows:
        les = row["lesson"]
        lid, level = les["id"], les.get("level") or row["level"]
        for card in (les.get("srs") or {}).get("introduces_cards") or []:
            item = card["item"]
            ns = item.split(":", 1)[0]
            counts[f"{ns}_cards"] += 1
            pick = None
            pool: list[str] = []              # sentences carrying the item, before the display rule
            admitted: list[str] = []          # ... and after it, in rank order
            if ns == "vocab" and item in V:
                pool = by_vocab.get(item, [])
                admitted = ranked([s for s in pool if showable(s, level)], row, item)
                for s in admitted:
                    if (sp := vocab_span(by_slug[s], V[item], item)):
                        pick = (s, sp, "the card's own token, whole form")
                        break
            elif ns == "gram":
                segs = sorted((x for x in probes.get(item, set()) if len(x) > 1),
                              key=lambda x: (-len(x), x))
                single = sorted(x for x in probes.get(item, set()) if len(x) == 1)
                tagged = by_gram.get(item, [])
                tset = set(tagged)
                spelled = [s for s, r in by_slug.items() if s not in tset
                           and any(g in (r.get("jp") or "") for g in segs)] if segs else []
                pool = tagged + spelled
                admitted = (ranked([s for s in tagged if showable(s, level)], row, item)
                            + ranked([s for s in spelled if showable(s, level)], row, item))
                for s in admitted:
                    if (sp := gram_span(by_slug[s], segs, single, s in tset)):
                        pick = (s, sp, "a probe segment of the point, tagged sentence" if s in tset
                                else "a probe segment of the point, spelled (no tagged sentence fit)")
                        break
            elif ns == "kanji":
                ch = item.split(":", 1)[1]
                pool = by_kanji.get(ch, [])
                admitted = ranked([s for s in pool if showable(s, level)], row, item)
                for s in admitted:
                    if (sp := kanji_span(by_slug[s], ch)):
                        pick = (s, sp, "the whole token that carries the character")
                        break
            if pick is None:
                if ns == "kana":
                    why = "kana-family"
                elif not pool:
                    why = "no-sentence-carries-item"
                elif not admitted:
                    why = "none-passes-display-rule"
                else:
                    why = "no-alignable-span"
                missing.append({"lesson": lid, "item": item, "why": why})
                counts[f"missing_{why}"] += 1
                continue
            s, (a, b), how = pick
            jp = by_slug[s]["jp"]
            tier = ("rendered by the lesson" if s in row["rendered"] else
                    "i+0 in the known set" if bve.sentence_ok(s, row, need) else
                    "i+1 within the level budget")
            out.append({"lesson": lid, "item": item, "sentence": s,
                        "cloze": {"start": a, "end": b, "answer": jp[a:b]},
                        "why": f"{tier}; cloze = {how}"})
            counts[f"{ns}_with_example"] += 1
            counts[tier] += 1
            if ((by_slug[s].get("provenance") or {}).get("jp_source")) == "ai-generated":
                counts["ai_generated_sentence"] += 1

    doc = {
        "what_this_is": ("W28: the example sentence and cloze span of every SRS card, keyed (lesson, "
                         "item). Derived by scripts/derive_card_examples.py from the exported tree; "
                         "applied by scripts/apply_card_examples.py into card_example (migration "
                         "018); export_course.py joins it onto srs.introduces_cards[].example. "
                         "design/srs_design.md §9."),
        "derived_by": "scripts/derive_card_examples.py",
        "counts": dict(sorted(counts.items())),
        "row_count": len(out),
        "rows": out,
        "no_example": missing,
    }
    dest = Path(args.out) if args.out else TABLE
    dest.write_text(json.dumps(doc, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(f"wrote {dest}: {len(out)} rows, {len(missing)} card(s) with no example")
    print(json.dumps(doc["counts"], ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
