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

ROLE ASSIGNMENT is by particle, with two refinements that matter:
  * は is `binding`, not a case particle. It marks the TOPIC, which is frequently not the subject, and
    conflating the two is the single most common way a course teaches は wrong. It gets its own role.
  * に and で are genuinely ambiguous (に: dative / location-of-existence / time / direction; で: place
    of action / means). Rather than guess, they map to a role that names the particle instead of
    over-committing: `ni-phrase`, `de-phrase`. A drill can still use them; a lesson can still explain
    them; nothing claims a distinction the data does not carry.

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
import argparse, json, sqlite3, sys
from collections import Counter
from pathlib import Path
sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
ROOT = Path(__file__).resolve().parents[2]
DB = ROOT / "db" / "corpus.sqlite"
OUT = ROOT / "research" / "derived" / "sentence_patterns.json"

# Particle -> role. Neutral English enum values (design/i18n.md); only prose is localised.
ROLE = {
    "は": "topic", "が": "subject", "を": "object", "も": "also",
    "の": "modifier", "と": "with", "から": "from", "まで": "until",
    "へ": "direction", "より": "than",
    # Deliberately not over-committed: both are ambiguous and the data does not disambiguate them.
    "に": "ni-phrase", "で": "de-phrase",
}
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

        pattern, buf = [], []
        for tid, pos, surf, pc in toks:
            if pc == "補助記号":                       # punctuation closes nothing and carries no role
                continue
            is_particle = pc == "助詞"
            ft = fin.get(tid)
            if is_particle and ft == "sentence-final":
                if buf:
                    pattern.append({"chunk": "".join(buf), "role": "predicate"})
                    buf = []
                pattern.append({"chunk": surf, "role": "sentence-final", "particle": surf})
                continue
            if is_particle and surf in ROLE and buf:
                pattern.append({"chunk": "".join(buf), "role": ROLE[surf], "particle": surf})
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

    OUT.write_text(json.dumps(
        {"note": "Roadmap F. Mechanical sentence patterns derived from the dissection: chunks from the "
                 "token array, roles from the particle closing each chunk. は is TOPIC, not subject. "
                 "に and で map to ni-phrase / de-phrase rather than guessing between their senses.",
         "count": len(out), "sentences": out}, ensure_ascii=False), encoding="utf-8")
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
