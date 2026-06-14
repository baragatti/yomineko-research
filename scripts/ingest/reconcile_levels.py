#!/usr/bin/env python3
"""P2 — level reconciliation + N5/N4 vocab promotion + per-reading tiering.

Policy (PLAN_REVIEW D1): weighted union across >=3 community lists. An item is in-scope
at the EARLIEST level any list assigns it (teach earlier); level_confidence = votes-for-
assigned / total-votes; level_agreement = "x/y"; level_sources = JSON {source: level}.

Steps:
  1) reconcile KANJI levels over the curated `kanji` inventory (4 lists).
  2) reconcile VOCAB and PROMOTE the N5/N4 set into curated `vocab` (+forms/senses/kanji
     links), matching each list entry to a JMdict entry (normalize: split `;`/`/`, strip
     `～`, drop parentheticals, split する). romaji via jaconv.
  3) seed per-reading `introduced_at_level` from the leveled vocab (heuristic, needs_review).
  4) write disagreements/unmatched to reports/validation.md.

Idempotent: skips kanji-leveling / vocab-promotion if already done. Run with venv python.
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
VALID = ROOT / "reports" / "validation.md"


def log(m: str) -> None:
    print(m, flush=True)


def hira(s: str) -> str:
    return jaconv.kata2hira(s or "")


def romaji_of(kana: str) -> str:
    return jaconv.kana2alphabet(hira(kana)) if kana else ""


# ───────────────── list loaders → {source_name: {item: level}} ─────────────────
def kanji_lists() -> dict[str, dict[str, str]]:
    out: dict[str, dict[str, str]] = {}
    # davidluzgouveia kanji.json (jlpt_new)
    kj = json.loads((JLPT / "kanji.json").read_text(encoding="utf-8"))
    out["davidluzgouveia"] = {c: f"n{v['jlpt_new']}" for c, v in kj.items()
                              if v.get("jlpt_new") in (4, 5)}
    # kanjiapi.dev (arrays per level)
    d = {}
    for lvl, fn in (("n5", "kanjiapi_kanji_n5.json"), ("n4", "kanjiapi_kanji_n4.json")):
        for ch in json.loads((JLPT / fn).read_text(encoding="utf-8")):
            d[ch] = lvl
    out["kanjiapi"] = d
    # anchori (flat array, jlpt field "N5"/"N4")
    d = {}
    for o in json.loads((JLPT / "anchori_kanji.json").read_text(encoding="utf-8")):
        j = (o.get("jlpt") or "").lower()
        if j in ("n5", "n4"):
            d[o["kanji"]] = j
    out["anchori"] = d
    # bluskyo kanji csvs (col Kanji)
    d = {}
    for lvl, fn in (("n5", "bluskyo_kanji_n5.csv"), ("n4", "bluskyo_kanji_n4.csv")):
        with open(JLPT / fn, encoding="utf-8") as f:
            for row in csv.DictReader(f):
                ch = (row.get("Kanji") or row.get("kanji") or "").strip()
                if ch:
                    d[ch] = lvl
    out["bluskyo"] = d
    return out


def vocab_lists() -> dict[str, list[tuple[str, str, str]]]:
    """{source: [(headword_raw, reading, level)]}"""
    out: dict[str, list[tuple[str, str, str]]] = {}

    def csv_expr(fn: str, lvl: str, src: list, hk="expression", rk="reading"):
        with open(JLPT / fn, encoding="utf-8") as f:
            for row in csv.DictReader(f):
                hw = (row.get(hk) or "").strip()
                if hw:
                    src.append((hw, (row.get(rk) or "").strip(), lvl))

    out["elzup"] = []
    csv_expr("n5.csv", "n5", out["elzup"]); csv_expr("n4.csv", "n4", out["elzup"])
    out["openanki"] = []
    csv_expr("openanki_vocab_n5.csv", "n5", out["openanki"])
    csv_expr("openanki_vocab_n4.csv", "n4", out["openanki"])
    out["bluskyo"] = []
    csv_expr("bluskyo_vocab_n5.csv", "n5", out["bluskyo"], hk="Kanji", rk="Reading")
    csv_expr("bluskyo_vocab_n4.csv", "n4", out["bluskyo"], hk="Kanji", rk="Reading")
    out["jlptvocabapi"] = []
    for lvl, fn in (("n5", "jlptvocabapi_n5.json"), ("n4", "jlptvocabapi_n4.json")):
        data = json.loads((JLPT / fn).read_text(encoding="utf-8"))
        words = data.get("words", []) if isinstance(data, dict) else data
        for w in words:
            hw = (w.get("word") or "").strip()
            if hw:
                out["jlptvocabapi"].append((hw, (w.get("furigana") or "").strip(), lvl))
    return out


def assign(votes: dict[str, str]) -> tuple[str, float, str, str]:
    """votes={source:level}; earliest level wins; returns (level, conf, agreement, sources_json)."""
    levels = set(votes.values())
    lvl = "n5" if "n5" in levels else ("n4" if "n4" in levels else next(iter(levels)))
    n_for = sum(1 for v in votes.values() if v == lvl)
    total = len(votes)
    return lvl, round(n_for / total, 3), f"{n_for}/{total}", json.dumps(votes, ensure_ascii=False)


# ───────────────────────── normalization ─────────────────────────
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


# ───────────────────────── main ─────────────────────────
def reconcile_kanji(con: sqlite3.Connection) -> dict:
    leveled = con.execute("SELECT COUNT(*) FROM kanji WHERE level IS NOT NULL").fetchone()[0]
    if leveled > 0:
        log(f"  [skip] kanji already leveled ({leveled})")
        return {}
    lists = kanji_lists()
    votes: dict[str, dict[str, str]] = defaultdict(dict)
    for src, d in lists.items():
        for ch, lvl in d.items():
            votes[ch][src] = lvl
    cur = con.cursor()
    disagreements = []
    n = 0
    for ch, v in votes.items():
        lvl, conf, agree, srcs = assign(v)
        if len(set(v.values())) > 1:
            disagreements.append((ch, dict(v)))
        cur.execute("UPDATE kanji SET level=?, level_confidence=?, level_agreement=?, level_sources=? "
                    "WHERE character=?", (lvl, conf, agree, srcs, ch))
        n += cur.rowcount
    con.commit()
    by_lvl = dict(con.execute("SELECT level, COUNT(*) FROM kanji WHERE level IS NOT NULL GROUP BY level"))
    log(f"  kanji leveled: {n} (by level {by_lvl}); disagreements: {len(disagreements)}")
    return {"kanji_total": n, "kanji_by_level": by_lvl, "kanji_disagreements": disagreements,
            "kanji_lists": {k: len(v) for k, v in lists.items()}}


def reconcile_vocab(con: sqlite3.Connection) -> dict:
    if con.execute("SELECT COUNT(*) FROM vocab").fetchone()[0] > 0:
        log(f"  [skip] vocab already populated")
        return {}
    lists = vocab_lists()
    cur = con.cursor()
    entry_cache: dict[int, dict] = {}

    def load_entry(seq: int) -> dict:
        if seq not in entry_cache:
            row = con.execute("SELECT data FROM raw_jmdict_entry WHERE ent_seq=?", (seq,)).fetchone()
            entry_cache[seq] = json.loads(row[0]) if row else {}
        return entry_cache[seq]

    def match_entry(cands: list[str], reading: str) -> int | None:
        seqs: list[tuple[int, int]] = []  # (ent_seq, is_common)
        for c in cands:
            for seq, common in con.execute(
                    "SELECT ent_seq,is_common FROM raw_jmdict_form WHERE form=?", (c,)):
                seqs.append((seq, common))
        if not seqs:
            return None
        rd = hira(reading)
        # prefer entry whose kana matches the list reading; then prefer common
        def kana_match(seq: int) -> bool:
            if not rd:
                return False
            e = load_entry(seq)
            return any(hira(k.get("text", "")) == rd for k in (e.get("kana") or []))
        seqs_sorted = sorted(set(seqs), key=lambda s: (not kana_match(s[0]), not s[1]))
        return seqs_sorted[0][0]

    # vote per ent_seq
    votes: dict[int, dict[str, str]] = defaultdict(dict)
    unmatched: list[tuple[str, str, str]] = []
    for src, items in lists.items():
        for hw, reading, lvl in items:
            seq = match_entry(norm_candidates(hw), reading)
            if seq is None:
                unmatched.append((src, hw, lvl))
            else:
                # earliest level if a source lists the same entry twice
                prev = votes[seq].get(src)
                votes[seq][src] = "n5" if "n5" in {prev, lvl} else lvl

    POS_VERB = {"v1": "ichidan", "v5": "godan", "vs": "suru_irregular", "vk": "kuru_irregular"}
    n_vocab = 0
    for seq, v in votes.items():
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
        lvl, conf, agree, srcs = assign(v)
        cur.execute(
            "INSERT INTO vocab (slug,headword,kana,romaji,lexeme_type,verb_class,adj_class,common,"
            "jmdict_ref,level,level_confidence,level_agreement,level_sources,source,created_by,layer,"
            "needs_review) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (f"vocab:{seq}", headword, kana, romaji_of(kana), lexeme_type, verb_class, adj_class,
             common, str(seq), lvl, conf, agree, srcs, f"jmdict:{seq}", "dataset", "A", 0))
        vid = cur.lastrowid
        n_vocab += 1
        # forms
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
        # senses (gloss_en now; gloss_pt later in Layer B)
        for i, s in enumerate(senses):
            gloss_en = [g["text"] for g in s.get("gloss", []) if g.get("text")]
            cur.execute("INSERT INTO vocab_sense (vocab_id,sense_order,pos,field_tags,misc_tags,"
                        "gloss_en,gloss_pt,needs_review) VALUES (?,?,?,?,?,?,?,?)",
                        (vid, i, json.dumps(s.get("partOfSpeech", [])),
                         json.dumps(s.get("field", [])), json.dumps(s.get("misc", [])),
                         json.dumps(gloss_en, ensure_ascii=False), None, 1))
        # vocab_kanji links (kanji in headword present in inventory)
        for pos, ch in enumerate(headword):
            kid = con.execute("SELECT id FROM kanji WHERE character=?", (ch,)).fetchone()
            if kid:
                cur.execute("INSERT OR IGNORE INTO vocab_kanji (vocab_id,kanji_id,position) "
                            "VALUES (?,?,?)", (vid, kid[0], pos))
    con.commit()
    by_lvl = dict(con.execute("SELECT level, COUNT(*) FROM vocab GROUP BY level"))
    log(f"  vocab promoted: {n_vocab} (by level {by_lvl}); unmatched list entries: {len(unmatched)}")
    return {"vocab_total": n_vocab, "vocab_by_level": by_lvl, "unmatched": unmatched,
            "vocab_lists": {k: len(v) for k, v in lists.items()}}


def seed_reading_tiers(con: sqlite3.Connection) -> int:
    """Heuristic: a kanji reading is introduced at the earliest level of a leveled vocab that
    contains the kanji AND whose kana contains the reading (hiragana). needs_review=1."""
    cur = con.cursor()
    # map kanji_id -> leveled vocab [(level, kana)]
    rows = con.execute(
        "SELECT vk.kanji_id, v.level, v.kana FROM vocab_kanji vk JOIN vocab v ON v.id=vk.vocab_id "
        "WHERE v.level IS NOT NULL").fetchall()
    by_kanji: dict[int, list[tuple[str, str]]] = defaultdict(list)
    for kid, lvl, kana in rows:
        by_kanji[kid].append((lvl, hira(kana)))
    n = 0
    for kid, vocs in by_kanji.items():
        for rid, reading, okv in con.execute(
                "SELECT id, reading, okurigana FROM kanji_reading WHERE kanji_id=?", (kid,)):
            rd = hira(reading)
            if not rd:
                continue
            hits = [lvl for lvl, kana in vocs if rd in kana]
            if hits:
                lvl = "n5" if "n5" in hits else "n4"
                cur.execute("UPDATE kanji_reading SET introduced_at_level=?, needs_review=1 WHERE id=?",
                            (lvl, rid))
                n += cur.rowcount
    con.commit()
    log(f"  per-reading tiers seeded (heuristic): {n}")
    return n


def write_validation(kinfo: dict, vinfo: dict, tiers: int) -> None:
    lines = ["# Validation report", "", "_Phase P2 — level reconciliation._", ""]
    lines += ["## Lists used (≥3 each — PLAN_REVIEW D1/D2)",
              f"- kanji lists: {kinfo.get('kanji_lists', {})}",
              f"- vocab lists: {vinfo.get('vocab_lists', {})}", ""]
    lines += ["## Reconciliation results",
              f"- kanji leveled: {kinfo.get('kanji_total','—')} by level {kinfo.get('kanji_by_level',{})}",
              f"- vocab promoted: {vinfo.get('vocab_total','—')} by level {vinfo.get('vocab_by_level',{})}",
              f"- per-reading tiers seeded (heuristic, needs_review): {tiers}", ""]
    dis = kinfo.get("kanji_disagreements", [])
    lines += [f"## Kanji level disagreements across lists ({len(dis)})",
              "_Assigned the earliest voted level; review these._", ""]
    for ch, v in sorted(dis, key=lambda x: x[0])[:120]:
        lines.append(f"- {ch}: {v}")
    um = vinfo.get("unmatched", [])
    lines += ["", f"## Vocab list entries unmatched in JMdict ({len(um)})",
              "_Mostly affixes/counters/grammar-like/multiword; route to grammar or handle in P4. "
              "Sample (first 80):_", ""]
    for src, hw, lvl in um[:80]:
        lines.append(f"- [{src}/{lvl}] {hw}")
    VALID.write_text("\n".join(lines) + "\n", encoding="utf-8")
    log(f"  wrote {VALID.relative_to(ROOT)}")


def main() -> int:
    con = sqlite3.connect(DB)
    con.execute("PRAGMA foreign_keys = ON;")
    log("== reconcile kanji =="); kinfo = reconcile_kanji(con)
    log("== reconcile + promote vocab =="); vinfo = reconcile_vocab(con)
    log("== seed per-reading tiers =="); tiers = seed_reading_tiers(con)
    log("== validation report ==")
    if kinfo or vinfo:
        write_validation(kinfo, vinfo, tiers)
    con.close()
    log("P2 done.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
