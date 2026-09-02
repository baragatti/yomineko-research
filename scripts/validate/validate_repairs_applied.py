#!/usr/bin/env python3
"""Hard gate: every tracked repair table is REPLAYED against the committed export.

WHY THIS EXISTS
---------------
`research/reports/readiness/quality_provenance_review.md` finding **G7**: *"no gate replays the
repair tables against the export — 16 grammar `form_meanings` repairs silently no-oped and only the
audit noticed."* Six campaigns wrote 1,299 rows of `old`/`new`/`why` under
`research/derived/repairs/`, every applier is DB-only, and the exporter republishes afterwards.
Between the apply script's "repaired N fields" line and the JSON a learner is served there was no
check at all: a row could match nothing, be shadowed by a Layer-A column, be reverted by a later
campaign, or address a field the exporter does not project — and the suite stayed green while the
campaign ledger claimed the defect was fixed.

This validator closes that gap from the other end. It never reads `db/corpus.sqlite`; it reads the
committed export, walks every row of every tracked table, and asserts the row's `new` value is
what the export actually carries at the address the row names.

WHAT IT CHECKS, TABLE BY TABLE
------------------------------
The six tables are REGISTERED below with the addressing their applier uses (learned from
`scripts/apply_*.py`). A `.json` file appearing in `research/derived/repairs/` that is not
registered here is itself a FAILURE — a new campaign joins this gate the day it lands, not the day
someone remembers.

  * `sentence_text_repairs.json`      {slug, field, locale}      sentence[field][locale] == new
  * `jargon_pass2_repairs.json`       {slug, field, locale}      sentence[field][locale] == new
  * `translation_defect_repairs.json` {entity, slug, field, locale, token_position?}
        entity `sentence` -> sentence[field][locale] == new
        entity `token`    -> some token at `token_position` has [field][locale] == new
        (position is NOT unique — Sudachi's C-mode compound shares it with its A-mode parts, which
        is exactly why `apply_translation_defect_repairs.py` matches across all tokens there)
  * `translation_followups.json`      {store, slug, field, locale?}
        store `localized_text` -> sentence[field][locale] == new
        store `column`         -> sentence[field] == new           (kana / romaji, scalars)
  * `grammar_record_repairs.json`     {key, action}
        `text`   -> grammar[field][locale] carries new. 28 of the campaign's findings quote a
                    distinguishing SPAN rather than a whole field, and `resolve()` in the applier
                    lands those with `current.replace(old, new)`, so the predicate here is
                    CONTAINMENT, matching the applier's own semantics. The mode (exact / span) is
                    reported per failure so a substring pass is never mistaken for an exact one.
                    field `form_meanings` is a JSON map {form: meaning} -> see below.
        `forms`  -> [f["form"] for f in grammar["forms"]] == new (parsed)
        `unlink` -> the grammar key is ABSENT from the sentence's `grammar` list
  * `grammar_followups.json`          {action}
        `link`       -> the grammar key is PRESENT in the sentence's `grammar` list
        `no-link`    -> MARKED SKIP (see below) and still asserted: the sentence carries NO grammar
                        link, which is the judgement the row records
        `str`        -> grammar[structure_pattern|steps_unavailable] == new (new may be null)
        `json`       -> forms_json -> grammar["forms"] form list; references_json -> grammar["refs"];
                        formation_steps_json -> grammar["formation_steps"]; compared PARSED
        `ltext_json` -> form_meanings map, per form

`form_meanings` has no field of its own in the export. `scripts/export/export_corpus.py` builds
`forms` by iterating `forms_json` and looking the meaning up BY FORM STRING, so a meaning keyed on a
form that is not in `forms_json` is invisible to every consumer. That projection is what the 16
no-ops fell through, so a `form_meanings` row is checked per (form, meaning) pair against
`forms[].meaning[locale]`, and a missing form key is reported as its own root-cause class.

MARKED SKIPS — a marking is an assertion, never an excuse
---------------------------------------------------------
Two markings exist, and NEITHER is taken on trust: each is a claim this validator proves before it
lets the row out of the gate. That is the whole design rule here — a marker that stops being true
becomes a FAILURE, so marking a row can never hide a regression.

  * `grammar_followups.json` `action: "no-link"` (10 rows) — the orphaned sentences that illustrate
    no record in the registry. SKIP, and the judgement is still asserted: the sentence must carry
    ZERO grammar links. Tag one of them and the row fails (`link-still-present`, plant-proved).

  * `superseded_by: {"table": …, "row": N}` (7 rows in `sentence_text_repairs.json`) — a repair that
    landed and was then written over by a LATER campaign. SKIP only after all four of these hold:
    the named table is tracked, the row index is in range and is not this row itself, the successor
    addresses the SAME (slug, field, locale), the successor's `old` is this row's `new`, and the
    export carries the successor's `new`. Any one of them failing is `superseded_by-marker-does-not-
    chain`, a hard failure (plant-proved). Note what that buys: because the last condition compares
    against the export, a marked row still detects a regression — revert the field and the marker
    stops chaining.

The seven marked rows are `translation_literal` [pt-BR], six superseded by
`translation_defect_repairs.json` (rows 5, 1, 132, 76, 185, 15) and one by
`translation_followups.json` row 0; `translation_repairs_skipped.md` predicted exactly this
collision. An UNMARKED row in the same shape is still a failure
(`superseded-by-a-later-tracked-row`): `successor()` finds the chain and the report names the row
that needs the marker, so the marking stays a deliberate act.

Every other campaign's deliberate non-changes live in a report (`grammar_repairs_skipped.md`,
`translation_repairs_skipped.md`) or in a `DEFERRED` constant inside the apply script, NOT in the
table. Those rows are ordinary rows here and their failures are real findings.

NO RATCHET
----------
This gate is CLEAN: 2026-09-02, 1,299 rows, **1,282 PASS / 17 SKIP / 0 FAIL**. It carries no frozen
ceiling and no exemption file — any failure exits 1. The 7 rows that were the first run's only
failures now carry proved `superseded_by` markers instead of a ratcheted allowance, which is the
stronger arrangement: a ceiling counts failures, a marker has to keep chaining against the export.

G7's "16 `form_meanings` repairs silently no-oped" does NOT reproduce, and the difference is the
measurement, not the data. The audit tested by substring — it looked for the serialised map
`{"てほしい": "…"}` in the export text, which cannot match because the exporter projects that map
through `forms_json` into `forms[].meaning`. Replayed pair by pair through that projection, all 16
rows are carried by the export (`gp-152`, `gp-101`, `gp-121`, `gp-41`, `no-naka-de-a-ga-ichiban`,
`gp-133`, `gp-148`, `o-kudasai-2`, both locales each): the paired `forms` rows renamed the form keys
and `grammar_followups.json` finished the two records the first campaign could not reach. The
`form-key-absent-from-forms` class stays in the gate because the projection that hid it is still
there — a future rename that misses its meanings map lands in that class immediately (plant-proved).

Reads the exported JSON under `corpus/` (and confirms the `course/` tier is present — no tracked
table addresses a course record, and this gate fails if a repaired field ever starts being copied
into a lesson leaf instead of referenced by id).

Exit 1 on any failure, on an unregistered table, or on empty input.
Usage: validate_repairs_applied.py [--root PATH] [--all] [--table NAME]
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]

REPO = Path(__file__).resolve().parents[2]

# Floors far below the real counts, so growth never trips them but a vanished input always does.
MIN_TABLES = 6
MIN_ROWS_TOTAL = 1_000
MIN_SENTENCES = 5_000
MIN_GRAMMAR = 400
MIN_COURSE_FILES = 300

MAX_REPORT = 12

LOCALES = ("pt-BR", "en")

# ---------------------------------------------------------------------------------------------
# Root-cause classes. Every failure is classified and the fix for its class is printed with it.
# ---------------------------------------------------------------------------------------------
C_FORM_KEY_ABSENT = "form-key-absent-from-forms"
C_FORM_MEANING = "form-meaning-mismatch"
C_LAYER_A_SHADOW = "layer-a-en-shadows-the-row"
C_SUPERSEDED = "superseded-neither-old-nor-new"
C_SUPERSEDED_CHAIN = "superseded-by-a-later-tracked-row"
C_BAD_MARKER = "superseded_by-marker-does-not-chain"
C_NOT_APPLIED = "not-applied-old-still-present"
C_VALUE_MISMATCH = "value-mismatch"
C_NO_FIELD = "field-absent-from-export"
C_NO_RECORD = "address-does-not-resolve"
C_LINK_PRESENT = "link-still-present"
C_LINK_ABSENT = "link-absent"

FIXES = {
    C_FORM_KEY_ABSENT:
        "export_corpus.py builds `forms` by iterating `forms_json` and looking each meaning up BY "
        "FORM STRING (line ~335), so a form_meanings key that is not in forms_json is projected "
        "nowhere. Either the paired `forms` row must rename the key in forms_json first (the "
        "campaign's own contract), or the exporter must emit the leftover meanings so the loss is "
        "visible. Column: grammar_point.forms_json + localized_text(form_meanings).",
    C_FORM_MEANING:
        "the form key IS in forms_json but forms[].meaning[locale] is not the repaired text — the "
        "localized_text(grammar_point, form_meanings, <locale>) map was never updated for that key.",
    C_LAYER_A_SHADOW:
        "export_corpus.py renders translation/en as `sentence.en or localized_text` (line 512). On "
        "a mined record sentence.en is Layer A and shadows the repaired localized row, so the edit "
        "is invisible by design. Column: sentence.en. Spec §1.1 forbids editing it — the row, not "
        "the exporter, is what has to change.",
    C_SUPERSEDED:
        "the export carries neither `old` nor `new` and no tracked row explains the difference. "
        "Something outside the repair tables rewrote this field — that is the dangerous shape and "
        "it is the one class here with no automatic account of itself.",
    C_SUPERSEDED_CHAIN:
        "the repair DID land and a LATER tracked row then consumed it: the successor's `old` is "
        "this row's `new`, and the export carries the successor's `new`. Nothing in the exporter is "
        "wrong and no column needs changing. Add `superseded_by: {\"table\": …, \"row\": N}` naming "
        "the successor printed below and the row becomes a checked SKIP; the marker is re-proved "
        "against the export on every run, so it cannot outlive the chain it claims.",
    C_BAD_MARKER:
        "a `superseded_by` marker that no longer holds. Either it names a row that is not there, or "
        "addresses a different field, or the successor's `old` is not this row's `new`, or the "
        "export does not carry the successor's `new` (which is what a REGRESSION on a marked row "
        "looks like). Re-derive the chain; never widen the marker to make it fit.",
    C_NOT_APPLIED:
        "the export still carries `old` verbatim — the repair genuinely did not land. Re-run the "
        "applier and re-export, or record why the applier skipped it.",
    C_VALUE_MISMATCH:
        "the field exists and differs from `new` in some other way; read the printed value.",
    C_NO_FIELD:
        "the exporter does not project this field/locale at all for this record.",
    C_NO_RECORD:
        "the slug/key the row addresses is not in the export — a retired or re-pointed identity.",
    C_LINK_PRESENT:
        "an `unlink` row's grammar key is still on the sentence. `apply_grammar_record_repairs.py` "
        "REFUSES an unlink that would leave a record with zero sentences; that refusal is reported "
        "to stdout and to grammar_repairs_skipped.md but is not marked in the table.",
    C_LINK_ABSENT:
        "a `link` row's grammar key is missing from the sentence's `grammar` list.",
}

# No ratchet, no ceiling, no exemption file: this gate is clean and any failure exits 1. The debt it
# was first measured with (7 superseded rows) is carried by proved `superseded_by` markers instead —
# see MARKED SKIPS in the module docstring for why that is the stronger arrangement.


def die(msg: str) -> None:
    print(f"[FAIL] {msg}")
    raise SystemExit(1)


# ---------------------------------------------------------------------------------------------
# Export loading
# ---------------------------------------------------------------------------------------------
def load_export(root: Path) -> tuple[dict, dict, int]:
    bank = root / "corpus" / "sentences" / "bank.json"
    if not bank.exists():
        die(f"sentence bank not found: {bank}")
    sentences = json.loads(bank.read_text(encoding="utf-8"))
    if not isinstance(sentences, list) or len(sentences) < MIN_SENTENCES:
        die(f"sentence bank has {len(sentences)} records, floor is {MIN_SENTENCES} "
            f"(empty or truncated input must never certify a repair table)")
    by_slug = {s["slug"]: s for s in sentences}

    gfiles = sorted((root / "corpus" / "grammar").glob("*.json"))
    grammar: list[dict] = []
    for f in gfiles:
        grammar += json.loads(f.read_text(encoding="utf-8"))
    if len(grammar) < MIN_GRAMMAR:
        die(f"grammar registry has {len(grammar)} records over {len(gfiles)} file(s), floor is "
            f"{MIN_GRAMMAR}")
    by_key = {g["key"]: g for g in grammar}

    course = list((root / "course").rglob("*.json"))
    if len(course) < MIN_COURSE_FILES:
        die(f"course tier has {len(course)} JSON files, floor is {MIN_COURSE_FILES}")
    return by_slug, by_key, len(course)


def course_scalar_values(root: Path) -> set[str]:
    """Every scalar string in the course tier, for the embedded-copy check."""
    out: set[str] = set()

    def walk(node) -> None:
        if isinstance(node, str):
            if len(node) >= 60:
                out.add(node)
        elif isinstance(node, list):
            for v in node:
                walk(v)
        elif isinstance(node, dict):
            for v in node.values():
                walk(v)

    for f in (root / "course").rglob("*.json"):
        walk(json.loads(f.read_text(encoding="utf-8")))
    return out


# ---------------------------------------------------------------------------------------------
# Field readers
# ---------------------------------------------------------------------------------------------
def locale_value(rec: dict, field: str, locale: str):
    v = rec.get(field)
    if isinstance(v, dict):
        return v.get(locale)
    return None


def is_mined(sent: dict) -> bool:
    """A record whose English is a SELECTED source pair (Layer A), not authored text."""
    prov = sent.get("provenance") or {}
    src = str(prov.get("jp_source") or "")
    return not str(sent.get("slug", "")).startswith("sent:gen-") or src.startswith("tatoeba")


def classify_text(current, old, new) -> str:
    if current is None:
        return C_NO_FIELD
    if isinstance(current, str) and isinstance(old, str) and old and old in current:
        return C_NOT_APPLIED
    return C_SUPERSEDED if isinstance(current, str) else C_VALUE_MISMATCH


def check_text(rec, field, locale, old, new, *, span_ok: bool) -> tuple[bool, str, str]:
    """(ok, cls, note). `span_ok` mirrors the applier that accepts a quoted span."""
    cur = locale_value(rec, field, locale) if locale else rec.get(field)
    if cur == new:
        return True, "", "exact"
    if span_ok and isinstance(cur, str) and isinstance(new, str) and new and new in cur:
        return True, "", "span"
    return False, classify_text(cur, old, new), repr(cur)[:220]


def check_form_meanings(rec, locale, new) -> tuple[str, str]:
    """("", "") when every (form, meaning) pair of `new` is carried by forms[]; else (class, note).

    `form_meanings` has no field of its own in the export: export_corpus.py iterates `forms_json`
    and looks each meaning up BY FORM STRING, so this walks the map the row wrote and asks the
    projection for it, pair by pair. A naive substring search for the serialised map (which is how
    the readiness audit measured it) cannot see through that projection and reports every row as a
    no-op — which is why G7 counted 16.
    """
    if isinstance(new, str):
        new = json.loads(new)
    if not isinstance(new, dict) or not new:
        return C_VALUE_MISMATCH, f"`new` is not a non-empty form->meaning map: {new!r}"[:200]
    index = {f.get("form"): f for f in (rec.get("forms") or []) if isinstance(f, dict)}
    notes: list[str] = []
    cls = ""
    for form, meaning in new.items():
        entry = index.get(form)
        if entry is None:
            cls = cls or C_FORM_KEY_ABSENT
            notes.append(f"form {form!r} is not in forms[] (forms carry {sorted(index)!r}), so the "
                         f"meaning is projected nowhere")
        else:
            got = (entry.get("meaning") or {}).get(locale)
            if got != meaning:
                cls = cls or C_FORM_MEANING
                notes.append(f"forms[{form!r}].meaning[{locale}] = {got!r}"[:200])
    return (cls, "; ".join(notes)) if cls else ("", "")


# ---------------------------------------------------------------------------------------------
# Per-table handlers. Each returns rows of (status, cls, address, detail).
# status: "ok" | "fail" | "skip"
# ---------------------------------------------------------------------------------------------
# (slug, field, locale) -> [(table, row_index, old, new)] across EVERY tracked table, so a row that
# a later campaign consumed can be told apart from a row that was simply lost. Built once in main().
CHAINS: dict[tuple, list[tuple]] = {}
# table name -> its rows, for resolving `superseded_by`. Built once in main().
TABLES: dict[str, list[dict]] = {}


def row_address(r) -> tuple:
    """The (entity, field, locale) a `superseded_by` marker must agree with on both ends."""
    return (r.get("slug") or r.get("key"), r.get("field"), r.get("locale"))


def check_marker(r, table, i, current) -> tuple[str, str]:
    """("", note) when a `superseded_by` marker chains; (class, note) when it does not.

    Five conditions, all of them necessary. The last one is what keeps a marked row honest: it
    compares against the EXPORT, so reverting the field breaks the marker instead of hiding behind
    it. `no-link` works the same way — a marking here is an assertion, not an excuse.
    """
    m = r["superseded_by"]
    if not isinstance(m, dict) or set(m) != {"table", "row"}:
        return C_BAD_MARKER, f"`superseded_by` must be {{table, row}}, got {m!r}"[:200]
    t, j = m["table"], m["row"]
    rows = TABLES.get(t)
    if rows is None:
        return C_BAD_MARKER, f"names table {t!r}, which is not a tracked repair table"
    if not isinstance(j, int) or isinstance(j, bool) or not 0 <= j < len(rows):
        return C_BAD_MARKER, f"names {t} row {j!r}, out of range 0..{len(rows) - 1}"
    if (t, j) == (table, i):
        return C_BAD_MARKER, "points at itself"
    succ = rows[j]
    if row_address(succ) != row_address(r):
        return C_BAD_MARKER, (f"names {t} row {j}, which addresses {row_address(succ)} — not this "
                              f"row's address {row_address(r)}")
    if succ.get("old") != r["new"]:
        return C_BAD_MARKER, (f"{t} row {j} does not continue the chain: its `old` is not this "
                              f"row's `new`")
    if current != succ.get("new"):
        return C_BAD_MARKER, (f"{t} row {j} chains, but the export carries neither its `new` nor "
                              f"anything this chain explains; export carries {current!r}")[:240]
    return "", (f"superseded by {t} row {j} (chain proved: successor `old` == this `new`, export == "
                f"successor `new`)")


def successor(r, current) -> str | None:
    """The later tracked row that consumed this one, if any.

    Campaigns run in sequence and several of them touch the same fields. When a later row's `old` is
    this row's `new` and the export carries that later row's `new`, the repair DID land and was then
    improved — a completely different situation from a repair that never landed, and the report has
    to say which.
    """
    key = (r.get("slug"), r.get("field"), r.get("locale"))
    for table, i, old, new in CHAINS.get(key, []):
        if old == r["new"] and current == new:
            return f"{table} row {i}"
    return None


def marker_gate(r, table, i, current, addr) -> tuple | None:
    """None when the row carries no `superseded_by`; otherwise its final result tuple.

    Checked BEFORE the ordinary value comparison, so a marker on a row that is in fact still live
    (or on a field that regressed) fails instead of quietly passing as a skip.
    """
    if r.get("superseded_by") is None:
        return None
    cls, note = check_marker(r, table, i, current)
    return ("fail", cls, addr, note) if cls else ("skip", "", addr, note)


def _sentence_field(r, sents, table, i) -> tuple:
    """One localized (or scalar-column) field on a sentence. Exactly one result tuple."""
    slug, field, locale = r["slug"], r["field"], r.get("locale")
    addr = f"{table} row {i}: {slug}.{field}" + (f"[{locale}]" if locale else " (column)")
    s = sents.get(slug)
    if s is None:
        return "fail", C_NO_RECORD, addr, "no such sentence in the export"
    cur = locale_value(s, field, locale) if locale else s.get(field)
    marked = marker_gate(r, table, i, cur, addr)
    if marked:
        return marked
    ok, cls, note = check_text(s, field, locale, r["old"], r["new"], span_ok=False)
    if ok:
        return "ok", "", addr, note
    nxt = successor(r, cur)
    if nxt:
        return ("fail", C_SUPERSEDED_CHAIN, addr,
                f"`new` landed and was then consumed by {nxt} — add `superseded_by` naming it; "
                f"export carries {note}")
    if field == "translation" and locale == "en" and is_mined(s):
        return "fail", C_LAYER_A_SHADOW, addr, f"export carries {note}"
    return "fail", cls, addr, f"export carries {note}"


def handle_sentence_text_repairs(rows, sents, gram, table):
    return [_sentence_field(r, sents, table, i) for i, r in enumerate(rows)]


def handle_jargon_pass2(rows, sents, gram, table):
    return [_sentence_field(r, sents, table, i) for i, r in enumerate(rows)]


def handle_translation_followups(rows, sents, gram, table):
    return [_sentence_field(r, sents, table, i) for i, r in enumerate(rows)]


def handle_translation_defect(rows, sents, gram, table):
    out = []
    for i, r in enumerate(rows):
        if r["entity"] == "sentence":
            out.append(_sentence_field(r, sents, table, i))
            continue
        slug, field, locale = r["slug"], r["field"], r["locale"]
        pos = r["token_position"]
        addr = f"{table} row {i}: {slug} token[{pos}].{field}[{locale}]"
        s = sents.get(slug)
        if s is None:
            out.append(("fail", C_NO_RECORD, addr, "no such sentence in the export"))
            continue
        at = [t for t in (s.get("tokens") or []) if t.get("position") == pos]
        if not at:
            out.append(("fail", C_NO_RECORD, addr, f"no token at position {pos}"))
            continue
        # `position` is not unique (C-mode compound + its A-mode parts), so the applier matched
        # across every token there and so does this.
        got = [locale_value(t, field, locale) for t in at]
        if r["new"] in got:
            out.append(("ok", "", addr, "exact"))
        else:
            cls = classify_text(next((g for g in got if g is not None), None), r["old"], r["new"])
            out.append(("fail", cls, addr, f"tokens at that position carry {got!r}"[:240]))
    return out


def handle_grammar_record_repairs(rows, sents, gram, table):
    out = []
    for i, r in enumerate(rows):
        key, act = r["key"], r["action"]
        g = gram.get(key)
        if act == "unlink":
            addr = f"{table} row {i}: unlink {r['sentence']} -/-> {key}"
            s = sents.get(r["sentence"])
            if s is None:
                out.append(("fail", C_NO_RECORD, addr, "no such sentence in the export"))
            elif key in (s.get("grammar") or []):
                out.append(("fail", C_LINK_PRESENT, addr,
                            f"sentence.grammar = {(s.get('grammar') or [])!r:.160}"))
            else:
                out.append(("ok", "", addr, "link absent"))
            continue
        if g is None:
            out.append(("fail", C_NO_RECORD, f"{table} row {i}: {key}",
                        "no such grammar point in the export"))
            continue
        if act == "forms":
            addr = f"{table} row {i}: {key}.forms"
            want = json.loads(r["new"]) if isinstance(r["new"], str) else r["new"]
            got = [f.get("form") for f in (g.get("forms") or [])]
            out.append(("ok", "", addr, "exact") if got == want
                       else ("fail", C_VALUE_MISMATCH, addr, f"forms[] = {got!r}"[:220]))
            continue
        # act == "text"
        field, locale = r["field"], r["locale"]
        addr = f"{table} row {i}: {key}.{field}[{locale}]"
        if field == "form_meanings":
            cls, note = check_form_meanings(g, locale, r["new"])
            out.append(("ok", "", addr, "exact") if not cls else ("fail", cls, addr, note))
            continue
        marked = marker_gate(r, table, i, locale_value(g, field, locale), addr)
        if marked:
            out.append(marked)
            continue
        ok, cls, note = check_text(g, field, locale, r["old"], r["new"], span_ok=True)
        out.append(("ok", "", addr, note) if ok
                   else ("fail", cls, addr, f"export carries {note}"))
    return out


JSON_COLUMN_TO_EXPORT = {
    "references_json": "refs",
    "formation_steps_json": "formation_steps",
}


def handle_grammar_followups(rows, sents, gram, table):
    out = []
    for i, r in enumerate(rows):
        act = r["action"]
        if act in ("link", "no-link"):
            slug = r["sentence"]
            key = r.get("key")
            addr = (f"{table} row {i}: link {slug} -> {key}" if act == "link"
                    else f"{table} row {i}: no-link {slug}")
            s = sents.get(slug)
            if s is None:
                out.append(("fail", C_NO_RECORD, addr, "no such sentence in the export"))
                continue
            links = s.get("grammar") or []
            if act == "link":
                out.append(("ok", "", addr, "link present") if key in links
                           else ("fail", C_LINK_ABSENT, addr, f"sentence.grammar = {links!r:.160}"))
            else:
                # MARKED SKIP: the applier never writes these. The judgement is still asserted.
                out.append(("skip", "", addr, "marked no-link; sentence untagged as recorded")
                           if not links
                           else ("fail", C_LINK_PRESENT, addr,
                                 f"recorded as illustrating no record but carries {links!r:.160}"))
            continue
        key = r["key"]
        g = gram.get(key)
        if g is None:
            out.append(("fail", C_NO_RECORD, f"{table} row {i}: {key}",
                        "no such grammar point in the export"))
            continue
        if act == "str":
            col = r["column"]
            addr = f"{table} row {i}: {key}.{col}"
            got = g.get(col)
            out.append(("ok", "", addr, "exact") if got == r["new"]
                       else ("fail", C_VALUE_MISMATCH, addr, f"export carries {got!r:.200}"))
            continue
        if act == "json":
            col = r["column"]
            if col == "forms_json":
                addr = f"{table} row {i}: {key}.forms_json -> forms[]"
                got = [f.get("form") for f in (g.get("forms") or [])]
                out.append(("ok", "", addr, "exact") if got == r["new"]
                           else ("fail", C_VALUE_MISMATCH, addr, f"forms[] = {got!r:.200}"))
            else:
                dest = JSON_COLUMN_TO_EXPORT[col]
                addr = f"{table} row {i}: {key}.{col} -> {dest}"
                got = g.get(dest)
                out.append(("ok", "", addr, "exact") if got == r["new"]
                           else ("fail", C_VALUE_MISMATCH, addr, f"export carries {got!r:.200}"))
            continue
        # act == "ltext_json" (form_meanings)
        locale = r["locale"]
        addr = f"{table} row {i}: {key}.form_meanings[{locale}]"
        cls, note = check_form_meanings(g, locale, r["new"])
        out.append(("ok", "", addr, "exact") if not cls else ("fail", cls, addr, note))
    return out


# name -> (handler, required keys per row)
REGISTRY = {
    "sentence_text_repairs.json": handle_sentence_text_repairs,
    "jargon_pass2_repairs.json": handle_jargon_pass2,
    "translation_defect_repairs.json": handle_translation_defect,
    "translation_followups.json": handle_translation_followups,
    "grammar_record_repairs.json": handle_grammar_record_repairs,
    "grammar_followups.json": handle_grammar_followups,
}


# ---------------------------------------------------------------------------------------------
def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", type=Path, default=REPO,
                    help="tree to validate (corpus/, course/, research/derived/repairs/)")
    ap.add_argument("--all", action="store_true", help="print every failure, not the first "
                                                       f"{MAX_REPORT} per class")
    ap.add_argument("--table", help="restrict to one table (diagnostics; never use in the gate)")
    args = ap.parse_args()
    root: Path = args.root.resolve()

    rdir = root / "research" / "derived" / "repairs"
    if not rdir.is_dir():
        die(f"repair table directory not found: {rdir}")
    present = sorted(p.name for p in rdir.glob("*.json"))
    if not present:
        die(f"{rdir} contains no repair tables — an empty table directory must never pass")
    unregistered = [n for n in present if n not in REGISTRY]
    if unregistered:
        die(f"unregistered repair table(s) {unregistered}: a new campaign's table must be "
            f"registered in REGISTRY with its addressing before it can be replayed")
    missing = [n for n in REGISTRY if n not in present]
    if missing:
        die(f"registered repair table(s) missing from {rdir}: {missing}")
    if len(present) < MIN_TABLES:
        die(f"{len(present)} repair tables, floor is {MIN_TABLES}")

    sents, gram, ncourse = load_export(root)
    print(f"export: {len(sents)} sentences, {len(gram)} grammar points, {ncourse} course files "
          f"(root {root})")

    tables: dict[str, list[dict]] = {}
    for name in present:
        rows = json.loads((rdir / name).read_text(encoding="utf-8"))
        if not isinstance(rows, list) or not rows:
            die(f"{name}: table is empty or not a list")
        tables[name] = rows
    total_rows = sum(len(v) for v in tables.values())
    if total_rows < MIN_ROWS_TOTAL:
        die(f"{total_rows} repair rows across {len(tables)} tables, floor is {MIN_ROWS_TOTAL}")

    # The course tier addresses the corpus by id, with ONE sanctioned exception: the speaking units
    # embed the pt-BR translation of the sentence they cite (validate_speaking_path.py: "embedded
    # content derivable from the cited item"). An embedded copy is a second home for a repaired
    # string, so a repair that landed in `corpus/` and not in that copy leaves the course teaching
    # the defect. Assert the pre-repair text survives NOWHERE in the course tier.
    cvals = course_scalar_values(root)
    stale = []
    for name, rows in tables.items():
        for i, r in enumerate(rows):
            v = r.get("old")
            if isinstance(v, str) and len(v) >= 60 and v in cvals and v != r.get("new"):
                stale.append(f"{name} row {i} ({r.get('slug') or r.get('key')}): the PRE-repair "
                             f"`old` text is still a scalar in the course tier")
    if stale:
        for s in stale[:MAX_REPORT]:
            print(f"  [FAIL] {s}")
        die(f"{len(stale)} pre-repair value(s) survive as embedded copies under course/; the "
            f"repair reached corpus/ only")

    TABLES.update(tables)          # so `superseded_by` can resolve across campaigns

    # Cross-table chain index (see successor()). Sentence-addressed rows only: those are the ones
    # several campaigns collide on.
    for name, rows in tables.items():
        for i, r in enumerate(rows):
            if r.get("slug") and isinstance(r.get("old"), str) and isinstance(r.get("new"), str):
                CHAINS.setdefault((r["slug"], r["field"], r.get("locale")), []).append(
                    (name, i, r["old"], r["new"]))

    print()
    results: dict[str, list[tuple]] = {}
    for name in sorted(tables):
        if args.table and args.table not in name:
            continue
        results[name] = REGISTRY[name](tables[name], sents, gram, name)

    grand_ok = grand_fail = grand_skip = 0
    all_classes: Counter = Counter()
    samples: dict[str, list[str]] = defaultdict(list)

    for name in sorted(results):
        rows = results[name]
        # 1:1 with the table. A handler that silently dropped rows would certify them; this is the
        # empty-input rule applied per table.
        if len(rows) != len(tables[name]):
            die(f"{name}: handler produced {len(rows)} results for {len(tables[name])} rows — every "
                f"row must be checked exactly once")
        ok = sum(1 for s, *_ in rows if s == "ok")
        span = sum(1 for s, _, _, note in rows if s == "ok" and note == "span")
        skip = sum(1 for s, *_ in rows if s == "skip")
        bad = [r for r in rows if r[0] == "fail"]
        classes = Counter(c for _, c, _, _ in bad)
        all_classes.update(classes)
        for _, c, addr, detail in bad:
            samples[c].append(f"{addr}\n        {detail}")
        grand_ok += ok
        grand_fail += len(bad)
        grand_skip += skip
        cls_txt = ", ".join(f"{c}={n}" for c, n in sorted(classes.items())) or "-"
        print(f"  {name:34} rows={len(tables[name]):4}  PASS={ok:4} (span {span:3})  "
              f"SKIP={skip:2}  FAIL={len(bad):3}  [{cls_txt}]")

    print(f"\n  TOTAL rows={total_rows}  checks={grand_ok + grand_fail + grand_skip}  "
          f"PASS={grand_ok}  SKIP={grand_skip}  FAIL={grand_fail}")

    if all_classes:
        print("\n--- failures by root cause ---")
        for c, n in all_classes.most_common():
            print(f"\n  [{c}] × {n}")
            print(f"      fix: {FIXES.get(c, '(unclassified)')}")
            shown = samples[c] if args.all else samples[c][:MAX_REPORT]
            for s in shown:
                print(f"      - {s}")
            if len(samples[c]) > len(shown):
                print(f"      … {len(samples[c]) - len(shown)} more (--all)")

    if args.table:
        # Deliberately NOT exit 0: a partial run must never be mistakable for a green gate, in CI
        # or in a scrollback. --table is for reading one campaign, nothing else.
        print("\n[info] --table given: partial run, not the gate. Exit 2.")
        return 2

    if grand_fail:
        print(f"\nRESULT: FAIL — {grand_fail} repair row(s) the export does not carry, across "
              f"{len(all_classes)} root-cause class(es)")
        return 1

    print(f"\nRESULT: PASS — {grand_ok} rows replayed clean, {grand_skip} checked skips "
          f"(no-link + superseded_by), 0 FAIL")
    return 0


if __name__ == "__main__":
    sys.exit(main())
