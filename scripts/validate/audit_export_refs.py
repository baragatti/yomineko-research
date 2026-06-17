#!/usr/bin/env python3
"""P7/P8 — audit the EXPORTED courseware against the EXPORTED corpus (not the DB).

The DB-level validators can pass while the exported files are inconsistent (e.g. a kanji is taught + referenced
in a lesson body but, having no level, is dropped from corpus/kanji/*.json — a dangling ref an app would choke
on). This loads the exported corpus ref-sets (kanji chars, vocab headwords, grammar keys, sentence slugs, kana
families) and, for every exported lesson leaf, checks:
  - leaf schema conformance: `id` (les:…) present, NO legacy `slug`; title/description are locale-objects
    ({"pt-BR":…}); objectives a list of locale-objects.
  - every unlock ref resolves to an exported corpus record (kanji/vocab/grammar/kana-family).
  - every inline body ref (<kanji|vocab|grammar ref=…/>, <sentence ref=…/>) resolves.
Read-only; exits non-zero on any FAIL. Usage: audit_export_refs.py
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
ROOT = Path(__file__).resolve().parents[2]
COURSE = ROOT / "course"
CORPUS = ROOT / "corpus"
LOC = "pt-BR"
REF_RX = re.compile(r'<(kanji|vocab|grammar|sentence)\s+ref="([^"]+)"')


def _load(sub: str, key: str) -> set:
    out: set = set()
    for f in (CORPUS / sub).glob("*.json"):
        try:
            d = json.loads(f.read_text(encoding="utf-8"))
        except Exception:
            continue
        items = d if isinstance(d, list) else (d.get(sub) if isinstance(d, dict) else [])
        for it in (items or []):
            if isinstance(it, dict) and key in it:
                out.add(it[key])
    return out


def main() -> int:
    # pools keyed by the FULL ref form, so comparisons are uniform (no per-kind prefix stripping)
    kanji = {f"kanji:{c}" for c in _load("kanji", "character")}
    vocab = {f"vocab:{h}" for h in _load("vocab", "headword")}
    grammar = {f"gram:{k}" for k in _load("grammar", "key")}
    sents = _load("sentences", "slug")  # already "sent:…"
    kana: set = set()
    fjson = CORPUS / "kana" / "families.json"
    if fjson.exists():
        fd = json.loads(fjson.read_text(encoding="utf-8"))
        # shape: {"hiragana": [{id:"kana:hiragana-a",…}], "katakana": [...]}  (or a flat list)
        groups = fd.values() if isinstance(fd, dict) else [fd]
        for grp in groups:
            for fam in (grp if isinstance(grp, list) else []):
                if isinstance(fam, dict):
                    kana.add(fam.get("id") or fam.get("slug"))  # "kana:…"
    body_pool = {"kanji": kanji, "vocab": vocab, "grammar": grammar, "sentence": sents}
    unlock_set = {"kanji": kanji, "vocab": vocab, "grammar": grammar, "kana-family": kana}

    fails: list[str] = []
    n = 0
    for leaf in COURSE.glob("*/topic-*/lesson-*.json"):
        n += 1
        d = json.loads(leaf.read_text(encoding="utf-8"))
        lid = d.get("id", leaf.stem)
        # schema conformance
        if not str(d.get("id", "")).startswith("les:"):
            fails.append(f"{leaf.name}: missing/!les id (id={d.get('id')!r}, slug={d.get('slug')!r})")
        if "slug" in d:
            fails.append(f"{lid}: legacy 'slug' field present (should be 'id')")
        for fld in ("title", "description"):
            if not (isinstance(d.get(fld), dict) and LOC in d[fld]):
                fails.append(f"{lid}: {fld} not a locale-object")
        if not all(isinstance(o, dict) and LOC in o for o in d.get("objectives", [])):
            fails.append(f"{lid}: objectives not locale-objects")
        # unlock refs resolve to exported corpus (full-ref compare)
        for u in d.get("unlocks", []):
            typ, ref = u.get("type"), u.get("ref", "")
            if typ in unlock_set and ref not in unlock_set[typ]:
                fails.append(f"{lid}: unlock {typ} '{ref}' not in exported corpus")
        # body inline refs resolve (full-ref compare)
        for kind, ref in REF_RX.findall(d.get("body", "") or ""):
            if ref not in body_pool[kind]:
                fails.append(f"{lid}: body <{kind} ref='{ref}'/> not in exported corpus")
    print(f"export-ref audit: {n} lesson leaves; corpus kanji={len(kanji)} vocab={len(vocab)} "
          f"grammar={len(grammar)} sentences={len(sents)} kana={len(kana)}")
    if fails:
        print(f"=== {len(fails)} FAIL ===")
        for f in fails[:50]:
            print(f"  FAIL {f}")
        return 1
    print("=== 0 FAIL — every leaf is schema-conformant and all refs resolve in the export ===")
    return 0


if __name__ == "__main__":
    sys.exit(main())
