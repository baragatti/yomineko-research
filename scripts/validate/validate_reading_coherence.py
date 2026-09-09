#!/usr/bin/env python3
"""W15 — is a reading box a TEXT, or a pile of sentences?

WHY THIS EXISTS
---------------
`validate_readings.py` proves a box is READABLE (every kanji and content word already taught). It
says nothing about whether the sentences belong together, which is how
`read:n5-adjetivos-04-01` shipped as "どこに行くところですか。ありがとうございます！" — two unrelated
Tatoeba sentences concatenated under a heading that calls them a Leitura. APP_PLAN W15 promises
"a coherence check (one topic, tense/pronoun continuity) becomes a validator". This is it.

WHAT IT CAN AND CANNOT DECIDE
-----------------------------
Coherence is not decidable from text. What IS decidable is a set of surface signals, and this
validator is careful about which side of that line each check falls on:

  HARD (gates the build — no judgement involved)
    H1  an authored W15 passage has 3-6 sentences               — the campaign's own contract
    H2  the token stream re-concatenates to `jp`                 — string equality
    H3  `uses` is inside the gating lesson's cumulative_known_set — set containment (re-asserted
        here so the coherence gate is self-contained; `validate_readings.py` owns the same rule)
    H4  a NON-DIALOGUE passage does not mix first-person pronouns (私 / 僕 / 俺 / あたし …)

  ADVISORY (counted against a frozen baseline; may shrink, never grow)
    A1  a sentence that shares no content word and no kanji with anything before it (topic drift)
    A2  more than one past <-> non-past switch inside one passage (tense drift)
    A3  a passage mixing です・ます and plain sentence endings (register drift)

The three advisory checks are heuristics over surface morphology. A quoted line, an embedded
relative clause, a deliberate flashback or a narrator aside can each make any of them fire on text
that is perfectly coherent — so they FLAG, they do not fail. H4 is hard only when the passage
carries no 「」 quotation: two speakers legitimately using different pronouns is exactly the case a
mechanical rule cannot judge, so a dialogue drops to advisory.

PLANT PROOF
-----------
`--selftest` builds a throwaway tree containing a copy of THIS FILE and a small corpus/course, plants
one violation per check, and asserts each is caught and that the clean control passes. The copy
matters: a validator that resolves ROOT from `__file__` and is run from the repo reads the repo's
own data and reports green no matter what the fixture says.

Reads the EXPORTED JSON only. Exit 1 on a hard failure or an advisory count above its baseline.
Usage: validate_reading_coherence.py [--record] [--selftest] [--root PATH]
"""
from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
HERE = Path(__file__).resolve()
DEFAULT_ROOT = HERE.parents[2]
BASELINE = HERE.parent / "reading_coherence_baseline.json"

AUTHORED_SOURCE = "authored:w15-passages"
TERM, CLOSE = "。！？!?", "」』）)"
PRONOUNS = ("私", "わたし", "わたくし", "僕", "ぼく", "俺", "おれ", "あたし")
POLITE_LEMMAS = {"ます", "です", "ございます", "くださる"}
CONTENT_POS = {"名詞", "動詞", "形容詞", "形状詞", "副詞", "代名詞"}
# Words so common that sharing one is no evidence of a shared topic. Keeping them in would make A1
# unfireable, which is the same as not having the check.
TOPIC_STOP = {"する", "ある", "いる", "なる", "こと", "もの", "の", "ん", "それ", "これ", "あれ",
              "ここ", "そこ", "そう", "こう", "とても", "です", "ます", "いう", "言う", "人",
              "日", "今日", "時", "とき", "私", "わたし", "僕", "できる", "行く", "来る", "みる",
              "見る", "思う", "很", "ない", "よい", "いい"}
KANJI = re.compile(r"[一-鿿]")


def sentences(jp: str) -> list[str]:
    """Split on a terminator, taking any closing quote with it — a dialogue terminates every line
    inside 「…。」, so a plain split on 。 makes a six-line exchange look like one sentence."""
    out, start, i = [], 0, 0
    while i < len(jp):
        if jp[i] in TERM:
            j = i + 1
            while j < len(jp) and jp[j] in CLOSE:
                j += 1
            out.append(jp[start:j])
            start = i = j
        else:
            i += 1
    if jp[start:].strip():
        out.append(jp[start:])
    return [s for s in out if s.strip()]


class Analyzer:
    def __init__(self) -> None:
        from sudachipy import dictionary, tokenizer  # imported here so --selftest can report why
        self.tok = dictionary.Dictionary(dict="full").create()
        self.C = tokenizer.Tokenizer.SplitMode.C

    def parse(self, s: str) -> list:
        return list(self.tok.tokenize(s, self.C))

    def content(self, s: str) -> set[str]:
        out = set()
        for m in self.parse(s):
            if m.part_of_speech()[0] in CONTENT_POS:
                lemma = m.dictionary_form()
                if lemma not in TOPIC_STOP and len(lemma) > 1 or KANJI.search(lemma or ""):
                    out.add(lemma)
        return {x for x in out if x not in TOPIC_STOP}

    def tail(self, s: str) -> list:
        ms = [m for m in self.parse(s) if m.part_of_speech()[0] not in ("補助記号", "空白", "記号")]
        return ms[-3:]

    def polite(self, s: str) -> bool:
        return any(m.dictionary_form() in POLITE_LEMMAS or m.surface() == "ください"
                   for m in self.tail(s))

    def past(self, s: str) -> bool:
        return any(m.dictionary_form() == "た" for m in self.tail(s))


def known_sets(root: Path) -> dict:
    known = {}
    for lf in root.glob("course/*/topic-*/lesson-*.json"):
        d = json.loads(lf.read_text(encoding="utf-8"))
        cks = d.get("cumulative_known_set") or {}
        known[d["id"]] = ({x.split(":", 1)[1] for x in cks.get("kanji") or []},
                          set(cks.get("vocab") or []))
    return known


def run(root: Path, quiet: bool = False) -> tuple[list[str], dict, int]:
    a = Analyzer()
    known = known_sets(root)
    hard: list[str] = []
    adv = {"topic_drift_sentences": 0, "tense_drift_passages": 0, "register_drift_passages": 0,
           "pronoun_drift_dialogues": 0}
    total = 0
    flagged: list[str] = []
    for rf in sorted((root / "corpus" / "readings").glob("n*.json")):
        for r in json.loads(rf.read_text(encoding="utf-8")):
            total += 1
            slug, lesson = r["slug"], r.get("gated_to_lesson")
            jp = r.get("jp") or ""
            sents = sentences(jp)
            authored = r.get("source") == AUTHORED_SOURCE

            # H1 — against the box's OWN segmentation (the authoring unit), not a re-split of `jp`
            units = r.get("sentences") or sents
            if "".join(units) != jp:
                hard.append(f"H1 {slug}: `sentences` does not re-concatenate to `jp`")
            elif authored and not 3 <= len(units) <= 6:
                hard.append(f"H1 {slug}: {len(units)} sentences (an authored passage is 3-6)")
            # H2
            joined = "".join(t.get("s", "") for t in (r.get("tokens") or []))
            if joined != jp:
                hard.append(f"H2 {slug}: tokens do not re-concatenate to jp "
                            f"({len(joined)} vs {len(jp)} chars)")
            # H3
            kk, vv = known.get(lesson, (set(), set()))
            if lesson not in known:
                hard.append(f"H3 {slug}: gated_to_lesson {lesson!r} is not an exported lesson")
            else:
                out_k = [k for k in (r.get("uses") or {}).get("kanji", []) if k not in kk]
                out_v = [v for v in (r.get("uses") or {}).get("vocab", []) if v not in vv]
                if out_k or out_v:
                    hard.append(f"H3 {slug}: {len(out_k)} kanji + {len(out_v)} vocab outside "
                                f"{lesson}'s known set ({(out_k + out_v)[:3]})")
            # H4 / pronoun
            used = [p for p in PRONOUNS if p in jp]
            dialogue = "「" in jp
            if len(used) > 1:
                if dialogue:
                    adv["pronoun_drift_dialogues"] += 1
                    flagged.append(f"A4 {slug}: dialogue mixes {used}")
                else:
                    hard.append(f"H4 {slug}: one narrator, {len(used)} first-person pronouns {used}")
            # A1 topic
            seen: set[str] = set()
            for i, s in enumerate(sents):
                c = a.content(s)
                if i and not (c & seen):
                    adv["topic_drift_sentences"] += 1
                    flagged.append(f"A1 {slug}#{i + 1}: shares nothing with what came before "
                                   f"({s[:24]})")
                seen |= c | set(KANJI.findall(s))
            # A2 tense
            switches = sum(1 for i in range(1, len(sents)) if a.past(sents[i]) != a.past(sents[i - 1]))
            if switches > 1:
                adv["tense_drift_passages"] += 1
                flagged.append(f"A2 {slug}: {switches} past/non-past switches")
            # A3 register
            pol = {a.polite(s) for s in sents}
            if len(pol) > 1:
                adv["register_drift_passages"] += 1
                flagged.append(f"A3 {slug}: mixes です・ます and plain endings")

    if not quiet:
        for h in hard[:20]:
            print(f"  FAIL {h}")
        if len(hard) > 20:
            print(f"  … and {len(hard) - 20} more hard failures")
        for f in flagged[:12]:
            print(f"  flag {f}")
        if len(flagged) > 12:
            print(f"  … and {len(flagged) - 12} more flags")
    return hard, adv, total


NL_FAIL = chr(10) + "  FAIL "
NL_FLAG = chr(10) + "  flag "


def selftest() -> int:
    """Copy this validator into a throwaway tree with its own corpus and course, plant one violation
    per check, and prove each is caught and the control is clean."""
    ok = True
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        (root / "scripts" / "validate").mkdir(parents=True)
        shutil.copy2(HERE, root / "scripts" / "validate" / HERE.name)
        (root / "corpus" / "readings").mkdir(parents=True)
        (root / "course" / "n5" / "topic-01-x").mkdir(parents=True)
        (root / "course" / "n5" / "topic-01-x" / "lesson-01.json").write_text(json.dumps({
            "id": "les:x-01",
            "cumulative_known_set": {"kanji": ["kanji:本", "kanji:私", "kanji:僕"],
                                     "vocab": ["vocab:1"]},
        }, ensure_ascii=False), encoding="utf-8")

        def box(slug: str, jp: str, **over) -> dict:
            toks = over.pop("tokens", None)
            d = {"slug": slug, "level": "n5", "gated_to_lesson": "les:x-01", "jp": jp,
                 "tokens": toks if toks is not None else [{"s": jp, "r": "", "ro": "", "pos": "noun"}],
                 "translation": {"pt-BR": "x", "en": "x"}, "length_band": "paragraph",
                 "uses": {"kanji": [], "vocab": []}, "source_slugs": [],
                 "ai_generated": True, "needs_review": True, "layer": "C",
                 "source": AUTHORED_SOURCE}
            d.update(over)
            return d

        clean = box("read:ok-01", "私は本を読みます。その本はとてもおもしろいです。"
                                 "私は毎日その本を読みます。")
        plants = {
            "H1": box("read:h1-01", "私は本を読みます。その本はおもしろいです。"),
            "H2": box("read:h2-01", "私は本を読みます。その本はおもしろいです。私は読みます。",
                      tokens=[{"s": "ちがう", "r": "", "ro": "", "pos": "noun"}]),
            "H3": box("read:h3-01", "私は本を読みます。その本はおもしろいです。私は読みます。",
                      uses={"kanji": ["kanji:海"], "vocab": []}),
            "H4": box("read:h4-01", "私は本を読みます。僕はその本が好きです。私は毎日読みます。"),
            "A1": box("read:a1-01", "私は本を読みます。その本はおもしろいです。"
                                    "きのう電車で駅まで走りました。"),
            "A2": box("read:a2-01", "私は本を読みました。その本はおもしろいです。"
                                    "私は毎日その本を読みました。"),
            "A3": box("read:a3-01", "私は本を読みます。その本はおもしろい。私は毎日その本を読みます。"),
        }
        for name, planted in list(plants.items()) + [("CONTROL", None)]:
            items = [clean] + ([planted] if planted else [])
            (root / "corpus" / "readings" / "n5.json").write_text(
                json.dumps(items, ensure_ascii=False), encoding="utf-8")
            p = subprocess.run([sys.executable, str(root / "scripts" / "validate" / HERE.name),
                                "--no-baseline"], capture_output=True, text=True,
                               encoding="utf-8", errors="replace")
            out = chr(10) + (p.stdout or "") + (p.stderr or "")
            if name == "CONTROL":
                good = p.returncode == 0 and NL_FAIL not in out and NL_FLAG not in out
            elif name.startswith("H"):
                good = p.returncode != 0 and (NL_FAIL + name + " ") in out
            else:
                good = (NL_FLAG + name + " ") in out
            print(f"  [{'PASS' if good else 'FAIL'}] plant {name}")
            if not good:
                ok = False
                print("    " + out.strip().replace("\n", "\n    ")[:900])
    print(f"\nvalidate_reading_coherence --selftest: {'ALL PLANTS CAUGHT' if ok else 'PLANT ESCAPED'}")
    return 0 if ok else 1


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=str(DEFAULT_ROOT))
    ap.add_argument("--record", action="store_true", help="freeze the advisory counts as the baseline")
    ap.add_argument("--no-baseline", action="store_true", help="report advisory counts, do not ratchet")
    ap.add_argument("--selftest", action="store_true")
    args = ap.parse_args()
    if args.selftest:
        return selftest()

    root = Path(args.root)
    if not (root / "corpus" / "readings").exists():
        print("validate_reading_coherence: no exported readings (nothing to check)")
        return 0
    hard, adv, total = run(root)

    if args.record:
        BASELINE.write_text(json.dumps({
            "what": "advisory coherence flags; may shrink, never grow",
            "why_these_are_not_hard": (
                "A1 counts a sentence sharing no content lemma and no kanji with anything before "
                "it. Japanese drops the subject and the object once they are established, so a "
                "perfectly coherent line like 'また後で電話するね。' shares nothing lexically with "
                "its own paragraph. A2 counts past/non-past switches: a passage that narrates "
                "yesterday and then comments on today legitimately switches. A3 counts mixed "
                "です・ます and plain endings, which a quotation inside a polite text produces on "
                "purpose. Each is a REVIEW SIGNAL for the teacher pass, not a quality verdict."),
            "measured_on": ("the W15 apply (282 authored passages + 4 held). The same validator "
                            "over the pre-apply concatenations scored topic 814 / tense 86 / "
                            "register 201 with 3 hard failures."),
            "counts": adv}, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
        print(f"recorded baseline: {adv}")
        return 0
    grew = []
    if not args.no_baseline and BASELINE.exists():
        base = json.loads(BASELINE.read_text(encoding="utf-8"))["counts"]
        for k, v in adv.items():
            was = base.get(k)
            if was is None:
                grew.append(f"{k}: no baseline entry — record one with a reason")
            elif v > was:
                grew.append(f"{k}: {v} > baseline {was}")
    print(f"\nvalidate_reading_coherence: {total} readings | hard {len(hard)} FAIL | "
          f"advisory {adv}")
    for g in grew:
        print(f"  RATCHET {g}")
    return 1 if (hard or grew) else 0


if __name__ == "__main__":
    sys.exit(main())
