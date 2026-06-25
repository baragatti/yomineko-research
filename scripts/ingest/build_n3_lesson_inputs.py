#!/usr/bin/env python3
"""Build per-topic lesson-authoring inputs for N3: each content topic gets its grammar points (with the
pt-BR Layer-C) + a DISJOINT slice of N3 vocab and kanji to teach/unlock (disjoint => no introduce-once
collisions across topics). Writes research/_n3_lesson_inputs.json. Run with venv python."""
from __future__ import annotations
import json, sqlite3, sys
from pathlib import Path
sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
ROOT = Path(__file__).resolve().parents[2]
DB = ROOT / "db" / "corpus.sqlite"
con = sqlite3.connect(DB)


def lt(etype, eid, field):
    r = con.execute("SELECT value FROM localized_text WHERE entity_type=? AND entity_id=? AND field=? "
                    "AND locale='pt-BR'", (etype, eid, field)).fetchone()
    return r[0] if r else ""


# content topics in order (exclude revisao)
topics = con.execute(
    "SELECT t.id,t.slug,t.title_pt,t.theme_pt,t.ord FROM topic t JOIN course_module m ON m.id=t.module_id "
    "WHERE m.level='n3' AND t.slug NOT LIKE '%revisao%' ORDER BY t.ord").fetchall()

# vocab pool: N3, common first, with a pt gloss; disjoint slices
vrows = con.execute(
    "SELECT v.id,v.headword,v.kana FROM vocab v WHERE v.level='n3' ORDER BY v.common DESC, v.id").fetchall()
vocab_pool = []
for vid, hw, kana in vrows:
    sid = con.execute("SELECT id FROM vocab_sense WHERE vocab_id=? ORDER BY sense_order LIMIT 1", (vid,)).fetchone()
    gloss = json.loads(lt("vocab_sense", sid[0], "gloss") or "[]") if sid else []
    if gloss:
        vocab_pool.append({"hw": hw, "kana": kana, "gloss": gloss[:3]})
# kanji pool: N3, by frequency (common first)
krows = con.execute("SELECT id,character FROM kanji WHERE level='n3' ORDER BY (freq_rank IS NULL), freq_rank, id").fetchall()
kanji_pool = []
for kid, ch in krows:
    m = json.loads(lt("kanji", kid, "meanings") or "[]")
    kanji_pool.append({"k": ch, "meaning": m[:3]})

NT = len(topics)
VPER = min(55, max(20, len(vocab_pool) // NT))   # disjoint vocab slice per topic
KPER = max(8, len(kanji_pool) // NT)
out = []
for i, (tid, slug, title, theme, ordn) in enumerate(topics):
    gps = []
    for gid, key, pat in con.execute(
            "SELECT id,key,structure_pattern FROM grammar_point WHERE introducing_topic_id=? AND level='n3' "
            "ORDER BY id", (tid,)):
        gps.append({"key": key, "jp": pat,
                    "label": lt("grammar_point", gid, "label"),
                    "explanation": lt("grammar_point", gid, "explanation"),
                    "formation": lt("grammar_point", gid, "formation"),
                    "nuance": lt("grammar_point", gid, "nuance")})
    out.append({
        "slug": slug, "title_pt": title, "theme_pt": theme, "order": ordn,
        "grammar": gps,
        "vocab": vocab_pool[i * VPER:(i + 1) * VPER],
        "kanji": kanji_pool[i * KPER:(i + 1) * KPER],
    })
(ROOT / "research" / "_n3_lesson_inputs.json").write_text(json.dumps(out, ensure_ascii=False), encoding="utf-8")
print(f"wrote {len(out)} topic inputs; grammar={sum(len(t['grammar']) for t in out)} "
      f"vocab_assigned={sum(len(t['vocab']) for t in out)} kanji_assigned={sum(len(t['kanji']) for t in out)} "
      f"(VPER={VPER} KPER={KPER})")
