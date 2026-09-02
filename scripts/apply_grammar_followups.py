#!/usr/bin/env python3
"""Finish the two jobs the grammar-record campaign could not do in its own action set.

`scripts/apply_grammar_record_repairs.py` landed 255 findings from research/reports/qa_sweep/
grammar_accuracy_1..4.md, but it could only edit a `localized_text` field, `forms_json`, or DELETE a
`sentence_grammar` row. Two classes of finding fell outside that, and both are written up in
research/reports/qa_sweep/grammar_repairs_skipped.md. This script closes them.

1. RETAG. `unlink` can only remove a link, never move one, so 62 sentences came out of that run with
   ZERO grammar tags -- a real coverage debt no gate catches, since validate.py does not check grammar
   coverage. Each of the 62 was read here (jp + pattern + the unlink rationale) and sent to the record
   it actually illustrates: the destination the report named where the report named one
   (gram:rareru, gram:you-ni-you-na, gram:gp-124, gram:nara, gram:nakute-wa-ikenai,
   gram:teiru-tokoro), otherwise the best-fitting existing record whose `forms` occur in the sentence.
   The hard rule of the campaign that produced them holds in reverse here: a sentence is NEVER pushed
   onto a record whose explicitly excluded sense it shows -- that is exactly what the unlinks undid.
   11 of the 62 illustrate no record in the registry and stay untagged; they are carried in the table
   as `no-link` rows with the reason, so the table is the whole story of all 62 rather than 51 of them.

2. COLUMNS. The findings whose right fix needs a column the campaign never touched:
   `structure_pattern` (D4 n3-sukoshimo-nai, D7 n3-sono-tame-ni), `references_json.label_en` (D4:
   gp-148 ×てすみ, gp-101 ×はの一つ), `formation_steps_json` (E1 the three replace-ending outliers,
   E2 n3-okagede's 勉強するおかげで, F-32 n3-zu-ni's unauthored chain), `steps_unavailable` (L-5, two
   obsolete "record is corrupted" notes), and `forms_json` + `form_meanings` together (X-9 gp-42,
   where writing one without the other recreates defect S-2). Plus gram:gp-36, whose `forms[]` listed
   the bare morphemes た / ている instead of the relative clause it teaches -- the campaign's table had
   no row for it at all.

FORMS ARE MATCHED AGAINST REAL TEXT, so a form has to be a string that can occur in a sentence.
scripts/export/pattern_forms.py splits a form on its placeholders and requires every literal piece to
appear IN ORDER, and scripts/validate/validate_speaking_path.py fails a unit whose named pattern has
none of its forms in the unit's own phrases. Every form written here is either placeholder-free
(そのために, けっこうです, てすみません) or keeps a MEDIAL slot whose removal is the defect itself
(すこしも～ない, た[A]) -- and in both of those the new value is strictly more permissive than the old,
so nothing that matches today can stop matching.

DB ONLY. This writes db/corpus.sqlite and nothing else; corpus/grammar/*.json and corpus/sentences/
bank.json are exported from the DB by the orchestrator afterwards -- do not run an exporter from here.

PRECONDITIONS ARE EXACT. A link is inserted only when the sentence still has zero grammar tags (that
is the condition this campaign exists to repair); a column is written only when its stored value
equals the recorded `old` -- compared as parsed JSON for the JSON columns, so a whitespace reflow
cannot masquerade as a content change. Anything else is SKIPPED and printed, never overwritten.

Idempotent: a link already present, a column already carrying `new`, and a `no-link` sentence still
untagged are all no-ops, so a second run reports 0 changes and `--check` after an apply exits clean.

Usage: apply_grammar_followups.py [--check] [--data PATH]
"""
from __future__ import annotations

import argparse
import json
import sqlite3
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]

ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / "db" / "corpus.sqlite"

# The verified follow-up table. TRACKED, not session-scoped, so the run is auditable and repeatable.
DATA = ROOT / "research" / "derived" / "repairs" / "grammar_followups.json"

ACTIONS = {"link", "no-link", "str", "json", "ltext_json"}
STR_COLUMNS = {"structure_pattern", "steps_unavailable"}
JSON_COLUMNS = {"forms_json", "references_json", "formation_steps_json"}
LTEXT_FIELDS = {"form_meanings"}
LOCALES = {"pt-BR", "en"}


def load(path: Path) -> list[dict]:
    """Read the table and refuse it outright if a row is malformed or a target appears twice."""
    rows = json.loads(path.read_text(encoding="utf-8"))
    seen: set[tuple] = set()
    for i, r in enumerate(rows):
        where = f"row {i} ({r.get('key') or r.get('sentence')!r})"
        act = r.get("action")
        if act not in ACTIONS:
            raise SystemExit(f"{where}: unknown action {act!r}")
        if not r.get("why"):
            raise SystemExit(f"{where}: every row needs a `why`")
        if act in ("link", "no-link"):
            if not r.get("sentence"):
                raise SystemExit(f"{where}: {act} needs `sentence`")
            if act == "link" and not r.get("key"):
                raise SystemExit(f"{where}: link needs `key`")
            target = ("sentence", r["sentence"])
        else:
            if not r.get("key"):
                raise SystemExit(f"{where}: {act} needs `key`")
            if "old" not in r or "new" not in r:
                raise SystemExit(f"{where}: {act} needs `old` and `new`")
            if r["old"] == r["new"]:
                raise SystemExit(f"{where}: `new` is identical to `old`")
            if act == "str":
                if r.get("column") not in STR_COLUMNS:
                    raise SystemExit(f"{where}: unexpected column {r.get('column')!r}")
                for k in ("old", "new"):
                    if r[k] is not None and not isinstance(r[k], str):
                        raise SystemExit(f"{where}: str `{k}` must be a string or null")
                target = (r["key"], r["column"])
            elif act == "json":
                if r.get("column") not in JSON_COLUMNS:
                    raise SystemExit(f"{where}: unexpected column {r.get('column')!r}")
                target = (r["key"], r["column"])
            else:
                if r.get("field") not in LTEXT_FIELDS:
                    raise SystemExit(f"{where}: unexpected field {r.get('field')!r}")
                if r.get("locale") not in LOCALES:
                    raise SystemExit(f"{where}: unexpected locale {r.get('locale')!r}")
                target = (r["key"], r["field"], r["locale"])
        if target in seen:
            raise SystemExit(f"{where}: duplicate target {target}")
        seen.add(target)
    return rows


def parse(raw: str | None):
    """Stored JSON as a Python object; None stays None (a NULL column is a legitimate `old`)."""
    return None if raw is None else json.loads(raw)


def dump(value) -> str | None:
    return None if value is None else json.dumps(value, ensure_ascii=False)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true", help="report what would change; write nothing")
    ap.add_argument("--data", type=Path, default=DATA, help="path to the follow-up table (JSON)")
    args = ap.parse_args()

    if not args.data.exists():
        raise SystemExit(f"follow-up table not found: {args.data}")
    rows = load(args.data)

    con = sqlite3.connect(DB)
    con.execute("PRAGMA busy_timeout=60000")

    changed = already = 0
    skipped: list[str] = []
    untagged: list[tuple[str, str]] = []
    # Links this run has inserted but not yet committed -- under --check the zero-tag precondition
    # must not re-fire for a sentence this run has already claimed.
    linked: set[str] = set()

    def note(label: str, why: str) -> None:
        print(f"  {label}")
        print(f"     why: {why}")

    def grammar_id(key: str, label: str) -> int | None:
        g = con.execute("SELECT id FROM grammar_point WHERE key=?", (key,)).fetchone()
        if not g:
            skipped.append(f"{label}: no grammar point with key {key!r}")
            return None
        return g[0]

    def sentence_id(slug: str, label: str) -> int | None:
        s = con.execute("SELECT id FROM sentence WHERE slug=?", (slug,)).fetchone()
        if not s:
            skipped.append(f"{label}: no sentence with slug {slug!r}")
            return None
        return s[0]

    for r in rows:
        act = r["action"]

        # ---- 1. retag: insert the sentence_grammar row the campaign could not move ---------------
        if act == "link":
            label = f"{r['sentence']} -> {r['key']}"
            sid = sentence_id(r["sentence"], label)
            gid = grammar_id(r["key"], label)
            if sid is None or gid is None:
                continue
            if con.execute("SELECT 1 FROM sentence_grammar WHERE sentence_id=? AND grammar_id=?",
                           (sid, gid)).fetchone():
                already += 1                      # this exact link already landed
                continue
            n = con.execute("SELECT count(*) FROM sentence_grammar WHERE sentence_id=?",
                            (sid,)).fetchone()[0]
            if n and r["sentence"] not in linked:
                skipped.append(f"{label}: REFUSED -- the sentence already carries {n} grammar "
                               f"tag(s), so it is not one of the orphans this pass repairs; "
                               f"something else has touched it")
                continue
            note(label, r["why"])
            if not args.check:
                con.execute("INSERT INTO sentence_grammar (sentence_id, grammar_id) VALUES (?, ?)",
                            (sid, gid))
            linked.add(r["sentence"])
            changed += 1
            continue

        # ---- 2. deliberately untagged: never written, always reported ---------------------------
        if act == "no-link":
            label = r["sentence"]
            sid = sentence_id(label, label)
            if sid is None:
                continue
            n = con.execute("SELECT count(*) FROM sentence_grammar WHERE sentence_id=?",
                            (sid,)).fetchone()[0]
            if n:
                skipped.append(f"{label}: recorded as illustrating no record, but it now carries "
                               f"{n} grammar tag(s) -- the judgement below needs re-reading")
                continue
            untagged.append((label, r["why"]))
            continue

        key = r["key"]
        gid = grammar_id(key, key)
        if gid is None:
            continue

        # ---- 3. a plain TEXT column on grammar_point --------------------------------------------
        if act == "str":
            col = r["column"]
            label = f"{key}.{col}"
            cur = con.execute(f"SELECT {col} FROM grammar_point WHERE id=?", (gid,)).fetchone()[0]
            if cur == r["new"]:
                already += 1
                continue
            if cur != r["old"]:
                skipped.append(f"{label}: current value matches neither the expected defective text "
                               f"nor the rewrite -- not touching it")
                continue
            note(label, r["why"])
            if not args.check:
                con.execute(f"UPDATE grammar_point SET {col}=? WHERE id=?", (r["new"], gid))
            changed += 1
            continue

        # ---- 4. a JSON column on grammar_point; compared PARSED, so whitespace is not content ---
        if act == "json":
            col = r["column"]
            label = f"{key}.{col}"
            raw = con.execute(f"SELECT {col} FROM grammar_point WHERE id=?", (gid,)).fetchone()[0]
            try:
                cur = parse(raw)
            except json.JSONDecodeError as e:
                skipped.append(f"{label}: stored value is not valid JSON ({e})")
                continue
            if cur == r["new"]:
                already += 1
                continue
            if cur != r["old"]:
                skipped.append(f"{label}: current value matches neither the expected defective value "
                               f"nor the rewrite -- not touching it")
                continue
            note(label, r["why"])
            if not args.check:
                con.execute(f"UPDATE grammar_point SET {col}=? WHERE id=?", (dump(r["new"]), gid))
            changed += 1
            continue

        # ---- 5. a localized_text row whose value is a JSON map (form_meanings) ------------------
        field, locale = r["field"], r["locale"]
        label = f"{key}.{field} [{locale}]"
        row = con.execute(
            "SELECT value FROM localized_text WHERE entity_type='grammar_point' AND entity_id=? "
            "AND field=? AND locale=?", (gid, field, locale)).fetchone()
        if row is None or row[0] is None:
            skipped.append(f"{label}: no localized_text row")
            continue
        try:
            cur = json.loads(row[0])
        except json.JSONDecodeError as e:
            skipped.append(f"{label}: stored value is not valid JSON ({e})")
            continue
        if cur == r["new"]:
            already += 1
            continue
        if cur != r["old"]:
            skipped.append(f"{label}: current value matches neither the expected defective value nor "
                           f"the rewrite -- not touching it")
            continue
        note(label, r["why"])
        if not args.check:
            con.execute(
                "UPDATE localized_text SET value=? WHERE entity_type='grammar_point' AND "
                "entity_id=? AND field=? AND locale=?", (dump(r["new"]), gid, field, locale))
        changed += 1

    if not args.check:
        con.commit()

    zero = con.execute(
        "SELECT count(*) FROM sentence s LEFT JOIN sentence_grammar sg ON sg.sentence_id = s.id "
        "WHERE sg.grammar_id IS NULL").fetchone()[0]
    con.close()

    verb = "would apply" if args.check else "applied"
    actionable = [r for r in rows if r["action"] != "no-link"]
    print(f"\n{verb} {changed} of {len(actionable)} actionable finding(s); "
          f"{already} already carried the repair")
    if untagged:
        print(f"\nleft untagged on purpose ({len(untagged)}) -- these illustrate no record in the "
              f"registry:")
        for slug, why in untagged:
            print(f"  {slug}")
            print(f"     why: {why}")
    print(f"\nsentences with zero grammar links, corpus-wide: {zero}")
    for s in skipped:
        print(f"  ! {s}")
    return 1 if (args.check and changed) else (2 if skipped else 0)


if __name__ == "__main__":
    sys.exit(main())
