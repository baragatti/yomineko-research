#!/usr/bin/env python3
"""Translation pipeline — EXTRACT step. Collects the DISTINCT source strings for a translation task and writes
batch files (for the AI workflow) + a load map (distinct value -> all rows that carry it). Translating distinct
values once and mapping back is what makes the corpus-wide en/pt passes tractable.

Tasks:
  n2n1_pt    : EN -> pt-BR.  N2/N1 kanji meanings_en + vocab_sense gloss_en (columns) -> localized_text pt-BR.
  grammar_en : pt-BR -> EN.  grammar_point {label,explanation,formation,nuance,form_meanings} + family
               {label,governing_rule} (localized_text pt-BR) -> localized_text en.
  sentence_en: pt-BR -> EN.  sentence {structure_explanation,translation_literal} + token {gloss,role,
               conjugation_note} + particle {function,explanation} (localized_text pt-BR) -> localized_text en.

Each occurrence is a localized_text target row keyed (entity_type, entity_id, field, is_list). Rows that
already have the TARGET locale are skipped (idempotent). Usage: tr_extract.py <task> [--batch 300]
"""
from __future__ import annotations
import argparse, json, sqlite3, sys
from pathlib import Path
sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
ROOT = Path(__file__).resolve().parents[2]
DB = ROOT / "db" / "corpus.sqlite"

# task -> (target_locale, [sources]); each source = (entity_type, field, is_list, kind, sql)
# kind 'col' reads a column off the entity table (value already EN); 'lt' reads localized_text pt-BR.
TASKS = {
    "n2n1_pt": ("pt-BR", [
        ("kanji", "meanings", 1, "col",
         "SELECT id, meanings_en FROM kanji WHERE level IN ('n2','n1') AND meanings_en IS NOT NULL "
         "AND meanings_en NOT IN ('[]','')"),
        ("vocab_sense", "gloss", 1, "col",
         "SELECT vs.id, vs.gloss_en FROM vocab_sense vs JOIN vocab v ON v.id=vs.vocab_id "
         "WHERE v.level IN ('n2','n1') AND vs.gloss_en IS NOT NULL AND vs.gloss_en NOT IN ('[]','')"),
    ]),
    "grammar_en": ("en", [
        ("grammar_point", f, 0, "lt", None) for f in ("label", "explanation", "formation", "nuance")
    ] + [("grammar_point", "form_meanings", 1, "lt", None),
         ("family", "label", 0, "lt", None), ("family", "governing_rule", 0, "lt", None)]),
    "sent_trans_en": ("en", [  # natural translation EN only for sentences missing the Tatoeba en column
        ("sentence", "translation", 0, "col",
         "SELECT s.id, lt.value FROM sentence s JOIN localized_text lt ON lt.entity_id=s.id "
         "WHERE lt.entity_type='sentence' AND lt.field='translation' AND lt.locale='pt-BR' "
         "AND (s.en IS NULL OR s.en='')"),
    ]),
    "sentence_en": ("en", [
        ("sentence", "structure_explanation", 0, "lt", None),
        ("sentence", "translation_literal", 0, "lt", None),
        ("token", "gloss", 0, "lt", None), ("token", "role", 0, "lt", None),
        ("token", "conjugation_note", 0, "lt", None),
        ("particle", "function", 0, "lt", None), ("particle", "explanation", 0, "lt", None),
    ]),
}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("task", choices=TASKS)
    ap.add_argument("--batch", type=int, default=300)
    args = ap.parse_args()
    target, sources = TASKS[args.task]
    con = sqlite3.connect(DB)
    has_target = {(r[0], r[1], r[2]) for r in con.execute(
        "SELECT entity_type, entity_id, field FROM localized_text WHERE locale=?", (target,))}

    distinct: dict[str, int] = {}          # source text (json) -> idx
    texts: list = []                       # idx -> python value (str or list)
    occ: dict[int, list] = {}              # idx -> [[entity_type, entity_id, field, is_list], ...]
    skipped = 0
    for et, field, is_list, kind, sql in sources:
        if kind == "col":
            rows = con.execute(sql).fetchall()
        else:
            rows = con.execute(
                "SELECT entity_id, value FROM localized_text WHERE entity_type=? AND field=? AND locale='pt-BR'",
                (et, field)).fetchall()
        for eid, raw in rows:
            if (et, eid, field) in has_target:
                skipped += 1
                continue
            if raw is None or raw == "" or raw == "[]":
                continue
            val = json.loads(raw) if is_list else raw
            if is_list and not val:
                continue
            key = json.dumps(val, ensure_ascii=False)
            if key not in distinct:
                distinct[key] = len(texts)
                texts.append(val)
            idx = distinct[key]
            occ.setdefault(idx, []).append([et, eid, field, is_list])

    outdir = ROOT / "research" / "derived" / "tr" / args.task
    outdir.mkdir(parents=True, exist_ok=True)
    for old in outdir.glob("batch_*.json"):
        old.unlink()
    items = [{"i": i, "t": texts[i]} for i in range(len(texts))]
    nb = (len(items) + args.batch - 1) // args.batch
    for b in range(nb):
        (outdir / f"batch_{b:04d}.json").write_text(
            json.dumps(items[b * args.batch:(b + 1) * args.batch], ensure_ascii=False), encoding="utf-8")
    (outdir / "_map.json").write_text(json.dumps({
        "target": target, "occ": occ, "n_distinct": len(texts),
    }, ensure_ascii=False), encoding="utf-8")
    print(f"task={args.task} target={target}: {sum(len(v) for v in occ.values())} rows, "
          f"{len(texts)} distinct -> {nb} batches (skipped already-translated={skipped})")
    con.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
