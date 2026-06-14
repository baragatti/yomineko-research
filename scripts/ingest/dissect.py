#!/usr/bin/env python3
"""P5 core — the single dissection skeleton generator (spec §6, Layer A).

Given a Japanese sentence, produces the deterministic structural skeleton that EVERY sentence
in the system shares: SudachiPy tokens in BOTH split modes (C = word boundaries, A = smallest
sub-units linked to their C parent), per-token surface/lemma/reading/romaji/POS, full-sentence
kana + romaji (with particle overrides は→わ, へ→え, を→o), auto-links to our vocab/kanji
registries, and the particle list. The LLM later adds ONLY Layer-B glosses/translation/
explanations on top of this skeleton (it may NOT alter surface/lemma/reading/pos — spec §7.2).

Usage:
  from dissect import Dissector
  d = Dissector(); skel = d.skeleton("私はパンを食べました。")
"""
from __future__ import annotations

import sqlite3
import sys
from pathlib import Path

import jaconv
from sudachipy import dictionary, tokenizer

ROOT = Path(__file__).resolve().parents[2]
DB = ROOT / "db" / "corpus.sqlite"

PARTICLE_KANA = {"は": "わ", "へ": "え"}            # kana display override for particles
PARTICLE_ROMAJI = {"は": "wa", "へ": "e", "を": "o"}  # romaji override for particles
# beginner-standard readings where Sudachi's dictionary reading differs from the common one
COMMON_READING = {"私": "わたし"}
KANJI_RE = __import__("re").compile(r"[一-鿿㐀-䶿]")


def hira(s: str) -> str:
    return jaconv.kata2hira(s or "")


class Dissector:
    def __init__(self, db: Path = DB):
        self.tok = dictionary.Dictionary(dict="full").create()
        self.A = tokenizer.Tokenizer.SplitMode.A
        self.C = tokenizer.Tokenizer.SplitMode.C
        self.con = sqlite3.connect(db)
        # lookup caches
        self._vocab_by_form: dict[str, int] = {}
        for form, vid in self.con.execute(
                "SELECT form, vocab_id FROM vocab_form"):
            self._vocab_by_form.setdefault(form, vid)
        for hw, vid in self.con.execute("SELECT headword, id FROM vocab"):
            self._vocab_by_form.setdefault(hw, vid)
        for kana, vid in self.con.execute("SELECT kana, id FROM vocab"):
            self._vocab_by_form.setdefault(kana, vid)
        self._kanji_by_char: dict[str, int] = {
            ch: kid for ch, kid in self.con.execute("SELECT character, id FROM kanji")}

    def _vocab_id(self, lemma: str, surface: str) -> int | None:
        return self._vocab_by_form.get(lemma) or self._vocab_by_form.get(surface)

    def _is_particle(self, m) -> bool:
        return m.part_of_speech()[0] == "助詞"

    def _tok_kana(self, m) -> str:
        if self._is_particle(m) and m.surface() in PARTICLE_KANA:
            return PARTICLE_KANA[m.surface()]
        if m.surface() in COMMON_READING:
            return COMMON_READING[m.surface()]
        r = hira(m.reading_form())
        return r or hira(m.surface())

    def _tok_romaji(self, m) -> str:
        if self._is_particle(m) and m.surface() in PARTICLE_ROMAJI:
            return PARTICLE_ROMAJI[m.surface()]
        return jaconv.kana2alphabet(self._tok_kana(m))

    def skeleton(self, jp: str) -> dict:
        c_morphs = list(self.tok.tokenize(jp, self.C))
        a_morphs = list(self.tok.tokenize(jp, self.A))
        tokens = []
        for pos, m in enumerate(c_morphs):
            p = m.part_of_speech()
            lemma = m.dictionary_form()
            surface = m.surface()
            kana = self._tok_kana(m)
            tokens.append({
                "position": pos, "split_mode": "C", "surface": surface, "lemma": lemma,
                "reading": kana, "romaji": self._tok_romaji(m),
                "pos_coarse": p[0], "pos_fine": p[1],
                "begin": m.begin(), "end": m.end(),
                "vocab_id": self._vocab_id(lemma, surface),
                "kanji_ids": [self._kanji_by_char[ch] for ch in surface if ch in self._kanji_by_char],
                "is_particle": self._is_particle(m),
                # Layer-B placeholders (LLM fills):
                "role_pt": None, "gloss_pt": None, "conjugation_note_pt": None,
            })
        # mode-A subunits linked to their C parent by char span
        sub = []
        for am in a_morphs:
            parent = next((t["position"] for t in tokens
                           if t["begin"] <= am.begin() and am.end() <= t["end"]), None)
            if parent is not None and am.surface() != c_morphs[parent].surface():
                p = am.part_of_speech()
                sub.append({"split_mode": "A", "parent_position": parent, "surface": am.surface(),
                            "lemma": am.dictionary_form(), "reading": self._tok_kana(am),
                            "pos_coarse": p[0], "pos_fine": p[1]})
        kana = "".join(t["reading"] for t in tokens)
        # sentence romaji from the full corrected kana (handles gemination っ + long vowels correctly),
        # with particle を read as 'o'. Word boundaries from C tokens are not preserved here on purpose —
        # phonetic correctness matters more for the support-only romaji.
        romaji = jaconv.kana2alphabet(kana).replace("wo", "o") if kana else ""
        kanji_ids = sorted({kid for t in tokens for kid in t["kanji_ids"]})
        vocab_ids = sorted({t["vocab_id"] for t in tokens if t["vocab_id"]})
        particles = [{"position": t["position"], "particle": t["surface"]}
                     for t in tokens if t["is_particle"]]
        return {
            "jp": jp, "kana": kana, "romaji": romaji,
            "tokens": tokens, "subtokens": sub, "particles": particles,
            "vocab_ids": vocab_ids, "kanji_ids": kanji_ids,
        }


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
    import json
    d = Dissector()
    for s in (sys.argv[1:] or ["私はパンを食べました。", "学校へ行って、本を読んでください。"]):
        sk = d.skeleton(s)
        print(json.dumps({k: sk[k] for k in ("jp", "kana", "romaji", "particles", "vocab_ids", "kanji_ids")},
                         ensure_ascii=False))
        for t in sk["tokens"]:
            print(f"  {t['position']} {t['surface']}\t{t['lemma']}\t{t['reading']}\t{t['romaji']}\t"
                  f"{t['pos_coarse']}/{t['pos_fine']}\tvocab={t['vocab_id']}")
