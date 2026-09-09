#!/usr/bin/env python3
"""Export the `reading` table (in-lesson reading-practice boxes — design/reading_practice.md) to durable corpus
JSON, split by level. Readings are assembled by SELECTION from the verified sentence bank (real Tatoeba/JEC text,
human EN, our re-authored pt-BR, dissected); each is i+0 for the lesson it is gated to (every kanji + content
vocab already in that lesson's cumulative_known_set). Shape per box:
  {slug, level, gated_to_lesson, title:{pt-BR,en}, jp, tokens:[{s,r,ro,pos}…],
   translation:{pt-BR,en}, length_band, uses:{kanji:[char…],vocab:[vocab:<jmdict_id>…]}, source_slugs:[sent:…],
   ai_generated, needs_review, layer}
Re-run after build_readings.py. Usage: export_readings.py"""
from __future__ import annotations
import json, sqlite3, sys
from pathlib import Path
sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
# W01: honour --db / $YOMINEKO_DB so a rebuild can target a scratch DB (scripts/dbtarget.py).
import sys as _sys, pathlib as _pl  # noqa: E402
_sys.path.append(str(next(p for p in _pl.Path(__file__).resolve().parents if p.name == "scripts")))
from dbtarget import db_target, out_root  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
DB = db_target(ROOT / "db" / "corpus.sqlite")
OUT = out_root(ROOT) / "corpus" / "readings"


INDEX_HEAD = (
    "# corpus/readings — in-lesson reading-practice boxes (our format)\n"
    "\n"
    "Short reading passages attached to lessons. Two provenances live here and every record says which it is in `source`:\n"
    "\n"
    "- **`authored:w15-passages`** (Layer **C**, `ai_generated: true`, `needs_review: true`) — a 3–6 sentence passage written for that lesson, independently verified, gated to the lesson's known set, and coherent as a text. APP_PLAN W15. These replaced the assembled boxes, which read as a pile of unrelated true sentences rather than a text.\n"
    "- **`selection:sentence-bank`** (Layer **B**) — the historical assembly by SELECTION from the verified bank (real **Tatoeba (CC BY 2.0 FR)** / **JEC (CC BY 3.0)** Japanese, human EN, our re-authored pt-BR, fully dissected). A box still carrying this is one W15 HELD: its authored passage needs an unlock its gating lesson does not have yet (W21b).\n"
    "\n"
    "Every box is **i+0** for the lesson it is gated to — every kanji and content word it uses is already in that lesson's `cumulative_known_set` (HARD gate, `scripts/validate/validate_readings.py`); `scripts/validate/validate_reading_coherence.py` adds the coherence checks (one topic, tense / pronoun / register continuity). See `design/reading_practice.md`.\n"
    "\n"
    "Per box: `{slug, level, gated_to_lesson, title, jp, sentences:[…], tokens:[{s,r,ro,pos}], translation:{pt-BR,en}, length_band, uses:{kanji,vocab}, source_slugs:[sent:…], source, comprehension?}`.\n"
    "\n"
    "`sentences` is the box's own segmentation, concatenating exactly to `jp` — stored rather than re-derived because a quoted dialogue terminates every line inside 「…。」 (a plain split on 。 yields one unit for a six-line exchange) and `design/translation_style.md` §3 drops the final 。 on generated Japanese. An authored box carries the segmentation its author wrote; a selection-era box carries the split of its own `jp`.\n"
    "\n"
    "`uses` is a **SNAPSHOT**, not a live projection: it records what this passage's own SudachiPy mode-C tokenisation resolved to at the moment it was applied, in published slug space (`vocab:<jmdict_id>`, never headwords — 93 headwords name more than one record). It is deliberately NOT recomputed from `sentence_kanji` / `sentence_vocab`: those link tables grow with every later dissection pass, and a recompute would push already-gated boxes out of their lesson's known set. Only records the gating lesson already teaches are credited, so `uses` is inside the known set by construction.\n"
    "\n"
    "`comprehension` names the box's own 内容一致 question in `corpus/exam_banks/<level>_reading_comp.json` (`item`). The question STRING is not copied here — the bank is its single source. `about_current_text` says whether that question was authored against the text this box prints now; the question and its options are resolved into this file only when it is true, and W18 regenerating the bank over the new passages flips the rest with no second apply.\n"
    "\n"
    "`source_slugs` credit the underlying bank sentences of a selection-era box (provenance).\n"
    "\n"
)


def main() -> int:
    con = sqlite3.connect(DB)
    if not con.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='reading'").fetchone():
        print("export_readings: no reading table (run build_readings.py first) — nothing to export")
        return 0
    OUT.mkdir(parents=True, exist_ok=True)
    char_by_kid = {i: ch for i, ch in con.execute("SELECT id,character FROM kanji")}
    # The DB stores uses.vocab as vocab ROW IDS -- the exact records, no ambiguity. The old export
    # collapsed them to headwords, which re-introduced the very homograph problem the course layer
    # was migrated away from (6,200 refs, 558 of them naming more than one record). Publish the slug.
    slug_by_vid = {i: sl for i, sl in con.execute("SELECT id,slug FROM vocab")}
    by_level: dict = {}
    # W15: the comprehension question is NOT stored on the reading. It lives once, in the authored
    # exam bank, and `reading.comprehension` holds only the pointer plus `about_current_text` — the
    # flag that says whether that question was written against the text this box currently prints.
    # Resolving it here means W18's regeneration reaches the in-lesson box with no second apply, and
    # a question about a passage that no longer exists is never published as if it still applied.
    rc = {}
    for bf in sorted((ROOT / "corpus" / "exam_banks").glob("*_reading_comp.json")):
        for it in json.loads(bf.read_text(encoding="utf-8")):
            if it.get("reading"):
                rc[it["reading"]] = it
    for (slug, level, lesson, tpt_title, ten_title, jp, tokens, tpt, ten, uses, band, src, ai, nr,
         layer, source, comp, sents) in con.execute(
            "SELECT slug,level,gated_to_lesson,title_pt,title_en,jp,tokens,translation_pt,translation_en,uses,"
            "length_band,source_slugs,ai_generated,needs_review,layer,source,comprehension,sentences "
            "FROM reading ORDER BY gated_to_lesson,slug"):
        u = json.loads(uses or "{}")
        c = json.loads(comp or "null")
        comprehension = None
        if c and c.get("item"):
            comprehension = {"item": c["item"], "about_current_text": bool(c.get("about_current_text"))}
            item = rc.get(slug)
            if comprehension["about_current_text"] and item:
                comprehension.update({"question": item["question"], "correct": item["correct"],
                                      "options": sorted([item["correct"], *item["distractors"]])})
        by_level.setdefault(level, []).append({
            "slug": slug, "level": level, "gated_to_lesson": lesson,
            "title": {"pt-BR": tpt_title or "Leitura", "en": ten_title or "Reading"},
            "jp": jp, "sentences": json.loads(sents or "[]"),
            "tokens": json.loads(tokens or "[]"),
            "translation": {"pt-BR": tpt or "", "en": ten or ""},
            "length_band": band,
            "uses": {"kanji": [char_by_kid[k] for k in u.get("kanji", []) if k in char_by_kid],
                     "vocab": [slug_by_vid[v] for v in u.get("vocab", []) if v in slug_by_vid]},
            "source_slugs": json.loads(src or "[]"),
            "ai_generated": bool(ai), "needs_review": True if nr is None else bool(nr),
            "layer": layer or "B", "source": source or "selection:sentence-bank",
            **({"comprehension": comprehension} if comprehension else {})})
    counts = {}
    for lvl, items in by_level.items():
        (OUT / f"{lvl}.json").write_text(json.dumps(items, ensure_ascii=False), encoding="utf-8")
        counts[lvl] = len(items)
    (OUT / "INDEX.md").write_text(
        INDEX_HEAD + "".join(f"- `{lvl}.json` \u2014 {n} boxes\n"
                              for lvl, n in sorted(counts.items())),
        encoding="utf-8")
    con.close()
    print(f"exported readings -> corpus/readings/  {counts}  (total {sum(counts.values())})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
