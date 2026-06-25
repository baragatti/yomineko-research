#!/usr/bin/env python3
"""Export the corpus layer from db/corpus.sqlite to LLM-readable JSON + Markdown.

Canonical, committed, AI-reviewable artifacts; SQLite is a regenerable index.

i18n shape: EVERY localized field is a locale-object — `{"pt-BR": <content>, "en": <source>}` — where the
`en` key (when present) holds the authoritative Layer-A English source (KANJIDIC/JMdict/Tatoeba) and `pt-BR`
holds our locale content. Adding a locale = adding a key, never a schema change (design/i18n.md).
Mechanical enums (pos/inflection/particle function/register) are language-neutral English tokens (Layer A).
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
LEVELS = ["n5", "n4", "n3"]
# N2/N1 are BANK-ONLY (kanji + vocab for FSRS study; no sentences/grammar/lessons/conjugations). Kanji and
# vocab export over LEVELS + BANK_LEVELS; everything else stays on LEVELS.
BANK_LEVELS = ["n2", "n1"]
KV_LEVELS = LEVELS + BANK_LEVELS
LOC = DEFAULT_LOCALE  # "pt-BR"

# JMdict misc tag -> neutral register/usage enum (Layer A; what you can rely on for tone/UX warnings).
REGISTER_MAP = {
    "col": "colloquial", "sl": "slang", "net-sl": "internet-slang", "vulg": "vulgar",
    "derog": "derogatory", "hon": "honorific", "hum": "humble", "pol": "polite", "fam": "familiar",
    "arch": "archaic", "obs": "obsolete", "obsc": "obscure", "dated": "dated", "hist": "historical",
    "form": "formal", "joc": "jocular", "chn": "childish", "on-mim": "onomatopoeic", "id": "idiomatic",
    "euph": "euphemistic", "male": "male-speech", "fem": "female-speech", "rare": "rare",
    "yoji": "four-char-idiom", "uk": "usually-kana", "abbr": "abbreviation", "poet": "poetical",
    "proverb": "proverb", "X": "rude-or-X-rated", "sens": "sensitive",
}


def jw(path: Path, obj) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def jloads(s):
    return json.loads(s) if s else None


def loc(pt=None, en=None):
    """Locale-object: include only the keys that have content. None if empty."""
    o = {}
    if pt is not None and pt != "":
        o[LOC] = pt
    if en is not None and en != "":
        o["en"] = en
    return o or None


def register_of(misc):
    if not misc:
        return None
    out = [REGISTER_MAP.get(t, t) for t in misc]
    return out or None


def export_kanji(con: sqlite3.Connection) -> dict:
    L = get_all(con, "kanji")
    SL = get_all(con, "vocab_sense")
    # first sense per vocab -> (sense_id, gloss_en) for example-word glosses
    first_sense: dict[int, tuple] = {}
    for sid, vid, go in con.execute(
            "SELECT id,vocab_id,gloss_en FROM vocab_sense ORDER BY vocab_id, sense_order"):
        first_sense.setdefault(vid, (sid, go))
    out_counts, index_rows = {}, []
    for lvl in KV_LEVELS:
        records = []
        for k in con.execute(
            "SELECT id,slug,character,strokes,grade,freq_rank,unicode_cp,kanjivg_ref,kangxi_radical,"
            "meanings_en,level,level_confidence,level_agreement,level_sources "
            "FROM kanji WHERE level=? ORDER BY freq_rank IS NULL, freq_rank", (lvl,)
        ):
            (kid, slug, ch, strokes, grade, freq, cp, kvg, radical, men,
             level, lconf, lagree, lsrc) = k
            # nanori are rare name-readings (KANJIDIC2) — kept for fidelity, flagged low-priority so the
            # UI can de-emphasize/hide them (this is what jisho does).
            readings = [
                {"reading": r[0], "type": r[1], "okurigana": r[2], "introduced_at_level": r[3],
                 "common": r[1] != "nanori", "example_vocab_ids": jloads(r[4])}
                for r in con.execute(
                    "SELECT reading,reading_type,okurigana,introduced_at_level,example_vocab_ids "
                    "FROM kanji_reading WHERE kanji_id=? ORDER BY reading_type", (kid,))
            ]
            components = [r[0] for r in con.execute(
                "SELECT component FROM kanji_component WHERE kanji_id=?", (kid,))]
            # example words: vocab written with this kanji (common first), with kana + meaning
            example_words = []
            for vhw, vkana, vid in con.execute(
                    "SELECT v.headword,v.kana,v.id FROM vocab_kanji vk JOIN vocab v ON v.id=vk.vocab_id "
                    "WHERE vk.kanji_id=? ORDER BY v.common DESC, v.freq_rank IS NULL, v.freq_rank LIMIT 10",
                    (kid,)):
                fs = first_sense.get(vid)
                example_words.append({
                    "headword": vhw, "kana": vkana, "vocab_id": vid,
                    "gloss": loc(pt=SL.get((fs[0], "gloss")) if fs else None,
                                 en=jloads(fs[1]) if fs and fs[1] else None)})
            # example sentences (phrases) containing this kanji
            # Deterministic + real-preferring: real (ai_generated=0) first, then higher confidence, then a
            # STABLE slug tiebreak. Without an ORDER BY this was id-ordered → non-reproducible churn that also
            # preferred AI sentences over real ones (against §1.2).
            example_sentences = [r[0] for r in con.execute(
                "SELECT s.slug FROM sentence_kanji sk JOIN sentence s ON s.id=sk.sentence_id "
                "WHERE sk.kanji_id=? ORDER BY s.ai_generated, s.translation_confidence DESC, s.slug "
                "LIMIT 6", (kid,))]
            rec = {
                "id": kid, "slug": slug, "character": ch, "level": level,
                "level_confidence": lconf, "level_agreement": lagree, "level_sources": jloads(lsrc),
                "strokes": strokes, "grade": grade, "freq_rank": freq, "unicode": cp,
                "kanjivg_ref": kvg, "kangxi_radical": radical,
                "meanings": loc(pt=L.get((kid, "meanings")), en=jloads(men)),
                "notes": loc(pt=L.get((kid, "notes"))),
                "readings": readings, "components": components,
                "example_words": example_words, "example_sentences": example_sentences,
            }
            records.append(rec)
            men_pt = (L.get((kid, "meanings")) or jloads(men) or [])[:3]
            index_rows.append((ch, level, strokes, len(readings), ", ".join(men_pt)))
        jw(CORPUS / "kanji" / f"{lvl}.json", records)
        out_counts[lvl] = len(records)
    lines = ["# Corpus — Kanji (leveled)", "",
             f"_Generated {_dt.date.today().isoformat()}. `meanings` = {{\"{LOC}\":[…],\"en\":[…]}}; "
             f"readings carry `common` (nanori=false)._", "",
             "| kanji | level | strokes | #readings | meanings |",
             "|-------|-------|--------:|----------:|----------|"]
    for ch, lvl, st, nr, mn in index_rows:
        lines.append(f"| {ch} | {lvl} | {st} | {nr} | {mn} |")
    (CORPUS / "kanji" / "INDEX.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    return out_counts


def export_vocab(con: sqlite3.Connection) -> dict:
    SL = get_all(con, "vocab_sense")
    VL = get_all(con, "vocab")
    out_counts, index_rows = {}, []
    for lvl in KV_LEVELS:
        records = []
        for v in con.execute(
            "SELECT id,slug,headword,kana,romaji,lexeme_type,verb_class,adj_class,common,jmdict_ref,"
            "level,level_confidence,level_agreement,level_sources FROM vocab WHERE level=? "
            "ORDER BY headword", (lvl,)
        ):
            (vid, slug, hw, kana, romaji, lex, vclass, aclass, common, jref,
             level, lconf, lagree, lsrc) = v
            senses = []
            for s in con.execute(
                    "SELECT id,sense_order,pos,field_tags,misc_tags,gloss_en FROM vocab_sense "
                    "WHERE vocab_id=? ORDER BY sense_order", (vid,)):
                misc = jloads(s[4])
                senses.append({
                    "order": s[1], "pos": jloads(s[2]), "field": jloads(s[3]), "misc": misc,
                    "register": register_of(misc),
                    "gloss": loc(pt=SL.get((s[0], "gloss")), en=jloads(s[5])),
                })
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
            # vocab-level register = union of sense registers (handy for filtering/UX warnings)
            vreg = sorted({r for s in senses if s["register"] for r in s["register"]}) or None
            rec = {
                "id": vid, "slug": slug, "headword": hw, "kana": kana, "romaji": romaji,
                "level": level, "level_confidence": lconf, "level_agreement": lagree,
                "level_sources": jloads(lsrc), "lexeme_type": lex, "verb_class": vclass,
                "adj_class": aclass, "common": bool(common), "register": vreg, "jmdict_ref": jref,
                "notes": loc(pt=VL.get((vid, "notes"))), "pitch": pitch, "forms": forms,
                "senses": senses, "kanji": kanji,
            }
            records.append(rec)
            g0 = senses[0]["gloss"] if senses else None
            first = (g0.get(LOC) or g0.get("en") or []) if g0 else []
            index_rows.append((hw, kana, level, ", ".join(first[:2])))
        jw(CORPUS / "vocab" / f"{lvl}.json", records)
        out_counts[lvl] = len(records)
    lines = ["# Corpus — Vocabulary (leveled)", "",
             f"_Generated {_dt.date.today().isoformat()}. `gloss` = {{\"{LOC}\":[…],\"en\":[…]}} (en = JMdict "
             f"source); `register` = neutral usage enum from JMdict misc._", "",
             "| headword | kana | level | meaning |", "|----------|------|-------|---------|"]
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
        gcols = [r[1] for r in con.execute("PRAGMA table_info(grammar_point)")]
        extra = "".join(f",{c}" for c in ("forms_json", "register_json", "caution") if c in gcols)
        for g in con.execute(
            "SELECT id,slug,key,structure_pattern,register,references_json,level,level_confidence,"
            f"level_agreement,level_sources,needs_review{extra} FROM grammar_point WHERE level=? "
            "ORDER BY key", (lvl,)
        ):
            (gid, slug, key, pattern, reg, refs, level, lconf, lagree, lsrc, nr) = g[:11]
            ex = dict(zip(("forms_json", "register_json", "caution"), g[11:]))
            forms_json = ex.get("forms_json")
            form_meanings = L.get((gid, "form_meanings")) or {}
            forms = [{"form": fm, "meaning": loc(pt=form_meanings.get(fm))}
                     for fm in (jloads(forms_json) or [])]
            register = jloads(ex["register_json"]) if ex.get("register_json") else ([reg] if reg else None)
            related = [r[0] for r in con.execute(
                "SELECT g.key FROM grammar_related gr JOIN grammar_point g ON g.id=gr.related_grammar_id "
                "WHERE gr.grammar_id=?", (gid,))]
            expl = L.get((gid, "explanation"))
            rec = {
                "id": gid, "slug": slug, "key": key,
                "label": loc(pt=L.get((gid, "label"))),
                "forms": forms or None,
                "structure_pattern": pattern, "register": register, "caution": ex.get("caution"),
                "level": level,
                "level_confidence": lconf, "level_agreement": lagree, "level_sources": jloads(lsrc),
                "explanation": loc(pt=expl), "formation": loc(pt=L.get((gid, "formation"))),
                "nuance": loc(pt=L.get((gid, "nuance"))),
                "related": related, "refs": jloads(refs), "needs_review": bool(nr),
            }
            records.append(rec)
            index_rows.append((key, pattern or "", level, "authored" if expl else "stub"))
        jw(CORPUS / "grammar" / f"{lvl}.json", records)
        out_counts[lvl] = len(records)
    lines = ["# Corpus — Grammar points", "",
             f"_Generated {_dt.date.today().isoformat()}. `label`/`explanation`/`formation`/`nuance` are "
             f"locale-objects ({LOC}, Layer C, needs_review)._", "",
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
                            "id": mid, "intra_order": order, "is_core": bool(core),
                            "note": loc(pt=note)})
        records.append({
            "id": fid, "slug": slug, "type": ftype, "label": loc(pt=L.get((fid, "label"))),
            "description": loc(pt=L.get((fid, "description"))), "importance_rank": rank,
            "governing_rule": loc(pt=L.get((fid, "governing_rule"))), "spans_levels": jloads(spans),
            "members": members,
        })
        lbl = L.get((fid, "label"))
        index_rows.append((slug, ftype, lbl, len(members)))
    jw(CORPUS / "families" / "families.json", records)
    lines = ["# Corpus — Families / groups", "",
             f"_Generated {_dt.date.today().isoformat()}. `label`/`description`/`governing_rule` = locale-objects "
             f"({LOC})._", "",
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
    for row in con.execute("SELECT * FROM sentence ORDER BY slug"):  # stable identity (numeric id is volatile)
        s = dict(zip(cols, row))
        sid = s["id"]
        tokens = []
        for t in con.execute(
                "SELECT id,position,split_mode,surface,lemma,reading,romaji,pos_coarse,pos_fine,"
                "pos,inflection,inflection_type,vocab_id FROM token WHERE sentence_id=? "
                "ORDER BY split_mode, position", (sid,)):
            tid = t[0]
            tokens.append({
                "position": t[1], "split_mode": t[2], "surface": t[3], "lemma": t[4],
                "reading": t[5], "romaji": t[6],
                # mechanical Layer-A grammar (neutral enums + raw Sudachi)
                "pos": t[9], "pos_coarse": t[7], "pos_fine": t[8],
                "inflection": t[10], "inflection_type": t[11],
                # authored Layer-B (locale-objects)
                "role": loc(pt=TL.get((tid, "role"))), "gloss": loc(pt=TL.get((tid, "gloss"))),
                "conjugation_note": loc(pt=TL.get((tid, "conjugation_note"))), "vocab_id": t[12]})
        particles = []
        for p in con.execute("SELECT id,particle,function_type FROM particle WHERE sentence_id=?", (sid,)):
            pid = p[0]
            particles.append({
                "particle": p[1], "function_type": p[2],  # neutral enum (case/binding/conjunctive/...)
                "function": loc(pt=PL.get((pid, "function"))),
                "explanation": loc(pt=PL.get((pid, "explanation")))})
        grammar = [r[0] for r in con.execute(
            "SELECT g.key FROM sentence_grammar sg JOIN grammar_point g ON g.id=sg.grammar_id "
            "WHERE sg.sentence_id=? ORDER BY g.key", (sid,))]
        rec = {
            # slug is THE stable identity (spec §1.7). The DB numeric id is a volatile autoincrement (shifts
            # whenever the sentence set changes) and is consumed by nothing — intentionally NOT exported.
            "slug": s["slug"], "jp": s["jp"], "kana": s["kana"], "romaji": s["romaji"],
            "translation": loc(pt=SL.get((sid, "translation")), en=s["en"]),
            "translation_literal": loc(pt=SL.get((sid, "translation_literal"))),
            "level": s["level"],
            "provenance": {"jp_source": s["jp_source"], "pt_source": s["pt_source"],
                           "pt_validated_against": s["pt_validated_against"],
                           "translation_confidence": s["translation_confidence"],
                           "tier": s["dissection_tier"], "ai_generated": bool(s["ai_generated"]),
                           "needs_review": bool(s["needs_review"]), "locale": LOC},
            "structure_explanation": loc(pt=SL.get((sid, "structure_explanation"))),
            "tags": jloads(s["tags"]), "new_items": jloads(s["new_items"]),
            "tokens": tokens, "particles": particles, "grammar": grammar,
        }
        records.append(rec)
        tr = SL.get((sid, "translation"))
        index_rows.append((s["slug"], s["jp"], tr, s["level"]))
    jw(CORPUS / "sentences" / "bank.json", records)
    lines = ["# Corpus — Dissected sentence bank", "",
             f"_Generated {_dt.date.today().isoformat()}. Full §6 dissection. `translation` = "
             f"{{\"{LOC}\":…,\"en\":…}}; tokens carry mechanical `pos`/`inflection`; particles carry "
             f"`function_type`. Lessons reference these BY `slug` (the stable id)._", "",
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
        f"**These JSON/MD files are the source of truth.** Localized content uses locale-objects keyed by "
        f"`{LOC}` (+ `en` source); mechanical enums are neutral. See `design/i18n.md`._", "",
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
    # Conjugations are maintained by conjugate.py (separate from the DB export); list them from disk if present.
    conj = CORPUS / "conjugations"
    if (conj / "n5.json").exists():
        c5 = len(json.loads((conj / "n5.json").read_text(encoding="utf-8")))
        c4 = len(json.loads((conj / "n4.json").read_text(encoding="utf-8"))) if (conj / "n4.json").exists() else 0
        lines.append(f"| conjugations | `corpus/conjugations/<level>.json` | {c5} | {c4} |")
    # kana registry (pré-N5; built by build_kana.py) — columns repurposed to hiragana / katakana family counts
    fam = CORPUS / "kana" / "families.json"
    if fam.exists():
        kf = json.loads(fam.read_text(encoding="utf-8"))
        lines.append(f"| kana _(hira/kata families)_ | `corpus/kana/<script>.json` | {len(kf['hiragana'])} | "
                     f"{len(kf['katakana'])} |")
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
