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
import re as _re  # noqa: E402

from vocab_identity import VocabIdentity  # noqa: E402

_LESSON_SLUG: dict = {}

# Lesson refs arrive as `vocab:<row_id>` / `kanji:<row_id>`, which are storage row numbers and mean
# nothing outside the working index. Rewrite them to the PUBLISHED address of the record: for kanji
# that is `kanji:<character>`, for vocab `vocab:<jmdict_id>` — in both cases exactly the `slug` that
# corpus/{kanji,vocab}/*.json carries, so a courseware ref and a corpus record agree on one identity.
#
# This used to rewrite vocab to `vocab:<headword>`, which reads better but is not an address: 93
# headwords are shared by 193 records (人 is both the N5 "pessoa" and an N1 sense; 仏 is both "Buda"
# and "França"), so 24,031 references resolved to whichever record an index happened to load last, and
# the prototype's own headword index quietly collapsed 7,401 records into 7,301. Headwords are still
# what a human reads — they are looked up for the generated Markdown below — but they are a LABEL, and
# the ref is the identity.
_NUM_MAP: dict = {}
_LABEL: dict = {}


def _load_maps(con) -> None:
    if _NUM_MAP:
        return
    for vid, slug, hw in con.execute("SELECT id, slug, headword FROM vocab"):
        _NUM_MAP[("vocab", str(vid))] = slug.split(":", 1)[1] if ":" in slug else slug
        _LABEL[f"vocab:{_NUM_MAP[('vocab', str(vid))]}"] = hw
    for kid, ch in con.execute("SELECT id, character FROM kanji"):
        _NUM_MAP[("kanji", str(kid))] = ch
        _LABEL[f"kanji:{ch}"] = ch


_IDENT = None
_LEVEL_OF_LESSON: dict = {}


def _identity(con):
    global _IDENT
    if _IDENT is None:
        _IDENT = VocabIdentity(con)
    return _IDENT


def _lesson_level(con, lesson_id) -> str | None:
    if not _LEVEL_OF_LESSON:
        for lid, slug, lvl in con.execute(
                "SELECT l.id, l.slug, m.level FROM lesson l JOIN topic t ON t.id=l.topic_id "
                "JOIN course_module m ON m.id=t.module_id"):
            _LEVEL_OF_LESSON[lid] = lvl
            _LESSON_SLUG[lid] = slug
    return _LEVEL_OF_LESSON.get(lesson_id)


def _deref(con, ref: str, lesson_id=None) -> str:
    """Rewrite a courseware ref to the published address of the record it names.

    Two input forms exist and both are storage artefacts rather than addresses: `vocab:1421` is a row
    number in the working index, and `vocab:人` is a headword that up to three records answer to.
    Both become `vocab:<jmdict_id>`, which is the `slug` corpus/vocab/*.json publishes.
    """
    if ":" not in ref:
        return ref
    ns, ident = ref.split(":", 1)
    if ns not in ("vocab", "kanji"):
        return ref
    # str.isdigit() is true for full-width digits too, and `vocab:０` is a real headword (the N5 word
    # for zero), not a row number. Require ASCII before treating the ref as an index row id.
    if ident.isascii() and ident.isdigit():
        _load_maps(con)
        val = _NUM_MAP.get((ns, ident))
        return f"{ns}:{val}" if val else ref
    if ns == "vocab":
        level = _lesson_level(con, lesson_id) if lesson_id else None   # also fills _LESSON_SLUG
        slug, _how = _identity(con).resolve(ident, level, _LESSON_SLUG.get(lesson_id))
        return slug or ref
    return ref  # kanji:<character> is already the published address


def _label(con, ref: str) -> str:
    """The human-readable form of a ref, for generated Markdown only. Never written into a ref field."""
    _load_maps(con)
    return _LABEL.get(ref, ref.split(":", 1)[1] if ":" in ref else ref)


_CUM: dict = {}
_CUM_KEYS = ("kana-family", "vocab", "kanji", "grammar", "conjugation-form", "phrase")


def _cumulative(con) -> dict:
    """cumulative_known_set per lesson, recomputed here rather than read from the index.

    It is by definition the union of every unlock up to and including the lesson, in course order —
    that is what ingest/load_lessons.py:recompute_cumulative writes. Deriving it at export time instead
    of trusting the stored copy does two things. It picks up unlock edits made after the last recompute
    (97 of 322 lessons had a stored set that still listed refs their unlocks no longer contain), and it
    means the refs land here already dereferenced to slugs, so `cumulative_known_set` speaks the same
    identity as `unlocks` instead of a parallel headword vocabulary that cannot be resolved to one
    record. No headword is guessed at: the unlock row ids map 1:1 onto slugs.
    """
    if _CUM:
        return _CUM
    acc: dict = {k: [] for k in _CUM_KEYS}
    seen: dict = {k: set() for k in _CUM_KEYS}
    for (lid,) in con.execute(
            "SELECT l.id FROM lesson l JOIN topic t ON t.id=l.topic_id ORDER BY t.ord, l.ord"):
        for typ, ref in con.execute(
                "SELECT unlock_type, ref FROM lesson_unlocks WHERE lesson_id=?", (lid,)):
            if typ in acc:
                r = _deref(con, ref, lid)
                if r not in seen[typ]:
                    seen[typ].add(r)
                    acc[typ].append(r)
        _CUM[lid] = {k: list(v) for k, v in acc.items()}
    return _CUM


def _deref_body(con, body: str, lesson_id=None) -> str:
    """Rewrite the inline <vocab .../> and <kanji .../> refs in lesson prose to published addresses.

    Both ref forms appear here — `vocab:1421` (31 of them) and `vocab:物質` (5,468) — and both become
    the record's slug, exactly as the unlock refs do. The lesson id is passed through because the
    headword form needs it to disambiguate; kanji refs already name the character, which IS the slug.
    """
    if not body:
        return body
    return _re.sub(
        r'(<(?:vocab|kanji) ref=")((?:vocab|kanji):[^"]+)(")',
        lambda m: m.group(1) + _deref(con, m.group(2), lesson_id) + m.group(3), body)

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

    def _reading(self, slug):
        try:
            r = self.con.execute("SELECT jp, translation_pt FROM reading WHERE slug=?", (slug,)).fetchone()
        except sqlite3.OperationalError:
            return f"`{slug}`"  # reading table not built yet
        if not r:
            return f"`{slug}`"
        return f"{r[0]} — {r[1] or ''}".strip(" —")

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
        elif tag == "reading":
            self._flush()
            self.out.append(f"> 📖 {self._reading(a.get('ref', ''))}")
        elif tag == "exercise":
            pass  # exercises are listed separately below the body
        elif tag in ("vocab", "kanji", "grammar"):
            # The .md is the human-review view, so a vocab ref renders as its headword. Stripping the
            # prefix was enough while refs WERE headwords; now that they are JMdict ids it would print
            # "1421" in the middle of a Portuguese sentence.
            ref = a.get("ref", "")
            self.buf.append(_label(self.con, ref) if tag == "vocab" else ref.split(":", 1)[-1])
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
        tail = L["tslug"].split(":", 1)[1].replace("pre-n5-", "").replace("n5-", "").replace("n4-", "").replace("n3-", "")
        reldir = f"topic-{L['tord']:02d}-{tail}"
        d = COURSE / L["level"] / reldir
        d.mkdir(parents=True, exist_ok=True)
        unlocks = [{"type": u[0], "ref": _deref(con, u[1], L["id"])} for u in con.execute(
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
            exercises.append({"id": e["slug"], "type": e["type"],
                              "prompt": {LOC: get_text(con, "exercise", e["id"], "prompt")},
                              "answer": json.loads(e["answer"]) if e["answer"] else None,
                              "explanation": {LOC: get_text(con, "exercise", e["id"], "explanation")},
                              "sentence_refs": erefs})
        title = get_text(con, "lesson", L["id"], "title")
        description = get_text(con, "lesson", L["id"], "description")
        objectives = get_text(con, "lesson", L["id"], "objectives") or []
        body = _deref_body(con, get_text(con, "lesson", L["id"], "body"), L["id"])
        cks = _cumulative(con)[L["id"]]
        rec = {
            "id": L["slug"], "schema_version": "1.0", "level": L["level"], "topic": L["tslug"],
            "order": L["ord"], "title": {LOC: title}, "description": {LOC: description},
            "objectives": [{LOC: o} for o in objectives],
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
        # The Markdown is for a human reviewer, so it shows headwords; the JSON above carries the refs.
        intro = {"kanji": [u["ref"].split(":", 1)[1] for u in unlocks if u["type"] == "kanji"],
                 "vocab": [_label(con, u["ref"]) for u in unlocks if u["type"] == "vocab"],
                 "grammar": [u["ref"].split(":", 1)[1] for u in unlocks if u["type"] == "grammar"],
                 "kana": [u["ref"] for u in unlocks if u["type"] == "kana-family"]}
        # readable MD
        md = [f"# {title}", "",
              f"> Lição `{L['slug']}` · tópico `{L['tslug']}` · **needs_review** (Layer C, aguarda professor).",
              "", "**Objetivos:**"]
        md += [f"- {o}" for o in objectives]
        md += ["", "**Introduz:** "
               f"gramática [{', '.join(intro['grammar']) or '—'}] · "
               f"vocabulário [{', '.join(intro['vocab']) or '—'}] · "
               f"kanji [{' '.join(intro['kanji']) or '—'}] · "
               f"kana [{', '.join(intro['kana']) or '—'}]", "",
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
    tail = tslug.split(":", 1)[1].replace("pre-n5-", "").replace("n5-", "").replace("n4-", "").replace("n3-", "")
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
            if lst:  # only list + emit a topic once it has authored lessons (avoid dangling refs)
                course_topics.append({"id": tslug, "order": tord, "title": {LOC: t["title"]}, "theme": t["theme"],
                                      "path": f"{tdir}/topic.json", "lesson_count": len(lst),
                                      "unlocks_summary": t["counts"]})
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
                "SELECT headword, kana, level, slug FROM vocab WHERE introducing_topic_id=? "
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
                # `introduces` is the readable listing (headwords); `introduces_refs` is the
                # addressable one. Two fields rather than one ambiguous field: a headword is not
                # unique, and this file is described as machine-readable.
                "introduces": {
                    "vocab": [v["headword"] for v in vocab],
                    "kanji": kanji,
                    "grammar": [g["key"] for g in grammar],
                },
                "introduces_refs": {
                    "vocab": [v["slug"] for v in vocab],
                    "kanji": [f"kanji:{c}" for c in kanji],
                    "grammar": [f"gram:{g['key']}" for g in grammar],
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
    tot = {lvl: {"vocab": 0, "kanji": 0, "grammar": 0} for lvl in ("pre-n5", "n5", "n4", "n3")}
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

    # Publish whatever the headword->slug resolution could not settle on evidence alone. This is a
    # short list (the vast majority of headwords name exactly one record) but it is the part a teacher
    # has to look at, so it gets a file rather than a line of console output that scrolls away.
    ident = _IDENT
    if ident is not None and ident.review:
        rows = sorted(ident.review, key=lambda r: (r["how"] != "unresolved", r["headword"]))
        seen_hw, deduped = set(), []
        for r in rows:
            if r["headword"] in seen_hw:
                continue
            seen_hw.add(r["headword"])
            deduped.append(r)
        (COURSE / "vocab_disambiguation_review.json").write_text(
            json.dumps({"generated": _dt_today,
                        "why": "Lessons address vocabulary by headword; these headwords name more "
                               "than one record and the lesson's level did not single one out. "
                               "`how` says what decided it: 'frequency' used the sentence bank, "
                               "'unresolved' had nothing to go on and took the lowest JMdict entry. "
                               "Both need a teacher to confirm which sense the lesson teaches.",
                        "count": len(deduped), "items": deduped},
                       ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        nfreq = sum(1 for r in deduped if r["how"] == "frequency")
        print(f"vocab disambiguation: {len(deduped)} headword(s) needed more than the lesson level "
              f"({nfreq} settled by corpus frequency, {len(deduped) - nfreq} await a teacher) "
              f"-> course/vocab_disambiguation_review.json")
    con.close()
    print(f"exported outline: {sum(len(m['topics']) for m in outline)} topics, {nles} lessons, "
          f"4-tier manifest -> course/")
    return 0


if __name__ == "__main__":
    sys.exit(main())
