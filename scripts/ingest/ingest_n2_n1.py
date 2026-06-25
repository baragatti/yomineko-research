#!/usr/bin/env python3
"""P2-N2/N1 — ADDITIVE bank-only ingest for N2 + N1 (kanji + vocab ONLY).

Per the owner directive: add N2/N1 kanji + words to the registries for FSRS study, restricted to MODERN,
in-use, exam-relevant characters (no archaic / name-only / non-Joyo). NO sentences, NO grammar, NO lessons,
NO pedagogy. Additive + idempotent (mirrors ingest_n3.py); never touches existing N5/N4/N3 rows.

MODERN/USED FILTER (the "kanjis that make sense" gate):
  * KANJI: a char is eligible only if it is JOYO (KANJIDIC grade 1-8) AND listed N2/N1 by a community
    lineage. The Joyo gate (the official 2,136 regular-use set, 2010) is what excludes jinmeiyo name-kanji
    (grade 9-10) and rare/archaic no-grade kanji. 4 independent lineages vote N2 vs N1
    (davidluzgouveia jlpt_new, AnchorI jlpt, kanjiapi.dev, Bluskyo/Tanos); level = majority (N2 wins ties),
    confidence = agreement/4. needs_review=1 (relaxed spec 1.5). English meanings backfilled (Layer A).
  * VOCAB: union of 3 N2/N1 lists (jlpt-vocab-api, Bluskyo/Tanos, open-anki), matched to JMdict, INSERT
    only ent_seqs not already present. Single open lineage (Tanos/Waller) -> needs_review + low confidence.
    Skips entries whose PRIMARY JMdict sense is archaic/obsolete (misc arch/obs/obsc) -> "not ancient".

Run with venv python AFTER the N5/N4/N3 build exists.
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
ARCHAIC = {"arch", "obs", "obsc"}  # JMdict misc -> drop if the PRIMARY sense is one of these


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


# ───────────────── N2/N1 kanji (additive, Joyo-gated, 4-lineage consensus) ─────────────────
def kanji_votes() -> dict[str, dict[str, str]]:
    votes: dict[str, dict[str, str]] = defaultdict(dict)
    dlg = json.loads((JLPT / "kanji.json").read_text(encoding="utf-8"))
    for c, v in dlg.items():
        if v.get("jlpt_new") in (1, 2):
            votes[c]["davidluzgouveia"] = f"n{v['jlpt_new']}"
    for e in json.loads((JLPT / "anchori_kanji.json").read_text(encoding="utf-8")):
        lv = (e.get("jlpt") or "").lower()
        if lv in ("n1", "n2"):
            votes[e["kanji"]]["anchori"] = lv
    for lv in ("n2", "n1"):
        for c in json.loads((JLPT / f"kanjiapi_kanji_{lv}.json").read_text(encoding="utf-8")):
            votes[c]["kanjiapi"] = lv
        p = JLPT / f"bluskyo_kanji_{lv}.csv"
        if p.exists():
            with open(p, encoding="utf-8") as f:
                for row in csv.DictReader(f):
                    c = (row.get("Kanji") or row.get("kanji") or "").strip()
                    if c:
                        votes[c]["bluskyo"] = lv
    return votes


def kanji_meanings_en() -> dict[str, list]:
    dlg = json.loads((JLPT / "kanji.json").read_text(encoding="utf-8"))
    return {c: v.get("meanings", []) for c, v in dlg.items() if v.get("meanings")}


def add_kanji(con: sqlite3.Connection) -> dict:
    cur = con.cursor()
    votes = kanji_votes()
    means = kanji_meanings_en()
    added = {"n2": 0, "n1": 0}
    non_joyo = already = missing = 0
    for ch, v in votes.items():
        row = cur.execute("SELECT level, grade, meanings_en FROM kanji WHERE character=?", (ch,)).fetchone()
        if row is None:
            missing += 1
            continue
        level_now, grade, men = row
        if level_now is not None:
            already += 1  # already n5/n4/n3 — earlier wins
            continue
        if grade is None or not (1 <= grade <= 8):  # JOYO gate — exclude jinmeiyo + rare/archaic
            non_joyo += 1
            continue
        lv = [v[s] for s in v]
        level = "n2" if lv.count("n2") >= lv.count("n1") else "n1"
        agree = len(v)
        men_en = json.dumps(means.get(ch, []), ensure_ascii=False) if (not men and means.get(ch)) else men
        cur.execute(
            "UPDATE kanji SET level=?, level_confidence=?, level_agreement=?, level_sources=?, "
            "meanings_en=?, needs_review=1 WHERE character=?",
            (level, round(agree / 4, 3), f"{agree}/4", json.dumps(v, ensure_ascii=False), men_en, ch))
        added[level] += cur.rowcount
    con.commit()
    log(f"  kanji: +{added['n2']} N2, +{added['n1']} N1  (excluded non-Joyo={non_joyo}, "
        f"already-leveled={already}, not-in-inventory={missing})")
    return added


# ───────────────── N2/N1 vocab (additive, 3-list union, JMdict-matched, non-archaic) ─────────────────
def vocab_list() -> list[tuple[str, str, str]]:
    """Union of jlpt-vocab-api + Bluskyo/Tanos + open-anki for N2 then N1 -> [(headword, reading, level)].
    N2 processed first so a word listed at both levels resolves to N2 (earlier)."""
    seen: set[tuple[str, str]] = set()
    out: list[tuple[str, str, str]] = []

    def add(hw: str, reading: str, level: str) -> None:
        hw, reading = hw.strip(), (reading or "").strip()
        if not hw:
            return
        key = (hw, hira(reading))
        if key in seen:
            return
        seen.add(key)
        out.append((hw, reading, level))

    for level in ("n2", "n1"):
        n = level[1]
        api = json.loads((JLPT / f"jlptvocabapi_{level}.json").read_text(encoding="utf-8"))
        api = api if isinstance(api, list) else api.get("words", [])
        for e in api:
            add(e.get("word", ""), e.get("furigana", ""), level)
        with open(JLPT / f"bluskyo_vocab_{level}.csv", encoding="utf-8") as f:
            for row in csv.DictReader(f):
                add(row.get("Kanji") or "", row.get("Reading") or "", level)
        oa = JLPT / f"openanki_vocab_{level}.csv"
        if oa.exists():
            with open(oa, encoding="utf-8") as f:
                for row in csv.DictReader(f):
                    add(row.get("expression") or "", row.get("reading") or "", level)
    return out


def add_vocab(con: sqlite3.Connection) -> dict:
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
    added = {"n2": 0, "n1": 0}
    unmatched = dup_existing = archaic = 0
    for hw, reading, level in vocab_list():
        seq = match_entry(norm_candidates(hw), reading)
        if seq is None:
            unmatched += 1
            continue
        if seq in existing or seq in seen_seq:
            dup_existing += 1
            continue
        e = load_entry(seq)
        if not e:
            continue
        senses = e.get("sense") or []
        if senses and any(t in ARCHAIC for t in senses[0].get("misc", [])):
            archaic += 1  # primary sense is archaic/obsolete -> not modern, skip
            continue
        seen_seq.add(seq)
        kanji_forms = [k["text"] for k in (e.get("kanji") or []) if k.get("text")]
        kana_forms = [k["text"] for k in (e.get("kana") or []) if k.get("text")]
        kana = kana_forms[0] if kana_forms else ""
        headword = kanji_forms[0] if kanji_forms else kana
        common = 1 if any(x.get("common") for x in (e.get("kanji") or []) + (e.get("kana") or [])) else 0
        pos_all = senses[0].get("partOfSpeech", []) if senses else []
        verb_class = next((cls for tag in pos_all for pre, cls in POS_VERB.items() if tag.startswith(pre)), None)
        adj_class = ("i_adj" if any(t.startswith("adj-i") for t in pos_all)
                     else "na_adj" if any(t.startswith("adj-na") for t in pos_all) else None)
        lexeme_type = ("counter" if "ctr" in pos_all else
                       "suru_verb" if (verb_class == "suru_irregular" and headword.endswith("する"))
                       else "word")
        srcs = json.dumps({"jlpt-lists": level}, ensure_ascii=False)
        cur.execute(
            "INSERT INTO vocab (slug,headword,kana,romaji,lexeme_type,verb_class,adj_class,common,"
            "jmdict_ref,level,level_confidence,level_agreement,level_sources,source,created_by,layer,"
            "needs_review) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (f"vocab:{seq}", headword, kana, romaji_of(kana), lexeme_type, verb_class, adj_class,
             common, str(seq), level, 0.34, "1/3", srcs, "jmdict:" + str(seq), "dataset", "A", 1))
        vid = cur.lastrowid
        added[level] += 1
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
    log(f"  vocab: +{added['n2']} N2, +{added['n1']} N1  (unmatched-in-JMdict={unmatched}, "
        f"already-present={dup_existing}, archaic-skipped={archaic})")
    return added


def main() -> int:
    con = sqlite3.connect(DB)
    con.execute("PRAGMA foreign_keys = ON;")
    log("== add N2/N1 kanji (additive, Joyo-gated, 4-lineage consensus) =="); add_kanji(con)
    log("== add N2/N1 vocab (additive, 3-list union, JMdict-matched, non-archaic) =="); add_vocab(con)
    by = dict(con.execute("SELECT level, COUNT(*) FROM kanji WHERE level IS NOT NULL GROUP BY level"))
    bv = dict(con.execute("SELECT level, COUNT(*) FROM vocab GROUP BY level"))
    log(f"  kanji by level now: {by}")
    log(f"  vocab by level now: {bv}")
    con.close()
    log("N2/N1 additive bank ingest done.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
