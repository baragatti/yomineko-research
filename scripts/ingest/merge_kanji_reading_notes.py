#!/usr/bin/env python3
"""Merge the per-reading grouping + pt-BR notes into the corpus. Roadmap item D, final step.

Inputs, both produced upstream and already reviewed:
  research/derived/kanji_reading_groups.json   step 1, mechanical: which example words use which reading
  research/derived/kanji_reading_notes/        step 2, authored: one pt-BR note per reading

Writes two things into the DB, then the exporter surfaces them:
  kanji_reading.example_vocab_ids   the grouped compounds' vocab ids. The column already existed and was
                                    almost entirely null; this is what fills it.
  localized_text(kanji_reading, note, pt-BR)   the note. Layer C, needs_review, because it is pedagogy.
  localized_text(kanji, irregular_note, pt-BR) one line about the 熟字訓 that belong to no reading.

Joining is on (kanji_id, reading, okurigana) — okurigana is part of the key, not decoration. Without it
生.きる, 生.かす and 生.ける are the same row and the note lands on whichever comes first.

REFUSALS, so a bad authoring batch cannot reach the corpus:
  * a note whose (reading, okurigana) has no matching kanji_reading row is dropped, not guessed at;
  * a note is refused if it is instruction-shaped, contains an em dash, or contains no Latin letters at
    all (a pt-BR note that is pure kana is not a pt-BR note);
  * a note for a reading whose compounds list is EMPTY is still accepted, since those legitimately exist,
    but is counted separately so the ratio is visible.

Usage: merge_kanji_reading_notes.py [--apply]
"""
from __future__ import annotations
import argparse, glob, json, re, sqlite3, sys
from collections import Counter
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from reconcile_levels import derive_reading_tiers  # noqa: E402
sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
# W01: honour --db / $YOMINEKO_DB so a rebuild can target a scratch DB (scripts/dbtarget.py).
import sys as _sys, pathlib as _pl  # noqa: E402
_sys.path.append(str(next(p for p in _pl.Path(__file__).resolve().parents if p.name == "scripts")))
from dbtarget import db_target  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
DB = db_target(ROOT / "db" / "corpus.sqlite")
GROUPS = ROOT / "research" / "derived" / "kanji_reading_groups.json"
NOTES = ROOT / "research" / "derived" / "kanji_reading_notes"
INSTRUCTION = re.compile(
    r"^(replace|change|set|update|remove|delete|add|rewrite|trocar|corrigir|substituir)\b|->|→|"
    r"\bshould be\b|\bdeveria\b", re.I)
LATIN = re.compile(r"[A-Za-zÀ-ÿ]")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args()
    if not NOTES.exists():
        print(f"missing {NOTES.relative_to(ROOT)} — run the authoring pass first")
        return 1

    groups = {e["character"]: e for e in
              json.loads(GROUPS.read_text(encoding="utf-8"))["entries"]}
    authored: dict[str, dict] = {}
    for f in sorted(glob.glob(str(NOTES / "batch-*.json"))):
        for e in json.loads(Path(f).read_text(encoding="utf-8")).get("entries", []):
            authored[e["character"]] = e
    print(f"{len(groups)} kanji grouped, {len(authored)} authored")

    con = sqlite3.connect(DB)
    kid_of = {ch: i for i, ch in con.execute("SELECT id,character FROM kanji")}
    stats, dropped = Counter(), Counter()

    for ch, g in groups.items():
        kid = kid_of.get(ch)
        if kid is None:
            dropped["kanji not in registry"] += 1
            continue
        notes = {(r["reading"], r.get("okurigana") or ""): r
                 for r in (authored.get(ch) or {}).get("readings", [])}

        for r in g["readings"]:
            key = (r["reading"], r.get("okurigana") or "")
            row = con.execute(
                "SELECT id FROM kanji_reading WHERE kanji_id=? AND reading=? AND "
                "COALESCE(okurigana,'')=?", (kid, key[0], key[1])).fetchone()
            if not row:
                dropped["no kanji_reading row for that (reading, okurigana)"] += 1
                continue
            rid = row[0]

            ids = [c["vocab_id"] for c in r.get("compounds", []) if c.get("vocab_id")]
            if args.apply:
                con.execute("UPDATE kanji_reading SET example_vocab_ids=? WHERE id=?",
                            (json.dumps(ids, ensure_ascii=False) if ids else None, rid))
            if ids:
                stats["readings_with_compounds"] += 1

            note = (notes.get(key) or {}).get("note_pt") or ""
            if not note:
                dropped["no authored note"] += 1
                continue
            if INSTRUCTION.search(note) or "—" in note or not LATIN.search(note):
                dropped["note refused (instruction / em dash / no Latin text)"] += 1
                continue
            if args.apply:
                con.execute(
                    "INSERT OR REPLACE INTO localized_text "
                    "(entity_type,entity_id,field,locale,value,is_list,layer) "
                    "VALUES ('kanji_reading',?,'note','pt-BR',?,0,'C')", (rid, note))
            stats["notes_written"] += 1
            if not ids:
                stats["notes_on_empty_readings"] += 1

        irr = (authored.get(ch) or {}).get("irregular_note_pt") or ""
        if irr and g.get("irregular") and not INSTRUCTION.search(irr) and "—" not in irr:
            if args.apply:
                con.execute(
                    "INSERT OR REPLACE INTO localized_text "
                    "(entity_type,entity_id,field,locale,value,is_list,layer) "
                    "VALUES ('kanji',?,'irregular_note','pt-BR',?,0,'C')", (kid, irr))
            stats["irregular_notes"] += 1

    if args.apply:
        con.execute("UPDATE kanji_reading SET needs_review=1 WHERE id IN "
                    "(SELECT entity_id FROM localized_text WHERE entity_type='kanji_reading' "
                    "AND field='note')")
        con.commit()
        # `introduced_at_level` is documented as derived FROM the example vocab (design/schema_v2.md),
        # and the line above is where that vocab becomes final — so the tier is re-derived here rather
        # than left at whatever P2 could guess before any grouping existed.
        stats["tiers_derived"] = derive_reading_tiers(con)
    print(f"merge ({'APPLIED' if args.apply else 'dry-run'}): {dict(stats)}")
    if dropped:
        print(f"  dropped: {dict(dropped)}")
    con.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
