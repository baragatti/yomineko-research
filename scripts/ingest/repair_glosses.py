#!/usr/bin/env python3
"""P5 self-heal — fill any CONTENT token missing a pt-BR gloss after a dissection batch.

Dissection agents occasionally skip an "obvious" content token (an interjection like ありがとう, an
auxiliary adjective/verb like ない・いる). The §7 validator flags these as errors. This step fills them
deterministically so the cycle stays green without manual edits:
  1) if the token links a vocab item, use that vocab's first sense pt-BR gloss (Layer A→B, trustworthy);
  2) else fall back to a small closed-class dictionary of recurring function words / interjections;
  3) anything still unfilled is reported (rare) for a targeted re-dissection.
Idempotent: only touches tokens whose gloss is currently NULL/empty. Run with venv python.
"""
from __future__ import annotations

import json
import sqlite3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
from i18n_text import DEFAULT_LOCALE, set_text  # noqa: E402

DB = Path(__file__).resolve().parents[2] / "db" / "corpus.sqlite"

CONTENT_POS = ("名詞", "動詞", "形容詞", "形状詞", "副詞", "代名詞", "連体詞", "接続詞", "感動詞")

# Closed-class / interjection fallbacks (surface -> (gloss, role)). Only for tokens with no vocab link.
COMMON: dict[str, tuple[str, str]] = {
    "ありがとう": ("obrigado(a)", "interjeição (agradecimento)"),
    "ない": ("não (negação)", "auxiliar de negação"),
    "ある": ("haver / existir / ter", "verbo existencial"),
    "いる": ("estar / haver (animado)", "verbo existencial / auxiliar"),
    "なる": ("tornar-se / ficar", "verbo principal"),
    "する": ("fazer", "verbo principal"),
    "こんにちは": ("olá / boa tarde", "interjeição (saudação)"),
    "はい": ("sim", "interjeição (afirmação)"),
    "いいえ": ("não", "interjeição (negação)"),
    "さようなら": ("até logo / adeus", "interjeição (despedida)"),
}


def first_vocab_gloss(con: sqlite3.Connection, vocab_id: int) -> str | None:
    sid = con.execute(
        "SELECT id FROM vocab_sense WHERE vocab_id=? ORDER BY sense_order LIMIT 1", (vocab_id,)).fetchone()
    if not sid:
        return None
    row = con.execute(
        "SELECT value FROM localized_text WHERE entity_type='vocab_sense' AND entity_id=? AND field='gloss' "
        "AND locale=?", (sid[0], DEFAULT_LOCALE)).fetchone()
    if not row or not row[0]:
        return None
    try:
        vals = json.loads(row[0])
        return vals[0] if isinstance(vals, list) and vals else (row[0] if isinstance(row[0], str) else None)
    except (json.JSONDecodeError, TypeError):
        return row[0]


def main() -> int:
    con = sqlite3.connect(DB)
    q = f"""SELECT t.id, t.surface, t.vocab_id FROM token t
            WHERE t.split_mode='C' AND t.pos_coarse IN ({','.join('?' * len(CONTENT_POS))})
            AND NOT EXISTS (SELECT 1 FROM localized_text lt WHERE lt.entity_type='token'
                AND lt.entity_id=t.id AND lt.field='gloss' AND lt.value IS NOT NULL AND lt.value<>'')"""
    missing = con.execute(q, CONTENT_POS).fetchall()
    filled_vocab = filled_dict = 0
    unresolved: list[str] = []
    for tid, surface, vocab_id in missing:
        gloss = role = None
        if vocab_id:
            gloss = first_vocab_gloss(con, vocab_id)
            if gloss:
                filled_vocab += 1
        if not gloss and surface in COMMON:
            gloss, role = COMMON[surface]
            filled_dict += 1
        if not gloss:
            unresolved.append(surface)
            continue
        set_text(con, "token", tid, "gloss", gloss, layer="B")
        if role:
            set_text(con, "token", tid, "role", role, layer="B")
    con.commit()
    con.close()
    print(f"repair_glosses: filled {filled_vocab} from vocab links + {filled_dict} from dictionary; "
          f"unresolved={len(unresolved)} {unresolved[:20]}")
    return 1 if unresolved else 0


if __name__ == "__main__":
    sys.exit(main())
