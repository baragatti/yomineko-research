"""W31 - derive sentence-level `register` for the bank (5,889) and the W13 rows (4,223).

DERIVATION ONLY. Reads committed JSON + the JMdict zip; writes one table under
research/derived/pending/. Never touches db/, course/, design/ or any exporter.

Predicate detection is done with SudachiPy (dict=full, split mode C) on the LAST BUNSETSU of
each sentence unit - never by a suffix string match.
"""
import sys, os, json, re, hashlib, argparse, datetime
sys.stdout.reconfigure(encoding="utf-8")

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(REPO, "scripts"))
from derive_sentence_register import build_jmdict_map, DIALECT_TAGS  # JMdict misc map + cache

from sudachipy import dictionary, tokenizer

# W31 apply. The tree being read is a PARAMETER, not this file's own location:
# scripts/validate/validate_sentence_register.py re-derives on the tree it is validating, and a
# plant proof copies the whole thing into a fixture. A validator left reading the real repo passes
# falsely (memory: validator-plant-proof-root), so every input below hangs off ROOT and ROOT is set
# by --root. The JMdict zip is the one exception: it is a licensed dataset, not corpus content, and
# it is always read from the repo.
ROOT = REPO
BANK = ACCEPTED = GENERATED = GRAMMAR_DIR = FIRST = OUT = None


def set_root(root):
    """Point every input at `root`. Called once from main(), before anything is read."""
    global ROOT, BANK, ACCEPTED, GENERATED, GRAMMAR_DIR, FIRST, OUT
    ROOT = os.path.abspath(root)
    BANK = os.path.join(ROOT, "corpus", "sentences", "bank.json")
    ACCEPTED = os.path.join(ROOT, "research", "derived", "n3_mined", "accepted.json")
    GENERATED = os.path.join(ROOT, "research", "derived", "n3_mined", "generated.json")
    GRAMMAR_DIR = os.path.join(ROOT, "corpus", "grammar")
    FIRST = os.path.join(ROOT, "research", "derived", "pending", "sentence_register.json")
    # W31 apply: the table moved pending/ -> repairs/ the day it was applied. `pending` means
    # "authored, not applied" (STATE aj) and the replay gate owns `repairs/`.
    OUT = os.path.join(ROOT, "research", "derived", "repairs", "sentence_register.json")


set_root(REPO)

D7 = ("neutral", "polite", "casual", "formal", "vulgar", "archaic", "epistolary", "dialect", "slang")
PRECEDENCE = ("epistolary", "archaic", "vulgar", "dialect", "slang", "formal", "polite", "casual", "neutral")

# ---------------------------------------------------------------- lexical sets

HON_STRICT = {"いらっしゃる", "おっしゃる", "仰る", "なさる", "為さる", "召し上がる", "召しあがる",
              "おいでになる", "お出でになる"}
HUMBLE = {"伺う", "窺う", "申す", "申し上げる", "致す", "存ずる", "存じる", "存じ上げる",
          "参る", "拝見", "拝借", "拝聴", "差し上げる", "承る", "頂戴", "いたす"}
GOZARU = {"ござる", "御座る"}
FIXED_GOZAIMASU = ("ありがとうござい", "有り難うござい", "おはようござい", "お早うござい",
                   "おめでとうござい", "御目出度うござい", "ごちそうさま", "いらっしゃいませ",
                   "お世話さま", "おかげさま")
POLITE_SET_PHRASES = ("こんにちは", "こんばんは", "おやすみなさい", "さようなら", "さよなら",
                      "すみません", "すいません", "ごめんなさい", "はじめまして", "初めまして",
                      "いらっしゃいませ", "失礼します", "失礼しました", "おかげさまで",
                      "ありがとうございます", "ありがとうございました", "おはようございます")
CASUAL_SET_PHRASES = ("じゃあね", "じゃーね", "またね", "バイバイ", "ばいばい", "ごめんね",
                      "ありがとね", "おっす", "うっす", "また明日", "じゃあ、")
# 「よっ」 and 「やあ」 were dropped: they match inside によって / いやあ and cost more than
# the two greetings they catch.
# Greetings whose casual form is the SAME string as the stem of a polite one: only count them
# when the polite continuation is absent.
CASUAL_GREETING_GUARDED = (("おはよう", "おはようござい"), ("ごめん", "ごめんなさい"),
                           ("ありがとう", "ありがとうござい"), ("おめでとう", "おめでとうござい"),
                           ("おやすみ", "おやすみなさい"))

SECOND_ROUGH = {"てめえ", "てめぇ", "てめー", "貴様", "きさま", "手前ら", "われ"}
SECOND_CASUAL = {"お前", "おまえ", "オマエ", "あんた", "あんたら", "おめえ", "お前ら", "君たち", "君ら"}
VULGAR_STRINGS = ("くたばれ", "くたばっ", "ちくしょう", "畜生", "くそったれ", "クソったれ",
                  "ぶっ殺", "ぶちのめ", "死ね", "うんこ", "ばか野郎", "馬鹿野郎", "この野郎")

EPISTOLARY = ("拝啓", "敬具", "謹啓", "敬白", "前略", "草々", "拝復", "取り急ぎ", "略儀",
              "ご清栄", "御清栄", "ご健勝", "御健勝", "お慶び申し上げ", "謹んで申し上げ",
              "貴社ますます", "時下ますます")
# 「〜の候」 must close a clause: 「后の候補は6名いた」 matched it as a substring.
EPISTOLARY_RE = re.compile(r"の候(?:[。．、！？!?\s]|$)")

# 〜たい (desiderative), 〜ばい and 〜けん were REMOVED from this list: they collide with
# standard Japanese (飲みたい, 冷たい, 〜ばいい, 〜けん as a noun) and produced 95 false
# "dialect" calls on the first run. Only markers with no standard homograph survive.
DIALECT_FINAL_RE = re.compile(
    r"(やねん|まんねん|へんで|へんねん|だっぺ|だべ|じゃけん|ばってん|ちゃうで|どすえ|"
    r"とちゃう|やで|やわ|やろ|やん)(?:[。．！？!?…\s]|$)")
DIALECT_RE = re.compile(r"(あかん|おおきに|ほんま|せやな|せやで|なんぼ|めんこい|だべさ)"
                        r"(?:[。．、！？!?…\sでやなねと]|$)")
SLANG_SURFACES = {"やばい", "ヤバい", "ヤバイ", "やべえ", "マジ", "まじ", "ウケる", "うける",
                  "ダサい", "だせえ", "キモい", "きもい", "めっちゃ", "メッチャ", "パクる",
                  "ドタキャン", "エモい", "ググる", "っす", "ぶっちゃけ"}

HARD_FINALS = {"ぞ", "ぜ", "さ", "かしら", "っけ", "じゃん", "もん", "だい", "かい", "い", "や"}
SOFT_FINALS = {"よ", "ね", "な", "なあ", "なぁ", "ねえ", "ねぇ", "の", "かな", "かなあ", "わ"}
CONTRACTION_AUX = {"てる", "でる", "とく", "どく", "とる", "ちゃう", "じゃう", "ちまう", "じまう"}
CONTRACTION_STRINGS = ("なきゃ", "なくちゃ", "なくっちゃ")

FUNC_POS = {"助詞", "助動詞", "接尾辞", "補助記号", "空白"}

# Sudachi tags several LIVING constructions with a 文語 inflection class because of their
# etymology. Measured over the 10,112 rows: 文語助動詞-ベシ fires 47× on 〜べきだ (a modern N3
# point the registry itself calls `neutral`), 文語サ行変格 6× on the 〜すべき of the same
# construction, 文語四段-カ行 + 文語助動詞-リ on 〜における (standard written Japanese) and
# 文語助動詞-ジ once on the kana string じ meaning 字. Only these classes are archaic, and
# ベシ only in its genuinely classical surfaces.
ARCHAIC_BUNGO = {"文語形容詞-ク", "文語形容詞-シク", "文語助動詞-ケリ", "文語助動詞-ナリ-断定",
                 "文語助動詞-タリ-断定", "文語助動詞-ゴトシ", "文語助動詞-マジ",
                 "文語助動詞-ズ", "文語助動詞-キ", "文語助動詞-ム"}
ARCHAIC_BESHI_SURFACES = {"べし", "べから", "べかざ"}

GRAMMAR_MAP = {  # registry vocabulary (grammar points) -> D7
    "plain": "neutral", "neutral": "neutral", "written": "neutral", "literary": "neutral",
    "polite": "polite", "formal": "formal", "honorific": "formal", "humble": "formal",
    "casual": "casual", "colloquial": "casual",
}
GRAMMAR_IGNORE = {"masculine", "feminine"}

W13_MAP = {"plain": "neutral", "colloquial": "casual", "honorific": "formal",
           "neutral": "neutral", "polite": "polite", "casual": "casual", "formal": "formal"}

# ---------------------------------------------------------------- helpers


class Tok:
    __slots__ = ("s", "p0", "p1", "p4", "p5", "norm", "dic")

    def __init__(self, m):
        p = m.part_of_speech()
        self.s = m.surface()
        self.p0, self.p1, self.p4, self.p5 = p[0], p[1], p[4], p[5]
        self.norm = m.normalized_form()
        self.dic = m.dictionary_form()

    def __repr__(self):
        return "%s[%s|%s|%s]" % (self.s, self.p0, self.p4, self.p5)


def split_units(toks):
    """Sentence units: break after a 補助記号|句点 token."""
    units, cur = [], []
    for t in toks:
        cur.append(t)
        if t.p0 == "補助記号" and t.p1 == "句点":
            units.append(cur)
            cur = []
    if cur:
        units.append(cur)
    return [u for u in units if any(t.p0 not in ("補助記号", "空白") for t in u)]


def last_bunsetsu(unit):
    """The final bunsetsu of one unit: its content head plus every function word after it,
    extended leftwards across te-linked auxiliary verbs. Returns (head_i, start_i, tokens)."""
    end = len(unit)
    while end > 0 and unit[end - 1].p0 in ("補助記号", "空白"):
        end -= 1
    if end == 0:
        return None
    i = end - 1
    while i >= 0 and unit[i].p0 in FUNC_POS:
        i -= 1
    if i < 0:
        return None
    head = i
    j = head
    while j - 2 >= 0 and unit[j - 1].p0 == "助詞" and unit[j - 1].p1 == "接続助詞" \
            and unit[j - 1].s in ("て", "で", "ちゃ", "じゃ") and unit[j - 2].p0 in ("動詞", "形容詞"):
        j -= 2
    return head, j, unit[j:end]


def analyse_unit(unit):
    """Politeness facts of one sentence unit, read off its last bunsetsu."""
    out = {"has_pred": False, "polite": None, "plain": False, "head": None,
           "imperative": False, "finals": [], "chain": []}
    lb = last_bunsetsu(unit)
    if not lb:
        return out
    head_i, start_i, chain = lb
    out["chain"] = [t.s for t in chain]
    head = unit[head_i]
    out["head"] = head

    for t in chain:
        if t.p0 == "助詞" and t.p1 == "終助詞":
            out["finals"].append(t.s)

    for t in chain:
        if t.p4 in ("助動詞-マス", "助動詞-デス"):
            if t.s in ("っす", "ッス"):
                continue                       # casual-polite slang, not です
            out["polite"] = t.s
            break
    if out["polite"] is None:
        for t in chain:                        # ございます / でございます
            if t.norm in GOZARU:
                out["polite"] = t.s
                break

    if head.p0 in ("動詞", "形容詞", "形状詞"):
        out["has_pred"] = True
    elif head.p0 in ("名詞", "代名詞") and any(t.p4 in ("助動詞-ダ", "助動詞-デス") for t in chain):
        out["has_pred"] = True
    elif any(t.p0 == "助動詞" for t in chain):
        out["has_pred"] = True
    for t in chain:
        if t.p5 and "命令形" in t.p5 and t.p0 == "動詞":
            out["imperative"] = True
    out["plain"] = out["has_pred"] and out["polite"] is None
    return out


def jmdict_tags(tok_vocab_ids, toks, jm):
    """Misc tags per token. `id` hits come from the bank's Layer-A vocab link and are decisive;
    form hits are decisive only on an uninflected surface."""
    hits = []
    for vid in tok_vocab_ids:
        tags = jm["by_id"].get(vid)
        if tags:
            hits.append({"surface": "vocab:%s" % vid, "tags": tags, "by": "id",
                         "decisive": True, "pos": None})
    for t in toks:
        if t.p0 in ("助詞", "助動詞", "補助記号", "空白"):
            continue
        for form in (t.dic, t.s):
            if form and len(form) > 1:
                tags = jm["by_form"].get(form)
                if tags:
                    hits.append({"surface": t.s, "tags": tags, "by": "form",
                                 "decisive": t.s == t.dic, "pos": t.p0})
                    break
    return hits


def load_grammar_registers():
    reg = {}
    for name in sorted(os.listdir(GRAMMAR_DIR)):
        if name.endswith(".json"):
            for it in json.load(open(os.path.join(GRAMMAR_DIR, name), encoding="utf-8")):
                reg[it.get("key")] = list(it.get("register") or [])
    return reg


def grammar_signal(keys, gram_reg):
    """(mapped value or None, raw notes). Unambiguous == the mapped set has exactly one member."""
    mapped, raw = set(), []
    for k in keys:
        vals = gram_reg.get(k)
        if not vals:
            continue
        raw.append("%s=%s" % (k, "/".join(vals)))
        for v in vals:
            if v in GRAMMAR_IGNORE:
                continue
            m = GRAMMAR_MAP.get(v)
            if m:
                mapped.add(m)
    if len(mapped) == 1:
        return mapped.pop(), raw
    return None, raw


# ---------------------------------------------------------------- the decision


_STEM_CACHE = {}


def is_verb_stem(surface, tok, MODE):
    """True when `surface` is the 連用形 stem of a verb (読み, 帰り, 待ち) rather than an ordinary
    noun (金持ち). Tested by re-tokenising surface+ます: お読みになる is honorific, お金持ちになる
    is not, and Sudachi tags both middles 名詞|普通名詞|一般 so only this test separates them."""
    if surface in _STEM_CACHE:
        return _STEM_CACHE[surface]
    ms = list(tok.tokenize(surface + "ます", MODE))
    ok = (len(ms) == 2 and ms[0].surface() == surface
          and ms[0].part_of_speech()[0] == "動詞"
          and ms[1].part_of_speech()[4] == "助動詞-マス")
    _STEM_CACHE[surface] = ok
    return ok


def decide(jp, toks, uinfo, jhits, gram_val, tok=None, MODE=None):
    """Returns (register or None, rule, confidence, signals[])."""
    sig = []
    surfaces = {t.s for t in toks}
    norms = {t.norm for t in toks}

    def tagged(tag):
        return [h for h in jhits if tag in h["tags"] and h["decisive"]]

    # ---- 1. epistolary
    ep = [m for m in EPISTOLARY if m in jp]
    if EPISTOLARY_RE.search(jp):
        ep.append("〜の候")
    if ep:
        sig.append("letter formula %s" % "/".join(ep[:2]))
        return "epistolary", "epistolary-formula", 0.9, sig

    # ---- 2. archaic
    bungo = [t for t in toks if t.p4 in ARCHAIC_BUNGO
             or (t.p4 == "文語助動詞-ベシ" and t.s in ARCHAIC_BESHI_SURFACES)]
    if bungo:
        sig.append("classical inflection %s (%s)" % (bungo[0].s, bungo[0].p4))
        return "archaic", "bungo-inflection", 0.9 if len(bungo) > 1 else 0.85, sig
    if re.search(r"(候|そうろう)(?:[。．、！？!?]|$)", jp) or "たまえ" in jp or "給え" in jp:
        sig.append("classical clause-final 候/〜たまえ")
        return "archaic", "classical-final", 0.8, sig
    arch = [h for h in tagged("arch") + tagged("obs")
            if h["by"] == "id"]           # form hits are too noisy (徐々 read as arch)
    if arch:
        sig.append("JMdict arch/obs on %s" % arch[0]["surface"])
        return "archaic", "jmdict-arch", 0.7, sig

    # ---- 3. vulgar
    vulg = tagged("vulg") + tagged("X")
    rough = sorted(surfaces & SECOND_ROUGH)
    vstr = [v for v in VULGAR_STRINGS if v in jp]
    if vulg:
        by_id = any(h["by"] == "id" for h in vulg)
        sig.append("JMdict vulg/X on %s" % vulg[0]["surface"])
        return "vulgar", "jmdict-vulg", 0.9 if by_id else 0.75, sig
    if rough:
        sig.append("rough second person %s" % rough[0])
        return "vulgar", "rough-address", 0.75, sig
    if vstr:
        sig.append("vulgar lexeme %s" % vstr[0])
        return "vulgar", "vulgar-lexeme", 0.75, sig

    # ---- 4. dialect
    # アホ carries JMdict `ksb` but is a nationwide insult, not a regional variety: it belongs
    # to a content flag, never to `dialect`.
    dtag = [h for h in jhits if h["decisive"] and (set(h["tags"]) & DIALECT_TAGS)
            and h["surface"] not in ("アホ", "あほ", "あほう", "アホウ", "阿呆")]
    dm = DIALECT_RE.search(jp)
    dstr = [dm.group(1)] if dm else []
    dfin = DIALECT_FINAL_RE.search(jp)
    kansai_copula = any(t.p4 == "助動詞-ヤ" for t in toks)
    if dtag:
        sig.append("JMdict %s on %s" % ("/".join(sorted(set(dtag[0]["tags"]) & DIALECT_TAGS)),
                                        dtag[0]["surface"]))
        return "dialect", "jmdict-dialect", 0.8, sig
    if dfin or kansai_copula or dstr:
        w = dfin.group(1) if dfin else ("copula や" if kansai_copula else dstr[0])
        sig.append("dialect marker %s" % w)
        return "dialect", "dialect-marker", 0.6, sig

    # ---- 5. slang
    sl = tagged("sl")
    sslang = sorted(surfaces & SLANG_SURFACES)
    if sl:
        sig.append("JMdict sl on %s" % sl[0]["surface"])
        return "slang", "jmdict-slang", 0.75, sig
    if sslang:
        sig.append("slang lexeme %s" % sslang[0])
        return "slang", "slang-lexeme", 0.65, sig

    # ---- 6. formal (keigo)
    # であります is polite, not the written copula (see below); ~なさい is the instructional
    # imperative of なさる, NOT business keigo: 145 rows (立ちなさい / 爪を噛むのはよしなさい)
    # came out `formal` on the first run. It only counts as keigo with a ます behind it.
    polite_anywhere0 = any(t.p4 in ("助動詞-マス", "助動詞-デス") and t.s not in ("っす", "ッス")
                           for t in toks)
    nasai_directive = ("為さる" in norms or "なさる" in norms) and not polite_anywhere0
    hon = sorted(n for n in (norms & HON_STRICT)
                 if not (nasai_directive and n in ("為さる", "なさる")))
    hum = sorted(norms & HUMBLE)
    gozaru = bool([t.s for t in toks if t.norm in GOZARU]) and \
        not any(g in jp for g in FIXED_GOZAIMASU)
    ohon = False
    for i in range(len(toks) - 3):
        if toks[i].p0 == "接頭辞" and toks[i].s in ("お", "ご", "御") and toks[i + 1].p0 == "名詞" \
                and toks[i + 2].s == "に" and toks[i + 3].norm in ("成る", "なる") \
                and (tok is None or is_verb_stem(toks[i + 1].s, tok, MODE)):
            ohon = True
    orimasu = any(toks[i].norm == "おる" and i + 1 < len(toks) and toks[i + 1].p4 == "助動詞-マス"
                  for i in range(len(toks) - 1))
    # であります is polite, not the written copula: the negative lookahead keeps
    # 「よい年でありますように」 out of `formal`.
    dearu = re.search(r"であ(る|っ|れ)|であり(?!ま)", jp) is not None
    polite_anywhere = any(t.p4 in ("助動詞-マス", "助動詞-デス") and t.s not in ("っす", "ッス")
                          for t in toks)
    any_polite = any(u["polite"] for u in uinfo)
    if hon or hum or gozaru or ohon or orimasu:
        what = (hon or hum or (["ございます"] if gozaru else []) or
                (["お/ご~になる"] if ohon else []) or ["~ております"])[0]
        sig.append("keigo predicate %s" % what)
        if hon:
            sig.append("honorific")
        if hum or orimasu:
            sig.append("humble")
        return "formal", "keigo", 0.9 if any_polite else 0.75, sig
    if dearu and not polite_anywhere:
        sig.append("written copula である")
        return "formal", "written-copula", 0.7, sig

    # ---- 7. polite (です/ます on the FINAL BUNSETSU of a unit)
    polite_units = [u for u in uinfo if u["polite"]]
    plain_final = [u for u in uinfo if u["plain"]]
    if polite_units:
        sig.append("polite auxiliary %s on the final bunsetsu (%s)"
                   % (polite_units[-1]["polite"], "".join(polite_units[-1]["chain"])))
        return "polite", "polite-predicate", 0.95, sig
    # です/ます present but the sentence does not END on a predicate (〜ますように, 〜ますから…)
    if polite_anywhere and not plain_final:
        sig.append("polite auxiliary present, sentence does not end on a predicate")
        return "polite", "polite-nonfinal", 0.8, sig
    if any(t.norm in ("下さる", "くださる") and t.p5 and "命令形" in t.p5 for t in toks):
        sig.append("polite request ~ください")
        return "polite", "polite-request", 0.85, sig
    if nasai_directive:
        sig.append("instructional imperative ~なさい (なさる, no ます)")
        return "polite", "polite-request-nasai", 0.6, sig
    pset = [p for p in POLITE_SET_PHRASES if p in jp]
    if pset:
        sig.append("polite set phrase %s" % pset[0])
        return "polite", "polite-set-phrase", 0.8, sig

    # ---- 8. casual (a plain predicate PLUS a marker of informal speech)
    # 終助詞 are scanned over the WHOLE token stream, not only the last bunsetsu: a right-
    # dislocated sentence puts them mid-string (「アイス買ってきてよ、カップ系のやつ。」). The
    # last-bunsetsu rule governs politeness (です/ます vs plain), not these.
    hard, soft = [], []
    for t in toks:
        if t.p0 == "助詞" and t.p1 == "終助詞":
            if t.s in HARD_FINALS:
                hard.append(t.s)
            elif t.s in SOFT_FINALS:
                soft.append(t.s)
    contr = sorted({t.norm for t in toks if t.p0 == "助動詞" and t.norm in CONTRACTION_AUX})
    cstr = [c for c in CONTRACTION_STRINGS if c in jp]
    # んだ only: 〜のだ is the plain written explanatory and 〜なので puts の before the 連用形
    # で of だ — both were read as casual on the first run.
    nda = any(toks[i].p1 == "準体助詞" and toks[i].s == "ん"
              and toks[i + 1].p4 == "助動詞-ダ" and toks[i + 1].s.startswith("だ")
              for i in range(len(toks) - 1))
    jya = any(t.p0 == "助動詞" and t.s.startswith("じゃ") for t in toks)
    tte = any(t.s == "って" and t.p0 == "助詞" for t in toks)
    n_final = any(t.p4 == "助動詞-ヌ" and t.p5 and "撥音便" in t.p5 for t in toks)
    sec = sorted(surfaces & SECOND_CASUAL)
    # JMdict `col`/`fam` on a NOUN or a common verb is not sentence register (やる 61 rows,
    # みたい 27, パパ, お巡りさん…). Only casual ADDRESS forms count: あいつ / こいつ / お前.
    colfam = [h["surface"] for h in jhits
              if h["decisive"] and h["pos"] == "代名詞" and ("col" in h["tags"])]
    cset = [c for c in CASUAL_SET_PHRASES if c in jp]
    cset += [a for a, guard in CASUAL_GREETING_GUARDED if a in jp and guard not in jp]
    imper = any(u["imperative"] for u in uinfo)

    hard_ev = []
    if hard:
        hard_ev.append("sentence-final %s" % "/".join(sorted(set(hard))))
    if contr:
        hard_ev.append("contraction ~%s" % "/".join(contr))
    if cstr:
        hard_ev.append("contraction %s" % cstr[0])
    if nda:
        hard_ev.append("explanatory んだ")
    if jya:
        hard_ev.append("contracted copula じゃ")
    if tte:
        hard_ev.append("colloquial quotative って")
    if n_final:
        hard_ev.append("colloquial negative ~ん")
    if sec:
        hard_ev.append("casual second person %s" % sec[0])
    if cset:
        hard_ev.append("casual set phrase %s" % cset[0])
    if imper:
        hard_ev.append("bare imperative %s" % next((u["head"].s for u in uinfo if u["imperative"]), "?"))
    if colfam:
        hard_ev.append("JMdict col/fam on %s" % colfam[0])

    if hard_ev:
        sig += hard_ev
        return "casual", "casual-marker", 0.85, sig
    if soft:
        sig.append("soft sentence-final %s" % "/".join(sorted(set(soft))))
        return "casual", "soft-final", 0.7, sig

    if gram_val == "casual":
        sig.append("tagged grammar point is casual")
        return "casual", "grammar-register", 0.6, sig

    # ---- 9. neutral: a plain predicate and no marker at all
    plain_units = [u for u in uinfo if u["plain"]]
    if plain_units:
        u = plain_units[-1]
        sig.append("plain predicate %s on the final bunsetsu (%s)"
                   % (u["head"].s, "".join(u["chain"])))
        return "neutral", "plain-predicate", 0.8, sig

    return None, "no-signal", 0.0, sig


# ---------------------------------------------------------------- main


def main():
    ap = argparse.ArgumentParser()
    import tempfile
    ap.add_argument("--jmdict-cache", default=os.path.join(
        tempfile.gettempdir(), "yomineko_jmdict_misc.json"))
    ap.add_argument("--root", default=REPO,
                    help="tree to derive FROM (corpus/sentences, corpus/grammar, "
                         "research/derived/n3_mined) and write the table into")
    ap.add_argument("--out", default=None, help="write the table here instead of <root>/" +
                    "research/derived/repairs/sentence_register.json")
    ap.add_argument("--skip-w13", action="store_true",
                    help="derive the bank only; the W13 rows need research/derived/n3_mined, which "
                         "a fixture tree need not carry")
    ap.add_argument("--quiet", action="store_true")
    args = ap.parse_args()
    set_root(args.root)
    out_path = args.out or OUT

    if not args.quiet:
        print("loading JMdict misc map ...", flush=True)
    jm = build_jmdict_map(args.jmdict_cache)
    gram_reg = load_grammar_registers()
    tok = dictionary.Dictionary(dict="full").create()
    MODE = tokenizer.Tokenizer.SplitMode.C

    rows_in = []
    bank = json.load(open(BANK, encoding="utf-8"))
    for s in bank:
        vids = []
        for t in s.get("tokens") or []:
            v = t.get("vocab")
            if v and v.startswith("vocab:"):
                vids.append(v.split(":", 1)[1])
        rows_in.append({"key": s["slug"], "set": "bank", "jp": s["jp"], "level": s.get("level"),
                        "grammar": list(s.get("grammar") or []), "vocab_ids": sorted(set(vids)),
                        "authored": None,
                        "source": (s.get("provenance", {}).get("jp_source") or "?").split(":")[0]})
    acc, gen = [], []
    if not args.skip_w13:
        acc = json.load(open(ACCEPTED, encoding="utf-8"))["rows"]
        gen = json.load(open(GENERATED, encoding="utf-8"))["rows"]
    for r in acc:
        tg = r.get("targets") or []
        rows_in.append({"key": "tatoeba-%s" % r["tatoeba_id"], "set": "w13", "jp": r["jp"],
                        "level": "n3", "grammar": [t for t in tg if t.startswith("gram:")],
                        "vocab_ids": [t.split(":", 1)[1] for t in tg if t.startswith("vocab:")],
                        "authored": r.get("register"), "source": "tatoeba"})
    for r in gen:
        tg = r.get("targets") or []
        key = "gen-" + hashlib.sha1(r["jp"].encode("utf-8")).hexdigest()[:12]
        rows_in.append({"key": key, "set": "w13", "jp": r["jp"], "level": "n3",
                        "grammar": [t for t in tg if t.startswith("gram:")],
                        "vocab_ids": [t.split(":", 1)[1] for t in tg if t.startswith("vocab:")],
                        "authored": r.get("register"), "source": "ai-generated"})
    if not args.quiet:
        print("rows: %d (bank %d / w13 %d)" % (len(rows_in), len(bank), len(acc) + len(gen)),
              flush=True)

    out_rows, residue, conflicts = [], [], []
    for n, r in enumerate(rows_in):
        if n % 2000 == 0 and not args.quiet:
            print("  %d ..." % n, flush=True)
        jp = r["jp"]
        toks = [Tok(m) for m in tok.tokenize(jp, MODE)]
        uinfo = [analyse_unit(u) for u in split_units(toks)]
        jhits = jmdict_tags(r["vocab_ids"], toks, jm)
        gram_val, gram_raw = grammar_signal(r["grammar"], gram_reg)
        reg, rule, conf, sig = decide(jp, toks, uinfo, jhits, gram_val, tok, MODE)

        cfl = []
        pol = sum(1 for u in uinfo if u["polite"])
        pla = sum(1 for u in uinfo if u["plain"])
        if pol and pla:
            cfl.append({"kind": "mixed-predicate",
                        "detail": "%d polite / %d plain sentence units" % (pol, pla)})
        if gram_val and reg and gram_val != reg and rule != "grammar-register":
            cfl.append({"kind": "grammar-vs-predicate", "grammar": gram_val,
                        "points": gram_raw})
        norm_authored = W13_MAP.get(r["authored"]) if r["authored"] else None
        if norm_authored and reg and norm_authored != reg:
            cfl.append({"kind": "w13-authored-vs-derived", "authored": r["authored"],
                        "normalized": norm_authored})
        if gram_raw:
            sig.append("grammar register %s" % "; ".join(gram_raw))

        row = {"key": r["key"], "set": r["set"], "level": r["level"], "jp": jp,
               "register": reg, "rule": rule, "signals": sig, "confidence": round(conf, 2),
               "conflicts": cfl,
               "authored_w13": r["authored"], "authored_normalized": norm_authored,
               "needs_review": bool(reg is None or conf < 0.8 or cfl)}
        if reg is None:
            residue.append({"key": r["key"], "set": r["set"], "level": r["level"], "jp": jp,
                            "reason": "no predicate on the final bunsetsu and no lexical or "
                                      "grammatical signal"})
        out_rows.append(row)
        for c in cfl:
            conflicts.append(dict(c, key=r["key"], jp=jp, derived=reg, rule=rule))

    first = ({x["slug"]: x["new"] for x in json.load(open(FIRST, encoding="utf-8"))}
             if os.path.exists(FIRST) else {})
    same = diff = 0
    disagreements = []
    for row in out_rows:
        if row["set"] != "bank":
            continue
        f = first.get(row["key"])
        if f is None:
            continue
        if f == row["register"]:
            same += 1
        else:
            diff += 1
            disagreements.append({"key": row["key"], "jp": row["jp"], "first_attempt": f,
                                  "derived": row["register"], "rule": row["rule"],
                                  "signals": row["signals"][:2]})

    payload = {
        "unit": "W31",
        "phase": "derivation (A8 sentence register)",
        "table": "sentence register — the value and the rule that decided it, per sentence",
        "what_this_is": (
            "The exact-match table behind sentence.register / sentence.register_rule. `rows` with "
            "set == 'bank' address corpus/sentences/bank.json by slug and are APPLIED by "
            "scripts/apply_sentence_register.py; `rows` with set == 'w13' address sentences that "
            "are not in the bank yet (research/derived/n3_mined) and are DEFERRED to the W13 "
            "ingest, which reads this table for the value rather than re-deriving one. Regenerate "
            "with scripts/derive_sentence_register_v2.py; "
            "scripts/validate/validate_sentence_register.py re-derives on every gate run and fails "
            "on any stored value this table would no longer produce."),
        "applied_by": "scripts/apply_sentence_register.py",
        "generated_at": datetime.datetime.now().isoformat(timespec="seconds"),
        "generator": "scripts-equivalent derivation, SudachiPy dict=full split mode C",
        "sources": {"bank": "corpus/sentences/bank.json",
                    "w13_accepted": "research/derived/n3_mined/accepted.json",
                    "w13_generated": "research/derived/n3_mined/generated.json",
                    "jmdict": "research/datasets/jmdict/jmdict-eng-3.6.2+20260608153333.json.zip",
                    "grammar_registers": "corpus/grammar/*.json"},
        "value_set": list(D7),
        "precedence": list(PRECEDENCE),
        "counts": {"rows": len(out_rows), "bank": sum(1 for r in out_rows if r["set"] == "bank"),
                   "w13": sum(1 for r in out_rows if r["set"] == "w13"),
                   "residue": len(residue), "conflicts": len(conflicts)},
        "first_attempt_comparison": {
            "table": "research/derived/pending/sentence_register.json",
            "compared": same + diff, "agree": same, "disagree": diff,
            "agreement_rate": round(same / max(1, same + diff), 4),
            "disagreements": disagreements},
        "rows": out_rows,
        "residue": residue,
        "conflicts": conflicts,
    }
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as fh:
        json.dump(payload, fh, ensure_ascii=False, indent=1)
        fh.write("\n")
    print("wrote", out_path)
    if args.quiet:
        return

    from collections import Counter
    print("register:", Counter(r["register"] for r in out_rows).most_common())
    print("rule:", Counter(r["rule"] for r in out_rows).most_common())
    print("residue:", len(residue), " conflicts:", Counter(c["kind"] for c in conflicts).most_common())
    print("first-attempt agreement: %d/%d = %.2f%%" % (same, same + diff, 100 * same / max(1, same + diff)))


if __name__ == "__main__":
    main()
