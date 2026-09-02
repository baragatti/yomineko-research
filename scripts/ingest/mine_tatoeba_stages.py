#!/usr/bin/env python3
"""Mine raw_tatoeba_sentence for the speaking path's thin stages. Spec: design/speaking_path.md section 6.

`lodging`, `past_stories` and `opinions` come out short because the 5,565-sentence bank has too few real
sentences on those themes. The fix is SELECTION, not generation (corpus spec 1.2): raw_tatoeba_sentence
already holds 248,705 human-written CC-BY sentences and raw_tatoeba_translation holds 285,215 English
pairings, both ingested and attributed. Nothing here invents Japanese.

What a candidate must satisfy:
  * carries a stage seed (the same seeds build_speaking_path.py uses);
  * is NOT already in the bank;
  * has an English translation, so the later pt-BR authoring pass has a Layer-A source to work from
    rather than translating blind;
  * is short enough to be a beginner phrase (<= MAX_LEN characters, <= MAX_KANJI kanji);
  * every kanji in it is one we already teach at N5-N3, which is a cheap stand-in for "inside the known
    set" — the raw rows are undissected, so a token-level check is not available until after ingestion.

Output: research/derived/tatoeba_mined_stages.json. This script SELECTS ONLY. Ingestion (dissection,
pt-BR authoring, validation) is downstream and deliberately separate, so a bad mine costs nothing.

Usage: mine_tatoeba_stages.py [--per-stage N]
"""
from __future__ import annotations
import argparse, json, re, sqlite3, sys
from pathlib import Path
sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
# W01: honour --db / $YOMINEKO_DB so a rebuild can target a scratch DB (scripts/dbtarget.py).
import sys as _sys, pathlib as _pl  # noqa: E402
_sys.path.append(str(next(p for p in _pl.Path(__file__).resolve().parents if p.name == "scripts")))
from dbtarget import db_target  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
DB = db_target(ROOT / "db" / "corpus.sqlite")
OUT = ROOT / "research" / "derived" / "tatoeba_mined_stages.json"
KANJI = re.compile(r"[一-鿿㐀-䶿]")
MAX_LEN, MAX_KANJI = 34, 6

STAGE_SEEDS: dict[str, tuple[str, ...]] = {
    "lodging": ("ホテル", "部屋", "泊ま", "鍵", "予約", "トイレ", "風呂", "シャワー", "荷物",
                "寝る", "寝ま", "泊まり", "宿", "フロント", "チェックイン", "布団", "枕", "毛布"),
    "past_stories": ("昨日", "初めて", "経験", "旅行", "楽しかった", "去年", "思い出", "先週",
                     "おととい", "子供の頃", "だった", "行った", "見た", "食べた", "会った"),
    "opinions": ("と思う", "と思い", "だから", "たぶん", "かもしれ", "方がいい", "はず", "理由",
                 "意見", "賛成", "反対", "そう思", "気がする", "ようだ", "でしょう"),
}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--per-stage", type=int, default=120)
    args = ap.parse_args()
    con = sqlite3.connect(DB)

    have = {jp for jp, in con.execute("SELECT jp FROM sentence")}
    teach = {ch for ch, in con.execute(
        "SELECT character FROM kanji WHERE level IN ('n5','n4','n3')")}
    eng: dict[int, str] = {}
    for jid, txt in con.execute(
            "SELECT jp_id,text FROM raw_tatoeba_translation WHERE lang='eng'"):
        eng.setdefault(jid, txt)

    rows = list(con.execute("SELECT id,text FROM raw_tatoeba_sentence"))
    print(f"scanning {len(rows)} raw Tatoeba sentences against {len(have)} already banked…")

    out: dict[str, list[dict]] = {}
    seen_text: set[str] = set()
    for stage, seeds in STAGE_SEEDS.items():
        picked: list[dict] = []
        for rid, text in rows:
            if len(picked) >= args.per_stage:
                break
            if not text or text in have or text in seen_text:
                continue
            if len(text) > MAX_LEN or rid not in eng:
                continue
            ks = [c for c in text if KANJI.match(c)]
            if len(ks) > MAX_KANJI or any(c not in teach for c in ks):
                continue
            if not any(s in text for s in seeds):
                continue
            seen_text.add(text)
            picked.append({"tatoeba_id": rid, "jp": text, "en": eng[rid], "stage": stage})
        out[stage] = picked
        print(f"  {stage:14s} {len(picked)} candidates")

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(
        {"source": "raw_tatoeba_sentence + raw_tatoeba_translation (CC-BY, see ATTRIBUTION.md)",
         "method": f"stage seeds, not already banked, has an English pairing, <= {MAX_LEN} chars, "
                   f"<= {MAX_KANJI} kanji, every kanji taught at N5-N3",
         "note": "SELECTION ONLY. Japanese is Layer A verbatim from Tatoeba; the English is Tatoeba's "
                 "own pairing and is the SOURCE for a later pt-BR authoring pass, never itself edited.",
         "candidates": out}, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"wrote {OUT.relative_to(ROOT)}: {sum(len(v) for v in out.values())} candidates")
    con.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
