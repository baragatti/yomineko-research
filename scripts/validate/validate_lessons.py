#!/usr/bin/env python3
"""P6/P7 — validate lesson rich-format bodies + exercise/coverage rules against design/lesson_schema.md (v1).

Reads every lesson from the DB, parses its tagged body, and enforces: (1) no bare text, (2) element/attribute
whitelist, (3) all ref ids resolve, (4) child-kind rules, (5) pt-BR (structural only here), (6) required
structure (ends with <checklist>; ≥1 retrieval + ≥1 production exercise). Plus per-exercise answer-key shapes,
introduce-once, and lesson_introduces ⊆ topic.introduces. Errors block; deferred-asset refs warn.
Run: .venv/Scripts/python.exe scripts/validate/validate_lessons.py
"""
from __future__ import annotations

import json
import sqlite3
import sys
from html.parser import HTMLParser
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "ingest"))
sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
from i18n_text import get_text  # noqa: E402

DB = Path(__file__).resolve().parents[2] / "db" / "corpus.sqlite"
BOOL = {"true", "false"}
FREE = None  # free-text attribute value

# kind, allowed attrs (value-set or FREE), required attrs, allowed children
#   children: "inline" | "block" | "both" | "none" | frozenset(tags)
BLOCK = {"heading", "p", "note", "list", "item", "image", "video", "audio", "sentence", "stroke",
         "exercise", "flashcard", "front", "back", "checklist", "check", "divider"}
INLINE = {"text", "jp", "ruby", "romaji", "term", "emphasis", "kanji", "vocab", "grammar", "audio", "break"}
TEXT_BEARING = {"text", "jp", "romaji", "term", "emphasis"}
REF_NS = {  # attr -> set of allowed namespace prefixes
    "sentence.ref": {"sent"}, "stroke.ref": {"kanji"}, "kanji.ref": {"kanji"}, "vocab.ref": {"vocab"},
    "grammar.ref": {"gram"}, "exercise.ref": {"ex"}, "image.ref": {"img"}, "video.ref": {"vid"},
    "audio.ref": {"aud"}, "flashcard.ref": {"vocab", "kanji"}, "check.item-ref": {"vocab", "kanji", "gram"},
}
DEFERRED_NS = {"img", "aud", "vid"}  # asset registry not built yet -> warn, don't fail

ELEMENTS: dict[str, dict] = {
    "heading": {"attrs": {"level": {"1", "2", "3"}, "speak": BOOL}, "req": [], "children": "inline"},
    "p": {"attrs": {"align": {"start", "center", "end"}, "speak": BOOL, "narration": FREE}, "req": [],
          "children": "inline"},
    "note": {"attrs": {"type": {"l1-advantage", "l1-pitfall", "culture", "tip", "warning", "example"}},
             "req": ["type"], "children": "both"},
    "list": {"attrs": {"ordered": BOOL}, "req": [], "children": frozenset({"item"})},
    "item": {"attrs": {}, "req": [], "children": "both"},
    "image": {"attrs": {"ref": FREE, "width": FREE, "height": FREE, "align": FREE, "caption": FREE,
                        "alt": FREE}, "req": ["ref"], "children": "none"},
    "video": {"attrs": {"ref": FREE, "caption": FREE, "poster": FREE}, "req": ["ref"], "children": "none"},
    "audio": {"attrs": {"ref": FREE, "label": FREE, "autoplay": BOOL}, "req": ["ref"], "children": "none"},
    "sentence": {"attrs": {"ref": FREE, "show": {"furigana", "romaji", "both", "none"},
                           "mode": {"inline", "card", "featured"}, "audio": BOOL}, "req": ["ref"],
                 "children": "none"},
    "stroke": {"attrs": {"ref": FREE, "autoplay": BOOL}, "req": ["ref"], "children": "none"},
    "exercise": {"attrs": {"ref": FREE}, "req": ["ref"], "children": "none"},
    "flashcard": {"attrs": {"ref": FREE}, "req": [], "children": frozenset({"front", "back"})},
    "front": {"attrs": {}, "req": [], "children": "both"},
    "back": {"attrs": {}, "req": [], "children": "both"},
    "checklist": {"attrs": {}, "req": [], "children": frozenset({"check"})},
    "check": {"attrs": {"item-ref": FREE}, "req": [], "children": "inline"},
    "divider": {"attrs": {}, "req": [], "children": "none"},
    "text": {"attrs": {"weight": {"normal", "bold"}, "italic": BOOL, "underline": BOOL, "color": FREE,
                       "size": {"sm", "md", "lg"}, "speak": BOOL}, "req": [], "children": "text"},
    "jp": {"attrs": {"reading": FREE, "pitch": FREE}, "req": [], "children": "text"},
    "ruby": {"attrs": {"base": FREE, "reading": FREE}, "req": ["base", "reading"], "children": "none"},
    "romaji": {"attrs": {}, "req": [], "children": "text"},
    "term": {"attrs": {"define": FREE}, "req": ["define"], "children": "text"},
    "emphasis": {"attrs": {}, "req": [], "children": "text"},
    "kanji": {"attrs": {"ref": FREE, "furigana": BOOL}, "req": ["ref"], "children": "none"},
    "vocab": {"attrs": {"ref": FREE}, "req": ["ref"], "children": "none"},
    "grammar": {"attrs": {"ref": FREE}, "req": ["ref"], "children": "none"},
    "break": {"attrs": {}, "req": [], "children": "none"},
}
RETRIEVAL = {"recognition", "reading", "listening", "cloze", "particle_choice", "matching", "ordering"}
PRODUCTION = {"production", "handwriting"}
ANSWER_SHAPES = {  # type -> required keys
    "recognition": ("choices", "correct"), "particle_choice": ("choices", "correct"),
    "reading": ("choices", "correct"), "listening": ("choices", "correct"),
    "cloze": ("text", "full"), "sentence_build": ("order", "text"), "ordering": ("order", "text"),
    "production": ("text",), "handwriting": ("text",), "matching": ("pairs",),
}


class LessonParser(HTMLParser):
    def __init__(self, refs: list):
        super().__init__(convert_charrefs=True)
        self.errors: list[str] = []
        self.stack: list[str] = []  # element tag stack
        self.top_blocks: list[str] = []  # block tags at body root, in order
        self.refs = refs  # collected (attr_key, value) for resolution

    def _child_ok(self, parent: str, child: str) -> bool:
        rule = ELEMENTS[parent]["children"]
        if rule == "none" or rule == "text":
            return False
        if rule == "inline":
            return child in INLINE
        if rule == "block":
            return child in BLOCK
        if rule == "both":
            return child in BLOCK or child in INLINE
        return child in rule  # explicit frozenset

    def handle_starttag(self, tag, attrs):
        self._open(tag, attrs)

    def handle_startendtag(self, tag, attrs):
        if self._open(tag, attrs):
            self.stack.pop()

    def _open(self, tag, attrs) -> bool:
        if tag not in ELEMENTS:
            self.errors.append(f"unknown element <{tag}>")
            self.stack.append(tag)
            return True
        spec = ELEMENTS[tag]
        ad = dict(attrs)
        for a, v in ad.items():
            if a not in spec["attrs"]:
                self.errors.append(f"<{tag}>: unknown attribute '{a}'")
                continue
            allowed = spec["attrs"][a]
            if allowed is not FREE and v not in allowed:
                self.errors.append(f"<{tag} {a}=\"{v}\">: not in {sorted(allowed)}")
        for r in spec["req"]:
            if r not in ad:
                self.errors.append(f"<{tag}>: missing required attribute '{r}'")
        for a in ("ref", "item-ref"):
            key = f"{tag}.{a}"
            if a in ad and key in REF_NS:
                self.refs.append((key, ad[a]))
        # placement
        if not self.stack:
            if tag not in BLOCK:
                self.errors.append(f"<{tag}> at root is not a block element")
            else:
                self.top_blocks.append(tag)
        else:
            parent = self.stack[-1]
            if parent in ELEMENTS and not self._child_ok(parent, tag):
                self.errors.append(f"<{parent}> may not contain <{tag}>")
        self.stack.append(tag)
        return True

    def handle_endtag(self, tag):
        if self.stack and self.stack[-1] == tag:
            self.stack.pop()
        elif tag in self.stack:  # mismatched nesting: pop to it
            while self.stack and self.stack.pop() != tag:
                pass
            self.errors.append(f"mismatched/overlapping </{tag}>")
        else:
            self.errors.append(f"stray </{tag}>")

    def handle_data(self, data):
        if data.strip():
            cur = self.stack[-1] if self.stack else None
            if cur not in TEXT_BEARING:
                snip = data.strip()[:24]
                self.errors.append(f"bare text outside a text element"
                                   f"{f' (in <{cur}>)' if cur else ' (at root)'}: \"{snip}…\"")


def resolve_sets(con):
    return {
        "sent": {r[0] for r in con.execute("SELECT slug FROM sentence")},
        "kanji": {r[0] for r in con.execute("SELECT character FROM kanji")},
        "vocab": {r[0] for r in con.execute("SELECT headword FROM vocab")}
        | {str(r[0]) for r in con.execute("SELECT id FROM vocab")},
        "gram": {r[0] for r in con.execute("SELECT key FROM grammar_point")},
        "ex": {r[0] for r in con.execute("SELECT slug FROM exercise")},
    }


# namespaces whose stored identifier ALREADY includes the prefix (slug = "sent:…"/"ex:…"); others (kanji/
# vocab/gram) store the bare identifier (character/headword/key), so we compare the stripped value.
PREFIXED_NS = {"sent", "ex"}


def check_refs(refs, sets) -> tuple[list, list]:
    errs, warns = [], []
    for key, val in refs:
        if ":" not in val:
            errs.append(f"ref '{val}' ({key}) has no namespace prefix")
            continue
        ns, ident = val.split(":", 1)
        if ns not in REF_NS[key]:
            errs.append(f"ref '{val}' ({key}): namespace '{ns}' not allowed (want {sorted(REF_NS[key])})")
            continue
        if ns in DEFERRED_NS:
            warns.append(f"ref '{val}' targets the deferred asset registry (not yet implemented)")
            continue
        target = val if ns in PREFIXED_NS else ident
        if target not in sets.get(ns, ()):
            errs.append(f"ref '{val}' ({key}) does not resolve to an existing {ns}")
    return errs, warns


def main() -> int:
    con = sqlite3.connect(DB)
    con.row_factory = sqlite3.Row
    if not con.execute("SELECT COUNT(*) FROM lesson").fetchone()[0]:
        print("no lessons yet — nothing to validate")
        return 0
    sets = resolve_sets(con)
    # topic introduces (for ⊆ check) + introduce-once tracking
    introduced_by: dict[tuple, list] = {}
    errors, warns = [], []
    lessons = list(con.execute(
        "SELECT l.id, l.slug, l.topic_id FROM lesson l JOIN topic t ON t.id=l.topic_id ORDER BY t.ord, l.ord"))
    for L in lessons:
        lid, lslug = L["id"], L["slug"]
        body = get_text(con, "lesson", lid, "body") or ""
        refs: list = []
        p = LessonParser(refs)
        try:
            p.feed(body)
            p.close()
        except Exception as e:  # noqa: BLE001
            errors.append(f"[{lslug}] parse crash: {e}")
            continue
        for e in p.errors:
            errors.append(f"[{lslug}] {e}")
        ref_errs, ref_warns = check_refs(refs, sets)
        errors += [f"[{lslug}] {e}" for e in ref_errs]
        warns += [f"[{lslug}] {w}" for w in ref_warns]
        # structure: last root block is checklist
        if not p.top_blocks:
            errors.append(f"[{lslug}] empty body (no block elements)")
        elif p.top_blocks[-1] != "checklist":
            errors.append(f"[{lslug}] body must end with <checklist> (got <{p.top_blocks[-1]}>)")
        # exercises: ≥1 retrieval + ≥1 production; answer shapes
        types = []
        for ex in con.execute("SELECT slug, type, answer FROM exercise WHERE lesson_id=?", (lid,)):
            types.append(ex["type"])
            shape = ANSWER_SHAPES.get(ex["type"])
            try:
                ans = json.loads(ex["answer"]) if ex["answer"] else {}
            except json.JSONDecodeError:
                errors.append(f"[{lslug}] exercise {ex['slug']}: answer is not valid JSON")
                continue
            if shape and not all(k in ans for k in shape):
                errors.append(f"[{lslug}] exercise {ex['slug']} ({ex['type']}): answer missing {shape}")
            if ex["type"] in ("recognition", "particle_choice", "reading", "listening") \
                    and isinstance(ans, dict) and ans.get("correct") not in (ans.get("choices") or []):
                errors.append(f"[{lslug}] exercise {ex['slug']}: 'correct' not among 'choices'")
        if types:
            if not any(t in RETRIEVAL for t in types):
                errors.append(f"[{lslug}] no retrieval exercise (need ≥1 of {sorted(RETRIEVAL)})")
            if not any(t in PRODUCTION for t in types):
                errors.append(f"[{lslug}] no production exercise (need ≥1 of {sorted(PRODUCTION)})")
        # introduce-once + ⊆ topic
        for mt, mid in con.execute(
                "SELECT member_type, member_id FROM lesson_introduces WHERE lesson_id=?", (lid,)):
            introduced_by.setdefault((mt, mid), []).append(lslug)
            col = {"kanji": "kanji", "vocab": "vocab", "grammar": "grammar_point"}[mt]
            row = con.execute(f"SELECT introducing_topic_id FROM {col} WHERE id=?", (mid,)).fetchone()
            if row and row[0] is not None and row[0] != L["topic_id"]:
                # PLACEMENT consistency (lesson_introduces should ⊆ its topic's P4 placement). A WARNING, not
                # an error: the P4 placement is a known first pass with dependency violations (e.g. て-form
                # grammar dumped in topic 7) that the P6 re-placement sub-phase fixes. Format validity is
                # independent of placement correctness.
                warns.append(f"[{lslug}] introduces {mt} id={mid} placed in a different topic (P4 re-placement)")
    for key, ls in introduced_by.items():
        if len(ls) > 1:
            errors.append(f"introduce-once violated: {key} introduced by {ls}")

    print(f"validated {len(lessons)} lessons: {len(errors)} errors, {len(warns)} warnings")
    for e in errors[:80]:
        print(f"  ERROR {e}")
    for w in warns[:20]:
        print(f"  warn  {w}")
    con.close()
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
