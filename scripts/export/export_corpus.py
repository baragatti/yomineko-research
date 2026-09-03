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

# W01: honour --db / $YOMINEKO_DB so a rebuild can target a scratch DB (scripts/dbtarget.py).
import sys as _sys, pathlib as _pl  # noqa: E402
_sys.path.append(str(next(p for p in _pl.Path(__file__).resolve().parents if p.name == "scripts")))
from dbtarget import db_target, out_root, build_date  # noqa: E402
from review_ledger import Ledger  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
DB = db_target(ROOT / "db" / "corpus.sqlite")
CORPUS = out_root(ROOT) / "corpus"
LEVELS = ["n5", "n4", "n3"]
# N2/N1 are BANK-ONLY (kanji + vocab for FSRS study; no sentences/grammar/lessons/conjugations). Kanji and
# vocab export over LEVELS + BANK_LEVELS; everything else stays on LEVELS.
BANK_LEVELS = ["n2", "n1"]
KV_LEVELS = LEVELS + BANK_LEVELS
LOC = DEFAULT_LOCALE  # "pt-BR"

# Rank order for "is this word at or below that record's own level?". Level is DATA, not structure
# (CLAUDE.md §1.6): a new level is a new row here, never a schema change. Unleveled rows sort last.
LEVEL_ORD = {lv: i for i, lv in enumerate(["pre-n5", "n5", "n4", "n3", "n2", "n1"], start=1)}
UNLEVELED_ORD = 99
# The same ladder as a SQL expression, so ORDER BY can band rows without a temp table.
LEVEL_ORD_SQL = ("CASE v.level " + " ".join(f"WHEN '{lv}' THEN {o}" for lv, o in LEVEL_ORD.items())
                 + f" ELSE {UNLEVELED_ORD} END")

# Example words are a TEACHING slot, not a dump of the vocab_kanji join, so the 10 that fit are ranked:
#   1. NOT a proper name. Names teach nothing about the character's everyday use, so they sink below
#      every ordinary word and surface only when a kanji has nothing else (spec §3 keeps JMnedict out
#      for exactly this reason). `pos` is a JSON list, hence the quoted LIKE — '%"n-pr"%' must not
#      also match "n-pref".
#   2. At or below the kanji's OWN level first. 名 was spending 6 of its 10 slots on N1/N2 compounds
#      while 平仮名 and 片仮名 — n5, already in this corpus — were not shown at all, and 何 omitted
#      eight n5 words. Above-level words then fill whatever is left, so nothing gets thinner.
#   3. Inside each band, the old ordering: common first, then frequency rank, nulls last.
#   4. `v.slug` last, so the LIMIT cut is REPRODUCIBLE. 不 and 主 tie on every other key (all common,
#      all freq_rank null), so the previous cut fell on undefined row order and could change per build.
# DISTINCT via the IN-subquery because vocab_kanji is keyed per OCCURRENCE — 日曜日 joins 日 twice and
# 滅茶苦茶 joins 茶 twice, which spent a real slot on a byte-identical repeat.
EXAMPLE_WORDS_SQL = f"""
SELECT v.headword, v.kana, v.id, v.slug
  FROM vocab v
 WHERE v.id IN (SELECT vocab_id FROM vocab_kanji WHERE kanji_id = ?)
 ORDER BY (SELECT CASE WHEN COUNT(*) > 0
                        AND SUM(CASE WHEN s.pos LIKE '%"n-pr"%' THEN 1 ELSE 0 END) = COUNT(*)
                       THEN 1 ELSE 0 END
             FROM vocab_sense s WHERE s.vocab_id = v.id),
          CASE WHEN {LEVEL_ORD_SQL} <= ? THEN 0 ELSE 1 END,
          v.common DESC, v.freq_rank IS NULL, v.freq_rank, v.slug
 LIMIT 10
"""

# kun -> on -> nanori. `ORDER BY reading_type` was a plain string sort, and 'kun' < 'nanori' < 'on'
# alphabetically, so the name-readings block wedged itself between the two groups a learner needs:
# 理's single on reading リ (料理, 理由, 無理) sat at index 17 of 18, behind 16 nanori. `kr.id` keeps
# the within-group order stable across rebuilds.
READING_ORDER_SQL = "ORDER BY CASE kr.reading_type WHEN 'kun' THEN 0 WHEN 'on' THEN 1 ELSE 2 END, kr.id"

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


# W06. The approval ledger is applied HERE, at the single point every record file leaves this
# script, so no future export path can forget it. `apply_all` stamps `review_status` onto exactly
# the records a LIVE entry covers — one whose content hash still matches the text it approved — and
# writes nothing at all onto the rest, so an empty ledger leaves the export byte-identical. A stale
# entry exports nothing and is counted; design/review_ledger.md has the three states.
LEDGER: Ledger | None = None


def jw(path: Path, obj) -> None:
    if LEDGER is not None:
        LEDGER.apply_all(obj)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def jloads(s):
    return json.loads(s) if s else None


# Confidence and sources reach us straight from the working index, which stores whatever each ingest
# pass happened to write. Three author-added kanji (米, 港, 市) carry the string "low" where all 10,025
# other leveled rows carry a float, and one of them stores its sources as a bare list where its two
# siblings use a dict. Normalising on the way out means the exported contract is uniform no matter what
# the index holds, which is the point of having a contract at all.
_CONF_WORDS = {"low": 0.0, "medium": 0.5, "high": 1.0}


def confidence(v):
    """level_confidence as a float in [0,1]. A word grade maps to its midpoint; None stays None."""
    if v is None or isinstance(v, (int, float)):
        return v
    try:
        return float(v)
    except (TypeError, ValueError):
        return _CONF_WORDS.get(str(v).strip().lower())


def sources(s):
    """level_sources as an object. A bare list is the 'lists' member of that object, not a rival shape."""
    v = jloads(s)
    return {"lists": v} if isinstance(v, list) else v


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


# Sentences kept in the bank but NOT auto-surfaced as kanji-page examples (clinical/crude register that reads
# oddly next to a beginner kanji — owner-flagged 2026-06-27, e.g. "fezes moles" on the 出 page). Term-based so
# new bank sentences are covered on every export.
SENSITIVE_PT = ("diarr", "fezes", "vomit", "urin", "suicid", "cadáver", "estupro")


def sensitive_slugs(con: sqlite3.Connection) -> set:
    q = " OR ".join("lt.value LIKE ?" for _ in SENSITIVE_PT)
    return {r[0] for r in con.execute(
        "SELECT s.slug FROM sentence s JOIN localized_text lt ON lt.entity_type='sentence' "
        f"AND lt.entity_id=s.id AND lt.field='translation' AND lt.locale='pt-BR' WHERE {q}",
        tuple(f"%{t}%" for t in SENSITIVE_PT))}


# Filled by main() before any export runs: vocab row id -> published slug, and
# (member_type, member_row_id) -> [family slug,...] (see family_backlinks).
VOCAB_SLUG_BY_ID: dict = {}
FAMILY_OF: dict = {}


def export_kanji(con: sqlite3.Connection) -> dict:
    SENSITIVE = sensitive_slugs(con)
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
            "SELECT id,slug,character,strokes,grade,freq_rank,unicode_cp,kanjivg_ref,kangxi_radical,radical_char,"
            "meanings_en,level,level_confidence,level_agreement,level_sources "
            "FROM kanji WHERE level=? ORDER BY freq_rank IS NULL, freq_rank", (lvl,)
        ):
            (kid, slug, ch, strokes, grade, freq, cp, kvg, radical, rchar, men,
             level, lconf, lagree, lsrc) = k
            # nanori are rare name-readings (KANJIDIC2) — kept for fidelity, flagged low-priority so the
            # UI can de-emphasize/hide them (this is what jisho does).
            # Per-reading enrichment (roadmap D): `note` is a pt-BR line on what the reading means and
            # when it is used; `example_vocab_ids` are the compounds that actually USE this reading,
            # grouped positionally rather than by substring. Both are null for readings nobody enriched.
            readings = [
                {"reading": r[0], "type": r[1], "okurigana": r[2], "introduced_at_level": r[3],
                 "common": r[1] != "nanori", "example_vocab_ids": jloads(r[4]),
                 # the published address form of the same edge; the row ids stay for compatibility
                 "example_vocab": [VOCAB_SLUG_BY_ID[v] for v in (jloads(r[4]) or [])
                                   if v in VOCAB_SLUG_BY_ID],
                 "note": loc(pt=r[5]) if r[5] else None,
                 # W05. 3,970 of these 33,785 rows are flagged in the working index and the flag
                 # never reached the export, so a teacher reading corpus/kanji/*.json could not see
                 # that a reading NOTE is unreviewed Layer-C prose. It means here exactly what it
                 # means everywhere else (common.schema.json -> Provenance.needs_review).
                 "needs_review": bool(r[6])}
                for r in con.execute(
                    "SELECT kr.reading,kr.reading_type,kr.okurigana,kr.introduced_at_level,"
                    "kr.example_vocab_ids,"
                    "(SELECT value FROM localized_text WHERE entity_type='kanji_reading' "
                    " AND entity_id=kr.id AND field='note' AND locale='pt-BR'),"
                    "kr.needs_review "
                    f"FROM kanji_reading kr WHERE kr.kanji_id=? {READING_ORDER_SQL}", (kid,))
            ]
            irr_note = con.execute(
                "SELECT value FROM localized_text WHERE entity_type='kanji' AND entity_id=? "
                "AND field='irregular_note' AND locale='pt-BR'", (kid,)).fetchone()
            components = [r[0] for r in con.execute(
                "SELECT component FROM kanji_component WHERE kanji_id=?", (kid,))]
            # example words: vocab written with this kanji, ranked by EXAMPLE_WORDS_SQL (see there),
            # with kana + meaning
            example_words = []
            for vhw, vkana, vid, vslug in con.execute(
                    EXAMPLE_WORDS_SQL, (kid, LEVEL_ORD.get(level, UNLEVELED_ORD))):
                fs = first_sense.get(vid)
                # `slug` is the published address; `vocab_id` is the storage row and is kept only
                # because existing consumers read it. A reader linking to the word wants the slug —
                # resolving by `headword` instead lands on the wrong record for 93 shared headwords.
                example_words.append({
                    "headword": vhw, "kana": vkana, "vocab_id": vid, "slug": vslug,
                    "gloss": loc(pt=SL.get((fs[0], "gloss")) if fs else None,
                                 en=jloads(fs[1]) if fs and fs[1] else None)})
            # example sentences (phrases) containing this kanji
            # Deterministic + real-preferring: real (ai_generated=0) first, then higher confidence, then a
            # STABLE slug tiebreak. Without an ORDER BY this was id-ordered → non-reproducible churn that also
            # preferred AI sentences over real ones (against §1.2).
            example_sentences = [r[0] for r in con.execute(
                "SELECT s.slug FROM sentence_kanji sk JOIN sentence s ON s.id=sk.sentence_id "
                "WHERE sk.kanji_id=? ORDER BY s.ai_generated, s.translation_confidence DESC, s.slug "
                "LIMIT 18", (kid,)) if r[0] not in SENSITIVE][:6]
            rec = {
                "id": kid, "slug": slug, "character": ch, "level": level,
                "level_confidence": confidence(lconf), "level_agreement": lagree, "level_sources": sources(lsrc),
                "strokes": strokes, "grade": grade, "freq_rank": freq, "unicode": cp,
                "kanjivg_ref": kvg, "kangxi_radical": radical, "radical_char": rchar,
                "meanings": loc(pt=L.get((kid, "meanings")), en=jloads(men)),
                "notes": loc(pt=L.get((kid, "notes"))),
                "readings": readings, "irregular_note": loc(pt=irr_note[0]) if irr_note else None,
                "components": components,
                "example_words": example_words, "example_sentences": example_sentences,
                # Back-pointer into the family layer, so a family is reachable FROM its members
                # (spec 1.7); without it all 396 families were graph orphans.
                "families": FAMILY_OF.get(("kanji", kid), []),
            }
            records.append(rec)
            men_pt = (L.get((kid, "meanings")) or jloads(men) or [])[:3]
            index_rows.append((ch, level, strokes, len(readings), ", ".join(men_pt)))
        jw(CORPUS / "kanji" / f"{lvl}.json", records)
        out_counts[lvl] = len(records)
    lines = ["# Corpus — Kanji (leveled)", "",
             f"_Generated {build_date()}. `meanings` = {{\"{LOC}\":[…],\"en\":[…]}}; "
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
                    "SELECT id,sense_order,pos,field_tags,misc_tags,gloss_en,needs_review "
                    "FROM vocab_sense WHERE vocab_id=? ORDER BY sense_order", (vid,)):
                misc = jloads(s[4])
                senses.append({
                    "order": s[1], "pos": jloads(s[2]), "field": jloads(s[3]), "misc": misc,
                    "register": register_of(misc),
                    "gloss": loc(pt=SL.get((s[0], "gloss")), en=jloads(s[5])),
                    # W05. The pt-BR gloss is Layer B — derived by a model from the JMdict `en`
                    # beside it — and all 10,592 senses are flagged unreviewed in the working
                    # index. Dropping the flag on the way out published 10,592 unreviewed
                    # translations that looked, to any consumer, exactly like approved ones.
                    "needs_review": bool(s[6]),
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
                "level": level, "level_confidence": confidence(lconf), "level_agreement": lagree,
                "level_sources": sources(lsrc), "lexeme_type": lex, "verb_class": vclass,
                "adj_class": aclass, "common": bool(common), "register": vreg, "jmdict_ref": jref,
                "notes": loc(pt=VL.get((vid, "notes"))), "pitch": pitch, "forms": forms,
                "senses": senses, "kanji": kanji,
                "families": FAMILY_OF.get(("vocab", vid), []),
            }
            records.append(rec)
            g0 = senses[0]["gloss"] if senses else None
            first = (g0.get(LOC) or g0.get("en") or []) if g0 else []
            index_rows.append((hw, kana, level, ", ".join(first[:2])))
        jw(CORPUS / "vocab" / f"{lvl}.json", records)
        out_counts[lvl] = len(records)
    lines = ["# Corpus — Vocabulary (leveled)", "",
             f"_Generated {build_date()}. `gloss` = {{\"{LOC}\":[…],\"en\":[…]}} (en = JMdict "
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
    Len = get_all(con, "grammar_point", "en")
    out_counts, index_rows = {}, []
    gcols = [r[1] for r in con.execute("PRAGMA table_info(grammar_point)")]
    for lvl in LEVELS:
        records = []
        # Roadmap E added four; guarded by `if c in gcols` so an un-migrated DB still exports.
        GEXTRA = ("forms_json", "register_json", "caution",
                 "formation_steps_json", "nuance_tags_json", "usage_contexts_json",
                 "steps_unavailable")
        extra = "".join(f",{c}" for c in GEXTRA if c in gcols)
        # W08 (owner decision A3): a record merged into another keeps its row but leaves the ACTIVE
        # registry. `deprecated_by` holds the survivor's slug; NULL means live. Guarded on the column
        # so a DB built before scripts/migrate_grammar_merge.py still exports.
        live = " AND deprecated_by IS NULL" if "deprecated_by" in gcols else ""
        for g in con.execute(
            "SELECT id,slug,key,structure_pattern,register,references_json,level,level_confidence,"
            f"level_agreement,level_sources,needs_review{extra} FROM grammar_point WHERE level=?{live} "
            "ORDER BY key", (lvl,)
        ):
            (gid, slug, key, pattern, reg, refs, level, lconf, lagree, lsrc, nr) = g[:11]
            ex = dict(zip([c for c in GEXTRA if c in gcols], g[11:]))
            forms_json = ex.get("forms_json")
            form_meanings = L.get((gid, "form_meanings")) or {}
            form_meanings_en = Len.get((gid, "form_meanings"))
            if not isinstance(form_meanings_en, dict):
                form_meanings_en = {}
            forms = [{"form": fm, "meaning": loc(pt=form_meanings.get(fm), en=form_meanings_en.get(fm))}
                     for fm in (jloads(forms_json) or [])]
            register = jloads(ex["register_json"]) if ex.get("register_json") else ([reg] if reg else None)
            related = [r[0] for r in con.execute(
                "SELECT g.key FROM grammar_related gr JOIN grammar_point g ON g.id=gr.related_grammar_id "
                "WHERE gr.grammar_id=?", (gid,))]
            expl = L.get((gid, "explanation"))
            rec = {
                "id": gid, "slug": slug, "key": key,
                "label": loc(pt=L.get((gid, "label")), en=Len.get((gid, "label"))),
                "forms": forms or None,
                "structure_pattern": pattern, "register": register, "caution": ex.get("caution"),
                "level": level,
                "level_confidence": confidence(lconf), "level_agreement": lagree, "level_sources": sources(lsrc),
                "explanation": loc(pt=expl, en=Len.get((gid, "explanation"))),
                "formation": loc(pt=L.get((gid, "formation")), en=Len.get((gid, "formation"))),
                # Roadmap E (migration 008). Mechanical build steps alongside the prose formation, so a
                # generator can act on the pattern instead of only a human reading it. `variants` is one
                # step list PER accepting base and is never flattened; `steps_unavailable` carries the
                # reason when a formation cannot be stated safely, which includes the 50 points whose
                # steps the verification pass refused. Neutral enums (design/i18n.md).
                "formation_steps": jloads(ex.get("formation_steps_json")),
                "nuance_tags": jloads(ex.get("nuance_tags_json")) or [],
                "usage_contexts": jloads(ex.get("usage_contexts_json")) or [],
                "steps_unavailable": ex.get("steps_unavailable"),
                "nuance": loc(pt=L.get((gid, "nuance")), en=Len.get((gid, "nuance"))),
                "related": related, "refs": jloads(refs), "needs_review": bool(nr),
                "families": FAMILY_OF.get(("grammar", gid), []),
            }
            records.append(rec)
            index_rows.append((key, pattern or "", level, "authored" if expl else "stub"))
        jw(CORPUS / "grammar" / f"{lvl}.json", records)
        out_counts[lvl] = len(records)
    lines = ["# Corpus — Grammar points", "",
             f"_Generated {build_date()}. `label`/`explanation`/`formation`/`nuance` are "
             f"locale-objects ({LOC}, Layer C, needs_review)._", "",
             "| key | pattern | level | explanation |", "|-----|---------|-------|-------------|"]
    for key, pat, lvl, st in index_rows:
        lines.append(f"| {key} | {pat} | {lvl} | {st} |")
    # W08: the redirect. Every address that used to resolve to a merged-away record resolves through
    # this map instead, so a consumer holding an old slug is never left guessing. Written on every
    # export (empty object when nothing is deprecated) so its absence always means "not exported yet",
    # never "nothing was merged".
    # It lives BESIDE corpus/grammar/, not inside it: validate_course_chain.check_catalogue refuses a
    # sidecar that the grammar glob (`corpus/grammar/*.json`, packing 'list') would match — "a sidecar
    # inside a registry glob poisons every consumer; move it out" — after the unregistered_chars.json
    # incident broke four gates. corpus/exam_banks/ solves the same problem by narrowing its glob to
    # n[0-9]_*.json; the grammar glob is not narrowed, so the file moves instead. Listed in
    # design/generated_artifacts.json, as that gate also requires.
    dep = {}
    if "deprecated_by" in gcols:
        dep = {slug: by for slug, by in con.execute(
            "SELECT slug, deprecated_by FROM grammar_point WHERE deprecated_by IS NOT NULL ORDER BY slug")}
    jw(CORPUS / "grammar_deprecated.json", dep)
    lines += ["", f"**Deprecated:** {len(dep)} record(s) merged into another and dropped from the "
                  f"lists above; `../grammar_deprecated.json` maps each old slug to its survivor."]
    (CORPUS / "grammar" / "INDEX.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    return out_counts


def family_backlinks(con: sqlite3.Connection) -> dict:
    """(member_type, member_row_id) -> [family slug, ...] so records can point back at their families.

    Without this the family layer is write-only: families name their members but no member names its
    family, so nothing in the published graph can reach a family from a record (spec 1.7).
    """
    out: dict = {}
    for fslug, mtype, mid in con.execute(
            "SELECT f.slug, fm.member_type, fm.member_id FROM family_member fm "
            "JOIN family f ON f.id = fm.family_id ORDER BY f.importance_rank, f.slug"):
        out.setdefault((mtype, mid), []).append(fslug)
    return out


_LEVEL_SEQ = ["pre-n5", "n5", "n4", "n3", "n2", "n1"]


def _member_span(con: sqlite3.Connection, fid: int) -> list:
    """The set of levels a family's members actually occupy, in teaching order."""
    found = set()
    for mtype, mid in con.execute(
            "SELECT member_type, member_id FROM family_member WHERE family_id=?", (fid,)):
        tbl = {"kanji": "kanji", "vocab": "vocab", "grammar": "grammar_point"}.get(mtype)
        if not tbl:
            continue
        r = con.execute(f"SELECT level FROM {tbl} WHERE id=?", (mid,)).fetchone()
        if r and r[0]:
            found.add(r[0])
    return [lv for lv in _LEVEL_SEQ if lv in found]


def export_families(con: sqlite3.Connection) -> int:
    if not con.execute("SELECT COUNT(*) FROM family").fetchone()[0]:
        return 0
    L = get_all(con, "family")
    Len = get_all(con, "family", "en")
    records, index_rows = [], []
    for f in con.execute(
        "SELECT id,slug,type,importance_rank,spans_levels,needs_review FROM family "
        "ORDER BY importance_rank, slug"
    ):
        fid, slug, ftype, rank, spans, needs_review = f
        members = []
        for m in con.execute(
            "SELECT member_type,member_id,intra_order,is_core,note_pt FROM family_member "
            "WHERE family_id=? ORDER BY intra_order", (fid,)
        ):
            mtype, mid, order, core, note = m
            # `ref` stays the human-readable form (headword/character/key); `slug` is the ADDRESS.
            # 73 of the 1,652 vocab member refs are headwords shared by more than one record, so the
            # display form alone cannot be resolved; the slug can.
            if mtype == "kanji":
                row = con.execute("SELECT character, slug FROM kanji WHERE id=?", (mid,)).fetchone()
            elif mtype == "vocab":
                row = con.execute("SELECT headword, slug FROM vocab WHERE id=?", (mid,)).fetchone()
            else:
                row = con.execute("SELECT key, slug FROM grammar_point WHERE id=?", (mid,)).fetchone()
            members.append({"member_type": mtype, "ref": row[0] if row else None,
                            "slug": row[1] if row else None,
                            "id": mid, "intra_order": order, "is_core": bool(core),
                            "note": loc(pt=note)})
        records.append({
            "id": fid, "slug": slug, "type": ftype,
            "label": loc(pt=L.get((fid, "label")), en=Len.get((fid, "label"))),
            "description": loc(pt=L.get((fid, "description")), en=Len.get((fid, "description"))),
            "importance_rank": rank,
            "governing_rule": loc(pt=L.get((fid, "governing_rule")), en=Len.get((fid, "governing_rule"))),
            # spans_levels is DERIVED from the members, not read from the stored column: 16 families
            # (14 kanji_component + 2 others) declared ['n5','n4'] while holding members outside it,
            # because the column froze at authoring time and the membership moved. A derived claim
            # cannot go stale. Order follows the teaching sequence.
            "spans_levels": _member_span(con, fid),
            # W05. Every one of the 396 families is authored Layer-C grouping — the label, the
            # description and the governing rule are pedagogy — and all 396 are flagged in the
            # working index. The flag belongs on the record a teacher actually opens.
            "needs_review": bool(needs_review),
            "members": members,
        })
        lbl = L.get((fid, "label"))
        index_rows.append((slug, ftype, lbl, len(members)))
    jw(CORPUS / "families" / "families.json", records)
    lines = ["# Corpus — Families / groups", "",
             f"_Generated {build_date()}. `label`/`description`/`governing_rule` = locale-objects "
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
    SLen = get_all(con, "sentence", "en")
    TLen = get_all(con, "token", "en")
    PLen = get_all(con, "particle", "en")
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
                # The vocab SLUG is the published sentence->vocab edge; `vocab_id` (below, kept for
                # compatibility) is a storage row number no consumer should key on.
                "vocab": VOCAB_SLUG_BY_ID.get(t[12]),
                # mechanical Layer-A grammar (neutral enums + raw Sudachi)
                "pos": t[9], "pos_coarse": t[7], "pos_fine": t[8],
                "inflection": t[10], "inflection_type": t[11],
                # authored Layer-B (locale-objects)
                "role": loc(pt=TL.get((tid, "role")), en=TLen.get((tid, "role"))),
                "gloss": loc(pt=TL.get((tid, "gloss")), en=TLen.get((tid, "gloss"))),
                "conjugation_note": loc(pt=TL.get((tid, "conjugation_note")), en=TLen.get((tid, "conjugation_note"))),
                "vocab_id": t[12]})
        particles = []
        for p in con.execute("SELECT id,particle,function_type FROM particle WHERE sentence_id=?", (sid,)):
            pid = p[0]
            particles.append({
                "particle": p[1], "function_type": p[2],  # neutral enum (case/binding/conjunctive/...)
                "function": loc(pt=PL.get((pid, "function")), en=PLen.get((pid, "function"))),
                "explanation": loc(pt=PL.get((pid, "explanation")), en=PLen.get((pid, "explanation")))})
        grammar = [r[0] for r in con.execute(
            "SELECT g.key FROM sentence_grammar sg JOIN grammar_point g ON g.id=sg.grammar_id "
            "WHERE sg.sentence_id=? ORDER BY g.key", (sid,))]
        rec = {
            # slug is THE stable identity (spec §1.7). The DB numeric id is a volatile autoincrement (shifts
            # whenever the sentence set changes) and is consumed by nothing — intentionally NOT exported.
            "slug": s["slug"], "jp": s["jp"], "kana": s["kana"], "romaji": s["romaji"],
            "translation": loc(pt=SL.get((sid, "translation")), en=s["en"] or SLen.get((sid, "translation"))),
            "translation_literal": loc(pt=SL.get((sid, "translation_literal")), en=SLen.get((sid, "translation_literal"))),
            "level": s["level"],
            "provenance": {"jp_source": s["jp_source"], "pt_source": s["pt_source"],
                           "pt_validated_against": s["pt_validated_against"],
                           "translation_confidence": s["translation_confidence"],
                           "tier": s["dissection_tier"], "ai_generated": bool(s["ai_generated"]),
                           "needs_review": bool(s["needs_review"]), "locale": LOC},
            "structure_explanation": loc(pt=SL.get((sid, "structure_explanation")), en=SLen.get((sid, "structure_explanation"))),
            "tags": jloads(s["tags"]), "new_items": jloads(s["new_items"]),
            # Roadmap F (migration 007). `pattern` is Layer B and wholly mechanical -- chunks from the
            # token array, roles from the (particle, function_type) pair closing each chunk, so it is
            # regenerable and carries no judgement. `clause_structure` is Layer C: one closed-enum value
            # judged from the Japanese, which is why it is a sibling field and not folded into pattern.
            "pattern": jloads(s["pattern_json"]),
            "clause_structure": s["clause_structure"],
            "tokens": tokens, "particles": particles, "grammar": grammar,
        }
        records.append(rec)
        tr = SL.get((sid, "translation"))
        index_rows.append((s["slug"], s["jp"], tr, s["level"]))
    jw(CORPUS / "sentences" / "bank.json", records)
    lines = ["# Corpus — Dissected sentence bank", "",
             f"_Generated {build_date()}. Full §6 dissection. `translation` = "
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
        f"_Generated {build_date()} from `db/corpus.sqlite` (regenerable index). "
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


def _fill_link_caches(con: sqlite3.Connection) -> None:
    VOCAB_SLUG_BY_ID.clear()
    for vid, slug in con.execute("SELECT id, slug FROM vocab"):
        VOCAB_SLUG_BY_ID[vid] = slug
    FAMILY_OF.clear()
    FAMILY_OF.update(family_backlinks(con))


def main() -> int:
    global LEDGER
    # A malformed ledger raises rather than exporting a partial set of approvals: an export that
    # silently drops the entries it could not parse claims fewer reviews than a teacher made.
    LEDGER = Ledger.load(ROOT)
    con = sqlite3.connect(DB)
    _fill_link_caches(con)
    kc = export_kanji(con)
    vc = export_vocab(con)
    gc = export_grammar(con)
    fc = export_families(con)
    sc = export_sentences(con)
    write_corpus_index(kc, vc, gc, fc, sc)
    con.close()
    print(f"exported kanji={kc} vocab={vc} grammar={gc} families={fc} sentences={sc} -> corpus/")
    rep = LEDGER.report
    if rep.entries:
        print(f"review ledger: {rep.entries} entr(y/ies), {rep.live} live verdict(s) stamped onto "
              f"{rep.stamped_records} record(s), {rep.stale} STALE (rewritten after review, "
              f"exported as nothing)")
        for line in rep.stale_examples:
            print(f"  stale: {line}")
    else:
        print("review ledger: empty — no record carries a review_status yet (design/review_ledger.md)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
