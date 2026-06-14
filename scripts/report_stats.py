#!/usr/bin/env python3
"""Write reports/stats.md — row counts per table + key metrics. Re-runnable each phase."""
from __future__ import annotations

import datetime as _dt
import sqlite3
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / "db" / "corpus.sqlite"
OUT = ROOT / "reports" / "stats.md"


def main() -> int:
    con = sqlite3.connect(DB)
    tables = [r[0] for r in con.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' "
        "AND name NOT LIKE 'raw_tatoeba_fts%' ORDER BY name")]
    counts = {t: con.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0] for t in tables}

    def q(sql: str):
        try:
            return con.execute(sql).fetchone()[0]
        except sqlite3.Error:
            return "—"

    eng_n = q("SELECT COUNT(*) FROM raw_tatoeba_translation WHERE lang='eng'")
    por_n = q("SELECT COUNT(*) FROM raw_tatoeba_translation WHERE lang='por'")

    lines = [
        "# Corpus stats",
        f"_Generated {_dt.date.today().isoformat()} from `db/corpus.sqlite`._",
        "",
        "## Row counts",
        "| table | rows |",
        "|-------|-----:|",
    ]
    for t in tables:
        lines.append(f"| {t} | {counts[t]:,} |")

    lines += [
        "",
        "## Key metrics",
        f"- kanji inventory: **{counts.get('kanji',0):,}** (readings {counts.get('kanji_reading',0):,}, "
        f"components {counts.get('kanji_component',0):,})",
        f"- kanji with KanjiVG ref: **{q('SELECT COUNT(*) FROM kanji WHERE kanjivg_ref IS NOT NULL')}**",
        f"- JMdict raw entries: **{counts.get('raw_jmdict_entry',0):,}** "
        f"(common {q('SELECT COUNT(*) FROM raw_jmdict_entry WHERE common=1')}), "
        f"forms {counts.get('raw_jmdict_form',0):,}",
        f"- Tatoeba JP sentences: **{counts.get('raw_tatoeba_sentence',0):,}** "
        f"(with audio {q('SELECT COUNT(*) FROM raw_tatoeba_sentence WHERE has_audio=1')})",
        f"- Tatoeba translations: eng={eng_n}, por={por_n}",
        f"- leveled kanji (P2): {q('SELECT COUNT(*) FROM kanji WHERE level IS NOT NULL')}",
        f"- vocab (curated, P2+): {counts.get('vocab',0):,}",
        f"- grammar points (P3+): {counts.get('grammar_point',0):,}",
        f"- dissected sentences (P5+): {counts.get('sentence',0):,}",
        f"- lessons authored (P6+): {counts.get('lesson',0):,}",
    ]
    OUT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    con.close()
    print(f"wrote {OUT.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
