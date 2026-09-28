#!/usr/bin/env python3
"""W46: the one renderer of particle explanations (design/particle_functions.md §7).

A particle occurrence carries a usage id from the closed enum in design/particle_functions.json. Its
`explanation` is NOT authored: it is `templates[usage.template][locale]` filled with `desc` and the
slots below, computed from the sentence's C tokens. The apply step (scripts/apply_particle_usage.py),
the table builder (scripts/assemble_particle_usage.py) and the hard gate
(scripts/validate/validate_particle_usage.py) all import this module, so "re-renders identically" is
checked against the same code that wrote the text.

Tokens are dicts with the export's keys: surface, lemma, pos_coarse, pos_fine, inflection.

Slots
  particle    the token surface
  chunk       the noun phrase the particle closes: chunk_head() of derive_layerb_templates_v2 (head +
              genuine modifiers, the W13b fix). A particle right after another particle (には, からは)
              takes the chunk of the first one plus the particles between (学校に). A particle right
              after a closing bracket takes the bracketed text (「博士」と).
  left        the predicate the particle attaches to: the run to its left up to punctuation or a
              particle, passing through the conjunctive て/で of a te-form (読んでいる).
  expression  compounds: the tokens the compound spans (までに). lex.fixed: the fixed expression,
              chosen by the table builder and grounded in the sentence (a prefix of it covers the
              particle in jp; see expression_grounded()).
A slot that finds nothing renders as a neutral phrase (FALLBACK), never as an empty string.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))
from derive_layerb_templates_v2 import chunk_head  # noqa: E402

PUNCT = {"補助記号", "空白"}
BRACKETS = {"」": "「", "』": "『"}
LOCALES = ("pt-BR", "en")
FALLBACK = {
    "chunk": {"pt-BR": "a parte anterior", "en": "the preceding part"},
    "left": {"pt-BR": "a oração anterior", "en": "the preceding clause"},
}
TEMPLATE_SLOTS = {"chunk", "left", "expression"}

Tok = dict[str, Any]


def load_enum(root: Path) -> dict[str, Any]:
    pf = json.loads((root / "design" / "particle_functions.json").read_text(encoding="utf-8"))
    return {"usages": {u["id"]: u for u in pf["usages"]}, "templates": pf["templates"],
            "classes": {c["id"]: c for c in pf["classes"]}, "version": pf["schema_version"]}


def chunk_slot(toks: list[Tok], i: int) -> str | None:
    j = i
    while j > 0 and toks[j - 1]["pos_coarse"] == "助詞":
        j -= 1
    if j > 0 and toks[j - 1]["surface"] in BRACKETS:           # 「博士」と呼ばれる: the quoted text
        open_ = BRACKETS[toks[j - 1]["surface"]]
        k = next((k for k in range(j - 2, -1, -1) if toks[k]["surface"] == open_), None)
        if k is not None:
            return "".join(t["surface"] for t in toks[k:i])
    head = chunk_head(toks, j)
    return head + "".join(t["surface"] for t in toks[j:i]) if head else None


def left_slot(toks: list[Tok], i: int) -> str | None:
    k = i - 1
    while k >= 0:
        t = toks[k]
        if t["pos_coarse"] in PUNCT:
            break
        if t["pos_coarse"] == "助詞" and not (t.get("pos_fine") == "接続助詞" and t["surface"] in ("て", "で")):
            break
        k -= 1
    return "".join(t["surface"] for t in toks[k + 1:i]) or None


def forms(u: dict[str, Any]) -> list[str]:
    """Surfaces a usage is spelled with: a compound is ONE spelling (particle + the remaining tokens)."""
    if u["compound"]:
        return [u["particle"] + "".join(u["allomorphs"])]
    return [u["particle"], *u["allomorphs"]]


def span_spelling(toks: list[Tok], i: int, spellings: list[str]) -> list[int] | None:
    """Positions of the shortest contiguous token span containing i that spells one of `spellings`."""
    longest = max(len(s) for s in spellings)
    for a in range(i, -1, -1):
        if sum(len(t["surface"]) for t in toks[a:i]) >= longest:
            break
        text = ""
        for b in range(a, len(toks)):
            text += toks[b]["surface"]
            if len(text) > longest:
                break
            if b >= i and text in spellings:
                return list(range(a, b + 1))
    return None


def surface_matches(toks: list[Tok], i: int, u: dict[str, Any]) -> bool:
    if u["id"] == "lex.fixed":
        return True
    fs = forms(u)
    if not u["compound"] and toks[i]["surface"] in fs:
        return True
    return span_spelling(toks, i, fs) is not None


def _jp_offsets(toks: list[Tok], i: int) -> tuple[str, int, int]:
    jp = "".join(t["surface"] for t in toks)
    begin = sum(len(t["surface"]) for t in toks[:i])
    return jp, begin, begin + len(toks[i]["surface"])


def expression_grounded(toks: list[Tok], i: int, expr: str) -> bool:
    """A prefix of `expr` longer than the particle occurs in the sentence covering the particle.

    Dictionary forms count (気にかける grounds 気にかけて), a free-floating phrase does not.
    """
    jp, begin, end = _jp_offsets(toks, i)
    for n in range(len(expr), len(toks[i]["surface"]), -1):
        p = expr[:n]
        start = jp.find(p)
        while start != -1:
            if start <= begin and start + n >= end:
                return True
            start = jp.find(p, start + 1)
    return False


def fallback_expression(toks: list[Tok], i: int) -> str:
    """The particle with its non-punctuation neighbours (the table builder's last resort)."""
    lo = i - 1 if i > 0 and toks[i - 1]["pos_coarse"] not in PUNCT else i
    hi = i + 1 if i + 1 < len(toks) and toks[i + 1]["pos_coarse"] not in PUNCT else i
    return "".join(t["surface"] for t in toks[lo:hi + 1])


def slots_for(enum: dict[str, Any], usage: str, toks: list[Tok], i: int,
              expression: str | None = None) -> dict[str, Any]:
    """The template slots of one occurrence. `expression` is only read for lex.fixed."""
    u = enum["usages"][usage]
    need = set(enum["templates"][u["template"]]["slots"]) & TEMPLATE_SLOTS
    out: dict[str, Any] = {}
    if "chunk" in need:
        out["chunk"] = chunk_slot(toks, i)
    if "left" in need:
        out["left"] = left_slot(toks, i)
    if "expression" in need:
        if u["compound"]:
            span = span_spelling(toks, i, forms(u))
            out["expression"] = "".join(toks[k]["surface"] for k in span) if span else None
        else:
            out["expression"] = expression
    return out


def render(enum: dict[str, Any], usage: str, particle: str, slots: dict[str, Any]) -> dict[str, str]:
    u = enum["usages"][usage]
    tpl = enum["templates"][u["template"]]
    out = {}
    for loc in LOCALES:
        vals = {"particle": particle, "desc": u["desc"][loc]}
        for k in TEMPLATE_SLOTS:
            if k in slots:
                vals[k] = slots[k] if slots[k] is not None else FALLBACK.get(k, {}).get(loc, "")
        out[loc] = tpl[loc].format(**vals)
    return out


def _selftest() -> int:
    root = Path(__file__).resolve().parents[1]
    enum = load_enum(root)

    def T(spec: str) -> list[Tok]:
        out = []
        for part in spec.split():
            s, pc, pf = (part.split("/") + ["", ""])[:3]
            out.append({"surface": s, "lemma": s, "pos_coarse": pc, "pos_fine": pf, "inflection": None})
        return out

    toks = T("七/名詞/数詞 時/名詞/助数詞 に/助詞/格助詞 起き/動詞/一般 ます/助動詞/*")
    s = slots_for(enum, "ni.time-point", toks, 2)
    assert render(enum, "ni.time-point", "に", s)["pt-BR"] == "に marca 七時 como o momento em que a ação acontece.", s
    toks = T("学校/名詞/普通名詞 に/助詞/格助詞 は/助詞/係助詞 行く/動詞/一般")
    assert chunk_slot(toks, 2) == "学校に"
    toks = T("「/補助記号/括弧開 博士/名詞/普通名詞 」/補助記号/括弧閉 と/助詞/格助詞 呼ぶ/動詞/一般")
    assert chunk_slot(toks, 3) == "「博士」"
    toks = T("五/名詞/数詞 時/名詞/助数詞 まで/助詞/副助詞 に/助詞/格助詞 帰る/動詞/一般")
    assert slots_for(enum, "madeni.deadline", toks, 3) == {"expression": "までに"}
    assert render(enum, "madeni.deadline", "に", {"expression": "までに"})["pt-BR"].startswith("までに funciona")
    toks = T("撮っ/動詞/一般 て/助詞/接続助詞 は/助詞/係助詞 いけ/動詞/一般 ない/助動詞/*")
    assert surface_matches(toks, 2, enum["usages"]["teha.condition"])
    assert surface_matches(toks, 1, enum["usages"]["teha.condition"])
    assert not surface_matches(toks, 2, enum["usages"]["ga.subject"])
    toks = T("読ん/動詞/一般 で/助詞/接続助詞 いる/動詞/非自立可能 から/助詞/接続助詞 、/補助記号/読点")
    assert left_slot(toks, 3) == "読んでいる"
    toks = T("気/名詞/普通名詞 に/助詞/格助詞 かけ/動詞/一般 て/助詞/接続助詞")
    assert expression_grounded(toks, 1, "気にかける") and not expression_grounded(toks, 1, "役に立つ")
    assert render(enum, "ha.topic", "は", {"chunk": None})["pt-BR"] == "は destaca a parte anterior: o tópico da frase (o assunto do qual se fala)."
    print("particle_usage_render selftest: ok")
    return 0


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
    sys.exit(_selftest())
