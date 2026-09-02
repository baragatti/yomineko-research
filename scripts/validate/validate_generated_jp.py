#!/usr/bin/env python3
"""§9.1 deterministic gate for GENERATED Japanese (translation_qa.md). Nothing generated ships on the model's
word alone: every generated JP string runs this battery; any hard failure ⇒ reject (regenerate or escalate).

Checks (all deterministic, no model calls):
  1. PARSE      — Sudachi re-tokenizes with no OOV/unknown morphemes (catches fabricated/garbled JP).
  2. KANJI      — every kanji character is a real KANJIDIC kanji (present in our kanji registry).
  3. WORDS      — every content morpheme is a real word (Sudachi-recognized, not OOV) — no hallucinated vocab.
  4. READINGS   — every kanji has attested KANJIDIC readings; single-kanji tokens must match an attested on/kun
                  reading (no invented furigana). Sudachi supplies the contextual reading from its lexicon.
  5. KNOWN-SET  — (optional) every kanji ∈ known kanji and every content word ∈ known vocab for the target
                  lesson's cumulative_known_set (i+1 gate). Particles/auxiliaries/copula are always allowed.
  6. ATTESTED   — (naturalness) adjacent content-word bigrams are attested in the real Tatoeba/JEC FTS corpus;
                  a collocation that appears NOWHERE in millions of real sentences is a red flag.

Returns a structured verdict + composite trust score (§9.4). HARD checks (1-4) gate accept; known-set + low
attestation are soft (down-score / quarantine). Usage:
  validate_generated_jp.py                  # --selftest: assert the gate is OPERATIONAL (suite mode)
  validate_generated_jp.py "猫が魚を食べた"
  validate_generated_jp.py --file gen.txt [--known-lesson <lesson_slug>] [--json]
Importable: from validate_generated_jp import validate_jp ; validate_jp(text, known=None) -> dict

SUITE MODE (--selftest, and the no-argument default). This file gates every generated sentence the
project will ever ship, and until 2026-09-02 it was in no suite at all: nothing noticed that under
the system interpreter it raised `ModuleNotFoundError: Package sudachidict_core does not exist`
before reaching a single check. A gate that cannot run is indistinguishable from a gate that passes,
so the no-argument run asserts the machinery and its data sources are alive, with floors far below
the live counts: Sudachi tokenizes a control string with zero OOV, the kanji registry and the
attested-reading table are populated, the Tatoeba/JEC attestation corpus answers, and two control
strings still classify the way §9.5 says they must. `run_golden.py` is the behavioural regression on
top of this; this is the pulse check underneath it. Deleting the kanji rows, dropping the FTS
tables, or loading the wrong Sudachi dictionary each fail it."""
from __future__ import annotations
import argparse, json, re, sqlite3, sys
from functools import lru_cache
from pathlib import Path
sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
# W01: honour --db / $YOMINEKO_DB so a rebuild can target a scratch DB (scripts/dbtarget.py).
import sys as _sys, pathlib as _pl  # noqa: E402
_sys.path.append(str(next(p for p in _pl.Path(__file__).resolve().parents if p.name == "scripts")))
from dbtarget import db_target  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
DB = db_target(ROOT / "db" / "corpus.sqlite")
KANJI_RE = re.compile(r"[一-鿿㐀-䶿]")
# POS (Sudachi top-level) that are pure grammar — always allowed, never "content vocab" for the known-set gate
GRAMMAR_POS = {"助詞", "助動詞", "補助記号", "空白", "記号"}


def _kata2hira(s: str) -> str:
    return "".join(chr(ord(c) - 0x60) if "ァ" <= c <= "ン" else c for c in s)


@lru_cache(maxsize=1)
def _sudachi():
    from sudachipy import dictionary, tokenizer
    return dictionary.Dictionary().create(), tokenizer.Tokenizer.SplitMode.C


@lru_cache(maxsize=1)
def _kanji_readings() -> dict:
    """char -> set of attested readings (hiragana), incl. kun stems (reading+okurigana) and on (kata→hira)."""
    con = sqlite3.connect(DB)
    out: dict = {}
    for ch, rdg, rtype, oku in con.execute(
            "SELECT k.character, kr.reading, kr.reading_type, kr.okurigana FROM kanji_reading kr "
            "JOIN kanji k ON k.id=kr.kanji_id"):
        s = out.setdefault(ch, set())
        h = _kata2hira(rdg)
        s.add(h)
        if oku:
            s.add(h + oku)  # full kun reading with okurigana
    con.close()
    return out


@lru_cache(maxsize=1)
def _kanji_set() -> frozenset:
    con = sqlite3.connect(DB)
    s = frozenset(r[0] for r in con.execute("SELECT character FROM kanji"))
    con.close()
    return s


def _attested(con: sqlite3.Connection, phrase: str) -> bool:
    if len(phrase) < 2:
        return True
    q = '"' + phrase.replace('"', '') + '"'
    for tbl in ("raw_tatoeba_fts", "raw_jec_fts"):
        try:
            if con.execute(f"SELECT 1 FROM {tbl} WHERE {tbl} MATCH ? LIMIT 1", (q,)).fetchone():
                return True
        except sqlite3.OperationalError:
            pass
    return False


def load_known(lesson_slug: str) -> dict | None:
    """Known set from the EXPORTED lesson leaf (course/), not the DB: the export is the source of
    truth, speaks slug space, and the DB's stored copy can lag it. Prefix-strip so the comparisons
    below see bare characters/slug idents ('kanji:食' -> '食')."""
    for lf in ROOT.glob("course/*/topic-*/lesson-*.json"):
        d = json.loads(lf.read_text(encoding="utf-8"))
        if d.get("id") == lesson_slug:
            ks = d.get("cumulative_known_set") or {}
            return {k: [x.split(":", 1)[1] if isinstance(x, str) and ":" in x else x for x in v]
                    for k, v in ks.items()}
    return None


def validate_jp(text: str, known: dict | None = None) -> dict:
    tk, mode = _sudachi()
    kset = _kanji_set()
    krd = _kanji_readings()
    con = sqlite3.connect(DB)
    morphs = list(tk.tokenize(text, mode))
    fails: list[str] = []
    warns: list[str] = []

    # 1. PARSE — no OOV; and no raw Latin letters (always a leak/garble in generated JP: abc, でshou, ほotn)
    oov = [m.surface() for m in morphs if m.is_oov()]
    if oov:
        fails.append(f"parse: OOV/unknown tokens {oov}")
    latin = re.findall(r"[A-Za-z]+", text)
    if latin:
        fails.append(f"parse: raw Latin letters in JP (leak/garble) {latin}")

    # 2/3. KANJI exist + 4. readings
    bad_kanji = sorted({c for c in text if KANJI_RE.match(c) and c not in kset})
    if bad_kanji:
        fails.append(f"kanji: not in KANJIDIC registry {bad_kanji}")
    no_reading = sorted({c for c in text if KANJI_RE.match(c) and c in kset and not krd.get(c)})
    if no_reading:
        fails.append(f"readings: kanji with no attested reading {no_reading}")
    # single-kanji token contextual reading must be an attested reading
    for m in morphs:
        s = m.surface()
        if len(s) == 1 and KANJI_RE.match(s) and s in krd:
            rd = _kata2hira(m.reading_form())
            if rd and rd not in krd[s] and not any(rd in r or r in rd for r in krd[s]):
                warns.append(f"reading: {s}={rd} not in attested {sorted(krd[s])[:6]}")

    # 5. KNOWN-SET (soft)
    if known is not None:
        kk = set(known.get("kanji", []))
        kv = set(known.get("vocab", []))
        unknown_k = sorted({c for c in text if KANJI_RE.match(c) and c not in kk})
        if unknown_k:
            warns.append(f"known-set: kanji outside lesson set {unknown_k}")
        for m in morphs:
            pos = m.part_of_speech()[0]
            if pos in GRAMMAR_POS:
                continue
            base = m.dictionary_form()
            if base not in kv and m.surface() not in kv:
                warns.append(f"known-set: content word outside set «{m.surface()}» ({base})")

    # 6. ATTESTATION (naturalness, soft) — adjacent content-word surface bigrams
    content = [m.surface() for m in morphs if m.part_of_speech()[0] not in GRAMMAR_POS and m.surface().strip()]
    bigrams = [content[i] + content[i + 1] for i in range(len(content) - 1)]
    attested = [b for b in bigrams if _attested(con, b)]
    att_ratio = (len(attested) / len(bigrams)) if bigrams else 1.0
    if bigrams and att_ratio < 0.34:
        warns.append(f"attestation: only {len(attested)}/{len(bigrams)} content bigrams attested in real corpus")
    con.close()

    hard_ok = not fails
    # trust score §9.4: hard checks dominate; soft checks shade it
    score = 0.0
    if hard_ok:
        score = 0.6 + 0.2 * att_ratio + (0.2 if not warns else 0.1)
    verdict = "reject" if not hard_ok else ("accept" if score >= 0.8 and not warns else "quarantine")
    return {"text": text, "verdict": verdict, "trust": round(score, 3),
            "hard_fail": fails, "warn": warns, "attestation": round(att_ratio, 3),
            "tokens": [m.surface() for m in morphs]}


# --- suite mode: is the gate alive? -----------------------------------------------------------------
# Floors sit far below the live values (10,384 kanji / 10,108 with readings at the 2026-09-02 index)
# so growth never trips them while a vanished table does.
KANJI_FLOOR = 5000
READING_FLOOR = 5000
CONTROL_PARSE = "今日はいい天気ですね"          # must tokenize with zero OOV
CONTROL_ATTESTED = ["図書館", "コーヒー", "食べた"]  # real corpus n-grams; ≥2 must be found
CONTROL_GOOD = "毎朝コーヒーを飲みます"           # §9.5 'good': must NOT reject
CONTROL_BAD = "わたしはabcを食べる"              # §9.5 'bad':  MUST reject


def selftest() -> int:
    fails: list[str] = []
    try:
        tk, mode = _sudachi()
        morphs = list(tk.tokenize(CONTROL_PARSE, mode))
    except Exception as exc:  # the exact class of rot that hid this gate — surface it, do not swallow
        print(f"[FAIL] sudachi: dictionary unavailable ({type(exc).__name__}: {exc})")
        print("selftest: 1 FAIL — the generation gate cannot run")
        return 1
    oov = [m.surface() for m in morphs if m.is_oov()]
    print(f"[{'OK  ' if morphs and not oov else 'FAIL'}] sudachi: {len(morphs)} morphemes, "
          f"{len(oov)} OOV on «{CONTROL_PARSE}»")
    if not morphs or oov:
        fails.append(f"sudachi tokenized «{CONTROL_PARSE}» into {len(morphs)} morphemes, OOV={oov}")

    n_kanji, n_read = len(_kanji_set()), len(_kanji_readings())
    print(f"[{'OK  ' if n_kanji >= KANJI_FLOOR else 'FAIL'}] kanji registry: {n_kanji} "
          f"(floor {KANJI_FLOOR})")
    print(f"[{'OK  ' if n_read >= READING_FLOOR else 'FAIL'}] attested readings: {n_read} chars "
          f"(floor {READING_FLOOR})")
    if n_kanji < KANJI_FLOOR:
        fails.append(f"kanji registry holds {n_kanji} characters, under the floor {KANJI_FLOOR}")
    if n_read < READING_FLOOR:
        fails.append(f"reading table covers {n_read} characters, under the floor {READING_FLOOR}")

    con = sqlite3.connect(DB)
    found = [p for p in CONTROL_ATTESTED if _attested(con, p)]
    con.close()
    print(f"[{'OK  ' if len(found) >= 2 else 'FAIL'}] attestation corpus: {len(found)}/"
          f"{len(CONTROL_ATTESTED)} control phrases found {found}")
    if len(found) < 2:
        fails.append(f"attestation corpus answered for {len(found)} of {len(CONTROL_ATTESTED)} "
                     "control phrases — the Tatoeba/JEC FTS tables are missing or empty")

    for text, must_reject in ((CONTROL_GOOD, False), (CONTROL_BAD, True)):
        verdict = validate_jp(text)["verdict"]
        ok = (verdict == "reject") if must_reject else (verdict != "reject")
        print(f"[{'OK  ' if ok else 'FAIL'}] control {'bad ' if must_reject else 'good'}: "
              f"verdict={verdict} on «{text}»")
        if not ok:
            fails.append(f"control {'bad' if must_reject else 'good'} «{text}» -> {verdict}")

    for f in fails:
        print(f"  FAIL {f}")
    print(f"selftest: {len(fails)} FAIL — the generation gate is "
          f"{'BROKEN' if fails else 'operational'}")
    return 1 if fails else 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("text", nargs="?")
    ap.add_argument("--file")
    ap.add_argument("--known-lesson")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--selftest", action="store_true",
                    help="assert the gate is operational (the no-argument default; suite mode)")
    args = ap.parse_args()
    if args.selftest or not (args.text or args.file):
        return selftest()
    known = load_known(args.known_lesson) if args.known_lesson else None
    items = []
    if args.file:
        items = [ln.strip() for ln in Path(args.file).read_text(encoding="utf-8").splitlines() if ln.strip()]
    else:
        items = [args.text]
    results = [validate_jp(t, known) for t in items]
    if args.json:
        print(json.dumps(results, ensure_ascii=False, indent=2))
    else:
        for r in results:
            mark = {"accept": "OK ", "quarantine": "QTN", "reject": "BAD"}[r["verdict"]]
            print(f"[{mark}] trust={r['trust']:.2f} att={r['attestation']:.2f}  {r['text']}")
            for f in r["hard_fail"]:
                print(f"        ✗ {f}")
            for w in r["warn"]:
                print(f"        ⚠ {w}")
    bad = sum(1 for r in results if r["verdict"] == "reject")
    print(f"\n{len(results)} checked · {bad} reject · "
          f"{sum(1 for r in results if r['verdict']=='quarantine')} quarantine · "
          f"{sum(1 for r in results if r['verdict']=='accept')} accept")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
