#!/usr/bin/env python3
"""Validate course/speak/ — the speaking-first path. Spec: design/speaking_path.md.

The path's whole premise is that it REFERENCES the corpus and never embeds it, so the thing that can
silently rot is a dangling ID: a unit pointing at a sentence/vocab/grammar slug that no longer
exists after a corpus rebuild. That is what this checks, against the committed JSON export rather
than the SQLite index (the export is the source of truth — see CLAUDE.md).

WHY THE CHECKPOINT, EMBED AND MANIFEST BLOCKS WERE ADDED
--------------------------------------------------------
Three whole layers of the path were structurally invisible to the suite:

  * SPEAK-01/02 — the 359 `checkpoint` entries reference exam-bank items, but validate_contracts.scan()
    treats any ID-shaped string under an `id` key as a record DECLARING its own address, so a
    checkpoint's `so:n3:498` self-registered instead of becoming a graph edge, and no script in
    scripts/validate/ mentioned the word `checkpoint`. A checkpoint could point at an item the bank no
    longer has and every gate stayed green. 93 bank items were deleted in the P7 migration; the units
    were re-picked afterwards, and this is what keeps them re-picked.
  * SPEAK-04 — the units embed 426 verbatim copies of corpus content (production `answer_key` = the
    bank sentence's `jp`, `prompt_pt` = its pt-BR translation). The embed is deliberate, because the
    grader needs a literal string, but nothing compared a copy to its source, and STATE.md records an
    open queue that REWRITES generated Japanese. A desync there means the page shows one sentence and
    the server grades against another. The embeds are now an allowlist: those fields must still equal
    their source, and NO other field may hold Japanese text at all.
  * Only `totals.units` was checked, so ten of the eleven manifest counters and the whole `shortfall`
    list were unfalsifiable — the manifest could claim a stage complete while it was short.

WHAT IS *NOT* CHECKED FOR EQUALITY, AND WHY
-------------------------------------------
`checkpoint[].distractors` is NOT compared to the bank item's own distractors, and must not be: all 288
embedded arrays differ from the bank on purpose. scripts/export/build_speaking_checkpoints.py re-draws
every wrong answer from the learner's KNOWN set ("overrides the bank's, all inside the known set"),
because the bank draws its distractors from the whole level and an unseen distractor is eliminated on
sight as unfamiliar instead of on meaning. Only 3 of the 288 items could keep the bank's distractors
even in principle. The real invariant — the one enforced here — is that the re-draw preserved the
item's option count, kept the options distinct, never leaked the correct answer, and used nothing
outside the learner's known vocabulary. The STEM and the CORRECT answer still come from the audited
bank item and are never copied into the unit at all.

Also enforced:
  * every unit id is unique and matches its stage + order
  * say_now is non-empty, and every phrase is a real bank sentence unless the unit says otherwise
  * a unit either introduces vocabulary or is a set-phrase unit; a unit that does neither is padding
  * cumulative_known_vocab never decreases along the path (the known set only grows)
  * shortfall entries in course.json match what the units actually contain, so the manifest cannot
    claim a stage is complete when it is not
  * no unit teaches one grammar point twice under two identities (two patterns claiming the SAME
    effective form set are one point; nested sets are NOT — see commit 531b47c2)
  * kanji stays RECOGNITION ONLY: a production answer written with kanji must accept a kana-only answer

ADVISORY section (reported, never fatal): the vocabulary load of a checkpoint's stem sentence, and the
agreement between a unit's declared patterns and the grammar tags the corpus itself records for its
phrases. Both are content queues, not code defects; the numbers are printed so they can be watched.

Reads exported JSON only; never db/corpus.sqlite.
Usage: validate_speaking_path.py [--root PATH] [--list]
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]

MAX_REPORT = 15
PHRASES_PER_UNIT = 6          # build_speaking_path.PHRASES_PER_UNIT — drives `shortfall`
UNITS_PER_STAGE = 6           # build_speaking_path.UNITS_PER_STAGE
PER_UNIT = 6                  # build_speaking_checkpoints.PER_UNIT (advisory ceiling)
MAX_PER_TYPE = 2              # build_speaking_checkpoints.MAX_PER_TYPE (advisory ceiling)
KANJI_PER_UNIT = 6            # build_speaking_path.KANJI_PER_UNIT
MAX_UNKNOWN_IN_STEM = 3       # advisory budget; today's worst stem carries 3 unknown words

KANJI = re.compile(r"[一-鿿㐀-䶿]")
CJK = re.compile(r"[぀-ヿ㐀-䶿一-鿿]")

# The only field paths in a speak unit permitted to hold Japanese text. Anything else holding kana or
# kanji is corpus content embedded where a stable ID belongs (design/speaking_path.md §1).
EMBED_ALLOWLIST = {
    "title.pt-BR", "production[].prompt_pt", "production[].answer_key",
    "production[].accepted_variants[]", "checkpoint[].distractors[]",
    "fluency.prompt_pt", "kanji_recognition[]",
}
# checkpoint type -> the exam-bank id prefix it must carry.
TYPE_PREFIX = {"context_fill": "cf", "kanji_reading": "kr", "sentence_order": "so",
               "paraphrase": "pp", "grammar_form": "gf", "usage": "us"}
# Types the path excludes on purpose (build_speaking_checkpoints.EXCLUDED): kanji production, long
# reading, and everything needing audio that does not exist yet.
EXCLUDED_TYPES = {"orthography", "reading_comp", "text_grammar", "listening_task", "listening_point",
                  "listening_gist", "listening_say", "listening_reply"}
# Formats whose wrong answers are re-drawn from the known set, and the vocab field they draw from.
DISTRACTOR_FIELD = {"kanji_reading": "kana", "context_fill": "hw", "paraphrase": "hw"}
# A pattern whose entire justification in a unit is one of these does not generalise (advisory B).
COPULA_ONLY = {"です", "ます", "ません", "ました", "ませんでした", "だった", "でした"}


def load_ids(corpus: Path) -> tuple[set[str], set[str], set[str]]:
    """Collect every sentence / vocab / grammar slug present in the committed corpus export."""
    sent: set[str] = set()
    vocab: set[str] = set()
    gram: set[str] = set()
    for p in corpus.rglob("*.json"):
        try:
            data = json.loads(p.read_text(encoding="utf-8"))
        except Exception:
            continue
        items = data if isinstance(data, list) else [data]
        for it in items:
            if not isinstance(it, dict):
                continue
            sid = it.get("slug") or it.get("id")
            if not isinstance(sid, str):
                continue
            (sent if sid.startswith("sent:") else
             vocab if sid.startswith("vocab:") else
             gram if sid.startswith("gram:") else set()).add(sid)
    return sent, vocab, gram


def load_records(corpus: Path) -> tuple[dict, dict, dict, dict]:
    """The records themselves: sentences by slug, vocab by slug and by integer id, grammar by slug."""
    sentences: dict[str, dict] = {}
    for p in sorted((corpus / "sentences").rglob("*.json")):
        for s in json.loads(p.read_text(encoding="utf-8")):
            if isinstance(s, dict) and s.get("slug"):
                sentences[s["slug"]] = s
    vocab_by_slug: dict[str, dict] = {}
    vocab_by_int: dict[int, dict] = {}
    for p in sorted((corpus / "vocab").glob("*.json")):
        for v in json.loads(p.read_text(encoding="utf-8")):
            vocab_by_slug[v["slug"]] = v
            vocab_by_int[v["id"]] = v
    grammar: dict[str, dict] = {}
    for p in sorted((corpus / "grammar").glob("*.json")):
        for g in json.loads(p.read_text(encoding="utf-8")):
            grammar[g["slug"]] = g
    return sentences, vocab_by_slug, vocab_by_int, grammar


def load_exam_items(corpus: Path) -> dict[str, dict]:
    """Every exam-bank item by id, tagged with the type and level its FILE NAME declares."""
    items: dict[str, dict] = {}
    for p in sorted((corpus / "exam_banks").glob("n[0-9]_*.json")):
        parts = p.stem.split("_", 1)
        if len(parts) != 2:
            continue
        level, typ = parts
        data = json.loads(p.read_text(encoding="utf-8"))
        if not isinstance(data, list):
            continue
        for it in data:
            it["_type"], it["_level"] = typ, level
            items[it["id"]] = it
    return items


def grammar_forms(record: dict) -> set[str]:
    """Form strings of a grammar record. The export writes {form, meaning} objects, not bare strings —
    reading them as strings silently yields an empty set and every form check passes vacuously."""
    out: set[str] = set()
    for f in record.get("forms") or []:
        if isinstance(f, dict) and f.get("form"):
            out.add(f["form"])
        elif isinstance(f, str) and f:
            out.add(f)
    return out


def sentence_vocab(sent: dict, vocab_by_int: dict, kana_count: Counter) -> set[str]:
    """The vocab a sentence uses, under build_speaking_path.link_ok — the same acceptance rule the
    builder applied, re-run over the EXPORT so a regressed index cannot change the answer."""
    out: set[str] = set()
    for tk in sent.get("tokens") or []:
        vid = tk.get("vocab_id")
        if tk.get("split_mode") != "C" or vid is None:
            continue
        v = vocab_by_int.get(vid)
        if not v:
            continue
        surface, lemma = tk.get("surface") or "", tk.get("lemma") or ""
        if (v["headword"] in (lemma, surface)
                or any(ch in surface for ch in v["headword"] if KANJI.match(ch))
                or (v["kana"] == lemma and kana_count[v["kana"]] == 1)):
            out.add(v["slug"])
    return out


def embed_paths(node: object, path: str, found: dict[str, int]) -> None:
    """Every field path in a unit that holds Japanese text, with how many strings it holds."""
    if isinstance(node, str):
        if CJK.search(node):
            found[path] = found.get(path, 0) + 1
    elif isinstance(node, list):
        for x in node:
            embed_paths(x, path + "[]", found)
    elif isinstance(node, dict):
        for k, v in node.items():
            embed_paths(v, f"{path}.{k}" if path else k, found)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[2],
                    help="repo root to validate (default: this checkout)")
    ap.add_argument("--list", action="store_true", help="print every failure, not the first 15")
    args = ap.parse_args()
    root = args.root.resolve()
    speak = root / "course" / "speak"
    corpus = root / "corpus"
    if not speak.exists():
        print("validate_speaking_path: course/speak not built — run build_speaking_path.py")
        return 0

    sent, vocab, gram = load_ids(corpus)
    sentences, vocab_by_slug, vocab_by_int, grammar = load_records(corpus)
    exam = load_exam_items(corpus)
    kana_count: Counter = Counter(v["kana"] for v in vocab_by_slug.values())
    key_to_slug = {g["key"]: g["slug"] for g in grammar.values() if g.get("key")}

    course = json.loads((speak / "course.json").read_text(encoding="utf-8"))
    fails: list[str] = []
    warns: list[str] = []
    adv: list[str] = []
    seen_ids: set[str] = set()
    last_known = 0
    phrases_before: set = set()      # say_now slugs from all EARLIER units (R44, R79a)
    unit_count = 0

    # accumulators for the manifest recomputation. Every key is seeded so that a total which happens to
    # be zero still counts as recomputed rather than as a counter nothing checks.
    actual: Counter = Counter({k: 0 for k in (
        "stages", "units", "phrases", "real_phrases", "vocab_introduced", "production", "fluency",
        "drills", "patterns_kept", "patterns_chunked", "checkpoint_items")})
    words_seen: dict[str, str] = {}
    real_from_bank = 0
    shortfall: list[dict] = []
    # accumulators for the checkpoint walk
    known_vocab: set[str] = set()      # slugs, cumulative INCLUDING the current unit
    known_surfaces: set[str] = set()   # headwords + kana of the above
    checkpoint_owner: dict[str, str] = {}
    stem_load: Counter = Counter()
    generated_stems = 0
    stems_checked = 0
    embeds: Counter = Counter()
    tag_misses = 0
    copula_only = 0

    for stage in course["stages"]:
        slug = stage["slug"].split(":", 1)[1]
        stage_units = 0
        for uid in stage["unit_ids"]:
            n = int(uid.rsplit("-", 1)[1])
            p = speak / slug / f"unit-{n:02d}.json"
            if not p.exists():
                fails.append(f"{uid}: file missing ({p.relative_to(root)})")
                continue
            u = json.loads(p.read_text(encoding="utf-8"))
            unit_count += 1
            stage_units += 1
            if u["id"] in seen_ids:
                fails.append(f"{u['id']}: duplicate unit id")
            seen_ids.add(u["id"])
            if u["id"] != uid or u["stage"] != stage["slug"] or u["order"] != n:
                fails.append(f"{u['id']}: id/stage/order disagree with course.json")

            for ref in u["say_now"]:
                if sent and ref not in sent:
                    fails.append(f"{u['id']}: dangling sentence ref {ref}")
            for ref in u["words"]:
                if vocab and ref not in vocab:
                    fails.append(f"{u['id']}: dangling vocab ref {ref}")
            for ref in u["patterns"]:
                if gram and ref not in gram:
                    fails.append(f"{u['id']}: dangling grammar ref {ref}")

            if not u["say_now"]:
                fails.append(f"{u['id']}: no phrases")
            if not u["words"] and not u["chunk_phrases"]:
                fails.append(f"{u['id']}: introduces nothing and teaches no set phrase (padding)")
            if u["cumulative_known_vocab"] < last_known:
                fails.append(f"{u['id']}: known set shrank "
                             f"({last_known} -> {u['cumulative_known_vocab']})")
            last_known = u["cumulative_known_vocab"]
            if u.get("untranslated"):
                warns.append(f"{u['id']}: {len(u['untranslated'])} phrase(s) without a pt-BR translation")
            if not u.get("needs_review"):
                fails.append(f"{u['id']}: sequencing is Layer C and must carry needs_review")

            # ---- production and fluency (learning_science.md R44, R45, R79, R80, R81) ----------
            for pr in u.get("production", []):
                # R45: an ungraded production item cannot be counted, so refuse to ship one.
                if not pr.get("answer_key") or not pr.get("accepted_variants"):
                    fails.append(f"{u['id']}: production item without answer_key/accepted_variants (R45)")
                if not pr.get("prompt_pt"):
                    fails.append(f"{u['id']}: production item without a pt-BR prompt (R45)")
                # R44: production may never be an item's FIRST retrieval, so its sentence must have
                # been modelled in an EARLIER unit.
                if pr.get("sentence") and pr["sentence"] not in phrases_before:
                    fails.append(f"{u['id']}: production item {pr['sentence']} was not modelled in an "
                                 f"earlier unit (R44)")

            fl = u.get("fluency")
            if fl:
                if not fl.get("prompt_pt"):
                    fails.append(f"{u['id']}: fluency block without a situational prompt (R79b)")
                if not fl.get("seconds_target"):
                    fails.append(f"{u['id']}: fluency block without a speed target (R79c)")
                for ref in fl.get("items", []):
                    if ref not in phrases_before:
                        fails.append(f"{u['id']}: fluency item {ref} is not already-known material (R79a)")
                if len(fl.get("items", [])) < 6:
                    warns.append(f"{u['id']}: fluency block has {len(fl.get('items', []))} items, want 6 (R79d)")
            elif phrases_before:
                # Only the very first unit may lack one: before it, nothing is known to be fluent in.
                fails.append(f"{u['id']}: no fluency block despite {len(phrases_before)} known phrases (R79)")

            for dr in u.get("drills", []):
                if len(dr.get("examples", [])) < 3:
                    fails.append(f"{u['id']}: drill for {dr.get('pattern')} has "
                                 f"{len(dr.get('examples', []))} examples, R80/R81 require 3")
                if dr.get("pattern") not in u["patterns"]:
                    fails.append(f"{u['id']}: drill for a pattern not listed in patterns (R80)")
            # R80: every surviving pattern must have a drill; the rest belong in patterns_chunked.
            drilled = {d.get("pattern") for d in u.get("drills", [])}
            for ps in u["patterns"]:
                if ps not in drilled:
                    fails.append(f"{u['id']}: pattern {ps} has no drill and was not demoted (R80)")
            for ref in u.get("patterns_chunked", []):
                if gram and ref not in gram:
                    fails.append(f"{u['id']}: dangling grammar ref {ref} in patterns_chunked")

            if u.get("strands") and abs(sum(u["strands"].values()) - 100) > 2:
                fails.append(f"{u['id']}: strand histogram sums to {sum(u['strands'].values())} (R77)")

            # ---- every remaining reference resolves in the export -------------------------------
            if sentences:
                for ref in u.get("shadowing", []) + u.get("chunk_phrases", []):
                    if ref not in sentences:
                        fails.append(f"{u['id']}: dangling sentence ref {ref}")
                for dr in u.get("drills", []):
                    for ref in dr.get("examples", []):
                        if ref not in sentences:
                            fails.append(f"{u['id']}: dangling drill example {ref}")
                for pr in u.get("production", []):
                    if pr.get("sentence") and pr["sentence"] not in sentences:
                        fails.append(f"{u['id']}: dangling production sentence {pr['sentence']}")
                for ref in (u.get("fluency") or {}).get("items", []):
                    if ref not in sentences:
                        fails.append(f"{u['id']}: dangling fluency item {ref}")
            if set(u.get("chunk_phrases", [])) - set(u["say_now"]):
                fails.append(f"{u['id']}: chunk_phrases holds phrases that are not in say_now")
            if u.get("shadowing") != u["say_now"]:
                fails.append(f"{u['id']}: shadowing is not the say_now list (it is the same material)")
            if u.get("layer") != "C":
                fails.append(f"{u['id']}: layer is {u.get('layer')!r}, sequencing is Layer C")
            if not (u.get("title") or {}).get("pt-BR"):
                fails.append(f"{u['id']}: no pt-BR title")

            # ---- embedded corpus text: allowlist, then equality with the source -----------------
            found: dict[str, int] = {}
            embed_paths(u, "", found)
            for path, count in sorted(found.items()):
                if path not in EMBED_ALLOWLIST:
                    fails.append(f"{u['id']}: {path} holds {count} Japanese string(s) — corpus content "
                                 f"embedded where an ID belongs")
                else:
                    embeds[path] += count
            for pr in u.get("production", []):
                src = sentences.get(pr.get("sentence") or "")
                if not src:
                    continue
                if pr.get("answer_key") != src["jp"]:
                    fails.append(f"{u['id']}: production answer_key drifted from {pr['sentence']} "
                                 f"({pr.get('answer_key')!r} vs {src['jp']!r})")
                if pr.get("prompt_pt") != (src.get("translation") or {}).get("pt-BR"):
                    fails.append(f"{u['id']}: production prompt_pt drifted from {pr['sentence']}'s "
                                 f"pt-BR translation")
                variants = pr.get("accepted_variants") or []
                if len(set(variants)) != len(variants):
                    fails.append(f"{u['id']}: production accepted_variants repeats an answer")
                if pr.get("answer_key") and pr["answer_key"] not in variants:
                    fails.append(f"{u['id']}: production answer_key is not among its accepted_variants")
                # Kanji is RECOGNITION ONLY on this path: a kana answer must be graded correct.
                if pr.get("answer_key") and KANJI.search(pr["answer_key"]):
                    if not any(not KANJI.search(v) for v in variants):
                        fails.append(f"{u['id']}: production {pr['answer_key']!r} accepts no kana-only "
                                     f"answer, so the path demands written kanji")
            phrase_text = "".join(sentences[s]["jp"] for s in u["say_now"] if s in sentences)
            kr = u.get("kanji_recognition", [])
            if len(kr) != len(set(kr)):
                fails.append(f"{u['id']}: kanji_recognition repeats a character")
            if len(kr) > KANJI_PER_UNIT:
                fails.append(f"{u['id']}: kanji_recognition lists {len(kr)}, the cap is {KANJI_PER_UNIT}")
            for ch in kr:
                if phrase_text and ch not in phrase_text:
                    fails.append(f"{u['id']}: kanji_recognition {ch} is in none of the unit's phrases")

            # ---- one grammar point, one identity -------------------------------------------------
            pats = list(dict.fromkeys(u["patterns"]))
            for i in range(len(pats)):
                for j in range(i + 1, len(pats)):
                    a, b = pats[i], pats[j]
                    if a not in grammar or b not in grammar:
                        continue
                    fa, fb = grammar_forms(grammar[a]), grammar_forms(grammar[b])
                    # EQUALITY only. A strict-subset rule is the exact logic commit 531b47c2
                    # reverted in the builder: composite patterns list their components as separate
                    # forms (wa-yori-desu carries yori AND desu), so subset marks two DIFFERENT
                    # points as one. Two records are the same point only when they claim the same
                    # effective forms.
                    if fa and fa == fb:
                        fails.append(f"{u['id']}: {a} {sorted(fa)} and {b} {sorted(fb)} are the same "
                                     f"point taught twice under two identities")

            # ---- the checkpoint: the unit's own words count as known before it runs --------------
            new_words = set(u["words"])
            known_vocab |= new_words
            for w in new_words:
                v = vocab_by_slug.get(w)
                if v:
                    known_surfaces.update(x for x in (v.get("headword"), v.get("kana")) if x)
            per_type: Counter = Counter()
            for cp in u.get("checkpoint", []):
                cid = cp.get("id")
                if cid in checkpoint_owner:
                    fails.append(f"{u['id']}: checkpoint {cid} is already used by "
                                 f"{checkpoint_owner[cid]}")
                checkpoint_owner[cid] = u["id"]
                item = exam.get(cid)
                if item is None:
                    fails.append(f"{u['id']}: checkpoint {cid} resolves to no exam-bank item")
                    continue
                ctype = cp.get("type")
                per_type[ctype] += 1
                if item["_type"] != ctype:
                    fails.append(f"{u['id']}: checkpoint {cid} is declared {ctype} but the bank has it "
                                 f"as {item['_type']}")
                elif TYPE_PREFIX.get(ctype) != cid.split(":", 1)[0]:
                    fails.append(f"{u['id']}: checkpoint {cid} is declared {ctype}, whose id prefix is "
                                 f"{TYPE_PREFIX.get(ctype)}")
                if ctype in EXCLUDED_TYPES:
                    fails.append(f"{u['id']}: checkpoint {cid} is a {ctype} item, a format this path "
                                 f"excludes")
                if item.get("level") != item["_level"] or cid.split(":")[1] != item["_level"]:
                    fails.append(f"{u['id']}: checkpoint {cid} disagrees with its bank about level "
                                 f"({item.get('level')} / {item['_level']})")
                via = cp.get("via")
                if via == "phrase":
                    ok = item.get("sentence") in set(u["say_now"])
                elif via == "new-word":
                    v = vocab_by_int.get(item.get("vocab_id"))
                    ok = bool(v) and v["slug"] in new_words
                elif via == "review":
                    v = vocab_by_int.get(item.get("vocab_id"))
                    ok = bool(v) and v["slug"] in (known_vocab - new_words)
                else:
                    ok = False
                if not ok:
                    fails.append(f"{u['id']}: checkpoint {cid} claims via={via}, which is not true of "
                                 f"the item")
                options = cp.get("distractors")
                if ctype == "sentence_order":
                    if options is not None:
                        fails.append(f"{u['id']}: checkpoint {cid} is assembled from its own pieces and "
                                     f"must carry no distractors")
                elif ctype in DISTRACTOR_FIELD:
                    if not options:
                        fails.append(f"{u['id']}: checkpoint {cid} carries no re-drawn distractors")
                    else:
                        bank_count = len(item.get("distractors") or [])
                        if len(options) != bank_count:
                            fails.append(f"{u['id']}: checkpoint {cid} shows {len(options)} options, "
                                         f"the bank item has {bank_count}")
                        if len(set(options)) != len(options):
                            fails.append(f"{u['id']}: checkpoint {cid} repeats a distractor")
                        for o in options:
                            if o in (item.get("correct"), item.get("answer")):
                                fails.append(f"{u['id']}: checkpoint {cid} lists the correct answer "
                                             f"as a distractor")
                            if o not in known_surfaces:
                                fails.append(f"{u['id']}: checkpoint {cid} distractor {o!r} is not a "
                                             f"word the learner has met")
                    if (item.get("correct") or "") not in known_surfaces:
                        fails.append(f"{u['id']}: checkpoint {cid} answers with {item.get('correct')!r}, "
                                     f"which the learner has not been taught")
                else:
                    visible = [item.get("correct") or "", *(item.get("distractors")
                                                            or item.get("wrong") or [])]
                    for o in visible:
                        if o and o not in known_surfaces:
                            fails.append(f"{u['id']}: checkpoint {cid} shows {o!r}, which the learner "
                                         f"has not met, and its format cannot be re-drawn")
                # ADVISORY: how much unknown vocabulary the item's stem sentence carries.
                stem = sentences.get(item.get("sentence") or "")
                if stem:
                    stems_checked += 1
                    if (stem.get("provenance") or {}).get("ai_generated"):
                        generated_stems += 1
                    unknown = len(sentence_vocab(stem, vocab_by_int, kana_count) - known_vocab)
                    stem_load[unknown] += 1
                    if unknown > MAX_UNKNOWN_IN_STEM:
                        fails.append(f"{u['id']}: checkpoint {cid} stem carries {unknown} unknown "
                                     f"words, over the budget of {MAX_UNKNOWN_IN_STEM}")
            if len(u.get("checkpoint", [])) > PER_UNIT:
                warns.append(f"{u['id']}: {len(u['checkpoint'])} checkpoint items, the target is {PER_UNIT}")
            for t, c in per_type.items():
                if c > MAX_PER_TYPE:
                    warns.append(f"{u['id']}: {c} {t} items, the per-format cap is {MAX_PER_TYPE}")

            # ---- ADVISORY: patterns vs the grammar tags the corpus records for the phrases --------
            named = set(u["patterns"]) | set(u.get("patterns_chunked", []))
            named_keys = {grammar[s]["key"] for s in named if s in grammar}
            for s in u["say_now"]:
                for tag in (sentences.get(s) or {}).get("grammar") or []:
                    if tag not in named_keys and key_to_slug.get(tag) not in named:
                        tag_misses += 1
            chunk = set(u.get("chunk_phrases", []))
            open_text = "".join(sentences[s]["jp"] for s in u["say_now"]
                                if s in sentences and s not in chunk)
            for ps in named:
                if ps not in grammar:
                    continue
                long_forms = {f for f in grammar_forms(grammar[ps]) if len(f) >= 2}
                if not long_forms:
                    continue
                matched = {f for f in long_forms if f in open_text}
                if not matched:
                    fails.append(f"{u['id']}: pattern {ps} has none of its forms {sorted(long_forms)} "
                                 f"in the unit's own phrases")
                elif ps in u["patterns"] and matched <= COPULA_ONLY:
                    copula_only += 1

            # ---- manifest accumulators -----------------------------------------------------------
            actual["phrases"] += len(u["say_now"])
            actual["real_phrases"] += u.get("real_phrases", 0)
            actual["production"] += len(u.get("production", []))
            actual["fluency"] += len((u.get("fluency") or {}).get("items", []))
            actual["drills"] += len(u.get("drills", []))
            actual["patterns_kept"] += len(u["patterns"])
            actual["patterns_chunked"] += len(u.get("patterns_chunked", []))
            actual["checkpoint_items"] += len(u.get("checkpoint", []))
            for w in u["words"]:
                if w in words_seen:
                    fails.append(f"{u['id']}: vocab {w} is already introduced by {words_seen[w]}")
                words_seen[w] = u["id"]
            for s in u["say_now"]:
                rec = sentences.get(s)
                if rec and not (rec.get("provenance") or {}).get("ai_generated"):
                    real_from_bank += 1
            if len(u["say_now"]) < PHRASES_PER_UNIT:
                shortfall.append({"stage": stage["slug"], "unit": u["id"],
                                  "got": len(u["say_now"]), "want": PHRASES_PER_UNIT})

            phrases_before.update(u["say_now"])

        if stage_units < UNITS_PER_STAGE:
            shortfall.append({"stage": stage["slug"], "units": stage_units, "want": UNITS_PER_STAGE})
        if stage.get("unit_count") != len(stage["unit_ids"]):
            fails.append(f"{stage['slug']}: unit_count {stage.get('unit_count')} but "
                         f"{len(stage['unit_ids'])} unit_ids")

    # ---- the manifest is a true statement about the units on disk ----------------------------
    actual["stages"] = len(course["stages"])
    actual["units"] = unit_count
    actual["vocab_introduced"] = len(words_seen)
    declared = course["totals"]
    for k in sorted(set(declared) | set(actual)):
        if k not in declared:
            fails.append(f"course.json totals has no {k} (actual {actual[k]})")
        elif k not in actual:
            fails.append(f"course.json totals claims {k}={declared[k]}, which nothing recomputes")
        elif declared[k] != actual[k]:
            fails.append(f"course.json claims {k}={declared[k]}, found {actual[k]}")
    if actual["real_phrases"] != real_from_bank:
        fails.append(f"units claim {actual['real_phrases']} real phrases, the bank says "
                     f"{real_from_bank} of them are not ai_generated")
    if [dict(x) for x in course.get("shortfall", [])] != shortfall:
        fails.append(f"course.json shortfall has {len(course.get('shortfall', []))} entries, "
                     f"recomputation gives {len(shortfall)}")
    orders = [s.get("order") for s in course["stages"]]
    if orders != list(range(1, len(orders) + 1)):
        fails.append(f"stage order is {orders}, not 1..{len(orders)}")
    stage_dirs = {p.name for p in speak.iterdir() if p.is_dir()}
    declared_dirs = {s["slug"].split(":", 1)[1] for s in course["stages"]}
    for extra in sorted(stage_dirs - declared_dirs):
        fails.append(f"course/speak/{extra}/ is a stage directory no stage declares")
    for missing in sorted(declared_dirs - stage_dirs):
        fails.append(f"stage {missing} has no directory under course/speak/")

    # Orphans: unit files on disk that no stage references. These ship to the app (the prototype
    # loaded 72 units for a 66-unit path) while being invisible to every manifest-driven check.
    on_disk = {p for p in speak.rglob("unit-*.json")}
    referenced = {speak / s["slug"].split(":", 1)[1] / f"unit-{int(u.rsplit('-', 1)[1]):02d}.json"
                  for s in course["stages"] for u in s["unit_ids"]}
    for p in sorted(on_disk - referenced):
        fails.append(f"orphan unit file not referenced by course.json: {p.relative_to(root)}")

    adv.append(f"checkpoint stems: {stems_checked} resolve to a bank sentence, unknown-word histogram "
               f"{dict(sorted(stem_load.items()))}, {generated_stems} sit on AI-generated Japanese")
    adv.append(f"grammar tags: {tag_misses} (phrase, tag) pairs the unit teaching the phrase never "
               f"names; {copula_only} drilled patterns justified only by a copula or polite ending")
    adv.append("embedded corpus text: " + ", ".join(f"{k}={v}" for k, v in sorted(embeds.items())))

    for line in adv:
        print(f"  [adv]  {line}")
    for line in warns[:10]:
        print(f"  [warn] {line}")
    if len(warns) > 10:
        print(f"  [warn] … and {len(warns) - 10} more")
    for line in (fails if args.list else fails[:MAX_REPORT]):
        print(f"  [FAIL] {line}")
    if not args.list and len(fails) > MAX_REPORT:
        print(f"  [FAIL] … and {len(fails) - MAX_REPORT} more (re-run with --list)")
    print(f"validate_speaking_path: {unit_count} units, {course['totals']['phrases']} phrases, "
          f"{actual['checkpoint_items']} checkpoint items, {len(fails)} FAIL, {len(warns)} warn")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
