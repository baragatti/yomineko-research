#!/usr/bin/env python3
"""Build a deterministic stratified sample of translated pairs for an adversarial QUALITY audit (faithfulness
of the pt-BR/en translations the deterministic checks can't judge). Writes research/derived/tr/audit/batch_*.json
as [{id, dim, src_lang, src, tgt_lang, tgt, ctx}]. Usage: tr_audit_sample.py [--per 40] [--batch 30]"""
from __future__ import annotations
import argparse, json, random, sqlite3, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "ingest"))
sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
from i18n_text import get_text  # noqa: E402
ROOT = Path(__file__).resolve().parents[2]
DB = ROOT / "db" / "corpus.sqlite"


RANDOM = False


def stratify(rows, per):
    if len(rows) <= per:
        return rows
    if RANDOM:
        return random.sample(rows, per)
    step = len(rows) / per
    return [rows[int(i * step)] for i in range(per)]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--per", type=int, default=40)
    ap.add_argument("--batch", type=int, default=30)
    ap.add_argument("--random", action="store_true")
    args = ap.parse_args()
    global RANDOM
    RANDOM = args.random
    c = sqlite3.connect(DB)
    sample = []

    # 1) N2/N1 kanji: en meanings (COLUMN) -> pt meanings (localized_text)
    rows = c.execute("SELECT id,character,meanings_en FROM kanji WHERE level IN ('n2','n1') "
                     "AND meanings_en IS NOT NULL AND meanings_en NOT IN ('[]','') ORDER BY id").fetchall()
    for kid, ch, en_raw in stratify(rows, args.per):
        en = json.loads(en_raw); pt = get_text(c, "kanji", kid, "meanings", "pt-BR")
        if en and pt:
            sample.append({"dim": "kanji_pt", "src_lang": "en", "src": en, "tgt_lang": "pt-BR", "tgt": pt, "ctx": ch})

    # 2) N2/N1 vocab sense: en gloss (COLUMN) -> pt gloss (localized_text)
    rows = c.execute("SELECT vs.id, v.headword, vs.gloss_en FROM vocab_sense vs JOIN vocab v ON v.id=vs.vocab_id "
                     "WHERE v.level IN ('n2','n1') AND vs.gloss_en IS NOT NULL AND vs.gloss_en NOT IN ('[]','') "
                     "ORDER BY vs.id").fetchall()
    for sid, hw, en_raw in stratify(rows, args.per):
        en = json.loads(en_raw); pt = get_text(c, "vocab_sense", sid, "gloss", "pt-BR")
        if en and pt:
            sample.append({"dim": "vocab_pt", "src_lang": "en", "src": en, "tgt_lang": "pt-BR", "tgt": pt, "ctx": hw})

    # 3) grammar: pt explanation -> en explanation
    rows = c.execute("SELECT id,key FROM grammar_point ORDER BY id").fetchall()
    for gid, key in stratify(rows, args.per):
        pt = get_text(c, "grammar_point", gid, "explanation"); en = get_text(c, "grammar_point", gid, "explanation", "en")
        if pt and en:
            sample.append({"dim": "grammar_en", "src_lang": "pt-BR", "src": pt, "tgt_lang": "en", "tgt": en, "ctx": key})

    # 4) sentence translation (AI-translated ones; en in localized_text) + 5) structure_explanation
    srows = c.execute("SELECT s.id,s.jp FROM sentence s JOIN localized_text l ON l.entity_type='sentence' "
                      "AND l.entity_id=s.id AND l.field='translation' AND l.locale='en' ORDER BY s.id").fetchall()
    for sid, jp in stratify(srows, args.per):
        pt = get_text(c, "sentence", sid, "translation"); en = get_text(c, "sentence", sid, "translation", "en")
        if pt and en:
            sample.append({"dim": "sent_trans", "src_lang": "pt-BR", "src": pt, "tgt_lang": "en", "tgt": en, "ctx": jp})
    arows = c.execute("SELECT id,jp FROM sentence ORDER BY id").fetchall()
    for sid, jp in stratify(arows, args.per):
        pt = get_text(c, "sentence", sid, "structure_explanation"); en = get_text(c, "sentence", sid, "structure_explanation", "en")
        if pt and en:
            sample.append({"dim": "struct_en", "src_lang": "pt-BR", "src": pt, "tgt_lang": "en", "tgt": en, "ctx": jp})
    trows = c.execute("SELECT t.id, t.surface, s.jp FROM token t JOIN sentence s ON s.id=t.sentence_id "
                      "JOIN localized_text l ON l.entity_type='token' AND l.entity_id=t.id AND l.field='gloss' "
                      "AND l.locale='pt-BR' WHERE t.split_mode='C' ORDER BY t.id").fetchall()
    for tid, surf, jp in stratify(trows, args.per):
        pt = get_text(c, "token", tid, "gloss"); en = get_text(c, "token", tid, "gloss", "en")
        if pt and en:
            sample.append({"dim": "token_en", "src_lang": "pt-BR", "src": pt, "tgt_lang": "en",
                           "tgt": en, "ctx": f"{surf} in {jp}"})

    for i, s in enumerate(sample):
        s["id"] = i
    outdir = ROOT / "research" / "derived" / "tr" / "audit"
    outdir.mkdir(parents=True, exist_ok=True)
    for old in outdir.glob("batch_*.json"):
        old.unlink()
    nb = (len(sample) + args.batch - 1) // args.batch
    for b in range(nb):
        (outdir / f"batch_{b:04d}.json").write_text(
            json.dumps(sample[b * args.batch:(b + 1) * args.batch], ensure_ascii=False), encoding="utf-8")
    print(f"audit sample: {len(sample)} pairs across {len(set(s['dim'] for s in sample))} dims -> {nb} batches")
    c.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
