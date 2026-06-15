#!/usr/bin/env python3
"""Parse grammar_point.structure_pattern into a clean forms[] array (neutral Japanese surface forms).

E.g. "だ / です" -> ["だ","です"]; "一番（いちばん）" -> ["一番"]; "Verb［れる・られる］" -> ["れる","られる"];
"～たほうがいい" -> ["たほうがいい"]. Strips readings (（…）), ASCII placeholders (Verb/Number/+/[]), and the
～/〜 tilde. Stores JSON in grammar_point.forms_json (added if missing). Idempotent. The pt-BR *meaning* of
each form is added later by the AI grammar pass. Run with venv python.
"""
from __future__ import annotations

import json
import re
import sqlite3
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
DB = Path(__file__).resolve().parents[2] / "db" / "corpus.sqlite"
JP = re.compile(r"[ぁ-んァ-ヶー一-龯]")


def parse_forms(pattern: str) -> list[str]:
    if not pattern:
        return []
    p = re.sub(r"（[^）]*）", "", pattern)         # drop full-width reading glosses
    p = re.sub(r"\([^)]*\)", "", p)                # drop ascii parens
    p = re.sub(r"[A-Za-z＋+\[\]［］{}＜＞<>0-9]", "", p)  # drop ascii placeholders/brackets
    out = []
    for part in re.split(r"[/／・,、|]", p):
        x = part.replace("～", "").replace("〜", "").strip()
        if x and JP.search(x) and x not in out:
            out.append(x)
    return out


def main() -> int:
    con = sqlite3.connect(DB)
    if "forms_json" not in [r[1] for r in con.execute("PRAGMA table_info(grammar_point)")]:
        con.execute("ALTER TABLE grammar_point ADD COLUMN forms_json TEXT")
    n = 0
    for gid, pat in con.execute("SELECT id, structure_pattern FROM grammar_point"):
        forms = parse_forms(pat or "")
        con.execute("UPDATE grammar_point SET forms_json=? WHERE id=?",
                    (json.dumps(forms, ensure_ascii=False) if forms else None, gid))
        if forms:
            n += 1
    con.commit()
    con.close()
    print(f"build_grammar_forms: populated forms[] for {n} grammar points")
    return 0


if __name__ == "__main__":
    sys.exit(main())
