#!/usr/bin/env python3
"""P6b — normalize vocab refs in authored lesson JSON to their CANONICAL registry headword.

Authors naturally reach for the KANA of a word (コップ, タバコ, すぐに, たち) when the registry headword is an
obscure ateji/rare-kanji form (洋杯, 煙草, 直ぐに, 立ち). A `vocab:<kana>` ref then dangles — it joins nothing in
the graph. This step rewrites every `vocab:<X>` ref (in unlocks, body, and exercise item_refs) to
`vocab:<headword>` when X is not itself a headword but is the EXACT kana of exactly one vocab. It NEVER guesses:
- X is already a headword            -> left as-is (canonical).
- X is the exact kana of ONE vocab   -> rewritten to that headword.
- X matches 0 vocab, or >1 (homograph kana) -> left as-is and REPORTED (manual call).

Run after write_authored_lessons.py and before load_lessons.py. Idempotent. Usage:
  normalize_lesson_refs.py            # all research/derived/lessons/*.json
  normalize_lesson_refs.py <slug...>  # only the named lessons (slug without les: or with)
"""
from __future__ import annotations

import json
import re
import sqlite3
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
ROOT = Path(__file__).resolve().parents[2]
DB = ROOT / "db" / "corpus.sqlite"
LESSON_DIR = ROOT / "research" / "derived" / "lessons"


def _build_maps(con) -> tuple[set[str], dict[str, list[str]]]:
    headwords: set[str] = set()
    kana_to_hw: dict[str, list[str]] = {}
    for hw, kana in con.execute("SELECT headword, kana FROM vocab"):
        if hw:
            headwords.add(hw)
        if kana:
            kana_to_hw.setdefault(kana, []).append(hw)
    return headwords, kana_to_hw


def _resolve(ident: str, headwords: set[str], kana_to_hw: dict[str, list[str]]) -> tuple[str | None, str]:
    """Return (canonical_headword_or_None, status). status in {ok, already, none, ambiguous}."""
    if ident in headwords:
        return ident, "already"
    hws = kana_to_hw.get(ident, [])
    if len(hws) == 1:
        return hws[0], "ok"
    if len(hws) > 1:
        return None, "ambiguous"
    return None, "none"


def normalize_file(path: Path, headwords: set[str], kana_to_hw: dict[str, list[str]],
                   reports: list[str]) -> int:
    d = json.loads(path.read_text(encoding="utf-8"))
    slug = d.get("slug", path.stem)
    # collect every vocab ident referenced anywhere
    idents: set[str] = set()
    for u in d.get("unlocks", []):
        if u.get("type") == "vocab" and isinstance(u.get("ref"), str) and u["ref"].startswith("vocab:"):
            idents.add(u["ref"].split(":", 1)[1])
    for ex in d.get("exercises", []):
        for it in ex.get("item_refs", []):
            if it.get("type") == "vocab" and isinstance(it.get("ref"), str) and it["ref"].startswith("vocab:"):
                idents.add(it["ref"].split(":", 1)[1])
    body = d.get("body", "") or ""
    for m in re.findall(r'vocab:([^"\'\s/<>]+)', body):
        idents.add(m)
    # build rename map
    rename: dict[str, str] = {}
    for ident in idents:
        hw, status = _resolve(ident, headwords, kana_to_hw)
        if status == "ok" and hw and hw != ident:
            rename[ident] = hw
        elif status in ("none", "ambiguous"):
            reports.append(f"{slug}: vocab:{ident} -> UNRESOLVED ({status}) — leaving as-is")
    if not rename:
        return 0
    changes = 0
    for old, new in rename.items():
        for u in d.get("unlocks", []):
            if u.get("type") == "vocab" and u.get("ref") == f"vocab:{old}":
                u["ref"] = f"vocab:{new}"
                changes += 1
        for ex in d.get("exercises", []):
            for it in ex.get("item_refs", []):
                if it.get("type") == "vocab" and it.get("ref") == f"vocab:{old}":
                    it["ref"] = f"vocab:{new}"
                    changes += 1
        # body: replace the exact ref token (bounded so a prefix can't be partially matched)
        pat = re.compile(r'vocab:' + re.escape(old) + r'(?=["\'\s/<>])')
        d["body"], n = pat.subn(f"vocab:{new}", d.get("body", "") or "")
        changes += n
        reports.append(f"{slug}: vocab:{old} -> vocab:{new}")
    path.write_text(json.dumps(d, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return changes


def main() -> int:
    con = sqlite3.connect(DB)
    headwords, kana_to_hw = _build_maps(con)
    con.close()
    if len(sys.argv) > 1:
        files = []
        for a in sys.argv[1:]:
            stem = a.split(":", 1)[1] if ":" in a else a
            files.append(LESSON_DIR / f"{stem}.json")
    else:
        files = sorted(LESSON_DIR.glob("*.json"))
    reports: list[str] = []
    total = 0
    touched = 0
    for f in files:
        if not f.exists():
            print(f"  skip (missing) {f.name}")
            continue
        c = normalize_file(f, headwords, kana_to_hw, reports)
        if c:
            touched += 1
            total += c
    print(f"normalized {total} ref(s) across {touched} file(s)")
    for r in reports:
        print(f"  {r}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
