#!/usr/bin/env python3
"""Build ROLE-IDENTIFICATION drills from the sentence patterns. Consumer for roadmap item F.

Why this drill and not a word-order one. The obvious use of pattern[] is to scramble the chunks and ask
the learner to reassemble them, and the bank already has 873 `sentence_order` items doing exactly that
with raw tokens. That design has a defect this project already documented: Japanese word order is
flexible, so 私は明日東京に行く and 明日私は東京に行く are both correct, and an auto-graded ordering item
cannot tell the learner which one it wanted. Scrambling CHUNKS instead of tokens makes it worse, because
chunks are precisely the units that move freely.

Role identification has no such ambiguity. "Which part is the direct object?" has exactly one answer,
fixed by the を that closes the chunk, and the answer is DERIVED rather than judged. It also happens to
teach the thing the ordering drill only pretends to: that Japanese marks grammatical role with a
particle rather than with position, which is the single hardest idea for a Portuguese speaker whose L1
marks role BY position.

An item shows a sentence, names a role in pt-BR, and offers the sentence's own chunks as options:

    猫の毛はとてもきれいだ      Qual parte é o TÓPICO?      -> 毛 (は)     vs 猫 / とてもきれいだ

Constraints that make it answerable:
  * the target role must occur EXACTLY ONCE in the sentence. Two を chunks means two defensible answers.
  * at least 3 chunks, so there are real distractors; at most 6, so the options stay readable.
  * `ni-phrase` and `de-phrase` are excluded as TARGETS. They exist precisely because に and で are
    ambiguous, so asking "which part is the ni-phrase" tests reading the particle off the page rather
    than understanding a role. They stay as distractors, where they are honest.

Output: corpus/exercises/roles/<level>_roles.json.
Usage: build_role_exercises.py
"""
from __future__ import annotations
import hashlib, json, sqlite3, sys
from collections import Counter
from pathlib import Path
sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
ROOT = Path(__file__).resolve().parents[2]
DB = ROOT / "db" / "corpus.sqlite"
SRC = ROOT / "research" / "derived" / "sentence_patterns.json"
OUT = ROOT / "corpus" / "exercises" / "roles"

# Roles worth asking about, with the pt-BR prompt. Neutral English keys, localised prompt (design/i18n.md).
ASKABLE = {
    "topic": "o TÓPICO (o que a frase apresenta antes de comentar)",
    "subject": "o SUJEITO",
    "object": "o OBJETO DIRETO",
    "predicate": "o PREDICADO (o que a frase diz)",
    "modifier": "o MODIFICADOR (a parte ligada por の)",
    "with": "a parte marcada por と (companhia ou par)",
    "from": "a ORIGEM (marcada por から)",
    "direction": "o DESTINO (marcado por へ)",
}
MIN_CHUNKS, MAX_CHUNKS = 3, 6


def spread(anchor: str, value: str) -> str:
    return hashlib.sha1(f"{anchor}{value}".encode("utf-8")).hexdigest()


def main() -> int:
    con = sqlite3.connect(DB)
    level_of = {slug: lv for slug, lv in con.execute("SELECT slug,level FROM sentence")}
    data = json.loads(SRC.read_text(encoding="utf-8"))["sentences"]

    banks: dict[str, list] = {}
    stats, skipped = Counter(), Counter()
    for s in data:
        pat = s["pattern"]
        if not (MIN_CHUNKS <= len(pat) <= MAX_CHUNKS):
            skipped["wrong chunk count"] += 1
            continue
        lv = level_of.get(s["slug"])
        if lv not in ("n5", "n4", "n3"):
            skipped["level outside n5-n3"] += 1
            continue
        counts = Counter(p["role"] for p in pat)
        for role, prompt in ASKABLE.items():
            if counts.get(role) != 1:
                continue                      # absent, or ambiguous because it occurs twice
            answer = next(p for p in pat if p["role"] == role)
            others = [p for p in pat if p is not answer]
            if len(others) < 2:
                skipped["not enough distractors"] += 1
                continue
            iid = f"rl:{lv}:{s['slug'].split(':', 1)[1]}:{role}"
            opts = [answer["chunk"]] + [p["chunk"] for p in others]
            if len(set(opts)) != len(opts):
                skipped["repeated chunk text"] += 1
                continue
            banks.setdefault(f"{lv}_roles", []).append({
                "id": iid, "level": lv, "sentence": s["slug"], "jp": s["jp"],
                "role": role, "prompt": {"pt-BR": f"Qual parte é {prompt}?"},
                "correct": answer["chunk"],
                "particle": answer.get("particle"),
                "distractors": sorted((p["chunk"] for p in others), key=lambda c: spread(iid, c))[:3],
                "source": "sentence-patterns", "layer": "B", "needs_review": 0,
            })
            stats[role] += 1

    OUT.mkdir(parents=True, exist_ok=True)
    for name, items in sorted(banks.items()):
        items.sort(key=lambda i: i["id"])
        (OUT / f"{name}.json").write_text(json.dumps(items, ensure_ascii=False, indent=1) + "\n",
                                          encoding="utf-8")
    total = sum(len(v) for v in banks.values())
    (OUT / "INDEX.md").write_text(
        "# corpus/exercises/roles - which part plays which grammatical role\n\n"
        "Built by `scripts/export/build_role_exercises.py` from the mechanical sentence patterns "
        "(roadmap F). Every answer is DERIVED from the particle that closes the chunk, so the bank is "
        "Layer B: no AI, no judgement.\n\n"
        "**Why this and not a word-order drill.** Japanese word order is flexible, so an auto-graded "
        "reassembly item cannot tell the learner which of several correct orders it wanted - a defect "
        "the existing `sentence_order` bank has. Role identification has exactly one answer, and it "
        "teaches the idea the ordering drill only gestures at: Japanese marks grammatical role with a "
        "PARTICLE, not with position, which is the hardest single adjustment for a Portuguese speaker "
        "whose L1 marks role by position.\n\n"
        f"**{total} items** across "
        + ", ".join(f"{k.split('_')[0].upper()} {len(v)}" for k, v in sorted(banks.items()))
        + ".\n\nA role is only asked about when it occurs EXACTLY ONCE in the sentence; two を chunks "
        "would mean two defensible answers. `ni-phrase` and `de-phrase` are never targets - they exist "
        "because に and で are ambiguous, so asking for them would test reading the particle off the "
        "page rather than understanding a role. They remain as distractors, where they are honest.\n",
        encoding="utf-8")

    print(f"role exercises: {total} items  " + "  ".join(f"{k}={len(v)}" for k, v in sorted(banks.items())))
    print("  by role: " + "  ".join(f"{k}={v}" for k, v in stats.most_common()))
    print(f"  skipped: {dict(skipped)}")
    con.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
