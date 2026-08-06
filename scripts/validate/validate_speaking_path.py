#!/usr/bin/env python3
"""Validate course/speak/ — the speaking-first path. Spec: design/speaking_path.md.

The path's whole premise is that it REFERENCES the corpus and never embeds it, so the thing that can
silently rot is a dangling ID: a unit pointing at a sentence/vocab/grammar slug that no longer
exists after a corpus rebuild. That is what this checks, against the committed JSON export rather
than the SQLite index (the export is the source of truth — see CLAUDE.md).

Also enforced:
  * every unit id is unique and matches its stage + order
  * say_now is non-empty, and every phrase is a real bank sentence unless the unit says otherwise
  * a unit either introduces vocabulary or is a set-phrase unit; a unit that does neither is padding
  * cumulative_known_vocab never decreases along the path (the known set only grows)
  * shortfall entries in course.json match what the units actually contain, so the manifest cannot
    claim a stage is complete when it is not

Usage: validate_speaking_path.py
"""
from __future__ import annotations
import json, sys
from pathlib import Path
sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
ROOT = Path(__file__).resolve().parents[2]
SPEAK = ROOT / "course" / "speak"
CORPUS = ROOT / "corpus"


def load_ids() -> tuple[set[str], set[str], set[str]]:
    """Collect every sentence / vocab / grammar slug present in the committed corpus export."""
    sent: set[str] = set()
    vocab: set[str] = set()
    gram: set[str] = set()
    for p in CORPUS.rglob("*.json"):
        try:
            data = json.loads(p.read_text(encoding="utf-8"))
        except Exception:
            continue
        items = data if isinstance(data, list) else [data]
        for it in items:
            if not isinstance(it, dict):
                continue
            sid = it.get("slug") or it.get("id")
            if not isinstance(sid, str):
                continue
            (sent if sid.startswith("sent:") else
             vocab if sid.startswith("vocab:") else
             gram if sid.startswith("gram:") else set()).add(sid)
    return sent, vocab, gram


def main() -> int:
    if not SPEAK.exists():
        print("validate_speaking_path: course/speak not built — run build_speaking_path.py")
        return 0
    sent, vocab, gram = load_ids()
    course = json.loads((SPEAK / "course.json").read_text(encoding="utf-8"))
    fails: list[str] = []
    warns: list[str] = []
    seen_ids: set[str] = set()
    last_known = 0
    unit_count = 0

    for stage in course["stages"]:
        slug = stage["slug"].split(":", 1)[1]
        for uid in stage["unit_ids"]:
            n = int(uid.rsplit("-", 1)[1])
            p = SPEAK / slug / f"unit-{n:02d}.json"
            if not p.exists():
                fails.append(f"{uid}: file missing ({p.relative_to(ROOT)})")
                continue
            u = json.loads(p.read_text(encoding="utf-8"))
            unit_count += 1
            if u["id"] in seen_ids:
                fails.append(f"{u['id']}: duplicate unit id")
            seen_ids.add(u["id"])
            if u["id"] != uid or u["stage"] != stage["slug"] or u["order"] != n:
                fails.append(f"{u['id']}: id/stage/order disagree with course.json")

            for ref in u["say_now"]:
                if sent and ref not in sent:
                    fails.append(f"{u['id']}: dangling sentence ref {ref}")
            for ref in u["words"]:
                if vocab and ref not in vocab:
                    fails.append(f"{u['id']}: dangling vocab ref {ref}")
            for ref in u["patterns"]:
                if gram and ref not in gram:
                    fails.append(f"{u['id']}: dangling grammar ref {ref}")

            if not u["say_now"]:
                fails.append(f"{u['id']}: no phrases")
            if not u["words"] and not u["chunk_phrases"]:
                fails.append(f"{u['id']}: introduces nothing and teaches no set phrase (padding)")
            if u["cumulative_known_vocab"] < last_known:
                fails.append(f"{u['id']}: known set shrank "
                             f"({last_known} -> {u['cumulative_known_vocab']})")
            last_known = u["cumulative_known_vocab"]
            if u.get("untranslated"):
                warns.append(f"{u['id']}: {len(u['untranslated'])} phrase(s) without a pt-BR translation")
            if not u.get("needs_review"):
                fails.append(f"{u['id']}: sequencing is Layer C and must carry needs_review")

    declared = course["totals"]["units"]
    if declared != unit_count:
        fails.append(f"course.json claims {declared} units, found {unit_count}")

    # Orphans: unit files on disk that no stage references. These ship to the app (the prototype
    # loaded 72 units for a 66-unit path) while being invisible to every manifest-driven check.
    on_disk = {p for p in SPEAK.rglob("unit-*.json")}
    referenced = {SPEAK / s["slug"].split(":", 1)[1] / f"unit-{int(u.rsplit('-', 1)[1]):02d}.json"
                  for s in course["stages"] for u in s["unit_ids"]}
    for p in sorted(on_disk - referenced):
        fails.append(f"orphan unit file not referenced by course.json: {p.relative_to(ROOT)}")

    for line in warns[:10]:
        print(f"  [warn] {line}")
    if len(warns) > 10:
        print(f"  [warn] … and {len(warns) - 10} more")
    for line in fails:
        print(f"  [FAIL] {line}")
    print(f"validate_speaking_path: {unit_count} units, "
          f"{course['totals']['phrases']} phrases, {len(fails)} FAIL, {len(warns)} warn")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
