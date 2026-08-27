#!/usr/bin/env python3
"""Deterministic display-consistency gate (owner-flagged 2026-06-27: "explanation not matching the phrase").
Checks that everything SHOWN NEXT TO a phrase actually belongs to that phrase:
  1. token-concat == sentence.jp (split C)          -> the Análise breakdown matches the displayed phrase
  2. reading.tokens concat == reading.jp            -> reading-box furigana matches its passage
  3. structure_explanation (pt+en) quotes only Japanese that OCCURS in the sentence (allows dictionary-form
     citations of a conjugated verb via stem-prefix match, and 〜pattern citations)
  4. particle.explanation mentions only Japanese present in its sentence; the particle char itself is in jp
  5. token.gloss "(parte de X)" -> X must occur in the sentence

WHY 3-5 NOW GATE (review finding F16)
-------------------------------------
Checks 3-5 used to end at `return 1 if (hard or (gate and soft)) else 0`, where `gate` came only from a
--gate flag that nothing passes: validate_all.py runs this script bare, so three learner-visible rules were
printed and then discarded, inside a validator the gate table reports as [OK ]. They gate now, against the
frozen SOFT_BASELINE below: any mismatch that is not already listed fails the build, and any baseline entry
that stops matching fails too, so the list shrinks as the content is repaired and can never rot. Its 47
keys are the open triage (52 findings — a key is a sentence plus the string it wrongly cites, and four
sentences hit the same gloss on several tokens), each carrying its reason; --gate still exists and now
means "fail on the baseline as well", i.e. the state this validator is aiming at.

Usage: validate_display_consistency.py [--root PATH] [--gate]"""
from __future__ import annotations
import argparse, json, re, sqlite3, sys
from pathlib import Path
sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
REPO_ROOT = Path(__file__).resolve().parents[2]

JP_RUN = re.compile(r"[ぁ-んァ-ヶー一-鿿々〆]{2,}")
WS = re.compile(r"[\s　]")
strip = lambda s: WS.sub("", s or "")

# Open triage for checks 3-5, keyed "class|sentence-slug|cited". Every entry is a learner-visible
# explanation/gloss that quotes Japanese absent from the phrase it sits beside; each is held for the
# content pass that re-authors it. A finding NOT listed here fails the build, and an entry that stops
# matching (the text was repaired, or the sentence was re-dissected) fails too, so this list can only
# shrink. Delete the line when the string is fixed.
_TRIAGE = "open triage 2026-08-26 (F16): cross-sentence citation, queued for the content re-authoring pass"
SOFT_BASELINE: dict[str, str] = {
    "expl[en]|sent:gen-74ea68439313|要りません,要る": _TRIAGE,
    "expl[en]|sent:gen-941ec1bd04ae|無くなった": _TRIAGE,
    "expl[en]|sent:gen-e9848d9848e8|小さくする": _TRIAGE,
    "expl[en]|sent:tatoeba-119272|行く,行ってもいい,言う": _TRIAGE,
    "expl[en]|sent:tatoeba-141890|病気にかかる": _TRIAGE,
    "expl[en]|sent:tatoeba-146817|手伝わせてください": _TRIAGE,
    "expl[en]|sent:tatoeba-168902|てくれと頼む": _TRIAGE,
    "expl[en]|sent:tatoeba-172836|行かなければ,行く": _TRIAGE,
    "expl[en]|sent:tatoeba-202786|寄ってくる,寄る": _TRIAGE,
    "expl[en]|sent:tatoeba-229409|放っておく": _TRIAGE,
    "expl[en]|sent:tatoeba-74910|何をやっているのだ": _TRIAGE,
    "expl[en]|sent:tatoeba-75792|知っている": _TRIAGE,
    "expl[en]|sent:tatoeba-76355|って言うか": _TRIAGE,
    "expl[en]|sent:tatoeba-80880|気をつけて": _TRIAGE,
    "expl[en]|sent:tatoeba-83147|ぴんと来ない": _TRIAGE,
    "expl[en]|sent:tatoeba-8703703|お金をかける,に行く": _TRIAGE,
    "expl[pt-BR]|sent:gen-74ea68439313|要りません,要る": _TRIAGE,
    "expl[pt-BR]|sent:gen-941ec1bd04ae|無くなった": _TRIAGE,
    "expl[pt-BR]|sent:gen-e9848d9848e8|小さくする": _TRIAGE,
    "expl[pt-BR]|sent:gen-f10b790cf3c8|大きいトピックは,小さい主語が,述語": _TRIAGE,
    "expl[pt-BR]|sent:tatoeba-119272|行く,行ってもいい,言う": _TRIAGE,
    "expl[pt-BR]|sent:tatoeba-141890|病気にかかる": _TRIAGE,
    "expl[pt-BR]|sent:tatoeba-143418|の準体助詞": _TRIAGE,
    "expl[pt-BR]|sent:tatoeba-146817|手伝わせてください": _TRIAGE,
    "expl[pt-BR]|sent:tatoeba-168902|てくれと頼む": _TRIAGE,
    "expl[pt-BR]|sent:tatoeba-172836|行かなければ,行く": _TRIAGE,
    "expl[pt-BR]|sent:tatoeba-202786|寄ってくる,寄る": _TRIAGE,
    "expl[pt-BR]|sent:tatoeba-229409|放っておく": _TRIAGE,
    "expl[pt-BR]|sent:tatoeba-74910|何をやっているのだ": _TRIAGE,
    "expl[pt-BR]|sent:tatoeba-75792|知っている": _TRIAGE,
    "expl[pt-BR]|sent:tatoeba-76355|って言うか": _TRIAGE,
    "expl[pt-BR]|sent:tatoeba-80880|気をつけて": _TRIAGE,
    "expl[pt-BR]|sent:tatoeba-83147|ぴんと来ない": _TRIAGE,
    "expl[pt-BR]|sent:tatoeba-8703703|お金をかける,に行く": _TRIAGE,
    "particle-expl[en]|sent:tatoeba-125814|の準体助詞": _TRIAGE,
    "particle-expl[en]|sent:tatoeba-137738|の準体助詞": _TRIAGE,
    "particle-expl[en]|sent:tatoeba-202786|寄っ,寄ってくる": _TRIAGE,
    "particle-expl[pt-BR]|sent:tatoeba-125814|の準体助詞": _TRIAGE,
    "particle-expl[pt-BR]|sent:tatoeba-13513556|の準体助詞": _TRIAGE,
    "particle-expl[pt-BR]|sent:tatoeba-137738|の準体助詞": _TRIAGE,
    "particle-expl[pt-BR]|sent:tatoeba-202786|寄っ,寄ってくる": _TRIAGE,
    "particle-expl[pt-BR]|sent:tatoeba-74350|わびを入れる": _TRIAGE,
    "particle-expl[pt-BR]|sent:tatoeba-82900|病気にかかる": _TRIAGE,
    "token-gloss|sent:gen-67098aef1bd0|そうして": _TRIAGE,
    "token-gloss|sent:tatoeba-121924|猫も杓子も": _TRIAGE,
    "token-gloss|sent:tatoeba-13804129|かっこいい": _TRIAGE,
    "token-gloss|sent:tatoeba-192185|日極め": _TRIAGE,
}


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


def collect(db: Path) -> tuple[int, list[tuple[str, str, str, str]]]:
    """Returns (hard-fail count, soft findings as (class, slug, detail, context))."""
    c = sqlite3.connect(db)
    hard = 0
    soft: list[tuple[str, str, str, str]] = []

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
            soft.append((f"expl[{loc}]", slug, ",".join(bad), jp[:24]))

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
            soft.append(("particle", slug, pchar[eid], jp[:24]))
        bad = contaminated(val, jp)
        if bad:
            soft.append((f"particle-expl[{loc}]", slug, ",".join(bad), jp[:24]))

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
            soft.append(("token-gloss", slug, r, jp[:24]))

    c.close()
    return hard, soft


def describe(cls: str, slug: str, detail: str, jp: str) -> str:
    if cls == "particle":
        return f"{cls} {slug}: particle '{detail}' not in jp={jp}"
    if cls == "token-gloss":
        return f"{cls} {slug}: '(parte de {detail})' not in jp={jp}"
    return f"{cls} {slug}: cites [{detail}] not in jp={jp}"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=str(REPO_ROOT), help="tree to validate (default: repo root)")
    ap.add_argument("--gate", action="store_true", help="also fail on the baselined findings")
    args = ap.parse_args()
    hard, soft = collect(Path(args.root).resolve() / "db" / "corpus.sqlite")

    from collections import Counter
    byclass = Counter(cls for cls, _s, _d, _j in soft)
    seen = {f"{cls}|{slug}|{detail}" for cls, slug, detail, _j in soft}
    new = [t for t in soft if f"{t[0]}|{t[1]}|{t[2]}" not in SOFT_BASELINE]
    stale = sorted(k for k in SOFT_BASELINE if k not in seen)
    bad = len(soft) if args.gate else len(new)
    print(f"\nvalidate_display_consistency: HARD={hard}  soft-mismatches={len(soft)} "
          f"(baselined {len(soft)-len(new)}, NEW {len(new)}, stale-baseline {len(stale)}) "
          f"by-class={dict(byclass)}")
    for t in (soft if args.gate else new)[:15]:
        print("  FAIL", describe(*t))
    if bad > 15:
        print(f"  ... +{bad-15} more")
    for k in stale[:15]:
        print(f"  FAIL stale baseline entry (repaired — delete it): {k}")
    if len(stale) > 15:
        print(f"  ... +{len(stale)-15} more stale")
    held = [t for t in soft if f"{t[0]}|{t[1]}|{t[2]}" in SOFT_BASELINE] if not args.gate else []
    for t in held[:15]:
        print("  baselined", describe(*t))
    if len(held) > 15:
        print(f"  ... +{len(held)-15} more baselined (see SOFT_BASELINE)")
    return 1 if (hard or bad or stale) else 0


if __name__ == "__main__":
    sys.exit(main())
