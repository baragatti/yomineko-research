#!/usr/bin/env python3
"""Ingest JEC Basic Sentence Data (Kyoto U. Kurohashi-Kawahara Lab + NICT MASTAR) — a CLEAN, permissive
second REAL source. License: CC-BY 3.0 Unported (commercial + redistribution OK, attribution, NO share-alike).

5,304 basic sentences with manual ja/en/zh; we load the ja+en pairs, dropping the ~538 that contain latin
(X/Y) or 〜 placeholder variables (templates, not natural sentences). Stored in raw_jec + raw_jec_fts so the
miners can select JEC sentences exactly like Tatoeba. Records the source in dataset_source. Idempotent.
Run with venv python after downloading research/datasets/jec/JEC_basic_sentence_v1-2.xls.
"""
from __future__ import annotations

import hashlib
import re
import sqlite3
import sys
from pathlib import Path

import xlrd

sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
ROOT = Path(__file__).resolve().parents[2]
DB = ROOT / "db" / "corpus.sqlite"
XLS = ROOT / "research" / "datasets" / "jec" / "JEC_basic_sentence_v1-2.xls"
PLACEHOLDER = re.compile(r"[A-Za-z〜～]")  # template variables -> not natural sentences
URL = "https://nlp.ist.i.kyoto-u.ac.jp/EN/index.php?JEC%20Basic%20Sentence%20Data"


def main() -> int:
    con = sqlite3.connect(DB)
    con.execute("CREATE TABLE IF NOT EXISTS raw_jec (id TEXT PRIMARY KEY, ja TEXT, en TEXT)")
    con.execute("CREATE VIRTUAL TABLE IF NOT EXISTS raw_jec_fts USING fts5(ja, content='raw_jec', "
                "content_rowid='rowid', tokenize='trigram')")
    wb = xlrd.open_workbook(str(XLS))
    sh = wb.sheet_by_index(0)
    kept = skipped = 0
    con.execute("DELETE FROM raw_jec")
    con.execute("DELETE FROM raw_jec_fts")
    for r in range(sh.nrows):
        jid = str(sh.cell_value(r, 0)).strip()
        ja = str(sh.cell_value(r, 1)).strip()
        en = str(sh.cell_value(r, 2)).strip()
        if not ja or PLACEHOLDER.search(ja):
            skipped += 1
            continue
        con.execute("INSERT OR IGNORE INTO raw_jec (id, ja, en) VALUES (?,?,?)", (f"jec:{jid}", ja, en))
        kept += 1
    con.execute("INSERT INTO raw_jec_fts (rowid, ja) SELECT rowid, ja FROM raw_jec")
    # provenance
    sha = hashlib.sha256(XLS.read_bytes()).hexdigest()
    con.execute("DELETE FROM dataset_source WHERE name='JEC Basic Sentence Data'")
    con.execute("INSERT INTO dataset_source (name,version,url,license,commercial_note,sha256,fetched_at) "
                "VALUES (?,?,?,?,?,?,?)",
                ("JEC Basic Sentence Data", "v1-2", URL, "CC-BY 3.0 Unported",
                 "Commercial + redistribute OK with attribution; NO share-alike. Attribute BOTH "
                 "Kurohashi-Kawahara Lab (Japanese) and NICT MASTAR (English/Chinese).", sha, "2026-06-15"))
    con.commit()
    n = con.execute("SELECT count(*) FROM raw_jec").fetchone()[0]
    print(f"ingest_jec: loaded {kept} sentences (skipped {skipped} placeholder/empty); raw_jec={n}; sha {sha[:16]}")
    con.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
