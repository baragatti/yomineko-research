#!/usr/bin/env python3
"""Build the W15 tracked table: which authored passages replace which reading box, and which are HELD.

WHAT THIS IS
------------
`corpus/readings/*.json` holds 286 in-lesson reading boxes. Every one of them was ASSEMBLED by
`scripts/ingest/build_readings.py` by concatenating i+0 sentences out of the bank, which is why
`read:n5-adjetivos-04-01` reads "どこに行くところですか。ありがとうございます！" — two unrelated
Tatoeba sentences glued together and called a passage (APP_PLAN W15, "A1 real passages").

The W15 campaign authored a real 3-6 sentence passage for each of those 286 slugs, verified them,
and left them under `research/derived/passages/`. This script decides, mechanically, which of them
can be applied — every kanji and every content word already inside the gating lesson's exported
`cumulative_known_set`, `max_new = 0` — and writes the result as an exact-match repair table.

THE DECISION IS THE GATE, NOT AN OPINION
----------------------------------------
The known-set check is `scripts/ingest/known_set.py`, which carries the W15 dissector rule (a surface
the known set contains must not resolve to an unknown lemma — the ください -> 下さる trap). A passage
that still fails after that rule fails for a COURSE-DATA reason: the gating lesson's own grammar
target is built on a word the lesson never unlocks. Those are HELD, never rewritten, and the table
names the missing unlock so W21b can move it.

WHICH FILE WINS
---------------
298 files, 286 slugs: twelve slugs also have a `read-<slug>.json` copy from the campaign's first
pilot batch (all written 2026-09-02 03:07, all superseded that afternoon by the run that produced
the unprefixed files). The unprefixed file is the campaign output of record and is the one used; the
pilot copies are recorded in the table as `superseded_pilots` so the choice is auditable rather than
implicit in a glob order.

OUTPUT: research/derived/repairs/reading_passages.json
  rows[]   one per applicable passage: {slug, lesson, level, source_file, old:{jp}, new:{…}, why}
  held[]   one per passage that cannot pass, with the reason and the missing unlock named
`new.uses` is in PUBLISHED SLUG SPACE (kanji:<char> / vocab:<jmdict_id>) so the row can be replayed
against the export by `validate_repairs_applied.py` and read by a human. The token stream is NOT in
the table: it is re-derived deterministically from `new.jp` by the applier (SudachiPy mode C), and
the applier asserts the tokens re-concatenate to `jp`.

Usage: build_reading_passage_table.py [--out PATH]
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(ROOT / "scripts" / "ingest"))
from known_set import PassageGate, load_known_sets                       # noqa: E402

PASSAGES = ROOT / "research" / "derived" / "passages"
READINGS = ROOT / "corpus" / "readings"
OUT = ROOT / "research" / "derived" / "repairs" / "reading_passages.json"
SOURCE = "authored:w15-passages"          # Layer-C provenance for an applied passage
SOURCE_HELD = "selection:sentence-bank"   # what an unreplaced box has always been
EM = re.compile(r"—")


def band(n: int) -> str:
    return "short" if n <= 2 else ("paragraph" if n <= 5 else "long")


def pick_files() -> tuple[dict[str, Path], list[str]]:
    """slug -> the campaign file of record; plus the superseded pilot copies, named."""
    chosen: dict[str, Path] = {}
    pilots: list[str] = []
    for f in sorted(PASSAGES.glob("*.json")):
        d = json.loads(f.read_text(encoding="utf-8"))
        if f.name.startswith("read-"):
            pilots.append(f.name)
            continue
        chosen[d["slug"]] = f
    return chosen, pilots


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=str(OUT))
    args = ap.parse_args()

    current = {}
    for lf in sorted(READINGS.glob("n*.json")):
        for r in json.loads(lf.read_text(encoding="utf-8")):
            current[r["slug"]] = r
    known = load_known_sets(ROOT)
    gate = PassageGate()

    files, pilots = pick_files()
    rows, held = [], []
    rescued_total = 0
    for slug in sorted(files):
        f = files[slug]
        d = json.loads(f.read_text(encoding="utf-8"))
        cur = current.get(slug)
        lesson = d.get("lesson")
        problems: list[str] = []
        missing: list[dict] = []
        if cur is None:
            problems.append("no reading box carries this slug")
        elif cur["gated_to_lesson"] != lesson:
            problems.append(f"passage says {lesson}, the box is gated to {cur['gated_to_lesson']}")
        if lesson not in known:
            problems.append(f"gating lesson {lesson} is not an exported lesson")

        sents = d.get("jp_sentences") or []
        jp = d.get("jp") or ""
        if "".join(sents) != jp:
            problems.append("jp != ''.join(jp_sentences)")
        if not 3 <= len(sents) <= 6:
            problems.append(f"{len(sents)} sentences (the W15 contract is 3-6)")
        tpt = (d.get("translation_pt") or "").strip()
        ten = (d.get("translation_en") or "").strip()
        if not tpt:
            problems.append("no pt-BR translation")
        if not ten:
            problems.append("no en translation")
        if EM.search(jp + tpt + (d.get("title_pt") or "")):
            problems.append("em dash in learner-facing text")

        res = None
        if lesson in known and not problems:
            res = gate.analyse(jp, known[lesson])
            rescued_total += len(res.rescued)
            for ch in res.unknown_kanji:
                missing.append({"kind": "kanji", "ref": f"kanji:{ch}"})
            for u in res.unknown_vocab:
                missing.append({"kind": "vocab", "ref": u["slug"], "headword": u["headword"],
                                "level": u["level"], "surface": u["surface"], "lemma": u["lemma"]})
            if missing:
                problems.append(f"{len(missing)} item(s) outside the gating lesson's known set")

        if problems:
            held.append({"slug": slug, "lesson": lesson, "level": d.get("level"),
                         "source_file": f.name, "reasons": problems, "missing_unlocks": missing,
                         "first_sentence": sents[0] if sents else ""})
            continue

        assert res is not None
        rows.append({
            "slug": slug,
            "lesson": lesson,
            "level": d["level"],
            "source_file": f.name,
            "old": {"jp": cur["jp"]},
            "new": {
                "jp": jp,
                "jp_sentences": sents,
                "title_pt": d.get("title_pt") or "Leitura",
                "title_en": d.get("title_en") or "Reading",
                "translation_pt": tpt,
                "translation_en": ten,
                "length_band": band(len(sents)),
                # Published space, exactly as `export_readings.py` emits it: bare characters for
                # kanji, `vocab:<jmdict_id>` slugs for vocab. The row is replayed against the export
                # by validate_repairs_applied.py, so it has to speak the export's own space.
                "uses": {
                    "kanji": sorted({c for c in jp if c in gate.kid_by_char} & set(known[lesson].kanji)),
                    "vocab": sorted(gate.slug_by_vid[v] for v in res.uses_vocab_ids),
                },
                "source_slugs": [],
                "ai_generated": True,
                "needs_review": True,
                "layer": "C",
                "source": SOURCE,
            },
            "why": ("W15: the box held a concatenation of unrelated bank sentences; this is the "
                    "authored, verified, known-set-gated passage for the same slug"),
            "rescued_by_surface_rule": res.rescued,
            "rescued_by_run_rule": res.rescued_runs,
            "carve_out": res.carve_out,
        })

    doc = {
        "table": "reading_passages",
        "unit": "W15",
        "what": ("Real Layer-C reading passages replacing the concatenated selection in "
                 "corpus/readings. Applier: scripts/apply_reading_passages.py. `new.uses` is a "
                 "SNAPSHOT of what this passage's own SudachiPy mode-C tokenisation resolved to at "
                 "apply time, in published slug space -- not a recompute from sentence_kanji / "
                 "sentence_vocab, which grow with every later dissection pass."),
        "known_set_rule": ("scripts/ingest/known_set.py: max_new=0 against the gating lesson's "
                           "EXPORTED cumulative_known_set, with the W15 surface rule (a surface the "
                           "known set contains never resolves to an unknown lemma)."),
        "held_are_not_rewritten": ("A passage that cannot pass is HELD. Every held row names the "
                                   "unlock its gating lesson is missing; that is W21b's work, not a "
                                   "rewrite of verified Layer-C text."),
        "superseded_pilots": pilots,
        "counts": {
            "passages_on_disk": len(files),
            "applicable": len(rows),
            "held": len(held),
            "lessons_touched": len({r["lesson"] for r in rows}),
            "rescued_tokens_by_surface_rule": rescued_total,
            "rescued_passages_by_surface_rule": len([r for r in rows if r["rescued_by_surface_rule"]]),
            "rescued_tokens_by_run_rule": sum(len(r["rescued_by_run_rule"]) for r in rows),
            "rescued_passages_by_run_rule": len([r for r in rows if r["rescued_by_run_rule"]]),
            "carve_out_tokens": sum(len(r["carve_out"]) for r in rows),
        },
        "row_count": len(rows),
        "rows": rows,
        "held": held,
    }
    Path(args.out).write_text(json.dumps(doc, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(json.dumps(doc["counts"], ensure_ascii=False, indent=1))
    print(f"-> {args.out}")
    for h in held:
        print(f"  HELD {h['slug']} ({h['lesson']}): {'; '.join(h['reasons'])}")
        for m in h["missing_unlocks"][:6]:
            print(f"       missing {m['kind']} {m['ref']}"
                  + (f" {m.get('headword','')} [{m.get('level','')}] seen as {m.get('surface','')}"
                     if m["kind"] == "vocab" else ""))
    return 0


if __name__ == "__main__":
    sys.exit(main())
