#!/usr/bin/env python3
"""JLPT alignment — course re-sequencing for promoted KANJI (design/jlpt_alignment_plan.md §4.4).

Creates per-level exam-prep topics (top:n5-kanji-exame / top:n4-kanji-exame) with TEMPLATE lessons that teach
the kanji promoted INTO that level (anchor members not yet taught by that level's course). Bodies are built
ONLY from verified corpus facts (kanji chip + stroke viewer + readings via the chip's detail page + example
words already in the registry) — no generated Japanese. Unlocks are MOVED: removed from their donor lesson
(the N4/N3 lesson that used to introduce the kanji) and introduced by the new lesson. Idempotent by slug.
Usage: build_exam_kanji_lessons.py"""
from __future__ import annotations
import json, sqlite3, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
from i18n_text import set_text  # noqa: E402
# W01: honour --db / $YOMINEKO_DB so a rebuild can target a scratch DB (scripts/dbtarget.py).
import sys as _sys, pathlib as _pl  # noqa: E402
_sys.path.append(str(next(p for p in _pl.Path(__file__).resolve().parents if p.name == "scripts")))
from dbtarget import db_target, out_root  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
DB = db_target(ROOT / "db" / "corpus.sqlite")
# W01: the lesson authoring layer is both read and rewritten by the rebuild chain, so it
# follows --out-root / $YOMINEKO_OUT_ROOT: a redirected rebuild works on its own copy and
# never edits the repo's tracked lessons. Unset, this is the same path it always was.
LESSONS = out_root(ROOT) / "research" / "derived" / "lessons"
PER_LESSON = 8

TOPIC_META = {
    "n5": ("top:n5-kanji-exame", "Kanji do exame N5: reforço", "kanji"),
    "n4": ("top:n4-kanji-exame", "Kanji do exame N4: reforço", "kanji"),
}


def taught_by_level(con, prefixes: tuple) -> set:
    q = " OR ".join("l.slug LIKE ?" for _ in prefixes)
    return {r[0].split(":", 1)[1] for r in con.execute(
        f"SELECT u.ref FROM lesson_unlocks u JOIN lesson l ON l.id=u.lesson_id "
        f"WHERE u.unlock_type='kanji' AND ({q})", tuple(f"les:{p}-%" for p in prefixes))}


def main() -> int:
    con = sqlite3.connect(DB)
    A = json.loads((ROOT / "research/datasets/jlpt_anchor/anchor_kanji.json").read_text(encoding="utf-8"))
    A5, A4 = set(A["n5"]) | {"二"}, set(A["n4"]) - {"二"}
    need = {
        "n5": sorted(A5 - taught_by_level(con, ("pre-n5", "n5"))),
        "n4": sorted(A4 - taught_by_level(con, ("pre-n5", "n5", "n4"))),
    }
    # kanji facts for the template body
    kfact = {ch: (kid,) for kid, ch in con.execute("SELECT id,character FROM kanji")}

    for lvl, kanji_list in need.items():
        # remove n5-list items that n4 will also try to add (n5 wins)
        if lvl == "n4":
            kanji_list = [k for k in kanji_list if k not in need["n5"]]
        if not kanji_list:
            print(f"{lvl}: nothing to add")
            continue
        tslug, ttitle, theme = TOPIC_META[lvl]
        # topic row (idempotent)
        row = con.execute("SELECT id FROM topic WHERE slug=?", (tslug,)).fetchone()
        if row:
            tid = row[0]
        else:
            mod_id = con.execute("SELECT id FROM course_module WHERE level=?", (lvl,)).fetchone()[0]
            maxord = con.execute("SELECT MAX(ord) FROM topic").fetchone()[0] or 0
            con.execute("INSERT INTO topic (slug,module_id,ord,source,created_by,layer,needs_review) "
                        "VALUES (?,?,?,?,'ai','C',1)", (tslug, mod_id, maxord + 1, "jlpt-align"))
            tid = con.execute("SELECT id FROM topic WHERE slug=?", (tslug,)).fetchone()[0]
        set_text(con, "topic", tid, "title", ttitle, layer="C")
        set_text(con, "topic", tid, "theme", theme, layer="C")

        # donor removal: drop these kanji unlocks from the lessons that currently introduce them
        donors = {}
        for ch in kanji_list:
            for (lslug,) in con.execute(
                    "SELECT l.slug FROM lesson_unlocks u JOIN lesson l ON l.id=u.lesson_id "
                    "WHERE u.unlock_type='kanji' AND u.ref=?", (f"kanji:{ch}",)):
                donors.setdefault(lslug, []).append(ch)
        for lslug, chars in donors.items():
            fp = LESSONS / (lslug[4:] + ".json")
            if not fp.exists():
                continue
            d = json.loads(fp.read_text(encoding="utf-8"))
            refs = {f"kanji:{c}" for c in chars}
            d["unlocks"] = [u for u in d.get("unlocks", []) if not (u.get("type") == "kanji" and u.get("ref") in refs)]
            fp.write_text(json.dumps(d, ensure_ascii=False, indent=2), encoding="utf-8")

        # template lessons
        chunks = [kanji_list[i:i + PER_LESSON] for i in range(0, len(kanji_list), PER_LESSON)]
        for n, chunk in enumerate(chunks, 1):
            slug = f"les:{lvl}-kanji-exame-{n:02d}"
            body = [f'<heading level="2"><text>Kanji do exame: reforço {n}</text></heading>',
                    '<p><text>Estes kanji fazem parte do conjunto esperado no exame deste nível. '
                    'Alguns você já viu dentro de palavras; aqui cada um ganha um momento próprio: '
                    'observe o traçado, as leituras e as palavras de exemplo na página de cada kanji '
                    '(toque no kanji para abrir).</text></p>']
            for ch in chunk:
                body.append(f'<heading level="3"><kanji ref="kanji:{ch}"/></heading>')
                body.append(f'<stroke ref="kanji:{ch}"/>')
            body.append("<checklist>")
            for ch in chunk:
                body.append(f' <check item-ref="kanji:{ch}"><text>Reconheço o kanji </text><jp>{ch}</jp>'
                            f'<text> e sei onde conferir suas leituras.</text></check>')
            body.append("</checklist>")
            lesson = {
                "slug": slug, "topic": tslug, "order": n, "schema_version": "1.0",
                "title": f"Kanji do exame: reforço {n}",
                "description": "Reforço dos kanji do conjunto do exame: traçado, leituras e exemplos.",
                "objectives": [f"Reconhecer os kanji {('、'.join(chunk))} e localizar suas leituras"],
                "needs": [], "feature_unlocks": [], "sentence_refs": [],
                "unlocks": [{"type": "kanji", "ref": f"kanji:{ch}"} for ch in chunk],
                "body": "".join(body),
                "exercises": [],
            }
            (LESSONS / (slug[4:] + ".json")).write_text(
                json.dumps(lesson, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"{lvl}: {len(kanji_list)} kanji -> {len(chunks)} lessons in {tslug}; donors touched: {len(donors)}")
    con.commit()
    con.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
