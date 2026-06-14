#!/usr/bin/env python3
"""Clear the sentence bank + authored lessons so they can be rebuilt cleanly (e.g. after a
dissect.py fix). Leaves corpus registries (kanji/vocab/grammar/families) + placement intact."""
import sqlite3
import sys
from pathlib import Path

DB = Path(__file__).resolve().parents[2] / "db" / "corpus.sqlite"
TABLES = ["exercise_sentence", "exercise_item", "exercise", "lesson_sentence", "lesson_introduces",
          "lesson", "sentence_grammar", "sentence_kanji", "sentence_vocab", "particle", "token",
          "sentence"]


def main() -> int:
    con = sqlite3.connect(DB)
    cur = con.cursor()
    for t in TABLES:
        cur.execute(f"DELETE FROM {t}")
    con.commit()
    print("cleared:", ", ".join(TABLES))
    con.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
