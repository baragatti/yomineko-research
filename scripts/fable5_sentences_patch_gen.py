#!/usr/bin/env python3
"""Phase-3 sentence QA: findings -> anchored patch ops (vocab-pipeline pattern).

Reads every research/derived/fable5_validation/phase3_sentences_wave*.json,
keeps verdict == 'confirmed' findings only, and emits

    research/derived/fable5_validation/phase3_sentences_patch.json

with per-SENTENCE op groups — never per-field apply, because kana / romaji /
expl / tokens cascade together (e.g. 何時 いつ→なんじ touches 6 fields of one
sentence). Everything the guard rails reject lands in the same file's
`manual` queue with a machine-readable reason.

Guard rails (policy lives HERE; the apply script obeys the patch file):
  - `jp` is never auto-patched. A confirmed jp defect sends the WHOLE sentence
    to manual (`jp_reauthor`) and suppresses its other auto ops — a jp change
    invalidates kana/romaji/tokens/translations, so the unit is re-dissection.
  - `tokens[i].s` (surface) is never auto-patched (`surface_retokenize`):
    surfaces must concatenate back to jp, so changing one means retokenizing.
  - Anchor check: the finding's `current` must match the live bank value
    (exact, else NFC+strip). If it instead matches a UNIQUE substring of the
    live value, the op becomes mode='substring' (targeted snippet replace) —
    finders quote only the defective snippet of long expl_* texts. A
    non-unique substring -> `anchor_ambiguous_substring`; no match ->
    `anchor_mismatch`.
  - tokens[i].note is a locale OBJECT {pt-BR, en} in the bank; finders flatten
    it as 'pt-BR: X / en: Y'. When current parses back to the live object the
    op becomes mode='locale_note' with a parsed {pt-BR, en} fix; when current
    equals exactly one locale's value the op targets that key only.
  - Same (slug, field) hit by two different fixes -> `field_collision` (both
    go manual; the second fix was authored against the original text, not the
    first fix's output).
  - Empty / meta / ambiguous fixes -> manual.
  - Cascade flags per sentence (for the adversarial audit + apply step):
    token reading changed -> token.romaji recompute + sentence kana/romaji
    check; kana<->romaji desync; expl/lit/translation pair desync; sentence
    referenced by exam banks (deterministic banks need regen after apply;
    listening_reply prompts are byte-verbatim bank sentences).

MANUAL-RESOLUTION NOTE (split_mode blind spot): the bank stores TWO
tokenization granularities per sentence — split_mode 'A' atomic sub-tokens
(gloss-less, sharing a position) alongside 'C' compound display tokens
(e.g. 消し+ゴム(A) next to 消しゴム(C)). The finder batch projection dropped
split_mode/position, so finders report "duplicated tokens with null glosses"
(お+金+お金, 高校+生+高校生, …). Those are INTENTIONAL structure, not defects;
they cannot anchor to a single field so they land here in `manual` — refute
them during manual resolution instead of "fixing" the token array.
"""
import collections
import glob
import json
import os
import re
import unicodedata

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
VAL = os.path.join(ROOT, "research", "derived", "fable5_validation")
OUT = os.path.join(VAL, "phase3_sentences_patch.json")

TOKEN_FIELD = re.compile(r"^tokens\[(\d+)\]\.(s|r|en|pt|role|note)$")
SIMPLE_PATHS = {
    "jp": ("jp",),
    "kana": ("kana",),
    "romaji": ("romaji",),
    "en": ("translation", "en"),
    "pt": ("translation", "pt-BR"),
    "lit_en": ("translation_literal", "en"),
    "lit_pt": ("translation_literal", "pt-BR"),
    "expl_en": ("structure_explanation", "en"),
    "expl_pt": ("structure_explanation", "pt-BR"),
}
TOKEN_PATHS = {
    "s": ("surface",),
    "r": ("reading",),
    "en": ("gloss", "en"),
    "pt": ("gloss", "pt-BR"),
    "role": ("role", "pt-BR"),
    "note": ("conjugation_note",),
}
META_FIXES = {"n/a", "none", "no change", "ok", "correct", "unchanged", "remove", "delete"}
SEV_ORDER = {"critical": 0, "major": 1, "minor": 2}


def nrm(x):
    return unicodedata.normalize("NFC", x).strip() if isinstance(x, str) else x


def dig(obj, path):
    cur = obj
    for k in path:
        if cur is None:
            return None
        cur = cur.get(k) if isinstance(cur, dict) else None
    return cur


def resolve(sentence, field):
    """-> (kind, json_path_tuple, live_value) or (None, None, reason)."""
    if field in SIMPLE_PATHS:
        p = SIMPLE_PATHS[field]
        return "simple", p, dig(sentence, p)
    m = TOKEN_FIELD.match(field)
    if not m:
        return None, None, "bad_field"
    idx, sub = int(m.group(1)), m.group(2)
    toks = sentence.get("tokens") or []
    if idx >= len(toks):
        return None, None, "bad_token_index"
    p = TOKEN_PATHS[sub]
    return "token", ("tokens", idx) + p, dig(toks[idx], p)


def exam_bank_refs():
    """slug -> sorted list of exam bank files that mention it."""
    refs = collections.defaultdict(set)
    for path in sorted(glob.glob(os.path.join(ROOT, "corpus", "exam_banks", "*.json"))):
        raw = open(path, encoding="utf-8").read()
        rel = os.path.relpath(path, ROOT)
        for slug in set(re.findall(r"sent:[a-z0-9-]+", raw)):
            refs[slug].add(rel)
    return {k: sorted(v) for k, v in refs.items()}


def main():
    wave_files = sorted(glob.glob(os.path.join(VAL, "phase3_sentences_wave*_batches*.json")))
    if not wave_files:
        raise SystemExit("no wave files found")
    bank = {s["slug"]: s for s in json.load(open(os.path.join(ROOT, "corpus", "sentences", "bank.json"), encoding="utf-8"))}
    refs = exam_bank_refs()

    findings = []
    per_wave = {}
    for wf in wave_files:
        data = json.load(open(wf, encoding="utf-8"))
        fs = data.get("findings") or []
        per_wave[os.path.basename(wf)] = {
            "total": len(fs),
            "confirmed": sum(1 for f in fs if f.get("verdict") == "confirmed"),
        }
        findings.extend(f for f in fs if f.get("verdict") == "confirmed")

    stats = collections.Counter()
    stats["confirmed_in"] = len(findings)

    # exact-duplicate dedupe (same slug+field+fix)
    seen = set()
    deduped = []
    for f in findings:
        key = (f["slug"], f["field"], nrm(f.get("fix")))
        if key in seen:
            stats["dupe_dropped"] += 1
            continue
        seen.add(key)
        deduped.append(f)

    # (slug, field) collision detection — different fixes on the same field
    by_sf = collections.defaultdict(list)
    for f in deduped:
        by_sf[(f["slug"], f["field"])].append(f)

    manual = []
    auto_by_slug = collections.defaultdict(list)

    def to_manual(f, reason, extra=None):
        stats["manual_" + reason] += 1
        entry = {"slug": f["slug"], "field": f["field"], "reason": reason, "finding": f}
        if extra:
            entry.update(extra)
        manual.append(entry)

    for (slug, field), fs in sorted(by_sf.items()):
        if len(fs) > 1:
            for f in fs:
                to_manual(f, "field_collision")
            continue
        f = fs[0]
        s = bank.get(slug)
        if s is None:
            to_manual(f, "missing_sentence")
            continue
        fix = f.get("fix")
        if not isinstance(fix, str) or not fix.strip() or fix.strip().lower() in META_FIXES:
            to_manual(f, "empty_or_meta_fix")
            continue
        if " OR " in fix or "||" in fix:
            to_manual(f, "ambiguous_fix")
            continue
        kind, path, live = resolve(s, field)
        if kind is None:
            to_manual(f, live)  # live carries the reason string
            continue
        if field == "jp":
            to_manual(f, "jp_reauthor")
            continue
        if kind == "token" and path[-1] == "surface":
            to_manual(f, "surface_retokenize")
            continue
        cur = f.get("current")
        op = None
        if isinstance(live, dict):
            # locale-object field (conjugation_note): {pt-BR, en}
            m = re.match(r"^pt-BR:\s*(.*?)\s*/\s*en:\s*(.*)$", cur or "", re.S)
            if m and nrm(m.group(1)) == nrm(live.get("pt-BR")) and nrm(m.group(2)) == nrm(live.get("en")):
                fm = re.match(r"^pt-BR:\s*(.*?)\s*/\s*en:\s*(.*)$", fix, re.S)
                if not fm:
                    to_manual(f, "locale_note_fix_unparseable", {"live_value": live})
                    continue
                op = {"mode": "locale_note", "path": list(path),
                      "current": live, "fix": {"pt-BR": fm.group(1), "en": fm.group(2)}}
            else:
                hit = [k for k in ("pt-BR", "en") if nrm(live.get(k)) == nrm(cur)]
                if len(hit) == 1:
                    op = {"mode": "replace", "path": list(path) + hit,
                          "current": live[hit[0]], "fix": fix}
                else:
                    to_manual(f, "anchor_mismatch", {"live_value": live})
                    continue
        elif nrm(live) == nrm(cur):
            if nrm(live) == nrm(fix):
                stats["noop_dropped"] += 1
                continue
            op = {"mode": "replace", "path": list(path), "current": live, "fix": fix}
        else:
            if nrm(live) == nrm(fix):
                stats["already_applied"] += 1
                continue
            snippet = cur if isinstance(cur, str) and isinstance(live, str) and cur and cur in live else None
            if snippet is None and isinstance(cur, str) and isinstance(live, str) and cur.strip() and cur.strip() in live:
                snippet = cur.strip()
            if snippet is not None:
                n = live.count(snippet)
                if n == 1:
                    if snippet == fix or live.replace(snippet, fix, 1) == live:
                        stats["noop_dropped"] += 1
                        continue
                    op = {"mode": "substring", "path": list(path),
                          "current": snippet, "fix": fix, "full_before": live}
                else:
                    to_manual(f, "anchor_ambiguous_substring", {"live_value": live, "occurrences": n})
                    continue
            else:
                to_manual(f, "anchor_mismatch", {"live_value": live})
                continue
        op.update({"field": field, "severity": f.get("severity"),
                   "confidence": f.get("confidence"), "issue": f.get("issue")})
        auto_by_slug[slug].append(op)

    # a confirmed jp defect suppresses the sentence's other auto ops
    jp_slugs = {m["slug"] for m in manual if m["reason"] == "jp_reauthor"}
    for slug in sorted(jp_slugs):
        for op in auto_by_slug.pop(slug, []):
            stats["manual_suppressed_by_jp_reauthor"] += 1
            manual.append({"slug": slug, "field": op["field"],
                           "reason": "suppressed_by_jp_reauthor", "finding": op})

    sentences = []
    flag_hist = collections.Counter()
    for slug in sorted(auto_by_slug):
        ops = sorted(auto_by_slug[slug], key=lambda o: (SEV_ORDER.get(o["severity"], 9), o["field"]))
        fields = {o["field"] for o in ops}
        flags = []
        token_r = any(TOKEN_FIELD.match(x) and x.endswith(".r") for x in fields)
        if token_r:
            flags.append("recompute_token_romaji")
            if "kana" not in fields or "romaji" not in fields:
                flags.append("check_sentence_kana_romaji_cascade")
        if "kana" in fields and "romaji" not in fields:
            flags.append("kana_changed_verify_romaji")
        if "romaji" in fields and "kana" not in fields:
            flags.append("romaji_changed_verify_kana")
        for a, b, tag in (("expl_en", "expl_pt", "expl_pair_desync_check"),
                          ("lit_en", "lit_pt", "lit_pair_desync_check"),
                          ("en", "pt", "translation_pair_desync_check")):
            if (a in fields) != (b in fields):
                flags.append(tag)
        s = bank[slug]
        entry = {
            "slug": slug,
            "gen": bool((s.get("provenance") or {}).get("ai_generated")),
            "level": s.get("level"),
            "ops": ops,
            "flags": flags,
        }
        if slug in refs:
            entry["exam_refs"] = refs[slug]
            flags.append("exam_banks_reference_this_sentence")
        for fl in flags:
            flag_hist[fl] += 1
        sentences.append(entry)

    stats["auto_ops"] = sum(len(e["ops"]) for e in sentences)
    stats["auto_sentences"] = len(sentences)
    stats["manual_total"] = len(manual)

    out = {
        "generated_from": [os.path.basename(w) for w in wave_files],
        "per_wave": per_wave,
        "stats": dict(sorted(stats.items())),
        "flag_histogram": dict(flag_hist.most_common()),
        "sentences": sentences,
        "manual": manual,
    }
    with open(OUT, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(out, fh, ensure_ascii=False, indent=1)
    print("waves:", len(wave_files), "->", OUT)
    for k, v in out["stats"].items():
        print(f"  {k}: {v}")
    print("  flags:", json.dumps(out["flag_histogram"], ensure_ascii=False))


if __name__ == "__main__":
    main()
