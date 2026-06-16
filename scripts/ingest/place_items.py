#!/usr/bin/env python3
"""P4 — persist modules/topics + place every leveled item at an introducing topic.

First-pass placement (refined to lesson level during P6 authoring):
  * modules pre-n5 / n5 / n4 and the topic sequence from design/course_outline.md.
  * vocab: assigned to the earliest topic where its POS category is unlocked (i+1 dependency
    gate) and within a per-topic frequency budget; high-frequency first, overflow cascades.
  * kanji: by frequency from the kanji-strand start (N5 T03+), cascading.
  * grammar: core points keyword-mapped to topics; the rest pooled into their level by order.
cumulative-known-set is computed from topic order at query time (no materialization needed).
Idempotent: skips if topics already placed. Run with venv python.
"""
from __future__ import annotations

import json
import sqlite3
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
ROOT = Path(__file__).resolve().parents[2]
DB = ROOT / "db" / "corpus.sqlite"

MODULES = [("mod:pre-n5", "pre-n5", 1, "Fundamentos (pré-N5)"),
           ("mod:n5", "n5", 2, "N5"), ("mod:n4", "n4", 3, "N4")]

# (order, module_level, slug, title_pt, theme_pt, [unlocked categories], vocab_cap)
TOPICS = [
    (1, "pre-n5", "top:pre-n5-orientacao", "Boas-vindas e como aprender", "método", [], 0),
    (2, "pre-n5", "top:pre-n5-sons", "Os sons do japonês e vantagens do português", "fonologia", [], 0),
    (3, "pre-n5", "top:pre-n5-hiragana", "Hiragana", "escrita", [], 0),
    (4, "pre-n5", "top:pre-n5-katakana", "Katakana", "escrita", [], 0),
    (5, "pre-n5", "top:pre-n5-pronuncia", "Pronúncia e ritmo", "fonologia", [], 0),
    (6, "pre-n5", "top:pre-n5-saudacoes", "Saudações e sobrevivência", "sobrevivência",
     ["int", "exp"], 30),
    (7, "n5", "top:n5-desu-wa", "Frases básicas: o tópico は e o copula です", "identificação",
     ["n", "pn", "conj", "pref", "suf", "prt"], 60),
    (8, "n5", "top:n5-perguntas", "Perguntas e demonstrativos", "perguntar", [], 55),
    (9, "n5", "top:n5-numeros-tempo", "Números, horas e datas", "tempo/dinheiro", ["num", "ctr"], 60),
    (10, "n5", "top:n5-verbos", "Verbos: dicionário + ます; partículas を e が", "ações", ["verb"], 70),
    (11, "n5", "top:n5-particulas-lugar", "Lugar, tempo e direção: で/に/へ/と", "lugar", ["adv"], 60),
    (12, "n5", "top:n5-passado", "Passado polido e nuances", "passado", [], 55),
    (13, "n5", "top:n5-adjetivos", "Adjetivos い e な", "descrever", ["adj-i", "adj-na"], 70),
    (14, "n5", "top:n5-comparacoes", "Comparações, desejos e preferências", "preferências", [], 55),
    (15, "n5", "top:n5-te-form", "A forma て e seus usos", "conectar ações", [], 55),
    (16, "n5", "top:n5-convites", "Convites, sugestões e habilidade", "interação", [], 50),
    (17, "n5", "top:n5-rotina", "Rotina, frequência e advérbios", "rotina", [], 50),
    (18, "n5", "top:n5-conectando", "Conectando ideias e opiniões", "discurso", [], 50),
    (19, "n5", "top:n5-revisao", "Revisão N5 e consolidação", "revisão", [], 100000),
    (20, "n4", "top:n4-forma-simples", "Forma simples e registro casual", "registro", [], 55),
    (21, "n4", "top:n4-oracoes-relativas", "Orações relativas", "descrever", [], 50),
    (22, "n4", "top:n4-condicionais", "Condicionais (たら/ば/と/なら)", "hipóteses", [], 50),
    (23, "n4", "top:n4-potencial", "Potencial", "capacidade", [], 45),
    (24, "n4", "top:n4-volitivo", "Volitivo e intenção", "intenção", [], 45),
    (25, "n4", "top:n4-transitividade", "Transitivos × intransitivos", "pares verbais", [], 45),
    (26, "n4", "top:n4-dar-receber", "Dar e receber", "favores", [], 40),
    (27, "n4", "top:n4-experiencia", "Experiência e mudança", "experiência", [], 40),
    (28, "n4", "top:n4-obrigacao", "Obrigação e permissão", "deveres", [], 40),
    (29, "n4", "top:n4-aspecto", "Tentar, preparar, completar", "aspecto", [], 40),
    (30, "n4", "top:n4-suposicao", "Aparência e suposição", "inferir", [], 40),
    (31, "n4", "top:n4-passiva", "Voz passiva", "passiva", [], 40),
    (32, "n4", "top:n4-causativa", "Causativa e causativa-passiva", "causar", [], 40),
    (33, "n4", "top:n4-keigo", "Keigo básico", "formalidade", [], 40),
    (34, "n4", "top:n4-conectores", "Conectores avançados", "discurso", [], 45),
    (35, "n4", "top:n4-revisao", "Revisão N4 e can-do", "revisão", [], 100000),
]

def category(pos_lists: list[list[str]]) -> str:
    tags = {t for pl in pos_lists for t in (pl or [])}
    if any(t.startswith("v") for t in tags):
        return "verb"
    if any(t.startswith("adj-i") for t in tags):
        return "adj-i"
    if any(t.startswith("adj-na") or t.startswith("adj-no") for t in tags):
        return "adj-na"
    for cat in ("num", "ctr", "pn", "int", "conj", "exp", "pref", "suf", "adv", "prt"):
        if any(t == cat or t.startswith(cat) for t in tags):
            return cat
    return "n"


def main() -> int:
    con = sqlite3.connect(DB)
    con.execute("PRAGMA foreign_keys = ON;")
    cur = con.cursor()
    if con.execute("SELECT COUNT(*) FROM topic").fetchone()[0] == 0:
        mod_id = {}
        for slug, level, order, title in MODULES:
            cur.execute("INSERT INTO course_module (slug,level,ord,title_pt,source,created_by,layer,"
                        "needs_review) VALUES (?,?,?,?,?,?,?,?)",
                        (slug, level, order, title, "outline", "ai", "C", 1))
            mod_id[level] = cur.lastrowid
        for order, level, slug, title, theme, unlocks, cap in TOPICS:
            cur.execute("INSERT INTO topic (slug,module_id,ord,title_pt,theme_pt,source,created_by,layer,"
                        "needs_review) VALUES (?,?,?,?,?,?,?,?,?)",
                        (slug, mod_id[level], order, title, theme, "outline", "ai", "C", 1))
        con.commit()
    # build maps (DB ids + TOPICS constants) — re-runnable
    topic_id = {s: i for s, i in con.execute("SELECT slug, id FROM topic")}
    topic_order = {t[2]: t[0] for t in TOPICS}
    topic_level = {t[2]: t[1] for t in TOPICS}
    topic_cap = {t[2]: t[6] for t in TOPICS}
    # reset placements so the script can be re-run after cap/map changes
    cur.execute("UPDATE vocab SET introducing_topic_id=NULL WHERE level IN ('n5','n4')")
    cur.execute("UPDATE kanji SET introducing_topic_id=NULL WHERE level IN ('n5','n4')")
    cur.execute("UPDATE grammar_point SET introducing_topic_id=NULL WHERE level IN ('n5','n4')")
    con.commit()

    # cumulative unlock order per category (min global order at which a category is teachable)
    gate: dict[str, int] = {}
    for order, level, slug, title, theme, unlocks, cap in TOPICS:
        for c in unlocks:
            gate.setdefault(c, order)
    DEFAULT_GATE = 7  # nouns etc. from first N5 topic
    ordered_topics = [t[2] for t in TOPICS]
    first_order = {"pre-n5": 1, "n5": 7, "n4": 20}
    last_topic = {"n5": "top:n5-revisao", "n4": "top:n4-revisao"}

    # ---- vocab placement ----
    vocab = []
    for vid, level, freq in con.execute(
            "SELECT id, level, freq_rank FROM vocab WHERE level IN ('n5','n4')"):
        poss = [json.loads(r[0]) for r in con.execute(
            "SELECT pos FROM vocab_sense WHERE vocab_id=? AND pos IS NOT NULL", (vid,))]
        cat = category(poss)
        g = gate.get(cat, DEFAULT_GATE)
        # int/exp may seed pre-n5 saudacoes; everything else cannot precede its module's first topic
        earliest = g if cat in ("int", "exp") else max(g, first_order[level])
        vocab.append({"id": vid, "level": level, "freq": freq if freq is not None else 10**9,
                      "cat": cat, "earliest": earliest})
    vocab.sort(key=lambda v: v["freq"])  # high-frequency first
    placed_v = {}
    count_in = {s: 0 for s in ordered_topics}
    for v in vocab:
        for slug in ordered_topics:
            o = topic_order[slug]
            if o < v["earliest"]:
                continue
            if topic_level[slug] != v["level"] and not (v["cat"] in ("int", "exp")
                                                        and slug == "top:pre-n5-saudacoes"):
                continue
            if count_in[slug] >= topic_cap[slug]:
                continue
            placed_v[v["id"]] = topic_id[slug]
            count_in[slug] += 1
            break
        else:
            placed_v[v["id"]] = topic_id[last_topic[v["level"]]]
    cur.executemany("UPDATE vocab SET introducing_topic_id=? WHERE id=?",
                    [(tid, vid) for vid, tid in placed_v.items()])

    # ---- kanji placement (from kanji strand start, by frequency) ----
    KANJI_START = {"n5": topic_order["top:n5-numeros-tempo"], "n4": first_order["n4"]}
    KANJI_CAP = {"n5": 8, "n4": 13}  # n4 has ~170 kanji over ~14 topics
    kanji = [{"id": r[0], "level": r[1], "freq": r[2] if r[2] is not None else 10**9}
             for r in con.execute("SELECT id, level, freq_rank FROM kanji WHERE level IN ('n5','n4')")]
    kanji.sort(key=lambda k: k["freq"])
    kcount = {s: 0 for s in ordered_topics}
    placed_k = {}
    for k in kanji:
        for slug in ordered_topics:
            if topic_level[slug] != k["level"]:
                continue
            if topic_order[slug] < KANJI_START[k["level"]]:
                continue
            if slug.endswith("revisao"):
                continue
            if kcount[slug] >= KANJI_CAP[k["level"]]:
                continue
            placed_k[k["id"]] = topic_id[slug]
            kcount[slug] += 1
            break
        else:
            placed_k[k["id"]] = topic_id[last_topic[k["level"]]]
    cur.executemany("UPDATE kanji SET introducing_topic_id=? WHERE id=?",
                    [(tid, kid) for kid, tid in placed_k.items()])

    # ---- grammar placement (curated P6a map: design/grammar_placement.json — AI-classified + adversarially
    # verified into dependency-correct themed topics; durable + teacher-reviewable). The earlier keyword
    # heuristic dumped 64 points into topic 7 via loose substring matches ("da" in "kudasai" etc.). ----
    gmap = {}
    placement_file = ROOT / "design" / "grammar_placement.json"
    if placement_file.exists():
        for rec in json.loads(placement_file.read_text(encoding="utf-8")):
            gmap[rec["key"]] = rec["topic"]
    placed_g = {}
    unmatched = {"n5": [], "n4": []}
    for gid, level, key, pattern in con.execute(
            "SELECT id, level, key, structure_pattern FROM grammar_point WHERE level IN ('n5','n4')"):
        slug = gmap.get(key)
        if slug and topic_level.get(slug) == level and not slug.endswith("revisao"):
            placed_g[gid] = topic_id[slug]
        else:
            unmatched[level].append(gid)
    # any point not in the curated map -> spread across the level's content topics (avoids a topic-7 dump)
    for level in ("n5", "n4"):
        ctopics = [t[2] for t in TOPICS if t[1] == level and not t[2].endswith("revisao")]
        for i, gid in enumerate(unmatched[level]):
            placed_g[gid] = topic_id[ctopics[i % len(ctopics)]]
    cur.executemany("UPDATE grammar_point SET introducing_topic_id=? WHERE id=?",
                    [(tid, gid) for gid, tid in placed_g.items()])
    if any(unmatched.values()):
        print(f"  WARN grammar not in curated map (spread): n5={len(unmatched['n5'])} n4={len(unmatched['n4'])}")
    con.commit()

    # report
    print(f"modules={len(MODULES)} topics={len(TOPICS)}")
    print(f"vocab placed={len(placed_v)} kanji placed={len(placed_k)} grammar placed={len(placed_g)}")
    resid_v = sum(1 for t in placed_v.values() if t in (topic_id['top:n5-revisao'], topic_id['top:n4-revisao']))
    resid_g = sum(1 for t in placed_g.values() if t in (topic_id['top:n5-revisao'], topic_id['top:n4-revisao']))
    print(f"  vocab in residual(revisão)={resid_v}; grammar in residual={resid_g}")
    con.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
