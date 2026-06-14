#!/usr/bin/env python3
"""Export the corpus layer from db/corpus.sqlite to LLM-readable JSON + Markdown.

Canonical, committed, AI-reviewable artifacts; SQLite is a regenerable index. Localized content comes
from `localized_text` (default locale pt-BR); output uses NEUTRAL field names (`meanings`, `gloss`,
`translation`, `explanation`…) holding that locale's content, with English source fields kept as `*_en`.
"""
from __future__ import annotations

import datetime as _dt
import json
import sqlite3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "ingest"))
sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
from i18n_text import get_all, DEFAULT_LOCALE  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
DB = ROOT / "db" / "corpus.sqlite"
CORPUS = ROOT / "corpus"
LEVELS = ["n5", "n4"]
LOC = DEFAULT_LOCALE


def jw(path: Path, obj) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def jloads(s):
    return json.loads(s) if s else None


def export_kanji(con: sqlite3.Connection) -> dict:
    L = get_all(con, "kanji")
    out_counts, index_rows = {}, []
    for lvl in LEVELS:
        records = []
        for k in con.execute(
            "SELECT id,slug,character,strokes,grade,freq_rank,unicode_cp,kanjivg_ref,kangxi_radical,"
            "meanings_en,level,level_confidence,level_agreement,level_sources "
            "FROM kanji WHERE level=? ORDER BY freq_rank IS NULL, freq_rank", (lvl,)
        ):
            (kid, slug, ch, strokes, grade, freq, cp, kvg, radical, men,
             level, lconf, lagree, lsrc) = k
            readings = [
                {"reading": r[0], "type": r[1], "okurigana": r[2], "introduced_at_level": r[3],
                 "example_vocab_ids": jloads(r[4])}
                for r in con.execute(
                    "SELECT reading,reading_type,okurigana,introduced_at_level,example_vocab_ids "
                    "FROM kanji_reading WHERE kanji_id=? ORDER BY reading_type", (kid,))
            ]
            components = [r[0] for r in con.execute(
                "SELECT component FROM kanji_component WHERE kanji_id=?", (kid,))]
            rec = {
                "id": kid, "slug": slug, "character": ch, "level": level,
                "level_confidence": lconf, "level_agreement": lagree, "level_sources": jloads(lsrc),
                "strokes": strokes, "grade": grade, "freq_rank": freq, "unicode": cp,
                "kanjivg_ref": kvg, "kangxi_radical": radical,
                "meanings_en": jloads(men), "meanings": L.get((kid, "meanings")),
                "notes": L.get((kid, "notes")),
                "readings": readings, "components": components,
            }
            records.append(rec)
            index_rows.append((ch, level, strokes, len(readings), ", ".join((rec["meanings"] or [])[:3])))
        jw(CORPUS / "kanji" / f"{lvl}.json", records)
        out_counts[lvl] = len(records)
    lines = ["# Corpus — Kanji (leveled)", "",
             f"_Generated {_dt.date.today().isoformat()}. Source of truth: these files. `meanings` = {LOC}._",
             "", "| kanji | level | strokes | #readings | meanings (pt-BR) |",
             "|-------|-------|--------:|----------:|------------------|"]
    for ch, lvl, st, nr, mn in index_rows:
        lines.append(f"| {ch} | {lvl} | {st} | {nr} | {mn} |")
    (CORPUS / "kanji" / "INDEX.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    return out_counts


def export_vocab(con: sqlite3.Connection) -> dict:
    SL = get_all(con, "vocab_sense")
    VL = get_all(con, "vocab")
    out_counts, index_rows = {}, []
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
                {"order": s[1], "pos": jloads(s[2]), "field": jloads(s[3]), "misc": jloads(s[4]),
                 "gloss_en": jloads(s[5]), "gloss": SL.get((s[0], "gloss"))}
                for s in con.execute(
                    "SELECT id,sense_order,pos,field_tags,misc_tags,gloss_en FROM vocab_sense "
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
                "notes": VL.get((vid, "notes")), "pitch": pitch, "forms": forms,
                "senses": senses, "kanji": kanji,
            }
            records.append(rec)
            first = senses[0]["gloss"] if (senses and senses[0]["gloss"]) else []
            index_rows.append((hw, kana, level, ", ".join(first[:2])))
        jw(CORPUS / "vocab" / f"{lvl}.json", records)
        out_counts[lvl] = len(records)
    lines = ["# Corpus — Vocabulary (leveled)", "",
             f"_Generated {_dt.date.today().isoformat()}. `gloss` = {LOC}; `gloss_en` = JMdict source._", "",
             "| headword | kana | level | meaning (pt-BR) |",
             "|----------|------|-------|------------------|"]
    for hw, kana, lvl, mn in index_rows:
        lines.append(f"| {hw} | {kana} | {lvl} | {mn} |")
    (CORPUS / "vocab" / "INDEX.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    return out_counts


def export_grammar(con: sqlite3.Connection) -> dict:
    if not con.execute("SELECT COUNT(*) FROM grammar_point").fetchone()[0]:
        return {}
    L = get_all(con, "grammar_point")
    out_counts, index_rows = {}, []
    for lvl in LEVELS:
        records = []
        for g in con.execute(
            "SELECT id,slug,key,structure_pattern,register,references_json,level,level_confidence,"
            "level_agreement,level_sources,needs_review FROM grammar_point WHERE level=? ORDER BY key", (lvl,)
        ):
            (gid, slug, key, pattern, reg, refs, level, lconf, lagree, lsrc, nr) = g
            related = [r[0] for r in con.execute(
                "SELECT g.key FROM grammar_related gr JOIN grammar_point g ON g.id=gr.related_grammar_id "
                "WHERE gr.grammar_id=?", (gid,))]
            expl = L.get((gid, "explanation"))
            rec = {
                "id": gid, "slug": slug, "key": key, "label": L.get((gid, "label")),
                "structure_pattern": pattern, "register": reg, "level": level,
                "level_confidence": lconf, "level_agreement": lagree, "level_sources": jloads(lsrc),
                "explanation": expl, "formation": L.get((gid, "formation")), "nuance": L.get((gid, "nuance")),
                "related": related, "refs": jloads(refs), "needs_review": bool(nr),
            }
            records.append(rec)
            index_rows.append((key, pattern or "", level, "authored" if expl else "stub"))
        jw(CORPUS / "grammar" / f"{lvl}.json", records)
        out_counts[lvl] = len(records)
    lines = ["# Corpus — Grammar points", "",
             f"_Generated {_dt.date.today().isoformat()}. `label`/`explanation`/`formation`/`nuance` = {LOC} "
             f"(Layer C, needs_review)._", "",
             "| key | pattern | level | explanation |", "|-----|---------|-------|-------------|"]
    for key, pat, lvl, st in index_rows:
        lines.append(f"| {key} | {pat} | {lvl} | {st} |")
    (CORPUS / "grammar" / "INDEX.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    return out_counts


def export_families(con: sqlite3.Connection) -> int:
    if not con.execute("SELECT COUNT(*) FROM family").fetchone()[0]:
        return 0
    L = get_all(con, "family")
    records, index_rows = [], []
    for f in con.execute(
        "SELECT id,slug,type,importance_rank,spans_levels FROM family ORDER BY importance_rank, slug"
    ):
        fid, slug, ftype, rank, spans = f
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
                            "id": mid, "intra_order": order, "is_core": bool(core), "note": note})
        records.append({
            "id": fid, "slug": slug, "type": ftype, "label": L.get((fid, "label")),
            "description": L.get((fid, "description")), "importance_rank": rank,
            "governing_rule": L.get((fid, "governing_rule")), "spans_levels": jloads(spans),
            "members": members,
        })
        index_rows.append((slug, ftype, L.get((fid, "label")), len(members)))
    jw(CORPUS / "families" / "families.json", records)
    lines = ["# Corpus — Families / groups", "",
             f"_Generated {_dt.date.today().isoformat()}. `label`/`description`/`governing_rule` = {LOC}._", "",
             "| family | type | label | #members |", "|--------|------|-------|---------:|"]
    for slug, ftype, label, n in index_rows:
        lines.append(f"| {slug} | {ftype} | {label} | {n} |")
    (CORPUS / "families" / "INDEX.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    return len(records)


def export_sentences(con: sqlite3.Connection) -> int:
    if not con.execute("SELECT COUNT(*) FROM sentence").fetchone()[0]:
        return 0
    SL = get_all(con, "sentence")
    TL = get_all(con, "token")
    PL = get_all(con, "particle")
    records, index_rows = [], []
    cols = [d[0] for d in con.execute("SELECT * FROM sentence LIMIT 1").description]
    for row in con.execute("SELECT * FROM sentence ORDER BY id"):
        s = dict(zip(cols, row))
        sid = s["id"]
        tokens = []
        for t in con.execute(
                "SELECT id,position,split_mode,surface,lemma,reading,romaji,pos_coarse,pos_fine,vocab_id "
                "FROM token WHERE sentence_id=? ORDER BY split_mode, position", (sid,)):
            tid = t[0]
            tokens.append({"position": t[1], "split_mode": t[2], "surface": t[3], "lemma": t[4],
                           "reading": t[5], "romaji": t[6], "pos_coarse": t[7], "pos_fine": t[8],
                           "role": TL.get((tid, "role")), "gloss": TL.get((tid, "gloss")),
                           "conjugation_note": TL.get((tid, "conjugation_note")), "vocab_id": t[9]})
        particles = []
        for p in con.execute("SELECT id,particle FROM particle WHERE sentence_id=?", (sid,)):
            pid = p[0]
            particles.append({"particle": p[1], "function": PL.get((pid, "function")),
                              "explanation": PL.get((pid, "explanation"))})
        grammar = [r[0] for r in con.execute(
            "SELECT g.key FROM sentence_grammar sg JOIN grammar_point g ON g.id=sg.grammar_id "
            "WHERE sg.sentence_id=?", (sid,))]
        translation = SL.get((sid, "translation"))
        rec = {
            "id": sid, "slug": s["slug"], "jp": s["jp"], "kana": s["kana"], "romaji": s["romaji"],
            "translation": translation, "translation_literal": SL.get((sid, "translation_literal")),
            "en": s["en"], "level": s["level"],
            "provenance": {"jp_source": s["jp_source"], "pt_source": s["pt_source"],
                           "pt_validated_against": s["pt_validated_against"],
                           "translation_confidence": s["translation_confidence"],
                           "tier": s["dissection_tier"], "ai_generated": bool(s["ai_generated"]),
                           "needs_review": bool(s["needs_review"]), "locale": LOC},
            "structure_explanation": SL.get((sid, "structure_explanation")),
            "tags": jloads(s["tags"]), "new_items": jloads(s["new_items"]),
            "tokens": tokens, "particles": particles, "grammar": grammar,
        }
        records.append(rec)
        index_rows.append((s["slug"], s["jp"], translation, s["level"]))
    jw(CORPUS / "sentences" / "bank.json", records)
    lines = ["# Corpus — Dissected sentence bank", "",
             f"_Generated {_dt.date.today().isoformat()}. Full §6 dissection; `translation`/`gloss`/`function` "
             f"= {LOC}. Lessons reference these BY ID._", "",
             "| slug | jp | translation | level |", "|------|----|----|-------|"]
    for slug, jp, tr, lvl in index_rows:
        lines.append(f"| {slug} | {jp} | {tr} | {lvl} |")
    (CORPUS / "sentences" / "INDEX.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    return len(records)


def write_corpus_index(kc, vc, gc=None, fc=0, sc=0) -> None:
    gc = gc or {}
    lines = [
        "# Corpus layer (LLM-readable, canonical)", "",
        f"_Generated {_dt.date.today().isoformat()} from `db/corpus.sqlite` (regenerable index). "
        f"**These JSON/MD files are the source of truth.** Localized content is the **{LOC}** locale "
        f"(neutral field names; `localized_text` model — see `design/i18n.md`)._", "",
        "| entity | files | n5 | n4 |", "|--------|-------|---:|---:|",
        f"| kanji | `corpus/kanji/<level>.json` | {kc.get('n5',0)} | {kc.get('n4',0)} |",
        f"| vocab | `corpus/vocab/<level>.json` | {vc.get('n5',0)} | {vc.get('n4',0)} |",
        (f"| grammar | `corpus/grammar/<level>.json` | {gc.get('n5',0)} | {gc.get('n4',0)} |"
         if gc else "| grammar | _(P4+)_ | — | — |"),
        (f"| sentences | `corpus/sentences/bank.json` | {sc} | (dissected) |"
         if sc else "| sentences | _(P5+)_ | — | — |"),
        (f"| families | `corpus/families/families.json` | {fc} | (cross-level) |"
         if fc else "| families | _(P4+)_ | — | — |"),
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
