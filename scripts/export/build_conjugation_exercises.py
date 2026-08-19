#!/usr/bin/env python3
"""Build the conjugation exercise bank -> corpus/exercises/conjugation/. Roadmap item C.

Planned since 2026-06 and never built: corpus/exercises/ did not exist. The roadmap's step 1 was to mine
example sentences per (verb, form), but only 1,765 of 19,784 possible pairs are attested in the sentence
bank, so mining alone cannot carry an exercise bank. It does not have to. The DETERMINISTIC conjugation
bank (corpus/conjugations) already holds the answer key for every form of every verb and adjective, so
the items are derivable with ZERO AI and zero generation - Layer B throughout.

An item asks the learner to put a dictionary form into a named form:
    食べる -> forma て        answer 食べて
Distractors are OTHER FORMS OF THE SAME WORD (食べた, 食べない, 食べます), which is what makes the item
test form discrimination rather than vocabulary. A distractor drawn from a different verb would be
eliminable from the stem alone.

Where a real bank sentence actually contains the answer surface, its slug is attached as `example`, so
the app can show the form in use. That is the surviving half of the roadmap's mining step, and the
INDEX records how few items get one rather than implying full coverage.

Guards, each mirroring a defect already fixed elsewhere in this corpus:
  * an item whose answer equals the prompt (dictionary -> dictionary) is not a question; dropped.
  * distractors must be distinct from each other AND from the answer AS STRINGS. Several forms coincide
    for some words (na-adjective attributive vs terminal), and a duplicated option is unanswerable.
  * ties among candidate distractors break on a hash of (item id, candidate), never alphabetically - the
    alphabetical tiebreak in build_exam_banks collapsed 400 items onto 31 distinct distractors.
  * an entry with fewer than 4 distinct surfaces cannot furnish 3 distractors; skipped and counted.

Usage: build_conjugation_exercises.py
"""
from __future__ import annotations
import glob, hashlib, json, sqlite3, sys
from collections import Counter
from pathlib import Path
sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
ROOT = Path(__file__).resolve().parents[2]
DB = ROOT / "db" / "corpus.sqlite"
OUT = ROOT / "corpus" / "exercises" / "conjugation"
DISTRACTORS = 3

# pt-BR labels for the form names the conjugation bank uses. Learner-facing, so pt-BR (CLAUDE.md); the
# KEYS stay neutral English because they are mechanical enum values (design/i18n.md).
LABEL = {
    "dictionary": "forma de dicionário", "masu": "forma ます (polida)",
    "masu_negative": "ます negativa", "masu_past": "ます no passado",
    "masu_past_negative": "ます passado negativo", "te": "forma て",
    "past": "passado (forma simples)", "negative": "negativa (forma simples)",
    "past_negative": "passado negativo (forma simples)", "potential": "potencial (conseguir)",
    "passive": "passiva", "causative": "causativa", "causative_passive": "causativa passiva",
    "imperative": "imperativa", "volitional": "volitiva (vamos)",
    "conditional_ba": "condicional ば", "conditional_tara": "condicional たら",
    "attributive": "atributiva (antes do substantivo)", "adverbial": "adverbial",
    "polite": "polida", "terminal": "terminal", "stem": "radical",
    "progressive": "progressiva (ている)", "desiderative": "desiderativa (たい)",
}


def spread(anchor: str, value: str) -> str:
    return hashlib.sha1(f"{anchor}{value}".encode("utf-8")).hexdigest()


def main() -> int:
    con = sqlite3.connect(DB)
    sentences = [(slug, jp) for slug, jp in con.execute("SELECT slug,jp FROM sentence")]
    sentences.sort(key=lambda t: len(t[1]))          # shortest first: the gentlest example wins

    entries = []
    for f in sorted(glob.glob(str(ROOT / "corpus" / "conjugations" / "*.json"))):
        entries += json.loads(Path(f).read_text(encoding="utf-8"))

    # answer surface -> slug of a real bank sentence containing it
    wanted = {x["surface"] for e in entries for x in e["conjugations"]
              if len(x.get("surface") or "") > 1}
    by_surface: dict[str, str] = {}
    for slug, jp in sentences:
        for s in wanted:
            if s not in by_surface and s in jp:
                by_surface[s] = slug

    banks: dict[str, list] = {}
    stats, skipped = Counter(), Counter()
    for e in entries:
        forms = [x for x in e["conjugations"] if (x.get("surface") or "").strip()]
        pool = {x["surface"] for x in forms}
        dict_surface = next((x["surface"] for x in forms if x["form"] == "dictionary"),
                            e["headword"])
        if len(pool) < DISTRACTORS + 1:
            skipped["fewer than 4 distinct surfaces"] += 1
            continue
        for x in forms:
            form, ans = x["form"], x["surface"]
            if form == "dictionary" or ans == dict_surface:
                skipped["answer equals the prompt"] += 1
                continue
            iid = f"cj:{e['level']}:{e['vocab_id']}:{form}"
            cands = sorted((c for c in pool if c != ans),
                           key=lambda c: (abs(len(c) - len(ans)), spread(iid, c)))
            dis = cands[:DISTRACTORS]
            if len(set(dis)) < DISTRACTORS:
                skipped["cannot furnish 3 distinct distractors"] += 1
                continue
            banks.setdefault(f"{e['level']}_conjugation", []).append({
                "id": iid, "level": e["level"], "vocab_id": e["vocab_id"], "slug": e["slug"],
                "headword": e["headword"], "kind": e["kind"], "class": e.get("class"),
                "prompt": dict_surface, "form": form,
                "form_label": {"pt-BR": LABEL.get(form, form)},
                "correct": ans, "kana": x.get("kana"), "romaji": x.get("romaji"),
                "distractors": dis, "example": by_surface.get(ans),
                "source": "conjugations", "layer": "B", "needs_review": 0,
            })
            stats[e["level"]] += 1
            if by_surface.get(ans):
                stats["with_example"] += 1

    OUT.mkdir(parents=True, exist_ok=True)
    for name, items in sorted(banks.items()):
        items.sort(key=lambda i: (i["vocab_id"], i["form"]))
        (OUT / f"{name}.json").write_text(json.dumps(items, ensure_ascii=False, indent=1) + "\n",
                                          encoding="utf-8")
    total = sum(len(v) for v in banks.values())
    (OUT / "INDEX.md").write_text(
        "# corpus/exercises/conjugation - form-discrimination drills\n\n"
        "Roadmap item C. Built by `scripts/export/build_conjugation_exercises.py` from the "
        "DETERMINISTIC conjugation bank (`corpus/conjugations`), so every answer key is derived rather "
        "than authored: zero AI, Layer B.\n\n"
        "An item gives a dictionary form plus a target form name and asks for the conjugated surface. "
        "**Distractors are other forms of the SAME word**, which is what makes the item test form "
        "discrimination; a distractor from a different verb would be eliminable from the stem alone.\n\n"
        f"**{total} items** across "
        + ", ".join(f"{k.split('_')[0].upper()} {len(v)}" for k, v in sorted(banks.items()))
        + f". **{stats['with_example']}** carry an `example` slug, a real bank sentence that actually "
        "contains the answer surface. The rest do not, and that is the honest state of the roadmap's "
        "mining step: only 1,765 of 19,784 possible (word, form) pairs are attested in the sentence "
        "bank.\n\n"
        "Item: `{id, level, vocab_id, slug, headword, kind, class, prompt, form, form_label, correct, "
        "kana, romaji, distractors, example}`.\n",
        encoding="utf-8")

    print(f"conjugation exercises: {total} items  "
          + " ".join(f"{k}={len(v)}" for k, v in sorted(banks.items())))
    print(f"  with a real example sentence: {stats['with_example']}")
    print(f"  skipped: {dict(skipped)}")
    con.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
