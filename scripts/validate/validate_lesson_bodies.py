#!/usr/bin/env python3
"""Gate the lesson BODY string in the exported courseware — the one artifact no gate was reading.

WHY THIS EXISTS (the defect it was built for). CLAUDE.md names the committed JSON under `course/`
the source of truth, yet every hard rule about a lesson body lived in `validate_lessons.py`, which
reads `db/corpus.sqlite` — a regenerable index whose 259-of-322 bodies had already drifted from the
export. The 2026-08-26 course review found what that blind spot cost:
  * 80 `<check item-ref="vocab:…">` chips across 34 lessons still spoke the retired
    `vocab:<headword>` scheme and resolved to nothing in `corpus/vocab/*.json`, 5 of them naming an
    ambiguous headword (vocab:人, vocab:先, vocab:米, vocab:居る, vocab:分) — while
    `audit_export_refs.py` printed "0 FAIL" because its REF_RX never matched the `item-ref`
    attribute, and `validate_contracts.py` never opened the body at all (to it, a body is one opaque
    string that does not start with an id prefix);
  * `<jp reading="">合</jp>` and `<jp reading="">専門</jp>` shipped in les:n4-aspecto-07, invisible to
    `validate_furigana.py` because that gate returns early on `if not HIRA.search(plain)` — the
    857 pure-kanji bases, exactly the spans where the reading is the ONLY pronunciation the learner
    ever sees, were unchecked;
  * 11 N3 exercise prompts carried raw `<jp>` markup in a field that is HTML-escaped on the way out,
    so the learner read the tag verbatim.
Every one of those is repaired at HEAD. This validator is what keeps them repaired, reading the
exported JSON and nothing else.

CHECKS (all hard unless marked advisory):
  wellformed   balanced markup: no stray/mismatched end tag, nothing left open, body non-empty,
               last root-level block is <checklist>
  refs         EVERY ref-bearing attribute resolves against the EXPORTED corpus, for ALL kinds —
               <vocab|kanji|grammar|sentence|reading ref>, <stroke ref>, <check item-ref>,
               <flashcard ref>, <exercise ref> (against the lesson's own exercises[].id), plus
               <ruby base/reading> shape. img:/aud:/vid: warn (asset registry still deferred).
  vocab-slug   every whole-string `vocab:…` identifier in course/ is a numeric JMdict slug, never a
               headword — the migration has to stay migrated
  furigana     <jp reading="…"> is non-empty whenever the base carries kanji, is kana-only, and
               covers the hiragana literally present in the base (the subsequence rule ported from
               validate_furigana.py, which reads the DB and skips pure-kanji bases)
  plaintext    no XML/HTML markup in any plain-text learner-facing field: lesson title/description/
               objectives, exercise prompt/explanation and every string inside exercise answer, and
               the locale strings of topic.json / course.json

Reads course/**/*.json + corpus/**; never db/corpus.sqlite. Exit 1 on any FAIL.
Usage: validate_lesson_bodies.py [--root PATH] [--list]
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter
from html.parser import HTMLParser
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]

DEFAULT_ROOT = Path(__file__).resolve().parents[2]
LOC = "pt-BR"
MAX_PRINT = 15

# Elements written as <tag …/>: html.parser hands them to handle_startendtag, but an author may also
# write a bare <break>, so they are exempted from the "still open at EOF" rule rather than required
# to close. Everything else must be closed explicitly.
SELF_CLOSING = {"sentence", "stroke", "reading", "exercise", "kanji", "vocab", "grammar", "break",
                "ruby", "image", "video", "audio", "divider"}
# Root-level containers, in the sense of design/lesson_schema.md: the body must end with <checklist>.
BLOCK = {"heading", "p", "note", "list", "item", "image", "video", "audio", "sentence", "stroke",
         "reading", "exercise", "flashcard", "front", "back", "checklist", "check", "divider"}
# attr key -> namespaces the schema allows there (mirrors validate_lessons.py REF_NS)
REF_NS = {
    "sentence.ref": {"sent"}, "stroke.ref": {"kanji", "kana"}, "kanji.ref": {"kanji"},
    "vocab.ref": {"vocab"}, "reading.ref": {"read"}, "grammar.ref": {"gram"}, "exercise.ref": {"ex"},
    "image.ref": {"img"}, "video.ref": {"vid"}, "audio.ref": {"aud"},
    "flashcard.ref": {"vocab", "kanji", "kana"},
    "check.item-ref": {"vocab", "kanji", "gram", "grammar", "kana", "sent", "read"},
}
DEFERRED_NS = {"img", "aud", "vid"}

JPTAG = re.compile(r'<jp\s+reading="([^"]*)"\s*>(.*?)</jp>', re.S)
TAGS = re.compile(r"<[^>]+>")
HIRA = re.compile(r"[ぁ-ん]")            # deliberately excludes ー and katakana
KANJI = re.compile(r"[一-鿿々〆]")
DIGIT = re.compile(r"[0-9０-９]")
# kana blocks (which already contain ー ゝ ゞ ヽ ヾ) + the punctuation a reading may legitimately echo
READING_OK = re.compile(r"[ぁ-ゟ゠-ヿ、。・？！～〜「」『』（）()… 　]")
# One tag anywhere in a field that is HTML-escaped on the way out (render-body.server.ts `esc`).
# A bare '<' used as a comparison sign does not match, so no exemption list is needed.
MARKUP = re.compile(r"</?[a-z][a-z0-9-]*(\s[^<>]*)?/?>", re.I)
VOCAB_SLUG = re.compile(r"^vocab:(.+)$")


# ---------------------------------------------------------------- corpus pools


def _records(path: Path, key: str) -> list:
    """Every record in a corpus file, whatever the packing (bare list, or {key: [...]})."""
    try:
        d = json.loads(path.read_text(encoding="utf-8"))
    except Exception:  # noqa: BLE001 — a malformed corpus file is another gate's finding
        return []
    if isinstance(d, list):
        return d
    if isinstance(d, dict):
        v = d.get(key)
        if isinstance(v, list):
            return v
        return [x for vals in d.values() if isinstance(vals, list) for x in vals]
    return []


def load_pools(corpus: Path) -> dict[str, set[str]]:
    kanji = {f"kanji:{r['character']}" for f in (corpus / "kanji").glob("*.json")
             for r in _records(f, "kanji") if isinstance(r, dict) and r.get("character")}
    vocab = {r["slug"] for f in (corpus / "vocab").glob("*.json")
             for r in _records(f, "vocab") if isinstance(r, dict) and r.get("slug")}
    gram = {f"gram:{r['key']}" for f in (corpus / "grammar").glob("*.json")
            for r in _records(f, "grammar") if isinstance(r, dict) and r.get("key")}
    sent = {r["slug"] for r in _records(corpus / "sentences" / "bank.json", "sentences")
            if isinstance(r, dict) and r.get("slug")}
    read = {r["slug"] for f in (corpus / "readings").glob("*.json")
            for r in _records(f, "readings") if isinstance(r, dict) and r.get("slug")}
    # kana: family ids (kana:hiragana-a) AND glyph ids (kana:hiragana-あ) are both legal item-refs
    kana: set[str] = set()
    kana_char: dict[str, str] = {}
    fam = corpus / "kana" / "families.json"
    if fam.exists():
        fd = json.loads(fam.read_text(encoding="utf-8"))
        for grp in (fd.values() if isinstance(fd, dict) else [fd]):
            for f in (grp if isinstance(grp, list) else []):
                if isinstance(f, dict) and f.get("id"):
                    kana.add(f["id"])
    for name in ("hiragana.json", "katakana.json"):
        p = corpus / "kana" / name
        if p.exists():
            for r in _records(p, name.split(".")[0]):
                if isinstance(r, dict) and r.get("id"):
                    kana.add(r["id"])
                    kana_char[r["id"]] = r.get("char", "")
    strokes_kanji = {r["character"] for f in (corpus / "strokes").glob("n*.json")
                     for r in _records(f, "strokes")
                     if isinstance(r, dict) and r.get("character") and "lines" not in f.stem}
    strokes_kana = {r["char"] for r in _records(corpus / "strokes" / "kana.json", "strokes")
                    if isinstance(r, dict) and r.get("char")}
    return {"kanji": kanji, "vocab": vocab, "gram": gram, "grammar": gram, "sent": sent,
            "read": read, "kana": kana, "_stroke_kanji": strokes_kanji,
            "_stroke_kana": strokes_kana, "_kana_char": kana_char}  # type: ignore[dict-item]


# ---------------------------------------------------------------- body parser


class BodyParser(HTMLParser):
    """Balance-only parser: it says nothing about the element whitelist (that is validate_lessons'
    job) so that a whitelist change cannot silently turn this gate off."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.errors: list[str] = []
        self.stack: list[str] = []
        self.top_blocks: list[str] = []
        self.refs: list[tuple[str, str]] = []   # (attr key "tag.attr", value)
        self.rubies: list[dict] = []

    def _open(self, tag: str, attrs: list) -> None:
        ad = dict(attrs)
        if tag == "ruby":
            self.rubies.append(ad)
        for a in ("ref", "item-ref"):
            if a in ad:
                self.refs.append((f"{tag}.{a}", ad[a] or ""))
        if not self.stack and tag in BLOCK:
            self.top_blocks.append(tag)
        self.stack.append(tag)

    def handle_starttag(self, tag, attrs):
        self._open(tag, attrs)

    def handle_startendtag(self, tag, attrs):
        self._open(tag, attrs)
        self.stack.pop()

    def handle_endtag(self, tag):
        if self.stack and self.stack[-1] == tag:
            self.stack.pop()
        elif tag in self.stack:
            while self.stack and self.stack.pop() != tag:
                pass
            self.errors.append(f"mismatched/overlapping </{tag}>")
        else:
            self.errors.append(f"stray </{tag}>")

    def finish(self) -> None:
        for tag in self.stack:
            if tag not in SELF_CLOSING:
                self.errors.append(f"<{tag}> still open at end of body")


# ---------------------------------------------------------------- helpers


def walk_strings(v, path: str = ""):
    """Yield (path, string) for every string in a JSON tree."""
    if isinstance(v, str):
        yield path, v
    elif isinstance(v, dict):
        for k, x in v.items():
            yield from walk_strings(x, f"{path}.{k}" if path else str(k))
    elif isinstance(v, list):
        for i, x in enumerate(v):
            yield from walk_strings(x, f"{path}[{i}]")


def missing_kana(reading: str, text: str) -> str:
    """First hiragana of `text` the reading fails to cover, or ''. Ported verbatim from
    validate_furigana.py — that subsequence rule is correct; what it lacked was reaching the spans
    with no hiragana at all."""
    required = HIRA.findall(TAGS.sub("", text))
    it = iter(reading)
    for ch in required:
        if ch not in it:
            return ch
    return ""


def bad_reading_chars(reading: str, base: str) -> list[str]:
    """Characters a furigana reading may not contain. ASCII/full-width digits are allowed only when
    the SAME digit stands literally in the annotated base (les:n3-estrutura-05 writes この10年 and
    reads この10ねん); a kanji echoed from the base is still a failure."""
    bad = []
    for ch in reading:
        if READING_OK.match(ch):
            continue
        if DIGIT.match(ch) and ch in base:
            continue
        bad.append(ch)
    return bad


def check_furigana(fails: list[str], stats: Counter, where: str, text: str) -> None:
    for reading, base in JPTAG.findall(text or ""):
        stats["spans"] += 1
        plain = TAGS.sub("", base)
        if not reading.strip():
            if KANJI.search(plain):
                stats["empty"] += 1
                fails.append(f"{where}: <jp reading=\"\"> on a kanji base '{plain}' — the reading is "
                             f"the only pronunciation the learner gets")
            else:
                stats["empty_kana_base"] += 1  # advisory: redundant but harmless on a kana-only base
            continue
        bad = bad_reading_chars(reading, plain)
        if bad:
            stats["non_kana"] += 1
            fails.append(f"{where}: <jp reading=\"{reading}\"> is not kana-only "
                         f"(offending: {' '.join(sorted(set(bad)))}) on base '{plain}'")
            continue
        miss = missing_kana(reading, base)
        if miss:
            stats["coverage"] += 1
            fails.append(f"{where}: furigana '{reading}' does not cover '{miss}' of base '{plain}'")


# ---------------------------------------------------------------- main


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=str(DEFAULT_ROOT), help="repo root (point at a mutated copy to test)")
    ap.add_argument("--list", action="store_true", help="print every failure, not just the first 15")
    args = ap.parse_args()
    root = Path(args.root).resolve()
    course, corpus = root / "course", root / "corpus"
    if not course.exists():
        print(f"validate_lesson_bodies: no course/ under {root}")
        return 1

    pools = load_pools(corpus)
    stroke_kanji: set[str] = pools.pop("_stroke_kanji")      # type: ignore[assignment]
    stroke_kana: set[str] = pools.pop("_stroke_kana")        # type: ignore[assignment]
    kana_char: dict[str, str] = pools.pop("_kana_char")      # type: ignore[assignment]

    fail: dict[str, list[str]] = {k: [] for k in
                                  ("wellformed", "refs", "vocab-slug", "furigana", "plaintext")}
    warns: list[str] = []
    stats: Counter = Counter()
    by_kind: Counter = Counter()

    leaves = sorted(course.glob("*/topic-*/lesson-*.json"))
    for leaf in leaves:
        d = json.loads(leaf.read_text(encoding="utf-8"))
        lid = d.get("id") or leaf.stem
        body = d.get("body") or ""
        stats["lessons"] += 1

        # --- wellformedness -------------------------------------------------
        p = BodyParser()
        try:
            p.feed(body)
            p.close()
            p.finish()
        except Exception as e:  # noqa: BLE001
            fail["wellformed"].append(f"{lid}: parse crash: {e}")
            continue
        for e in p.errors:
            fail["wellformed"].append(f"{lid}: {e}")
        if not p.top_blocks:
            fail["wellformed"].append(f"{lid}: empty body (no root-level block elements)")
        elif p.top_blocks[-1] != "checklist":
            fail["wellformed"].append(
                f"{lid}: body must end with <checklist> (last root block is <{p.top_blocks[-1]}>)")

        # --- ruby shape -----------------------------------------------------
        for ad in p.rubies:
            stats["ruby"] += 1
            if not (ad.get("base") or "").strip() or not (ad.get("reading") or "").strip():
                fail["refs"].append(f"{lid}: <ruby> missing base/reading ({ad})")
                continue
            bad = bad_reading_chars(ad["reading"], ad["base"])
            if bad:
                fail["furigana"].append(
                    f"{lid}: <ruby base=\"{ad['base']}\" reading=\"{ad['reading']}\"> is not kana-only "
                    f"(offending: {' '.join(sorted(set(bad)))})")

        # --- every ref-bearing attribute resolves ---------------------------
        ex_ids = {ex.get("id") for ex in (d.get("exercises") or []) if isinstance(ex, dict)}
        for key, val in p.refs:
            stats["refs"] += 1
            if ":" not in val:
                fail["refs"].append(f"{lid}: <{key}> ref '{val}' has no namespace prefix")
                continue
            ns, ident = val.split(":", 1)
            by_kind[f"{key}:{ns}"] += 1
            allowed = REF_NS.get(key)
            if allowed is None:
                warns.append(f"{lid}: <{key}> is not a known ref-bearing attribute (ref '{val}')")
                continue
            if ns not in allowed:
                fail["refs"].append(
                    f"{lid}: <{key}> ref '{val}': namespace '{ns}' not allowed (want {sorted(allowed)})")
                continue
            if ns in DEFERRED_NS:
                warns.append(f"{lid}: <{key}> ref '{val}' targets the deferred asset registry")
                continue
            if key == "exercise.ref":
                if val not in ex_ids:
                    fail["refs"].append(f"{lid}: <exercise ref='{val}'/> is not an exercise of this lesson")
                continue
            if key == "stroke.ref":
                ok = (ident in stroke_kanji) if ns == "kanji" else (kana_char.get(val, ident) in stroke_kana)
                if not ok:
                    fail["refs"].append(f"{lid}: <stroke ref='{val}'/> has no stroke record in corpus/strokes")
                continue
            pool = pools.get(ns)
            if pool is None:
                fail["refs"].append(f"{lid}: <{key}> ref '{val}': unknown namespace '{ns}'")
            elif val not in pool:
                fail["refs"].append(f"{lid}: <{key}> ref '{val}' does not resolve in the exported corpus")

        # --- furigana in the body -------------------------------------------
        check_furigana(fail["furigana"], stats, lid, body)

        # --- plain-text fields carry no markup ------------------------------
        plain_fields: list[tuple[str, object]] = [
            ("title", d.get("title")), ("description", d.get("description")),
            ("objectives", d.get("objectives")),
        ]
        for ex in (d.get("exercises") or []):
            if not isinstance(ex, dict):
                continue
            xid = ex.get("id") or "?"
            plain_fields += [(f"{xid}.prompt", ex.get("prompt")),
                             (f"{xid}.explanation", ex.get("explanation")),
                             (f"{xid}.answer", ex.get("answer"))]
        for name, val in plain_fields:
            for sub, s in walk_strings(val, name):
                stats["plain_fields"] += 1
                if MARKUP.search(s):
                    fail["plaintext"].append(f"{lid}/{sub}: markup in a plain-text field: {s[:150]!r}")

    # --- topic.json / course.json: same plain-text rule, same furigana rule ---
    for meta in sorted(list(course.glob("*/topic-*/topic.json")) + list(course.glob("*/course.json"))
                       + list(course.glob("course.json"))):
        d = json.loads(meta.read_text(encoding="utf-8"))
        mid = d.get("id") or meta.stem
        for key in ("title", "description", "objectives", "overview", "theme"):
            for sub, s in walk_strings(d.get(key), key):
                stats["plain_fields"] += 1
                if MARKUP.search(s):
                    fail["plaintext"].append(f"{mid}/{sub}: markup in a plain-text field: {s[:150]!r}")

    # --- furigana anywhere else in the shipped courseware ---------------------
    # Lessons are the only place carrying <jp> today; scan speak units and readings too so a new
    # producer cannot introduce an unchecked annotation channel.
    for extra in sorted(list(course.glob("speak/*/unit-*.json"))
                        + list((corpus / "readings").glob("*.json"))):
        d = json.loads(extra.read_text(encoding="utf-8"))
        for sub, s in walk_strings(d):
            if "<jp" in s:
                check_furigana(fail["furigana"], stats, f"{extra.name}/{sub}", s)

    # --- every whole-string vocab identifier in course/ is a numeric slug -----
    for f in sorted(course.rglob("*.json")):
        for sub, s in walk_strings(json.loads(f.read_text(encoding="utf-8"))):
            m = VOCAB_SLUG.match(s)
            if m:
                stats["vocab_ids"] += 1
                if not m.group(1).isascii() or not m.group(1).isdigit():
                    fail["vocab-slug"].append(
                        f"{f.relative_to(course)}/{sub}: '{s}' uses the retired vocab:<headword> "
                        f"scheme (93 headwords name 193 records — it cannot be resolved to one word)")
    # body attributes are not whole strings, so they need their own pass
    for leaf in leaves:
        d = json.loads(leaf.read_text(encoding="utf-8"))
        for attr, val in re.findall(r'(ref|item-ref)="(vocab:[^"]+)"', d.get("body") or ""):
            stats["vocab_ids"] += 1
            ident = val.split(":", 1)[1]
            if not ident.isascii() or not ident.isdigit():
                fail["vocab-slug"].append(
                    f"{d.get('id')}: body {attr}=\"{val}\" uses the retired vocab:<headword> scheme")

    total = sum(len(v) for v in fail.values())
    print(f"lesson bodies: {stats['lessons']} lessons, {stats['refs']} refs, {stats['spans']} furigana "
          f"spans, {stats['plain_fields']} plain-text fields, {stats['vocab_ids']} vocab ids — "
          f"{total} FAIL {dict((k, len(v)) for k, v in fail.items() if v)} , {len(warns)} warn")
    if stats["empty_kana_base"]:
        print(f"  note  {stats['empty_kana_base']} <jp reading=\"\"> spans on kana-only bases "
              f"(redundant, not a defect)")
    if total:
        shown = 0
        for rule, msgs in fail.items():
            for m in msgs:
                if not args.list and shown >= MAX_PRINT:
                    break
                print(f"  FAIL [{rule}] {m}")
                shown += 1
        if not args.list and total > MAX_PRINT:
            print(f"  … {total - MAX_PRINT} more (run with --list)")
        return 1
    for w in warns[:5]:
        print(f"  warn  {w}")
    if stats['lessons'] < 300:
        # a gate whose data vanished must FAIL, not certify nothing; the course has 322 lessons and only shrinks by deliberate archive moves
        print(f"FAIL: only {stats['lessons']} lesson leaves found (floor 300) — the glob is no longer "
              f"finding the course")
        return 1
    print("=== 0 FAIL — every body parses, every ref resolves, every reading is kana, "
          "no markup leaked into a plain-text field ===")
    return 0


if __name__ == "__main__":
    sys.exit(main())
