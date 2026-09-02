#!/usr/bin/env python3
"""Emit dissection skeletons + a style reference for the 324 staged mined sentences.

The mined rows carry only `pt` and `pt_literal`. Every sentence in the bank is dissection_tier "full",
which validate.py reads as a promise of a Layer-B gloss on EVERY content token, an explanation on every
particle, and a structure paragraph. That gap is the sole blocker on ingesting them (STATE entry v).

This script runs the Dissector over each staged sentence and writes exactly what an author needs to fill
in: the token positions persist_dissection.persist() will key on, each token's surface/lemma/POS, and the
particle positions. Nothing here authors anything; it only lays out the slots.

It also samples REAL existing rows so the authoring pass matches the bank's established voice instead of
inventing a new one. Style drift across 324 sentences would be its own defect.

Usage: prep_mined_skeletons.py
"""
from __future__ import annotations
import json, sqlite3, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.stdout.reconfigure(encoding="utf-8")
# W01: honour --db / $YOMINEKO_DB so a rebuild can target a scratch DB (scripts/dbtarget.py).
import sys as _sys, pathlib as _pl  # noqa: E402
_sys.path.append(str(next(p for p in _pl.Path(__file__).resolve().parents if p.name == "scripts")))
from dbtarget import db_target  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
DB = db_target(ROOT / "db" / "corpus.sqlite")
SRC = ROOT / "research" / "derived" / "mined_pt" / "_accepted.json"
OUT = ROOT / "research" / "derived" / "mined_pt" / "_skeletons.json"
CONTENT = {"名詞", "動詞", "形容詞", "副詞", "形状詞", "連体詞", "感動詞", "接続詞", "代名詞"}


def main() -> int:
    from dissect import Dissector
    con = sqlite3.connect(DB)
    diss = Dissector(DB)
    rows = [r for r in json.loads(SRC.read_text(encoding="utf-8"))["rows"] if not r.get("reject")]

    # style reference: real rows the bank already ships, so authors copy the house voice
    ex = []
    for sid, jp in con.execute(
            "SELECT id,jp FROM sentence WHERE dissection_tier='full' AND length(jp) BETWEEN 12 AND 26 "
            "ORDER BY id LIMIT 3"):
        toks = []
        for tid, pos, surf in con.execute(
                "SELECT id,position,surface FROM token WHERE sentence_id=? AND split_mode='C' "
                "ORDER BY position", (sid,)):
            g = con.execute("SELECT value FROM localized_text WHERE entity_type='token' AND entity_id=? "
                            "AND field='gloss' AND locale='pt-BR'", (tid,)).fetchone()
            r = con.execute("SELECT value FROM localized_text WHERE entity_type='token' AND entity_id=? "
                            "AND field='role' AND locale='pt-BR'", (tid,)).fetchone()
            toks.append({"position": pos, "surface": surf,
                         "gloss_pt": g[0] if g else None, "role_pt": r[0] if r else None})
        st = con.execute("SELECT value FROM localized_text WHERE entity_type='sentence' AND entity_id=? "
                         "AND field='structure_explanation' AND locale='pt-BR'", (sid,)).fetchone()
        parts = []
        for pid, particle in con.execute("SELECT id,particle FROM particle WHERE sentence_id=?", (sid,)):
            f = con.execute("SELECT value FROM localized_text WHERE entity_type='particle' AND "
                            "entity_id=? AND field='function' AND locale='pt-BR'", (pid,)).fetchone()
            e = con.execute("SELECT value FROM localized_text WHERE entity_type='particle' AND "
                            "entity_id=? AND field='explanation' AND locale='pt-BR'", (pid,)).fetchone()
            parts.append({"particle": particle, "function_pt": f[0] if f else None,
                          "explanation_pt": e[0] if e else None})
        ex.append({"jp": jp, "tokens": toks, "particles": parts,
                   "structure_explanation_pt": st[0] if st else None})

    out = []
    for r in rows:
        sk = diss.skeleton(r["jp"])
        out.append({
            "tatoeba_id": r["tatoeba_id"], "jp": r["jp"], "en": r.get("en"),
            "pt": r.get("pt"), "pt_literal": r.get("pt_literal"), "stage": r.get("stage"),
            "tokens": [{"position": t["position"], "surface": t["surface"], "lemma": t["lemma"],
                        "reading": t["reading"], "pos": t["pos_coarse"],
                        "content": t["pos_coarse"] in CONTENT}
                       for t in sk["tokens"]],
            "particles": [{"position": p["position"], "particle": p["particle"],
                           "function_type": p.get("function_type")} for p in sk["particles"]],
        })
    OUT.write_text(json.dumps({"style_reference": ex, "sentences": out}, ensure_ascii=False, indent=1),
                   encoding="utf-8")
    n_tok = sum(sum(1 for t in s["tokens"] if t["content"]) for s in out)
    n_par = sum(len(s["particles"]) for s in out)
    print(f"{len(out)} sentences: {n_tok} content tokens needing a gloss, {n_par} particles, "
          f"{len(out)} structure paragraphs. style_reference has {len(ex)} real examples.")
    con.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
