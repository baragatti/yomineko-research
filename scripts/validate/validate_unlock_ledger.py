#!/usr/bin/env python3
"""The unlock ledger: in the PUBLISHED SLUG NAMESPACE, every taught-level corpus record is unlocked by
exactly one lesson, and no lesson unlocks the same record twice.

WHY THIS EXISTS (two confirmed defects, both invisible to every gate that preceded it):

  STRUCT-03 — 17 vocab records tagged n5/n4/n3 were unlocked by no lesson at all, so they never entered
  any cumulative_known_set or SRS deck, yet audit_jlpt_coverage.py printed "all taught" for every level.
  It compared `SELECT headword FROM vocab` against headword-shaped `lesson_unlocks.ref` values, so the
  homograph 米/こめ counted as covered by the 米/メートル record. Two hard coverage gates were silenced by
  running in the wrong namespace. This validator therefore keys EVERY registry by its stable slug —
  vocab.slug, kanji.slug, grammar.slug, kana family id — and never by headword, character, key, or an
  integer row id, and it reads the exported JSON rather than db/corpus.sqlite.

  STRUCT-04 — the vocab disambiguation resolved an ambiguous headword ref onto a record the SAME lesson
  already unlocked through a second ref (les:n3-conectores-05 -> vocab:1454500 twice,
  les:n3-perspectiva-06 -> vocab:2648780 twice), duplicating the unlock and the SRS card and silently
  deleting the sibling word from the course. The DB could not see it: lesson_unlocks has
  PRIMARY KEY (lesson_id, unlock_type, ref), so the collision only exists after export. Hence the
  duplicate checks live here, on the exported lesson leaves.

Checks (all hard unless marked REPORT):
  A  every unlock entry has a known type, a ref in that type's namespace, and a ref that resolves
  B  no (type, ref) appears twice inside one lesson                              [STRUCT-04]
  C  no ref is unlocked by two different lessons
  D  every registry record whose level is one the courseware teaches is unlocked, or is listed in
     course/coverage_exemptions.json with a reason; an exemption that matches nothing is itself a
     failure, so the held-back list cannot rot                                   [STRUCT-03]
  E  cross-level teaching may only run EARLIER than a record's own level, never later (REPORT: the
     full (kind, registry_level, teaching_level) table; REPORT: records outside the taught levels)
  F  srs.introduces_cards names exactly the lesson's item unlocks, each card once
  G  course/vocab_disambiguation_review.json is honest: count matches, every chosen/candidate slug
     resolves, chosen is one of its own candidates, a row that says it affects an unlock really is
     unlocked there, and no row's chosen collides with a sibling the same lesson already teaches
     (REPORT: rows that elimination has already decided, so they leave the teacher's queue)

Usage: validate_unlock_ledger.py [--root PATH] [--list]
"""
from __future__ import annotations
import argparse, collections, json, re, sys
from pathlib import Path
sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]

DEFAULT_ROOT = Path(__file__).resolve().parents[2]
MAX_SHOWN = 15

# unlock type -> (registry glob relative to root, namespace prefix)
ITEM_REGISTRIES: dict[str, tuple[str, str]] = {
    "vocab": ("corpus/vocab/*.json", "vocab"),
    "kanji": ("corpus/kanji/*.json", "kanji"),
    "grammar": ("corpus/grammar/*.json", "gram"),
    "kana-family": ("corpus/kana/families.json", "kana"),
}
# item unlocks are the ones that become SRS cards; feature/srs-deck unlocks do not
NON_ITEM_TYPES = {"feature", "srs-deck"}
NON_ITEM_PREFIX = {"feature": "feat", "srs-deck": "deck"}
TOPIC_NUM = re.compile(r"topic-(\d+)")


def load_registries(root: Path) -> dict[str, dict[str, str | None]]:
    """kind -> {stable slug: level}. Kana families carry no level field; they are pre-n5 by definition."""
    reg: dict[str, dict[str, str | None]] = {}
    for kind, (glob_pat, _) in ITEM_REGISTRIES.items():
        table: dict[str, str | None] = {}
        for path in sorted(root.glob(glob_pat)):
            data = json.loads(path.read_text(encoding="utf-8"))
            if kind == "kana-family":
                for script_rows in data.values():
                    for rec in script_rows:
                        table[rec["id"]] = "pre-n5"
            else:
                for rec in data:
                    table[rec["slug"]] = rec.get("level")
        reg[kind] = table
    return reg


def load_lessons(root: Path, level_order: dict[str, int]) -> list[tuple[Path, dict]]:
    """Every lesson leaf, in course order (course.order, topic number, lesson.order)."""
    out = []
    for path in root.glob("course/*/topic-*/lesson-*.json"):
        lesson = json.loads(path.read_text(encoding="utf-8"))
        topic_num = int(m.group(1)) if (m := TOPIC_NUM.search(path.parent.name)) else 0
        key = (level_order.get(path.parts[-3], 99), topic_num, lesson.get("order", 0), path.name)
        out.append((key, path, lesson))
    out.sort(key=lambda t: t[0])
    return [(p, d) for _, p, d in out]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=str(DEFAULT_ROOT), help="tree to validate (default: repo root)")
    ap.add_argument("--list", action="store_true", help="print every failure instead of the first 15")
    args = ap.parse_args()
    root = Path(args.root).resolve()

    manifest = json.loads((root / "course" / "manifest.json").read_text(encoding="utf-8"))
    taught = [c["level"] for c in sorted(manifest["courses"], key=lambda c: c["order"])]
    level_order = {lv: i for i, lv in enumerate(taught)}
    for later in ("n2", "n1"):  # levels the courseware does not reach yet, ordered after everything taught
        level_order.setdefault(later, len(level_order))

    enums = json.loads((root / "design" / "unlock_enums.json").read_text(encoding="utf-8"))
    known_types = set(enums["unlock_type"])
    non_item_members = {"feature": set(enums["feature"]), "srs-deck": set(enums["deck"])}

    reg = load_registries(root)
    lessons = load_lessons(root, level_order)

    fails: list[str] = []
    unlocked_by: dict[tuple[str, str], list[str]] = collections.defaultdict(list)
    cross = collections.Counter()

    for path, lesson in lessons:
        lid = lesson["id"]
        llevel = lesson.get("level")
        seen = collections.Counter()
        item_refs: list[str] = []
        for entry in lesson.get("unlocks", []):
            utype, ref = entry.get("type"), entry.get("ref")
            if utype not in known_types:
                fails.append(f"A {lid}: unlock type {utype!r} is not in design/unlock_enums.json")
                continue
            prefix = (ITEM_REGISTRIES[utype][1] if utype in ITEM_REGISTRIES
                      else NON_ITEM_PREFIX.get(utype, ""))
            if not isinstance(ref, str) or not ref.startswith(prefix + ":"):
                fails.append(f"A {lid}: {utype} unlock ref {ref!r} is not in the {prefix}: namespace")
                continue
            # -- A: does the ref address a real record?
            if utype in ITEM_REGISTRIES:
                if ref not in reg[utype]:
                    fails.append(f"A {lid}: {utype} unlock {ref} resolves to no exported record")
                    continue
                item_refs.append(ref)
                rlevel = reg[utype][ref]
                if rlevel and llevel and rlevel != llevel:
                    cross[(utype, rlevel, llevel)] += 1
                    # -- E: front-loading an item is allowed; postponing it past its own level is not
                    if level_order.get(llevel, 99) > level_order.get(rlevel, 99):
                        fails.append(f"E {lid} ({llevel}) teaches {ref}, a {rlevel} record, after its own level")
            elif utype in NON_ITEM_TYPES:
                # unlock_enums lists decks with their prefix ("deck:vocab-n5") and features without it
                members = non_item_members[utype]
                if ref not in members and ref.split(":", 1)[1] not in members:
                    fails.append(f"A {lid}: {utype} unlock {ref} is not a registered {utype}")
            seen[(utype, ref)] += 1
            unlocked_by[(utype, ref)].append(lid)
        # -- B: the STRUCT-04 collision
        for (utype, ref), n in sorted(seen.items()):
            if n > 1:
                fails.append(f"B {lid}: unlocks {utype} {ref} {n}x — two refs resolved onto one record")
        # -- F: SRS cards are derived from item unlocks, so they must mirror them exactly
        cards = lesson.get("srs", {}).get("introduces_cards", [])
        card_items = [c.get("item") for c in cards]
        dup_cards = [i for i, n in collections.Counter(card_items).items() if n > 1]
        if dup_cards:
            fails.append(f"F {lid}: srs.introduces_cards lists {sorted(dup_cards)[:3]} more than once")
        if set(card_items) != set(item_refs):
            only_card = sorted(set(card_items) - set(item_refs))[:3]
            only_unlock = sorted(set(item_refs) - set(card_items))[:3]
            fails.append(f"F {lid}: srs cards != item unlocks (card-only {only_card}, unlock-only {only_unlock})")

    # -- C: one record, one introducing lesson
    for (utype, ref), lids in sorted(unlocked_by.items()):
        holders = sorted(set(lids))
        if len(holders) > 1:
            fails.append(f"C {utype} {ref} unlocked by {len(holders)} lessons: {holders[:4]}")

    # -- D: taught-level coverage in the slug namespace, with an explicit held-back list
    exem_path = root / "course" / "coverage_exemptions.json"
    exemptions: dict[str, dict[str, str]] = {}
    if exem_path.exists():
        raw = json.loads(exem_path.read_text(encoding="utf-8"))
        for kind, rows in raw.items():
            if not isinstance(rows, list):
                continue  # prose keys such as "why"
            if kind not in reg:
                fails.append(f"D coverage_exemptions.json: {kind!r} is not an unlock kind")
                continue
            table: dict[str, str] = {}
            for row in rows:
                rid, reason = row.get("id"), (row.get("reason") or "").strip()
                if not rid:
                    fails.append(f"D coverage_exemptions.json [{kind}]: entry without an id")
                    continue
                if not reason:
                    fails.append(f"D coverage_exemptions.json: {rid} carries no reason")
                if rid in table:
                    fails.append(f"D coverage_exemptions.json: {rid} listed twice")
                table[rid] = reason
            exemptions[kind] = table

    coverage_lines: list[str] = []
    outside_lines: list[str] = []
    for kind, table in reg.items():
        unlocked = {ref for (k, ref) in unlocked_by if k == kind}
        at_level = {slug for slug, lv in table.items() if lv in level_order and lv in taught}
        missing = sorted(at_level - unlocked)
        held = exemptions.get(kind, {})
        for slug in missing:
            if slug not in held:
                fails.append(f"D {kind} {slug} ({table[slug]}) is taught-level but no lesson unlocks it")
        for slug in sorted(held):
            if slug not in missing:
                why = "record is unlocked" if slug in unlocked else "no such taught-level record"
                fails.append(f"D coverage_exemptions.json: {slug} matches nothing ({why}) — stale entry")
        coverage_lines.append(f"  {kind:12s} taught-level {len(at_level):5d}  unlocked {len(at_level & unlocked):5d}"
                              f"  held back {len(held):2d}  uncovered {len([m for m in missing if m not in held])}")
        outside = collections.Counter(lv for lv in table.values() if lv not in taught)
        if outside:
            outside_lines.append(f"  {kind:12s} " + ", ".join(f"{lv} {n}" for lv, n in sorted(outside.items())))

    # -- G: the homograph review queue
    review_path = root / "course" / "vocab_disambiguation_review.json"
    review_note = "no review file"
    if review_path.exists():
        review = json.loads(review_path.read_text(encoding="utf-8"))
        items = review.get("items", [])
        if review.get("count") != len(items):
            fails.append(f"G vocab_disambiguation_review.json: count {review.get('count')} != {len(items)} items")
        vocab_by_lesson: dict[str, set[str]] = collections.defaultdict(set)
        for (utype, ref), lids in unlocked_by.items():
            if utype == "vocab":
                for lid in lids:
                    vocab_by_lesson[lid].add(ref)
        lesson_ids = {d["id"] for _, d in lessons}
        chosen_seen: dict[tuple[str, str], list[str]] = collections.defaultdict(list)
        decidable = 0
        for row in items:
            hw, lid, chosen = row.get("headword"), row.get("lesson"), row.get("chosen")
            where = f"{hw} @ {lid}"
            cands = [c.get("slug") for c in row.get("candidates", [])]
            for slug in [chosen, *cands]:
                if slug not in reg["vocab"]:
                    fails.append(f"G review {where}: {slug} resolves to no vocab record")
            if chosen not in cands:
                fails.append(f"G review {where}: chosen {chosen} is not among its own candidates {cands}")
            if lid not in lesson_ids:
                fails.append(f"G review {where}: names a lesson that does not exist")
            taught_here = vocab_by_lesson.get(lid, set())
            if "unlock" in (row.get("affects") or []) and chosen not in taught_here:
                fails.append(f"G review {where}: says it affects an unlock, but {lid} does not unlock {chosen}")
            # the STRUCT-04 evidence rule: a sibling the lesson already teaches rules the choice out
            collide = [c for c in cands if c != chosen and c in taught_here]
            if collide:
                fails.append(f"G review {where}: chosen {chosen} collides — {lid} already teaches sibling {collide}")
            chosen_seen[(lid, chosen)].append(hw)
            survivors = [c for c in cands if c == chosen or c not in taught_here]
            if len(survivors) == 1 and row.get("how") == "unresolved":
                decidable += 1
        for (lid, chosen), hws in sorted(chosen_seen.items()):
            if len(hws) > 1:
                fails.append(f"G review {lid}: headwords {hws} all resolved onto {chosen}")
        review_note = f"{len(items)} open rows, {decidable} decidable by elimination"

    print("coverage in the published slug namespace:")
    for line in coverage_lines:
        print(line)
    if outside_lines:
        print("expected-untaught (levels the courseware does not reach yet):")
        for line in outside_lines:
            print(line)
    if cross:
        print("cross-level teaching (front-loading is legal, postponing is not):")
        for (kind, rlevel, llevel), n in sorted(cross.items()):
            print(f"  {kind:12s} {rlevel} record taught in {llevel} lesson: {n}")
    print(f"homograph review queue: {review_note}")

    shown = fails if args.list else fails[:MAX_SHOWN]
    for f in shown:
        print("  FAIL", f)
    if len(fails) > len(shown):
        print(f"  ... {len(fails) - len(shown)} more (--list for all)")
    total_unlocks = sum(len(v) for v in unlocked_by.values())
    print(f"\nvalidate_unlock_ledger: {len(lessons)} lessons, {total_unlocks} unlocks, "
          f"{len(unlocked_by)} distinct refs, "
          f"{'FAIL ' + str(len(fails)) if fails else 'ALL OK'}")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
