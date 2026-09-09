#!/usr/bin/env python3
"""Gate: the homograph resolver still reads the reading the lesson prints beside the chip.

WHY THIS EXISTS

A6 (W11a). Four lesson bodies shipped a vocabulary card whose reading and gloss contradicted the
sentence printed next to it — «かね» captioned "(きん) = 'ouro (metal)'", «ひん» captioned
"(しな) = 'artigo, mercadoria'", «え» captioned "(がら): 'estampa, padrão'", «かみ» captioned
"(じょう) = 'do ponto de vista de'". Every one of them was a homograph the exporter had to guess
at, and in every one the lesson had already written the answer down: the kana inside `<jp>…</jp>`
immediately after the chip. `scripts/export/vocab_identity.py` consulted the sibling filter, the
lesson level, the placement topic and the sentence bank's frequency counts, and never that.

Worse, frequency was actively wrong here and looked authoritative: the bank counts 金 as かね 46
times (from お金) and 品 as ひん 5 times (from 作品/製品/商品), so the two rows the review file
labelled "settled by frequency" were exactly the two that pointed at the wrong record.

So the rule went into the resolver, and this file is what stops it rotting. It is a UNIT test with a
fixture DB, not a tree validator: the rule is a property of the resolver, and asserting it against
the live corpus would only re-measure data that the ruling table already pins.

WHAT IS ASSERTED (each numbered check is one way the rule can break)

  1  the printed reading picks the record that reads that way, even when frequency says otherwise
  2  ... and with the reading withheld the same call returns the frequency answer, so check 1 is
     measuring the rule and not some other tier that happened to agree
  3  ABSTAIN when two candidates share the printed reading (位 names three records, two read くらい)
  4  ABSTAIN when the printed reading is not any candidate's reading
  5  PER-OCCURRENCE, not per-lesson: 柄 is taught as え and as がら, and one lesson asking for both
     must get both — the per-(headword, lesson) decision cache must not swallow the second
  5b ... and the ordering that makes that possible: a guess CACHED by an earlier, unannotated chip
     in the same lesson must not shadow the reading (nor, 5c, a ruling)
  6  an owner RULING outranks every heuristic
  7  a ruling that CONTRADICTS the printed reading is a hard error, never a silent override
  8  the extractor accepts the shape the bodies actually use — chip, punctuation-only <text>, bare
     <jp>kana</jp> — and REFUSES an example compound such as `<jp reading="…">法律上</jp>` (which
     les:n3-relato-04 really does print, a few words after the 上 chip) and a <jp> separated from
     the chip by prose. Note honestly which half of the pattern does that work: the KANA-ONLY
     content class is what refuses 法律上. Loosening `<jp>` to `<jp …>` was measured against all 322
     lesson bodies and changes no resolution today, so refusing attributes is a deliberate margin
     rather than a live constraint — it keeps a furigana-annotated EXPRESSION from ever being read
     as a gloss of the chip beside it.
  9  ... and does not carry a hint across to a later, unannotated chip in the same body

PLANT PROOF (the entry requirement, scripts/validate/README.md)

Run 2026-09-09 on a COPIED tree — `scripts/{validate,export,ingest,dbtarget.py}` plus the two inputs
those imports read (`design/unlock_enums.json`, `research/derived/repairs/homograph_rulings.json`) —
with `--root` pointed at the copy, so the copy is what is under test. Control run on the untouched
copy: 13 checks PASS. Then one plant at a time, each reverted before the next:

  A  reading tier disabled (`if by_reading:` -> `if False:`)
     -> 4 FAIL: 1 printed-reading-beats-frequency (got vocab:2648780 (frequency)), 1b 金-きん,
        5 per-occurrence, 5b reading-beats-the-cache
  B  the uniqueness guard removed (`if len(hit) == 1` -> `if hit`)
     -> 1 FAIL: 3 abstain-on-ambiguous-reading — it picked a record off くらい, which two records read
  C  the per-lesson decision cache consulted BEFORE the ruling and reading tiers
     -> 1 FAIL: 5b reading-beats-the-cache — "a cached vocab:1508290 (unresolved) shadowed the
        printed がら". Check 5 alone does NOT catch this (nothing has cached anything yet when it
        runs), which is why 5b exists.
  D  the contradiction guard removed (`if by_reading and by_reading != chosen` -> `if False and …`)
     -> 1 FAIL: 7 contradicting-ruling-is-loud

  E  `<jp>` loosened to `<jp[^>]*>` -> NOT CAUGHT, and recorded here rather than papered over. The
     kana-only content class already refuses `<jp reading="ほうりつじょう">法律上</jp>`, and the same
     loosening measured over all 322 lesson bodies produces zero extra hits on an ambiguous headword,
     so today the attribute restriction changes nothing. It stays because a furigana-annotated
     kana EXPRESSION is a plausible future body shape and it is not a gloss of the chip.

Usage: test_vocab_identity_reading.py [--root PATH]
"""
from __future__ import annotations

import argparse
import sqlite3
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]

DEFAULT_ROOT = Path(__file__).resolve().parents[2]

# A fixture is only evidence if it is the real shape. These are the live records, verbatim from
# corpus/vocab/*.json, for the four homographs the defect was found on plus the two abstain cases.
# (row id, slug, headword, kana, level, introducing_topic_id)
VOCAB = [
    (2007, "vocab:1583470", "品", "しな", "n3", 40),
    (2666, "vocab:2648780", "品", "ひん", "n3", 40),
    (1629, "vocab:1242590", "金", "かね", "n3", 38),
    (1744, "vocab:1242600", "金", "きん", "n3", 38),
    (1493, "vocab:1508290", "柄", "え", "n3", 38),
    (1640, "vocab:1508300", "柄", "がら", "n3", 38),
    (74, "vocab:1352150", "上", "かみ", "n3", 38),
    (1473, "vocab:1352170", "上", "じょう", "n3", 39),
    # 位 is the abstain case: three records, two of which read くらい.
    (2101, "vocab:1155400", "位", "くらい", "n3", 41),
    (2102, "vocab:2078930", "位", "くらい", "n3", 41),
    (2103, "vocab:1155390", "位", "い", "n3", 41),
]
LESSONS = [(9001, "les:fixture-a", 49), (9002, "les:fixture-b", 44)]
# The frequency tier's input: the bank counts that made 品 resolve to ひん and 金 to かね.
TOKENS = [("品", "ひん")] * 5 + [("金", "かね")] * 46 + [("金", "きん")] * 1

FAILS: list[str] = []


def check(ok: bool, label: str, detail: str = "") -> None:
    if not ok:
        FAILS.append(f"{label}: {detail}")


def build_db() -> sqlite3.Connection:
    con = sqlite3.connect(":memory:")
    con.execute("CREATE TABLE vocab (id INTEGER PRIMARY KEY, slug TEXT, headword TEXT, kana TEXT, "
                "level TEXT, introducing_topic_id INTEGER)")
    con.executemany("INSERT INTO vocab (id, slug, headword, kana, level, introducing_topic_id) "
                    "VALUES (?,?,?,?,?,?)",
                    [(i, s, h, k, lv, t) for i, s, h, k, lv, t in VOCAB])
    con.execute("CREATE TABLE lesson (id INTEGER PRIMARY KEY, slug TEXT, topic_id INTEGER)")
    con.executemany("INSERT INTO lesson (id, slug, topic_id) VALUES (?,?,?)", LESSONS)
    con.execute("CREATE TABLE lesson_unlocks (lesson_id INTEGER, unlock_type TEXT, ref TEXT)")
    con.execute("CREATE TABLE token (surface TEXT, reading TEXT)")
    con.executemany("INSERT INTO token (surface, reading) VALUES (?,?)", TOKENS)
    return con


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", type=Path, default=DEFAULT_ROOT,
                    help="tree whose scripts/export is under test (that is how the plant proof runs)")
    args = ap.parse_args()
    root: Path = args.root.resolve()
    sys.path.insert(0, str(root / "scripts" / "export"))
    sys.path.insert(0, str(root / "scripts" / "ingest"))
    from vocab_identity import VocabIdentity          # noqa: E402
    from export_course import _READING_HINT           # noqa: E402

    con = build_db()

    # 1 + 2 — the printed reading beats frequency, and withholding it restores the old answer.
    plain = VocabIdentity(con, rulings={})
    got, how = plain.resolve("品", "n3", "les:fixture-a", "body", reading="しな")
    check((got, how) == ("vocab:1583470", "reading"), "1 printed-reading-beats-frequency",
          f"got {got} ({how}), want vocab:1583470 (reading)")
    base = VocabIdentity(con, rulings={})
    got, how = base.resolve("品", "n3", "les:fixture-a", "body")
    check((got, how) == ("vocab:2648780", "frequency"), "2 without-the-reading-frequency-still-wins",
          f"got {got} ({how}) — check 1 is not measuring the reading tier")

    got, how = VocabIdentity(con, rulings={}).resolve("金", "n3", "les:fixture-b", "body", reading="きん")
    check((got, how) == ("vocab:1242600", "reading"), "1b 金-きん",
          f"got {got} ({how}), want vocab:1242600 (reading)")

    # 3 — two candidates read くらい, so the printed reading identifies nothing. Abstain.
    got, how = VocabIdentity(con, rulings={}).resolve("位", "n3", "les:fixture-a", "body", reading="くらい")
    check(how != "reading", "3 abstain-on-ambiguous-reading",
          f"resolved by {how!r} on a reading two candidates share")

    # 4 — a reading no candidate has must not select anything.
    got, how = VocabIdentity(con, rulings={}).resolve("品", "n3", "les:fixture-a", "body", reading="ほん")
    check(how != "reading", "4 abstain-on-unknown-reading", f"resolved by {how!r} on a foreign reading")

    # 5 — per occurrence. One lesson, two annotated chips for 柄, two different records.
    ident = VocabIdentity(con, rulings={})
    a, howa = ident.resolve("柄", "n3", "les:fixture-a", "body", reading="え")
    b, howb = ident.resolve("柄", "n3", "les:fixture-a", "body", reading="がら")
    check((a, b) == ("vocab:1508290", "vocab:1508300"), "5 per-occurrence",
          f"え -> {a} ({howa}), がら -> {b} ({howb}) — the per-lesson cache swallowed one of them")

    # 5b — the ORDER that makes 5 possible: an unannotated chip earlier in the same lesson caches a
    # guess, and the annotated one after it must still get the reading's answer. Consulting the
    # cache first passes check 5 (nothing had cached anything yet) and fails here, which is why
    # both exist.
    ident2 = VocabIdentity(con, rulings={})
    first, howf = ident2.resolve("柄", "n3", "les:fixture-a", "body")          # caches a guess
    b2, howb2 = ident2.resolve("柄", "n3", "les:fixture-a", "body", reading="がら")
    check((b2, howb2) == ("vocab:1508300", "reading"), "5b reading-beats-the-cache",
          f"a cached {first} ({howf}) shadowed the printed がら: got {b2} ({howb2})")

    # 5c — the same ordering for a ruling. A cached guess must not outrank a recorded decision.
    ident3 = VocabIdentity(con, rulings={("柄", "les:fixture-a"): {"new": "vocab:1508300"}})
    ident3.resolve("柄", "n3", "les:fixture-a", "unlock")
    c3, howc3 = ident3.resolve("柄", "n3", "les:fixture-a", "body")
    check((c3, howc3) == ("vocab:1508300", "ruling"), "5c ruling-beats-the-cache",
          f"got {c3} ({howc3})")

    # 6 — a ruling outranks the heuristics (this is how the 7 rows with no printed reading land).
    ruled = VocabIdentity(con, rulings={("金", "les:fixture-b"): {"new": "vocab:1242600"}})
    got, how = ruled.resolve("金", "n3", "les:fixture-b", "body")
    check((got, how) == ("vocab:1242600", "ruling"), "6 ruling-outranks-heuristics",
          f"got {got} ({how}), want vocab:1242600 (ruling)")

    # 7 — a ruling that contradicts the lesson's own text is a defect, not an override.
    bad = VocabIdentity(con, rulings={("金", "les:fixture-b"): {"new": "vocab:1242590"}})
    try:
        bad.resolve("金", "n3", "les:fixture-b", "body", reading="きん")
        check(False, "7 contradicting-ruling-is-loud", "a ruling contradicting <jp>きん</jp> passed silently")
    except SystemExit:
        pass

    # 8 — the extractor, on the shapes the bodies really carry.
    body_ok = ('<item><vocab ref="vocab:品"/><text> (</text><jp>しな</jp><text>) = "artigo".</text></item>')
    hits = [(m.group("ref"), m.group("reading")) for m in _READING_HINT.finditer(body_ok)]
    check(hits == [("vocab:品", "しな")], "8a extracts-the-printed-reading", f"got {hits}")

    body_compound = ('<vocab ref="vocab:上"/><text> = "do ponto de vista de". Como em </text>'
                     '<jp reading="ほうりつじょう">法律上</jp><text>.</text>')
    hits = [(m.group("ref"), m.group("reading")) for m in _READING_HINT.finditer(body_compound)]
    check(hits == [], "8b refuses-an-example-compound",
          f"read {hits} off a <jp reading=…> example, which glosses the compound, not the chip")

    body_prose = '<vocab ref="vocab:品"/><text>: artigo, mercadoria</text><jp>しな</jp>'
    hits = [(m.group("ref"), m.group("reading")) for m in _READING_HINT.finditer(body_prose)]
    check(hits == [], "8c refuses-a-distant-jp",
          f"read {hits} across a <text> node carrying words — only punctuation may separate them")

    # 9 — a hint must not drift onto a later, unannotated chip.
    body_two = ('<vocab ref="vocab:柄"/><text> (</text><jp>がら</jp><text>): estampa.</text>'
                '<vocab ref="vocab:柄"/><text>: cabo, punho</text>')
    hits = [m.start("ref") for m in _READING_HINT.finditer(body_two)]
    check(len(hits) == 1 and hits[0] == body_two.index('vocab:柄'), "9 hint-stays-on-its-occurrence",
          f"offsets {hits}")

    con.close()
    if FAILS:
        for f in FAILS:
            print(f"[FAIL] {f}")
        print(f"\ntest_vocab_identity_reading: {len(FAILS)} FAIL (root {root})")
        return 1
    print(f"test_vocab_identity_reading: 13 checks PASS — the resolver reads the reading the lesson "
          f"prints, abstains when it identifies nothing, and a ruling that contradicts it is loud "
          f"(root {root})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
