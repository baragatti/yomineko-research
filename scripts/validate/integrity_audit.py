#!/usr/bin/env python3
"""Full-stack integrity audit — cross-checks data consistency beyond the §7 dissection validator.

Provenance, ai_generated/needs_review discipline, level correctness, orphan graph edges, localized_text
health (JSON parse / em dash / orphans), enum validity, registry completeness, conjugation coverage, and
the §10 numbers. Read-only. Prints PASS/WARN/FAIL per check. Run with venv python.
"""
from __future__ import annotations

import json
import sqlite3
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "ingest"))
sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
from dissect import POS_MAP, INFLECTION_MAP, PARTICLE_FUNCTION_MAP  # noqa: E402

DB = Path(__file__).resolve().parents[2] / "db" / "corpus.sqlite"
LV = {"pre-n5": 1, "n5": 2, "n4": 3, "n3": 4, "n2": 5, "n1": 6}
c = sqlite3.connect(DB)
fails = warns = 0


def chk(cond, name, detail=""):
    global fails, warns
    tag = "PASS" if cond is True else ("WARN" if cond == "warn" else "FAIL")
    if tag == "FAIL":
        fails += 1
    if tag == "WARN":
        warns += 1
    print(f"[{tag}] {name}{(' — ' + detail) if detail else ''}")


# 1. provenance + flags
n = c.execute("SELECT count(*) FROM sentence").fetchone()[0]
nosrc = c.execute("SELECT count(*) FROM sentence WHERE jp_source IS NULL OR jp_source=''").fetchone()[0]
chk(nosrc == 0, "every sentence has jp_source", f"{nosrc} missing")
gen_noreview = c.execute("SELECT count(*) FROM sentence WHERE ai_generated=1 AND needs_review=0").fetchone()[0]
chk(gen_noreview == 0, "ai_generated ⇒ needs_review", f"{gen_noreview} violations")
ai = c.execute("SELECT count(*) FROM sentence WHERE ai_generated=1").fetchone()[0]
real = n - ai
chk(True, "real vs AI sentences", f"{real} real ({100*real//n}%) / {ai} AI ({100*ai//n}%)")

# 2. level correctness: sentence.level >= max component level
bad_level = 0
vlev = {r[0]: r[1] for r in c.execute("SELECT id,level FROM vocab")}
klev = {r[0]: r[1] for r in c.execute("SELECT id,level FROM kanji")}
for sid, slvl in c.execute("SELECT id,level FROM sentence"):
    comp = [vlev.get(v) for (v,) in c.execute("SELECT vocab_id FROM sentence_vocab WHERE sentence_id=?", (sid,))]
    comp += [klev.get(k) for (k,) in c.execute("SELECT kanji_id FROM sentence_kanji WHERE sentence_id=?", (sid,))]
    mx = max([LV.get(x, 0) for x in comp] + [0])
    if mx and LV.get(slvl, 0) < mx:
        bad_level += 1
chk(bad_level == 0 or "warn", "sentence.level ≥ component levels", f"{bad_level} below (computed_level fallback)")

# 3. orphan graph edges
for tbl, col, ref in [("sentence_vocab", "vocab_id", "vocab"), ("sentence_grammar", "grammar_id", "grammar_point"),
                      ("sentence_kanji", "kanji_id", "kanji")]:
    o = c.execute(f"SELECT count(*) FROM {tbl} t LEFT JOIN {ref} r ON r.id=t.{col} WHERE r.id IS NULL").fetchone()[0]
    chk(o == 0, f"no orphan {tbl} edges", f"{o} orphans")

# 4. localized_text health
broken = 0
for (v,) in c.execute("SELECT value FROM localized_text WHERE is_list=1"):
    try:
        json.loads(v)
    except Exception:
        broken += 1
chk(broken == 0, "localized_text JSON (is_list) parses", f"{broken} broken")
emdash = c.execute("SELECT count(*) FROM localized_text WHERE value LIKE '%—%'").fetchone()[0]
chk(emdash == 0, "no em dash in localized_text", f"{emdash} found")

# 5. enum validity
badpos = c.execute("SELECT count(*) FROM token WHERE pos IS NOT NULL AND pos NOT IN ({})".format(
    ",".join("?" * len(set(POS_MAP.values())))), tuple(set(POS_MAP.values()))).fetchone()[0]
chk(badpos == 0, "token.pos values in enum", f"{badpos} invalid")
badpf = c.execute("SELECT count(*) FROM particle WHERE function_type IS NOT NULL AND function_type NOT IN ({})".format(
    ",".join("?" * len(set(PARTICLE_FUNCTION_MAP.values())))), tuple(set(PARTICLE_FUNCTION_MAP.values()))).fetchone()[0]
chk(badpf == 0, "particle.function_type values in enum", f"{badpf} invalid")

# 6. registry completeness
for lvl in ("n5", "n4"):
    kt = c.execute("SELECT count(*) FROM kanji WHERE level=?", (lvl,)).fetchone()[0]
    km = c.execute("SELECT count(*) FROM localized_text WHERE entity_type='kanji' AND field='meanings' AND "
                   "entity_id IN (SELECT id FROM kanji WHERE level=?)", (lvl,)).fetchone()[0]
    chk(km == kt, f"{lvl} kanji all have pt meanings", f"{km}/{kt}")
vno = c.execute("SELECT count(*) FROM vocab v WHERE NOT EXISTS (SELECT 1 FROM vocab_sense s WHERE s.vocab_id=v.id)").fetchone()[0]
chk(vno == 0, "every vocab has ≥1 sense", f"{vno} without")
gno = c.execute("SELECT count(*) FROM grammar_point g WHERE NOT EXISTS (SELECT 1 FROM localized_text l WHERE "
                "l.entity_type='grammar_point' AND l.entity_id=g.id AND l.field='explanation')").fetchone()[0]
chk(gno == 0, "every grammar point has explanation", f"{gno} without")

# 7. conjugation coverage
conj_targets = c.execute("SELECT count(*) FROM vocab WHERE verb_class IS NOT NULL OR adj_class IS NOT NULL").fetchone()[0]
cj = 0
for f in (Path(DB).parents[1] / "corpus" / "conjugations").glob("*.json"):
    cj += len(json.loads(f.read_text(encoding="utf-8")))
chk(cj >= conj_targets * 0.97 or "warn", "conjugation bank covers verbs/adj", f"{cj}/{conj_targets}")

# 8. §10 coverage numbers
vc = Counter(r[0] for r in c.execute("SELECT vocab_id FROM sentence_vocab"))
gc = Counter(r[0] for r in c.execute("SELECT grammar_id FROM sentence_grammar"))
for lvl in ("n5", "n4"):
    vids = [r[0] for r in c.execute("SELECT id FROM vocab WHERE level=?", (lvl,))]
    gids = [r[0] for r in c.execute("SELECT id FROM grammar_point WHERE level=?", (lvl,))]
    v3 = sum(1 for i in vids if vc.get(i, 0) >= 3)
    g5 = sum(1 for i in gids if gc.get(i, 0) >= 5)
    chk(True, f"§10 {lvl}", f"vocab ≥3 {v3}/{len(vids)} ({100*v3//len(vids)}%); grammar ≥5 {g5}/{len(gids)} ({100*g5//len(gids)}%)")

print(f"\n=== audit: {fails} FAIL, {warns} WARN ===")
c.close()
sys.exit(1 if fails else 0)
