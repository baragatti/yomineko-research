#!/usr/bin/env python3
"""Remove pointless empty furigana attributes: <jp reading="">かな</jp> -> <jp>かな</jp>.

validate_furigana flags 34 spans whose reading attribute is empty. They split cleanly:

  22 spans annotate text with NO KANJI at all (しまう, やってみる, この, を). Furigana over kana is
     meaningless, so the empty attribute is not a missing reading - it is a stray attribute. Dropping it
     is deterministic and loses nothing; the text still renders, just without an empty ruby.
  12 spans DO contain kanji. Those are genuinely missing readings and cannot be derived safely here
     (guessing a reading is exactly the fabrication the Layer-A guard exists to prevent), so they are
     left alone and reported for authoring.

Emits research/derived/fable5_validation/phase6_empty_furigana_fix.json. Applies nothing.
Usage: fable5_fix_empty_furigana.py
"""
from __future__ import annotations
import json, re, sqlite3, sys
from pathlib import Path
sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
ROOT = Path(__file__).resolve().parents[1]
FD = ROOT / "research" / "derived" / "fable5_validation"
EMPTY_TAG = re.compile(r'<jp\s+reading=""\s*>(.*?)</jp>', re.S)
KANJI = re.compile(r"[一-鿿]")
TAGS = re.compile(r"<[^>]+>")


def main() -> int:
    con = sqlite3.connect(ROOT / "db" / "corpus.sqlite")
    edits, needs_author = [], []
    for etype in ("lesson", "topic"):
        for eid, field, value in con.execute(
                "SELECT entity_id, field, value FROM localized_text WHERE entity_type=? AND locale='pt-BR'",
                (etype,)):
            if not value or 'reading=""' not in value:
                continue
            kept = []

            def repl(m):
                inner = m.group(1)
                if KANJI.search(TAGS.sub("", inner)):
                    kept.append(TAGS.sub("", inner)[:60])   # has kanji: needs a real reading
                    return m.group(0)
                return f"<jp>{inner}</jp>"

            new = EMPTY_TAG.sub(repl, value)
            for k in kept:
                needs_author.append({"entity_type": etype, "entity_id": eid, "field": field, "text": k})
            if new != value:
                edits.append({"entity_type": etype, "entity_id": eid, "field": field,
                              "current": value, "fix": new})
    con.close()
    (FD / "phase6_empty_furigana_fix.json").write_text(json.dumps(
        {"note": "Drops empty reading attributes over kana-only text (meaningless ruby). Spans whose text "
                 "contains kanji are NOT touched - a missing reading must be authored, never guessed.",
         "edits": edits, "needs_authoring": needs_author}, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"empty-furigana fix: {len(edits)} fields cleaned; {len(needs_author)} kanji spans need authoring")
    return 0


if __name__ == "__main__":
    sys.exit(main())
