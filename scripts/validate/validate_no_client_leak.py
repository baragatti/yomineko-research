#!/usr/bin/env python3
"""Gate: the built browser bundle carries NO corpus content — the SSR-only guarantee.

WHY THIS EXISTS (review finding F11)
------------------------------------
prototype/README.md promises that the paid corpus never reaches the browser: the server renders the
handful of sentences a page shows and the client bundle holds UI code only ("Searching build/client
for corpus sentences returns nothing"). That promise was enforced by a sentence in a README asking a
human to run a grep. One `import sentences from "~/data/sentences.json"` inside a client component,
one loader value returned instead of consumed server-side, and 5,889 dissected sentences plus every
answer key become a scrapable static asset — the difference between private paid content and a free
API. Nothing in the suite looked at prototype/build at all.

HOW IT CHECKS
-------------
Two independent nets, because a bundler can leak content in two shapes.
  (1) PROBES — a deterministic sample (stride-based, so it is stable across runs and reviewable)
      of real corpus strings: sentence jp + pt-BR translation, vocabulary pt-BR glosses, kanji pt-BR
      meanings, grammar pt-BR label + nuance, and tag-stripped slices of lesson bodies. Every file
      under build/client is read as text and searched for every probe.
  (2) BULK — any .json shipped to the client above BULK_JSON_LIMIT bytes, and any single client file
      whose size explodes past FILE_SIZE_LIMIT. A corpus snapshot copied into the client output shows
      up as weight even if it is re-encoded and the probes miss it.
Probes shorter than the per-script minimum are dropped so that ordinary UI words cannot false-positive.

This gate belongs AFTER `npm run build`. With no prototype/build/client it prints SKIP and exits 0.
Reads the exported JSON only — never db/corpus.sqlite.

Usage: validate_no_client_leak.py [--root PATH] [--list N]
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
REPO_ROOT = Path(__file__).resolve().parents[2]

# A probe must be long enough that no UI label, route name or third-party string can match it by
# accident. Japanese carries far more meaning per character, so it gets the lower floor.
MIN_JP = 6
MIN_LATIN = 24
# The client bundle is UI code. Anything above these is a data file that should have stayed on the
# server (today's whole build/client is ~525 KB across 45 files).
BULK_JSON_LIMIT = 64 * 1024
FILE_SIZE_LIMIT = 512 * 1024

TAGS = re.compile(r"<[^>]+>")
CJK = re.compile(r"[぀-ヿ㐀-鿿]")
STRIDE_TARGET = 120     # ~this many probes per source family


def _read(p: Path):
    return json.loads(p.read_text(encoding="utf-8"))


def _records(d: Path) -> list[dict]:
    """Every record in corpus/<dir>/*.json.

    List-shaped files only: a corpus directory also holds hand-written companions that are objects,
    not registries (corpus/kanji/unregistered_chars.json is one), and a probe builder that assumed
    every *.json was a record list would crash the moment somebody added another.
    """
    out: list[dict] = []
    if not d.is_dir():
        return out
    for f in sorted(d.glob("*.json")):
        data = _read(f)
        if isinstance(data, list):
            out.extend(x for x in data if isinstance(x, dict))
    return out


def _sample(seq: list, target: int) -> list:
    """Deterministic stride sample — no RNG, so a failure is reproducible from the printed probe."""
    if len(seq) <= target:
        return list(seq)
    step = len(seq) // target
    return [seq[i] for i in range(0, len(seq), step)][:target]


def _pt(v) -> list[str]:
    """Every pt-BR string inside a locale object, whether it holds a string or a list of them."""
    if not isinstance(v, dict):
        return []
    x = v.get("pt-BR")
    if isinstance(x, str):
        return [x]
    if isinstance(x, list):
        return [s for s in x if isinstance(s, str)]
    return []


def build_probes(root: Path) -> list[tuple[str, str]]:
    """Return [(probe, where-it-came-from)], deterministically ordered."""
    corpus, course = root / "corpus", root / "course"
    raw: list[tuple[str, str]] = []

    sents = sorted(_records(corpus / "sentences"), key=lambda x: x.get("slug") or "")
    if sents:
        for s in _sample(sents, STRIDE_TARGET):
            if s.get("jp"):
                raw.append((s["jp"], f"sentence {s.get('slug')} jp"))
            for t in _pt(s.get("translation")):
                raw.append((t, f"sentence {s.get('slug')} translation"))

    vocab = _records(corpus / "vocab")
    for v in _sample(sorted(vocab, key=lambda x: x.get("slug") or ""), STRIDE_TARGET):
        for sense in v.get("senses") or []:
            for g in _pt(sense.get("gloss")):
                raw.append((g, f"vocab {v.get('slug')} gloss"))

    kanji = _records(corpus / "kanji")
    for k in _sample(sorted(kanji, key=lambda x: x.get("slug") or ""), STRIDE_TARGET):
        for m in _pt(k.get("meanings")):
            raw.append((m, f"kanji {k.get('slug')} meaning"))

    grammar = _records(corpus / "grammar")
    for g in _sample(sorted(grammar, key=lambda x: x.get("slug") or ""), STRIDE_TARGET):
        for field in ("label", "nuance"):
            for s in _pt(g.get(field)):
                raw.append((s, f"grammar {g.get('slug')} {field}"))

    lessons = sorted(course.glob("*/topic-*/lesson-*.json"))
    for f in _sample(lessons, STRIDE_TARGET):
        rec = _read(f)
        plain = TAGS.sub(" ", rec.get("body") or "")
        plain = re.sub(r"\s+", " ", plain).strip()
        if len(plain) > 40:
            raw.append((plain[:200], f"lesson {rec.get('id')} body"))

    probes, seen = [], set()
    for text, where in raw:
        text = text.strip()
        floor = MIN_JP if CJK.search(text) else MIN_LATIN
        if len(text) < floor or text in seen:
            continue
        seen.add(text)
        probes.append((text, where))
    return probes


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=str(REPO_ROOT), help="tree to validate (default: repo root)")
    ap.add_argument("--list", type=int, default=15, help="max FAIL lines to print")
    args = ap.parse_args()
    root = Path(args.root).resolve()
    client = root / "prototype" / "build" / "client"
    if not client.is_dir():
        print(f"validate_no_client_leak: SKIP — no {client}; run `npm run build` in prototype/ "
              "before this gate means anything")
        return 0

    probes = build_probes(root)
    if len(probes) < 300:
        print(f"  FAIL probe set is only {len(probes)} strings — the corpus did not load, so a clean "
              f"result would prove nothing")
        print(f"\nvalidate_no_client_leak: FAIL (probe set too small)")
        return 1

    files = sorted(p for p in client.rglob("*") if p.is_file())
    fails: list[str] = []
    total = 0
    for p in files:
        size = p.stat().st_size
        total += size
        rel = p.relative_to(client).as_posix()
        if p.suffix == ".json" and size > BULK_JSON_LIMIT:
            fails.append(f"{rel}: {size} bytes of JSON in the client bundle (limit {BULK_JSON_LIMIT})")
        if size > FILE_SIZE_LIMIT:
            fails.append(f"{rel}: {size} bytes (limit {FILE_SIZE_LIMIT}) — a data file, not UI code")
        text = p.read_text(encoding="utf-8", errors="ignore")
        for probe, where in probes:
            if probe in text:
                fails.append(f"{rel}: leaks {where} — {probe[:60]!r}")

    for f in fails[:args.list]:
        print("  FAIL", f)
    if len(fails) > args.list:
        print(f"  ... {len(fails) - args.list} more")
    print(f"\nvalidate_no_client_leak: {len(files)} files / {total} bytes under build/client, "
          f"{len(probes)} probes, "
          + (f"FAIL {len(fails)}" if fails else "ALL OK"))
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
