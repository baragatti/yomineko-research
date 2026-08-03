#!/usr/bin/env python3
"""Render the COMPLETE Phase-3 sentence patch as a before/after diff, without touching the DB.

Consolidates all three apply sources into one in-memory projection per sentence:
  1. phase3_sentences_patch.json   — 3,033 deterministic auto ops (modes: replace / substring / locale_note)
  2. phase3_manual_apply.json      — 119 verifier-clean manual ops (no jp changes)
  3. the whitespace/kigou class    — same rule as fable5_fix_whitespace_tokens.py (69 sentences)

Then it CHECKS THE HARD INVARIANTS on the projected result, which is the real point of this pass:
  I1  concat(C-token surfaces) == jp
  I2  kana   == concat(C-token readings)
  I3  romaji == concat(C-token romaji)
  I4  no op's `current` anchor drifted from the live DB value (stale-patch protection)
  I5  no learner-facing field left empty, and no build metadata (coverage/cobertura) survives
Any violation is reported per sentence and the sentence is marked unsafe; a clean run means the patch can
be applied without breaking validate_display_consistency / validate_groundtruth.

Outputs: phase3_diff/<key>.json audit batches + phase3_diff_report.json (counts + every violation).
Usage: fable5_sentences_render_diff.py [--per-batch 25]
"""
from __future__ import annotations
import argparse, json, re, sqlite3, sys
from collections import Counter
from pathlib import Path
sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts" / "validate"))
from validate_groundtruth import kana2romaji  # noqa: E402  (project romanizer, single source of truth)
FD = ROOT / "research" / "derived" / "fable5_validation"
OUT = FD / "phase3_diff"
TEXT_FIELDS = {"translation", "translation_literal", "structure_explanation"}
TOKEN_LOCALIZED = {"gloss", "role", "conjugation_note"}
META_RE = re.compile(r"\bcoverage\b|\bcobertura\b", re.I)
# Some findings phrased their `fix` as an INSTRUCTION ("tokens[0].r: X -> Y", "null (space token has no
# reading)", "same fix for tokens[6].r") instead of the replacement VALUE. Writing those verbatim puts
# ASCII path text inside a kana/reading field (audit round 1 caught 95 criticals of exactly this).
# Detect conservatively: a bare arrow is legitimate inside a conjugation note ("大きい -> 大きくて"),
# so only unambiguous instruction markers count.
INSTRUCTION_RE = re.compile(r"tokens\[|^null\b|same fix for|\bshould be\b|\bmust be\b|"
                            r"^\(?(remove|delete|merge)\b|and update|the same token|\byields\b", re.I)
# Structural guards on the RESULT (keyword matching on the input can always be phrased around):
# a phonetic kana field must contain no Latin letters, and romaji no kana/CJK.
LATIN_RE = re.compile(r"[A-Za-z]")
JP_RE = re.compile(r"[぀-ヿ一-鿿]")


def load_sentence(con, slug):
    row = con.execute("SELECT id, jp, kana, romaji, COALESCE(ai_generated,0) FROM sentence WHERE slug=?",
                      (slug,)).fetchone()
    if not row:
        return None
    sid, jp, kana, romaji, gen = row
    texts = {}
    for field, locale, value in con.execute(
            "SELECT field, locale, value FROM localized_text WHERE entity_type='sentence' AND entity_id=?",
            (sid,)):
        texts.setdefault(field, {})[locale] = value
    # CRITICAL: finder/patch token indices are in the BATCH-FILE order the splitter emitted, which is
    # ORDER BY split_mode, position, id -- i.e. the atomic 'A' sub-tokens come BEFORE the 'C' display
    # tokens, so an index can even point at an A row. Indexing by DB C-order would edit the wrong token
    # (caught as ANCHOR_DRIFT on 61 ops). Load in batch order; compute invariants from the C subset only.
    tokens = []
    for tid, mode, surf, read, rom in con.execute(
            "SELECT id, split_mode, surface, reading, romaji FROM token WHERE sentence_id=? "
            "ORDER BY split_mode, position, id", (sid,)):
        loc = {}
        for field, locale, value in con.execute(
                "SELECT field, locale, value FROM localized_text WHERE entity_type='token' AND entity_id=?",
                (tid,)):
            loc.setdefault(field, {})[locale] = value
        tokens.append({"id": tid, "mode": mode, "surface": surf, "reading": read or "",
                       "romaji": rom or "", **loc})
    return {"id": sid, "jp": jp, "kana": kana, "romaji": romaji, "gen": bool(gen),
            "texts": texts, "tokens": tokens}


PUNCT_MAP = str.maketrans({"、": ",", "。": ".", "！": "!", "？": "?", "・": "-"})


def corpus_romaji(cur, nxt):
    """Romanize ONE token's reading the way this corpus does it.

    kana2romaji() alone diverges from the committed convention in three ways, so patching a reading with
    it silently rewrites style: (1) it expands the katakana長音 ー that the bank keeps as '-', (2) it
    leaves Japanese punctuation, which commit aeec3ac ASCII-ized corpus-wide, (3) it drops the
    apostrophe after a syllabic ん before a vowel/y. Gemination is handled at the BOUNDARY (だっ|た ->
    'dat'+'ta', never 'daxtsu'+'ta') by romanizing (cur+nxt) and stripping the next token's own romaji."""
    if not cur:
        return ""
    if nxt:
        joined, tail = kana2romaji(cur + nxt), kana2romaji(nxt)
        base = joined[:-len(tail)] if tail and joined.endswith(tail) else kana2romaji(cur)
    else:
        base = kana2romaji(cur)
    # keep the bank's long-vowel dash instead of kana2romaji's vowel doubling
    if "ー" in cur:
        base = "".join(("-" if ch == "ー" else kana2romaji(ch)) for ch in cur)
    # NOTE: do NOT insert an apostrophe after ん. Audit round 2 caught that as a regression -- it turned
    # なんじ into "n'anji" -- and the bank uses no apostrophes at all in sentence romaji (0 occurrences
    # across all 5,565 rows; cf. kouennikuru, gaikokujinno). The vocab table's an'i/ten'in convention is a
    # DIFFERENT field with a different rule.
    return base.translate(PUNCT_MAP)


def romanize_chain(cs):
    """Romanize each C token IN CONTEXT. kana2romaji() alone renders a trailing small tsu as 'xtsu'
    (IME style), so だっ|た romanized per token gives 'daxtsu'+'ta'. Gemination is a property of the
    BOUNDARY, so romanize (this + next) and strip the next token's own romaji off the end; the pieces
    still concatenate to the joined romanization, preserving romaji == concat(token romaji)."""
    out = []
    for i, t_ in enumerate(cs):
        cur = t_["reading"] or ""
        nxt = cs[i + 1]["reading"] if i + 1 < len(cs) else ""
        if not nxt:
            out.append(kana2romaji(cur))
            continue
        joined, tail = kana2romaji(cur + nxt), kana2romaji(nxt)
        out.append(joined[:-len(tail)] if tail and joined.endswith(tail) else kana2romaji(cur))
    return out


def c_tokens_of(rec):
    """c_tokens() for a plain (already-copied) record dict."""
    return [t for t in rec["tokens"] if t["mode"] == "C"]


def c_tokens(rec):
    """The display granularity: the only tokens the kana/romaji/jp invariants are computed over."""
    return [t for t in rec["tokens"] if t["mode"] == "C"]


def get_at(rec, path):
    p0 = path[0]
    if p0 in ("jp", "kana", "romaji"):
        return rec[p0]
    if p0 in TEXT_FIELDS:
        return rec["texts"].get(p0, {}).get(path[1])
    if p0 == "tokens":
        t = rec["tokens"][path[1]] if path[1] < len(rec["tokens"]) else None
        if t is None:
            return None
        attr = path[2]
        if attr in ("reading", "romaji", "surface"):
            return t[attr]
        if len(path) == 3:
            return t.get(attr)
        return (t.get(attr) or {}).get(path[3])
    return None


def set_at(rec, path, value):
    p0 = path[0]
    if p0 in ("jp", "kana", "romaji"):
        rec[p0] = value
        return True
    if p0 in TEXT_FIELDS:
        rec["texts"].setdefault(p0, {})[path[1]] = value
        return True
    if p0 == "tokens":
        if path[1] >= len(rec["tokens"]):
            return False
        t = rec["tokens"][path[1]]
        attr = path[2]
        if attr in ("reading", "romaji", "surface"):
            t[attr] = value
            return True
        if len(path) == 3:
            t[attr] = value
            return True
        t.setdefault(attr, {})[path[3]] = value
        return True
    return False


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--per-batch", type=int, default=25)
    args = ap.parse_args()
    con = sqlite3.connect(ROOT / "db" / "corpus.sqlite")

    auto = json.loads((FD / "phase3_sentences_patch.json").read_text(encoding="utf-8"))["sentences"]
    manual = json.loads((FD / "phase3_manual_apply.json").read_text(encoding="utf-8"))["sentences"]
    # str.strip() (not SQL TRIM) so the ideographic space U+3000 is caught too
    ws_sids = {sid for sid, surf in con.execute(
        "SELECT sentence_id, surface FROM token WHERE split_mode='C'") if surf.strip() == ""}
    ws_slugs = {r[0] for r in con.execute(
        f"SELECT slug FROM sentence WHERE id IN ({','.join('?' * len(ws_sids))})", tuple(ws_sids))} \
        if ws_sids else set()

    ops_by_slug = {}
    for s in auto:
        ops_by_slug.setdefault(s["slug"], []).extend([{**o, "src": "auto"} for o in s["ops"]])
    for s in manual:
        ops_by_slug.setdefault(s["slug"], []).extend([{**o, "src": "manual"} for o in s["ops"]])
    for extra in ("phase3_author151_repairs.json",):
        f_ = FD / extra
        if f_.exists():
            for s in json.loads(f_.read_text(encoding="utf-8"))["sentences"]:
                ops_by_slug.setdefault(s["slug"], []).extend(
                    [{**o, "src": "author151"} for o in s["ops"]])
    repairs_f = FD / "phase3_audit_repairs.json"
    if repairs_f.exists():
        for s in json.loads(repairs_f.read_text(encoding="utf-8"))["sentences"]:
            # appended last so they land on top of the base op for the same field
            ops_by_slug.setdefault(s["slug"], []).extend([{**o, "src": "audit_repair"} for o in s["ops"]])
    for slug in ws_slugs:
        ops_by_slug.setdefault(slug, []).append({"src": "whitespace", "mode": "whitespace_class",
                                                 "field": "tokens/jp/kana/romaji",
                                                 "issue": "whitespace token glossed 記号/きごう leaks a "
                                                          "phantom word into kana+romaji"})

    diffs, violations, cascaded, unsafe = [], [], set(), []
    for slug in sorted(ops_by_slug):
        rec = load_sentence(con, slug)
        if not rec:
            violations.append({"slug": slug, "code": "MISSING", "detail": "sentence not in DB"})
            continue
        before = json.loads(json.dumps(rec))
        notes = []
        for op in ops_by_slug[slug]:
            mode = op.get("mode")
            if mode == "whitespace_class":
                # Blank the phantom reading only. Deleting the space from jp merged separate sentences
                # (audit round 3), and U+3000 is legitimate Japanese punctuation, so jp is never touched.
                for t in rec["tokens"]:
                    if t["surface"].strip() == "":
                        t["reading"] = ""
                        t["romaji"] = ""
                cs_ws = c_tokens(rec)
                rec["kana"] = "".join(t["reading"] for t in cs_ws)
                rec["romaji"] = "".join(t["romaji"] for t in cs_ws)
                continue
            if isinstance(op.get("fix"), str) and INSTRUCTION_RE.search(op["fix"]):
                notes.append({"code": "I6_INSTRUCTION_AS_VALUE", "field": op.get("field"),
                              "fix": op["fix"][:120]})
                continue
            path = op["path"]
            cur = get_at(rec, path)
            if mode == "replace":
                if op.get("current") is not None and cur is not None and cur != op["current"] \
                        and op["src"] == "auto":
                    notes.append({"code": "ANCHOR_DRIFT", "field": op.get("field"),
                                  "db": str(cur)[:120], "expected": str(op["current"])[:120]})
                set_at(rec, path, op["fix"])
            elif mode == "substring":
                if cur is None or op["current"] not in cur:
                    notes.append({"code": "SUBSTRING_NOT_FOUND", "field": op.get("field"),
                                  "needle": str(op["current"])[:120]})
                else:
                    set_at(rec, path, cur.replace(op["current"], op["fix"], 1))
            elif mode == "locale_note":
                for loc, val in op["fix"].items():
                    set_at(rec, path + [loc], val)

        # ---- CASCADE: a corrected reading must propagate, or the record desyncs ----
        # The patch fixes sentence kana/romaji and token readings independently; without this step the
        # projection breaks I2/I3 on ~350 sentences. Token romaji is derived from the token's reading, and
        # the sentence's phonetic fields are the concatenation over the C tokens (verified invariant).
        touched_reading = any(o.get("path") and o["path"][0] == "tokens" and len(o["path"]) > 2
                              and o["path"][2] == "reading" for o in ops_by_slug[slug]
                              if o.get("mode") != "whitespace_class")
        touched_kana = any(o.get("path") == ["kana"] or o.get("path") == ["romaji"]
                           for o in ops_by_slug[slug] if o.get("mode") != "whitespace_class")
        if touched_reading or touched_kana:
            cs = c_tokens(rec)
            if touched_reading:
                # Recompute ONLY the tokens whose reading changed. Regenerating the whole string rewrote
                # untouched tokens into a different romanization style (audit round 1: 206 objections of
                # exactly that collateral drift), so the original values must survive.
                before_read = {t["id"]: t["reading"] for t in c_tokens_of(before)}
                for i, t in enumerate(cs):
                    if before_read.get(t["id"]) != t["reading"]:
                        nxt = cs[i + 1]["reading"] if i + 1 < len(cs) else ""
                        t["romaji"] = corpus_romaji(t["reading"], nxt)
                rec["kana"] = "".join(t["reading"] for t in cs)
            rec["romaji"] = "".join(t["romaji"] for t in cs)
            cascaded.add(slug)

        # ---- hard invariants on the projected result (C granularity only) ----
        cs = c_tokens(rec)
        cat_surface = "".join(t["surface"] for t in cs)
        if cat_surface != rec["jp"]:
            notes.append({"code": "I1_SURFACE_NE_JP", "jp": rec["jp"], "concat": cat_surface})
        cat_read = "".join(t["reading"] for t in cs)
        if cat_read != rec["kana"]:
            notes.append({"code": "I2_KANA_NE_READINGS", "kana": rec["kana"], "concat": cat_read})
        cat_rom = "".join(t["romaji"] for t in cs)
        if cat_rom != rec["romaji"]:
            notes.append({"code": "I3_ROMAJI_NE_TOKENS", "romaji": rec["romaji"], "concat": cat_rom})
        if LATIN_RE.search(rec["kana"] or ""):
            notes.append({"code": "I7_LATIN_IN_KANA", "kana": rec["kana"][:120]})
        if JP_RE.search(rec["romaji"] or ""):
            notes.append({"code": "I8_JP_IN_ROMAJI", "romaji": rec["romaji"][:120]})
        for t_ in cs:
            if LATIN_RE.search(t_["reading"] or ""):
                notes.append({"code": "I7_LATIN_IN_KANA", "token_reading": t_["reading"][:80]})
                break
        for f, locs in rec["texts"].items():
            for loc, v in locs.items():
                if not (v or "").strip():
                    notes.append({"code": "I5_EMPTY_TEXT", "field": f"{f}.{loc}"})
                elif META_RE.search(v or ""):
                    notes.append({"code": "I5_METADATA_LEAK", "field": f"{f}.{loc}",
                                  "text": (v or "")[:160]})
        if notes:
            violations.append({"slug": slug, "notes": notes})
        # Structural invariants are non-negotiable: if the projection breaks I1/I2/I3 the sentence is NOT
        # safe to apply as field edits (it needs re-dissection), so keep it out of the applied set.
        if any(n["code"].startswith(("I1_", "I2_", "I3_", "I6_")) for n in notes):
            unsafe.append({"slug": slug, "codes": sorted({n["code"] for n in notes
                                                          if n["code"].startswith(("I1_", "I2_", "I3_", "I6_", "I7_", "I8_"))}),
                           "detail": [n for n in notes if not n["code"].startswith("I5_")]})
            continue
        diffs.append({"slug": slug, "gen": rec["gen"], "sources": sorted({o["src"] for o in ops_by_slug[slug]}),
                      "ops": [{"field": o.get("field"), "severity": o.get("severity"),
                               "issue": (o.get("issue") or "")[:400], "src": o["src"]}
                              for o in ops_by_slug[slug]],
                      "before": {"jp": before["jp"], "kana": before["kana"], "romaji": before["romaji"],
                                 "texts": before["texts"],
                                 "tokens": [{"i": i, "s": t["surface"], "r": t["reading"],
                                             "gloss": t.get("gloss"), "role": t.get("role"),
                                             "note": t.get("conjugation_note")}
                                            for i, t in enumerate(before["tokens"])]},
                      "after": {"jp": rec["jp"], "kana": rec["kana"], "romaji": rec["romaji"],
                                "texts": rec["texts"],
                                "tokens": [{"i": i, "s": t["surface"], "r": t["reading"],
                                            "gloss": t.get("gloss"), "role": t.get("role"),
                                            "note": t.get("conjugation_note")}
                                           for i, t in enumerate(rec["tokens"])]},
                      "violations": notes})
    con.close()

    OUT.mkdir(parents=True, exist_ok=True)
    for f in OUT.glob("*.json"):
        f.unlink()
    keys = []
    for n in range(0, len(diffs), args.per_batch):
        key = f"d{n // args.per_batch:03d}"
        (OUT / f"{key}.json").write_text(
            json.dumps({"sentences": diffs[n:n + args.per_batch]}, ensure_ascii=False, indent=1),
            encoding="utf-8")
        keys.append(key)

    codes = Counter(n["code"] for v in violations for n in v.get("notes", []))
    (FD / "phase3_diff_report.json").write_text(json.dumps(
        {"sentences": len(diffs), "batches": len(keys), "keys": keys, "cascaded": len(cascaded),
         "sentences_with_violations": len(violations), "violation_codes": dict(codes),
         "violations": violations}, ensure_ascii=False, indent=1), encoding="utf-8")
    (FD / "phase3_unsafe_quarantine.json").write_text(json.dumps(
        {"note": "Projected result breaks a structural invariant (concat(surfaces)==jp, kana==concat("
                 "readings), romaji==concat(token romaji)). Excluded from the apply; needs re-dissection "
                 "or a hand fix.", "sentences": unsafe}, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"quarantined (structural invariant): {len(unsafe)}")
    print(f"diff rendered: {len(diffs)} sentences -> {len(keys)} audit batches")
    print(f"cascade-recomputed (token romaji + sentence kana/romaji): {len(cascaded)}")
    print(f"sentences with invariant violations: {len(violations)}")
    print("violation codes:", dict(codes) or "NONE")
    return 0


if __name__ == "__main__":
    sys.exit(main())
