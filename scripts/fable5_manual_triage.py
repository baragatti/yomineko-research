#!/usr/bin/env python3
"""Triage the Phase-3 patch `manual` queue against the DB (STATE runbook step 5).

The finder batch projection dropped `split_mode`, so finders saw the bank's TWO tokenization
granularities flattened together and reported the atomic split_mode='A' sub-tokens (誕生+日 next to
誕生日) as "stray/duplicate/null-gloss tokens". Those are INTENTIONAL structure, never defects.

Ground truth per sentence, straight from the DB:
  * C-mode tokens are the display granularity and MUST satisfy concat(surface) == jp;
  * A-mode tokens are atomic sub-tokens of a single compound and legitimately do not.

Classification:
  refute_split_mode_a  — token-structure complaint whose named surfaces are A-mode rows while the C-mode
                         chain still reconstructs jp exactly. No action; the token array is correct.
  real_whitespace_tok  — a C-mode token whose surface is whitespace (usually glossed 記号/きごう). Real:
                         it injects a phantom word into kana/romaji. Fix = drop the token AND the stray
                         space in jp, then recompute kana/romaji.
  real_token_structure — C-mode chain does NOT reconstruct jp: genuine tokenization damage.
  needs_human          — anything else (content rewrites, jp re-authoring, style/spelling).

Writes phase3_manual_triage.json ({counts, items:[{slug, field, reason, verdict, why}]}) and prints a
summary. Read-only w.r.t. the DB and the patch. Usage: fable5_manual_triage.py
"""
from __future__ import annotations
import json, re, sqlite3, sys
from collections import Counter
from pathlib import Path
sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
# W01: honour --db / $YOMINEKO_DB so a rebuild can target a scratch DB (scripts/dbtarget.py).
import sys as _sys, pathlib as _pl  # noqa: E402
_sys.path.append(str(next(p for p in _pl.Path(__file__).resolve().parents if p.name == "scripts")))
from dbtarget import db_target  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
FD = ROOT / "research" / "derived" / "fable5_validation"
PATCH = FD / "phase3_sentences_patch.json"
STRUCT_RE = re.compile(
    r"stray|duplicat|orphan|null[- ]gloss|stray token|spurious|out of (?:sentence )?order|"
    r"retokeniz|concatenat|reconstruct|sub-?token|fragment|prepend|token list",
    re.I)
TOKEN_FIELD_RE = re.compile(r"^tokens\[\d+\]")


def main() -> int:
    patch = json.loads(PATCH.read_text(encoding="utf-8"))
    manual = patch["manual"]
    con = sqlite3.connect(db_target(ROOT / "db" / "corpus.sqlite"))

    cache: dict = {}

    def sent(slug):
        if slug not in cache:
            row = con.execute("SELECT id, jp FROM sentence WHERE slug=?", (slug,)).fetchone()
            if not row:
                cache[slug] = None
            else:
                sid, jp = row
                toks = con.execute("SELECT split_mode, surface FROM token WHERE sentence_id=? ORDER BY id",
                                   (sid,)).fetchall()
                a = [s for m, s in toks if m == "A"]
                c = [s for m, s in toks if m == "C"]
                cache[slug] = {"jp": jp, "a": a, "c": c, "c_ok": "".join(c) == jp,
                               "ws": [s for s in c if s.strip() == ""]}
        return cache[slug]

    out = []
    for m in manual:
        f = m.get("finding", {})
        issue = f.get("issue", "") or ""
        cur = str(f.get("current", "") or "")
        s = sent(m["slug"])
        verdict, why = "needs_human", ""
        if not s:
            verdict, why = "needs_human", "sentence not in DB"
        elif s["ws"] and ("きごう" in issue or "記号" in issue or "whitespace" in issue.lower()
                          or "space" in issue.lower()):
            verdict = "real_whitespace_tok"
            why = f"C-mode has whitespace token(s); jp carries {len(s['ws'])} stray space(s)"
        elif STRUCT_RE.search(issue) and (TOKEN_FIELD_RE.match(m["field"]) or m["field"] == "tokens"
                                          or "token" in m["field"]):
            named = set(re.findall(r"[぀-ヿ一-鿿]+", cur)) or set(re.findall(r"[぀-ヿ一-鿿]+", issue))
            in_a = {x for x in named if x in s["a"]}
            if s["c_ok"] and in_a:
                verdict = "refute_split_mode_a"
                why = f"C-chain reconstructs jp; named surfaces {sorted(in_a)} are split_mode='A' sub-tokens"
            elif not s["c_ok"]:
                verdict = "real_token_structure"
                why = "C-mode chain does NOT reconstruct jp"
            else:
                verdict = "needs_human"
                why = "structure complaint but surfaces not matched to A-rows"
        out.append({"slug": m["slug"], "field": m["field"], "reason": m["reason"],
                    "verdict": verdict, "why": why})
    con.close()

    counts = Counter(x["verdict"] for x in out)
    by_reason = Counter((x["reason"], x["verdict"]) for x in out)
    (FD / "phase3_manual_triage.json").write_text(
        json.dumps({"counts": dict(counts), "items": out}, ensure_ascii=False, indent=1), encoding="utf-8")
    print("manual triage:", dict(counts))
    print("\nby reason -> verdict:")
    for (r, v), n in sorted(by_reason.items()):
        print(f"  {r:28s} {v:22s} {n}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
