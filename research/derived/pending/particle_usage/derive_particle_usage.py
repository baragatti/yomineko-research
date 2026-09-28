#!/usr/bin/env python3
"""Particle usage derivation (migration step M3, research/reports/particle_taxonomy_research.md §4 and §6).

Assigns a usage id from design/particle_functions.json to every particle occurrence where the mechanical
tier is `auto`, and packages every other occurrence for the enum-constrained author/verifier pass (M5)
or a ruling (M6). Also derives the token items of design/token_roles.json that follow mechanically
(function by POS, aux_function by lemma, chunk_role from the closing particle's usage).

Inputs (read-only):
  * the DB, snapshotted with the sqlite3 backup API (never opened for writing): particle rows bound to
    their C token (`particle.token_id`), tokens, localized labels/explanations/roles, pattern_json;
  * corpus/sentences/bank.json at git HEAD (jp + translations; cross-checked against the DB);
  * design/particle_functions.json (usages, classes, cues, lexicons) and design/token_roles.json;
  * SudachiPy (full dict, mode C) for the 3rd POS field (形状詞可能, 助数詞可能) and 形状詞 subclass (タリ).
    Optional: without it the cues that need those fields fall back to the DB's two POS fields.

Tiers (report §4.1):
  auto        the (surface, class) admits one usage, a unique compound (までに, について, かな, かい),
              or a cue and the label independently agree              -> derived.json
  default     no specific signal; the pair's default by exclusion     -> work files
  cue-only    a cue fired; label silent, ambiguous or only the modal  -> work files
  label-only  an occurrence-specific label maps to a usage; no cue    -> work files
  lexicalized the label says "part of a fixed expression" -> lex.fixed -> work files
  ruling      cue vs specific label disagree, or no signal/no default -> work files

Outputs (files only, under the output dir):
  derived.json               auto rows + meta (tier counts, per-pair table, work-file index)
  work-NN.json               <= 300 rows each, one tier per file, n5 first
  token_roles_derived.json   per-sentence token function / aux_function / chunk / chunk_role / role

Usage: derive_particle_usage.py [--db PATH] [--bank PATH|git] [--out DIR] [--selftest]
"""
from __future__ import annotations

import argparse
import collections
import datetime as dt
import glob
import hashlib
import importlib.util
import json
import os
import re
import sqlite3
import subprocess
import sys
from pathlib import Path
from typing import Any, Callable, Iterable

sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]

ROOT = next(p for p in Path(__file__).resolve().parents if (p / "design" / "particle_functions.json").exists())
DEFAULT_OUT = ROOT / "research" / "derived" / "pending" / "particle_usage"
WORK_ROWS = 300
LEVEL_ORDER = {"n5": 0, "n4": 1, "n3": 2, "n2": 3, "n1": 4}
TIER_ORDER = ["cue-only", "label-only", "default", "lexicalized", "ruling"]

FT_TO_UNIDIC = {"case": "格助詞", "binding": "係助詞", "adverbial": "副助詞", "conjunctive": "接続助詞",
                "sentence-final": "終助詞", "nominalizer": "準体助詞"}
NOMINAL = {"名詞", "代名詞", "接尾辞", "接頭辞"}
PRED = {"動詞", "形容詞", "形状詞"}
PUNCT = {"補助記号", "空白"}
CLOSE_BRACKETS = {"」", "』", "）", ")", "】", "〕", "”", "’"}

# Script-local lexicon: next.stative-predicate names its lemmas only by example in the design doc.
# ponytail: local list; the apply unit should publish it as cue_lexicons.STATIVE in particle_functions.json.
STATIVE = {"好き", "嫌い", "大好き", "大嫌い", "分かる", "判る", "解る", "出来る", "できる", "欲しい", "上手",
           "下手", "得意", "苦手", "要る", "見える", "聞こえる", "怖い", "羨ましい", "必要"}
TIME_COUNTERS = {"時", "分", "日", "月", "年", "曜日", "秒", "時半"}
PERIOD_TAIL = ("日", "週", "週間", "月", "年", "時間", "ヶ月", "か月", "カ月")

# Pair defaults by exclusion (report §4.1 `default`). に, と/case, まで, か/adverbial, って, な and
# の/sentence-final have none on purpose: their modal label is not a safe default (report §4.2).
PAIR_DEFAULT = {
    ("は", "binding"): "ha.topic", ("を", "case"): "wo.object", ("が", "case"): "ga.subject",
    ("で", "case"): "de.location-action", ("て", "conjunctive"): "te.sequence",
    ("で", "conjunctive"): "te.sequence", ("の", "case"): "no.noun-modifier",
    ("か", "sentence-final"): "ka.question", ("も", "binding"): "mo.also",
    ("よ", "sentence-final"): "yo.assertion", ("の", "nominalizer"): "no.nominalizer",
    ("ん", "nominalizer"): "no.explanatory", ("から", "case"): "kara.starting-point",
    ("が", "conjunctive"): "ga.contrast", ("けど", "conjunctive"): "kedo.contrast",
    ("けれど", "conjunctive"): "kedo.contrast", ("けれども", "conjunctive"): "kedo.contrast",
    ("より", "case"): "yori.comparison", ("ばかり", "adverbial"): "bakari.only",
}
# Cue combination per usage: the JSON lists cue ids; ALL of them must fire unless listed here.
CUE_ANY = {"ha.contrast", "ni.agent", "to.comitative"}
# ga.preface: the design's `clause-final` never holds before the comma of すみませんが、, so the
# preface lemma alone is the cue.
CUE_OVERRIDE = {"ga.preface": ["prev.preface-lemma"]}
# Usages whose pair-unique assignment is not trusted (report §4.3: 来たって was た + って).
NEVER_UNIQUE = {"tatte.concessive"}

# When several cues fire, the dominated usage is dropped (winner -> losers).
CUE_DOMINANCE: dict[str, set[str]] = {
    "ni.result": {"ni.adverbial", "ni.goal", "ni.location-existence", "ni.target", "ni.standard",
                  "ni.recipient", "ni.time-point"},
    "ni.purpose": {"ni.goal", "ni.location-existence"},
    "ni.frequency": {"ni.time-point"},
    "ni.time-point": {"ni.goal", "ni.location-existence", "ni.recipient", "ni.agent", "ni.causee",
                      "ni.adverbial"},
    "ni.agent": {"ni.recipient", "ni.goal", "ni.location-existence", "ni.target"},
    "ni.causee": {"ni.recipient", "ni.goal", "ni.location-existence"},
    "te.subsidiary": {"te.manner", "te.request"},
    "te.cause": {"te.parallel"},
    "de.copula": {"de.means", "de.material", "de.cause", "de.scope", "de.limit", "de.manner"},
    "de.manner": {"de.limit"},
    "no.explanatory": {"no.nominalizer", "no.pronoun"},
    "mo.concessive": {"mo.also", "mo.both", "mo.total-negation", "mo.emphasis-quantity"},
    "mo.total-negation": {"mo.both"},
    "ka.invitation": {"ka.question"},
    "ka.acknowledgment": {"ka.question"},
    "to.result": {"to.comitative", "to.parallel", "to.quotative", "to.comparison"},
    "to.comparison": {"to.comitative", "to.parallel"},
    "to.adverbial": {"to.quotative", "to.comitative"},
    "made.until": {"made.as-far-as"},
    "kara.after": {"kara.source", "kara.material"},
    "ga.preface": {"ga.contrast"},
}
LABEL_DOMINANCE: dict[str, set[str]] = {
    "te.subsidiary": {"te.request"},
    "ka.invitation": {"ka.question"},
    "ga.stative-object": {"ga.subject"},
    "no.explanatory": {"no.nominalizer"},
}
LEX_RE = re.compile(r"part of|component of|\bcomponent\b|fixed (expression|locution|phrase)|set phrase|idiom|"
                    r"locution|forms? (the )?(connector|conjunction|word|expression|adverb)|within the word|"
                    r"lexicali[sz]ed|frozen")
# English label keywords -> usages (a one-off migration signal; report §4.1). Intersected with the
# row's candidates, so e.g. "explanat" resolves by class.
LABEL_RULES: list[tuple[str, list[str]]] = [
    (r"contrast", ["ha.contrast"]), (r"topic|theme", ["ha.topic", "tte.topic"]),
    (r"desired|liking|\blike|ability|emotion|\bneed|object of (the )?(state|feeling|desire)|stative",
     ["ga.stative-object"]),
    (r"subject|nominative", ["ga.subject", "no.subject-in-modifier"]),
    (r"\bbut\b|adversative|although|though|however", ["ga.contrast", "kedo.contrast"]),
    (r"preface|softening|introduc|opener|hesita|trailing|background", ["ga.preface", "kedo.softening"]),
    (r"route|path|travers|through", ["wo.path"]),
    (r"departure|leav|left behind|exit", ["wo.departure"]),
    (r"causee|causative", ["wo.causee", "ni.causee"]),
    (r"direct.object|accusative|object marker|object particle", ["wo.object"]),
    (r"existence|exists|location", ["ni.location-existence"]),
    (r"destination|direction|\bgoal|toward|arrival", ["ni.goal", "he.direction", "made.as-far-as"]),
    (r"point in time|\btime\b|moment|\bdate\b|\bhour", ["ni.time-point"]),
    (r"purpose|in order to", ["ni.purpose", "noni.purpose"]),
    (r"recipient|addressee|indirect object|dative|receiver|interlocutor|to whom", ["ni.recipient"]),
    (r"\bagent|passive|by whom", ["ni.agent"]),
    (r"from whom|source|sender", ["ni.source", "kara.source"]),
    (r"result|transform|becom", ["ni.result", "to.result"]),
    (r"frequency|\brate\b|\bper\b", ["ni.frequency"]),
    (r"standard|reference|criterion", ["ni.standard", "to.comparison", "yori.comparison"]),
    (r"compar|\bthan\b", ["to.comparison", "yori.comparison"]),
    (r"target", ["ni.target"]),
    (r"cause|reason|because", ["ni.cause", "de.cause", "kara.reason", "te.cause", "node.reason"]),
    (r"adverb", ["ni.adverbial", "to.adverbial"]),
    (r"quot|content of|thought|citation|hearsay|reported", ["to.quotative", "tte.quotative"]),
    (r"enumerat|listing|\band\b|parallel", ["to.parallel", "ya.partial-list", "te.parallel", "mo.both"]),
    (r"accompan|companion|together|\bwith\b|partner|reciproc", ["to.comitative"]),
    (r"condition|whenever|\bwhen\b|\bif\b", ["to.conditional", "ba.conditional", "teha.condition"]),
    (r"naming|called|named", ["toiu.naming"]),
    (r"place of (the )?action|place where|place of occurrence|locative", ["de.location-action"]),
    (r"means|instrument|tool|method|language", ["de.means"]),
    (r"material|made (of|from)|raw", ["de.material", "kara.material"]),
    (r"scope|extent|range|among|within", ["de.scope"]),
    (r"\blimit|total|\bsum\b", ["de.limit"]),
    (r"manner|alone|\bstate\b", ["de.manner", "te.manner"]),
    (r"copula|だ|nominal predicate", ["de.copula"]),
    (r"starting|\bfrom\b|origin|\bstart", ["kara.starting-point", "yori.starting-point"]),
    (r"\bafter\b|てから|te-kara", ["kara.after"]),
    (r"until|up to", ["made.until"]),
    (r"deadline|\bby\b", ["madeni.deadline"]),
    (r"\beven\b", ["made.even", "sae.even", "demo.even"]),
    (r"link|possess|genitive|attributive|modif|\bof\b", ["no.noun-modifier"]),
    (r"nominali[sz]", ["no.nominalizer"]),
    (r"explanat|のだ|んです|のです", ["no.explanatory", "no.final-explanation"]),
    (r"pronoun|the one|substitut", ["no.pronoun"]),
    (r"question|interrog", ["no.final-question", "ka.question"]),
    (r"also|\btoo\b|inclusion|addition", ["mo.also"]),
    (r"both|neither", ["mo.both"]),
    (r"negat|not even|nothing|nobody|\bnone\b", ["mo.total-negation"]),
    (r"quantity|as many|as much|as long", ["mo.emphasis-quantity"]),
    (r"concess|even if|even though|ても", ["mo.concessive", "tatte.concessive"]),
    (r"sequen|and then|successive", ["te.sequence"]),
    (r"subsidiary|auxiliary verb|ている|てください|くださ|てみる|てしまう|ておく|progressive|てある|"
     r"てもらう|てくれる|てあげる|てくる|ていく|continuous", ["te.subsidiary"]),
    (r"request|casual command", ["te.request"]),
    (r"invit|proposal|suggest", ["ka.invitation"]),
    (r"acknowledg|realiz|そうですか", ["ka.acknowledgment"]),
    (r"wonder|doubt|かな", ["kana.wondering"]),
    (r"alternative|\bor\b|choice|either", ["ka.alternative"]),
    (r"indefinite|some(one|thing|where|how|body)?\b|uncertain", ["ka.indefinite"]),
    (r"embedded|indirect|whether", ["ka.embedded-question"]),
    (r"urg|encourag|let's|insist|exhort", ["yo.urging"]),
    (r"assert|emphasis|emphatic|inform|warning|assur|promise", ["yo.assertion"]),
    (r"prohibit|don't|negative imperative", ["na.prohibition"]),
    (r"exclam|admir|musing|feeling|reflect|emotive", ["na.emotive"]),
    (r"soft order|なさい", ["na.soft-command"]),
    (r"just (done|did|happened)|たばかり|recently", ["bakari.just-done"]),
    (r"only|nothing but|always", ["bakari.only"]),
]
LABEL_RULES_C = [(re.compile(p), us) for p, us in LABEL_RULES]


# ----------------------------------------------------------------------------------------------- data
class Tok(dict):
    """One C-mode token: surface s, lemma l, pos_coarse pc, pos_fine pf, inflection inf, pos3, pos2."""


def load_design() -> tuple[dict[str, Any], dict[str, Any]]:
    pf = json.loads((ROOT / "design" / "particle_functions.json").read_text(encoding="utf-8"))
    tr = json.loads((ROOT / "design" / "token_roles.json").read_text(encoding="utf-8"))
    return pf, tr


def snapshot(db_path: Path) -> sqlite3.Connection:
    src = sqlite3.connect(f"file:{db_path.as_posix()}?mode=ro", uri=True)
    mem = sqlite3.connect(":memory:")
    src.backup(mem)
    src.close()
    return mem


def load_bank(spec: str) -> tuple[list[dict[str, Any]], str]:
    if spec == "git":
        head = subprocess.run(["git", "-C", str(ROOT), "rev-parse", "HEAD"], capture_output=True, text=True,
                              check=True).stdout.strip()
        raw = subprocess.run(["git", "-C", str(ROOT), "show", "HEAD:corpus/sentences/bank.json"],
                             capture_output=True, check=True).stdout
        return json.loads(raw), f"git:{head}"
    return json.loads(Path(spec).read_text(encoding="utf-8")), spec


def sudachi_pos(sentences: dict[int, tuple[str, list[Tok]]]) -> tuple[int, int]:
    """Attach Sudachi's full POS tuple (pos2, pos3) to tokens when mode-C surfaces align. Returns
    (aligned, total)."""
    try:
        from sudachipy import dictionary, tokenizer  # type: ignore[import-not-found]
    except ImportError:
        return 0, len(sentences)
    tk = dictionary.Dictionary(dict="full").create()
    mode = tokenizer.Tokenizer.SplitMode.C
    ok = 0
    for jp, toks in sentences.values():
        ms = tk.tokenize(jp, mode)
        if [m.surface() for m in ms] != [t["s"] for t in toks]:
            continue
        ok += 1
        for m, t in zip(ms, toks):
            p = m.part_of_speech()
            t["pos2"], t["pos3"] = p[1], p[2]
    return ok, len(sentences)


# ----------------------------------------------------------------------------------------------- cues
class Ctx:
    """Cue evaluation context for the particle at index i of a sentence's C tokens."""

    def __init__(self, toks: list[Tok], i: int, lex: dict[str, set[str]], sent_particles: list[str]):
        self.t, self.i, self.lex, self.sp = toks, i, lex, sent_particles

    def at(self, k: int) -> Tok | None:
        return self.t[k] if 0 <= k < len(self.t) else None

    @property
    def prev(self) -> Tok | None:
        return self.at(self.i - 1)

    @property
    def next(self) -> Tok | None:
        return self.at(self.i + 1)

    def clause_end(self) -> int:
        for k in range(self.i + 1, len(self.t)):
            if self.t[k]["pc"] in PUNCT:
                return k
        return len(self.t)

    def clause_start(self) -> int:
        for k in range(self.i - 1, -1, -1):
            if self.t[k]["pc"] in PUNCT:
                return k + 1
        return 0

    def first_pred(self) -> int | None:
        end = self.clause_end()
        for k in range(self.i + 1, end):
            t = self.t[k]
            if t["pc"] in PRED:
                # a verbal noun right before する/できる is the predicate (散歩する, 参加できる)
                return k
        return None

    def pred_lemmas(self) -> set[str]:
        k = self.first_pred()
        if k is None:
            return set()
        out = {self.t[k]["l"]}
        p1, p2 = self.at(k - 1), self.at(k - 2)
        if k - 1 > self.i and p1 and p1["pc"] == "名詞":
            out.add(p1["l"])                      # 散歩 + する, 参加 + できる
        if k - 2 > self.i and p1 and p2 and p1["s"] == "を" and p2["pc"] == "名詞":
            out.add(p2["l"])                      # 気 を つける
        return out

    def aux_run_after(self, k: int) -> list[Tok]:
        out = []
        for j in range(k + 1, len(self.t)):
            if self.t[j]["pc"] == "助動詞" or (self.t[j]["pc"] == "動詞" and self.t[j]["l"] in ("させる", "せる")):
                out.append(self.t[j])
            else:
                break
        return out

    def strict_clause_final(self) -> bool:
        k = self.i + 1
        while k < len(self.t) and self.t[k]["s"] in CLOSE_BRACKETS:
            k += 1
        n = self.at(k)
        return n is None or n["pf"] == "句点" or (n["pc"] == "助詞" and n["pf"] == "終助詞")


def _is_num(t: Tok | None) -> bool:
    return bool(t) and t["pf"] == "数詞"


def _neg_until_break(c: Ctx) -> bool:
    for k in range(c.i + 1, c.clause_end()):
        t = c.t[k]
        if t["l"] in c.lex["NEG"] and t["pc"] in ("助動詞", "形容詞"):
            return True
    return False


def _pred_in(name: str) -> Callable[[Ctx], bool]:
    return lambda c: bool(c.pred_lemmas() & c.lex[name])


def _aux_after_pred(lemmas: set[str]) -> Callable[[Ctx], bool]:
    def f(c: Ctx) -> bool:
        k = c.first_pred()
        return k is not None and any(t["l"] in lemmas for t in c.aux_run_after(k))
    return f


def _temorau(c: Ctx) -> bool:
    k = c.first_pred()
    a, b = (c.at(k + 1), c.at(k + 2)) if k is not None else (None, None)
    return bool(a and b and a["s"] in ("て", "で") and b["l"] in ("もらう", "貰う", "いただく", "頂く"))


CUES: dict[str, Callable[[Ctx], bool]] = {
    "aux.causative": _aux_after_pred({"せる", "させる"}),
    "aux.passive": _aux_after_pred({"れる", "られる"}),
    "clause-final": lambda c: c.strict_clause_final(),
    "not.clause-final": lambda c: not c.strict_clause_final(),
    "clause.ichiban": lambda c: any(t["l"] in ("一番", "最も") for t in c.t[c.clause_start():c.clause_end()]),
    "clause.negative": _neg_until_break,
    "next.case-particle": lambda c: bool(c.next) and c.next["pc"] == "助詞" and c.next["pf"] in ("格助詞", "係助詞"),
    "next.comparison": _pred_in("COMPAR"),
    "next.copula": lambda c: bool(c.next) and c.next["pc"] == "助動詞" and c.next["l"] in ("だ", "です"),
    "next.emotion": lambda c: bool(c.next) and (c.next["l"] in c.lex["EMO"] or c.next["l"] in (
        "すみません", "済みません", "ありがとう", "嬉しい", "残念") or c.next["s"].startswith(("すみ", "すい"))),
    "next.issho": lambda c: bool(c.next) and c.next["l"] in ("一緒", "共"),
    "next.motion-verb": lambda c: bool(c.next) and c.next["l"] in ("行く", "来る", "帰る", "出かける", "戻る"),
    "next.nai-aru": lambda c: (lambda n: bool(n) and n["l"] in ("ない", "無い", "ある", "有る", "在る")
                               and n["pc"] in ("形容詞", "動詞", "助動詞"))(
        c.at(c.i + 2) if c.next and c.next["s"] in ("は", "も") else c.next),
    "next.naru-suru": lambda c: bool(c.next) and c.next["l"] in ("なる", "成る", "する", "為る", "変わる", "変える"),
    "next.not-saying-verb": lambda c: (not c.strict_clause_final() and c.first_pred() is not None
                                       and not (c.pred_lemmas() & c.lex["SAYING"])),
    "next.noun": lambda c: bool(c.next) and c.next["pc"] in NOMINAL,
    "next.predicate": lambda c: bool(c.next) and c.next["pc"] in PRED,
    "next.question-mark": lambda c: bool(c.next) and c.next["s"] in ("？", "?"),
    "next.standard-predicate": _pred_in("STANDARD"),
    "next.start-verb": lambda c: bool(c.pred_lemmas() & {"始まる", "開始", "始める"}),
    "next.stative-predicate": lambda c: bool(c.pred_lemmas() & STATIVE) or (
        c.first_pred() is not None and any(t["l"] == "たい" for t in c.aux_run_after(c.first_pred()))),
    "next.subsidiary": lambda c: bool(c.next) and c.next["pc"] in ("動詞", "形容詞", "助動詞")
    and c.next["l"] in c.lex["SUBSID"],
    "next.temorau": _temorau,
    "next.use-evaluate": lambda c: bool(c.pred_lemmas() & {"使う", "便利", "いい", "良い", "必要", "役立つ", "役に立つ"}),
    "prev.adjective": lambda c: bool(c.prev) and c.prev["pc"] == "形容詞",
    "prev.adjective-or-noun": lambda c: bool(c.prev) and (c.prev["pc"] == "形容詞" or c.prev["pc"] in NOMINAL),
    "prev.adverb": lambda c: bool(c.prev) and (c.prev["pc"] == "副詞" or (
        c.prev["pc"] == "形状詞" and c.prev.get("pos2") == "タリ")),
    "prev.cause-noun": lambda c: bool(c.prev) and c.prev["l"] in c.lex["CAUSE_N"],
    "prev.continuative": lambda c: bool(c.prev) and c.prev["pc"] == "動詞" and c.prev["inf"] == "continuative",
    "prev.interrogative": lambda c: bool(c.prev) and c.prev["l"] in c.lex["INTERROG"],
    "prev.manner-noun": lambda c: bool(c.prev) and c.prev["l"] in c.lex["MANNER"],
    "prev.masen": lambda c: bool(c.at(c.i - 2) and c.prev) and c.at(c.i - 2)["l"] == "ます" and c.prev["l"] in ("ぬ", "ず"),
    "prev.means-noun": lambda c: bool(c.prev) and (c.prev["l"] in c.lex["MEANS"] or (
        c.prev["pc"] == "名詞" and c.prev["s"].endswith("語"))),
    "prev.na-stem": lambda c: bool(c.prev) and (c.prev["pc"] == "形状詞" or (
        c.prev["pc"] == "名詞" and c.prev.get("pos3") == "形状詞可能")),
    "prev.noun-next.noun": lambda c: bool(c.prev and c.next) and c.prev["pc"] in NOMINAL and c.next["pc"] in NOMINAL,
    "prev.number": lambda c: _is_num(c.prev) or (bool(c.prev) and c.prev["pc"] in ("接尾辞", "名詞")
                                                   and c.prev["pf"] != "数詞" and _is_num(c.at(c.i - 2))),
    "prev.particle": lambda c: bool(c.prev) and c.prev["pc"] == "助詞",
    "prev.period-next.number": lambda c: bool(c.prev) and c.prev["s"].endswith(PERIOD_TAIL) and _is_num(c.next),
    "prev.predicate": lambda c: bool(c.prev) and c.prev["pc"] in PRED | {"助動詞"},
    "prev.preface-lemma": lambda c: any(t and (t["l"] in c.lex["PREFACE"] or t["s"].startswith(("すみ", "すい")))
                                        for t in (c.prev, c.at(c.i - 2))),
    "prev.sou-desu": lambda c: bool(c.at(c.i - 2) and c.prev) and c.at(c.i - 2)["s"] == "そう" and c.prev["l"] == "です",
    "prev.ta": lambda c: bool(c.prev) and c.prev["pc"] == "助動詞" and c.prev["l"] == "た",
    "prev.te": lambda c: bool(c.prev) and c.prev["pc"] == "助詞" and c.prev["s"] in ("て", "で") and c.prev["pf"] == "接続助詞",
    "prev.time-noun": lambda c: bool(c.prev) and (c.prev["l"] in c.lex["TIME"] or (
        c.prev["l"] in TIME_COUNTERS and (_is_num(c.at(c.i - 2)) or c.prev.get("pos3") == "助数詞可能"))),
    "prev.verb-terminal": lambda c: bool(c.prev) and c.prev["pc"] == "動詞" and c.prev["inf"] in ("terminal", "attributive"),
    "prev.volitional-or-te": lambda c: bool(c.prev) and (c.prev["inf"] in ("volitional", "imperative")
                                                         or c.prev["l"] in ("う", "よう")
                                                         or (c.prev["pc"] == "助詞" and c.prev["s"] in ("て", "で"))),
    "sentence.two-ha": lambda c: c.sp.count("は") >= 2,
    "sentence.two-mo": lambda c: c.sp.count("も") >= 2,
    "verb.departure": _pred_in("DEPART"),
    "verb.emotion-cause": _pred_in("EMO"),
    "verb.existence": _pred_in("EXIST"),
    "verb.giving-telling": _pred_in("GIVE"),
    "verb.make": _pred_in("MAKE"),
    "verb.motion": _pred_in("MOTION"),
    "verb.path": _pred_in("PATH"),
    "verb.receiving": _pred_in("RECEIVE"),
    "verb.reciprocal": _pred_in("RECIP"),
    "verb.saying": _pred_in("SAYING"),
    "verb.target": _pred_in("TARGET"),
}


# ----------------------------------------------------------------------------------------------- classifier
class Enum:
    """The usage enum plus the lookups the classifier needs."""

    def __init__(self, pf: dict[str, Any]):
        self.usages = {u["id"]: u for u in pf["usages"]}
        self.class_pos = {c["id"]: set(c["unidic_pos_fine"]) for c in pf["classes"]}
        self.lex = {k: set(v) for k, v in pf["cue_lexicons"].items()}
        self.usage_cues: dict[str, tuple[str, list[str]]] = {}
        for u in pf["usages"]:
            cues = CUE_OVERRIDE.get(u["id"], u["cues"])
            if cues:
                self.usage_cues[u["id"]] = ("any" if u["id"] in CUE_ANY else "all", cues)
        missing = {c for _, cs in self.usage_cues.values() for c in cs} - CUES.keys()
        if missing:
            raise SystemExit(f"cue ids without an implementation: {sorted(missing)}")
        undefined = {c for _, cs in self.usage_cues.values() for c in cs} - pf["cues"].keys()
        if undefined:
            raise SystemExit(f"cue ids not defined in particle_functions.json: {sorted(undefined)}")

    def candidates(self, surface: str, ft: str | None) -> list[str]:
        unidic = FT_TO_UNIDIC.get(ft or "")
        out = []
        for uid, u in self.usages.items():
            if u["compound"] or uid == "lex.fixed":
                continue
            if surface not in [u["particle"], *u["allomorphs"]]:
                continue
            if unidic and unidic in self.class_pos[u["class"]]:
                out.append(uid)
        return out


def compound_at(toks: list[Tok], i: int) -> tuple[str | None, list[int], list[str]]:
    """Compound usage spanning token i. Returns (auto usage or None, positions, extra candidates)."""
    t = toks[i]
    s = t["s"]
    at = lambda k: toks[k] if 0 <= k < len(toks) else None  # noqa: E731
    p, n, n2 = at(i - 1), at(i + 1), at(i + 2)
    part = lambda x, *ss: bool(x) and x["pc"] == "助詞" and (not ss or x["s"] in ss)  # noqa: E731
    final = lambda x: x is None or x["pc"] in PUNCT or part(x, *()) and x["pf"] == "終助詞"  # noqa: E731
    # までに (deadline)
    if s == "まで" and part(n, "に"):
        return "madeni.deadline", [i, i + 1], []
    if s == "に" and part(p, "まで"):
        return "madeni.deadline", [i - 1, i], []
    # について
    if s == "に" and n and n["l"] in ("つく", "付く") and n["s"] == "つい" and part(n2, "て"):
        return "nitsuite.about", [i, i + 1, i + 2], []
    if s == "て" and p and p["s"] == "つい" and part(at(i - 2), "に"):
        return "nitsuite.about", [i - 2, i - 1, i], []
    # かな / かい at the end of the sentence
    if s == "か" and t["pf"] == "終助詞" and part(n, "な", "なあ", "なぁ") and final(n2):
        return "kana.wondering", [i, i + 1], []
    if s in ("な", "なあ", "なぁ") and part(p, "か") and p["pf"] == "終助詞" and final(n):
        return "kana.wondering", [i - 1, i], []
    if s == "か" and part(n, "い") and final(n2):
        return "kai.question", [i, i + 1], []
    if s == "い" and part(p, "か") and final(n):
        return "kai.question", [i - 1, i], []
    # non-unique compounds: offered as candidates only
    if s == "の" and part(n, "で") and not (n2 and n2["s"] in ("は", "も", "ある", "ない", "しょう")):
        return None, [i, i + 1], ["node.reason"]
    if s == "で" and part(p, "の") and not (n and n["s"] in ("は", "も", "ある", "ない", "しょう")):
        return None, [i - 1, i], ["node.reason"]
    if s == "の" and part(n, "に"):
        return None, [i, i + 1], ["noni.concessive", "noni.purpose"]
    if s == "に" and part(p, "の"):
        return None, [i - 1, i], ["noni.concessive", "noni.purpose"]
    if s == "で" and part(n, "も") and p and p["pc"] in NOMINAL:
        return None, [i, i + 1], ["demo.example", "demo.even"]
    if s == "も" and part(p, "で") and at(i - 2) and at(i - 2)["pc"] in NOMINAL:
        return None, [i - 1, i], ["demo.example", "demo.even"]
    if s == "と" and n and n["pc"] == "動詞" and n["l"] in ("言う", "いう") and n2 and n2["pc"] in NOMINAL:
        return None, [i, i + 1], ["toiu.naming"]
    return None, [], []


def _dominate(found: set[str], dom: dict[str, set[str]]) -> set[str]:
    return {u for u in found if not any(u in dom.get(w, set()) for w in found if w != u)}


def label_usages(label: str | None, cands: Iterable[str]) -> set[str]:
    if not label:
        return set()
    lab = label.lower()
    if LEX_RE.search(lab):
        return {"lex.fixed"}
    allowed = set(cands)
    hit = {u for rx, us in LABEL_RULES_C if rx.search(lab) for u in us if u in allowed}
    return _dominate(hit, LABEL_DOMINANCE)


def classify(enum: Enum, toks: list[Tok], i: int, ft: str | None, label_en: str | None, modal: str | None,
             sent_particles: list[str]) -> dict[str, Any]:
    """Tier + evidence for the particle at C index i. Pure function of its inputs (selftest target)."""
    s = toks[i]["s"]
    cands = enum.candidates(s, ft)
    comp_auto, positions, comp_extra = compound_at(toks, i)
    base: dict[str, Any] = {"candidates": cands + [c for c in comp_extra if c not in cands]}
    if positions:
        base["positions"] = positions
    if comp_auto:
        return {**base, "tier": "auto", "usage": comp_auto, "derived_by": "compound",
                "evidence": {"compound": comp_auto}}
    ctx = Ctx(toks, i, enum.lex, sent_particles)
    fired_cues: dict[str, list[str]] = {}
    for uid in base["candidates"]:
        if uid not in enum.usage_cues:
            continue
        mode, cues = enum.usage_cues[uid]
        hits = [c for c in cues if CUES[c](ctx)]
        if hits and (mode == "any" or len(hits) == len(cues)):
            fired_cues[uid] = hits
    cue = _dominate(set(fired_cues), CUE_DOMINANCE)
    lab = label_usages(label_en, base["candidates"])
    specific = bool(label_en) and label_en.lower() != (modal or "").lower()
    ev = {"cues": {u: fired_cues[u] for u in sorted(cue)}, "label_usages": sorted(lab),
          "label_is_modal": bool(label_en) and not specific}
    base["evidence"] = ev
    default = PAIR_DEFAULT.get((s, ft or ""))
    if default and default not in base["candidates"]:
        default = None
    cue1 = next(iter(cue)) if len(cue) == 1 else None
    lab1 = next(iter(lab)) if len(lab) == 1 else None

    if "lex.fixed" in lab:
        return {**base, "tier": "lexicalized", "suggested": "lex.fixed"}
    if len(cands) == 1 and not comp_extra and cands[0] not in NEVER_UNIQUE:
        return {**base, "tier": "auto", "usage": cands[0], "derived_by": "pair-unique"}
    if not base["candidates"]:
        return {**base, "tier": "ruling", "suggested": None}
    if cue1 and lab1 == cue1 and not comp_extra:   # a possible compound (のに, ので, でも, という) is never auto
        return {**base, "tier": "auto", "usage": cue1, "derived_by": "cue+label"}
    if cue1 and lab1 and specific:
        return {**base, "tier": "ruling", "suggested": None}
    if cue1:
        return {**base, "tier": "cue-only", "suggested": cue1}
    if cue:
        return {**base, "tier": "ruling" if lab1 not in cue else "cue-only",
                "suggested": lab1 if lab1 in cue else None}
    if lab1 and specific:
        return {**base, "tier": "label-only", "suggested": lab1}
    if default and (lab1 is None or lab1 == default):
        return {**base, "tier": "default", "suggested": default}
    return {**base, "tier": "ruling", "suggested": lab1}


# ----------------------------------------------------------------------------------------------- chunks + token roles
def load_patterns_module() -> Any:
    spec = importlib.util.spec_from_file_location("bsp", ROOT / "scripts" / "export" / "build_sentence_patterns.py")
    mod = importlib.util.module_from_spec(spec)  # type: ignore[arg-type]
    spec.loader.exec_module(mod)  # type: ignore[union-attr]
    return mod


def chunk_tokens(bsp: Any, toks: list[Tok], ft_at: dict[int, str]) -> tuple[list[dict[str, Any]], list[int | None]]:
    """Same chunking as scripts/export/build_sentence_patterns.py, but keeps each token's chunk index."""
    pattern: list[dict[str, Any]] = []
    member: list[int | None] = [None] * len(toks)
    buf: list[int] = []
    prev_pc = None

    def close(role: str, particle_idx: int | None = None) -> None:
        nonlocal buf
        entry: dict[str, Any] = {"chunk": "".join(toks[k]["s"] for k in buf), "role": role}
        if particle_idx is not None:
            entry["particle"] = toks[particle_idx]["s"]
        for k in buf + ([particle_idx] if particle_idx is not None else []):
            member[k] = len(pattern)
        entry["_idx"] = list(buf)
        entry["_particle"] = particle_idx
        pattern.append(entry)
        buf = []

    for k, t in enumerate(toks):
        pc = t["pc"]
        if pc == "補助記号":
            if buf:
                close("phrase")
            continue
        is_particle = pc == "助詞"
        ft = ft_at.get(k)
        if is_particle and ft == "sentence-final":
            if buf:
                close("predicate")
            buf = []
            member[k] = len(pattern)
            pattern.append({"chunk": t["s"], "role": "sentence-final", "particle": t["s"], "_idx": [], "_particle": k})
            continue
        role = bsp.role_of(t["s"], ft, prev_pc) if is_particle else None
        prev_pc = pc
        if role and buf:
            close(role, k)
            continue
        buf.append(k)
    if buf:
        last_pc = next((t["pc"] for t in reversed(toks) if t["pc"] != "補助記号"), "")
        close("predicate" if last_pc in bsp.PREDICATE_POS else "phrase")
    return pattern, member


AUX_POS_FUNCTION = {"助詞": "particle", "補助記号": "punctuation", "空白": "punctuation", "助動詞": "auxiliary",
                    "接頭辞": "prefix", "接尾辞": "suffix", "接続詞": "conjunction", "感動詞": "interjection",
                    "副詞": "adverb", "連体詞": "determiner"}


def token_items(toks: list[Tok], pattern: list[dict[str, Any]], chunk_role: list[str | None],
                aux_by_lemma: dict[str, str], subsid: set[str]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = [{"position": k, "surface": t["s"]} for k, t in enumerate(toks)]
    for k, t in enumerate(toks):
        f = AUX_POS_FUNCTION.get(t["pc"])
        if t["pf"] == "数詞":
            f = "numeral"
        if f:
            out[k]["function"], out[k]["derived_by"] = f, "pos"
            if f == "auxiliary" and t["l"] in aux_by_lemma:
                out[k]["aux_function"], out[k]["derived_by"] = aux_by_lemma[t["l"]], "lemma"
        elif t["pc"] == "動詞" and t["l"] in subsid and k > 0 and toks[k - 1]["pc"] == "助詞" \
                and toks[k - 1]["s"] in ("て", "で") and toks[k - 1]["pf"] == "接続助詞":
            out[k]["function"], out[k]["derived_by"] = "subsidiary-verb", "lemma"
    for ci, ch in enumerate(pattern):
        idx = ch["_idx"]
        for k in idx:
            out[k]["chunk"] = ci
        if ch["_particle"] is not None:
            out[ch["_particle"]]["chunk"] = ci
        if not idx:
            continue
        if ch["role"] == "predicate" and ci == len(pattern) - 1 or (
                ch["role"] == "predicate" and all(p["role"] == "sentence-final" for p in pattern[ci + 1:])):
            head = next((k for k in idx if toks[k]["pc"] in PRED | {"名詞", "代名詞"} and "function" not in out[k]), None)
            if head is not None:
                out[head]["function"], out[head]["derived_by"] = "predicate-head", "chunk"
            continue
        nominal = [k for k in idx if toks[k]["pc"] in ("名詞", "代名詞") and "function" not in out[k]]
        if ch["_particle"] is not None and nominal and nominal[-1] == max(
                (k for k in idx if toks[k]["pc"] not in PUNCT), default=-1):
            h = nominal[-1]
            out[h]["function"], out[h]["derived_by"] = "head", "chunk"
            for k in reversed(nominal[:-1]):
                between = range(k + 1, h)
                if all(toks[j]["pc"] in NOMINAL or toks[j]["pf"] == "数詞" for j in between):
                    out[k]["function"], out[k]["derived_by"] = "noun-modifier", "chunk"
        # verb/adjective run directly before a nominal in the same chunk -> adnominal-predicate
        for pos_in, k in enumerate(idx):
            if toks[k]["pc"] not in PRED or "function" in out[k]:
                continue
            j = pos_in + 1
            while j < len(idx) and toks[idx[j]]["pc"] == "助動詞":
                j += 1
            if j < len(idx) and toks[idx[j]]["pc"] in ("名詞", "代名詞"):
                out[k]["function"], out[k]["derived_by"] = "adnominal-predicate", "chunk"
    for k, t in enumerate(toks):
        ci = out[k].get("chunk")
        if ci is not None and chunk_role[ci] and out[k].get("function") != "particle":
            out[k]["chunk_role"] = chunk_role[ci]
    return out


def render_role(item: dict[str, Any], tr_fn: dict[str, Any], tr_role: dict[str, Any], tr_aux: dict[str, Any],
                tpl: dict[str, Any]) -> dict[str, str] | None:
    f = item.get("function")
    if not f:
        return None
    rec = tr_fn[f]
    kind = rec["template"]
    if kind == "tpl.role.self":
        return {loc: tpl[kind][loc].format(function=rec["label"][loc]) for loc in ("pt-BR", "en")}
    if kind == "tpl.role.aux" and item.get("aux_function"):
        return {loc: tpl[kind][loc].format(aux_function=tr_aux[item["aux_function"]]["label"][loc])
                for loc in ("pt-BR", "en")}
    if kind == "tpl.role.of" and item.get("chunk_role") and tr_role[item["chunk_role"]].get("of"):
        return {loc: tpl[kind][loc].format(function=rec["label"][loc], role_of=tr_role[item["chunk_role"]]["of"][loc])
                for loc in ("pt-BR", "en")}
    return None


# ----------------------------------------------------------------------------------------------- main
def sha256(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def run(args: argparse.Namespace) -> int:
    pf, tr = load_design()
    enum = Enum(pf)
    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)
    db = snapshot(Path(args.db))
    bank, bank_src = load_bank(args.bank)
    bank_by_slug = {s["slug"]: s for s in bank}

    sents = {sid: (slug, jp, level, pj) for sid, slug, jp, level, pj in
             db.execute("SELECT id, slug, jp, level, pattern_json FROM sentence")}
    toks_by_sid: dict[int, list[Tok]] = collections.defaultdict(list)
    tok_index: dict[int, tuple[int, int]] = {}
    bad_positions = set()
    for tid, sid, pos, surf, lemma, pc, pf_, inf in db.execute(
            "SELECT id, sentence_id, position, surface, lemma, pos_coarse, pos_fine, inflection FROM token "
            "WHERE split_mode='C' ORDER BY sentence_id, position"):
        lst = toks_by_sid[sid]
        if pos != len(lst):
            bad_positions.add(sid)
        tok_index[tid] = (sid, len(lst))
        lst.append(Tok(id=tid, s=surf, l=lemma or surf, pc=pc or "", pf=pf_ or "", inf=inf))
    loc: dict[tuple[str, int, str], dict[str, str]] = collections.defaultdict(dict)
    for et, eid, field, locale, value in db.execute(
            "SELECT entity_type, entity_id, field, locale, value FROM localized_text "
            "WHERE (entity_type='particle' AND field IN ('function','explanation')) "
            "OR (entity_type='token' AND field='role')"):
        loc[(et, eid, field)][locale] = value

    aligned, total = sudachi_pos({sid: (sents[sid][1], t) for sid, t in toks_by_sid.items()})

    prows = db.execute("SELECT id, sentence_id, token_id, particle, function_type FROM particle ORDER BY id").fetchall()
    modal_count: dict[tuple[str, str], collections.Counter[str]] = collections.defaultdict(collections.Counter)
    for pid, _, _, part, ft in prows:
        lab = loc.get(("particle", pid, "function"), {}).get("en")
        if lab:
            modal_count[(part, ft or "")][lab.lower()] += 1
    modal = {k: c.most_common(1)[0][0] for k, c in modal_count.items()}
    sent_particles: dict[int, list[str]] = collections.defaultdict(list)
    for _, sid, _, part, _ in prows:
        sent_particles[sid].append(part)

    stats = collections.Counter()
    jp_mismatch = [sents[sid][0] for sid in sents if sents[sid][0] in bank_by_slug
                   and bank_by_slug[sents[sid][0]]["jp"] != sents[sid][1]]
    derived, work = [], []
    usage_at: dict[tuple[int, int], dict[str, Any]] = {}
    pair_tier: dict[str, collections.Counter[str]] = collections.defaultdict(collections.Counter)
    for pid, sid, tid, part, ft in prows:
        slug, jp, level, _ = sents[sid]
        if tid not in tok_index or sid in bad_positions:
            stats["unanchored"] += 1
            res = {"tier": "ruling", "suggested": None, "candidates": enum.candidates(part, ft), "evidence": {}}
            i = None
        else:
            _, i = tok_index[tid]
            toks = toks_by_sid[sid]
            if toks[i]["s"] != part:
                stats["surface_mismatch"] += 1
            lab_en = loc.get(("particle", pid, "function"), {}).get("en")
            res = classify(enum, toks, i, ft, lab_en, modal.get((part, ft or "")), sent_particles[sid])
        stats[res["tier"]] += 1
        stats[f"{level}:{res['tier']}"] += 1
        pair_tier[f"{part}/{ft}"][res["tier"]] += 1
        if i is not None:
            usage_at[(sid, i)] = res
        if res["tier"] == "auto":
            u = enum.usages[res["usage"]]
            row = {"particle_id": pid, "slug": slug, "level": level, "position": i, "particle": part,
                   "function_type": ft, "usage": res["usage"], "class": u["class"], "usage_status": "auto",
                   "derived_by": res["derived_by"], "evidence": res.get("evidence", {})}
            if "positions" in res:
                row["positions"] = res["positions"]
            derived.append(row)
            continue
        b = bank_by_slug.get(slug, {})
        toks = toks_by_sid[sid]
        cand = list(res["candidates"])
        if "lex.fixed" not in cand:
            cand.append("lex.fixed")
        one = lambda d: (d or {}).get("en") or (d or {}).get("pt-BR")  # noqa: E731  context only; apply reads the DB
        wrow = {
            "particle_id": pid, "slug": slug, "level": level, "tier": res["tier"],
            "jp": jp, "translation": b.get("translation"), "position": i, "particle": part, "function_type": ft,
            "suggested": res.get("suggested"), "candidates": cand,
            "label": one(loc.get(("particle", pid, "function"))),
            "explanation": one(loc.get(("particle", pid, "explanation"))),
            "evidence": res.get("evidence", {}),
            # [position, surface, lemma, pos_coarse, role (en, else pt-BR, else null)]
            "tokens": [[k, t["s"], t["l"], t["pc"], one(loc.get(("token", t["id"], "role")))]
                       for k, t in enumerate(toks)],
        }
        if "positions" in res:
            wrow["positions"] = res["positions"]
        work.append(wrow)

    # ---- work files: one tier per file, n5 first, then pair, then sentence
    for old in glob.glob(str(out_dir / "work-*.json")):
        os.remove(old)
    work.sort(key=lambda r: (TIER_ORDER.index(r["tier"]), LEVEL_ORDER.get(r["level"] or "", 9),
                             r["particle"], r["function_type"] or "", r["slug"], r["position"] or 0))
    files, n = [], 0
    for tier in TIER_ORDER:
        rows = [r for r in work if r["tier"] == tier]
        for start in range(0, len(rows), WORK_ROWS):
            n += 1
            chunk = rows[start:start + WORK_ROWS]
            name = f"work-{n:02d}.json"
            head = json.dumps({"unit": "particle_usage", "tier": tier, "rows": len(chunk),
                               "tokens_format": "[position, surface, lemma, pos_coarse, role]",
                               "answer_contract": "per row: exactly one id from `candidates`, or `ruling`; a null "
                                                  "or failed verdict excludes the row, never passes it"},
                              ensure_ascii=False)
            body = ",\n".join(json.dumps(r, ensure_ascii=False, separators=(",", ":")) for r in chunk)
            (out_dir / name).write_text(head[:-1] + ',"items":[\n' + body + "\n]}\n", encoding="utf-8")
            files.append({"file": name, "tier": tier, "rows": len(chunk),
                          "levels": dict(collections.Counter(r["level"] for r in chunk))})

    # ---- token roles
    bsp = load_patterns_module()
    aux_by_lemma = {lem: a["id"] for a in tr["aux_functions"] for lem in a["lemmas"]}
    tr_fn = {f["id"]: f for f in tr["token_functions"]}
    tr_role = {r["id"]: r for r in tr["chunk_roles"]}
    tr_aux = {a["id"]: a for a in tr["aux_functions"]}
    ft_by_sid: dict[int, dict[int, str]] = collections.defaultdict(dict)
    for _, _, tid, _, ft in prows:
        if tid in tok_index:
            s2, i2 = tok_index[tid]
            ft_by_sid[s2][i2] = ft
    trs, tstats = [], collections.Counter()
    for sid, toks in sorted(toks_by_sid.items()):
        slug, jp, level, pj = sents[sid]
        ft_at = ft_by_sid[sid]
        pattern, _ = chunk_tokens(bsp, toks, ft_at)
        published = json.loads(pj) if pj else None
        mine = [{k: v for k, v in p.items() if not k.startswith("_")} for p in pattern]
        same = None if published is None else published == mine
        tstats[{None: "pattern_absent", True: "pattern_match", False: "pattern_mismatch"}[same]] += 1
        roles: list[str | None] = []
        for ch in pattern:
            r = None
            pi = ch["_particle"]
            if ch["role"] == "sentence-final":
                r = "sentence-final"
            elif pi is not None:
                res = usage_at.get((sid, pi))
                if res and res["tier"] == "auto":
                    r = enum.usages[res["usage"]]["role"]
                elif res and res["tier"] != "lexicalized":
                    rs = {enum.usages[u]["role"] for u in res["candidates"]}
                    r = rs.pop() if len(rs) == 1 else None
            elif ch["role"] == "predicate":
                r = "predicate"
            elif ch["_idx"] and all(toks[k]["pc"] == "副詞" for k in ch["_idx"]):
                r = "adverbial"
            elif len(ch["_idx"]) == 1 and toks[ch["_idx"][0]]["pc"] in ("接続詞", "感動詞"):
                r = "connective" if toks[ch["_idx"][0]]["pc"] == "接続詞" else "interjection"
            roles.append(r)
        items = token_items(toks, pattern, roles, aux_by_lemma, enum.lex["SUBSID"])
        for it in items:
            rr = render_role(it, tr_fn, tr_role, tr_aux, tr["templates"])
            if rr:
                it["role"] = rr
            tstats["tokens"] += 1
            if it.get("function") and it["function"] not in ("particle", "punctuation"):
                tstats["content_with_function"] += 1
            if toks[it["position"]]["pc"] not in ("助詞", "補助記号", "空白"):
                tstats["content_tokens"] += 1
                tstats["content_with_role" if rr else "content_without_role"] += 1
            if it.get("aux_function"):
                tstats["aux_with_function"] += 1
            if toks[it["position"]]["pc"] == "助動詞":
                tstats["aux_tokens"] += 1
            if it.get("chunk_role"):
                tstats["with_chunk_role"] += 1
        # `chunk` on a token indexes `chunks` here; it equals the exported pattern[] index when
        # pattern_matches_export is true (null = the sentence has no exported pattern yet).
        trs.append({"slug": slug, "pattern_matches_export": same,
                    "chunks": [{**m, "chunk_role": r} for m, r in zip(mine, roles)], "tokens": items})

    script = Path(__file__).resolve()
    meta = {
        "unit": "particle_usage", "step": "M3 (research/reports/particle_taxonomy_research.md §6)",
        "generated": dt.datetime.now().isoformat(timespec="seconds"),
        "script": {"path": script.relative_to(ROOT).as_posix(), "sha256": sha256(script)},
        "inputs": {"bank": bank_src, "db": "sqlite3 backup-API snapshot of " + Path(args.db).as_posix(),
                   "design": {p: sha256(ROOT / p) for p in ("design/particle_functions.json", "design/token_roles.json")},
                   "sudachi_aligned_sentences": f"{aligned}/{total}"},
        "checks": {"particle_rows": len(prows), "sentences": len(sents), "bank_sentences": len(bank),
                   "bank_jp_mismatch": jp_mismatch[:50], "bank_jp_mismatch_count": len(jp_mismatch),
                   "unanchored": stats["unanchored"], "surface_mismatch": stats["surface_mismatch"],
                   "sentences_with_position_gaps": len(bad_positions)},
        "tiers": {t: stats[t] for t in ["auto", *TIER_ORDER]},
        "tiers_share": {t: round(100 * stats[t] / max(len(prows), 1), 1) for t in ["auto", *TIER_ORDER]},
        "tiers_by_level": {lv: {t: stats[f"{lv}:{t}"] for t in ["auto", *TIER_ORDER]} for lv in LEVEL_ORDER},
        "derived_by": dict(collections.Counter(r["derived_by"] for r in derived)),
        "by_pair": {k: dict(v) for k, v in sorted(pair_tier.items(), key=lambda kv: -sum(kv[1].values()))},
        "work_files": files,
        "report_reference": {"auto": 25.4, "default": 32.1, "cue-only": 15.9, "label-only": 17.5,
                             "lexicalized": 2.4, "ruling": 6.7},
        "local_lexicons": {"STATIVE": sorted(STATIVE)},
    }
    (out_dir / "derived.json").write_text(json.dumps({"meta": meta, "rows": derived}, ensure_ascii=False, indent=1),
                                          encoding="utf-8")
    (out_dir / "token_roles_derived.json").write_text(json.dumps(
        {"meta": {"unit": "particle_usage/token_roles", "design": "design/token_roles.json",
                  "rule": "function by POS/lemma/chunk position; aux_function by lemma; chunk_role from the "
                          "closing particle's AUTO usage, or when every candidate usage gives the same role; "
                          "trailing verbal run -> predicate. Nothing else is guessed: a missing field is pending.",
                  "stats": dict(tstats), "script_sha256": meta["script"]["sha256"]},
         "sentences": trs}, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    print(json.dumps({"tiers": meta["tiers"], "share": meta["tiers_share"], "checks": meta["checks"] | {"bank_jp_mismatch": None},
                      "sudachi": meta["inputs"]["sudachi_aligned_sentences"], "work_files": len(files),
                      "token_stats": dict(tstats)}, ensure_ascii=False, indent=1))
    return 0


# ----------------------------------------------------------------------------------------------- selftest
def selftest() -> int:
    pf, _ = load_design()
    enum = Enum(pf)

    def T(spec: str) -> list[Tok]:
        out = []
        for part in spec.split():
            s, l, pc, pf_, *inf = part.split("/")
            out.append(Tok(id=0, s=s, l=l, pc=pc, pf=pf_, inf=inf[0] if inf else None))
        return out

    N, V, P = "名詞", "動詞", "助詞"
    # 七時に起きる: time cue + time label -> auto
    t = T(f"七/七/{N}/数詞 時/時/{N}/普通名詞 に/に/{P}/格助詞 起きる/起きる/{V}/一般/terminal")
    r = classify(enum, t, 2, "case", "time marker", "destination/direction particle", ["に"])
    assert r["tier"] == "auto" and r["usage"] == "ni.time-point", r
    # same row, modal label pasted ("destination"): cue says time -> not auto (W13b error class)
    r = classify(enum, t, 2, "case", "destination/direction particle", "destination/direction particle", ["に"])
    assert r["tier"] == "cue-only" and r["suggested"] == "ni.time-point", r
    # 映画を見に行く: purpose dominates goal
    t = T(f"映画/映画/{N}/普通名詞 を/を/{P}/格助詞 見/見る/{V}/一般/continuative に/に/{P}/格助詞 行く/行く/{V}/一般/terminal")
    r = classify(enum, t, 3, "case", "purpose particle", "destination/direction particle", ["を", "に"])
    assert r["tier"] == "auto" and r["usage"] == "ni.purpose", r
    # 五時までに帰る: compound auto on both tokens
    t = T(f"五/五/{N}/数詞 時/時/{N}/普通名詞 まで/まで/{P}/副助詞 に/に/{P}/格助詞 帰る/帰る/{V}/一般/terminal")
    for k in (2, 3):
        r = classify(enum, t, k, "adverbial" if k == 2 else "case", None, None, ["まで", "に"])
        assert r["usage"] == "madeni.deadline" and r["positions"] == [2, 3], r
    # 来たって (report §4.3 miss): たって is never pair-unique auto
    t = T(f"来/来る/{V}/一般/continuative たって/たって/{P}/接続助詞 感じ/感じ/{N}/普通名詞")
    r = classify(enum, t, 1, "conjunctive", None, None, ["たって"])
    assert r["tier"] != "auto", r
    # へ is pair-unique
    t = T(f"日本/日本/{N}/固有名詞 へ/へ/{P}/格助詞 行く/行く/{V}/一般/terminal")
    assert classify(enum, t, 1, "case", None, None, ["へ"])["usage"] == "he.direction"
    # lexicalized label wins over pair-unique
    r = classify(enum, T(f"雨/雨/{N}/普通名詞 か/か/{P}/副助詞 も/も/{P}/係助詞 しれ/知れる/{V}/一般/irrealis ない/ない/助動詞/*"),
                 1, "adverbial", "part of かもしれない", None, ["か", "も"])
    assert r["tier"] == "lexicalized", r
    # は with no signal -> default topic, never auto
    t = T(f"私/私/代名詞/* は/は/{P}/係助詞 学生/学生/{N}/普通名詞 です/です/助動詞/*/terminal")
    r = classify(enum, t, 1, "binding", "topic particle", "topic particle", ["は"])
    assert r["tier"] == "default" and r["suggested"] == "ha.topic", r
    # 作るのに３円かかる: の before に may be the compound のに -> never auto, compound offered
    t = T(f"作る/作る/{V}/一般/attributive の/の/{P}/準体助詞 に/に/{P}/格助詞 三/三/{N}/数詞 円/円/接尾辞/名詞的 かかる/掛かる/{V}/一般/terminal")
    r = classify(enum, t, 1, "nominalizer", "nominalizer", "nominalizer", ["の", "に"])
    assert r["tier"] != "auto" and "noni.purpose" in r["candidates"] and r["positions"] == [1, 2], r
    print("selftest: passed")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--db", default=str(ROOT / "db" / "corpus.sqlite"))
    ap.add_argument("--bank", default="git", help="'git' = corpus/sentences/bank.json at HEAD, or a path")
    ap.add_argument("--out", default=str(DEFAULT_OUT))
    ap.add_argument("--selftest", action="store_true")
    args = ap.parse_args()
    return selftest() if args.selftest else run(args)


if __name__ == "__main__":
    sys.exit(main())
