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
# only content tokens are linked to the vocab registry (avoids particle/aux false matches に→二)
CONTENT_POS = {"名詞", "動詞", "形容詞", "形状詞", "副詞", "代名詞", "連体詞", "接続詞", "感動詞"}
KANJI_RE = __import__("re").compile(r"[一-鿿㐀-䶿]")

# Neutral (language-agnostic) enums derived mechanically from Sudachi/UniDic POS (Layer A). The raw
# Japanese pos_coarse/pos_fine/inflection strings are kept too, for traceability.
POS_MAP = {
    "名詞": "noun", "代名詞": "pronoun", "動詞": "verb", "形容詞": "i-adjective",
    "形状詞": "na-adjective", "副詞": "adverb", "連体詞": "adnominal", "接続詞": "conjunction",
    "感動詞": "interjection", "助詞": "particle", "助動詞": "auxiliary", "接頭辞": "prefix",
    "接尾辞": "suffix", "補助記号": "punctuation", "記号": "symbol", "空白": "whitespace",
    "数詞": "numeral", "フィラー": "filler",
}
# Sudachi 活用形 (inflection form), base part before the '-' euphonic suffix -> neutral enum.
INFLECTION_MAP = {
    "未然形": "irrealis", "連用形": "continuative", "終止形": "terminal", "連体形": "attributive",
    "仮定形": "conditional", "命令形": "imperative", "意志推量形": "volitional", "語幹": "stem",
    "ク語法": "ku-form",
}
# Sudachi 助詞 subtype (pos_fine) -> neutral particle function enum (standard joshi classification).
PARTICLE_FUNCTION_MAP = {
    "格助詞": "case", "係助詞": "binding", "副助詞": "adverbial", "接続助詞": "conjunctive",
    "終助詞": "sentence-final", "準体助詞": "nominalizer", "並立助詞": "parallel",
}
# Hepburn gemination: doubling consonant borrowed from the following mora's initial.
_GEMINATE_FIRST = {"c": "t"}  # ち/ちゃ… (chi/cha) geminate as っち = "tchi"


def hira(s: str) -> str:
    return jaconv.kata2hira(s or "")


def neutral_inflection(infl_form: str) -> str | None:
    """Map a Sudachi 活用形 (e.g. '連用形-促音便', '命令形') to a neutral enum, else None."""
    if not infl_form or infl_form == "*":
        return None
    base = infl_form.split("-", 1)[0]
    return INFLECTION_MAP.get(base)


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

    @staticmethod
    def _fix_sokuon_romaji(tokens: list[dict]) -> None:
        """jaconv renders a TRAILING small っ as IME-style 'xtsu' (e.g. 行っ→'ixtsu'). Realize the
        gemination in Hepburn by doubling the following mora's initial consonant onto this token
        (行っ + た → 'it' + 'ta' = 'itta'); drop it if there is no consonant to borrow."""
        for i, t in enumerate(tokens):
            r = t["romaji"]
            if not r or "xtsu" not in r:
                continue
            base = r[: r.index("xtsu")]
            nxt = tokens[i + 1]["romaji"] if i + 1 < len(tokens) else ""
            geminate = ""
            if nxt and nxt[0] not in "aeiou":  # gemination only before a consonant
                geminate = _GEMINATE_FIRST.get(nxt[0], nxt[0])
            t["romaji"] = base + geminate

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
                # neutral mechanical enums (Layer A) + raw Sudachi inflection for traceability
                "pos": POS_MAP.get(p[0]),
                "inflection": neutral_inflection(p[5]),
                "inflection_type": p[4] if p[4] and p[4] != "*" else None,
                "begin": m.begin(), "end": m.end(),
                "vocab_id": self._vocab_id(lemma, surface) if p[0] in CONTENT_POS else None,
                "kanji_ids": [self._kanji_by_char[ch] for ch in surface if ch in self._kanji_by_char],
                "is_particle": self._is_particle(m),
                "particle_function": PARTICLE_FUNCTION_MAP.get(p[1]) if self._is_particle(m) else None,
                # Layer-B placeholders (LLM fills):
                "role_pt": None, "gloss_pt": None, "conjugation_note_pt": None,
            })
        self._fix_sokuon_romaji(tokens)
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
        particles = [{"position": t["position"], "particle": t["surface"],
                      "function_type": t["particle_function"]}
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
