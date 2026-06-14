#!/usr/bin/env python3
"""Export the corpus layer from db/corpus.sqlite to LLM-readable JSON + Markdown.

Per the owner directive, JSON/MD under corpus/ are the CANONICAL, committed, AI-reviewable
artifacts; the SQLite DB is a regenerable working index. Re-run after every phase that
changes corpus data. Currently exports kanji + vocab (grammar/sentences/families added as
those phases land). Pretty JSON (indent=2, ensure_ascii=False), sharded by level.
"""
from __future__ import annotations

import datetime as _dt
import json
import sqlite3
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
ROOT = Path(__file__).resolve().parents[2]
DB = ROOT / "db" / "corpus.sqlite"
CORPUS = ROOT / "corpus"
LEVELS = ["n5", "n4"]


def jw(path: Path, obj) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def jloads(s):
    return json.loads(s) if s else None


def export_kanji(con: sqlite3.Connection) -> dict:
    out_counts = {}
    index_rows = []
    for lvl in LEVELS:
        records = []
        for k in con.execute(
            "SELECT id,slug,character,strokes,grade,freq_rank,unicode_cp,kanjivg_ref,kangxi_radical,"
            "meanings_pt,meanings_en,level,level_confidence,level_agreement,level_sources "
            "FROM kanji WHERE level=? ORDER BY freq_rank IS NULL, freq_rank", (lvl,)
        ):
            (kid, slug, ch, strokes, grade, freq, cp, kvg, radical, mpt, men,
             level, lconf, lagree, lsrc) = k
            readings = [
                {"reading": r[0], "type": r[1], "okurigana": r[2], "introduced_at_level": r[3]}
                for r in con.execute(
                    "SELECT reading,reading_type,okurigana,introduced_at_level FROM kanji_reading "
                    "WHERE kanji_id=? ORDER BY reading_type", (kid,))
            ]
            components = [r[0] for r in con.execute(
                "SELECT component FROM kanji_component WHERE kanji_id=?", (kid,))]
            rec = {
                "id": kid, "slug": slug, "character": ch, "level": level,
                "level_confidence": lconf, "level_agreement": lagree, "level_sources": jloads(lsrc),
                "strokes": strokes, "grade": grade, "freq_rank": freq, "unicode": cp,
                "kanjivg_ref": kvg, "kangxi_radical": radical,
                "meanings_en": jloads(men), "meanings_pt": jloads(mpt),
                "readings": readings, "components": components,
            }
            records.append(rec)
            index_rows.append((ch, level, strokes, len(readings),
                               ", ".join((jloads(men) or [])[:3])))
        jw(CORPUS / "kanji" / f"{lvl}.json", records)
        out_counts[lvl] = len(records)
    # index
    lines = ["# Corpus — Kanji (leveled)", "",
             f"_Generated {_dt.date.today().isoformat()}. Source of truth: these files (DB is regenerable)._",
             "", "| kanji | level | strokes | #readings | meanings (en, partial) |",
             "|-------|-------|--------:|----------:|------------------------|"]
    for ch, lvl, st, nr, mn in index_rows:
        lines.append(f"| {ch} | {lvl} | {st} | {nr} | {mn} |")
    (CORPUS / "kanji" / "INDEX.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    return out_counts


def export_vocab(con: sqlite3.Connection) -> dict:
    out_counts = {}
    index_rows = []
    for lvl in LEVELS:
        records = []
        for v in con.execute(
            "SELECT id,slug,headword,kana,romaji,lexeme_type,verb_class,adj_class,common,jmdict_ref,"
            "level,level_confidence,level_agreement,level_sources FROM vocab WHERE level=? "
            "ORDER BY headword", (lvl,)
        ):
            (vid, slug, hw, kana, romaji, lex, vclass, aclass, common, jref,
             level, lconf, lagree, lsrc) = v
            senses = [
                {"order": s[0], "pos": jloads(s[1]), "field": jloads(s[2]), "misc": jloads(s[3]),
                 "gloss_en": jloads(s[4]), "gloss_pt": jloads(s[5])}
                for s in con.execute(
                    "SELECT sense_order,pos,field_tags,misc_tags,gloss_en,gloss_pt FROM vocab_sense "
                    "WHERE vocab_id=? ORDER BY sense_order", (vid,))
            ]
            forms = [
                {"form": f[0], "is_kana": bool(f[1]), "is_common": bool(f[2]), "is_primary": bool(f[3])}
                for f in con.execute(
                    "SELECT form,is_kana,is_common,is_primary FROM vocab_form WHERE vocab_id=?", (vid,))
            ]
            kanji = [r[0] for r in con.execute(
                "SELECT k.character FROM vocab_kanji vk JOIN kanji k ON k.id=vk.kanji_id "
                "WHERE vk.vocab_id=? ORDER BY vk.position", (vid,))]
            rec = {
                "id": vid, "slug": slug, "headword": hw, "kana": kana, "romaji": romaji,
                "level": level, "level_confidence": lconf, "level_agreement": lagree,
                "level_sources": jloads(lsrc), "lexeme_type": lex, "verb_class": vclass,
                "adj_class": aclass, "common": bool(common), "jmdict_ref": jref,
                "forms": forms, "senses": senses, "kanji": kanji,
            }
            records.append(rec)
            first_gloss = (senses[0]["gloss_en"][:2] if senses and senses[0]["gloss_en"] else [])
            index_rows.append((hw, kana, level, ", ".join(first_gloss)))
        jw(CORPUS / "vocab" / f"{lvl}.json", records)
        out_counts[lvl] = len(records)
    lines = ["# Corpus — Vocabulary (leveled)", "",
             f"_Generated {_dt.date.today().isoformat()}. Source of truth: these files (DB is regenerable). "
             f"`gloss_pt` is filled in the Layer-B pass._", "",
             "| headword | kana | level | meaning (en, partial) |",
             "|----------|------|-------|------------------------|"]
    for hw, kana, lvl, mn in index_rows:
        lines.append(f"| {hw} | {kana} | {lvl} | {mn} |")
    (CORPUS / "vocab" / "INDEX.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    return out_counts


def write_corpus_index(kc: dict, vc: dict) -> None:
    lines = [
        "# Corpus layer (LLM-readable, canonical)", "",
        f"_Generated {_dt.date.today().isoformat()} by `scripts/export/export_corpus.py` from "
        f"`db/corpus.sqlite` (a regenerable index). **These JSON/MD files are the source of truth.**_", "",
        "| entity | files | n5 | n4 |",
        "|--------|-------|---:|---:|",
        f"| kanji | `corpus/kanji/<level>.json` + INDEX.md | {kc.get('n5',0)} | {kc.get('n4',0)} |",
        f"| vocab | `corpus/vocab/<level>.json` + INDEX.md | {vc.get('n5',0)} | {vc.get('n4',0)} |",
        "| grammar | _(P4+)_ | — | — |",
        "| sentences | _(P5+)_ | — | — |",
        "| families | _(P4+)_ | — | — |",
        "",
        "Each record carries `level_confidence`/`level_agreement`/`level_sources` (provenance) and a `source`. "
        "pt-BR meanings (`meanings_pt`/`gloss_pt`) are populated in the Layer-B pass.",
    ]
    (CORPUS / "INDEX.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    con = sqlite3.connect(DB)
    kc = export_kanji(con)
    vc = export_vocab(con)
    write_corpus_index(kc, vc)
    con.close()
    print(f"exported kanji={kc} vocab={vc} -> corpus/")
    return 0


if __name__ == "__main__":
    sys.exit(main())
