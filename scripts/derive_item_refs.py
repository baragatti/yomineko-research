#!/usr/bin/env python3
"""W23. `item_refs[]` on every lesson exercise: which corpus items it TESTS. Derived, not authored.

WHY
---
An exercise could not say what it tests, so there was nothing to key a mistake index, a topic test or a
placement probe on (design/assessment.md §1). The field existed in the authoring source, empty on every
exercise, and the exporter never emitted it. This script fills it by the rule of design/assessment.md
§2.2; `scripts/apply_item_refs.py` writes it into both layers; `validate_item_refs.py` re-derives it on
the tree being validated (check E) by importing `derive_all` from here.

THE RULE (design/assessment.md §2.2, in order; `derived_by` names the rule that produced an entry)
------------------------------------------------------------------------------------------------
  0  a tracked table that declares `targets` for the exercise wins; nothing else runs
     (`table:practice_kanji_exercises`, `table:practice_vocab_exercises`)
  0b the exercise's own AUTHORED refs in research/derived/lessons/ (556 exercises carried them,
     unexported; see Context), each resolved to the one published id inside the lesson's known set;
     nothing else runs when at least one resolves (`authored`)
  1  `<vocab|kanji|grammar ref>` markup in the prompt (`markup`)
  2  the answer surfaces, per type (`answer`): cloze `text` (else `full`); production / handwriting
     `text`; recognition / reading / listening / particle_choice `correct`; sentence_build / ordering
     `text`; matching both members of every pair. Distractors and `accept` variants are never read.
     Vocab by the practice gate's MaxMatch tiler (an answer that IS a cited sentence is read through
     that sentence's token dissection instead), kanji by containment, grammar by probe segment.
     Every hit is intersected with the lesson's cumulative_known_set.
  3  the prompt's Japanese, kept only where it names an item THIS lesson unlocks (`prompt-unlocks`)
  4  only if 2-3 found nothing: the cited sentence's own dissection, known-set only, narrowed to the
     lesson's unlocks when that is non-empty (`cited-sentence`)
  5  only if 1-4 found nothing and the lesson unlocks kana: the answer strings and the prompt tiled
     longest-match against the kana glyph registry, plus quoted romaji ('ryo'), kept where the glyph's
     family is unlocked by this lesson (`kana`)
  6  narrowing: if the set meets the lesson's own unlocks, that intersection is the target set
The matcher is `validate_practice_coverage.py`'s, imported: one definition of "asks about this item".
Only `role: target` is written (`context` is contracted and empty, §2.1).

OUTPUT
------
  research/derived/repairs/item_refs.json        rows {exercise, lesson, item_refs[]} (every exercise
                                                  with >= 1 target)
  course/item_ref_exemptions.json                exercises whose lesson unlocks no item at all and is
                                                  not a review lesson: course metalanguage and
                                                  phonology, not a corpus item (§2.4)
  research/derived/pending/item_refs_residue.json the rest of the exercises with no target: the
                                                  authoring residue (listed, not authored here)

Reads the EXPORTED tree (course/, corpus/) + the two practice tables. Deterministic.
Usage: derive_item_refs.py [--root PATH] [--check]
"""
from __future__ import annotations

import argparse
import collections
import json
import re
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
_SCRIPTS = Path(__file__).resolve().parent
sys.path.insert(0, str(_SCRIPTS / "validate"))
import validate_practice_coverage as vpc  # noqa: E402

REPO = _SCRIPTS.parent
TABLES = ("practice_kanji_exercises", "practice_vocab_exercises")
TYPE_OF_PREFIX = {"vocab": "vocab", "kanji": "kanji", "gram": "grammar", "kana": "kana",
                  "conj": "conjugation-form", "phrase": "phrase"}
ITEM_UNLOCKS = ("vocab", "kanji", "grammar", "kana-family", "conjugation-form", "phrase")
ROMAJI_RX = re.compile(r"'([a-z]{1,4})'")
EXEMPT_REASON = ("The lesson unlocks no corpus item: the question is about course method, pronunciation "
                 "or orientation, so there is no vocab, kanji, grammar or kana record to target "
                 "(design/assessment.md §2.4, class 'method, phonology and course metalanguage').")


def ref_type(ref: str) -> str | None:
    return TYPE_OF_PREFIX.get(ref.split(":", 1)[0])


def answer_strings(ex: dict) -> list[str]:
    """Rule 2's strings, per exercise type (design/assessment.md §2.2 table)."""
    a = ex.get("answer") if isinstance(ex.get("answer"), dict) else {}
    t = ex.get("type")
    out: list[str] = []
    if t == "cloze":
        out = [a.get("text") or a.get("full") or ""]
    elif t in ("production", "handwriting", "sentence_build", "ordering"):
        out = [a.get("text") or ""]
    elif t in ("recognition", "reading", "listening", "particle_choice"):
        out = [a.get("correct") or ""]
    elif t == "matching":
        out = [x for pair in (a.get("pairs") or []) if isinstance(pair, list) for x in pair]
    return [s for s in out if isinstance(s, str) and s]


class Context:
    """Everything the rule reads, loaded once per tree."""

    def __init__(self, root: Path):
        self.root = root
        surfaces, max_len = vpc.load_vocab(root)
        self.tile = vpc.make_tiler(surfaces, max_len)
        self.kanji_char = vpc.load_kanji(root)                     # slug -> char
        self.char_kanji = {c: s for s, c in self.kanji_char.items()}
        self.gram_probes, _labels = vpc.load_grammar(root)
        self.sentences = vpc.load_sentences(root)
        self.glyphs: dict[str, tuple[str, str]] = {}               # char -> (glyph id, family)
        self.romaji: dict[str, list[tuple[str, str]]] = collections.defaultdict(list)
        for script in ("hiragana", "katakana"):
            p = root / "corpus" / "kana" / f"{script}.json"
            for rec in (json.loads(p.read_text(encoding="utf-8")) if p.exists() else []):
                self.glyphs[rec["char"]] = (rec["id"], rec["family"])
                self.romaji[rec["romaji"]].append((rec["id"], rec["family"]))
        self.glyph_family = {gid: fam for gid, fam in self.glyphs.values()}
        self.max_glyph = max((len(c) for c in self.glyphs), default=1)
        # Rule 0b. 556 exercises already carried AUTHORED item_refs in the authoring source (bare
        # {type, ref}: kanji character, grammar key, vocab headword), loaded into `exercise_item` by
        # load_lessons.py and never exported, which is why the design measured the field as empty.
        # They name what the author asked about (the causative-passive point, not the kanji of the
        # stem), so they win over every matcher. After the apply they sit in the same file resolved,
        # with `derived_by: authored`, and are read back unchanged.
        self.vocab_by_form: dict[str, set[str]] = collections.defaultdict(set)
        for p in sorted(root.glob("corpus/vocab/*.json")):
            for rec in json.loads(p.read_text(encoding="utf-8")):
                for form in (rec["slug"], rec["slug"].split(":", 1)[1], rec.get("headword")):
                    if form:
                        self.vocab_by_form[form].add(rec["slug"])
        self.authored: dict[str, list[dict]] = {}
        for p in sorted((root / "research" / "derived" / "lessons").glob("*.json")):
            for ex in json.loads(p.read_text(encoding="utf-8")).get("exercises") or []:
                refs = [e for e in ex.get("item_refs") or []
                        if e.get("derived_by") in (None, "authored")]
                if refs:
                    self.authored[ex.get("slug")] = refs
        self.tables: dict[str, tuple[str, list[str]]] = {}         # ex id -> (table, targets)
        for name in TABLES:
            p = root / "research" / "derived" / "repairs" / f"{name}.json"
            if p.exists():
                for r in json.loads(p.read_text(encoding="utf-8"))["rows"]:
                    # 65 kanji rows name the bare character (探), the rest the slug (kanji:探).
                    self.tables[r["exercise"]["id"]] = (
                        name, [t if ":" in t else f"kanji:{t}" for t in r["targets"]])

    # --- matchers over one string set --------------------------------------------------------
    def items_in(self, strings: list[str], cited: set[str]) -> set[str]:
        """vocab / kanji / grammar refs a string set names, by the practice gate's matchers."""
        out: set[str] = set()
        verbatim = {self.sentences[s][3]: s for s in cited}
        runs: list[str] = []
        for s in strings:
            sent = verbatim.get(vpc.fold_sentence(s))
            if sent is not None:
                out |= self.sentences[sent][0]
            else:
                for run in vpc.JP_RUN_RX.findall(s):
                    self.tile(run, out)
            runs += vpc.JP_RUN_RX.findall(s)
        text = "".join(runs)
        whole = set(strings)
        out |= {self.char_kanji[c] for c in text if c in self.char_kanji}
        for slug, segs in self.gram_probes.items():
            if any((len(g) > 1 and g in text) or (len(g) == 1 and g in whole) for g in segs):
                out.add(slug)
        return out

    def kana_in(self, strings: list[str], prompt: str) -> set[str]:
        out: set[str] = set()
        for s in strings + [prompt]:
            i = 0
            while i < len(s):
                for n in range(min(self.max_glyph, len(s) - i), 0, -1):
                    hit = self.glyphs.get(s[i:i + n])
                    if hit:
                        out.add(hit[0])
                        i += n
                        break
                else:
                    i += 1
        for rom in ROMAJI_RX.findall(prompt):
            out |= {gid for gid, _fam in self.romaji.get(rom, [])}
        return out


def _known(ctx: Context, ref: str, cks: dict[str, set[str]]) -> bool:
    t = ref_type(ref)
    if t == "kana":
        return ctx.glyph_family.get(ref, ref) in cks["kana-family"] or ref in cks["kana-family"]
    key = {"vocab": "vocab", "kanji": "kanji", "grammar": "grammar",
           "conjugation-form": "conjugation-form", "phrase": "phrase"}.get(t or "")
    return bool(key) and ref in cks[key]


def _own(ctx: Context, ref: str, unlocks: set[str]) -> bool:
    return ref in unlocks or ctx.glyph_family.get(ref) in unlocks


def resolve_authored(ctx: Context, entry: dict, cks: dict[str, set[str]]) -> str | None:
    """A legacy authored ref ({type, ref} with a bare identifier) -> the one published id it names
    inside the lesson's known set, or None when it names none or several. An entry already written
    with `derived_by: authored` is its own published id."""
    ref = entry.get("ref") or ""
    if entry.get("derived_by") == "authored":
        return ref if ref_type(ref) and _known(ctx, ref, cks) else None
    ident = ref.split(":", 1)[1] if ":" in ref else ref
    t = entry.get("type")
    cands = ({f"kanji:{ident}"} if t == "kanji" else {f"gram:{ident}"} if t == "grammar"
             else ctx.vocab_by_form.get(ident, set()) if t == "vocab" else set())
    inside = {c for c in cands if _known(ctx, c, cks)}
    return inside.pop() if len(inside) == 1 else None


def derive_exercise(ctx: Context, lesson: dict, ex: dict, use_tables: bool = True) -> list[dict]:
    """The exercise's `item_refs`, sorted by (type, ref). Empty when no rule finds a target."""
    if use_tables and ex["id"] in ctx.tables:
        name, targets = ctx.tables[ex["id"]]
        return sorted(({"type": ref_type(r), "ref": r, "role": "target", "derived_by": f"table:{name}"}
                       for r in targets), key=lambda e: (e["type"], e["ref"]))
    cks = {k: set((lesson.get("cumulative_known_set") or {}).get(k) or []) for k in ITEM_UNLOCKS}
    if use_tables and ex["id"] in ctx.authored:
        got = {resolve_authored(ctx, e, cks) for e in ctx.authored[ex["id"]]} - {None}
        if got:
            return sorted(({"type": ref_type(r), "ref": r, "role": "target", "derived_by": "authored"}
                           for r in got), key=lambda e: (e["type"], e["ref"]))
    unlocks = {u["ref"] for u in lesson.get("unlocks") or [] if u.get("type") in ITEM_UNLOCKS}
    prompt = json.dumps(ex.get("prompt"), ensure_ascii=False) if ex.get("prompt") is not None else ""
    prompt_pt = (ex.get("prompt") or {}).get(vpc.LOC) or "" if isinstance(ex.get("prompt"), dict) else ""
    cited = {s for s in (ex.get("sentence_refs") or []) if s in ctx.sentences}
    found: dict[str, str] = {}                                     # ref -> first rule

    def add(refs, rule: str) -> None:
        for r in sorted(refs):
            found.setdefault(r, rule)

    add({r for r in vpc.TARGET_REF_RX.findall(prompt) if ref_type(r)}, "markup")
    strings = answer_strings(ex)
    add({r for r in ctx.items_in(strings, cited) if _known(ctx, r, cks)}, "answer")
    add({r for r in ctx.items_in([prompt_pt], set()) if r in unlocks}, "prompt-unlocks")
    if not found and cited:
        sent = set()
        for s in cited:
            v, g, surf, _f = ctx.sentences[s]
            sent |= v | g | {ctx.char_kanji[c] for c in surf if c in ctx.char_kanji}
        sent = {r for r in sent if _known(ctx, r, cks)}
        own = {r for r in sent if r in unlocks}
        add(own or sent, "cited-sentence")
    if not found and cks["kana-family"] & unlocks:
        add({g for g in ctx.kana_in(strings, prompt_pt) if ctx.glyph_family.get(g) in unlocks}, "kana")
    own = {r for r in found if _own(ctx, r, unlocks)}
    keep = own or set(found)
    return sorted(({"type": ref_type(r), "ref": r, "role": "target", "derived_by": found[r]}
                   for r in keep if ref_type(r)), key=lambda e: (e["type"], e["ref"]))


def load_lessons(root: Path) -> list[dict]:
    return [json.loads(p.read_text(encoding="utf-8"))
            for p in sorted(root.glob("course/*/topic-*/lesson-*.json"))]


def derive_all(root: Path, use_tables: bool = True) -> tuple[Context, dict[str, dict]]:
    """ex id -> {lesson, level, type, item_refs, teaches}. `teaches` = the lesson unlocks an item."""
    ctx = Context(root)
    out: dict[str, dict] = {}
    for les in load_lessons(root):
        # A review lesson unlocks nothing ON PURPOSE: its questions target earlier lessons' items, so
        # an empty result there is authoring residue, never a metalanguage exemption.
        teaches = (any(u.get("type") in ITEM_UNLOCKS for u in les.get("unlocks") or [])
                   or "revisao" in (les.get("topic") or ""))
        for ex in les.get("exercises") or []:
            out[ex["id"]] = {"lesson": les["id"], "level": les.get("level"), "type": ex.get("type"),
                             "teaches": teaches,
                             "item_refs": derive_exercise(ctx, les, ex, use_tables)}
    return ctx, out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=str(REPO))
    ap.add_argument("--check", action="store_true", help="measure only; write nothing")
    args = ap.parse_args()
    root = Path(args.root).resolve()
    ctx, derived = derive_all(root)

    rows, exempt, residue = [], [], []
    by_rule: collections.Counter = collections.Counter()
    for ex_id, d in sorted(derived.items()):
        if d["item_refs"]:
            rows.append({"exercise": ex_id, "lesson": d["lesson"], "item_refs": d["item_refs"]})
            by_rule[" + ".join(sorted({e["derived_by"] for e in d["item_refs"]}))] += 1
        elif not d["teaches"]:
            exempt.append({"id": ex_id, "lesson": d["lesson"], "reason": EXEMPT_REASON})
        else:
            residue.append({"id": ex_id, "lesson": d["lesson"], "level": d["level"], "type": d["type"]})

    # Honesty check (§2.4): rules 1-6 against the rows whose true target a table carries.
    _c, blind = derive_all(root, use_tables=False)
    rec_hit = rec_all = auth_hit = auth_all = 0
    for ex_id, (_name, targets) in ctx.tables.items():
        if ex_id in blind:
            got = {e["ref"] for e in blind[ex_id]["item_refs"]}
            rec_all += len(targets)
            rec_hit += len(set(targets) & got)
    for ex_id, d in derived.items():
        mine = {e["ref"] for e in d["item_refs"] if e["derived_by"] == "authored"}
        if mine:
            auth_all += len(mine)
            auth_hit += len(mine & {e["ref"] for e in blind[ex_id]["item_refs"]})
    # Authored refs that name no single published item inside the lesson's known set. The apply
    # replaces the authoring entry with the resolved set, so these are listed here, not lost.
    lessons = {les["id"]: les for les in load_lessons(root)}
    unresolved = []
    for ex_id, entries in sorted(ctx.authored.items()):
        d = derived.get(ex_id)
        if d is None:
            continue
        cks = {k: set((lessons[d["lesson"]].get("cumulative_known_set") or {}).get(k) or [])
               for k in ITEM_UNLOCKS}
        unresolved += [{"id": ex_id, "lesson": d["lesson"], "type": e.get("type"), "ref": e.get("ref")}
                       for e in entries if resolve_authored(ctx, e, cks) is None]
    n_refs = [len(r["item_refs"]) for r in rows]
    counts = {
        "exercises": len(derived), "with_target": len(rows), "exempt": len(exempt),
        "residue": len(residue), "target_refs": sum(n_refs),
        "by_rule": dict(sorted(by_rule.items())),
        "table_recovery": f"{rec_hit}/{rec_all}",
        "authored_recovery": f"{auth_hit}/{auth_all}",
        "residue_by_level_type": dict(sorted(collections.Counter(
            f"{r['level']}|{r['type']}" for r in residue).items())),
        "max_refs": max(n_refs, default=0),
    }
    print(json.dumps(counts, ensure_ascii=False, indent=1))
    if args.check:
        return 0

    table = {
        "why": "W23: every lesson exercise's `item_refs` (what it TESTS), derived by the rule of "
               "design/assessment.md §2.2 from the exported tree. Nothing authored.",
        "generated_by": "scripts/derive_item_refs.py",
        "applied_by": "scripts/apply_item_refs.py",
        "counts": counts,
        "row_count": len(rows),
        "rows": rows,
        "authored_unresolved_why": "Pre-W23 authored refs that resolve to no single published item in "
                                   "the lesson's known set. Not exported; apply_item_refs.py keeps them "
                                   "verbatim in the authoring source so the author's words survive.",
        "authored_unresolved": unresolved,
    }
    (root / "research" / "derived" / "repairs" / "item_refs.json").write_text(
        json.dumps(table, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    (root / "course" / "item_ref_exemptions.json").write_text(json.dumps({
        "why": "Lesson exercises that legitimately target no corpus item, each with its reason. Read by "
               "scripts/validate/validate_item_refs.py checks C and D: an exercise here with a target, or "
               "an entry naming no exercise, FAILS, so the list cannot rot. Written by "
               "scripts/derive_item_refs.py. (Not course/gating_exemptions.json#item_refs, which is "
               "about lesson-body refs.)",
        "exercises": exempt}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    pend = root / "research" / "derived" / "pending"
    pend.mkdir(parents=True, exist_ok=True)
    (pend / "item_refs_residue.json").write_text(json.dumps({
        "why": "W23 authoring residue: exercises in a lesson that teaches items for which no rule of "
               "design/assessment.md §2.2 finds a target (conjugated cloze fillers, grammar answers "
               "shorter than their probe, review and contrast items whose target is an earlier "
               "lesson's). Listed, not authored; held by scripts/validate/item_refs_baseline.json.",
        "count": len(residue), "exercises": residue}, ensure_ascii=False, indent=1) + "\n",
        encoding="utf-8")
    print(f"wrote {len(rows)} rows, {len(exempt)} exemptions, {len(residue)} residue")
    return 0


if __name__ == "__main__":
    sys.exit(main())
