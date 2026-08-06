#!/usr/bin/env python3
"""Build a word-frequency table from the RAW Tatoeba Japanese corpus, then populate vocab.freq_rank.

Why we need this: `vocab.freq_rank` is declared in the schema but was never filled, and `common` is 1 for
all 7,401 rows (JMdict's flag, applied to everything we ingested), so the corpus had NO usable "which words
matter most" signal. The speaking-first course path is ordered by frequency, so it needs one.

Where the signal comes from: `raw_tatoeba_sentence` — 248,705 human-written Japanese sentences, CC-BY, already
ingested and attributed (see ATTRIBUTION.md / design/sources.md). This is LAYER A: no AI, no judgement, just
counting tokens in real sentences written by humans. Tatoeba's register skews conversational/everyday, which
is exactly the register a "learn to talk on a trip" path needs — a written-corpus list (news, Wikipedia)
would over-rank 政府 and under-rank ちょっと.

Honest limits, recorded here so nobody over-trusts the number:
  * Tatoeba is contributed sentences, not a balanced corpus. It over-represents textbook-ish clause patterns
    and under-represents true spontaneous speech (fillers, aizuchi, contractions).
  * Counting is by Sudachi mode-C lemma, so a word split differently by the analyzer counts differently.
  * Rank is therefore a strong ORDERING hint, not a citable statistic. It is Layer A because it is a
    mechanical count of Layer-A text — not because it is authoritative about Japanese at large.

Writes research/derived/frequency/tatoeba_lemma_freq.json (full table, versioned) and sets vocab.freq_rank
for every vocab row whose headword or kana matches a counted lemma. Idempotent: re-running recomputes and
overwrites. Usage: build_frequency.py [--limit N] [--skip-count]
"""
from __future__ import annotations
import argparse, json, re, sqlite3, sys, time
from collections import Counter
from pathlib import Path

import jaconv

jaconv_hira = jaconv.kata2hira
sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
ROOT = Path(__file__).resolve().parents[2]
DB = ROOT / "db" / "corpus.sqlite"
OUT = ROOT / "research" / "derived" / "frequency"
JP = re.compile(r"[぀-ヿ一-鿿㐀-䶿]")
JP_KANJI = re.compile(r"[一-鿿㐀-䶿]")
# POS we never want in a learner-facing frequency list: they are analyzer artefacts, not words.
DROP_POS = {"補助記号", "記号", "空白"}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=0, help="only read N sentences (smoke test)")
    ap.add_argument("--skip-count", action="store_true", help="reuse the saved table, only set freq_rank")
    args = ap.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    table_path = OUT / "tatoeba_lemma_freq.json"
    con = sqlite3.connect(DB)

    sents: list[str] = []
    if args.skip_count and table_path.exists():
        rows = json.loads(table_path.read_text(encoding="utf-8"))["lemmas"]
        print(f"reusing {len(rows)} counted entries")
    else:
        from sudachipy import dictionary, tokenizer  # noqa: E402  (heavy import, only when counting)
        tok = dictionary.Dictionary(dict="full").create()
        MODE = tokenizer.Tokenizer.SplitMode.C          # display tokens — matches how vocab is headworded
        sql = "SELECT text FROM raw_tatoeba_sentence"
        if args.limit:
            sql += f" LIMIT {args.limit}"
        sents = [r[0] for r in con.execute(sql)]
        print(f"counting over {len(sents)} Tatoeba sentences…", flush=True)

        freq: Counter = Counter()
        reading: dict[str, str] = {}
        pos_of: dict[str, str] = {}
        t0, done = time.time(), 0
        for s in sents:
            if not s:
                continue
            try:
                morphs = tok.tokenize(s, MODE)
            except Exception:
                continue                                  # a malformed row must not kill a 248k-row pass
            for m in morphs:
                pos = m.part_of_speech()
                if pos[0] in DROP_POS:
                    continue
                lemma = m.dictionary_form() or m.surface()
                if not lemma or not JP.search(lemma):
                    continue
                freq[lemma] += 1
                if lemma not in pos_of:
                    pos_of[lemma] = pos[0]
                    reading[lemma] = m.reading_form() or ""
            done += 1
            if done % 25000 == 0:
                print(f"  {done}/{len(sents)}  {time.time()-t0:.0f}s  {len(freq)} distinct", flush=True)

        rows = [{"lemma": w, "reading": reading.get(w, ""), "pos": pos_of.get(w, ""),
                 "count": n, "method": "lemma"}
                for w, n in freq.most_common()]

        # ---- second pass: multi-token expressions -------------------------------------------------
        # Mode C still splits plenty of things a LEARNER meets as one word: 一つ -> 一+つ, どうも -> どう+も,
        # では -> で+は, 誰か -> 誰+か, すぐに -> すぐ+に, どうして -> どう+し+て, 五日 -> 五+日. Those can
        # never surface as a lemma, so counting lemmas alone left 一つ/二つ/三つ, the date counters, and
        # several everyday adverbs UNRANKED — which in a frequency-ordered path would have sorted them
        # last. For every vocab entry the lemma pass missed, count literal occurrences instead.
        # This is a coarser measure (substring hits, so it can over-count a form nested in a longer word)
        # and is tagged method="surface" so consumers can tell the two apart.
        counted = {r["lemma"] for r in rows}
        blob = "\n".join(sents)
        extra: list[dict] = []
        for hw, kana in con.execute("SELECT DISTINCT headword,kana FROM vocab"):
            if hw in counted or (not JP_KANJI.search(hw) and kana in counted):
                continue
            # Count the headword as written. The kana form is counted too — many of our headwords carry a
            # kanji spelling Tatoeba rarely uses (直ぐに vs すぐに, 其れから vs それから, 如何して vs
            # どうして) — but only from 3 morae up: shorter kana are homophone soup (する also reads 刷る,
            # こと also reads 琴, よう also reads 用/様) and would import an unrelated word's count.
            n = max(blob.count(hw), blob.count(kana) if len(kana) >= 3 else 0)
            if n:
                extra.append({"lemma": hw, "reading": kana, "pos": "", "count": n, "method": "surface"})
        rows = sorted(rows + extra, key=lambda r: (-r["count"], r["lemma"]))
        for i, r in enumerate(rows):
            r["rank"] = i + 1
        print(f"  + {len(extra)} multi-token expressions counted by surface")

        table_path.write_text(json.dumps(
            {"source": "raw_tatoeba_sentence (CC-BY, see ATTRIBUTION.md)",
             "method": "SudachiPy full dict, SplitMode.C, dictionary_form(); 補助記号/記号/空白 dropped. "
                       "Vocab entries the lemma pass missed are counted by literal surface occurrence "
                       "(method=surface) because mode C splits them (一つ, どうも, では, 五日).",
             "sentences": len(sents), "distinct_entries": len(rows),
             "total_tokens": sum(freq.values()),
             "caveat": "Contributed-sentence corpus, not balanced: it over-represents textbook-ish clause "
                       "patterns, under-represents spontaneous speech, and 'トム' ranks ~25th because it is "
                       "Tatoeba's default placeholder name. method=surface counts are substring hits and "
                       "can over-count. A strong ORDERING hint, not a citable statistic. Layer A because "
                       "it is a mechanical count of Layer-A text.",
             "lemmas": rows}, ensure_ascii=False), encoding="utf-8")
        print(f"wrote {table_path.relative_to(ROOT)}: {len(rows)} entries, "
              f"{sum(freq.values())} tokens, {time.time()-t0:.0f}s")

    # ---- populate vocab.freq_rank -------------------------------------------------------------
    # Match on the WRITTEN form only. An earlier version also matched our kana against each lemma's
    # reading, which looked like better coverage and was in fact badly wrong: it made 歯 (は) inherit the
    # particle は's 168k count and rank #1, 手 (て) rank #7, 二 (に) rank #4, 琴 (こと) rank #22. Reading
    # equality is homophony, not identity. A vocab entry now takes a rank only from its own headword, or
    # from its kana when the headword IS kana; anything else is handled by the surface pass above, which
    # counts the actual string rather than borrowing another word's number.
    rank = {r["lemma"]: r["rank"] for r in rows}
    vocab = list(con.execute("SELECT id,headword,kana FROM vocab"))
    con.execute("BEGIN")
    hit = miss = 0
    for vid, hw, kana in vocab:
        r = rank.get(hw) or (rank.get(kana) if not JP_KANJI.search(hw) else None)
        if r:
            con.execute("UPDATE vocab SET freq_rank=? WHERE id=?", (r, vid))
            hit += 1
        else:
            con.execute("UPDATE vocab SET freq_rank=NULL WHERE id=?", (vid,))
            miss += 1
    con.commit()
    print(f"vocab.freq_rank set for {hit}/{len(vocab)} entries ({miss} not attested in Tatoeba)")
    for lvl in ("n5", "n4", "n3", "n2", "n1"):
        n, got = con.execute("SELECT COUNT(*), SUM(freq_rank IS NOT NULL) FROM vocab WHERE level=?",
                             (lvl,)).fetchone()
        if n:
            print(f"  {lvl}: {got}/{n} ranked")
    con.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
