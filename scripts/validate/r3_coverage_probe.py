#!/usr/bin/env python3
"""Phase R3 — empirical source-coverage probe.

Measures, with REAL numbers, whether the open datasets can deliver the corpus:
  * dictionary completeness for the candidate N5/N4 kanji & vocab sets
  * KanjiVG stroke-order + Kradfile decomposition coverage
  * Tatoeba JP sentence supply: % with PT translation, % with EN, % with audio
  * per-target sentence supply (sample of N5 vocab + grammar markers), incl. a
    beginner-simplicity proxy for i+1 feasibility

Stdlib only. Prints a human summary and writes machine-readable JSON to
research/coverage/r3_probe_results.json. Substring matching is a deliberate
proxy here (P5 will use SudachiPy lemma matching for exactness) — flagged in output.
"""
from __future__ import annotations

import bz2
import gzip
import json
import re
import sys
import tarfile
from collections import Counter
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]

ROOT = Path(__file__).resolve().parents[2]
DS = ROOT / "research" / "datasets"
OUT = ROOT / "research" / "coverage"
OUT.mkdir(parents=True, exist_ok=True)

KANJI_RE = re.compile(r"[一-鿿㐀-䶿]")


def log(m: str) -> None:
    print(m, flush=True)


def load_tgz_json(path: Path) -> dict:
    with tarfile.open(path, "r:gz") as t:
        member = next(m for m in t.getmembers() if m.name.endswith(".json"))
        return json.loads(t.extractfile(member).read().decode("utf-8"))  # type: ignore[union-attr]


def newest(glob: str) -> Path:
    return sorted(DS.glob(glob))[-1]


# ---------------------------------------------------------------- target sets
def candidate_kanji() -> dict[str, dict]:
    kj = json.loads((DS / "jlpt" / "kanji.json").read_text(encoding="utf-8"))
    out = {}
    for ch, v in kj.items():
        lvl = v.get("jlpt_new")
        if lvl in (5, 4):
            out[ch] = {"level": f"n{lvl}"}
    return out


def candidate_vocab() -> dict[str, list[dict]]:
    import csv

    out: dict[str, list[dict]] = {"n5": [], "n4": []}
    for lvl in ("n5", "n4"):
        with open(DS / "jlpt" / f"{lvl}.csv", encoding="utf-8") as f:
            for row in csv.DictReader(f):
                expr = (row.get("expression") or "").strip()
                read = (row.get("reading") or "").strip()
                if expr:
                    out[lvl].append({"expr": expr, "reading": read})
    return out


# ---------------------------------------------------------------- dictionaries
def kanjidic_index() -> dict[str, dict]:
    data = load_tgz_json(newest("jmdict/kanjidic2-en-*.tgz"))
    idx = {}
    for c in data["characters"]:
        lit = c["literal"]
        misc = c.get("misc", {})
        on, kun, meanings = [], [], []
        for g in c.get("readingMeaning", {}).get("groups", []):
            for r in g.get("readings", []):
                if r["type"] == "ja_on":
                    on.append(r["value"])
                elif r["type"] == "ja_kun":
                    kun.append(r["value"])
            for m in g.get("meanings", []):
                if m.get("lang") == "en":
                    meanings.append(m["value"])
        idx[lit] = {
            "strokes": (misc.get("strokeCounts") or [None])[0],
            "grade": misc.get("grade"),
            "on": on,
            "kun": kun,
            "meanings": meanings,
        }
    return idx


def jmdict_common_index() -> tuple[set[str], set[str], dict[str, bool]]:
    """Return (all_surface_forms, common_surface_forms, _) where surface form is any
    kanji-form or kana-form string."""
    data = load_tgz_json(newest("jmdict/jmdict-eng-common-*.tgz"))
    all_forms: set[str] = set()
    common_forms: set[str] = set()
    for w in data["words"]:
        for el in (w.get("kanji") or []) + (w.get("kana") or []):
            t = el.get("text")
            if not t:
                continue
            all_forms.add(t)
            if el.get("common"):
                common_forms.add(t)
    return all_forms, common_forms, {}


def kradfile_set() -> set[str]:
    data = load_tgz_json(newest("jmdict/kradfile-*.tgz"))
    return set(data.get("kanji", {}).keys())


def kanjivg_set() -> set[str]:
    chars: set[str] = set()
    with gzip.open(newest("kanjivg/kanjivg-*.xml.gz"), "rt", encoding="utf-8") as f:
        text = f.read()
    for hexcp in re.findall(r'id="kvg:kanji_0*([0-9a-fA-F]+)"', text):
        try:
            chars.add(chr(int(hexcp, 16)))
        except ValueError:
            pass
    return chars


# ---------------------------------------------------------------- tatoeba
def load_jpn_sentences() -> dict[int, str]:
    out: dict[int, str] = {}
    with bz2.open(DS / "tatoeba" / "jpn_sentences.tsv.bz2", "rt", encoding="utf-8") as f:
        for line in f:
            parts = line.rstrip("\n").split("\t")
            if len(parts) >= 3:
                out[int(parts[0])] = parts[2]
    return out


def load_id_set(fname: str) -> set[int]:
    out: set[int] = set()
    with bz2.open(DS / "tatoeba" / fname, "rt", encoding="utf-8") as f:
        for line in f:
            i = line.split("\t", 1)[0]
            if i:
                try:
                    out.add(int(i))
                except ValueError:
                    pass
    return out


def load_audio_ids() -> set[int]:
    out: set[int] = set()
    with tarfile.open(DS / "tatoeba" / "sentences_with_audio.tar.bz2", "r:bz2") as t:
        f = t.extractfile(t.getmembers()[0])
        for line in f:  # type: ignore[union-attr]
            sid = line.split(b"\t", 1)[0]
            if sid:
                try:
                    out.add(int(sid))
                except ValueError:
                    pass
    return out


def stream_links_for_jp(jp_ids: set[int], por_ids: set[int], eng_ids: set[int]):
    jp_por: set[int] = set()
    jp_eng: set[int] = set()
    n = 0
    with tarfile.open(DS / "tatoeba" / "links.tar.bz2", "r:bz2") as t:
        f = t.extractfile(t.getmembers()[0])
        for line in f:  # type: ignore[union-attr]
            n += 1
            tab = line.find(b"\t")
            if tab < 0:
                continue
            a = int(line[:tab])
            if a in jp_ids:
                b = int(line[tab + 1 :])
                if b in por_ids:
                    jp_por.add(a)
                if b in eng_ids:
                    jp_eng.add(a)
    return jp_por, jp_eng, n


# ---------------------------------------------------------------- main
def main() -> int:
    log("R3 coverage probe — loading target sets…")
    kanji = candidate_kanji()
    vocab = candidate_vocab()
    n_kanji = len(kanji)
    n5v, n4v = len(vocab["n5"]), len(vocab["n4"])
    log(f"  candidate kanji (N5+N4): {n_kanji} | vocab N5={n5v} N4={n4v}")

    log("Loading dictionaries…")
    kd = kanjidic_index()
    jm_all, jm_common, _ = jmdict_common_index()
    krad = kradfile_set()
    kvg = kanjivg_set()
    log(f"  KANJIDIC2 chars={len(kd):,} | JMdict-common forms={len(jm_all):,} "
        f"(common={len(jm_common):,}) | kradfile={len(krad):,} | KanjiVG={len(kvg):,}")

    # kanji completeness
    kanji_report = {
        "total": n_kanji,
        "in_kanjidic": sum(1 for c in kanji if c in kd),
        "with_strokes": sum(1 for c in kanji if kd.get(c, {}).get("strokes")),
        "with_on_or_kun": sum(1 for c in kanji if kd.get(c, {}).get("on") or kd.get(c, {}).get("kun")),
        "with_meanings": sum(1 for c in kanji if kd.get(c, {}).get("meanings")),
        "in_kanjivg": sum(1 for c in kanji if c in kvg),
        "in_kradfile": sum(1 for c in kanji if c in krad),
    }
    missing_kvg = [c for c in kanji if c not in kvg]
    missing_krad = [c for c in kanji if c not in krad]

    # vocab completeness (match expr against any JMdict-common surface form)
    def vocab_cov(items: list[dict]) -> dict:
        in_jm = sum(1 for it in items if it["expr"] in jm_all)
        common = sum(1 for it in items if it["expr"] in jm_common)
        # fall back to reading match for the not-found
        miss = [it for it in items if it["expr"] not in jm_all]
        by_reading = sum(1 for it in miss if it.get("reading") and it["reading"] in jm_all)
        return {
            "total": len(items),
            "in_jmdict_common": in_jm,
            "common_marked": common,
            "recovered_by_reading": by_reading,
            "still_missing": len(miss) - by_reading,
            "sample_missing": [it["expr"] for it in miss[:25]],
        }

    vocab_report = {"n5": vocab_cov(vocab["n5"]), "n4": vocab_cov(vocab["n4"])}

    log("Loading Tatoeba JP sentences + id sets…")
    jp = load_jpn_sentences()
    jp_ids = set(jp.keys())
    log(f"  JP sentences: {len(jp):,}")
    por_ids = load_id_set("por_sentences.tsv.bz2")
    eng_ids = load_id_set("eng_sentences.tsv.bz2")
    log(f"  POR ids: {len(por_ids):,} | ENG ids: {len(eng_ids):,}")
    audio_ids = load_audio_ids()
    jp_audio = jp_ids & audio_ids
    log(f"  audio ids (all langs): {len(audio_ids):,} | JP with audio: {len(jp_audio):,}")

    log("Streaming links.csv (≈30M rows) for JP→PT / JP→EN …")
    jp_por, jp_eng, nlinks = stream_links_for_jp(jp_ids, por_ids, eng_ids)
    log(f"  links scanned: {nlinks:,} | JP w/ PT: {len(jp_por):,} | JP w/ EN: {len(jp_eng):,}")

    tatoeba_overall = {
        "jp_total": len(jp),
        "jp_with_pt": len(jp_por),
        "jp_with_en": len(jp_eng),
        "jp_with_audio": len(jp_audio),
        "pct_pt": round(100 * len(jp_por) / len(jp), 1),
        "pct_en": round(100 * len(jp_eng) / len(jp), 1),
        "pct_audio": round(100 * len(jp_audio) / len(jp), 1),
    }

    # precompute per-sentence simplicity metrics
    log("Computing per-sentence metrics + per-target supply…")
    sent_items = list(jp.items())  # (id, text)
    simple_flag: dict[int, bool] = {}
    for sid, text in sent_items:
        kc = len(set(KANJI_RE.findall(text)))
        simple_flag[sid] = (len(text) <= 24 and kc <= 6)

    def supply_for(term: str) -> dict:
        matched = [sid for sid, text in sent_items if term in text]
        n = len(matched)
        with_pt = sum(1 for s in matched if s in jp_por)
        with_audio = sum(1 for s in matched if s in jp_audio)
        simple = sum(1 for s in matched if simple_flag[s])
        simple_pt = sum(1 for s in matched if simple_flag[s] and s in jp_por)
        return {
            "n": n, "with_pt": with_pt, "with_audio": with_audio,
            "simple": simple, "simple_with_pt": simple_pt,
        }

    # sample of N5 vocab: spread across the list, prefer length>=2 to cut false positives
    n5_words = [it["expr"] for it in vocab["n5"] if len(it["expr"]) >= 2]
    step = max(1, len(n5_words) // 60)
    sample_words = n5_words[::step][:60]
    word_supply = {w: supply_for(w) for w in sample_words}

    def pct_meeting(thresh: int, key: str) -> float:
        ok = sum(1 for s in word_supply.values() if s[key] >= thresh)
        return round(100 * ok / len(word_supply), 1)

    vocab_supply_summary = {
        "sample_size": len(sample_words),
        "pct_with_>=3_total": pct_meeting(3, "n"),
        "pct_with_>=3_with_pt": pct_meeting(3, "with_pt"),
        "pct_with_>=3_simple": pct_meeting(3, "simple"),
        "pct_with_>=1_total": pct_meeting(1, "n"),
        "median_total": sorted(s["n"] for s in word_supply.values())[len(word_supply) // 2],
        "median_simple": sorted(s["simple"] for s in word_supply.values())[len(word_supply) // 2],
        "examples": dict(list(word_supply.items())[:12]),
    }

    grammar_markers = ["は", "を", "が", "に", "で", "へ", "と", "も", "から", "まで",
                       "ね", "よ", "か", "て", "た", "ない", "ます", "たい", "でしょう", "なければ"]
    grammar_supply = {g: supply_for(g) for g in grammar_markers}
    grammar_summary = {
        "pct_with_>=5_total": round(
            100 * sum(1 for s in grammar_supply.values() if s["n"] >= 5) / len(grammar_supply), 1),
        "pct_with_>=5_simple": round(
            100 * sum(1 for s in grammar_supply.values() if s["simple"] >= 5) / len(grammar_supply), 1),
        "examples": grammar_supply,
    }

    results = {
        "candidate_sets": {"kanji_n5_n4": n_kanji, "vocab_n5": n5v, "vocab_n4": n4v,
                           "kanji_by_level": dict(Counter(v["level"] for v in kanji.values()))},
        "kanji_completeness": kanji_report,
        "kanji_missing_kanjivg": missing_kvg,
        "kanji_missing_kradfile": missing_krad,
        "vocab_completeness": vocab_report,
        "tatoeba_overall": tatoeba_overall,
        "vocab_sentence_supply": vocab_supply_summary,
        "grammar_marker_supply": grammar_summary,
        "method_notes": [
            "Vocab/grammar sentence supply uses SUBSTRING matching (proxy). P5 uses SudachiPy lemma matching.",
            "'simple' = sentence length<=24 chars AND <=6 distinct kanji (i+1 feasibility proxy, not true cumulative-set check).",
            "Candidate level sets from 2 community lists only (kanji.json jlpt_new; elzup vocab). P2 must reconcile >=3.",
        ],
    }

    (OUT / "r3_probe_results.json").write_text(
        json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
    log("\n===== RESULTS (JSON) =====")
    log(json.dumps(results, ensure_ascii=False, indent=2))
    log("\nwrote research/coverage/r3_probe_results.json")
    return 0


if __name__ == "__main__":
    sys.exit(main())
