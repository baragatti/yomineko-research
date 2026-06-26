#!/usr/bin/env python3
"""Ground-truth field audit sampler (translation_qa.md §3.1). For a corpus field-class, build the DISTINCT
(pt, en) pairs (with an anchor for context) so an agent can judge whether the pt-BR faithfully + correctly +
naturally renders the authoritative en (dictionary gloss / source). Dedup by (pt,en) makes it tractable.
Writes research/derived/tr/gt-<key>/batch_*.json as [{id, anchor, pt, en, is_list}].
Usage: gt_audit_sample.py <key> [--batch 50]   key in CONFIG below."""
from __future__ import annotations
import argparse, json, sqlite3, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "ingest"))
sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
ROOT = Path(__file__).resolve().parents[2]
DB = ROOT / "db" / "corpus.sqlite"

# key -> (entity_type, field, is_list, en_source 'col'|'lt', en_col, anchor_sql)
#   anchor_sql: SELECT entity_id, anchor_text FROM ...  (maps entity_id -> a short context string)
CONFIG = {
    "grammar.explanation": ("grammar_point", "explanation", 0, "lt", None,
                            "SELECT id, key||'  ['||COALESCE(structure_pattern,'')||']' FROM grammar_point"),
    "grammar.nuance": ("grammar_point", "nuance", 0, "lt", None,
                       "SELECT id, key||'  ['||COALESCE(structure_pattern,'')||']' FROM grammar_point"),
    "grammar.formation": ("grammar_point", "formation", 0, "lt", None,
                          "SELECT id, key||'  ['||COALESCE(structure_pattern,'')||']' FROM grammar_point"),
    "grammar.label": ("grammar_point", "label", 0, "lt", None,
                      "SELECT id, key||'  ['||COALESCE(structure_pattern,'')||']' FROM grammar_point"),
    "kanji.meanings": ("kanji", "meanings", 1, "col", "meanings_en", "SELECT id, character FROM kanji"),
    "vocab.gloss": ("vocab_sense", "gloss", 1, "col", "gloss_en",
                    "SELECT vs.id, v.headword||' ('||COALESCE(v.kana,'')||')' FROM vocab_sense vs "
                    "JOIN vocab v ON v.id=vs.vocab_id"),
    "token.gloss": ("token", "gloss", 0, "lt", None,
                    "SELECT t.id, t.surface||'  «'||s.jp||'»' FROM token t JOIN sentence s ON s.id=t.sentence_id "
                    "WHERE t.split_mode='C'"),
    "particle.function": ("particle", "function", 0, "lt", None,
                          "SELECT p.id, p.particle||'  «'||s.jp||'»' FROM particle p JOIN sentence s ON s.id=p.sentence_id"),
}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("key", choices=CONFIG)
    ap.add_argument("--batch", type=int, default=50)
    args = ap.parse_args()
    et, field, is_list, en_src, en_col, anchor_sql = CONFIG[args.key]
    c = sqlite3.connect(DB)
    anchor = {r[0]: r[1] for r in c.execute(anchor_sql)}
    # pt from localized_text; en from column or localized_text en
    pt_rows = {(eid): v for eid, v in c.execute(
        "SELECT entity_id, value FROM localized_text WHERE entity_type=? AND field=? AND locale='pt-BR'",
        (et, field))}
    if en_src == "lt":
        en_rows = {eid: v for eid, v in c.execute(
            "SELECT entity_id, value FROM localized_text WHERE entity_type=? AND field=? AND locale='en'",
            (et, field))}
    else:
        en_rows = {r[0]: r[1] for r in c.execute(f"SELECT id, {en_col} FROM {et}")}

    seen: dict = {}
    sample = []
    for eid, pt_raw in pt_rows.items():
        en_raw = en_rows.get(eid)
        if not pt_raw or not en_raw:
            continue
        pt = json.loads(pt_raw) if (is_list and pt_raw.startswith("[")) else pt_raw
        en = json.loads(en_raw) if (is_list and str(en_raw).startswith("[")) else en_raw
        if is_list and (not pt or not en):
            continue
        dk = json.dumps([pt, en], ensure_ascii=False)
        if dk in seen:
            continue
        seen[dk] = 1
        sample.append({"id": len(sample), "anchor": anchor.get(eid, ""), "pt": pt, "en": en, "is_list": bool(is_list)})
    outdir = ROOT / "research" / "derived" / "tr" / ("gt-" + args.key.replace(".", "_"))
    outdir.mkdir(parents=True, exist_ok=True)
    for old in outdir.glob("batch_*.json"):
        old.unlink()
    nb = (len(sample) + args.batch - 1) // args.batch
    for b in range(nb):
        (outdir / f"batch_{b:04d}.json").write_text(
            json.dumps(sample[b * args.batch:(b + 1) * args.batch], ensure_ascii=False), encoding="utf-8")
    (outdir / "_sample.json").write_text(json.dumps(sample, ensure_ascii=False), encoding="utf-8")
    print(f"{args.key}: {len(pt_rows)} rows -> {len(sample)} distinct (pt,en) -> {nb} batches  dir={outdir.name}")
    c.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
