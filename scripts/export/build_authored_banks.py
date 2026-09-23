#!/usr/bin/env python3
"""Assemble the AUTHORED exam banks (paraphrase 言い換え + usage 用法) from the workflow output
(research/derived/reauthor/exam_authored/authored_{lvl}.json), excluding verifier-flagged vids, with
deterministic HARD guards: Japanese-only answer fields, correct != distractors (paraphrase correct must not
equal the headword/kana), usage keeps the REAL example as the correct option + 3 authored wrong-usage
sentences (all distinct, none equal to the real one), no em dash. Items are Layer C, needs_review (teacher
sign-off) and carry provenance.

W17. Two provenance fields were only ever written by `migrate_exam_banks_p7.py`, a one-shot migration
that is now disabled — so regenerating these banks STRIPPED them, which is the same defect the A2
review measured on the deterministic banks (`w15_apply_report.md` §7 named it for these two):
  * `vocab` — the published `vocab:<jmdict_id>` slug beside the storage row number. `contracts/README.md`
    forbids a row number as an address, and `validate_exam_banks` check D fails a `vocab_id` with no
    slug next to it.
  * `ai_generated` — copied from the STEM SENTENCE's provenance, because on an exam item the flag means
    "the Japanese the learner reads was model-generated rather than selected", which is what the exam
    picker's real-first rule keys on. 42 of 366 authored items are true. Absent, the picker read every
    one of them as real.
`--out DIR` writes elsewhere than corpus/exam_banks so a prototype run touches nothing under corpus/.

W18. The W18b replacements (`pp_us_w18b.json`: 42 items re-selected inside the level-clean sentence pool,
each through one independent verifier) replace the item of the same id or join the bank, with their pt-BR
`explanation`. Then the LEVEL RULE (validate_exam_level_gate's, via exam_rules.TaughtSets over the exported
course and corpus/sentences/bank.json): an item whose Japanese is not taught by the end of its level is
withheld from the bank and stays in the journal. W18b sized the replacements so every paper still fills at
3x. Run `export_course.py` first, as for build_exam_banks.py.
Usage: build_authored_banks.py [--flagged '{"n5":[vids...]}'] [--out DIR]"""
from __future__ import annotations
import argparse, json, re, sqlite3, sys
from pathlib import Path
sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
# W01: honour --db / $YOMINEKO_DB so a rebuild can target a scratch DB (scripts/dbtarget.py).
import sys as _sys, pathlib as _pl  # noqa: E402
_sys.path.append(str(next(p for p in _pl.Path(__file__).resolve().parents if p.name == "scripts")))
from dbtarget import db_target  # noqa: E402
_sys.path.append(str(_pl.Path(__file__).resolve().parent))
from exam_rules import TaughtSets  # noqa: E402
ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "research" / "derived" / "reauthor" / "exam_authored"
W18B = SRC / "pp_us_w18b.json"
OUT = ROOT / "corpus" / "exam_banks"
DB = db_target(ROOT / "db" / "corpus.sqlite")
JP_OK = re.compile(r"^[ぁ-んァ-ヶー一-鿿々〆0-9０-９、。！？!?（）()・\s]+$")


def main() -> int:
    ap = argparse.ArgumentParser()
    # W17. The verifier's rejects used to reach this script ONLY as a command-line argument, so a
    # regeneration that forgot the flag silently re-admitted every item a verifier had thrown out
    # (measured: 12 n5 + 8 n4 + 4 n3 paraphrase/usage items come back). The tracked table is the
    # default now, and `--flagged` overrides it; `--flagged {}` is still how you build without it.
    ap.add_argument("--flagged", default=None)
    ap.add_argument("--out", default=None,
                    help="write the banks here instead of corpus/exam_banks (prototype mode)")
    args = ap.parse_args()
    out_dir = Path(args.out) if args.out else OUT
    out_dir.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(DB)
    slug_of_vid = {vid: slug for vid, slug in con.execute("SELECT id, slug FROM vocab")}
    hw_of_vid = {vid: hw for vid, hw in con.execute("SELECT id, headword FROM vocab")}
    sent_ai = {slug: bool(ai) for slug, ai in
               con.execute("SELECT slug, COALESCE(ai_generated,0) FROM sentence")}
    con.close()
    raw = args.flagged
    if raw is None:
        fp = SRC / "_flagged.json"
        raw = fp.read_text(encoding="utf-8") if fp.is_file() else "{}"
        print(f"flagged table: {fp if fp.is_file() else '(none on disk)'}")
    flagged: dict = {}
    for key, v in json.loads(raw).items():
        lvl = key.split("_")[0]  # accepts level keys or batch keys (n5_b1)
        flagged.setdefault(lvl, set()).update(b["vid"] if isinstance(b, dict) else b for b in v)
    counts, skipped, withheld = {}, {}, {}
    taught = TaughtSets(ROOT)
    bank = {s["slug"]: s for s in json.loads(
        (ROOT / "corpus" / "sentences" / "bank.json").read_text(encoding="utf-8"))}

    def level_clean(it: dict, lvl: str) -> bool:
        """validate_exam_level_gate's rule for a sentence-backed item: every kanji printed, the
        item's own word, and the source sentence's token vocabulary and grammar tags are taught by
        the end of `lvl`."""
        s = bank.get(it.get("sentence") or "")
        printed = [it.get("stem"), it.get("target"), it.get("correct"),
                   *(it.get("distractors") or []), *(it.get("wrong") or [])]
        return (s is not None and taught.strings_kanji_ok(printed, lvl)
                and taught.vocab_ok(it["vocab"], lvl)
                and all(taught.vocab_ok(t["vocab"], lvl) for t in s.get("tokens") or [] if t.get("vocab"))
                and all(taught.grammar_ok(g, lvl) for g in s.get("grammar") or []))

    w18b: dict = {}
    table = json.loads(W18B.read_text(encoding="utf-8"))
    for row in table["rows"]:
        expl = (table["extras"].get(row["id"], {}).get("explanation") or "").strip()
        if "—" in expl:
            raise SystemExit(f"{row['id']}: em dash in the authored explanation")
        w18b.setdefault((row["id"][:2], row["level"]), []).append(
            {**row, **({"explanation": {"pt-BR": expl}} if expl else {})})
    for lvl in ("n5", "n4", "n3"):
        facts = {i["vid"]: i for i in json.loads((SRC / f"input_{lvl}.json").read_text(encoding="utf-8"))}
        authored = []
        for bf in sorted(SRC.glob(f"authored_{lvl}_b*.json")):
            d = json.loads(bf.read_text(encoding="utf-8"))
            authored += (d.get("items", []) if isinstance(d, dict) else d)
        if not authored:
            print(f"{lvl}: no authored batches (skip)")
            continue
        para, usage, skip = [], [], []
        for it in authored:
            vid = it.get("vid")
            f = facts.get(vid)
            if not f or vid in flagged.get(lvl, set()):
                skip.append((vid, "flagged/unknown")); continue
            p = it.get("paraphrase") or {}
            pc, pd = (p.get("correct") or "").strip(), [d.strip() for d in (p.get("distractors") or [])]
            uw = [s.strip() for s in (it.get("usage_wrong") or [])]
            probs = []
            if not pc or pc in (f["hw"], f["kana"]) or pc in pd or len(set(pd)) != 3:
                probs.append("paraphrase set invalid")
            if any(not JP_OK.match(x) for x in [pc] + pd if x):
                probs.append("non-JP in paraphrase")
            if len(set(uw)) != 3 or any(not JP_OK.match(s) for s in uw) or f["example"] in uw \
                    or any(f["hw"] not in s for s in uw):
                probs.append("usage set invalid")
            if any("—" in x for x in [pc] + pd + uw):
                probs.append("em dash")
            if probs:
                skip.append((vid, ";".join(probs))); continue
            vslug = slug_of_vid.get(vid)
            if vslug is None:
                skip.append((vid, "no vocab record for this id")); continue
            # W17. The item's `target` must BE the record's headword — that is what
            # validate_exam_banks checks K and L assert, and it is the guard the A9 re-point needed:
            # the authored facts for vid 745 name 運, but vocab:1001090's headword is うん after the
            # re-point, so `pp:n4:745` / `us:n4:745` are Japanese selected for a lexeme this row no
            # longer is. They were pulled by hand into removed_items.json; a rule keeps them out of
            # every future rebuild, which a ledger entry cannot.
            if hw_of_vid.get(vid) != f["hw"]:
                skip.append((vid, f"target {f['hw']!r} is not the headword of {vslug} "
                                  f"({hw_of_vid.get(vid)!r}) — record re-pointed since authoring"))
                continue
            ai = sent_ai.get(f["ex_slug"], False)
            para.append({"id": f"pp:{lvl}:{vid}", "level": lvl, "stem": f["example"], "target": f["hw"],
                         "correct": pc, "distractors": pd, "vocab": vslug, "vocab_id": vid,
                         "sentence": f["ex_slug"], "layer": "C", "needs_review": True,
                         "ai_generated": ai, "source": "authored+verified"})
            usage.append({"id": f"us:{lvl}:{vid}", "level": lvl, "target": f["hw"],
                          "correct": f["example"], "wrong": uw, "vocab": vslug, "vocab_id": vid,
                          "sentence": f["ex_slug"], "layer": "C", "needs_review": True,
                          "ai_generated": ai, "source": "authored+verified(real-correct)"})
        # W18. The W18b replacements (research/derived/reauthor/exam_authored/pp_us_w18b.json:
        # re-selected inside the level-clean sentence pool, one independent verifier per batch)
        # take the id they replace, or join the bank. Then the level rule: an item whose Japanese
        # is not inside the level's taught set is withheld. It stays in the journal; W18b's own
        # deficit table sized the replacements so every paper still fills at 3x from what is left.
        for fam, items in (("pp", para), ("us", usage)):
            pos = {it["id"]: i for i, it in enumerate(items)}
            for row in w18b.get((fam, lvl), []):
                if row["id"] in pos:
                    items[pos[row["id"]]] = row
                else:
                    items.append(row)
        for items in (para, usage):
            withheld[lvl] = withheld.get(lvl, 0) + sum(not level_clean(it, lvl) for it in items)
            items[:] = [it for it in items if level_clean(it, lvl)]
        (out_dir / f"{lvl}_paraphrase.json").write_text(json.dumps(para, ensure_ascii=False), encoding="utf-8")
        (out_dir / f"{lvl}_usage.json").write_text(json.dumps(usage, ensure_ascii=False), encoding="utf-8")
        counts[lvl] = (len(para), len(usage))
        skipped[lvl] = len(skip)
        if skip[:3]:
            print(f"  {lvl} sample skips:", skip[:3])
    print("authored banks (paraphrase, usage):", counts, "| skipped:", skipped,
          "| withheld by the level rule:", withheld)
    return 0


if __name__ == "__main__":
    sys.exit(main())
