#!/usr/bin/env python3
"""P6b — build the KANA registry (Layer A, deterministic) for the pré-N5 family lessons.

Generates hiragana + katakana (gojūon base, dakuten/handakuten, yōon, ん, sokuon, long mark) grouped into
FAMILIES ("Família do A/KA/SA…"), each addressable by id `kana:<script>-<row>` (the `kana-family` unlock ref).
Katakana glyphs are derived from hiragana by the +0x60 codepoint offset (exact for the standard block).
Writes DB tables `kana` + `kana_family` and corpus/kana/{hiragana,katakana,families}.json + INDEX.md.
Stroke counts are deferred (handwriting starts from static diagrams; see design/kana.md). Idempotent.
"""
from __future__ import annotations

import json
import sqlite3
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
ROOT = Path(__file__).resolve().parents[2]
DB = ROOT / "db" / "corpus.sqlite"
OUT = ROOT / "corpus" / "kana"

# row -> (PT family label suffix, [(hiragana, romaji)]). Katakana derived by +0x60.
BASE = [
    ("a", "A", [("あ", "a"), ("い", "i"), ("う", "u"), ("え", "e"), ("お", "o")]),
    ("ka", "KA", [("か", "ka"), ("き", "ki"), ("く", "ku"), ("け", "ke"), ("こ", "ko")]),
    ("sa", "SA", [("さ", "sa"), ("し", "shi"), ("す", "su"), ("せ", "se"), ("そ", "so")]),
    ("ta", "TA", [("た", "ta"), ("ち", "chi"), ("つ", "tsu"), ("て", "te"), ("と", "to")]),
    ("na", "NA", [("な", "na"), ("に", "ni"), ("ぬ", "nu"), ("ね", "ne"), ("の", "no")]),
    ("ha", "HA", [("は", "ha"), ("ひ", "hi"), ("ふ", "fu"), ("へ", "he"), ("ほ", "ho")]),
    ("ma", "MA", [("ま", "ma"), ("み", "mi"), ("む", "mu"), ("め", "me"), ("も", "mo")]),
    ("ya", "YA", [("や", "ya"), ("ゆ", "yu"), ("よ", "yo")]),
    ("ra", "RA", [("ら", "ra"), ("り", "ri"), ("る", "ru"), ("れ", "re"), ("ろ", "ro")]),
    ("wa", "WA", [("わ", "wa"), ("を", "wo")]),
    ("n", "N", [("ん", "n")]),
]
DAKUTEN = [
    ("ga", "GA", "dakuten", [("が", "ga"), ("ぎ", "gi"), ("ぐ", "gu"), ("げ", "ge"), ("ご", "go")]),
    ("za", "ZA", "dakuten", [("ざ", "za"), ("じ", "ji"), ("ず", "zu"), ("ぜ", "ze"), ("ぞ", "zo")]),
    ("da", "DA", "dakuten", [("だ", "da"), ("ぢ", "ji"), ("づ", "zu"), ("で", "de"), ("ど", "do")]),
    ("ba", "BA", "dakuten", [("ば", "ba"), ("び", "bi"), ("ぶ", "bu"), ("べ", "be"), ("ぼ", "bo")]),
    ("pa", "PA", "handakuten", [("ぱ", "pa"), ("ぴ", "pi"), ("ぷ", "pu"), ("ぺ", "pe"), ("ぽ", "po")]),
]
YOON = [
    ("kya", "KYA", [("きゃ", "kya"), ("きゅ", "kyu"), ("きょ", "kyo")]),
    ("sha", "SHA", [("しゃ", "sha"), ("しゅ", "shu"), ("しょ", "sho")]),
    ("cha", "CHA", [("ちゃ", "cha"), ("ちゅ", "chu"), ("ちょ", "cho")]),
    ("nya", "NYA", [("にゃ", "nya"), ("にゅ", "nyu"), ("にょ", "nyo")]),
    ("hya", "HYA", [("ひゃ", "hya"), ("ひゅ", "hyu"), ("ひょ", "hyo")]),
    ("mya", "MYA", [("みゃ", "mya"), ("みゅ", "myu"), ("みょ", "myo")]),
    ("rya", "RYA", [("りゃ", "rya"), ("りゅ", "ryu"), ("りょ", "ryo")]),
    ("gya", "GYA", [("ぎゃ", "gya"), ("ぎゅ", "gyu"), ("ぎょ", "gyo")]),
    ("ja", "JA", [("じゃ", "ja"), ("じゅ", "ju"), ("じょ", "jo")]),
    ("bya", "BYA", [("びゃ", "bya"), ("びゅ", "byu"), ("びょ", "byo")]),
    ("pya", "PYA", [("ぴゃ", "pya"), ("ぴゅ", "pyu"), ("ぴょ", "pyo")]),
]


def to_kata(hira: str) -> str:
    return "".join(chr(ord(c) + 0x60) if "ぁ" <= c <= "ゖ" else c for c in hira)


def build_rows():
    """Yield (script, family_row, label_pt, kana_type, [(char, romaji)]) for both scripts."""
    groups = [(r, lbl, "base", kk) for r, lbl, kk in BASE] \
        + [(r, lbl, t, kk) for r, lbl, t, kk in DAKUTEN] \
        + [(r, lbl, "yoon", kk) for r, lbl, kk in YOON]
    order = 0
    for script in ("hiragana", "katakana"):
        for row, lbl, ktype, kk in groups:
            order += 1
            members = [(c if script == "hiragana" else to_kata(c), rom) for c, rom in kk]
            yield script, row, lbl, ktype, order, members
        # script-specific specials
        if script == "hiragana":
            order += 1
            yield script, "sokuon", "っ (Sokuon)", "sokuon", order, [("っ", "(geminada)")]
        else:
            order += 1
            yield script, "sokuon", "ッ (Sokuon)", "sokuon", order, [("ッ", "(geminada)")]
            order += 1
            yield script, "chouon", "ー (Vogal longa)", "long-vowel", order, [("ー", "(alongamento)")]


def main() -> int:
    con = sqlite3.connect(DB)
    cur = con.cursor()
    cur.execute("CREATE TABLE IF NOT EXISTS kana_family (id TEXT PRIMARY KEY, script TEXT, row TEXT, "
                "label_pt TEXT, kana_type TEXT, ord INTEGER)")
    cur.execute("CREATE TABLE IF NOT EXISTS kana (id TEXT PRIMARY KEY, char TEXT, script TEXT, romaji TEXT, "
                "family_id TEXT, kana_type TEXT, ord INTEGER)")
    cur.execute("DELETE FROM kana")
    cur.execute("DELETE FROM kana_family")
    fam_json: dict[str, list] = {"hiragana": [], "katakana": []}
    kana_json: dict[str, list] = {"hiragana": [], "katakana": []}
    nk = 0
    for script, row, lbl, ktype, order, members in build_rows():
        fid = f"kana:{script}-{row}"
        label = f"Família do {lbl}" if ktype in ("base", "dakuten", "handakuten", "yoon") else lbl
        cur.execute("INSERT INTO kana_family (id, script, row, label_pt, kana_type, ord) VALUES (?,?,?,?,?,?)",
                    (fid, script, row, label, ktype, order))
        fam_members = []
        for i, (char, rom) in enumerate(members):
            kid = f"kana:{script}-{char}"
            cur.execute("INSERT OR REPLACE INTO kana (id, char, script, romaji, family_id, kana_type, ord) "
                        "VALUES (?,?,?,?,?,?,?)", (kid, char, script, rom, fid, ktype, order * 10 + i))
            fam_members.append({"id": kid, "char": char, "romaji": rom})
            kana_json[script].append({"id": kid, "char": char, "romaji": rom, "family": fid,
                                      "family_label": {"pt-BR": label}, "type": ktype})
            nk += 1
        fam_json[script].append({"id": fid, "label": {"pt-BR": label}, "row": row, "type": ktype,
                                 "order": order, "members": fam_members})
    con.commit()
    OUT.mkdir(parents=True, exist_ok=True)
    for script in ("hiragana", "katakana"):
        (OUT / f"{script}.json").write_text(json.dumps(kana_json[script], ensure_ascii=False, indent=2) + "\n",
                                            encoding="utf-8")
    (OUT / "families.json").write_text(json.dumps(fam_json, ensure_ascii=False, indent=2) + "\n",
                                       encoding="utf-8")
    nf = con.execute("SELECT count(*) FROM kana_family").fetchone()[0]
    lines = ["# Corpus — Kana registry (Layer A)", "",
             "_Gojūon families for the pré-N5 kana lessons. `kana-family` unlock refs = `kana:<script>-<row>`. "
             "Katakana derived from hiragana by codepoint offset. Stroke data deferred (design/kana.md)._", "",
             "| script | families | kana |", "|--------|---------:|-----:|"]
    for script in ("hiragana", "katakana"):
        fc = sum(1 for f in fam_json[script])
        kc = sum(1 for k in kana_json[script])
        lines.append(f"| {script} | {fc} | {kc} |")
    (OUT / "INDEX.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"build_kana: {nk} kana in {nf} families -> corpus/kana/ + DB (kana, kana_family)")
    con.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
