#!/usr/bin/env python3
"""Q4 (W18b listening half): the verified listening re-authoring, written into the journal the builder reads.

WHAT
----
W18 left 175 listening items over the level line (173 on an untaught kanji) in the 13 authored
listening banks. The W18b campaign re-authored every one of them against the level-clean pool
(author batch `research/derived/repairs/listening_reauthor/listening_authored-work-NN.json`, one
independent verifier per batch, `research/derived/pending/listening_authored-<NN-1>.verdict.json`:
139 ok, 36 corrected, 0 rejected). This script folds author + verdict into ONE tracked table
(`research/derived/repairs/listening_reauthor.json`, `--assemble`) and applies it to the authoring
journal `research/derived/reauthor/exam_authored/authored_listen_<level>_<sub>.json`, which
`scripts/export/build_listening_bank.py` turns into `corpus/exam_banks/<level>_listening_<sub>.json`.
The verifier's `corrected` value wins over the author's wherever the verdict is not ok.

REPLY IDS FOLLOW THE SENTENCE
-----------------------------
A reply item's id is `lr:<level>:<sentence slug>` (the builder derives it). Six reply items were
re-selected onto a different real sentence, so they take the new sentence's id; the old id goes. The
prompt of a re-selected item must be the new sentence verbatim, so its `{slug, jp}` joins
`input_listen_<level>_reply.json` (the builder's verbatim check reads it). Two N4 reply items had to
be EDITED (the Tatoeba sentence used a form above the level): they cite no sentence any more, keep the
id they had (`adapted_from` records the sentence they were adapted from) and the builder skips the
verbatim check for them.

EXACT MATCH. Each row carries the journal item before (`old`) and after (`new`). A journal item at
`new` is done, at `old` is written, at neither is drift and the run refuses. Idempotent.
Usage: apply_listening_reauthor.py [--assemble] [--check]
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
ROOT = Path(__file__).resolve().parents[1]
JOURNAL = ROOT / "research" / "derived" / "reauthor" / "exam_authored"
PENDING = ROOT / "research" / "derived" / "pending"
REPAIRS = ROOT / "research" / "derived" / "repairs"
AUTHORED = REPAIRS / "listening_reauthor"
TABLE = REPAIRS / "listening_reauthor.json"
BANK = ROOT / "corpus" / "sentences" / "bank.json"


def load(p: Path):
    return json.loads(p.read_text(encoding="utf-8"))


def dump(p: Path, d, indent: int | None = 1) -> None:
    p.write_text(json.dumps(d, ensure_ascii=False, indent=indent) + "\n", encoding="utf-8")


def journal_item(sub: str, ref, final: dict, old_id: str) -> dict:
    key = final["key"]
    dis = [o for o in final["options"] if o != key]
    if sub != "reply":
        return {"n": ref, "script": final["script"], "question": final["question"],
                "correct": key, "distractors": dis}
    if "sentence" in final and final["sentence"] is None:       # edited: cites no sentence
        return {"slug": None, "id": old_id, "adapted_from": ref, "script": final["script"],
                "correct": key, "distractors": dis}
    return {"slug": final.get("sentence") or ref, "script": final["script"], "correct": key,
            "distractors": dis}


def assemble() -> int:
    jp = {s["slug"]: s["jp"] for s in load(BANK)}
    rows = []
    for nn in range(1, 10):
        work = load(AUTHORED / f"listening_authored-work-{nn:02d}.json")
        verdict = load(PENDING / f"listening_authored-{nn - 1}.verdict.json")
        inp = {i["id"]: i for i in load(PENDING / "listening_work" / f"work-{nn:02d}.json")["items"]}
        for iid, authored in work.items():
            if iid.startswith("_"):
                continue
            v = verdict[iid]
            if not v.get("ok") and not v.get("corrected"):
                raise SystemExit(f"{iid}: rejected with no correction; exclude it explicitly")
            final = authored if v.get("ok") else v["corrected"]
            it = inp[iid]
            lvl, sub = it["level"], it["family"]
            jfile = f"authored_listen_{lvl}_{sub}.json"
            ref = int(iid.rsplit(":", 1)[1]) if sub != "reply" else "sent:" + iid.split(":", 2)[2]
            items = load(JOURNAL / jfile)["items"]
            old = next(x for x in items if (x.get("n") if sub != "reply" else x.get("slug")) == ref)
            new = journal_item(sub, ref, final, iid)
            new_id = iid
            row = {"id": iid, "level": lvl, "sub": sub, "journal": jfile, "ref": ref,
                   "verdict": "ok" if v.get("ok") else "corrected",
                   "source": final.get("source"), "changed_tokens": final.get("changed_tokens") or []}
            if v.get("problem"):
                row["problem"] = v["problem"]
            if sub == "reply":
                if new["slug"] is None:
                    row["adapted_from"] = ref
                else:
                    new_id = f"lr:{lvl}:{new['slug'].split(':', 1)[1]}"
                    if new["script"][0]["text"] != jp.get(new["slug"]):
                        raise SystemExit(f"{iid}: prompt {new['script'][0]['text']!r} is not "
                                         f"{new['slug']} verbatim ({jp.get(new['slug'])!r})")
                    if new["slug"] != ref:
                        row["input_add"] = {"slug": new["slug"], "jp": jp[new["slug"]]}
            row.update({"new_id": new_id, "old": old, "new": new})
            rows.append(row)
    doc = {"unit": "Q4-listening-residues (APP_PLAN W18b, listening half)",
           "what": "The 175 listening items W18 left over the level line, re-authored inside the level-"
                   "clean pool; author + one independent verifier per batch; the verifier's corrected "
                   "value applied where the verdict is not ok.",
           "sources": {"authored": "research/derived/repairs/listening_reauthor/listening_authored-work-NN.json",
                       "verdicts": "research/derived/pending/listening_authored-<NN-1>.verdict.json",
                       "work_lists": "research/derived/pending/listening_work/work-NN.json"},
           "applied_by": "scripts/apply_listening_reauthor.py",
           "provenance": {"layer": "C", "ai_generated": True, "needs_review": True},
           "counts": {"rows": len(rows), "ok": sum(r["verdict"] == "ok" for r in rows),
                      "corrected": sum(r["verdict"] == "corrected" for r in rows),
                      "reply_reselected": sum("input_add" in r for r in rows),
                      "reply_edited": sum("adapted_from" in r for r in rows)},
           "row_count": len(rows), "rows": rows}
    dump(TABLE, doc)
    print(f"assembled {len(rows)} rows -> {TABLE.relative_to(ROOT)}: {doc['counts']}")
    return 0


def locate(items: list, r: dict) -> int | None:
    for i, x in enumerate(items):
        if r["sub"] != "reply":
            if x.get("n") == r["ref"]:
                return i
        elif x.get("slug") == r["ref"] or x == r["new"]:
            return i
    return None


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--assemble", action="store_true", help="fold author + verdict into the table")
    ap.add_argument("--check", action="store_true", help="report what would change; write nothing")
    args = ap.parse_args()
    if args.assemble:
        return assemble()
    doc = load(TABLE)
    if doc["row_count"] != len(doc["rows"]):
        raise SystemExit("row_count mismatch")
    journals: dict[str, dict] = {}
    inputs: dict[str, dict] = {}
    done = written = added = 0
    drift = []
    for r in doc["rows"]:
        j = journals.setdefault(r["journal"], load(JOURNAL / r["journal"]))
        i = locate(j["items"], r)
        cur = None if i is None else j["items"][i]
        if cur == r["new"]:
            done += 1
        elif cur == r["old"]:
            j["items"][i] = r["new"]
            written += 1
        else:
            drift.append(f"{r['id']}: journal item is neither the row's old nor its new")
        if "input_add" in r:
            f = f"input_listen_{r['level']}_reply.json"
            inp = inputs.setdefault(f, load(JOURNAL / f))
            if r["input_add"]["slug"] not in {x["slug"] for x in inp["items"]}:
                inp["items"].append(r["input_add"])
                inp["count"] = len(inp["items"])
                added += 1
    if drift:
        for d in drift[:20]:
            print(f"  DRIFT {d}")
        print("NOTHING WRITTEN")
        return 2
    if not args.check:
        # Same layout as the files the workflow wrote: journal compact, input lists indent=1.
        for f, d in journals.items():
            (JOURNAL / f).write_text(json.dumps(d, ensure_ascii=False), encoding="utf-8")
        for f, d in inputs.items():
            (JOURNAL / f).write_text(json.dumps(d, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"listening re-authoring: {len(doc['rows'])} rows, {written} written, {done} already applied, "
          f"{added} reply prompt(s) added to the input lists{' (check only)' if args.check else ''}")
    return 1 if (args.check and (written or added)) else 0


if __name__ == "__main__":
    sys.exit(main())
