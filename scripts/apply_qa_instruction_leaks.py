#!/usr/bin/env python3
"""Repair seven lessons whose learner-facing text is a QA reviewer's instruction.

Phase-6 QA ran against the pre-renumbering copy of the N3 tree and its findings were applied to the
renumbered one. In seven lessons the finding TEXT was pasted into the field instead of the correction
it asked for, so the instruction is what a learner now reads. The clearest case is
`les:n3-conectores-07`, whose title is:

    "Retitle to the actual content, e.g. 'Pessoas, crime e medida: vocabulário da linha は', and
     update the matching <heading level="2"> at the top of body, which repeats the old title."

An independent audit of the archived copies surfaced these; each was then confirmed field by field
against both copies before being listed here.

These are NOT blind reverts. Where the reviewer's instruction contains the improvement they were
asking for, the improvement is applied and only the instruction wrapper is removed — restoring the old
copy would throw the QA finding away. Where the live copy is simply damaged (a Cyrillic т inside
～にとって, and a dropped clause) the clean text is restored.

Writes BOTH layers of every lesson:
  * `db/corpus.sqlite` localized_text -- what the exporters read, and
  * `research/derived/lessons/<slug>.json` -- the tracked authoring source that load_lessons.py
    re-authors the DB from.
The first version of this script wrote only the DB. That was the wrong layer on its own: db/*.sqlite is
git-ignored and regenerable, so the repair looked done in the exports while all nine fields stayed
corrupt in the durable source, and the next `load_lessons.py` + `export_course.py` cycle would have
reintroduced every one of them (including the Cyrillic mojibake). Run export_course.py afterwards.

Idempotent: every edit is matched on its exact current value, so a second run reports 0 changes. The two
layers are checked independently, so a field already repaired in one layer is still repaired in the other.
Usage: apply_qa_instruction_leaks.py [--check]
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
LESSON_SRC = ROOT / "research" / "derived" / "lessons"

# (lesson slug, field, index-or-None, exact current value, corrected value, why)
FIXES: list[tuple[str, str, int | None, str, str, str]] = [
    (
        "les:n3-conectores-07", "title", None,
        "Retitle to the actual content, e.g. 'Pessoas, crime e medida: vocabulário da linha は', and "
        "update the matching <heading level=\"2\"> at the top of body, which repeats the old title.",
        "Pessoas, crime e medida: vocabulário da linha は",
        "The instruction names the title it wants; apply it rather than restoring the generic old one.",
    ),
    (
        "les:n3-desejos-07", "title", None,
        "Title: 'Corpo, natureza e cotidiano: o bloco ほ'",
        "Corpo, natureza e cotidiano: o bloco ほ",
        "Only the `Title: '...'` wrapper leaked. The proposed title is also better than the archived "
        "'Lar, corpo e natureza: o batch ho', which left the English word 'batch' in pt-BR prose.",
    ),
    (
        "les:n3-estado-07", "objectives", 1,
        "Empregar termos de ciência e matéria como 物質 e 物理 (fix the parallel <check> in the body "
        "checklist too)",
        "Empregar termos de ciência e matéria como 物質, 物理 e 不正",
        "The instruction's parenthetical replaced the third item; the clean copy still lists 不正.",
    ),
    (
        "les:n3-tempo-07", "objectives", 1,
        "Distinguir palavras parecidas: 額 (ひたい, testa; がく, quantia) e os verbos que soam ひく, como "
        "轢く (atropelar). Aplicar a mesma correção ao item idêntico do <checklist> no body e ao 'com "
        "atenção aos homófonos' da description, para a lição não voltar a usar o termo errado.",
        "Distinguir palavras parecidas: 額 (ひたい, testa; がく, quantia) e os verbos que soam ひく, como "
        "轢く (atropelar).",
        "Keep the reviewer's rewritten sentence — it is more precise than the archived one — and drop "
        "only the instruction that followed it. The body already carries the same corrected wording.",
    ),
    (
        "les:n3-causa-07", "description", None,
        "Esta lição ensina prefixos de negação como 不 e 無 e Esta lição ensina prefixos de negação como "
        "不 e 無 e um grupo de palavras N3 com leitura fu e bu, de ansiedade e infelicidade a casal, arma "
        "e paisagem. (matches the house phrasing 'com leitura fu e bu' used in "
        "course/n3/topic-40-estado/lesson-07.json and topic-42-estado/lesson-07.json; the same edit "
        "should also be applied to the mirrored copies in course/n3/topic-39-causa/ and to the title "
        "'Prefixos de negação e palavras do cotidiano com fu').",
        "Esta lição ensina prefixos de negação como 不 e 無 e um grupo de palavras N3 com leitura fu e "
        "bu, de ansiedade e infelicidade a casal, arma e paisagem.",
        "The opening clause was pasted twice and the rationale note left attached. Keep the reviewer's "
        "'fu e bu' correction, drop the duplication and the note.",
    ),
    (
        "les:n3-perspectiva-05", "description", None,
        "Lição de expansão de vocabulário N3 com foco em referência e ponto de vista: palavras para "
        "encontros (出会い, 出会う), propostas e prazos (提案, 定期, 提出), grau e adequação (程度, 適する), "
        "além de termos do clima e do cotidiano. As frases-exemplo reaproveitam estruturas já vistas, "
        "como ～について, ～にとття, ～において.",
        "Lição de expansão de vocabulário N3 com foco em referência e ponto de vista: palavras para "
        "encontros (出会い, 出会う), propostas e prazos (提案, 定期, 提出), grau e adequação (程度, 適する), "
        "além de termos do clima e do cotidiano. As frases-exemplo reaproveitam estruturas já vistas, "
        "como ～について, ～にとって, ～において e ～にかわって.",
        "Two separate defects: a Cyrillic т and я inside ～にとって (mojibake, so the form is unsearchable "
        "and renders wrong), and the dropped final item ～にかわって.",
    ),
]

# Body edits, keyed the same way: (lesson slug, exact substring, replacement, why)
BODY_FIXES: list[tuple[str, str, str, str]] = [
    (
        "les:n3-conectores-07",
        "<heading level=\"2\"><text>Conectores e organização do discurso</text></heading>",
        "<heading level=\"2\"><text>Pessoas, crime e medida: vocabulário da linha は</text></heading>",
        "The instruction asked for the body heading to follow the retitle; it still repeated the old one.",
    ),
    (
        "les:n3-estado-07",
        "Emprego termos de ciência e matéria como 物質 e 物理.",
        "Emprego termos de ciência e matéria como 物質, 物理 e 不正.",
        "The parallel <check> the instruction referred to, brought in line with the objective.",
    ),
]

EXERCISE_FIXES: list[tuple[str, str, str, str, str]] = [
    (
        "ex:n3-relato-06-2", "prompt",
        "Qual destes verbos se lê はく e significa vomitar? (mesma correção na cópia "
        "course/n3/topic-48-relato/lesson-06.json)",
        "Qual destes verbos se lê はく e significa vomitar?",
        "Keep the reviewer's rewritten prompt, drop the note about the mirrored copy.",
    ),
]


class SourceLayer:
    """The tracked authoring source, edited in place without reflowing anything else.

    Files are pretty-printed with `json.dumps(..., ensure_ascii=False, indent=2)`; some carry CRLF and
    some have no trailing newline. Each file is only touched when re-serialising the parsed object
    reproduces it byte for byte, so a whitespace reflow can never ride along with a content repair.
    """

    def __init__(self, check: bool) -> None:
        self.check = check
        self.loaded: dict[str, tuple[dict, str, bool]] = {}
        self.dirty: set[str] = set()

    def _path(self, lesson_slug: str) -> Path:
        return LESSON_SRC / (lesson_slug.replace("les:", "") + ".json")

    def get(self, lesson_slug: str):
        if lesson_slug in self.loaded:
            return self.loaded[lesson_slug]
        p = self._path(lesson_slug)
        if not p.exists():
            return None
        raw = p.read_text(encoding="utf-8", newline="")
        newline = "\r\n" if "\r\n" in raw else "\n"
        norm = raw.replace("\r\n", "\n")
        trailing = norm.endswith("\n")
        obj = json.loads(norm)
        if json.dumps(obj, ensure_ascii=False, indent=2) + ("\n" if trailing else "") != norm:
            return None
        self.loaded[lesson_slug] = (obj, newline, trailing)
        return self.loaded[lesson_slug]

    def save(self) -> None:
        for slug in sorted(self.dirty):
            obj, newline, trailing = self.loaded[slug]
            text = json.dumps(obj, ensure_ascii=False, indent=2) + ("\n" if trailing else "")
            self._path(slug).write_bytes(text.replace("\n", newline).encode("utf-8"))

    # -- edits; each returns 'applied' | 'noop' | 'skip:<reason>' --
    def field(self, lesson_slug: str, field: str, idx, before: str, after: str) -> str:
        got = self.get(lesson_slug)
        if got is None:
            return "skip:source file missing or not byte-reproducible"
        obj = got[0]
        if field not in obj:
            return "skip:field absent from source"
        if idx is None:
            cur, container, key = obj[field], obj, field
        else:
            items = obj[field]
            if not isinstance(items, list) or idx >= len(items):
                return "skip:index out of range"
            cur, container, key = items[idx], items, idx
        if cur == after:
            return "noop"
        if cur != before:
            return "skip:source value does not match the expected corrupted text"
        if not self.check:
            container[key] = after
            self.dirty.add(lesson_slug)
        return "applied"

    def body(self, lesson_slug: str, before: str, after: str) -> str:
        got = self.get(lesson_slug)
        if got is None:
            return "skip:source file missing or not byte-reproducible"
        obj = got[0]
        cur = obj.get("body")
        if not isinstance(cur, str):
            return "skip:no body in source"
        if before not in cur:
            return "noop" if after in cur else "skip:expected body text not found"
        if cur.count(before) != 1:
            return f"skip:expected body text occurs {cur.count(before)}x"
        if not self.check:
            obj["body"] = cur.replace(before, after)
            self.dirty.add(lesson_slug)
        return "applied"

    def exercise(self, lesson_slug: str, ex_slug: str, field: str, before: str, after: str) -> str:
        got = self.get(lesson_slug)
        if got is None:
            return "skip:source file missing or not byte-reproducible"
        obj = got[0]
        match = [e for e in obj.get("exercises", []) if e.get("slug") == ex_slug]
        if not match:
            return "skip:exercise absent from source"
        ex = match[0]
        if ex.get(field) == after:
            return "noop"
        if ex.get(field) != before:
            return "skip:source value does not match the expected corrupted text"
        if not self.check:
            ex[field] = after
            self.dirty.add(lesson_slug)
        return "applied"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args()
    con = sqlite3.connect(DB)
    con.execute("PRAGMA busy_timeout=60000")
    src = SourceLayer(args.check)

    changed, skipped = 0, []

    def report(label: str, status: str, why: str) -> None:
        """Fold a SourceLayer result into the same counters the DB edits use."""
        nonlocal changed
        if status == "applied":
            print(f"  {label}\n     why: {why}")
            changed += 1
        elif status.startswith("skip:"):
            skipped.append(f"{label}: {status[5:]}")

    def lesson_id(slug: str):
        r = con.execute("SELECT id FROM lesson WHERE slug=?", (slug,)).fetchone()
        return r[0] if r else None

    def get(etype: str, eid: int, field: str):
        r = con.execute(
            "SELECT value, is_list FROM localized_text WHERE entity_type=? AND entity_id=? "
            "AND field=? AND locale='pt-BR'", (etype, eid, field)).fetchone()
        return r if r else (None, None)

    def put(etype: str, eid: int, field: str, value: str, is_list: int) -> None:
        con.execute(
            "UPDATE localized_text SET value=? WHERE entity_type=? AND entity_id=? AND field=? "
            "AND locale='pt-BR'", (value, etype, eid, field))

    for slug, field, idx, before, after, why in FIXES:
        label = f"{slug}.{field}" + ("" if idx is None else f"[{idx}]")
        lid = lesson_id(slug)
        if lid is None:
            skipped.append(f"{slug}: no such lesson")
        else:
            raw, is_list = get("lesson", lid, field)
            if raw is None:
                skipped.append(f"{label} (db): no localized_text row")
            else:
                new = None
                if is_list:
                    items = json.loads(raw)
                    if idx is None or idx >= len(items):
                        skipped.append(f"{label} (db): index out of range")
                    elif items[idx] == after:
                        pass                                   # already repaired
                    elif items[idx] != before:
                        skipped.append(f"{label} (db): current value does not match the expected "
                                       f"corrupted text — not touching it")
                    else:
                        items[idx] = after
                        new = json.dumps(items, ensure_ascii=False)
                else:
                    if raw == after:
                        pass
                    elif raw != before:
                        skipped.append(f"{label} (db): current value does not match the expected "
                                       f"corrupted text — not touching it")
                    else:
                        new = after
                if new is not None:
                    print(f"  {label} (db)")
                    print(f"     why: {why}")
                    if not args.check:
                        put("lesson", lid, field, new, is_list)
                    changed += 1
        report(f"{label} (source)", src.field(slug, field, idx, before, after), why)

    for slug, before, after, why in BODY_FIXES:
        lid = lesson_id(slug)
        if lid is None:
            skipped.append(f"{slug}: no such lesson")
        else:
            raw, is_list = get("lesson", lid, "body")
            if raw is None:
                skipped.append(f"{slug}.body (db): no localized_text row")
            elif after in raw:
                pass
            elif before not in raw:
                skipped.append(f"{slug}.body (db): expected text not found — not touching it")
            else:
                print(f"  {slug}.body (db)\n     why: {why}")
                if not args.check:
                    put("lesson", lid, "body", raw.replace(before, after), is_list)
                changed += 1
        report(f"{slug}.body (source)", src.body(slug, before, after), why)

    for eslug, field, before, after, why in EXERCISE_FIXES:
        r = con.execute(
            "SELECT e.id, l.slug FROM exercise e JOIN lesson l ON l.id=e.lesson_id WHERE e.slug=?",
            (eslug,)).fetchone()
        if not r:
            skipped.append(f"{eslug}: no such exercise"); continue
        raw, is_list = get("exercise", r[0], field)
        if raw is None:
            skipped.append(f"{eslug}.{field} (db): no localized_text row")
        elif raw == after:
            pass
        elif raw != before:
            skipped.append(f"{eslug}.{field} (db): current value does not match — not touching it")
        else:
            print(f"  {eslug}.{field} (db)\n     why: {why}")
            if not args.check:
                put("exercise", r[0], field, after, is_list)
            changed += 1
        report(f"{eslug}.{field} (source)", src.exercise(r[1], eslug, field, before, after), why)

    if not args.check:
        con.commit()
        src.save()
    verb = "would repair" if args.check else "repaired"
    print(f"\n{verb} {changed} field(s)")
    for s in skipped:
        print(f"  ! {s}")
    return 1 if (args.check and changed) else (2 if skipped else 0)


if __name__ == "__main__":
    sys.exit(main())
