#!/usr/bin/env python3
"""Q2 (c) — the course follows the token relink: repoint the wrong-sibling unlocks, both layers.

WHAT WAS WRONG
--------------
Eight lessons unlocked a same-reading sibling of the word they teach (刷る 'imprimir' for する,
生る 'dar fruto' for なる, 罹る for かかる, 用 for よう, 報 for ほう, 動 for どう, ...): the unlock was
resolved by written form, and W21b then placed each one at the first lesson whose token links named
it. Once the token links are repaired (scripts/apply_token_link_repairs.py) the sibling has no
sentences and the word the lesson shows is unknown everywhere it appears.

WHAT THIS APPLIES
-----------------
research/derived/repairs/sibling_unlock_repoint.json. Per row, in `lesson`: the sibling's unlock is
replaced IN THE SAME SLOT by the record the lesson teaches (or removed, for 動: どう has no record, or
added, for 呉れる at the lesson that teaches くれる); a later unlock of that record (`moved_from`) is
removed, so it is introduced once. Written to:
  * research/derived/lessons/<slug>.json (authoring source) and db/corpus.sqlite: lesson_unlocks,
    lesson_introduces, then lesson.cumulative_known_set recomputed with the ingest's own routine;
  * card_production_key (db) and research/derived/repairs/card_production_keys.json: the retired
    card's key is dropped, a moved card's key is re-homed verbatim, a card with no key gets the
    derived key in `derived_keys` below (the W21b precedent: the table is lesson-addressed and a
    rebuild replays it against sources that already carry the move);
  * research/derived/repairs/w21b_forward_refs.json: the W21b moves of a retired sibling, or of a
    target this repoint moved away from its W21b home, are marked `retired_by` (the move is history;
    apply_forward_refs.py and its replay handler skip them).
  * a `keeps` row adds the record beside a sibling the lesson's own prose teaches (罹る at
    les:n5-verbos-03 stays; 掛かる joins it);
  * course/coverage_exemptions.json (repo-side): the sibling no lesson teaches any more (刷る) is
    listed with its reason, and a record this table unlocks leaves the list; the W11a
    `hold` on 様/よう in homograph_rulings.json is marked `released_by` this table.
The SRS card itself follows the unlock (export_course._srs_cards). Lesson bodies are not touched.

Idempotent: a second run reports 0 changes. Refuses (writes nothing) on any row the tree contradicts.
Run apply_card_production_keys.py and the exporters afterwards.
Usage: apply_sibling_unlock_repoint.py [--check]
"""
from __future__ import annotations

import argparse
import json
import sqlite3
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
import sys as _sys, pathlib as _pl  # noqa: E402
_sys.path.append(str(next(p for p in _pl.Path(__file__).resolve().parents if p.name == "scripts")))
from dbtarget import db_target, out_root  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
DB = db_target(ROOT / "db" / "corpus.sqlite")
SRC = out_root(ROOT) / "research" / "derived" / "lessons"
REPAIRS = ROOT / "research" / "derived" / "repairs"
TABLE = REPAIRS / "sibling_unlock_repoint.json"
CARD_TABLE = REPAIRS / "card_production_keys.json"
W21B = REPAIRS / "w21b_forward_refs.json"
REPORT = "research/reports/q2_token_links_report.md"
MARK = "sibling_unlock_repoint.json"
COVERAGE = out_root(ROOT) / "course" / "coverage_exemptions.json"
HOMOGRAPH = REPAIRS / "homograph_rulings.json"
# course/coverage_exemptions.json: a taught-level record no lesson unlocks must say why.
EXEMPT_REASON = {
    "vocab:1298670": "Same-reading sibling of vocab:1157170 (為る/する). Q2-token-links: les:n5-verbos-02 "
                     "unlocked 刷る 'to print' for する 'to do'; that slot now unlocks 為る and no lesson "
                     "teaches 刷る. Its N5 tally is the four lists' kana entry する 'to do' (the evidence now "
                     "also on 為る, research/derived/repairs/level_transfer_repairs.json); its own glossed "
                     "entries are N2. Held until the sibling tallies are corrected "
                     "(research/reports/q2_token_links_report.md).",
}

# The W27 residue template for the two cards that never had a key: the record's pt-BR gloss for the
# sense the lesson teaches plus a cue naming the lesson's use. `accept` is computed, never typed.
DERIVED_KEYS = [
    {"lesson": "les:n4-oracoes-relativas-07", "item": "vocab:1605840", "sense_index": 2,
     "prompt": {"pt-BR": "como, igual a (a raiz よう de ～ように e ～ような)"},
     "why": "sense 2 of 3 ('tipo, como (este/esse)'): the lesson teaches のように/のような 'como / igual a' "
            "and says 'A raiz よう nunca muda'. Cue names the pattern so the card is not 様子 or 方法."},
    {"lesson": "les:n5-particulas-lugar-07", "item": "vocab:1269130", "sense_index": 0,
     "prompt": {"pt-BR": "dar (a mim ou ao meu grupo)"},
     "why": "sense 0 of 2 ('dar (a mim/nós)'): the lesson is 'Dar e receber: あげる, くれる e もらう' and "
            "teaches くれる as giving toward the speaker. Distinct from 上げる (dar a outra pessoa)."},
]


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def dump(path: Path, doc: dict, indent: int) -> None:
    path.write_text(json.dumps(doc, ensure_ascii=False, indent=indent) + "\n", encoding="utf-8")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true", help="report what would change; write nothing")
    args = ap.parse_args()
    doc = load(TABLE)
    rows = doc["rows"]
    if doc.get("row_count") != len(rows):
        raise SystemExit(f"{TABLE.name}: row_count {doc.get('row_count')} != {len(rows)}")

    con = sqlite3.connect(DB)
    con.execute("PRAGMA busy_timeout=60000")
    lid = dict(con.execute("SELECT slug, id FROM lesson"))
    vid = dict(con.execute("SELECT slug, id FROM vocab"))
    problems: list[str] = []
    n = {"source": 0, "unlock": 0, "introduces": 0, "card_key_db": 0, "card_table": 0, "w21b": 0,
         "exemptions": 0, "homograph_hold": 0}

    def w(sql: str, params: tuple) -> None:
        if not args.check:
            con.execute(sql, params)

    def has_unlock(lesson: str, ref: str) -> bool:
        return con.execute("SELECT 1 FROM lesson_unlocks WHERE lesson_id=? AND unlock_type='vocab' AND ref=?",
                           (lid[lesson], ref)).fetchone() is not None

    for r in rows:
        L, M = r["lesson"], r.get("moved_from")
        for x in (L, M):
            if x and x not in lid:
                problems.append(f"{x}: not a lesson in the index")
        for x in (r.get("retire"), r.get("unlock")):
            if x and x not in vid:
                problems.append(f"{x}: not a vocab record")
    if problems:
        for p in problems:
            print(f"  ! {p}")
        return 2

    sources: dict[str, dict] = {}

    def src(lesson: str) -> dict:
        if lesson not in sources:
            f = SRC / f"{lesson.split(':', 1)[1]}.json"
            if not f.exists():
                raise SystemExit(f"{lesson}: authoring source {f.name} missing")
            sources[lesson] = {"path": f, "doc": load(f), "dirty": False}
        return sources[lesson]

    for r in rows:
        L, M = r["lesson"], r.get("moved_from")
        old_src, new_ref = r.get("retire_src"), r.get("unlock")
        # ---- authoring source: the lesson ---------------------------------------------------
        s = src(L)
        ul = s["doc"].setdefault("unlocks", [])
        ent_old = {"type": "vocab", "ref": old_src} if old_src else None
        ent_new = {"type": "vocab", "ref": new_ref} if new_ref else None
        if ent_old and ent_old in ul:
            i = ul.index(ent_old)
            if ent_new and ent_new not in ul:
                ul[i] = ent_new
            else:
                del ul[i]
            s["dirty"] = True
        elif ent_new and ent_new not in ul:
            if ent_old:
                problems.append(f"{L}: source unlocks neither {old_src} nor {new_ref}")
                continue
            ul.append(ent_new)
            s["dirty"] = True
        if M:
            sm = src(M)
            ent_m = {"type": "vocab", "ref": r["moved_from_src"]}
            if ent_m in sm["doc"].get("unlocks") or []:
                sm["doc"]["unlocks"].remove(ent_m)
                sm["dirty"] = True
        # ---- index: unlocks + introduces --------------------------------------------------
        if old_src and has_unlock(L, old_src):
            n["unlock"] += 1
            if new_ref and not has_unlock(L, new_ref):
                w("UPDATE lesson_unlocks SET ref=? WHERE lesson_id=? AND unlock_type='vocab' AND ref=?",
                  (new_ref, lid[L], old_src))
            else:
                w("DELETE FROM lesson_unlocks WHERE lesson_id=? AND unlock_type='vocab' AND ref=?",
                  (lid[L], old_src))
        elif new_ref and not has_unlock(L, new_ref):
            if old_src:
                problems.append(f"{L}: index unlocks neither {old_src} nor {new_ref}")
                continue
            n["unlock"] += 1
            w("INSERT INTO lesson_unlocks (lesson_id, unlock_type, ref) VALUES (?,?,?)",
              (lid[L], "vocab", new_ref))
        # ---- a sibling the lesson's own prose teaches stays unlocked beside the new record ----
        K = r.get("keeps")
        if K:
            ent_k = {"type": "vocab", "ref": r["keeps_src"]}
            if ent_k not in ul:
                ul.append(ent_k)
                s["dirty"] = True
            if not has_unlock(L, r["keeps_src"]):
                n["unlock"] += 1
                w("INSERT INTO lesson_unlocks (lesson_id, unlock_type, ref) VALUES (?,?,?)",
                  (lid[L], "vocab", r["keeps_src"]))
            if not con.execute("SELECT 1 FROM lesson_introduces WHERE lesson_id=? AND member_type='vocab' "
                               "AND member_id=?", (lid[L], vid[K])).fetchone():
                n["introduces"] += 1
                w("INSERT INTO lesson_introduces (lesson_id, member_type, member_id) VALUES (?,?,?)",
                  (lid[L], "vocab", vid[K]))
        # ---- the sibling goes back to the lesson whose prose teaches it (W21b move undone) ---
        H = r.get("returns_to")
        if H:
            sh = src(H)
            ent_h = {"type": "vocab", "ref": r["retire"]}
            if ent_h not in sh["doc"].setdefault("unlocks", []):
                sh["doc"]["unlocks"].append(ent_h)
                sh["dirty"] = True
            if not has_unlock(H, r["retire"]):
                n["unlock"] += 1
                w("INSERT INTO lesson_unlocks (lesson_id, unlock_type, ref) VALUES (?,?,?)",
                  (lid[H], "vocab", r["retire"]))
            if not con.execute("SELECT 1 FROM lesson_introduces WHERE lesson_id=? AND member_type='vocab' "
                               "AND member_id=?", (lid[H], vid[r["retire"]])).fetchone():
                n["introduces"] += 1
                w("INSERT INTO lesson_introduces (lesson_id, member_type, member_id) VALUES (?,?,?)",
                  (lid[H], "vocab", vid[r["retire"]]))
        if M and has_unlock(M, r["moved_from_src"]):
            n["unlock"] += 1
            w("DELETE FROM lesson_unlocks WHERE lesson_id=? AND unlock_type='vocab' AND ref=?",
              (lid[M], r["moved_from_src"]))
        intro = "SELECT 1 FROM lesson_introduces WHERE lesson_id=? AND member_type='vocab' AND member_id=?"
        if r.get("retire") and con.execute(intro, (lid[L], vid[r["retire"]])).fetchone():
            n["introduces"] += 1
            w("DELETE FROM lesson_introduces WHERE lesson_id=? AND member_type='vocab' AND member_id=?",
              (lid[L], vid[r["retire"]]))
        if new_ref and not con.execute(intro, (lid[L], vid[new_ref])).fetchone():
            n["introduces"] += 1
            w("INSERT INTO lesson_introduces (lesson_id, member_type, member_id) VALUES (?,?,?)",
              (lid[L], "vocab", vid[new_ref]))
        if M and new_ref and con.execute(intro, (lid[M], vid[new_ref])).fetchone():
            n["introduces"] += 1
            w("DELETE FROM lesson_introduces WHERE lesson_id=? AND member_type='vocab' AND member_id=?",
              (lid[M], vid[new_ref]))
        # ---- index: the production key follows the card ------------------------------------
        if r.get("retire") and con.execute("SELECT 1 FROM card_production_key WHERE lesson_id=? AND item=?",
                                           (lid[L], r["retire"])).fetchone():
            n["card_key_db"] += 1
            if H:
                w("UPDATE card_production_key SET lesson_id=? WHERE lesson_id=? AND item=?",
                  (lid[H], lid[L], r["retire"]))
            else:
                w("DELETE FROM card_production_key WHERE lesson_id=? AND item=?", (lid[L], r["retire"]))
        if M and new_ref and con.execute("SELECT 1 FROM card_production_key WHERE lesson_id=? AND item=?",
                                         (lid[M], new_ref)).fetchone():
            n["card_key_db"] += 1
            w("UPDATE card_production_key SET lesson_id=? WHERE lesson_id=? AND item=?",
              (lid[L], lid[M], new_ref))

    # ---- placement: the record's introducing topic follows its unlock (W21b's rule) ----------
    tpc = dict(con.execute("SELECT l.slug, l.topic_id FROM lesson l"))
    for r in rows:
        for rec, home in ((r.get("unlock"), r["lesson"]), (r.get("retire"), r.get("returns_to"))):
            if not rec or not home:
                continue
            got = con.execute("SELECT introducing_topic_id FROM vocab WHERE slug=?", (rec,)).fetchone()
            if got and got[0] != tpc[home]:
                n["topic"] = n.get("topic", 0) + 1
                w("UPDATE vocab SET introducing_topic_id=? WHERE slug=?", (tpc[home], rec))

    # ---- the lesson-addressed card-key table ------------------------------------------------
    ct = load(CARD_TABLE)
    retired = {(r["lesson"], r["retire"]) for r in rows if r.get("retire") and not r.get("returns_to")}
    moved = {(r["moved_from"], r["unlock"]): r["lesson"] for r in rows if r.get("moved_from")}
    moved.update({(r["lesson"], r["retire"]): r["returns_to"] for r in rows if r.get("returns_to")})
    keep = []
    dropped = ct.get("retired_by_q2") or []
    for x in ct["rows"]:
        k = (x["lesson"], x["item"])
        if k in retired:
            dropped.append({"lesson": x["lesson"], "item": x["item"], "prompt": x["prompt"],
                            "accept": x["accept"], "why": "the unlock is retired by "
                            "sibling_unlock_repoint.json (the lesson teaches the same-reading sibling)"})
            n["card_table"] += 1
            continue
        if k in moved:
            x["lesson"] = moved[k]
            n["card_table"] += 1
        keep.append(x)
    have = {(x["lesson"], x["item"]) for x in keep}
    if any((d["lesson"], d["item"]) not in have for d in DERIVED_KEYS):
        sys.path.insert(0, str(ROOT / "scripts"))
        from build_card_key_table import load_form_tags, load_vocab, strip_accept  # noqa: PLC0415
        vocab, tags = load_vocab(), load_form_tags()
        for d in DERIVED_KEYS:
            if (d["lesson"], d["item"]) in have:
                continue
            rec = vocab[d["item"]]
            kept, removed = strip_accept([f["form"] for f in rec["forms"]], rec,
                                         tags.get(d["item"].split(":", 1)[1], {}))
            keep.append({"lesson": d["lesson"], "item": d["item"], "origin": "q2-derived",
                         "prompt": d["prompt"], "accept": kept, "sense_index": d["sense_index"],
                         "why": d["why"], "verified": "derived", "verified_by": REPORT,
                         "accept_removed": removed})
            n["card_table"] += 1
    if n["card_table"]:
        ct["rows"], ct["row_count"] = keep, len(keep)
        ct["counts"]["rows"] = len(keep)
        ct["retired_by_q2"] = dropped
        prompts = [x["prompt"]["pt-BR"] for x in keep]
        if len(set(prompts)) != len(prompts):
            problems.append("card_production_keys.json: a derived prompt collides with another card's")

    # ---- W21b moves that this repoint supersedes --------------------------------------------
    wt = load(W21B)
    gone = {r["retire"] for r in rows if r.get("retire")}
    away = {(r["moved_from"], r["unlock"]) for r in rows if r.get("moved_from")}
    for x in wt["rows"]:
        if x.get("retired_by"):
            continue
        if x["item"] in gone or (x["to"], x["item"]) in away:
            x["retired_by"] = MARK
            back = next((r["returns_to"] for r in rows if r.get("retire") == x["item"]
                         and r.get("returns_to") == x["from"]), None)
            x["retired_why"] = ("move undone: the lesson it came from teaches the record in prose, and the "
                                "first use that drew it here was a mislinked token" if back else
                                "the record this move placed is retired from the course (same-reading "
                                "sibling)" if x["item"] in gone else
                                "the record now lives at the lesson that unlocked its sibling")
            n["w21b"] += 1

    # ---- repo-side exemption file + the W11a hold this repoint releases -----------------------
    cov = None
    if COVERAGE.is_file():                         # a rebuild work root carries no course/ files
        cov = load(COVERAGE)
        unlocked_now = {r["unlock"] for r in rows if r.get("unlock")}
        keep = [e for e in cov["vocab"] if e["id"] not in unlocked_now]
        have_ids = {e["id"] for e in keep}
        for r in rows:
            if r.get("retire") and not r.get("returns_to") and r["retire"] not in have_ids:
                keep.append({"id": r["retire"], "reason": EXEMPT_REASON[r["retire"]]})
        if keep != cov["vocab"]:
            cov["vocab"] = keep
            n["exemptions"] = 1
        else:
            cov = None
    hg = load(HOMOGRAPH)
    for x in hg["rows"] if isinstance(hg, dict) else hg:
        if x.get("kind") == "hold" and not x.get("released_by") and \
                any(r.get("unlock") == x["new"] for r in rows):
            x["released_by"] = MARK
            x["released_why"] = ("Q2-token-links unlocks this record at the lesson that teaches ように/ような "
                                 "(les:n4-oracoes-relativas-07), in the slot that unlocked 用 for the same よう; "
                                 "the course already carried a card there, for the wrong record. The general "
                                 "policy question (a card for every grammar-bearing formal noun: こと, もの, "
                                 "ところ) is still open.")
            n["homograph_hold"] += 1
    if problems:
        for p in problems:
            print(f"  ! {p}")
        print("NOTHING WAS WRITTEN.")
        con.rollback()
        return 2
    if not args.check:
        if cov is not None:
            dump(COVERAGE, cov, 2)
        if n["homograph_hold"]:
            dump(HOMOGRAPH, hg, 2)
    for lesson, s in sources.items():
        if s["dirty"]:
            n["source"] += 1
            if not args.check:
                dump(s["path"], s["doc"], 2)
    if not args.check:
        if n["card_table"]:
            dump(CARD_TABLE, ct, 1)
        if n["w21b"]:
            dump(W21B, wt, 1)
        sys.path.insert(0, str(ROOT / "scripts" / "ingest"))
        from load_lessons import recompute_cumulative  # noqa: PLC0415
        print(f"  recomputed cumulative_known_set for {recompute_cumulative(con)} lessons (db)")
        con.commit()
    con.close()
    verb = "would write" if args.check else "wrote"
    print(f"apply_sibling_unlock_repoint: {len(rows)} rows; {verb} " + ", ".join(f"{k} {v}" for k, v in n.items()))
    return 1 if (args.check and any(n.values())) else 0


if __name__ == "__main__":
    sys.exit(main())
