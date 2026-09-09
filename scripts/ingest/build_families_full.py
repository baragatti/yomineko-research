#!/usr/bin/env python3
"""P4b — complete family coverage: every item the course TEACHES is in at least one family.

Builds, on top of the class families of `build_families.py`:
  * `topic_set`      one per topic, over the grammar points that topic unlocks, and one per topic
                     over the kanji it unlocks;
  * `word_family`    vocab sharing a leading kanji (>= 2 members), derivational/compound groups;
  * `topic_residual` per topic, the vocabulary that no word family and no conjugation class already
                     groups — the leftovers, named for what they are.

W11b — TWO NAMES THAT LIED, AND ONE SNAPSHOT THAT FROZE
--------------------------------------------------------
`research/reports/family_layer_rebuild.md` §2.4: **272 of the 364 grammar memberships named the
wrong family.** The builder grouped grammar by `grammar_point.introducing_topic_id`, a column a P4
placement pass wrote once; the N4/N3 renumbering and every later placement pass moved the course
underneath it and nothing recomputed. A learner opening "Gramática: partículas de lugar" was shown
ている. The grouping is now derived from `lesson_unlocks` — the live course, the same ledger
`validate_unlock_ledger.py` gates and `course/**/lesson-*.json` publishes — through
`familylib.unlock_topic_map()`, so the family and the lesson cannot disagree about where a point is
taught. `scripts/validate/validate_families.py` F1/F2 assert exactly that.

And the two types were misnamed. A grouping keyed on the introducing topic is not a `function_set`
(a communicative function — asking, requesting, comparing — is independent of topic order), and a
bucket holding whatever vocabulary fell through the other rules is not a `semantic_field` (food,
body, transport are meaning judgements no Layer-A field carries). They are `topic_set` and
`topic_residual`. The rename happens HERE, before anything links the slugs, so the two honest names
are free for the authored families of W39 and no reader trusts a label the data does not earn. The
slugs themselves (`grp:gram-*`, `grp:theme-*`, `grp:kanji-topic-*`) are published addresses and do
NOT change; only the type and, for the residual buckets, the label that claimed to be a semantic
field.

Scope comes from `course_module.level`, never a hardcoded `level IN ('n5','n4')` — that literal is
why n3 had zero vocab families while its 1,596 words sat in the registry (§2.6).

Recomputes; retires a slug it no longer derives (see `scripts/familylib.py`). Run with venv python.
"""
from __future__ import annotations

import re
import sqlite3
import sys
from collections import defaultdict
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
# W01: honour --db / $YOMINEKO_DB so a rebuild can target a scratch DB (scripts/dbtarget.py).
import sys as _sys, pathlib as _pl  # noqa: E402
_sys.path.append(str(next(p for p in _pl.Path(__file__).resolve().parents if p.name == "scripts")))
from dbtarget import db_target  # noqa: E402
from familylib import (member_levels, recompute, retire_unbuilt, taught_levels,  # noqa: E402
                       unlock_order, unlock_topic_map)
from i18n_text import get_text  # noqa: E402

DB = db_target(Path(__file__).resolve().parents[2] / "db" / "corpus.sqlite")
KANJI_RE = re.compile(r"[一-鿿]")

RULE_GRAM = ("Os pontos de gramática que este tópico apresenta, na ordem em que as lições os "
             "introduzem.",
             "The grammar points this topic introduces, in the order its lessons unlock them.")
RULE_KANJI = ("Os kanji que este tópico apresenta, na ordem em que as lições os introduzem.",
              "The kanji this topic introduces, in the order its lessons unlock them.")
RULE_RESID = ("O vocabulário deste tópico que nenhuma família de palavras nem classe de conjugação "
              "já agrupa.",
              "This topic's vocabulary that no word family and no conjugation class already groups.")


def topic_titles(con) -> dict:
    """topic row id -> (slug, pt-BR title, en title). The en title is what the family's en label is
    built from; it falls back to the pt-BR one so a topic with no en title still exports a label
    rather than a null."""
    out = {}
    for tid, slug in con.execute("SELECT id, slug FROM topic"):
        pt = get_text(con, "topic", tid, "title") or ""
        en = get_text(con, "topic", tid, "title", locale="en") or pt
        out[tid] = (slug, pt, en)
    return out


def main() -> int:
    con = sqlite3.connect(DB)
    con.execute("PRAGMA foreign_keys = ON;")
    cur = con.cursor()
    levels = taught_levels(con)
    ph = ",".join("?" * len(levels))
    topics = topic_titles(con)
    unlock_topic = unlock_topic_map(con)
    order = unlock_order(con)
    built: set = set()

    # ---- grammar: one topic_set per topic, from the LIVE unlock ledger --------------------------
    by_topic_g = defaultdict(list)
    for (mtype, mid), tid in unlock_topic.items():
        if mtype == "grammar":
            by_topic_g[tid].append(mid)
    rank = 100
    for tid in sorted(by_topic_g, key=lambda t: topics[t][0]):
        slug, title_pt, title_en = topics[tid]
        members = [("grammar", g, order.get(("grammar", g))) for g in by_topic_g[tid]]
        fslug = f"grp:gram-{slug.split(':')[1]}"
        recompute(con, cur, fslug, "topic_set", rank, members, member_levels(con, members),
                  f"Gramática: {title_pt}", f"Grammar: {title_en}", *RULE_GRAM)
        built.add(fslug)
        rank += 1
    n_gram_fam, n_gram_mem = len(by_topic_g), sum(len(v) for v in by_topic_g.values())

    # ---- kanji: one topic_set per topic ----------------------------------------------------------
    # Before W11b this ran only over the kanji that no `kanji_component` family already held. D14
    # retired that cache, so the topic sets are now the whole taught kanji set, once each — which is
    # also what makes validate_families' F2 (exactly one topic-derived family per unlocked item)
    # provable instead of a coincidence of which builder ran first.
    by_topic_k = defaultdict(list)
    for (mtype, mid), tid in unlock_topic.items():
        if mtype == "kanji":
            by_topic_k[tid].append(mid)
    rank = 700
    for tid in sorted(by_topic_k, key=lambda t: topics[t][0]):
        slug, title_pt, title_en = topics[tid]
        members = [("kanji", k, order.get(("kanji", k))) for k in by_topic_k[tid]]
        fslug = f"grp:kanji-topic-{slug.split(':')[1]}"
        recompute(con, cur, fslug, "topic_set", rank, members, member_levels(con, members),
                  f"Kanji do tópico: {title_pt}", f"Topic kanji: {title_en}", *RULE_KANJI)
        built.add(fslug)
        rank += 1
    n_kanji_fam, n_kanji_mem = len(by_topic_k), sum(len(v) for v in by_topic_k.values())

    # ---- vocab: word_family by shared leading kanji ----------------------------------------------
    lead = defaultdict(list)
    for vid, hw, freq in con.execute(
            f"SELECT id, headword, freq_rank FROM vocab WHERE level IN ({ph})", levels):
        if hw and KANJI_RE.match(hw[0]):
            lead[hw[0]].append((vid, freq))
    # What already claims a word, measured from the CLASS layer this run's predecessor just
    # recomputed — never from "whatever is in family_member", which still holds the previous run's
    # residual buckets at this point and would hide every word they used to carry.
    in_fam_v = {r[0] for r in con.execute(
        "SELECT DISTINCT fm.member_id FROM family_member fm JOIN family f ON f.id = fm.family_id "
        "WHERE fm.member_type='vocab' AND f.deprecated_by IS NULL "
        "AND f.type IN ('conjugation_class','function_set')")}
    rank = 300
    n_word = 0
    for ch in sorted(lead):
        rows = lead[ch]
        if len(rows) < 2:
            continue
        fslug = f"grp:word-{ord(ch):x}"
        members = [("vocab", vid, freq) for vid, freq in rows]
        recompute(con, cur, fslug, "word_family", rank, members, member_levels(con, members),
                  f"Família de palavras com {ch}", f"Word family with {ch}",
                  f"Palavras que compartilham o kanji {ch}.", f"Words that share the kanji {ch}.")
        built.add(fslug)
        in_fam_v.update(vid for vid, _ in rows)
        rank += 1
        n_word += 1

    # ---- vocab: topic_residual, everything the rules above did not catch --------------------------
    by_topic_v = defaultdict(list)
    for (mtype, mid), tid in unlock_topic.items():
        if mtype == "vocab" and mid not in in_fam_v:
            by_topic_v[tid].append(mid)
    freq_of = {r[0]: r[1] for r in con.execute("SELECT id, freq_rank FROM vocab")}
    rank = 500
    for tid in sorted(by_topic_v, key=lambda t: topics[t][0]):
        slug, title_pt, title_en = topics[tid]
        members = [("vocab", v, freq_of.get(v)) for v in by_topic_v[tid]]
        fslug = f"grp:theme-{slug.split(':')[1]}"
        recompute(con, cur, fslug, "topic_residual", rank, members, member_levels(con, members),
                  f"Vocabulário do tópico: {title_pt}", f"Topic vocabulary: {title_en}", *RULE_RESID)
        built.add(fslug)
        rank += 1
    n_res_fam, n_res_mem = len(by_topic_v), sum(len(v) for v in by_topic_v.values())

    # ---- retire the slugs this builder owns and no longer derives ---------------------------------
    # A topic whose vocabulary is now entirely claimed by a word family or a conjugation class leaves
    # no residue, so its bucket stops existing. The address stays and redirects to the topic's own
    # family list, which is the thing that now answers "what does this topic group?".
    retired = retire_unbuilt(cur, exact=set(),
                             prefixes=("grp:gram-", "grp:kanji-topic-", "grp:word-", "grp:theme-"),
                             built=built, successor="topic.family_ids")

    con.commit()
    print(f"taught levels: {levels}")
    print(f"  topic_set (grammar):  {n_gram_fam:4d} families {n_gram_mem:6d} members")
    print(f"  topic_set (kanji):    {n_kanji_fam:4d} families {n_kanji_mem:6d} members")
    print(f"  word_family:          {n_word:4d} families")
    print(f"  topic_residual:       {n_res_fam:4d} families {n_res_mem:6d} members")
    print(f"  newly retired this run: {retired}")
    for t, total_q in (("vocab", f"SELECT count(*) FROM vocab WHERE level IN ({ph})"),
                       ("kanji", f"SELECT count(*) FROM kanji WHERE level IN ({ph})"),
                       ("grammar", "SELECT count(*) FROM grammar_point")):
        infam = con.execute("SELECT count(DISTINCT member_id) FROM family_member "
                            "WHERE member_type=?", (t,)).fetchone()[0]
        total = con.execute(total_q, levels if "level IN" in total_q else ()).fetchone()[0]
        print(f"  {t} in >=1 family: {infam}/{total}")
    nf = con.execute("SELECT COUNT(*) FROM family WHERE deprecated_by IS NULL").fetchone()[0]
    nm = con.execute("SELECT COUNT(*) FROM family_member").fetchone()[0]
    print(f"families live: {nf}; memberships: {nm}")
    con.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
