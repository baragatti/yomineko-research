#!/usr/bin/env python3
"""Deterministic Japanese conjugation engine (Layer A — rule-based, no AI).

Generates the standard conjugation set for verbs (godan/ichidan/する/来る) and adjectives (い/な) from a
dictionary form + class. Operates on the kana reading (phonetic truth) and mirrors the same suffix
transformation onto the kanji headword (their okurigana tails coincide), so both `surface` and `kana` are
produced. Form keys are language-neutral enums. Used to build the verb-conjugation exercise bank.
"""
from __future__ import annotations

import jaconv

# godan: final-kana -> (a-stem, i-stem, e-stem, o-stem, te, ta)
GODAN = {
    "う": ("わ", "い", "え", "お", "って", "った"),
    "く": ("か", "き", "け", "こ", "いて", "いた"),
    "ぐ": ("が", "ぎ", "げ", "ご", "いで", "いだ"),
    "す": ("さ", "し", "せ", "そ", "して", "した"),
    "つ": ("た", "ち", "て", "と", "って", "った"),
    "ぬ": ("な", "に", "ね", "の", "んで", "んだ"),
    "ぶ": ("ば", "び", "べ", "ぼ", "んで", "んだ"),
    "む": ("ま", "み", "め", "も", "んで", "んだ"),
    "る": ("ら", "り", "れ", "ろ", "って", "った"),
}
# the conjugation forms we emit, in display order
VERB_FORMS = [
    "dictionary", "masu", "masu_negative", "masu_past", "masu_past_negative", "te", "past",
    "negative", "past_negative", "negative_te", "potential", "passive", "causative",
    "causative_passive", "volitional", "volitional_polite", "imperative", "conditional_ba",
    "conditional_tara",
]
ADJ_FORMS = [
    "dictionary", "negative", "past", "past_negative", "te", "adverbial", "conditional_ba",
    "polite", "polite_negative", "polite_past", "attributive",
]


def _romaji(kana: str) -> str:
    return jaconv.kana2alphabet(kana).replace("xtsu", "")


def _pair(surface: str, kana: str, strip: int, add: str) -> dict:
    s = surface[:-strip] + add if strip else surface + add
    k = kana[:-strip] + add if strip else kana + add
    return {"surface": s, "kana": k, "romaji": _romaji(k)}


def conjugate_verb(surface: str, kana: str, vclass: str) -> dict | None:
    """Return {form_key: {surface, kana, romaji}} or None if unsupported."""
    f: dict[str, dict] = {}
    if vclass == "godan":
        end = kana[-1]
        if end not in GODAN:
            return None
        a, i, e, o, te, ta = GODAN[end]
        if kana.endswith("いく") or kana.endswith("行く"):  # 行く euphonic exception
            te, ta = "って", "った"
        f["dictionary"] = _pair(surface, kana, 0, "")
        f["masu"] = _pair(surface, kana, 1, i + "ます")
        f["masu_negative"] = _pair(surface, kana, 1, i + "ません")
        f["masu_past"] = _pair(surface, kana, 1, i + "ました")
        f["masu_past_negative"] = _pair(surface, kana, 1, i + "ませんでした")
        f["te"] = _pair(surface, kana, 1, te)
        f["past"] = _pair(surface, kana, 1, ta)
        f["negative"] = _pair(surface, kana, 1, a + "ない")
        f["past_negative"] = _pair(surface, kana, 1, a + "なかった")
        f["negative_te"] = _pair(surface, kana, 1, a + "なくて")
        f["potential"] = _pair(surface, kana, 1, e + "る")
        f["passive"] = _pair(surface, kana, 1, a + "れる")
        f["causative"] = _pair(surface, kana, 1, a + "せる")
        f["causative_passive"] = _pair(surface, kana, 1, a + "せられる")
        f["volitional"] = _pair(surface, kana, 1, o + "う")
        f["volitional_polite"] = _pair(surface, kana, 1, i + "ましょう")
        f["imperative"] = _pair(surface, kana, 1, e)
        f["conditional_ba"] = _pair(surface, kana, 1, e + "ば")
        f["conditional_tara"] = _pair(surface, kana, 1, ta + "ら")
        return f
    if vclass == "ichidan":
        if not kana.endswith("る"):
            return None
        f["dictionary"] = _pair(surface, kana, 0, "")
        f["masu"] = _pair(surface, kana, 1, "ます")
        f["masu_negative"] = _pair(surface, kana, 1, "ません")
        f["masu_past"] = _pair(surface, kana, 1, "ました")
        f["masu_past_negative"] = _pair(surface, kana, 1, "ませんでした")
        f["te"] = _pair(surface, kana, 1, "て")
        f["past"] = _pair(surface, kana, 1, "た")
        f["negative"] = _pair(surface, kana, 1, "ない")
        f["past_negative"] = _pair(surface, kana, 1, "なかった")
        f["negative_te"] = _pair(surface, kana, 1, "なくて")
        f["potential"] = _pair(surface, kana, 1, "られる")
        f["passive"] = _pair(surface, kana, 1, "られる")
        f["causative"] = _pair(surface, kana, 1, "させる")
        f["causative_passive"] = _pair(surface, kana, 1, "させられる")
        f["volitional"] = _pair(surface, kana, 1, "よう")
        f["volitional_polite"] = _pair(surface, kana, 1, "ましょう")
        f["imperative"] = _pair(surface, kana, 1, "ろ")
        f["conditional_ba"] = _pair(surface, kana, 1, "れば")
        f["conditional_tara"] = _pair(surface, kana, 1, "たら")
        return f
    if vclass == "suru_irregular":
        # operate on the trailing する; noun/prefix part is preserved
        if not kana.endswith("する"):
            return None
        suru = {
            "dictionary": "する", "masu": "します", "masu_negative": "しません", "masu_past": "しました",
            "masu_past_negative": "しませんでした", "te": "して", "past": "した", "negative": "しない",
            "past_negative": "しなかった", "negative_te": "しなくて", "potential": "できる",
            "passive": "される", "causative": "させる", "causative_passive": "させられる",
            "volitional": "しよう", "volitional_polite": "しましょう", "imperative": "しろ",
            "conditional_ba": "すれば", "conditional_tara": "したら",
        }
        for k, suf in suru.items():
            f[k] = _pair(surface, kana, 2, suf)
        return f
    if vclass == "kuru_irregular":
        kana_forms = {
            "dictionary": "くる", "masu": "きます", "masu_negative": "きません", "masu_past": "きました",
            "masu_past_negative": "きませんでした", "te": "きて", "past": "きた", "negative": "こない",
            "past_negative": "こなかった", "negative_te": "こなくて", "potential": "こられる",
            "passive": "こられる", "causative": "こさせる", "causative_passive": "こさせられる",
            "volitional": "こよう", "volitional_polite": "きましょう", "imperative": "こい",
            "conditional_ba": "くれば", "conditional_tara": "きたら",
        }
        kanji = surface.startswith("来")
        for k, kf in kana_forms.items():
            surf = ("来" + kf[1:]) if kanji else kf
            f[k] = {"surface": surf, "kana": kf, "romaji": _romaji(kf)}
        return f
    return None


def conjugate_adjective(surface: str, kana: str, aclass: str) -> dict | None:
    f: dict[str, dict] = {}
    if aclass == "i_adj":
        if not kana.endswith("い"):
            return None
        if kana in ("いい", "よい"):  # いい/良い conjugates on the irregular よ- stem
            f["dictionary"] = {"surface": surface, "kana": kana, "romaji": _romaji(kana)}
            for key, suf in [("negative", "よくない"), ("past", "よかった"),
                             ("past_negative", "よくなかった"), ("te", "よくて"), ("adverbial", "よく"),
                             ("conditional_ba", "よければ"), ("polite", "いいです"),
                             ("polite_negative", "よくないです"), ("polite_past", "よかったです"),
                             ("attributive", "いい")]:
                f[key] = {"surface": suf, "kana": suf, "romaji": _romaji(suf)}
            return f
        f["dictionary"] = _pair(surface, kana, 0, "")
        f["negative"] = _pair(surface, kana, 1, "くない")
        f["past"] = _pair(surface, kana, 1, "かった")
        f["past_negative"] = _pair(surface, kana, 1, "くなかった")
        f["te"] = _pair(surface, kana, 1, "くて")
        f["adverbial"] = _pair(surface, kana, 1, "く")
        f["conditional_ba"] = _pair(surface, kana, 1, "ければ")
        f["polite"] = _pair(surface, kana, 0, "です")
        f["polite_negative"] = _pair(surface, kana, 1, "くないです")
        f["polite_past"] = _pair(surface, kana, 1, "かったです")
        f["attributive"] = _pair(surface, kana, 0, "")
        return f
    if aclass == "na_adj":
        f["dictionary"] = _pair(surface, kana, 0, "だ")
        f["negative"] = _pair(surface, kana, 0, "じゃない")
        f["past"] = _pair(surface, kana, 0, "だった")
        f["past_negative"] = _pair(surface, kana, 0, "じゃなかった")
        f["te"] = _pair(surface, kana, 0, "で")
        f["adverbial"] = _pair(surface, kana, 0, "に")
        f["conditional_ba"] = _pair(surface, kana, 0, "なら")
        f["polite"] = _pair(surface, kana, 0, "です")
        f["polite_negative"] = _pair(surface, kana, 0, "じゃないです")
        f["polite_past"] = _pair(surface, kana, 0, "でした")
        f["attributive"] = _pair(surface, kana, 0, "な")
        return f
    return None
