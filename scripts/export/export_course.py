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
from html.parser import HTMLParser  # noqa: E402

from i18n_text import get_text, DEFAULT_LOCALE as LOC  # noqa: E402
import enums  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
DB = ROOT / "db" / "corpus.sqlite"
COURSE = ROOT / "course"
_dt_today = _dt.date.today().isoformat()


class _Flatten(HTMLParser):
    """Render a rich tagged lesson body to readable Markdown for the human-review .md view (refs resolved)."""

    def __init__(self, con):
        super().__init__(convert_charrefs=True)
        self.con = con
        self.out: list[str] = []
        self.buf: list[str] = []  # current inline run

    def _flush(self):
        line = "".join(self.buf).strip()
        if line:
            self.out.append(line)
        self.buf = []

    def _sentence(self, slug):
        r = self.con.execute("SELECT id, jp FROM sentence WHERE slug=?", (slug,)).fetchone()
        if not r:
            return f"`{slug}`"
        pt = get_text(self.con, "sentence", r[0], "translation") or ""
        return f"{r[1]} — {pt}".strip(" —")

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == "heading":
            self._flush()
            self.out.append("")
            self.buf.append("#" * (int(a.get("level", "2")) + 1) + " ")
        elif tag in ("p", "item", "check"):
            self._flush()
            if tag in ("item", "check"):
                self.buf.append("- ")
        elif tag == "note":
            self._flush()
            self.out.append("")
            self.buf.append(f"> **[{a.get('type', 'note')}]** ")
        elif tag == "divider":
            self._flush()
            self.out.append("\n---\n")
        elif tag == "sentence":
            self._flush()
            self.out.append(f"> 🗣 {self._sentence(a.get('ref', ''))}")
        elif tag == "exercise":
            pass  # exercises are listed separately below the body
        elif tag in ("vocab", "kanji", "grammar"):
            self.buf.append(a.get("ref", "").split(":", 1)[-1])
        elif tag == "ruby":
            self.buf.append(a.get("base", ""))
        elif tag == "break":
            self.buf.append(" ")

    def handle_endtag(self, tag):
        if tag in ("heading", "p", "item", "note", "check", "list", "checklist"):
            self._flush()

    def handle_data(self, data):
        if data.strip():
            self.buf.append(data)

    def result(self):
        self._flush()
        return "\n".join(self.out).strip()


def flatten_body(con, body: str) -> str:
    if not body:
        return ""
    f = _Flatten(con)
    try:
        f.feed(body)
        f.close()
        return f.result()
    except Exception:  # noqa: BLE001
        return body  # fall back to raw on any parse issue


def _srs_cards(unlocks: list, level: str) -> list:
    """Derive the FSRS cards a lesson enrolls from its item unlocks (deck by skill; card types per deck)."""
    cards = []
    for u in unlocks:
        deck = enums.deck_for(u["type"], u["ref"], level)
        if deck and deck in enums.DECK_REGISTRY:
            cards.append({"deck": deck, "item": u["ref"],
                          "card_types": enums.DECK_REGISTRY[deck]["card_types"]})
    return cards


def export_lessons(con: sqlite3.Connection, stubs: dict) -> int:
    """Emit each lesson leaf JSON/MD and collect required-layer stubs (keyed by topic slug) for the manifest."""
    if not con.execute("SELECT COUNT(*) FROM lesson").fetchone()[0]:
        return 0
    n = 0
    for L in con.execute(
        "SELECT l.*, t.slug AS tslug, t.ord AS tord, t.module_id AS mid, m.level AS level "
        "FROM lesson l JOIN topic t ON t.id=l.topic_id JOIN course_module m ON m.id=t.module_id "
        "ORDER BY t.ord, l.ord"
    ):
        tail = L["tslug"].split(":", 1)[1].replace("n5-", "").replace("n4-", "").replace("pre-n5-", "")
        reldir = f"topic-{L['tord']:02d}-{tail}"
        d = COURSE / L["level"] / reldir
        d.mkdir(parents=True, exist_ok=True)
        unlocks = [{"type": u[0], "ref": u[1]} for u in con.execute(
            "SELECT unlock_type, ref FROM lesson_unlocks WHERE lesson_id=? ORDER BY unlock_type, ref", (L["id"],))]
        needs = [{"type": u[0], "ref": u[1]} for u in con.execute(
            "SELECT need_type, ref FROM lesson_needs WHERE lesson_id=? ORDER BY need_type, ref", (L["id"],))]
        feature_unlocks = [u["ref"] for u in unlocks if u["type"] == "feature"]
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
        description = get_text(con, "lesson", L["id"], "description")
        objectives = get_text(con, "lesson", L["id"], "objectives") or []
        body = get_text(con, "lesson", L["id"], "body")
        cks = json.loads(L["cumulative_known_set"]) if L["cumulative_known_set"] else {}
        rec = {
            "slug": L["slug"], "schema_version": "1.0", "level": L["level"], "topic": L["tslug"],
            "order": L["ord"], "title": title, "description": description, "objectives": objectives,
            "needs": needs, "unlocks": unlocks, "feature_unlocks": feature_unlocks,
            "srs": {"introduces_cards": _srs_cards(unlocks, L["level"])},
            "cumulative_known_set": cks, "sentence_refs": srefs, "exercises": exercises,
            "body": body, "needs_review": bool(L["needs_review"]),
        }
        (d / f"lesson-{L['ord']:02d}.json").write_text(
            json.dumps(rec, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        stubs.setdefault(L["tslug"], []).append({
            "id": L["slug"], "order": L["ord"], "title": {LOC: title},
            "description": {LOC: description}, "path": f"{reldir}/lesson-{L['ord']:02d}.json",
            "needs": needs, "unlocks": unlocks})
        intro = {"kanji": [u["ref"].split(":", 1)[1] for u in unlocks if u["type"] == "kanji"],
                 "vocab": [u["ref"].split(":", 1)[1] for u in unlocks if u["type"] == "vocab"],
                 "grammar": [u["ref"].split(":", 1)[1] for u in unlocks if u["type"] == "grammar"]}
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
               "", "---", "", flatten_body(con, body), "", "---", "", "## Exercícios"]
        for i, ex in enumerate(exercises, 1):
            md += [f"### {i}. ({ex['type']}) {ex['prompt']}",
                   f"- **Resposta:** `{json.dumps(ex['answer'], ensure_ascii=False)}`",
                   f"- {ex['explanation']}",
                   (f"- frases: {', '.join('`'+s+'`' for s in ex['sentence_refs'])}"
                    if ex["sentence_refs"] else ""), ""]
        (d / f"lesson-{L['ord']:02d}.md").write_text("\n".join(md) + "\n", encoding="utf-8")
        n += 1
    return n


def _topic_dir(tslug: str, tord: int) -> str:
    tail = tslug.split(":", 1)[1].replace("n5-", "").replace("n4-", "").replace("pre-n5-", "")
    return f"topic-{tord:02d}-{tail}"


def export_manifest(con, outline, stubs) -> None:
    """Emit the required-layer manifest tiers: course/manifest.json -> <level>/course.json -> topic.json."""
    courses = []
    for mod in outline:
        lvl = mod["level"]
        course_topics, mod_lessons = [], 0
        for t in mod["topics"]:
            tslug, tord = t["slug"], t["order"]
            lst = sorted(stubs.get(tslug, []), key=lambda s: s["order"])
            mod_lessons += len(lst)
            tdir = _topic_dir(tslug, tord)
            course_topics.append({"id": tslug, "order": tord, "title": {LOC: t["title"]}, "theme": t["theme"],
                                  "path": f"{tdir}/topic.json", "lesson_count": len(lst),
                                  "unlocks_summary": t["counts"]})
            if lst:  # emit topic.json only once a topic has authored lessons
                td = COURSE / lvl / tdir
                td.mkdir(parents=True, exist_ok=True)
                (td / "topic.json").write_text(json.dumps(
                    {"id": tslug, "order": tord, "level": lvl, "title": {LOC: t["title"]}, "theme": t["theme"],
                     "objectives": [{LOC: o} for o in t["objectives"]], "lessons": lst},
                    ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        (COURSE / lvl).mkdir(parents=True, exist_ok=True)
        (COURSE / lvl / "course.json").write_text(json.dumps(
            {"id": mod["slug"], "level": lvl, "order": mod["order"], "title": {LOC: mod["title"]},
             "overview": {LOC: mod["overview"]}, "topics": course_topics},
            ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        courses.append({"id": mod["slug"], "level": lvl, "order": mod["order"], "title": {LOC: mod["title"]},
                        "path": f"{lvl}/course.json", "topic_count": len(mod["topics"]),
                        "lesson_count": mod_lessons})
    (COURSE / "manifest.json").write_text(json.dumps(
        {"schema_version": "1.0", "generated": _dt_today, "courses": courses,
         "enums_ref": "design/unlock_enums.json"}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


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
    stubs: dict = {}
    nles = export_lessons(con, stubs)
    export_manifest(con, outline, stubs)
    con.close()
    print(f"exported outline: {sum(len(m['topics']) for m in outline)} topics, {nles} lessons, "
          f"4-tier manifest -> course/")
    return 0


if __name__ == "__main__":
    sys.exit(main())
