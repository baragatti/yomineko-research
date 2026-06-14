#!/usr/bin/env python3
"""Export the courseware OUTLINE (modules -> topics -> introduced items) to LLM-readable files.

course/outline.json (machine) + course/<level>/INDEX.md (readable) + course/INDEX.md.
Lessons (P6) reference the corpus by ID; this outline shows each topic's introducing-item set
(first-pass P4 placement). Re-run after placement/authoring changes.
"""
from __future__ import annotations

import datetime as _dt
import json
import sqlite3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "ingest"))
sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
from i18n_text import get_text  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
DB = ROOT / "db" / "corpus.sqlite"
COURSE = ROOT / "course"


def export_lessons(con: sqlite3.Connection) -> int:
    if not con.execute("SELECT COUNT(*) FROM lesson").fetchone()[0]:
        return 0
    n = 0
    for L in con.execute(
        "SELECT l.*, t.slug AS tslug, t.ord AS tord, t.module_id AS mid, m.level AS level "
        "FROM lesson l JOIN topic t ON t.id=l.topic_id JOIN course_module m ON m.id=t.module_id "
        "ORDER BY t.ord, l.ord"
    ):
        tail = L["tslug"].split(":", 1)[1].replace("n5-", "").replace("n4-", "").replace("pre-n5-", "")
        d = COURSE / L["level"] / f"topic-{L['tord']:02d}-{tail}"
        d.mkdir(parents=True, exist_ok=True)
        intro = {"kanji": [], "vocab": [], "grammar": []}
        for mt, mid in con.execute(
                "SELECT member_type, member_id FROM lesson_introduces WHERE lesson_id=?", (L["id"],)):
            if mt == "kanji":
                r = con.execute("SELECT character FROM kanji WHERE id=?", (mid,)).fetchone()
            elif mt == "vocab":
                r = con.execute("SELECT headword FROM vocab WHERE id=?", (mid,)).fetchone()
            else:
                r = con.execute("SELECT key FROM grammar_point WHERE id=?", (mid,)).fetchone()
            if r:
                intro[mt].append(r[0])
        srefs = [r[0] for r in con.execute(
            "SELECT s.slug FROM lesson_sentence ls JOIN sentence s ON s.id=ls.sentence_id "
            "WHERE ls.lesson_id=?", (L["id"],))]
        exercises = []
        for e in con.execute("SELECT * FROM exercise WHERE lesson_id=? ORDER BY ord", (L["id"],)):
            erefs = [r[0] for r in con.execute(
                "SELECT s.slug FROM exercise_sentence es JOIN sentence s ON s.id=es.sentence_id "
                "WHERE es.exercise_id=?", (e["id"],))]
            exercises.append({"slug": e["slug"], "type": e["type"],
                              "prompt": get_text(con, "exercise", e["id"], "prompt"),
                              "answer": json.loads(e["answer"]) if e["answer"] else None,
                              "explanation": get_text(con, "exercise", e["id"], "explanation"),
                              "sentence_refs": erefs})
        title = get_text(con, "lesson", L["id"], "title")
        objectives = get_text(con, "lesson", L["id"], "objectives") or []
        body = get_text(con, "lesson", L["id"], "body")
        rec = {
            "slug": L["slug"], "level": L["level"], "topic": L["tslug"], "order": L["ord"],
            "title": title, "objectives": objectives,
            "introduces": intro, "sentence_refs": srefs, "exercises": exercises,
            "body": body, "needs_review": bool(L["needs_review"]),
        }
        (d / f"lesson-{L['ord']:02d}.json").write_text(
            json.dumps(rec, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        # readable MD
        md = [f"# {title}", "",
              f"> Lição `{L['slug']}` · tópico `{L['tslug']}` · **needs_review** (Layer C, aguarda professor).",
              "", "**Objetivos:**"]
        md += [f"- {o}" for o in objectives]
        md += ["", "**Introduz:** "
               f"gramática [{', '.join(intro['grammar']) or '—'}] · "
               f"vocabulário [{', '.join(intro['vocab']) or '—'}] · "
               f"kanji [{' '.join(intro['kanji']) or '—'}]", "",
               "**Frases (por ID, do banco dissecado):** " + (", ".join(f"`{s}`" for s in srefs) or "—"),
               "", "---", "", body or "", "", "---", "", "## Exercícios"]
        for i, ex in enumerate(exercises, 1):
            md += [f"### {i}. ({ex['type']}) {ex['prompt']}",
                   f"- **Resposta:** `{json.dumps(ex['answer'], ensure_ascii=False)}`",
                   f"- {ex['explanation']}",
                   (f"- frases: {', '.join('`'+s+'`' for s in ex['sentence_refs'])}"
                    if ex["sentence_refs"] else ""), ""]
        (d / f"lesson-{L['ord']:02d}.md").write_text("\n".join(md) + "\n", encoding="utf-8")
        n += 1
    return n


def main() -> int:
    con = sqlite3.connect(DB)
    con.row_factory = sqlite3.Row
    outline = []
    for m in con.execute("SELECT * FROM course_module ORDER BY ord"):
        mod = {"slug": m["slug"], "level": m["level"], "order": m["ord"],
               "title": get_text(con, "course_module", m["id"], "title"),
               "overview": get_text(con, "course_module", m["id"], "overview"), "topics": []}
        for t in con.execute("SELECT * FROM topic WHERE module_id=? ORDER BY ord", (m["id"],)):
            tid = t["id"]
            vocab = [dict(r) for r in con.execute(
                "SELECT headword, kana, level FROM vocab WHERE introducing_topic_id=? "
                "ORDER BY freq_rank IS NULL, freq_rank", (tid,))]
            kanji = [r[0] for r in con.execute(
                "SELECT character FROM kanji WHERE introducing_topic_id=? "
                "ORDER BY freq_rank IS NULL, freq_rank", (tid,))]
            grammar = [dict(r) for r in con.execute(
                "SELECT key, structure_pattern, level FROM grammar_point WHERE introducing_topic_id=? "
                "ORDER BY key", (tid,))]
            mod["topics"].append({
                "slug": t["slug"], "order": t["ord"],
                "title": get_text(con, "topic", tid, "title"), "theme": get_text(con, "topic", tid, "theme"),
                "objectives": get_text(con, "topic", tid, "objectives") or [],
                "counts": {"vocab": len(vocab), "kanji": len(kanji), "grammar": len(grammar)},
                "introduces": {
                    "vocab": [v["headword"] for v in vocab],
                    "kanji": kanji,
                    "grammar": [g["key"] for g in grammar],
                },
            })
        outline.append(mod)

    COURSE.mkdir(parents=True, exist_ok=True)
    (COURSE / "outline.json").write_text(json.dumps(outline, ensure_ascii=False, indent=2) + "\n",
                                         encoding="utf-8")
    # per-module readable index
    for mod in outline:
        lvl = mod["level"]
        lines = [f"# Curso — Módulo {mod['title']} ({lvl})", "",
                 f"_Gerado {_dt.date.today().isoformat()}. Colocação P4 (1ª passada); lições autoradas em P6 "
                 f"referenciam o corpus por ID._", "",
                 "| # | tópico | tema | vocab | kanji | gramática |",
                 "|--:|--------|------|------:|------:|----------:|"]
        for t in mod["topics"]:
            c = t["counts"]
            lines.append(f"| {t['order']} | {t['title']} | {t['theme'] or ''} | "
                         f"{c['vocab']} | {c['kanji']} | {c['grammar']} |")
        # sample of introduced items per topic
        lines += ["", "## Itens introduzidos por tópico (amostra)", ""]
        for t in mod["topics"]:
            intro = t["introduces"]
            kanji_s = " ".join(intro["kanji"][:20]) or "—"
            vocab_s = "、".join(intro["vocab"][:15]) or "—"
            gram_s = ", ".join(intro["grammar"][:12]) or "—"
            lines += [f"### {t['order']}. {t['title']}",
                      f"- **kanji** ({len(intro['kanji'])}): {kanji_s}",
                      f"- **vocab** ({len(intro['vocab'])}, amostra): {vocab_s}",
                      f"- **gramática** ({len(intro['grammar'])}): {gram_s}", ""]
        (COURSE / lvl).mkdir(parents=True, exist_ok=True)
        (COURSE / lvl / "INDEX.md").write_text("\n".join(lines) + "\n", encoding="utf-8")

    # top index
    tot = {lvl: {"vocab": 0, "kanji": 0, "grammar": 0} for lvl in ("pre-n5", "n5", "n4")}
    for mod in outline:
        for t in mod["topics"]:
            for k in ("vocab", "kanji", "grammar"):
                tot[mod["level"]][k] += t["counts"][k]
    lines = ["# Courseware layer — outline (P4 placement)", "",
             f"_Generated {_dt.date.today().isoformat()}. `course/outline.json` is the machine-readable "
             f"Module→Topic→introducing-item map; per-level `INDEX.md` are readable. Lessons (P6) will hold "
             f"dense pt-BR text + exercises + corpus refs BY ID._", "",
             "| module | topics | vocab | kanji | grammar |",
             "|--------|-------:|------:|------:|--------:|"]
    for mod in outline:
        n = len(mod["topics"])
        t = tot[mod["level"]]
        lines.append(f"| {mod['title']} ({mod['level']}) | {n} | {t['vocab']} | {t['kanji']} | {t['grammar']} |")
    (COURSE / "INDEX.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    nles = export_lessons(con)
    con.close()
    print(f"exported outline: {sum(len(m['topics']) for m in outline)} topics, {nles} lessons -> course/")
    return 0


if __name__ == "__main__":
    sys.exit(main())
