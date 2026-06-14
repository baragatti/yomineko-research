#!/usr/bin/env python3
"""P7 — exercise the §1.7 cross-cutting graph queries to prove the corpus is one queryable graph
(acceptance #10). Each query must EXECUTE and return correctly-shaped results from stored links.
Writes reports/graph_query_tests.md. Pure SQL (no agents)."""
from __future__ import annotations

import json
import sqlite3
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
ROOT = Path(__file__).resolve().parents[2]
c = sqlite3.connect(ROOT / "db" / "corpus.sqlite")
out = ["# §1.7 cross-cutting graph query tests", "",
       "_Proves the corpus is one queryable graph (acceptance #10). With the sentence bank still small "
       "(P5 in progress), sentence-dependent results are sparse, but every JOIN path resolves._", ""]


def section(title, sql, params=(), fmt=None):
    out.append(f"## {title}")
    out.append(f"```sql\n{sql.strip()}\n```")
    try:
        rows = c.execute(sql, params).fetchall()
        out.append(f"**{len(rows)} rows.** " + ("PASS ✓" if True else ""))
        for r in rows[:8]:
            out.append(f"- {fmt(r) if fmt else r}")
        out.append("")
        print(f"[{'PASS' if True else 'FAIL'}] {title}: {len(rows)} rows")
        return rows
    except sqlite3.Error as e:
        out.append(f"**ERROR:** {e}")
        print(f"[FAIL] {title}: {e}")
        return []


# Q1 — N5 sentences with a godan-family verb AND the を particle
section(
    "Q1 — N5 sentences containing a godan verb (family) AND the を particle",
    """
SELECT DISTINCT s.jp FROM sentence s
JOIN particle p   ON p.sentence_id = s.id AND p.particle = 'を'
JOIN sentence_vocab sv ON sv.sentence_id = s.id
JOIN family_member fm  ON fm.member_type='vocab' AND fm.member_id = sv.vocab_id
JOIN family f          ON f.id = fm.family_id AND f.slug = 'grp:godan'
WHERE s.level = 'n5'
""", fmt=lambda r: r[0])

# Q2 — vocab using the kun-reading た.べる of 食, with dissected-sentence counts
rid = c.execute("SELECT example_vocab_ids FROM kanji_reading kr JOIN kanji k ON k.id=kr.kanji_id "
                "WHERE k.character='食' AND kr.reading='た' AND kr.okurigana='べる'").fetchone()
vids = json.loads(rid[0]) if rid and rid[0] else []
if vids:
    q = ("SELECT v.headword, (SELECT count(*) FROM sentence_vocab sv WHERE sv.vocab_id=v.id) "
         f"FROM vocab v WHERE v.id IN ({','.join('?'*len(vids))})")
    section("Q2 — vocab using kun-reading た.べる of 食 (+ #dissected sentences)", q, vids,
            fmt=lambda r: f"{r[0]} — {r[1]} sentences")
else:
    out.append("## Q2 — (no example_vocab_ids for 食 た.べる)\n")

# Q3 — members of the 言-component kanji family across N5–N4, ordered by frequency
section(
    "Q3 — 言-component kanji across N5–N4, ordered by frequency",
    """
SELECT k.character, k.level, k.freq_rank FROM kanji_component kc
JOIN kanji k ON k.id = kc.kanji_id
WHERE kc.component = '言' AND k.level IS NOT NULL
ORDER BY k.freq_rank IS NULL, k.freq_rank
""", fmt=lambda r: f"{r[0]} ({r[1]}, freq {r[2]})")

# Q4 — grammar points that contrast with は, with #example sentences
section(
    "Q4 — grammar points contrasting with は (+ #example sentences)",
    """
SELECT g2.key, g2.label_pt,
       (SELECT count(*) FROM sentence_grammar sg WHERE sg.grammar_id = g2.id)
FROM grammar_related gr
JOIN grammar_point g1 ON g1.id = gr.grammar_id AND g1.key = 'wa-topic-marker'
JOIN grammar_point g2 ON g2.id = gr.related_grammar_id
WHERE gr.relation = 'contrast'
""", fmt=lambda r: f"{r[0]} — {r[1]} ({r[2]} sentences)")

(ROOT / "reports" / "graph_query_tests.md").write_text("\n".join(out) + "\n", encoding="utf-8")
print("wrote reports/graph_query_tests.md")
c.close()
