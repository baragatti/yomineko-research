#!/usr/bin/env python3
"""The known-set gate for reading passages — one implementation, shared by every consumer.

WHY THIS MODULE EXISTS
----------------------
"Every kanji and every content word of this passage is already in the gating lesson's
`cumulative_known_set`" (design/reading_practice.md §3, `max_new = 0`) was implemented three times:
in `build_readings.py` (by set arithmetic over `sentence_kanji`/`sentence_vocab`), in
`validate_readings.py` (over the exported `uses`), and once more, from scratch, in the W15 authoring
campaign's own checker. The three disagreed on exactly one thing, and that disagreement cost the
campaign thirteen passages: **which registry record a surface names**.

THE RULE THIS MODULE ADDS (W15)
-------------------------------
SudachiPy's `dictionary_form()` is a LEMMA. A lemma can name a different registry record, at a
different JLPT level, than the surface in front of the learner:

    surface ください   lemma くださる   ->  vocab:1184280  下さる  N4
    surface ください   surface itself   ->  vocab:1184270  下さい  N5    <- what N5 unlocks

Resolving lemma-first therefore reported every N5 passage containing てください as introducing an
N4 word its lesson never unlocks, and てください — the single most common polite request form at
N5 — became unusable in N5 reading. That is not a fact about the passage; it is an artefact of the
resolver.

    A surface the gating lesson's known set contains must not resolve to an unknown lemma.

`Dissector.vocab_candidates()` returns the ordered candidates (lemma, surface, kana-normalised
surface); `resolve_token` below takes the FIRST candidate the known set already contains, and falls
back to the lemma when none of them is known. Every tier is a real `vocab_form`/`headword`/`kana`
lookup, so no tier can invent a record: the rule can only choose between records the token genuinely
names, never launder a word the learner has not met. When no candidate is known, the word is still
NEW and the passage is still held — which is what keeps `こと` in `n4-oracoes-relativas-02` a
course-data gap (W21b) instead of something a resolver rule can paper over.

WHAT `uses` MEANS HERE
----------------------
`uses` is a SNAPSHOT, not a live projection. It records the kanji and vocab records that THIS
passage's own Sudachi tokenisation resolved to, at the moment the passage was applied — not a
recompute from `sentence_kanji`/`sentence_vocab`, which grow with every later dissection pass and
would push already-gated boxes out of their lesson's known set (see
`apply_readings_composition_repairs.py`). Only records the gating lesson already teaches are
credited: a kana-only word that resolves to an out-of-set record is the §3 carve-out
("kana-only words, numbers, punctuation and proper nouns are allowed anyway") and is reported, not
credited, so `uses` stays inside the known set by construction and `validate_readings.py` compares
like with like.

Usage:
    from known_set import load_known_sets, PassageGate
    gate = PassageGate()                       # opens db/corpus.sqlite read-only
    known = load_known_sets(ROOT)              # from the EXPORTED courseware leaves
    r = gate.analyse(jp, known["les:n5-te-form-06"])
    r.ok, r.unknown_vocab, r.unknown_kanji, r.uses_vocab_ids, r.tokens
"""
from __future__ import annotations

import json
import sqlite3
import sys
from dataclasses import dataclass, field
from pathlib import Path

_HERE = Path(__file__).resolve()
sys.path.append(str(_HERE.parent))                      # scripts/ingest (dissect)
sys.path.append(str(_HERE.parents[1]))                  # scripts (dbtarget)
from dissect import CONTENT_POS, Dissector, hira        # noqa: E402
from dbtarget import db_target                          # noqa: E402

ROOT = _HERE.parents[2]


def is_kana_only(s: str) -> bool:
    """§3 carve-out test: the surface is written entirely in kana (plus ー / ゝ repetition marks)."""
    return bool(s) and all("ぁ" <= c <= "ヿ" or c in "ー〜～" for c in s)


# design/reading_practice.md §3, verbatim: "allowed-anyway: kana-only words, NUMBERS, punctuation,
# and (flagged) proper nouns". Sudachi tags a numeral 名詞/数詞, so the carve-out is mechanical. It
# matters: `read:n5-numeros-tempo-04-01` is a lesson about numbers whose 二かい / 二こ resolved to
# vocab:1461140 二, a record the numbers lesson never unlocks as a WORD even though it teaches the
# kanji and the counter — the passage was held for a rule the design document had already waived.
NUMERAL_POS_FINE = "数詞"
# Punctuation and whitespace end a run: a "word" spelled across a 。 is a coincidence, not a word.
RUN_STOP_POS = {"補助記号", "記号", "空白"}
RUN_MAX = 4


def is_kanji(ch: str) -> bool:
    return "一" <= ch <= "鿿" or "㐀" <= ch <= "䶿"


@dataclass(frozen=True)
class KnownSet:
    lesson: str
    kanji: frozenset          # bare characters, from `kanji:<char>`
    vocab: frozenset          # `vocab:<jmdict_id>` slugs, verbatim
    grammar: frozenset        # `gram:<key>` slugs, verbatim


def load_known_sets(root: Path = ROOT) -> dict[str, KnownSet]:
    """Cumulative known sets from the EXPORTED courseware leaves — the same source
    `validate_readings.py` reads. The DB's copy is regenerable state and can lag the export."""
    out: dict[str, KnownSet] = {}
    for lf in root.glob("course/*/topic-*/lesson-*.json"):
        d = json.loads(lf.read_text(encoding="utf-8"))
        cks = d.get("cumulative_known_set") or {}
        out[d["id"]] = KnownSet(
            lesson=d["id"],
            kanji=frozenset(x.split(":", 1)[1] for x in (cks.get("kanji") or [])),
            vocab=frozenset(cks.get("vocab") or []),
            grammar=frozenset(cks.get("grammar") or []),
        )
    return out


@dataclass
class GateResult:
    jp: str
    tokens: list = field(default_factory=list)        # [{s,r,ro,pos}] — the reading-table shape
    uses_kanji_ids: list = field(default_factory=list)
    uses_vocab_ids: list = field(default_factory=list)
    unknown_kanji: list = field(default_factory=list)  # [char]
    unknown_vocab: list = field(default_factory=list)  # [{surface, lemma, slug, level, headword}]
    carve_out: list = field(default_factory=list)      # kana-only / numeral, resolves outside the set
    unlinked: list = field(default_factory=list)       # content token naming no record at all
    rescued: list = field(default_factory=list)        # [{surface, lemma_slug, chosen_slug}] — the surface rule
    rescued_runs: list = field(default_factory=list)   # [{surface, run, slug}] — the run rule

    @property
    def ok(self) -> bool:
        return not self.unknown_kanji and not self.unknown_vocab


class PassageGate:
    """Tokenise a passage and decide it against a lesson's known set. Read-only on the index."""

    def __init__(self, db: Path | None = None, dissector: Dissector | None = None):
        path = db_target(ROOT / "db" / "corpus.sqlite") if db is None else db
        self.d = dissector or Dissector(db=Path(path))
        con = sqlite3.connect(f"file:{str(path).replace(chr(92), '/')}?mode=ro", uri=True)
        self.slug_by_vid = {i: s for i, s in con.execute("SELECT id,slug FROM vocab")}
        self.level_by_vid = {i: (lv or "") for i, lv in con.execute("SELECT id,level FROM vocab")}
        self.head_by_vid = {i: h for i, h in con.execute("SELECT id,headword FROM vocab")}
        self.kid_by_char = {c: i for c, i in con.execute("SELECT character,id FROM kanji")}
        con.close()

    # ---- the rule ------------------------------------------------------------------------
    def resolve_token(self, lemma: str, surface: str, known: KnownSet) -> tuple[int | None, list[int]]:
        """Return (chosen vocab id or None, the ordered candidate list).

        The chosen id is the FIRST candidate the known set already contains; when none is known the
        lemma-first candidate is returned so the caller can name the record that is actually missing.
        """
        cands = self.d.vocab_candidates(lemma, surface)
        for vid in cands:
            if self.slug_by_vid.get(vid) in known.vocab:
                return vid, cands
        return (cands[0] if cands else None), cands

    def resolve_run(self, tokens: list, i: int, known: KnownSet) -> tuple[int | None, str]:
        """Second chance for a token whose own candidates are all untaught: does a CONTIGUOUS RUN of
        tokens containing it spell a word the learner already knows?

        SudachiPy mode C is a word segmenter, not a dictionary aligner, so it splits お|茶 and
        要する|に while the registry — and the lesson — carry お茶 (N5, taught) and 要するに (N3,
        taught). Charging the learner for 茶 (N3) and 要する (N1) in that situation is the same
        category of error as the lemma trap: the SURFACE in front of them is a word they have been
        taught. This is the R2 rule `build_sentence_vocab.py` has always used for linking, applied
        to the readability gate.

        The run must be contiguous, must contain the failing token, must not cross punctuation, is
        at most RUN_MAX tokens, and its joined surface must be an EXACT registry form owned by a
        record that is ALREADY in the known set. So it can only ever say "this longer word is one
        you were taught"; it can never introduce a record the text does not spell.
        """
        n = len(tokens)
        for w in range(2, RUN_MAX + 1):
            for s in range(max(0, i - w + 1), min(i, n - w) + 1):
                part = tokens[s:s + w]
                if len(part) < w or any(t["pos_coarse"] in RUN_STOP_POS for t in part):
                    continue
                run = "".join(t["surface"] for t in part)
                for vid in self.d.form_owners(run):
                    if self.slug_by_vid.get(vid) in known.vocab:
                        return vid, run
        return None, ""

    # ---- the gate ------------------------------------------------------------------------
    def analyse(self, jp: str, known: KnownSet) -> GateResult:
        skel = self.d.skeleton(jp)
        res = GateResult(jp=jp, tokens=[{"s": t["surface"], "r": t["reading"], "ro": t["romaji"],
                                         "pos": t["pos"] or "noun"} for t in skel["tokens"]])
        res.unknown_kanji = sorted({ch for ch in jp if is_kanji(ch) and ch not in known.kanji})
        kanji_ids, vocab_ids = set(), set()
        for ch in jp:
            if is_kanji(ch) and ch in known.kanji and ch in self.kid_by_char:
                kanji_ids.add(self.kid_by_char[ch])
        toks = skel["tokens"]
        for i, t in enumerate(toks):
            if t["pos_coarse"] not in CONTENT_POS:
                continue
            lemma, surface = t["lemma"], t["surface"]
            vid, cands = self.resolve_token(lemma, surface, known)
            if vid is None:
                if t["pos_fine"] == NUMERAL_POS_FINE:
                    continue                                     # §3: numbers are allowed anyway
                res.unlinked.append({"surface": surface, "lemma": lemma, "pos": t["pos_coarse"]})
                continue
            slug = self.slug_by_vid.get(vid)
            if slug in known.vocab:
                vocab_ids.add(vid)
                if cands and cands[0] != vid:                    # the W15 surface rule changed the answer
                    res.rescued.append({"surface": surface, "lemma": lemma,
                                        "lemma_slug": self.slug_by_vid.get(cands[0]),
                                        "chosen_slug": slug})
                continue
            run_vid, run = self.resolve_run(toks, i, known)       # the W15 run rule
            if run_vid is not None:
                vocab_ids.add(run_vid)
                res.rescued_runs.append({"surface": surface, "run": run,
                                         "slug": self.slug_by_vid.get(run_vid)})
            elif is_kana_only(surface) or t["pos_fine"] == NUMERAL_POS_FINE:
                res.carve_out.append({"surface": surface, "lemma": lemma, "slug": slug,
                                      "level": self.level_by_vid.get(vid, ""),
                                      "why": "numeral" if t["pos_fine"] == NUMERAL_POS_FINE else "kana-only"})
            else:
                res.unknown_vocab.append({"surface": surface, "lemma": lemma, "slug": slug,
                                          "headword": self.head_by_vid.get(vid, ""),
                                          "level": self.level_by_vid.get(vid, "")})
        res.uses_kanji_ids = sorted(kanji_ids)
        res.uses_vocab_ids = sorted(vocab_ids)
        return res


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
    g = PassageGate()
    ks = load_known_sets()
    lesson = sys.argv[1] if len(sys.argv) > 1 else "les:n5-te-form-06"
    text = sys.argv[2] if len(sys.argv) > 2 else "ちょっと待ってください。"
    r = g.analyse(text, ks[lesson])
    print(json.dumps({"ok": r.ok, "unknown_kanji": r.unknown_kanji, "unknown_vocab": r.unknown_vocab,
                      "carve_out": r.carve_out, "rescued": r.rescued, "rescued_runs": r.rescued_runs,
                      "unlinked": r.unlinked},
                     ensure_ascii=False, indent=1))
