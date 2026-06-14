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
            pitch = [{"reading": p[0], "accent_positions": jloads(p[1])} for p in con.execute(
                "SELECT reading,accent_positions FROM vocab_pitch WHERE vocab_id=?", (vid,))]
            rec = {
                "id": vid, "slug": slug, "headword": hw, "kana": kana, "romaji": romaji,
                "level": level, "level_confidence": lconf, "level_agreement": lagree,
                "level_sources": jloads(lsrc), "lexeme_type": lex, "verb_class": vclass,
                "adj_class": aclass, "common": bool(common), "jmdict_ref": jref,
                "pitch": pitch, "forms": forms, "senses": senses, "kanji": kanji,
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


def export_grammar(con: sqlite3.Connection) -> dict:
    out_counts = {}
    index_rows = []
    has = con.execute("SELECT COUNT(*) FROM grammar_point").fetchone()[0]
    if not has:
        return out_counts
    for lvl in LEVELS:
        records = []
        for g in con.execute(
            "SELECT id,slug,key,label_pt,structure_pattern,register,explanation_pt,formation_pt,"
            "nuance_pt,references_json,level,level_confidence,level_agreement,level_sources,needs_review "
            "FROM grammar_point WHERE level=? ORDER BY key", (lvl,)
        ):
            (gid, slug, key, label_pt, pattern, reg, expl, form, nuance, refs,
             level, lconf, lagree, lsrc, nr) = g
            rec = {
                "id": gid, "slug": slug, "key": key, "label_pt": label_pt,
                "structure_pattern": pattern, "register": reg, "level": level,
                "level_confidence": lconf, "level_agreement": lagree, "level_sources": jloads(lsrc),
                "explanation_pt": expl, "formation_pt": form, "nuance_pt": nuance,
                "refs": jloads(refs), "needs_review": bool(nr),
            }
            records.append(rec)
            index_rows.append((key, pattern or "", level, "authored" if expl else "stub"))
        jw(CORPUS / "grammar" / f"{lvl}.json", records)
        out_counts[lvl] = len(records)
    lines = ["# Corpus — Grammar points (enumerated)", "",
             f"_Generated {_dt.date.today().isoformat()}. Membership reconciled from ≥3 lists; "
             f"explanation_pt/formation_pt/nuance_pt are authored (Layer C) in P6._", "",
             "| key | pattern | level | explanation |",
             "|-----|---------|-------|-------------|"]
    for key, pat, lvl, st in index_rows:
        lines.append(f"| {key} | {pat} | {lvl} | {st} |")
    (CORPUS / "grammar" / "INDEX.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    return out_counts


def export_families(con: sqlite3.Connection) -> int:
    if not con.execute("SELECT COUNT(*) FROM family").fetchone()[0]:
        return 0
    records, index_rows = [], []
    for f in con.execute(
        "SELECT id,slug,type,label_pt,description_pt,importance_rank,governing_rule_pt,spans_levels "
        "FROM family ORDER BY importance_rank, slug"
    ):
        fid, slug, ftype, label, desc, rank, rule, spans = f
        members = []
        for m in con.execute(
            "SELECT member_type,member_id,intra_order,is_core,note_pt FROM family_member "
            "WHERE family_id=? ORDER BY intra_order", (fid,)
        ):
            mtype, mid, order, core, note = m
            if mtype == "kanji":
                ref = con.execute("SELECT character FROM kanji WHERE id=?", (mid,)).fetchone()
            elif mtype == "vocab":
                ref = con.execute("SELECT headword FROM vocab WHERE id=?", (mid,)).fetchone()
            else:
                ref = con.execute("SELECT key FROM grammar_point WHERE id=?", (mid,)).fetchone()
            members.append({"member_type": mtype, "ref": ref[0] if ref else None,
                            "id": mid, "intra_order": order, "is_core": bool(core), "note_pt": note})
        records.append({
            "id": fid, "slug": slug, "type": ftype, "label_pt": label, "description_pt": desc,
            "importance_rank": rank, "governing_rule_pt": rule, "spans_levels": jloads(spans),
            "members": members,
        })
        index_rows.append((slug, ftype, label, len(members)))
    jw(CORPUS / "families" / "families.json", records)
    lines = ["# Corpus — Families / groups", "",
             f"_Generated {_dt.date.today().isoformat()}. Structural families (conjugation/adjective classes, "
             f"counters, kanji-component). Semantic & derivational families refined later._", "",
             "| family | type | label | #members |", "|--------|------|-------|---------:|"]
    for slug, ftype, label, n in index_rows:
        lines.append(f"| {slug} | {ftype} | {label} | {n} |")
    (CORPUS / "families" / "INDEX.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    return len(records)


def export_sentences(con: sqlite3.Connection) -> int:
    if not con.execute("SELECT COUNT(*) FROM sentence").fetchone()[0]:
        return 0
    records, index_rows = [], []
    for s in con.execute("SELECT * FROM sentence ORDER BY id"):
        cols = [d[0] for d in con.execute("SELECT * FROM sentence LIMIT 1").description]
        s = dict(zip(cols, s))
        sid = s["id"]
        tokens = [dict(zip(["position", "split_mode", "surface", "lemma", "reading", "romaji",
                            "pos_coarse", "pos_fine", "role_pt", "gloss_pt", "conjugation_note_pt",
                            "vocab_id"], r))
                  for r in con.execute(
                      "SELECT position,split_mode,surface,lemma,reading,romaji,pos_coarse,pos_fine,"
                      "role_pt,gloss_pt,conjugation_note_pt,vocab_id FROM token WHERE sentence_id=? "
                      "ORDER BY split_mode, position", (sid,))]
        particles = [dict(zip(["particle", "function_pt", "explanation_pt"], r))
                     for r in con.execute(
                         "SELECT particle,function_pt,explanation_pt FROM particle WHERE sentence_id=?", (sid,))]
        grammar = [r[0] for r in con.execute(
            "SELECT g.key FROM sentence_grammar sg JOIN grammar_point g ON g.id=sg.grammar_id "
            "WHERE sg.sentence_id=?", (sid,))]
        rec = {
            "id": sid, "slug": s["slug"], "jp": s["jp"], "kana": s["kana"], "romaji": s["romaji"],
            "pt": s["pt"], "pt_literal": s["pt_literal"], "en": s["en"], "level": s["level"],
            "provenance": {"jp_source": s["jp_source"], "pt_source": s["pt_source"],
                           "pt_validated_against": s["pt_validated_against"],
                           "translation_confidence": s["translation_confidence"],
                           "tier": s["dissection_tier"], "ai_generated": bool(s["ai_generated"]),
                           "needs_review": bool(s["needs_review"])},
            "structure_explanation_pt": s["structure_explanation_pt"],
            "tags": jloads(s["tags"]), "new_items": jloads(s["new_items"]),
            "tokens": tokens, "particles": particles, "grammar": grammar,
        }
        records.append(rec)
        index_rows.append((s["slug"], s["jp"], s["pt"], s["level"]))
    jw(CORPUS / "sentences" / "bank.json", records)
    lines = ["# Corpus — Dissected sentence bank", "",
             f"_Generated {_dt.date.today().isoformat()}. Each sentence carries the full §6 dissection "
             f"(tokens A+C, per-token pt-BR gloss, particle explanations, structure paragraph) + provenance. "
             f"Lessons reference these BY ID._", "",
             "| slug | jp | pt | level |", "|------|----|----|-------|"]
    for slug, jp, pt, lvl in index_rows:
        lines.append(f"| {slug} | {jp} | {pt} | {lvl} |")
    (CORPUS / "sentences" / "INDEX.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    return len(records)


def write_corpus_index(kc: dict, vc: dict, gc: dict | None = None, fc: int = 0, sc: int = 0) -> None:
    gc = gc or {}
    lines = [
        "# Corpus layer (LLM-readable, canonical)", "",
        f"_Generated {_dt.date.today().isoformat()} by `scripts/export/export_corpus.py` from "
        f"`db/corpus.sqlite` (a regenerable index). **These JSON/MD files are the source of truth.**_", "",
        "| entity | files | n5 | n4 |",
        "|--------|-------|---:|---:|",
        f"| kanji | `corpus/kanji/<level>.json` + INDEX.md | {kc.get('n5',0)} | {kc.get('n4',0)} |",
        f"| vocab | `corpus/vocab/<level>.json` + INDEX.md | {vc.get('n5',0)} | {vc.get('n4',0)} |",
        (f"| grammar | `corpus/grammar/<level>.json` + INDEX.md | {gc.get('n5',0)} | {gc.get('n4',0)} |"
         if gc else "| grammar | _(P4+)_ | — | — |"),
        (f"| sentences | `corpus/sentences/bank.json` + INDEX.md | {sc} | (dissected) |"
         if sc else "| sentences | _(P5+)_ | — | — |"),
        (f"| families | `corpus/families/families.json` + INDEX.md | {fc} | (cross-level) |"
         if fc else "| families | _(P4+)_ | — | — |"),
        "",
        "Each record carries `level_confidence`/`level_agreement`/`level_sources` (provenance) and a `source`. "
        "pt-BR meanings (`meanings_pt`/`gloss_pt`) are populated in the Layer-B pass.",
    ]
    (CORPUS / "INDEX.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    con = sqlite3.connect(DB)
    kc = export_kanji(con)
    vc = export_vocab(con)
    gc = export_grammar(con)
    fc = export_families(con)
    sc = export_sentences(con)
    write_corpus_index(kc, vc, gc, fc, sc)
    con.close()
    print(f"exported kanji={kc} vocab={vc} grammar={gc} families={fc} sentences={sc} -> corpus/")
    return 0


if __name__ == "__main__":
    sys.exit(main())
