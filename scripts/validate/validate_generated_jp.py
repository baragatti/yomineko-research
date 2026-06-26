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
  validate_generated_jp.py "猫が魚を食べた"
  validate_generated_jp.py --file gen.txt [--known-lesson <lesson_slug>] [--json]
Importable: from validate_generated_jp import validate_jp ; validate_jp(text, known=None) -> dict"""
from __future__ import annotations
import argparse, json, re, sqlite3, sys
from functools import lru_cache
from pathlib import Path
sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
ROOT = Path(__file__).resolve().parents[2]
DB = ROOT / "db" / "corpus.sqlite"
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
    con = sqlite3.connect(DB)
    r = con.execute("SELECT cumulative_known_set FROM lesson WHERE slug=?", (lesson_slug,)).fetchone()
    con.close()
    if not r or not r[0]:
        return None
    ks = json.loads(r[0])
    # cumulative_known_set shape: {"kanji":[...], "vocab":[...]} (ids or surfaces) — normalize to surfaces
    return ks


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


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("text", nargs="?")
    ap.add_argument("--file")
    ap.add_argument("--known-lesson")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()
    known = load_known(args.known_lesson) if args.known_lesson else None
    items = []
    if args.file:
        items = [ln.strip() for ln in Path(args.file).read_text(encoding="utf-8").splitlines() if ln.strip()]
    elif args.text:
        items = [args.text]
    else:
        ap.error("give TEXT or --file")
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
