#!/usr/bin/env python3
"""Tranche-3 inputs: cover the REMAINING unplaced N3 vocab + kanji as themed vocabulary-expansion lessons.
Each spec = one lesson: a DISJOINT slice (~VPER vocab + a couple kanji) attached to an existing N3 content
topic (round-robin by theme), reviewing that topic's already-taught grammar (NOT re-introducing it).
Deterministic; writes research/_n3_lesson_inputs_b.json. Run with venv python."""
from __future__ import annotations
import json, math, sqlite3, sys
from pathlib import Path
sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
ROOT = Path(__file__).resolve().parents[2]
DB = ROOT / "db" / "corpus.sqlite"
VPER = 18          # vocab introduced per expansion lesson
con = sqlite3.connect(DB)


def lt(etype, eid, field):
    r = con.execute("SELECT value FROM localized_text WHERE entity_type=? AND entity_id=? AND field=? "
                    "AND locale='pt-BR'", (etype, eid, field)).fetchone()
    return r[0] if r else ""


topics = con.execute(
    "SELECT t.id,t.slug,t.title_pt,t.theme_pt,t.ord FROM topic t JOIN course_module m ON m.id=t.module_id "
    "WHERE m.level='n3' AND t.slug NOT LIKE '%revisao%' ORDER BY t.ord").fetchall()
maxord = {}
for tid, slug, *_ in topics:
    maxord[tid] = con.execute("SELECT COALESCE(MAX(ord),0) FROM lesson WHERE topic_id=?", (tid,)).fetchone()[0]
tgrammar = {}
for tid, *_ in topics:
    tgrammar[tid] = [{"key": k, "jp": p or "", "label": lt("grammar_point", gid, "label")}
                     for gid, k, p in con.execute(
                         "SELECT id,key,structure_pattern FROM grammar_point WHERE introducing_topic_id=? "
                         "AND level='n3' ORDER BY id", (tid,))]

# unplaced vocab (common first, then frequency) with a pt gloss
vrows = con.execute(
    "SELECT v.id,v.headword,v.kana FROM vocab v WHERE v.level='n3' AND v.introducing_topic_id IS NULL "
    "ORDER BY v.common DESC, v.id").fetchall()
vpool = []
for vid, hw, kana in vrows:
    sid = con.execute("SELECT id FROM vocab_sense WHERE vocab_id=? ORDER BY sense_order LIMIT 1", (vid,)).fetchone()
    gloss = json.loads(lt("vocab_sense", sid[0], "gloss") or "[]") if sid else []
    if gloss:
        vpool.append({"hw": hw, "kana": kana, "gloss": gloss[:3]})
# unplaced kanji
krows = con.execute("SELECT id,character FROM kanji WHERE level='n3' AND introducing_topic_id IS NULL "
                    "ORDER BY (freq_rank IS NULL), freq_rank, id").fetchall()
kpool = [{"k": ch, "meaning": json.loads(lt("kanji", kid, "meanings") or "[]")[:3]} for kid, ch in krows]

n_lessons = math.ceil(len(vpool) / VPER)
specs = []
ord_cursor = dict(maxord)
ki = 0
for i in range(n_lessons):
    tid, slug, title, theme, tord = topics[i % len(topics)]
    ord_cursor[tid] += 1
    vslice = vpool[i * VPER:(i + 1) * VPER]
    kslice = kpool[ki:ki + 2]; ki += 2
    base = slug.replace("top:", "")
    specs.append({
        "slug": f"les:{base}-{ord_cursor[tid]:02d}", "topic": slug, "order": ord_cursor[tid],
        "title_pt": title, "theme_pt": theme, "review_grammar": tgrammar[tid][:4],
        "vocab": vslice, "kanji": kslice,
    })
(ROOT / "research" / "_n3_lesson_inputs_b.json").write_text(json.dumps(specs, ensure_ascii=False), encoding="utf-8")
print(f"specs={len(specs)} vocab_to_place={sum(len(s['vocab']) for s in specs)} "
      f"kanji_to_place={sum(len(s['kanji']) for s in specs)} (unplaced vocab pool={len(vpool)}, kanji={len(kpool)})")
