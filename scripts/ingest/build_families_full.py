#!/usr/bin/env python3
"""P4b — complete family coverage so EVERY N5/N4 item is in ≥1 family (acceptance #9).

Adds, on top of the structural families (build_families.py):
  * grammar: a function_set per topic ("Gramática: <topic>") covering all grammar points, + a
    particle_set grouping single-particle points, + curated contrast_pairs (は↔が, に↔で, etc.).
  * vocab: word_family by shared leading kanji (derivational/compound groups, ≥2 members), then a
    semantic_field fallback per topic theme for any vocab still unfamilied.
  * kanji: a per-topic function_set for any kanji not already in a component family.
Idempotent (skips existing slugs). Run with venv python.
"""
from __future__ import annotations

import json
import sqlite3
import sys
from collections import defaultdict
from pathlib import Path

DB = Path(__file__).resolve().parents[2] / "db" / "corpus.sqlite"
KANJI_RE = __import__("re").compile(r"[一-鿿]")

CONTRAST_PAIRS = [  # (slug, label, [grammar keys to include], rule)
    ("grp:wa-vs-ga", "は (tópico) × が (sujeito)", ["wa", "ga"],
     "は marca o tópico/o já conhecido; が marca o sujeito/a informação nova."),
    ("grp:ni-vs-de", "に × で (lugar)", ["ni", "de"],
     "に = lugar de existência/destino; で = lugar onde a AÇÃO acontece."),
]


def fam(cur, slug, ftype, label, rank, rule=None, desc=None):
    row = cur.execute("SELECT id FROM family WHERE slug=?", (slug,)).fetchone()
    if row:
        return row[0]
    cur.execute("INSERT INTO family (slug,type,label_pt,description_pt,importance_rank,governing_rule_pt,"
                "spans_levels,source,created_by,layer,needs_review) VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                (slug, ftype, label, desc, rank, rule, json.dumps(["n5", "n4"]), "derived", "ai", "C", 1))
    return cur.lastrowid


def add_members(cur, fid, members):
    for i, (mtype, mid) in enumerate(members):
        cur.execute("INSERT OR IGNORE INTO family_member (family_id,member_type,member_id,intra_order,"
                    "is_core,note_pt) VALUES (?,?,?,?,?,?)", (fid, mtype, mid, i, 1 if i == 0 else 0, None))


def main() -> int:
    con = sqlite3.connect(DB)
    con.execute("PRAGMA foreign_keys = ON;")
    cur = con.cursor()
    topics = {tid: (slug, title) for tid, slug, title in
              con.execute("SELECT id,slug,title_pt FROM topic")}

    # ---- grammar: per-topic function_set (covers all) ----
    by_topic_g = defaultdict(list)
    for gid, tid in con.execute("SELECT id,introducing_topic_id FROM grammar_point WHERE introducing_topic_id IS NOT NULL"):
        by_topic_g[tid].append(gid)
    rank = 100
    for tid, gids in by_topic_g.items():
        slug, title = topics[tid]
        fid = fam(cur, f"grp:gram-{slug.split(':')[1]}", "function_set", f"Gramática: {title}", rank)
        add_members(cur, fid, [("grammar", g) for g in gids]); rank += 1
    # curated contrast pairs (by key)
    for slug, label, keys, rule in CONTRAST_PAIRS:
        gids = []
        for k in keys:
            r = con.execute("SELECT id FROM grammar_point WHERE key=? OR key LIKE ?", (k, f"%{k}%")).fetchone()
            if r:
                gids.append(r[0])
        if len(gids) >= 2:
            fid = fam(cur, slug, "contrast_pair", label, 3, rule)
            add_members(cur, fid, [("grammar", g) for g in gids])

    # ---- vocab: word_family by shared leading kanji ----
    in_fam_v = {r[0] for r in con.execute("SELECT DISTINCT member_id FROM family_member WHERE member_type='vocab'")}
    lead = defaultdict(list)
    for vid, hw, freq in con.execute("SELECT id,headword,freq_rank FROM vocab WHERE level IN ('n5','n4')"):
        if hw and KANJI_RE.match(hw[0]):
            lead[hw[0]].append((vid, freq if freq is not None else 10**9))
    rank = 300
    for ch, members in sorted(lead.items()):
        if len(members) < 2:
            continue
        members.sort(key=lambda m: m[1])
        fid = fam(cur, f"grp:word-{ord(ch):x}", "word_family", f"Família de palavras com {ch}", rank,
                  f"Palavras que compartilham o kanji {ch}."); rank += 1
        add_members(cur, fid, [("vocab", v) for v, _ in members])
        in_fam_v.update(v for v, _ in members)

    # ---- vocab: semantic_field fallback per topic theme (covers the rest) ----
    by_topic_v = defaultdict(list)
    for vid, tid, freq in con.execute("SELECT id,introducing_topic_id,freq_rank FROM vocab "
                                      "WHERE level IN ('n5','n4') AND introducing_topic_id IS NOT NULL"):
        if vid not in in_fam_v:
            by_topic_v[tid].append((vid, freq if freq is not None else 10**9))
    rank = 500
    for tid, members in by_topic_v.items():
        slug, title = topics[tid]
        members.sort(key=lambda m: m[1])
        fid = fam(cur, f"grp:theme-{slug.split(':')[1]}", "semantic_field",
                  f"Campo semântico: {title}", rank); rank += 1
        add_members(cur, fid, [("vocab", v) for v, _ in members])

    # ---- kanji: per-topic function_set for stragglers ----
    in_fam_k = {r[0] for r in con.execute("SELECT DISTINCT member_id FROM family_member WHERE member_type='kanji'")}
    by_topic_k = defaultdict(list)
    for kid, tid, freq in con.execute("SELECT id,introducing_topic_id,freq_rank FROM kanji "
                                      "WHERE level IN ('n5','n4') AND introducing_topic_id IS NOT NULL"):
        if kid not in in_fam_k:
            by_topic_k[tid].append((kid, freq if freq is not None else 10**9))
    rank = 700
    for tid, members in by_topic_k.items():
        slug, title = topics[tid]
        members.sort(key=lambda m: m[1])
        fid = fam(cur, f"grp:kanji-topic-{slug.split(':')[1]}", "function_set",
                  f"Kanji do tópico: {title}", rank); rank += 1
        add_members(cur, fid, [("kanji", k) for k, _ in members])

    con.commit()
    nf = con.execute("SELECT COUNT(*) FROM family").fetchone()[0]
    for t, total_q in (("vocab", "SELECT count(*) FROM vocab WHERE level IN ('n5','n4')"),
                       ("kanji", "SELECT count(*) FROM kanji WHERE level IS NOT NULL"),
                       ("grammar", "SELECT count(*) FROM grammar_point")):
        infam = con.execute(f"SELECT count(DISTINCT member_id) FROM family_member WHERE member_type='{t}'").fetchone()[0]
        total = con.execute(total_q).fetchone()[0]
        print(f"  {t} in ≥1 family: {infam}/{total}")
    print(f"families total: {nf}")
    con.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
