#!/usr/bin/env python3
"""Deterministic corpus-wide accent sweep over localized_text REGISTRY fields (translation_qa.md §0.1 feedback
loop). Restores stripped pt-BR diacritics (você/ação/partícula/relação/tópico/...) using the curated safe map
(fix_accents_lessons.MAP) merged with the vetted -ção/-ões/-ário/-ável family map. Word-bounded, case-preserving.

SCOPE: sentence/token/particle/grammar_point/kanji/vocab_sense/family/topic/course_module/exercise* text only.
EXCLUDES lesson/exercise BODY-like markup fields (entity_type 'lesson' and field 'body') — those are XML-ish and
are sourced from research/derived/lessons/*.json (fixed there by fix_accents_lessons, which is markup-aware);
sweeping raw markup here can corrupt tags. Idempotent. Usage: accent_sweep_localized.py [--apply]"""
from __future__ import annotations
import json, re, sqlite3, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "ingest"))
sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
from fix_accents_lessons import MAP as CUR  # noqa: E402
ROOT = Path(__file__).resolve().parents[2]
DB = ROOT / "db" / "corpus.sqlite"
EXCLUDE = {"lesson"}                         # JSON-sourced + markup; handled by fix_accents_lessons on the JSON


def build_map():
    m = {}
    vp = ROOT / "research" / "derived" / "_accent_vetted.json"
    if vp.exists():
        m.update(json.loads(vp.read_text(encoding="utf-8")))
    m.update(CUR)                            # curated (hand-vetted) wins on conflict
    return {k: v for k, v in m.items() if k != v}


def main() -> int:
    apply = "--apply" in sys.argv
    m = build_map()
    keys = sorted(m, key=len, reverse=True)
    rx = re.compile(r"(?<![0-9A-Za-zÀ-ÿ])(" + "|".join(re.escape(k) for k in keys) + r")(?![0-9A-Za-zÀ-ÿ])", re.I)

    def case(s, r):
        return r.upper() if s.isupper() else (r[:1].upper() + r[1:] if s[:1].isupper() else r)

    def fix(s):
        n = [0]

        def sub(mt):
            r = m.get(mt.group(1).lower())
            if r:
                n[0] += 1
                return case(mt.group(1), r)
            return mt.group(1)
        return rx.sub(sub, s), n[0]

    con = sqlite3.connect(DB)
    words = touched = 0
    for et, eid, field, val, is_list in con.execute(
            "SELECT entity_type, entity_id, field, value, is_list FROM localized_text "
            "WHERE locale='pt-BR' AND value IS NOT NULL AND value!=''"):
        if et in EXCLUDE or field == "body":
            continue
        if is_list:
            try:
                obj = json.loads(val)
            except json.JSONDecodeError:
                continue
            ch = 0
            if isinstance(obj, list):
                out = []
                for x in obj:
                    if isinstance(x, str):
                        nx, k = fix(x); ch += k; out.append(nx)
                    else:
                        out.append(x)
                new = json.dumps(out, ensure_ascii=False)
            elif isinstance(obj, dict):
                out = {}
                for kk, vv in obj.items():
                    if isinstance(vv, str):
                        nv, k = fix(vv); ch += k; out[kk] = nv
                    else:
                        out[kk] = vv
                new = json.dumps(out, ensure_ascii=False)
            else:
                continue
            if ch and apply:
                con.execute("UPDATE localized_text SET value=? WHERE entity_type=? AND entity_id=? AND field=? "
                            "AND locale='pt-BR'", (new, et, eid, field))
            words += ch; touched += 1 if ch else 0
        else:
            new, k = fix(val)
            if k and apply:
                con.execute("UPDATE localized_text SET value=? WHERE entity_type=? AND entity_id=? AND field=? "
                            "AND locale='pt-BR'", (new, et, eid, field))
            words += k; touched += 1 if k else 0
    if apply:
        con.commit()
    print(f"accent sweep ({'applied' if apply else 'dry-run'}): {words} words across {touched} registry fields "
          f"(map {len(m)}; excluded lesson/body)")
    con.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
