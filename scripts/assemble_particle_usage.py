#!/usr/bin/env python3
"""W46: assemble the particle-usage and token-role tables that apply_particle_usage.py writes.

INPUTS (read-only)
  research/derived/repairs/particle_usage/derived.json         5,418 rows derived mechanically (tier auto)
  research/derived/repairs/particle_usage/ruled-work-NN.json    19,353 rows ruled per batch, keyed slug#position
  research/derived/pending/particle_usage/ruled-N.verdict.json  the independent verifier's verdict per row,
                                                                joined BY ROW IDENTITY (slug#position), never
                                                                by file number
  research/derived/repairs/particle_usage/token_roles_derived.json   token function / aux_function / chunk_role
  design/particle_functions.json, design/token_roles.json       the enums
  db/corpus.sqlite (read-only)                                  C tokens, particle rows, legacy texts
All four row sources come from scripts/derive_particle_usage.py (commit 6d1875c2) and its campaign.

RULES
  * auto row                      -> usage as derived, usage_status `auto`
  * ruled + verdict ok            -> ruled usage, `verified`
  * ruled + verdict corrected     -> the verifier's id, `ruled`
  * verdict ok:false, no id       -> HELD (verifier-rejected)
  * a null / malformed verdict    -> HELD (never passed)
  * the final id does not spell the particle's surface (particle_usage_render.surface_matches) -> HELD
Every applied row carries its template slots (particle_usage_render.slots_for) and a guard on the
legacy explanation it moves to `note` (sha256[:16] per locale, null when the locale is absent).
lex.fixed expressions: the Japanese quoted by the ruling, the verifier or the legacy label/explanation,
the longest one grounded in the sentence (expression_grounded) whose kanji the sentence shows; else the
particle with its neighbours.

Token roles: function / aux_function as derived; chunk_role re-derived from the FINAL usage of the
particle that closes the chunk (design/token_roles.md §2: "the particle usage that closes the chunk"),
which the derivation could only do for auto rows. lex.fixed and held closers keep the derived value.

OUTPUTS
  research/derived/repairs/particle_usage.json   rows + held
  research/derived/repairs/token_roles.json      rows: {slug, tokens: [[position, surface, function, aux_function, chunk_role]]}
Deterministic; re-running on the same inputs rewrites byte-identical files.
Usage: assemble_particle_usage.py [--db PATH] [--check]
"""
from __future__ import annotations

import argparse
import collections
import glob
import hashlib
import json
import re
import sqlite3
import sys
from pathlib import Path
from typing import Any

sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from particle_usage_render import (expression_grounded, fallback_expression, forms, load_enum,  # noqa: E402
                                   slots_for, span_spelling, surface_matches)

SRC = ROOT / "research" / "derived" / "repairs" / "particle_usage"
VERDICTS = ROOT / "research" / "derived" / "pending" / "particle_usage"
OUT_USAGE = ROOT / "research" / "derived" / "repairs" / "particle_usage.json"
OUT_ROLES = ROOT / "research" / "derived" / "repairs" / "token_roles.json"
JP_RUN = re.compile(r"[ぁ-ヿ一-鿿々ー]+")
KANJI = re.compile(r"[一-鿿々]")


def sha(text: str | None) -> str | None:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:16] if text is not None else None


def file_sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def load_keyed(pattern: str) -> tuple[dict[str, Any], dict[str, str]]:
    rows: dict[str, Any] = {}
    origin: dict[str, str] = {}
    for f in sorted(glob.glob(pattern)):
        for k, v in json.loads(Path(f).read_text(encoding="utf-8")).items():
            if k in rows:
                raise SystemExit(f"{k} appears in {origin[k]} and {Path(f).name}")
            rows[k] = v
            origin[k] = Path(f).name
    return rows, origin


def pick_expression(toks: list[dict], i: int, texts: list[str | None]) -> tuple[str, str]:
    best: tuple[int, int, str] | None = None
    jp = "".join(t["surface"] for t in toks)
    kanji_in_jp = set(KANJI.findall(jp))
    for text in texts:
        for run in JP_RUN.findall(text or ""):
            if len(run) <= len(toks[i]["surface"]) or not expression_grounded(toks, i, run):
                continue
            if not set(KANJI.findall(run)) <= kanji_in_jp:
                continue    # やって来る for やってきた: a spelling the learner does not see
            grounded = max(n for n in range(len(run), 0, -1) if run[:n] in jp)
            key = (grounded, -len(run), run)
            if best is None or key[:2] > best[:2]:
                best = key
    if best:
        return best[2], "quoted"
    return fallback_expression(toks, i), "neighbours"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--db", type=Path, default=ROOT / "db" / "corpus.sqlite")
    ap.add_argument("--check", action="store_true", help="build and report; write nothing")
    args = ap.parse_args()
    enum = load_enum(ROOT)
    U = enum["usages"]
    tr = json.loads((ROOT / "design" / "token_roles.json").read_text(encoding="utf-8"))
    enums = {k: {x["id"] for x in tr[k]} for k in ("token_functions", "aux_functions", "chunk_roles")}

    derived_doc = json.loads((SRC / "derived.json").read_text(encoding="utf-8"))
    derived = {f"{r['slug']}#{r['position']}": r for r in derived_doc["rows"]}
    ruled, _ = load_keyed(str(SRC / "ruled-work-*.json"))
    verdicts, _ = load_keyed(str(VERDICTS / "ruled-*.verdict.json"))
    if set(derived) & set(ruled):
        raise SystemExit("a row is both derived and ruled")
    if set(ruled) != set(verdicts):
        raise SystemExit(f"ruled/verdict identities differ: {len(set(ruled) ^ set(verdicts))}")

    con = sqlite3.connect(f"file:{args.db.as_posix()}?mode=ro", uri=True)
    toks_of: dict[str, list[dict]] = collections.defaultdict(list)
    for slug, pos, surf, lem, pc, pf, inf in con.execute(
            "SELECT s.slug, t.position, t.surface, t.lemma, t.pos_coarse, t.pos_fine, t.inflection FROM token t "
            "JOIN sentence s ON s.id = t.sentence_id WHERE t.split_mode = 'C' ORDER BY s.slug, t.position"):
        if pos != len(toks_of[slug]):
            raise SystemExit(f"{slug}: C positions are not contiguous at {pos}")
        toks_of[slug].append({"surface": surf, "lemma": lem, "pos_coarse": pc, "pos_fine": pf, "inflection": inf})
    loc: dict[tuple[int, str, str], str] = {}
    for eid, field, lc, val in con.execute(
            "SELECT entity_id, field, locale, value FROM localized_text WHERE entity_type = 'particle'"):
        loc[(eid, field, lc)] = val
    # the authored explanation: `note` once apply_particle_usage.py has moved it, else `explanation`
    # (a particle is moved as a whole, so a note in either locale means the move happened)
    moved = {eid for (eid, field, _lc) in loc if field == "note"}

    def legacy(pid: int, lc: str) -> str | None:
        return loc.get((pid, "note" if pid in moved else "explanation", lc))

    particles = {}
    for pid, slug, pos, par in con.execute(
            "SELECT p.id, s.slug, t.position, p.particle FROM particle p JOIN sentence s ON s.id = p.sentence_id "
            "JOIN token t ON t.id = p.token_id"):
        particles[f"{slug}#{pos}"] = (pid, par)
    if set(particles) != set(derived) | set(ruled):
        raise SystemExit(f"table identities != DB particle rows ({len(set(particles) ^ (set(derived) | set(ruled)))})")

    rows, held = [], []
    stats: collections.Counter = collections.Counter()
    final: dict[str, str] = {}
    for key in sorted(particles, key=lambda k: (k.rsplit("#", 1)[0], int(k.rsplit("#", 1)[1]))):
        slug, pos_s = key.rsplit("#", 1)
        pos = int(pos_s)
        pid, par = particles[key]
        toks = toks_of[slug]
        if toks[pos]["surface"] != par:
            raise SystemExit(f"{key}: token surface {toks[pos]['surface']!r} != particle {par!r}")
        ruling = verdict = None
        if key in derived:
            usage, status = derived[key]["usage"], "auto"
        else:
            ruling, verdict = ruled[key], verdicts[key]
            if not isinstance(verdict, dict) or not isinstance(verdict.get("ok"), bool):
                usage, status = None, "verdict-missing"
            elif verdict["ok"]:
                usage, status = ruling.get("usage"), "verified"
            else:
                usage, status = verdict.get("corrected"), "ruled"
            if usage not in U:
                held.append({"slug": slug, "position": pos, "particle": par,
                             "reason": "verifier-rejected" if status != "verdict-missing" else status,
                             "ruled": ruling.get("usage") if isinstance(ruling, dict) else None,
                             "problem": (verdict or {}).get("problem")})
                stats["held:verifier-rejected"] += 1
                continue
        if not surface_matches(toks, pos, U[usage]):
            held.append({"slug": slug, "position": pos, "particle": par, "reason": "surface-mismatch",
                         "ruled": usage, "problem": f"{usage} is spelled {U[usage]['particle']!r}"
                                                    f"{' / ' + ' / '.join(U[usage]['allomorphs']) if U[usage]['allomorphs'] else ''}; "
                                                    f"no token span containing the particle spells it"})
            stats["held:surface-mismatch"] += 1
            continue
        expr = None
        if usage == "lex.fixed":
            texts = [(ruling or {}).get("reason"), (verdict or {}).get("problem")] + \
                    [loc.get((pid, "function", lc)) for lc in ("pt-BR", "en")] + \
                    [legacy(pid, lc) for lc in ("pt-BR", "en")]
            expr, how = pick_expression(toks, pos, texts)
            stats[f"lex-expression:{how}"] += 1
        slots = slots_for(enum, usage, toks, pos, expr)
        for k, v in slots.items():
            stats[f"slot:{k}:{'value' if v else 'fallback'}"] += 1
        row = {"slug": slug, "position": pos, "particle": par, "usage": usage, "usage_status": status,
               "legacy": {"pt-BR": sha(legacy(pid, "pt-BR")), "en": sha(legacy(pid, "en"))}}
        if U[usage]["compound"]:
            row["positions"] = span_spelling(toks, pos, forms(U[usage]))
        row.update(slots)
        rows.append(row)
        final[key] = usage
        stats[f"status:{status}"] += 1

    # compound spans: every particle inside one span should carry the same compound usage
    split = 0
    for r in rows:
        for p in r.get("positions") or []:
            other = final.get(f"{r['slug']}#{p}")
            if other is not None and other != r["usage"]:
                split += 1
    stats["compound-span-disagreements"] = split

    # ---------------------------------------------------------------- token roles
    td = json.loads((SRC / "token_roles_derived.json").read_text(encoding="utf-8"))
    roles: dict[str, list[list[Any]]] = {}
    for s in td["sentences"]:
        slug = s["slug"]
        toks = toks_of[slug]
        closer: dict[int, str | None] = {}
        for c, ch in enumerate(s["chunks"]):
            if not ch.get("particle"):
                continue
            ps = [t["position"] for t in s["tokens"] if t.get("chunk") == c and t.get("function") == "particle"]
            u = final.get(f"{slug}#{ps[-1]}") if ps else None
            closer[c] = U[u]["role"] if u and u != "lex.fixed" else None
        out = []
        for t in s["tokens"]:
            pos = t["position"]
            if pos >= len(toks) or toks[pos]["surface"] != t["surface"]:
                raise SystemExit(f"{slug}@{pos}: token_roles_derived surface {t['surface']!r} != DB")
            fn, ax, cr = t.get("function"), t.get("aux_function"), t.get("chunk_role")
            c = t.get("chunk")
            if fn not in ("particle", "punctuation") and closer.get(c):
                if cr and cr != closer[c]:
                    stats["chunk_role:changed-by-final-usage"] += 1
                elif not cr:
                    stats["chunk_role:filled-by-final-usage"] += 1
                cr = closer[c]
            for val, name in ((fn, "token_functions"), (ax, "aux_functions"), (cr, "chunk_roles")):
                if val is not None and val not in enums[name]:
                    raise SystemExit(f"{slug}@{pos}: {val!r} not in {name}")
            if fn or ax or cr:
                out.append([pos, t["surface"], fn, ax, cr])
                stats["tokens:with-role-fields"] += 1
                if cr:
                    stats["tokens:with-chunk_role"] += 1
        if out:
            roles[slug] = out

    usage_counts = collections.Counter(r["usage"] for r in rows)
    doc = {
        "unit": "W46 particle usage apply (research/reports/APP_PLAN.md Lane E)",
        "applied_by": "scripts/apply_particle_usage.py",
        "built_by": "scripts/assemble_particle_usage.py",
        "enum": {"file": "design/particle_functions.json", "schema_version": enum["version"],
                 "sha256": file_sha(ROOT / "design" / "particle_functions.json")},
        "inputs": {"derived": file_sha(SRC / "derived.json"),
                   "ruled": {Path(f).name: file_sha(Path(f)) for f in sorted(glob.glob(str(SRC / "ruled-work-*.json")))},
                   "verdicts": {Path(f).name: file_sha(Path(f)) for f in sorted(glob.glob(str(VERDICTS / "ruled-*.verdict.json")))}},
        "row_count": len(rows), "held_count": len(held),
        "stats": dict(sorted(stats.items())),
        "usage_counts": dict(sorted(usage_counts.items())),
        "rows": rows, "held": held,
    }
    roles_doc = {
        "unit": "W46 token roles (design/token_roles.json)", "applied_by": "scripts/apply_particle_usage.py",
        "built_by": "scripts/assemble_particle_usage.py",
        "source": {"file": "research/derived/repairs/particle_usage/token_roles_derived.json",
                   "sha256": file_sha(SRC / "token_roles_derived.json")},
        "columns": ["position", "surface", "function", "aux_function", "chunk_role"],
        "row_count": len(roles), "token_count": sum(len(v) for v in roles.values()),
        "rows": [{"slug": slug, "tokens": toks} for slug, toks in roles.items()],
    }
    print(json.dumps({"rows": len(rows), "held": len(held), "stats": doc["stats"]}, ensure_ascii=False, indent=1))
    if args.check:
        return 0

    def dump(path: Path, d: dict, row_keys: tuple[str, ...]) -> None:
        head = {k: v for k, v in d.items() if k not in row_keys}
        parts = [json.dumps(head, ensure_ascii=False, indent=1)[:-2]]
        for k in row_keys:
            v = d[k]
            if isinstance(v, list):
                body = ",\n".join("  " + json.dumps(x, ensure_ascii=False, separators=(",", ":")) for x in v)
                parts.append(f',\n "{k}": [\n{body}\n ]')
            else:
                body = ",\n".join(f"  {json.dumps(s, ensure_ascii=False)}: {json.dumps(x, ensure_ascii=False, separators=(',', ':'))}"
                                  for s, x in v.items())
                parts.append(f',\n "{k}": {{\n{body}\n }}')
        path.write_text("".join(parts) + "\n}\n", encoding="utf-8")
        json.loads(path.read_text(encoding="utf-8"))

    dump(OUT_USAGE, doc, ("rows", "held"))
    dump(OUT_ROLES, roles_doc, ("rows",))
    print(f"wrote {OUT_USAGE.relative_to(ROOT)} and {OUT_ROLES.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
