#!/usr/bin/env python3
"""Deterministic display-consistency gate (owner-flagged 2026-06-27: "explanation not matching the phrase").
Checks that everything SHOWN NEXT TO a phrase actually belongs to that phrase:
  1. token-concat == sentence.jp (split C)          -> the Análise breakdown matches the displayed phrase
  2. reading.tokens concat == reading.jp            -> reading-box furigana matches its passage
  3. structure_explanation (pt+en) quotes only Japanese that OCCURS in the sentence (allows dictionary-form
     citations of a conjugated verb via stem-prefix match, and 〜pattern citations)
  4. particle.explanation mentions only Japanese present in its sentence; the particle char itself is in jp
  5. token.gloss "(parte de X)" -> X must occur in the sentence
Exit 1 on hard fails (1,2). 3-5 are reported and gate once triaged (run with --gate to enforce).
Usage: validate_display_consistency.py [--gate]"""
from __future__ import annotations
import json, re, sqlite3, sys
from pathlib import Path
sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
DB = Path(__file__).resolve().parents[2] / "db" / "corpus.sqlite"

JP_RUN = re.compile(r"[ぁ-んァ-ヶー一-鿿々〆]{2,}")
WS = re.compile(r"[\s　]")
strip = lambda s: WS.sub("", s or "")


def kata2hira(s: str) -> str:
    return "".join(chr(ord(ch) - 0x60) if "ァ" <= ch <= "ヶ" else ch for ch in s)


def runs_ok(text: str, hay: str) -> list[str]:
    """JP runs in `text` that do NOT occur in `hay` (with stem/citation tolerance)."""
    bad = []
    h = kata2hira(hay)
    for run in JP_RUN.findall(text or ""):
        r = run.strip("〜～てでるた")  # pattern citations 〜ている / trailing citation endings
        if len(r) < 2:
            continue
        rh = kata2hira(r)
        if rh in h or rh[:-1] in h and len(rh) >= 3:
            continue
        # dictionary-form citation: stem (all but last kana) present, e.g. 読む cited for 読んでいる
        if len(rh) >= 2 and rh[:-1] in h:
            continue
        bad.append(run)
    return bad


def main() -> int:
    gate = "--gate" in sys.argv
    c = sqlite3.connect(DB)
    hard = 0
    soft: list[str] = []

    toks: dict = {}
    for sid, surf in c.execute("SELECT sentence_id,surface FROM token WHERE split_mode='C' ORDER BY sentence_id,id"):
        toks.setdefault(sid, []).append(surf or "")
    jp_by_id = {}
    for sid, slug, jp in c.execute("SELECT id,slug,jp FROM sentence"):
        jp_by_id[sid] = (slug, jp)
        if strip("".join(toks.get(sid, []))) != strip(jp):
            hard += 1
            print(f"  HARD tokens!=jp {slug}")

    if c.execute("SELECT name FROM sqlite_master WHERE name='reading'").fetchone():
        for slug, jp, tk in c.execute("SELECT slug,jp,tokens FROM reading"):
            if strip("".join(t.get("s", "") for t in json.loads(tk or "[]"))) != strip(jp):
                hard += 1
                print(f"  HARD reading tokens!=jp {slug}")

    # ---- structure_explanation cross-sentence contamination (HIGH-precision tier) ----
    # An explanation may legitimately cite: grammar jargon (動詞/尊敬語…), the kanji SPELLING of a kana word in
    # the phrase (たいざい→滞在), or an equivalent citation form. It must NOT cite content (kanji words) from a
    # DIFFERENT sentence. Flag when the kanji of cited runs are disjoint from the phrase's kanji AND the run
    # isn't jargon or a vocab whose kana appears in the phrase; require >=3 such runs or one >=5 chars.
    KANJI = re.compile(r"[一-鿿]")
    JARGON = re.compile(r"^(お|ご)?(形状詞|動詞|名詞|助詞|助動詞|形容動詞|形容詞|副詞|接続詞|代名詞|連体詞|感動詞"
                        r"|丁寧語?|尊敬語?|謙譲語?|美化語|疑問文|疑問詞|否定|過去|現在|未来|可能形?|受身|使役"
                        r"|命令形|意向形|条件形|辞書形|普通形|連用形|終止形|礼儀|敬語|準体助詞|終助詞|格助詞"
                        r"|接続助詞|副助詞|と言っていた|と言った)(の)?(て形|た形|形)?(で|だ)?$")
    vkana = {}
    for hw, kana in c.execute("SELECT headword,kana FROM vocab"):
        vkana.setdefault(hw, kana or "")

    def contaminated(val: str, jp: str) -> list[str]:
        jpk = set(KANJI.findall(jp))
        hira = kata2hira(jp)
        alien = []
        for r in set(JP_RUN.findall(val or "")):
            rk = set(KANJI.findall(r))
            if not rk or (rk & jpk) or JARGON.match(r):
                continue
            k = None
            for cut in range(0, min(5, len(r) - 1)):  # strip conjugation tail: 滞在している -> 滞在(する)
                k = vkana.get(r if cut == 0 else r[:-cut])
                if k:
                    break
            if k and k[:2] in hira:
                continue  # kanji spelling of a kana word that IS in the phrase
            alien.append(r)
        return sorted(alien)[:4] if (len(alien) >= 3 or any(len(r) >= 5 for r in alien)) else []

    for eid, loc, val in c.execute(
            "SELECT entity_id,locale,value FROM localized_text WHERE entity_type='sentence' "
            "AND field='structure_explanation'"):
        slug, jp = jp_by_id.get(eid, ("?", ""))
        bad = contaminated(val, jp)
        if bad:
            soft.append(f"expl[{loc}] {slug}: cites {bad} not in jp={jp[:24]}")

    psent = dict(c.execute("SELECT id,sentence_id FROM particle"))
    pchar = dict(c.execute("SELECT id,particle FROM particle"))
    seen_pchar = set()
    for eid, loc, val in c.execute(
            "SELECT entity_id,locale,value FROM localized_text WHERE entity_type='particle' AND field='explanation'"):
        sid = psent.get(eid)
        if sid is None:
            continue
        slug, jp = jp_by_id.get(sid, ("?", ""))
        if pchar.get(eid) and pchar[eid] not in jp and eid not in seen_pchar:
            seen_pchar.add(eid)
            soft.append(f"particle {slug}: particle '{pchar[eid]}' not in jp={jp[:24]}")
        bad = contaminated(val, jp)
        if bad:
            soft.append(f"particle-expl[{loc}] {slug}: cites {bad} not in jp={jp[:24]}")

    tsent = dict(c.execute("SELECT id,sentence_id FROM token"))
    PARTE = re.compile(r"\((?:parte d[eo]|part of)[^)]*?([ぁ-んァ-ヶー一-鿿々〆]{2,})")
    for eid, val in c.execute(
            "SELECT entity_id,value FROM localized_text WHERE entity_type='token' AND field='gloss' "
            "AND value LIKE '%parte d%' OR entity_type='token' AND field='gloss' AND value LIKE '%part of%'"):
        sid = tsent.get(eid)
        if sid is None:
            continue
        slug, jp = jp_by_id.get(sid, ("?", ""))
        hira = kata2hira(jp)
        for m in PARTE.finditer(val or ""):
            r = m.group(1)
            # lemma tolerance: gloss cites the citation form of a conjugated word (規則正しい for 規則正しく),
            # or the kanji spelling of a kana word (日極め for ひぎめ)
            if r in jp or r[:-1] in jp or (len(r) > 3 and r[:-2] in jp):
                continue
            k = vkana.get(r) or vkana.get(r[:-1])
            if k and kata2hira(k)[:2] in hira:
                continue
            soft.append(f"token-gloss {slug}: '(parte de {r})' not in jp={jp[:24]}")

    c.close()
    from collections import Counter
    byclass = Counter(s.split(" ")[0] for s in soft)
    print(f"\nvalidate_display_consistency: HARD={hard}  soft-mismatches={len(soft)}  by-class={dict(byclass)}")
    for s in soft[:150]:
        print("  SOFT", s)
    if len(soft) > 150:
        print(f"  ... +{len(soft)-150} more")
    return 1 if (hard or (gate and soft)) else 0


if __name__ == "__main__":
    sys.exit(main())
