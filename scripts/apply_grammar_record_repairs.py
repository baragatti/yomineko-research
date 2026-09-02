#!/usr/bin/env python3
"""Apply the per-record grammar repairs the four accuracy sweeps asked for.

Four auditors read all 496 grammar records (research/reports/qa_sweep/grammar_accuracy_1.md ..
_4.md). This script lands the findings that are a CORRECTION TO ONE NAMED RECORD. Three kinds:

  * `text`   -- a `localized_text` field on the grammar point (formation / explanation / nuance /
                form_meanings, pt-BR or en). The worst of these are formation rules that would make
                a learner PRODUCE wrong Japanese: gram:n3-nanka licensing ×行くなんか, gram:n3-you-ni-3
                telling you to build the な-adjective branch with に (which yields the ordinary adverb
                静かに), gram:naide whose whole pt-BR formation was gram:naa's text pasted in verbatim,
                gp-101 saying 一人 counts animals, gp-56 calling くれる's ます-form irregular when every
                form it lists is the regular ichidan output. The rest are meaning/nuance errors,
                broken punctuation that swallowed whole sentences into a parenthetical, pipeline
                residue ("the seed", raw "gid 428" row ids) and eaten pt-BR diacritics.
  * `forms`   -- `grammar_point.forms_json`. The placeholder stripper turned patterns into non-words
                (×はの一つだ, ×しし, ×てすみ, ×おください). The paired `form_meanings` key is renamed in the
                same table, since that map is keyed by the form string.
  * `unlink`  -- a `sentence_grammar` row where the sentence illustrates the sense the record
                EXPLICITLY EXCLUDES, or a different point entirely: ようだ shown by five ようと思う
                sentences, gp-63 (passive) shown by two potentials and an honorific, ちゃいけない
                (prohibition) shown by four なくちゃいけない (obligation), ずっと durative shown by the
                comparative ずっと.

The hard rule on unlink: a record is NEVER left with zero sentences. Where every one of a record's
carriers was off-point, nothing is emitted and the record is reported in
research/reports/qa_sweep/grammar_repairs_skipped.md instead -- an unillustrated point is worse than
a mis-illustrated one, and the fix there is to author or re-tag carriers first. The guard below is
enforced against the live count as it shrinks, not against a precomputed one.

OUT OF SCOPE and deliberately untouched: identity merges / duplicate pairs, re-keying, populating
`related`, family membership, level tags, `structure_pattern`, `references_json`,
`formation_steps_json` and `steps_unavailable`. Those are owner decisions or need an action this
table cannot express; every one of them is listed in the skipped report.

DB ONLY. This writes `db/corpus.sqlite` and nothing else; corpus/grammar/*.json is exported from the
DB by the orchestrator afterwards -- do not run an exporter from here.

Matching. A `text` or `forms` edit first tries the EXACT stored value. 28 of the 178 findings quote a
distinguishing SPAN of a long field rather than the whole of it, so a second pass accepts `old` as a
substring, and only when it occurs EXACTLY ONCE -- two occurrences is an ambiguous edit and is
skipped, never guessed. The mode used is printed per row.

Idempotent: a field already carrying `new` (whole value or substring) is a no-op, so a second run
reports 0 changes and `--check` after an apply exits clean. Likewise an already-deleted link. A row
whose stored text is neither the expected defective value nor the rewrite is SKIPPED and reported; it
is never overwritten.

Usage: apply_grammar_record_repairs.py [--check] [--data PATH]
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

# The verified repair table: [{key, action, ...}, ...]. TRACKED, not session-scoped, so the run is
# auditable and repeatable. --data PATH still overrides.
DATA = ROOT / "research" / "derived" / "repairs" / "grammar_record_repairs.json"

FIELDS = {"formation", "explanation", "nuance", "meaning", "form_meanings"}
LOCALES = {"pt-BR", "en"}
ACTIONS = {"text", "forms", "unlink"}


def load(path: Path) -> list[dict]:
    rows = json.loads(path.read_text(encoding="utf-8"))
    seen: set[tuple] = set()
    for i, r in enumerate(rows):
        where = f"row {i} ({r.get('key')!r})"
        if "key" not in r or "action" not in r:
            raise SystemExit(f"row {i}: missing `key` or `action`")
        act = r["action"]
        if act not in ACTIONS:
            raise SystemExit(f"{where}: unknown action {act!r}")
        if act == "unlink":
            if not r.get("sentence"):
                raise SystemExit(f"{where}: unlink needs `sentence`")
            target = (r["key"], "unlink", r["sentence"])
        else:
            for k in ("old", "new"):
                if k not in r:
                    raise SystemExit(f"{where}: {act} needs `{k}`")
            if r["old"] == r["new"]:
                raise SystemExit(f"{where}: `new` is identical to `old`")
            if act == "text":
                if r.get("field") not in FIELDS:
                    raise SystemExit(f"{where}: unexpected field {r.get('field')!r}")
                if r.get("locale") not in LOCALES:
                    raise SystemExit(f"{where}: unexpected locale {r.get('locale')!r}")
                target = (r["key"], "text", r["field"], r["locale"])
            else:
                target = (r["key"], "forms")
        if target in seen:
            raise SystemExit(f"{where}: duplicate target {target}")
        seen.add(target)
    return rows


def resolve(current: str, old: str, new: str) -> tuple[str | None, str]:
    """(replacement, mode). replacement is None for a no-op or a skip; mode says which.

    The `new in current` test cannot stand alone as the already-applied signal, in either direction:
    an ADDITIVE span edit (gp-105's nuance, which prepends a lead sentence to the quoted span) still
    contains `old` after it lands and would otherwise be applied twice, while a DELETION span edit
    (gp-152's explanation, which drops a trailing sentence) already contains `new` before it lands
    and would otherwise never be applied at all. So an additive edit is judged done by finding `new`,
    and everything else by no longer finding `old`.
    """
    if current == new:
        return None, "noop"
    if current == old:
        return new, "exact"
    if old in new and new in current:
        return None, "noop"                       # additive span edit; already landed
    n = current.count(old)
    if n == 1:
        return current.replace(old, new), "span"
    if n > 1:
        return None, f"skip:the quoted span occurs {n}x -- ambiguous, not guessing which"
    if new in current:
        return None, "noop"                       # the span was already rewritten in place
    return None, "skip:current value matches neither the expected defective text nor the rewrite"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true", help="report what would change; write nothing")
    ap.add_argument("--data", type=Path, default=DATA, help="path to the repair table (JSON)")
    args = ap.parse_args()

    if not args.data.exists():
        raise SystemExit(f"repair table not found: {args.data}")
    rows = load(args.data)

    con = sqlite3.connect(DB)
    con.execute("PRAGMA busy_timeout=60000")

    changed = already = 0
    skipped: list[str] = []
    # Links this run has removed but not yet committed -- the last-sentence guard must see them.
    dropped: dict[int, int] = {}

    def note(label: str, why: str) -> None:
        print(f"  {label}")
        if why:
            print(f"     why: {why}")

    for r in rows:
        key, act = r["key"], r["action"]
        g = con.execute("SELECT id FROM grammar_point WHERE key=?", (key,)).fetchone()
        if not g:
            skipped.append(f"{key}: no such grammar point")
            continue
        gid = g[0]

        if act == "unlink":
            label = f"{key} -/- {r['sentence']}"
            s = con.execute("SELECT id FROM sentence WHERE slug=?", (r["sentence"],)).fetchone()
            if not s:
                skipped.append(f"{label}: no such sentence")
                continue
            sid = s[0]
            live = con.execute(
                "SELECT 1 FROM sentence_grammar WHERE sentence_id=? AND grammar_id=?",
                (sid, gid)).fetchone()
            if not live:
                already += 1                       # already unlinked
                continue
            total = con.execute("SELECT count(*) FROM sentence_grammar WHERE grammar_id=?",
                                (gid,)).fetchone()[0] - (dropped.get(gid, 0) if args.check else 0)
            if total <= 1:
                skipped.append(f"{label}: REFUSED -- it is the record's last sentence; a record is "
                               f"never left with zero examples")
                continue
            note(label, r.get("why", ""))
            if not args.check:
                con.execute("DELETE FROM sentence_grammar WHERE sentence_id=? AND grammar_id=?",
                            (sid, gid))
            dropped[gid] = dropped.get(gid, 0) + 1
            changed += 1
            continue

        if act == "forms":
            label = f"{key}.forms"
            cur = con.execute("SELECT forms_json FROM grammar_point WHERE id=?", (gid,)).fetchone()[0]
            if cur is None:
                skipped.append(f"{label}: forms_json is NULL")
                continue
            repl, mode = resolve(cur, r["old"], r["new"])
            if mode.startswith("skip:"):
                skipped.append(f"{label}: {mode[5:]}")
                continue
            if repl is None:
                already += 1
                continue
            note(f"{label} [{mode}]", r.get("why", ""))
            if not args.check:
                con.execute("UPDATE grammar_point SET forms_json=? WHERE id=?", (repl, gid))
            changed += 1
            continue

        field, locale = r["field"], r["locale"]
        label = f"{key}.{field} [{locale}]"
        row = con.execute(
            "SELECT value FROM localized_text WHERE entity_type='grammar_point' AND entity_id=? "
            "AND field=? AND locale=?", (gid, field, locale)).fetchone()
        if row is None or row[0] is None:
            skipped.append(f"{label}: no localized_text row")
            continue
        repl, mode = resolve(row[0], r["old"], r["new"])
        if mode.startswith("skip:"):
            skipped.append(f"{label}: {mode[5:]}")
            continue
        if repl is None:
            already += 1
            continue
        note(f"{label} [{mode}]", r.get("why", ""))
        if not args.check:
            con.execute(
                "UPDATE localized_text SET value=? WHERE entity_type='grammar_point' AND "
                "entity_id=? AND field=? AND locale=?", (repl, gid, field, locale))
        changed += 1

    if not args.check:
        con.commit()
    con.close()

    verb = "would repair" if args.check else "repaired"
    print(f"\n{verb} {changed} of {len(rows)} finding(s); {already} already carried the repair")
    for s in skipped:
        print(f"  ! {s}")
    return 1 if (args.check and changed) else (2 if skipped else 0)


if __name__ == "__main__":
    sys.exit(main())
