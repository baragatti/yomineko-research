#!/usr/bin/env python3
"""P2-N3 — ADDITIVE level reconciliation for N3 (kanji + vocab).

Unlike reconcile_levels.py (a one-shot full build that SKIPS if already populated), this script ADDS
N3 rows on top of the existing N5/N4 corpus WITHOUT touching it, so the Layer-B pt-BR meanings, the
manual fixes (e.g. 看護師), placement and families all survive:

  * KANJI: set level='n3' only on kanji rows whose level IS NULL today. Votes from 3 genuinely
    agreeing lineages (davidluzgouveia jlpt_new=3, kanjiapi jlpt-3, bluskyo n3) -> real consensus (~367).
  * VOCAB: match the bluskyo N3 Tanos list (new-test, ~1835) to JMdict and INSERT only ent_seqs not
    already present as vocab. N3 vocab is SINGLE-LINEAGE open data (Tanos/Waller), so per the approved
    relaxation of spec 1.5 every N3 vocab is tagged level_confidence (low) + needs_review=1.

Idempotent: re-running adds nothing new (kanji already n3 are skipped; vocab already present are skipped).
Run with venv python AFTER the N5/N4 build exists. Mirrors reconcile_levels.py's JMdict matching exactly.
"""
from __future__ import annotations

import csv
import json
import re
import sqlite3
import sys
from collections import defaultdict
from pathlib import Path

import jaconv

sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
ROOT = Path(__file__).resolve().parents[2]
JLPT = ROOT / "research" / "datasets" / "jlpt"
DB = ROOT / "db" / "corpus.sqlite"


def log(m: str) -> None:
    print(m, flush=True)


def hira(s: str) -> str:
    return jaconv.kata2hira(s or "")


def romaji_of(kana: str) -> str:
    return jaconv.kana2alphabet(hira(kana)) if kana else ""


def norm_candidates(raw: str) -> list[str]:
    s = re.sub(r"[（(].*?[)）]", "", raw).strip()
    out: list[str] = []
    for p in re.split(r"[;；/・、,]", s):
        p = p.strip().strip("～〜~").strip().strip("-").strip()
        if not p:
            continue
        out.append(p)
        if p.endswith("する") and len(p) > 2:
            out.append(p[:-2])
    return list(dict.fromkeys(out))


# ───────────────── N3 kanji (additive) ─────────────────
def n3_kanji_votes() -> dict[str, dict[str, str]]:
    votes: dict[str, dict[str, str]] = defaultdict(dict)
    kj = json.loads((JLPT / "kanji.json").read_text(encoding="utf-8"))
    for c, v in kj.items():
        if v.get("jlpt_new") == 3:
            votes[c]["davidluzgouveia"] = "n3"
    for ch in json.loads((JLPT / "kanjiapi_kanji_n3.json").read_text(encoding="utf-8")):
        votes[ch]["kanjiapi"] = "n3"
    p = JLPT / "bluskyo_kanji_n3.csv"
    if p.exists():
        with open(p, encoding="utf-8") as f:
            for row in csv.DictReader(f):
                ch = (row.get("Kanji") or row.get("kanji") or "").strip()
                if ch:
                    votes[ch]["bluskyo"] = "n3"
    return votes


def add_n3_kanji(con: sqlite3.Connection) -> dict:
    cur = con.cursor()
    votes = n3_kanji_votes()
    added, conflicts, missing = 0, 0, 0
    for ch, v in votes.items():
        row = cur.execute("SELECT level FROM kanji WHERE character=?", (ch,)).fetchone()
        if row is None:
            missing += 1
            continue
        if row[0] is not None:
            if row[0] != "n3":
                conflicts += 1  # already n5/n4 (earlier wins) — leave it
            continue
        total = len(v)
        srcs = json.dumps(v, ensure_ascii=False)
        cur.execute("UPDATE kanji SET level='n3', level_confidence=?, level_agreement=?, "
                    "level_sources=? WHERE character=?",
                    (round(total / 3, 3), f"{total}/3", srcs, ch))
        added += cur.rowcount
    con.commit()
    log(f"  N3 kanji: +{added} leveled (conflicts already-leveled={conflicts}, not-in-inventory={missing})")
    return {"added": added}


# ───────────────── N3 vocab (additive, single-lineage) ─────────────────
def n3_vocab_list() -> list[tuple[str, str]]:
    """bluskyo N3 (clean Tanos new-test): [(headword, reading)]."""
    out: list[tuple[str, str]] = []
    with open(JLPT / "bluskyo_vocab_n3.csv", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            hw = (row.get("Kanji") or "").strip()
            if hw:
                out.append((hw, (row.get("Reading") or "").strip()))
    return out


def add_n3_vocab(con: sqlite3.Connection) -> dict:
    cur = con.cursor()
    entry_cache: dict[int, dict] = {}

    def load_entry(seq: int) -> dict:
        if seq not in entry_cache:
            row = con.execute("SELECT data FROM raw_jmdict_entry WHERE ent_seq=?", (seq,)).fetchone()
            entry_cache[seq] = json.loads(row[0]) if row else {}
        return entry_cache[seq]

    def match_entry(cands: list[str], reading: str) -> int | None:
        seqs: list[tuple[int, int]] = []
        for c in cands:
            for seq, common in con.execute(
                    "SELECT ent_seq,is_common FROM raw_jmdict_form WHERE form=?", (c,)):
                seqs.append((seq, common))
        if not seqs:
            return None
        rd = hira(reading)

        def kana_match(seq: int) -> bool:
            if not rd:
                return False
            e = load_entry(seq)
            return any(hira(k.get("text", "")) == rd for k in (e.get("kana") or []))
        return sorted(set(seqs), key=lambda s: (not kana_match(s[0]), not s[1]))[0][0]

    existing = {int(r[0]) for r in con.execute("SELECT jmdict_ref FROM vocab WHERE jmdict_ref IS NOT NULL "
                                               "AND jmdict_ref!=''") if str(r[0]).isdigit()}
    POS_VERB = {"v1": "ichidan", "v5": "godan", "vs": "suru_irregular", "vk": "kuru_irregular"}
    seen_seq: set[int] = set()
    added, unmatched, dup_existing = 0, 0, 0
    for hw, reading in n3_vocab_list():
        seq = match_entry(norm_candidates(hw), reading)
        if seq is None:
            unmatched += 1
            continue
        if seq in existing:
            dup_existing += 1  # already taught at n5/n4 (earlier wins) — skip
            continue
        if seq in seen_seq:
            continue
        seen_seq.add(seq)
        e = load_entry(seq)
        if not e:
            continue
        kanji_forms = [k["text"] for k in (e.get("kanji") or []) if k.get("text")]
        kana_forms = [k["text"] for k in (e.get("kana") or []) if k.get("text")]
        kana = kana_forms[0] if kana_forms else ""
        headword = kanji_forms[0] if kanji_forms else kana
        common = 1 if any(x.get("common") for x in (e.get("kanji") or []) + (e.get("kana") or [])) else 0
        senses = e.get("sense") or []
        pos_all = senses[0].get("partOfSpeech", []) if senses else []
        verb_class = next((cls for tag in pos_all for pre, cls in POS_VERB.items() if tag.startswith(pre)), None)
        adj_class = ("i_adj" if any(t.startswith("adj-i") for t in pos_all)
                     else "na_adj" if any(t.startswith("adj-na") for t in pos_all) else None)
        lexeme_type = ("counter" if "ctr" in pos_all else
                       "suru_verb" if (verb_class == "suru_irregular" and headword.endswith("する"))
                       else "word")
        # single open lineage (Tanos/Waller via bluskyo) -> relaxed spec 1.5: low confidence + needs_review
        srcs = json.dumps({"bluskyo": "n3"}, ensure_ascii=False)
        cur.execute(
            "INSERT INTO vocab (slug,headword,kana,romaji,lexeme_type,verb_class,adj_class,common,"
            "jmdict_ref,level,level_confidence,level_agreement,level_sources,source,created_by,layer,"
            "needs_review) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (f"vocab:{seq}", headword, kana, romaji_of(kana), lexeme_type, verb_class, adj_class,
             common, str(seq), "n3", 0.34, "1/3", srcs, "jmdict:" + str(seq), "dataset", "A", 1))
        vid = cur.lastrowid
        added += 1
        for k in (e.get("kanji") or []):
            if k.get("text"):
                cur.execute("INSERT INTO vocab_form (vocab_id,form,is_kana,is_common,is_primary) "
                            "VALUES (?,?,?,?,?)", (vid, k["text"], 0, 1 if k.get("common") else 0,
                                                   1 if k["text"] == headword else 0))
        for k in (e.get("kana") or []):
            if k.get("text"):
                cur.execute("INSERT INTO vocab_form (vocab_id,form,is_kana,is_common,is_primary) "
                            "VALUES (?,?,?,?,?)", (vid, k["text"], 1, 1 if k.get("common") else 0,
                                                   1 if (not kanji_forms and k["text"] == headword) else 0))
        for i, s in enumerate(senses):
            gloss_en = [g["text"] for g in s.get("gloss", []) if g.get("text")]
            cur.execute("INSERT INTO vocab_sense (vocab_id,sense_order,pos,field_tags,misc_tags,"
                        "gloss_en,gloss_pt,needs_review) VALUES (?,?,?,?,?,?,?,?)",
                        (vid, i, json.dumps(s.get("partOfSpeech", [])),
                         json.dumps(s.get("field", [])), json.dumps(s.get("misc", [])),
                         json.dumps(gloss_en, ensure_ascii=False), None, 1))
        for pos, ch in enumerate(headword):
            kid = con.execute("SELECT id FROM kanji WHERE character=?", (ch,)).fetchone()
            if kid:
                cur.execute("INSERT OR IGNORE INTO vocab_kanji (vocab_id,kanji_id,position) "
                            "VALUES (?,?,?)", (vid, kid[0], pos))
    con.commit()
    log(f"  N3 vocab: +{added} inserted (unmatched-in-JMdict={unmatched}, already-taught-earlier={dup_existing})")
    return {"added": added, "unmatched": unmatched}


def main() -> int:
    con = sqlite3.connect(DB)
    con.execute("PRAGMA foreign_keys = ON;")
    log("== add N3 kanji (additive) =="); add_n3_kanji(con)
    log("== add N3 vocab (additive, single-lineage + needs_review) =="); add_n3_vocab(con)
    by = dict(con.execute("SELECT level, COUNT(*) FROM kanji WHERE level IS NOT NULL GROUP BY level"))
    bv = dict(con.execute("SELECT level, COUNT(*) FROM vocab GROUP BY level"))
    log(f"  kanji by level now: {by}")
    log(f"  vocab by level now: {bv}")
    con.close()
    log("N3 additive ingest done.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
