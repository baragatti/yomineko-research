#!/usr/bin/env python3
"""Gate: every generated .md view under course/ is the CURRENT rendering of its JSON source.

WHY THIS EXISTS (review finding F13)
------------------------------------
scripts/export/export_course.py writes `lesson-NN.json` and `lesson-NN.md` in the same pass, so the
pair is consistent the moment it is generated — and never again. Every later fix has been applied to
the JSON alone (apply_qa_instruction_leaks.py is one), which leaves the .md a stale copy of text a
teacher is asked to review. Nothing in the suite opened a .md at all. The review also found the
renderer itself dropping a space-only `<text> </text>` node between a bold run and a following
`<jp>`, fusing words in 21 of 322 files ("não substituiにとって"); that bug is fixed in
export_course.py's `handle_data`, and REGRESSION below pins the fix so it cannot come back silently.

HOW IT CHECKS
-------------
  (A) PAIRING   — every lesson-NN.json has a sibling lesson-NN.md and no .md is an orphan.
  (B) LESSONS   — re-render each lesson's .md from its own .json using export_course's renderer
                  (imported, never re-implemented — a private copy would drift and then agree with
                  itself) and require BYTE equality. This subsumes every weaker check: title, id and
                  topic header, objectives, introduced items, sentence-ref manifest, body prose and
                  the exercise listing all have to match.
  (C) INDEXES   — re-render course/INDEX.md and course/<level>/INDEX.md from course/outline.json and
                  compare with the generation date normalised away (the exporter stamps today's
                  date, which is not a staleness signal).
  (D) REGRESSION— assert on a synthetic body that the renderer still keeps a space-only text node as
                  a word boundary, i.e. F13's defect stays fixed.

THE ONE SANCTIONED DB READ: rendering a `<sentence ref>` / `<reading ref>` line means printing the
sentence's Japanese and its pt-BR translation, and the renderer resolves those through
db/corpus.sqlite. Every other validator in this batch reads the exported JSON only; this one cannot,
because reproducing the .md byte-for-byte means running the real renderer, and the real renderer
takes a sqlite3 connection. The DB is used strictly as the renderer's lookup table — nothing is
validated against it. It defaults to <root>/db/corpus.sqlite and falls back to the repo's own copy
(so --root can point at a data-only tree); --db overrides.

Usage: validate_md_views.py [--root PATH] [--db PATH] [--list N]
"""
from __future__ import annotations

import argparse
import difflib
import json
import re
import sqlite3
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
REPO_ROOT = Path(__file__).resolve().parents[2]
# The renderer always comes from THIS repo's exporter, even when --root points elsewhere: --root
# selects the data under test, not the code under test.
sys.path.insert(0, str(REPO_ROOT / "scripts" / "export"))
import export_course as ec  # noqa: E402

ISO_DATE = re.compile(r"\b\d{4}-\d{2}-\d{2}\b")
LEVELS = ("pre-n5", "n5", "n4", "n3")


def render_lesson_md(con: sqlite3.Connection, rec: dict) -> str:
    """Rebuild a lesson's .md from its exported JSON — a transcription of export_course.py's
    export_lessons() md block (lines ~332-356), reading the leaf instead of the DB rows."""
    loc = ec.LOC
    title = rec["title"].get(loc) or ""
    objectives = [o.get(loc) or "" for o in rec.get("objectives") or []]
    unlocks = rec.get("unlocks") or []
    srefs = rec.get("sentence_refs") or []
    intro = {"kanji": [u["ref"].split(":", 1)[1] for u in unlocks if u["type"] == "kanji"],
             "vocab": [ec._label(con, u["ref"]) for u in unlocks if u["type"] == "vocab"],
             "grammar": [u["ref"].split(":", 1)[1] for u in unlocks if u["type"] == "grammar"],
             "kana": [u["ref"] for u in unlocks if u["type"] == "kana-family"]}
    md = [f"# {title}", "",
          f"> Lição `{rec['id']}` · tópico `{rec['topic']}` · "
          f"**needs_review** (Layer C, aguarda professor).",
          "", "**Objetivos:**"]
    md += [f"- {o}" for o in objectives]
    md += ["", "**Introduz:** "
           f"gramática [{', '.join(intro['grammar']) or '—'}] · "
           f"vocabulário [{', '.join(intro['vocab']) or '—'}] · "
           f"kanji [{' '.join(intro['kanji']) or '—'}] · "
           f"kana [{', '.join(intro['kana']) or '—'}]", "",
           "**Frases (por ID, do banco dissecado):** " + (", ".join(f"`{s}`" for s in srefs) or "—"),
           "", "---", "", ec.flatten_body(con, rec.get("body") or ""), "", "---", "", "## Exercícios"]
    for i, ex in enumerate(rec.get("exercises") or [], 1):
        md += [f"### {i}. ({ex['type']}) {ex['prompt'].get(loc) or ''}",
               f"- **Resposta:** `{json.dumps(ex['answer'], ensure_ascii=False)}`",
               f"- {ex['explanation'].get(loc) or ''}",
               (f"- frases: {', '.join('`' + s + '`' for s in ex['sentence_refs'])}"
                if ex["sentence_refs"] else ""), ""]
    return "\n".join(md) + "\n"


def render_level_index(mod: dict) -> str:
    """Transcription of export_course.py's per-module INDEX.md block (lines ~480-503)."""
    lines = [f"# Curso — Módulo {mod['title']} ({mod['level']})", "",
             "_Gerado <date>. Colocação P4 (1ª passada); lições autoradas em P6 "
             "referenciam o corpus por ID._", "",
             "| # | tópico | tema | vocab | kanji | gramática |",
             "|--:|--------|------|------:|------:|----------:|"]
    for t in mod["topics"]:
        c = t["counts"]
        lines.append(f"| {t['order']} | {t['title']} | {t['theme'] or ''} | "
                     f"{c['vocab']} | {c['kanji']} | {c['grammar']} |")
    lines += ["", "## Itens introduzidos por tópico (amostra)", ""]
    for t in mod["topics"]:
        intro = t["introduces"]
        lines += [f"### {t['order']}. {t['title']}",
                  f"- **kanji** ({len(intro['kanji'])}): {' '.join(intro['kanji'][:20]) or '—'}",
                  f"- **vocab** ({len(intro['vocab'])}, amostra): {'、'.join(intro['vocab'][:15]) or '—'}",
                  f"- **gramática** ({len(intro['grammar'])}): {', '.join(intro['grammar'][:12]) or '—'}",
                  ""]
    return "\n".join(lines) + "\n"


def render_top_index(outline: list) -> str:
    """Transcription of export_course.py's top-level INDEX.md block (lines ~505-521)."""
    tot = {lvl: {"vocab": 0, "kanji": 0, "grammar": 0} for lvl in LEVELS}
    for mod in outline:
        for t in mod["topics"]:
            for k in ("vocab", "kanji", "grammar"):
                tot.setdefault(mod["level"], {"vocab": 0, "kanji": 0, "grammar": 0})[k] += t["counts"][k]
    lines = ["# Courseware layer — outline (P4 placement)", "",
             "_Generated <date>. `course/outline.json` is the machine-readable "
             "Module→Topic→introducing-item map; per-level `INDEX.md` are readable. Lessons (P6) will hold "
             "dense pt-BR text + exercises + corpus refs BY ID._", "",
             "| module | topics | vocab | kanji | grammar |",
             "|--------|-------:|------:|------:|--------:|"]
    for mod in outline:
        t = tot[mod["level"]]
        lines.append(f"| {mod['title']} ({mod['level']}) | {len(mod['topics'])} | "
                     f"{t['vocab']} | {t['kanji']} | {t['grammar']} |")
    return "\n".join(lines) + "\n"


def _undate(s: str) -> str:
    return ISO_DATE.sub("<date>", s)


def _first_diff(committed: str, rendered: str) -> str:
    d = list(difflib.unified_diff(committed.splitlines(), rendered.splitlines(),
                                  "committed", "rendered", lineterm="", n=0))
    return " | ".join(x[:110] for x in d[2:6]) or "(differs only in trailing whitespace)"


def check_regression(con: sqlite3.Connection) -> list[str]:
    """F13's defect, pinned: a space-only text node between two runs is a word boundary."""
    body = ('<p><text weight="bold">não substitui</text><text> </text><jp reading="">にとって</jp></p>')
    out = ec.flatten_body(con, body)
    if "substituiにとって" in out or "não substitui にとって" not in out:
        return [f"renderer regression: space-only <text> node dropped — flatten_body gave {out!r}"]
    return []


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=str(REPO_ROOT), help="tree to validate (default: repo root)")
    ap.add_argument("--db", default=None, help="renderer lookup DB (default: <root>/db/corpus.sqlite)")
    ap.add_argument("--list", type=int, default=15, help="max FAIL lines to print")
    args = ap.parse_args()
    root = Path(args.root).resolve()
    course = root / "course"
    if not course.is_dir():
        print(f"validate_md_views: no {course} (skip)")
        return 0

    db = Path(args.db) if args.db else (root / "db" / "corpus.sqlite")
    if not db.exists():
        db = REPO_ROOT / "db" / "corpus.sqlite"
    if not db.exists():
        print(f"validate_md_views: FAIL — no renderer DB at {db}; the .md view cannot be re-rendered")
        return 1
    con = sqlite3.connect(db)
    con.row_factory = sqlite3.Row

    fails: list[str] = []
    fails += check_regression(con)

    # (A) pairing + (B) byte-equal lesson views
    jsons = sorted(course.glob("*/topic-*/lesson-*.json"))
    mds = {p for p in course.glob("*/topic-*/lesson-*.md")}
    n_lessons = n_ok = 0
    for p in jsons:
        m = p.with_suffix(".md")
        mds.discard(m)
        n_lessons += 1
        if not m.exists():
            fails.append(f"{m.relative_to(root).as_posix()}: missing .md view for its .json")
            continue
        rec = json.loads(p.read_text(encoding="utf-8"))
        committed = m.read_text(encoding="utf-8")
        rendered = render_lesson_md(con, rec)
        if committed == rendered:
            n_ok += 1
        else:
            fails.append(f"{m.relative_to(root).as_posix()}: stale — {_first_diff(committed, rendered)}")
    for orphan in sorted(mds):
        fails.append(f"{orphan.relative_to(root).as_posix()}: .md view with no .json source")

    # (C) generated index tables, date-normalised
    n_index = 0
    outline_p = course / "outline.json"
    if outline_p.exists():
        outline = json.loads(outline_p.read_text(encoding="utf-8"))
        targets = [(course / "INDEX.md", render_top_index(outline))]
        targets += [(course / mod["level"] / "INDEX.md", render_level_index(mod)) for mod in outline]
        for path, rendered in targets:
            n_index += 1
            if not path.exists():
                fails.append(f"{path.relative_to(root).as_posix()}: missing generated index")
                continue
            committed = path.read_text(encoding="utf-8")
            if _undate(committed) != _undate(rendered):
                fails.append(f"{path.relative_to(root).as_posix()}: stale vs course/outline.json — "
                             f"{_first_diff(_undate(committed), _undate(rendered))}")
    con.close()

    for f in fails[:args.list]:
        print("  FAIL", f)
    if len(fails) > args.list:
        print(f"  ... {len(fails) - args.list} more")
    print(f"\nvalidate_md_views: {n_ok}/{n_lessons} lesson .md byte-identical to a fresh render, "
          f"{n_index} generated indexes, "
          + (f"FAIL {len(fails)} — re-run scripts/export/export_course.py" if fails else "ALL OK"))
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
