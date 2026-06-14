#!/usr/bin/env python3
"""P1 — ingest authoritative datasets into db/corpus.sqlite.

- KANJIDIC2 + Kradfile + KanjiVG  -> curated `kanji` / `kanji_reading` / `kanji_component`
  inventory (Layer A; full inventory, levels assigned later in P2).
- JMdict (common)                 -> raw_jmdict_entry / raw_jmdict_form staging (promoted to
  `vocab` for the N5/N4 set in P2).
- Tatoeba (jpn + eng/por links + audio) -> raw_tatoeba_sentence / raw_tatoeba_translation + FTS.
- dataset_source provenance rows.

Idempotent: each section is skipped if already populated. Stdlib only. Run with the venv python.
"""
from __future__ import annotations

import bz2
import datetime as _dt
import gzip
import json
import re
import sqlite3
import sys
import tarfile
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]

ROOT = Path(__file__).resolve().parents[2]
DS = ROOT / "research" / "datasets"
DB = ROOT / "db" / "corpus.sqlite"


def log(m: str) -> None:
    print(m, flush=True)


def newest(glob: str) -> Path:
    return sorted(DS.glob(glob))[-1]


def load_tgz_json(path: Path) -> dict:
    with tarfile.open(path, "r:gz") as t:
        member = next(m for m in t.getmembers() if m.name.endswith(".json"))
        return json.loads(t.extractfile(member).read().decode("utf-8"))  # type: ignore[union-attr]


def count(con: sqlite3.Connection, table: str) -> int:
    return con.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]


# ───────────────────────── kanji inventory ─────────────────────────
def ingest_kanji(con: sqlite3.Connection) -> None:
    if count(con, "kanji") > 0:
        log(f"  [skip] kanji already populated ({count(con,'kanji')})")
        return
    log("  parsing KANJIDIC2 + Kradfile + KanjiVG …")
    kd = load_tgz_json(newest("jmdict/kanjidic2-en-*.tgz"))
    krad = load_tgz_json(newest("jmdict/kradfile-*.tgz")).get("kanji", {})
    # KanjiVG present codepoints
    kvg: set[str] = set()
    with gzip.open(newest("kanjivg/kanjivg-*.xml.gz"), "rt", encoding="utf-8") as f:
        for hexcp in re.findall(r'id="kvg:kanji_0*([0-9a-fA-F]+)"', f.read()):
            try:
                kvg.add(chr(int(hexcp, 16)))
            except ValueError:
                pass

    cur = con.cursor()
    kanji_rows, reading_rows, comp_rows = [], [], []
    char_to_kid: dict[str, int] = {}
    next_id = 1
    for c in kd["characters"]:
        ch = c["literal"]
        misc = c.get("misc", {})
        classical = next(
            (r["value"] for r in c.get("radicals", []) if r.get("type") == "classical"),
            None,
        )
        on, kun, nanori, meanings = [], [], [], []
        rm = c.get("readingMeaning") or {}
        for g in rm.get("groups", []):
            for r in g.get("readings", []):
                if r["type"] == "ja_on":
                    on.append(r["value"])
                elif r["type"] == "ja_kun":
                    kun.append(r["value"])
            for m in g.get("meanings", []):
                if m.get("lang") == "en":
                    meanings.append(m["value"])
        nanori = rm.get("nanori", []) or []
        kid = next_id
        next_id += 1
        char_to_kid[ch] = kid
        kanji_rows.append((
            kid, f"kanji:{ch}", ch,
            (misc.get("strokeCounts") or [None])[0], misc.get("grade"),
            misc.get("frequency"), f"U+{ord(ch):04X}",
            (f"{ord(ch):05x}" if ch in kvg else None), classical,
            None, json.dumps(meanings, ensure_ascii=False), None,
            None, None, None, None,
            f"kanjidic2:{ch}", "dataset", "A", 0,
        ))
        for typ, lst in (("on", on), ("kun", kun), ("nanori", nanori)):
            for rd in lst:
                okuri = rd.split(".", 1)[1] if (typ == "kun" and "." in rd) else None
                base = rd.split(".", 1)[0] if (typ == "kun" and "." in rd) else rd
                reading_rows.append((kid, base, typ, okuri, None, None, None, None,
                                     f"kanjidic2:{ch}", "dataset", "A", 0))
    # components (kradfile) — only for kanji we have
    for ch, comps in krad.items():
        kid = char_to_kid.get(ch)
        if kid is None:
            continue
        for comp in comps:
            comp_rows.append((kid, comp, char_to_kid.get(comp)))

    cur.executemany(
        "INSERT INTO kanji (id,slug,character,strokes,grade,freq_rank,unicode_cp,kanjivg_ref,"
        "kangxi_radical,meanings_pt,meanings_en,notes_pt,level,level_confidence,level_agreement,"
        "level_sources,source,created_by,layer,needs_review) "
        "VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)", kanji_rows)
    cur.executemany(
        "INSERT INTO kanji_reading (kanji_id,reading,reading_type,okurigana,introduced_at_level,"
        "level_confidence,level_sources,example_vocab_ids,source,created_by,layer,needs_review) "
        "VALUES (?,?,?,?,?,?,?,?,?,?,?,?)", reading_rows)
    cur.executemany(
        "INSERT OR IGNORE INTO kanji_component (kanji_id,component,component_kanji_id) VALUES (?,?,?)",
        comp_rows)
    con.commit()
    log(f"  kanji={len(kanji_rows)} readings={len(reading_rows)} components={len(comp_rows)} "
        f"(kanjivg refs: {sum(1 for r in kanji_rows if r[7])})")


# ───────────────────────── JMdict (raw staging) ─────────────────────────
def ingest_jmdict(con: sqlite3.Connection) -> None:
    if count(con, "raw_jmdict_entry") > 0:
        log(f"  [skip] raw_jmdict_entry already populated ({count(con,'raw_jmdict_entry')})")
        return
    log("  parsing JMdict (common) …")
    data = load_tgz_json(newest("jmdict/jmdict-eng-common-*.tgz"))
    entries, forms = [], []
    for w in data["words"]:
        seq = int(w["id"])
        ks = w.get("kanji") or []
        ns = w.get("kana") or []
        common = 1 if any(e.get("common") for e in ks + ns) else 0
        entries.append((seq, common, json.dumps(w, ensure_ascii=False)))
        for e in ks:
            if e.get("text"):
                forms.append((seq, e["text"], 0, 1 if e.get("common") else 0))
        for e in ns:
            if e.get("text"):
                forms.append((seq, e["text"], 1, 1 if e.get("common") else 0))
    con.executemany("INSERT OR REPLACE INTO raw_jmdict_entry (ent_seq,common,data) VALUES (?,?,?)", entries)
    con.executemany("INSERT INTO raw_jmdict_form (ent_seq,form,is_kana,is_common) VALUES (?,?,?,?)", forms)
    con.commit()
    log(f"  jmdict entries={len(entries)} forms={len(forms)} common_entries="
        f"{sum(1 for e in entries if e[1])}")


# ───────────────────────── Tatoeba (raw staging + FTS) ─────────────────────────
def _load_lang_map(fname: str) -> dict[int, str]:
    out: dict[int, str] = {}
    with bz2.open(DS / "tatoeba" / fname, "rt", encoding="utf-8") as f:
        for line in f:
            p = line.rstrip("\n").split("\t")
            if len(p) >= 3:
                out[int(p[0])] = p[2]
    return out


def ingest_tatoeba(con: sqlite3.Connection) -> None:
    if count(con, "raw_tatoeba_sentence") > 0:
        log(f"  [skip] raw_tatoeba_sentence already populated ({count(con,'raw_tatoeba_sentence')})")
        return
    log("  loading JP sentences + audio …")
    jp = _load_lang_map("jpn_sentences.tsv.bz2")
    audio: set[int] = set()
    with tarfile.open(DS / "tatoeba" / "sentences_with_audio.tar.bz2", "r:bz2") as t:
        f = t.extractfile(t.getmembers()[0])
        for line in f:  # type: ignore[union-attr]
            sid = line.split(b"\t", 1)[0]
            if sid:
                try:
                    audio.add(int(sid))
                except ValueError:
                    pass
    con.executemany(
        "INSERT OR REPLACE INTO raw_tatoeba_sentence (id,text,has_audio) VALUES (?,?,?)",
        [(i, txt, 1 if i in audio else 0) for i, txt in jp.items()])
    con.commit()
    log(f"  jp_sentences={len(jp)} with_audio={sum(1 for i in jp if i in audio)}")

    log("  loading EN/PT maps + streaming links (≈28M) …")
    eng = _load_lang_map("eng_sentences.tsv.bz2")
    por = _load_lang_map("por_sentences.tsv.bz2")
    jp_ids = set(jp.keys())
    batch, total = [], 0
    cur = con.cursor()
    with tarfile.open(DS / "tatoeba" / "links.tar.bz2", "r:bz2") as t:
        f = t.extractfile(t.getmembers()[0])
        for line in f:  # type: ignore[union-attr]
            tab = line.find(b"\t")
            if tab < 0:
                continue
            a = int(line[:tab])
            if a in jp_ids:
                b = int(line[tab + 1:])
                if b in eng:
                    batch.append((a, "eng", b, eng[b]))
                elif b in por:
                    batch.append((a, "por", b, por[b]))
                else:
                    continue
                if len(batch) >= 50000:
                    cur.executemany("INSERT OR IGNORE INTO raw_tatoeba_translation "
                                    "(jp_id,lang,trans_id,text) VALUES (?,?,?,?)", batch)
                    total += len(batch)
                    batch.clear()
    if batch:
        cur.executemany("INSERT OR IGNORE INTO raw_tatoeba_translation "
                        "(jp_id,lang,trans_id,text) VALUES (?,?,?,?)", batch)
        total += len(batch)
    con.commit()
    en_n = con.execute("SELECT COUNT(*) FROM raw_tatoeba_translation WHERE lang='eng'").fetchone()[0]
    pt_n = con.execute("SELECT COUNT(*) FROM raw_tatoeba_translation WHERE lang='por'").fetchone()[0]
    log(f"  translations stored: {total} (eng={en_n}, por={pt_n})")

    log("  building trigram FTS …")
    con.execute("INSERT INTO raw_tatoeba_fts(raw_tatoeba_fts) VALUES('rebuild')")
    con.commit()
    log("  FTS built.")


# ───────────────────────── provenance ─────────────────────────
def populate_sources(con: sqlite3.Connection) -> None:
    today = _dt.date.today().isoformat()
    rows = [
        ("JMdict (common)", "3.6.2+20260608", "https://github.com/scriptin/jmdict-simplified",
         "EDRDG CC BY-SA 4.0", "ShareAlike — owner legal review", None, today),
        ("KANJIDIC2", "3.6.2+20260608", "https://github.com/scriptin/jmdict-simplified",
         "EDRDG CC BY-SA 4.0", "ShareAlike; do not use its jlpt field as modern level", None, today),
        ("Kradfile/Radkfile", "3.6.2+20260608", "https://github.com/scriptin/jmdict-simplified",
         "EDRDG CC BY-SA", "ShareAlike", None, today),
        ("KanjiVG", "r20250816", "https://github.com/KanjiVG/kanjivg",
         "CC BY-SA 3.0", "ShareAlike on derivative SVGs", None, today),
        ("Tatoeba", "export 2026-06", "https://tatoeba.org/en/downloads",
         "CC BY 2.0 FR", "commercial OK with attribution; audio varies", None, today),
        ("kanji-data (jlpt_new)", "fetch 2026-06-13",
         "https://github.com/davidluzgouveia/kanji-data", "verify", "community level list (1 of >=3)", None, today),
        ("jlpt-word-list (elzup)", "fetch 2026-06-13",
         "https://github.com/elzup/jlpt-word-list", "verify", "community level list (1 of >=3)", None, today),
    ]
    con.executemany(
        "INSERT OR REPLACE INTO dataset_source (name,version,url,license,commercial_note,sha256,fetched_at) "
        "VALUES (?,?,?,?,?,?,?)", rows)
    con.commit()
    log(f"  dataset_source rows: {count(con,'dataset_source')}")


def main() -> int:
    con = sqlite3.connect(DB)
    con.execute("PRAGMA foreign_keys = ON;")
    con.execute("PRAGMA journal_mode = WAL;")
    log("== kanji inventory =="); ingest_kanji(con)
    log("== jmdict (raw) =="); ingest_jmdict(con)
    log("== tatoeba (raw + fts) =="); ingest_tatoeba(con)
    log("== provenance =="); populate_sources(con)
    con.close()
    log("P1 ingestion done.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
