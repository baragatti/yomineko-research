#!/usr/bin/env python3
"""W13 step 2 — mine REAL Tatoeba sentences for every under-exemplified N3 target.

Spec §1.2 is the whole point: a human-written sentence beats a generated one, so generation is only
allowed where this script finds nothing. It SELECTS ONLY — no Japanese is written here, and the
English is Tatoeba's own directly-linked pairing, kept because the pt-BR authoring pass needs a
Layer-A source (commit c7048fe6: a row shape without `en` cost 324 anchors).

Tatoeba access mirrors scripts/ingest/ingest_all.py::ingest_tatoeba — the same three dumps, the same
"first directly-linked English translation" rule — but reads the dumps directly instead of
db/corpus.sqlite, because the DB is a regenerable index and W01 is diffing it.

A candidate for target T introduced by lesson L must:
  * be 6–40 characters and carry a directly-linked English pair;
  * not already be in corpus/sentences/bank.json (that is a re-link problem, not a mining one);
  * CONTAIN T for real —
      vocab:   a Sudachi C-mode token whose lemma/surface resolves, through the same vocab-form map
               the Dissector uses, to T's slug. Not a substring test: 目 in 目的 is not 目, and a
               substring hit that the Dissector would not link produces a sentence that never counts
               toward coverage;
      grammar: pattern_forms.form_in on any of T's forms (the placeholder-aware matcher);
  * respect L's i+1 budget: every content token maps into L's cumulative_known_set, except T itself
    and at most ONE further unknown content word.

Ranked by unknown_count, then length, then unknown kanji, then id. Up to --per candidates per target.

Output: research/derived/n3_candidates.json, grouped by target. Targets that come out empty are the
spec §1.2 last-resort generation cases and are listed explicitly.

Usage: mine_n3_targets.py [--per 8] [--min-len 6] [--max-len 40] [--rebuild-cache]
"""
from __future__ import annotations

import argparse
import bz2
import json
import re
import sys
import tarfile
import time
from datetime import date
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
sys.path.append(str(Path(__file__).resolve().parents[1] / "export"))
from pattern_forms import form_in, form_pieces  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
DS = ROOT / "research" / "datasets" / "tatoeba"
TARGETS = ROOT / "research" / "derived" / "n3_targets.json"
OUT = ROOT / "research" / "derived" / "n3_candidates.json"
CACHE = ROOT / "tmp" / "w13"           # git-ignored working cache; rebuildable from the dumps

KANJI_RE = re.compile(r"[一-鿿㐀-䶿]")
# same set dissect.py links to the vocab registry (particles/auxiliaries never carry a vocab id)
CONTENT_POS = {"名詞", "動詞", "形容詞", "形状詞", "副詞", "代名詞", "連体詞", "接続詞", "感動詞"}


def log(msg: str) -> None:
    print(f"[{time.strftime('%H:%M:%S')}] {msg}", flush=True)


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


# ───────────────────────────── vocab-form map (mirrors dissect.Dissector) ─────────────────────────
def vocab_form_map() -> dict[str, str]:
    """surface/lemma -> vocab slug, built in the Dissector's precedence order: explicit forms first,
    then headwords, then kana, first writer wins (`setdefault`)."""
    records = []
    for lvl in ("n5", "n4", "n3", "n2", "n1"):
        p = ROOT / "corpus" / "vocab" / f"{lvl}.json"
        if p.exists():
            records.extend(load(p))
    records.sort(key=lambda r: r["id"])
    m: dict[str, str] = {}
    for r in records:
        for f in r.get("forms") or []:
            if f.get("form"):
                m.setdefault(f["form"], r["slug"])
    for r in records:
        if r.get("headword"):
            m.setdefault(r["headword"], r["slug"])
    for r in records:
        if r.get("kana"):
            m.setdefault(r["kana"], r["slug"])
    return m


# ───────────────────────────── stage 1: the eligible Tatoeba pool ─────────────────────────────────
def build_pool(min_len: int, max_len: int, rebuild: bool) -> list[tuple[int, str, str]]:
    cache = CACHE / f"pool_{min_len}_{max_len}.jsonl"
    if cache.exists() and not rebuild:
        log(f"reusing pool cache {cache.relative_to(ROOT)}")
        rows = [json.loads(l) for l in cache.read_text(encoding="utf-8").splitlines()]
        return [(r[0], r[1], r[2]) for r in rows]

    log("loading jpn_sentences.tsv.bz2 …")
    jp: dict[int, str] = {}
    with bz2.open(DS / "jpn_sentences.tsv.bz2", "rt", encoding="utf-8") as f:
        for line in f:
            p = line.rstrip("\n").split("\t")
            if len(p) >= 3:
                jp[int(p[0])] = p[2]
    log(f"  {len(jp)} Japanese sentences")

    log("loading eng_sentences.tsv.bz2 …")
    eng: dict[int, str] = {}
    with bz2.open(DS / "eng_sentences.tsv.bz2", "rt", encoding="utf-8") as f:
        for line in f:
            p = line.rstrip("\n").split("\t")
            if len(p) >= 3:
                eng[int(p[0])] = p[2]
    log(f"  {len(eng)} English sentences")

    log("streaming links.tar.bz2 for direct jpn→eng pairs …")
    pair: dict[int, str] = {}
    with tarfile.open(DS / "links.tar.bz2", "r:bz2") as t:
        fh = t.extractfile(t.getmembers()[0])
        for line in fh:  # type: ignore[union-attr]
            tab = line.find(b"\t")
            if tab < 0:
                continue
            a = int(line[:tab])
            if a in jp and a not in pair:
                b = int(line[tab + 1:])
                if b in eng:
                    pair[a] = eng[b]
    log(f"  {len(pair)} Japanese sentences carry a directly-linked English pair")

    banked = {s["jp"] for s in load(ROOT / "corpus" / "sentences" / "bank.json")}
    pool = [(i, txt, pair[i]) for i, txt in jp.items()
            if i in pair and min_len <= len(txt) <= max_len and txt not in banked]
    pool.sort()
    CACHE.mkdir(parents=True, exist_ok=True)
    cache.write_text("\n".join(json.dumps(r, ensure_ascii=False) for r in pool), encoding="utf-8")
    log(f"  pool: {len(pool)} sentences ({min_len}–{max_len} chars, paired, not already banked)")
    return pool


# ───────────────────────────── stage 2: Sudachi skeletons for the pool ────────────────────────────
def tokenize_pool(pool: list[tuple[int, str, str]], vmap: dict[str, str],
                  rebuild: bool) -> list[list[list]]:
    """Per sentence: [[surface, lemma, slug_or_null, is_free], …] over CONTENT tokens only.

    `is_free` marks a numeral — a 数詞 is a content noun to Sudachi but is taught pre-N5 and would
    otherwise burn the single i+1 slot on '三' in every sentence that counts something."""
    cache = CACHE / f"toks_{len(pool)}.jsonl"
    if cache.exists() and not rebuild:
        log(f"reusing token cache {cache.relative_to(ROOT)}")
        return [json.loads(l) for l in cache.read_text(encoding="utf-8").splitlines()]

    from sudachipy import dictionary, tokenizer  # noqa: PLC0415
    tok = dictionary.Dictionary(dict="full").create()
    C = tokenizer.Tokenizer.SplitMode.C
    out: list[list[list]] = []
    t0 = time.time()
    for n, (_i, text, _en) in enumerate(pool):
        toks = []
        for m in tok.tokenize(text, C):
            p = m.part_of_speech()
            if p[0] not in CONTENT_POS:
                continue
            lemma, surface = m.dictionary_form(), m.surface()
            toks.append([surface, lemma, vmap.get(lemma) or vmap.get(surface),
                         1 if (p[1] == "数詞" or p[0] == "数詞") else 0])
        out.append(toks)
        if n and n % 20000 == 0:
            log(f"  tokenized {n}/{len(pool)} ({n / (time.time() - t0):.0f}/s)")
    CACHE.mkdir(parents=True, exist_ok=True)
    cache.write_text("\n".join(json.dumps(r, ensure_ascii=False) for r in out), encoding="utf-8")
    log(f"  tokenized {len(out)} sentences in {time.time() - t0:.0f}s")
    return out


def diagnose_empty(empty: list[dict], pool: list[tuple[int, str, str]],
                   vmap: dict[str, str]) -> None:
    """Say WHY a target came out empty, because the four reasons need four different answers.

    A word like 何か or 実は is all over Tatoeba and still matches nothing: Sudachi splits it into
    何+か, so no token ever carries its slug. 上 (vocab:1352150) is everywhere too, but the
    vocab-form map already gave the surface 上 to another record, so the Dissector would link an
    occurrence to that other record. Neither case is fixed by generating a sentence — the generated
    one goes through the same Dissector and also fails to link — so they must not be filed with the
    spec §1.2 generation cases."""
    log(f"diagnosing {len(empty)} empty targets …")
    texts = [p[1] for p in pool]
    for e in empty:
        if e["matched_pool_rows"] > 0:
            e["reason"] = "i_plus_1"
            e["note"] = ("occurs in the pool but every occurrence breaches the lesson's i+1 budget — "
                         "real material exists, it is just too hard here")
            continue
        occ: dict[str, int] = {}
        owner: dict[str, str | None] = {}
        if e["kind"] == "grammar":
            # a form is matched piece by piece, in order, so probe the PIECES: gluing them
            # ("たとえ～ても" -> "たとえても") invents a string the matcher never looks for.
            for f in e["surfaces"] or []:
                for piece in form_pieces(f):
                    occ.setdefault(piece, sum(1 for t in texts if piece in t))
            e["piece_occurrences"] = occ
            if not occ or min(occ.values()) == 0:
                e["reason"] = "absent"
                e["note"] = ("a literal piece of the form never occurs in 224k paired Tatoeba "
                             "sentences — the pattern as this record spells it is not attested here")
            else:
                e["reason"] = "form_literal"
                e["note"] = ("every piece occurs, but never contiguously and in order — the pattern "
                             "is inflected or reordered in the wild and pattern_forms is deliberately "
                             "literal, so either the record should list the attested form or this is "
                             "a generation case")
            continue
        for s in e["surfaces"] or []:
            if not s:
                continue
            occ[s] = sum(1 for t in texts if s in t)
            owner[s] = vmap.get(s)
        e["surface_occurrences"] = occ
        if max(occ.values(), default=0) == 0:
            e["reason"] = "absent"
            e["note"] = "the written form does not occur in 224k paired Tatoeba sentences"
        elif any(v is not None and v != e["target_id"] for v in owner.values()):
            e["reason"] = "homograph_collision"
            e["owner"] = {k: v for k, v in owner.items() if v and v != e["target_id"]}
            e["note"] = ("the surface occurs, but the vocab-form map already assigns it to another "
                         "record, so no dissection can ever link it here — generation does not fix "
                         "this; the registry does")
        else:
            e["reason"] = "multi_token"
            e["note"] = ("the surface occurs but Sudachi C-mode never emits it as one token (a "
                         "multi-token expression), so no dissection links it — generation does not "
                         "fix this either")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--per", type=int, default=8)
    ap.add_argument("--min-len", type=int, default=6)
    ap.add_argument("--max-len", type=int, default=40)
    ap.add_argument("--rebuild-cache", action="store_true")
    args = ap.parse_args()

    spec = load(TARGETS)
    targets, lessons = spec["targets"], spec["lessons"]
    pool = build_pool(args.min_len, args.max_len, args.rebuild_cache)
    vmap = vocab_form_map()
    toks = tokenize_pool(pool, vmap, args.rebuild_cache)

    # inverted index: vocab slug -> pool positions that carry a token linked to it
    log("building the slug index …")
    by_slug: dict[str, list[int]] = {}
    kanji_of: list[frozenset[str]] = []
    for n, (tl, (_i, text, _en)) in enumerate(zip(toks, pool)):
        kanji_of.append(frozenset(ch for ch in text if KANJI_RE.match(ch)))
        for s in {t[2] for t in tl if t[2]}:
            by_slug.setdefault(s, []).append(n)
    log(f"  {len(by_slug)} distinct vocab slugs occur in the pool")

    known_cache: dict[str, tuple[set[str], set[str]]] = {}

    def known(lesson_id: str) -> tuple[set[str], set[str]]:
        if lesson_id not in known_cache:
            cks = lessons[lesson_id]["cumulative_known_set"]
            # cks kanji are slugs ("kanji:一"); the pool index holds bare characters
            known_cache[lesson_id] = (set(cks["vocab"]),
                                      {s.split(":", 1)[-1] for s in cks["kanji"]})
        return known_cache[lesson_id]

    def judge(pos: int, kv: set[str], kk: set[str], target_slug: str | None):
        """(unknown content words, unknown kanji) for pool sentence `pos` against a known set."""
        unknown: list[str] = []
        seen: set[str] = set()
        for surface, lemma, slug, free in toks[pos]:
            if free:
                continue
            if slug is not None and (slug in kv or slug == target_slug):
                continue
            key = slug or lemma
            if key in seen:
                continue
            seen.add(key)
            unknown.append(lemma or surface)
        return unknown, sorted(kanji_of[pos] - kk)

    results: dict[str, dict] = {}
    empty: list[dict] = []
    t0 = time.time()
    for n, t in enumerate(targets):
        lid = t["lesson"]
        kv, kk = known(lid)
        tid = t["target_id"]
        if t["kind"] == "vocab":
            positions = by_slug.get(tid, [])
            target_slug = tid
            forms = []
            # a kanji-written headword matched only through its kana form is the weak case: Sudachi
            # lemmatizes どうしよう's しよう to the noun しよう, which the vocab-form map (and so the
            # Dissector, and so the bank's own coverage count) reads as 使用. Demoted, never silent.
            kanji_headword = bool(KANJI_RE.search(t.get("headword") or ""))
        else:
            forms = t["forms"] or ([t["structure_pattern"]] if t.get("structure_pattern") else [])
            positions = [p for p in range(len(pool))
                         if any(form_in(f, pool[p][1]) for f in forms)]
            target_slug = None
            kanji_headword = False
        cands = []
        for p in positions:
            unknown, ukanji = judge(p, kv, kk, target_slug)
            if len(unknown) > 1:
                continue
            sid, text, en = pool[p]
            if t["kind"] == "vocab":
                matched = sorted({tk[0] for tk in toks[p] if tk[2] == tid})
            else:
                matched = [f for f in forms if form_in(f, text)]
            kana_only = bool(kanji_headword and matched
                             and not any(KANJI_RE.search(s) for s in matched))
            cands.append((len(unknown), 1 if kana_only else 0, len(text), len(ukanji), sid,
                          {"tatoeba_id": sid, "jp": text, "en": en,
                           "unknown_count": len(unknown), "unknown": unknown,
                           "unknown_kanji": ukanji, "matched": matched,
                           **({"kana_form_match": True} if kana_only else {})}))
        cands.sort(key=lambda c: c[:5])
        picked = [c[5] for c in cands[:args.per]]
        entry = {"target_id": tid, "kind": t["kind"], "batch": t["batch"], "lesson": lid,
                 "have": t["have"], "need": t["need"],
                 "display": t.get("headword") or t.get("key"),
                 "matched_pool_rows": len(positions), "candidates": picked}
        results[tid] = entry
        if not picked:
            empty.append({"target_id": tid, "kind": t["kind"], "batch": t["batch"], "lesson": lid,
                          "display": entry["display"],
                          "gloss": (t.get("gloss") or {}).get("pt-BR") or t.get("label", {}).get("pt-BR"),
                          "surfaces": t.get("surfaces") or t.get("forms") or [],
                          "matched_pool_rows": len(positions)})
        if n and n % 200 == 0:
            log(f"  {n}/{len(targets)} targets ({time.time() - t0:.0f}s)")

    diagnose_empty(empty, pool, vmap)

    counts = {
        "targets": len(targets),
        "targets_with_candidates": sum(1 for e in results.values() if e["candidates"]),
        "targets_with_zero_candidates": len(empty),
        "targets_meeting_need": sum(1 for tid, e in results.items()
                                    if len(e["candidates"]) >= e["need"]),
        "total_candidates": sum(len(e["candidates"]) for e in results.values()),
        "zero_by_kind": {k: sum(1 for e in empty if e["kind"] == k) for k in ("vocab", "grammar")},
        "zero_by_reason": {r: sum(1 for e in empty if e["reason"] == r) for r in
                           ("absent", "multi_token", "homograph_collision", "form_literal",
                            "i_plus_1")},
        "candidates_flagged_kana_form_match": sum(
            1 for e in results.values() for c in e["candidates"] if c.get("kana_form_match")),
        "pool_rows": len(pool),
    }
    payload = {
        "generated": date.today().isoformat(),
        "unit": "W13 — N3 exemplification, mining stage",
        "source": "research/datasets/tatoeba (jpn + eng sentences, links dump) — CC-BY, ATTRIBUTION.md",
        "method": {
            "pool": f"{args.min_len}–{args.max_len} chars, a directly-linked English pair, not "
                    "already in corpus/sentences/bank.json",
            "vocab_match": "a Sudachi C-mode token whose lemma/surface resolves to the target slug "
                           "through the Dissector's vocab-form map (never a substring test)",
            "grammar_match": "scripts/export/pattern_forms.form_in on any of the record's forms",
            "i_plus_1": "every content token inside the introducing lesson's cumulative_known_set "
                        "except the target itself, plus at most ONE further unknown content word "
                        "(numerals exempt)",
            "ranking": "unknown_count, then length, then unknown kanji, then tatoeba id",
        },
        "note": "SELECTION ONLY. jp is Layer A verbatim; en is Tatoeba's own pairing and is the "
                "SOURCE for the later pt-BR authoring pass, never itself edited.",
        "counts": counts,
        "zero_candidate_targets": empty,
        "targets": results,
    }
    OUT.write_text(json.dumps(payload, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps(counts, ensure_ascii=False, indent=1))
    print(f"wrote {OUT.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
