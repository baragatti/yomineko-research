#!/usr/bin/env python3
"""P4-w32-ingest, step 1: fold the W32 Layer-B into ONE tracked table the ingest reads.

Inputs (all under research/derived/pending/, the verdict stays there as the audit trail):
  w32_layerb_derived.json          62 unbanked survival-core rows, mechanical Layer-B + residue
  w32_layerb_authored.json         the residue, authored (62 literals, 62 paragraphs, 25 particle
                                   explanations, 8 rulings reaching the 9 ambiguous tokens), kind-tagged
  w32_layerb_authored.verdict.json the independent verifier: 151 ok, 6 corrected, 0 rejected, plus
                                   `outside_scope` findings on DERIVED slots the authored file never held

The derived and authored files were folded into the output and removed from pending/ when it was
applied (git history keeps them); the verdict stays. A re-run needs them restored from that commit.

Output: research/derived/repairs/w32_layerb.json, one row per sentence in the shape
scripts/ingest/ingest_mined_stages.py reads as a --source row WITH its Layer-B inline
(tokens / particles / structure paragraph), so one exact-match table is both the source and the batch.

Merge rules, none of them a judgement made here:
  * an authored value lands only under a verdict: ok -> as authored, ok false -> the verifier's
    `corrected` fields (every other authored field stands). A missing or null verdict is a refusal,
    never an acceptance (memory: a dead verifier excludes its rows).
  * rulings reach exactly the tokens they list, matched on key + position + lemma + pos.
  * OUTSIDE_SCOPE below: the verifier's findings on derived slots, each value named by it (or, for
    the two template wordings, the template with the real topic in place of the head noun).
  * finally every residue slot must be filled, every content token glossed, every particle carry a
    function and an explanation, and no learner-facing string may carry an em or en dash.

Every value keeps an `origin` so the table says who wrote it. Deterministic; writes one file.
Usage: python scripts/assemble_w32_layerb.py
"""
from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]

ROOT = Path(__file__).resolve().parents[1]
PENDING = ROOT / "research" / "derived" / "pending"
DERIVED = PENDING / "w32_layerb_derived.json"
AUTHORED = PENDING / "w32_layerb_authored.json"
VERDICT = PENDING / "w32_layerb_authored.verdict.json"
TABLE = PENDING / "speak_survival_cores.json"
OUT = ROOT / "research" / "derived" / "repairs" / "w32_layerb.json"

TOPIC_TEMPLATE = ("は apresenta {} como o tópico da frase, ou seja, o assunto sobre o qual se faz a "
                  "afirmação seguinte.")

# The verifier's outside_scope findings on DERIVED slots (w32_layerb_authored.verdict.json). Each entry:
# (key, position, field, old value it must replace, new value, which finding). A stale `old` refuses.
OUTSIDE_SCOPE: tuple[tuple[str, int, str, str, str, str], ...] = (
    ("1171888", 0, "gloss_pt", "quando", "que horas",
     "outside_scope 0: 何時 in 何時まで開いてますか is なんじ, 'que horas' (as in 172526 / 189309)"),
    ("122877", 0, "gloss_pt", "luz do sol; raios de sol", "Nikko (cidade)",
     "outside_scope 1: 日光 here is the place Nikko (bank precedent: 京都 'Kyoto (cidade)')"),
    ("11870768", 1, "gloss_pt", "lado, direção", "opção",
     "outside_scope 4: 方 in その方がいい is the comparative 'opção'"),
    ("235430", 2, "explanation_pt", TOPIC_TEMPLATE.format("部屋"), TOPIC_TEMPLATE.format("２人部屋"),
     "outside_scope 2: the topic is the compound ２人部屋, not its head noun"),
    ("3549484", 3, "explanation_pt", TOPIC_TEMPLATE.format("メニュー"),
     TOPIC_TEMPLATE.format("英語のメニュー"),
     "outside_scope 2: the topic is the の-phrase 英語のメニュー, not its head noun"),
)
DASHES = ("—", "–")


def load(p: Path) -> dict:
    return json.loads(p.read_text(encoding="utf-8"))


def verdict_value(verdicts: dict, kind: str, vkey: str, field: str, authored: str) -> tuple[str, str]:
    v = verdicts[kind].get(vkey)
    if not v or v.get("ok") is None:
        raise SystemExit(f"no verdict for {kind} {vkey}: an unverified row is never merged")
    if v["ok"]:
        return authored, "authored"
    if field not in (v.get("corrected") or {}):
        return authored, "authored"          # ok false corrected another field of the row
    return v["corrected"][field], "verifier-corrected"


def main() -> int:
    derived, authored, verdict = load(DERIVED), load(AUTHORED), load(VERDICT)
    verdicts = verdict["verdicts"]
    if verdict["counts"].get("rejected"):
        raise SystemExit("the verdict rejects rows; this assembler has no rule for them")
    registers = {r["sentence_slug"]: r["register"] for r in load(TABLE)["rows"]}

    rows: dict[str, dict] = {}
    for s in derived["sentences"]:
        rows[s["key"]] = {
            "key": s["key"], "slug": s["slug"], "stage": s["stage"], "function": s["function"],
            "tatoeba_id": None if s["generated"] else int(s["tatoeba_id"]),
            "generated": bool(s["generated"]), "jp": s["jp"], "en": s["en"], "pt": s["pt"],
            "register": registers[s["slug"]],
            "pt_literal": None, "structure_explanation_pt": None, "origin": {},
            "tokens": [dict({k: t[k] for k in ("position", "surface", "lemma", "pos", "gloss_pt")
                             if k in t}, origin=t["gloss_origin"]) for t in s["tokens"]],
            "particles": [{"position": p["position"], "particle": p["particle"],
                           "function_type": p["function_type"], "function_pt": p["function_pt"],
                           "function_origin": p["function_status"],
                           "explanation_pt": p["explanation_pt"],
                           "explanation_origin": p["explanation_status"]} for p in s["particles"]],
            "_residue": list(s["residue"]),
        }

    stats: Counter = Counter()
    for a in authored["rows"]:
        kind = a["kind"]
        if kind in ("literals", "paragraphs"):
            r = rows[a["key"]]
            src_field = "pt_literal" if kind == "literals" else "structure_explanation_pt"
            val, origin = verdict_value(verdicts, kind, a["key"], src_field, a[src_field])
            r[src_field] = val
            r["origin"][src_field] = origin
            r["_residue"].remove("translation_literal" if kind == "literals" else src_field)
        elif kind == "particles":
            r = rows[a["key"]]
            p = next(q for q in r["particles"] if q["position"] == a["position"])
            if (p["particle"], p["function_type"]) != (a["surface"], a["function_type"]):
                raise SystemExit(f"particle {a['key']}#{a['position']} no longer matches its slot")
            val, origin = verdict_value(verdicts, kind, f"{a['key']}#{a['position']}",
                                        "explanation_pt", a["explanation_pt"])
            p["explanation_pt"], p["explanation_origin"] = val, origin
            if a.get("function_pt"):
                p["function_pt"], p["function_origin"] = a["function_pt"], "authored"
            r["_residue"].remove(f"particle#{a['position']}:explanation")
        elif kind == "rulings":
            val, origin = verdict_value(verdicts, kind, f"{a['lemma']}|{a['pos']}", "ruling",
                                        a["ruling"])
            for reach in a["tokens"]:
                r = rows[reach["key"]]
                t = next(x for x in r["tokens"] if x["position"] == reach["position"])
                if (t["lemma"], t["pos"]) != (a["lemma"], a["pos"]):
                    raise SystemExit(f"ruling {a['lemma']}|{a['pos']} reaches {reach} which is "
                                     f"{t['lemma']}|{t['pos']}")
                t["gloss_pt"], t["origin"] = val, "ruling:" + origin
                r["_residue"].remove(f"token#{reach['position']}:ambiguous-verify")
        else:
            raise SystemExit(f"unknown authored kind {kind!r}")
        stats[kind] += 1

    for key, pos, field, old, new, why in OUTSIDE_SCOPE:
        r = rows[key]
        slot = next(x for x in (r["tokens"] if field == "gloss_pt" else r["particles"])
                    if x["position"] == pos)
        if slot[field] != old:
            raise SystemExit(f"outside_scope {key}@{pos} {field}: expected {old!r}, found "
                             f"{slot[field]!r}")
        slot[field] = new
        slot["origin" if field == "gloss_pt" else "explanation_origin"] = "verifier-outside-scope"
        slot["fix"] = why
        stats["outside_scope"] += 1

    problems = []
    for r in rows.values():
        if r["_residue"]:
            problems.append(f"{r['key']}: residue left {r['_residue']}")
        if not (r["pt_literal"] and r["structure_explanation_pt"]):
            problems.append(f"{r['key']}: literal or paragraph missing")
        problems += [f"{r['key']}@{t['position']}: no gloss" for t in r["tokens"] if not t.get("gloss_pt")]
        problems += [f"{r['key']}@{p['position']}: particle incomplete" for p in r["particles"]
                     if not (p["function_pt"] and p["explanation_pt"])]
        texts = [r["pt"], r["pt_literal"], r["structure_explanation_pt"]] + \
                [t["gloss_pt"] for t in r["tokens"]] + \
                [x for p in r["particles"] for x in (p["function_pt"], p["explanation_pt"])]
        if any(d in (x or "") for x in texts for d in DASHES):
            problems.append(f"{r['key']}: em/en dash in learner-facing text")
        del r["_residue"]
    if problems:
        print("\n".join(problems))
        raise SystemExit(f"{len(problems)} problem(s); nothing written")

    doc = {
        "unit": "P4-w32-ingest",
        "kind": "W32 survival-core rows with their Layer-B, verified and folded (ingest source + inline "
                "Layer-B)",
        "generated_by": "scripts/assemble_w32_layerb.py",
        "applied_by": "scripts/ingest/ingest_mined_stages.py --source research/derived/repairs/"
                      "w32_layerb.json --tag w32-survival-core --provenance-source w32:survival-core",
        "folded_from": ["research/derived/pending/w32_layerb_derived.json (scripts/derive_w32_layerb.py)",
                        "research/derived/pending/w32_layerb_authored.json",
                        "research/derived/pending/w32_layerb_authored.verdict.json (kept)"],
        "origin_values": {
            "authored": "authored residue, verifier ok",
            "verifier-corrected": "the verifier's `corrected` value",
            "verifier-outside-scope": "a derived slot the verifier flagged; value in `fix`",
            "ruling:authored": "an authored gloss ruling (verifier ok) on an ambiguous token",
            "other": "the derivation's own origin (registry / bank-modal / ruling / template ...)"},
        "counts": {"rows": len(rows), **dict(sorted(stats.items())),
                   "verdict": verdict["counts"]},
        "rows": sorted(rows.values(), key=lambda r: (r["generated"], r["tatoeba_id"] or 0)),
    }
    OUT.write_text(json.dumps(doc, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(json.dumps(doc["counts"], ensure_ascii=False))
    print(f"wrote {OUT.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
