#!/usr/bin/env python3
"""Hard gate for the family layer: the groupings must be a DERIVATION, not a snapshot.

WHY THIS EXISTS
---------------
`research/reports/family_layer_rebuild.md` §2.4: **272 of the 364 grammar `function_set`
memberships named the wrong family** — a learner opening "Gramática: partículas de lugar" was shown
the aspect marker ている. The cause was not a bad rule; it was that `build_families.py` was
"idempotent" by *refusing to run* (`if COUNT(*) > 0: skip`), so the layer froze at a pre-N4/N3
snapshot of `grammar_point.introducing_topic_id` and every later placement pass moved the course
underneath it. §2.3 is the same failure in `kanji_component`, §2.6 the same in `word_family`.

Nothing gated any of it. `validate_graph_edges.py` checks that a membership *resolves* and that the
back-pointer is its inverse — both true of a membership that names the wrong family. So this
validator asserts the one thing those cannot: that the member set of a derived family **equals** the
set computed from the store it derives from, at the scope it declares. Drift becomes a red gate
instead of silence, which is the load-bearing half of the fix (§4(b)); un-freezing the builders
without it just re-freezes at a newer snapshot.

It reads the EXPORTED JSON under `corpus/` and `course/` (the source of truth, CLAUDE.md). The one
exception is F9's second half, which compares the export against `db/corpus.sqlite` on purpose —
that check exists precisely because the two disagreed and nothing noticed; see F9 below.

WHAT IT CHECKS
--------------
  F1  topic binding — a family whose slug ends in a live topic id's suffix (`grp:gram-n5-rotina`
      -> `top:n5-rotina`) is TOPIC-DERIVED, and every member of it must be unlocked by a lesson of
      that topic. This is finding §2.4 stated as an assertion.
  F2  topic completeness — every grammar point and every kanji the course unlocks belongs to
      exactly ONE topic-derived family, and it is the family bound to its own unlocking topic.
      (Vocabulary is deliberately excluded: a word's topic-derived family is the residual bucket it
      lands in only when no word_family or conjugation class claims it.)
  F3  conjugation coverage — each `conjugation_class` family holds exactly the vocab whose
      JMdict-derived class matches it, over the levels the published courses teach. The scope is
      read from `course/manifest.json`, so an N2 course widens it with no edit here (CLAUDE.md
      §1.6: level is data, not structure).
  F4  no empty family, no unresolvable member, no duplicate slug, and no member listed twice.
  F5  `related` — present on every family (a stable shape from day one), both endpoints resolve,
      `relation` is in the enum, `contrast_pair` is symmetric, `sub_family` is directed, acyclic
      and never self-referential.
  F6  word families — a `word_family` holds exactly the taught-level vocabulary sharing its leading
      kanji, and every eligible group of >=2 words has one. This is §2.6 stated as an assertion:
      the builder filtered `level IN ('n5','n4')` as a literal, so n3 had zero.
  F7  `topic.family_ids` — present on every topic, every entry resolves to a live family, and the
      list EQUALS the inverse recomputed here from `lesson.unlocks[]` + `family.members[]`. The
      export derives it; this is what stops anyone reintroducing a stored snapshot of it.
  F8  retirement — `corpus/families_deprecated.json` and `corpus/families/families.json` are
      disjoint, every redirect points at a live family or a real exported field path, and no
      record's `families[]` back-pointer names a retired address.
  F9  `spans_levels` — the published span EQUALS the levels its own members carry (not merely
      "covers" them, which is all validate_graph_edges G10 asserts), AND the stored
      `family.spans_levels` column in `db/corpus.sqlite` says the same thing.

      F9 is the one check here that opens the database, because DB-vs-export agreement is the only
      claim you cannot test from one side. It is why: W11b derived the span at export time and had
      `familylib.recompute()` write the same value back into the column, but
      `scripts/ingest/fix_contrasts.py` did not go through `recompute()` — its own `fam()` helper
      wrote the literal `["n5","n4"]` on INSERT and never touched the column again — so three
      families (`grp:particles-core`, `grp:wa-vs-ga`, `grp:ni-vs-de`) shipped `["n5"]` in
      `corpus/families/families.json` while the index still said `["n5","n4"]`. Nothing in the gate
      compared them. The builder now goes through `recompute()`; this check is what stops the next
      builder from not doing so. The DB half SKIPS (out loud, in the counts block) when there is no
      `db/corpus.sqlite` under `--root`: the index is git-ignored, so a fresh checkout has none and
      a fixture only has one if the plant proof copies it. The export half always runs.

FALSIFIABILITY
--------------
Plant-proved on a COPIED tree, never on the repository. The fixture holds only what this validator
reads AND a copy of this file, so a plant cannot be read around by resolving ROOT back to the real
repo; the pristine copy is run first and must PASS, or no plant below means anything. Nine plants,
nine caught, 2026-09-09:

    [control] pristine copy -> exit 0   OK  every check passed
    [CAUGHT] P1 one grammar membership moved into another topic's family  (gram:te-form)
             [F1] grp:gram-n5-desu-wa: grammar gram:te-form is taught under top:n5-te-form, not
                  top:n5-desu-wa
    [CAUGHT] P2 families.json emptied to []
             [F2] 1128  grammar gram:aida (taught under top:n4-oracoes-relativas) is in no
                  topic-derived family        <- "no families at all" is not the cheapest way to pass
    [CAUGHT] P3 one word dropped from a word_family  (grp:word-4e00 - vocab:1576060)
             [F6] grp:word-4e00: 1 missing, 0 extra (e.g. vocab:1576060)
    [CAUGHT] P4 one topic's family_ids emptied  (top:n3-conectores)
             [F7] top:n3-conectores: family_ids is not the computed inverse - 66 missing, 0 extra
    [CAUGHT] P5 one conjugation_class member removed  (vocab:1611000)
             [F3] grp:godan: 1 eligible vocab not in the class, e.g. vocab:1611000
    [CAUGHT] P6 a live family also listed as retired  (grp:godan)
             [F8] grp:godan is listed as retired and is ALSO a live family
    [CAUGHT] P7 a related edge pointing at a family that does not exist
             [F5] grp:wa-vs-ga: related family 'grp:does-not-exist' resolves to no family
    [CAUGHT] P8 a member ref that resolves to no record  (vocab:99999999)
             [F4] grp:ichidan: vocab member 'vocab:99999999' resolves to no live record
    [CAUGHT] P9 a topic-derived family whose suffix names no live topic
             [F4] grp:gram-n5-topic-that-was-deleted: built under a topic-derived prefix but its
                  suffix names no live topic - an orphan a builder left behind

WHAT IT DOES NOT ASSERT, ON PURPOSE
-----------------------------------
A one-member family is allowed. `grp:kuru-irregular` has exactly one member because 来る is the only
kuru-irregular verb in the language, and `grp:kanji-topic-n4-keigo` has one because that topic
introduces one kanji. The rebuild report's draft assertion ("none has a single member") would have
failed on a correct derivation; EMPTY is the failure, because an empty family groups nothing.

Usage: validate_families.py [--root PATH]
Exit 0 when every check passes, 1 otherwise.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from collections import defaultdict
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]

# The six conjugation classes and the Layer-A vocab field each one derives from. Curated here on
# purpose: the pairing lives in scripts/ingest/build_families.py's CONJ table, and widening it is an
# edit in that builder plus this line, never a silent side effect of the data changing.
CONJ_CLASSES = {
    "grp:godan": ("verb_class", "godan"),
    "grp:ichidan": ("verb_class", "ichidan"),
    "grp:suru-irregular": ("verb_class", "suru_irregular"),
    "grp:kuru-irregular": ("verb_class", "kuru_irregular"),
    "grp:i-adj": ("adj_class", "i_adj"),
    "grp:na-adj": ("adj_class", "na_adj"),
}
RELATIONS = {"contrast_pair", "sub_family"}
# Teaching order, for F9. Same sequence as scripts/familylib.py LEVEL_SEQ — the two must agree,
# because one writes `spans_levels` and the other asserts it; duplicated rather than imported so
# the validator can run against a fixture that carries no scripts/ tree.
LEVEL_SEQ = ["pre-n5", "n5", "n4", "n3", "n2", "n1"]
# A `deprecated_by` value is either a surviving family slug or the exported field path that now
# answers the question the retired family used to answer. The path form is enumerated rather than
# pattern-matched, so "some string with a dot in it" can never pass as a redirect target.
FIELD_SUCCESSORS = {"kanji.components", "topic.family_ids"}
# Every prefix a topic-derived family is built under. Used to catch the inverse of F1: a family that
# LOOKS topic-derived but binds to no live topic is an orphan a builder left behind.
TOPIC_PREFIXES = ("grp:gram-", "grp:kanji-topic-", "grp:theme-")
KANJI_RE = re.compile(r"[一-鿿]")
# Member types that are taught one-per-topic and therefore must be completely covered by the
# topic-derived families (F2). Vocabulary is excluded — see the module docstring.
TOPIC_COMPLETE_TYPES = ("grammar", "kanji")


class Result:
    def __init__(self) -> None:
        self.fails: list[tuple[str, str]] = []
        self.counts: dict[str, int] = {}

    def fail(self, check: str, msg: str) -> None:
        self.fails.append((check, msg))

    def seen(self, label: str, n: int) -> None:
        self.counts[label] = n


def load_list(root: Path, glob: str) -> list:
    out: list = []
    for p in sorted(root.glob(glob)):
        data = json.loads(p.read_text(encoding="utf-8"))
        out += data if isinstance(data, list) else [data]
    return out


def main(root: Path) -> int:
    r = Result()
    fams = load_list(root, "corpus/families/families.json")
    vocab = load_list(root, "corpus/vocab/*.json")
    kanji = load_list(root, "corpus/kanji/*.json")
    grammar = load_list(root, "corpus/grammar/*.json")
    topics = load_list(root, "course/*/topic-*/topic.json")
    lessons = load_list(root, "course/*/topic-*/lesson-*.json")
    courses = json.loads((root / "course" / "manifest.json").read_text(encoding="utf-8"))
    taught_levels = {c["level"] for c in courses["courses"]}

    # An empty family file is not a pass. The registries below are what the layer must cover, so a
    # missing families.json fails here rather than vacuously satisfying every per-family loop.
    if not fams:
        r.fail("F4", "corpus/families/families.json holds no families at all")

    dep_path = root / "corpus" / "families_deprecated.json"
    deprecated: dict = json.loads(dep_path.read_text(encoding="utf-8")) if dep_path.exists() else {}

    v_by_slug = {v["slug"]: v for v in vocab}
    k_by_char = {k["character"]: k for k in kanji}
    g_by_key = {g["key"]: g for g in grammar}
    g_by_slug = {g["slug"]: g for g in grammar}

    # ---- the course's own answer to "where is this taught?": the unlock ledger ------------------
    # `lesson.unlocks[].ref` is the live course (validate_unlock_ledger.py gates introduce-once over
    # it), so it — not a frozen `introducing_topic_id` column — is what a family must agree with.
    unlock_topic: dict[tuple[str, str], str] = {}
    for les in lessons:
        tid = les.get("topic")
        for u in les.get("unlocks") or []:
            mt, ref = u.get("type"), u.get("ref")
            if mt in ("vocab", "kanji", "grammar") and isinstance(ref, str):
                unlock_topic.setdefault((mt, ref), tid)

    topic_ids = {t["id"] for t in topics}
    # A family is TOPIC-DERIVED when its slug ends with a live topic id's suffix; the longest match
    # wins so `grp:gram-n5-desu-wa` can never be read as the shorter `top:n5-desu` of another topic.
    suffixes = sorted(((tid.split(":", 1)[1], tid) for tid in topic_ids), key=lambda s: -len(s[0]))

    def bound_topic(slug: str):
        for suf, tid in suffixes:
            if slug.endswith("-" + suf):
                return tid
        return None

    # ---- per-family structure -------------------------------------------------------------------
    seen_slugs: set = set()
    fam_by_slug: dict = {}
    topic_families: dict = {}          # family slug -> topic id
    member_topic_fams: dict = defaultdict(list)
    n_members = 0
    for f in fams:
        slug = f.get("slug")
        if slug in seen_slugs:
            r.fail("F4", f"duplicate family slug {slug}")
        seen_slugs.add(slug)
        fam_by_slug[slug] = f
        members = f.get("members") or []
        if not members:
            r.fail("F4", f"{slug}: empty family — a grouping with no members teaches nothing")
        keys = set()
        resolved = []
        for m in members:
            n_members += 1
            mt, ref, msl = m.get("member_type"), m.get("ref"), m.get("slug")
            key = (mt, msl or ref)
            if key in keys:
                r.fail("F4", f"{slug}: member {key} listed twice")
            keys.add(key)
            if mt == "vocab":
                rec = v_by_slug.get(msl)
            elif mt == "kanji":
                rec = k_by_char.get(ref) if isinstance(ref, str) else None
            elif mt == "grammar":
                rec = g_by_slug.get(msl) or (g_by_key.get(ref) if isinstance(ref, str) else None)
            else:
                rec = None
                r.fail("F4", f"{slug}: member_type {mt!r} is not vocab/kanji/grammar")
            if mt in ("vocab", "kanji", "grammar") and rec is None:
                r.fail("F4", f"{slug}: {mt} member {msl or ref!r} resolves to no live record")
            elif rec is not None:
                resolved.append((mt, rec["slug"]))

        tid = bound_topic(slug)
        if tid:
            topic_families[slug] = tid
            for mt, mslug in resolved:
                member_topic_fams[(mt, mslug)].append(slug)
                got = unlock_topic.get((mt, mslug))
                if got is None:
                    r.fail("F1", f"{slug}: {mt} {mslug} is in a topic-derived family but no lesson "
                                 f"unlocks it")
                elif got != tid:
                    r.fail("F1", f"{slug}: {mt} {mslug} is taught under {got}, not {tid}")

    r.seen("families", len(fams))
    r.seen("memberships", n_members)
    r.seen("topic-derived families", len(topic_families))

    # ---- F4 the inverse of F1: a family SHAPED like a topic family that binds to no live topic ----
    # Without this, deleting a topic silently downgrades its family from "checked by F1" to
    # "unchecked", which is the failure mode this whole validator exists to make impossible.
    for slug in sorted(fam_by_slug):
        if slug.startswith(TOPIC_PREFIXES) and slug not in topic_families:
            r.fail("F4", f"{slug}: built under a topic-derived prefix but its suffix names no live "
                         f"topic — an orphan a builder left behind")

    # ---- F8 retirement ---------------------------------------------------------------------------
    for old_slug, successor in sorted(deprecated.items()):
        if old_slug in fam_by_slug:
            r.fail("F8", f"{old_slug} is listed as retired and is ALSO a live family")
        if successor not in fam_by_slug and successor not in FIELD_SUCCESSORS:
            r.fail("F8", f"{old_slug}: redirect target {successor!r} is neither a live family nor "
                         f"one of the exported field paths {sorted(FIELD_SUCCESSORS)}")
    r.seen("retired family addresses", len(deprecated))

    # ---- F2 topic completeness ------------------------------------------------------------------
    n_complete = 0
    for (mt, mslug), tid in sorted(unlock_topic.items()):
        if mt not in TOPIC_COMPLETE_TYPES:
            continue
        n_complete += 1
        got = member_topic_fams.get((mt, mslug)) or []
        if not got:
            r.fail("F2", f"{mt} {mslug} (taught under {tid}) is in no topic-derived family")
        elif len(got) > 1:
            r.fail("F2", f"{mt} {mslug} is in {len(got)} topic-derived families: {sorted(got)}")
    r.seen("unlocked grammar+kanji", n_complete)

    # ---- F3 conjugation coverage ----------------------------------------------------------------
    n_conj = 0
    for slug, (field, value) in CONJ_CLASSES.items():
        f = fam_by_slug.get(slug)
        if f is None:
            r.fail("F3", f"conjugation class {slug} is missing from the family layer")
            continue
        have = {m.get("slug") for m in f.get("members") or [] if m.get("member_type") == "vocab"}
        truth = {v["slug"] for v in vocab
                 if v.get(field) == value and v.get("level") in taught_levels}
        n_conj += len(truth)
        missing, extra = sorted(truth - have), sorted(have - truth)
        if missing:
            r.fail("F3", f"{slug}: {len(missing)} eligible vocab not in the class, "
                         f"e.g. {', '.join(missing[:3])}")
        if extra:
            r.fail("F3", f"{slug}: {len(extra)} member(s) the class does not derive, e.g. {extra[0]}")
    r.seen("conjugation-eligible vocab", n_conj)

    # ---- F5 related ------------------------------------------------------------------------------
    edges: set = set()
    for f in fams:
        slug = f.get("slug")
        rel = f.get("related")
        if rel is None:
            r.fail("F5", f"{slug}: no `related` property — the edge list must exist (empty when "
                         f"there are no edges) so the shape is stable for consumers")
            continue
        if not isinstance(rel, list):
            r.fail("F5", f"{slug}: `related` is {type(rel).__name__}, not a list")
            continue
        for e in rel:
            tgt, relation = e.get("slug"), e.get("relation")
            if relation not in RELATIONS:
                r.fail("F5", f"{slug}: relation {relation!r} is not one of {sorted(RELATIONS)}")
            if tgt not in fam_by_slug:
                r.fail("F5", f"{slug}: related family {tgt!r} resolves to no family")
                continue
            if tgt == slug:
                r.fail("F5", f"{slug}: related to itself")
            edges.add((slug, tgt, relation))
    for a, b, relation in sorted(edges):
        if relation == "contrast_pair" and (b, a, relation) not in edges:
            r.fail("F5", f"contrast_pair {a} -> {b} is not mirrored back; the relation is symmetric")
        if relation == "sub_family" and (b, a, relation) in edges:
            r.fail("F5", f"sub_family {a} <-> {b} points both ways; the relation is directed")
    # sub_family must be a forest: walk parents from every node and refuse a cycle.
    parents = defaultdict(set)
    for a, b, relation in edges:
        if relation == "sub_family":
            parents[a].add(b)
    for start in sorted(parents):
        seen, stack = {start}, [start]
        while stack:
            cur = stack.pop()
            for p in parents.get(cur, ()):
                if p in seen:
                    r.fail("F5", f"sub_family cycle through {start} and {p}")
                    continue
                seen.add(p)
                stack.append(p)
    r.seen("family_related edges", len(edges))

    # ---- F6 word families ------------------------------------------------------------------------
    # A word_family is a pure derivation of `vocab.headword`: the taught-level words whose first
    # character is the same kanji, when at least two of them exist. §2.6 measured the builder
    # filtering `level IN ('n5','n4')` as a literal, which is why n3's 1,596 words were in no vocab
    # family at all. Asserting the set BOTH ways is what makes "we widened the filter" checkable
    # instead of a claim about a diff.
    lead: dict = defaultdict(set)
    for v in vocab:
        hw = v.get("headword")
        if hw and KANJI_RE.match(hw[0]) and v.get("level") in taught_levels:
            lead[hw[0]].add(v["slug"])
    want = {f"grp:word-{ord(ch):x}": members for ch, members in lead.items() if len(members) >= 2}
    have = {slug: {m.get("slug") for m in f.get("members") or []}
            for slug, f in fam_by_slug.items() if f.get("type") == "word_family"}
    for slug in sorted(set(want) - set(have)):
        r.fail("F6", f"{slug}: {len(want[slug])} taught-level words share this leading kanji and no "
                     f"word_family holds them")
    for slug in sorted(set(have) - set(want)):
        r.fail("F6", f"{slug}: a word_family the headwords do not derive")
    for slug in sorted(set(have) & set(want)):
        if have[slug] != want[slug]:
            miss, extra = sorted(want[slug] - have[slug]), sorted(have[slug] - want[slug])
            r.fail("F6", f"{slug}: {len(miss)} missing, {len(extra)} extra "
                         f"(e.g. {(miss or extra)[0]})")
    r.seen("word families derived", len(want))

    # ---- F7 topic.family_ids ---------------------------------------------------------------------
    # The inverse edge, recomputed from the two published sides — the lessons' unlocks and the
    # families' members — and compared to what course/*/topic-*/topic.json actually carries. The
    # export derives this; the check is what stops a future change quietly storing a snapshot of it,
    # which is the exact shape that froze the layer in the first place.
    fam_of_member: dict = defaultdict(list)
    for f in fams:
        for m in f.get("members") or []:
            fam_of_member[(m.get("member_type"), m.get("slug"))].append(f["slug"])
    lessons_by_topic: dict = defaultdict(list)
    for les in lessons:
        lessons_by_topic[les.get("topic")].append(les)
    n_edges = 0
    for t in sorted(topics, key=lambda x: x["id"]):
        got = t.get("family_ids")
        if got is None:
            r.fail("F7", f"{t['id']}: no `family_ids` — the topic->family edge of spec 1.7 must "
                         f"exist in both directions")
            continue
        want_set = set()
        for les in lessons_by_topic.get(t["id"], []):
            for u in les.get("unlocks") or []:
                if u.get("type") in ("vocab", "kanji", "grammar"):
                    want_set.update(fam_of_member.get((u["type"], u["ref"]), ()))
        unknown = [s for s in got if s not in fam_by_slug]
        if unknown:
            r.fail("F7", f"{t['id']}: family_ids names {len(unknown)} family that does not exist, "
                         f"e.g. {unknown[0]}")
        if set(got) != want_set:
            miss, extra = sorted(want_set - set(got)), sorted(set(got) - want_set)
            r.fail("F7", f"{t['id']}: family_ids is not the computed inverse — {len(miss)} missing, "
                         f"{len(extra)} extra (e.g. {(miss or extra)[0]})")
        if len(got) != len(set(got)):
            r.fail("F7", f"{t['id']}: family_ids lists the same family twice")
        n_edges += len(got)
    r.seen("topic->family edges", n_edges)

    # ---- F8 no record points back at a retired address --------------------------------------------
    if deprecated:
        n_back = 0
        for rec in vocab + kanji + grammar:
            for fs in rec.get("families") or []:
                n_back += 1
                if fs in deprecated:
                    r.fail("F8", f"{rec['slug']}: `families` back-pointer names the retired address "
                                 f"{fs} (redirects to {deprecated[fs]})")
        r.seen("record->family back-pointers", n_back)

    # ---- F9 spans_levels, in BOTH layers ---------------------------------------------------------
    # The export derives the span from the members (export_corpus.py `_member_span`) and
    # familylib.recompute() writes the same value into family.spans_levels. Two halves:
    #   (a) the published span EQUALS the member levels. G10 in validate_graph_edges only asserts
    #       "covers", which a span of every level in the language would satisfy.
    #   (b) db/corpus.sqlite agrees with what shipped. This is the drift that shipped: a builder
    #       that wrote the column outside recompute() froze it at ["n5","n4"] on three families.
    lvl_of = {"vocab": lambda m: (v_by_slug.get(m.get("slug")) or {}).get("level"),
              "kanji": lambda m: (k_by_char.get(m.get("ref")) or {}).get("level"),
              "grammar": lambda m: (g_by_slug.get(m.get("slug"))
                                    or g_by_key.get(m.get("ref")) or {}).get("level")}
    derived_span: dict[str, list] = {}
    for f in fams:
        found = {lvl_of[m["member_type"]](m) for m in (f.get("members") or [])
                 if m.get("member_type") in lvl_of}
        want = [lv for lv in LEVEL_SEQ if lv in found]
        derived_span[f["slug"]] = want
        got = f.get("spans_levels") or []
        if got != want:
            r.fail("F9", f"{f['slug']}: spans_levels is {got}, its members occupy {want} — the "
                         f"published span is not the derivation it claims to be")
    r.seen("spans_levels derived", len(derived_span))

    db_path = root / "db" / "corpus.sqlite"
    if not db_path.exists():
        r.seen("spans_levels vs db/corpus.sqlite", -1)   # printed as SKIPPED below
    else:
        import sqlite3
        con = sqlite3.connect(f"file:{db_path.as_posix()}?mode=ro", uri=True)
        n_db = 0
        for slug, raw in con.execute(
                "SELECT slug, spans_levels FROM family WHERE deprecated_by IS NULL"):
            if slug not in derived_span:
                continue        # retired between index and export; F8 owns that case
            n_db += 1
            stored = json.loads(raw) if raw else []
            if stored != derived_span[slug]:
                r.fail("F9", f"{slug}: db/corpus.sqlite stores spans_levels {stored}, the export "
                             f"publishes {derived_span[slug]} — the index and the source of truth "
                             f"disagree about a field a builder is supposed to own")
        con.close()
        r.seen("spans_levels vs db/corpus.sqlite", n_db)

    # ---- report ----------------------------------------------------------------------------------
    print("validate_families — the family layer as a derivation")
    for label, n in r.counts.items():
        print(f"  {label:28s} {'SKIPPED (no db/corpus.sqlite under --root)' if n == -1 else n}")
    if not r.fails:
        print("OK  every check passed")
        return 0
    by_check: dict = defaultdict(list)
    for check, msg in r.fails:
        by_check[check].append(msg)
    print(f"FAIL {len(r.fails)} problem(s)")
    for check in sorted(by_check):
        msgs = by_check[check]
        print(f"  [{check}] {len(msgs)}")
        for m in msgs[:8]:
            print(f"      {m}")
        if len(msgs) > 8:
            print(f"      ... and {len(msgs) - 8} more")
    return 1


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=str(Path(__file__).resolve().parents[2]),
                    help="tree to validate (a copied fixture for the plant proof)")
    a = ap.parse_args()
    sys.exit(main(Path(a.root)))
