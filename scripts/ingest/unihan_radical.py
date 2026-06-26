#!/usr/bin/env python3
"""Adopt the PERMISSIVE Unihan `kRSUnicode` Kangxi radical (Unicode License) as the authoritative radical for
each kanji (license_audit.md D-LIC-2 — removes reliance on CC BY-SA KRADFILE for the radical). Also derives the
radical's CJK character for display via Unicode NFKD of the Kangxi-Radical block glyph (U+2F00+N-1 → e.g. ⼝→口),
so no hand-kept 214-radical table is needed. Multi-component decomposition (`kanji_component`) is left as-is —
it is uncopyrightable FACT, credited to EDRDG. Idempotent. Usage: unihan_radical.py"""
from __future__ import annotations
import re, sqlite3, sys, unicodedata, zipfile
from pathlib import Path
sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
ROOT = Path(__file__).resolve().parents[2]
DB = ROOT / "db" / "corpus.sqlite"
UNIHAN = ROOT / "research" / "datasets" / "unihan" / "Unihan.zip"
RS_RE = re.compile(r"(\d+)'?\.-?\d+")


def radical_char(n: int) -> str | None:
    """Kangxi radical number -> CJK character (via NFKD of the Kangxi-Radical block glyph)."""
    if not (1 <= n <= 214):
        return None
    k = chr(0x2F00 + n - 1)            # Kangxi Radical block (⼀ … ⿕)
    nf = unicodedata.normalize("NFKD", k)
    return nf[0] if nf else k


def main() -> int:
    krs: dict = {}
    with zipfile.ZipFile(UNIHAN) as z:
        for ln in z.read("Unihan_IRGSources.txt").decode("utf-8").splitlines():
            if "\tkRSUnicode\t" not in ln:
                continue
            cp_s, _, val = ln.split("\t", 2)
            m = RS_RE.match(val.split()[0])
            if m:
                krs[chr(int(cp_s[2:], 16))] = int(m.group(1))
    con = sqlite3.connect(DB)
    cols = [r[1] for r in con.execute("PRAGMA table_info(kanji)")]
    if "radical_char" not in cols:
        con.execute("ALTER TABLE kanji ADD COLUMN radical_char TEXT")
    if "radical_source" not in cols:
        con.execute("ALTER TABLE kanji ADD COLUMN radical_source TEXT")
    upd = changed = nochar = 0
    for kid, ch, cur in con.execute(
            "SELECT id, character, kangxi_radical FROM kanji WHERE level IN ('n5','n4','n3','n2','n1')").fetchall():
        rad = krs.get(ch, cur)
        rc = radical_char(rad) if rad else None
        if rad != cur:
            changed += 1
        con.execute("UPDATE kanji SET kangxi_radical=?, radical_char=?, radical_source=? WHERE id=?",
                    (rad, rc, "unihan:kRSUnicode" if ch in krs else "kanjidic2", kid))
        upd += 1
        if rad and not rc:
            nochar += 1
    con.commit()
    con.close()
    print(f"unihan radical: updated {upd} kanji ({changed} radicals changed to Unihan's value); "
          f"{nochar} without a derivable radical char")
    return 0


if __name__ == "__main__":
    sys.exit(main())
