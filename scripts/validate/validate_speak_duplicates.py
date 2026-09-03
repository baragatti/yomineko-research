#!/usr/bin/env python3
"""W34 / readiness G4 — near-duplicate phrases inside one speaking-path stage, above R86.

THE RULE THIS SITS ON TOP OF, VERBATIM (design/speaking_path.md §3.8):

    R86 — punctuation is not a phrase. Two bank sentences whose Japanese is identical once
    punctuation and spacing are stripped are **one phrase** and compete for **one** slot, path-wide.
    おはよう！ and おはよう。 are the same thing said out loud, and `arrival` spent **8 of its 36
    slots** teaching four greetings twice over; `politeness-01` taught おめでとうございます。 and
    おめでとうございます！ side by side. The duplication propagated: `arrival-03` shipped two
    production items with the identical prompt "Bom dia!". This path is scored on speech, where the
    difference is inaudible.

R86 holds: **0** punctuation-normalised duplicate groups path-wide, and that clause gates hard here.
It is also the weakest possible version of its own argument. A path "scored on speech" does not get
four separate slots for 長い事お待たせしてすみません / 長くお待たせしてすみませんでした /
こんなに長い間待たせてすみません / 長い間、お待たせしてすみませんでした just because the strings
differ by a particle — three of those four carry the IDENTICAL pt-BR prompt. R86 cannot see any of
it, because none of the four are equal after stripping punctuation.

THE NEAR-DUPLICATE RULE, STATED
--------------------------------
Two `say_now` phrases **in the same stage** are near-duplicates when

    (ratio(jp_a, jp_b) + ratio(pt_a, pt_b)) / 2  >=  0.72

where `ratio` is `difflib.SequenceMatcher(None, a, b).ratio()` and

    jp_x  the sentence's `jp` with R86's own punctuation/space class removed — the builder's
          PUNCT_RE, imported rather than retyped so the two can never disagree about what R86 strips
    pt_x  the sentence's pt-BR translation, NFKD-normalised, lowercased, accents dropped, reduced to
          [a-z0-9] — so "Obrigado por ter vindo." and "obrigado por ter vindo" are one string

Both halves are required because either alone is wrong in a way this corpus demonstrates. Japanese
alone scores おはよう against おはようございます at 0.615 and would miss it, though the pt-BR is
identical; pt-BR alone scores 教えてくれてありがとう against 来てくれてありがとう on translations that
differ by a verb, though the Japanese is 0.857 the same. The mean catches both classes and is what
`research/reports/readiness/speak_fast_path.md` measured at **24 in-stage pairs**.

Scope is `say_now` within one stage, and that is deliberate: R86's unit of competition is the phrase
SLOT, and two similar phrases eleven stages apart are spacing, not duplication.

The 0.72 threshold is the readiness measurement's, not a derived constant, and it is stated here
rather than tuned: it is the line at which the four apologies and the four 〜てくれてありがとう
variants in `arrival` come out as one cluster each.

WHAT GATES HARD, TODAY
-----------------------
  * R86 itself: two say_now phrases whose punctuation-normalised Japanese is equal, anywhere on the
    path, FAIL. Zero today — this is the wall that keeps the rule from silently regressing while the
    softer ratchet below absorbs attention.
  * A say_now ref resolving to no bank sentence FAILS (it would otherwise drop out of the pairing
    and lower the count).
  * Floors: fewer than 12 stages or 400 phrase slots is a vanished tree, and an empty tree scores
    zero duplicates, which is the most flattering possible wrong answer.

WHAT IS RATCHETED
-----------------
Per stage, the number of near-duplicate pairs, frozen in `speak_duplicate_baseline.json` at today's
**24 pairs — 13 of them in `arrival`**, the first stage a learner meets. Growth is a hard failure; a
shrink prints "lower the ceiling". (The readiness report says "12 of them in `arrival`"; that figure
is its Japanese-only count. The rule stated above — the mean of both ratios, which is what produces
its headline 24 — puts `arrival` at 13. Frozen at the measurement, not at the prose.)

The pair list itself is the content work list and lands in
`research/reports/speak_near_duplicates.json`, rewritten only when its content changes.

FALSIFIABILITY (2026-09-02, six plants on a copied tree, all caught)
--------------------------------------------------------------------
Fixture as in `validate_speak_strands.py`: the COPIED validator run with `--root <fixture>`, so
R86's punctuation class and the baseline resolve inside the fixture. The unmutated copy reports
0 FAIL.

  おはようございます planted twice under two bank slugs
  (sent:tatoeba-335372 + sent:tatoeba-1576172)         -> R86: 'おはようございます' occupies 2 phrase
                                                          slots path-wide
  two near-identical apologies MOVED into `lodging`,
  and replaced in `arrival`, so no slug is reused and
  R86's exact clause has nothing to say                -> ratchet lodging: near-duplicate pairs grew
                                                          0 -> 1  (this is the plant that proves the
                                                          ≥0.72 rule independently of R86)
  a say_now ref pointing at no bank sentence           -> speak:eating-03: resolves to no bank
                                                          sentence, so it silently lowers the count
  corpus/sentences emptied                             -> empty sentence bank, 1 FAIL
  baseline ceilings emptied                            -> 13 FAIL: nothing frozen, nothing falsifiable

Reads exported JSON only; never db/corpus.sqlite.
Usage: validate_speak_duplicates.py [--root PATH] [--record] [--list]
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import unicodedata
from difflib import SequenceMatcher
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from speak_path_common import (  # noqa: E402
    REPO, builder_module, iter_units, jload, load_course, load_sentences, write_if_changed,
)

sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]

BASELINE = Path(__file__).resolve().parent / "speak_duplicate_baseline.json"
WORKLIST_REL = "research/reports/speak_near_duplicates.json"
MAX_REPORT = 20

THRESHOLD = 0.72
FLOOR_STAGES, FLOOR_PHRASES = 12, 400
NOT_ALNUM = re.compile(r"[^a-z0-9]")

NOTE = ("W34 ratchet (readiness G4). Per stage: `pairs` counts say_now phrase pairs whose mean of "
        "(punctuation-normalised Japanese ratio, accent-folded pt-BR ratio) reaches 0.72 under "
        "difflib.SequenceMatcher — the semantic near-duplicate class R86's punctuation-equality "
        "cannot see. It is DEBT and may only shrink; growth is a hard failure. Re-record with "
        "--record only after a deliberate re-selection, never to silence a failure. Retired by the "
        "arrival/health mining pass (G4), which replaces the near-duplicate clusters with the "
        "survival frames the stages never teach.")


def norm_jp(text: str, punct_re: re.Pattern[str]) -> str:
    """R86's own normalisation, using the builder's punctuation class."""
    return punct_re.sub("", text or "")


def norm_pt(text: str) -> str:
    """pt-BR reduced to a comparable spine: NFKD, lowercased, accents dropped, [a-z0-9] only."""
    s = unicodedata.normalize("NFKD", (text or "").lower())
    s = "".join(ch for ch in s if not unicodedata.combining(ch))
    return NOT_ALNUM.sub("", s)


def similarity(a: dict, b: dict, punct_re: re.Pattern[str]) -> tuple[float, float, float]:
    """(mean, jp ratio, pt ratio) for two bank sentences."""
    rj = SequenceMatcher(None, norm_jp(a.get("jp", ""), punct_re),
                         norm_jp(b.get("jp", ""), punct_re)).ratio()
    pa = norm_pt((a.get("translation") or {}).get("pt-BR"))
    pb = norm_pt((b.get("translation") or {}).get("pt-BR"))
    rp = SequenceMatcher(None, pa, pb).ratio() if pa and pb else 0.0
    return (rj + rp) / 2, rj, rp


def main() -> int:
    ap = argparse.ArgumentParser(description="semantic near-duplicate say_now phrases within a stage")
    ap.add_argument("--root", default=str(REPO), help="tree to validate (default: repo root)")
    ap.add_argument("--record", action="store_true",
                    help="re-freeze the ratchet after a DELIBERATE re-selection; never to hide a failure")
    ap.add_argument("--list", action="store_true", help="print every failure, not the first 20")
    ap.add_argument("--baseline", default=str(BASELINE), help=argparse.SUPPRESS)
    args = ap.parse_args()
    root = Path(args.root).resolve()
    baseline_path = Path(args.baseline).resolve()

    fails: list[str] = []
    try:
        course = load_course(root)
        units = iter_units(root, course)
    except (FileNotFoundError, ValueError) as exc:
        print(f"  [FAIL] {exc}")
        print("validate_speak_duplicates: the speaking path could not be read — 1 FAIL")
        return 1

    sentences = load_sentences(root)
    if not sentences:
        print("  [FAIL] corpus/sentences holds no sentences — every phrase would be unresolvable and "
              "no pair could ever be compared")
        print("validate_speak_duplicates: empty sentence bank — 1 FAIL")
        return 1
    punct_re = builder_module().PUNCT_RE

    # ---- collect the phrase slots, stage by stage, in course order --------------------------------
    by_stage: dict[str, list[tuple[str, str]]] = {}     # stage -> [(unit id, sentence slug)]
    slots = 0
    for row in units:
        for ref in row["unit"].get("say_now") or []:
            slots += 1
            if ref not in sentences:
                fails.append(f"{row['id']}: say_now ref {ref} resolves to no bank sentence, so it "
                             f"cannot be compared and silently lowers the duplicate count")
                continue
            by_stage.setdefault(row["stage"], []).append((row["id"], ref))

    if len(by_stage) < FLOOR_STAGES:
        fails.append(f"{len(by_stage)} stages hold phrases, floor is {FLOOR_STAGES}")
    if slots < FLOOR_PHRASES:
        fails.append(f"{slots} say_now slots, floor is {FLOOR_PHRASES} — an empty path has no "
                     f"duplicates, which is not the same as a clean one")

    # ---- R86 itself, path-wide, hard --------------------------------------------------------------
    exact: dict[str, list[tuple[str, str]]] = {}
    for stage, items in by_stage.items():
        for uid, ref in items:
            exact.setdefault(norm_jp(sentences[ref]["jp"], punct_re), []).append((uid, ref))
    for key, group in sorted(exact.items()):
        if len(group) > 1:
            where = ", ".join(f"{u}:{r}" for u, r in group)
            fails.append(f"R86: {key!r} occupies {len(group)} phrase slots path-wide ({where}) — the "
                         f"same thing said out loud, competing for one slot")

    # ---- the near-duplicate measurement -----------------------------------------------------------
    observed: dict[str, int] = {}
    worklist: dict[str, list[dict]] = {}
    for stage, items in by_stage.items():
        pairs: list[dict] = []
        for i in range(len(items)):
            for j in range(i + 1, len(items)):
                a, b = sentences[items[i][1]], sentences[items[j][1]]
                mean, rj, rp = similarity(a, b, punct_re)
                if mean >= THRESHOLD:
                    pairs.append({
                        "mean": round(mean, 3), "jp_ratio": round(rj, 3), "pt_ratio": round(rp, 3),
                        "a": {"unit": items[i][0], "sentence": items[i][1], "jp": a.get("jp"),
                              "pt": (a.get("translation") or {}).get("pt-BR")},
                        "b": {"unit": items[j][0], "sentence": items[j][1], "jp": b.get("jp"),
                              "pt": (b.get("translation") or {}).get("pt-BR")},
                    })
        pairs.sort(key=lambda p: -p["mean"])
        observed[stage] = len(pairs)
        if pairs:
            worklist[stage] = pairs

    total = sum(observed.values())

    # ---- the ratchet ------------------------------------------------------------------------------
    if args.record:
        payload = {"note": NOTE, "threshold": THRESHOLD, "total": total,
                   "phrase_slots": slots,
                   "ceilings": {k: observed[k] for k in sorted(observed)}}
        baseline_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
                                 encoding="utf-8")
        print(f"recorded {total} near-duplicate pairs over {len(observed)} stages "
              f"-> {baseline_path.name}")
        return 0

    base = jload(baseline_path) if baseline_path.exists() else {}
    ceilings = base.get("ceilings", {}) if isinstance(base, dict) else {}
    if not ceilings:
        fails.append(f"{baseline_path.name} holds no ceilings — a ratchet with nothing frozen in it "
                     f"cannot fail on growth. Record it with --record.")
    frozen_threshold = base.get("threshold") if isinstance(base, dict) else None
    if frozen_threshold is not None and abs(float(frozen_threshold) - THRESHOLD) > 1e-9:
        fails.append(f"{baseline_path.name} was frozen at threshold {frozen_threshold}, this run "
                     f"measures at {THRESHOLD} — the counts are not comparable")

    shrank: list[str] = []
    for stage in sorted(set(observed) | set(ceilings)):
        got, want = observed.get(stage), ceilings.get(stage)
        if got is None:
            fails.append(f"ratchet {stage}: the baseline freezes a stage this tree no longer has — a "
                         f"stale ceiling nothing can falsify. Re-record it.")
            continue
        if want is None:
            fails.append(f"ratchet {stage}: {got} near-duplicate pairs and no frozen ceiling — new "
                         f"debt cannot arrive unmeasured")
            continue
        if got > int(want):
            fails.append(f"ratchet {stage}: near-duplicate pairs grew {want} -> {got}. A re-selection "
                         f"put more of the same phrase into one stage's slots.")
        elif got < int(want):
            shrank.append(f"{stage}: {want} -> {got}")

    # ---- the work list ------------------------------------------------------------------------------
    if not args.record and root == REPO:
        wrote = write_if_changed(root / WORKLIST_REL, {
            "note": "W34 / readiness G4 work list: say_now phrases inside one stage that are the same "
                    "utterance to a listener. Rule and threshold in "
                    "scripts/validate/validate_speak_duplicates.py.",
            "threshold": THRESHOLD, "total": total,
            "stages": {k: worklist[k] for k in sorted(worklist)},
        })
        if wrote:
            print(f"  [adv]  work list updated: {WORKLIST_REL}")

    # ---- report ---------------------------------------------------------------------------------------
    print(f"  [adv]  rule: mean(SequenceMatcher over punctuation-stripped jp, over accent-folded "
          f"pt-BR) ≥ {THRESHOLD}, within one stage; R86 exact-equality path-wide is the hard clause")
    print(f"  [adv]  {slots} phrase slots, {len(by_stage)} stages, {total} near-duplicate pairs")
    for stage in by_stage:
        n = observed[stage]
        if n:
            worst = worklist[stage][0]
            print(f"  [adv]  {stage:16}{n:4} pair(s), worst {worst['mean']} "
                  f"({worst['a']['jp']} / {worst['b']['jp']})")
    if shrank:
        print("\n  RATCHET SHRANK — lower these ceilings with --record:")
        for line in shrank[:MAX_REPORT]:
            print(f"    {line}")
    for line in (fails if args.list else fails[:MAX_REPORT]):
        print(f"  [FAIL] {line}")
    if not args.list and len(fails) > MAX_REPORT:
        print(f"  [FAIL] … and {len(fails) - MAX_REPORT} more (re-run with --list)")
    print(f"validate_speak_duplicates: {slots} phrases, {total} near-duplicate pairs over "
          f"{len(by_stage)} stages, {len(fails)} FAIL")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
