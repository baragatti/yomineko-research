#!/usr/bin/env python3
"""P5/P7 — the validation suite (spec §7; rubric hard gates G1–G3).

Validates persisted dissected sentences against the dictionaries + provenance rules:
  §7.1 reading/lemma integrity   — token lemmas exist in JMdict (common subset → warn if not);
                                   every kanji in the sentence is in our KANJIDIC2 inventory.
  §7.2 tokenization agreement    — re-derive the SudachiPy skeleton from sentence.jp and confirm
                                   the stored tokens' surface/lemma/reading/pos were not altered.
  §7.5 provenance completeness   — source + jp_source present; ai_generated ⇒ needs_review;
                                   Layer-B/C carry needs_review where required.
  §7.6 level consistency         — sentence.level ≥ max(level of linked vocab/kanji).
  Layer-B completeness (full tier) — pt + pt_literal + structure_explanation_pt present; every
                                   content token has gloss_pt; every particle has explanation_pt.

Returns issues per sentence (severity error|warn). CLI validates all and writes a section to
reports/validation.md. Run with venv python.
"""
from __future__ import annotations

import json
import sqlite3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "ingest"))
sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
from dissect import Dissector  # noqa: E402
from i18n_text import get_text  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
DB = ROOT / "db" / "corpus.sqlite"
VALID = ROOT / "reports" / "validation.md"
LEVEL_ORDER = {None: 0, "pre-n5": 1, "n5": 2, "n4": 3, "n3": 4, "n2": 5, "n1": 6}
CONTENT_POS = {"名詞", "動詞", "形容詞", "形状詞", "副詞", "代名詞", "連体詞", "接続詞", "感動詞"}


def validate_sentence(con: sqlite3.Connection, diss: Dissector, sid: int) -> list[tuple[str, str]]:
    issues: list[tuple[str, str]] = []
    s = con.execute("SELECT * FROM sentence WHERE id=?", (sid,)).fetchone()
    cols = [d[0] for d in con.execute("SELECT * FROM sentence WHERE id=?", (sid,)).description]
    s = dict(zip(cols, s))
    jp = s["jp"]

    # §7.5 provenance
    if not s["source"]:
        issues.append(("error", "missing source"))
    if not s["jp_source"]:
        issues.append(("error", "missing jp_source"))
    if s["ai_generated"] and not s["needs_review"]:
        issues.append(("error", "ai_generated but needs_review=0 (§1.2)"))

    # §7.1 kanji inventory
    for ch in jp:
        if ("一" <= ch <= "鿿") and not con.execute(
                "SELECT 1 FROM kanji WHERE character=?", (ch,)).fetchone():
            issues.append(("warn", f"kanji {ch} not in inventory"))

    # stored tokens (mode C)
    toks = con.execute(
        "SELECT id,position,surface,lemma,reading,pos_coarse,pos_fine,vocab_id FROM token "
        "WHERE sentence_id=? AND split_mode='C' ORDER BY position", (sid,)).fetchall()

    # §7.2 tokenization agreement (re-derive, compare)
    skel = diss.skeleton(jp)
    ref = [(t["surface"], t["lemma"], t["reading"], t["pos_coarse"]) for t in skel["tokens"]]
    got = [(t[2], t[3], t[4], t[5]) for t in toks]
    if got != ref:
        issues.append(("error", f"tokenization mismatch vs analyzer (stored {len(got)} vs {len(ref)})"))

    # §7.1 lemma existence (JMdict-common subset → warn) + Layer-B token gloss completeness (localized_text)
    for tid, pos, surface, lemma, reading, pc, pf, vid in toks:
        if pc in CONTENT_POS:
            if lemma and not con.execute(
                    "SELECT 1 FROM raw_jmdict_form WHERE form=? LIMIT 1", (lemma,)).fetchone():
                issues.append(("warn", f"lemma {lemma} not in JMdict-common (may be in full)"))
            if s["dissection_tier"] == "full" and not get_text(con, "token", tid, "gloss"):
                issues.append(("error", f"content token '{surface}' missing gloss (Layer B)"))

    # particles have explanation (full tier)
    if s["dissection_tier"] == "full":
        for pid, particle in con.execute("SELECT id,particle FROM particle WHERE sentence_id=?", (sid,)):
            if not get_text(con, "particle", pid, "explanation"):
                issues.append(("error", f"particle {particle} missing explanation"))
        for field in ("translation", "translation_literal", "structure_explanation"):
            if not get_text(con, "sentence", sid, field):
                issues.append(("error", f"missing {field} (full tier)"))

    # §7.6 level consistency
    comp_levels = [r[0] for r in con.execute(
        "SELECT v.level FROM sentence_vocab sv JOIN vocab v ON v.id=sv.vocab_id WHERE sv.sentence_id=?",
        (sid,))]
    comp_levels += [r[0] for r in con.execute(
        "SELECT k.level FROM sentence_kanji sk JOIN kanji k ON k.id=sk.kanji_id WHERE sk.sentence_id=?",
        (sid,))]
    maxlvl = max([LEVEL_ORDER.get(x, 0) for x in comp_levels], default=0)
    if LEVEL_ORDER.get(s["level"], 0) < maxlvl:
        issues.append(("warn", f"sentence level {s['level']} below max component level"))

    return issues


def main() -> int:
    con = sqlite3.connect(DB)
    n = con.execute("SELECT COUNT(*) FROM sentence").fetchone()[0]
    if n == 0:
        print("no sentences to validate yet.")
        return 0
    diss = Dissector()
    all_issues = {}
    errors = warns = 0
    for (sid,) in con.execute("SELECT id FROM sentence ORDER BY id"):
        iss = validate_sentence(con, diss, sid)
        if iss:
            all_issues[sid] = iss
            errors += sum(1 for s, _ in iss if s == "error")
            warns += sum(1 for s, _ in iss if s == "warn")
    print(f"validated {n} sentences: {errors} errors, {warns} warns, "
          f"{n - len(all_issues)} clean")
    # append section to validation.md
    lines = ["", "---", "## Sentence validation (§7)", "",
             f"Validated {n} sentences — **{errors} errors, {warns} warnings**, "
             f"{n - len(all_issues)} clean."]
    for sid, iss in list(all_issues.items())[:60]:
        jp = con.execute("SELECT jp FROM sentence WHERE id=?", (sid,)).fetchone()[0]
        lines.append(f"- sentence {sid} `{jp}`:")
        for sev, msg in iss:
            lines.append(f"  - **{sev}**: {msg}")
    prev = VALID.read_text(encoding="utf-8") if VALID.exists() else "# Validation report\n"
    VALID.write_text(prev + "\n".join(lines) + "\n", encoding="utf-8")
    con.close()
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
