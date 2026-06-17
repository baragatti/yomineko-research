#!/usr/bin/env python3
"""P8 — undo accidental accenting of IDENTIFIER fields (one-off repair).

fix_accents_lessons.py walked every string field and accented Latin words even inside identifiers (slug, topic,
exercise slugs, and ref="…" attributes in the body), e.g. n5-numeros-tempo -> n5-números-tempo. Identifiers must
be ASCII. This reverse-accents ONLY identifier fields/attributes (never learner prose), using the inverse of the
accent map, and reconciles any file whose NAME got accented (rename to the ASCII slug, overwriting the stale
sibling with this — newer — content). Run once, then load/validate. Usage: fix_identifier_accents.py
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
from fix_accents_lessons import MAP  # noqa: E402

LESSON_DIR = Path(__file__).resolve().parents[2] / "research" / "derived" / "lessons"
REV = {v: k for k, v in MAP.items()}  # accented -> ascii
_RX = re.compile(r"(?<![0-9A-Za-zÀ-ÿ])(" + "|".join(sorted(REV, key=len, reverse=True)) + r")(?![0-9A-Za-zÀ-ÿ])")


def _deaccent(s: str) -> str:
    return _RX.sub(lambda m: REV[m.group(1)], s)


def _fix_refs_in_body(body: str) -> str:
    # only touch ref="…" attribute values, never prose
    return re.sub(r'(ref=")([^"]*)(")', lambda m: m.group(1) + _deaccent(m.group(2)) + m.group(3), body)


def fix_record(d: dict) -> dict:
    if isinstance(d.get("slug"), str):
        d["slug"] = _deaccent(d["slug"])
    if isinstance(d.get("topic"), str):
        d["topic"] = _deaccent(d["topic"])
    for u in d.get("unlocks", []) + d.get("needs", []):
        if isinstance(u.get("ref"), str):
            u["ref"] = _deaccent(u["ref"])
    d["sentence_refs"] = [_deaccent(s) for s in d.get("sentence_refs", [])]
    for ex in d.get("exercises", []):
        if isinstance(ex.get("slug"), str):
            ex["slug"] = _deaccent(ex["slug"])
        ex["sentence_refs"] = [_deaccent(s) for s in ex.get("sentence_refs", [])]
        for it in ex.get("item_refs", []):
            if isinstance(it.get("ref"), str):
                it["ref"] = _deaccent(it["ref"])
    if isinstance(d.get("body"), str):
        d["body"] = _fix_refs_in_body(d["body"])
    return d


def main() -> int:
    fixed = 0
    renamed = 0
    for f in sorted(LESSON_DIR.glob("*.json")):
        d = json.loads(f.read_text(encoding="utf-8"))
        before = json.dumps(d, ensure_ascii=False)
        d = fix_record(d)
        after = json.dumps(d, ensure_ascii=False)
        # target filename = ASCII slug tail
        slug_tail = d["slug"].split(":", 1)[1] if ":" in d.get("slug", "") else f.stem
        target = LESSON_DIR / f"{slug_tail}.json"
        changed = after != before
        if f.name != target.name:
            # accented filename (or mismatch): write content to ASCII target (overwrite stale sibling), drop f
            target.write_text(json.dumps(d, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            f.unlink()
            renamed += 1
            print(f"  renamed {f.name} -> {target.name} (overwrote stale)")
        elif changed:
            f.write_text(json.dumps(d, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            fixed += 1
    print(f"de-accented identifiers in {fixed} file(s); reconciled {renamed} accented filename(s)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
