"""W31 / A8 — deterministic first-pass sentence register classifier.

Reads the committed corpus (never the SQLite index) and derives, for every sentence in
`corpus/sentences/bank.json`:

  * one primary `register` from the D7 value set
    (neutral | polite | casual | formal | vulgar | archaic | epistolary | dialect | slang),
  * a `flags[]` list of orthogonal content warnings
    (insult | sexual | violence | stereotype | medical-intimate | proper-name),
  * a confidence in 0..1 and a one-line `evidence` naming the token / tag / ending that decided it,
  * the raw signals it saw, so a later authoring pass (and a teacher) can audit the call.

Signals, all mechanical:
  1. JMdict misc / dialect tags of each token, looked up by `vocab:<jmdict id>` when the token
     carries a vocab link, otherwise by surface/lemma form.
  2. `register[]` of the grammar points the sentence is tagged with (`corpus/grammar/*.json`).
  3. Sentence-final and clause-internal morphology from the Sudachi tokens
     (です/ます vs plain vs だ/だろ/ぜ/ぞ/わ/かしら, contractions, imperatives).
  4. Honorific / humble (keigo) verbs.
  5. Second-person pronouns (お前 / てめえ / あんた / 貴様).
  6. Classical morphology (adjectival 〜し, 〜べし, 〜なり, 〜けり, 候, 〜ざる).
  7. Letter formulae (拝啓 / 敬具 / 前略 / 草々 / 取り急ぎ / 〜の候).
  8. Dialect markers (あかん / ほんま / やねん / なんぼ / 〜へんで / だべ …).
  9. `provenance.jp_source` (tatoeba | jec | ai-generated).

Outputs (nothing else is written; no exporter is run, no DB is touched):
  research/derived/register_signals.json          — full signal record per slug
  research/derived/repairs/sentence_register.json — the flat repair table (slug/field/new/…)

Usage (from the repo root):
    python scripts/derive_sentence_register.py [--jmdict-cache PATH] [--batch-size 200]

The JMdict misc map is cached: the first run parses the 117 MB
`research/datasets/jmdict/jmdict-eng-*.json.zip` and writes the cache next to it in the given
path (default: a temp file under the system temp dir), later runs reuse it.
"""

import argparse
import json
import os
import re
import sys
import tempfile
import zipfile
from collections import Counter

sys.stdout.reconfigure(encoding="utf-8")

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BANK = os.path.join(ROOT, "corpus", "sentences", "bank.json")
GRAMMAR_DIR = os.path.join(ROOT, "corpus", "grammar")
JMDICT_DIR = os.path.join(ROOT, "research", "datasets", "jmdict")
OUT_SIGNALS = os.path.join(ROOT, "research", "derived", "register_signals.json")
OUT_TABLE = os.path.join(ROOT, "research", "derived", "repairs", "sentence_register.json")

# ---------------------------------------------------------------- value set (D7)

REGISTERS = (
    "neutral", "polite", "casual", "formal",
    "vulgar", "archaic", "epistolary", "dialect", "slang",
)
FLAGS = ("insult", "sexual", "violence", "stereotype", "medical-intimate", "proper-name")

# Precedence: the first bucket that fires wins the single primary register.
PRECEDENCE = ("epistolary", "archaic", "vulgar", "dialect", "slang",
              "formal", "polite", "casual", "neutral")

# ---------------------------------------------------------------- lexical evidence

# JMdict misc tags we keep, and what each one argues for.
MISC_KEEP = {
    "vulg", "sl", "col", "arch", "hon", "hum", "pol", "derog", "X",
    "fam", "male", "fem", "chn", "poet", "rare", "obs", "dated", "joc",
    "ksb", "osb", "ktb", "kyb", "tsb", "thb", "tsug", "kyu", "rkb", "nab", "hob",
    "id", "proverb", "quote", "yoji",
}
DIALECT_TAGS = {"ksb", "osb", "ktb", "kyb", "tsb", "thb", "tsug", "kyu", "rkb", "nab", "hob"}

# Keigo. 〜てくださる / 〜ていただく are deliberately absent: they are ordinary polite-request
# grammar, not business keigo, and folding them in would recolour most polite requests.
HONORIFIC_LEMMAS = {
    "いらっしゃる", "おっしゃる", "仰る", "なさる", "召し上がる", "めしあがる",
    "ご覧", "御覧", "おいでになる", "お出でになる",
}
# Surfaces that belong to ordinary polite grammar even though their lemma or JMdict entry is
# keigo: 〜てください, 〜なさい, 〜ていただく. They never decide `formal` on their own.
KEIGO_EXEMPT_SURFACES = {"ください", "下さい", "くださっ", "くださる", "下さる", "くださいまし",
                         "なさい", "いただく", "いただき", "いただけ", "いただい", "頂く",
                         "頂き", "頂け", "いただこ"}
HUMBLE_LEMMAS = {
    "伺う", "うかがう", "申す", "申し上げる", "致す", "いたす", "存じる", "存ずる",
    "存じ上げる", "参る", "まいる", "拝見", "拝見する", "拝借", "差し上げる",
    "承る", "うけたまわる", "おる",
}
FORMAL_COPULA = {"ござる", "御座る"}
POLITE_AUX = {"ます", "です"}
# ございます inside a fixed greeting is everyday politeness, not business keigo.
FIXED_POLITE_GREETINGS = ("ありがとうござい", "おはようござい", "おめでとうござい",
                          "ごちそうさま", "いらっしゃいませ", "お世話さま")
# Set phrases that are polite with no です/ます of their own.
POLITE_SET_PHRASES = ("こんにちは", "こんばんは", "おやすみなさい", "さようなら", "すみません",
                      "ごめんなさい", "はじめまして", "いらっしゃいませ", "失礼します",
                      "失礼しました", "おかげさまで")
CASUAL_SET_PHRASES = ("おはよう。", "おはよう！", "じゃあね", "じゃーね", "またね", "バイバイ",
                      "ごめんね", "ありがとね", "やあ", "よっ")

SECOND_PERSON_CASUAL = {"お前", "おまえ", "あんた", "あんたら", "おめえ", "君たち"}
SECOND_PERSON_ROUGH = {"てめえ", "てめぇ", "てめー", "貴様", "きさま", "手前ども"}

VULGAR_SURFACES = {"くたばれ", "くたばる", "ちくしょう", "畜生", "ぶっ殺す", "くそったれ"}

INSULT_LEMMAS = {
    "馬鹿", "ばか", "バカ", "阿呆", "あほ", "アホ", "あほう", "間抜け", "まぬけ", "のろま",
    "無能", "愚か", "愚かしい", "ブス", "デブ", "ハゲ", "気違い", "キチガイ",
    "低能", "変態", "臆病者", "嘘つき", "嘘つき者", "死ね", "黙れ",
}
SEXUAL_LEMMAS = {
    "セックス", "性交", "エッチ", "裸", "ヌード", "ポルノ", "童貞", "処女",
    "売春", "性欲", "愛撫", "淫ら", "みだら", "ストリップ",
}
VIOLENCE_LEMMAS = {
    "殺す", "殺し", "殺人", "殴る", "撃つ", "銃", "拳銃", "ピストル", "刺す",
    "暴力", "戦争", "爆弾", "自殺", "虐待", "拷問", "死体", "絞め殺す", "襲う",
}
MEDICAL_INTIMATE_LEMMAS = {
    "痔", "下痢", "便秘", "嘔吐", "生理", "月経", "流産", "勃起", "陰茎",
    "睾丸", "陰部", "肛門", "膀胱", "尿", "おしっこ", "大便", "糞", "性病",
    "淋病", "梅毒", "精液", "乳房", "おっぱい", "包茎", "痴漢",
}
DEMONYMS = {
    "日本人", "アメリカ人", "中国人", "韓国人", "ドイツ人", "フランス人", "イタリア人",
    "イギリス人", "ロシア人", "インド人", "ブラジル人", "スペイン人", "外国人",
    "黒人", "白人", "ユダヤ人", "アラブ人", "アジア人", "西洋人", "東洋人",
}
GENERALIZERS = {"みんな", "皆", "みな", "全員", "すべて", "全て", "一般", "たいてい",
                "大抵", "いつも", "よく", "誰も", "みんな中"}

# Classical / literary morphology.
# Anchored to the end of a clause: 「ひたりきっていた」 contains たりき and is modern.
CLASSICAL_FINAL_RE = re.compile(
    r"(べし|べからず|けり|なりけり|ざりき|たりき|せり|ごとし|如し|まじ|候)(?:[。．、！？!?]|$)")
CLASSICAL_ANYWHERE = ("たまえ", "給え", "ぬべし", "ざるべから")
WRITTEN_COPULA = ("である", "であっ", "であり", "であります", "でありました")
CLASSICAL_WEAK_AUX = {"ぬ", "ず", "り"}
EPISTOLARY_MARKERS = ("拝啓", "敬具", "謹啓", "敬白", "前略", "草々", "拝復", "取り急ぎ",
                      "略儀", "ご清栄", "御清栄", "ご健勝", "御健勝", "お慶び申し上げ",
                      "謹んで申し上げ", "何卒", "の候")

# Dialect: distinctive whole tokens, plus endings anchored to the end of the sentence so that
# なんばい飲みましたか does not read as Kyushu 〜ばい and 見せやすい does not read as せや.
DIALECT_TOKENS = {"あかん", "おおきに", "ほんま", "せや", "なんぼ", "めんこい"}
DIALECT_FINAL_RE = re.compile(
    r"(やねん|まんねん|へんで|へんねん|だっぺ|だべ|じゃけん|ばってん|ちゃうで|どすえ|やん|"
    r"とちゃう|やで|やわ|やろ)(?:[。．！？!?…]|$)")

SLANG_SURFACES = {"やばい", "ヤバい", "マジ", "まじ", "ウケる", "ダサい", "キモい",
                  "めっちゃ", "パクる", "ドタキャン", "エモい"}

CASUAL_FINAL_PARTICLES = {"ぜ", "ぞ", "かしら", "さ", "っけ", "もん", "じゃん", "な", "わ",
                          "なあ", "なぁ", "ねえ", "ねぇ", "かい", "だい"}
SOFT_FINAL_PARTICLES = {"よ", "ね", "かな", "の"}
# Sudachi lemmatises the spoken contractions, so they are matched as auxiliary LEMMAS —
# substring matching would read 捨てる and 出る as 〜てる.
CASUAL_CONTRACTION_LEMMAS = {"てる", "でる", "ちゃう", "じゃう", "とく", "とる", "ちまう"}
CASUAL_CONTRACTION_STRINGS = ("なきゃ", "なくちゃ", "なくっちゃ")
# Bare だ / だろう are the plain declarative of expository writing, not a marker of casual
# speech, so they are NOT casual triggers; じゃ (ではの contraction) is.
PLAIN_COPULA = {"じゃ", "じゃん"}

# ---------------------------------------------------------------- JMdict misc map


CACHE_VERSION = 2


def _sense_tags(sense):
    tags = set()
    for t in sense.get("misc", []):
        if t in MISC_KEEP:
            tags.add(t)
    for t in sense.get("dialect", []) or []:
        if t in MISC_KEEP:
            tags.add(t)
    return tags


def build_jmdict_map(cache_path):
    """Misc-tag maps built from the FIRST sense only, plus a unanimity rule for form lookups.

    Why not any-sense: 行く carries a slang sense, 出る and やる carry a vulgar one, また and
    強い carry dialect senses. Unioning every sense mislabels ordinary words — a measured 2,520
    of 5,889 sentences came out "archaic" that way. A tag on sense 1 is what the word *is*.
    Form lookups additionally require unanimity: every JMdict entry spelled that way must carry
    the tag on its first sense, otherwise the homograph decides nothing.
    Any-sense tags are still recorded (`by_id_any`) as non-decisive context.
    """
    if cache_path and os.path.exists(cache_path):
        with open(cache_path, encoding="utf-8") as fh:
            cached = json.load(fh)
        if cached.get("version") == CACHE_VERSION:
            return cached
    zips = [f for f in os.listdir(JMDICT_DIR)
            if f.startswith("jmdict-eng-3") and f.endswith(".json.zip")]
    if not zips:
        raise SystemExit("JMdict zip not found under %s" % JMDICT_DIR)
    src = os.path.join(JMDICT_DIR, sorted(zips)[-1])
    zf = zipfile.ZipFile(src)
    with zf.open(zf.namelist()[0]) as fh:
        data = json.load(fh)

    by_id, by_id_any = {}, {}
    form_primary = {}   # form -> list of per-entry first-sense tag sets
    for w in data["words"]:
        senses = w.get("sense", [])
        primary = _sense_tags(senses[0]) if senses else set()
        anytags = set()
        for s in senses:
            anytags |= _sense_tags(s)
        if primary:
            by_id[str(w["id"])] = sorted(primary)
        if anytags:
            by_id_any[str(w["id"])] = sorted(anytags)
        for k in list(w.get("kanji", [])) + list(w.get("kana", [])):
            form_primary.setdefault(k["text"], []).append(primary)

    by_form = {}
    for form, sets in form_primary.items():
        unanimous = set.intersection(*sets) if sets else set()
        if unanimous:
            by_form[form] = sorted(unanimous)
    out = {"version": CACHE_VERSION, "by_id": by_id, "by_id_any": by_id_any, "by_form": by_form}
    if cache_path:
        with open(cache_path, "w", encoding="utf-8") as fh:
            json.dump(out, fh, ensure_ascii=False)
    return out


def load_grammar_registers():
    """key -> register[] for every grammar point in the corpus registry."""
    reg = {}
    for name in sorted(os.listdir(GRAMMAR_DIR)):
        if not name.endswith(".json"):
            continue
        with open(os.path.join(GRAMMAR_DIR, name), encoding="utf-8") as fh:
            items = json.load(fh)
        for it in items:
            reg[it.get("key")] = list(it.get("register") or [])
    return reg


# ---------------------------------------------------------------- per-sentence signals


def content_tokens(sent):
    """Mode-C tokens (the word-level split), punctuation and whitespace removed."""
    toks = [t for t in sent["tokens"] if t.get("split_mode") == "C"]
    if not toks:
        toks = sent["tokens"]
    return [t for t in toks if t.get("pos") not in ("punctuation", "whitespace")]


def lookup_misc(tok, jm):
    """JMdict misc tags for a token: by entry id when linked, else by form."""
    slug = tok.get("vocab")
    if slug and slug.startswith("vocab:"):
        tags = jm["by_id"].get(slug.split(":", 1)[1])
        if tags:
            return tags, "id"
    if tok.get("pos") in ("particle", "auxiliary", None):
        return [], None
    for form in (tok.get("lemma"), tok.get("surface")):
        if form and len(form) > 1:
            tags = jm["by_form"].get(form)
            if tags:
                return tags, "form"
    return [], None


def collect(sent, jm, gram_reg):
    """All raw signals for one sentence, as plain data."""
    jp = sent["jp"]
    toks = content_tokens(sent)
    sig = {
        "jmdict_misc": [], "grammar_register": [], "final": None, "polite": [],
        "keigo": [], "second_person": [], "classical": [], "epistolary": [],
        "dialect": [], "slang": [], "casual": [], "proper_name": [], "polite_noun": [],
        "source": (sent.get("provenance", {}).get("jp_source") or "?").split(":")[0],
    }

    for t in toks:
        tags, how = lookup_misc(t, jm)
        if tags:
            # A form lookup on an INFLECTED surface is not evidence: 「ござい」, 「小さ」,
            # 「おいし」 and 「もた」 all matched entries whose tag belongs to a different word.
            decisive = how == "id" or t.get("surface") == t.get("lemma")
            sig["jmdict_misc"].append({"surface": t.get("surface"), "lemma": t.get("lemma"),
                                       "tags": tags, "matched_by": how, "decisive": decisive,
                                       "pos": t.get("pos")})
        if t.get("pos_fine") == "固有名詞":
            sig["proper_name"].append(t.get("surface"))

    for key in sent.get("grammar") or []:
        r = gram_reg.get(key)
        if r:
            sig["grammar_register"].append({"grammar": key, "register": r})

    lemmas = [t.get("lemma") or "" for t in toks]
    surfaces = [t.get("surface") or "" for t in toks]

    # politeness morphology
    greeting = any(g in jp for g in FIXED_POLITE_GREETINGS)
    for t in toks:
        if t.get("pos") == "auxiliary" and (t.get("lemma") in POLITE_AUX):
            sig["polite"].append(t.get("surface"))
        elif t.get("lemma") in POLITE_AUX and t.get("surface", "").startswith(("です", "ます")):
            sig["polite"].append(t.get("surface"))
    if greeting:
        sig["polite"].append("fixed greeting 〜ございます")
    for p in POLITE_SET_PHRASES:
        if p in jp:
            sig["polite"].append("polite set phrase %s" % p)
            break
    # keigo — predicate keigo only. Kinship nouns (父/母/お宅/お母さん) carry JMdict hum/hon but
    # are ordinary vocabulary: they never make a sentence formal, so noun hits are recorded as
    # `polite_noun` and left out of the decision.
    for t in toks:
        lem = t.get("lemma")
        if (t.get("surface") or "") in KEIGO_EXEMPT_SURFACES:
            continue
        if lem in HONORIFIC_LEMMAS:
            sig["keigo"].append({"surface": t.get("surface"), "kind": "honorific"})
        elif lem in HUMBLE_LEMMAS:
            sig["keigo"].append({"surface": t.get("surface"), "kind": "humble"})
        elif lem in FORMAL_COPULA and not greeting:
            sig["keigo"].append({"surface": t.get("surface"), "kind": "formal-copula"})
    for w in WRITTEN_COPULA:
        if w in jp:
            sig["keigo"].append({"surface": w, "kind": "written-copula"})
            break
    for entry in sig["jmdict_misc"]:
        if not entry["decisive"] or (entry["surface"] or "") in KEIGO_EXEMPT_SURFACES:
            continue
        kind = "honorific" if "hon" in entry["tags"] else ("humble" if "hum" in entry["tags"] else None)
        if not kind:
            continue
        if entry["pos"] in ("verb", "auxiliary"):
            sig["keigo"].append({"surface": entry["surface"],
                                 "kind": "%s (JMdict)" % kind})
        else:
            sig.setdefault("polite_noun", []).append(entry["surface"])

    # second person
    for s in surfaces:
        if s in SECOND_PERSON_ROUGH:
            sig["second_person"].append({"surface": s, "kind": "rough"})
        elif s in SECOND_PERSON_CASUAL:
            sig["second_person"].append({"surface": s, "kind": "casual"})

    # classical morphology. The adjectival 〜し only counts on the LAST content token: 「おいし
    # そうですね」 and 「小さすぎる」 put an adjective stem mid-sentence, which is modern.
    for i, t in enumerate(toks):
        s = t.get("surface") or ""
        last = i == len(toks) - 1
        if last and t.get("pos") == "i-adjective" and s.endswith("し") and len(s) > 1:
            sig["classical"].append("sentence-final adjectival 〜し (%s)" % s)
        if s in CLASSICAL_WEAK_AUX and t.get("pos") == "auxiliary":
            sig["classical"].append("classical auxiliary %s (weak)" % s)
    m = CLASSICAL_FINAL_RE.search(jp)
    if m:
        sig["classical"].append("clause-final classical %s" % m.group(1))
    for c in CLASSICAL_ANYWHERE:
        if c in jp:
            sig["classical"].append("classical %s" % c)
    if "ざる" in jp and "ざるを得" not in jp:
        sig["classical"].append("classical ざる")
    for entry in sig["jmdict_misc"]:
        if not entry["decisive"] or entry["lemma"] in FORMAL_COPULA:
            continue
        if "arch" in entry["tags"] or "obs" in entry["tags"]:
            sig["classical"].append("JMdict arch/obs on %s" % entry["surface"])

    # letters
    for m in EPISTOLARY_MARKERS:
        if m in jp:
            sig["epistolary"].append(m)

    # dialect
    for s in surfaces:
        if s in DIALECT_TOKENS:
            sig["dialect"].append("dialect token %s" % s)
    m = DIALECT_FINAL_RE.search(jp)
    if m:
        sig["dialect"].append("sentence-final %s" % m.group(1))
    for entry in sig["jmdict_misc"]:
        if not entry["decisive"] or entry["lemma"] in INSULT_LEMMAS:
            continue  # アホ is Kansai in origin but nationwide as an insult: flag, not dialect
        d = [t for t in entry["tags"] if t in DIALECT_TAGS]
        if d:
            sig["dialect"].append("%s (JMdict %s)" % (entry["surface"], "/".join(d)))

    # slang
    for s in surfaces:
        if s in SLANG_SURFACES:
            sig["slang"].append(s)
    for entry in sig["jmdict_misc"]:
        if entry["decisive"] and "sl" in entry["tags"]:
            sig["slang"].append("%s (JMdict sl)" % entry["surface"])

    # casual morphology
    for t in toks:
        s = t.get("surface") or ""
        if t.get("pos_fine") == "終助詞" and s in CASUAL_FINAL_PARTICLES:
            sig["casual"].append("sentence-final %s" % s)
        elif t.get("pos_fine") == "終助詞" and s in SOFT_FINAL_PARTICLES:
            sig["casual"].append("sentence-final %s (soft)" % s)
        if t.get("pos") == "auxiliary" and s in PLAIN_COPULA:
            sig["casual"].append("plain copula %s" % s)
        # って must be a particle token: 散らかって / 帰ってきた contain the string but are て-forms
        if s == "って" and t.get("pos") == "particle":
            sig["casual"].append("colloquial quotative って")
        if t.get("pos") == "auxiliary" and t.get("lemma") in CASUAL_CONTRACTION_LEMMAS:
            sig["casual"].append("contraction 〜%s" % t.get("lemma"))
    for c in CASUAL_CONTRACTION_STRINGS:
        if c in jp:
            sig["casual"].append("contraction %s" % c)
    for p in CASUAL_SET_PHRASES:
        if p in jp and not any(g in jp for g in FIXED_POLITE_GREETINGS):
            sig["casual"].append("casual set phrase %s" % p)
            break
    for entry in sig["jmdict_misc"]:
        if entry["decisive"] and ("col" in entry["tags"] or "fam" in entry["tags"]):
            sig["casual"].append("%s (JMdict col/fam)" % entry["surface"])
    for sp in sig["second_person"]:
        if sp["kind"] == "casual":
            sig["casual"].append("second person %s" % sp["surface"])
    for g in sig["grammar_register"]:
        if {"casual", "colloquial"} & set(g["register"]):
            sig["casual"].append("grammar %s is %s" % (g["grammar"], "/".join(g["register"])))

    # final form label (last content token, for the record)
    if toks:
        last = toks[-1]
        sig["final"] = {"surface": last.get("surface"), "lemma": last.get("lemma"),
                        "pos": last.get("pos"), "pos_fine": last.get("pos_fine")}
    sig["lemmas"] = lemmas
    return sig


def derive_flags(sent, sig):
    """Orthogonal content warnings. Independent of the primary register."""
    jp = sent["jp"]
    lemmas = set(sig["lemmas"])
    flags, why = [], []

    tagset = Counter()
    for entry in sig["jmdict_misc"]:
        for t in entry["tags"]:
            tagset[t] += 1

    derog = [e["surface"] for e in sig["jmdict_misc"] if "derog" in e["tags"] and e["decisive"]]
    if lemmas & INSULT_LEMMAS or derog \
            or any(sp["kind"] == "rough" for sp in sig["second_person"]):
        flags.append("insult")
        hit = sorted(lemmas & INSULT_LEMMAS) or derog or \
            [sp["surface"] for sp in sig["second_person"] if sp["kind"] == "rough"]
        why.append("insult: %s" % ", ".join(hit[:3]))

    xrated = [e["surface"] for e in sig["jmdict_misc"] if "X" in e["tags"] and e["decisive"]]
    if lemmas & SEXUAL_LEMMAS or xrated:
        flags.append("sexual")
        hit = sorted(lemmas & SEXUAL_LEMMAS) or xrated
        why.append("sexual: %s" % ", ".join(hit[:3]))

    if lemmas & VIOLENCE_LEMMAS:
        flags.append("violence")
        why.append("violence: %s" % ", ".join(sorted(lemmas & VIOLENCE_LEMMAS)[:3]))

    if lemmas & MEDICAL_INTIMATE_LEMMAS:
        flags.append("medical-intimate")
        why.append("medical-intimate: %s" % ", ".join(sorted(lemmas & MEDICAL_INTIMATE_LEMMAS)[:3]))

    demonym = lemmas & DEMONYMS
    if demonym:
        topicalised = any(("%sは" % d) in jp or ("%sって" % d) in jp for d in demonym)
        generalised = bool(lemmas & GENERALIZERS)
        if topicalised or generalised:
            flags.append("stereotype")
            why.append("stereotype candidate: %s topicalised/generalised" %
                       ", ".join(sorted(demonym)[:2]))

    if sig["proper_name"]:
        flags.append("proper-name")
        why.append("proper noun: %s" % ", ".join(sig["proper_name"][:3]))

    return flags, why


def decide(sent, sig):
    """One primary register + confidence + one-line evidence."""
    strong_classical = [c for c in sig["classical"] if "weak" not in c]

    if sig["epistolary"]:
        return ("epistolary", 0.9,
                "letter formula %s" % ", ".join(sig["epistolary"][:2]))

    if strong_classical:
        conf = 0.85 if len(strong_classical) > 1 else 0.72
        return ("archaic", conf, "classical morphology: %s" % strong_classical[0])

    vulgar_hits = [e["surface"] for e in sig["jmdict_misc"]
                   if "vulg" in e["tags"] and e["decisive"]]
    rough = [sp["surface"] for sp in sig["second_person"] if sp["kind"] == "rough"]
    surface_vulgar = [v for v in VULGAR_SURFACES if v in sent["jp"]]
    if vulgar_hits or surface_vulgar:
        hit = (vulgar_hits or surface_vulgar)[0]
        by_id = any("vulg" in e["tags"] and e["matched_by"] == "id"
                    for e in sig["jmdict_misc"])
        return ("vulgar", 0.9 if by_id else 0.75, "JMdict vulg / vulgar lexeme %s" % hit)
    if rough:
        return ("vulgar", 0.7, "rough second person %s" % rough[0])

    if sig["dialect"]:
        by_tag = [d for d in sig["dialect"] if "JMdict" in d]
        return ("dialect", 0.75 if by_tag else 0.6,
                "dialect marker %s" % (by_tag or sig["dialect"])[0])

    if sig["slang"]:
        return ("slang", 0.7, "slang lexeme %s" % sig["slang"][0])

    keigo = sig["keigo"]
    polite = sig["polite"]
    if keigo:
        kinds = sorted({k["kind"].split(" ")[0] for k in keigo})
        conf = 0.85 if polite else 0.7
        return ("formal", conf, "keigo (%s): %s" % ("/".join(kinds), keigo[0]["surface"]))

    if polite:
        hit = polite[0]
        return ("polite", 0.95,
                hit if hit[0] not in "ですま" else "polite auxiliary %s" % hit)

    casual = sig["casual"]
    # "hard" = morphology in the sentence itself. A grammar point's authored register and the
    # soft finals よ/ね/の are real but weaker evidence, so they yield the lower confidence.
    hard = [c for c in casual if "(soft)" not in c and not c.startswith("grammar ")]
    if hard:
        return ("casual", 0.8, hard[0])
    if casual:
        return ("casual", 0.6, casual[0])

    # Nothing fired. Neutral is an absence-of-evidence call, so it is confident only when the
    # sentence actually ends on a canonical plain predicate.
    final = sig["final"] or {}
    plain_end = (final.get("pos") in ("verb", "auxiliary", "i-adjective", "na-adjective")
                 or (final.get("surface") or "").endswith(("だ", "た", "ない", "い", "る", "う")))
    return ("neutral", 0.7 if plain_end else 0.5,
            "plain, unmarked; ends on %s (%s)" % (final.get("surface"), final.get("pos")))


def main():
    ap = argparse.ArgumentParser()
    default_cache = os.path.join(tempfile.gettempdir(), "yomineko_jmdict_misc.json")
    ap.add_argument("--jmdict-cache", default=default_cache)
    ap.add_argument("--batch-size", type=int, default=200)
    args = ap.parse_args()

    with open(BANK, encoding="utf-8") as fh:
        bank = json.load(fh)
    jm = build_jmdict_map(args.jmdict_cache)
    gram_reg = load_grammar_registers()

    rows = []
    for sent in bank:
        sig = collect(sent, jm, gram_reg)
        register, conf, evidence = decide(sent, sig)
        flags, flag_why = derive_flags(sent, sig)
        rows.append({
            "slug": sent["slug"],
            "jp": sent["jp"],
            "level": sent.get("level"),
            "source": sig["source"],
            "register": register,
            "confidence": round(conf, 2),
            "evidence": evidence,
            "flags": flags,
            "flag_evidence": flag_why,
            "signals": {
                "jmdict_misc": sig["jmdict_misc"],
                "grammar_register": sig["grammar_register"],
                "final": sig["final"],
                "polite": sig["polite"],
                "keigo": sig["keigo"],
                "second_person": sig["second_person"],
                "classical": sig["classical"],
                "epistolary": sig["epistolary"],
                "dialect": sig["dialect"],
                "slang": sig["slang"],
                "casual": sig["casual"],
                "proper_name": sig["proper_name"],
                "polite_noun": sig.get("polite_noun", []),
            },
        })

    # Review batching: everything that is not a high-confidence neutral/polite call goes first,
    # so batch 1..N are ordered by how much a human/LLM pass is likely to change them.
    def priority(r):
        if r["register"] in ("archaic", "epistolary", "vulgar", "dialect", "slang"):
            return 0
        if r["flags"]:
            return 1
        if r["confidence"] < 0.7:
            return 2
        if r["register"] in ("formal", "casual"):
            return 3
        return 4

    rows.sort(key=lambda r: (priority(r), r["slug"]))
    for i, r in enumerate(rows):
        r["batch"] = i // args.batch_size + 1
        r["needs_review"] = bool(r["confidence"] < 0.8 or r["flags"] or
                                 r["register"] not in ("polite", "neutral"))

    signals = {r["slug"]: {k: v for k, v in r.items() if k != "slug"} for r in rows}
    with open(OUT_SIGNALS, "w", encoding="utf-8") as fh:
        json.dump(signals, fh, ensure_ascii=False, indent=1)

    table = [{
        "slug": r["slug"],
        "field": "register",
        "old": None,
        "new": r["register"],
        "flags": r["flags"],
        "confidence": r["confidence"],
        "evidence": r["evidence"],
        "needs_review": r["needs_review"],
        "batch": r["batch"],
        "why": "; ".join([r["evidence"]] + r["flag_evidence"]),
    } for r in sorted(rows, key=lambda x: x["slug"])]
    with open(OUT_TABLE, "w", encoding="utf-8") as fh:
        json.dump(table, fh, ensure_ascii=False, indent=1)

    print("sentences: %d  batches: %d (size %d)" %
          (len(rows), rows[-1]["batch"], args.batch_size))
    print("register:", Counter(r["register"] for r in rows).most_common())
    fc = Counter()
    for r in rows:
        for f in r["flags"]:
            fc[f] += 1
    print("flags:", fc.most_common())
    print("needs_review:", sum(1 for r in rows if r["needs_review"]))
    print("wrote", OUT_SIGNALS)
    print("wrote", OUT_TABLE)


if __name__ == "__main__":
    main()
