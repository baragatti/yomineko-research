#!/usr/bin/env python3
"""P6b — enforce introduce-once across authored lesson JSON by removing duplicate unlocks.

Planners occasionally assign the same item (vocab/kanji/grammar/…) to two lessons, or a topic dump re-lists an
item already placed elsewhere. That violates introduce-once. This pass keeps the unlock on the EARLIEST lesson
(by course order = topic.ord, then lesson order) and removes it from every later lesson. This is SAFE: the body
of a later lesson may still reference the item via a chip, because cumulative_known_set is cumulative across all
prior lessons, so the earlier unlock keeps it in scope. Every removal is reported. Run after normalize_lesson_refs
and before load_lessons. Idempotent. Usage: dedupe_unlocks.py
"""
from __future__ import annotations

import json
import sqlite3
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
ROOT = Path(__file__).resolve().parents[2]
DB = ROOT / "db" / "corpus.sqlite"
LESSON_DIR = ROOT / "research" / "derived" / "lessons"
# unlock types that must be introduce-once (feature/srs-deck may legitimately repeat)
ONCE_TYPES = {"vocab", "kanji", "grammar", "kana-family", "phrase", "conjugation-form", "kanji-family"}


def _topic_ord(con) -> dict[str, int]:
    return {slug: ordv for slug, ordv in con.execute("SELECT slug, ord FROM topic")}


def main() -> int:
    con = sqlite3.connect(DB)
    topic_ord = _topic_ord(con)
    con.close()
    files = sorted(LESSON_DIR.glob("*.json"))
    recs = []
    for f in files:
        d = json.loads(f.read_text(encoding="utf-8"))
        ordkey = (topic_ord.get(d.get("topic"), 9999), int(d.get("order", 0)), d.get("slug", f.stem))
        recs.append((ordkey, f, d))
    recs.sort(key=lambda r: r[0])
    seen: dict[tuple[str, str], str] = {}  # (type, ref) -> owning lesson slug
    removals: list[str] = []
    changed: set[Path] = set()
    for _, f, d in recs:
        slug = d.get("slug", f.stem)
        kept = []
        for u in d.get("unlocks", []):
            typ, ref = u.get("type"), u.get("ref")
            if typ in ONCE_TYPES:
                key = (typ, ref)
                if key in seen:
                    removals.append(f"{slug}: drop {typ} {ref} (already unlocked by {seen[key]})")
                    changed.add(f)
                    continue
                seen[key] = slug
            kept.append(u)
        if f in changed:
            d["unlocks"] = kept
            f.write_text(json.dumps(d, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"deduped {len(removals)} duplicate unlock(s) across {len(changed)} file(s)")
    for r in removals:
        print(f"  {r}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
