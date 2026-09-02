#!/usr/bin/env python3
"""Clear the sentence bank + authored lessons so they can be rebuilt cleanly (e.g. after a
dissect.py fix). Leaves corpus registries (kanji/vocab/grammar/families) + placement intact."""
import sqlite3
import sys
from pathlib import Path

# W01: honour --db / $YOMINEKO_DB so a rebuild can target a scratch DB (scripts/dbtarget.py).
import sys as _sys, pathlib as _pl  # noqa: E402
_sys.path.append(str(next(p for p in _pl.Path(__file__).resolve().parents if p.name == "scripts")))
from dbtarget import db_target  # noqa: E402

DB = db_target(Path(__file__).resolve().parents[2] / "db" / "corpus.sqlite")
TABLES = ["exercise_sentence", "exercise_item", "exercise", "lesson_sentence", "lesson_introduces",
          "lesson", "sentence_grammar", "sentence_kanji", "sentence_vocab", "particle", "token",
          "sentence"]


def main() -> int:
    con = sqlite3.connect(DB)
    cur = con.cursor()
    for t in TABLES:
        cur.execute(f"DELETE FROM {t}")
    # clear orphaned localized_text for the entity types we just wiped
    cur.execute("DELETE FROM localized_text WHERE entity_type IN "
                "('sentence','token','particle','lesson','exercise')")
    con.commit()
    print("cleared:", ", ".join(TABLES), "+ localized_text(sentence/token/particle/lesson/exercise)")
    con.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
