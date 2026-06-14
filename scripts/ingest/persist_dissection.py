#!/usr/bin/env python3
"""P5 — persist a dissected sentence (skeleton + authored Layer-B) into the corpus DB.

Takes a record with the raw jp + provenance + Layer-B pt-BR (translation, per-token gloss keyed
by token position, particle explanations, structure paragraph). Runs the Dissector to get the
authoritative skeleton (Layer A), merges Layer-B, and writes sentence/token/particle + the
sentence↔vocab/kanji/grammar graph edges. Idempotent by slug. Returns the sentence id.
"""
from __future__ import annotations

import json
import sqlite3


def find_grammar(con: sqlite3.Connection, term: str) -> int | None:
    row = con.execute("SELECT id FROM grammar_point WHERE key=?", (term,)).fetchone()
    if row:
        return row[0]
    row = con.execute(
        "SELECT id FROM grammar_point WHERE key LIKE ? OR structure_pattern LIKE ? "
        "ORDER BY length(key) LIMIT 1", (f"%{term}%", f"%{term}%")).fetchone()
    return row[0] if row else None


def persist(con: sqlite3.Connection, diss, rec: dict) -> int:
    cur = con.cursor()
    slug = rec["slug"]
    existing = cur.execute("SELECT id FROM sentence WHERE slug=?", (slug,)).fetchone()
    if existing:
        return existing[0]
    sk = diss.skeleton(rec["jp"])
    tier = rec.get("tier", "full")
    en = rec.get("en")
    cur.execute(
        "INSERT INTO sentence (slug,jp,kana,romaji,pt,pt_literal,en,level,jp_source,pt_source,"
        "pt_validated_against,translation_confidence,structure_explanation_pt,difficulty,tags,"
        "new_items,dissection_tier,ai_generated,verified,source,created_by,layer,needs_review) "
        "VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
        (slug, rec["jp"], sk["kana"], sk["romaji"], rec.get("pt"), rec.get("pt_literal"), en,
         rec.get("level", "n5"), rec["jp_source"], "ai",
         "en" if en else "dict", rec.get("translation_confidence"),
         rec.get("structure_explanation_pt"), float(len(rec["jp"])),
         json.dumps(rec.get("tags", []), ensure_ascii=False),
         json.dumps(rec.get("new_items", []), ensure_ascii=False),
         tier, int(rec.get("ai_generated", 0)), 0, rec["jp_source"], "ai", "B", 1))
    sid = cur.lastrowid

    # C tokens (+ Layer-B merge) — build position->token_id map
    tokmap: dict[int, int] = {}
    tlb = rec.get("tokens", {})
    for t in sk["tokens"]:
        lb = tlb.get(t["position"], {})
        cur.execute(
            "INSERT INTO token (sentence_id,position,split_mode,parent_token_id,surface,lemma,reading,"
            "romaji,pos_coarse,pos_fine,role_pt,gloss_pt,conjugation_note_pt,vocab_id,kanji_ids) "
            "VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (sid, t["position"], "C", None, t["surface"], t["lemma"], t["reading"], t["romaji"],
             t["pos_coarse"], t["pos_fine"], lb.get("role_pt"), lb.get("gloss_pt"),
             lb.get("conjugation_note_pt"), t["vocab_id"], json.dumps(t["kanji_ids"])))
        tokmap[t["position"]] = cur.lastrowid
    # A subtokens
    for st in sk["subtokens"]:
        cur.execute(
            "INSERT INTO token (sentence_id,position,split_mode,parent_token_id,surface,lemma,reading,"
            "pos_coarse,pos_fine) VALUES (?,?,?,?,?,?,?,?,?)",
            (sid, st["parent_position"], "A", tokmap.get(st["parent_position"]), st["surface"],
             st["lemma"], st["reading"], st["pos_coarse"], st["pos_fine"]))
    # particles (+ Layer-B)
    plb = rec.get("particles", {})
    for p in sk["particles"]:
        lb = plb.get(p["position"], {})
        cur.execute(
            "INSERT INTO particle (sentence_id,token_id,particle,function_pt,explanation_pt) "
            "VALUES (?,?,?,?,?)",
            (sid, tokmap.get(p["position"]), p["particle"], lb.get("function_pt"),
             lb.get("explanation_pt")))
    # graph edges
    for vid in sk["vocab_ids"]:
        cur.execute("INSERT OR IGNORE INTO sentence_vocab (sentence_id,vocab_id) VALUES (?,?)", (sid, vid))
    for kid in sk["kanji_ids"]:
        cur.execute("INSERT OR IGNORE INTO sentence_kanji (sentence_id,kanji_id) VALUES (?,?)", (sid, kid))
    for term in rec.get("grammar_keys", []):
        gid = find_grammar(con, term)
        if gid:
            cur.execute("INSERT OR IGNORE INTO sentence_grammar (sentence_id,grammar_id,usage_note_pt) "
                        "VALUES (?,?,?)", (sid, gid, rec.get("grammar_notes", {}).get(term)))
    con.commit()
    return sid
