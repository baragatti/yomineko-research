#!/usr/bin/env python3
"""W21b: measure the forward-reference ledger, decide each use (move / rewrite / hold), simulate.

A FORWARD USE is (lesson L, item I) where L references I through one of `derive_needs.py`'s five
channels (body chip, body sentence, lesson `sentence_refs`, exercise `sentence_refs`, body reading
`uses`) and the lesson that unlocks I sits LATER in course order. The learner meets I before the
course teaches it. `validate_lesson_gating.py` check C excludes such edges from `needs[]` by
construction, so until this unit nothing counted them; check C5 now ratchets them by tier.

THE DECISION RULE (per item I, taught at M, with earlier users U):

  HOLD      the user is at an earlier LEVEL than M (the i+1 backlog: moving an unlock across levels
            changes the item's level placement), or the owner held the item (`HELD`), or a replayed
            step writes or asserts I's unlock at M (`homograph_rulings.json` unlock rows and the
            `ref` rows that affect an unlock, `lesson_ref_addresses.json`, the hardcoded adds of
            `apply_missing_homograph_unlocks.py`): moving it would make the replay write it twice.
  MOVE      the unlock moves to the FIRST same-level user T. The SRS card is derived from the unlock,
            so it moves with it; M keeps its explanation. Feasible only if
              R1  T is not a review lesson (W22 review shape: zero item unlocks),
              R2  I is not M's only item unlock,
              R6  T renders a retrieval + production pair once it teaches,
              R7  I is not M's last kanji/grammar/kana unlock (a vocabulary-only lesson has no
                  capability; validate_graph_edges capability_coverage).
            If the first user fails, the next same-level user is tried (homes only move earlier and
            the passes repeat until nothing changes).
  REWRITE   a same-level use left before the final home: the span must be re-authored or re-selected.

THE EXERCISE (owner ruling 2026-09-23, APP_PLAN W21b (1)): an exercise of M whose only M-target is I
TRAVELS with the unlock when it asks about nothing T does not know yet (R4) and M keeps a rendered
retrieval + production pair without it (R5). Otherwise it STAYS in M as review - M comes later, so
it knows every word the exercise uses. The derivation used to block the move instead (R3/R4 were
move blockers, 122 rewrite rows); they now only decide whether the exercise travels. A moved item
that its new home does not practise is listed in `u5_drills` for the W20 generator (unit U5), and
`validate_practice_coverage.py` holds exactly that list as debt that can only shrink.

"Practised" and "target" are `validate_practice_coverage.py`'s own definitions, imported from the
gate, never re-implemented.

SIMULATION: the moves are replayed on a copy of the tree (fixture), every `cumulative_known_set` is
recomputed and compared (no key may shrink), `needs[]` is re-derived with `build_needs_table.build()`
(what C4 checks), and the gates run on both copies. The DB half moves `lesson_unlocks` rows on a
backup of db/corpus.sqlite and asserts no running union shrinks; it also records the ref string each
move finds in the index (`db_ref`), which is what `apply_forward_refs.py` re-proves before writing.

Writes ONLY the table (default research/derived/pending/w21b_forward_refs.json) and a work dir.
Usage: derive_forward_refs.py [--work DIR] [--out PATH] [--keep-work]
"""
from __future__ import annotations

import argparse
import copy
import importlib.util
import json
import re
import shutil
import sqlite3
import subprocess
import sys
import tempfile
from collections import Counter, defaultdict
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]

REPO = Path(__file__).resolve().parents[1]
DB = REPO / "db" / "corpus.sqlite"
OUT_DEFAULT = REPO / "research/derived/pending/w21b_forward_refs.json"

COPY_DIRS = ["course", "corpus/kanji", "corpus/vocab", "corpus/grammar", "corpus/readings", "corpus/kana"]
COPY_FILES = ["corpus/sentences/bank.json", "design/unlock_enums.json",
              "research/reports/lesson_sentence_baseline.json",
              "scripts/derive_needs.py", "scripts/build_needs_table.py",
              "scripts/validate/validate_lesson_gating.py", "scripts/validate/validate_unlock_ledger.py",
              "scripts/validate/validate_practice_coverage.py",
              "scripts/validate/practice_coverage_baseline.json",
              "scripts/validate/validate_exercise_contracts.py", "scripts/validate/validate_srs_decks.py"]
VALIDATORS = [("validate_lesson_gating.py", ["--no-report"]), ("validate_unlock_ledger.py", []),
              ("validate_practice_coverage.py", ["--no-report"]), ("validate_exercise_contracts.py", []),
              ("validate_srs_decks.py", [])]

# Owner rulings (APP_PLAN W21b, 2026-09-23). An item here is never moved, whatever the rule allows.
HELD = {
    "gram:nasaru": "owner ruling 2026-09-23 (APP_PLAN W21b (2)): the move is legal but would put the "
                   "card 60 lessons ahead of its keigo explanation in les:n4-keigo-03",
}
LOCKED_TABLES = ("homograph_rulings.json", "lesson_ref_addresses.json")

TEACHING = {"kana-family", "vocab", "kanji", "grammar", "conjugation-form", "phrase"}
# unlock types corpus/capabilities maps to a capability; a lesson with none of them needs an exemption
CAPABILITY_TYPES = {"kana-family", "kanji", "grammar"}
KINDS = ("kana-family", "vocab", "kanji", "grammar", "conjugation-form", "phrase")
NS_KIND = {"vocab": "vocab", "kanji": "kanji", "gram": "grammar"}
RETRIEVAL = {"recognition", "reading", "listening", "cloze", "particle_choice", "matching", "ordering"}
PRODUCTION = {"production", "handwriting"}
EX_TAG = re.compile(r'<exercise\s+ref="([^"]+)"\s*/>')

RULES = {
    "A-move": "MOVE: the item's unlock (and its SRS card, derived from the unlock) moves to the FIRST "
              "same-level lesson that uses it; the teaching lesson keeps its explanation. An exercise "
              "whose only target in the teaching lesson is the item travels when R4 and R5 allow, "
              "otherwise it stays behind as review. Feasible only if R1, R2, R6 and R7 pass.",
    "A-move-partial": "MOVE to a LATER same-level user because the move to the first one fails R1/R2/R6/R7; "
                      "this row is cleared, the uses before the new home stay as B-rewrite rows.",
    "B-rewrite": "REWRITE: same-topic/same-level use whose move fails R1, R2, R6 or R7; the use (span) must be "
                 "re-authored or re-selected (authoring list).",
    "C-hold": "HOLD: the using lesson is at an EARLIER level than the teaching lesson; moving an unlock "
              "across levels changes the item's level placement, so the use stays in the frozen i+1 "
              "backlog (check D baseline) for the level-aware re-selection campaign (W14).",
    "C-hold/owner": "HOLD by owner ruling (HELD in scripts/derive_forward_refs.py).",
    "C-hold/table": "HOLD: a replayed lesson-addressed step writes or asserts this unlock at its current "
                    "lesson (homograph_rulings.json / lesson_ref_addresses.json / "
                    "apply_missing_homograph_unlocks.py); moving it would make the rebuild write it twice.",
    "R1": "the target lesson is a review lesson (zero item unlocks by W22's review shape)",
    "R2": "the item is the teaching lesson's only unlock (it would stop being a teaching lesson)",
    "R4": "(exercise stays behind) the exercise asks about items the target lesson does not know yet",
    "R5": "(exercise stays behind) moving it would leave the teaching lesson without a rendered "
          "retrieval+production pair",
    "R6": "the target lesson would teach but renders no retrieval+production pair",
    "R7": "the item is the teaching lesson's last kanji/grammar/kana unlock (it would lose its capability)",
}


def load_mod(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)  # type: ignore[arg-type]
    sys.modules[name] = mod
    spec.loader.exec_module(mod)  # type: ignore[union-attr]
    return mod


def make_fixture(dst: Path) -> None:
    """Copy what the derivation and the five gates read. A frozen copy, so the simulation can write."""
    if dst.exists():
        shutil.rmtree(dst)
    dst.mkdir(parents=True)
    for d in COPY_DIRS:
        shutil.copytree(REPO / d, dst / d, ignore=shutil.ignore_patterns("__pycache__"))
    for f in COPY_FILES:
        (dst / f).parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(REPO / f, dst / f)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--work", type=Path, help="work dir for the fixtures (default: a temp dir)")
    ap.add_argument("--out", type=Path, default=OUT_DEFAULT, help="where to write the table")
    ap.add_argument("--keep-work", action="store_true", help="do not delete the work dir")
    args = ap.parse_args()
    work = args.work or Path(tempfile.mkdtemp(prefix="w21b_"))
    work.mkdir(parents=True, exist_ok=True)
    fx_before, fx_after, snap = work / "fx_before", work / "fx_after", work / "c.sqlite"
    try:
        return run(work, fx_before, fx_after, snap, args.out)
    finally:
        if not args.keep_work and not args.work:
            shutil.rmtree(work, ignore_errors=True)


def run(work: Path, FX_BEFORE: Path, FX_AFTER: Path, SNAP: Path, OUT: Path) -> int:
    # ------------------------------------------------------------------ freeze the inputs
    make_fixture(FX_BEFORE)
    src = sqlite3.connect(DB)
    dst = sqlite3.connect(SNAP)
    src.backup(dst)
    src.close()
    dst.close()
    sys.path.insert(0, str(FX_BEFORE / "scripts"))
    DN = load_mod("derive_needs", FX_BEFORE / "scripts/derive_needs.py")
    BNT = load_mod("build_needs_table", FX_BEFORE / "scripts/build_needs_table.py")
    PC = load_mod("vpc", FX_BEFORE / "scripts/validate/validate_practice_coverage.py")
    ROOT = FX_BEFORE

    lessons = DN.load_course(ROOT)
    order = [d["id"] for d in lessons]
    pos = {lid: i for i, lid in enumerate(order)}
    by_id = {d["id"]: d for d in lessons}
    level = {d["id"]: d.get("level") for d in lessons}
    topic = {d["id"]: d.get("topic") for d in lessons}
    is_review = {lid: "revisao" in (topic[lid] or "") for lid in order}
    lesson_path = {}
    for p in sorted(ROOT.glob("course/*/topic-*/lesson-*.json")):
        lesson_path[json.loads(p.read_text(encoding="utf-8"))["id"]] = p.relative_to(ROOT)

    introducer: dict[str, str] = {}
    utype: dict[str, str] = {}
    for d in lessons:
        for u in d.get("unlocks") or []:
            introducer.setdefault(u["ref"], d["id"])
            utype[u["ref"]] = u["type"]

    sent_idx = DN.load_sentence_index(ROOT)
    read_idx = DN.load_reading_index(ROOT)
    bank = {s["slug"]: s for s in json.loads((ROOT / "corpus/sentences/bank.json").read_text(encoding="utf-8"))}

    # practice-coverage primitives, reused verbatim from the gate
    VSURF, VMAX = PC.load_vocab(ROOT)
    TILE = PC.make_tiler(VSURF, VMAX)
    KCHAR = PC.load_kanji(ROOT)                      # kanji slug -> character
    CHAR2K = {c: s for s, c in KCHAR.items()}
    GPROBES, _ = PC.load_grammar(ROOT)
    SENTS = PC.load_sentences(ROOT)
    PEX = {e["id"] for e in json.loads((ROOT / "course/practice_exemptions.json").read_text(encoding="utf-8"))["lessons"]}

    # (lesson, item) pairs a replayed lesson-addressed table writes an unlock for
    # (lesson, item) pairs a replayed table writes or asserts as an unlock of that lesson: the unlock
    # rows and the `ref` rulings that affect an unlock (homograph_rulings), and every address rewrite
    # (lesson_ref_addresses). Moving one of those would make the replay fail or write it twice.
    locked: dict[tuple[str, str], str] = {}
    for name in LOCKED_TABLES:
        doc = json.loads((REPO / "research/derived/repairs" / name).read_text(encoding="utf-8"))
        for r in doc["rows"]:
            if name == "homograph_rulings.json" and not (
                    r.get("kind") == "unlock" or (r.get("kind") == "ref" and "unlock" in (r.get("affects") or []))):
                continue
            locked[(r["lesson"], r["new"])] = name
    # exercises a replayed table addresses in a way a re-home cannot follow: the homograph practice
    # rows, and the W20 rows whose exported id is an `apply_id_remap` target (keyed by old id + lesson)
    locked_ex = {r["exercise"] for r in json.loads((REPO / "research/derived/repairs/homograph_rulings.json")
                                                   .read_text(encoding="utf-8"))["rows"]
                 if r.get("kind") == "practice"}
    locked_ex |= {m["to"] for m in json.loads((REPO / "research/derived/repairs/practice_kanji_exercises.json")
                                              .read_text(encoding="utf-8")).get("apply_id_remap") or []}
    # scripts/apply_missing_homograph_unlocks.py (a replayed step) hardcodes six (lesson, record) unlocks
    MHU = load_mod("apply_missing_homograph_unlocks", REPO / "scripts/apply_missing_homograph_unlocks.py")
    for lesson_, _hw_ref, slug_, _lvl in MHU.ADDS:
        locked[(lesson_, slug_)] = "apply_missing_homograph_unlocks.py"

    def pool(exercises: list[dict]):
        """The practice pools exactly as validate_practice_coverage.main builds them for one lesson."""
        answer_strings: list[str] = []
        marked: set[str] = set()
        cited: set[str] = set()
        tiled: set[str] = set()
        for ex in exercises:
            mine = PC.answer_surfaces(ex.get("answer"))
            answer_strings += mine
            if ex.get("prompt") is not None:
                marked |= set(PC.TARGET_REF_RX.findall(json.dumps(ex["prompt"], ensure_ascii=False)))
            exc = {s for s in (ex.get("sentence_refs") or []) if isinstance(s, str) and s in SENTS}
            cited |= exc
            verbatim = {SENTS[s][3] for s in exc}
            for s in mine:
                if PC.fold_sentence(s) in verbatim:
                    continue
                for run_ in PC.JP_RUN_RX.findall(s):
                    TILE(run_, tiled)
        runs: list[str] = []
        for s in answer_strings:
            runs += PC.JP_RUN_RX.findall(s)
        answer_text = "".join(runs)
        sv: set[str] = set()
        sg: set[str] = set()
        st = ""
        for s in cited:
            v, g, surf, _ = SENTS[s]
            sv |= v
            sg |= g
            st += surf
        return tiled, marked, sv, sg, set(answer_text) | set(st), answer_text, set(answer_strings)

    def practised(ref: str, P) -> bool:
        tiled, marked, sv, sg, kpool, answer_text, whole = P
        ns = ref.split(":", 1)[0]
        if ns == "vocab":
            return ref in tiled or ref in marked or ref in sv
        if ns == "kanji":
            return KCHAR.get(ref, "\x00") in kpool or ref in marked
        if ns == "gram":
            return ref in marked or ref in sg or any(
                (len(seg) > 1 and seg in answer_text) or (len(seg) == 1 and seg in whole)
                for seg in GPROBES.get(ref, ()))
        return False

    def all_targets(ex: dict) -> set[str]:
        tiled, marked, sv, sg, kpool, answer_text, whole = P = pool([ex])
        out = set(tiled) | marked | sv | sg | {CHAR2K[c] for c in kpool if c in CHAR2K}
        out |= {g for g in GPROBES if practised(g, P)}
        for s in ex.get("sentence_refs") or []:
            out |= sent_idx.get(s, set())
        return out

    # ------------------------------------------------------------------ 1. the ledger
    def harvest(d: dict) -> dict[str, list[dict]]:
        """ref -> spans [{channel, via}], the five derive_needs channels, with the carrying pointer."""
        uses: dict[str, list[dict]] = defaultdict(list)
        body = d.get("body") or ""

        def add(ref: str, ch: str, via: str) -> None:
            if ":" in ref and ref.split(":", 1)[0] in DN.UNLOCK_NS:
                span = {"channel": ch, "via": via}
                if via in bank:
                    span["jp"] = bank[via]["jp"]
                if span not in uses[ref]:
                    uses[ref].append(span)

        for m in DN.ITEM_TAG.finditer(body):
            for ref in DN.ITEM_ATTR.findall(m.group(2)):
                add(ref, "body-chip", f"<{m.group(1)}>")
        for slug in DN.SENT_TAG.findall(body):
            for ref in sent_idx.get(slug, ()):
                add(ref, "body-sentence", slug)
        for slug in d.get("sentence_refs") or []:
            for ref in sent_idx.get(slug, ()):
                add(ref, "lesson-sentence-refs", slug)
        for ex in d.get("exercises") or []:
            for slug in (ex.get("sentence_refs") or []) + ((ex.get("answer") or {}).get("sentence_refs") or []):
                for ref in sent_idx.get(slug, ()):
                    add(ref, "exercise-sentence", slug)
        for slug in DN.READ_TAG.findall(body):
            for ref in read_idx.get(slug, ()):
                add(ref, "body-reading", slug)
        return uses

    def tier_of(L: str, M: str) -> str:
        if topic[L] == topic[M]:
            return "same-topic"
        if level[L] == level[M]:
            return "same-level"
        return "cross-level"

    fwd_rows: list[dict] = []
    for d in lessons:
        L = d["id"]
        for ref, spans in harvest(d).items():
            M = introducer.get(ref)
            if M is None or pos[M] <= pos[L]:
                continue
            fwd_rows.append({"lesson": L, "item": ref, "kind": NS_KIND.get(ref.split(":")[0], ref.split(":")[0]),
                             "teaching_lesson": M, "tier": tier_of(L, M), "use_span": spans})

    payload_before, _ = DN.build(ROOT)
    edges_before = payload_before["forward_edge_defects"]

    def edge_tiers(edges: list[dict]) -> dict[str, int]:
        c: Counter = Counter()
        for e in edges:
            a, b = e["lesson"], e["needs_lesson"]
            c["same-topic" if topic[a] == topic[b] else "same-level" if level[a] == level[b] else "cross-level"] += 1
        return dict(c)

    # ------------------------------------------------------------------ 2. W15 holds + W22 rows
    W15 = [("les:n4-oracoes-relativas-03", "vocab:1215230", "read:n4-oracoes-relativas-03-01", "間 (4 occurrences)",
            "the lesson teaches 〜間 / 〜間に and never unlocks 間"),
           ("les:n3-perspectiva-01", "vocab:1215790", "read:n3-perspectiva-01-01", "関し (関する)",
            "the lesson teaches 〜に関して"),
           ("les:n3-limites-05", "vocab:1610160", "read:n3-limites-05-02", "対し (対する)",
            "the lesson teaches 〜に対して"),
           ("les:n4-keigo-04", "vocab:1456130", "read:n4-keigo-04-01", "読み (お読みになる)",
            "Sudachi reads お読み as prefix + the noun 読み; the lesson teaches the verb 読む")]
    w15_rows = []
    for L, ref, rd, surf, why in W15:
        M = introducer.get(ref)
        w15_rows.append({"lesson": L, "item": ref, "kind": "vocab", "teaching_lesson": M,
                         "tier": tier_of(L, M) if M else "never-unlocked",
                         "use_span": [{"channel": "held-passage (W15)", "via": rd, "surface": surf, "note": why}],
                         "source": "w15-hold", "forward": bool(M and pos[M] > pos[L])})

    w22 = json.loads((REPO / "research/derived/pending/w22_n3_dead_end.json").read_text(encoding="utf-8"))["form_unlocks"]
    w22_rows = []
    for b in w22["built_on_before_named"]:
        row = next(r for r in w22["rows"] if r["form"] == b["form"])
        w22_rows.append({"lesson": b["required_as_base_at"], "item": f"conj:{b['form']}", "kind": "conjugation-form",
                         "teaching_lesson": b["first_taught_at"],
                         "tier": tier_of(b["required_as_base_at"], b["first_taught_at"]),
                         "use_span": [{"channel": "formation_steps (W22 F-a)", "via": row["candidates"]["F-a"]["lesson"],
                                       "evidence": row["candidates"]["F-a"]["evidence"]}],
                         "source": "w22-base-form"})

    def polite_past_hit(slug: str) -> str | None:
        toks = bank.get(slug, {}).get("tokens") or []
        for i in range(len(toks) - 1):
            a, b = toks[i], toks[i + 1]
            if a.get("inflection_type") == "助動詞-マス" and a["surface"] == "まし" and b["surface"] == "た":
                return "mashita"
            if a["surface"] == "ませ" and b["surface"] == "ん" and i + 3 < len(toks) and toks[i + 2]["surface"] == "でし":
                return "masendeshita"
        return None

    pp_first: dict[str, tuple[str, str, str]] = {}
    for d in lessons:
        if level[d["id"]] != "n5" or pos[d["id"]] >= pos["les:n5-revisao-02"]:
            continue
        slugs = set(DN.SENT_TAG.findall(d.get("body") or "")) | set(d.get("sentence_refs") or [])
        for ex in d.get("exercises") or []:
            slugs |= set(ex.get("sentence_refs") or [])
        for s in sorted(slugs):
            f = polite_past_hit(s)
            if f and f not in pp_first:
                pp_first[f] = (d["id"], s, bank[s]["jp"])
            if f == "mashita" and "polite-past" not in pp_first:
                pp_first["polite-past"] = (d["id"], s, bank[s]["jp"])
    for form in ("mashita", "masendeshita", "polite-past"):
        home = next(r for r in w22["rows"] if r["form"] == form)["lesson"]
        if form in pp_first:
            L, s, jp = pp_first[form]
            w22_rows.append({"lesson": L, "item": f"conj:{form}", "kind": "conjugation-form", "teaching_lesson": home,
                             "tier": tier_of(L, home),
                             "use_span": [{"channel": "displayed sentence token (まし+た / ませ+ん+でし+た)",
                                           "via": s, "jp": jp}], "source": "w22-mashita"})
        else:
            w22_rows.append({"lesson": home, "item": f"conj:{form}", "kind": "conjugation-form", "teaching_lesson": home,
                             "tier": "none", "use_span": [], "source": "w22-mashita"})

    # ------------------------------------------------------------------ 3. decide (working state)
    W_unlocks = {lid: [dict(u) for u in (by_id[lid].get("unlocks") or [])] for lid in order}
    W_ex = {lid: [copy.deepcopy(e) for e in (by_id[lid].get("exercises") or [])] for lid in order}
    W_rendered = {lid: set(EX_TAG.findall(by_id[lid].get("body") or "")) for lid in order}
    W_uses = {lid: set(harvest(by_id[lid])) for lid in order}
    intro_pos = {ref: pos[m] for ref, m in introducer.items()}
    POOL_CACHE: dict[str, tuple] = {}

    def lpool(lid: str):
        if lid not in POOL_CACHE:
            POOL_CACHE[lid] = pool(W_ex[lid])
        return POOL_CACHE[lid]

    def teach_refs(lid: str) -> set[str]:
        return {u["ref"] for u in W_unlocks[lid] if u["type"] in TEACHING}

    def has_pair(types: set[str]) -> bool:
        return bool(types & RETRIEVAL and types & PRODUCTION)

    def try_move(I: str, M: str, T: str) -> tuple[bool, str, dict]:
        """Feasibility of moving the unlock of I from M to T on the working state. (ok, reason, effect)."""
        if is_review[T]:
            return False, f"R1: {T} is a review lesson; the review shape carries zero item unlocks (W22)", {}
        mine = teach_refs(M)
        if not is_review[M] and mine - {I} == set():
            return False, (f"R2: {I} is the only item {M} unlocks; moving it leaves the teaching lesson with "
                           f"no unlock or card of its own"), {}
        if utype[I] in CAPABILITY_TYPES and not {r for r in mine - {I} if utype.get(r) in CAPABILITY_TYPES}:
            return False, (f"R7: {I} is the last kanji/grammar/kana unlock of {M}; the capability registry "
                           f"cannot express a vocabulary-only lesson, so {M} would lose its capability "
                           f"(validate_graph_edges capability_coverage)"), {}
        e_I = [e for e in W_ex[M] if practised(I, pool([e]))]
        lost = [e for e in e_I if {r for r in mine if practised(r, pool([e]))} == {I}]
        travel: list[dict] = []
        stay: dict[str, str] = {e["id"]: "shared: also practises other items of the teaching lesson"
                                for e in e_I if e not in lost}
        for e in lost:
            if e["id"] in locked_ex:
                stay[e["id"]] = "addressed by homograph_rulings.json (a replayed practice row)"
                continue
            unknown = sorted(t for t in all_targets(e)
                             if t != I and t in intro_pos and intro_pos[t] > pos[T] and t not in W_uses[T])
            if unknown:
                stay[e["id"]] = f"R4: asks about {unknown[:4]}, which {T} does not know yet"
            else:
                travel.append(e)
        if travel and (mine - {I}) and M not in PEX:
            ids = {e["id"] for e in travel}
            if not has_pair({e["type"] for e in W_ex[M] if e["id"] not in ids and e["id"] in W_rendered[M]}):
                for e in travel:
                    stay[e["id"]] = "R5: the teaching lesson would lose its rendered retrieval+production pair"
                travel = []
        if T not in PEX:
            rt = ({e["type"] for e in W_ex[T] if e["id"] in W_rendered[T]}
                  | {e["type"] for e in travel if e["id"] in W_rendered[M]})
            if not has_pair(rt):
                return False, (f"R6: {T} becomes a teaching lesson but renders no retrieval+production pair "
                               f"(rendered {sorted(rt)})"), {}
        return True, "", {"exercises": sorted(e["id"] for e in travel), "left_behind": stay}

    def apply_move(I: str, M: str, T: str, eff: dict) -> None:
        u = next(x for x in W_unlocks[M] if x["ref"] == I)
        W_unlocks[M].remove(u)
        W_unlocks[T].append(u)
        for eid in eff["exercises"]:
            e = next(x for x in W_ex[M] if x["id"] == eid)
            W_ex[M].remove(e)
            W_ex[T].append(e)
            if eid in W_rendered[M]:
                W_rendered[M].discard(eid)
                W_rendered[T].add(eid)
            for s in (e.get("sentence_refs") or []) + ((e.get("answer") or {}).get("sentence_refs") or []):
                W_uses[T] |= sent_idx.get(s, set())
        intro_pos[I] = pos[T]
        POOL_CACHE.pop(M, None)
        POOL_CACHE.pop(T, None)

    users: dict[str, list[str]] = defaultdict(list)
    for r in fwd_rows + [r for r in w15_rows if r["forward"]]:
        users[r["item"]].append(r["lesson"])
    cand = []
    held_items: dict[str, str] = {}
    for I, Ls in users.items():
        M = introducer[I]
        S = sorted({L for L in Ls if level[L] == level[M]}, key=pos.get)
        if not S:
            continue
        if I in HELD:
            held_items[I] = "C-hold/owner"
            continue
        if (M, I) in locked:
            held_items[I] = "C-hold/table"
            continue
        cand.append((I, M, S))
    cand.sort(key=lambda c: (pos[c[2][0]], pos[c[1]], c[0]))

    moves: dict[str, dict] = {}
    fail_at: dict[tuple[str, str], str] = {}
    home = {I: M for I, M, _ in cand}
    HOPS: list[tuple[str, str, str, dict]] = []
    changed = True
    passes = 0
    while changed:
        changed = False
        passes += 1
        for I, M0, S in cand:
            H = home[I]
            for T in [L for L in S if pos[L] < pos[H]]:
                ok, why, eff = try_move(I, H, T)
                if not ok:
                    fail_at[(I, T)] = why
                    continue
                apply_move(I, H, T, eff)
                mv = moves.setdefault(I, {"item": I, "kind": utype[I], "from": M0, "exercises_moved": [],
                                          "exercises_left_behind": {}, "hops": []})
                mv.update(to=T, tier=tier_of(T, M0), cks_gain_lessons=pos[M0] - pos[T], partial=(T != S[0]))
                mv["exercises_moved"] = sorted(set(mv["exercises_moved"]) | set(eff["exercises"]))
                for k, v in eff["left_behind"].items():
                    mv["exercises_left_behind"].setdefault(k, {"lesson": H, "why": v})
                HOPS.append((I, H, T, eff))
                mv["hops"].append({"from": H, "to": T, "pass": passes, "exercises": eff["exercises"]})
                home[I] = T
                for L in S:
                    if pos[L] >= pos[T]:
                        fail_at.pop((I, L), None)
                changed = True
                break

    # drill at the new home, measured on the FINAL working state (a later move can bring one in)
    for I, mv in moves.items():
        mv["moves_card"] = True          # the card is derived from the unlock by export_course._srs_cards
        mv["drill_at_new_home"] = practised(I, lpool(mv["to"]))
        mv["topic_from"], mv["topic_to"] = topic[mv["from"]], topic[mv["to"]]
    u5 = sorted(({"lesson": mv["to"], "item": I, "kind": mv["kind"], "from": mv["from"],
                  "old_exercises_left_behind": sorted(mv["exercises_left_behind"])}
                 for I, mv in moves.items() if not mv["drill_at_new_home"]),
                key=lambda r: (pos[r["lesson"]], r["item"]))

    # ------------------------------------------------------------------ 4. rows
    def decide(r: dict) -> dict:
        I, L = r["item"], r["lesson"]
        M = r["teaching_lesson"]
        out = {"lesson": L, "item": I, "kind": r["kind"], "tier": r["tier"], "teaching_lesson": M,
               "use_span": r["use_span"][:3], "use_span_count": len(r["use_span"]),
               "source": r.get("source", "ledger")}
        if M is None:
            out.update(decision="rewrite", rule="B-rewrite/never-unlocked",
                       reason="no lesson unlocks this item, so there is no unlock to move; add an unlock (course "
                              "call) or keep the use out")
            return out
        if level[L] != level[M]:
            out.update(decision="hold", rule="C-hold",
                       reason=f"{L} is {level[L]}, the item is taught at {level[M]} ({M}): across levels")
            return out
        if I in held_items:
            out.update(decision="hold", rule=held_items[I],
                       reason=HELD.get(I) or f"{locked.get((M, I))} writes this unlock at {M}")
            return out
        mv = moves.get(I)
        if mv and pos[mv["to"]] <= pos[L]:
            out.update(decision="move", rule="A-move-partial" if mv["partial"] else "A-move",
                       new_unlock_lesson=mv["to"], exercises_moved=mv["exercises_moved"],
                       drill_at_new_home=mv["drill_at_new_home"],
                       cks_delta={"kind": utype[I], "lessons_gaining": mv["cks_gain_lessons"],
                                  "range": [mv["to"], order[pos[M] - 1]], "lessons_shrinking": 0})
            if r["kind"] == "grammar":
                out["review_flag"] = (f"grammar card now precedes its explanation in {M} by "
                                      f"{mv['cks_gain_lessons']} lesson(s)")
            return out
        why = fail_at.get((I, L), "no same-level candidate")
        out.update(decision="rewrite", rule=f"B-rewrite/{why.split(':')[0]}", reason=why, move_tried_to=L)
        if mv:
            out["item_moved_to_later_user"] = mv["to"]
            out["tier_after"] = tier_of(L, mv["to"])
        return out

    rows = [decide(r) for r in fwd_rows]
    w15_out = []
    for r in w15_rows:
        if r["forward"]:
            w15_out.append(decide(r))
        else:
            M = r["teaching_lesson"]
            o = {"lesson": r["lesson"], "item": r["item"], "kind": "vocab", "tier": r["tier"], "teaching_lesson": M,
                 "use_span": r["use_span"], "use_span_count": 1, "source": "w15-hold"}
            if M is None:
                o.update(decision="rewrite", rule="B-rewrite/never-unlocked",
                         reason="no lesson unlocks this word; an unlock must be ADDED (not moved) at the gating "
                                "lesson, or the passage stays selection-era - course call")
            else:
                o.update(decision="none", rule="already-known",
                         reason=f"already unlocked at or before the gating lesson by {M}")
            w15_out.append(o)

    # W22: analytic only. No conj: unlock exists yet (the W22 apply is queued), so these rows confirm the
    # gate-sound home the W22 apply must write; nothing here writes a form unlock.
    w22_out = []
    for r in w22_rows:
        L, M, I = r["lesson"], r["teaching_lesson"], r["item"]
        o = {"lesson": L, "item": I, "kind": "conjugation-form", "tier": r["tier"], "teaching_lesson": M,
             "use_span": r["use_span"], "use_span_count": len(r["use_span"]), "source": r["source"],
             "applies_with": "W22 apply (form unlocks are not in the tree yet)"}
        if L == M:
            o.update(decision="rewrite", rule="B-rewrite/no-earlier-use",
                     reason=("no lesson before the review-lesson home displays the form, so there is no first "
                             "user to move the unlock to. Authoring: a non-review N5 lesson must teach the verb "
                             "past (top:n5-passado teaches only the copula past) - owner/W25"))
        elif is_review[L]:
            o.update(decision="rewrite", rule="B-rewrite/R1", reason=RULES["R1"])
        elif level[L] == level[M]:
            o.update(decision="move", rule="A-move", new_unlock_lesson=L,
                     cks_delta={"kind": "conjugation-form", "lessons_gaining": pos[M] - pos[L],
                                "range": [L, order[pos[M] - 1]], "lessons_shrinking": 0,
                                "relative_to": "W22 teach-true home"},
                     reason=("W22 gate-sound home confirmed: the grammar point is built on the form here"
                             if r["source"] == "w22-base-form" else
                             "first N5 lesson that displays the form; moving the unlock out of the review "
                             "lesson restores the zero-unlock review shape. Authoring debt remains: no "
                             "lesson explains the verb past - owner/W25"))
        else:
            o.update(decision="hold", rule="C-hold", reason="across levels")
        w22_out.append(o)

    all_rows = rows + w15_out + w22_out

    # ------------------------------------------------------------------ 5. simulate on fixture + DB snapshot
    if FX_AFTER.exists():
        shutil.rmtree(FX_AFTER)
    shutil.copytree(FX_BEFORE, FX_AFTER, ignore=shutil.ignore_patterns("__pycache__"))
    fx_lessons = {lid: json.loads((FX_AFTER / rel).read_text(encoding="utf-8")) for lid, rel in lesson_path.items()}
    for I, M, T, eff in HOPS:
        dm, dt = fx_lessons[M], fx_lessons[T]
        u = next(x for x in dm["unlocks"] if x["ref"] == I)
        dm["unlocks"].remove(u)
        dt["unlocks"].append(u)
        cards_m = dm["srs"]["introduces_cards"]
        c = next((x for x in cards_m if x["item"] == I), None)
        if c:
            cards_m.remove(c)
            dt["srs"].setdefault("introduces_cards", []).append(c)
        for eid in eff["exercises"]:
            e = next(x for x in dm["exercises"] if x["id"] == eid)
            dm["exercises"].remove(e)
            dt["exercises"].append(e)
            tag = f'<exercise ref="{eid}"/>'
            if tag in dm["body"]:
                dm["body"] = dm["body"].replace(tag, "", 1)
                i = dt["body"].rfind("<checklist>")
                dt["body"] = dt["body"][:i] + tag + dt["body"][i:] if i >= 0 else dt["body"] + tag

    run_ = {k: set() for k in KINDS}
    shrinks, grows = [], Counter()
    for lid in order:
        d = fx_lessons[lid]
        for u in d["unlocks"]:
            if u["type"] in run_:
                run_[u["type"]].add(u["ref"])
        old = by_id[lid]["cumulative_known_set"]
        new = {k: sorted(run_[k]) for k in KINDS}
        for k in KINDS:
            o, n = set(old.get(k) or []), set(new[k])
            if o - n:
                shrinks.append((lid, k, sorted(o - n)[:3]))
            if n - o:
                grows[k] += len(n - o)
        d["cumulative_known_set"] = new
    for lid, rel in lesson_path.items():
        (FX_AFTER / rel).write_text(json.dumps(fx_lessons[lid], ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    gex_path = FX_AFTER / "course/gating_exemptions.json"
    gex = json.loads(gex_path.read_text(encoding="utf-8"))
    gex_dropped, keep = [], []
    for e in gex.get("item_refs") or []:
        kind = NS_KIND.get(e["ref"].split(":", 1)[0])
        if kind and e["ref"] in set(fx_lessons[e["lesson"]]["cumulative_known_set"].get(kind) or []):
            gex_dropped.append(f"{e['lesson']} / {e['ref']}")
        else:
            keep.append(e)
    gex["item_refs"] = keep
    gex_path.write_text(json.dumps(gex, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    table = BNT.build(FX_AFTER)
    need_rows = defaultdict(list)
    for r in table["rows"]:
        need_rows[r["lesson"]].append({"type": "lesson", "ref": r["ref"], "note": r["note"]})
    for lid, rel in lesson_path.items():
        fx_lessons[lid]["needs"] = need_rows.get(lid, [])
        (FX_AFTER / rel).write_text(json.dumps(fx_lessons[lid], ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    rex_path = FX_AFTER / "course/needs_root_exemptions.json"
    rex = json.loads(rex_path.read_text(encoding="utf-8"))
    rootless_after = [lid for lid in order if not need_rows.get(lid) and lid != order[0]]
    held_before = [e["lesson"] for e in rex["lessons"]]
    rex["lessons"] = [e for e in rex["lessons"] if e["lesson"] in rootless_after]
    rex["count"] = len(rex["lessons"])
    rex_path.write_text(json.dumps(rex, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    payload_after, _ = DN.build(FX_AFTER)
    edges_after = payload_after["forward_edge_defects"]
    intro_after: dict[str, str] = {}
    for lid in order:
        for u in fx_lessons[lid]["unlocks"]:
            intro_after.setdefault(u["ref"], lid)
    uses_after: Counter = Counter()
    pairs_after = set()
    for lid in order:
        for ref in harvest(fx_lessons[lid]):
            M2 = intro_after.get(ref)
            if M2 and pos[M2] > pos[lid]:
                uses_after[tier_of(lid, M2)] += 1
                pairs_after.add((lid, ref))
    new_pairs = sorted(pairs_after - {(r["lesson"], r["item"]) for r in fwd_rows})

    def run_validators(root: Path) -> dict[str, str]:
        out = {}
        for name, extra in VALIDATORS:
            p = subprocess.run([sys.executable, str(root / "scripts/validate" / name), "--root", str(root), *extra],
                               capture_output=True, text=True, encoding="utf-8")
            tail = [ln for ln in p.stdout.strip().splitlines() if ln.strip()][-1:] or [p.stderr.strip()[-300:]]
            out[name] = f"exit {p.returncode} | {tail[0][:400]}"
            (work / f"val_{root.name}_{name}.txt").write_text(p.stdout + "\n" + p.stderr, encoding="utf-8")
        return out

    val_before = run_validators(FX_BEFORE)
    val_after = run_validators(FX_AFTER)

    # DB snapshot: find each move's stored ref, move it, check no running union shrinks
    db = sqlite3.connect(SNAP)
    les_db = {slug: i for i, slug in db.execute("SELECT id, slug FROM lesson")}
    vrow = {s: (h, i) for s, h, i in db.execute("SELECT slug, headword, id FROM vocab")}

    def db_unions() -> dict[str, dict[str, set[str]]]:
        acc = {k: set() for k in KINDS}
        out = {}
        for lid in order:
            for t, r in db.execute("SELECT unlock_type, ref FROM lesson_unlocks WHERE lesson_id=?", (les_db[lid],)):
                if t in acc:
                    acc[t].add(r)
            out[lid] = {k: set(v) for k, v in acc.items()}
        return out

    db_before = db_unions()
    db_unmapped = []
    for mv in moves.values():
        I, M, T = mv["item"], mv["from"], mv["to"]
        cands = {I}
        if I.startswith("vocab:") and I in vrow:
            cands |= {f"vocab:{vrow[I][0]}", f"vocab:{vrow[I][1]}"}
        have = [r for (r,) in db.execute("SELECT ref FROM lesson_unlocks WHERE lesson_id=? AND unlock_type=?",
                                         (les_db[M], mv["kind"])) if r in cands]
        if len(have) != 1:
            db_unmapped.append((I, M, have))
            continue
        mv["db_ref"] = have[0]
        # An AMBIGUOUS headword ref would be re-resolved at the new home, and the resolver's
        # introducing_topic tier reads a placement a rebuild does not reproduce (å¹´ went to its
        # sibling in a replay). The new home therefore gets the published slug: exact in every tier.
        # T's body has no chip for the item (check B would have failed), so the sibling filter the
        # slug feeds only confirms what T's chips for the OTHER sibling already meant.
        mv["ref_at_new_home"] = have[0]
        if I.startswith("vocab:") and have[0] != I and                 db.execute("SELECT COUNT(*) FROM vocab WHERE headword=?", (vrow[I][0],)).fetchone()[0] > 1:
            mv["ref_at_new_home"] = I
        db.execute("UPDATE lesson_unlocks SET lesson_id=? WHERE lesson_id=? AND unlock_type=? AND ref=?",
                   (les_db[T], les_db[M], mv["kind"], have[0]))
    db_after = db_unions()
    db_shrinks = [(lid, k) for lid in order for k in KINDS if db_before[lid][k] - db_after[lid][k]]
    db_gains = sum(len(db_after[lid][k] - db_before[lid][k]) for lid in order for k in KINDS)
    db.rollback()
    db.close()

    # ------------------------------------------------------------------ 6. write the table
    dec_counts = Counter(r["decision"] for r in all_rows)
    by_tier_dec = Counter((r["tier"], r["decision"]) for r in rows)
    by_kind_dec = Counter((r["kind"], r["decision"]) for r in rows)
    doc = {
        "schema_version": 2,
        "unit": "W21b",
        "status": "derived; apply with scripts/apply_forward_refs.py (reads `rows`)",
        "generated_by": "scripts/derive_forward_refs.py (frozen fixture copy of the tree; DB via sqlite backup)",
        "rulings": {"exercise_stays_behind": "APP_PLAN W21b (1), 2026-09-23", "held": HELD,
                    "locked_tables": list(LOCKED_TABLES)},
        "definition": ("A forward use is (lesson L, item I) where L references I through one of derive_needs.py's five "
                       "channels (body chip, body sentence, lesson sentence_refs, exercise sentence_refs, body reading "
                       "`uses`) and the lesson that unlocks I sits LATER in course order."),
        "rules": RULES,
        "counts": {
            "forward_uses_ledger": len(rows),
            "forward_uses_by_kind": dict(Counter(r["kind"] for r in rows)),
            "forward_uses_by_tier": dict(Counter(r["tier"] for r in rows)),
            "forward_edges_before": len(edges_before),
            "forward_edges_before_by_tier": edge_tiers(edges_before),
            "w15_rows": len(w15_out), "w22_rows": len(w22_out),
            "decisions_all_rows": dict(dec_counts),
            "decisions_ledger_by_tier": {f"{a}/{b}": n for (a, b), n in sorted(by_tier_dec.items())},
            "decisions_ledger_by_kind": {f"{a}/{b}": n for (a, b), n in sorted(by_kind_dec.items())},
            "rules": dict(Counter(r["rule"] for r in all_rows)),
            "moves": len(moves), "moves_by_kind": dict(Counter(m["kind"] for m in moves.values())),
            "moves_partial": sum(1 for m in moves.values() if m["partial"]),
            "moves_multi_hop": sum(1 for m in moves.values() if len(m["hops"]) > 1),
            "moves_with_exercise": sum(1 for m in moves.values() if m["exercises_moved"]),
            "exercises_moved": sum(len(m["exercises_moved"]) for m in moves.values()),
            "exercises_left_behind": sum(len(m["exercises_left_behind"]) for m in moves.values()),
            "moves_without_drill_at_new_home": len(u5),
            "moves_without_drill_by_kind": dict(Counter(r["kind"] for r in u5)),
            "held_items": held_items,
            "decision_passes": passes,
        },
        "simulation": {
            "cks_shrinks_fixture": shrinks, "cks_item_gains_fixture": dict(grows),
            "forward_edges_after": len(edges_after),
            "forward_edges_after_by_tier": edge_tiers(edges_after),
            "forward_uses_after_by_tier": dict(uses_after),
            "forward_uses_created_by_moves": new_pairs,
            "move_rows_still_forward": sorted((r["lesson"], r["item"]) for r in rows
                                              if r["decision"] == "move" and (r["lesson"], r["item"]) in pairs_after),
            "needs_rows_after": table["counts"],
            "rootless_after": len(rootless_after), "rootless_held_before": len(held_before),
            "root_exemptions_dropped": sorted(set(held_before) - set(rootless_after)),
            "new_rootless": sorted(set(rootless_after) - set(held_before)),
            "validators_before": val_before, "validators_after": val_after,
            "gating_exemptions_dropped": gex_dropped,
            "db_snapshot": {"unlock_rows_moved": len(moves) - len(db_unmapped), "unmapped": db_unmapped,
                            "running_union_shrinks": db_shrinks, "running_union_item_gains": db_gains},
        },
        "u5_drills": u5,
        "row_count": len(moves),
        # `rows` are the MOVES (what apply_forward_refs.py writes and validate_repairs_applied replays);
        # `ledger` is every forward use with its decision, the authoring / re-selection work list.
        "rows": sorted(moves.values(), key=lambda m: (pos[m["to"]], m["item"])),
        "ledger": sorted(all_rows, key=lambda r: (r["source"] != "ledger", pos.get(r["lesson"], 0), r["item"])),
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(doc, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(json.dumps({"counts": doc["counts"],
                      "simulation": {k: v for k, v in doc["simulation"].items() if k != "cks_shrinks_fixture"}},
                     ensure_ascii=False, indent=1))
    print(f"cks shrinks: {len(shrinks)}; wrote {OUT}")
    return 1 if (shrinks or db_shrinks or db_unmapped or new_pairs) else 0


if __name__ == "__main__":
    sys.exit(main())
