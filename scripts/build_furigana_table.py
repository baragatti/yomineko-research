#!/usr/bin/env python3
"""Derive the missing `reading` attribute for lesson-body `<jp>` spans — mechanically, or not at all.

THE DEFECT (PENDING.md A7, third bullet). 875 `<jp>` spans in the exported lesson bodies contain
kanji and carry no `reading`. `<jp reading="…">` is the only pronunciation a learner is given for a
bare Japanese span in prose, so those 875 are silent. `validate_lesson_bodies.py` could not see them
either: its `JPTAG` regex requires the attribute to be present before it checks anything, so an
EMPTY reading was a hard failure while a MISSING one was invisible.

THE RULES, in order. A span gets a reading only if a registry says so; nothing here is authored.

  rule i   the span text is a vocabulary headword (or an alternate form) that the lesson's own
           `cumulative_known_set` already contains, and exactly one such record exists -> that
           record's `kana`. This is the strongest signal available: the lesson has taught that
           word, so that is the word it is printing.
  rule ii  otherwise SudachiPy (mode C) reads the span; the reading is assembled token by token,
           katakana-to-hiragana, and then VERIFIED:
             * a token whose surface carries no kanji contributes its SURFACE, not its reading, so
               genuine katakana survives (アメリカ人 -> アメリカじん, never あめりかじん) and a
               placeholder 〜 stays a 〜 rather than becoming きごう;
             * a kanji-bearing token whose surface names registry records must name exactly ONE
               reading among them, and Sudachi must agree with it. Two records spelled the same
               and read differently is the homograph case, and out of context Sudachi is guessing;
             * a LONE kanji that names no record at all is only accepted when its dictionary form
               names one; otherwise the character's own reading list decides, and a character with
               more than one reading is refused for the same reason.

  Then, whatever the rule: the reading must be kana-only by `validate_lesson_bodies.READING_OK`, it
  must cover the hiragana literally written in the base (the subsequence rule the gate applies), and
  it must ALIGN against the Layer-A kanji registry through `scripts/export/kanji_align.py` — the
  same whole-word alignment that regrouped 4,591 compounds, so a reading that credits a kanji with a
  sound it does not make is refused rather than shipped.

  residue  everything else, written into the table with BOTH candidates and the reason, and NOT
           applied. The gate is ratcheted at the residue count, so it can only shrink.

Two exclusions worth naming. A character the kanji registry does not carry is a radical or a
component in this corpus (亻 氵 宀 艹 頁 罒 扌), not a word: the body prints it inside a
decomposition explanation and there is nothing to verify a reading against, so it is residue by
construction. And `<vocab ref>` chips are EMPTY elements in this schema, so no `<jp>` span can sit
inside one; the "never annotate a chip that already shows its reading" rule has nothing to bite on,
which the table records as a measured zero rather than an assumption.

Deterministic. Requires the project venv (SudachiPy + jaconv).
Usage: build_furigana_table.py [--check]
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

import jaconv                                          # noqa: E402
from sudachipy import dictionary, tokenizer            # noqa: E402
from export import kanji_align                         # noqa: E402

TABLE = ROOT / "research" / "derived" / "repairs" / "lesson_furigana.json"

JP_ANY = re.compile(r"<jp\b([^>]*)>(.*?)</jp>", re.S)
ATTR = re.compile(r'(\w+)="([^"]*)"')
KANJI = re.compile(r"[一-鿿々〆]")
HIRA = re.compile(r"[ぁ-ん]")
KATA = re.compile(r"[ァ-ヴー]+")
# mirrors validate_lesson_bodies.READING_OK — the same characters a reading may contain
READING_OK = re.compile(r"[ぁ-ゟ゠-ヿ、。・？！～〜「」『』（）()… 　]")
TAGS = re.compile(r"<[^>]+>")


def registries(root: Path):
    by_head: dict[str, list[dict]] = collections.defaultdict(list)
    for f in sorted((root / "corpus" / "vocab").glob("*.json")):
        for v in json.loads(f.read_text(encoding="utf-8")):
            by_head[v["headword"]].append(v)
            for fm in v.get("forms") or []:
                if fm.get("form") and fm["form"] != v["headword"]:
                    by_head[fm["form"]].append(v)
    kread: dict[str, set[str]] = collections.defaultdict(set)
    for f in sorted((root / "corpus" / "kanji").glob("*.json")):
        for k in json.loads(f.read_text(encoding="utf-8")):
            for r in k.get("readings") or []:
                if (r.get("type") or "").lower() == "nanori":
                    continue
                b = kanji_align.bare(r.get("reading"))
                if b:
                    kread[k["character"]].add(b)
    return by_head, kread


def missing_kana(reading: str, text: str) -> str:
    it = iter(reading)
    for ch in HIRA.findall(text):
        if ch not in it:
            return ch
    return ""


def restore_katakana(surface: str, reading: str) -> str | None:
    """Sudachi hands a whole token back in katakana, so a base that CONTAINS katakana comes out
    all-hiragana. Put the literal runs back where the base writes them; refuse if a run cannot be
    located, because then the mapping is a guess."""
    for run in KATA.findall(surface):
        if run in reading:
            continue
        h = jaconv.kata2hira(run)
        i = reading.find(h)
        if i < 0:
            return None
        reading = reading[:i] + run + reading[i + len(h):]
    return reading


class Deriver:
    def __init__(self, root: Path) -> None:
        self.by_head, self.kread = registries(root)
        self.aligner = kanji_align.default()
        self.tk = dictionary.Dictionary().create()
        self.mode = tokenizer.Tokenizer.SplitMode.C

    def unknown_kanji(self, surface: str) -> list[str]:
        return [c for c in surface if KANJI.match(c) and c not in self.kread]

    def one_kana(self, surface: str) -> tuple[str | None, int]:
        recs = self.by_head.get(surface)
        if not recs:
            return None, 0
        ks = {v["kana"] for v in recs}
        return (next(iter(ks)) if len(ks) == 1 else None), len(ks)

    def sudachi(self, surface: str) -> tuple[str | None, str | None]:
        try:
            toks = self.tk.tokenize(surface, self.mode)
        except Exception as e:                            # noqa: BLE001
            return None, f"SudachiPy could not tokenize the span ({e})"
        parts = []
        for t in toks:
            s = t.surface()
            if not KANJI.search(s):
                parts.append(s)
                continue
            r = t.reading_form()
            if not r:
                return None, f"Sudachi returns no reading for the token {s}"
            r = jaconv.kata2hira(r)
            k1, n = self.one_kana(s)
            if n > 1:
                return None, f"{s} names {n} registry records with different readings"
            if n == 1 and k1 != r:
                return None, f"Sudachi reads {s} as {r}, the registry says {k1}"
            if n == 0:
                _, n2 = self.one_kana(t.dictionary_form())
                if n2 > 1:
                    return None, (f"the dictionary form {t.dictionary_form()} names {n2} registry "
                                  f"records with different readings")
                if len(s) == 1 and n2 == 0:
                    rs = self.kread.get(s, set())
                    if len(rs) != 1:
                        return None, (f"the lone kanji {s} has {len(rs)} registry readings; out of "
                                      f"context Sudachi cannot pick one")
                    if r not in rs:
                        return None, f"Sudachi reads {s} as {r}, which is not a registry reading"
            parts.append(r)
        return "".join(parts), None

    def derive(self, surface: str, known: set[str]) -> dict:
        """-> {reading, rule} or {reading: None, why, candidate_registry, candidate_sudachi}."""
        unk = self.unknown_kanji(surface)
        if unk:
            return {"reading": None, "candidate_registry": None, "candidate_sudachi": None,
                    "why": (f"{'/'.join(unk)} is not in the kanji registry — in this corpus it is a "
                            f"radical or component printed inside a decomposition, not a word")}
        cands = [v for v in self.by_head.get(surface, []) if v["slug"] in known]
        ks = {v["kana"] for v in cands}
        r_i = next(iter(ks)) if len(ks) == 1 else None
        r_ii, why_ii = self.sudachi(surface)
        reading = rule = why = None
        if r_i:
            if r_ii and r_ii != r_i:
                why = f"rule i (the lesson's own registry record) says {r_i}, Sudachi says {r_ii}"
            else:
                reading, rule = r_i, "i"
        elif len(ks) > 1:
            why = f"the lesson knows {len(ks)} records spelled {surface} ({'/'.join(sorted(ks))})"
        elif r_ii:
            reading, rule = r_ii, "ii"
        else:
            why = why_ii
        if reading and KATA.search(surface):
            fixed = restore_katakana(surface, reading)
            if fixed is None:
                reading, why = None, f"the katakana of {surface} is not traceable in {reading}"
            else:
                reading = fixed
        if reading:
            bad = [c for c in reading if not READING_OK.match(c)]
            if bad:
                reading, why = None, f"the derived reading is not kana-only ({''.join(sorted(set(bad)))})"
            elif missing_kana(reading, surface):
                reading, why = None, f"{reading} does not cover the kana written in {surface}"
            else:
                try:
                    ok = self.aligner.align(surface, reading) is not None
                except Exception:                          # noqa: BLE001
                    ok = False
                if not ok:
                    reading, why = None, (f"{reading} does not align against the Layer-A kanji "
                                          f"registry for {surface}")
        if reading:
            return {"reading": reading, "rule": rule}
        return {"reading": None, "why": why, "candidate_registry": r_i, "candidate_sudachi": r_ii}


def prior_scope() -> dict[tuple[str, str], int]:
    """(lesson, surface) -> occurrences, remembered from the tracked table itself.

    THE SCOPE HAS TO BE REMEMBERED. This table's input is "spans that carry kanji and no reading",
    and applying it REMOVES rows from that input: run the builder again afterwards and the annotated
    spans are no longer bare, so the table could not re-derive itself and no gate could check it
    against the data. The scope is therefore the union of what is bare NOW and what this table
    already records. A pair enters only by having been bare once — which git history proves — so the
    memo widens the scope by exactly nothing, and the derivation itself never reads the current
    attribute: what a row says is what the registries say today."""
    if not TABLE.exists():
        return {}
    doc = json.loads(TABLE.read_text(encoding="utf-8"))
    out = {(r["lesson"], r["surface"]): r["occurrences"] for r in doc.get("rows", [])}
    for r in doc.get("residue", []):
        out.setdefault((r["lesson"], r["surface"]), r["occurrences"])
    return out


def build(root: Path) -> dict:
    dv = Deriver(root)
    rows: list[dict] = []
    residue: list[dict] = []
    spans_total = chips = 0
    memo = prior_scope()
    for f in sorted((root / "course").rglob("lesson-*.json")):
        d = json.loads(f.read_text(encoding="utf-8"))
        lid = d["id"]
        known = set((d.get("cumulative_known_set") or {}).get("vocab") or [])
        body = d.get("body") or ""
        chips += len(re.findall(r"<vocab\b[^>]*>[^<]", body))   # a chip with content: 0 by schema
        counts: collections.Counter = collections.Counter()
        for m in JP_ANY.finditer(body):
            if "reading" in dict(ATTR.findall(m.group(1))):
                continue
            plain = TAGS.sub("", m.group(2))
            if KANJI.search(plain):
                counts[plain] += 1
        for (ml, ms), mn in memo.items():                   # annotated by an earlier run of the apply
            if ml == lid and ms not in counts:
                counts[ms] = mn
        for surface, n in sorted(counts.items()):
            spans_total += n
            got = dv.derive(surface, known)
            if got["reading"]:
                rows.append({"lesson": lid, "file": f"{f.parent.name}/{f.name}",
                             "surface": surface, "reading": got["reading"],
                             "rule": got["rule"], "occurrences": n})
            else:
                residue.append({"lesson": lid, "surface": surface, "occurrences": n,
                                "candidate_registry": got.get("candidate_registry"),
                                "candidate_sudachi": got.get("candidate_sudachi"),
                                "why": got.get("why")})
    written = sum(r["occurrences"] for r in rows)
    left = sum(r["occurrences"] for r in residue)
    return {
        "generated_by": "scripts/build_furigana_table.py",
        "what_this_is": (
            "Every lesson-body <jp> span that carries kanji and no `reading`, split into the ones a "
            "registry can settle (rows, applied) and the ones it cannot (residue, listed with both "
            "candidates and NOT applied). Keyed by (lesson, surface): one surface has one reading "
            "inside one lesson, which is also what makes the apply idempotent and exact-match."),
        "applied_by": "scripts/apply_lesson_furigana.py",
        "counts": {"spans_without_reading": spans_total,
                   "written": written, "rule_i": sum(r["occurrences"] for r in rows if r["rule"] == "i"),
                   "rule_ii": sum(r["occurrences"] for r in rows if r["rule"] == "ii"),
                   "residue": left,
                   "distinct_rows": len(rows), "distinct_residue": len(residue),
                   "lessons_touched": len({r["lesson"] for r in rows}),
                   "jp_spans_inside_vocab_chips": chips},
        "row_count": len(rows),
        "rows": rows,
        "residue": residue,
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args()
    doc = build(ROOT)
    text = json.dumps(doc, ensure_ascii=False, indent=1) + "\n"
    same = TABLE.exists() and TABLE.read_text(encoding="utf-8") == text
    print(json.dumps(doc["counts"], ensure_ascii=False))
    if args.check:
        print("table is current" if same else "TABLE IS STALE — re-run without --check")
        return 0 if same else 1
    if not same:
        TABLE.write_text(text, encoding="utf-8")
    print("wrote " + str(TABLE.relative_to(ROOT)) if not same else "table unchanged")
    return 0


if __name__ == "__main__":
    sys.exit(main())
