#!/usr/bin/env python3
"""Layer-A ground-truth validator for the MASS registries (owner ask 2026-06-27): verify vocab / kanji /
readings / romaji / links against the authoritative facts, deterministically.

FAST tier (default; runs in validate_all):
  F1 vocab.romaji is consistent with vocab.kana (own kana->romaji, same scheme as the corpus)
  F2 vocab_kanji edges == kanji actually present in the headword (both directions)
  F3 kanji.strokes (KANJIDIC2) == kanji_stroke.total_strokes (Kanji Alive) — two INDEPENDENT sources agree
  F4 kanji_reading.example_vocab_ids all resolve to existing vocab
  F5 sentence.kana is kana-only (no kanji leaked into the reading line)
DEEP tier (--deep; slow, unzips the raw datasets — run after any ingest/restructuring):
  D1 every (headword, kana) pair exists in raw JMdict
  D2 every kanji's on/kun readings ⊆ raw KANJIDIC2 readings; stroke count matches
Exit 1 on any FAST failure (or DEEP failure when --deep). Usage: validate_groundtruth.py [--deep]"""
from __future__ import annotations
import json, re, sqlite3, sys, zipfile, tarfile, io
from pathlib import Path
sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
# W01: honour --db / $YOMINEKO_DB so a rebuild can target a scratch DB (scripts/dbtarget.py).
import sys as _sys, pathlib as _pl  # noqa: E402
_sys.path.append(str(next(p for p in _pl.Path(__file__).resolve().parents if p.name == "scripts")))
from dbtarget import db_target  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
DB = db_target(ROOT / "db" / "corpus.sqlite")
DS = ROOT / "research" / "datasets"

KANJI_RE = re.compile(r"[一-鿿々〆]")
KANA_ONLY = re.compile(r"^[ぁ-んァ-ヶーゝゞ・、。！？!?\s0-9０-９a-zA-ZＡ-Ｚａ-ｚ「」『』（）()〜～,.…]*$")

B = {"あ":"a","い":"i","う":"u","え":"e","お":"o","か":"ka","き":"ki","く":"ku","け":"ke","こ":"ko","が":"ga","ぎ":"gi","ぐ":"gu","げ":"ge","ご":"go","さ":"sa","し":"shi","す":"su","せ":"se","そ":"so","ざ":"za","じ":"ji","ず":"zu","ぜ":"ze","ぞ":"zo","た":"ta","ち":"chi","つ":"tsu","て":"te","と":"to","だ":"da","ぢ":"ji","づ":"zu","で":"de","ど":"do","な":"na","に":"ni","ぬ":"nu","ね":"ne","の":"no","は":"ha","ひ":"hi","ふ":"fu","へ":"he","ほ":"ho","ば":"ba","び":"bi","ぶ":"bu","べ":"be","ぼ":"bo","ぱ":"pa","ぴ":"pi","ぷ":"pu","ぺ":"pe","ぽ":"po","ま":"ma","み":"mi","む":"mu","め":"me","も":"mo","や":"ya","ゆ":"yu","よ":"yo","ら":"ra","り":"ri","る":"ru","れ":"re","ろ":"ro","わ":"wa","ゐ":"i","ゑ":"e","を":"o","ん":"n","ぁ":"a","ぃ":"i","ぅ":"u","ぇ":"e","ぉ":"o","ゃ":"ya","ゅ":"yu","ょ":"yo","ゔ":"vu"}
Y = {"きゃ":"kya","きゅ":"kyu","きょ":"kyo","ぎゃ":"gya","ぎゅ":"gyu","ぎょ":"gyo","しゃ":"sha","しゅ":"shu","しょ":"sho","じゃ":"ja","じゅ":"ju","じょ":"jo","ちゃ":"cha","ちゅ":"chu","ちょ":"cho","にゃ":"nya","にゅ":"nyu","にょ":"nyo","ひゃ":"hya","ひゅ":"hyu","ひょ":"hyo","びゃ":"bya","びゅ":"byu","びょ":"byo","ぴゃ":"pya","ぴゅ":"pyu","ぴょ":"pyo","みゃ":"mya","みゅ":"myu","みょ":"myo","りゃ":"rya","りゅ":"ryu","りょ":"ryo",
     "ふぁ":"fa","ふぃ":"fi","ふぇ":"fe","ふぉ":"fo","てぃ":"ti","でぃ":"di","どぅ":"du","とぅ":"tu","うぃ":"wi","うぇ":"we","うぉ":"wo","ちぇ":"che","しぇ":"she","じぇ":"je","ゔぁ":"va","ゔぃ":"vi","ゔぇ":"ve","ゔぉ":"vo","つぁ":"tsa","つぇ":"tse","つぉ":"tso","いぇ":"ye"}
k2h = lambda s: "".join(chr(ord(c) - 0x60) if "ァ" <= c <= "ヶ" else c for c in s)


def kana2romaji(kana: str) -> str:
    s = k2h(kana or "")
    out, i = "", 0
    while i < len(s):
        if s[i:i+2] in Y: out += Y[s[i:i+2]]; i += 2; continue
        c = s[i]
        if c == "っ":
            n = Y.get(s[i+1:i+3]) or B.get(s[i+1:i+2], "")
            out += n[:1] if n else "xtsu"  # solitary/final っ -> wapuro xtsu (あっ = axtsu)
            i += 1; continue
        if c == "ー": out += out[-1:] if out else ""; i += 1; continue
        out += B.get(c, c); i += 1
    return out


def main() -> int:
    deep = "--deep" in sys.argv
    c = sqlite3.connect(DB)
    fails = 0

    def fail(msg, n, ex):
        nonlocal fails
        if n: fails += n; print(f"  FAIL {msg}: {n}  e.g. {ex[:5]}")
        else: print(f"  ok   {msg}")

    # F1 romaji consistency. The corpus writes the chōonpu ー as "-" (apa-to); expand it to a doubled vowel
    # before comparing so only REAL mismatches (wrong reading) fail, not the scheme.
    def norm_ro(s: str) -> str:
        s = re.sub(r"([aeiou])-", r"\1\1", (s or "").lower())
        return re.sub(r"[^a-z]", "", s)
    bad = [(hw, ro, kana2romaji(ka)) for hw, ka, ro in c.execute(
        "SELECT headword,kana,romaji FROM vocab WHERE romaji IS NOT NULL AND romaji!=''")
        if norm_ro(ro) != norm_ro(kana2romaji(ka))]
    fail("F1 vocab.romaji matches kana", len(bad), bad)

    # F2 vocab_kanji edges vs headword content
    vk = {}
    for vid, ch in c.execute("SELECT vk.vocab_id,k.character FROM vocab_kanji vk JOIN kanji k ON k.id=vk.kanji_id"):
        vk.setdefault(vid, set()).add(ch)
    inv = {ch for (ch,) in c.execute("SELECT character FROM kanji")}
    bad = []
    for vid, hw in c.execute("SELECT id,headword FROM vocab"):
        want = {ch for ch in hw if KANJI_RE.match(ch)} & inv
        if want != vk.get(vid, set()):
            bad.append((hw, "".join(sorted(want - vk.get(vid, set()))), "".join(sorted(vk.get(vid, set()) - want))))
    fail("F2 vocab_kanji edges == headword kanji", len(bad), bad)

    # F3 stroke count: KANJIDIC2 vs Kanji Alive. Known SOURCE disagreements (both faithful to their source,
    # verified vs raw KANJIDIC 2026-06-27): 極 12/13, 離 19/18 — excluded so only NEW divergences fail.
    F3_KNOWN = {"極", "離"}
    bad = [(ch, sd, sa) for ch, sd, sa in c.execute(
        "SELECT k.character,k.strokes,ks.total_strokes FROM kanji k JOIN kanji_stroke ks ON ks.kanji_id=k.id")
        if sd is not None and sa is not None and sd != sa and ch not in F3_KNOWN]
    fail("F3 stroke count KANJIDIC==KanjiAlive", len(bad), bad)

    # F4 example_vocab_ids resolve
    vids = {r[0] for r in c.execute("SELECT id FROM vocab")}
    bad = []
    for kid, ev in c.execute("SELECT kanji_id,example_vocab_ids FROM kanji_reading WHERE example_vocab_ids IS NOT NULL"):
        miss = [v for v in (json.loads(ev) or []) if v not in vids]
        if miss: bad.append((kid, miss))
    fail("F4 kanji_reading.example_vocab_ids resolve", len(bad), bad)

    # F5 sentence.kana is kana-only
    bad = [(slug, ka[:20]) for slug, ka in c.execute("SELECT slug,kana FROM sentence WHERE kana IS NOT NULL AND kana!=''")
           if KANJI_RE.search(ka)]
    fail("F5 sentence.kana kana-only", len(bad), bad)

    if deep:
        # D1 (headword, kana) in raw JMdict
        zp = next(DS.glob("jmdict/jmdict-eng-3*.json.zip"), None)
        pairs = set()
        with zipfile.ZipFile(zp) as z, z.open(z.namelist()[0]) as f:
            d = json.load(io.TextIOWrapper(f, encoding="utf-8"))
        for w in d["words"]:
            ks = [k["text"] for k in w.get("kanji", [])]
            rs = [r["text"] for r in w.get("kana", [])]
            for kk in (ks or [""]):
                for rr in rs:
                    pairs.add((kk, rr))
                    if not kk: pairs.add((rr, rr))
        bad = [(hw, ka) for hw, ka in c.execute("SELECT headword,kana FROM vocab")
               if (hw, ka) not in pairs and (hw, k2h(ka or "")) not in pairs]
        fail("D1 (headword,kana) in raw JMdict", len(bad), bad)
        del d, pairs

        # D2 kanji readings + strokes vs raw KANJIDIC2
        tp = next(DS.glob("jmdict/kanjidic2-en-3*.json.tgz"), None)
        with tarfile.open(tp) as t:
            m = next(x for x in t.getmembers() if x.name.endswith(".json"))
            kd = json.load(io.TextIOWrapper(t.extractfile(m), encoding="utf-8"))
        raw = {}
        for ch in kd["characters"]:
            rm = ch.get("readingMeaning") or {}
            rd = set()
            for g in rm.get("groups", []):
                for r in g.get("readings", []):
                    if r["type"] in ("ja_on", "ja_kun"):
                        v = r["value"].replace("-", "")
                        rd.add(v.replace(".", ""))
                        rd.add(v.split(".", 1)[0])  # kun STEM (we store stem + okurigana separately)
            sc = (ch.get("misc") or {}).get("strokeCounts") or []
            raw[ch["literal"]] = ({k2h(x) for x in rd}, sc[0] if sc else None)
        bad = []
        for ch, kid, strokes in c.execute("SELECT character,id,strokes FROM kanji"):
            if ch not in raw: bad.append((ch, "not-in-kanjidic")); continue
            rd, sc = raw[ch]
            if strokes is not None and sc is not None and strokes != sc:
                bad.append((ch, f"strokes {strokes}!={sc}"))
            ours = {((r or "") + (ok or "")).replace(".", "").replace("-", "") for r, ok in c.execute(
                "SELECT reading,okurigana FROM kanji_reading WHERE kanji_id=? AND reading_type IN ('on','kun')",
                (kid,))} | {(r or "").replace(".", "").replace("-", "") for (r,) in c.execute(
                "SELECT reading FROM kanji_reading WHERE kanji_id=? AND reading_type IN ('on','kun')", (kid,))}
            extra = {o for o in ours if o and k2h(o) not in rd}
            if extra: bad.append((ch, f"readings not in KANJIDIC: {sorted(extra)[:3]}"))
        fail("D2 kanji readings+strokes vs raw KANJIDIC2", len(bad), bad)

    c.close()
    print(f"\nvalidate_groundtruth: {'FAIL '+str(fails) if fails else 'ALL OK'}{' (deep)' if deep else ''}")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
