#!/usr/bin/env python3
"""W37 — derive the provenance backfill table from the working index (read-only).

Writes `research/derived/repairs/provenance_backfill.json` with two sections:

  rows           what the export must publish for the ten W37 entities: one row per record
                 (`field: null` = the record root: layer / source / created_by / needs_review) and one
                 row per field whose layer differs from the root (`field_layers`, APP_PLAN D13).
                 Asserted by scripts/validate/validate_repairs_applied.py (handle_provenance_backfill).
  index_repairs  the four index writes that make the published values true and rebuild-reproducible
                 (research/reports/w37_provenance_report.md §7.3). Applied by
                 scripts/apply_provenance_backfill.py.

Nothing is authored. Record provenance is RECOVERED from the index columns (kanji, vocab, topic,
course_module), or is the builder's own declared contract (conjugations, kana, capabilities, the course
manifest); per-field layers are read from `localized_text.layer`. The one ruling it encodes is §6.1:
builder-literal pt-BR labels (kana family labels) are Layer C (owner sign-off pending, PENDING B-W37).

Run BEFORE the apply: afterwards `index_repairs` would read empty. Usage: derive_provenance_backfill.py
"""
from __future__ import annotations

import datetime as _dt
import json
import sqlite3
import sys
from collections import Counter
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
_SCRIPTS = next(p for p in Path(__file__).resolve().parents if p.name == "scripts")
sys.path.append(str(_SCRIPTS))
from dbtarget import db_target  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
DB = db_target(ROOT / "db" / "corpus.sqlite")
OUT = ROOT / "research" / "derived" / "repairs" / "provenance_backfill.json"
KV_LEVELS = ("n5", "n4", "n3", "n2", "n1")
PT = "pt-BR"


def main() -> int:
    con = sqlite3.connect(f"file:{DB}?mode=ro", uri=True)
    lt = {(e, i, f): lay for e, i, f, lay in con.execute(
        "SELECT entity_type, entity_id, field, layer FROM localized_text WHERE locale=?", (PT,))}
    rows: list[dict] = []
    repairs: list[dict] = []

    def rec(entity, rid, layer, source, created_by, needs_review=None):
        r = {"entity": entity, "id": rid, "field": None, "layer": layer, "source": source,
             "created_by": created_by}
        if needs_review is not None:
            r["needs_review"] = needs_review
        rows.append(r)

    def fld(entity, rid, field, layer, root):
        if layer and layer != root:
            rows.append({"entity": entity, "id": rid, "field": field, "layer": layer})

    # ---- kanji: KANJIDIC2 record (A); meanings B, example glosses B (copy), notes C -------------
    ph = ",".join("?" * len(KV_LEVELS))
    note_layer = dict(con.execute(
        "SELECT kr.kanji_id, MIN(l.layer) FROM kanji_reading kr JOIN localized_text l ON "
        "l.entity_type='kanji_reading' AND l.entity_id=kr.id AND l.field='note' AND l.locale=? "
        "GROUP BY kr.kanji_id", (PT,)))
    glossed = {k for (k,) in con.execute(
        "SELECT DISTINCT vk.kanji_id FROM vocab_kanji vk JOIN vocab_sense s ON s.vocab_id=vk.vocab_id")}
    for kid, slug, src, by, layer in con.execute(
            f"SELECT id,slug,source,created_by,layer FROM kanji WHERE level IN ({ph}) ORDER BY slug", KV_LEVELS):
        want_by = "dataset" if layer == "A" and (src or "").startswith("kanjidic2:") else by
        if want_by != by:
            repairs.append({"kind": "kanji.created_by", "slug": slug, "from": by, "to": want_by,
                            "why": "Layer-A KANJIDIC2 record stamped by the pt-BR meanings campaign "
                                   "(19cf804a); the AI claim belongs to field_layers.meanings"})
        irr = lt.get(("kanji", kid, "irregular_note"))
        rec("kanji", slug, layer, src, want_by, needs_review=irr is not None)
        fld("kanji", slug, "meanings", lt.get(("kanji", kid, "meanings")), layer)
        fld("kanji", slug, "example_words[].gloss", "B" if kid in glossed else None, layer)
        fld("kanji", slug, "readings[].note", note_layer.get(kid), layer)
        fld("kanji", slug, "irregular_note", irr, layer)

    # ---- vocab: JMdict record (A); glosses and the one note B -----------------------------------
    gloss_layer = dict(con.execute(
        "SELECT s.vocab_id, MIN(l.layer) FROM vocab_sense s JOIN localized_text l ON "
        "l.entity_type='vocab_sense' AND l.entity_id=s.id AND l.field='gloss' AND l.locale=? "
        "GROUP BY s.vocab_id", (PT,)))
    for vid, slug, jref, src, by, layer in con.execute(
            f"SELECT id,slug,jmdict_ref,source,created_by,layer FROM vocab WHERE level IN ({ph}) "
            f"ORDER BY slug", KV_LEVELS):
        want_src = f"jmdict:{jref}" if jref else src
        if want_src != src:
            repairs.append({"kind": "vocab.source", "slug": slug, "from": src, "to": want_src,
                            "why": "source still names the JMdict entry the record was re-pointed away "
                                   "from (modernize_nurse_term.py, fixed there too)"})
        rec("vocab", slug, layer, want_src, by)
        fld("vocab", slug, "senses[].gloss", gloss_layer.get(vid), layer)
        fld("vocab", slug, "notes", lt.get(("vocab", vid, "notes")), layer)

    # ---- builder-declared records --------------------------------------------------------------
    for f in sorted((ROOT / "corpus" / "conjugations").glob("n[0-9].json")):
        for r in json.loads(f.read_text(encoding="utf-8")):
            rec("conjugation", r["slug"], "A", "derived:conjugation-rules", "script")
    for (kid,) in con.execute("SELECT id FROM kana ORDER BY id"):
        rec("kana", kid, "A", "unicode-gojuon", "script", needs_review=True)
        fld("kana", kid, "family_label", "C", "A")
    for (fid,) in con.execute("SELECT id FROM kana_family ORDER BY id"):
        rec("kana_family", fid, "A", "unicode-gojuon", "script", needs_review=True)
        fld("kana_family", fid, "label", "C", "A")
    caps = json.loads((ROOT / "corpus" / "capabilities" / "registry.json").read_text(encoding="utf-8"))
    for c in sorted(caps, key=lambda c: c["id"]):
        rec("capability", c["id"], "C", "capability-registry", "ai", needs_review=True)

    # ---- courseware placement records: recovered from the index --------------------------------
    for tid, slug, src, by, layer, nr in con.execute(
            "SELECT t.id,t.slug,t.source,t.created_by,t.layer,t.needs_review FROM topic t "
            "WHERE EXISTS (SELECT 1 FROM lesson l WHERE l.topic_id=t.id) ORDER BY t.slug"):
        rec("topic", slug, layer, src, by, needs_review=bool(nr))
    for mid, slug, src, by, layer, nr in con.execute(
            "SELECT id,slug,source,created_by,layer,needs_review FROM course_module ORDER BY ord"):
        rec("course", slug, layer, src, by, needs_review=bool(nr))
    rec("course_manifest", "course/manifest.json", "C", "derived:course-chain", "script", needs_review=True)

    # ---- index repair: NULL localized_text.layer on the placement records ----------------------
    for etype, table in (("topic", "topic"), ("course_module", "course_module")):
        for slug, field, layer in con.execute(
                f"SELECT r.slug, l.field, r.layer FROM localized_text l JOIN {table} r ON r.id=l.entity_id "
                f"WHERE l.entity_type=? AND l.locale=? AND l.layer IS NULL ORDER BY r.slug, l.field",
                (etype, PT)):
            repairs.append({"kind": "localized_text.layer", "entity_type": etype, "slug": slug,
                            "field": field, "from": None, "to": layer,
                            "why": "per-field layer never stored; inherits the record's own layer"})

    # ---- index repair: a reading flag with no note to review ----------------------------------
    for slug, reading, rtype, n in con.execute(
            "SELECT k.slug, kr.reading, kr.reading_type, COUNT(*) FROM kanji_reading kr "
            "JOIN kanji k ON k.id=kr.kanji_id WHERE kr.needs_review=1 AND NOT EXISTS "
            "(SELECT 1 FROM localized_text l WHERE l.entity_type='kanji_reading' AND l.entity_id=kr.id "
            " AND l.field='note') GROUP BY 1,2,3 ORDER BY 1,2,3"):
        repairs.append({"kind": "kanji_reading.needs_review", "slug": slug, "reading": reading,
                        "reading_type": rtype, "rows": n, "from": 1, "to": 0,
                        "why": "the flag means 'this reading note is unreviewed' "
                               "(merge_kanji_reading_notes.py); the note is gone"})

    doc = {
        "unit": "W37", "generated": _dt.date.today().isoformat(),
        "generator": "scripts/derive_provenance_backfill.py",
        "report": "research/reports/w37_w40_apply_report.md",
        "what_this_is": "rows: the provenance the export publishes for the ten W37 entities (field null = "
                        "record root; a field row = a field_layers entry, present only where the field's "
                        "layer differs from the root's). index_repairs: the index writes behind it.",
        "rulings": {"builder-literal-label": "kana family labels are Layer C (W37 report §6.1); owner "
                                             "sign-off pending as PENDING B-W37",
                    "exempt": {"review_ledger": "an approval sidecar, not corpus content",
                               "capability_lesson_map": "a join of two records that both carry provenance"}},
        "counts": {"rows": len(rows),
                   "by_entity": dict(sorted(Counter(r["entity"] for r in rows).items())),
                   "field_rows": dict(sorted(Counter(f"{r['entity']}.{r['field']}" for r in rows
                                                     if r["field"]).items())),
                   "index_repairs": dict(sorted(Counter(r["kind"] for r in repairs).items()))},
        "index_repairs": repairs,
        "rows": rows,
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    body = ",\n".join(json.dumps(r, ensure_ascii=False, separators=(",", ":")) for r in rows)
    head = json.dumps({k: v for k, v in doc.items() if k != "rows"}, ensure_ascii=False, indent=1)
    OUT.write_text(head[:-2] + ',\n "rows": [\n' + body + "\n]}\n", encoding="utf-8")
    assert json.loads(OUT.read_text(encoding="utf-8"))["rows"] == rows
    print(json.dumps(doc["counts"], ensure_ascii=False, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
