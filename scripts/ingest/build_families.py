#!/usr/bin/env python3
"""P4 — build the structural family/group set (spec §5.6, acceptance #9).

Algorithmically derivable families now: conjugation classes (godan/ichidan/する/来る),
adjective classes (i/na), counters, and kanji-component families. Each family gets members
with intra_order (by frequency) and is_core (most frequent). Semantic-field and derivational
word-families + full importance ranking are refined later (need classification). Governing
rules for conjugation classes are short pt-BR Layer-C stubs (needs_review).
Idempotent: skips if families already built. Run with venv python.
"""
from __future__ import annotations

import json
import sqlite3
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
ROOT = Path(__file__).resolve().parents[2]
DB = ROOT / "db" / "corpus.sqlite"

CONJ = [
    ("grp:godan", "conjugation_class", "Verbos godan (う)", 1,
     "Verbos do grupo I: a última sílaba está na coluna -u (く, む, る, す…) e muda de coluna "
     "conforme a forma (negativa →あ, ます →い, vontade →お etc.).", "verb_class", "godan"),
    ("grp:ichidan", "conjugation_class", "Verbos ichidan (る)", 2,
     "Verbos do grupo II: terminam em -eru/-iru e conjugam tirando る e acrescentando a "
     "terminação (食べる→食べます, 食べない, 食べて).", "verb_class", "ichidan"),
    ("grp:suru-irregular", "conjugation_class", "Verbo irregular する", 6,
     "する e os compostos 〜する são irregulares (し-, さ-, せ-); base de muitos verbos a partir "
     "de substantivos (勉強する).", "verb_class", "suru_irregular"),
    ("grp:kuru-irregular", "conjugation_class", "Verbo irregular 来る", 7,
     "来る é irregular: a leitura muda na flexão — 来(く)る → 来(き)ます → 来(こ)ない.",
     "verb_class", "kuru_irregular"),
    ("grp:i-adj", "conjugation_class", "Adjetivos い", 4,
     "Adjetivos terminados em い conjugam no próprio adjetivo (高い→高くない→高かった); não usam です "
     "para negar/passar ao passado.", "adj_class", "i_adj"),
    ("grp:na-adj", "conjugation_class", "Adjetivos な", 5,
     "Adjetivos な comportam-se como substantivos: usam な antes do substantivo e だ/です para "
     "tempo/negação (静かな, 静かじゃない).", "adj_class", "na_adj"),
]


def add_family(cur, slug, ftype, label, rank, rule):
    cur.execute(
        "INSERT INTO family (slug,type,label_pt,description_pt,importance_rank,governing_rule_pt,"
        "spans_levels,source,created_by,layer,needs_review) VALUES (?,?,?,?,?,?,?,?,?,?,?)",
        (slug, ftype, label, None, rank, rule, json.dumps(["n5", "n4"]),
         "derived", "ai", "C", 1))
    return cur.lastrowid


def add_members(cur, fid, rows):
    """rows: [(member_type, member_id, freq_rank)] ; ordered by freq, core=first."""
    rows = sorted(rows, key=lambda r: (r[2] is None, r[2] if r[2] is not None else 0))
    for i, (mtype, mid, _f) in enumerate(rows):
        cur.execute(
            "INSERT OR IGNORE INTO family_member (family_id,member_type,member_id,intra_order,is_core,note_pt)"
            " VALUES (?,?,?,?,?,?)", (fid, mtype, mid, i, 1 if i == 0 else 0, None))


def main() -> int:
    con = sqlite3.connect(DB)
    con.execute("PRAGMA foreign_keys = ON;")
    cur = con.cursor()
    if con.execute("SELECT COUNT(*) FROM family").fetchone()[0] > 0:
        print(f"[skip] families already built ({con.execute('SELECT COUNT(*) FROM family').fetchone()[0]})")
        return 0

    # conjugation + adjective classes
    for slug, ftype, label, rank, rule, col, val in CONJ:
        fid = add_family(cur, slug, ftype, label, rank, rule)
        rows = con.execute(
            f"SELECT id, freq_rank FROM vocab WHERE {col}=? AND level IS NOT NULL", (val,)).fetchall()
        add_members(cur, fid, [("vocab", r[0], r[1]) for r in rows])

    # counters
    fid = add_family(cur, "grp:counters", "function_set", "Contadores (助数詞)", 8,
                     "O contador é escolhido pela forma/categoria do objeto; muitos sofrem rendaku "
                     "(本: いっぽん/さんぼん). Fallback nativo ひとつ–とお para 1–9.")
    rows = con.execute("SELECT id, freq_rank FROM vocab WHERE lexeme_type='counter'").fetchall()
    add_members(cur, fid, [("vocab", r[0], r[1]) for r in rows])

    # kanji-component families (components appearing in >=4 leveled kanji, excluding self)
    comp_groups: dict[str, list] = {}
    for comp, kid, freq, ch, kchar in con.execute(
        "SELECT kc.component, k.id, k.freq_rank, k.character, k.character "
        "FROM kanji_component kc JOIN kanji k ON k.id=kc.kanji_id WHERE k.level IS NOT NULL"
    ):
        if comp == ch:  # skip the kanji's own char listed as a component
            continue
        comp_groups.setdefault(comp, []).append((kid, freq))
    n_comp = 0
    for comp, members in sorted(comp_groups.items()):
        if len(members) < 4:
            continue
        slug = f"grp:kanji-comp-{ord(comp):x}"
        fid = add_family(cur, slug, "kanji_component", f"Família do componente {comp}", 20 + n_comp,
                         f"Kanji que compartilham o componente {comp} (ajuda a memorizar por partes).")
        add_members(cur, fid, [("kanji", kid, f) for kid, f in members])
        n_comp += 1

    con.commit()
    nf = con.execute("SELECT COUNT(*) FROM family").fetchone()[0]
    nm = con.execute("SELECT COUNT(*) FROM family_member").fetchone()[0]
    by_type = dict(con.execute("SELECT type, COUNT(*) FROM family GROUP BY type"))
    print(f"families built: {nf} ({by_type}); members: {nm}; kanji-component families: {n_comp}")
    con.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
