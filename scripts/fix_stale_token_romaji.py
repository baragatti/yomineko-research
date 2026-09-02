#!/usr/bin/env python3
"""Repair stale TOKEN romaji so concat(token romaji) == sentence romaji again (invariant I3).

The re-dissection audit found 336 sentences where the token-level romaji no longer concatenates to the
sentence's own romaji. The obvious repair -- recompute every token -- is exactly what caused the
206-objection collateral drift during the Phase-3 patch (su-pa- became suupaa, kesa, became kesa、), so
this uses a gate that makes guessing impossible:

    For each violating sentence, recompute EVERY token's romaji from its own reading. Accept the
    sentence only if the recomputed concatenation reproduces the stored sentence romaji BYTE FOR BYTE.
    Then write back only the tokens whose value actually changed.

The sentence-level romaji is the audited authority (it went through the Phase-3 review), so reproducing
it exactly is proof that the recompute agrees with what a human already signed off. If it does not
reproduce, the disagreement is not about romanization at all but about which READING a kanji has -- the
sentence says juu where the token says ichi, or bei where the token says kome -- and silently rewriting
romaji there would paper over a reading error. Those sentences are reported, never touched.

Measured: 327 sentences / 365 tokens are safe, 9 are reading disputes.

Romanization comes from corpus_romaji() in scripts/fable5_sentences_render_diff.py, the same
boundary-aware function the Phase-3 patch used, so the house conventions hold: gemination resolved
across the token boundary, katakana 長音 written as '-', ASCII punctuation, and no apostrophes in
sentence romaji (an'i/ten'in apostrophes are the vocab and conjugation convention, not this one).

Usage: fix_stale_token_romaji.py [--apply]
"""
from __future__ import annotations
import argparse, importlib.util, json, sqlite3, sys
from pathlib import Path
sys.stdout.reconfigure(encoding="utf-8")
# W01: honour --db / $YOMINEKO_DB so a rebuild can target a scratch DB (scripts/dbtarget.py).
import sys as _sys, pathlib as _pl  # noqa: E402
_sys.path.append(str(next(p for p in _pl.Path(__file__).resolve().parents if p.name == "scripts")))
from dbtarget import db_target  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
DB = db_target(ROOT / "db" / "corpus.sqlite")
REPORT = ROOT / "research" / "derived" / "romaji_reading_disputes.json"


def load_romanizer():
    spec = importlib.util.spec_from_file_location(
        "rd", ROOT / "scripts" / "fable5_sentences_render_diff.py")
    mod = importlib.util.module_from_spec(spec)
    try:
        spec.loader.exec_module(mod)          # the module runs a main(); we only want its functions
    except SystemExit:
        pass
    return mod.corpus_romaji


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args()
    cr = load_romanizer()
    con = sqlite3.connect(DB)

    fixed_s = fixed_t = 0
    disputes = []
    for sid, slug, ro in con.execute("SELECT id,slug,romaji FROM sentence"):
        toks = con.execute("SELECT id,position,surface,reading,romaji FROM token WHERE sentence_id=? "
                           "AND split_mode='C' ORDER BY position", (sid,)).fetchall()
        if "".join(t[4] or "" for t in toks) == (ro or ""):
            continue
        want = []
        for i, (tid, pos, surf, read, cur) in enumerate(toks):
            nxt = toks[i + 1][3] if i + 1 < len(toks) else ""
            try:
                want.append(cr(read or "", nxt or ""))
            except Exception:
                want.append(cur or "")
        if "".join(want) != (ro or ""):
            # Not a romanization problem: the sentence and the tokens disagree about a READING.
            diff = [{"position": t[1], "surface": t[2], "reading": t[3],
                     "stored_romaji": t[4], "recomputed": w}
                    for t, w in zip(toks, want) if (t[4] or "") != w]
            disputes.append({"slug": slug, "sentence_romaji": ro, "tokens": diff})
            continue
        changed = [(t[0], w) for t, w in zip(toks, want) if (t[4] or "") != w]
        if args.apply:
            for tid, w in changed:
                con.execute("UPDATE token SET romaji=? WHERE id=?", (w, tid))
        fixed_s += 1
        fixed_t += len(changed)

    if args.apply:
        con.commit()
    REPORT.write_text(json.dumps(
        {"note": "Sentences where token romaji and sentence romaji disagree because of a READING "
                 "difference, not a romanization one. Rewriting romaji here would hide a reading error, "
                 "so they are left alone and need a human or a re-dissection.",
         "count": len(disputes), "sentences": disputes}, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"stale token romaji ({'APPLIED' if args.apply else 'dry-run'}): "
          f"{fixed_s} sentences, {fixed_t} tokens")
    print(f"reading disputes left alone: {len(disputes)} -> {REPORT.relative_to(ROOT)}")
    con.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
