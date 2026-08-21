#!/usr/bin/env python3
"""Derive a machine-readable sentence PATTERN from the dissection. Roadmap item F.

Have: per-token pos / inflection / role / gloss, particle function_type, grammar links, and a prose
structure_explanation. Gap: nothing a program can build a sentence-construction drill from. The prose
explains the shape to a human; `pattern[]` states it to code.

    私はピアノを習いたい
    -> [{chunk: 私,   role: topic,     particle: は},
        {chunk: ピアノ, role: object,   particle: を},
        {chunk: 習いたい, role: predicate}]

Wholly mechanical, zero AI: chunks come from the token array, roles from the particle that closes each
chunk. All 14,184 particles in the bank are linked to their token, which is what makes the join exact
rather than positional guesswork.

ROLE ASSIGNMENT is by (particle, function_type) -- NOT by the particle surface alone. Every particle in
the bank carries a `function_type` from a closed, language-neutral enum, and the same surface plays
different roles depending on it. Reading only the surface shipped three wrong drills into the role bank:

    仕事から帰った        から/case         origin       "a ORIGEM"       correct
    高いから買わない      から/conjunctive  cause        "a ORIGEM"       WRONG, it means "porque"
    私の本              の/case          genitive     "o MODIFICADOR"  correct
    走るのが好き          の/nominalizer   nominalizer  "o MODIFICADOR"  WRONG, it modifies nothing
    雨が降る            が/case          subject      "o SUJEITO"      correct
    高いですが買う        が/conjunctive  adversative  "o SUJEITO"      WRONG, it means "mas"

Three further refinements:
  * は is `binding`, not a case particle. It marks the TOPIC, which is frequently not the subject, and
    conflating the two is the single most common way a course teaches は wrong. It gets its own role.
  * に and で are genuinely ambiguous (に: dative / location-of-existence / time / direction; で: place
    of action / means). Rather than guess, they map to a role that names the particle instead of
    over-committing: `ni-phrase`, `de-phrase`. A drill can still use them; a lesson can still explain
    them; nothing claims a distinction the data does not carry.
  * と gets the SAME treatment, and this one was learned the hard way. It used to map to `with`, so the
    role drill asked "which part is marked by と (companhia ou par)?" of 花は切られるとすぐにしぼむ
    (conditional と) and 早く起きろと父に言われた (quotative と). `function_type` separates the
    conditional (`conjunctive`, 81 of them) but NOT the quotative from the comitative: both are `case`
    and UniDic calls both 格助詞, so no language-neutral field in the corpus carries that distinction.
    The only place it exists is the per-sentence pt-BR `function_pt` prose, and deriving a mechanical
    role by grepping Portuguese would break the language-agnostic rule (design/i18n.md) besides being
    fragile. A heuristic was tried -- comitative iff the preceding token is nominal and no verb of
    saying follows -- and scored against that prose: it labelled 10 quotatives `with` and lost 7 real
    comitatives (友達と話す trips the saying-verb test). So と maps to `to-phrase` and is not a drill
    target. Recovering the comitative properly needs a finer `sense` enum on the particle record, which
    is an authoring pass, not a heuristic.

The PREDICATE is the trailing verbal/adjectival run, taken whole: 習い + たい is one chunk, because
splitting a verb from its auxiliary produces drill pieces no learner should have to assemble separately.

Sentence-final particles (ね, よ, か) are kept as their own trailing chunk rather than folded into the
predicate, since they are exactly what a "make it softer / make it a question" drill manipulates.

KNOWN LIMITATION, visible in the output: an adverb has no particle to close it, so it glues to the
following noun (どんどんガソリンの値段が上がります gives "どんどんガソリン[modifier]" rather than a
separate adverb chunk). Splitting on POS instead would break the predicate run, which matters more --
習い + たい must stay one drill piece. Fixing it properly needs adverb detection, not a different
delimiter, so it is recorded rather than papered over.

Output: research/derived/sentence_patterns.json. Not written into corpus/ yet - it wants a validator and
a consumer first.

Usage: build_sentence_patterns.py [--limit N]
"""
from __future__ import annotations
import argparse, json, os, sqlite3, sys
from collections import Counter
from pathlib import Path
sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
ROOT = Path(__file__).resolve().parents[2]
DB = ROOT / "db" / "corpus.sqlite"
OUT = ROOT / "research" / "derived" / "sentence_patterns.json"

# (particle, function_type) -> role. Neutral English enum values (design/i18n.md); only prose is
# localised. Keyed on the PAIR because the surface alone is not the role -- see the module docstring.
ROLE = {
    ("は", "binding"): "topic",
    ("が", "case"): "subject",
    ("が", "conjunctive"): "ga-clause",          # adversative "mas", not a subject
    ("を", "case"): "object",
    ("も", "binding"): "also",
    ("の", "case"): "modifier",
    ("の", "nominalizer"): "nominalizer",        # 走るのが好き -- nominalises a clause, modifies nothing
    ("から", "case"): "from",
    ("から", "conjunctive"): "kara-clause",  # "porque", not an origin
    ("まで", "adverbial"): "until",
    ("へ", "case"): "direction",
    ("より", "case"): "than",
    # Deliberately not over-committed; the data does not disambiguate these.
    ("に", "case"): "ni-phrase",
    ("に", "conjunctive"): "ni-clause",           # のに, concessive -- joins clauses, marks nothing
    ("で", "case"): "de-phrase",
    ("で", "conjunctive"): "de-clause",
    ("と", "case"): "to-phrase",
    ("と", "conjunctive"): "to-clause",
}
# Used when a particle carries a function_type this table does not list. Every ambiguous surface falls
# back to its NON-COMMITTAL role, so an unexpected function_type can never invent a claim -- it degrades
# to a chunk the drill will not ask about. All 14,184 particles are currently linked and typed, so this
# is a guard against future data rather than a path anything takes today.
ROLE_FALLBACK = {
    "は": "topic", "を": "object", "も": "also", "まで": "until",
    "へ": "direction", "より": "than",
    "が": "ga-phrase", "の": "no-phrase", "から": "kara-phrase",
    "に": "ni-phrase", "で": "de-phrase", "と": "to-phrase",
}


NOMINAL = {"名詞", "代名詞", "数詞", "接尾辞"}


def role_of(surface: str, ft: str | None, prev_pc: str | None) -> str | None:
    """The role a particle assigns to the chunk it closes, or None if it closes no chunk.

    `prev_pc` is the part of speech of the token the particle attaches to, and it is needed for exactly
    one distinction that `function_type` does not draw: 〜てから. Both 東から上る and 食べてから出かけます
    carry から/case, but only the first is an origin -- the second means "after doing X", and asking
    "qual parte é a ORIGEM?" of 食べて teaches a starting point that is not there. A case particle marking
    origin attaches to a NOMINAL; the て of 〜てから is a 助詞, so the two separate cleanly (93 nominal vs
    11 particle-attached across the bank, and all 11 of those are 〜てから).
    """
    if surface == "から" and ft == "case" and prev_pc is not None and prev_pc not in NOMINAL:
        return "te-kara"          # sequence, not origin. Never a drill target.
    if (surface, ft) in ROLE:
        return ROLE[(surface, ft)]
    return ROLE_FALLBACK.get(surface)
PREDICATE_POS = {"動詞", "形容詞", "形状詞", "助動詞"}
CONTENT_POS = {"名詞", "代名詞", "動詞", "形容詞", "副詞", "形状詞", "連体詞", "感動詞",
               "接続詞", "接頭辞", "接尾辞", "数詞"}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=0)
    args = ap.parse_args()
    con = sqlite3.connect(DB)

    fin = {}          # token_id -> function_type, for particles
    for tid, ft in con.execute("SELECT token_id,function_type FROM particle WHERE token_id IS NOT NULL"):
        fin[tid] = ft

    q = "SELECT id,slug,jp FROM sentence ORDER BY id"
    if args.limit:
        q += f" LIMIT {args.limit}"
    out, stats = [], Counter()

    for sid, slug, jp in con.execute(q):
        toks = con.execute(
            "SELECT id,position,surface,pos_coarse FROM token WHERE sentence_id=? AND split_mode='C' "
            "ORDER BY position", (sid,)).fetchall()
        if not toks:
            stats["no tokens"] += 1
            continue

        pattern, buf, prev_pc = [], [], None
        for tid, pos, surf, pc in toks:
            if pc == "補助記号":
                # Punctuation CLOSES the running chunk. Skipping it silently glued text across a comma
                # (みえて、返事 became the chunk みえて返事), producing chunks that are not substrings of
                # the sentence at all — 325 role-drill options the learner could not find on the page.
                # A comma is also a clause boundary, so closing there is right on its own terms.
                if buf:
                    pattern.append({"chunk": "".join(buf), "role": "phrase"})
                    buf = []
                continue
            is_particle = pc == "助詞"
            ft = fin.get(tid)
            if is_particle and ft == "sentence-final":
                if buf:
                    pattern.append({"chunk": "".join(buf), "role": "predicate"})
                    buf = []
                pattern.append({"chunk": surf, "role": "sentence-final", "particle": surf})
                continue
            role = role_of(surf, ft, prev_pc) if is_particle else None
            prev_pc = pc
            if role and buf:
                pattern.append({"chunk": "".join(buf), "role": role, "particle": surf})
                buf = []
                continue
            if is_particle:
                # a particle we do not map, or one with nothing before it: keep it in the running chunk
                buf.append(surf)
                continue
            buf.append(surf)

        if buf:
            # The trailing run is the predicate when it ends verbal/adjectival; otherwise it is a bare
            # noun phrase (体言止め, headlines, one-word answers) and saying "predicate" would be false.
            last_pc = next((pc for tid, pos, surf, pc in reversed(toks) if pc != "補助記号"), "")
            pattern.append({"chunk": "".join(buf),
                            "role": "predicate" if last_pc in PREDICATE_POS else "phrase"})

        if not pattern:
            stats["empty pattern"] += 1
            continue
        # I1 for patterns: the chunks must reconstruct the sentence minus its punctuation.
        # The particle lives in its own field, so it must be counted here too or every sentence with a
        # case particle "fails" reconstruction — which is exactly what happened first time: 5,278 of
        # 5,889 skipped, hiding every topic/object role behind a bogus integrity failure.
        joined = "".join(p["chunk"] + (p.get("particle") or "") for p in pattern
                         if p["role"] != "sentence-final") +                  "".join(p["chunk"] for p in pattern if p["role"] == "sentence-final")
        bare = "".join(s for _, _, s, pc in toks if pc != "補助記号")
        if joined != bare:
            stats["chunks do not reconstruct the sentence"] += 1
            continue
        out.append({"slug": slug, "jp": jp, "pattern": pattern})
        stats["patterns"] += 1
        stats[f"roles:{len(pattern)}"] += 0
        for p in pattern:
            stats[f"role.{p['role']}"] += 1

    # Written via a temp file + os.replace: the clause-structure pass reads this file concurrently,
    # and a non-atomic write hands a reader truncated JSON.
    TMP = OUT.with_suffix(".json.tmp")
    TMP.write_text(json.dumps(
        {"note": "Roadmap F. Mechanical sentence patterns derived from the dissection: chunks from the "
                 "token array, roles from the (particle, function_type) PAIR closing each chunk -- the "
                 "pair, because から/case is an origin while から/conjunctive means 'porque', and "
                 "の/case links nouns while の/nominalizer modifies nothing. は is TOPIC, not subject. "
                 "に, で and と map to ni-phrase / de-phrase / to-phrase rather than guessing senses.",
         "count": len(out), "sentences": out}, ensure_ascii=False), encoding="utf-8")
    os.replace(TMP, OUT)
    roles = {k[5:]: v for k, v in stats.items() if k.startswith("role.")}
    print(f"sentence patterns: {stats['patterns']} built")
    print("  roles: " + "  ".join(f"{k}={v}" for k, v in sorted(roles.items(), key=lambda t: -t[1])))
    bad = {k: v for k, v in stats.items() if not k.startswith("role") and k != "patterns"}
    if bad:
        print(f"  skipped: {bad}")
    con.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
