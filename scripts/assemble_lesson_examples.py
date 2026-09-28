#!/usr/bin/env python3
"""Q5-lesson-examples. Fold the verified W14-residue table into rows the W14 applier can apply.

INPUTS (research/derived/pending/, both stay there)
  lesson_examples_gap.json          the W14 residue, worked: picks for the 14 N5/N4 lessons that render
                                    no sentence, and a fix for each of the 154 held links
  lesson_examples_gap.verdict.json  the independent verifier, keyed by the row's identity
                                    (`pick|lesson|slug`, `lesson|lesson`, `held|lesson|slug`)

WHAT LANDS, and only under a verdict (ok -> as written, ok false -> the verifier's `corrected`; a
missing verdict refuses the row, never accepts it):
  add      a lesson's verified picks that are ALREADY BANK SENTENCES and pass today's W14 rule
           (derive_lesson_sentences.py: level <= lesson, i+0 load, build_vocab_exercises.sentence_ok,
           model-text register, not already rendered, picked once), as a `Mais exemplos` block
           before the lesson's practice anchor (the table's own proposed_markup).
  remove   a held link whose verified fix is `remove`, when the tag is unique and the lesson keeps
           another sentence.
  replace  a held link whose verified fix swaps it for a bank sentence that passes the same rule.

WHAT DOES NOT LAND (the `residue` section, each with its reason): picks that are not in the bank
(raw Tatoeba or generated: a dissection plus a full-tier Layer-B is owed first, see
scripts/derive_lesson_examples_layerb.py), bank picks the rule refuses today (a verified `needs_fix`
link repair comes first), link repairs (relink / unlock / regrade / recompute level: the link lane's),
and the keep-with-gloss rows (the gloss has no markup on a sentence card yet).

A held link an SRS card of its lesson cites as its example (W28) is never removed or swapped here:
the card may cite a sentence above the lesson only because the lesson renders it
(validate_card_content check F), so the card example is re-derived first.

Reads the EXPORTED tree, so it runs BEFORE the apply; it refuses to overwrite the applied ledger.
Deterministic. Writes research/derived/repairs/lesson_examples.json.
Usage: assemble_lesson_examples.py [--out PATH] [--force]
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "scripts" / "validate"))
import build_vocab_exercises as bve  # noqa: E402
import derive_lesson_sentences as dls  # noqa: E402  (the W14 rule: fit, anchors, heading)
import derive_needs  # noqa: E402

PENDING = ROOT / "research" / "derived" / "pending"
GAP = PENDING / "lesson_examples_gap.json"
VERDICT = PENDING / "lesson_examples_gap.verdict.json"
OUT = ROOT / "research" / "derived" / "repairs" / "lesson_examples.json"


def verdict_of(verdicts: dict, key: str) -> dict:
    v = verdicts.get(key)
    if not v or v.get("ok") is None:
        raise SystemExit(f"no verdict for {key}: an unverified row is never merged")
    return v


def pick_slug(p: dict) -> str:
    if p.get("slug"):
        return p["slug"]
    if p.get("generated_key"):
        return p["generated_key"]
    if p.get("slug_after_ingest"):
        return p["slug_after_ingest"]
    return f"sent:tatoeba-{p['tatoeba_id']}"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", type=Path, default=OUT)
    ap.add_argument("--force", action="store_true", help="overwrite the applied ledger")
    args = ap.parse_args()
    root = ROOT
    gap = json.loads(GAP.read_text(encoding="utf-8"))
    verdicts = json.loads(VERDICT.read_text(encoding="utf-8"))

    rows = bve.load_lessons(root)
    bve.SENT_REFS.update(derive_needs.load_sentence_index(root))
    by_slug, _bv, _bg, need, _att = bve.index_bank(root)
    kanji_chars = {k["character"] for kf in sorted(root.glob("corpus/kanji/*.json"))
                   for k in json.loads(kf.read_text(encoding="utf-8"))}
    vid2slug: dict[int, str] = {}
    for vf in sorted(root.glob("corpus/vocab/*.json")):
        for v in json.loads(vf.read_text(encoding="utf-8")):
            vid2slug[v["id"]] = v["slug"]
    row_of = {r["lesson"]["id"]: r for r in rows}
    taken: set[str] = set()

    def card_examples(node) -> set[str]:
        """Sentences the lesson's SRS cards cite as their example (W28): the card may cite a
        sentence above the lesson only because the lesson renders it (validate_card_content F)."""
        out: set[str] = set()
        if isinstance(node, dict):
            ex = node.get("example")
            if isinstance(ex, dict) and isinstance(ex.get("sentence"), str):
                out.add(ex["sentence"])
            for v in node.values():
                out |= card_examples(v)
        elif isinstance(node, list):
            for v in node:
                out |= card_examples(v)
        return out

    def rule(slug: str, row: dict) -> str | None:
        """None when the sentence may be shown in the lesson today, else why not."""
        s = by_slug.get(slug)
        if s is None:
            return "not in the bank"
        if slug in taken:
            return "already picked by another row of this table"
        if slug in row["rendered"]:
            return "the lesson already renders it (body or exercise)"
        if s.get("register") not in dls.SHOWABLE_REGISTERS:
            return f"register {s.get('register')!r} is not model text"
        above, load = dls.fit(s, row["lesson"], kanji_chars, vid2slug)
        if above:
            return f"graded {s.get('level')}, above the lesson"
        if load:
            return f"i+{load} at the lesson's known set"
        if not bve.sentence_ok(slug, row, need):
            return "build_vocab_exercises.sentence_ok refuses it (unknown item or forward reference)"
        return None

    table: list[dict] = []
    residue: list[dict] = []
    stats: Counter = Counter()

    # ---- the zero-sentence lessons ----------------------------------------------------------------
    for L in gap["lessons"]:
        lid = L["lesson"]
        row = row_of.get(lid)
        if row is None:
            raise SystemExit(f"{lid}: not in the exported course")
        final: list[tuple[dict, str]] = []
        for p in L["picks"]:
            v = verdict_of(verdicts, f"pick|{lid}|{pick_slug(p)}")
            final.append((p, "ok") if v["ok"] else (v["corrected"], "verifier-corrected"))
        lv = verdicts.get(f"lesson|{lid}")
        if lv and not lv["ok"] and (lv.get("corrected") or {}).get("add_pick"):
            final.append((lv["corrected"]["add_pick"], "verifier-added"))
        body = row["lesson"].get("body") or ""
        before = len(dls.SENT_TAG.findall(body))
        placed: list[str] = []
        for p, origin in final:
            slug = pick_slug(p)
            base = {"lesson": lid, "sentence": slug, "jp": p.get("jp"), "pt-BR": p.get("pt-BR"),
                    "source_kind": p.get("source_kind"), "origin": origin}
            if p.get("source_kind") != "bank":
                residue.append({**base, "kind": "needs-ingest",
                                "why": "not in the bank: a dissection and a full-tier Layer-B "
                                       "(gloss, particle explanations, translation_literal, "
                                       "structure paragraph) are owed before it can be linked",
                                "ingest_note": p.get("needs_ingest") or p.get("requires"),
                                "ai_generated": bool(p.get("ai_generated"))})
                stats["pick:needs-ingest"] += 1
                continue
            why = rule(slug, row)
            if why:
                residue.append({**base, "kind": "rule-refuses-today", "why": why,
                                "needs_fix": p.get("needs_fix")})
                stats["pick:held"] += 1
                continue
            taken.add(slug)
            placed.append(slug)
            stats["pick:applied"] += 1
        if placed:
            anchor = next((a for a in dls.ANCHORS if body.count(a) == 1), None)
            if anchor is None:
                raise SystemExit(f"{lid}: no unique anchor to place the block before")
            if before:
                raise SystemExit(f"{lid}: renders {before} sentence(s) today; the table was for "
                                 f"lessons rendering none")
            block = dls.HEADING + "\n" + "".join(
                f'<sentence ref="{s}" show="furigana" mode="card"/>\n' for s in placed) + "\n"
            table.append({"lesson": lid, "op": "add", "sentences": placed, "from": anchor,
                          "to": block + anchor, "source": "lesson_examples_gap.json (verified)"})

    # ---- the held links -------------------------------------------------------------------------
    for hl in gap["held_links"]:
        lid, slug = hl["lesson"], hl["sentence"]
        v = verdict_of(verdicts, f"held|{lid}|{slug}")
        cor = {} if v["ok"] else (v.get("corrected") or {})
        fix = cor.get("fix", hl["fix"])
        repl = cor["replacement"] if "replacement" in cor else hl.get("replacement")
        gloss = cor["gloss_pt"] if "gloss_pt" in cor else hl.get("gloss_pt")
        also = cor["also_fix"] if "also_fix" in cor else hl.get("also_fix")
        origin = "ok" if v["ok"] else "verifier-corrected"
        base = {"lesson": lid, "sentence": slug, "jp": hl["jp"], "fix": fix, "origin": origin}
        stats[f"held:{fix}"] += 1
        row = row_of.get(lid)
        body = (row["lesson"].get("body") or "") if row else ""
        tags = [m for m in dls.SENT_TAG.finditer(body) if m.group(1) == slug]
        if fix in ("remove", "replace") and row and slug in card_examples(row["lesson"]):
            residue.append({**base, "kind": "card-example", "replacement": repl,
                            "why": "an SRS card of this lesson cites it as its example (W28); the "
                                   "card example must be re-derived before the link can go"})
            continue
        if fix == "remove":
            others = [m for m in dls.SENT_TAG.finditer(body) if m.group(1) != slug]
            if len(tags) != 1 or not others:
                residue.append({**base, "kind": "held", "why": "tag not unique or the lesson would "
                                "render no sentence"})
                continue
            tag = tags[0].group(0)
            lit = tag + "\n" if body.count(tag + "\n") == 1 else tag
            table.append({"lesson": lid, "op": "remove", "sentence_out": slug, "from": lit,
                          "to": "", "source": "lesson_examples_gap.json held link (verified)"})
            stats["held:remove:applied"] += 1
            continue
        if fix == "replace":
            rslug = (repl or {}).get("slug")
            if not rslug:
                residue.append({**base, "kind": "needs-ingest", "replacement": repl,
                                "why": "the replacement is a new sentence: ingest + Layer-B owed"})
                continue
            why = rule(rslug, row) if row else "lesson not in the export"
            if why or len(tags) != 1:
                residue.append({**base, "kind": "rule-refuses-today", "replacement": repl,
                                "why": why or "old tag not unique",
                                "needs_fix": (repl or {}).get("needs_fix")})
                continue
            taken.add(rslug)
            tag = tags[0].group(0)
            table.append({"lesson": lid, "op": "replace", "sentence_out": slug, "sentence_in": rslug,
                          "from": tag, "to": tag.replace(f'ref="{slug}"', f'ref="{rslug}"'),
                          "source": "lesson_examples_gap.json held link (verified)"})
            stats["held:replace:applied"] += 1
            continue
        if fix in ("relink-token", "unlock-suru") or also:
            residue.append({**base, "kind": "link-lane", "also_fix": also,
                            "why": "a token / unlock / level repair, not a lesson edit"})
        if gloss:
            residue.append({**base, "kind": "gloss", "gloss_pt": gloss,
                            "why": "keep the link and show the gloss: no gloss markup exists for a "
                                   "sentence card yet (renderer/design call)"})

    residue_counts = Counter(r["kind"] for r in residue)
    doc = {
        "unit": "Q5-lesson-examples",
        "what_this_is": "The verified rows of research/derived/pending/lesson_examples_gap.json that a "
                        "lesson edit can carry today, as literal body substitutions for "
                        "scripts/apply_lesson_sentences.py --table (the W14 applier). Bank sentences "
                        "only; nothing authored here.",
        "generated_by": "scripts/assemble_lesson_examples.py",
        "rule": "derive_lesson_sentences.py (W14): level <= lesson, i+0 load, "
                "build_vocab_exercises.sentence_ok, model-text register, not already rendered, "
                "picked once; re-checked on today's export, not trusted from the table",
        "counts": {**dict(sorted(stats.items())), "rows": len(table),
                   "residue": dict(sorted(residue_counts.items()))},
        "residue_note": "Not rows: nothing here is applied. needs-ingest = the sentence is not in the "
                        "bank (pending/lesson_examples_layerb_derived.json has its mechanical Layer-B "
                        "and what is left to author); rule-refuses-today = a bank sentence the W14 rule "
                        "refuses on today's tree (its needs_fix, a link repair, comes first); link-lane "
                        "= token/unlock/level repairs; gloss = verified glosses with no markup to land in.",
        "residue": residue,
        "row_count": len(table),
        "rows": table,
    }
    if args.out == OUT and OUT.exists() and not args.force:
        # after the apply the tree already renders these rows, so a re-run would derive a different
        # (smaller) table and erase the ledger the replay reads
        raise SystemExit(f"{OUT.name} exists; it is the applied ledger. Use --out or --force.")
    args.out.write_text(json.dumps(doc, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(doc["counts"], ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
