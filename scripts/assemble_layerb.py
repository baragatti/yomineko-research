#!/usr/bin/env python3
"""W13b Assemble — merge the authored Layer-B back into the derived batches, by stable identity.

Reads `research/derived/n3_mined/layerb_derived/batch-*.json` (the mechanical derivation) and every
authoring output plus its verdict in `research/derived/n3_mined/layerb_out/`, and writes the merged
result to `research/derived/mined_layerb_n3/batch-NN.json` — the shape
`scripts/ingest/ingest_mined_stages.py` reads — plus `_summary.json`.

IDENTITY. Nothing merges by file order or array index; an authoring pass that drops, reorders or
re-batches its rows must still land on the right slot:

    tokens      (sentence key, position)
    particles   (sentence key, position)
    rulings     (lemma, pos)            — one decision, applied to every ambiguous token with that key
    paragraphs  (sentence key)

`key` is `str(tatoeba_id)` for a real sentence and `gen-<sha1(jp)[:12]>` for a generated one — see
scripts/derive_layerb.py::sentence_key. `position` is the C-token position from the Dissector, which is
also what persist_dissection.py keys Layer-B by, so the identity is the same one all the way to the DB.

VERDICTS LIVE IN A SIDECAR FILE, NOT IN THE ROW. The authors left `verdict: null` on every row
(9,177 of 9,177) and the independent verifiers wrote a separate file. Two filename patterns were
used — `<name>.json.verdict.json` and `<name>.verdict.json` — and ten batches carry both. A verdict
file is matched to its authored file by stripping either suffix; when both patterns exist for one
authored file they must be byte-identical, otherwise the later mtime wins and the divergence is
logged. Reading them as if they were authored files (which an earlier version of this script did,
because it globbed `*.json` and let `_kind` fall back to the filename prefix) double-counts every
verdict as an unverified authored row — that is what produced the 7,823 "unverified" paragraph rows
in a set that only holds 4,223.

The verifiers also used five different containers for their entries, all of them read here:

    {"rows": [ … ]}                        list of entries carrying their own identity
    {"verdicts": {"<id>": { … }}}          map keyed by identity
    {"entries":  {"<id>": { … }}}          map keyed by identity
    {"checks":   [ … ]}                    list of entries
    {"<id>": { … }, …}                     bare map, no wrapper at all

and the identity in a map key is `<key>` for paragraphs and `<key>#<position>` for particles/tokens.

A verdict entry says `ok: true/false` (and sometimes a `verdict` string). The replacement text, when
there is one, arrives as `corrected` (a plain string, or an object holding the field by name),
`verifier_<field>`, or `corrected_<field>`. The decision:

    ok true, no replacement          accept the authored text            status "verified"
    ok true, replacement present     merge the replacement               status "corrected"
    ok false / verdict "fix"         merge the replacement               status "corrected"
    ok false, no replacement         drop the row                        counted `rejected_no_correction`
    verdict "reject"                 drop the row                        counted `rejected`
    no entry at all                  EXCLUDED, never merged              counted `unverified_excluded`

The last line is the rule an earlier unit got wrong in the other direction (a null verdict silently
passing the row), and it is why the summary reports `unverified_excluded` per kind rather than
folding those rows into a success count.

RULINGS AND THEIR CONTEXT SPLITS. One ruling is one decision about a `(lemma, pos)` pair and reaches
every `ambiguous-verify` token carrying that pair. Where the author split the pair by context, the
split rides inside the ruling row under `context_overrides` / `per_context` / `context_glosses` (and
inside a verifier's `corrected` object under `per_context`), addressed by sentence key — sometimes by
`(key, position)`. Those splits inherit the ruling's verdict because they are part of the row the
verifier signed. The five `tokens-from-rulings-*.json` sidecars are a flattening of the same splits:
243 of their 302 rows restate a split already present in a verified ruling row (0 disagreements) and
are ignored as redundant; the 59 that appear nowhere else have no verdict of their own and are
excluded, so those tokens fall back to the verified pair-level ruling.

HONEST DEGRADATION. With no authoring outputs at all, this script still runs and still writes the
batches: every derived gloss is carried, every authored slot stays `author`, and the summary says
`ingest_ready: false` with the exact count of slots that would fail validate.py. It never invents a
value to fill a required field.

WHAT `ingest_ready` MEANS. `scripts/ingest/ingest_mined_stages.py` hands persist_dissection.py a
`structure_explanation_pt`, a `tokens` dict and a `particles` dict, and every bank sentence is
`dissection_tier: "full"`, which `scripts/validate/validate.py` reads as a hard promise of: a gloss on
every content token, an explanation on every particle, and a structure paragraph on the sentence.
Those three are the REQUIRED slots. `function_pt` is carried but is not required by the validator.

Read-only with respect to the corpus: no DB is opened, nothing under corpus/ or db/ is touched.

Usage: python scripts/assemble_layerb.py [--out DIR] [--outputs DIR] [--derived DIR]
"""
from __future__ import annotations

import argparse
import hashlib
import json
import random
import sys
from collections import Counter, defaultdict
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]

ROOT = Path(__file__).resolve().parents[1]
MINED = ROOT / "research" / "derived" / "n3_mined"
DERIVED = MINED / "layerb_derived"
OUTPUTS = MINED / "layerb_out"
TARGET = ROOT / "research" / "derived" / "mined_layerb_n3"

# The field each kind authors, and the field name a verifier's `corrected` object uses for it.
PRIMARY = {"rulings": "ruling", "tokens": "gloss_pt",
           "particles": "explanation_pt", "paragraphs": "structure_explanation_pt"}
# A rulings author sometimes wrote the decision under the token field name instead.
PRIMARY_ALIASES = {"rulings": ("ruling", "gloss_pt"), "tokens": ("gloss_pt",),
                   "particles": ("explanation_pt",), "paragraphs": ("structure_explanation_pt",)}

ROW_CONTAINERS = ("rows", "rulings", "tokens", "particles", "paragraphs")
VERDICT_CONTAINERS = ("rows", "verdicts", "entries", "checks")

VERIFIED, CORRECTED = "verified", "corrected"


# --------------------------------------------------------------------------- shape readers
def _rows(doc: object) -> list[dict]:
    """The authored rows, whichever container name this batch's author reached for."""
    if isinstance(doc, list):
        return [r for r in doc if isinstance(r, dict)]
    if isinstance(doc, dict):
        for field in ROW_CONTAINERS:
            v = doc.get(field)
            if isinstance(v, list):
                return [r for r in v if isinstance(r, dict)]
    return []


def _verdict_entries(doc: object) -> list[tuple[str | None, dict]]:
    """(map key or None, entry) for every verdict, across all five containers seen in the wild."""
    out: list[tuple[str | None, dict]] = []
    if isinstance(doc, list):
        return [(None, e) for e in doc if isinstance(e, dict)]
    if not isinstance(doc, dict):
        return out
    for field in VERDICT_CONTAINERS:
        v = doc.get(field)
        if isinstance(v, list):
            return [(None, e) for e in v if isinstance(e, dict)]
        if isinstance(v, dict):
            return [(k, e) for k, e in v.items() if isinstance(e, dict)]
    # No wrapper: a bare map from identity to entry. Only accept it when every value is an entry,
    # so a metadata-only header is never mistaken for one.
    if doc and all(isinstance(v, dict) for v in doc.values()):
        return [(k, e) for k, e in doc.items()]
    return out


def _kind(path: Path, doc: object) -> str:
    declared = doc.get("kind") if isinstance(doc, dict) else None
    if isinstance(declared, str):
        d = declared.lower().replace("-verdict", "").strip()
        if d in PRIMARY:
            return d
        # e.g. "authored particle explanations (Layer C)"
        for k in ("ruling", "token", "particle", "paragraph"):
            if k in d:
                return k + "s"
    stem = path.name.lower()
    for k in ("ruling", "token", "particle", "paragraph"):
        if stem.startswith(k):
            return k + "s"
    return "unknown"


# --------------------------------------------------------------------------- identity
def _ident(kind: str, row: dict, map_key: str | None) -> tuple | None:
    """The stable identity of an authored row or a verdict entry."""
    if kind == "rulings":
        lemma, pos = row.get("lemma"), row.get("pos")
        if lemma is None and map_key and "|" in map_key:
            lemma, _, pos = map_key.partition("|")
        return (lemma, pos) if lemma is not None else None
    if kind == "paragraphs":
        key = row.get("key") if row.get("key") is not None else map_key
        return (str(key),) if key is not None else None
    # tokens / particles
    key, position = row.get("key"), row.get("position")
    if (key is None or position is None) and map_key and "#" in map_key:
        mk, _, mp = map_key.rpartition("#")
        if key is None:
            key = mk
        if position is None and mp.isdigit():
            position = int(mp)
    if key is None or position is None:
        return None
    return (str(key), int(position))


# --------------------------------------------------------------------------- verdict decision
def _text(v: object) -> str | None:
    return v.strip() if isinstance(v, str) and v.strip() else None


def _replacement(entry: dict, field: str) -> str | None:
    """The verifier's replacement text for `field`, in any of the shapes the verifiers used."""
    c = entry.get("corrected")
    if isinstance(c, str):
        t = _text(c)
        if t:
            return t
    elif isinstance(c, dict):
        for f in (field, f"{field}_revised", f"{field}_corrected"):
            t = _text(c.get(f))
            if t:
                return t
    for f in (f"verifier_{field}", f"corrected_{field}", f"{field}_corrected"):
        t = _text(entry.get(f))
        if t:
            return t
    return None


def _function_replacement(entry: dict) -> str | None:
    c = entry.get("corrected")
    if isinstance(c, dict):
        for f in ("function_pt", "function_pt_revised", "corrected_function_pt"):
            t = _text(c.get(f))
            if t:
                return t
    return _text(entry.get("corrected_function_pt")) or _text(entry.get("verifier_function_pt"))


def _corrected_object(entry: dict) -> dict:
    c = entry.get("corrected")
    return c if isinstance(c, dict) else {}


def decide(entry: dict | None, field: str,
           side_fields: tuple[str, ...] = ()) -> tuple[str, str | None]:
    """(decision, replacement).

    decision ∈ accept | accept_side_fix | correct | reject | no_correction | unverified.

    `side_fields` are fields of the same row that are NOT the authored text this slot needs —
    for particles, `function_pt`. Fifteen particle verdicts read `ok: false` while the object under
    `corrected` holds only `function_pt`, and the `problem` text explicitly endorses the authored
    explanation ("A explicação já diz …") — the verifier is rejecting the bank's modal LABEL, not
    the learner-facing explanation. Dropping those rows would empty fifteen required slots over a
    complaint about a different field, so the primary text is accepted and the side correction is
    applied on top, under its own count (`accepted_with_side_fix`) so the split stays auditable.
    """
    if entry is None:
        return "unverified", None
    verdict = (entry.get("verdict") or "").strip().lower() if isinstance(entry.get("verdict"), str) else ""
    ok = entry.get("ok")
    repl = _replacement(entry, field)
    if verdict == "reject":
        return "reject", None
    if ok is False or verdict == "fix":
        if repl:
            return "correct", repl
        if any(_replacement(entry, sf) or (sf == "function_pt" and _function_replacement(entry))
               for sf in side_fields):
            return "accept_side_fix", None
        return "no_correction", None
    if ok is True or verdict == "ok":
        # A verifier that marked a row ok but still wrote a replacement means the replacement.
        return ("correct", repl) if repl else ("accept", None)
    return "unverified", None


# --------------------------------------------------------------------------- context splits
def _split_targets(e: dict) -> list[tuple[str, int | None]]:
    """(sentence key, position or None) addressed by one context-split entry."""
    out: list[tuple[str, int | None]] = []
    for k in (e.get("keys") or []):
        out.append((str(k), None))
    if e.get("key") is not None:
        out.append((str(e["key"]), e.get("position") if isinstance(e.get("position"), int) else None))
    for o in (e.get("occurrences") or []):
        if isinstance(o, dict) and o.get("key") is not None:
            p = o.get("position")
            out.append((str(o["key"]), p if isinstance(p, int) else None))
        elif isinstance(o, (str, int)):
            out.append((str(o), None))
    return out


def collect_splits(row: dict, entry: dict | None) -> list[tuple[str, int | None, str]]:
    """Context splits declared by an accepted ruling row (verifier's version wins when present)."""
    sources: list[dict] = []
    corr = _corrected_object(entry or {})
    for fld in ("context_overrides", "per_context", "context_glosses"):
        v = corr.get(fld) if isinstance(corr.get(fld), list) else row.get(fld)
        if isinstance(v, list):
            sources.append({fld: v})
    out: list[tuple[str, int | None, str]] = []
    for src in sources:
        for _, entries in src.items():
            for e in entries:
                if not isinstance(e, dict):
                    continue
                g = _text(e.get("gloss_pt")) or _text(e.get("ruling"))
                if not g:
                    continue
                for key, pos in _split_targets(e):
                    out.append((key, pos, g))
    return out


# --------------------------------------------------------------------------- file pairing
def pair_files(outputs: Path, warnings: list[str]) -> tuple[list[Path], dict[str, Path]]:
    """(authored files, authored-name -> verdict file), collapsing the two verdict filename patterns."""
    authored: list[Path] = []
    candidates: dict[str, list[Path]] = defaultdict(list)
    for f in sorted(outputs.glob("*.json")):
        if f.name.startswith("_"):
            continue
        if f.name.endswith(".json.verdict.json"):
            candidates[f.name[: -len(".json.verdict.json")] + ".json"].append(f)
        elif f.name.endswith(".verdict.json"):
            candidates[f.name[: -len(".verdict.json")] + ".json"].append(f)
        else:
            authored.append(f)
    verdicts: dict[str, Path] = {}
    for base, files in candidates.items():
        if len(files) == 1:
            verdicts[base] = files[0]
            continue
        digests = {hashlib.sha256(f.read_bytes()).hexdigest() for f in files}
        chosen = max(files, key=lambda f: f.stat().st_mtime)
        if len(digests) == 1:
            warnings.append(f"{base}: {len(files)} verdict files under both filename patterns "
                            f"({', '.join(f.name for f in files)}) — byte-identical, read once")
        else:
            warnings.append(f"{base}: {len(files)} verdict files DISAGREE "
                            f"({', '.join(f.name for f in files)}) — later mtime wins: {chosen.name}")
        verdicts[base] = chosen
    orphan = sorted(set(verdicts) - {f.name for f in authored})
    for o in orphan:
        warnings.append(f"verdict file for {o} has no authored file — ignored")
        verdicts.pop(o, None)
    return authored, verdicts


# --------------------------------------------------------------------------- main
def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--derived", type=Path, default=DERIVED)
    ap.add_argument("--outputs", type=Path, default=OUTPUTS)
    ap.add_argument("--out", type=Path, default=TARGET)
    ap.add_argument("--sample", type=int, default=0, help="write N random sentences to --sample-out")
    ap.add_argument("--sample-out", type=Path, default=None)
    ap.add_argument("--sample-seed", type=int, default=13)
    args = ap.parse_args()

    batches = sorted(args.derived.glob("batch-*.json"))
    if not batches:
        print(f"no derived batches in {args.derived} — run scripts/derive_layerb.py first")
        return 1

    warnings: list[str] = []
    args.outputs.mkdir(parents=True, exist_ok=True)
    authored_files, verdict_files = pair_files(args.outputs, warnings)

    stats: Counter = Counter()
    files_read: list[dict] = []
    token_gloss: dict[tuple, tuple[str, str]] = {}        # (key,pos)   -> (text, status)
    particle_expl: dict[tuple, tuple[str, str]] = {}      # (key,pos)   -> (text, status)
    particle_func: dict[tuple, tuple[str, str]] = {}      # (key,pos)   -> (label, status)
    ruling: dict[tuple, tuple[str, str]] = {}             # (lemma,pos) -> (text, status)
    ruling_ctx: dict[tuple, tuple[str, str]] = {}         # (lemma,pos,key[,pos]) -> (text, status)
    paragraph: dict[str, tuple[str, str]] = {}            # key         -> (text, status)
    dead_batches: list[str] = []
    excluded_tokens: list[dict] = []                      # rows dropped for want of a verdict

    for f in authored_files:
        doc = json.loads(f.read_text(encoding="utf-8"))
        kind, rows = _kind(f, doc), _rows(doc)
        field = PRIMARY.get(kind, "")
        vf = verdict_files.get(f.name)
        ventries: dict[tuple, dict] = {}
        if vf is not None:
            vdoc = json.loads(vf.read_text(encoding="utf-8"))
            for mk, e in _verdict_entries(vdoc):
                ident = _ident(kind, e, mk)
                if ident is None:
                    stats[f"{kind}:verdict-entry-without-identity"] += 1
                    continue
                ventries[ident] = e
        rec = {"file": f.name, "kind": kind, "rows": len(rows),
               "verdict_file": vf.name if vf else None, "verdict_entries": len(ventries)}
        files_read.append(rec)
        if rows and not ventries:
            dead_batches.append(f.name)
            rec["dead"] = "no parseable verdict entries — every row excluded"

        counted: Counter = Counter()
        for r in rows:
            ident = _ident(kind, r, None)
            if ident is None:
                stats[f"{kind}:row-without-identity"] += 1
                continue
            entry = ventries.get(ident)
            # a rulings author may have written the decision under the token field name
            if kind == "rulings" and not r.get("ruling") and r.get("gloss_pt"):
                r = {**r, "ruling": r["gloss_pt"]}
            decision, repl = decide(entry, field,
                                    side_fields=("function_pt",) if kind == "particles" else ())
            if decision == "unverified":
                stats[f"{kind}:unverified_excluded"] += 1
                counted["unverified"] += 1
                if kind == "tokens":
                    excluded_tokens.append({"file": f.name, "key": str(r.get("key")),
                                            "position": r.get("position"), "lemma": r.get("lemma"),
                                            "pos": r.get("pos"),
                                            "gloss_pt": _text(r.get("gloss_pt"))})
                continue
            if decision == "reject":
                stats[f"{kind}:rejected"] += 1
                continue
            if decision == "no_correction":
                stats[f"{kind}:rejected_no_correction"] += 1
                continue
            if decision == "correct":
                text, status = repl, CORRECTED
            else:
                text, status = None, VERIFIED
                for alias in PRIMARY_ALIASES.get(kind, (field,)):
                    text = _text(r.get(alias))
                    if text:
                        break
                if decision == "accept_side_fix":
                    stats[f"{kind}:accepted_with_side_fix"] += 1
            if not text:
                stats[f"{kind}:empty-text"] += 1
                continue
            stats[f"{kind}:{status}"] += 1

            if kind == "rulings":
                ruling[ident] = (text, status)
                for skey, spos, sgloss in collect_splits(r, entry):
                    ruling_ctx[(ident[0], ident[1], skey, spos)] = (sgloss, status)
                    stats["rulings:context_splits"] += 1
            elif kind == "tokens":
                token_gloss[ident] = (text, status)
            elif kind == "particles":
                particle_expl[ident] = (text, status)
                fixed = _function_replacement(entry or {})
                if fixed:
                    particle_func[ident] = (fixed, CORRECTED)
                    stats["particles:function_pt_corrected"] += 1
                else:
                    fn = (_text(r.get("function_pt_corrected"))
                          or _text(r.get("function_pt_revised")) or _text(r.get("function_pt")))
                    if fn:
                        particle_func[ident] = (fn, VERIFIED)
            elif kind == "paragraphs":
                paragraph[ident[0]] = (text, status)
            else:
                stats["unknown-kind-rows"] += 1

    # How much of an excluded token row is already said by a VERIFIED ruling context split — the
    # difference between "redundant, nothing lost" and "a decision that reaches the corpus nowhere".
    sidecar_unique: list[dict] = []
    for x in excluded_tokens:
        ctx = (ruling_ctx.get((x["lemma"], x["pos"], x["key"], x["position"]))
               or ruling_ctx.get((x["lemma"], x["pos"], x["key"], None)))
        if ctx and (ctx[0] or "").strip() == (x["gloss_pt"] or "").strip():
            stats["tokens:excluded_but_redundant_with_verified_ruling_split"] += 1
        elif ctx:
            stats["tokens:excluded_and_DISAGREES_with_verified_ruling_split"] += 1
            sidecar_unique.append(x)
        else:
            stats["tokens:excluded_and_said_nowhere_else"] += 1
            sidecar_unique.append(x)

    # ------------------------------------------------------------------ merge
    args.out.mkdir(parents=True, exist_ok=True)
    for f in args.out.glob("batch-*.json"):
        f.unlink()

    counts: Counter = Counter()
    empty_reasons: Counter = Counter()
    missing_examples: list[dict] = []
    all_sentences: list[dict] = []

    def note_empty(kind: str, key: str, position: int | None, reason: str) -> None:
        empty_reasons[f"{kind}:{reason}"] += 1
        if len(missing_examples) < 40:
            missing_examples.append({"kind": kind, "key": key, "position": position,
                                     "reason": reason})

    for bi, bf in enumerate(batches, 1):
        doc = json.loads(bf.read_text(encoding="utf-8"))
        out = []
        for s in doc["sentences"]:
            key = str(s["key"])
            toks = []
            for t in s["tokens"]:
                gloss = t.get("gloss_pt")
                origin, status = t.get("gloss_origin"), t["gloss_status"]
                counts["token:slots"] += 1
                lp = (t.get("lemma"), t.get("pos"))
                authored = token_gloss.get((key, t["position"]))
                if authored:
                    gloss, origin, status = authored[0], "authored", authored[1]
                elif t["gloss_status"] == "ambiguous-verify":
                    ctx = (ruling_ctx.get((lp[0], lp[1], key, t["position"]))
                           or ruling_ctx.get((lp[0], lp[1], key, None)))
                    if ctx:
                        gloss, origin, status = ctx[0], "ruling-context", ctx[1]
                    else:
                        ruled = ruling.get(lp)
                        if ruled:
                            gloss, origin, status = ruled[0], "ruling", ruled[1]
                        else:
                            counts["token:ruling_missing"] += 1
                if status in (VERIFIED, CORRECTED):
                    counts[f"token:filled_{status}"] += 1
                elif status == "unique-accept":
                    counts["token:derived_carried"] += 1
                else:
                    counts[f"token:{status}"] += 1
                row = {"position": t["position"], "lemma": t.get("lemma"), "pos": t.get("pos"),
                       "gloss_status": status, "gloss_origin": origin}
                if gloss:
                    row["gloss_pt"] = gloss
                else:
                    counts["token:EMPTY"] += 1
                    note_empty("token", key, t["position"],
                               "no ruling for (lemma, pos)" if t["gloss_status"] == "ambiguous-verify"
                               else "residue token never authored (work list tokens-residue.json "
                                    "has no output file)")
                toks.append(row)

            parts = []
            for p in s["particles"]:
                expl, estatus = p.get("explanation_pt"), p["explanation_status"]
                counts["particle:slots"] += 1
                authored = particle_expl.get((key, p["position"]))
                if authored:
                    expl, estatus = authored[0], authored[1]
                fpair = particle_func.get((key, p["position"]))
                func = fpair[0] if fpair else p.get("function_pt")
                fstatus = fpair[1] if fpair else p.get("function_status")
                if estatus in (VERIFIED, CORRECTED):
                    counts[f"particle:filled_{estatus}"] += 1
                elif estatus == "template":
                    counts["particle:derived_carried"] += 1
                else:
                    counts[f"particle:{estatus}"] += 1
                if not expl:
                    counts["particle:EMPTY"] += 1
                    note_empty("particle", key, p["position"],
                               "authored row excluded or never written")
                parts.append({"position": p["position"], "particle": p["particle"],
                              "function_type": p["function_type"], "function_pt": func,
                              "function_status": fstatus,
                              "explanation_pt": expl, "explanation_status": estatus})

            counts["structure:slots"] += 1
            para = paragraph.get(key)
            if para:
                ptext, sstatus = para
                counts[f"structure:filled_{sstatus}"] += 1
            else:
                ptext, sstatus = s.get("structure_explanation_pt"), s.get("structure_status", "author")
                if ptext:
                    counts["structure:derived_carried"] += 1
                else:
                    counts["structure:EMPTY"] += 1
                    note_empty("structure", key, None, "paragraph row excluded or never written")

            rec = {"key": key, "tatoeba_id": s.get("tatoeba_id"), "slug": s.get("slug"),
                   "generated": s.get("generated"), "jp": s.get("jp"),
                   "lesson": s.get("lesson"), "targets": s.get("targets"),
                   "clause_structure_predicted": s.get("clause_structure_predicted"),
                   "tokens": toks, "particles": parts,
                   "structure_explanation_pt": ptext,
                   "structure_status": sstatus}
            out.append(rec)
            all_sentences.append(rec)
        (args.out / f"batch-{bi:02d}.json").write_text(
            json.dumps({"batch": bi, "unit": "W13b",
                        "kind": "assembled mined N3 Layer-B (derived + authored + verified)",
                        "sentences": out}, ensure_ascii=False, indent=1), encoding="utf-8")

    # ------------------------------------------------------------------ summary
    def kind_block(kind: str) -> dict:
        return {
            "slots_total": counts[f"{kind}:slots"],
            "derived_carried": counts[f"{kind}:derived_carried"],
            "filled_verified": counts[f"{kind}:filled_verified"],
            "filled_corrected": counts[f"{kind}:filled_corrected"],
            "still_empty": counts[f"{kind}:EMPTY"],
            "empty_reasons": {k.split(":", 1)[1]: v for k, v in sorted(empty_reasons.items())
                              if k.startswith(f"{kind}:")},
        }

    kinds = {k: kind_block(k) for k in ("token", "particle", "structure")}
    blocking = sum(kinds[k]["still_empty"] for k in kinds)
    summary = {
        "unit": "W13b",
        "generated_by": "scripts/assemble_layerb.py",
        "derived_from": str(args.derived.relative_to(ROOT)).replace("\\", "/"),
        "authored_files": len(files_read),
        "authored_rows": sum(r["rows"] for r in files_read),
        "verdict_entries": sum(r["verdict_entries"] for r in files_read),
        "dead_batches": dead_batches,
        "excluded_token_rows_said_nowhere_else": sorted(
            {x["file"] for x in sidecar_unique}) or [],
        "excluded_token_rows_said_nowhere_else_count": len(sidecar_unique),
        "warnings": warnings,
        "merge": dict(sorted(stats.items())),
        "kinds": kinds,
        "slots": dict(sorted(counts.items())),
        "ingest_ready": blocking == 0,
        "required_slots": ("token gloss on every content token, explanation on every particle, "
                           "structure paragraph on every sentence — validate.py's dissection_tier "
                           "'full' contract, read from scripts/validate/validate.py"),
        "blocking_empty_required_slots": blocking,
        "blocking_examples": missing_examples,
        "outputs_read": files_read,
        "note": ("A row whose verdict entry is absent is unverified and is never merged. "
                 "`ingest_ready: false` means validate.py would reject the ingest: some required "
                 "slot is still empty."),
    }
    (args.out / "_summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=1),
                                            encoding="utf-8")

    if args.sample and args.sample_out:
        rng = random.Random(args.sample_seed)
        picked = rng.sample(all_sentences, min(args.sample, len(all_sentences)))
        rulings_flat = [{"lemma": k[0], "pos": k[1], "ruling": v[0], "status": v[1]}
                        for k, v in ruling.items()]
        rng.shuffle(rulings_flat)
        args.sample_out.write_text(json.dumps(
            {"sentences": picked, "rulings": rulings_flat[:20],
             "ruling_contexts": [{"lemma": k[0], "pos": k[1], "key": k[2], "position": k[3],
                                  "gloss_pt": v[0], "status": v[1]}
                                 for k, v in list(ruling_ctx.items())]},
            ensure_ascii=False, indent=1), encoding="utf-8")

    print(f"read {len(files_read)} authoring file(s), "
          f"{summary['verdict_entries']} verdict entries")
    for w in warnings:
        print(f"  warning: {w}")
    print(json.dumps({"merge": summary["merge"], "kinds": kinds,
                      "ingest_ready": summary["ingest_ready"],
                      "blocking_empty_required_slots": blocking}, ensure_ascii=False, indent=1))
    print(f"wrote {len(batches)} batches to {args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
