#!/usr/bin/env python3
"""P5-n3-review: the `reading` of every bare kanji `<jp>` span in the three N3 review lessons.

WHY. The review lessons were authored with bare `<jp>` spans; `validate_lesson_bodies.py` ratchets
"spans with kanji and no reading" at 1 (C13 closed the rest), so 91 new bare spans fail the gate.
Nothing here is authored: a span gets a reading only when data already settles it.

THE RULES, in order, over the bodies in research/derived/repairs/n3_review_lessons.json
  furigana-i / -ii  scripts/build_furigana_table.py's own Deriver (the lesson's registry record, or
                    SudachiPy verified against the registries), unchanged.
  bank-sentence     the span IS a bank sentence verbatim (corpus/sentences/bank.json `jp`): the
                    reading is assembled from that sentence's own C-mode token dissection (Layer A
                    reading per token, context-resolved, which is what settles the homographs the
                    Deriver refuses: 私, 彼, 何, 時 ...). A token with no kanji and no digit keeps its
                    surface (so は stays は and katakana stays katakana); any other token gives its
                    `reading`.
  token-run         the span is a contiguous run of C-mode tokens of a bank sentence the SAME body
                    prints: the reading is that run's, assembled the same way (その上 in -01 is
                    read inside この靴は値段が高いし、その上、小さすぎる。).
Every reading, whatever the rule, then passes the Deriver's own verification: kana-only by the
gate's READING_OK, covers the hiragana written in the span, and aligns against the Layer-A kanji
registry through scripts/export/kanji_align.py. A span no rule settles is written to `residue` and
not applied, unless it is in REVIEWED (rule `reviewed`, F0-P5-finish: readings supplied by the
reviewing session, still kana-only and covering; the alignment is the check they failed).

OUTPUT research/derived/repairs/n3_review_furigana.json in the span-table shape
scripts/apply_lesson_body_spans.py applies (both layers). Deterministic. Needs the project venv.
Usage: .venv/Scripts/python.exe scripts/derive_n3_review_furigana.py [--check]
"""
from __future__ import annotations

import argparse
import collections
import json
import re
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import build_furigana_table as bft  # noqa: E402

LESSONS = ROOT / "research" / "derived" / "repairs" / "n3_review_lessons.json"
OUT = ROOT / "research" / "derived" / "repairs" / "n3_review_furigana.json"
DIGIT = re.compile(r"[0-9０-９]")

# F0-P5-finish: the 6 spans no rule settles (alignment refused: 姉 as ねえ, 明日/今日 jukujikun, 言う
# dissected as ゆう). Readings supplied and checked by the reviewing session; rule `reviewed`. Each
# still has to be kana-only and cover the span's own kana; only the registry alignment is waived.
REVIEWED: dict[tuple[str, str], str] = {
    ("les:n3-revisao-01", "私はあんたのお姉ちゃんだもん。"): "わたしはあんたのおねえちゃんだもん。",
    ("les:n3-revisao-02", "彼らは不平ばかり言う。"): "かれらはふへいばかりいう。",
    ("les:n3-revisao-02", "真実を言うべきだ。"): "しんじつをいうべきだ。",
    ("les:n3-revisao-03", "もしかすると明日雨が降るかもしれない。"): "もしかするとあしたあめがふるかもしれない。",
    ("les:n3-revisao-03", "ように言う"): "ようにいう",
    ("les:n3-revisao-03", "７月にしては今日はすずしい。"): "しちがつにしてはきょうはすずしい。",
}


def verify(dv: "bft.Deriver", surface: str, reading: str) -> str | None:
    """None when the reading passes the Deriver's checks, else the reason."""
    bad = [c for c in reading if not bft.READING_OK.match(c)]
    if bad:
        return f"not kana-only ({''.join(sorted(set(bad)))})"
    miss = bft.missing_kana(reading, surface)
    if miss:
        return f"{reading} does not cover the kana written in {surface}"
    try:
        ok = dv.aligner.align(surface, reading) is not None
    except Exception:                                      # noqa: BLE001
        ok = False
    return None if ok else f"{reading} does not align against the Layer-A kanji registry"


def token_reading(toks: list[dict]) -> str:
    return "".join(t["reading"] if (bft.KANJI.search(t["surface"]) or DIGIT.search(t["surface"]))
                   else t["surface"] for t in toks)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true", help="compare with the tracked table; write nothing")
    args = ap.parse_args()
    dv = bft.Deriver(ROOT)
    bank = {s["jp"]: [t for t in s["tokens"] if t.get("split_mode") == "C"]
            for s in json.loads((ROOT / "corpus" / "sentences" / "bank.json").read_text(encoding="utf-8"))}
    known_by = {}
    for f in (ROOT / "course").rglob("lesson-*.json"):
        d = json.loads(f.read_text(encoding="utf-8"))
        if d["id"].startswith("les:n3-revisao-"):
            known_by[d["id"]] = set((d.get("cumulative_known_set") or {}).get("vocab") or [])
    rows, residue = [], []
    for les in json.loads(LESSONS.read_text(encoding="utf-8"))["rows"]:
        lid, body = les["slug"], les["body"]
        spans = collections.Counter()
        for m in bft.JP_ANY.finditer(body):
            if "reading" in dict(bft.ATTR.findall(m.group(1))):
                continue
            plain = bft.TAGS.sub("", m.group(2))
            if bft.KANJI.search(plain):
                spans[(m.group(0), m.group(1), m.group(2), plain)] += 1
        shown = [bank[bft.TAGS.sub("", m.group(2))] for m in bft.JP_ANY.finditer(body)
                 if bft.TAGS.sub("", m.group(2)) in bank]
        for (tag, attrs, inner, plain), n in sorted(spans.items()):
            got = dv.derive(plain, known_by.get(lid, set()))
            reading, rule, why = got.get("reading"), got.get("rule"), got.get("why")
            if reading:
                rule = f"furigana-{rule}"
            elif plain in bank:
                reading, rule = token_reading(bank[plain]), "bank-sentence"
            else:
                for toks in shown:
                    for i in range(len(toks)):
                        acc = ""
                        for j in range(i, len(toks)):
                            acc += toks[j]["surface"]
                            if acc == plain:
                                reading, rule = token_reading(toks[i:j + 1]), "token-run"
                                break
                            if not plain.startswith(acc):
                                break
                        if reading:
                            break
                    if reading:
                        break
            if reading and rule in ("bank-sentence", "token-run"):
                bad = verify(dv, plain, reading)
                if bad:
                    why, reading = f"{rule}: {bad}", None
            if not reading and (lid, plain) in REVIEWED:
                reading, rule = REVIEWED[(lid, plain)], "reviewed"
                bad = verify(dv, plain, reading)
                if bad and "does not align" not in bad:   # jukujikun / いう vs ゆう: alignment is why they are here
                    raise SystemExit(f"reviewed reading {lid} {plain}: {bad}")
            if not reading:
                residue.append({"lesson": lid, "surface": plain, "occurrences": n, "why": why})
                continue
            rows.append({"lesson": lid, "surface": plain, "reading": reading, "rule": rule,
                         "occurrences": n,
                         "spans": [{"from": tag, "to": f'<jp{attrs} reading="{reading}">{inner}</jp>',
                                    "count": n}]})
    doc = {
        "what_this_is": ("The `reading` of every bare kanji <jp> span in the three N3 review lessons, "
                         "derived by scripts/derive_n3_review_furigana.py (rules in its docstring; "
                         "6 rows `reviewed`, supplied by the reviewing session) and applied by "
                         "scripts/apply_lesson_body_spans.py."),
        "unit": "P5-n3-review",
        "generated_by": "scripts/derive_n3_review_furigana.py",
        "applied_by": "scripts/apply_lesson_body_spans.py --table n3_review_furigana.json",
        "layer": "B",
        "counts": {"spans": sum(r["occurrences"] for r in rows) + sum(r["occurrences"] for r in residue),
                   "written": sum(r["occurrences"] for r in rows),
                   "by_rule": dict(collections.Counter(r["rule"] for r in rows)),
                   "residue": sum(r["occurrences"] for r in residue)},
        "row_count": len(rows),
        "rows": rows,
        "residue": residue,
    }
    text = json.dumps(doc, ensure_ascii=False, indent=1) + "\n"
    print(json.dumps(doc["counts"], ensure_ascii=False))
    for r in residue:
        print(f"  residue {r['lesson']} {r['surface']}: {r['why']}")
    same = OUT.exists() and OUT.read_text(encoding="utf-8") == text
    if args.check:
        print("table is current" if same else "TABLE IS STALE")
        return 0 if same else 1
    if not same:
        OUT.write_text(text, encoding="utf-8")
    print(f"wrote {OUT.relative_to(ROOT)}" if not same else "table unchanged")
    return 0


if __name__ == "__main__":
    sys.exit(main())
