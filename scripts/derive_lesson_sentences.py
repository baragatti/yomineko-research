#!/usr/bin/env python3
"""W14. Re-select the example sentences lessons render, from the bank, by rule. Writes the table only.

WHY
---
The course renders sentence links the i+1 rule forbids and many lessons render none at all.
`validate_lesson_gating.py` check D froze the backlog (above-level links, over-budget links, links
carrying an unknown kanji or word) in `research/reports/lesson_sentence_baseline.json`; 116 of 322
lessons displayed no dissected sentence (readiness `jlpt_course_path.md` G9); the survival words of
the pre-N5 greetings topic were printed as bare `<jp>` text, so no word modal could open for them.
All three are selection problems over a bank of 10,209 sentences, so a script settles them and no
sentence or prose is authored.

THE RULE (one rule, the one the gates already use)
-------------------------------------------------
A sentence may be shown in lesson L when
  1. it is graded at or below L's level (check D's "above lesson level" test);
  2. `build_vocab_exercises.sentence_ok`: i+0 over both registries (every kanji in the text and
     every linked word inside L's cumulative_known_set, no unlinked content token) AND every item
     `derive_needs` expands from it is taught by L or earlier (check C5's forward-reference test,
     grammar tags included). i+0 rather than i+1 on purpose: check D ratchets the COUNT of links
     that carry any new kanji or word, so a new i+1 link would grow it;
  3. it carries at least one item L itself unlocks (vocab, kanji or grammar), so it exemplifies
     the lesson rather than merely fitting it;
  4. L does not already show it, and no other row of this table picked it;
  5. the bank labels its register as model text (SHOWABLE_REGISTERS).
Ranking among the survivors: most not-yet-covered unlocks of L first (greedy cover), then a sentence
nothing else references (the orphan sweep), then a real sentence over a generated one (spec 1.2),
then at least 5 characters long, then shorter, then a stable hash.

WHAT IT DERIVES
---------------
  replace  a link check D flags (above level, or over the level's i+1 budget) that sits in an
           EXAMPLE BLOCK (nothing but other sentence tags between it and a heading in
           SENTENCE_HEADINGS, and no prose right after it) is swapped in place for a sentence
           that passes the rule AND carries what the old one was there to show: a lesson unlock
           the old sentence carried, else one of the lesson's grammar points, else any of its
           unlocks. show/mode are kept.
  remove   the same, when nothing passes: the tag goes. A sentence heading left with nothing
           under it goes with it (drop-heading). Never when it would leave the lesson showing no
           sentence at all: those links are held as residue instead.
  residue  a flagged link that prose introduces or discusses ("nesta primeira, いや recebe
           だった:") is NOT touched: swapping it breaks the explanation and a script may not
           rewrite prose. Listed under `residue` for an authored pass.
  add      a lesson that renders no sentence gets up to 3, in a `Mais exemplos` block (the heading
           65 lessons already use, mode="card"), placed before its practice section.
  chip     pre-N5: a vocab unlock with no chip in its own lesson, printed exactly once as a list
           item `<item><jp>KANA</jp>`, becomes `<item><vocab ref="vocab:SLUG"/>`. The chip's
           visible text is the record's kana, so the rendered lesson reads the same.
Existing links that pass are never touched.

Reads the EXPORTED tree (course/, corpus/). Writes research/derived/repairs/lesson_sentences.json.
Deterministic. Usage: derive_lesson_sentences.py [--out PATH] [--force]
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "scripts" / "validate"))
import build_vocab_exercises as bve  # noqa: E402  (sentence_ok: the rule, imported not copied)
import derive_needs  # noqa: E402
import validate_lesson_gating as vlg  # noqa: E402  (course order, level order, budgets)

TABLE = ROOT / "research" / "derived" / "repairs" / "lesson_sentences.json"
SEED = "w14-lesson-sentences-2026-09-23"
MAX_ADD = 3
MIN_LEN = 5
HEADING = '<heading level="3"><text>Mais exemplos</text></heading>'
# headings whose only content is example sentences; one left empty by a removal is dropped
SENTENCE_HEADINGS = ("Mais exemplos", "Exemplos do banco", "Exemplos reais", "Frases reais")
ANCHORS = ('<heading level="3"><text>Hora de praticar</text></heading>',
           '<heading level="3"><text>Leitura</text></heading>', "<checklist>")
SENT_TAG = re.compile(r'<sentence\s+ref="([^"]+)"[^>]*/>')
CHIP_UNLOCK = re.compile(r'<vocab\b[^>]*\bref="([^"]+)"')
UNLOCK_KINDS = ("vocab", "kanji", "grammar")
# the bank's own register label; archaic / slang / vulgar / dialect / unlabelled are not model text
SHOWABLE_REGISTERS = ("neutral", "polite", "casual", "formal")


def h(*parts: str) -> str:
    return hashlib.sha256("|".join((SEED,) + parts).encode("utf-8")).hexdigest()[:12]


def referenced_elsewhere(root: Path) -> set[str]:
    """Every sentence slug some exported record points at, outside the bank itself."""
    rx = re.compile(r'"(sent:[^"\\]+)"|ref=\\?"(sent:[^"\\]+)')
    out: set[str] = set()
    for base in ("course", "corpus"):
        for p in (root / base).rglob("*.json"):
            if "sentences" in p.relative_to(root).parts[:2]:
                continue
            for a, b in rx.findall(p.read_text(encoding="utf-8")):
                out.add(a or b)
    return out


SENT_AT_END = re.compile(r'<sentence\s+ref="[^"]+"[^>]*/>$')
SENT_AT_START = re.compile(r'<sentence\s+ref="[^"]+"[^>]*/>')
HEADING_AT_END = re.compile(r'<heading level="\d"><text>([^<]*)</text></heading>$')


def in_example_block(body: str, start: int) -> bool:
    """True when nothing but other sentence tags stands between this tag and an example heading,
    i.e. no prose introduces this particular sentence."""
    prefix = body[:start].rstrip()
    while (m := SENT_AT_END.search(prefix)):
        prefix = prefix[:m.start()].rstrip()
    m = HEADING_AT_END.search(prefix)
    if not (m and m.group(1) in SENTENCE_HEADINGS):
        return False
    # ... and no prose right after it either ("molde puríssimo: o verbo 勉強する ..." explains it)
    rest = body[start:]
    while (m2 := SENT_AT_START.match(rest)):
        rest = rest[m2.end():].lstrip()
    return not rest or rest.startswith(("<heading", "<checklist", "<exercise", "<reading"))


def fit(s: dict, les: dict, kanji_chars: set[str], vid2slug: dict) -> tuple[bool, int]:
    """(above lesson level, i+1 load): check D's own arithmetic, for the report and the guard."""
    cks = les.get("cumulative_known_set") or {}
    known_k = {x.split(":", 1)[1] for x in cks.get("kanji") or []}
    known_v = set(cks.get("vocab") or [])
    llv, slv = les.get("level", "n5"), s.get("level", "n5")
    order = vlg.LEVEL_ORDER
    above = slv in order and llv in order and order.index(slv) > order.index(llv)
    new_k = {c for c in s["jp"] if c in kanji_chars and c not in known_k}
    new_v = set()
    for t in s.get("tokens") or []:
        if t.get("split_mode") != "C":
            continue
        slug = t.get("vocab") or vid2slug.get(t.get("vocab_id"))
        if slug and slug not in known_v:
            new_v.add(slug)
    return above, len(new_k) + len(new_v)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", help="write the table here instead (a dry run on the current tree)")
    ap.add_argument("--force", action="store_true", help="overwrite the applied ledger")
    args = ap.parse_args()
    root = ROOT

    rows = bve.load_lessons(root)                      # fills bve.INTRO_POS, course order
    bve.SENT_REFS.update(derive_needs.load_sentence_index(root))
    by_slug, _bv, _bg, need, _att = bve.index_bank(root)
    order_gate = [d["id"] for d in vlg.load_course(root)]
    if order_gate != [r["id"] for r in rows]:
        raise SystemExit("course order disagrees between the practice gate and the gating gate")
    kanji_chars = {k["character"] for kf in sorted(root.glob("corpus/kanji/*.json"))
                   for k in json.loads(kf.read_text(encoding="utf-8"))}
    vocab: dict[str, dict] = {}
    vid2slug: dict[int, str] = {}
    for vf in sorted(root.glob("corpus/vocab/*.json")):
        for v in json.loads(vf.read_text(encoding="utf-8")):
            vocab[v["slug"]] = v
            vid2slug[v["id"]] = v["slug"]
    elsewhere = referenced_elsewhere(root)
    shown_anywhere = {s for r in rows for s in SENT_TAG.findall(r["lesson"].get("body") or "")}
    taken: set[str] = set()

    def unlock_refs(les: dict) -> set[str]:
        out = set()
        for u in les.get("unlocks") or []:
            if u.get("type") in UNLOCK_KINDS:
                out.add(u["ref"])
        return out

    def candidates(row: dict, les: dict, exclude: set[str]) -> list[str]:
        mine = unlock_refs(les)
        if not mine:
            return []
        out = []
        for slug, s in by_slug.items():
            if slug in exclude or slug in taken or slug in row["rendered"]:
                continue
            if not (bve.SENT_REFS.get(slug, set()) & mine):
                continue
            if s.get("register") not in SHOWABLE_REGISTERS:
                continue
            above, load = fit(s, les, kanji_chars, vid2slug)
            if above or load:
                continue
            if not bve.sentence_ok(slug, row, need):
                continue
            out.append(slug)
        return out

    def rank_key(slug: str, row: dict, want: set[str]):
        s = by_slug[slug]
        prov = s.get("provenance") or {}
        cover = len(bve.SENT_REFS.get(slug, set()) & want)
        return (-cover,
                0 if slug not in elsewhere and slug not in shown_anywhere else 1,
                1 if prov.get("jp_source") in ("ai-generated", "generated") else 0,
                0 if len(s["jp"]) >= MIN_LEN else 1,
                len(s["jp"]),
                h(row["id"], slug))

    table: list[dict] = []
    residue: list[dict] = []
    stats = {"lessons_zero_before": 0, "lessons_filled": 0, "added": 0, "replaced": 0,
             "replaced_sharing_old_unlock": 0, "removed": 0, "headings_dropped": 0, "chips": 0,
             "zero_left": []}

    for row in rows:
        les = row["lesson"]
        lid = les["id"]
        body = les.get("body") or ""
        mine = unlock_refs(les)
        tags = list(SENT_TAG.finditer(body))
        # ---- breaches: replace in place, else remove -----------------------------------------
        removed_here = []
        for m in tags:
            slug = m.group(1)
            s = by_slug.get(slug)
            if s is None:
                continue
            above, load = fit(s, les, kanji_chars, vid2slug)
            budget = vlg.BUDGET.get(les.get("level"), 2)
            if not above and load <= budget:
                continue
            why = {"above_lesson_level": above, "load": load, "budget": budget,
                   "sentence_level": s.get("level")}
            if not in_example_block(body, m.start()):
                # the prose right before (or after) this tag is about THIS sentence ("nesta primeira, いや
                # recebe だった:"); swapping or dropping it would break the explanation, and a
                # script cannot rewrite prose. Held for an authored pass.
                residue.append({"lesson": lid, "sentence": slug, "jp": s["jp"], "why": why,
                                "reason": "introduced or discussed by the prose around it"})
                continue
            # What the old sentence was there to show: the lesson items it carries; failing that,
            # the lesson's grammar (an example block of a grammar lesson shows grammar); failing
            # that, any unlock. A replacement must carry one of them, or the link is removed.
            gmine = {r for r in mine if r.startswith("gram:")}
            want = (bve.SENT_REFS.get(slug, set()) & mine) or gmine or mine
            cands = [c for c in candidates(row, les, {x.group(1) for x in tags})
                     if bve.SENT_REFS.get(c, set()) & want]
            share = bool(bve.SENT_REFS.get(slug, set()) & mine)
            if cands:
                pick = sorted(cands, key=lambda c: rank_key(c, row, want))[0]
                taken.add(pick)
                tag = m.group(0)
                if body.count(tag) != 1:
                    raise SystemExit(f"{lid}: {tag} is not unique in the body")
                new = tag.replace(f'ref="{slug}"', f'ref="{pick}"')
                table.append({"lesson": lid, "op": "replace", "sentence_out": slug,
                              "sentence_in": pick, "from": tag, "to": new, "why": why,
                              "carries": sorted(bve.SENT_REFS.get(pick, set()) & want),
                              "shares_old_unlock": share})
                stats["replaced"] += 1
                stats["replaced_sharing_old_unlock"] += share
            else:
                tag = m.group(0)
                lit = tag + "\n" if body.count(tag + "\n") == 1 else tag
                if body.count(lit) != 1:
                    raise SystemExit(f"{lid}: {tag} is not unique in the body")
                table.append({"lesson": lid, "op": "remove", "sentence_out": slug,
                              "from": lit, "to": "", "why": why})
                removed_here.append(lit)
                stats["removed"] += 1
        if removed_here and len(removed_here) == len(tags):
            # every sentence this lesson shows would go and nothing in-rule can take their place:
            # a lesson with no example is worse than one over budget, so these stay, held
            for r in [r for r in table if r["lesson"] == lid and r["op"] == "remove"]:
                table.remove(r)
                residue.append({"lesson": lid, "sentence": r["sentence_out"],
                                "jp": by_slug[r["sentence_out"]]["jp"], "why": r["why"],
                                "reason": "no in-rule replacement, and removing it would leave "
                                          "the lesson with no sentence"})
            stats["removed"] -= len(removed_here)
            removed_here = []
        if removed_here:
            sim = body
            for lit in removed_here:
                sim = sim.replace(lit, "", 1)
            for title in SENTENCE_HEADINGS:
                hd = f'<heading level="3"><text>{title}</text></heading>'
                for m2 in re.finditer(re.escape(hd) + r"\s*", sim):
                    rest = sim[m2.end():]
                    if rest and not rest.startswith(("<heading", "<checklist")):
                        continue                   # still heads something

                    lit = m2.group(0)
                    # only a heading whose sentences THIS pass removed; one introducing prose stays
                    was = re.search(re.escape(hd) + r"\s*", body)
                    if not (was and body[was.end():].startswith("<sentence")):
                        continue
                    if sim.count(lit) == 1 and body.count(lit) == 1:
                        table.append({"lesson": lid, "op": "drop-heading", "from": lit, "to": ""})
                        stats["headings_dropped"] += 1
        # ---- lessons that render nothing: add a block ------------------------------------------
        if not tags and mine:
            stats["lessons_zero_before"] += 1
            picks: list[str] = []
            uncovered = set(mine)
            for _ in range(MAX_ADD):
                cands = candidates(row, les, set(picks))
                if not cands:
                    break
                best = sorted(cands, key=lambda c: rank_key(c, row, uncovered))[0]
                if picks and not (bve.SENT_REFS.get(best, set()) & uncovered):
                    # nothing new left to exemplify: a second sentence for the same item is fine,
                    # a third is padding
                    if len(picks) >= 2:
                        break
                picks.append(best)
                taken.add(best)
                uncovered -= bve.SENT_REFS.get(best, set())
            if picks:
                anchor = next((a for a in ANCHORS if body.count(a) == 1), None)
                block = HEADING + "\n" + "".join(
                    f'<sentence ref="{p}" show="furigana" mode="card"/>\n' for p in picks) + "\n"
                if anchor is None:
                    raise SystemExit(f"{lid}: no unique anchor to place the block before")
                table.append({"lesson": lid, "op": "add", "sentences": picks,
                              "from": anchor, "to": block + anchor,
                              "covers": sorted(mine - uncovered)})
                stats["lessons_filled"] += 1
                stats["added"] += len(picks)
            else:
                stats["zero_left"].append(lid)
        # ---- pre-N5 survival words: chip the defining list item ---------------------------------
        if les.get("level") == "pre-n5":
            chipped = set(CHIP_UNLOCK.findall(body))
            for u in les.get("unlocks") or []:
                if u.get("type") != "vocab" or u["ref"] in chipped:
                    continue
                rec = vocab.get(u["ref"])
                kana = (rec or {}).get("kana")
                if not kana:
                    continue
                lit = f"<item><jp>{kana}</jp>"
                if body.count(lit) != 1:
                    continue
                table.append({"lesson": lid, "op": "chip", "item": u["ref"], "kana": kana,
                              "from": lit, "to": f'<item><vocab ref="{u["ref"]}"/>'})
                stats["chips"] += 1

    doc = {
        "what_this_is": "W14 lesson sentence re-selection, derived by scripts/derive_lesson_sentences.py "
                        "from the exported tree and applied by scripts/apply_lesson_sentences.py to both "
                        "layers. Every sentence comes from the bank; no sentence or prose is authored. "
                        "Rows are literal body substitutions applied in order within a lesson.",
        "rule": "level <= lesson level; build_vocab_exercises.sentence_ok (i+0 over both registries, "
                "every derive_needs reference taught at or before the lesson); carries an item the "
                "lesson unlocks; not already shown there; each sentence picked once.",
        "generated_by": "scripts/derive_lesson_sentences.py",
        "counts": {**{k: (len(v) if isinstance(v, list) else v) for k, v in stats.items()},
                   "residue_held": len(residue),
                   "residue_held_in_prose": sum(1 for r in residue if r["reason"].startswith("introduced"))},
        "zero_left": stats["zero_left"],
        "residue_note": "Breaching links left in place: a prose sentence introduces them, or no "
                        "in-rule sentence can replace them and removing them would empty the lesson. "
                        "Not rows: nothing here is applied. An authored pass owns these.",
        "residue": residue,
        "row_count": len(table),
        "rows": table,
    }
    text = json.dumps(doc, ensure_ascii=False, indent=2) + "\n"
    out = Path(args.out) if args.out else TABLE
    if out == TABLE and TABLE.exists() and not args.force:
        # after the apply this tree derives (almost) nothing: overwriting would erase the ledger
        raise SystemExit(f"{TABLE.name} exists; it is the applied ledger. Use --out or --force.")
    out.write_text(text, encoding="utf-8")
    print(json.dumps(doc["counts"], ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
