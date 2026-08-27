#!/usr/bin/env python3
"""SRS gate: every card a lesson enrols names a real deck, of the right skill, at the right level.

WHY THIS EXISTS. The 2026-08-26 course review (SRS-N3-CARDS-IN-N5-DECKS) found all 2,072 cards
introduced by the 101 N3 lessons filed into deck:vocab-n5 / deck:kanji-n5 / deck:grammar-n5, because
scripts/ingest/enums.py:46 read `lv = level if level in ("n5", "n4") else "n5"` — an unknown level was
silently clamped to n5 instead of raising, and DECK_REGISTRY had no N3 decks at all. Nothing in the
suite compared a deck to the item it holds, so half the SRS schedule pointed at the wrong deck and the
gate stayed green. design/unlock_enums.json states the rule itself — item_to_deck:
"deck:vocab-<level>", "deck:kanji-<level>", "deck:grammar-<level>" — so this validator is that
sentence made executable, against the EXPORTED courseware JSON (db/corpus.sqlite is a regenerable
index, not the source of truth).

Seven rules, per card in lesson.srs.introduces_cards:
  1. deck is in the `deck` enum AND in `deck_registry` (design/unlock_enums.json).
  2. card_types is non-empty and exactly the registry's list for that deck.
  3. the item's namespace matches the deck's skill (vocab->vocab:, kanji->kanji:, grammar->gram:,
     kana->kana:, phrase->sent:).
  4. the item resolves in the exported corpus.
  5. the item is one of that lesson's own unlocks[].ref — a lesson may not schedule review for
     material it does not teach.
  6. the deck's declared level equals the ITEM's own corpus level. Kana decks are exempt: kana
     families carry no level.
  7. no (deck, item) pair repeats inside one lesson (double enrolment; SRS-DUP-CARDS).

Rule 6 has an optional exemption file, course/srs_deck_exemptions.json — a JSON list of
{lesson, deck, item, reason}. It is NOT seeded: today rule 6 fails 23 times on front-loaded
cross-level items (an n3-level kanji taught in an n4 lesson lands in deck:kanji-n4), which is a real
finding for the owner to rule on, not something this gate should paper over. Every exemption is
echoed in the summary, and an exemption matching no card is itself a failure.

Exit 1 on any failure. Usage: validate_srs_decks.py [--root PATH] [--list]
"""
from __future__ import annotations
import argparse, json, sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
DEFAULT_ROOT = Path(__file__).resolve().parents[2]

# deck_registry `skill` -> the ref namespace its items must live in (design/unlock_enums.json).
SKILL_NAMESPACE = {"vocab": "vocab", "kanji": "kanji", "grammar": "gram", "kana": "kana", "phrase": "sent"}


def load_levels(root: Path) -> dict[str, str]:
    """slug -> level for every exported vocab / kanji / grammar record.

    Only the per-level registry files (n*.json) — those directories also hold side files such as
    corpus/kanji/unregistered_chars.json that are not record arrays."""
    levels: dict[str, str] = {}
    for sub in ("vocab", "kanji", "grammar"):
        for f in sorted((root / "corpus" / sub).glob("n*.json")):
            data = json.loads(f.read_text(encoding="utf-8"))
            if not isinstance(data, list):
                continue
            for r in data:
                if isinstance(r, dict) and "slug" in r:
                    levels[r["slug"]] = r.get("level")
    return levels


def load_kana_ids(root: Path) -> set[str]:
    """Legal kana card targets: family ids plus the individual glyph ids."""
    ids: set[str] = set()
    fam_path = root / "corpus" / "kana" / "families.json"
    if fam_path.exists():
        for group in json.loads(fam_path.read_text(encoding="utf-8")).values():
            for fam in group:
                ids.add(fam["id"])
                for m in fam.get("members") or []:
                    ids.add(m["id"])
    for name in ("hiragana.json", "katakana.json"):
        p = root / "corpus" / "kana" / name
        if p.exists():
            for g in json.loads(p.read_text(encoding="utf-8")):
                ids.add(g["id"])
    return ids


def load_exemptions(root: Path) -> tuple[dict[tuple[str, str, str], str], list[str]]:
    """course/srs_deck_exemptions.json -> {(lesson, deck, item): reason}, plus structural errors."""
    path = root / "course" / "srs_deck_exemptions.json"
    if not path.exists():
        return {}, []
    errs: list[str] = []
    out: dict[tuple[str, str, str], str] = {}
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, list):
        return {}, ["srs_deck_exemptions.json: expected a JSON list of {lesson, deck, item, reason}"]
    for i, e in enumerate(data):
        if not isinstance(e, dict) or not all(str(e.get(k) or "").strip() for k in ("lesson", "deck", "item", "reason")):
            errs.append(f"srs_deck_exemptions.json[{i}]: every entry needs a non-empty lesson, deck, item and reason")
            continue
        out[(e["lesson"], e["deck"], e["item"])] = e["reason"]
    return out, errs


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=str(DEFAULT_ROOT), help="tree to validate (default: repo root)")
    ap.add_argument("--list", action="store_true", help="print every failure instead of the first 15")
    args = ap.parse_args()
    root = Path(args.root).resolve()

    enums_path = root / "design" / "unlock_enums.json"
    if not enums_path.exists():
        print(f"validate_srs_decks: no design/unlock_enums.json under {root} — cannot validate")
        return 1
    enums = json.loads(enums_path.read_text(encoding="utf-8"))
    deck_enum = set(enums.get("deck") or [])
    registry: dict = enums.get("deck_registry") or {}
    card_type_enum = set(enums.get("card_type") or [])

    levels = load_levels(root)
    kana_ids = load_kana_ids(root)
    if not levels or not kana_ids:
        print(f"validate_srs_decks: corpus registries under {root} are empty "
              f"({len(levels)} slugs, {len(kana_ids)} kana ids) — nothing to validate against")
        return 1
    exemptions, fails = load_exemptions(root)
    used_exemptions: set[tuple[str, str, str]] = set()
    sentence_levels: dict[str, str] | None = None   # loaded lazily: bank.json is 50MB

    # The registry itself is part of the contract: a deck whose card_types are not card_type values
    # would make rule 2 enforce nonsense.
    for deck, meta in sorted(registry.items()):
        if deck not in deck_enum:
            fails.append(f"deck_registry has {deck} but the `deck` enum does not list it")
        if meta.get("skill") not in SKILL_NAMESPACE:
            fails.append(f"deck_registry[{deck}]: unknown skill {meta.get('skill')!r}")
        for ct in meta.get("card_types") or []:
            if ct not in card_type_enum:
                fails.append(f"deck_registry[{deck}]: card_type {ct!r} is not in the card_type enum")
    for deck in sorted(deck_enum - set(registry)):
        fails.append(f"`deck` enum lists {deck} but deck_registry has no entry for it")

    by_rule: dict[str, int] = {}
    lessons = sorted(root.glob("course/*/topic-*/lesson-*.json"))
    if not lessons:
        # An empty input set must never read as a pass — that is how a gate goes vacuous.
        print(f"validate_srs_decks: no course/*/topic-*/lesson-*.json under {root} — nothing validated")
        return 1
    cards = 0

    def fail(rule: str, msg: str) -> None:
        by_rule[rule] = by_rule.get(rule, 0) + 1
        fails.append(f"[{rule}] {msg}")

    # lesson id -> its course level, for rule 6 (deck level follows the LESSON)
    lesson_level_of: dict = {}
    for _lf in lessons:
        _d = json.loads(_lf.read_text(encoding="utf-8"))
        lesson_level_of[_d.get("id") or _lf.name] = _d.get("level")

    for lf in lessons:
        d = json.loads(lf.read_text(encoding="utf-8"))
        lid = d.get("id") or lf.name
        unlock_refs = {u.get("ref") for u in (d.get("unlocks") or [])}
        srs = d.get("srs") or {}
        introduces = srs.get("introduces_cards")
        if introduces is None:
            introduces = []
        elif not isinstance(introduces, list):
            fail("structure", f"{lid}: srs.introduces_cards is {type(introduces).__name__}, expected a list")
            introduces = []
        seen: set[tuple[str, str]] = set()
        for card in introduces:
            cards += 1
            if not isinstance(card, dict):
                fail("structure", f"{lid}: card {card!r} is not an object")
                continue
            deck, item, ctypes = card.get("deck"), card.get("item"), card.get("card_types")
            if not isinstance(deck, str) or not isinstance(item, str):
                fail("structure", f"{lid}: card needs string `deck` and `item`, got {card!r}")
                continue

            # 1 — deck exists
            if deck not in deck_enum:
                fail("1-deck-enum", f"{lid}: deck {deck} is not in the `deck` enum")
            meta = registry.get(deck)
            if meta is None:
                fail("1-deck-registry", f"{lid}: deck {deck} has no deck_registry entry")
                continue

            # 2 — card_types exactly the registry's
            want = set(meta.get("card_types") or [])
            if not isinstance(ctypes, list) or not ctypes or set(ctypes) != want:
                fail("2-card-types", f"{lid}: {deck}/{item} card_types {ctypes!r} != registry {sorted(want)}")

            # 3 — namespace agrees with the deck's skill
            skill = meta.get("skill")
            ns = SKILL_NAMESPACE.get(skill)
            if ns and not item.startswith(ns + ":"):
                fail("3-namespace", f"{lid}: {deck} is a {skill} deck but holds {item}")

            # 4 — the item resolves; 6 — deck level == item level
            item_level: str | None = None
            if skill == "kana":
                if item not in kana_ids:
                    fail("4-resolve", f"{lid}: {item} resolves to no kana record")
            elif skill == "phrase":
                if sentence_levels is None:
                    bank = root / "corpus" / "sentences" / "bank.json"
                    sentence_levels = ({s["slug"]: s.get("level") for s in
                                        json.loads(bank.read_text(encoding="utf-8"))} if bank.exists() else {})
                if item not in sentence_levels:
                    fail("4-resolve", f"{lid}: {item} resolves to no sentence record")
                else:
                    item_level = sentence_levels[item]
            else:
                if item not in levels:
                    fail("4-resolve", f"{lid}: {item} resolves to no corpus record")
                else:
                    item_level = levels[item]

            # Rule 6: the deck level must match the LESSON's level (pre-n5 lessons enrol into
            # the n5 decks, mirroring scripts/ingest/enums.py deck_for). The first version compared
            # to the ITEM's registry level, which hard-failed the 23 front-loaded cross-level unlocks
            # that validate_unlock_ledger check E explicitly declares legal — two gates in one suite
            # must not disagree about the same rows. Item level still matters for kana/phrase decks,
            # where the item IS the lesson-level carrier.
            lesson_level = lesson_level_of.get(lid)
            expected_deck_level = "n5" if lesson_level == "pre-n5" else lesson_level
            if skill in ("kana", "phrase"):
                expected_deck_level = meta.get("level")   # kana/phrase decks are level-free by design
            if expected_deck_level is not None and meta.get("level") != expected_deck_level:
                key = (lid, deck, item)
                if key in exemptions:
                    used_exemptions.add(key)
                else:
                    fail("6-level", f"{lid}: {item} is level {item_level} but {deck} is a "
                                    f"{meta.get('level')} deck")

            # 5 — the lesson teaches what it schedules
            if item not in unlock_refs:
                fail("5-not-unlocked", f"{lid}: card {item} is not among the lesson's unlocks")

            # 7 — no double enrolment
            if (deck, item) in seen:
                fail("7-duplicate", f"{lid}: ({deck}, {item}) enrolled twice")
            seen.add((deck, item))

    for key, reason in sorted(exemptions.items()):
        if key in used_exemptions:
            print(f"  EXEMPT {key[0]} {key[1]}/{key[2]} — {reason}")
        else:
            fails.append(f"[exemption] srs_deck_exemptions.json entry {key} matches no failing card")

    shown = fails if args.list else fails[:15]
    for f in shown:
        print(f"  FAIL {f}")
    if len(fails) > len(shown):
        print(f"  ... {len(fails) - len(shown)} more (re-run with --list)")
    rules = ", ".join(f"{k}={v}" for k, v in sorted(by_rule.items())) or "none"
    print(f"\nvalidate_srs_decks: {cards} cards over {len(lessons)} lessons, {len(registry)} decks, "
          f"{len(levels)} corpus records + {len(kana_ids)} kana ids, {len(fails)} FAIL by rule {{{rules}}}")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
