#!/usr/bin/env python3
"""Hard gate: every cross-entity edge in the exported graph resolves, and says something TRUE about
its target.

WHY THIS EXISTS
---------------
Spec §1.7 says the corpus is one cross-referenceable graph addressed by stable ID. Until now nothing
checked the half of that graph that is not a prefixed string. `validate_contracts.py` resolves
`kanji:食`-shaped references; it is structurally blind to the integer foreign keys
(`tokens[].vocab_id`, `example_vocab_ids`, `exam_item.vocab_id`), the bare-key ones
(`sentence.grammar[]` holds `wa-topic-marker`, not `gram:wa-topic-marker`), the bare-character ones
(`vocab.kanji[]`, `reading.uses.kanji[]`) and the foreign keys that live in a field named `slug`
(`conjugation.slug` is the vocab the paradigm is FOR). That is roughly 87,000 unguarded edges (G09).

Resolving is not enough, either. Every defect this file was written for was a link that resolved
perfectly and was false about what it pointed at:

  G01  kanji 婦 published three example sentences that do not contain 婦 — the sentences had been
       modernised 看護婦 -> 看護師 and the kanji index was never updated. A learner saw them on the
       live kanji page. No validator read `example_sentences` at all.
  G10  the kanji_component families are stale against `kanji.components`, the store they duplicate,
       and 16 families hold members at a level their own `spans_levels` does not declare.
  G04  the family layer had no inbound edge in either direction; the export now writes a `families`
       back-pointer on vocab / kanji / grammar, and this checks the two directions agree.
  G11  56 of 322 lessons carry no capability. 14 of those are principled; the other 42 unlock
       vocabulary the capability registry cannot express. Both live in an exemptions file with a
       written reason, so the gap is data rather than silence.
  G18  322 `vocab.kanji` entries name characters outside the leveled registry. Real, expected, and a
       dead link for any consumer that renders a kanji chip per character — so they are enumerated in
       design/unregistered_kanji_chars.json instead of being tolerated by a blanket skip.

Everything here reads the exported JSON under corpus/ and course/. db/corpus.sqlite is a regenerable
index and is never opened.

TWO DOCUMENTED EXCLUSIONS
-------------------------
  * `kanji.components[]` holds Kradfile radicals (⺅, 亠, ハ …) as well as standalone kanji. Radicals
    are not registry records and never will be, so components are not resolved as an edge.
  * `vocab.kanji[]` may name a character outside the leveled registry. Those are not skipped: each one
    must be listed in design/unregistered_kanji_chars.json, which `--write-unregistered` regenerates.

Usage: validate_graph_edges.py [--root PATH] [--write-unregistered]
Exit 0 only when every check passes.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]

MAX_REPORT = 15          # FAIL lines printed per check; beyond that, one example per failure KIND
ITEM_UNLOCKS = {"vocab", "kanji", "grammar", "kana-family"}
EXEMPT_STATUSES = {"principled", "pending-capability-design"}
# `vocab:` followed by everything up to a JSON/markup delimiter. Anchored nowhere, because the
# headword form this hunts for also hides inside lesson-body markup (`<check item-ref="vocab:人">`).
VOCAB_REF = re.compile(r"vocab:([^\s\"'\\,\]<>)}]+)")


# --------------------------------------------------------------------------- loading

class Corpus:
    """Every exported file this validator needs, loaded once and indexed by address."""

    def __init__(self, root: Path) -> None:
        self.root = root
        self.vocab = self._concat("corpus/vocab/n*.json")
        self.kanji = self._concat("corpus/kanji/n*.json")
        self.grammar = self._concat("corpus/grammar/n*.json")
        self.readings = self._concat("corpus/readings/n*.json")
        self.families = self._one("corpus/families/families.json") or []
        self.bank = self._one("corpus/sentences/bank.json") or []
        self.kana = self._concat("corpus/kana/hiragana.json") + self._concat("corpus/kana/katakana.json")

        self.v_by_id = {r["id"]: r for r in self.vocab}
        self.v_by_slug = {r["slug"]: r for r in self.vocab}
        self.k_by_char = {r["character"]: r for r in self.kanji}
        self.g_by_key = {r["key"]: r for r in self.grammar}
        self.g_by_slug = {r["slug"]: r for r in self.grammar}
        self.s_by_slug = {r["slug"]: r for r in self.bank}
        self.r_by_slug = {r["slug"]: r for r in self.readings}
        self.kana_chars = {r["char"] for r in self.kana}

        self.headwords: dict[str, list[str]] = defaultdict(list)
        for r in self.vocab:
            self.headwords[r["headword"]].append(r["slug"])

        self.lessons: dict[str, dict] = {}
        for p in sorted(root.glob("course/*/topic-*/lesson-*.json")):
            rec = json.loads(p.read_text(encoding="utf-8"))
            self.lessons[rec["id"]] = rec

    def _one(self, rel: str):
        p = self.root / rel
        return json.loads(p.read_text(encoding="utf-8")) if p.exists() else None

    def _concat(self, glob: str) -> list[dict]:
        out: list[dict] = []
        for p in sorted(self.root.glob(glob)):
            out += json.loads(p.read_text(encoding="utf-8"))
        return out

    def json_files(self):
        """Every exported JSON under corpus/ and course/, as (relative path, raw text)."""
        for base in ("corpus", "course"):
            for p in sorted((self.root / base).rglob("*.json")):
                yield p.relative_to(self.root).as_posix(), p.read_text(encoding="utf-8")


class Check:
    """One named invariant: its failures, and how many edges it looked at.

    Failures carry a `kind`, and when there are more of them than fit in the report the printout
    switches to a per-kind tally with one example each. A cap that simply truncates hides a NEW kind
    of breakage behind an old backlog — 16 known stale families would otherwise bury the seventeenth.
    """

    def __init__(self, name: str) -> None:
        self.name = name
        self.fails: list[tuple[str, str]] = []
        self.counts: dict[str, int] = {}
        self.notes: list[str] = []

    def fail(self, kind: str, msg: str) -> None:
        self.fails.append((kind, msg))

    def looked_at(self, label: str, n: int) -> None:
        self.counts[label] = n

    def report(self) -> None:
        mark = "OK " if not self.fails else "FAIL"
        seen = ", ".join(f"{n} {lbl}" for lbl, n in self.counts.items())
        print(f"  [{mark}] {self.name:24} {seen}"
              + (f" — {len(self.fails)} failure(s)" if self.fails else ""))
        for note in self.notes:
            print(f"         [info] {note}")
        if len(self.fails) <= MAX_REPORT:
            for _, msg in self.fails:
                print(f"         ! {msg}")
            return
        tally = Counter(kind for kind, _ in self.fails)
        first: dict[str, str] = {}
        for kind, msg in self.fails:
            first.setdefault(kind, msg)
        print(f"         ! {len(self.fails)} failures in {len(tally)} kind(s); one example each:")
        for kind, n in tally.most_common(MAX_REPORT):
            print(f"         ! [{kind} x{n}] {first[kind]}")
        if len(tally) > MAX_REPORT:
            print(f"         ! ...and {len(tally) - MAX_REPORT} more kind(s)")


# --------------------------------------------------------------------------- checks

def check_registries_present(c: Corpus) -> Check:
    """A registry that loaded zero records makes every edge into it vacuously fine.

    validate_contracts.py learned this the hard way: a moved directory, a renamed file and a stopped
    exporter all read as `0 records` and used to print OK. An empty side of a join is a failure here,
    not a quiet pass.
    """
    ck = Check("registries_present")
    for label, rows in (("vocab", c.vocab), ("kanji", c.kanji), ("grammar", c.grammar),
                        ("readings", c.readings), ("families", c.families),
                        ("sentences", c.bank), ("kana", c.kana), ("lessons", c.lessons)):
        ck.looked_at(label, len(rows))
        if not rows:
            ck.fail("empty_registry", f"{label}: loaded 0 records — the data moved, the exporter "
                                      f"stopped, or the glob is wrong. Every edge into it would "
                                      f"pass vacuously.")
    return ck


def check_kanji_example_links(c: Corpus) -> Check:
    """G01. A kanji's example links must be true of what they point at, not merely resolvable."""
    ck = Check("kanji_example_links")
    n_sent = n_word = n_read = 0
    for k in c.kanji:
        ch = k["character"]
        for slug in (k.get("example_sentences") or []):
            n_sent += 1
            s = c.s_by_slug.get(slug)
            if s is None:
                ck.fail("example_sentences", f"{ch}: example_sentences {slug} resolves to no sentence")
            elif ch not in s["jp"]:
                ck.fail("example_sentences",
                        f"{ch}: example_sentences {slug} does not contain {ch} — {s['jp'][:24]}")
        for w in (k.get("example_words") or []):
            n_word += 1
            slug = w.get("slug")
            v = c.v_by_slug.get(slug) if isinstance(slug, str) else None
            if v is None:
                ck.fail("example_words", f"{ch}: example_words slug {slug!r} resolves to no vocab")
                continue
            if w.get("vocab_id") is not None and v["id"] != w["vocab_id"]:
                ck.fail("example_words", f"{ch}: example_words {slug} carries vocab_id "
                                         f"{w['vocab_id']}, but that slug is id {v['id']}")
            elif ch not in (v.get("kanji") or []):
                ck.fail("example_words",
                        f"{ch}: example_words {slug} ({v['headword']}) does not use {ch}")
        for r in (k.get("readings") or []):
            for vid in (r.get("example_vocab_ids") or []):
                n_read += 1
                v = c.v_by_id.get(vid)
                if v is None:
                    ck.fail("reading_examples", f"{ch}: reading {r.get('reading')} "
                                                f"example_vocab_ids {vid} resolves to no vocab")
                elif ch not in (v.get("kanji") or []):
                    ck.fail("reading_examples", f"{ch}: reading {r.get('reading')} example "
                                                f"{v['headword']} does not use {ch}")
    ck.looked_at("sentence links", n_sent)
    ck.looked_at("word links", n_word)
    ck.looked_at("reading examples", n_read)
    return ck


def check_family_graph(c: Corpus) -> Check:
    """G04 / G10. Members resolve, the back-pointers agree, and spans_levels covers the members."""
    ck = Check("family_graph")
    n_member = 0
    forward: dict[str, set[tuple[str, str]]] = {}
    for f in c.families:
        slug = f["slug"]
        want: set[tuple[str, str]] = set()
        levels: set[str] = set()
        for m in f.get("members") or []:
            n_member += 1
            mt, ref, msl = m.get("member_type"), m.get("ref"), m.get("slug")
            rec = None
            if mt == "vocab":
                rec = c.v_by_slug.get(msl) if isinstance(msl, str) else None
                if rec is None:
                    ck.fail("member",
                            f"{slug}: vocab member slug {msl!r} (ref {ref!r}) resolves to no record")
                else:
                    if m.get("id") is not None and rec["id"] != m["id"]:
                        ck.fail("member", f"{slug}: member {msl} carries id {m['id']}, "
                                          f"that slug is {rec['id']}")
                    if rec["headword"] != ref:
                        ck.fail("member", f"{slug}: member {msl} ref {ref!r} "
                                          f"!= headword {rec['headword']!r}")
                    want.add(("vocab", rec["slug"]))
            elif mt == "kanji":
                rec = c.k_by_char.get(ref) if isinstance(ref, str) else None
                if rec is None:
                    ck.fail("member", f"{slug}: kanji member {ref!r} resolves to no kanji record")
                else:
                    if msl and msl != rec.get("slug"):
                        ck.fail("member", f"{slug}: kanji member {ref} slug {msl!r} "
                                          f"!= {rec.get('slug')!r}")
                    want.add(("kanji", rec["character"]))
            elif mt == "grammar":
                if isinstance(ref, str):
                    rec = c.g_by_key.get(ref) or c.g_by_slug.get(ref)
                if rec is None:
                    ck.fail("member", f"{slug}: grammar member {ref!r} resolves to no grammar point")
                else:
                    if msl and msl != rec.get("slug"):
                        ck.fail("member", f"{slug}: grammar member {ref} slug {msl!r} "
                                          f"!= {rec.get('slug')!r}")
                    want.add(("grammar", rec["key"]))
            else:
                ck.fail("member", f"{slug}: member_type {mt!r} is not vocab/kanji/grammar")
            if rec is not None:
                levels.add(rec["level"])
        forward[slug] = want

        spans = f.get("spans_levels") or []
        if not spans:
            ck.fail("spans_levels",
                    f"{slug}: spans_levels is empty — the family declares no level coverage")
        else:
            extra = sorted(levels - set(spans))
            if extra:
                ck.fail("spans_levels",
                        f"{slug}: spans_levels {spans} does not cover member level(s) {extra}")

    # The back-pointer the exporter now writes must name exactly the families that claim the record.
    back: dict[str, set[tuple[str, str]]] = defaultdict(set)
    for r in c.vocab:
        for fs in (r.get("families") or []):
            back[fs].add(("vocab", r["slug"]))
    for r in c.kanji:
        for fs in (r.get("families") or []):
            back[fs].add(("kanji", r["character"]))
    for r in c.grammar:
        for fs in (r.get("families") or []):
            back[fs].add(("grammar", r["key"]))

    for fs in sorted(set(back) - set(forward)):
        ck.fail("back_pointer",
                f"back-pointer to unknown family {fs} (e.g. {sorted(back[fs])[0][1]})")
    for slug, want in forward.items():
        got = back.get(slug, set())
        if not got:
            ck.fail("back_pointer",
                    f"{slug}: unreachable — no member carries it in its `families` back-pointer")
            continue
        missing, extra = sorted(want - got), sorted(got - want)
        if missing:
            ck.fail("back_pointer", f"{slug}: {len(missing)} member(s) lack the back-pointer, "
                                    f"e.g. {missing[0][1]}")
        if extra:
            ck.fail("back_pointer", f"{slug}: {len(extra)} record(s) point back at a family that "
                                    f"does not list them, e.g. {extra[0][1]}")
    ck.looked_at("families", len(c.families))
    ck.looked_at("member edges", n_member)
    ck.looked_at("back-pointers", sum(len(v) for v in back.values()))
    return ck


def check_capability_coverage(c: Corpus) -> Check:
    """G11. Every lesson is mapped to a capability or carries a written reason for not being."""
    ck = Check("capability_coverage")
    capd = c.root / "corpus" / "capabilities"
    if not (capd / "registry.json").exists():
        ck.notes.append("no capability registry exported — nothing to check")
        return ck
    reg = json.loads((capd / "registry.json").read_text(encoding="utf-8"))
    lmap = json.loads((capd / "lesson_map.json").read_text(encoding="utf-8"))

    ids = [cap["id"] for cap in reg]
    for cid, n in Counter(ids).items():
        if n > 1:
            ck.fail("registry", f"registry: capability id {cid} declared {n} times")
    owner: dict[str, str] = {}
    for cap in reg:
        for key in cap.get("grammar_keys") or []:
            if key not in c.g_by_key:
                ck.fail("registry",
                        f"{cap['id']}: grammar key {key!r} is in no exported grammar record")
            if key in owner:
                ck.fail("registry", f"grammar key {key!r} claimed by two capabilities: "
                                    f"{owner[key]} + {cap['id']}")
            owner[key] = cap["id"]
    unclaimed = sorted(set(c.g_by_key) - set(owner))
    if unclaimed:
        ck.fail("registry",
                f"{len(unclaimed)} grammar key(s) belong to no capability, e.g. {unclaimed[:5]}")

    idset = set(ids)
    for lid, caps in lmap.items():
        if lid not in c.lessons:
            ck.fail("lesson_map", f"lesson_map: {lid} is not an exported lesson")
        for cap in caps:
            if cap not in idset:
                ck.fail("lesson_map", f"lesson_map {lid}: capability {cap} is not in the registry")

    # ---- the exemption table -----------------------------------------------------------------
    epath = capd / "exemptions.json"
    exempt: dict[str, dict] = {}
    if not epath.exists():
        ck.fail("exemption", "corpus/capabilities/exemptions.json is missing — an unmapped lesson "
                             "has nowhere to declare why")
    else:
        doc = json.loads(epath.read_text(encoding="utf-8"))
        for e in doc.get("exemptions") or []:
            lid = e.get("lesson")
            if lid in exempt:
                ck.fail("exemption", f"exemptions: {lid} listed twice")
            exempt[lid] = e
            if not (e.get("reason") or "").strip():
                ck.fail("exemption", f"exemptions: {lid} carries no reason")
            if e.get("status") not in EXEMPT_STATUSES:
                ck.fail("exemption", f"exemptions: {lid} status {e.get('status')!r} not in "
                                     f"{sorted(EXEMPT_STATUSES)}")
            # An exemption that matches nothing is itself a failure.
            if lid not in c.lessons:
                ck.fail("exemption", f"exemptions: {lid} is not an exported lesson — stale entry")
            elif lid in lmap:
                ck.fail("exemption", f"exemptions: {lid} is now mapped to {lmap[lid]} — "
                                     f"delete the entry")
            elif e.get("status") == "principled":
                items = {u["type"] for u in (c.lessons[lid].get("unlocks") or [])} & ITEM_UNLOCKS
                if items:
                    ck.fail("exemption", f"exemptions: {lid} is exempt as 'principled' (introduces "
                                         f"no corpus item) but now unlocks {sorted(items)}")

    for lid in sorted(set(c.lessons) - set(lmap)):
        if lid not in exempt:
            types = Counter(u["type"] for u in (c.lessons[lid].get("unlocks") or []))
            ck.fail("unmapped",
                    f"{lid}: no capability and no exemption — unlocks {dict(types) or 'nothing'}")
    pending = sum(1 for e in exempt.values() if e.get("status") == "pending-capability-design")
    if pending:
        ck.notes.append(f"{pending} lesson(s) carried as 'pending-capability-design': they unlock "
                        f"vocabulary the registry cannot express (G11). Backlog, not a pass.")
    ck.looked_at("lessons", len(c.lessons))
    ck.looked_at("mapped", len(lmap))
    ck.looked_at("exempt", len(exempt))
    return ck


def check_conjugation_coverage(c: Corpus) -> Check:
    """Every inflecting word at a covered level has one paradigm, and every paradigm agrees with it."""
    ck = Check("conjugation_coverage")
    files = sorted((c.root / "corpus" / "conjugations").glob("n*.json"))
    if not files:
        ck.notes.append("no conjugation bank exported — nothing to check")
        return ck
    covered = {p.stem for p in files}      # derived from the tree: adding n2.json extends the gate
    rows: list[tuple[str, dict]] = []
    for p in files:
        for r in json.loads(p.read_text(encoding="utf-8")):
            rows.append((p.stem, r))

    by_slug: Counter = Counter(r["slug"] for _, r in rows)
    for slug, n in by_slug.items():
        if n > 1:
            ck.fail("duplicate", f"{slug}: {n} conjugation rows for one word")
    for flvl, r in rows:
        v = c.v_by_slug.get(r["slug"])
        if v is None:
            ck.fail("row_vs_vocab", f"{r['slug']}: conjugation row resolves to no vocab record")
            continue
        if r.get("vocab_id") is not None and v["id"] != r["vocab_id"]:
            ck.fail("row_vs_vocab", f"{r['slug']}: row carries vocab_id {r['vocab_id']}, "
                                    f"that slug is {v['id']}")
        cls = v.get("verb_class") or v.get("adj_class")
        if r.get("class") != cls:
            ck.fail("row_vs_vocab", f"{r['slug']}: row class {r.get('class')!r} "
                                    f"!= vocab class {cls!r}")
        if r.get("level") != v["level"]:
            ck.fail("row_vs_vocab", f"{r['slug']}: row level {r.get('level')!r} "
                                    f"!= vocab level {v['level']!r}")
        if flvl != v["level"]:
            ck.fail("row_vs_vocab",
                    f"{r['slug']}: row filed under {flvl}.json but the word is {v['level']}")

    missing = [v["slug"] for v in c.vocab
               if v["level"] in covered and (v.get("verb_class") or v.get("adj_class"))
               and v["slug"] not in by_slug]
    for slug in missing:
        v = c.v_by_slug[slug]
        ck.fail("missing_paradigm",
                f"{slug} ({v['headword']}, {v['level']}): inflects but has no conjugation row")
    outside = sum(1 for v in c.vocab if v["level"] not in covered
                  and (v.get("verb_class") or v.get("adj_class")))
    ck.notes.append(f"covered levels {sorted(covered)}; {outside} inflecting word(s) at levels the "
                    f"bank does not cover — information, not a failure")
    ck.looked_at("paradigms", len(rows))
    ck.looked_at("inflecting words", len(rows) + len(missing))
    return ck


def check_vocab_identity(c: Corpus) -> Check:
    """No exported field may address a vocabulary record by a headword that names more than one."""
    ck = Check("vocab_identity")
    ambiguous = {hw: sl for hw, sl in c.headwords.items() if len(sl) > 1}
    by_form: Counter = Counter()
    offenders: dict[str, tuple[str, int]] = {}
    for rel, text in c.json_files():
        for m in VOCAB_REF.finditer(text):
            tok = m.group(1)
            if tok.isdigit():
                by_form["slug"] += 1
                continue
            by_form["headword"] += 1
            if tok in ambiguous:
                prev = offenders.get(tok, (rel, 0))
                offenders[tok] = (prev[0], prev[1] + 1)
    for tok, (rel, n) in sorted(offenders.items(), key=lambda kv: -kv[1][1]):
        cands = ", ".join(f"{s} ({c.v_by_slug[s]['level']})" for s in ambiguous[tok])
        ck.fail("ambiguous_headword",
                f"vocab:{tok} x{n} (e.g. {rel}) is ambiguous — resolves by index order to one of "
                f"{cands}")
    if by_form["headword"] and not offenders:
        ck.notes.append(f"{by_form['headword']} reference(s) still use the headword form, but none of "
                        f"them is ambiguous — they resolve to exactly one record")
    ck.looked_at("`vocab:` strings scanned", sum(by_form.values()))
    ck.looked_at("ambiguous headwords in registry", len(ambiguous))
    return ck


def check_vocab_kanji_registry(c: Corpus, write: bool) -> Check:
    """G18. Characters in vocab.kanji outside the leveled registry are enumerated, not waved through."""
    ck = Check("vocab_kanji_registry")
    unregistered: dict[str, list[str]] = defaultdict(list)
    n_edge = 0
    for v in c.vocab:
        for chx in (v.get("kanji") or []):
            n_edge += 1
            if chx not in c.k_by_char:
                unregistered[chx].append(v["slug"])

    path = c.root / "design" / "unregistered_kanji_chars.json"
    if write:
        doc = {
            "why": ("Characters that appear in vocab.kanji but have no record in corpus/kanji/n*.json. "
                    "The kanji registry holds only leveled characters, so a word like ご馳走 names 馳, "
                    "which is outside the syllabus. The edge is real and expected; it is enumerated "
                    "here so a consumer that renders a kanji chip per character knows which chips have "
                    "no page behind them, and so a NEW dangling character fails the gate instead of "
                    "joining a silent pile (G18)."),
            "generated_by": "scripts/validate/validate_graph_edges.py --write-unregistered",
            "count": len(unregistered),
            "characters": [
                {"char": chx,
                 "reason": "outside the leveled kanji registry",
                 "used_by": sorted(slugs)[:4]}
                for chx, slugs in sorted(unregistered.items())
            ],
        }
        path.write_text(json.dumps(doc, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        ck.notes.append(f"rewrote design/unregistered_kanji_chars.json with "
                        f"{len(unregistered)} character(s)")

    listed: set[str] = set()
    if not path.exists():
        ck.fail("list_missing", "design/unregistered_kanji_chars.json is missing — regenerate it "
                                "with --write-unregistered")
    else:
        doc = json.loads(path.read_text(encoding="utf-8"))
        for e in doc.get("characters") or []:
            chx = e.get("char")
            if chx in listed:
                ck.fail("stale_entry", f"unregistered_chars: {chx} listed twice")
            listed.add(chx)
            if not (e.get("reason") or "").strip():
                ck.fail("stale_entry", f"unregistered_chars: {chx} carries no reason")
            if chx in c.k_by_char:
                ck.fail("stale_entry", f"unregistered_chars: {chx} now HAS a kanji record "
                                       f"({c.k_by_char[chx]['level']}) — delete the entry")
            elif chx not in unregistered:
                ck.fail("stale_entry",
                        f"unregistered_chars: {chx} appears in no vocab.kanji — stale entry")
    for chx, slugs in sorted(unregistered.items()):
        if chx not in listed:
            lv = sorted({c.v_by_slug[s]["level"] for s in slugs})
            ck.fail("unlisted_char", f"vocab.kanji names {chx} ({len(slugs)} word(s), level(s) {lv}) "
                                     f"with no kanji record and no entry in "
                                     f"design/unregistered_kanji_chars.json")
    ck.looked_at("vocab->kanji edges", n_edge)
    ck.looked_at("out-of-registry characters", len(unregistered))
    return ck


def check_reference_integrity(c: Corpus) -> Check:
    """G09. The integer, bare-key and bare-character foreign keys validate_contracts.py cannot see."""
    ck = Check("reference_integrity")
    seen: Counter = Counter()

    def edge(label: str, ok: bool, msg: str) -> None:
        seen[label] += 1
        if not ok:
            ck.fail(label, f"{label}: {msg}")

    for s in c.bank:
        for t in (s.get("tokens") or []):
            vid = t.get("vocab_id")
            if vid is not None:
                edge("sentence.tokens[].vocab_id", vid in c.v_by_id,
                     f"{s['slug']} token {t.get('surface')!r} -> vocab id {vid}")
        for key in (s.get("grammar") or []):
            edge("sentence.grammar[]", key in c.g_by_key, f"{s['slug']} -> grammar key {key!r}")

    for r in c.readings:
        uses = r.get("uses") or {}
        for chx in (uses.get("kanji") or []):
            edge("reading.uses.kanji[]", chx in c.k_by_char, f"{r['slug']} -> kanji {chx!r}")
        for ref in (uses.get("vocab") or []):
            edge("reading.uses.vocab[]", ref in c.v_by_slug, f"{r['slug']} -> vocab {ref!r}")
        for slug in (r.get("source_slugs") or []):
            edge("reading.source_slugs[]", slug in c.s_by_slug, f"{r['slug']} -> sentence {slug!r}")

    for p in sorted((c.root / "corpus" / "exam_banks").glob("*.json")):
        data = json.loads(p.read_text(encoding="utf-8"))
        if not isinstance(data, list):
            continue                       # removed_items.json is a ledger, not a bank
        for it in data:
            iid = it.get("id", p.name)
            if it.get("vocab_id") is not None:
                edge("exam_item.vocab_id", it["vocab_id"] in c.v_by_id,
                     f"{iid} -> vocab id {it['vocab_id']}")
            if it.get("vocab") is not None:
                v = c.v_by_slug.get(it["vocab"])
                edge("exam_item.vocab", v is not None, f"{iid} -> vocab {it['vocab']!r}")
                if v is not None and it.get("vocab_id") is not None and v["id"] != it["vocab_id"]:
                    ck.fail("exam_item.vocab", f"exam_item.vocab: {iid} names {it['vocab']} "
                                               f"(id {v['id']}) but carries vocab_id "
                                               f"{it['vocab_id']}")
            if it.get("grammar") is not None:
                edge("exam_item.grammar", it["grammar"] in c.g_by_key,
                     f"{iid} -> grammar key {it['grammar']!r}")
            if it.get("sentence") is not None:
                edge("exam_item.sentence", it["sentence"] in c.s_by_slug,
                     f"{iid} -> sentence {it['sentence']!r}")
            if it.get("reading") is not None:
                edge("exam_item.reading", it["reading"] in c.r_by_slug,
                     f"{iid} -> reading {it['reading']!r}")

    for p in sorted((c.root / "corpus" / "exercises" / "conjugation").glob("*.json")):
        for d in json.loads(p.read_text(encoding="utf-8")):
            edge("exercise_conjugation.slug", d.get("slug") in c.v_by_slug,
                 f"{d.get('id')} -> vocab {d.get('slug')!r}")
            if d.get("example") is not None:
                edge("exercise_conjugation.example", d["example"] in c.s_by_slug,
                     f"{d.get('id')} -> sentence {d['example']!r}")
    for p in sorted((c.root / "corpus" / "exercises" / "roles").glob("*.json")):
        for d in json.loads(p.read_text(encoding="utf-8")):
            edge("exercise_role.sentence", d.get("sentence") in c.s_by_slug,
                 f"{d.get('id')} -> sentence {d.get('sentence')!r}")

    for p in sorted((c.root / "course" / "speak").rglob("unit-*.json")):
        u = json.loads(p.read_text(encoding="utf-8"))
        for chx in (u.get("kanji_recognition") or []):
            edge("speak_unit.kanji_recognition[]", chx in c.k_by_char,
                 f"{u.get('id')} -> kanji {chx!r}")

    strokes = c.root / "corpus" / "strokes"
    for p in sorted(strokes.glob("n*.json")) + sorted(strokes.glob("lines_n*.json")):
        label = "stroke_lines.character" if p.name.startswith("lines_") else "stroke_order.character"
        for rec in json.loads(p.read_text(encoding="utf-8")):
            edge(label, rec.get("character") in c.k_by_char,
                 f"{p.name}: {rec.get('character')!r} has no kanji record")
    kana_path = strokes / "kana.json"
    if kana_path.exists() and c.kana_chars:
        # validate_stroke_integrity owns the stroke exemptions file; consume the same one here so the
        # two gates cannot disagree about the same rows (small kana + ヴ are declared, with reasons).
        exempt_chars: set = set()
        ex_path = strokes / "exemptions.json"
        if ex_path.exists():
            ex = json.loads(ex_path.read_text(encoding="utf-8"))
            for entry in ex.get("kana_orphans", []):
                if isinstance(entry, dict) and entry.get("char"):
                    exempt_chars.add(entry["char"])
        for rec in json.loads(kana_path.read_text(encoding="utf-8")):
            ch = rec.get("char")
            edge("stroke_kana.char", ch in c.kana_chars or ch in exempt_chars,
                 f"{ch!r} has no kana record and no exemption")

    for label, n in sorted(seen.items()):
        ck.looked_at(label, n)
    ck.notes.append("excluded by design: kanji.components[] (Kradfile radicals are not registry "
                    "records) and vocab.kanji[] (checked by vocab_kanji_registry above)")
    return ck


# --------------------------------------------------------------------------- main

def main() -> int:
    ap = argparse.ArgumentParser(description="validate the exported cross-entity graph")
    ap.add_argument("--root", default=str(Path(__file__).resolve().parents[2]),
                    help="repository root to validate (default: this checkout)")
    ap.add_argument("--write-unregistered", action="store_true",
                    help="regenerate design/unregistered_kanji_chars.json from the current vocab")
    args = ap.parse_args()

    root = Path(args.root).resolve()
    if not (root / "corpus").is_dir():
        print(f"validate_graph_edges: {root} has no corpus/ directory", file=sys.stderr)
        return 2
    c = Corpus(root)

    print("================ GRAPH EDGES ================")
    checks = [
        check_registries_present(c),
        check_kanji_example_links(c),
        check_family_graph(c),
        check_capability_coverage(c),
        check_conjugation_coverage(c),
        check_vocab_identity(c),
        check_vocab_kanji_registry(c, args.write_unregistered),
        check_reference_integrity(c),
    ]
    for ck in checks:
        ck.report()

    total = sum(len(ck.fails) for ck in checks)
    edges = sum(sum(ck.counts.values()) for ck in checks if ck.name != "registries_present")
    broken = [ck.name for ck in checks if ck.fails]
    print(f"\nvalidate_graph_edges: {edges} edges over {len(checks)} checks, "
          + (f"FAIL {total} in {', '.join(broken)}" if total else "ALL OK"))
    return 1 if total else 0


if __name__ == "__main__":
    sys.exit(main())
