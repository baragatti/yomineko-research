#!/usr/bin/env python3
"""Completeness audit — checks the corpus against spec §6 (dissection standard), §10 (acceptance),
and schema_v2, reporting what's complete vs missing so P5+ can proceed with confidence."""
from __future__ import annotations

import sqlite3
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
DB = Path(__file__).resolve().parents[2] / "db" / "corpus.sqlite"
c = sqlite3.connect(DB)


def n(q, p=()):
    return c.execute(q, p).fetchone()[0]


def line(label, got, total, note=""):
    ok = "✓" if (total and got == total) else ("·" if got else "✗")
    pct = f"{round(100*got/total)}%" if total else "—"
    print(f"  [{ok}] {label}: {got}/{total} ({pct}) {note}")


print("=" * 70)
print("A. DISSECTION STANDARD (§6) — the", n("SELECT count(*) FROM sentence"), "sentences in the bank")
print("=" * 70)
S = n("SELECT count(*) FROM sentence")
def Lc(et, field, table, cond="1=1"):  # count rows of `table` that have localized_text(et, field)
    return n(f"SELECT count(*) FROM {table} x WHERE {cond} AND EXISTS (SELECT 1 FROM localized_text lt "
             f"WHERE lt.entity_type='{et}' AND lt.entity_id=x.id AND lt.field='{field}')")


line("have translation (pt)", Lc("sentence", "translation", "sentence"), S)
line("have translation_literal", Lc("sentence", "translation_literal", "sentence"), S)
line("have kana", n("SELECT count(*) FROM sentence WHERE kana IS NOT NULL"), S)
line("have romaji", n("SELECT count(*) FROM sentence WHERE romaji IS NOT NULL"), S)
line("have en (cross-check)", n("SELECT count(*) FROM sentence WHERE en IS NOT NULL"), S)
line("have structure_explanation", Lc("sentence", "structure_explanation", "sentence"), S)
line("have mode-A subtokens", n("SELECT count(DISTINCT sentence_id) FROM token WHERE split_mode='A'"), S)
line("have mode-C tokens", n("SELECT count(DISTINCT sentence_id) FROM token WHERE split_mode='C'"), S)
line("have >=1 particle row", n("SELECT count(DISTINCT sentence_id) FROM particle"), S, "(some sentences may have 0 particles)")
line("have grammar links", n("SELECT count(DISTINCT sentence_id) FROM sentence_grammar"), S)
line("have vocab links", n("SELECT count(DISTINCT sentence_id) FROM sentence_vocab"), S)
# token-level completeness (localized_text)
CONTENT = "('名詞','動詞','形容詞','形状詞','副詞','代名詞','連体詞','接続詞','感動詞')"
CT = f"x.split_mode='C' AND x.pos_coarse IN {CONTENT}"
ct = n(f"SELECT count(*) FROM token WHERE split_mode='C' AND pos_coarse IN {CONTENT}")
line("content tokens w/ gloss", Lc("token", "gloss", "token", CT), ct)
line("content tokens w/ role", Lc("token", "role", "token", CT), ct, "(§6.2 'role')")
verbs = n("SELECT count(*) FROM token WHERE split_mode='C' AND pos_coarse='動詞'")
line("verb tokens w/ conjugation_note", Lc("token", "conjugation_note", "token", "x.split_mode='C' AND x.pos_coarse='動詞'"), verbs, "(some plain dict-form verbs need none)")
P = n("SELECT count(*) FROM particle")
line("particles w/ function", Lc("particle", "function", "particle"), P)
line("particles w/ explanation", Lc("particle", "explanation", "particle"), P)

print("\n" + "=" * 70)
print("B. KANJI (§5.1 / acceptance #1)")
print("=" * 70)
K = n("SELECT count(*) FROM kanji WHERE level IS NOT NULL")
line("meanings (pt)", Lc("kanji", "meanings", "kanji", "x.level IS NOT NULL"), K)
line("strokes", n("SELECT count(*) FROM kanji WHERE level IS NOT NULL AND strokes IS NOT NULL"), K)
line("kanjivg_ref", n("SELECT count(*) FROM kanji WHERE level IS NOT NULL AND kanjivg_ref IS NOT NULL"), K)
line("level_confidence+sources", n("SELECT count(*) FROM kanji WHERE level IS NOT NULL AND level_sources IS NOT NULL"), K)
line("has >=1 reading", n("SELECT count(DISTINCT kanji_id) FROM kanji_reading kr JOIN kanji k ON k.id=kr.kanji_id WHERE k.level IS NOT NULL"), K)
line("has >=1 component", n("SELECT count(DISTINCT kanji_id) FROM kanji_component kc JOIN kanji k ON k.id=kc.kanji_id WHERE k.level IS NOT NULL"), K)
line("readings w/ introduced_at_level (on/kun)", n("SELECT count(*) FROM kanji_reading kr JOIN kanji k ON k.id=kr.kanji_id WHERE k.level IS NOT NULL AND kr.reading_type!='nanori' AND kr.introduced_at_level IS NOT NULL"), n("SELECT count(*) FROM kanji_reading kr JOIN kanji k ON k.id=kr.kanji_id WHERE k.level IS NOT NULL AND kr.reading_type!='nanori'"), "(heuristic seed)")
line("kanji_reading.example_vocab_ids", n("SELECT count(*) FROM kanji_reading WHERE example_vocab_ids IS NOT NULL"), K, "(GAP — derivable)")
line("kanji w/ >=1 example word (vocab_kanji)", n("SELECT count(DISTINCT kanji_id) FROM vocab_kanji vk JOIN kanji k ON k.id=vk.kanji_id WHERE k.level IS NOT NULL"), K)
line("kanji w/ >=1 dissected sentence", n("SELECT count(DISTINCT kanji_id) FROM sentence_kanji"), K, "(grows with P5)")

print("\n" + "=" * 70)
print("C. VOCAB (§5.2 / acceptance #2)")
print("=" * 70)
V = n("SELECT count(*) FROM vocab WHERE level IS NOT NULL")
SE = n("SELECT count(*) FROM vocab_sense")
line("senses w/ gloss (pt)", Lc("vocab_sense", "gloss", "vocab_sense"), SE)
line("vocab w/ romaji", n("SELECT count(*) FROM vocab WHERE level IS NOT NULL AND romaji IS NOT NULL"), V)
line("vocab w/ pos (sense)", n("SELECT count(DISTINCT vocab_id) FROM vocab_sense WHERE pos IS NOT NULL"), V)
line("vocab w/ pitch", n("SELECT count(DISTINCT vocab_id) FROM vocab_pitch"), V, "(89.8% expected)")
line("vocab w/ >=1 form", n("SELECT count(DISTINCT vocab_id) FROM vocab_form"), V)
line("vocab w/ level conf/sources", n("SELECT count(*) FROM vocab WHERE level IS NOT NULL AND level_sources IS NOT NULL"), V)
line("vocab w/ >=3 dissected sentences", n("SELECT count(*) FROM (SELECT vocab_id FROM sentence_vocab GROUP BY vocab_id HAVING count(*)>=3)"), V, "(P5 target)")

print("\n" + "=" * 70)
print("D. GRAMMAR (§5.3 / acceptance #3)")
print("=" * 70)
G = n("SELECT count(*) FROM grammar_point")
for f in ("label", "explanation", "formation", "nuance"):
    line(f"{f} (pt)", Lc("grammar_point", f, "grammar_point"), G)
line("register", n("SELECT count(*) FROM grammar_point WHERE register IS NOT NULL"), G)
line("grammar w/ related_point links", n("SELECT count(DISTINCT grammar_id) FROM grammar_related"), G, "(GAP — only via contrast families)")
line("grammar w/ >=5 dissected examples", n("SELECT count(*) FROM (SELECT grammar_id FROM sentence_grammar GROUP BY grammar_id HAVING count(*)>=5)"), G, "(P5 target)")

print("\n" + "=" * 70)
print("E. FAMILIES (§5.6 / acceptance #9)")
print("=" * 70)
line("vocab in >=1 family", n("SELECT count(DISTINCT member_id) FROM family_member WHERE member_type='vocab'"), V)
line("kanji in >=1 family", n("SELECT count(DISTINCT member_id) FROM family_member WHERE member_type='kanji'"), K)
line("grammar in >=1 family", n("SELECT count(DISTINCT member_id) FROM family_member WHERE member_type='grammar'"), G)
F = n("SELECT count(*) FROM family")
line("families w/ importance_rank", n("SELECT count(*) FROM family WHERE importance_rank IS NOT NULL"), F)
line("families w/ >=1 is_core member", n("SELECT count(DISTINCT family_id) FROM family_member WHERE is_core=1"), F)

print("\n" + "=" * 70)
print("F. COURSEWARE (§5.5 / acceptance #6,#12)")
print("=" * 70)
T = n("SELECT count(*) FROM topic")
line("topics w/ objectives (pt)", Lc("topic", "objectives", "topic"), T, "(authored in P6)")
line("modules w/ overview (pt)", Lc("course_module", "overview", "course_module"), n("SELECT count(*) FROM course_module"), "(P6)")
print(f"  lessons authored: {n('SELECT count(*) FROM lesson')} (P6 grows)")
print(f"  exercises: {n('SELECT count(*) FROM exercise')}")
print(f"  items w/ introducing topic: vocab {n('SELECT count(*) FROM vocab WHERE introducing_topic_id IS NOT NULL')}/{V}, "
      f"kanji {n('SELECT count(*) FROM kanji WHERE introducing_topic_id IS NOT NULL')}/{K}, "
      f"grammar {n('SELECT count(*) FROM grammar_point WHERE introducing_topic_id IS NOT NULL')}/{G}")

print("\n" + "=" * 70)
print("G. PROVENANCE (§1.1 / acceptance #5)")
print("=" * 70)
line("kanji w/ source", n("SELECT count(*) FROM kanji WHERE source IS NOT NULL AND source!=''"), n("SELECT count(*) FROM kanji"))
line("vocab w/ source", n("SELECT count(*) FROM vocab WHERE source IS NOT NULL AND source!=''"), n("SELECT count(*) FROM vocab"))
line("grammar needs_review (Layer C)", n("SELECT count(*) FROM grammar_point WHERE needs_review=1"), G)
line("vocab_sense needs_review (Layer B)", n("SELECT count(*) FROM vocab_sense WHERE needs_review=1"), SE)
line("sentences needs_review (Layer B)", n("SELECT count(*) FROM sentence WHERE needs_review=1"), S)
c.close()
