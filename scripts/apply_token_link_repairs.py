#!/usr/bin/env python3
"""Q2 — apply the verified token-link repairs, edge-exact, and re-level the sentences they touch.

WHAT WAS WRONG
--------------
The dissector resolves a token to a vocabulary record by WRITTEN FORM (and the JLPT reconcile
resolved list entries by reading), so a kana token lands on whichever record owns that spelling:
every する on 刷る "imprimir", every なる on 生る "dar fruto", ように on 用, ほうが on 報. The
token-link audit re-read 38,764 linked tokens against the record's forms, readings and part of
speech and flagged 4,004; research/derived/repairs/token_link_repairs.json holds the verified
decision for each (scripts/assemble_token_link_repairs.py).

WHAT THIS WRITES (db/corpus.sqlite; the exporters republish corpus/ and course/)
  1. token.vocab_id per row, after the replay guard: the C token at (sentence, position) must read
     `surface` and carry `old_vocab` (or already carry the row's new value: idempotent).
  2. sentence_vocab, EDGE-EXACT. The new (sentence, vocab) pair is inserted with link_rule
     'token' (reading_verified computed as build_sentence_vocab.py computes it). The old pair is
     deleted only when nothing else in the index still produces it: no C token carries it (R1), no
     1..5-token run spells one of its forms while it sits in the n5/n4 registry (R2), no token
     lemma equals its headword while it is n3 (R3), and its row is not an `ortho` link.
     build_sentence_vocab.py is INSERT-only and never deletes, so it cannot do this half.
  3. sentence.level of the touched sentences whose COMPUTED level this repair moves: the table's
     `sentence_levels` rows (derived once as computed_level over the pre-relink edges vs the
     post-relink edges, both over the corrected registry), each written only over its `from` and
     re-proved against the edges. A touched sentence whose stored level was already stale for
     another reason (an N3 edge such as the で particle record) keeps it. Never
     recompute_all_levels(), which build_sentence_vocab.py documents as forbidden corpus-wide.
  4. reading.uses of the W15 boxes (`reading_uses`), in the index and in the W15 table's snapshot.

Run after scripts/apply_level_evidence.py --data research/derived/repairs/level_transfer_repairs.json
(the level half of the same repair: the re-level must see the corrected registry levels).

Idempotent: a second run writes 0 tokens, 0 edges, 0 levels. Refuses (exit 1, nothing committed)
when a row's token no longer matches. Out of scope in a --quick rebuild whose sentence table is empty.
Usage: apply_token_link_repairs.py [--check] [--table PATH]
"""
from __future__ import annotations

import argparse
import json
import sqlite3
import sys
from collections import defaultdict
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
import sys as _sys, pathlib as _pl  # noqa: E402
_SCRIPTS = next(p for p in _pl.Path(__file__).resolve().parents if p.name == "scripts")
_sys.path.append(str(_SCRIPTS))
_sys.path.append(str(_SCRIPTS / "ingest"))
from dbtarget import db_target  # noqa: E402
from persist_dissection import computed_level  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
DB = db_target(ROOT / "db" / "corpus.sqlite")
TABLE = ROOT / "research" / "derived" / "repairs" / "token_link_repairs.json"
LIVE_INDEX = Path(DB).resolve() == (ROOT / "db" / "corpus.sqlite").resolve()
MAXW = 5
R2_LEVELS = ("n5", "n4")
R3_LEVEL = "n3"
KATA_A, KATA_Z = 0x30A1, 0x30F6


def hira(s: str) -> str:
    return "".join(chr(ord(c) - 0x60) if KATA_A <= ord(c) <= KATA_Z else c for c in (s or ""))


def kana_only(s: str) -> bool:
    return bool(s) and all("ぁ" <= c <= "ゟ" or "ァ" <= c <= "ヿ" or c == "ー" for c in s)


def load_rows(path: Path) -> list[dict]:
    doc = json.loads(path.read_text(encoding="utf-8"))
    if doc.get("row_count") != len(doc["rows"]):
        raise SystemExit(f"{path.name}: row_count {doc.get('row_count')} != {len(doc['rows'])}")
    return doc["rows"]


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--check", action="store_true", help="report what would change; write nothing")
    ap.add_argument("--table", type=Path, default=TABLE)
    args = ap.parse_args()
    rows = load_rows(args.table)

    con = sqlite3.connect(DB)
    con.execute("PRAGMA busy_timeout=60000")
    if not con.execute("SELECT 1 FROM sentence LIMIT 1").fetchone():
        print(f"apply_token_link_repairs: {len(rows)} rows out of scope (empty sentence table)")
        return 0

    sid_of = dict(con.execute("SELECT slug, id FROM sentence"))
    vid_of = dict(con.execute("SELECT slug, id FROM vocab"))
    level_of: dict[int, str] = {}
    head_of: dict[int, str] = {}
    forms: dict[int, set[str]] = defaultdict(set)
    readings: dict[int, set[str]] = defaultdict(set)
    for vid, hw, kana, lvl in con.execute("SELECT id, headword, kana, level FROM vocab"):
        level_of[vid], head_of[vid] = lvl, hw
        for f in (hw, kana):
            if f:
                forms[vid].add(f)
        if kana:
            readings[vid].add(hira(kana))
    for vid, form in con.execute("SELECT vocab_id, form FROM vocab_form"):
        if form:
            forms[vid].add(form)
            if kana_only(form):
                readings[vid].add(hira(form))

    touched = {sid_of[r["sentence"]] for r in rows if r["sentence"] in sid_of}
    toks: dict[int, list[dict]] = defaultdict(list)
    q = ",".join("?" * len(touched))
    for tid, sid, pos, surf, lemma, rdg, vid in con.execute(
            f"SELECT id, sentence_id, position, surface, lemma, reading, vocab_id FROM token "
            f"WHERE split_mode='C' AND sentence_id IN ({q}) ORDER BY sentence_id, position",
            sorted(touched)):
        toks[sid].append({"id": tid, "pos": pos, "surface": surf or "", "lemma": lemma or "",
                          "reading": rdg or "", "vid": vid})
    at = {(sid, t["pos"]): t for sid, tl in toks.items() for t in tl}

    problems: list[str] = []
    plan: list[tuple[dict, dict, int, int | None, int]] = []   # (row, token, sid, new_vid, old_vid)
    already = replay_divergent = 0
    for i, r in enumerate(rows):
        addr = f"row {i}: {r['sentence']} @{r['position']} {r['surface']!r} {r['old_vocab']} -> {r['new_vocab']}"
        sid = sid_of.get(r["sentence"])
        old = vid_of.get(r["old_vocab"])
        new = vid_of.get(r["new_vocab"]) if r["new_vocab"] else None
        if sid is None or old is None or (r["new_vocab"] and new is None):
            problems.append(f"{addr}: sentence or record not in the index")
            continue
        t = at.get((sid, r["position"]))
        if t is None or t["surface"] != r["surface"]:
            problems.append(f"{addr}: no C token reading {r['surface']!r} at that position")
            continue
        if t["vid"] == new:
            already += 1
        elif t["vid"] != old:
            if LIVE_INDEX:
                problems.append(f"{addr}: the token carries vocab id {t['vid']}, not the row's old record")
                continue
            # Off the live index (a manifest replay) the dissector's written-form resolver can land
            # the same surface on a different sibling than it did live (いけ on 生ける instead of 池,
            # ため on 溜める instead of 為): the row's verified decision is about the word at this
            # address, so it applies, and the record actually there is the one whose edge goes.
            replay_divergent += 1
            old = t["vid"]
        plan.append((r, t, sid, new, old))
    if problems:
        for p in problems[:20]:
            print(f"  [FAIL] {p}")
        raise SystemExit(f"apply_token_link_repairs: {len(problems)} row(s) do not match the index; "
                         f"nothing written")

    cur = con.cursor()
    tok_w = ins = dele = kept = lvl_w = 0
    for r, t, sid, new, old in plan:
        if t["vid"] != new:
            if not args.check:
                cur.execute("UPDATE token SET vocab_id=? WHERE id=?", (new, t["id"]))
            t["vid"] = new
            tok_w += 1
    # ---- edges -------------------------------------------------------------------------------
    new_pairs: dict[tuple[int, int], bool] = {}
    old_pairs: set[tuple[int, int]] = set()
    for r, t, sid, new, old in plan:
        if new is not None:
            ok = hira(t["reading"]) in readings.get(new, ())
            new_pairs[(sid, new)] = new_pairs.get((sid, new), False) or ok
        old_pairs.add((sid, old))
    for (sid, vid), ok in sorted(new_pairs.items()):
        if con.execute("SELECT 1 FROM sentence_vocab WHERE sentence_id=? AND vocab_id=?",
                       (sid, vid)).fetchone():
            continue
        ins += 1
        if not args.check:
            cur.execute("INSERT INTO sentence_vocab (sentence_id, vocab_id, link_rule, reading_verified) "
                        "VALUES (?,?,?,?)", (sid, vid, "token", 1 if ok else 0))

    def still_produced(sid: int, vid: int) -> bool:
        tl = toks[sid]
        if any(t["vid"] == vid for t in tl):                                     # R1
            return True
        if level_of.get(vid) in R2_LEVELS:                                       # R2
            fs = forms.get(vid, set())
            for i in range(len(tl)):
                run = ""
                for w in range(MAXW):
                    if i + w >= len(tl):
                        break
                    run += tl[i + w]["surface"]
                    if run in fs:
                        return True
        if level_of.get(vid) == R3_LEVEL and any(t["lemma"] == head_of.get(vid) for t in tl):  # R3
            return True
        return False

    for sid, vid in sorted(old_pairs):
        row = con.execute("SELECT link_rule FROM sentence_vocab WHERE sentence_id=? AND vocab_id=?",
                          (sid, vid)).fetchone()
        if row is None:
            continue
        if row[0] == "ortho" or still_produced(sid, vid):
            kept += 1
            continue
        dele += 1
        if not args.check:
            cur.execute("DELETE FROM sentence_vocab WHERE sentence_id=? AND vocab_id=?", (sid, vid))
    # ---- scoped re-level: the table's `sentence_levels` (repair-driven moves only) ----------
    moves: dict[tuple[str, str], int] = defaultdict(int)
    for x in json.loads(args.table.read_text(encoding="utf-8")).get("sentence_levels") or []:
        sid = sid_of.get(x["sentence"])
        stored = con.execute("SELECT level FROM sentence WHERE id=?", (sid,)).fetchone()[0] if sid else None
        if stored == x["to"]:
            continue
        vids = [v for (v,) in con.execute("SELECT vocab_id FROM sentence_vocab WHERE sentence_id=?", (sid,))]
        kids = [k for (k,) in con.execute("SELECT kanji_id FROM sentence_kanji WHERE sentence_id=?", (sid,))]
        if stored != x["from"] or computed_level(con, vids, kids) != x["to"]:
            if LIVE_INDEX:
                problems.append(f"level {x['sentence']}: stored {stored!r}, edges compute "
                                f"{computed_level(con, vids, kids)}; the row moves {x['from']} -> {x['to']}")
                continue
            # a replay's ingest-time levels and run edges are not the live index's (bank.json is a
            # pinned file of rebuild_baseline.json); the row's level is the published one, so it lands
            replay_divergent += 1
        moves[(stored, x["to"])] += 1
        lvl_w += 1
        if not args.check:
            cur.execute("UPDATE sentence SET level=? WHERE id=?", (x["to"], sid))
    # ---- reading boxes: the `uses` snapshot, index + W15 table (both layers) ----------------
    ru = json.loads(args.table.read_text(encoding="utf-8")).get("reading_uses") or []
    rd_w = src_w = 0
    if ru and con.execute("SELECT name FROM sqlite_master WHERE name='reading'").fetchone():
        by_box: dict[str, list[dict]] = defaultdict(list)
        for x in ru:
            by_box[x["reading"]].append(x)
        for slug, xs in sorted(by_box.items()):
            got = con.execute("SELECT uses FROM reading WHERE slug=?", (slug,)).fetchone()
            if got is None:
                if LIVE_INDEX:
                    problems.append(f"reading {slug}: not in the index")
                else:                      # a replay's build_readings selection differs from live
                    replay_divergent += 1
                continue
            uses = json.loads(got[0] or "{}")
            vids = set(uses.get("vocab") or [])
            for x in xs:
                old = vid_of[x["retire"]]
                new = vid_of[x["replace"]] if x["replace"] else None
                if old in vids:
                    vids.discard(old)
                    if new is not None:
                        vids.add(new)
                elif new is not None and new not in vids:
                    if LIVE_INDEX:
                        problems.append(f"reading {slug}: uses carries neither {x['retire']} nor {x['replace']}")
                    else:
                        replay_divergent += 1
            if sorted(vids) != sorted(uses.get("vocab") or []):
                rd_w += 1
                uses["vocab"] = sorted(vids)
                if not args.check:
                    cur.execute("UPDATE reading SET uses=? WHERE slug=?",
                                (json.dumps(uses, ensure_ascii=False), slug))
        w15 = ROOT / "research" / "derived" / "repairs" / "reading_passages.json"
        wdoc = json.loads(w15.read_text(encoding="utf-8"))
        wrows = {r["slug"]: r for r in wdoc["rows"]}
        for slug, xs in sorted(by_box.items()):
            if slug not in wrows:          # a W15-held box: its uses live in the index only
                continue
            v = wrows[slug]["new"]["uses"]["vocab"]
            for x in xs:
                if x["retire"] in v:
                    i = v.index(x["retire"])
                    if x["replace"] and x["replace"] not in v:
                        v[i] = x["replace"]
                    else:
                        del v[i]
                    src_w += 1
        if src_w and not args.check:
            w15.write_text(json.dumps(wdoc, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    if problems:
        for p in problems[:20]:
            print(f"  [FAIL] {p}")
        con.rollback()
        raise SystemExit(f"apply_token_link_repairs: {len(problems)} level / reading row(s) do not "
                         f"match; nothing committed")
    if args.check:
        con.rollback()
    else:
        con.commit()
    con.close()
    print(f"  reading boxes: {rd_w} index uses rewritten, {src_w} W15 snapshot entr(ies) rewritten "
          f"({len(ru)} rows)")
    verb = "would write" if args.check else "wrote"
    if replay_divergent:
        print(f"  [replay] {replay_divergent} row(s) met a token record, stored level or box `uses` "
              f"other than the live index's (not db/corpus.sqlite): the row's decision applied anyway")
    print(f"apply_token_link_repairs: {len(rows)} rows verified ({already} already applied); {verb} "
          f"{tok_w} token link(s); sentence_vocab +{ins} / -{dele} ({kept} old pair(s) still produced "
          f"by another rule); {lvl_w} sentence level(s) over {len(touched)} touched sentences")
    for (a, b), n in sorted(moves.items()):
        print(f"    level {a} -> {b}: {n}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
