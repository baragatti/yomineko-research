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
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from i18n_text import set_text  # noqa: E402

LEVEL_ORDER = {None: 0, "pre-n5": 1, "n5": 2, "n4": 3, "n3": 4, "n2": 5, "n1": 6}
ORDER_LEVEL = {v: k for k, v in LEVEL_ORDER.items()}

# Content blocklist: sentences removed for appropriateness (sexual/creepy/etc., unfit for a general
# learner course). This is the durable chokepoint — persist() skips these slugs/jp_sources, so they can
# never re-enter the bank via replay_all or a re-mine. Edit research/derived/content_blocklist.json to manage.
_BLOCKLIST_PATH = Path(__file__).resolve().parents[2] / "research" / "derived" / "content_blocklist.json"


def _load_blocklist() -> tuple[set[str], set[str]]:
    if not _BLOCKLIST_PATH.exists():
        return set(), set()
    rows = json.loads(_BLOCKLIST_PATH.read_text(encoding="utf-8"))
    return ({r["slug"] for r in rows if r.get("slug")},
            {r["jp"] for r in rows if r.get("jp")})


BLOCKED_SLUGS, BLOCKED_JP = _load_blocklist()


def computed_level(con: sqlite3.Connection, vocab_ids, kanji_ids, fallback="n5") -> str:
    levels = [r[0] for r in con.execute(
        f"SELECT level FROM vocab WHERE id IN ({','.join('?'*len(vocab_ids))})", vocab_ids)] if vocab_ids else []
    levels += [r[0] for r in con.execute(
        f"SELECT level FROM kanji WHERE id IN ({','.join('?'*len(kanji_ids))})", kanji_ids)] if kanji_ids else []
    mx = max([LEVEL_ORDER.get(x, 0) for x in levels] + [LEVEL_ORDER.get(fallback, 2)])
    return ORDER_LEVEL[mx]


def recompute_all_levels(con: sqlite3.Connection) -> int:
    cur = con.cursor()
    n = 0
    for (sid,) in con.execute("SELECT id FROM sentence"):
        vids = [r[0] for r in con.execute("SELECT vocab_id FROM sentence_vocab WHERE sentence_id=?", (sid,))]
        kids = [r[0] for r in con.execute("SELECT kanji_id FROM sentence_kanji WHERE sentence_id=?", (sid,))]
        lvl = computed_level(con, vids, kids)
        cur.execute("UPDATE sentence SET level=? WHERE id=?", (lvl, sid))
        n += 1
    con.commit()
    return n


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
    if slug in BLOCKED_SLUGS or rec.get("jp") in BLOCKED_JP:
        return -1  # content-blocklisted (see research/derived/content_blocklist.json); never persist
    existing = cur.execute("SELECT id FROM sentence WHERE slug=?", (slug,)).fetchone()
    if existing:
        return existing[0]
    sk = diss.skeleton(rec["jp"])
    tier = rec.get("tier", "full")
    en = rec.get("en")
    level = computed_level(con, sk["vocab_ids"], sk["kanji_ids"], rec.get("level", "n5"))
    cur.execute(
        "INSERT INTO sentence (slug,jp,kana,romaji,en,level,jp_source,pt_source,"
        "pt_validated_against,translation_confidence,difficulty,tags,"
        "new_items,dissection_tier,ai_generated,verified,source,created_by,layer,needs_review) "
        "VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
        (slug, rec["jp"], sk["kana"], sk["romaji"], en,
         level, rec["jp_source"], "ai",
         "en" if en else "dict", rec.get("translation_confidence"),
         float(len(rec["jp"])),
         json.dumps(rec.get("tags", []), ensure_ascii=False),
         json.dumps(rec.get("new_items", []), ensure_ascii=False),
         tier, int(rec.get("ai_generated", 0)), 0, rec["jp_source"], "ai", "B", 1))
    sid = cur.lastrowid
    # Layer-B localized content -> localized_text (neutral fields)
    set_text(con, "sentence", sid, "translation", rec.get("pt"), layer="B")
    set_text(con, "sentence", sid, "translation_literal", rec.get("pt_literal"), layer="B")
    set_text(con, "sentence", sid, "structure_explanation", rec.get("structure_explanation_pt"), layer="C")

    # C tokens (+ Layer-B merge) — build position->token_id map
    tokmap: dict[int, int] = {}
    tlb = rec.get("tokens", {})
    for t in sk["tokens"]:
        lb = tlb.get(t["position"], {})
        cur.execute(
            "INSERT INTO token (sentence_id,position,split_mode,parent_token_id,surface,lemma,reading,"
            "romaji,pos_coarse,pos_fine,pos,inflection,inflection_type,vocab_id,kanji_ids) "
            "VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (sid, t["position"], "C", None, t["surface"], t["lemma"], t["reading"], t["romaji"],
             t["pos_coarse"], t["pos_fine"], t.get("pos"), t.get("inflection"),
             t.get("inflection_type"), t["vocab_id"], json.dumps(t["kanji_ids"])))
        tid = cur.lastrowid
        tokmap[t["position"]] = tid
        set_text(con, "token", tid, "role", lb.get("role_pt"), layer="B")
        set_text(con, "token", tid, "gloss", lb.get("gloss_pt"), layer="B")
        set_text(con, "token", tid, "conjugation_note", lb.get("conjugation_note_pt"), layer="B")
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
            "INSERT INTO particle (sentence_id,token_id,particle,function_type) VALUES (?,?,?,?)",
            (sid, tokmap.get(p["position"]), p["particle"], p.get("function_type")))
        pid = cur.lastrowid
        set_text(con, "particle", pid, "function", lb.get("function_pt"), layer="B")
        set_text(con, "particle", pid, "explanation", lb.get("explanation_pt"), layer="C")
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
