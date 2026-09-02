#!/usr/bin/env python3
"""Per-item exam-bank fixes the completed QA audits confirmed and that need no owner decision.

Three classes, all applied in place to the committed bank JSON (the banks are not regenerable yet —
see STATE.md / PENDING.md A2 — so in-place is the durable layer for now):

  1. UNANSWERABLE ORTHOGRAPHY ITEMS (n5): the builder emitted one item per homophone kanji over the
     SAME bare-word stem and the SAME option set — あつい keyed 厚い, 暑い and 熱い with identical
     options. A bare stem gives the learner nothing to choose with, so every item in such a group is
     unanswerable, not just the "extra" ones. Removed, with the whole group recorded, into
     corpus/exam_banks/removed_items.json. Builder-side guard (never emit a bare-stem item whose
     option set contains two homophones of the stem) is a regeneration item.
  2. EXACT DUPLICATE PAIRS (n4 sentence_order): identical pieces and answer under two ids. The later
     id is removed into the ledger; the earlier stays.
  3. THREE LISTENING SCRIPTS with a content defect the audits named:
       lt:n5:004  a student calls his OWN brother お兄さん when speaking to a teacher — out-group
                  honorific for an in-group person; 兄 is the form the level teaches.
       lp:n3:008  the script says the next showing after 6:00 is 7:30, then finds a 7:00 showing
                  with seats, contradicting itself. The 7:00 showing is now full at first and opens
                  on a cancellation, so every time mentioned is consistent and each distractor is
                  still mentioned-then-rejected.
       lr:n3:tatoeba-11510681  the prompt 見たいのかしら？ is, per the corpus's own translation,
                  "Será que ele quer ver?" — wondering about a third person. The key answered in the
                  first person about oneself. The key now replies to what was said; the old key is
                  not kept as a distractor because a learner reading かしら as addressed to them
                  could defend it.

Idempotent; exact preconditions; loud skips. Usage: apply_exam_bank_item_fixes.py [--check]
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
ROOT = Path(__file__).resolve().parents[1]
BANKS = ROOT / "corpus" / "exam_banks"
LEDGER = BANKS / "removed_items.json"

REASON_AMBIG = ("bare-word stem with the same option set keyed to different homophone kanji — "
                "nothing in the item lets the learner choose; whole group removed")
REASON_DUP = "exact duplicate (same pieces, same answer) of {keep}"

# (file, id, field, exact old, new)
LISTENING_FIXES = [
    ("n5_listening_task.json", "lt:n5:004", "script", 1, "text",
     "先生、お兄さんの辞書をなくしました。", "先生、兄の辞書をなくしました。"),
    ("n5_listening_task.json", "lt:n5:004", "script", 3, "text",
     "名前は書きませんでした。教室はもう見ましたが、ありませんでした。お兄さんに電話しましょうか。",
     "名前は書きませんでした。教室はもう見ましたが、ありませんでした。兄に電話しましょうか。"),
    ("n5_listening_task.json", "lt:n5:004", "distractors", 0, None,
     "お兄さんに電話する", "兄に電話する"),
    ("n3_listening_point.json", "lp:n3:008", "script", 4, "text",
     "次は７時半。でも、それだと終わるのが１０時を過ぎちゃうよ。",
     "７時の回も満席で、その次が７時半。でも、それだと終わるのが１０時を過ぎちゃうよ。"),
    ("n3_listening_point.json", "lp:n3:008", "script", 6, "text",
     "あれは別の映画だよ。あ、待って、７時からの回ならまだ席が空いてるって。これにしよう。",
     "あれは別の映画だよ。あ、待って、７時の回にキャンセルが出て、席が空いたって。これにしよう。"),
    ("n3_listening_reply.json", "lr:n3:tatoeba-11510681", "correct", None, None,
     "うん、見たいな。", "さあ、本人に聞いてみたら？"),
    ("n3_listening_reply.json", "lr:n3:tatoeba-11510681", "distractors", 1, None,
     "もう見せたよ。", "見たことはあるよ。"),
]


def load(p: Path):
    return json.loads(p.read_text(encoding="utf-8"))


def dump(p: Path, data) -> None:
    p.write_text(json.dumps(data, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args()
    ledger = load(LEDGER) if LEDGER.exists() else {"count": 0, "items": []}
    already = {(e["file"], e["item"]["id"]) for e in ledger["items"]}
    removed, changed, done, skipped = [], 0, 0, []

    # ---- 1. unanswerable orthography groups ------------------------------------------------------
    p = BANKS / "n5_orthography.json"
    items = load(p)
    groups: dict = defaultdict(list)
    for it in items:
        groups[(it.get("stem"), tuple(sorted(it.get("options", []))))].append(it)
    drop = {it["id"] for g in groups.values() if len({x["correct"] for x in g}) > 1 for it in g}
    if drop:
        for it in items:
            if it["id"] in drop and (p.name, it["id"]) not in already:
                removed.append({"file": p.name, "reason": REASON_AMBIG, "item": it})
        kept = [it for it in items if it["id"] not in drop]
        print(f"  n5_orthography: removing {len(items) - len(kept)} unanswerable items in "
              f"{sum(1 for g in groups.values() if len({x['correct'] for x in g}) > 1)} groups")
        if not args.check:
            dump(p, kept)
        changed += len(items) - len(kept)
    else:
        done += 1

    # ---- 2. exact duplicate pairs -----------------------------------------------------------------
    p = BANKS / "n4_sentence_order.json"
    items = load(p)

    def sig(it):
        # What the LEARNER sees: the pieces and the answer. Two items built from two different
        # source sentences with identical text are still the same question twice, so provenance
        # fields (sentence ref, source) are deliberately not part of the signature.
        body = {k: it.get(k) for k in ("stem", "pieces", "options", "correct", "prompt") if k in it}
        return json.dumps(body, ensure_ascii=False, sort_keys=True)
    seen: dict = {}
    dup_ids = {}
    for it in items:
        s = sig(it)
        if s in seen:
            dup_ids[it["id"]] = seen[s]
        else:
            seen[s] = it["id"]
    if dup_ids:
        for it in items:
            if it["id"] in dup_ids and (p.name, it["id"]) not in already:
                removed.append({"file": p.name, "reason": REASON_DUP.format(keep=dup_ids[it["id"]]),
                                "item": it})
        kept = [it for it in items if it["id"] not in dup_ids]
        print(f"  n4_sentence_order: removing {len(dup_ids)} exact duplicates "
              f"({', '.join(f'{a}->{b}' for a, b in dup_ids.items())})")
        if not args.check:
            dump(p, kept)
        changed += len(dup_ids)
    else:
        done += 1

    # ---- 3. listening scripts ---------------------------------------------------------------------
    by_file: dict = defaultdict(list)
    for f in LISTENING_FIXES:
        by_file[f[0]].append(f)
    for fname, fixes in by_file.items():
        p = BANKS / fname
        items = load(p)
        touched = False
        for _, iid, field, idx, sub, old, new in fixes:
            it = next((x for x in items if x["id"] == iid), None)
            if it is None:
                skipped.append(f"{iid}: not in {fname}")
                continue
            if idx is None:
                cur = it.get(field)
                if cur == new:
                    done += 1
                    continue
                if cur != old:
                    skipped.append(f"{iid}.{field}: expected {old!r}, found {cur!r}")
                    continue
                it[field] = new
            else:
                node = it[field][idx]
                cur = node[sub] if sub else node
                if cur == new:
                    done += 1
                    continue
                if cur != old:
                    skipped.append(f"{iid}.{field}[{idx}]: expected {old!r}, found {cur!r}")
                    continue
                if sub:
                    node[sub] = new
                else:
                    it[field][idx] = new
            print(f"  {iid}: {field}{'' if idx is None else f'[{idx}]'} fixed")
            changed += 1
            touched = True
        if touched and not args.check:
            dump(p, items)

    if removed and not args.check:
        ledger["items"].extend(removed)
        ledger["count"] = len(ledger["items"])
        dump(LEDGER, ledger)

    verb = "would change" if args.check else "changed"
    print(f"\n{verb} {changed}; already correct {done}; removed {len(removed)} into {LEDGER.name}")
    for s in skipped:
        print(f"  ! {s}")
    return 1 if (args.check and changed) else (2 if skipped else 0)


if __name__ == "__main__":
    sys.exit(main())
