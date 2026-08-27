#!/usr/bin/env python3
"""Full-stack integrity audit — cross-checks data consistency beyond the §7 dissection validator.

Provenance, ai_generated/needs_review discipline, level correctness, orphan graph edges, localized_text
health (JSON parse / em dash / orphans), enum validity, registry completeness, conjugation coverage, and
the §10 numbers. Read-only. Prints PASS/WARN/FAIL per check. Run with venv python.

WHY TWO CHECKS WERE REWRITTEN (review finding G17)
--------------------------------------------------
`chk(bad_level == 0 or "warn", …)` and `chk(cj >= conj_targets * 0.97 or "warn", …)` could not report FAIL:
in Python each expression evaluates to True or to the truthy string 'warn', never to False, and chk() only
counts a failure when the value is neither. Both are now written as an explicit True / 'warn' / False, so
the FAIL branch is reachable. The conjugation one had also been stuck on WARN since the n1/n2 vocabulary
arrived, because its denominator counted every vocab record with a verb_class/adj_class including the two
levels the bank does not cover by design — a ratio that can never reach the threshold measures nothing. It
is now scoped to the levels corpus/conjugations actually ships, where real coverage is 1,156/1,156, and
those targets are counted from the exported corpus JSON (the source of truth) rather than the index.

Usage: integrity_audit.py [--root PATH]
"""
from __future__ import annotations

import argparse
import json
import sqlite3
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "ingest"))
sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
from dissect import POS_MAP, INFLECTION_MAP, PARTICLE_FUNCTION_MAP  # noqa: E402

_ap = argparse.ArgumentParser()
_ap.add_argument("--root", default=str(Path(__file__).resolve().parents[2]),
                 help="tree to audit (default: repo root)")
ROOT = Path(_ap.parse_args().root).resolve()
DB = ROOT / "db" / "corpus.sqlite"
LV = {"pre-n5": 1, "n5": 2, "n4": 3, "n3": 4, "n2": 5, "n1": 6}
# Sentences whose declared level sits below a component's level fall back to computed_level in the app, so
# a handful are tolerable; the count is frozen here so the tolerance cannot quietly grow into the corpus.
SENTENCE_LEVEL_FALLBACK_CEILING = 585
CONJ_COVERAGE_FLOOR = 0.97  # below this the bank is missing drills for words the course teaches
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
# informational, not a check: there is no threshold a real/AI split could fail here
print(f"  [info] real vs AI sentences: {real} real ({round(100*real/n)}%) / {ai} AI ({round(100*ai/n)}%)")

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
chk(True if bad_level == 0 else ("warn" if bad_level <= SENTENCE_LEVEL_FALLBACK_CEILING else False),
    "sentence.level ≥ component levels",
    f"{bad_level} below (computed_level fallback; ceiling {SENTENCE_LEVEL_FALLBACK_CEILING})")

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

# 7. conjugation coverage — scoped to the levels the bank actually ships (n1/n2 have no bank by design,
#    and counting them made the ratio unreachable, so the check could only ever WARN).
cj = 0
bank_levels: set[str] = set()
for f in (ROOT / "corpus" / "conjugations").glob("*.json"):
    recs = json.loads(f.read_text(encoding="utf-8"))
    cj += len(recs)
    bank_levels |= {r.get("level") for r in recs if isinstance(r, dict) and r.get("level")} or {f.stem}
conj_targets = 0
for f in (ROOT / "corpus" / "vocab").glob("*.json"):
    if f.stem not in bank_levels:
        continue
    conj_targets += sum(1 for v in json.loads(f.read_text(encoding="utf-8"))
                        if v.get("verb_class") or v.get("adj_class"))
ratio = cj / conj_targets if conj_targets else 0.0
chk(True if (conj_targets and cj >= conj_targets) else ("warn" if ratio >= CONJ_COVERAGE_FLOOR else False),
    "conjugation bank covers verbs/adj",
    f"{cj}/{conj_targets} at levels {sorted(bank_levels)} (floor {CONJ_COVERAGE_FLOOR:.0%})")

# 8. §10 coverage numbers
vc = Counter(r[0] for r in c.execute("SELECT vocab_id FROM sentence_vocab"))
gc = Counter(r[0] for r in c.execute("SELECT grammar_id FROM sentence_grammar"))
for lvl in ("n5", "n4"):
    vids = [r[0] for r in c.execute("SELECT id FROM vocab WHERE level=?", (lvl,))]
    gids = [r[0] for r in c.execute("SELECT id FROM grammar_point WHERE level=?", (lvl,))]
    v3 = sum(1 for i in vids if vc.get(i, 0) >= 3)
    g5 = sum(1 for i in gids if gc.get(i, 0) >= 5)
    # informational: per-level §10 coverage is gated by validate_level_coverage advisory work,
    # not here — printing it as [PASS] claimed a check that never existed
    print(f"  [info] §10 {lvl}: vocab ≥3 {v3}/{len(vids)} ({100*v3//len(vids)}%); grammar ≥5 {g5}/{len(gids)} ({100*g5//len(gids)}%)")

print(f"\n=== audit: {fails} FAIL, {warns} WARN ===")
c.close()
sys.exit(1 if fails else 0)
