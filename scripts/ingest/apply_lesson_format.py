#!/usr/bin/env python3
"""Apply reformatted lesson bodies produced by reauthor_lesson_format_workflow.js, with HARD deterministic
guardrails so a bad rewrite can never silently corrupt a lesson. For each `<slug>.body.txt` in the scratch dir
it checks the new body against the ORIGINAL lesson JSON:
  - structural refs (<sentence>/<exercise>/<reading>) preserved EXACTLY (same set);
  - grammar/vocab/kanji refs are a SUBSET of the original (no invented refs -> no known-set break);
  - ends with <checklist>…</checklist>; no em dash; no backslash; only whitelisted tags;
  - all <X ref=...> namespaces valid.
Only bodies that pass ALL checks (and, if --passed given, are in the verifier-approved list) are written into
research/derived/lessons/<file>. Everything else is skipped and reported. Idempotent.
Usage: apply_lesson_format.py [--passed research/derived/reauthor/lesson_format/_passed.json] [--dry-run]"""
from __future__ import annotations
import argparse, json, re, sys
from pathlib import Path
sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
ROOT = Path(__file__).resolve().parents[2]
LESSONS = ROOT / "research" / "derived" / "lessons"
SCRATCH = ROOT / "research" / "derived" / "reauthor" / "lesson_format"

REF_RX = re.compile(r'<(grammar|vocab|kanji|sentence|exercise|reading)\s+ref="([^"]+)"')
TAG_RX = re.compile(r'</?([a-zA-Z][\w-]*)')
WHITELIST = {"heading", "p", "note", "list", "item", "image", "video", "audio", "sentence", "stroke",
             "reading", "exercise", "flashcard", "front", "back", "checklist", "check", "divider",
             "text", "jp", "ruby", "romaji", "term", "emphasis", "kanji", "vocab", "grammar", "break"}
# the structural refs that MUST be preserved exactly (pedagogically placed); the rest may be a subset
STRUCT = {"sentence", "exercise", "reading"}


NESTED_TEXT = re.compile(r"<text>\s*(<text\b[^>]*>[^<]*</text>)\s*</text>")


def normalize_body(b: str) -> str:
    """Deterministic fixups for benign AI malformations. Currently: unwrap a <text> that wraps a single
    <text> element (e.g. <text><text weight="bold">X</text></text> -> <text weight="bold">X</text>), which
    validate_lessons rejects (text children must be plain strings)."""
    prev = None
    while prev != b:
        prev = b
        b = NESTED_TEXT.sub(r"\1", b)
    return b


def refs_by_kind(body: str) -> dict:
    out: dict = {}
    for kind, ref in REF_RX.findall(body):
        out.setdefault(kind, set()).add(ref)
    return out


def check(orig_body: str, new_body: str) -> list[str]:
    errs: list[str] = []
    o, n = refs_by_kind(orig_body), refs_by_kind(new_body)
    for k in STRUCT:
        if o.get(k, set()) != n.get(k, set()):
            errs.append(f"{k} refs changed: missing={sorted(o.get(k,set())-n.get(k,set()))} "
                        f"added={sorted(n.get(k,set())-o.get(k,set()))}")
    for k in ("grammar", "vocab", "kanji"):
        extra = n.get(k, set()) - o.get(k, set())
        if extra:
            errs.append(f"invented {k} refs: {sorted(extra)}")
    tags = {t.lower() for t in TAG_RX.findall(new_body)}
    bad = tags - WHITELIST
    if bad:
        errs.append(f"non-whitelisted tags: {sorted(bad)}")
    if "<checklist>" not in new_body or not new_body.rstrip().endswith("</checklist>"):
        errs.append("must end with <checklist>…</checklist>")
    if "—" in new_body:
        errs.append("contains em dash")
    if "\\" in new_body:
        errs.append("contains backslash")
    if not new_body.strip():
        errs.append("empty body")
    return errs


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--passed", default="")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    passed = None
    if args.passed and Path(args.passed).exists():
        passed = set(json.loads(Path(args.passed).read_text(encoding="utf-8")))
    # map sanitized-slug -> lesson file (the scratch files are named slug.replace(/[^a-z0-9]+/i,'_'))
    sani = {}
    for lp in LESSONS.glob("*.json"):
        try:
            slug = json.loads(lp.read_text(encoding="utf-8")).get("slug", "")
        except Exception:
            continue
        if slug:
            sani[re.sub(r"[^a-zA-Z0-9]+", "_", slug)] = (slug, lp)
    applied, skipped = [], []
    for txt in sorted(SCRATCH.glob("*.body.txt")):
        key = txt.name[:-len(".body.txt")]
        if key not in sani:
            skipped.append((key, "no matching lesson")); continue
        slug, lp = sani[key]
        if passed is not None and slug not in passed:
            skipped.append((slug, "not in verifier-approved list")); continue
        d = json.loads(lp.read_text(encoding="utf-8"))
        new_body = normalize_body(txt.read_text(encoding="utf-8").strip())
        errs = check(d.get("body", ""), new_body)
        if errs:
            skipped.append((slug, "; ".join(errs))); continue
        if not args.dry_run:
            d["body"] = new_body
            d["needs_review"] = True  # Layer-C reformat -> teacher sign-off
            lp.write_text(json.dumps(d, ensure_ascii=False, indent=2), encoding="utf-8")
        applied.append(slug)
    print(f"apply_lesson_format ({'dry-run' if args.dry_run else 'applied'}): {len(applied)} applied, "
          f"{len(skipped)} skipped")
    for slug, why in skipped:
        print(f"  SKIP {slug}: {why}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
