#!/usr/bin/env python3
"""W13b Derive v2 — `derive_layerb.py` with the particle template and label rules REPAIRED.

Same file as `scripts/derive_layerb.py` in every other respect. It exists so a future re-derivation
does not reproduce the two defects the W13b template audit found in the 6,987 templated particles of
`research/derived/mined_layerb_n3/`:

  1. THE QUOTED CHUNK WAS THE WHOLE LEFT RUN.  `_left_chunk()` walked left until a particle or a
     punctuation mark, so anything adverbial sitting in front of the noun phrase was quoted as part
     of it. 明日雨が降る came out "marca 明日雨 como o sujeito", but 明日 is a time adverbial and the
     subject is 雨 alone; likewise 思わず大きな声を (adverb 思わず glued to 大きな声) and 急に人が
     (急に is 形状詞 + the 連用形 copula に, which is NOT a 助詞, so the old walk sailed straight
     through it). `_left_chunk()` is kept below as `_left_chunk_v1` — the audit diffs against it —
     and `_left_chunk()` is now head-and-genuine-modifiers only (`chunk_head()`).

  2. THE FUNCTION LABEL WAS THE PAIR MODAL, NEVER THE OCCURRENCE.  `function_pt` was the bank's most
     frequent short label for the (particle, function_type) pair, applied blind. That is right for
     the overwhelming majority and wrong for a fixed, enumerable set of occurrences: the case-marked
     で of ではない / でもある is the copula, not "lugar da ação"; も after an interrogative in a
     negative clause is total negation, not "também"; まで after a place is a spatial limit, not a
     temporal one; と before 一緒に or a reciprocal verb is comitative, not quotative; に after a
     na-adjective stem forms an adverb, it is not a destination; and sentence-final な is a
     prohibition only after a 終止形 verb. `function_pt_fix()` overrides exactly those six, and
     returns the pair modal untouched everywhere else.

  3. て INSIDE A FIXED LOCUTION IS NOT A CONNECTOR.  として / について / によって / に対して /
     にとって / に関して / を通して tokenize as と|し|て, and the て template then claimed
     "て liga する ao que vem depois". The template is withdrawn there (status `author`).

The chunk rules need Sudachi's third POS field (副詞可能 marks the adverbial nouns) which
`dissect.Dissector.skeleton()` does not carry, so `enrich_pos_fine3()` re-runs the same tokenizer in
the same split mode and zips the field back on by position before the templates run.

Run the rule tests with `--selftest`; they cover every example the batch-30 verifier raised.

W13b Derive — build the mechanical half of the mined-N3 Layer-B, and nothing else.

Reads the three W13b inputs and emits one file per batch under
`research/derived/n3_mined/layerb_derived/`, in EXACTLY the shape
`scripts/ingest/ingest_mined_stages.py` reads (`sentences[]`, token/particle rows keyed by the C-token
`position` from `dissect.Dissector.skeleton()`).

WHAT IS DERIVED HERE, and what is deliberately left empty:

  token `gloss_pt`      derived for 99.1 % of content tokens. `gloss_origin` says how:
                          bank-modal   the modal pt-BR gloss the bank already uses for the same
                                       (surface, lemma, pos_coarse) — 75.3 %
                          registry     '; '.join of the first three pt-BR glosses of the linked vocab's
                                       sense[0] — 23.9 % (the only sense convention the schema carries;
                                       lessons store no sense pointer)
                          rule-numeral a bare numeral rendered in pt-BR digits by rule, added here
                        `gloss_status` says how far to trust it: `unique-accept` (the key had exactly one
                        candidate), `ambiguous-verify` (more than one; a reviewer rules per lemma) or
                        `author` (nothing fired).

  token `role_pt`       NOT emitted. The residue carries a `role_pt_hint` (the bank's modal role for the
                        same surface) and it is frequently FALSE in a new sentence: 靴 comes back
                        "objeto direto" inside この靴は…, where it is the topic. role_pt is optional to
                        the validator, so a hint that is wrong that often goes into the work lists as a
                        hint and never into the corpus payload.

  particle `function_pt` the bank's modal short label for the (particle, function_type) pair — 99.89 %.

  particle `explanation_pt`
                        REQUIRED by validate.py, and mostly authored. The residue report's §3 proposes a
                        parameterised template over `build_sentence_patterns.role_of()`. Implemented, but
                        NOT over all 8,466 role-bearing particles: `role_of()` returns deliberately
                        NON-COMMITTAL roles for に / で / と / から-case / の-nominalizer / が-conjunctive
                        ("ni-phrase", "de-phrase", …) precisely because the corpus does not carry the
                        distinction, and rendering those into Portuguese would either be vacuous or claim
                        a sense the data does not have. build_sentence_patterns' own docstring records
                        three drills that shipped wrong for exactly that reason. So the template fires
                        only where the role is committal AND a structural guard confirms the shape:
                          は/binding     when it attaches to a nominal (kills では / には / とは)
                          が/case        when it attaches to a nominal
                          を/case        when it attaches to a nominal and a verb follows in the clause
                          の/case        when nominal on both sides
                          て/conjunctive when it attaches to a verbal and something follows
                        plus four context-free sentence-final pairs whose bank texts genuinely repeat
                        (measured on the bank: か 50.6 %, よ 92.9 %, ね 90.0 % of explanations name no
                        Japanese beyond the particle itself). Everything else is
                        `explanation_status: "author"`. な/sentence-final and の/sentence-final are
                        excluded on purpose: each is two different particles wearing one label
                        (proibição vs ênfase; pergunta vs explicativo).

  `structure_explanation_pt`
                        NEVER derived. The bank's 5,889 structure paragraphs are 5,889 distinct strings;
                        there is no precedent to inherit. The slot is emitted null with
                        `structure_status: "author"`, plus `clause_structure_predicted` — a 72.3 %-accurate
                        surface classifier, carried ONLY to batch the authoring work by sentence shape.

Nothing in this file writes to the database or to `corpus/`. The DB is opened only to run the Dissector;
pass `--db` at a copy.

Usage:
    python scripts/derive_layerb.py --db <copy.sqlite> [--skeletons cache.jsonl] [--batch-size 150]
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from collections import Counter
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]

ROOT = Path(__file__).resolve().parents[1]
MINED = ROOT / "research" / "derived" / "n3_mined"
OUT_DIR = MINED / "layerb_derived"

NOMINAL = {"名詞", "代名詞", "数詞", "接尾辞"}
VERBAL = {"動詞", "形容詞", "形状詞", "助動詞"}
PUNCT = {"補助記号"}


# --------------------------------------------------------------------------------------- identity
def sentence_key(row: dict) -> str:
    """The stable key for a mined sentence, in both the derived batches and the ingest.

    Real rows key on the Tatoeba id, because that is what the existing 324 authored batches use and what
    `sent:tatoeba-<id>` is built from. The 26 generated rows have `tatoeba_id: ""` — keying them on that
    collapses all 26 onto one key (blocker 1 of the residue report), so they key on the same hash the
    bank already uses for generated sentences: sha1(jp)[:12], slug `sent:gen-<hash>`.
    """
    tid = row.get("tatoeba_id")
    if not row.get("generated") and tid not in (None, ""):
        return str(tid)
    return "gen-" + hashlib.sha1(row["jp"].encode("utf-8")).hexdigest()[:12]


def sentence_slug(key: str) -> str:
    return f"sent:{key}" if key.startswith("gen-") else f"sent:tatoeba-{key}"


# ------------------------------------------------------------------------------------ numeral rule
MULT = {"万": 10_000, "億": 100_000_000, "兆": 1_000_000_000_000}
NUM_BODY = re.compile(r"^([0-9]+)([万億兆]?)$")


def numeral_gloss(surface: str) -> str | None:
    """pt-BR rendering of a bare arabic numeral, with or without a 万/億/兆 multiplier.

    Covers the bare numerals in the token residue (50, 12, 30万, 500万, 2020 …). Deliberately narrow: it
    fires only on a surface that is digits, optionally closed by one multiplier character. Anything with
    a counter, a kanji numeral or a mixed reading falls through to the author list rather than risking a
    wrong number.
    """
    s = surface.translate(str.maketrans("０１２３４５６７８９", "0123456789")).replace(",", "")
    m = NUM_BODY.match(s)
    if not m:
        return None
    n = int(m.group(1)) * MULT.get(m.group(2), 1)
    if n >= 1_000_000 and n % 1_000_000 == 0:
        q = n // 1_000_000
        return f"{q} milhão" if q == 1 else f"{q} milhões"
    if n >= 1_000 and n % 1_000 == 0:
        return f"{n // 1_000} mil"
    return f"{n:,}".replace(",", ".") if n >= 10_000 else str(n)


# ------------------------------------------------------------------------- clause-structure predictor
COND = ("たら", "なら", "れば", "けれ")
CAUSE = ("から", "ので")
TIME = ("とき", "時", "あと", "後", "前")


def predict_clause_structure(tokens: list[dict]) -> str:
    """The residue report's §4(a) surface classifier, retuned: 72.3 % against the bank's 5,825 labels.

    A BATCHING KEY, not data. It never reaches the corpus; it only groups the 4,223 authoring jobs by
    sentence shape so one instruction covers a run of them. Rule ORDER is the report's; three of the
    tests were tightened after scoring the literal reading of the report against the bank (63.5 %):

      * `fragment` was firing on every sentence closed by a sentence-final particle (…ですね, …だよ),
        because the last token is then a 助詞. The trailing run of punctuation and sentence-final
        particles is now stripped before the predicate test. Worth 177 sentences on its own.
      * `question` missed every question written with ？ and no か. Both now count.
      * `cause` and `subordinate-time` were matching から / ため / 前 / 後 as SUBSTRINGS, so 東京から
        (origin), 目の前 (a place) and 午後 (a time of day) all read as clause markers. They now test
        tokens, with the part of speech that makes the reading a clause link.
    """
    joined = "".join(t["surface"] for t in tokens)
    real = [t for t in tokens if t["pos_coarse"] not in PUNCT]
    # the predicate test ignores what trails the predicate: punctuation and sentence-final particles
    tail = list(real)
    while tail and (tail[-1].get("particle_function") == "sentence-final"
                    or tail[-1].get("pos_fine") == "終助詞"):
        tail.pop()

    if any(t["surface"] in ("か", "？", "?") and (t.get("particle_function") == "sentence-final"
                                                 or t["pos_coarse"] in PUNCT) for t in tokens):
        return "question"
    if any(t.get("inflection") == "imperative" for t in tokens) or "ください" in joined \
            or "下さい" in joined or "なさい" in joined:
        return "imperative"
    if "と言" in joined or "と思" in joined or "という" in joined:
        return "quote"
    if any(s in joined for s in COND):
        return "conditional"
    if any(t["surface"] in CAUSE and t.get("pos_fine") == "接続助詞" for t in tokens) \
            or any(t["surface"] in ("ため", "為") and t["pos_coarse"] == "名詞" for t in tokens):
        return "cause"
    if any(t["surface"] in TIME and t["pos_coarse"] == "名詞" for t in tokens):
        return "subordinate-time"
    if any(t.get("pos_fine") == "接続助詞" for t in tokens):
        return "coordinate"
    if any(t["surface"] == "は" and t.get("pos_fine") == "係助詞" for t in tokens):
        return "topic-comment"
    if not tail or tail[-1]["pos_coarse"] not in VERBAL:
        return "fragment"
    return "simple"


# -------------------------------------------------------------------------------- particle template
CONTEXT_FREE = {
    ("か", "sentence-final"):
        "か no fim transforma a frase em pergunta.",
    ("よ", "sentence-final"):
        "よ no fim passa a informação ao ouvinte com ênfase, como quem diz 'olha' ou 'viu'.",
    ("ね", "sentence-final"):
        "ね no fim suaviza a afirmação e pede a concordância de quem ouve, como o nosso 'né?'.",
    ("わ", "sentence-final"):
        "わ no fim suaviza a afirmação e dá um tom expressivo, tradicionalmente associado à fala "
        "feminina, sem mudar o sentido literal.",
}


def _left_chunk_v1(tokens: list[dict], i: int) -> str | None:
    """v1 — the contiguous run of non-particle, non-punctuation tokens that the particle at i closes.

    Kept only so the audit can diff v1 against v2. Do not call it to build an explanation.
    """
    buf = []
    j = i - 1
    while j >= 0:
        t = tokens[j]
        if t["pos_coarse"] in PUNCT or t["pos_coarse"] == "助詞":
            break
        buf.append(t["surface"])
        j -= 1
    return "".join(reversed(buf)) or None


# --------------------------------------------------------------------- v2 chunker: head + modifiers
# Sudachi's third POS field on a noun. 副詞可能 is the adverbial-capable class (明日, 昨日, 今朝,
# 毎日, 最近, 今度, 全部 …): such a noun in front of another noun is an adverbial adjunct of the
# clause, not a modifier of the noun, so it must not be quoted inside the noun phrase.
ADVERBIAL_NOUN_FINE3 = {"副詞可能"}
# Fallback for token rows that carry no pos_fine3 (a skeleton cache built before enrich_pos_fine3).
# Not a substitute for the field, just a floor: the frequent adverbial nouns of this corpus.
ADVERBIAL_NOUN_LEMMAS = {
    "明日", "昨日", "今日", "今朝", "今晩", "今夜", "今年", "去年", "来年", "毎日", "毎朝",
    "毎晩", "毎年", "毎週", "毎月", "今週", "来週", "先週", "今月", "来月", "先月", "最近",
    "今度", "今回", "前回", "次回", "当時", "後で", "全部", "全員", "みんな", "everyone",
}
# Coarse classes that can never sit inside a noun phrase as a modifier of its head.
NON_MODIFIER_COARSE = {"副詞", "接続詞", "感動詞", "フィラー", "記号", "空白"}
# Formal / bound nouns: they cannot head a phrase on their own, so whatever stands immediately to
# their left is part of the phrase whatever its class (土曜以外, 一人分, 車の方, 若いころ).
# Deliberately NOT here: 中 内 外 上 下 前 後 間 目 度 側 通り. Each is also an ordinary standalone
# noun in this corpus (目 = eye in 早く目が覚める), and keeping them would hold an adverbial in.
BOUND_NOUN_HEADS = {
    "以外", "以上", "以下", "以内", "以来", "以後", "以前", "分", "方", "ほう", "頃", "ころ",
    "際", "うち", "ため", "為", "とおり", "ほど", "くらい", "ぐらい", "たび", "おかげ", "せい",
    "所為", "はず", "つもり", "まま", "ばかり", "限り", "次第", "ごと", "たち", "ら",
}


def _is_adverbial_noun(t: dict) -> bool:
    f3 = t.get("pos_fine3")
    if f3 is not None and f3 != "*":
        return f3 in ADVERBIAL_NOUN_FINE3
    return (t.get("lemma") or t["surface"]) in ADVERBIAL_NOUN_LEMMAS


VERBAL_COARSE = {"動詞", "形容詞", "助動詞"}


def _is_modifier_of_head(t: dict, right: dict | None) -> bool:
    """True when token t, immediately LEFT of `right` inside the phrase, belongs to that phrase.

    Everything that is not a modifier ends the phrase: the walk stops, it does not skip. A modifier
    can only be adjacent to what it modifies, so anything further left is outside the noun phrase
    too (明日 大きな 声 keeps 大きな声 and drops 明日).

    `right` is what decides most of the hard cases. An inflected form is adverbial only when a
    NOMINAL follows it (早く目 → 目); when another inflecting form follows, the two are one
    predicate and both stay (やり+たい+こと, 引退+し+た+後, ぼんやり+し+た+表情).
    """
    c = t["pos_coarse"]
    if c in PUNCT or c == "助詞" or c in ("記号", "空白"):
        return False
    if right is not None and (right["pos_coarse"] == "接尾辞"
                              or (right.get("lemma") or right["surface"]) in BOUND_NOUN_HEADS):
        return True     # 十頭, 三人, 焼き加減 / 土曜以外, 一人分 — both bind to whatever is left
    if c in ("接頭辞", "連体詞", "形状詞"):               # ご意見 / この, 大きな / きれい(な)
        return True
    if c in VERBAL_COARSE:
        # ATTRIBUTIVE is a modifier outright (な of きれいな, た of 買った, 連体形 verbs). A
        # CONTINUATIVE/IRREALIS form belongs to the phrase only while the predicate continues to its
        # right: 早く目 drops 早く, 良くする案 keeps 良く, 思わ+ず+大きな声 drops ず (連体詞 follows).
        if t.get("inflection") in ("attributive", "stem"):
            return True     # 買った本; 薄+暮れ, 細+道 — a 語幹 form only ever heads a compound
        if right is None:
            return False
        if right["pos_coarse"] in VERBAL_COARSE:
            return True
        # a bare 連用形 VERB straight in front of a noun is the left half of a compound noun
        # (焼き加減, 読み方, 話し相手), never an adjunct — an adverbial verb needs て or a comma.
        # An i-adjective or a copula in the same slot IS the adjunct: 早く目, 急に人.
        return c == "動詞" and right["pos_coarse"] in NOMINAL
    if c == "副詞":
        # an adverb modifies a predicate, never a noun: keep it only when a predicate follows
        return right is not None and right["pos_coarse"] in (VERBAL_COARSE | {"形状詞", "副詞"})
    if c in ("接続詞", "感動詞", "フィラー"):
        return False
    if c in NOMINAL:
        # 日本語学校 yes; 明日雨 / 毎月給料 no. An adverbial noun is dropped even inside a relative
        # clause (今晩泊まる宿 → 泊まる宿): the chunk gets shorter but never says something false.
        return not _is_adverbial_noun(t)
    return False


def chunk_head(tokens: list[dict], i: int) -> str | None:
    """The noun phrase the particle at i actually marks: its head plus its genuine modifiers.

    Starts from the v1 run (stopped at the nearest particle or punctuation), keeps its rightmost
    token as the head, and walks left only through tokens that modify it.
    """
    j = i - 1
    while j >= 0 and tokens[j]["pos_coarse"] not in PUNCT and tokens[j]["pos_coarse"] != "助詞":
        j -= 1
    start = j + 1
    if start > i - 1:
        return None
    head = i - 1
    k = head - 1
    while k >= start and _is_modifier_of_head(tokens[k], tokens[k + 1]):
        k -= 1
    return "".join(t["surface"] for t in tokens[k + 1:head + 1]) or None


def _left_chunk(tokens: list[dict], i: int) -> str | None:
    return chunk_head(tokens, i)


def _prev(tokens: list[dict], i: int) -> dict | None:
    return tokens[i - 1] if i > 0 else None


def _next(tokens: list[dict], i: int) -> dict | None:
    for t in tokens[i + 1:]:
        if t["pos_coarse"] not in PUNCT:
            return t
    return None


def _verb_in_clause(tokens: list[dict], i: int) -> dict | None:
    """The nearest following verbal token, stopping at a comma (a clause boundary)."""
    for t in tokens[i + 1:]:
        if t["pos_coarse"] in PUNCT:
            return None
        if t["pos_coarse"] in ("動詞", "形容詞", "形状詞"):
            return t
    return None


# --------------------------------------------------------------------- fixed compound postpositions
# Each tokenizes as 助詞 + 動詞(連用形) + て, so the て template used to read it as a plain connector
# and claim "て liga する ao que vem depois". They are lexical units; the て is not doing that job.
TE_LOCUTIONS = {
    "として", "について", "によって", "に対して", "にとって", "に関して", "を通して",
    "に応じて", "に基づいて", "にわたって", "をめぐって", "に従って", "に比べて",
    "に加えて", "に向けて", "に沿って", "に際して", "に先立って", "に伴って",
    "に反して", "を通じて",
}
# Trigrams that are a locution ONLY in a wider frame, because the same three tokens are also an
# ordinary verb + て: をもって is 持って far more often than 以て, and にかけて is the locution only
# in AからBにかけて (礼儀にかけている is 欠ける). Each carries the extra token it needs.
TE_LOCUTIONS_GUARDED = {"にかけて": "から"}
# An auxiliary right after the て means the trigram is a real verb carrying real aspect, not a
# postposition: 必要としている is 必要とする + ている, 事実に基づいている is 基づく + ている,
# 位置についていた is 付く + ていた, 脇によってください is 寄る + てください.
TE_AUXILIARY_AFTER = {"いる", "ある", "おる", "くださる"}


def _in_te_locution(tokens: list[dict], i: int) -> bool:
    """True when the て at i is the tail of a fixed compound postposition (particle + verb + て)."""
    if i < 2:
        return False
    nxt = _next(tokens, i)
    if nxt and nxt["pos_coarse"] == "動詞" and (nxt.get("lemma") or "") in TE_AUXILIARY_AFTER:
        return False
    tri = tokens[i - 2]["surface"] + tokens[i - 1]["surface"] + tokens[i]["surface"]
    if tri in TE_LOCUTIONS:
        return True
    need = TE_LOCUTIONS_GUARDED.get(tri)
    return bool(need and any(t["surface"] == need for t in tokens[:i - 2]))


# ------------------------------------------------------------------- occurrence-checked pair labels
NEG_LEMMAS = {"ない", "ぬ"}
# どう / どの are deliberately ABSENT: どうも is the adverb "somehow", not an interrogative, and
# どうも〜ない (呼吸がどうも合わない) is not total negation.
INTERROGATIVE_LEMMAS = {"何", "誰", "どこ", "いつ", "どれ", "どちら", "どっち", "なに",
                        "どなた", "何処", "何時"}
MINIMIZER_LEMMAS = {"少し", "ちっとも", "全然", "一つ", "一人", "一度", "一言", "一切", "微塵"}
COMITATIVE_VERBS = {"話す", "会う", "結婚", "結婚する", "付き合う", "遊ぶ", "住む", "暮らす",
                    "戦う", "争う", "喧嘩", "けんか", "相談", "一致", "似る", "比べる",
                    "出会う", "知り合う", "別れる", "踊る", "話し合う", "競争", "同居"}
QUOTATIVE_VERBS = {"言う", "いう", "思う", "呼ぶ", "書く", "聞く", "考える", "答える",
                   "感じる", "分かる", "わかる", "見える", "決める", "read", "叫ぶ", "告げる"}
RESULTATIVE_VERBS = {"なる", "する"}
MOTION_VERBS = {"歩く", "行く", "来る", "帰る", "登る", "上る", "泳ぐ", "走る", "運ぶ", "送る",
                "伸びる", "延びる", "続く", "届く", "通う", "戻る", "進む", "案内", "移る",
                "飛ぶ", "乗る", "登山", "下る", "近づく", "至る", "たどり着く", "着く"}
TIME_NOUN_LEMMAS = {"今日", "明日", "昨日", "今", "朝", "昼", "夜", "夕方", "今朝", "今晩",
                    "来週", "先週", "今週", "来年", "去年", "今年", "時", "時間", "分", "秒",
                    "日", "月", "年", "週", "午前", "午後", "正午", "夜中", "今度", "最後",
                    "終わり", "明後日", "一昨日", "晩", "深夜", "夕べ", "いつ", "何時", "暮れ"}

LABEL_COPULA_DE = "で da cópula (forma で de です/だ)"
LABEL_TOTAL_NEG_MO = "も de negação total (nada / ninguém / nenhum)"
LABEL_SPATIAL_MADE = "まで de limite espacial ('até')"
LABEL_COMITATIVE_TO = "と de companhia ('com')"
LABEL_ADVERBIAL_NI = "に que forma advérbio"
LABEL_NA_SOFT_ORDER = "partícula final de ordem suave (〜な = 〜なさい)"
LABEL_NA_EMPHASIS = "partícula final de ênfase"


def _clause_has_negation(tokens: list[dict], i: int) -> bool:
    """A negation anywhere between i and the end of its clause (a comma closes the clause)."""
    for t in tokens[i + 1:]:
        if t["pos_coarse"] in PUNCT and t.get("pos_fine") == "読点":
            return False
        if t.get("lemma") in NEG_LEMMAS and t["pos_coarse"] in ("助動詞", "形容詞"):
            return True
    return False


def _is_time_noun(t: dict | None) -> bool:
    if not t:
        return False
    if (t.get("lemma") or t["surface"]) in TIME_NOUN_LEMMAS:
        return True
    f3 = t.get("pos_fine3")
    return bool(f3 and f3 != "*" and f3 == "副詞可能")


# Stems that build an adverb with に but that Sudachi files as ordinary nouns (サ変可能/一般), so
# 形状詞可能 alone does not reach them.
ADVERBIAL_NI_STEMS = {"一緒", "本当", "非常", "実際", "十分", "充分", "無事", "確実", "正直",
                      "自由", "適当", "個人的", "積極的", "具体的", "基本的", "一般的",
                      "最終的", "徐々", "次第", "別々", "順番", "同時", "一斉", "永久"}


def _na_adjective_stem(t: dict | None) -> bool:
    if not t:
        return False
    if t["pos_coarse"] == "形状詞":
        return True
    if (t.get("lemma") or t["surface"]) in ADVERBIAL_NI_STEMS:
        return True
    return t["pos_coarse"] in NOMINAL and t.get("pos_fine3") == "形状詞可能"


def function_pt_fix(tokens: list[dict], i: int, particle: str, ft: str | None,
                    modal: str | None) -> tuple[str, str] | None:
    """(corrected label, rule id) when the pair modal is wrong for THIS occurrence, else None.

    Six rules, each of them the narrowest test that separates the reading the modal names from the
    reading actually present. Everything the tests do not reach keeps the pair modal: this function
    is an override list, not a classifier.
    """
    key = (particle, ft or "")
    prev = _prev(tokens, i)
    nxt = _next(tokens, i)

    # 1. で before ない / ある is the copula of ではない・でもある, not the で of "lugar da ação"
    if key == ("で", "case"):
        n1 = tokens[i + 1] if i + 1 < len(tokens) else None
        n2 = n1
        if n1 and n1["pos_coarse"] == "助詞" and n1["surface"] in ("は", "も"):
            n2 = tokens[i + 2] if i + 2 < len(tokens) else None
        if n2 and n2.get("lemma") in ("ない", "ある") \
                and n2["pos_coarse"] in ("形容詞", "動詞", "助動詞"):
            return LABEL_COPULA_DE, "label-copula-de"

    # 2. も after an interrogative or a minimizer, in a negative clause, is total negation
    if key == ("も", "binding") and prev is not None:
        lem = prev.get("lemma") or prev["surface"]
        if (lem in INTERROGATIVE_LEMMAS or lem in MINIMIZER_LEMMAS) and _clause_has_negation(tokens, i):
            return LABEL_TOTAL_NEG_MO, "label-total-negation-mo"

    # 3. まで on a nominal that is not a time expression, with a verb of motion or extent in the
    #    clause, is a limit in SPACE. The motion verb is what makes it decidable: without it,
    #    クリスマスまで (time) and 第二次大戦まで (scope) look exactly like 駅まで to a parser.
    if key == ("まで", "adverbial") and prev is not None and "temporal" in (modal or ""):
        v = _verb_in_clause(tokens, i)
        if prev["pos_coarse"] in NOMINAL and not _is_time_noun(prev) \
                and v and (v.get("lemma") or "") in MOTION_VERBS:
            return LABEL_SPATIAL_MADE, "label-spatial-made"

    # 4. と between nominals, before 一緒に or a reciprocal verb, is comitative and not quotative
    if key == ("と", "case") and prev is not None and prev["pos_coarse"] in NOMINAL:
        v = _verb_in_clause(tokens, i)
        vlem = (v.get("lemma") if v else None) or ""
        if nxt and (nxt.get("lemma") or nxt["surface"]) == "一緒":
            return LABEL_COMITATIVE_TO, "label-comitative-to"
        if vlem in COMITATIVE_VERBS and vlem not in QUOTATIVE_VERBS:
            return LABEL_COMITATIVE_TO, "label-comitative-to"

    # 5. に on a na-adjective stem in front of a verb builds an adverb; it is not a destination.
    #    〜になる / 〜にする are the resultative pair, a different reading, so they are held back.
    if key == ("に", "case") and _na_adjective_stem(prev):
        v = _verb_in_clause(tokens, i)
        vlem = (v.get("lemma") if v else None) or ""
        if v and vlem not in RESULTATIVE_VERBS:
            return LABEL_ADVERBIAL_NI, "label-adverbial-ni"

    # 6. sentence-final な is a prohibition only on a plain-form VERB (行くな, 悩むな). On a
    #    continuative stem it is the soft order 〜なさい (行きな); after だ / です / an i-adjective /
    #    たい it is plain emphasis (期間だな, 欲しいな, 洗いたいな).
    #    TERMINAL and ATTRIBUTIVE both count: the two forms are homophonous for every regular verb
    #    and Sudachi's pick in front of a 終助詞 is arbitrary (読むな 終止形 vs 悩むな 連体形).
    if key == ("な", "sentence-final") and "proibi" in (modal or ""):
        if prev and prev["pos_coarse"] == "動詞":
            if prev.get("inflection") in ("terminal", "attributive"):
                return None
            if prev.get("inflection") == "continuative":
                return LABEL_NA_SOFT_ORDER, "label-na-soft-order"
        return LABEL_NA_EMPHASIS, "label-na-emphasis"

    return None


def particle_template(tokens: list[dict], i: int, particle: str, ft: str | None) -> str | None:
    """The templated pt-BR explanation, or None when the pair/shape is not covered (then: author).

    Every sentence produced here is true by construction from the dissection: it names the tokens the
    particle actually stands between and the role the (particle, function_type) pair actually assigns.
    It claims nothing about meaning that the corpus does not already record.
    """
    key = (particle, ft or "")
    if key in CONTEXT_FREE:
        return CONTEXT_FREE[key]

    prev, nxt = _prev(tokens, i), _next(tokens, i)
    chunk = _left_chunk(tokens, i)

    if key == ("は", "binding"):
        if not chunk or not prev or prev["pos_coarse"] not in NOMINAL:
            return None      # では / には / とは / 〜てはいけない: a different は, authored
        return (f"は apresenta {chunk} como o tópico da frase, ou seja, o assunto sobre o qual se faz a "
                f"afirmação seguinte.")

    if key == ("が", "case"):
        if not chunk or not prev or prev["pos_coarse"] not in NOMINAL:
            return None
        v = _verb_in_clause(tokens, i)
        if v:
            return (f"が marca {chunk} como o sujeito de {v['lemma']}, isto é, quem faz ou de quem se diz "
                    f"o que o predicado exprime.")
        return f"が marca {chunk} como o sujeito daquilo que se afirma em seguida."

    if key == ("を", "case"):
        v = _verb_in_clause(tokens, i)
        if not chunk or not prev or prev["pos_coarse"] not in NOMINAL or not v \
                or v["pos_coarse"] != "動詞":
            return None
        return (f"を marca {chunk} como o objeto direto de {v['lemma']}, ou seja, aquilo sobre o que a "
                f"ação recai.")

    if key == ("の", "case"):
        if not chunk or not prev or not nxt or prev["pos_coarse"] not in NOMINAL \
                or nxt["pos_coarse"] not in NOMINAL:
            return None
        # the modifier is the whole left chunk, not just the token の touches: 十頭の牛 modifies with
        # 十頭, not with 頭
        return (f"の liga {chunk} a {nxt['surface']} e junta os dois num bloco só, em que "
                f"{nxt['surface']} é o núcleo e {chunk} o modificador.")

    if key == ("て", "conjunctive"):
        if not prev or prev["pos_coarse"] not in ("動詞", "形容詞", "助動詞") or not nxt:
            return None
        if _in_te_locution(tokens, i):
            return None      # として / について / によって …: a compound postposition, authored
        # the lemma, so an auxiliary reads as いる rather than as the bare stem い it appears as
        right = nxt.get("lemma") or nxt["surface"]
        return (f"て liga {prev['lemma']} ao que vem depois ({right}) e encadeia os dois dentro "
                f"da mesma frase.")

    return None


# ------------------------------------------------------------------------------------------- inputs
def load_rows() -> list[dict]:
    rows = []
    for name, gen in (("accepted.json", False), ("generated.json", True)):
        for r in json.loads((MINED / name).read_text(encoding="utf-8"))["rows"]:
            if r.get("reject"):
                continue
            r = dict(r)
            r["generated"] = gen or bool(r.get("generated"))
            rows.append(r)
    return rows


def load_skeletons(rows: list[dict], db: Path | None, cache: Path | None) -> dict[str, dict]:
    """Skeletons by sentence key. Uses the cache when it covers the input; otherwise runs the Dissector."""
    by_jp: dict[str, dict] = {}
    if cache and cache.exists():
        for line in cache.read_text(encoding="utf-8").splitlines():
            if line.strip():
                sk = json.loads(line)
                by_jp[sk["jp"]] = sk
    missing = [r for r in rows if r["jp"] not in by_jp]
    if missing:
        if not db:
            raise SystemExit(f"{len(missing)} sentences have no cached skeleton and no --db was given")
        sys.path.insert(0, str(ROOT / "scripts" / "ingest"))
        sys.path.insert(0, str(ROOT / "scripts"))
        from dissect import Dissector           # noqa: PLC0415
        diss = Dissector(db)
        for r in missing:
            sk = diss.skeleton(r["jp"])
            by_jp[r["jp"]] = {"jp": r["jp"], "tokens": sk["tokens"], "particles": sk["particles"]}
        if cache:
            with cache.open("w", encoding="utf-8") as fh:
                for sk in by_jp.values():
                    fh.write(json.dumps(sk, ensure_ascii=False) + "\n")
    return {sentence_key(r): by_jp[r["jp"]] for r in rows}


ORIGIN = {"bank": "bank-modal", "registry-sense0": "registry"}


def enrich_pos_fine3(tokens: list[dict], jp: str) -> list[dict]:
    """Zip Sudachi's 3rd/4th POS fields onto skeleton tokens (the skeleton drops them).

    `dissect.Dissector` keeps only pos_coarse/pos_fine, but the chunk rules need 副詞可能 (adverbial
    noun) and 形状詞可能 (na-adjective-capable noun). Same tokenizer, same split mode, same order,
    so positions line up; if they ever do not, the tokens come back untouched and the rules fall back
    to `ADVERBIAL_NOUN_LEMMAS`.
    """
    try:
        from sudachipy import dictionary, tokenizer                       # noqa: PLC0415
    except ImportError:
        return tokens
    global _TOK
    if _TOK is None:
        _TOK = dictionary.Dictionary(dict="full").create()
    morphs = list(_TOK.tokenize(jp, tokenizer.Tokenizer.SplitMode.C))
    if len(morphs) != len(tokens):
        return tokens
    for t, m in zip(tokens, morphs):
        if t["surface"] != m.surface():
            return tokens
        p = m.part_of_speech()
        t["pos_fine3"], t["pos_fine4"] = p[2], p[3]
    return tokens


_TOK = None


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", type=Path, default=None, help="a COPY of corpus.sqlite (Dissector input)")
    ap.add_argument("--skeletons", type=Path, default=None, help="jsonl cache of dissector skeletons")
    ap.add_argument("--batch-size", type=int, default=150)
    ap.add_argument("--out", type=Path, default=OUT_DIR)
    args = ap.parse_args()

    rows = load_rows()
    residue = json.loads((MINED / "layerb_residue.json").read_text(encoding="utf-8"))
    res_by_jp = {s["jp"]: s for s in residue["sentences"]}
    skel = load_skeletons(rows, args.db, args.skeletons)
    print(f"{len(rows)} sentences, {len(skel)} skeletons, {len(res_by_jp)} residue records")

    stats: Counter = Counter()
    template_by_pair: Counter = Counter()
    author_by_pair: Counter = Counter()
    out_sentences = []

    for r in rows:
        key = sentence_key(r)
        sk = skel[key]
        res = res_by_jp.get(r["jp"], {})
        toks = enrich_pos_fine3(sk["tokens"], r["jp"])

        # -------- tokens
        tokens_out = []
        for rt in res.get("tokens", []):
            gloss, origin = rt.get("gloss_pt"), ORIGIN.get(rt.get("gloss_source"))
            if gloss:
                status = rt.get("confidence") or "ambiguous-verify"
            else:
                num = numeral_gloss(rt["surface"])
                if num is not None:
                    gloss, origin, status = num, "rule-numeral", "unique-accept"
                else:
                    origin, status = None, "author"
            stats[f"token:{status}"] += 1
            if origin:
                stats[f"origin:{origin}"] += 1
            # lemma + pos ride along so a per-(lemma, pos) ruling can be applied to this row later
            # without re-reading the residue; the ingest ignores keys it does not know.
            row = {"position": rt["position"], "lemma": rt.get("lemma"), "pos": rt.get("pos"),
                   "gloss_status": status, "gloss_origin": origin}
            if gloss:
                row["gloss_pt"] = gloss
            tokens_out.append(row)

        # -------- particles
        particles_out = []
        for rp in res.get("particles", []):
            pos = rp["position"]
            i = next((n for n, t in enumerate(toks) if t["position"] == pos), None)
            ft = rp.get("function_type")
            expl = particle_template(toks, i, rp["particle"], ft) if i is not None else None
            pair = f"{rp['particle']}/{ft}"
            if expl:
                template_by_pair[pair] += 1
                stats["particle:template"] += 1
            else:
                author_by_pair[pair] += 1
                stats["particle:author"] += 1
            if not rp.get("function_pt"):
                stats["particle:function_author"] += 1
            fn, fn_status = rp.get("function_pt"), "bank-modal" if rp.get("function_pt") else "author"
            fix = function_pt_fix(toks, i, rp["particle"], ft, fn) if i is not None else None
            if fix:
                fn, fn_status = fix[0], "occurrence-rule"
                stats[f"function_fix:{fix[1]}"] += 1
            particles_out.append({
                "position": pos,
                "particle": rp["particle"],
                "function_type": ft,
                "function_pt": fn,
                "function_status": fn_status,
                "explanation_pt": expl,
                "explanation_status": "template" if expl else "author",
            })

        cs = predict_clause_structure(toks)
        stats[f"clause:{cs}"] += 1
        out_sentences.append({
            "key": key,
            "tatoeba_id": r.get("tatoeba_id") if not key.startswith("gen-") else None,
            "slug": sentence_slug(key),
            "generated": bool(r.get("generated")),
            "jp": r["jp"],
            "lesson": r.get("lesson"),
            "targets": r.get("targets") or ([r["target"]] if r.get("target") else []),
            "clause_structure_predicted": cs,
            "tokens": tokens_out,
            "particles": particles_out,
            "structure_explanation_pt": None,
            "structure_status": "author",
        })
        stats["sentences"] += 1

    # -------- emit
    args.out.mkdir(parents=True, exist_ok=True)
    for f in args.out.glob("batch-*.json"):
        f.unlink()
    n = args.batch_size
    batches = [out_sentences[i:i + n] for i in range(0, len(out_sentences), n)]
    for bi, chunk in enumerate(batches, 1):
        (args.out / f"batch-{bi:02d}.json").write_text(
            json.dumps({"batch": bi, "unit": "W13b", "kind": "derived (mechanical) mined Layer-B",
                        "sentences": chunk}, ensure_ascii=False, indent=1), encoding="utf-8")
    summary = {
        "unit": "W13b",
        "generated_by": "scripts/derive_layerb.py",
        "inputs": ["research/derived/n3_mined/accepted.json",
                   "research/derived/n3_mined/generated.json",
                   "research/derived/n3_mined/layerb_residue.json"],
        "batches": len(batches),
        "batch_size": n,
        "counts": dict(sorted(stats.items())),
        "particle_template_by_pair": dict(template_by_pair.most_common()),
        "particle_author_by_pair": dict(author_by_pair.most_common(40)),
    }
    (args.out / "_summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=1),
                                            encoding="utf-8")
    print(json.dumps(summary["counts"], ensure_ascii=False, indent=1))
    print(f"wrote {len(batches)} batches to {args.out}")
    return 0


# ------------------------------------------------------------------------------------- rule tests
def _tokenize(jp: str) -> list[dict]:
    """Skeleton-shaped tokens straight from Sudachi — no DB, for the tests only."""
    from sudachipy import dictionary, tokenizer                            # noqa: PLC0415
    sys.path.insert(0, str(ROOT / "scripts" / "ingest"))
    from dissect import PARTICLE_FUNCTION_MAP, neutral_inflection          # noqa: PLC0415
    global _TOK
    if _TOK is None:
        _TOK = dictionary.Dictionary(dict="full").create()
    out = []
    for n, m in enumerate(_TOK.tokenize(jp, tokenizer.Tokenizer.SplitMode.C)):
        p = m.part_of_speech()
        out.append({"position": n, "surface": m.surface(), "lemma": m.dictionary_form(),
                    "pos_coarse": p[0], "pos_fine": p[1], "pos_fine3": p[2], "pos_fine4": p[3],
                    "inflection": neutral_inflection(p[5]),
                    "inflection_type": p[4] if p[4] != "*" else None,
                    "particle_function": (PARTICLE_FUNCTION_MAP.get(p[1]) if p[0] == "助詞"
                                          else None)})
    return out


def _at(toks: list[dict], surface: str, nth: int = 0) -> int:
    hits = [n for n, t in enumerate(toks) if t["surface"] == surface]
    return hits[nth]


# (sentence, particle surface, occurrence, v1 chunk, v2 chunk) — every chunk case the batch-30
# verifier raised, plus the shapes that must NOT change.
CHUNK_CASES = [
    ("明日雨が降るでしょう。",        "が", 0, "明日雨",         "雨"),
    ("思わず大きな声を出した。",      "を", 0, "思わず大きな声", "大きな声"),
    ("急に人が増えた。",              "が", 0, "急に人",         "人"),
    ("毎日日本語を勉強する。",        "を", 0, "毎日日本語",     "日本語"),
    ("今朝早く駅に着いた。",          "に", 0, "今朝早く駅",     "駅"),
    ("昨日彼は来た。",                "は", 0, "昨日彼",         "彼"),
    ("きれいな花が咲いた。",          "が", 0, "きれいな花",     "きれいな花"),
    ("十頭の牛がいる。",              "の", 0, "十頭",           "十頭"),
    ("彼は報酬として金の時計をもらった。", "は", 0, "彼",        "彼"),
    ("日本語学校は駅の前だ。",        "は", 0, "日本語学校",     "日本語学校"),
    # a predicate that keeps inflecting to the right is ONE phrase, never an adverbial + noun
    ("やりたいことを何でもやる。",    "を", 0, "やりたいこと",   "やりたいこと"),
    ("引退した後は何をするの？",      "は", 0, "引退した後",     "引退した後"),
    ("彼はぼんやりした表情をしていた。", "を", 0, "ぼんやりした表情", "ぼんやりした表情"),
    ("彼は生産率を良くする案を出した。", "を", 1, "良くする案",   "良くする案"),
    ("お肉の焼き加減はいかがですか。", "は", 0, "焼き加減",       "焼き加減"),
    ("そういう印象を与えた。",        "を", 0, "そういう印象",   "そういう印象"),
    ("彼らはより強力な武器を作った。", "を", 0, "より強力な武器", "より強力な武器"),
    # but an adverb sitting in front of a NOUN is an adjunct of the clause, and goes
    ("彼は早く目が覚める。",          "が", 0, "早く目",         "目"),
    ("彼は早く出発することを勧めた。", "を", 0, "早く出発すること", "出発すること"),
    ("特にこの場面が好きですねえ。",  "が", 0, "特にこの場面",   "この場面"),
    ("瓶には少し牛乳がある。",        "が", 0, "少し牛乳",       "牛乳"),
    ("薄暮れが迫った。",              "が", 0, "薄暮れ",         "薄暮れ"),
    # a formal noun cannot head the phrase alone, so its left neighbour survives the walk
    ("土曜以外は毎日働いています。",  "は", 0, "土曜以外",       "土曜以外"),
    ("車には一人分の空きがあった。",  "の", 0, "一人分",         "一人分"),
    ("もう１人分の空きはありますか。", "の", 0, "もう１人分",    "１人分"),
]

# (sentence, particle surface, occurrence, pair modal, expected label, expected rule)
LABEL_CASES = [
    ("これは本ではない。",     "で", 0, "partícula de lugar da ação",       LABEL_COPULA_DE,     "label-copula-de"),
    ("彼女は先生でもある。",   "で", 0, "partícula de lugar da ação",       LABEL_COPULA_DE,     "label-copula-de"),
    ("書斎で仕事をした。",     "で", 0, "partícula de lugar da ação",       None,                None),
    ("そこでは何もない。",     "も", 0, "partícula de inclusão ('também')", LABEL_TOTAL_NEG_MO,  "label-total-negation-mo"),
    ("誰も来なかった。",       "も", 0, "partícula de inclusão ('também')", LABEL_TOTAL_NEG_MO,  "label-total-negation-mo"),
    ("少しも分からない。",     "も", 0, "partícula de inclusão ('também')", LABEL_TOTAL_NEG_MO,  "label-total-negation-mo"),
    ("私も人間です。",         "も", 0, "partícula de inclusão ('também')", None,                None),
    ("川まで歩いた。",       "まで", 0, "limite temporal ('até')",          LABEL_SPATIAL_MADE,  "label-spatial-made"),
    ("三時まで待った。",     "まで", 0, "limite temporal ('até')",          None,                None),
    ("この症状はいつまで続くのですか。", "まで", 0, "limite temporal ('até')", None,             None),
    ("クリスマスまでもう２週間だ。", "まで", 0, "limite temporal ('até')",     None,              None),
    ("この本は第二次大戦までしか扱っていない。", "まで", 0, "limite temporal ('até')", None,      None),
    ("彼とはどうも呼吸が合わない。", "も", 0, "partícula de inclusão ('também')", None,           None),
    ("友達と一緒に行った。",   "と", 0, "partícula de citação",             LABEL_COMITATIVE_TO, "label-comitative-to"),
    ("彼と話した。",           "と", 0, "partícula de citação",             LABEL_COMITATIVE_TO, "label-comitative-to"),
    ("留守だと言いなさい。",   "と", 0, "partícula de citação",             None,                None),
    ("友達と一緒に行った。",   "に", 0, "partícula de destino/direção",     LABEL_ADVERBIAL_NI,  "label-adverbial-ni"),
    ("彼女は病気になった。",   "に", 0, "partícula de destino/direção",     None,                None),
    ("駅に着いた。",           "に", 0, "partícula de destino/direção",     None,                None),
    ("本を読むな。",           "な", 0, "partícula final de proibição",     None,                None),
    ("彼に逆らうな。",         "な", 0, "partícula final de proibição",     None,                None),
    ("早く行きな。",           "な", 0, "partícula final de proibição",     LABEL_NA_SOFT_ORDER, "label-na-soft-order"),
    ("いい天気だな。",         "な", 0, "partícula final de proibição",     LABEL_NA_EMPHASIS,   "label-na-emphasis"),
    ("そのことで悩むな。",     "な", 0, "partícula final de proibição",     None,                None),
    ("二人っきりで話したいな。", "な", 0, "partícula final de proibição",   LABEL_NA_EMPHASIS,   "label-na-emphasis"),
    ("チェスセットが欲しいな。", "な", 0, "partícula final de proibição",   LABEL_NA_EMPHASIS,   "label-na-emphasis"),
]

# sentences whose て must lose the template (compound postposition) and one that must keep it
TE_CASES = [("彼は報酬として金の時計をもらった。", True),
            ("その件について話した。", True),
            ("この結婚は彼の将来にとって有利になるだろう。", True),
            ("住民たちは騒音に対して苦情を訴えた。", True),
            ("５月から８月にかけて雨がよく降る。", True),      # guarded: から is present
            ("彼は礼儀にかけている。", False),                 # same trigram, no から: 欠ける
            ("その画家は独特なスタイルをもっている。", False),  # をもって is 持って here
            ("鳥は鋭い目をもっている。", False),
            ("姉は大学の先生の助手として働いている。", True),   # として + 働く: the locution
            ("彼らは援助を必要としている。", False),            # 必要とする + ている
            ("この話は事実に基づいている。", False),            # 基づく + ている
            ("その国は輸入を減らそうとしている。", False),      # 〜(よ)うとする + ている
            ("注はページの下欄についている。", False),          # 付く + ている
            ("脇によってください。", False),                    # 寄る + てください
            ("パンを食べて学校へ行った。", False)]


def selftest() -> int:
    bad = 0
    for jp, surf, nth, want_v1, want_v2 in CHUNK_CASES:
        toks = _tokenize(jp)
        i = _at(toks, surf, nth)
        got_v1, got_v2 = _left_chunk_v1(toks, i), chunk_head(toks, i)
        for label, got, want in (("v1", got_v1, want_v1), ("v2", got_v2, want_v2)):
            if got != want:
                bad += 1
                print(f"FAIL chunk/{label} {jp} @{surf}: got {got!r} want {want!r}")
    for jp, surf, nth, modal, want_label, want_rule in LABEL_CASES:
        toks = _tokenize(jp)
        i = _at(toks, surf, nth)
        ft = toks[i].get("particle_function")
        got = function_pt_fix(toks, i, surf, ft, modal)
        gl, gr = (got if got else (None, None))
        if (gl, gr) != (want_label, want_rule):
            bad += 1
            print(f"FAIL label {jp} @{surf} ({surf}/{ft}): got {(gl, gr)!r} want {(want_label, want_rule)!r}")
    for jp, want in TE_CASES:
        toks = _tokenize(jp)
        i = next(n for n, t in enumerate(toks) if t["surface"] == "て" and t["pos_coarse"] == "助詞")
        if _in_te_locution(toks, i) != want:
            bad += 1
            print(f"FAIL te-locution {jp}: got {not want} want {want}")
    n = len(CHUNK_CASES) * 2 + len(LABEL_CASES) + len(TE_CASES)
    print(f"{n - bad}/{n} rule assertions passed")
    return 1 if bad else 0


if __name__ == "__main__":
    if "--selftest" in sys.argv:
        sys.exit(selftest())
    sys.exit(main())
