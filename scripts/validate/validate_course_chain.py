#!/usr/bin/env python3
"""Hard gate: the exported manifest -> course -> topic -> lesson chain agrees with itself, and every
published JSON artifact is accounted for.

WHY THIS EXISTS
---------------
The courseware is published four times over: a manifest that counts topics and lessons, a course.json
whose topic stubs carry a copy of each topic's title/theme/order and an `unlocks_summary`, a topic.json
whose lesson stubs carry a copy of each lesson's title/description/needs/unlocks, and the lesson leaf
that is the actual source of truth. Nothing forced those four views to agree, and they drifted:

  * STRUCT-10 — 33 of 52 topic `unlocks_summary` blocks and the whole of course/outline.json reported
    the wrong number of items taught (top:n5-kanji-exame declared {vocab:0,kanji:0,grammar:0} while its
    lessons taught 23 kanji), and course/outline.json still listed pre-migration refs
    (kanji:会/新/社 under top:n4-forma-simples, which no lesson there unlocks any more). A number the UI
    prints is data like any other; both files are DERIVED and are now gated as derived.
  * Neither course/outline.json nor course/vocab_disambiguation_review.json appeared in
    contracts/manifest.json, so nothing schema-checked or graph-checked them — they were published,
    consumed, and invisible to every gate in the suite.
  * STRUCT-14 pinned two structural facts that look like bugs and are not: topic `order` is ONE global
    1..52 sequence (not per-level 1..n) and the directory prefix encodes the same number. Both are
    asserted here so the next renumbering cannot quietly break them.
  * The orphan-leaf failure mode (the one that put 223 files under archive/) is checked in both
    directions: every path the chain declares exists, and every lesson/topic file on disk is named by
    the chain.

audit_manifest.py walks the same chain but only checks that paths resolve and counts match; it reads
the SQLite index for sentence refs and never compares a parent's stub against its child. This validator
is the stricter, JSON-only replacement for the structural half of that walk.

WHAT IS DERIVED, AND FROM WHAT
------------------------------
`unlocks_summary` and outline `counts` are the number of DISTINCT vocab/kanji/grammar refs a topic's
lessons unlock; outline `introduces_refs` is that same set as an ordered list, in first-unlock order
(lesson order within the topic, unlock order within the lesson). Raw and distinct counts coincide on the
current tree — a ref unlocked twice inside one topic is validate_unlock_ledger's finding, not this one.

Reads exported JSON only; never db/corpus.sqlite.
Exit 0 only when every tier agrees. Usage: validate_course_chain.py [--root PATH] [--list]
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from collections import defaultdict
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]

MAX_REPORT = 15                       # FAIL lines printed; the rest are counted
KINDS = ("vocab", "kanji", "grammar")  # the three kinds the summaries count
SPEAK_DIR = "speak"                    # course/speak/ is its own path with its own validator
TOPIC_DIR = re.compile(r"^topic-(\d{2})-[a-z0-9-]+$")


def load(path: Path) -> object:
    return json.loads(path.read_text(encoding="utf-8"))


def pt(value: object) -> object:
    """Unwrap a locale object down to its pt-BR string; pass anything else through unchanged."""
    if isinstance(value, dict) and "pt-BR" in value:
        return value["pt-BR"]
    return value


def unlock_pairs(record: dict) -> list[tuple[str, str]]:
    return sorted((u.get("type"), u.get("ref")) for u in record.get("unlocks", []) or [])


class Chain:
    """One walk of manifest -> course -> topic -> lesson, collecting everything the checks need."""

    def __init__(self, root: Path) -> None:
        self.root = root
        self.course = root / "course"
        self.fails: list[str] = []
        self.courses: list[dict] = []       # course.json records, in manifest order
        self.topics: list[dict] = []        # topic.json records, in course order
        self.lessons: list[dict] = []       # lesson leaves, in topic order
        self.chained: set[Path] = set()     # every file the chain names
        self.topic_of_course: dict[str, list[dict]] = defaultdict(list)
        self.introduces: dict[str, dict[str, list[str]]] = {}  # topic id -> kind -> ordered refs

    def fail(self, msg: str) -> None:
        self.fails.append(msg)

    def walk(self) -> None:
        man_path = self.course / "manifest.json"
        if not man_path.exists():
            self.fail(f"course/manifest.json missing under {self.root}")
            return
        man = load(man_path)
        entries = man.get("courses", [])
        if not entries:
            self.fail("course/manifest.json declares no courses")
            return

        orders = [c.get("order") for c in entries]
        if sorted(orders) != list(range(1, len(entries) + 1)):
            self.fail(f"course.order is not contiguous 1..{len(entries)}: {orders}")
        if orders != sorted(orders):
            self.fail(f"courses are not listed in ascending order in manifest.json: {orders}")

        for stub in entries:
            self._course(stub)

    # -- tier 1 -----------------------------------------------------------------
    def _course(self, stub: dict) -> None:
        cid = stub.get("id", "<no id>")
        cpath = self.course / stub.get("path", "")
        if not cpath.exists():
            self.fail(f"{cid}: manifest path does not resolve: {stub.get('path')}")
            return
        self.chained.add(cpath.resolve())
        cd = load(cpath)
        self.courses.append(cd)
        for field in ("id", "level", "order", "title"):
            if stub.get(field) != cd.get(field):
                self.fail(f"{cid}: manifest stub {field}={stub.get(field)!r} != course.json {cd.get(field)!r}")

        topics = cd.get("topics", [])
        if stub.get("topic_count") != len(topics):
            self.fail(f"{cid}: manifest topic_count={stub.get('topic_count')} != {len(topics)} topics in course.json")

        torders = [t.get("order") for t in topics]
        if torders != sorted(torders):
            self.fail(f"{cid}: topics are not listed in ascending `order` inside course.json: {torders}")

        lesson_total = 0
        for tstub in topics:
            lesson_total += self._topic(cd, cpath, tstub)
        if stub.get("lesson_count") != lesson_total:
            self.fail(f"{cid}: manifest lesson_count={stub.get('lesson_count')} != {lesson_total} summed from topics")

    # -- tier 2 -----------------------------------------------------------------
    def _topic(self, cd: dict, cpath: Path, tstub: dict) -> int:
        tid = tstub.get("id", "<no id>")
        rel = tstub.get("path", "")
        tpath = cpath.parent / rel
        if not tpath.exists():
            self.fail(f"{tid}: course.json path does not resolve: {rel}")
            return 0
        self.chained.add(tpath.resolve())
        td = load(tpath)
        self.topics.append(td)
        self.topic_of_course[cd.get("id")].append(td)

        for field in ("id", "order", "title", "theme"):
            if tstub.get(field) != td.get(field):
                self.fail(f"{tid}: course.json stub {field}={pt(tstub.get(field))!r} "
                          f"!= topic.json {pt(td.get(field))!r}")
        if td.get("level") != cd.get("level"):
            self.fail(f"{tid}: topic.json level={td.get('level')!r} != course level {cd.get('level')!r}")

        dirname = rel.split("/")[0]
        m = TOPIC_DIR.match(dirname)
        if not m:
            self.fail(f"{tid}: directory {dirname!r} is not topic-<order:02d>-<slug>")
        elif int(m.group(1)) != (td.get("order") or -1):
            self.fail(f"{tid}: directory {dirname!r} encodes order {int(m.group(1))}, topic.order is {td.get('order')}")

        lessons = td.get("lessons", [])
        if tstub.get("lesson_count") != len(lessons):
            self.fail(f"{tid}: course.json lesson_count={tstub.get('lesson_count')} != {len(lessons)} in topic.json")
        lorders = [L.get("order") for L in lessons]
        if lorders != list(range(1, len(lessons) + 1)):
            self.fail(f"{tid}: lesson orders are not contiguous 1..{len(lessons)}: {lorders}")

        seq: dict[str, list[str]] = {k: [] for k in KINDS}
        for lstub in lessons:
            self._lesson(cd, cpath, td, lstub, seq)
        self.introduces[tid] = seq

        want = {k: len(seq[k]) for k in KINDS}
        got = tstub.get("unlocks_summary")
        if got != want:
            self.fail(f"{tid}: unlocks_summary {got} != recomputed from lesson leaves {want}")
        return len(lessons)

    # -- tier 3 -----------------------------------------------------------------
    def _lesson(self, cd: dict, cpath: Path, td: dict, lstub: dict,
                seq: dict[str, list[str]]) -> None:
        lid = lstub.get("id", "<no id>")
        rel = lstub.get("path", "")
        lpath = cpath.parent / rel
        if not lpath.exists():
            self.fail(f"{lid}: topic.json path does not resolve: {rel}")
            return
        self.chained.add(lpath.resolve())
        ld = load(lpath)
        self.lessons.append(ld)

        order = ld.get("order")
        if not isinstance(order, int):
            self.fail(f"{lid}: leaf `order` is {order!r}, not an integer")
        else:
            if lpath.name != f"lesson-{order:02d}.json":
                self.fail(f"{lid}: filename {lpath.name!r} does not match lesson-{order:02d}.json")
            if not str(lid).endswith(f"-{order:02d}"):
                self.fail(f"{lid}: lesson id does not end in -{order:02d}")

        for field in ("id", "order", "title", "description", "needs"):
            if lstub.get(field) != ld.get(field):
                self.fail(f"{lid}: topic.json stub {field}={pt(lstub.get(field))!r} "
                          f"!= leaf {pt(ld.get(field))!r}")
        if unlock_pairs(lstub) != unlock_pairs(ld):
            a, b = unlock_pairs(lstub), unlock_pairs(ld)
            only_stub = sorted(set(a) - set(b))[:3]
            only_leaf = sorted(set(b) - set(a))[:3]
            self.fail(f"{lid}: topic.json stub unlocks ({len(a)}) != leaf unlocks ({len(b)}); "
                      f"stub-only {only_stub} leaf-only {only_leaf}")
        if ld.get("topic") != td.get("id"):
            self.fail(f"{lid}: leaf topic={ld.get('topic')!r} != containing topic {td.get('id')!r}")
        if ld.get("level") != cd.get("level"):
            self.fail(f"{lid}: leaf level={ld.get('level')!r} != course level {cd.get('level')!r}")

        for u in ld.get("unlocks", []) or []:
            kind, ref = u.get("type"), u.get("ref")
            if kind in seq and ref not in seq[kind]:
                seq[kind].append(ref)


def check_global_order(chain: Chain) -> list[str]:
    """Topic `order` is ONE global contiguous sequence, ascending across courses (STRUCT-14)."""
    fails: list[str] = []
    flat: list[int] = []
    for cd in chain.courses:
        for td in chain.topic_of_course[cd.get("id")]:
            flat.append(td.get("order"))
    if any(o is None for o in flat):
        return [f"{sum(o is None for o in flat)} topics have no `order`"]
    if sorted(flat) != list(range(1, len(flat) + 1)):
        dups = sorted({o for o in flat if flat.count(o) > 1})
        gaps = sorted(set(range(1, len(flat) + 1)) - set(flat))
        fails.append(f"topic `order` across all courses is not contiguous 1..{len(flat)} "
                     f"(duplicates {dups[:8]}, gaps {gaps[:8]})")
    if flat != sorted(flat):
        fails.append(f"topic `order` does not ascend across courses taken in course.order: {flat}")
    return fails


def check_unique_ids(chain: Chain) -> list[str]:
    fails: list[str] = []
    for label, records in (("topic", chain.topics), ("lesson", chain.lessons)):
        seen: dict[str, int] = defaultdict(int)
        for r in records:
            seen[str(r.get("id"))] += 1
        for rid, n in sorted(seen.items()):
            if n > 1:
                fails.append(f"{label} id {rid!r} is declared by {n} files — ids must be globally unique")
    return fails


def check_filesystem(chain: Chain) -> list[str]:
    """No orphan and no duplicate leaf: every *.json under a level dir is named by the chain."""
    fails: list[str] = []
    levels = {cd.get("level") for cd in chain.courses}
    on_disk_dirs = {d.name for d in chain.course.iterdir()
                    if d.is_dir() and d.name not in (SPEAK_DIR, "archive")}
    for extra in sorted(on_disk_dirs - levels):
        fails.append(f"course/{extra}/ is on disk but no course in manifest.json claims that level")
    for missing in sorted(levels - on_disk_dirs):
        fails.append(f"manifest declares level {missing!r} but course/{missing}/ is not a directory")

    on_disk: set[Path] = set()
    for level in sorted(levels & on_disk_dirs):
        for p in (chain.course / level).rglob("*.json"):
            if "archive" in p.parts:
                continue
            on_disk.add(p.resolve())
    for orphan in sorted(on_disk - chain.chained):
        fails.append(f"orphan file not reachable from the chain: {orphan.relative_to(chain.root).as_posix()}")
    return fails


def check_outline(chain: Chain) -> list[str]:
    """course/outline.json is a projection of the leaves, not a remembered copy (STRUCT-10)."""
    fails: list[str] = []
    path = chain.course / "outline.json"
    if not path.exists():
        return ["course/outline.json is missing"]
    outline = load(path)
    if not isinstance(outline, list):
        return ["course/outline.json is not a list of courses"]

    by_slug = {c.get("slug"): c for c in outline}
    if len(by_slug) != len(outline):
        fails.append("course/outline.json repeats a course slug")
    declared = [c.get("slug") for c in outline]
    expected = [cd.get("id") for cd in chain.courses]
    if declared != expected:
        fails.append(f"outline course list {declared} != manifest course order {expected}")

    for cd in chain.courses:
        oc = by_slug.get(cd.get("id"))
        if oc is None:
            fails.append(f"outline has no entry for course {cd.get('id')}")
            continue
        for field, want in (("level", cd.get("level")), ("order", cd.get("order")),
                            ("title", pt(cd.get("title"))), ("overview", pt(cd.get("overview")))):
            if oc.get(field) != want:
                fails.append(f"outline {cd.get('id')}: {field}={oc.get(field)!r} != course.json {want!r}")
        ot = {t.get("slug"): t for t in oc.get("topics", [])}
        want_order = [td.get("id") for td in chain.topic_of_course[cd.get("id")]]
        if [t.get("slug") for t in oc.get("topics", [])] != want_order:
            fails.append(f"outline {cd.get('id')}: topic list/order differs from course.json")
        for td in chain.topic_of_course[cd.get("id")]:
            tid = td.get("id")
            o = ot.get(tid)
            if o is None:
                fails.append(f"outline has no entry for topic {tid}")
                continue
            for field, want in (("order", td.get("order")), ("title", pt(td.get("title"))),
                                ("theme", td.get("theme"))):
                if o.get(field) != want:
                    fails.append(f"outline {tid}: {field}={o.get(field)!r} != topic.json {want!r}")
            want_obj = [pt(x) for x in td.get("objectives", []) or []]
            if (o.get("objectives") or []) != want_obj:
                fails.append(f"outline {tid}: objectives differ from topic.json")
            seq = chain.introduces.get(tid, {k: [] for k in KINDS})
            if o.get("counts") != {k: len(seq[k]) for k in KINDS}:
                fails.append(f"outline {tid}: counts {o.get('counts')} "
                             f"!= recomputed {{{', '.join(f'{k}: {len(seq[k])}' for k in KINDS)}}}")
            refs = o.get("introduces_refs") or {}
            names = o.get("introduces") or {}
            for kind in KINDS:
                got = refs.get(kind, [])
                if got != seq[kind]:
                    extra = sorted(set(got) - set(seq[kind]))[:3]
                    absent = sorted(set(seq[kind]) - set(got))[:3]
                    fails.append(f"outline {tid}: introduces_refs.{kind} ({len(got)}) "
                                 f"!= lesson unlocks ({len(seq[kind])}); stale {extra} missing {absent}")
                if len(names.get(kind, [])) != len(got):
                    fails.append(f"outline {tid}: introduces.{kind} has {len(names.get(kind, []))} "
                                 f"display names for {len(got)} refs")
    return fails


def check_catalogue(root: Path) -> tuple[list[str], int, int]:
    """Every published *.json under course/ and corpus/ is claimed by an entity or listed as generated."""
    fails: list[str] = []
    cpath = root / "contracts" / "manifest.json"
    if not cpath.exists():
        return ([f"contracts/manifest.json missing under {root}"], 0, 0)
    claimed: set[Path] = set()
    for entity in load(cpath).get("entities", []):
        glob = entity.get("files")
        if not glob:
            continue
        # A file matched by an entity glob must also LOOK like that entity: a sidecar dropped inside
        # a registry directory (the unregistered_chars.json incident broke four gates) would
        # otherwise count as catalogued while poisoning every consumer of the glob. Packing 'list'
        # entities are JSON arrays; 'map'/'single' are objects.
        packing = entity.get("packing", "list")
        want = list if packing == "list" else dict
        for p in root.glob(glob):
            claimed.add(p.resolve())
            try:
                top = load(p)
            except Exception as exc:
                fails.append(f"{p}: matched by {entity.get('entity')} glob but unreadable: {exc}")
                continue
            if not isinstance(top, want):
                fails.append(f"{p}: matched by the {entity.get('entity')} glob but is a "
                             f"{type(top).__name__}, not the entity's {packing} packing — a sidecar "
                             f"inside a registry glob poisons every consumer; move it out")

    listed: dict[Path, str] = {}
    gpath = root / "design" / "generated_artifacts.json"
    if gpath.exists():
        for entry in load(gpath).get("files", []):
            resolved = (root / entry["path"]).resolve()
            if resolved in listed:
                fails.append(f"design/generated_artifacts.json lists {entry['path']} twice")
            listed[resolved] = entry.get("reason", "")
            if not entry.get("reason"):
                fails.append(f"design/generated_artifacts.json: {entry['path']} carries no reason")
    else:
        fails.append("design/generated_artifacts.json missing — the uncatalogued-artifact list is the "
                     "only thing keeping an unschema'd published file visible")

    published: set[Path] = set()
    for area in ("course", "corpus"):
        for p in (root / area).rglob("*.json"):
            if "archive" in p.parts:
                continue
            published.add(p.resolve())

    for p in sorted(published - claimed - set(listed)):
        fails.append(f"published but uncatalogued: {p.relative_to(root).as_posix()} — add it to "
                     f"contracts/manifest.json or to design/generated_artifacts.json with a reason")
    for p in sorted(set(listed) - published):
        fails.append(f"design/generated_artifacts.json lists {p.relative_to(root).as_posix()}, "
                     f"which is not published — a stale exemption is a failure")
    for p in sorted(set(listed) & claimed):
        fails.append(f"design/generated_artifacts.json lists {p.relative_to(root).as_posix()}, "
                     f"but contracts/manifest.json already catalogues it — remove the exemption")
    return fails, len(published), len(listed)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[2],
                    help="repo root to validate (default: this checkout)")
    ap.add_argument("--list", action="store_true", help="print every failure, not just the first 15")
    args = ap.parse_args()
    root = args.root.resolve()

    chain = Chain(root)
    chain.walk()
    fails = list(chain.fails)
    fails += check_global_order(chain)
    fails += check_unique_ids(chain)
    fails += check_filesystem(chain)
    fails += check_outline(chain)
    cat_fails, published, listed = check_catalogue(root)
    fails += cat_fails

    print(f"course chain: {len(chain.courses)} courses, {len(chain.topics)} topics, "
          f"{len(chain.lessons)} lessons, {len(chain.chained)} chained files")
    print(f"catalogue: {published} published JSON under course/ + corpus/, "
          f"{listed} listed as generated-not-schema'd")
    if fails:
        print(f"=== {len(fails)} FAIL ===")
        for f in fails if args.list else fails[:MAX_REPORT]:
            print(f"  FAIL {f}")
        if not args.list and len(fails) > MAX_REPORT:
            print(f"  ... {len(fails) - MAX_REPORT} more (re-run with --list)")
        return 1
    print("=== 0 FAIL — chain tiers agree, derived summaries recompute, every artifact catalogued ===")
    return 0


if __name__ == "__main__":
    sys.exit(main())
