#!/usr/bin/env python3
"""Fix the contrast_pair families + grammar_related: the earlier fuzzy LIKE match linked wrong
grammar points (は→'janai-dewa-nai', etc.). Rebuild with EXACT keys. Also add a particle_set family.
Idempotent. Run with venv python."""
from __future__ import annotations

import json
import sqlite3
import sys
from pathlib import Path

DB = Path(__file__).resolve().parents[2] / "db" / "corpus.sqlite"
sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]

PAIRS = [
    ("grp:wa-vs-ga", "は (tópico) × が (sujeito)", ["wa-topic-marker", "ga"],
     "は marca o tópico/o já conhecido; が marca o sujeito/a informação nova."),
    ("grp:ni-vs-de", "に × で (lugar)", ["ni", "de"],
     "に = lugar de existência/destino/tempo; で = lugar onde a AÇÃO acontece / meio."),
]
PARTICLE_SET = ("grp:particles-core", "Partículas essenciais",
                ["wa-topic-marker", "ga", "o-wo", "ni", "de", "gp-27", "mo", "mo"],
                "As partículas de caso e tópico que cobrem ~90% do uso (は も の を が で に へ と から まで).")


def kid(con, key):
    r = con.execute("SELECT id FROM grammar_point WHERE key=?", (key,)).fetchone()
    return r[0] if r else None


def fam(cur, slug, ftype, label, rank, rule):
    row = cur.execute("SELECT id FROM family WHERE slug=?", (slug,)).fetchone()
    if row:
        cur.execute("DELETE FROM family_member WHERE family_id=?", (row[0],))
        cur.execute("UPDATE family SET label_pt=?, governing_rule_pt=?, type=? WHERE id=?",
                    (label, rule, ftype, row[0]))
        return row[0]
    cur.execute("INSERT INTO family (slug,type,label_pt,description_pt,importance_rank,governing_rule_pt,"
                "spans_levels,source,created_by,layer,needs_review) VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                (slug, ftype, label, None, rank, rule, json.dumps(["n5", "n4"]), "derived", "ai", "C", 1))
    return cur.lastrowid


def main() -> int:
    con = sqlite3.connect(DB)
    cur = con.cursor()
    cur.execute("DELETE FROM grammar_related WHERE relation='contrast'")
    n_rel = 0
    for slug, label, keys, rule in PAIRS:
        gids = [g for g in (kid(con, k) for k in keys) if g]
        fid = fam(cur, slug, "contrast_pair", label, 3, rule)
        for i, g in enumerate(gids):
            cur.execute("INSERT OR IGNORE INTO family_member (family_id,member_type,member_id,intra_order,"
                        "is_core,note_pt) VALUES (?,?,?,?,?,?)", (fid, "grammar", g, i, 1 if i == 0 else 0, None))
        for a in gids:
            for b in gids:
                if a != b:
                    cur.execute("INSERT OR IGNORE INTO grammar_related (grammar_id,related_grammar_id,relation) "
                                "VALUES (?,?,?)", (a, b, "contrast"))
                    n_rel += cur.rowcount
    # particle_set
    slug, label, keys, rule = PARTICLE_SET
    gids = []
    for k in dict.fromkeys(keys):
        g = kid(con, k)
        if g and g not in gids:
            gids.append(g)
    fid = fam(cur, slug, "particle_set", label, 2, rule)
    for i, g in enumerate(gids):
        cur.execute("INSERT OR IGNORE INTO family_member (family_id,member_type,member_id,intra_order,"
                    "is_core,note_pt) VALUES (?,?,?,?,?,?)", (fid, "grammar", g, i, 1 if i == 0 else 0, None))
    con.commit()
    print(f"contrast pairs fixed; grammar_related contrast links: {n_rel}; particle_set members: {len(gids)}")
    # verify
    for r in con.execute("SELECT g1.key,g2.key FROM grammar_related gr JOIN grammar_point g1 ON g1.id=gr.grammar_id "
                         "JOIN grammar_point g2 ON g2.id=gr.related_grammar_id WHERE gr.relation='contrast'"):
        print("  ", r)
    con.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
