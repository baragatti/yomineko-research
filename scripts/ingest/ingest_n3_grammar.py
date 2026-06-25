#!/usr/bin/env python3
"""Ingest N3 grammar SHELLS from the hanabira N3 list (MIT, tristcoil/hanabira.org) and export the
English seeds for AI pt-BR Layer-C generation. Additive: only inserts grammar_point rows whose key is
not already present. Each N3 grammar point is Layer C, needs_review=1 (single open lineage).

Outputs: grammar_point rows (level='n3') + research/_n3_grammar_seed.json for the Layer-C workflow.
Run with venv python.
"""
from __future__ import annotations
import json, re, sqlite3, sys
from pathlib import Path
sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
ROOT = Path(__file__).resolve().parents[2]
DB = ROOT / "db" / "corpus.sqlite"
SRC = ROOT / "research" / "datasets" / "n3_grammar_hanabira.json"
SEED = ROOT / "research" / "_n3_grammar_seed.json"

JP = re.compile(r"[぀-ヿ一-鿿々～～]")


def parse_title(title: str) -> tuple[str, str]:
    """'A その上 B (A sono ue B)' -> (jp_pattern 'その上', romaji 'sono ue')."""
    m = re.search(r"\(([^()]*)\)\s*$", title)
    romaji = (m.group(1) if m else "").strip()
    pre = title[: m.start()].strip() if m else title.strip()
    # keep only JP runs from the pre-paren part (drops the A/B latin placeholders)
    jp = "".join(ch for ch in pre if JP.match(ch) or ch in "　 ").strip()
    jp = re.sub(r"\s+", "", jp)
    # romaji: drop standalone A/B placeholders
    romaji = re.sub(r"\b[AB]\b", "", romaji).strip()
    romaji = re.sub(r"\s+", " ", romaji)
    return jp, romaji


def slugify(romaji: str, jp: str, i: int) -> str:
    base = re.sub(r"[^a-z0-9]+", "-", romaji.lower()).strip("-")
    if not base:
        base = f"pt{i:03d}"
    return f"n3-{base}"


def main() -> int:
    data = json.loads(SRC.read_text(encoding="utf-8"))
    arr = data if isinstance(data, list) else (data.get("data") or list(data.values()))
    con = sqlite3.connect(DB); cur = con.cursor()
    existing = {r[0] for r in con.execute("SELECT key FROM grammar_point")}
    seed = []
    added = 0
    used_keys: set[str] = set()
    for i, g in enumerate(arr):
        title = g.get("title", "")
        jp, romaji = parse_title(title)
        if not jp:
            continue
        key = slugify(romaji, jp, i)
        k, n = key, 2
        while k in existing or k in used_keys:
            k = f"{key}-{n}"; n += 1
        key = k
        used_keys.add(key)
        cur.execute(
            "INSERT INTO grammar_point (slug,key,structure_pattern,register,forms_json,level,"
            "level_confidence,level_agreement,level_sources,source,created_by,layer,needs_review) "
            "VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (f"gram:{key}", key, jp, "neutral", json.dumps([jp], ensure_ascii=False), "n3",
             0.34, "1/1", json.dumps({"hanabira": "n3"}, ensure_ascii=False),
             "hanabira-mit", "ai", "C", 1))
        gid = cur.lastrowid
        added += 1
        seed.append({"gid": gid, "key": key, "jp": jp, "romaji": romaji, "title": title,
                     "short_en": g.get("short_explanation", ""), "long_en": g.get("long_explanation", ""),
                     "formation_en": g.get("formation", ""),
                     "examples": (g.get("examples") or [])[:3]})
    con.commit()
    SEED.write_text(json.dumps(seed, ensure_ascii=False), encoding="utf-8")
    by = dict(con.execute("SELECT level,COUNT(*) FROM grammar_point GROUP BY level"))
    print(f"N3 grammar shells inserted: {added}; grammar by level now: {by}")
    print(f"seed -> {SEED.relative_to(ROOT)} ({len(seed)} points)")
    con.close(); return 0


if __name__ == "__main__":
    sys.exit(main())
