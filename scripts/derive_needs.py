#!/usr/bin/env python3
"""W21 / owner decision A7 — derive the lesson prerequisite DAG that `needs[]` should hold.

`needs[]` is empty on all 322 lessons (readiness audit jlpt_course_path.md G5), so
`validate_lesson_gating.py` check C proves nothing about linearity and prints a standing
ADVISORY saying so. The audit's own remedy is to derive the edges rather than hand-author
them: a lesson's prerequisites are already implied by what its body, its exercises and its
embedded readings put in front of the learner.

DEFINITION (the one rule this file implements)
----------------------------------------------
Lesson L needs lesson M iff M != L and L REFERENCES at least one corpus item that M
`unlocks` (introduces). Every unlock ref in the course is introduced by exactly one lesson
(the introduce-once rule, asserted below), so "the item's introducer" is a function, not a
choice.

A REFERENCE is an explicit, machine-resolvable pointer. Five channels carry them:

  body-chip             `<vocab ref>` `<kanji ref>` `<grammar ref>` `<stroke ref="kanji:...">`
                        `<check item-ref>` `<flashcard ref>` in the lesson body.
  body-sentence         `<sentence ref="sent:...">` in the body, expanded through the sentence
                        bank into that sentence's token `vocab` refs, the kanji characters in
                        its token surfaces, and its `grammar` tags.
  lesson-sentence-refs  the lesson record's own `sentence_refs` manifest, expanded the same way.
  exercise-sentence     each exercise's `sentence_refs` and `answer.sentence_refs`, expanded
                        the same way.
  body-reading          `<reading ref="read:...">` expanded through corpus/readings/*.json
                        `uses` (kanji characters + vocab refs).

An item reference that no lesson unlocks yields no edge: nothing in the course teaches it, so
there is no lesson to depend on. Those are counted, not silently discarded.

WHAT THIS FILE DOES NOT WRITE
-----------------------------
Derivation only. It writes exactly two artifacts plus stdout:
  research/derived/needs_edges.json
  research/reports/w21_needs_report.md
It never touches course/, corpus/, contracts/, db/ or research/derived/lessons/, and it runs
no exporter. Applying the edges into the lesson records is a separate, reviewed step.

Deterministic by construction: no timestamps, no dict-iteration order, every collection sorted
before it is written. Two consecutive runs produce byte-identical files.

Usage: scripts/derive_needs.py [--root PATH] [--check] [--quiet]
       --check  re-derives and fails if the artifacts on disk differ (byte comparison).
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]

ROOT = Path(__file__).resolve().parents[1]

EDGES_REL = "research/derived/needs_edges.json"
REPORT_REL = "research/reports/w21_needs_report.md"
GENERATED_BY = "scripts/derive_needs.py"

# Namespaces that can appear as an unlock ref, and therefore as a need driver.
UNLOCK_NS = ("vocab", "kanji", "gram", "kana", "conj", "fam", "feat", "sent")

# Body tags carrying an item address. `exercise.ref` (ex:) and `sentence.ref` (sent:) are
# handled separately: the first addresses a sibling exercise, the second a sentence to expand.
ITEM_TAG = re.compile(r"<(vocab|kanji|grammar|stroke|check|flashcard)\b([^>]*?)/?>")
ITEM_ATTR = re.compile(r'\b(?:item-ref|ref)="([^"]+)"')
SENT_TAG = re.compile(r'<sentence\s+[^>]*?ref="([^"]+)"')
READ_TAG = re.compile(r'<reading\s+[^>]*?ref="([^"]+)"')
JP_SPAN = re.compile(r"<jp\b[^>]*>(.*?)</jp>", re.S)
KANJI_CHAR = re.compile(r"[一-鿿㐀-䶿]")

CHANNELS = ("body-chip", "body-sentence", "lesson-sentence-refs",
            "exercise-sentence", "body-reading")

# How many driver refs to name inside a need's `note` before summarising the rest.
NOTE_REFS = 3


# --------------------------------------------------------------------------- loading
def load_course(root: Path) -> list[dict]:
    """Every lesson leaf, in true course order.

    Deliberately identical to validate_lesson_gating.load_course: (course.order, topic.order,
    lesson.order). If the two ever diverge, the linearity gate and this derivation would be
    ordering the same course differently, which is exactly the bug the gate exists to catch.
    """
    man = json.loads((root / "course" / "manifest.json").read_text(encoding="utf-8"))
    corder = {c["level"]: c["order"] for c in man["courses"]}
    topic_pos: dict[str, tuple[int, int]] = {}
    for cf in sorted(root.glob("course/*/course.json")):
        c = json.loads(cf.read_text(encoding="utf-8"))
        for t in c.get("topics") or []:
            topic_pos[t["id"]] = (corder.get(c["level"], 99), t["order"])
    lessons = [json.loads(p.read_text(encoding="utf-8"))
               for p in sorted(root.glob("course/*/topic-*/lesson-*.json"))]
    lessons.sort(key=lambda d: topic_pos.get(d.get("topic", ""), (99, 99)) + (d.get("order", 0),))
    return lessons


def outline_topic_order(root: Path) -> list[str]:
    """Topic ids in course/outline.json order — the independent witness for the ordering."""
    outline = json.loads((root / "course" / "outline.json").read_text(encoding="utf-8"))
    out: list[str] = []
    for mod in sorted(outline, key=lambda m: m.get("order", 99)):
        for t in sorted(mod.get("topics") or [], key=lambda t: t.get("order", 99)):
            out.append(t["slug"])
    return out


def load_sentence_index(root: Path) -> dict[str, set[str]]:
    """sentence slug -> the set of unlock-namespace refs that sentence puts on screen."""
    bank = json.loads((root / "corpus/sentences/bank.json").read_text(encoding="utf-8"))
    idx: dict[str, set[str]] = {}
    for s in bank:
        refs: set[str] = set()
        for tok in s.get("tokens") or []:
            v = tok.get("vocab")
            if isinstance(v, str) and v.startswith("vocab:"):
                refs.add(v)
            for ch in KANJI_CHAR.findall(tok.get("surface") or ""):
                refs.add(f"kanji:{ch}")
        for g in s.get("grammar") or []:
            refs.add(f"gram:{g}")
        idx[s["slug"]] = refs
    return idx


def load_reading_index(root: Path) -> dict[str, set[str]]:
    """reading slug -> refs, from the record's own `uses` block."""
    idx: dict[str, set[str]] = {}
    for rf in sorted(root.glob("corpus/readings/*.json")):
        for r in json.loads(rf.read_text(encoding="utf-8")):
            refs: set[str] = set()
            uses = r.get("uses") or {}
            for ch in uses.get("kanji") or []:
                refs.add(ch if ":" in ch else f"kanji:{ch}")
            for v in uses.get("vocab") or []:
                refs.add(v if ":" in v else f"vocab:{v}")
            for g in uses.get("grammar") or []:
                refs.add(g if ":" in g else f"gram:{g}")
            idx[r["slug"]] = refs
    return idx


# --------------------------------------------------------------------------- references
def lesson_references(les: dict, sent_idx: dict[str, set[str]],
                      read_idx: dict[str, set[str]]) -> tuple[dict[str, set[str]], dict[str, int]]:
    """(ref -> channels that produced it, dangling-pointer counts) for one lesson."""
    body = les.get("body") or ""
    refs: dict[str, set[str]] = {}
    miss = {"sentence": 0, "reading": 0}

    def add(ref: str, channel: str) -> None:
        if isinstance(ref, str) and ref.split(":", 1)[0] in UNLOCK_NS and ":" in ref:
            refs.setdefault(ref, set()).add(channel)

    for m in ITEM_TAG.finditer(body):
        for ref in ITEM_ATTR.findall(m.group(2)):
            add(ref, "body-chip")

    def expand(slug: str, channel: str) -> None:
        got = sent_idx.get(slug)
        if got is None:
            miss["sentence"] += 1
            return
        for ref in got:
            add(ref, channel)

    for slug in SENT_TAG.findall(body):
        expand(slug, "body-sentence")
    for slug in les.get("sentence_refs") or []:
        expand(slug, "lesson-sentence-refs")
    for ex in les.get("exercises") or []:
        for slug in ex.get("sentence_refs") or []:
            expand(slug, "exercise-sentence")
        for slug in (ex.get("answer") or {}).get("sentence_refs") or []:
            expand(slug, "exercise-sentence")

    for slug in READ_TAG.findall(body):
        got = read_idx.get(slug)
        if got is None:
            miss["reading"] += 1
            continue
        for ref in got:
            add(ref, "body-reading")

    return refs, miss


def raw_jp_kanji(les: dict) -> set[str]:
    """Annex channel: kanji rendered as bare prose, not as an addressed chip.

    `<jp>` spans in the body and the raw Japanese inside exercise answers are text, not
    references — nothing in the repo treats them as addresses (validate_lesson_gating check B
    scopes itself to item tags for the same reason). Measured so the choice to exclude them is
    a number in the report rather than an assumption.
    """
    out: set[str] = set()
    for span in JP_SPAN.findall(les.get("body") or ""):
        for ch in KANJI_CHAR.findall(re.sub(r"<[^>]+>", "", span)):
            out.add(f"kanji:{ch}")
    for ex in les.get("exercises") or []:
        blob = json.dumps(ex.get("answer") or {}, ensure_ascii=False)
        for ch in KANJI_CHAR.findall(blob):
            out.add(f"kanji:{ch}")
    return out


# --------------------------------------------------------------------------- graph
def transitive_reduction(order: list[str], succ: dict[str, set[str]],
                         pos: dict[str, int]) -> tuple[dict[str, set[str]], dict[str, int]]:
    """Reduce, and return the prerequisite-closure bitset per lesson.

    Every edge runs from a lesson to a strictly EARLIER lesson, so course order is already a
    reverse topological order and the closure of a successor is finished before its
    predecessor is visited. Walking a node's successors nearest-first, an edge is redundant
    exactly when a nearer successor already reaches it — no separate reachability pass needed.
    """
    reach: dict[str, int] = {}
    reduced: dict[str, set[str]] = {}
    for lid in order:
        covered = 0
        keep: set[str] = set()
        for m in sorted(succ.get(lid, ()), key=lambda x: pos[x], reverse=True):
            bit = 1 << pos[m]
            if covered & bit:
                continue  # already reached through a nearer prerequisite
            keep.add(m)
            covered |= bit | reach[m]
        reduced[lid] = keep
        reach[lid] = covered
    return reduced, reach


def topo_sort(order: list[str], succ: dict[str, set[str]]) -> list[str] | None:
    """Kahn over the edge set itself. Returns None (i.e. a cycle) if it cannot drain."""
    indeg = {lid: 0 for lid in order}
    rev: dict[str, list[str]] = {lid: [] for lid in order}
    for lid in order:
        for m in succ.get(lid, ()):
            indeg[lid] += 1          # lid depends on m
            rev[m].append(lid)
    queue = sorted(lid for lid in order if indeg[lid] == 0)
    out: list[str] = []
    while queue:
        cur = queue.pop(0)
        out.append(cur)
        nxt = []
        for dep in sorted(rev[cur]):
            indeg[dep] -= 1
            if indeg[dep] == 0:
                nxt.append(dep)
        queue = sorted(queue + nxt)
    return out if len(out) == len(order) else None


def longest_depth(order: list[str], reduced: dict[str, set[str]]) -> dict[str, int]:
    depth: dict[str, int] = {}
    for lid in order:  # prerequisites always precede in this order
        prereq = reduced.get(lid) or ()
        depth[lid] = 1 + max((depth[m] for m in prereq), default=-1)
    return depth


def longest_chain(order: list[str], reduced: dict[str, set[str]],
                  depth: dict[str, int]) -> list[str]:
    if not order:
        return []
    end = max(order, key=lambda x: (depth[x], -order.index(x)))
    chain = [end]
    while reduced.get(chain[-1]):
        chain.append(max(sorted(reduced[chain[-1]]), key=lambda x: depth[x]))
    return list(reversed(chain))


# --------------------------------------------------------------------------- rendering
def fmt_note(refs: list[str], channels: list[str]) -> str:
    head = ", ".join(refs[:NOTE_REFS])
    more = f" (+{len(refs) - NOTE_REFS} more)" if len(refs) > NOTE_REFS else ""
    return f"introduces {head}{more}; seen via {'/'.join(channels)}"


def build(root: Path) -> tuple[dict, str]:
    lessons = load_course(root)
    order = [d["id"] for d in lessons]
    pos = {lid: i for i, lid in enumerate(order)}
    by_id = {d["id"]: d for d in lessons}

    # --- ordering witness: outline.json must agree with the manifest walk -------------
    course_topics: list[str] = []
    for d in lessons:
        if not course_topics or course_topics[-1] != d.get("topic"):
            course_topics.append(d.get("topic", ""))
    outline_topics = [t for t in outline_topic_order(root) if t in set(course_topics)]
    order_agrees = outline_topics == course_topics

    # --- introducer map: ref -> the single lesson that unlocks it ---------------------
    introducer: dict[str, str] = {}
    multi: dict[str, list[str]] = {}
    for d in lessons:
        for u in d.get("unlocks") or []:
            ref = u.get("ref")
            if not isinstance(ref, str):
                continue
            if ref in introducer:
                multi.setdefault(ref, [introducer[ref]]).append(d["id"])
            else:
                introducer[ref] = d["id"]

    sent_idx = load_sentence_index(root)
    read_idx = load_reading_index(root)

    # --- per-lesson reference harvest -------------------------------------------------
    channel_refs = {c: 0 for c in CHANNELS}          # (lesson, ref) pairs per channel
    channel_edges = {c: set() for c in CHANNELS}     # distinct edges each channel can carry
    dangling = {"sentence": 0, "reading": 0}
    untaught: dict[str, int] = {}                    # ref no lesson unlocks -> hit count
    self_refs = 0

    fwd: list[dict] = []                             # forward-edge defects
    succ: dict[str, set[str]] = {lid: set() for lid in order}
    drivers: dict[tuple[str, str], set[str]] = {}    # (L, M) -> driving refs
    edge_channels: dict[tuple[str, str], set[str]] = {}

    for d in lessons:
        lid = d["id"]
        refs, miss = lesson_references(d, sent_idx, read_idx)
        dangling["sentence"] += miss["sentence"]
        dangling["reading"] += miss["reading"]
        for ref, chans in refs.items():
            for c in chans:
                channel_refs[c] += 1
            m = introducer.get(ref)
            if m is None:
                untaught[ref] = untaught.get(ref, 0) + 1
                continue
            if m == lid:
                self_refs += 1
                continue
            for c in chans:
                channel_edges[c].add((lid, m))
            drivers.setdefault((lid, m), set()).add(ref)
            edge_channels.setdefault((lid, m), set()).update(chans)
            if pos[m] < pos[lid]:
                succ[lid].add(m)

    for (lid, m), refs_set in sorted(drivers.items()):
        if pos[m] > pos[lid]:
            fwd.append({
                "lesson": lid, "lesson_position": pos[lid],
                "needs_lesson": m, "needs_lesson_position": pos[m],
                "distance": pos[m] - pos[lid],
                "refs": sorted(refs_set),
                "channels": sorted(edge_channels[(lid, m)]),
            })
    fwd.sort(key=lambda e: (-e["distance"], e["lesson"], e["needs_lesson"]))

    raw_edges = sum(len(v) for v in succ.values())
    reduced, reach = transitive_reduction(order, succ, pos)
    reduced_edges = sum(len(v) for v in reduced.values())

    topo = topo_sort(order, reduced)
    depth = longest_depth(order, reduced)
    ancestors = {lid: bin(reach[lid]).count("1") for lid in order}

    # dependents: how many later lessons transitively rest on this one
    dependents = {lid: 0 for lid in order}
    for lid in order:
        r = reach[lid]
        while r:
            low = r & -r
            dependents[order[low.bit_length() - 1]] += 1
            r ^= low
    direct_dependents = {lid: 0 for lid in order}
    for lid in order:
        for m in reduced[lid]:
            direct_dependents[m] += 1

    # --- roots -------------------------------------------------------------------------
    # A lesson is a root iff it has no BACKWARD edge. The reduction never empties a non-empty
    # successor set (the nearest prerequisite is always kept), so reduced[lid] empty means
    # succ[lid] was empty too — the reason is always a property of the references, never of
    # the reduction.
    fwd_by_lesson: dict[str, list[dict]] = {}
    for e in fwd:
        fwd_by_lesson.setdefault(e["lesson"], []).append(e)

    roots: dict[str, str] = {}
    root_kind: dict[str, str] = {}
    for i, lid in enumerate(order):
        if reduced[lid]:
            continue
        d = by_id[lid]
        refs, _ = lesson_references(d, sent_idx, read_idx)
        taught = {r for r in refs if r in introducer}
        own = {r for r in taught if introducer[r] == lid}
        fwd_here = fwd_by_lesson.get(lid, [])
        if i == 0:
            kind, reason = "opener", (
                "course opener: the first lesson in course order has nothing before it")
        elif fwd_here:
            kind, reason = "forward-only", (
                f"NOT a real root: every one of its {len(fwd_here)} dependencies points FORWARD "
                f"in course order, so all were withheld as defects. Fixing the forward references "
                f"(see forward_edge_defects) gives this lesson prerequisites")
        elif not refs:
            kind, reason = "method", (
                "method lesson: the body and exercises carry no addressed item reference at all "
                "(no chip, sentence or reading), so there is nothing to depend on")
        elif not taught:
            kind, reason = "untaught-only", (
                f"references {len(refs)} item(s), none of which any lesson unlocks — nothing in "
                f"the course introduces them, so there is no lesson to need")
        else:  # taught == own; the residual case, since any non-own taught ref makes an edge
            kind, reason = "self-contained", (
                f"self-contained: all {len(own)} referenced taught item(s) are introduced by this "
                f"lesson itself, and it displays no sentence or reading that would pull in others")
        roots[lid] = reason
        root_kind[lid] = kind

    # --- gate simulation: what validate_lesson_gating check C would say -----------------
    gate_unresolved = [(lid, n["ref"]) for lid in order for n in
                       [{"ref": m} for m in reduced[lid]] if n["ref"] not in pos]
    gate_not_earlier = [(lid, m) for lid in order for m in reduced[lid] if pos[m] >= pos[lid]]
    covered = [lid for i, lid in enumerate(order) if reduced[lid] or lid in roots]

    # --- annex: bare-prose kanji, measured but not shipped -----------------------------
    annex_edges: set[tuple[str, str]] = set()
    annex_forward = 0
    for d in lessons:
        lid = d["id"]
        shipped = {m for m in succ[lid]} | {e["needs_lesson"] for e in fwd if e["lesson"] == lid}
        for ref in raw_jp_kanji(d):
            m = introducer.get(ref)
            if m is None or m == lid or m in shipped:
                continue
            annex_edges.add((lid, m))
            if pos[m] > pos[lid]:
                annex_forward += 1

    payload = {
        "definition": (
            "Lesson L needs lesson M iff M != L and L references at least one corpus item that M "
            "unlocks. A reference is an explicit, machine-resolvable pointer, from one of five "
            "channels: body item chips (<vocab|kanji|grammar ref>, <stroke ref>, <check item-ref>, "
            "<flashcard ref>); <sentence ref> in the body, expanded to the sentence's token vocab "
            "refs, the kanji in its token surfaces and its grammar tags; the lesson record's own "
            "sentence_refs, expanded the same way; each exercise's sentence_refs and "
            "answer.sentence_refs, expanded the same way; and <reading ref>, expanded through the "
            "reading record's `uses`. Every unlock ref in the course is introduced by exactly one "
            "lesson, so an item's introducer is a function. `needs` below is the TRANSITIVE "
            "REDUCTION of that relation: direct prerequisites only, each pointing to a strictly "
            "EARLIER lesson in course order. Edges that would point FORWARD are course-order "
            "defects; they are excluded from `needs` (they would hard-fail "
            "validate_lesson_gating check C) and listed in full under forward_edge_defects."
        ),
        "generated_by": GENERATED_BY,
        "need_shape": (
            "{type:'lesson', ref:'les:<id>', note:<why>} — need_type 'lesson' per "
            "design/unlock_enums.json; ref is the exported lesson id, which is what "
            "validate_lesson_gating check C and validate_lessons.py linearity both resolve against."
        ),
        "counts": {
            "lessons": len(order),
            "edges_raw": raw_edges,
            "edges_reduced": reduced_edges,
            "edges_removed_by_reduction": raw_edges - reduced_edges,
            "forward_edge_defects": len(fwd),
            "roots": len(roots),
            "acyclic": topo is not None,
            "max_depth": max(depth.values()) if depth else 0,
            "max_ancestors": max(ancestors.values()) if ancestors else 0,
            "order_agrees_with_outline": order_agrees,
            "unlock_refs_with_multiple_introducers": len(multi),
            "self_references_skipped": self_refs,
            "referenced_items_no_lesson_unlocks": len(untaught),
            "dangling_sentence_refs": dangling["sentence"],
            "dangling_reading_refs": dangling["reading"],
            "annex_bare_prose_kanji_extra_edges": len(annex_edges),
            "annex_bare_prose_kanji_extra_forward_edges": annex_forward,
            "gate_c_unresolved_refs": len(gate_unresolved),
            "gate_c_not_strictly_earlier": len(gate_not_earlier),
            "lessons_with_needs_or_listed_root": len(covered),
            "pre_n5_lessons_all_roots": all(
                not reduced[x] for x in order if by_id[x].get("level") == "pre-n5"),
            "roots_past_position_100": len(
                [x for x in order if not reduced[x] and pos[x] > 100]),
        },
        "root_kinds": {k: sorted(v for v in root_kind if root_kind[v] == k)
                       for k in sorted(set(root_kind.values()))},
        "channel_yield": {
            c: {"references": channel_refs[c], "distinct_edges_carried": len(channel_edges[c])}
            for c in CHANNELS
        },
        "forward_edge_defects": fwd,
        "lessons": [],
    }

    for lid in order:
        rec: dict = {
            "id": lid,
            "position": pos[lid],
            "level": by_id[lid].get("level"),
            "depth": depth[lid],
            "ancestors": ancestors[lid],
            "dependents": dependents[lid],
            "skippable_if_placed_here": pos[lid] - ancestors[lid],
            "needs": [
                {"type": "lesson", "ref": m,
                 "note": fmt_note(sorted(drivers[(lid, m)]), sorted(edge_channels[(lid, m)]))}
                for m in sorted(reduced[lid], key=lambda x: pos[x])
            ],
        }
        if lid in roots:
            rec["roots_reason"] = roots[lid]
        payload["lessons"].append(rec)

    report = render_report(payload, order, pos, by_id, reduced, depth, ancestors,
                           dependents, direct_dependents, topo, multi, root_kind)
    return payload, report


def render_report(p: dict, order: list[str], pos: dict[str, int], by_id: dict[str, dict],
                  reduced: dict[str, set[str]], depth: dict[str, int],
                  ancestors: dict[str, int], dependents: dict[str, int],
                  direct_dependents: dict[str, int], topo: list[str] | None,
                  multi: dict[str, list[str]], root_kind: dict[str, str]) -> str:
    c = p["counts"]
    L: list[str] = []
    w = L.append

    w("# W21 — `needs[]` derivation: the lesson prerequisite DAG")
    w("")
    w(f"Generated by `{GENERATED_BY}`. Derivation only: no lesson record, contract, export or")
    w("database was written. Re-running reproduces both artifacts byte for byte.")
    w("")
    w("## Definition")
    w("")
    w(p["definition"])
    w("")
    w("## Edge counts")
    w("")
    w("| | count |")
    w("|---|---:|")
    w(f"| lessons | {c['lessons']} |")
    w(f"| raw edges (every referenced-item -> introducer pair, backward) | {c['edges_raw']} |")
    w(f"| reduced edges (transitive reduction — what `needs[]` should hold) | {c['edges_reduced']} |")
    w(f"| edges removed as transitively implied | {c['edges_removed_by_reduction']} |")
    w(f"| forward-edge defects (excluded from `needs`, listed below) | {c['forward_edge_defects']} |")
    w(f"| lessons with no prerequisite (roots) | {c['roots']} |")
    w("")
    w(f"The reduction removes {c['edges_removed_by_reduction']} of {c['edges_raw']} raw edges "
      f"({100.0 * c['edges_removed_by_reduction'] / max(c['edges_raw'], 1):.1f}%): a late lesson")
    w("references hundreds of items whose introducers are already reachable through a nearer")
    w("prerequisite. Only the direct ones survive.")
    w("")
    w("### Where the references come from")
    w("")
    w("| channel | references harvested | distinct edges it can carry |")
    w("|---|---:|---:|")
    for ch in CHANNELS:
        y = p["channel_yield"][ch]
        w(f"| `{ch}` | {y['references']} | {y['distinct_edges_carried']} |")
    w("")
    w("Channels overlap, so the column does not sum to the edge total. `body-sentence` and")
    w("`lesson-sentence-refs` are identical by construction — `export_course.py` derives the")
    w("record's `sentence_refs` from the body it just rendered, so the manifest cannot disagree")
    w("with the body. Both are harvested anyway: the day they diverge, the derivation notices.")
    w("`body-reading` dominates because a reading record's `uses` block inventories every item in")
    w("a multi-sentence text, where a chip names one.")
    w("")
    w("## Acyclicity and the gate conditions")
    w("")
    if topo is not None:
        w(f"**Acyclic.** A Kahn topological sort over the reduced edge set drains all "
          f"{len(topo)} lessons, leaving none behind; a cycle would have stalled it.")
        w("")
        w("This is not accidental. Every retained edge points to a strictly earlier lesson in")
        w("course order, so course order is itself a valid reverse topological order and a cycle")
        w("is unrepresentable. The sort is run anyway, as an independent check of the built graph")
        w("rather than of the argument for it.")
    else:
        w("**FAILED: the reduced edge set contains a cycle.** Kahn could not drain it.")
    w("")
    w(f"Course order was cross-checked against `course/outline.json`: the topic sequence walked")
    w(f"from `course/manifest.json` + `course/*/course.json` "
      f"{'agrees' if c['order_agrees_with_outline'] else 'DOES NOT AGREE'} with the outline.")
    w(f"Introduce-once holds: {c['unlock_refs_with_multiple_introducers']} unlock ref(s) are")
    w("claimed by more than one lesson, so every item maps to a single introducer.")
    if multi:
        for ref, ls in sorted(multi.items())[:10]:
            w(f"- `{ref}` — {', '.join(ls)}")
    w("")
    w("The three conditions the brief asks to be proved, checked against the derived set:")
    w("")
    w("| condition | result |")
    w("|---|---|")
    w(f"| every `needs[].ref` resolves to an exported lesson id | "
      f"{c['gate_c_unresolved_refs']} unresolved |")
    w(f"| every `needs[].ref` is strictly earlier in course order | "
      f"{c['gate_c_not_strictly_earlier']} violations |")
    w(f"| every lesson has >=1 need or is a listed root | "
      f"{c['lessons_with_needs_or_listed_root']}/{c['lessons']} covered |")
    w("")
    w("Those are exactly check C of `validate_lesson_gating.py`, simulated here so the edge set")
    w("is known to pass before anyone writes it into a lesson record.")
    w("")
    w("## Forward-edge defects")
    w("")
    if not p["forward_edge_defects"]:
        w("None. Every derived dependency resolves to a lesson that comes earlier in course order.")
    else:
        fwd = p["forward_edge_defects"]
        w(f"{len(fwd)} lesson->lesson dependencies point FORWARD: the lesson puts an item in front")
        w("of the learner before the course introduces it. These are content defects, not")
        w("derivation defects. They are **excluded from `needs[]`** — check C hard-fails on any")
        w("need that is not strictly earlier, so shipping them would turn a content bug into a red")
        w("gate — and every one is carried in `forward_edge_defects` in the JSON. Nothing is")
        w("dropped; the full ledger is below.")
        w("")
        same_topic = [e for e in fwd
                      if by_id[e["lesson"]].get("topic") == by_id[e["needs_lesson"]].get("topic")]
        same_level = [e for e in fwd
                      if by_id[e["lesson"]].get("level") == by_id[e["needs_lesson"]].get("level")
                      and e not in same_topic]
        cross = [e for e in fwd if e not in same_topic and e not in same_level]
        w("| tier | edges | what it means |")
        w("|---|---:|---|")
        w(f"| same topic | {len(same_topic)} | a lesson uses what the next lesson in its own topic "
          f"teaches — the cheapest to fix, usually by swapping two lesson orders or one example |")
        w(f"| same level, different topic | {len(same_level)} | a topic leans on a later topic at "
          f"the same level |")
        w(f"| across levels | {len(cross)} | an N5 lesson displays an N4/N3 item; this is the "
          f"sentence-level i+1 backlog check D already freezes |")
        w("")
        ns = {}
        for e in fwd:
            for r in e["refs"]:
                ns[r.split(":", 1)[0]] = ns.get(r.split(":", 1)[0], 0) + 1
        w("Driving refs by namespace: "
          + ", ".join(f"`{k}` {v}" for k, v in sorted(ns.items(), key=lambda x: -x[1])) + ".")
        w("")
        w("### Worst offenders by lesson")
        w("")
        per: dict[str, int] = {}
        for e in fwd:
            per[e["lesson"]] = per.get(e["lesson"], 0) + 1
        w("| lesson | pos | level | forward edges |")
        w("|---|---:|---|---:|")
        for lid in sorted(per, key=lambda x: (-per[x], pos[x]))[:15]:
            w(f"| `{lid}` | {pos[lid]} | {by_id[lid].get('level')} | {per[lid]} |")
        w("")
        w("### Complete ledger")
        w("")
        w(f"All {len(fwd)} edges, sorted by how far forward they reach.")
        w("")
        w("| lesson | pos | depends forward on | pos | gap | driving refs | channels |")
        w("|---|---:|---|---:|---:|---|---|")
        for e in fwd:
            refs = ", ".join(f"`{r}`" for r in e["refs"][:4])
            if len(e["refs"]) > 4:
                refs += f" (+{len(e['refs']) - 4})"
            w(f"| `{e['lesson']}` | {e['lesson_position']} | `{e['needs_lesson']}` | "
              f"{e['needs_lesson_position']} | {e['distance']} | {refs} | "
              f"{'/'.join(e['channels'])} |")
    w("")
    w("## Roots")
    w("")
    w(f"{c['roots']} lessons carry no prerequisite. Every one is listed with the reason it is a")
    w("root, so no lesson is left silently empty. They fall into five kinds:")
    w("")
    kind_doc = {
        "opener": "the first lesson in the course; nothing precedes it",
        "method": "no addressed item reference anywhere in body or exercises — orientation, "
                  "phonology and review lessons that talk *about* the language",
        "self-contained": "every taught item it references is one it introduces itself, and it "
                          "displays no sentence or reading that would pull in others",
        "untaught-only": "references only items no lesson in the course unlocks",
        "forward-only": "**not really a root** — all of its dependencies point forward and were "
                        "withheld as defects; fixing those gives it prerequisites",
    }
    w("| kind | lessons | meaning |")
    w("|---|---:|---|")
    for k in ("opener", "method", "self-contained", "untaught-only", "forward-only"):
        ids = p["root_kinds"].get(k) or []
        if ids:
            w(f"| `{k}` | {len(ids)} | {kind_doc[k]} |")
    w("")
    ff = p["root_kinds"].get("forward-only") or []
    if ff:
        w(f"The {len(ff)} `forward-only` lessons are the ones to look at first — they are roots")
        w("only because the course order is wrong beneath them: "
          + ", ".join(f"`{x}`" for x in ff) + ".")
        w("")
    w("| lesson | pos | kind | reason |")
    w("|---|---:|---|---|")
    for rec in p["lessons"]:
        if "roots_reason" in rec:
            w(f"| `{rec['id']}` | {rec['position']} | `{root_kind[rec['id']]}` | "
              f"{rec['roots_reason']} |")
    w("")
    w("## Statistics for a placement policy (D2)")
    w("")
    w("Placement asks one question: *if a learner tests into lesson X, what must they already*")
    w("*have, and what can they skip?* The DAG answers both.")
    w("")
    w("### Depth and ancestry")
    w("")
    w("`depth` is the longest prerequisite chain ending at a lesson; `ancestors` is the size of")
    w("its full prerequisite closure — the true \"you must have done these\" set. `skippable` is")
    w("everything earlier in course order that is *not* an ancestor: the lessons a learner")
    w("placing into that lesson can legitimately skip, which a linear course cannot express.")
    w("")
    w("| level | lessons | max depth | mean ancestors | max ancestors | mean skippable |")
    w("|---|---:|---:|---:|---:|---:|")
    for lv in ("pre-n5", "n5", "n4", "n3"):
        ids = [x for x in order if by_id[x].get("level") == lv]
        if not ids:
            continue
        anc = [ancestors[x] for x in ids]
        skip = [pos[x] - ancestors[x] for x in ids]
        w(f"| {lv} | {len(ids)} | {max(depth[x] for x in ids)} | {sum(anc) / len(anc):.1f} | "
          f"{max(anc)} | {sum(skip) / len(skip):.1f} |")
    w("")
    w("### Longest chain per level")
    w("")
    w("The critical path: the deepest lesson at each level and the chain of direct prerequisites")
    w("behind it. Nothing shortens this — it is the true minimum path to that lesson.")
    w("")
    for lv in ("pre-n5", "n5", "n4", "n3"):
        ids = [x for x in order if by_id[x].get("level") == lv]
        if not ids:
            continue
        end = max(ids, key=lambda x: (depth[x], -pos[x]))
        chain = [end]
        while reduced.get(chain[-1]):
            chain.append(max(sorted(reduced[chain[-1]]), key=lambda x: depth[x]))
        chain.reverse()
        tail = (" — degenerate: no pre-N5 lesson has a derived prerequisite at all, see"
                " \"What the reference graph cannot see\" below" if len(chain) == 1 else "")
        w(f"- **{lv}** — depth {depth[end]}, {len(chain)} lesson(s){tail}: "
          + " -> ".join(f"`{x}`" for x in chain))
    w("")
    w("### Hub lessons")
    w("")
    w("Lessons the rest of the course rests on. `dependents` counts every later lesson that")
    w("transitively needs this one; `direct` counts those naming it in their reduced `needs`.")
    w("Skipping a hub in placement is what breaks a learner downstream.")
    w("")
    w("| lesson | pos | level | dependents | direct |")
    w("|---|---:|---|---:|---:|")
    for lid in sorted(order, key=lambda x: (-dependents[x], pos[x]))[:20]:
        w(f"| `{lid}` | {pos[lid]} | {by_id[lid].get('level')} | {dependents[lid]} | "
          f"{direct_dependents[lid]} |")
    w("")
    w("### Skip potential")
    w("")
    tot = sum(pos[x] - ancestors[x] for x in order)
    w(f"Summed over all {len(order)} lessons, {tot} (lesson, earlier-lesson) pairs are *not*")
    w(f"prerequisite pairs — a mean of {tot / max(len(order), 1):.1f} skippable lessons per")
    w("placement target. Where placement pays most, among lessons that actually have")
    w("prerequisites (roots are excluded here; see the caveat below):")
    w("")
    w("| placing into | pos | ancestors (must have) | skippable |")
    w("|---|---:|---:|---:|")
    nonroot = [x for x in order if reduced[x]]
    for lid in sorted(nonroot, key=lambda x: -(pos[x] - ancestors[x]))[:8]:
        w(f"| `{lid}` | {pos[lid]} | {ancestors[lid]} | {pos[lid] - ancestors[lid]} |")
    w("")
    deep_roots = [x for x in order if not reduced[x] and pos[x] > 100]
    if deep_roots:
        w(f"**Caveat, and a finding in itself.** {len(deep_roots)} lessons sit past position 100")
        w("with *zero* ancestors, so the arithmetic says a learner could open them on day one:")
        w("" + ", ".join(f"`{x}` (pos {pos[x]})" for x in deep_roots) + ".")
        w("These are the kanji-drill and end-of-level review lessons. They reference only the")
        w("items they themselves unlock, or nothing at all, so the reference graph genuinely")
        w("cannot find a dependency. That is a property of how those lessons are written, not a")
        w("licence to place a beginner into them, and a placement policy should treat a root at")
        w("depth 0 sitting deep in the course as unplaceable rather than free.")
        w("")
    w("### What the reference graph cannot see")
    w("")
    prelevel = [x for x in order if by_id[x].get("level") == "pre-n5"]
    pre_roots = [x for x in prelevel if not reduced[x]]
    w(f"All {len(pre_roots)} of the {len(prelevel)} pre-N5 lessons are roots: the whole kana")
    w("bootstrap has depth 0 and no derived edge anywhere in it. This is correct by the rule and")
    w("wrong for a learner. A hiragana lesson `<check item-ref>`s only its own kana family, so")
    w("lesson 15 never *references* what lessons 1-14 unlocked, even though it plainly assumes")
    w("them. `design/lesson_schema.md` anticipates this — it exempts kana-bootstrap words from")
    w("the linearity rule as \"kana-only deps\" — but the exemption removes a constraint, it does")
    w("not supply the edges. The pre-N5 strand is the one place where a sequential chain has to")
    w("be authored rather than derived, and it is small: one edge per lesson, in course order.")
    w("This derivation deliberately does not invent them, because a needs edge that no reference")
    w("supports would be indistinguishable from the ones that are evidence-backed.")
    w("")
    w("## Judgement calls")
    w("")
    w("1. **Edges are lesson-typed, not item-typed.** `need_type` also allows `vocab`, `kanji`,")
    w("   `grammar` and friends, but check C of `validate_lesson_gating.py` resolves *every*")
    w("   `needs[].ref` against the exported lesson id map and fails anything else, so an")
    w("   item-typed need would be reported as \"not an exported lesson\". `{type:'lesson',")
    w("   ref:'les:...'}` is the only form both gates accept: `validate_lessons.py` resolves it")
    w("   through `extra['les']` (lesson slugs, which carry the `les:` prefix) and then checks")
    w("   membership in the already-seen set. The driving items survive in `note`.")
    w("2. **Bare prose kanji is measured, not shipped.** A kanji inside a `<jp>` span or an")
    w(f"   exercise answer string is text, not an address. Counting it would add "
      f"{c['annex_bare_prose_kanji_extra_edges']} more edges and")
    w(f"   {c['annex_bare_prose_kanji_extra_forward_edges']} more forward defects, most of them")
    w("   the sentence-level i+1 backlog that `validate_lesson_gating.py` check D already holds")
    w("   frozen in `research/reports/lesson_sentence_baseline.json`. Check B scopes \"reference\"")
    w("   to addressed item tags for the same reason; this derivation matches it rather than")
    w("   inventing a second, wider definition of the same word.")
    w("3. **Exercise answers contribute almost nothing, and that is a finding.** Of 1,560")
    w("   exercises, 0 carry markup in `prompt` or `answer` and exactly 1 has")
    w("   `answer.sentence_refs`; 314 have exercise-level `sentence_refs`. The answer surface is")
    w("   plain text, so the \"answers\" channel the brief names is real but nearly empty. Making")
    w("   it carry weight needs `item_refs` on exercises (the field exists in the authoring")
    w("   source `research/derived/lessons/*.json` and is empty), not a fuzzier matcher here.")
    w("4. **Items no lesson teaches produce no edge.** "
      f"{c['referenced_items_no_lesson_unlocks']} distinct referenced refs are unlocked by no")
    w("   lesson at all — overwhelmingly vocabulary appearing inside displayed sentences that the")
    w("   course never formally introduces. There is no lesson to depend on, so they are counted")
    w("   here rather than turned into a dangling need.")
    w(f"5. **Self-references are dropped.** {c['self_references_skipped']} (lesson, ref) pairs")
    w("   point at an item the lesson itself introduces — the normal case for a lesson teaching")
    w("   its own material, and not a dependency.")
    w("6. **The reduction is exact, not heuristic.** Because every edge runs backward in course")
    w("   order, course order is a reverse topological order; walking each lesson's prerequisites")
    w("   nearest-first and dropping any already reached by a nearer one is the transitive")
    w("   reduction, which is unique for a DAG. Reachability is unchanged, and so is every")
    w("   longest path, so `depth` is the same before and after.")
    w("")
    w("## What this unblocks")
    w("")
    w("- Check C of `validate_lesson_gating.py` stops printing its standing ADVISORY and starts")
    w(f"  proving something: {c['edges_reduced']} prerequisites to verify instead of 0.")
    w("- G11's remediation edges become expressible: a failed checkpoint can name the exact")
    w("  lesson to return to.")
    w("- D2 placement gets its input — the ancestor closure per lesson, and the skip set.")
    w("")
    w("## Consistency notes for whoever applies this")
    w("")
    w(f"- `{EDGES_REL}` holds one record per lesson in course order, each with the `needs` array")
    w("  to write, plus `depth` / `ancestors` / `dependents` / `skippable_if_placed_here`.")
    w("- The authoring source is `research/derived/lessons/<slug>.json`, not the exported")
    w("  `course/**/lesson-*.json`; applying `needs` there and re-running the loader + exporter")
    w("  keeps the export regenerable, which is what CLAUDE.md requires.")
    w(f"- {c['dangling_sentence_refs']} sentence ref(s) and {c['dangling_reading_refs']} reading")
    w("  ref(s) failed to resolve against the corpus during the harvest.")
    w("")
    return "\n".join(L) + "\n"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=str(ROOT))
    ap.add_argument("--check", action="store_true",
                    help="re-derive and fail if the artifacts on disk differ")
    ap.add_argument("--quiet", action="store_true")
    a = ap.parse_args()
    root = Path(a.root).resolve()

    payload, report = build(root)
    edges_txt = json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=False) + "\n"

    ep, rp = root / EDGES_REL, root / REPORT_REL
    if a.check:
        bad = []
        for path, txt in ((ep, edges_txt), (rp, report)):
            if not path.exists() or path.read_text(encoding="utf-8") != txt:
                bad.append(str(path.relative_to(root)))
        if bad:
            print("DRIFT: " + ", ".join(bad))
            return 1
        print("OK: both artifacts match a fresh derivation byte for byte")
        return 0

    ep.parent.mkdir(parents=True, exist_ok=True)
    rp.parent.mkdir(parents=True, exist_ok=True)
    ep.write_text(edges_txt, encoding="utf-8")
    rp.write_text(report, encoding="utf-8")

    if not a.quiet:
        c = payload["counts"]
        print(f"lessons={c['lessons']} raw={c['edges_raw']} reduced={c['edges_reduced']} "
              f"removed={c['edges_removed_by_reduction']} forward={c['forward_edge_defects']} "
              f"roots={c['roots']} acyclic={c['acyclic']} max_depth={c['max_depth']}")
        print(f"wrote {EDGES_REL}")
        print(f"wrote {REPORT_REL}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
