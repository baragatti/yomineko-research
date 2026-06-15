#!/usr/bin/env python3
"""Strip the em dash (—) from authored pt-BR text — it reads as an AI tell.

Converts appositive/parenthetical em dashes to parentheses, trailing qualifiers to parentheses, and any
remaining em dash to a comma; tidies spacing. Operates on localized_text. --dry-run previews changes.
Run with venv python. Usage: clean_emdash.py [--apply]
"""
from __future__ import annotations

import re
import sqlite3
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
DB = Path(__file__).resolve().parents[2] / "db" / "corpus.sqlite"


def _tidy(s: str) -> str:
    s = re.sub(r"\s+", " ", s)
    for a, b in ((" )", ")"), ("( ", "("), (" ,", ","), (" .", "."), (",,", ","), ("()", "")):
        s = s.replace(a, b)
    return s.strip()


def fix(s: str) -> str:
    """Remove em dashes. Parenthesize a clean appositive/trailing segment only when it contains no
    existing parens (avoids nesting); otherwise fall back to a comma."""
    if not s or "—" not in s:
        return s
    # [^—()] ensures we never wrap across or inside existing parentheses
    t = re.sub(r"\s*—\s*([^—()]+?)\s*—", r" (\1) ", s)   # paired: — X — -> (X)
    t = re.sub(r"\s*—\s*([^—()]+?)\s*$", r" (\1)", t)     # trailing: X — Y -> X (Y)
    t = t.replace(" — ", ", ").replace("—", ", ")          # any remaining -> comma
    t = _tidy(t)
    if t.count("(") != t.count(")"):                       # nesting/imbalance -> comma-only fallback
        t = _tidy(s.replace(" — ", ", ").replace("—", ", "))
    return t


def main() -> int:
    import json
    apply = "--apply" in sys.argv
    con = sqlite3.connect(DB)
    rows = con.execute("SELECT entity_type,entity_id,field,locale,value,is_list FROM localized_text "
                       "WHERE value LIKE '%—%'").fetchall()
    changed = 0
    for i, (et, eid, field, loc, val, is_list) in enumerate(rows):
        if is_list:  # JSON value: clean each string leaf, never the JSON syntax
            try:
                obj = json.loads(val)
            except json.JSONDecodeError:
                continue
            if isinstance(obj, list):
                obj = [fix(x) if isinstance(x, str) else x for x in obj]
            elif isinstance(obj, dict):
                obj = {k: (fix(v) if isinstance(v, str) else v) for k, v in obj.items()}
            new = json.dumps(obj, ensure_ascii=False)
        else:
            new = fix(val)
        if new != val:
            changed += 1
            if apply:
                con.execute("UPDATE localized_text SET value=? WHERE entity_type=? AND entity_id=? "
                            "AND field=? AND locale=?", (new, et, eid, field, loc))
            elif i < 12:
                print(f"[{et}/{field}]\n  OLD: {val[:160]}\n  NEW: {new[:160]}\n")
    if apply:
        con.commit()
    print(f"{'applied' if apply else 'would change'} {changed}/{len(rows)} em-dash texts")
    con.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
