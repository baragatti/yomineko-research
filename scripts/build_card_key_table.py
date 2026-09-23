#!/usr/bin/env python3
"""W27 — turn the authored production keys into the exact-match table the apply replays.

WHY THIS IS A BUILDER AND NOT THE TABLE ITSELF
----------------------------------------------
`research/derived/card_keys_authored.json` (the campaign artifact, moved out of
`research/derived/pending/` by this apply) held 2,946 rows authored against the tree of
2026-09-02. Two things moved under it before it could be applied: W09 re-pointed eight vocab records
(`corpus/vocab_redirects.json`), so eight rows address a record their card no longer names, and W11a
created five unlocks, so five production cards have no row at all. The Fable 100-row sample
(`research/reports/w27_sample_report.md`) hit two of the eight by chance, called the table a pass at
2/100, and made three mechanical rules binding for the apply. This script is those rules, executable:

  1. **Resolve every `vocab` through `corpus/vocab_redirects.json`.** A row whose slug is redirected
     is DROPPED (its prompt describes the retired lexeme, not the card), and the re-authored row for
     the new record comes from `research/derived/card_key_residue.json` instead — together with the
     five W11a cards. Thirteen rows, and they are the only authoring in this unit.
  2. **Strip rare, archaic, search-only and irregular forms from `accept` by JMdict tag.** The sample
     found a learner could answer み for "mar" (海 accepted the out-dated み/わた/わだ) or あぢぃ for
     "quente". The tags are read from the ingested dictionary itself
     (`research/datasets/jmdict/jmdict-eng-*.json.zip`, `kanji[].tags` + `kana[].tags`), matched
     case-insensitively against {rK/rk, sK/sk, oK/ok, iK/ik, arch} — the set the sample report names,
     with both the kanji-side and kana-side spellings of each, because あぢぃ is `sk` and 其の is `rK`
     and the report cites both. `ateji`, `gikun` and `io` are deliberately NOT in the set: 珈琲, きょう
     and 隣り are how people actually write those words.
     The record's own headword and kana are never stripped, per the report's "keep the headword, its
     common kanji variants and the kana". `arch` is a sense-level misc in JMdict and tags no form, so
     it removes nothing; the archaic forms the sample complained about carry `ok`/`oK`.
  3. **Drop a form the record does not carry.** 56 accept forms are absent from the record's `forms[]`.
     54 are NFKC twins of a form it does carry — `5日` for `５日`, `FAX` for `ＦＡＸ`, `タヒぬ` for the
     halfwidth `ﾀﾋぬ` — and those are legitimate answers, so they stay (the same NFKC-twin rule the
     speak bank already uses for fullwidth keys). The other 2 are net-slang respellings of the topic
     particle, それでわ and じつわ, which no JMdict tag covers and which `validate_card_content.py`
     check C would refuse. They are dropped and logged.
  4. **Apply the residue file's `prompt_overrides`.** One campaign prompt failed
     `audit_hygiene_all_locales.py`: it used `comboio`, which is pt-PT for a train and means a convoy
     in pt-BR. The rewrite lives in `research/derived/card_key_residue.json`, not in the campaign
     artifact, so the artifact stays the record of what W27 authored and the change stays visible.

Every surviving row is stamped `verified: "sampled"` with a pointer to the sample report: this table
went through one verifier at authoring time and a Fable sample before apply, which is what
APP_PLAN §1 "verify once" asks for, and it is NOT the same claim as row-by-row verification.

OUTPUT
------
`research/derived/repairs/card_production_keys.json` — one row per (lesson, item) production card,
carrying the applied `prompt`/`accept`/`sense_index` AND, per row, what was removed and why. The row
is exact-match: `validate_repairs_applied.py` asserts the exported card carries exactly this key.

Idempotent and deterministic: same inputs, same bytes. Run it again after an edit to the residue
file or the redirects, then re-run `scripts/apply_card_production_keys.py`.

Usage: build_card_key_table.py [--out PATH]
"""
from __future__ import annotations

import argparse
import json
import sys
import unicodedata
import zipfile
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]

ROOT = Path(__file__).resolve().parents[1]
# The W27 campaign's own output, moved out of research/derived/pending/ when it was applied: pending/
# means authored-and-NOT-applied (STATE.md), and this table is applied now. It is kept verbatim as the
# authoring layer -- the record of what the campaign wrote -- and every change made to it since is a
# rule in this file or an override in the residue, never an edit to the artifact.
AUTHORED = ROOT / "research" / "derived" / "card_keys_authored.json"
RESIDUE = ROOT / "research" / "derived" / "card_key_residue.json"
REDIRECTS = ROOT / "corpus" / "vocab_redirects.json"
VOCAB = ROOT / "corpus" / "vocab"
COURSE = ROOT / "course"
JMDICT_DIR = ROOT / "research" / "datasets" / "jmdict"
OUT = ROOT / "research" / "derived" / "repairs" / "card_production_keys.json"
SAMPLE = "research/reports/w27_sample_report.md"
# Case-insensitive. JMdict spells the kanji-side and kana-side of the same idea differently
# (rK/rk, sK/sk, oK/ok, iK/ik); the sample report cites members of both, so both are in.
STRIP_TAGS = {"rk", "sk", "ok", "ik", "arch"}


def nfkc(s: str) -> str:
    return unicodedata.normalize("NFKC", s)


def load_form_tags() -> dict[str, dict[str, list[str]]]:
    """jmdict id -> {surface: [tags]}, read straight out of the archived dictionary."""
    zips = sorted(JMDICT_DIR.glob("jmdict-eng-3*.json.zip"))
    if not zips:
        raise SystemExit(f"no jmdict-eng zip under {JMDICT_DIR} — the tag source is not optional")
    z = zipfile.ZipFile(zips[-1])
    with z.open(z.namelist()[0]) as f:
        data = json.load(f)
    out: dict[str, dict[str, list[str]]] = {}
    for entry in data["words"]:
        m: dict[str, list[str]] = {}
        for group in (entry["kanji"], entry["kana"]):
            for k in group:
                m.setdefault(k["text"], []).extend(k.get("tags") or [])
        out[entry["id"]] = m
    return out


def load_vocab() -> dict[str, dict]:
    out = {}
    for f in sorted(VOCAB.glob("n*.json")):
        for rec in json.loads(f.read_text(encoding="utf-8")):
            out[rec["slug"]] = rec
    if not out:
        raise SystemExit(f"no vocab records under {VOCAB}")
    return out


def live_cards() -> dict[tuple[str, str], str]:
    """(lesson, item) -> deck, for every exported production card on a vocab record."""
    out: dict[tuple[str, str], str] = {}
    for f in sorted(COURSE.glob("n*/topic-*/lesson-*.json")) + \
             sorted(COURSE.glob("pre-n5/topic-*/lesson-*.json")):
        L = json.loads(f.read_text(encoding="utf-8"))
        for c in (L.get("srs") or {}).get("introduces_cards") or []:
            if "production" in (c.get("card_types") or []) and c["item"].startswith("vocab:"):
                out[(L["id"], c["item"])] = c["deck"]
    return out


def strip_accept(accept: list[str], rec: dict, tags: dict[str, list[str]]) -> tuple[list[str], list[dict]]:
    """Rules 2 and 3. Returns (kept, removed) with a reason per removed form."""
    forms = {f["form"] for f in rec["forms"]}
    nforms = {nfkc(f) for f in forms}
    protected = {rec["headword"], rec["kana"]}
    kept: list[str] = []
    removed: list[dict] = []
    for a in accept:
        hit = sorted({t for t in (tags.get(a) or []) if t.lower() in STRIP_TAGS})
        if hit and a not in protected:
            removed.append({"form": a, "reason": "jmdict-tag", "tags": hit})
            continue
        if a not in forms and nfkc(a) not in nforms:
            removed.append({"form": a, "reason": "not-a-form-of-this-record", "tags": hit})
            continue
        kept.append(a)
    return kept, removed


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=str(OUT))
    args = ap.parse_args()

    authored = json.loads(AUTHORED.read_text(encoding="utf-8"))["cards"]
    residue = json.loads(RESIDUE.read_text(encoding="utf-8"))
    redirects = json.loads(REDIRECTS.read_text(encoding="utf-8"))
    vocab = load_vocab()
    tags = load_form_tags()
    cards = live_cards()

    rows: list[dict] = []
    dropped_repointed: list[dict] = []
    counts = {"authored_in": len(authored), "residue_in": len(residue["rows"]),
              "dropped_repointed": 0, "rows": 0, "rows_with_a_form_removed": 0,
              "forms_removed": 0}
    by_tag: dict[str, int] = {}
    removed_not_a_form: list[dict] = []

    overrides = {(o["lesson"], o["vocab"]): o for o in residue.get("prompt_overrides") or []}
    applied_overrides: list[dict] = []

    for r in authored:
        if r["vocab"] in redirects:
            dropped_repointed.append({"lesson": r["lesson"], "vocab": r["vocab"],
                                      "now": redirects[r["vocab"]], "prompt_pt": r["prompt_pt"],
                                      "accept": r["accept"]})
            continue
        rec = vocab.get(r["vocab"])
        if rec is None:
            raise SystemExit(f"{r['lesson']}/{r['vocab']}: no such vocab record")
        kept, removed = strip_accept(r["accept"], rec, tags.get(r["vocab"].split(":", 1)[1], {}))
        ov = overrides.get((r["lesson"], r["vocab"]))
        if ov is not None:
            if ov["was"] != r["prompt_pt"]:
                raise SystemExit(f"{r['lesson']}/{r['vocab']}: override `was` does not match the "
                                 f"authored prompt -- the artifact moved under the override")
            applied_overrides.append(ov)
        prompt = ov["prompt"] if ov is not None else {"pt-BR": r["prompt_pt"]}
        rows.append({"lesson": r["lesson"], "item": r["vocab"],
                     "origin": "w27-campaign" if ov is None else "w27-campaign+hygiene",
                     "prompt": prompt, "accept": kept,
                     "sense_index": r["sense_index"], "why": r.get("why", ""),
                     "verified": "sampled", "verified_by": SAMPLE,
                     "accept_removed": removed})
        for x in removed:
            counts["forms_removed"] += 1
            if x["reason"] == "jmdict-tag":
                for t in x["tags"]:
                    by_tag[t] = by_tag.get(t, 0) + 1
            else:
                removed_not_a_form.append({"lesson": r["lesson"], "item": r["vocab"],
                                           "record": f"{rec['headword']}/{rec['kana']}",
                                           "form": x["form"]})
        if removed:
            counts["rows_with_a_form_removed"] += 1
    counts["dropped_repointed"] = len(dropped_repointed)
    if len(applied_overrides) != len(overrides):
        raise SystemExit(f"{len(overrides)} prompt override(s) declared, {len(applied_overrides)} "
                         f"matched a campaign row -- a stale override is a silent no-op")

    for r in residue["rows"]:
        rec = vocab.get(r["vocab"])
        if rec is None:
            raise SystemExit(f"{r['lesson']}/{r['vocab']}: residue names no such vocab record")
        kept, removed = strip_accept([f["form"] for f in rec["forms"]], rec,
                                     tags.get(r["vocab"].split(":", 1)[1], {}))
        if kept != r["accept_expected"]:
            raise SystemExit(f"{r['lesson']}/{r['vocab']}: accept_expected {r['accept_expected']} "
                             f"but the record's forms strip to {kept}")
        rows.append({"lesson": r["lesson"], "item": r["vocab"], "origin": r["origin"],
                     "prompt": r["prompt"], "accept": kept, "sense_index": r["sense_index"],
                     "why": r["why"], "verified": "sampled", "verified_by": SAMPLE,
                     "accept_removed": removed})
        for x in removed:
            counts["forms_removed"] += 1
            if x["reason"] == "jmdict-tag":
                for t in x["tags"]:
                    by_tag[t] = by_tag.get(t, 0) + 1

    # The table must be exactly the production cards the course issues — no more, no fewer.
    keys = [(r["lesson"], r["item"]) for r in rows]
    if len(set(keys)) != len(keys):
        raise SystemExit("the table addresses a card twice")
    missing = sorted(set(cards) - set(keys))
    extra = sorted(set(keys) - set(cards))
    if missing or extra:
        raise SystemExit(f"table vs export mismatch: {len(missing)} card(s) with no row "
                         f"{missing[:4]}, {len(extra)} row(s) with no card {extra[:4]}")
    prompts: dict[str, tuple[str, str]] = {}
    collisions = []
    for r in rows:
        p = r["prompt"]["pt-BR"]
        if p in prompts:
            collisions.append((p, prompts[p], (r["lesson"], r["item"])))
        prompts[p] = (r["lesson"], r["item"])
    rows.sort(key=lambda r: (r["lesson"], r["item"]))
    counts["rows"] = len(rows)

    doc = {
        "why": ("W27. Every production card now carries the answer key it was missing: what the "
                "learner is asked (pt-BR) and what a grader must accept (Japanese). Built by "
                "scripts/build_card_key_table.py from the W27 campaign table, the 13-row authoring "
                "residue and the archived JMdict, under the three rules in "
                f"{SAMPLE}."),
        "definition": ("One row per (lesson, item) production card. `prompt` is a locale object; "
                       "`accept` is the record's forms the grader takes, after the JMdict-tag strip; "
                       "`sense_index` is the sense the introducing lesson teaches; `accept_removed` "
                       "records every form the strip took out and why. `verified: \"sampled\"` is a "
                       "claim about the TABLE (one verifier at authoring time, then a 100-row Fable "
                       "sample), not about the row."),
        "generated_by": "scripts/build_card_key_table.py",
        "apply": "scripts/apply_card_production_keys.py (rebuild manifest step 119)",
        "counts": counts,
        "accept_removed_by_tag": dict(sorted(by_tag.items())),
        "accept_removed_not_a_form": removed_not_a_form,
        "dropped_because_repointed": dropped_repointed,
        "prompt_overrides_applied": applied_overrides,
        "prompt_collisions": collisions,
        "row_count": len(rows),
        "rows": rows,
    }
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(doc, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(f"{counts}")
    print(f"accept forms removed by tag: {doc['accept_removed_by_tag']}")
    print(f"accept forms removed as not-a-form: {len(removed_not_a_form)} "
          f"{[x['form'] for x in removed_not_a_form]}")
    print(f"prompt collisions: {len(collisions)}")
    print(f"wrote {len(rows)} row(s) -> {out.relative_to(ROOT).as_posix()}")
    return 1 if collisions else 0


if __name__ == "__main__":
    sys.exit(main())
