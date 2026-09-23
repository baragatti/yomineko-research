#!/usr/bin/env python3
"""W13 finish: the mechanical re-chunk of templated particle explanations, in BOTH layers.

The W13b template audit (`research/reports/w13b_template_audit.md` §2) found that the v1 template
quoted the whole left run in front of a particle as its noun phrase, so an adverb, an adverbial
noun, a 連用形 copula, a conjunction or an adverbially-used i-adjective ended up inside the quote:
「を marca 直に腹 como o objeto direto…」 where the object is 腹. `derive_layerb_templates_v2.py`
carries the fixed `chunk_head()` rule; the audit emitted one row per affected particle into
`research/derived/pending/particle_template_fixes.json`.

Two tracked tables, one per manifest step:

  * `research/derived/repairs/particle_template_fixes.json` (the default) — that pending file's 201
    `explanation_change: "replace"` rows, copied verbatim. Explanation only.
  * `research/derived/repairs/particle_template_fixes_second.json` (`--data`, U1) — the 74 rows of
    `research/derived/pending/particle_template_fixes_second.json`: the 50 withdrawn て-locution
    connector templates, re-authored and verified (new explanation AND new label), and the 24 label
    overrides of verified rows (new label only), signed off 2026-09-23.

A row names which fields it changes (`explanation_change`, `function_pt_change`: `replace` or
`none`) and is addressed by (sentence slug / Layer-B key, token position); every field it changes is
matched EXACTLY on its `old_*` value. Nothing else about the particle changes (`function_type` and the
particle itself are left alone). Layer-B also takes the row's `explanation_status_after` /
`function_status_after` where the row carries one.

TWO LAYERS, so a rebuild reproduces the repair:
  * db/corpus.sqlite   localized_text (particle, explanation|function, pt-BR) of the particle whose
                       token is the row's C-token position;
  * Layer-B source     research/derived/mined_layerb_n3/batch-NN.json, which
                       `ingest_mined_stages.py` reads, so a manifest replay ingests the fixed text
                       and this script's own replay step finds every row already applied.

Idempotent: a value already equal to `new_*` counts as applied; a value that is neither `old` nor
`new` is reported and never overwritten (exit 2). A batch file is rewritten only when a row in it
changed, in the file's own serialisation (indent 1, its own line endings), so an unchanged file
stays byte-identical.

Usage: apply_particle_template_fixes.py [--check] [--data PATH] [--layerb DIR]
"""
from __future__ import annotations

import argparse
import json
import sqlite3
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]

# W01: honour --db / $YOMINEKO_DB so a rebuild can target a scratch DB (scripts/dbtarget.py).
import sys as _sys, pathlib as _pl  # noqa: E402
_sys.path.append(str(next(p for p in _pl.Path(__file__).resolve().parents if p.name == "scripts")))
from dbtarget import db_target  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
DB = db_target(ROOT / "db" / "corpus.sqlite")
DATA = ROOT / "research" / "derived" / "repairs" / "particle_template_fixes.json"
LAYERB = ROOT / "research" / "derived" / "mined_layerb_n3"

# (localized_text field, Layer-B text key, row change flag, row old/new stem, Layer-B status key)
FIELDS = (
    ("explanation", "explanation_pt", "explanation_change", "explanation", "explanation_status"),
    ("function", "function_pt", "function_pt_change", "function_pt", "function_status"),
)


def changed_fields(r: dict) -> list[tuple[str, str, str, str, str]]:
    return [f for f in FIELDS if r.get(f[2]) == "replace"]


def load(path: Path) -> list[dict]:
    doc = json.loads(path.read_text(encoding="utf-8"))
    rows = doc["rows"]
    if doc.get("row_count") != len(rows):
        raise SystemExit(f"{path.name}: row_count {doc.get('row_count')} != {len(rows)} rows")
    seen: set[tuple[str, int]] = set()
    for i, r in enumerate(rows):
        flags = {r.get(f[2]) for f in FIELDS}
        if not flags <= {"replace", "none"} or not changed_fields(r):
            raise SystemExit(f"row {i} ({r.get('slug')}): a row must `replace` at least one field "
                             f"and every change flag must be `replace` or `none` (withdraw rows "
                             f"belong in pending/, not in a tracked table)")
        for _, _, _, stem, _ in changed_fields(r):
            if r[f"old_{stem}"] == r[f"new_{stem}"]:
                raise SystemExit(f"row {i} ({r['slug']}): `new_{stem}` is identical to `old`")
        k = (r["slug"], r["position"])
        if k in seen:
            raise SystemExit(f"row {i}: duplicate target {k}")
        seen.add(k)
    return rows


def plan(values: dict[str, str | None], r: dict) -> tuple[str, list[str]]:
    """values: {field: current text} -> ("already"|"change"|"mismatch", fields still at `old`)."""
    todo: list[str] = []
    for field, _, _, stem, _ in changed_fields(r):
        v = values.get(field)
        if v == r[f"new_{stem}"]:
            continue
        if v != r[f"old_{stem}"]:
            return "mismatch", [field]
        todo.append(field)
    return ("change" if todo else "already"), todo


def apply_db(con: sqlite3.Connection, rows: list[dict], write: bool) -> tuple[int, int, list[str]]:
    changed = already = 0
    problems: list[str] = []
    for r in rows:
        label = f"{r['slug']} @{r['position']} {r['surface']}"
        hit = con.execute(
            "SELECT p.id, p.particle FROM particle p "
            "JOIN sentence s ON s.id = p.sentence_id JOIN token t ON t.id = p.token_id "
            "WHERE s.slug=? AND t.position=? AND t.split_mode='C'",
            (r["slug"], r["position"])).fetchall()
        if len(hit) != 1:
            problems.append(f"db {label}: {len(hit)} particle rows at this position")
            continue
        pid, particle = hit[0]
        if particle != r["surface"]:
            problems.append(f"db {label}: the particle there is {particle!r}")
            continue
        values = dict(con.execute(
            "SELECT field, value FROM localized_text WHERE entity_type='particle' AND entity_id=? "
            "AND locale='pt-BR'", (pid,)).fetchall())
        state, todo = plan(values, r)
        if state == "already":
            already += 1
        elif state == "mismatch":
            problems.append(f"db {label}: stored {todo[0]} is neither `old` nor `new` - not touching it")
        else:
            if write:
                for field, _, _, stem, _ in changed_fields(r):
                    if field in todo:
                        con.execute("UPDATE localized_text SET value=? WHERE entity_type='particle' "
                                    "AND entity_id=? AND field=? AND locale='pt-BR'",
                                    (r[f"new_{stem}"], pid, field))
            changed += 1
    return changed, already, problems


def apply_layerb(layerb: Path, rows: list[dict], write: bool) -> tuple[int, int, list[str]]:
    by_batch: dict[int, list[dict]] = {}
    for r in rows:
        by_batch.setdefault(r["batch"], []).append(r)
    changed = already = 0
    problems: list[str] = []
    for batch, brows in sorted(by_batch.items()):
        path = layerb / f"batch-{batch:02d}.json"
        raw = path.read_text(encoding="utf-8", newline="") if path.is_file() else None
        if raw is None:
            problems.append(f"layer-b {path.name}: missing")
            continue
        doc = json.loads(raw)
        sents = {str(s.get("key") or s["tatoeba_id"]): s for s in doc["sentences"]}
        dirty = False
        for r in brows:
            label = f"{path.name} {r['key']} @{r['position']} {r['surface']}"
            s = sents.get(r["key"])
            ps = [p for p in (s or {}).get("particles", []) if p["position"] == r["position"]]
            if s is None or len(ps) != 1 or s.get("slug") != r["slug"]:
                problems.append(f"layer-b {label}: no single particle at this address")
                continue
            p = ps[0]
            if p["particle"] != r["surface"]:
                problems.append(f"layer-b {label}: the particle there is {p['particle']!r}")
                continue
            state, todo = plan({f[0]: p.get(f[1]) for f in FIELDS}, r)
            if state == "mismatch":
                problems.append(f"layer-b {label}: {todo[0]} is neither `old` nor `new` - "
                                f"not touching it")
                continue
            touched = False
            for field, key, _, stem, status_key in changed_fields(r):
                if field in todo:
                    p[key] = r[f"new_{stem}"]
                    touched = True
                after = r.get(f"{status_key}_after")
                if after and p.get(status_key) != after:
                    p[status_key] = after
                    touched = True
            if touched:
                dirty = True
                changed += 1
            else:
                already += 1
        if dirty and write:
            eol = "\r\n" if "\r\n" in raw else "\n"
            path.write_text(json.dumps(doc, ensure_ascii=False, indent=1).replace("\n", eol),
                            encoding="utf-8", newline="")
    return changed, already, problems


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true", help="report what would change; write nothing")
    ap.add_argument("--data", type=Path, default=DATA, help="tracked repair table")
    ap.add_argument("--layerb", type=Path, default=LAYERB, help="Layer-B batch dir")
    args = ap.parse_args()
    rows = load(args.data)
    con = sqlite3.connect(DB)
    con.execute("PRAGMA busy_timeout=60000")
    d_changed, d_already, d_prob = apply_db(con, rows, write=not args.check)
    l_changed, l_already, l_prob = apply_layerb(args.layerb, rows, write=not args.check)
    if not args.check:
        con.commit()
    con.close()
    verb = "would repair" if args.check else "repaired"
    print(f"{args.data.name}: {len(rows)} rows | db: {verb} {d_changed}, {d_already} already | "
          f"layer-b: {verb} {l_changed}, {l_already} already")
    for p in d_prob + l_prob:
        print(f"  ! {p}")
    if d_prob or l_prob:
        return 2
    return 1 if (args.check and (d_changed or l_changed)) else 0


if __name__ == "__main__":
    sys.exit(main())
