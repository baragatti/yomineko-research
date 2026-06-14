#!/usr/bin/env python3
"""Idempotent dataset fetcher for the Yomineko corpus build.

Used first in Phase R3 (source-coverage probing) and again in P1 (full ingestion).
Downloads the authoritative open datasets (spec Section 3) into research/datasets/,
computes SHA256, and writes a MANIFEST.md per source group. Re-running skips files
already present (size > 0). Network errors on optional sources are non-fatal.

Stdlib only (no third-party deps) so it can run before any venv is built.
"""
from __future__ import annotations

import datetime as _dt
import hashlib
import json
import os
import sys
import urllib.request
import urllib.error
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DATASETS = ROOT / "research" / "datasets"

UA = {"User-Agent": "yomineko-corpus-build/0.1 (dataset fetcher)"}
TIMEOUT = 120


def log(msg: str) -> None:
    print(msg, flush=True)


def http_get(url: str) -> bytes:
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
        return r.read()


def download(url: str, dest: Path, *, optional: bool = False) -> dict | None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    if dest.exists() and dest.stat().st_size > 0:
        log(f"  [skip] {dest.name} ({dest.stat().st_size:,} B) already present")
        return _record(url, dest)
    log(f"  [get ] {url}")
    try:
        req = urllib.request.Request(url, headers=UA)
        with urllib.request.urlopen(req, timeout=TIMEOUT) as r, open(dest, "wb") as f:
            total = 0
            while True:
                chunk = r.read(1 << 20)
                if not chunk:
                    break
                f.write(chunk)
                total += len(chunk)
        log(f"  [ok  ] {dest.name} ({total:,} B)")
        return _record(url, dest)
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError) as e:
        msg = f"  [FAIL] {dest.name}: {e}"
        log(msg)
        if dest.exists():
            dest.unlink(missing_ok=True)
        if optional:
            return None
        return {"url": url, "name": dest.name, "error": str(e)}


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _record(url: str, dest: Path) -> dict:
    return {
        "url": url,
        "name": dest.name,
        "path": str(dest.relative_to(ROOT)),
        "bytes": dest.stat().st_size,
        "sha256": sha256(dest),
    }


def latest_release_assets(repo: str) -> list[dict]:
    api = f"https://api.github.com/repos/{repo}/releases/latest"
    data = json.loads(http_get(api))
    return [{"name": a["name"], "url": a["browser_download_url"]} for a in data.get("assets", [])]


def write_manifest(group_dir: Path, records: list[dict]) -> None:
    today = _dt.date.today().isoformat()
    lines = [
        f"# Dataset manifest — {group_dir.name}",
        "",
        f"_Fetched {today}. Raw files are git-ignored; this manifest + checksums are tracked._",
        "",
        "| file | bytes | sha256 | url |",
        "|------|------:|--------|-----|",
    ]
    for r in records:
        if "error" in r:
            lines.append(f"| {r['name']} | — | ERROR: {r['error']} | {r['url']} |")
        else:
            lines.append(f"| {r['name']} | {r['bytes']:,} | `{r['sha256'][:16]}…` | {r['url']} |")
    (group_dir / "MANIFEST.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def fetch_group(repo: str, group: str, picks: list[tuple[str, str]]) -> list[dict]:
    """picks: list of (substring_match, kind) — first asset whose name contains the
    substring is downloaded. kind is just a label."""
    log(f"== {group} (github: {repo}) ==")
    out_dir = DATASETS / group
    records: list[dict] = []
    try:
        assets = latest_release_assets(repo)
    except Exception as e:  # noqa: BLE001
        log(f"  [FAIL] could not resolve release for {repo}: {e}")
        return [{"url": repo, "name": group, "error": f"release resolve failed: {e}"}]
    for substr, _kind in picks:
        match = next((a for a in assets if substr in a["name"]), None)
        if not match:
            log(f"  [warn] no asset matching '{substr}' in {repo}")
            records.append({"url": repo, "name": substr, "error": "asset not found"})
            continue
        rec = download(match["url"], out_dir / match["name"])
        if rec:
            records.append(rec)
    write_manifest(out_dir, records)
    return records


def fetch_fixed(group: str, urls: list[str], *, optional: bool = False) -> list[dict]:
    log(f"== {group} (fixed urls) ==")
    out_dir = DATASETS / group
    records: list[dict] = []
    for url in urls:
        name = url.split("/")[-1]
        rec = download(url, out_dir / name, optional=optional)
        if rec:
            records.append(rec)
    write_manifest(out_dir, records)
    return records


def main() -> int:
    DATASETS.mkdir(parents=True, exist_ok=True)
    all_records: dict[str, list[dict]] = {}

    # 1) jmdict-simplified: JMdict (full + common), Kanjidic2, Kradfile, Radkfile
    all_records["jmdict"] = fetch_group(
        "scriptin/jmdict-simplified",
        "jmdict",
        [
            ("jmdict-eng-common", "vocab-common"),
            ("kanjidic2-en", "kanji"),
            ("kradfile", "krad"),
            ("radkfile", "radk"),
        ],
    )
    # JMdict full (large) — best-effort, useful for P1; not required for R3 probe.
    try:
        assets = latest_release_assets("scriptin/jmdict-simplified")
        full = next(
            (a for a in assets if a["name"].startswith("jmdict-eng-3") and a["name"].endswith(".json.zip")),
            None,
        )
        if full:
            rec = download(full["url"], DATASETS / "jmdict" / full["name"], optional=True)
            if rec:
                all_records["jmdict"].append(rec)
                write_manifest(DATASETS / "jmdict", all_records["jmdict"])
    except Exception as e:  # noqa: BLE001
        log(f"  [warn] jmdict full skipped: {e}")

    # 2) KanjiVG — single XML (all kanji, stroke order + components)
    all_records["kanjivg"] = fetch_group(
        "KanjiVG/kanjivg",
        "kanjivg",
        [(".xml.gz", "stroke-order-xml")],
    )

    # 3) Tatoeba — sentences (jpn/eng/por), cross-language links, audio list
    base = "https://downloads.tatoeba.org/exports"
    all_records["tatoeba"] = fetch_fixed(
        "tatoeba",
        [
            f"{base}/per_language/jpn/jpn_sentences.tsv.bz2",
            f"{base}/per_language/eng/eng_sentences.tsv.bz2",
            f"{base}/per_language/por/por_sentences.tsv.bz2",
            f"{base}/links.tar.bz2",
            f"{base}/sentences_with_audio.tar.bz2",
        ],
    )

    # 4) JLPT community lists (best-effort; reconcile >=3 in P2). All optional.
    jlpt_urls = [
        # David Luz Gouveia kanji-data: kanji with reconstructed jlpt_new levels
        "https://raw.githubusercontent.com/davidluzgouveia/kanji-data/master/kanji.json",
        # open-anki-jlpt-decks: vocab CSVs per level (n5..n1)
        "https://raw.githubusercontent.com/jamsinclair/open-anki-jlpt-decks/main/src/data/n5-vocab.csv",
        "https://raw.githubusercontent.com/jamsinclair/open-anki-jlpt-decks/main/src/data/n4-vocab.csv",
        "https://raw.githubusercontent.com/jamsinclair/open-anki-jlpt-decks/main/src/data/n5-kanji.csv",
        "https://raw.githubusercontent.com/jamsinclair/open-anki-jlpt-decks/main/src/data/n4-kanji.csv",
        # jlpt-vocab community list (elzup)
        "https://raw.githubusercontent.com/elzup/jlpt-word-list/master/src/n5.csv",
        "https://raw.githubusercontent.com/elzup/jlpt-word-list/master/src/n4.csv",
    ]
    all_records["jlpt"] = fetch_fixed("jlpt", jlpt_urls, optional=True)

    # summary
    log("\n== SUMMARY ==")
    for group, recs in all_records.items():
        ok = sum(1 for r in recs if "error" not in r)
        bad = sum(1 for r in recs if "error" in r)
        total = sum(r.get("bytes", 0) for r in recs if "error" not in r)
        log(f"  {group}: {ok} ok, {bad} failed, {total:,} B")
    log("done.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
