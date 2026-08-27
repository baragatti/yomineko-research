#!/usr/bin/env python3
"""Stroke-data integrity gate over the EXPORTED JSON (migration-audit findings G12/G13/G14).

WHY THIS EXISTS. scripts/validate/validate_strokes.py checks that stroke *paths* are drawable, but it
reads db/corpus.sqlite (a regenerable index, not the source of truth), it never opens the kanji_stroke
table behind corpus/strokes/n*.json at all, and its stroke-count check is written
`WHERE ksl.count_match=1` — it inspects only the rows that already agree. So three defects sat in the
committed corpus with a green suite:

  G12  coverage was unvalidated in both directions: 7 kanji at TAUGHT levels have no stroke_lines
       record (n4 建 質 銀; n3 庭 御 段 解), i.e. the animation page renders nothing for them.
  G13  kanji.strokes contradicts stroke_order.total_strokes for 極 (12 vs 13) and 離 (19 vs 18),
       and the stroke_lines record for the same characters sides with kanji.strokes.
  G14  the kana registry and the kana stroke set disagree at both ends: 66 kana carry no stroke data
       (all yoon — defensible, but written down nowhere) and 17 stroke rows name a character with no
       kana record, so nothing in the graph can reach them.

Every one of those holes is declared in corpus/strokes/exemptions.json with a reason. An exemption that
matches nothing is itself a FAILURE, so the file can only shrink: the day the data is acquired, the
entry must go with it. Hard-gates taught levels (pre-n5..n3); n2/n1 coverage is reported as advisory
because those levels are not learner-facing yet.

Reads only corpus/*.json — never db/corpus.sqlite. Exit 1 on any failure.
Usage: validate_stroke_integrity.py [--root PATH]"""
from __future__ import annotations
import argparse, json, sys
from pathlib import Path
sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]

LEVELS = ("pre-n5", "n5", "n4", "n3", "n2", "n1")
TAUGHT = ("pre-n5", "n5", "n4", "n3")          # gated hard; n2/n1 are advisory
# A yoon digraph (きゃ, リョ, …) is drawn as its two component kana, which have their own stroke rows;
# it is the ONLY kana type allowed to carry no stroke record. Any other gap is a failure.
KANA_STROKELESS_TYPES = {"yoon"}
MAX_SHOWN = 15


def load(path: Path) -> list:
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else []


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=str(Path(__file__).resolve().parents[2]),
                    help="repo root to validate (default: this checkout)")
    args = ap.parse_args()
    root = Path(args.root).resolve()
    strokes_dir = root / "corpus" / "strokes"

    # ---------- load ----------
    kanji: dict[str, dict] = {}
    dup: list[str] = []
    for lv in LEVELS:
        for r in load(root / "corpus" / "kanji" / f"{lv}.json"):
            if r["character"] in kanji:
                dup.append(f"kanji {r['character']} declared twice in corpus/kanji")
            kanji[r["character"]] = r

    order: dict[str, dict] = {}
    order_lv: dict[str, str] = {}
    lines: dict[str, dict] = {}
    lines_lv: dict[str, str] = {}
    for lv in LEVELS:
        for r in load(strokes_dir / f"{lv}.json"):
            if r["character"] in order:
                dup.append(f"stroke_order {r['character']} declared twice")
            order[r["character"]] = r
            order_lv[r["character"]] = lv
        for r in load(strokes_dir / f"lines_{lv}.json"):
            if r["character"] in lines:
                dup.append(f"stroke_lines {r['character']} declared twice")
            lines[r["character"]] = r
            lines_lv[r["character"]] = lv

    kana: dict[str, dict] = {}
    kana_script: dict[str, str] = {}
    for script in ("hiragana", "katakana"):
        for r in load(root / "corpus" / "kana" / f"{script}.json"):
            kana[r["char"]] = r
            kana_script[r["char"]] = script
    kstroke: dict[str, dict] = {}
    for r in load(strokes_dir / "kana.json"):
        if r["char"] in kstroke:
            dup.append(f"stroke_kana {r['char']} declared twice")
        kstroke[r["char"]] = r

    ex_path = strokes_dir / "exemptions.json"
    if not ex_path.exists():
        print(f"validate_stroke_integrity: FAIL missing {ex_path}")
        return 1
    ex = json.loads(ex_path.read_text(encoding="utf-8"))
    ex_cov = {(e["character"], e["missing"]): e for e in ex.get("coverage", [])}
    ex_cnt = {e["character"]: e for e in ex.get("counts", [])}
    ex_orph = {e["char"]: e for e in ex.get("kana_orphans", [])}
    for name, entries in (("coverage", ex.get("coverage", [])), ("counts", ex.get("counts", [])),
                          ("kana_orphans", ex.get("kana_orphans", []))):
        for e in entries:
            if not str(e.get("reason", "")).strip():
                dup.append(f"exemption in '{name}' carries no reason: {e}")
    used: set = set()

    fails: list[str] = []

    def check(label: str, bad: list[str]) -> None:
        if bad:
            fails.extend(bad)
            print(f"  FAIL {label}: {len(bad)}  e.g. {bad[0]}")
        else:
            print(f"  ok   {label}")

    check("S0 no duplicate natural keys / every exemption has a reason", dup)

    # ---------- S1 coverage at taught levels (hard) ----------
    cov_bad: list[str] = []
    adv: dict[str, list[int]] = {lv: [0, 0, 0] for lv in LEVELS}   # [kanji, no-order, no-lines]
    for ch, k in kanji.items():
        lv = k.get("level")
        row = adv.setdefault(lv, [0, 0, 0])
        row[0] += 1
        for kind, table in (("stroke_order", order), ("stroke_lines", lines)):
            if ch in table:
                continue
            row[1 if kind == "stroke_order" else 2] += 1
            if lv not in TAUGHT:
                continue
            e = ex_cov.get((ch, kind))
            if e:
                used.add(("coverage", ch, kind))
            else:
                cov_bad.append(f"{lv} kanji {ch} has no {kind} record")
    check("S1 taught-level kanji have stroke_order + stroke_lines", cov_bad)

    # ---------- S2 stroke counts agree (hard, all levels) ----------
    cnt_bad: list[str] = []
    for ch in sorted(set(order) | set(lines)):
        k = kanji.get(ch)
        o = order.get(ch)
        vals = {}
        if k is not None and k.get("strokes") is not None:
            vals["kanji.strokes"] = k["strokes"]
        if o is not None:
            vals["total_strokes"] = o.get("total_strokes")
            vals["len(steps)"] = len(o.get("steps") or [])
        if ch in lines:
            vals["len(stroke_lines)"] = len(lines[ch].get("strokes") or [])
        if len(set(vals.values())) > 1:
            if ch in ex_cnt:
                used.add(("counts", ch))
            else:
                cnt_bad.append(f"{ch} ({(k or {}).get('level', '?')}) stroke counts disagree: " +
                               ", ".join(f"{n}={v}" for n, v in vals.items()))
        if o is not None and not (isinstance(vals.get("total_strokes"), int) and vals["total_strokes"] > 0):
            cnt_bad.append(f"{ch} stroke_order.total_strokes is not a positive int: {o.get('total_strokes')!r}")
    check("S2 kanji.strokes == total_strokes == len(steps) == len(stroke_lines)", cnt_bad)

    # ---------- S3 a stroke record lives in the file matching its kanji's level ----------
    place_bad = [f"stroke_order {ch} is in strokes/{order_lv[ch]}.json but the kanji is {kanji[ch]['level']}"
                 for ch in order if ch in kanji and order_lv[ch] != kanji[ch]["level"]]
    place_bad += [f"stroke_lines {ch} is in strokes/lines_{lines_lv[ch]}.json but the kanji is {kanji[ch]['level']}"
                  for ch in lines if ch in kanji and lines_lv[ch] != kanji[ch]["level"]]
    check("S3 stroke record filed under its kanji's own level", place_bad)

    # ---------- S4 no orphan kanji stroke records ----------
    orph_bad = [f"stroke_order {ch} (strokes/{order_lv[ch]}.json) has no kanji record" for ch in order if ch not in kanji]
    orph_bad += [f"stroke_lines {ch} (strokes/lines_{lines_lv[ch]}.json) has no kanji record" for ch in lines if ch not in kanji]
    check("S4 every kanji stroke record names a real kanji", orph_bad)

    # ---------- S5 kana coverage (hard for every non-exempt type) ----------
    kana_bad, yoon_skipped = [], 0
    for ch, r in kana.items():
        if ch in kstroke:
            continue
        if r.get("type") in KANA_STROKELESS_TYPES:
            yoon_skipped += 1
            continue
        kana_bad.append(f"kana {ch} (type={r.get('type')}) has no stroke_kana record")
    check(f"S5 every kana outside {sorted(KANA_STROKELESS_TYPES)} has stroke data", kana_bad)

    # ---------- S6 kana stroke orphans are a declared closed set ----------
    korph_bad = []
    for ch in kstroke:
        if ch in kana:
            continue
        if ch in ex_orph:
            used.add(("kana_orphans", ch))
        else:
            korph_bad.append(f"stroke_kana {ch} has no kana record and is not a declared orphan")
    check("S6 kana stroke orphans are exactly the declared set", korph_bad)

    # ---------- S7 stroke_kana.kind agrees with the registry script ----------
    kind_bad = [f"stroke_kana {ch} says kind={kstroke[ch].get('kind')} but the registry files it under {kana_script[ch]}"
                for ch in kstroke if ch in kana and kstroke[ch].get("kind") != kana_script[ch]]
    check("S7 stroke_kana.kind matches the kana registry script", kind_bad)

    # ---------- S8 no stale exemptions ----------
    stale = [f"exemption coverage {ch}/{kind} matches nothing — delete it" for (ch, kind) in ex_cov
             if ("coverage", ch, kind) not in used]
    stale += [f"exemption counts {ch} matches nothing — delete it" for ch in ex_cnt if ("counts", ch) not in used]
    stale += [f"exemption kana_orphans {ch} matches nothing — delete it" for ch in ex_orph
              if ("kana_orphans", ch) not in used]
    check("S8 every exemption still matches a real hole", stale)

    # ---------- advisory ----------
    print("  --- advisory (not gated) ---")
    for lv in LEVELS:
        n, no_o, no_l = adv.get(lv, [0, 0, 0])
        if n:
            tag = "TAUGHT" if lv in TAUGHT else "future"
            print(f"  {tag:6} {lv:6} {n:5} kanji · missing stroke_order {no_o:4} · missing stroke_lines {no_l:3}")
    print(f"  kana: {len(kana)} registry · {len(kstroke)} stroke rows · {yoon_skipped} yoon with no stroke data "
          f"(exempt by type) · {len(ex_orph)} declared orphan rows")

    for f in fails[:MAX_SHOWN]:
        print("  FAIL", f)
    if len(fails) > MAX_SHOWN:
        print(f"  ... {len(fails) - MAX_SHOWN} more")
    print(f"\nvalidate_stroke_integrity: {len(kanji)} kanji, {len(order)} stroke_order, {len(lines)} stroke_lines, "
          f"{len(kana)} kana, {len(kstroke)} stroke_kana, "
          f"{len(ex_cov) + len(ex_cnt) + len(ex_orph)} exemptions — "
          f"{'FAIL ' + str(len(fails)) if fails else 'ALL OK'}")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
