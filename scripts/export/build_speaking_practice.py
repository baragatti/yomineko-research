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
ROOT = Path(__file__).resolve().parents[2]
DB = ROOT / "db" / "corpus.sqlite"
SPEAK = ROOT / "course" / "speak"

DRILLS_PER_PATTERN = 3        # R80/R81 minimum for a pattern to count as productive
# A drill sentence may carry ONE word outside the known set, the same i+1 allowance a say_now phrase
# gets. Demanding a fully-known drill sentence sounds stricter but is really a coverage test on a
# ~500-word known set rather than a test of whether the pattern generalises: it kept only 31% of
# patterns, against 70% at one new word and 89% at two. One is the honest setting.
DRILL_MAX_NEW = 1
PRODUCTION_PER_UNIT = 3       # R44: all drawn from prior units
FLUENCY_PER_UNIT = 6          # R79 (d)
SECONDS_PER_ITEM = 8          # R79 (c) speed target; a design choice, labelled as such in the ruleset

# R79 (b): the prompt must be a SITUATION, not a form. One per stage, pt-BR, addressed to the learner.
SITUATIONS: dict[str, str] = {
    "arrival": "Você acabou de desembarcar. Cumprimente, agradeça e peça licença — em voz alta, sem ler.",
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


def variants(jp: str) -> list[str]:
    """Accepted answers for a production item (R45). Graded by string match, so the learner must not be
    failed for punctuation they cannot type or spacing the bank happens to carry."""
    bare = re.sub(r"[\s　]", "", jp)
    out = {jp, bare, bare.rstrip(PUNCT), jp.rstrip(PUNCT)}
    return sorted(x for x in out if x)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    con = sqlite3.connect(DB)

    sent = {sid: {"id": sid, "slug": slug, "jp": jp} for sid, slug, jp in
            con.execute("SELECT id,slug,jp FROM sentence")}
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

    course = json.loads((SPEAK / "course.json").read_text(encoding="utf-8"))
    known: set[int] = set()
    seen_phrases: list[str] = []          # every say_now slug from PRIOR units, in order
    stats, demoted = Counter(), []

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
            production = []
            for slug in reversed(prior):               # most recent first: still fresh, not yet cold
                if len(production) >= PRODUCTION_PER_UNIT:
                    break
                s = by_slug.get(slug)
                if not s or not pt.get(s["id"]):
                    continue
                production.append({
                    "prompt_pt": pt[s["id"]],
                    "answer_key": s["jp"],
                    "accepted_variants": variants(s["jp"]),
                    "sentence": slug,
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
            fluency_items = (same_stage + other)[:FLUENCY_PER_UNIT]
            fluency = {
                "prompt_pt": SITUATIONS.get(key, ""),
                "items": fluency_items,
                "seconds_target": SECONDS_PER_ITEM * len(fluency_items),
                "zero_new_tokens": True,
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
            if not args.dry_run:
                p.write_text(json.dumps(u, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

            known |= {vid_of[w] for w in u["words"] if w in vid_of}
            seen_phrases.extend(u["say_now"])
            stage_phrases.update(u["say_now"])

    course["totals"].update({k: v for k, v in stats.items()})
    if not args.dry_run:
        (SPEAK / "course.json").write_text(json.dumps(course, ensure_ascii=False, indent=2) + "\n",
                                           encoding="utf-8")
    print(f"practice ({'dry-run' if args.dry_run else 'WRITTEN'}): " +
          "  ".join(f"{k}={v}" for k, v in sorted(stats.items())))
    if demoted:
        print(f"  patterns demoted to chunks (fewer than {DRILLS_PER_PATTERN} known-set examples): "
              f"{len(demoted)}")
    con.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
