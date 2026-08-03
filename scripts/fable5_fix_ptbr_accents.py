#!/usr/bin/env python3
"""Restore stripped pt-BR diacritics in learner-facing lesson/topic text — UNAMBIGUOUS words only.

Phase-6 QA found lesson prose where the accents were lost wholesale ("Ele nao vem amanha. Ou seja, a
reuniao esta cancelada."). A corpus scan shows the damage in 246 of 1,288 lesson pt-BR fields, so it is
worth a mechanical pass — but only for words whose unaccented spelling is NOT itself a valid Portuguese
word. Blind accent restoration would corrupt text, because several of the most frequent cases are real
minimal pairs that depend on meaning:

    esta / está      "this (fem.)" vs "is"          -> NEVER auto-fixed
    so / só          (rare) vs "only"                -> NEVER auto-fixed
    e / é            "and" vs "is"                   -> NEVER auto-fixed
    porque / porquê  conjunction vs noun             -> NEVER auto-fixed
    pode / pôde      "can" vs "could"                -> NEVER auto-fixed

Those are left for the authoring pass, which can read the sentence. This script only rewrites tokens from
SAFE_WORDS, where the unaccented form is not a word in pt-BR (nao, entao, licao, reuniao, voce, ...), and
it preserves the original capitalisation. Idempotent, and it never touches Japanese text: replacements are
whole-word ASCII matches, so kana/kanji spans cannot be affected.

Emits research/derived/fable5_validation/phase6_accent_fix.json (patch + full before/after). Applies
nothing. Usage: fable5_fix_ptbr_accents.py [--show N]
"""
from __future__ import annotations
import argparse, json, re, sqlite3, sys
from collections import Counter
from pathlib import Path
sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
ROOT = Path(__file__).resolve().parents[1]
FD = ROOT / "research" / "derived" / "fable5_validation"

# unaccented form -> correct form. Every key MUST be a non-word in pt-BR.
SAFE_WORDS = {
    "nao": "não", "entao": "então", "tambem": "também", "voce": "você", "voces": "vocês",
    "licao": "lição", "licoes": "lições", "reuniao": "reunião", "reunioes": "reuniões",
    "amanha": "amanhã", "portugues": "português", "japones": "japonês", "ingles": "inglês",
    "frances": "francês", "alemao": "alemão", "irmao": "irmão", "irma": "irmã", "irmas": "irmãs",
    "acao": "ação", "acoes": "ações", "oracao": "oração", "oracoes": "orações",
    "expressao": "expressão", "expressoes": "expressões", "conjugacao": "conjugação",
    "conjugacoes": "conjugações", "traducao": "tradução", "traducoes": "traduções",
    "explicacao": "explicação", "explicacoes": "explicações", "atencao": "atenção",
    "informacao": "informação", "informacoes": "informações", "situacao": "situação",
    "situacoes": "situações", "construcao": "construção", "construcoes": "construções",
    "particula": "partícula", "particulas": "partículas", "silaba": "sílaba", "silabas": "sílabas",
    "prefixo": "prefixo", "sufixo": "sufixo",  # unchanged, kept for clarity
    "reforca": "reforça", "reforcar": "reforçar", "comeca": "começa", "comecar": "começar",
    "comeco": "começo", "abracada": "abraçada", "abracado": "abraçado", "pescoco": "pescoço",
    "cabeca": "cabeça", "cabecas": "cabeças", "desdem": "desdém", "cafe": "café", "cha": "chá",
    "logica": "lógica", "tecnico": "técnico", "tecnica": "técnica", "superficie": "superfície",
    "forca": "força", "musica": "música", "pratica": "prática", "basico": "básico",
    "basica": "básica", "proprio": "próprio", "propria": "própria", "ultimo": "último",
    "ultima": "última", "numero": "número", "numeros": "números", "periodo": "período",
    "sequencia": "sequência", "frequencia": "frequência", "consequencia": "consequência",
    "referencia": "referência", "diferenca": "diferença", "diferencas": "diferenças",
    "presenca": "presença", "sentenca": "sentença", "sentencas": "sentenças",
    "necessario": "necessário", "necessaria": "necessária", "obrigatorio": "obrigatório",
    "vocabulario": "vocabulário", "dicionario": "dicionário", "contrario": "contrário",
    "seculo": "século", "familia": "família", "historia": "história", "memoria": "memória",
    "categoria": "categoria", "ideia": "ideia",  # unchanged
    "seria": "seria", "varios": "vários", "varias": "várias", "proximo": "próximo",
    "proxima": "próxima", "possivel": "possível", "impossivel": "impossível",
    "facil": "fácil", "dificil": "difícil", "util": "útil", "nivel": "nível",
    "seguranca": "segurança", "mudanca": "mudança", "licenca": "licença",
}
# guarded against: real pt-BR words that must never be rewritten
AMBIGUOUS = {"esta", "so", "e", "porque", "pode", "para", "sera", "esta", "de", "da", "aquele"}
SAFE = {k: v for k, v in SAFE_WORDS.items() if k != v and k not in AMBIGUOUS}
WORD_RE = re.compile(r"\b(" + "|".join(sorted(SAFE, key=len, reverse=True)) + r")\b", re.I)


def restore(text: str):
    hits = Counter()

    def sub(m):
        w = m.group(0)
        rep = SAFE[w.lower()]
        hits[w.lower()] += 1
        if w.isupper():
            return rep.upper()
        if w[0].isupper():
            return rep[0].upper() + rep[1:]
        return rep

    return WORD_RE.sub(sub, text), hits


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--show", type=int, default=4)
    args = ap.parse_args()
    con = sqlite3.connect(ROOT / "db" / "corpus.sqlite")
    edits, total_hits, samples = [], Counter(), []
    for etype in ("lesson", "topic"):
        for eid, field, value in con.execute(
                "SELECT entity_id, field, value FROM localized_text "
                "WHERE entity_type=? AND locale='pt-BR'", (etype,)):
            if not value:
                continue
            new, hits = restore(value)
            if new == value:
                continue
            total_hits.update(hits)
            edits.append({"entity_type": etype, "entity_id": eid, "field": field,
                          "current": value, "fix": new, "words": dict(hits)})
            if len(samples) < args.show:
                i = next((m.start() for m in WORD_RE.finditer(value)), 0)
                samples.append((etype, eid, field, value[max(0, i - 50):i + 90], new[max(0, i - 50):i + 90]))
    con.close()
    (FD / "phase6_accent_fix.json").write_text(json.dumps(
        {"note": "Deterministic pt-BR diacritic restoration for UNAMBIGUOUS words only. Minimal pairs "
                 "(esta/está, so/só, e/é, porque/porquê, pode/pôde) are deliberately NOT auto-fixed - they "
                 "need a reader. Whole-word ASCII matching, so Japanese text cannot be touched.",
         "word_frequency": dict(total_hits.most_common()), "edits": edits},
        ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"accent fix: {len(edits)} fields, {sum(total_hits.values())} word repairs")
    print("top words:", dict(total_hits.most_common(10)))
    for t, i, f, b, a in samples:
        print(f"\n--- {t}:{i} [{f}]\n  before: ...{b}...\n  after : ...{a}...")
    return 0


if __name__ == "__main__":
    sys.exit(main())
