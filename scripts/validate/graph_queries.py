#!/usr/bin/env python3
"""Acceptance #10 — run the four §1.7 cross-cutting queries VERBATIM against the EXPORTED JSON.

WHY THIS FILE WAS REWRITTEN (findings G02 + G03, 2026-08-26 review)
------------------------------------------------------------------
The previous version of this script was the project's committed proof that the corpus is one
queryable graph (INDEX.md cites its report; the commit that added it claimed "all 4 PASS"), and it
could not fail on data. Its verdict was hardcoded:

    out.append(f"**{len(rows)} rows.** " + ("PASS ✓" if True else ""))
    print(f"[{'PASS' if True else 'FAIL'}] {title}: {len(rows)} rows")

Both ternaries are dead, so the only path to `[FAIL]` was a sqlite3.Error — i.e. the gate proved the
SQL parsed, never that it returned anything. Run against an all-empty replica of the graph tables it
printed three `[PASS] … 0 rows` lines and exited 0, and validate_all.py's grep-fail rule marked it
green (G02). It also ran against db/corpus.sqlite, which is git-ignored, regenerable, and which
STATE.md records as having regressed relative to the export.

Worse, two of the four queries were weaker than the spec sentences they cited (G03):
  * Q1 dropped the second family join. §1.7 asks for a godan verb *from the daily-routine family*;
    the committed query joined only grp:godan and reported 43 rows. With both joins the answer is 0,
    because the semantic_field families contain no verbs at all.
  * Q3 filtered `k.level IS NOT NULL` instead of the N5–N4 the heading advertised, so its own
    committed output listed 議 (n3) and 設 (n2) under "across N5–N4".

So this rewrite does three things. It reads only the exported JSON (never db/corpus.sqlite). It
states each query exactly as §1.7 words it, including every clause, and treats a zero-row result as
a FAILURE. And where the corpus genuinely cannot answer a query today, the reason is written down in
WAIVERS with its finding reference instead of being hidden inside a dead ternary — a waived query is
reported but does not gate, and a waived query that STARTS returning rows fails the build so the
waiver gets deleted rather than quietly outliving the defect.

Reads:  corpus/sentences/bank.json, corpus/families/families.json, corpus/kanji/*.json,
        corpus/vocab/*.json, corpus/grammar/*.json
Writes: reports/graph_query_tests.md
Usage:  graph_queries.py [--root PATH]
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
ROOT = Path(__file__).resolve().parents[2]
MAX_FAILS = 15
SAMPLE_ROWS = 8


class QueryError(RuntimeError):
    """The graph cannot express the query at all — a missing family, an unresolvable reference, an
    absent field. Distinct from 'the query ran and matched nothing', though both fail the gate."""


# ---------------------------------------------------------------------------------------------
# Waivers. A query listed here is allowed to fail; a query listed here that PASSES is a failure,
# because the defect the waiver documents has been fixed and the waiver must go. Every entry names
# the finding or the STATE.md line that owns the fix — no waiver without an owner.
# ---------------------------------------------------------------------------------------------
WAIVERS: dict[str, str] = {
    "Q1": "0 rows is the CORRECT answer today, and it is the defect: the 28 semantic_field families "
          "hold no verbs, so (grp:godan ∩ daily-routine) is empty by construction — "
          "build_families_full.py fills a semantic field only with vocab left over after the "
          "conjugation_class assignment, and every verb is already in a conjugation class. "
          "Finding G03/G04; STATE.md line 1927 'P4b — full families' owns the rebuild of the family "
          "layer over n5–n3. Delete this waiver once a semantic field can contain a verb.",
    "Q4": "The relation TYPE is not exported. grammar.related is a bare list of keys "
          "(wa-topic-marker -> ['ga']) with no 'contrast'/'synonym'/'confusable' label, and "
          "db/corpus.sqlite's grammar_related.relation is not carried into corpus/grammar/*.json, so "
          "the §1.7 clause 'that contrasts with は' cannot be evaluated — every candidate is filtered "
          "out for having no relation at all. Finding G04 (family/relation edges are write-only). "
          "Delete this waiver once export_corpus.py emits the relation.",
}


# ---------------------------------------------------------------------------------------------
# Loading — exported JSON only, read once, indexed into dicts.
# ---------------------------------------------------------------------------------------------
def _load_list(path: Path) -> list:
    if not path.exists():
        raise QueryError(f"missing export: {path}")
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, list):
        # A registry directory is addressed by a glob (corpus/kanji/*.json), so a sidecar dropped
        # beside the records — an exemption list, a report, an audit trail — silently joins the
        # entity for every consumer of that glob, this validator and infer_shapes.py included.
        # Sidecars belong outside the glob, not inside it, so this is a hard error rather than a skip.
        raise QueryError(f"{path.parent.name}/{path.name} is a {type(data).__name__}, not a list of "
                         f"records, but it sits inside the {path.parent.name} registry glob — move "
                         f"the sidecar out of corpus/{path.parent.name}/*.json")
    return data


def load_corpus(root: Path) -> dict:
    sentences = _load_list(root / "corpus" / "sentences" / "bank.json")
    families = _load_list(root / "corpus" / "families" / "families.json")
    kanji: list = []
    for p in sorted((root / "corpus" / "kanji").glob("*.json")):
        kanji += _load_list(p)
    vocab: list = []
    for p in sorted((root / "corpus" / "vocab").glob("*.json")):
        vocab += _load_list(p)
    grammar: list = []
    for p in sorted((root / "corpus" / "grammar").glob("*.json")):
        grammar += _load_list(p)

    # sentences per vocab, in both address spaces the export uses (integer row id and slug)
    sent_by_vocab_id: dict = defaultdict(list)
    sent_by_vocab_slug: dict = defaultdict(list)
    sent_by_grammar_key: dict = defaultdict(list)
    for s in sentences:
        seen_id, seen_slug = set(), set()
        for t in s.get("tokens") or []:
            vid, vsl = t.get("vocab_id"), t.get("vocab")
            if vid is not None and vid not in seen_id:
                seen_id.add(vid)
                sent_by_vocab_id[vid].append(s)
            if vsl and vsl not in seen_slug:
                seen_slug.add(vsl)
                sent_by_vocab_slug[vsl].append(s)
        for gk in s.get("grammar") or []:
            sent_by_grammar_key[gk].append(s)

    return {
        "sentences": sentences,
        "families": families,
        "family_by_slug": {f["slug"]: f for f in families if f.get("slug")},
        "kanji": kanji,
        "vocab": vocab,
        "vocab_by_id": {v["id"]: v for v in vocab if v.get("id") is not None},
        "vocab_by_slug": {v["slug"]: v for v in vocab if v.get("slug")},
        "grammar": grammar,
        "grammar_by_key": {g["key"]: g for g in grammar if g.get("key")},
        "sent_by_vocab_id": sent_by_vocab_id,
        "sent_by_vocab_slug": sent_by_vocab_slug,
        "sent_by_grammar_key": sent_by_grammar_key,
    }


def family_by_slug(db: dict, slug: str) -> dict:
    """Address a family by its SLUG, never by the integer `id` — the row number is not stable across
    a rebuild, and the previous script's `f.id = fm.family_id` join was only correct by accident."""
    fam = db["family_by_slug"].get(slug)
    if fam is None:
        raise QueryError(f"no family with slug {slug!r} in corpus/families/families.json")
    return fam


def semantic_field_matching(db: dict, needles: tuple[str, ...]) -> dict:
    """Resolve a family named in §1.7 by MEANING (the spec says 'the daily-routine family', it does
    not give a slug). Ambiguity is an error, not a first-match."""
    hits = []
    for f in db["families"]:
        if f.get("type") != "semantic_field":
            continue
        hay = (f.get("slug", "") + " " + json.dumps(f.get("label") or {}, ensure_ascii=False)).lower()
        if any(n in hay for n in needles):
            hits.append(f)
    if len(hits) != 1:
        raise QueryError(f"expected exactly 1 semantic_field family matching {needles}, "
                         f"found {len(hits)}: {[h.get('slug') for h in hits]}")
    return hits[0]


def vocab_slugs_of(fam: dict) -> set[str]:
    """The vocab members of a family, in slug space. A vocab member with no slug is a broken edge and
    must be reported, not silently dropped — that is how the headword-addressing defect hid."""
    out = set()
    for m in fam.get("members") or []:
        if m.get("member_type") != "vocab":
            continue
        slug = m.get("slug")
        if not slug:
            raise QueryError(f"family {fam.get('slug')}: vocab member {m.get('ref')!r} carries no slug")
        out.add(slug)
    return out


# ---------------------------------------------------------------------------------------------
# The four §1.7 queries, each stated as the spec words it.
# ---------------------------------------------------------------------------------------------
Q1_SPEC = "All N5 sentences containing a godan verb from the *daily-routine* family **and** the を particle."


def q1(db: dict) -> list[str]:
    """Every clause of the spec sentence is applied: level == n5, the を particle, AND a vocab that is
    a member of grp:godan AND of the daily-routine semantic field. Dropping either family join is the
    bug this query exists to catch (G03) — the committed variant kept only grp:godan and answered 43."""
    godan = vocab_slugs_of(family_by_slug(db, "grp:godan"))
    routine = vocab_slugs_of(semantic_field_matching(db, ("rotina", "routine", "daily")))
    target = godan & routine
    rows = []
    for s in db["sentences"]:
        if s.get("level") != "n5":
            continue
        if not any(p.get("particle") == "を" for p in (s.get("particles") or [])):
            continue
        if {t.get("vocab") for t in (s.get("tokens") or [])} & target:
            rows.append(f"{s['slug']} — {s['jp']}")
    return rows


Q2_SPEC = "Every vocab item using the kun-reading た.べる of 食, with its dissected sentences."


def q2(db: dict) -> list[str]:
    """Kanji -> reading -> example vocab -> dissected sentences, all four hops from stored links."""
    kanji = next((k for k in db["kanji"] if k.get("character") == "食"), None)
    if kanji is None:
        raise QueryError("kanji 食 is not in corpus/kanji/*.json")
    readings = [r for r in (kanji.get("readings") or [])
                if r.get("reading") == "た" and r.get("okurigana") == "べる"]
    if not readings:
        raise QueryError("食 has no kun-reading た.べる (reading='た', okurigana='べる')")
    rows = []
    for r in readings:
        for vid in r.get("example_vocab_ids") or []:
            v = db["vocab_by_id"].get(vid)
            if v is None:
                raise QueryError(f"食 た.べる example_vocab_ids -> {vid} resolves to no vocab record")
            sents = db["sent_by_vocab_id"].get(vid) or []
            rows.append(f"{v['headword']} ({v['slug']}) — {len(sents)} dissected sentences")
    return rows


Q3_SPEC = "All members of the 言-component kanji family across N5–N4, ordered by frequency."


def q3(db: dict) -> list[str]:
    """The N5–N4 filter is part of the spec sentence and is applied here; the committed query filtered
    `level IS NOT NULL` instead and printed n3/n2 kanji under an 'across N5–N4' heading (G03).
    freq_rank may be null, and nulls sort last."""
    members = [k for k in db["kanji"]
               if "言" in (k.get("components") or []) and k.get("level") in ("n5", "n4")]
    members.sort(key=lambda k: (k.get("freq_rank") is None, k.get("freq_rank") or 0, k["character"]))
    return [f"{k['character']} ({k['level']}, freq {k.get('freq_rank')})" for k in members]


Q4_SPEC = "Every grammar point that contrasts with は, with example sentences."


def q4(db: dict) -> list[str]:
    """`related` is normalised to (key, relation) so the spec's 'contrasts with' clause is a real
    filter. Today every entry is a bare string with no relation, so nothing survives the filter —
    which is exactly what the WAIVERS entry for Q4 records."""
    anchor = db["grammar_by_key"].get("wa-topic-marker")
    if anchor is None:
        raise QueryError("grammar key 'wa-topic-marker' is not in corpus/grammar/*.json")
    rows = []
    for entry in anchor.get("related") or []:
        if isinstance(entry, dict):
            key = entry.get("key") or entry.get("related") or entry.get("ref")
            relation = entry.get("relation")
        else:
            key, relation = entry, None
        if relation != "contrast":
            continue
        g = db["grammar_by_key"].get(key)
        if g is None:
            raise QueryError(f"wa-topic-marker related -> {key!r} resolves to no grammar point")
        label = (g.get("label") or {}).get("pt-BR")
        rows.append(f"{key} — {label} ({len(db['sent_by_grammar_key'].get(key) or [])} sentences)")
    return rows


QUERIES = [
    ("Q1", Q1_SPEC, q1),
    ("Q2", Q2_SPEC, q2),
    ("Q3", Q3_SPEC, q3),
    ("Q4", Q4_SPEC, q4),
]


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--root", default=str(ROOT), help="repo root to validate (default: this repo)")
    args = ap.parse_args()
    root = Path(args.root).resolve()

    try:
        db = load_corpus(root)
    except QueryError as e:
        print(f"  [FAIL] cannot load the exported corpus: {e}")
        print(f"\ngraph_queries: 0/{len(QUERIES)} §1.7 queries run — FAIL 1")
        return 1

    out = [
        "# §1.7 cross-cutting graph query tests",
        "",
        "_Acceptance #10. The four spec queries are run VERBATIM — every clause of the spec sentence is "
        "applied — against the exported JSON under `corpus/` (never `db/corpus.sqlite`). A query that "
        "returns zero rows FAILS. A query listed in the WAIVERS table of "
        "`scripts/validate/graph_queries.py` is allowed to fail with its reason recorded; if it starts "
        "returning rows, the gate fails so the waiver is removed._",
        "",
    ]
    fails: list[str] = []
    passed = waived = 0

    for qid, spec, fn in QUERIES:
        try:
            rows, err = fn(db), None
        except QueryError as e:
            rows, err = [], str(e)
        # A waiver covers exactly one thing: "the query ran and matched nothing, for the recorded
        # reason". It never covers a QueryError — a renamed family slug or an unresolvable member
        # edge means the graph cannot express the query at all, which is the failure §1.7 is about,
        # and a broad waiver would swallow it silently (proved by plant: renaming grp:godan used to
        # come back green under the Q1 waiver).
        waiver = None if err else WAIVERS.get(qid)
        ok = bool(rows) and err is None

        out.append(f"## {qid} — {spec}")
        out.append("")
        if err:
            out.append(f"**ERROR:** {err}")
        else:
            out.append(f"**{len(rows)} rows.**")
            for r in rows[:SAMPLE_ROWS]:
                out.append(f"- {r}")
            if len(rows) > SAMPLE_ROWS:
                out.append(f"- … {len(rows) - SAMPLE_ROWS} more")

        if ok and waiver:
            fails.append(f"{qid}: STALE WAIVER — the query now returns {len(rows)} rows. "
                         f"Delete its WAIVERS entry in scripts/validate/graph_queries.py.")
            out.append("")
            out.append("**STALE WAIVER** — this query passes now; the waiver must be deleted.")
        elif ok:
            passed += 1
            print(f"  [PASS] {qid}: {len(rows)} rows")
            out.append("")
            out.append("PASS")
        elif waiver:
            waived += 1
            print(f"  [WAIVE] {qid}: {err or '0 rows'} — waived, see WAIVERS in graph_queries.py")
            out.append("")
            out.append(f"**WAIVED** — {waiver}")
        else:
            fails.append(f"{qid}: {err or 'returned 0 rows'}")
            out.append("")
            out.append("**FAIL** — a §1.7 query that answers nothing means the model is incomplete.")
        out.append("")

    report = root / "reports" / "graph_query_tests.md"
    report.parent.mkdir(parents=True, exist_ok=True)
    report.write_text("\n".join(out) + "\n", encoding="utf-8")

    for f in fails[:MAX_FAILS]:
        print("  [FAIL]", f)
    if len(fails) > MAX_FAILS:
        print(f"  … {len(fails) - MAX_FAILS} more")
    print(f"\ngraph_queries: {len(QUERIES)} §1.7 queries · {passed} pass · {waived} waived · "
          f"{'FAIL ' + str(len(fails)) if fails else 'ALL OK'} "
          f"-> reports/graph_query_tests.md")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
