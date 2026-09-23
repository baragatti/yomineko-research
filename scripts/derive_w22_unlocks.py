#!/usr/bin/env python3
"""W22 re-derivation: feature home lessons (§2) and conjugation-form unlocks (§4) over a published tree.

The W22 derivation of 2026-09-10 (`research/reports/w22_derivation_report.md`) was computed by a
scratch script that was never landed, and the tree has moved since (W21b moved 276 unlocks,
including the grammar points that required 7 forms as a base; W14 re-selected lesson sentences).
This script re-states the same rules over whatever `course/` + `corpus/` it is pointed at, so the
apply table is always a function of the tree it lands on and a later unit can re-run it.

  §2 H1  the home of a never-unlocked feature is the FIRST lesson in course order whose own
         published JSON uses it (one detector per feature, below).
  §4 F   for each conjugation form, four candidate lessons, take the EARLIEST (ties a<b<c<d):
         F-a  a grammar point unlocked here is BUILT ON the form (`formation_steps` op `to-<form>`)
         F-b  a grammar point unlocked here IS the form (`form_anchor_table` vs `structure_pattern`)
         F-c  the body prints, inside <jp>, the conjugation-bank surface of the form for >=3
              distinct surfaces of the lesson's own cks words (or >=2 inside its exercise answer
              keys), maximal-match guarded across words (遊べ inside 遊べば and ある's ない inside
              来ない do not count); an answer key that IS a bare headword is a vocabulary drill and
              is not evidence for the dictionary form. Counting surfaces rather than records keeps
              homograph siblings (いい/良い -> one よければ) from counting twice. These three
              tightenings were added on 2026-09-23 when the W20 drills put headwords into answer
              keys; on the 2026-09-10 tree they reproduce all 25 homes of the original derivation.
         F-d  the lesson's own pt-BR title/description/objectives cite the form
§3 re-reads the review blocks' contents (lesson counts, grammar refs, the core anchor of each
topic's `grp:gram-<topic>` family) for the authoring brief; the block partition itself is the
recorded, owner-overridable choice.
The rule tables (`form_anchor_table`, `metadata_marker_table`, `bank_form_to_enum`,
`formation_op_to_enum`) are read from the W22 table itself, so a validator replays the same rules.

Usage: derive_w22_unlocks.py [--root DIR] [--rules TABLE] [--out FILE] [--check]
Writes nothing unless --out is given; --check fails when the tracked table has drifted.
"""
from __future__ import annotations

import argparse
import glob
import json
import re
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]

REPO = Path(__file__).resolve().parents[1]
DEFAULT_RULES = REPO / "research" / "derived" / "repairs" / "w22_n3_dead_end.json"
LOC = "pt-BR"
CHANNELS = ("F-a", "F-b", "F-c", "F-d")
JP_SPAN = re.compile(r"<jp\b[^>]*>(.*?)</jp>", re.S)
TAG = re.compile(r"<[^>]+>")
KANJI = re.compile(r"[一-鿿]")
KANA_ONLY = re.compile(r"^[぀-ヿー]+$")


def load_lessons(root: Path) -> list[dict]:
    out = []
    for f in glob.glob(str(root / "course" / "*" / "topic-*" / "lesson-*.json")):
        rec = json.loads(Path(f).read_text(encoding="utf-8"))
        rec["_tord"] = int(Path(f).parent.name.split("-")[1])
        out.append(rec)
    out.sort(key=lambda r: (r["_tord"], r["order"]))
    return out


def load_list(path: str) -> list[dict]:
    doc = json.loads(Path(path).read_text(encoding="utf-8"))
    return doc if isinstance(doc, list) else next(v for v in doc.values() if isinstance(v, list))


def ops(node) -> list[str]:
    if isinstance(node, dict):
        return ([node["op"]] if isinstance(node.get("op"), str) else []) + \
            [o for v in node.values() for o in ops(v)]
    if isinstance(node, list):
        return [o for v in node for o in ops(v)]
    return []


def answer_strings(ans) -> list[str]:
    if not isinstance(ans, dict):
        return []
    out = []
    for k in ("correct", "text", "full"):
        if isinstance(ans.get(k), str):
            out.append(ans[k])
    out += [a for a in ans.get("accept") or [] if isinstance(a, str)]
    return out


def guarded_hits(text: str, smap: dict[str, set[str]], maxlen: int) -> set[tuple[str, str]]:
    """(form, surface) pairs printed in `text`, maximal-match guarded: an occurrence covered by a
    strictly longer bank surface of ANY cks word is not counted (遊べ inside 遊べば; ある's ない
    inside 来ない)."""
    occ = [(p, p + n) for p in range(len(text)) for n in range(1, min(maxlen, len(text) - p) + 1)
           if text[p:p + n] in smap]
    hits = set()
    for a, b in occ:
        if any(c <= a and d >= b and d - c > b - a for c, d in occ):
            continue
        s = text[a:b]
        hits |= {(f, s) for f in smap[s]}
    return hits


def meta_text(L: dict) -> str:
    parts = [(L.get("title") or {}).get(LOC) or "", (L.get("description") or {}).get(LOC) or ""]
    parts += [(o or {}).get(LOC) or "" for o in L.get("objectives") or []]
    return "\n".join(parts)


def derive(root: Path, rules: dict) -> dict:
    fu = rules["form_unlocks"]
    anchors = {f: [re.compile(p) for p in ps] for f, ps in fu["form_anchor_table"].items()}
    markers = {f: [re.compile(p) for p in ps] for f, ps in fu["metadata_marker_table"].items()}
    bank2enum: dict[str, str] = fu["bank_form_to_enum"]
    op2enum: dict[str, str] = fu["formation_op_to_enum"]
    # every form any rule table names (the enum's 20 plus the six the bank forces)
    forms = sorted(set(op2enum.values()) | set(bank2enum.values()) | set(anchors) | set(markers))

    lessons = load_lessons(root)
    idx = {L["id"]: i for i, L in enumerate(lessons)}
    gram = {g["slug"]: g for f in glob.glob(str(root / "corpus" / "grammar" / "n*.json"))
            for g in load_list(f)}
    bank = {}
    for f in glob.glob(str(root / "corpus" / "conjugations" / "n*.json")):
        for e in load_list(f):
            bank[e["slug"]] = [(bank2enum[c["form"]], c["surface"]) for c in e["conjugations"]
                               if c["form"] in bank2enum]

    cand: dict[str, dict[str, dict]] = {}

    def offer(form: str, ch: str, i: int, evidence: str) -> None:
        cur = cand.setdefault(form, {}).get(ch)
        if cur is None or i < cur["course_index"]:
            L = lessons[i]
            cand[form][ch] = {"course_index": i, "lesson": L["id"], "topic": L["topic"],
                              "evidence": evidence}

    for i, L in enumerate(lessons):
        for u in L.get("unlocks") or []:
            if u["type"] != "grammar" or u["ref"] not in gram:
                continue
            g = gram[u["ref"]]
            for op in dict.fromkeys(ops(g.get("formation_steps"))):
                if op in op2enum:
                    offer(op2enum[op], "F-a", i, f"grammar `{u['ref']}` is BUILT ON this form "
                                                  f"(formation_steps op `{op}`)")
            sp = g.get("structure_pattern") or ""
            for form, pats in anchors.items():
                if any(p.search(sp) for p in pats):
                    offer(form, "F-b", i, f"grammar `{u['ref']}` IS this form (structure_pattern "
                                          f"{sp} matched the form_anchor_table)")
        # surface -> forms, over the lesson's own cks words. Counting DISTINCT SURFACES (not
        # records) keeps homograph siblings (いい/良い -> one よければ) from counting twice.
        smap: dict[str, set[str]] = {}
        for w in (L.get("cumulative_known_set") or {}).get("vocab") or []:
            for form, s in bank.get(w, ()):
                if s:
                    smap.setdefault(s, set()).add(form)
        maxlen = max(map(len, smap), default=0)
        spans = [TAG.sub("", s) for s in JP_SPAN.findall(L.get("body") or "")]
        keys = [s for e in L.get("exercises") or [] for s in answer_strings(e.get("answer"))]
        body_hits: dict[str, set[str]] = {}
        key_hits: dict[str, set[str]] = {}
        for sp in spans:
            for form, s in guarded_hits(sp, smap, maxlen):
                body_hits.setdefault(form, set()).add(s)
        for k in keys:
            for form, s in guarded_hits(k, smap, maxlen):
                # a key that IS a bare headword is a vocabulary drill, not a form
                if not (form == "dictionary" and k.strip().rstrip("。") == s):
                    key_hits.setdefault(form, set()).add(s)
        for form in set(body_hits) | set(key_hits):
            b, k = sorted(body_hits.get(form, ())), sorted(key_hits.get(form, ()))
            if len(b) >= 3 or len(k) >= 2:
                offer(form, "F-c", i, f"conjugation-bank surfaces printed: {len(b)} distinct in "
                                      f"<jp> spans ({', '.join(b[:4])}), {len(k)} in answer keys "
                                      f"({', '.join(k[:4])})")
        mt = meta_text(L)
        for form, pats in markers.items():
            m = next((p.search(mt) for p in pats if p.search(mt)), None)
            if m:
                offer(form, "F-d", i, f"the lesson's own pt-BR metadata cites the form "
                                      f"({m.group(0)!r})")

    rows, residue = [], []
    for form in forms:
        c = cand.get(form, {})
        if not c:
            residue.append({"form": form, "ref": f"conj:{form}", "rule": "F-residue"})
            continue
        ch = min(c, key=lambda k: (c[k]["course_index"], CHANNELS.index(k)))
        teach = [k for k in ("F-b", "F-c", "F-d") if k in c]
        tt = min(teach, key=lambda k: (c[k]["course_index"], CHANNELS.index(k))) if teach else None
        rows.append({"form": form, "ref": f"conj:{form}", "lesson": c[ch]["lesson"],
                     "topic": c[ch]["topic"], "course_index": c[ch]["course_index"], "rule": ch,
                     "evidence": c[ch]["evidence"],
                     "home_teach_true": c[tt]["lesson"] if tt else None,
                     "home_teach_true_rule": tt,
                     "candidates": {k: c[k] for k in CHANNELS if k in c}})
    rows.sort(key=lambda r: (r["course_index"], r["form"]))

    # drills: reachable = some lesson's cks holds both the word and the form
    home_idx = {r["form"]: r["course_index"] for r in rows}
    first_word: dict[str, int] = {}
    for i, L in enumerate(lessons):
        for w in (L.get("cumulative_known_set") or {}).get("vocab") or []:
            first_word.setdefault(w, i)
    drills = [d for f in glob.glob(str(root / "corpus" / "exercises" / "conjugation" / "*.json"))
              for d in load_list(f)]
    today_forms = {f for L in lessons for f in
                   ((L.get("cumulative_known_set") or {}).get("conjugation-form") or [])}
    reach_after = reach_before = by_form = unmapped = 0
    per_form: dict[str, int] = {}
    for d in drills:
        form = bank2enum.get(d["form"])
        if form is None:
            unmapped += 1
            continue
        per_form[form] = per_form.get(form, 0) + 1
        w = first_word.get(d["slug"])
        if w is not None and f"conj:{form}" in today_forms:
            reach_before += 1
        if w is not None and form in home_idx:
            reach_after += 1
            by_form += home_idx[form] > w
    for r in rows:
        r["drill_items"] = per_form.get(r["form"], 0)

    homes = derive_homes(root, lessons)
    review = derive_review(root, lessons, rules["review_topic"])
    return {"lessons": len(lessons), "rows": rows, "residue": residue, "homes": homes,
            "review": review,
            "drills": {"total": len(drills), "unmapped_form": unmapped,
                       "reachable_today": reach_before, "reachable_after": reach_after,
                       "gated_by_form_not_word": by_form}}


# --- §3 review blocks -----------------------------------------------------------------------------
def derive_review(root: Path, lessons: list[dict], rt: dict) -> list[dict]:
    """The block partition is the owner-overridable choice recorded in the table; the CONTENTS of
    each block (lesson counts, grammar re-tested, the core anchor of each topic's grammar family)
    are re-read from the tree so the authoring brief never cites a stale or malformed ref."""
    fam = {f["slug"]: f for f in load_list(str(root / "corpus" / "families" / "families.json"))}
    gram = {g["slug"] for f in glob.glob(str(root / "corpus" / "grammar" / "n*.json"))
            for g in load_list(f)}
    out = []
    for blk in rt["lessons"]:
        counts, refs, anchors = [], [], []
        for t in blk["retest_topics"]:
            ls = [L for L in lessons if L["topic"] == t]
            counts.append(len(ls))
            refs += [u["ref"] for L in ls for u in L.get("unlocks") or [] if u["type"] == "grammar"]
            f = fam.get("grp:gram-" + t.split(":", 1)[1]) or {}
            core = [m["slug"] for m in f.get("members") or [] if m.get("is_core")]
            anchors.append(core[0] if core else None)
        plan = []
        for p in blk["exercise_plan"]:
            ti = blk["retest_topics"].index(p["target_topic"])
            plan.append({**p, "target_ref": anchors[ti],
                         "target_exists": anchors[ti] in gram})
        out.append({"id": blk["id"], "retest_topics": blk["retest_topics"],
                    "retest_topic_lesson_counts": counts, "retest_grammar_count": len(refs),
                    "retest_grammar_refs": refs, "retest_grammar_anchor_refs": anchors,
                    "exercise_plan": plan,
                    "anchors_resolve": all(a in gram for a in anchors),
                    "refs_resolve": all(r in gram for r in refs)})
    return out


# --- §2 detectors -------------------------------------------------------------------------------
def derive_homes(root: Path, lessons: list[dict]) -> dict[str, dict]:
    fam = load_list(str(root / "corpus" / "families" / "families.json"))
    core = {m["slug"] for f in fam if f.get("slug") == "grp:particles-core"
            for m in f.get("members") or []}

    def mcq_kanji(e: dict) -> bool:
        ch = (e.get("answer") or {}).get("choices") or []
        return bool(ch) and all(isinstance(c, str) and len(c) == 1 and KANJI.match(c) for c in ch)

    def first_ex(L: dict, pred) -> str | None:
        return next((e["id"] for e in L.get("exercises") or [] if pred(e)), None)

    def first_match(rx: str, text: str) -> str | None:
        m = re.search(rx, text or "", re.S)
        return m.group(0) if m else None

    # each detector returns the evidence that fired (a span, an exercise id, the refs) or None
    det = {
        "feat:romaji-toggle": ("a <romaji> element in the body",
                               lambda L: first_match(r"<romaji>.*?</romaji>", L.get("body"))),
        "feat:furigana-toggle": ("a <jp reading> span over a kanji base",
                                 lambda L: first_match(r'<jp\b[^>]*\breading="[^"]+"[^>]*>[^<]*'
                                                       r'[一-鿿][^<]*</jp>', L.get("body"))),
        "feat:kana-input": ("a production exercise whose answer key is kana-only",
                            lambda L: first_ex(L, lambda e: e["type"] == "production" and bool(
                                KANA_ONLY.match((e.get("answer") or {}).get("text") or "")))),
        "feat:find-correct-particle": ("a particle_choice exercise",
                                       lambda L: first_ex(L, lambda e: e["type"] == "particle_choice")),
        "feat:phrase-builder": ("a sentence_build exercise",
                                lambda L: first_ex(L, lambda e: e["type"] == "sentence_build")),
        "feat:particle-drill": ("the cks holds >=2 members of grp:particles-core",
                                lambda L: (lambda s: ", ".join(sorted(s)) if len(s) >= 2 else None)(
                                    core & set((L.get("cumulative_known_set") or {}).get("grammar")
                                               or []))),
        "feat:kanji-lookup": ("a <kanji ref> chip",
                              lambda L: first_match(r'<kanji ref="[^"]+"', L.get("body"))),
        "feat:find-correct-kanji": ("an MCQ whose choices are all single kanji",
                                    lambda L: first_ex(L, mcq_kanji)),
        "feat:handwriting-input": ("a <stroke ref> element (stroke-order DISPLAY; 0 handwriting "
                                   "exercises exist)",
                                   lambda L: first_match(r'<stroke ref="[^"]+"', L.get("body"))),
    }
    out = {}
    for feat, (desc, fn) in det.items():
        hit = next(((i, s) for i, L in enumerate(lessons) for s in [fn(L)] if s), None)
        out[feat] = {"lesson": lessons[hit[0]]["id"] if hit else None,
                     "topic": lessons[hit[0]]["topic"] if hit else None,
                     "course_index": hit[0] if hit else None, "detector": desc,
                     "evidence": hit[1] if hit else None}
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", type=Path, default=REPO)
    ap.add_argument("--rules", type=Path, default=DEFAULT_RULES)
    ap.add_argument("--out", type=Path)
    ap.add_argument("--check", action="store_true",
                    help="exit 1 if the §2/§4 rows of --rules differ from the re-derivation")
    a = ap.parse_args()
    res = derive(a.root.resolve(), json.loads(a.rules.read_text(encoding="utf-8")))
    print(f"{res['lessons']} lessons; {len(res['rows'])} forms homed, residue "
          f"{[r['form'] for r in res['residue']]}; drills {res['drills']}")
    for r in res["rows"]:
        print(f"  {r['form']:18} {r['lesson']:30} {r['rule']}  idx {r['course_index']:3}  "
              f"teach-true {r['home_teach_true']}")
    for f, h in res["homes"].items():
        print(f"  {f:28} {h['lesson']} (idx {h['course_index']})")
    if a.out:
        a.out.write_text(json.dumps(res, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    if a.check:
        # the tracked table must still be what the rules say on this tree
        table = {(r["ref"], r["lesson"]) for r in json.loads(a.rules.read_text(encoding="utf-8"))["rows"]
                 if r["section"] in ("home_lessons", "form_unlocks")}
        derived = {(r["ref"], r["lesson"]) for r in res["rows"]} | \
            {(f, h["lesson"]) for f, h in res["homes"].items()}
        if table != derived:
            print(f"DRIFT: table-only {sorted(table - derived)} / derived-only {sorted(derived - table)}")
            return 1
        print(f"table matches the re-derivation ({len(table)} rows)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
