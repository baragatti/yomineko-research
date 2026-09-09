#!/usr/bin/env python3
"""Unit test for the W15 dissector rule: a surface the gating lesson's known set contains must not
resolve to an unknown lemma.

THE DEFECT
----------
SudachiPy's `dictionary_form()` is a lemma, and a lemma can name a different registry record — at a
different JLPT level — than the surface in front of the learner:

    surface ください   lemma くださる   ->  vocab:1184280  下さる  N4
    surface ください   surface itself   ->  vocab:1184270  下さい  N5   <- what N5 lessons unlock

The known-set gate resolved lemma-first, so every N5 reading passage containing てください was
reported as introducing an N4 word its lesson never unlocks. てください is the ordinary polite
request at N5; the campaign lost it in every N5 passage (`APP_PLAN` W15, "the ください -> 下さる
lemma trap"). `known_set.PassageGate.resolve_token` now takes the first candidate the known set
already contains.

WHAT THIS TEST PINS DOWN — both directions
------------------------------------------
The rule must RESCUE the record the learner was actually taught (T1, T2) and must NOT LAUNDER a word
they were not (T3, T5). The dangerous failure mode of a "prefer whatever is known" rule is a
resolver that reaches sideways — to a homophone, to a same-kanji neighbour — and calls a genuinely
new word known. T5 plants exactly that: 橋 and 箸 are both はし and both N5, the known set holds 箸
and the passage says 橋. A reading-based tier would pass it. The candidate tiers are form lookups
only (lemma, surface, kana-normalised surface), so it fails, which is correct.

Run with the project venv (needs SudachiPy + sudachidict_full). Exit 1 on any failure.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
ROOT = Path(__file__).resolve().parents[2]
sys.path.append(str(ROOT / "scripts" / "ingest"))
from known_set import KnownSet, PassageGate, is_kana_only          # noqa: E402
from dissect import hira                                            # noqa: E402

KUDASAI_N5 = "vocab:1184270"     # 下さい / ください — the record N5 unlocks
KUDASARU_N4 = "vocab:1184280"    # 下さる / くださる — the lemma Sudachi returns
HASHI_BRIDGE = "vocab:1237410"   # 橋 はし
HASHI_CHOPSTICKS = "vocab:1476410"  # 箸 はし


def ks(vocab, kanji=()) -> KnownSet:
    return KnownSet(lesson="les:test", kanji=frozenset(kanji), vocab=frozenset(vocab),
                    grammar=frozenset())


def main() -> int:
    gate = PassageGate()
    slug = gate.slug_by_vid
    fails: list[str] = []

    def check(name: str, cond: bool, detail: str = "") -> None:
        print(f"  [{'PASS' if cond else 'FAIL'}] {name}{(' — ' + detail) if detail else ''}")
        if not cond:
            fails.append(name)

    # the fixtures must be the records this test believes they are, or it proves nothing
    hon = next((v for v, h in gate.head_by_vid.items() if h == "本"), None)
    check("fixtures: the four records exist and are the ones named",
          slug.get(212) == KUDASAI_N5 or KUDASAI_N5 in slug.values(),
          "registry carries 下さい and 下さる as separate records")
    vid_of = {s: v for v, s in slug.items()}
    for s in (KUDASAI_N5, KUDASARU_N4, HASHI_BRIDGE, HASHI_CHOPSTICKS):
        if s not in vid_of:
            fails.append(f"fixture {s} is not in the registry")

    # ---- T1. the trap itself, kana surface --------------------------------------------------
    r = gate.analyse("ください。", ks({KUDASAI_N5}))
    check("T1 kana surface ください resolves to the N5 record the lesson unlocks",
          r.ok and vid_of[KUDASAI_N5] in r.uses_vocab_ids,
          f"unknown={r.unknown_vocab} uses={[slug[v] for v in r.uses_vocab_ids]}")
    check("T1 the rescue is reported, naming both records",
          any(x["lemma_slug"] == KUDASARU_N4 and x["chosen_slug"] == KUDASAI_N5 for x in r.rescued),
          str(r.rescued))

    # ---- T2. same trap through a kanji surface ----------------------------------------------
    known2 = {KUDASAI_N5} | ({slug[hon]} if hon else set())
    r = gate.analyse("本を下さい。", ks(known2, {"本", "下"}))
    check("T2 kanji surface 下さい resolves to the N5 record too",
          not r.unknown_vocab and vid_of[KUDASAI_N5] in r.uses_vocab_ids,
          f"unknown={r.unknown_vocab}")

    # ---- T3. control: nothing to rescue -> the word is still NEW -----------------------------
    r = gate.analyse("本を下さい。", ks(({slug[hon]} if hon else set()), {"本", "下"}))
    check("T3 with neither record taught the word stays unknown (no laundering)",
          any(x["slug"] == KUDASARU_N4 for x in r.unknown_vocab),
          f"unknown={r.unknown_vocab}")
    check("T3 nothing was reported as rescued", not r.rescued, str(r.rescued))

    # ---- T4. the lemma tier still wins when the lemma is the taught record --------------------
    r = gate.analyse("本を下さい。", ks({KUDASARU_N4} | ({slug[hon]} if hon else set()), {"本", "下"}))
    check("T4 lemma-first order is preserved when the lemma record is the known one",
          not r.unknown_vocab and vid_of[KUDASARU_N4] in r.uses_vocab_ids and not r.rescued,
          f"uses={[slug[v] for v in r.uses_vocab_ids]} rescued={r.rescued}")

    # ---- T5. the laundering plant: same reading, same level, different word -------------------
    r = gate.analyse("橋をわたる。", ks({HASHI_CHOPSTICKS}, {"橋"}))
    check("T5 a same-reading neighbour (箸 for 橋) is NOT reachable — 橋 stays unknown",
          any(x["slug"] == HASHI_BRIDGE for x in r.unknown_vocab),
          f"unknown={r.unknown_vocab}")

    # ---- T6. the kanji gate is independent of the vocab rule ---------------------------------
    r = gate.analyse("橋をわたる。", ks({HASHI_BRIDGE}, set()))
    check("T6 an untaught kanji fails even when its word resolves",
          r.unknown_kanji == ["橋"] and not r.ok, f"unknown_kanji={r.unknown_kanji}")

    # ---- T7. no tier can invent a record; a tier never changes WHICH record it names ----------
    bad = []
    for lemma, surface in (("くださる", "ください"), ("下さる", "下さい"), ("橋", "橋"),
                           ("行く", "行っ"), ("為る", "し"), ("間", "間")):
        for vid in gate.d.vocab_candidates(lemma, surface):
            forms = {lemma, surface, hira(surface)}
            if not any(gate.d._vocab_by_form.get(f) == vid for f in forms):
                bad.append((lemma, surface, slug.get(vid)))
    check("T7 every candidate is the first-wins record of a real form lookup", not bad, str(bad))

    # ---- T8. the kana carve-out still applies to words with no taught record ------------------
    check("T8 is_kana_only agrees with the §3 carve-out",
          is_kana_only("ください") and is_kana_only("とても") and not is_kana_only("下さい"))

    # ---- T9. §3 numerals are allowed anyway --------------------------------------------------
    # 二 is vocab:1461140 (N5) and les:n5-numeros-tempo-04 — the numbers lesson — does not unlock it
    # as a word. design/reading_practice.md §3 waives numbers; the gate has to as well.
    r = gate.analyse("きょうしつは二かいです。", ks(set(), {"二"}))
    check("T9 a numeral is carved out, not charged as a new word",
          not r.unknown_vocab and any(c["why"] == "numeral" for c in r.carve_out),
          f"unknown={r.unknown_vocab} carve={r.carve_out}")

    # ---- T10. the run rule: Sudachi splits a word the lesson actually teaches ------------------
    OCHA = "vocab:1002430"   # お茶 N5 — taught; 茶 alone is vocab:1422570 N3 — not
    r = gate.analyse("あさはお茶をのみます。", ks({OCHA}, {"茶"}))
    check("T10 お|茶 is credited to the taught word お茶, not charged as 茶",
          not r.unknown_vocab and any(x["run"] == "お茶" and x["slug"] == OCHA for x in r.rescued_runs),
          f"unknown={r.unknown_vocab} runs={r.rescued_runs}")

    # ---- T11. the run rule cannot launder ------------------------------------------------------
    r = gate.analyse("あさはお茶をのみます。", ks(set(), {"茶"}))
    check("T11 with お茶 untaught the run rule rescues nothing and 茶 stays unknown",
          any(x["slug"] == "vocab:1422570" for x in r.unknown_vocab) and not r.rescued_runs,
          f"unknown={r.unknown_vocab} runs={r.rescued_runs}")

    # ---- T12. a run never crosses punctuation --------------------------------------------------
    planted = [{"surface": "お", "pos_coarse": "接頭辞", "pos_fine": "*"},
               {"surface": "。", "pos_coarse": "補助記号", "pos_fine": "句点"},
               {"surface": "茶", "pos_coarse": "名詞", "pos_fine": "普通名詞"}]
    vid_run, run = gate.resolve_run(planted, 2, ks({OCHA}, {"茶"}))
    check("T12 a run spelled across a 。 is a coincidence, not a word", vid_run is None,
          f"joined {run!r} -> {slug.get(vid_run) if vid_run else None}")

    print(f"\ntest_known_set_surface: 12 groups checked, {len(fails)} FAIL")
    if fails:
        for f in fails:
            print(f"  ! {f}")
        return 1
    print("test_known_set_surface: ALL OK — a surface in the known set never resolves to an "
          "unknown lemma, and no rule reaches a record the token does not name")
    return 0


if __name__ == "__main__":
    sys.exit(main())
