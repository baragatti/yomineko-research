#!/usr/bin/env python3
"""P7 — close the last lesson-coverage gaps: items PLACED in a topic but never unlocked by any lesson.

The N4/N5 planners dropped a handful of placed items. Rather than re-author whole lessons, this inserts each
missing item into a contextually-fitting existing lesson: it adds the unlock AND a short "extras" mention before
the lesson's <checklist>, so the item is both covered (introduce-once) and minimally taught (a human reviewer can
enrich the prose). Idempotent: skips an item already unlocked by the target lesson. One-off; run once, then
load/validate/export. Usage: patch_coverage_gaps.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
ROOT = Path(__file__).resolve().parents[2]
LESSON_DIR = ROOT / "research" / "derived" / "lessons"

# lesson stem -> list of items to add. vocab: (type, headword, kana, pt_gloss); grammar: (type, key, form, pt)
PATCHES: dict[str, list[tuple]] = {
    "n5-passado-02": [("vocab", "点ける", "つける", "acender, ligar (luz, TV, fogo)")],
    "n5-particulas-lugar-08": [("vocab", "幾つ", "いくつ", "quantos? (quantidade)"),
                               ("vocab", "幾ら", "いくら", "quanto custa? / quanto?")],
    "n4-aspecto-06": [("vocab", "そろそろ", "そろそろ", "logo, daqui a pouco, está na hora de")],
    "n4-obrigacao-05": [("vocab", "市", "し", "cidade (município)")],
    "n4-volitivo-07": [("vocab", "許り", "ばかり", "só, apenas; (após verbo no passado) acabar de")],
    "n4-keigo-04": [("vocab", "参る", "まいる", "ir / vir (forma humilde de 行く e 来る)")],
    "n4-condicionais-08": [("grammar", "gp-91", "の次に", "depois de, em seguida a, ao lado de")],
}


def _build_section(items: list[tuple]) -> str:
    out = ['<heading level="3"><text>Mais um item para o seu repertório</text></heading>']
    lis = []
    for it in items:
        if it[0] == "vocab":
            _, hw, kana, pt = it
            lis.append(f'<item><jp reading="{kana}">{hw}</jp><text>: {pt}.</text></item>')
        else:  # grammar
            _, _key, form, pt = it
            lis.append(f'<item><jp>{form}</jp><text>: {pt}.</text></item>')
    out.append('<list ordered="false">' + "".join(lis) + '</list>')
    return "\n" + "\n".join(out) + "\n\n"


def main() -> int:
    patched = 0
    for stem, items in PATCHES.items():
        f = LESSON_DIR / f"{stem}.json"
        if not f.exists():
            print(f"  MISSING target lesson {stem} — skipped")
            continue
        d = json.loads(f.read_text(encoding="utf-8"))
        have = {(u["type"], u["ref"]) for u in d.get("unlocks", [])}
        new_items = []
        for it in items:
            typ = it[0]
            ref = f"vocab:{it[1]}" if typ == "vocab" else f"gram:{it[1]}"
            if (typ, ref) in have:
                continue
            d.setdefault("unlocks", []).append({"type": typ, "ref": ref})
            new_items.append(it)
        if not new_items:
            print(f"  {stem}: already patched — skip")
            continue
        body = d.get("body", "")
        idx = body.rfind("<checklist>")
        if idx < 0:
            print(f"  {stem}: no <checklist> — appending section at end")
            d["body"] = body + _build_section(new_items)
        else:
            d["body"] = body[:idx] + _build_section(new_items) + body[idx:]
        f.write_text(json.dumps(d, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(f"  {stem}: added {len(new_items)} item(s) -> {[i[1] for i in new_items]}")
        patched += 1
    print(f"patched {patched} lesson(s)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
