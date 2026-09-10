#!/usr/bin/env python3
"""Ingest the verified mined Tatoeba sentences into the bank. Step 3 of the thin-stage fix.

Pipeline recap, so this script's place is unambiguous:
  1. scripts/ingest/mine_tatoeba_stages.py   selected 360 real candidates (Layer A, verbatim)
  2. an authoring + two-reviewer workflow    produced pt-BR for them -> research/derived/mined_pt/
  3. THIS SCRIPT                             dissects and persists the accepted ones
  4. build_speaking_path -> build_speaking_checkpoints -> build_speaking_practice, then re-export

Nothing here authors Japanese or English. The `jp` is copied byte-for-byte from raw_tatoeba_sentence and
the `en` is Tatoeba's own pairing, both Layer A. Only the pt-BR is ours, and it is Layer B.

Persistence goes through persist_dissection.persist(), which already runs the Dissector, writes the
token/particle/graph rows, honours the content blocklist and is idempotent by slug. That matters: this
script must be safe to re-run after a partial failure, and it must not become a second, divergent way of
writing sentences into the corpus.

Guards before anything is written, because a bad ingest is expensive to unpick:
  * the jp must match the raw Tatoeba row for that id EXACTLY (catches an authoring agent having
    "tidied" Layer-A Japanese, which the reviewers were told to treat as critical);
  * the slug must not already exist (idempotency is persist()'s job, but a collision is worth reporting);
  * rows the authors rejected are skipped;
  * after each insert the three structural invariants are re-checked against what was actually stored --
    I1 concat(C-token surfaces) == jp, I2 kana == concat(token readings), I3 romaji == concat(token
    romaji) -- and ANY violation rolls the whole transaction back. The Phase-3 repair learned this the
    hard way: a partially-applied batch is worse than none.

W13b made three changes, all of them about which rows this script can carry:

  * --source PATH   the accepted-rows file. It used to be hardcoded at research/derived/mined_pt/
                    _accepted.json, which is the 360-candidate stage run; the mined N3 set lives at
                    research/derived/n3_mined/accepted.json and every later mining unit will land
                    somewhere else again. The default is unchanged, so existing invocations still work.
  * --tag TAG       replaces the `stage:<stage>` tag. `stage` is a field only the stage-mining rows
                    carry; every other source left it empty and the bank filled with `stage:` tags
                    pointing at nothing. The unit that produced the rows is what a later query actually
                    wants, so the tags become ["mined", "<tag>"] and the default keeps the old
                    behaviour when --tag is not given.
  * generated rows  a sentence with no Tatoeba id (`tatoeba_id: ""`, `generated: true`) used to collapse
                    onto the single Layer-B key "" and the single slug `sent:tatoeba-`, and would then
                    be dropped by the jp-vs-raw guard, which has nothing to compare against. They now
                    key and slug as `gen-<sha1(jp)[:12]>` / `sent:gen-<sha1(jp)[:12]>`, which is the
                    scheme prepare_generated.py already uses for the 2,213 generated sentences in the
                    bank, and the raw-Tatoeba guard is skipped for them (there is no Layer-A row to
                    compare to; their Japanese is ours, and is marked ai_generated).

Layer-B batches are read from --layerb (default research/derived/mined_layerb/) and indexed by
`key`, falling back to `str(tatoeba_id)` so the 324 already-authored batches, which predate the key,
still load.

W13 APPLY made four more changes, all of them about the ingest being safe to run 4,223 rows through:

  * --register-table PATH  W31 (A8/D7) derived `register` + `register_rule` for these 4,223 rows
                           BEFORE they were in the bank and filed them in the same exact-match table
                           as the 5,889 banked ones, as asserted deferrals: `validate_repairs_applied.py`
                           fails the moment one of their slugs appears in the export without the
                           table's value. So the ingest READS the table rather than deriving a value
                           of its own, and a row with no table entry is refused, not defaulted —
                           a defaulted `neutral` passes the speaking-path filter silently, which is
                           the failure that field exists to prevent.
  * batch atomicity        persist() now takes commit=False, so a Layer-B batch is ONE transaction:
                           if any sentence in it violates I1-I3 the whole batch rolls back and the
                           run stops. Before this, persist() committed per sentence and "rollback"
                           was a word with nothing behind it.
  * --provenance-source    `sentence.source` is the CAMPAIGN (w13:n3-exemplification), not a second
                           copy of `jp_source`. Where the Japanese came from is `jp_source`
                           (tatoeba / ai-generated) and stays Layer A.
  * grammar targets        a row whose `target`/`targets[]` names `gram:<key>` gets a
                           `sentence_grammar` row for that point — the verifier already proved the
                           form occurs in the sentence, and `validate_sentence_coverage.py` counts
                           the grammar floor off exactly this edge. Resolution is EXACT on
                           `grammar_point.key` only: persist_dissection.find_grammar()'s LIKE
                           fallback would silently tag a different point. The pass is idempotent
                           (INSERT OR IGNORE) and also runs over rows that were already banked, so a
                           re-run repairs a partial one instead of skipping it.

Usage: ingest_mined_stages.py [--apply] [--source PATH ...] [--layerb DIR] [--tag TAG] [--db PATH]
       [--register-table PATH] [--provenance-source NAME] [--batches 1,2,3]
       (default is a dry run)

DRY-RUN CAVEAT, found the hard way on the first run: persist_dissection.persist() used to COMMIT
internally, so wrapping it in BEGIN/rollback here did not undo anything and the first "dry run" of this
script wrote all 324 rows. Two things now stand between that and the corpus. Without --apply this is a
PRE-FLIGHT: every record is validated and reported and persist() is never called. With --apply, persist()
is called with commit=False, so a Layer-B batch is one transaction and a batch whose invariants fail is
rolled back whole and the run STOPS with the batches before it committed and the batches after it
untouched -- re-running resumes, because an already-banked slug is skipped.
"""
from __future__ import annotations
import argparse, hashlib, json, sqlite3, sys
from collections import Counter
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
# W01: honour --db / $YOMINEKO_DB so a rebuild can target a scratch DB (scripts/dbtarget.py).
import sys as _sys, pathlib as _pl  # noqa: E402
_sys.path.append(str(next(p for p in _pl.Path(__file__).resolve().parents if p.name == "scripts")))
from dbtarget import db_target  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
DB = db_target(ROOT / "db" / "corpus.sqlite")
SRC = ROOT / "research" / "derived" / "mined_pt" / "_accepted.json"
LAYERB = ROOT / "research" / "derived" / "mined_layerb"
REGISTER_TABLE = ROOT / "research" / "derived" / "repairs" / "sentence_register.json"


def sentence_key(row: dict) -> str:
    """The stable Layer-B key for a mined row: the Tatoeba id, or a content hash when it has none.

    Kept identical to scripts/derive_layerb.py::sentence_key — the derivation and the ingest have to
    agree on identity or the Layer-B silently lands on the wrong sentence (or, for the generated rows,
    on all of them at once).
    """
    tid = row.get("tatoeba_id")
    if not row.get("generated") and tid not in (None, ""):
        return str(tid)
    return "gen-" + hashlib.sha1(row["jp"].encode("utf-8")).hexdigest()[:12]


def sentence_slug(key: str) -> str:
    return f"sent:{key}" if key.startswith("gen-") else f"sent:tatoeba-{key}"


def invariants(con: sqlite3.Connection, sid: int) -> list[str]:
    """Re-read what was stored and check it against itself. Phrasing-proof: these are structural."""
    row = con.execute("SELECT jp,kana,romaji FROM sentence WHERE id=?", (sid,)).fetchone()
    if not row:
        return ["sentence row missing after insert"]
    jp, kana, romaji = row
    toks = con.execute("SELECT surface,reading,romaji FROM token WHERE sentence_id=? AND "
                       "split_mode='C' ORDER BY position", (sid,)).fetchall()
    bad = []
    if "".join(t[0] or "" for t in toks) != jp:
        bad.append("I1 concat(C surfaces) != jp")
    if "".join(t[1] or "" for t in toks) != (kana or ""):
        bad.append("I2 kana != concat(readings)")
    if "".join(t[2] or "" for t in toks) != (romaji or ""):
        bad.append("I3 romaji != concat(token romaji)")
    return bad


def load_register_table(path: Path) -> dict[str, tuple]:
    """{slug: (register, rule)} from research/derived/repairs/sentence_register.json.

    The table addresses a row two ways and both are indexed here, because the table is regenerated
    the day the ingest lands: BEFORE the ingest a W13 row's key is `tatoeba-<id>` / `gen-<hash>`
    (set "w13", and the slug it will have is `sent:` + the key); AFTER it, the derivation re-emits
    the same sentence as a plain bank row keyed by its slug. Indexing by slug makes the ingest read
    the same value from either generation of the table.
    """
    doc = json.loads(path.read_text(encoding="utf-8"))
    out: dict[str, tuple] = {}
    for r in doc["rows"]:
        key = r["key"]
        out[key if key.startswith("sent:") else "sent:" + key] = (r["register"], r["rule"])
    return out


def grammar_ids(con: sqlite3.Connection) -> dict[str, int]:
    """{key: grammar_point id}, EXACT. No LIKE fallback: `n3-koto` must never tag `n3-koto-da`."""
    return {k: i for i, k in con.execute("SELECT id, key FROM grammar_point")}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true", help="write; default is dry-run")
    ap.add_argument("--source", type=Path, action="append",
                    help="accepted-rows json; repeatable (real + generated live in two files)")
    ap.add_argument("--layerb", type=Path, default=LAYERB, help="dir of Layer-B batch-*.json")
    ap.add_argument("--tag", default=None,
                    help="unit tag written alongside 'mined'; default keeps the old stage:<stage>")
    ap.add_argument("--db", type=Path, default=None, help="target DB (default: db_target)")
    ap.add_argument("--register-table", type=Path, default=REGISTER_TABLE,
                    help="W31 exact-match register table; every ingested key must appear in it")
    ap.add_argument("--provenance-source", default=None,
                    help="sentence.source = the campaign (jp_source stays the Layer-A origin)")
    ap.add_argument("--batches", default=None,
                    help="comma-separated Layer-B batch numbers to ingest (default: all)")
    args = ap.parse_args()
    sources, db = args.source or [SRC], args.db or DB
    rows = []
    for src in sources:
        if not src.exists():
            print(f"missing {src} - run the authoring workflow first")
            return 1
        rows += [r for r in json.loads(src.read_text(encoding="utf-8"))["rows"]
                 if not r.get("reject")]
    print(f"{len(rows)} accepted rows to ingest from {len(sources)} source file(s)")

    from dissect import Dissector
    from persist_dissection import persist

    # Layer-B dissection content, authored and reviewed separately. Every bank sentence is
    # dissection_tier "full", which validate.py reads as a promise of a gloss on every content token,
    # an explanation on every particle, and a structure paragraph. Ingesting without these is what
    # produced 2,756 validator errors on the first trial run.
    #
    # The batch a key came from is remembered, because the batch is the UNIT OF ATOMICITY below.
    layerb: dict[str, dict] = {}
    batch_of: dict[str, str] = {}
    for f in sorted(args.layerb.glob("batch-*.json")):
        for s2 in json.loads(f.read_text(encoding="utf-8")).get("sentences", []):
            # `key` is W13b's; the 324 batches authored before it carry only tatoeba_id.
            k = str(s2.get("key") or s2["tatoeba_id"])
            layerb[k] = s2
            batch_of[k] = f.name
    print(f"{len(layerb)} sentences carry authored Layer-B dissection content in "
          f"{len(set(batch_of.values()))} batch file(s)")

    want_batches = None
    if args.batches:
        nums = {int(x) for x in args.batches.replace(" ", "").split(",") if x}
        want_batches = {f"batch-{n:02d}.json" for n in nums}
        print(f"restricted to {sorted(want_batches)}")

    registers = load_register_table(args.register_table)
    print(f"{len(registers)} rows in the register table {args.register_table.name}")

    con = sqlite3.connect(db)
    raw = {i: t for i, t in con.execute("SELECT id,text FROM raw_tatoeba_sentence")}
    have = {s for s, in con.execute("SELECT slug FROM sentence")}
    gids = grammar_ids(con)
    diss = Dissector(db)

    # ---- pre-flight over every row, before a single write ---------------------------------------
    # Grouped by Layer-B batch, so the run is resumable and one bad batch stops the rest.
    plan: dict[str, list[dict]] = {}
    stats, problems = Counter(), []
    for r in rows:
        tid, jp = r["tatoeba_id"], r["jp"]
        key = sentence_key(r)
        slug = sentence_slug(key)
        generated = key.startswith("gen-")
        if not generated and raw.get(tid) != jp:
            # The Japanese is Layer A. If it does not match the source row byte-for-byte, someone
            # edited it, and we drop rather than ingest a silently-altered original. A generated row
            # has no Layer-A original to compare against, so the guard does not apply to it - what
            # protects those is `ai_generated` + `needs_review`, not this check.
            problems.append((slug, "jp does not match the raw Tatoeba row"))
            stats["jp-altered"] += 1
            continue
        batch = batch_of.get(key)
        if batch is None:
            problems.append((slug, "no Layer-B batch carries this key - a full-tier sentence "
                                   "without glosses/explanations/paragraph fails validate.py"))
            stats["no-layerb"] += 1
            continue
        if want_batches is not None and batch not in want_batches:
            stats["out-of-scope"] += 1
            continue
        if slug not in registers:
            problems.append((slug, "no row in the register table - refusing to default a register"))
            stats["no-register"] += 1
            continue
        keys = sorted({t.split(":", 1)[1] for t in (r.get("targets")
                                                    or ([r["target"]] if r.get("target") else []))
                       if t.startswith("gram:")})
        unknown = [k for k in keys if k not in gids]
        if unknown:
            problems.append((slug, f"grammar target(s) name no grammar_point: {unknown}"))
            stats["grammar-unresolved"] += 1
            continue
        r["_key"], r["_slug"], r["_batch"] = key, slug, batch
        r["_generated"], r["_grammar"] = generated, keys
        plan.setdefault(batch, []).append(r)

    if (stats["jp-altered"] or stats["no-layerb"] or stats["no-register"]
            or stats["grammar-unresolved"]):
        print("PRE-FLIGHT REFUSED - nothing was written:")
        for s, w in problems[:25]:
            print(f"   {s}: {w}")
        print(f"   totals {dict(stats)}")
        con.close()
        return 1

    print(f"pre-flight clean: {sum(len(v) for v in plan.values())} rows over {len(plan)} batches")
    if not args.apply:
        for b in sorted(plan):
            n_new = sum(1 for r in plan[b] if r["_slug"] not in have)
            stats["would-ingest"] += n_new
            stats["already-banked"] += len(plan[b]) - n_new
        print(f"ingest (dry-run, nothing written): {dict(stats)}")
        con.close()
        return 0

    # ---- apply, one batch at a time, each batch ONE transaction ---------------------------------
    per_batch: list[tuple[str, int]] = []
    for batch in sorted(plan):
        con.execute("BEGIN")
        batch_ids, failed = [], []
        for r in plan[batch]:
            slug, key = r["_slug"], r["_key"]
            if slug in have:
                stats["already-banked"] += 1
                continue
            lb = layerb.get(key, {})
            # The English anchor is Layer A and belongs to the jp id, so read it from the source of
            # truth rather than trusting it to survive the authoring round-trip. The pt-BR authoring
            # schema ({tatoeba_id, jp, pt, pt_literal, register, reject, reject_reason}) has no `en`
            # key, so `r.get("en")` silently returned None for all 324 rows of the first run and
            # every one landed with no anchor -- see research/reports/en_anchor_backfill.md.
            anchor = r.get("en") or (None if r["_generated"] else (con.execute(
                "SELECT text FROM raw_tatoeba_translation WHERE jp_id=? AND lang='eng' "
                "ORDER BY trans_id LIMIT 1", (r["tatoeba_id"],)).fetchone() or (None,))[0])
            rec = {
                "slug": slug, "jp": r["jp"], "en": anchor,
                "pt": r.get("pt"), "pt_literal": r.get("pt_literal"),
                "structure_explanation_pt": lb.get("structure_explanation_pt"),
                # persist() keys these by token/particle POSITION, so they must be dicts, not lists.
                "tokens": {t["position"]: t for t in lb.get("tokens", [])},
                "particles": {q["position"]: q for q in lb.get("particles", [])},
                # "ai-generated" is prepare_generated.py's value and covers 2,207 of the 2,213 gen
                # rows already banked; matching it keeps one convention rather than adding a second.
                "jp_source": "ai-generated" if r["_generated"] else "tatoeba",
                "source": args.provenance_source,
                "ai_generated": 1 if r["_generated"] else 0,
                "tags": ["mined", args.tag or f"stage:{r.get('stage', '')}"],
                "translation_confidence": 0.8,
                "grammar_keys": r["_grammar"],
            }
            try:
                sid = persist(con, diss, rec, commit=False)
            except Exception as e:                  # noqa: BLE001 - one bad row must not kill the run
                failed.append((slug, f"persist failed: {e}"))
                continue
            if sid == -1:
                stats["content-blocklisted"] += 1
                continue
            bad = invariants(con, sid)
            if bad:
                failed.append((slug, "; ".join(bad)))
                continue
            reg, rule = registers[slug]
            # W31's value, placed. Nothing here decides a register.
            con.execute("UPDATE sentence SET register=?, register_rule=? WHERE id=?",
                        (reg, rule, sid))
            batch_ids.append(sid)
        if failed:
            con.rollback()
            print(f"ROLLED BACK {batch} ({len(batch_ids)} rows discarded) - refusing a partial "
                  f"ingest:")
            for s, w in failed[:20]:
                print(f"   {s}: {w}")
            print(f"   totals so far {dict(stats)}; batches done {per_batch}")
            con.close()
            return 1
        con.commit()
        have |= {r["_slug"] for r in plan[batch]}
        stats["ingested"] += len(batch_ids)
        per_batch.append((batch, len(batch_ids)))
        print(f"   {batch}: +{len(batch_ids)}")

    # ---- idempotent grammar-tag + register pass, over EVERY planned row --------------------------
    # persist() writes the grammar edges for the rows it created; this repeats the claim for rows an
    # earlier partial run had already banked, so a re-run repairs instead of skipping.
    sid_of = {s: i for s, i in con.execute("SELECT slug,id FROM sentence")}
    tagged = 0
    for batch in sorted(plan):
        for r in plan[batch]:
            sid = sid_of.get(r["_slug"])
            if sid is None:
                continue
            for k in r["_grammar"]:
                cur = con.execute("INSERT OR IGNORE INTO sentence_grammar "
                                  "(sentence_id,grammar_id,usage_note_pt) VALUES (?,?,NULL)",
                                  (sid, gids[k]))
                tagged += cur.rowcount or 0
            reg, rule = registers[r["_slug"]]
            con.execute("UPDATE sentence SET register=?, register_rule=? WHERE id=?",
                        (reg, rule, sid))
    con.commit()
    stats["grammar-tags-written"] = tagged

    print(f"ingest (APPLIED): {dict(stats)}")
    print(f"per batch: {per_batch}")
    for s, w in problems[:10]:
        print(f"   note {s}: {w}")
    print("next: export_corpus.py, then validate_all.py")
    con.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
