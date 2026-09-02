#!/usr/bin/env python3
"""Add the PRODUCTION side to speaking-path units: drills, production items, a fluency block and strand
tags. Implements design/learning_science.md R44, R45, R77, R79, R80, R81.

Why this exists: before it, `production` was emitted in 0 of 66 units. Every component the path had
(say_now, words, patterns, kanji_recognition, checkpoint) is input or language-focused. A course whose
stated purpose is SPEAKING shipped nothing that made the learner produce anything, which the four-strand
histogram (R77) makes impossible to hide.

Four things are added, each machine-checkable rather than authored:

  drills      (R80/R81) A `pattern` is only a pattern if it generalises. For each one we pull bank
              sentences carrying the same grammar id whose vocabulary is already inside the known set,
              excluding the unit's own phrases. >=3 -> the pattern stays and those sentences become its
              substitution drill. <3 -> it is NOT a pattern in this unit; it moves to
              `patterns_chunked` rather than being silently dropped, because a pattern that occurs in
              exactly one frozen phrase is a chunk, and calling it a pattern makes the field a lie the
              auditor then measures.

  production  (R44/R45) pt-BR prompt -> Japanese answer. R44 forbids a production item from being an
              item's FIRST retrieval, so these are drawn only from PRIOR units: the learner has already
              seen the phrase modelled (say_now) and tested (checkpoint) before being asked to produce
              it. R45 forbids counting ungraded production, so each item carries `answer_key` plus
              `accepted_variants` (punctuation- and spacing-insensitive forms) and is string-gradeable
              without ASR.

  fluency     (R79) Nation's four conditions, all checked: (a) every item is inside the known set with
              ZERO new tokens, (b) the prompt is a situation rather than a form, (c) a speed target is
              attached, (d) >=6 productions. This is the strand the teardowns found essentially every
              self-study competitor omits, and it costs no new content: "material the learner already
              knows" is exactly `cumulative_known_vocab`.

  strands     (R77) Every component tagged meaning-input / meaning-output / language-focused / fluency,
              with a per-unit histogram. Shadowing is tagged meaning-input, NOT output: it reuses the
              say_now ids and decoding someone else's sentence is not producing your own.

Run after build_speaking_path.py and build_speaking_checkpoints.py.
Usage: build_speaking_practice.py [--dry-run]
"""
from __future__ import annotations
import argparse, json, re, sqlite3, sys
from collections import Counter
from pathlib import Path
sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
# W01: honour --db / $YOMINEKO_DB so a rebuild can target a scratch DB (scripts/dbtarget.py).
import sys as _sys, pathlib as _pl  # noqa: E402
_sys.path.append(str(next(p for p in _pl.Path(__file__).resolve().parents if p.name == "scripts")))
from dbtarget import db_target  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
DB = db_target(ROOT / "db" / "corpus.sqlite")
SPEAK = ROOT / "course" / "speak"
# The stage seed lexicons, imported rather than restated: production ranks by how relevant an
# already-known phrase is to the situation the learner is now in, and a second copy of the seeds here
# would drift from the one that actually built the stages.
sys.path.insert(0, str(Path(__file__).resolve().parent))
from build_speaking_path import STAGES  # noqa: E402
STAGE_SEEDS: dict[str, tuple[str, ...]] = {s[0]: s[3] for s in STAGES}

# Registers a phrase can carry that make it wrong to put in a traveller's mouth. Reported, never
# filtered: what to do about them is an owner decision (PENDING.md A8), and a builder that silently
# dropped them would make the size of the problem invisible.
MARKED_REGISTERS = {"archaic", "classical", "epistolary", "literary", "vulgar", "written"}

DRILLS_PER_PATTERN = 3        # R80/R81 minimum for a pattern to count as productive
# A drill sentence may carry ONE word outside the known set, the same i+1 allowance a say_now phrase
# gets. Demanding a fully-known drill sentence sounds stricter but is really a coverage test on a
# ~500-word known set rather than a test of whether the pattern generalises: it kept only 31% of
# patterns, against 70% at one new word and 89% at two. One is the honest setting.
DRILL_MAX_NEW = 1
PRODUCTION_PER_UNIT = 3       # R44: all drawn from prior units
FLUENCY_PER_UNIT = 6          # R79 (d)
SECONDS_PER_ITEM = 8          # R79 (c) speed target; a design choice, labelled as such in the ruleset
# Prompt for a fluency block whose items all predate this stage. It happens at a stage's opening
# unit, where nothing from the new situation is known-material yet; naming it a recap is honest,
# where reusing the stage situation asks for a rehearsal the items cannot support.
RECAP_PROMPT = ("Antes de começar a nova situação, repasse em voz alta o que você já sabe dizer. "
                "Vá o mais rápido que conseguir, sem travar.")

# R79 (b): the prompt must be a SITUATION, not a form. One per stage, pt-BR, addressed to the learner.
SITUATIONS: dict[str, str] = {
    "arrival": "Você acabou de desembarcar. Cumprimente, agradeça e peça licença. Em voz alta, sem ler.",
    "shopping": "Você está numa loja com uma coisa na mão. Pergunte o preço e feche a compra.",
    "eating": "Você sentou num restaurante. Peça o que quer comer e beber, e diga se está bom.",
    "getting_around": "Você se perdeu perto da estação. Pergunte o caminho e confirme se entendeu.",
    "lodging": "Você chegou no hotel. Faça o check-in e resolva um problema no quarto.",
    "about_you": "Alguém puxou assunto com você. Diga quem você é, de onde vem e do que gosta.",
    "time_plans": "Um amigo quer marcar alguma coisa. Combine dia e horário.",
    "health": "Você não está bem. Explique o que está sentindo e peça ajuda.",
    "past_stories": "Alguém perguntou como foi seu fim de semana. Conte, no passado.",
    "politeness": "Você precisa pedir um favor a alguém mais velho. Peça com jeito.",
    "opinions": "Perguntaram sua opinião. Diga o que você acha e por quê.",
    "real_talk": "Você está numa conversa solta. Reaja, comente e conte o que ouviu de outra pessoa.",
}

# R77 strands. A component maps to exactly one.
STRAND = {
    "say_now": "meaning-input",
    "shadowing": "meaning-input",
    "words": "language-focused",
    "patterns": "language-focused",
    "kanji_recognition": "language-focused",
    "checkpoint": "language-focused",
    "drills": "language-focused",
    "production": "meaning-output",
    "fluency": "fluency",
}
PUNCT = "。、！？!?…，,．. 　"


def variants(jp: str, kana: str | None = None, kana_written: str | None = None) -> list[str]:
    """Accepted answers for a production item (R45). Graded by string match, so the learner must not be
    failed for punctuation they cannot type, spacing the bank happens to carry, a fullwidth character
    no IME emits — nor for writing in kana: the path's own contract (design/speaking_path.md section 1)
    is kanji RECOGNITION ONLY, never written.

    TWO kana forms are accepted, and the distinction is the whole point. The bank's `kana` column is
    PHONETIC: it records how the sentence SOUNDS, so the topic particle は appears as わ and the
    direction particle へ as え. A learner writing correct kana types は and へ — the spelling — and an
    audit found 92 of 213 production items accepting only the phonetic string, i.e. rejecting the
    orthographically correct answer and accepting a misspelling. `kana_written` is that orthographic
    form, rebuilt from the dissection by taking each token's SURFACE for particles and its READING
    otherwise. Both are accepted: a learner who transcribes what they hear is not wrong either.

    NFKC folds the fullwidth digits and Latin the bank carries (４点, ＳＰ, ８時) and squared
    characters like ㌔ onto what a normal IME actually produces."""
    import unicodedata
    out = set()
    for base in (jp, kana, kana_written):
        if not base:
            continue
        for form in {base, unicodedata.normalize("NFKC", base)}:
            bare = re.sub(r"[\s　]", "", form)
            out |= {form, bare, bare.rstrip(PUNCT), form.rstrip(PUNCT)}
    return sorted(x for x in out if x)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    con = sqlite3.connect(DB)

    sent = {sid: {"id": sid, "slug": slug, "jp": jp, "kana": kana} for sid, slug, jp, kana in
            con.execute("SELECT id,slug,jp,kana FROM sentence")}
    # Orthographic kana: the reading of every token EXCEPT particles, which keep their surface, so
    # the topic は stays は instead of collapsing to its sound わ. See variants().
    _ortho: dict = {}
    for sid, surface, reading, pos, lemma in con.execute(
            "SELECT sentence_id, surface, reading, pos, lemma FROM token WHERE split_mode='C' "
            "ORDER BY sentence_id, position"):
        piece = surface if pos == "particle" else (reading or surface)
        # 言う is the one common verb whose ANALYZER reading is not its spelling: SudachiPy emits
        # ユウ for the dictionary form (verified: 物を言う -> ユウ, 言わなかった -> イワ), so the bank
        # stores ゆう and validate.py §7.2 rightly holds it there as Layer A. But ゆう is how the word
        # sounds, not how it is written — no IME accepts it — so for the orthographic answer form the
        # ゆ-initial readings of this lemma become い-initial (ゆう -> いう). 14 bank tokens.
        if lemma == "言う" and pos != "particle" and piece.startswith("ゆ"):
            piece = "い" + piece[1:]
        _ortho[sid] = _ortho.get(sid, "") + (piece or "")
    for sid, rec in sent.items():
        rec["kana_written"] = _ortho.get(sid) or None
    by_slug = {s["slug"]: s for s in sent.values()}
    pt = {sid: v for sid, v in con.execute(
        "SELECT entity_id,value FROM localized_text WHERE entity_type='sentence' "
        "AND field='translation' AND locale='pt-BR'")}
    vid_of = {slug: i for slug, i in con.execute("SELECT slug,id FROM vocab")}
    gid_of = {slug: i for slug, i in con.execute("SELECT slug,id FROM grammar_point")}
    # a sentence's vocabulary, same dissection-based source the path builder uses
    svocab: dict[int, set[int]] = {}
    for sid, vid in con.execute("SELECT DISTINCT sentence_id,vocab_id FROM token "
                                "WHERE split_mode='C' AND vocab_id IS NOT NULL"):
        svocab.setdefault(sid, set()).add(vid)
    gram_sents: dict[int, list[int]] = {}
    for sid, gid in con.execute("SELECT sentence_id,grammar_id FROM sentence_grammar"):
        gram_sents.setdefault(gid, []).append(sid)
    # token lemmas per sentence — the same key build_speaking_path.py matches its seeds on.
    slem: dict[int, set[str]] = {}
    for sid, surf, lem in con.execute(
            "SELECT sentence_id,surface,lemma FROM token WHERE split_mode='C'"):
        slem.setdefault(sid, set()).add(lem or surf)
    # Register, wherever the corpus records one. There is no sentence-level register column today, so
    # the only signal available is the register of the grammar points a sentence is tagged with.
    gram_register = {gid: (reg or "") for gid, reg in
                     con.execute("SELECT id,register FROM grammar_point")}
    sent_register: dict[int, set[str]] = {}
    for gid, sids in gram_sents.items():
        r = gram_register.get(gid, "")
        for sid in sids:
            sent_register.setdefault(sid, set()).add(r)

    def stage_relevant(slug: str, stage_key: str) -> bool:
        """Is an already-known phrase about the situation this stage puts the learner in?"""
        s = by_slug.get(slug)
        if not s:
            return False
        lems = slem.get(s["id"], ())
        return any(k in lems or (len(k) >= 4 and k in s["jp"])
                   for k in STAGE_SEEDS.get(stage_key, ()))

    course = json.loads((SPEAK / "course.json").read_text(encoding="utf-8"))
    known: set[int] = set()
    seen_phrases: list[str] = []          # every say_now slug from PRIOR units, in order
    prev_fluency: list[str] = []          # the immediately preceding unit's fluency items
    stats, demoted = Counter(), []
    register_seen: Counter = Counter()    # register of say_now + production material, reported below

    for stage in course["stages"]:
        key = stage["slug"].split(":", 1)[1]
        d = SPEAK / key
        stage_phrases: set = set()      # phrases from EARLIER units of this same stage
        for uid in stage["unit_ids"]:
            n = int(uid.rsplit("-", 1)[1])
            p = d / f"unit-{n:02d}.json"
            u = json.loads(p.read_text(encoding="utf-8"))
            # Idempotency: a previous run rewrote `patterns` to the kept subset and parked the rest in
            # `patterns_chunked`. Re-running on that output would find every survivor passing and report
            # 0 demotions, so restore the full list before re-deciding. Scripts here are re-runnable by
            # contract (CLAUDE.md resumption protocol) and this one consumed its own output.
            u["patterns"] = list(u.get("patterns", [])) + list(u.get("patterns_chunked", []))
            prior = list(seen_phrases)                 # snapshot BEFORE this unit's phrases are added
            known_before = set(known)

            # ---- production (R44, R45) --------------------------------------------------------
            # Only prior-unit phrases: the learner has seen each modelled and tested already.
            #
            # COLD START AT A STAGE OPENING, and why the ORDER moves rather than the rule. A stage's
            # first unit has no prior phrases from its own stage, so production filled from the tail of
            # the PREVIOUS stage: health-01 asked "Quando foi a última vez que você cortou o cabelo?"
            # of a learner who had just been told to explain what hurts (own-stage 0/3 in all eleven
            # non-first stages).
            #
            # The tempting fix is to let the unit's OWN say_now in — and it is wrong for the same reason
            # the same fix was wrong for fluency (commit 92b833c5). R44 forbids production being an
            # item's FIRST retrieval and fixes the order model -> recognition/checkpoint -> production;
            # inside a unit `production` is scheduled BEFORE `checkpoint`, so a same-unit item is
            # exactly the first retrieval R44 names, and validate_speaking_path rejects it. The rule is
            # right and stays.
            #
            # What was actually broken is the RANKING: recency alone, which at a stage boundary means
            # "whatever the last stage happened to end on". Prior phrases are now ordered by how close
            # they are to the situation the learner is in — this stage's phrases, then earlier phrases
            # that carry one of this stage's seeds, then the rest by recency. health-01 now produces
            # 今日はちょっと頭が痛いの instead of a haircut. Every item is still strictly prior-known.
            pool = list(reversed(prior))               # most recent first: still fresh, not yet cold
            same = [s for s in pool if s in stage_phrases]
            topical = [s for s in pool if s not in stage_phrases and stage_relevant(s, key)]
            rest = [s for s in pool if s not in stage_phrases and s not in set(topical)]
            topical_set = set(topical)
            production = []
            for slug in same + topical + rest:
                if len(production) >= PRODUCTION_PER_UNIT:
                    break
                s = by_slug.get(slug)
                if not s or not pt.get(s["id"]):
                    continue
                production.append({
                    "prompt_pt": pt[s["id"]],
                    "answer_key": s["jp"],
                    "accepted_variants": variants(s["jp"], s.get("kana"), s.get("kana_written")),
                    "sentence": slug,
                    # Say which of the three the item is, so the app can label a carried-over item as
                    # review instead of presenting it as part of the new situation.
                    "kind": ("same-stage" if slug in stage_phrases else
                             "on-topic" if slug in topical_set else "review"),
                    "strand": "meaning-output",
                })

            # ---- fluency block (R79) ----------------------------------------------------------
            # Zero new tokens: every item's vocabulary must already be inside the known set as it stood
            # BEFORE this unit, and items already used for production are excluded so the block is not
            # the same six sentences twice.
            taken = {x["sentence"] for x in production}

            def eligible(slug: str) -> bool:
                s = by_slug.get(slug)
                # R79 (a): zero new tokens, measured against the known set as it stood BEFORE this unit
                return bool(s) and slug not in taken and svocab.get(s["id"], set()) <= known_before

            # Same-stage phrases first. The prompt is a SITUATION, so rehearsing it with sentences from
            # another scenario defeats it: an early version filled the "you are lost near the station"
            # block with 久しぶりに食べたらスープの味が変わってた, because it ranked by recency alone.
            same_stage = [s for s in reversed(prior) if s in stage_phrases and eligible(s)]
            other = [s for s in reversed(prior) if s not in stage_phrases and eligible(s)]

            # R79 wants repetition, but not the SAME six sentences in the same order twice running —
            # that is one rehearsal presented as two. Three units (arrival-06, about_you-04,
            # time_plans-05) shipped their predecessor's list verbatim, because the ranking is pure
            # recency and nothing had changed between them. The previous unit's items go to the back of
            # the queue rather than out of it: they are still legal fluency material, and starving a
            # block below six items to avoid a repeat would break R79(d) to fix a smaller problem.
            ranked = same_stage + other
            fresh = [s for s in ranked if s not in prev_fluency]
            repeat = [s for s in ranked if s in prev_fluency]
            fluency_items = (fresh + repeat)[:FLUENCY_PER_UNIT]

            # COLD START, and why the PROMPT moves rather than the items. At a stage's opening unit
            # `prior` holds nothing from this stage, so the block fills from earlier scenarios — and
            # it used to present that under the NEW stage's situation prompt, asking the learner to
            # talk about arriving somewhere and handing them six lines about a hotel room (own-stage
            # overlap was 0/6 in every opening unit).
            #
            # The tempting fix is to let the unit's own phrases in. That is wrong, and the validator
            # is right to reject it: R79(a) wants already-known material, and a sentence the learner
            # met a minute ago in this same unit is still being acquired. Fluency practice on
            # unlearned material is not fluency practice. So the items stay strictly prior-known and
            # the PROMPT stops lying — a recap block says it is a recap.
            is_recap = bool(fluency_items) and not any(i in stage_phrases for i in fluency_items)
            fluency = {
                "prompt_pt": (RECAP_PROMPT if is_recap else SITUATIONS.get(key, "")),
                "items": fluency_items,
                "seconds_target": SECONDS_PER_ITEM * len(fluency_items),
                "zero_new_tokens": True,
                "kind": "recap" if is_recap else "situation",
                "strand": "fluency",
            } if fluency_items else None

            # ---- drills, and the R80 pattern test ---------------------------------------------
            drills, kept, chunked = [], [], []
            unit_used: set[int] = set()      # per UNIT, not global: one sentence may illustrate a
                                             # pattern in unit 4 and a different one in unit 40, and
                                             # excluding globally starved later patterns down to 31%.
            for pslug in u["patterns"]:
                gid = gid_of.get(pslug)
                cands = []
                for sid in gram_sents.get(gid, []):
                    if sid in unit_used or sent[sid]["slug"] in u["say_now"]:
                        continue
                    if len(svocab.get(sid, set()) - known) <= DRILL_MAX_NEW:
                        cands.append(sid)
                # fewest unknown words first, then shortest: the gentlest illustration of the pattern
                cands.sort(key=lambda x: (len(svocab.get(x, set()) - known), len(sent[x]["jp"]), x))
                if len(cands) >= DRILLS_PER_PATTERN:
                    picked = cands[:DRILLS_PER_PATTERN]
                    unit_used.update(picked)
                    kept.append(pslug)
                    drills.append({"pattern": pslug,
                                   "examples": [sent[x]["slug"] for x in picked],
                                   "strand": "language-focused"})
                else:
                    chunked.append(pslug)
                    demoted.append((uid, pslug, len(cands)))

            # ---- write back --------------------------------------------------------------------
            u["patterns"] = kept
            u["patterns_chunked"] = chunked
            u["drills"] = drills
            u["production"] = production
            u["fluency"] = fluency
            counts = {
                "meaning-input": len(u["say_now"]) + len(u.get("shadowing", [])),
                "meaning-output": len(production),
                "language-focused": (len(u["words"]) + len(kept) + len(u.get("kanji_recognition", []))
                                     + len(u.get("checkpoint", [])) + len(drills)),
                "fluency": len(fluency_items),
            }
            total = sum(counts.values()) or 1
            u["strands"] = {k: round(100 * v / total) for k, v in counts.items()}
            u["strand_counts"] = counts

            stats["production"] += len(production)
            stats["fluency"] += len(fluency_items)
            stats["drills"] += len(drills)
            stats["patterns_kept"] += len(kept)
            stats["patterns_chunked"] += len(chunked)
            for slug in set(u["say_now"]) | {x["sentence"] for x in production}:
                s = by_slug.get(slug)
                regs = sent_register.get(s["id"], set()) if s else set()
                marked = regs & MARKED_REGISTERS
                register_seen["items"] += 1
                if marked:
                    for r in marked:
                        register_seen[r] += 1
                elif not regs or regs == {""}:
                    register_seen["unrecorded"] += 1
            if not args.dry_run:
                p.write_text(json.dumps(u, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

            known |= {vid_of[w] for w in u["words"] if w in vid_of}
            seen_phrases.extend(u["say_now"])
            stage_phrases.update(u["say_now"])
            prev_fluency = list(fluency_items)

    course["totals"].update({k: v for k, v in stats.items()})
    if not args.dry_run:
        (SPEAK / "course.json").write_text(json.dumps(course, ensure_ascii=False, indent=2) + "\n",
                                           encoding="utf-8")
    print(f"practice ({'dry-run' if args.dry_run else 'WRITTEN'}): " +
          "  ".join(f"{k}={v}" for k, v in sorted(stats.items())))
    if demoted:
        print(f"  patterns demoted to chunks (fewer than {DRILLS_PER_PATTERN} known-set examples): "
              f"{len(demoted)}")
    # Register census over say_now + production. Reported, never filtered — deciding what to do about a
    # marked-register phrase is an owner call (PENDING.md A8), and this is the number that call needs.
    marked = {k: v for k, v in register_seen.items()
              if k in MARKED_REGISTERS}
    print(f"  register census: {register_seen['items']} say_now/production items, "
          + (", ".join(f"{k}={v}" for k, v in sorted(marked.items())) if marked
             else "0 archaic/epistolary/vulgar")
          + f"; {register_seen['unrecorded']} carry no register signal at all. NOTE: the corpus has no "
            f"sentence-level `register` field — the only signal available is the register of the "
            f"grammar points a sentence is tagged with, whose vocabulary is "
            f"neutral/polite/casual/formal, so archaic, epistolary and vulgar are currently "
            f"UNRECORDABLE rather than absent.")
    con.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
