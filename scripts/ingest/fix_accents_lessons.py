#!/usr/bin/env python3
"""P8 — restore stripped pt-BR diacritics in lesson string fields via a curated whole-word map.

Some agents emitted accent-stripped Portuguese (nao/voce/licao). This replaces an UNAMBIGUOUS set of
accent-stripped forms with their correct accented spelling, as whole words, preserving capitalization. Only
words that are almost always wrong when unaccented are included (ambiguous ones like e/so/ja/para are NOT). Safe
and idempotent: fields without these misspellings are untouched. Run before load/validate. Usage:
  fix_accents_lessons.py            # all
  fix_accents_lessons.py <slug...>  # only named
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
LESSON_DIR = Path(__file__).resolve().parents[2] / "research" / "derived" / "lessons"

# lowercase unaccented -> correct accented (whole word, case preserved on output)
MAP = {
    "nao": "não", "voce": "você", "voces": "vocês", "licao": "lição", "licoes": "lições",
    "acao": "ação", "acoes": "ações", "portugues": "português", "tambem": "também",
    "entao": "então", "comeco": "começo", "comecamos": "começamos", "comeca": "começa",
    "comecar": "começar", "comecando": "começando", "familia": "família", "familias": "famílias",
    "consequencia": "consequência", "adverbio": "advérbio", "adverbios": "advérbios",
    "conjuncao": "conjunção", "conjuncoes": "conjunções", "mudanca": "mudança", "mudancas": "mudanças",
    "sequencia": "sequência", "informacao": "informação", "vocabulario": "vocabulário",
    "mnemonico": "mnemônico", "duvida": "dúvida", "intencao": "intenção", "intencoes": "intenções",
    "nuanca": "nuança", "nuancas": "nuanças", "possivel": "possível", "suposicao": "suposição",
    "topico": "tópico", "regiao": "região", "particula": "partícula", "particulas": "partículas",
    "relacao": "relação", "reconheco": "reconheço", "conheco": "conheço", "avanca": "avança",
    "constroi": "constrói", "numero": "número", "numeros": "números", "area": "área",
    "silaba": "sílaba", "silabas": "sílabas", "musica": "música", "musicas": "músicas",
    "pagina": "página", "paginas": "páginas", "proprio": "próprio", "propria": "própria",
    "ultimo": "último", "ultima": "última", "proximo": "próximo", "proxima": "próxima",
    "ingles": "inglês", "japones": "japonês", "tres": "três", "consciencia": "consciência",
    "experiencia": "experiência", "referencia": "referência", "diferenca": "diferença",
    "diferencas": "diferenças", "presenca": "presença", "sao": "são", "voce": "você",
    "alguem": "alguém", "ninguem": "ninguém", "porem": "porém", "alem": "além", "atencao": "atenção",
    "expressao": "expressão", "expressoes": "expressões", "construcao": "construção",
    "construir": "construir", "frances": "francês", "saudacoes": "saudações", "saudacao": "saudação",
    "negacao": "negação", "afirmacao": "afirmação", "particao": "partição", "secao": "seção",
    "padrao": "padrão", "padroes": "padrões", "razao": "razão", "razoes": "razões",
    "licaozinha": "liçãozinha", "comecou": "começou", "necessario": "necessário",
    "obrigatorio": "obrigatório", "automatico": "automático", "pratico": "prático",
    "fonetica": "fonética", "fonetico": "fonético", "gramatica": "gramática", "silabico": "silábico",
    "conjugacao": "conjugação", "conjugacoes": "conjugações", "explicacao": "explicação",
    "explicacoes": "explicações", "descricao": "descrição", "descricoes": "descrições",
    "nominalizacao": "nominalização", "oracao": "oração", "oracoes": "orações", "comecam": "começam",
}


def _case(src: str, repl: str) -> str:
    if src.isupper():
        return repl.upper()
    if src[:1].isupper():
        return repl[:1].upper() + repl[1:]
    return repl


# build one regex of all keys, longest first, word-bounded (unicode word chars)
_KEYS = sorted(MAP, key=len, reverse=True)
_RX = re.compile(r"(?<![0-9A-Za-zÀ-ÿ])(" + "|".join(_KEYS) + r")(?![0-9A-Za-zÀ-ÿ])", re.IGNORECASE)


def _fix(s: str) -> tuple[str, int]:
    n = [0]

    def sub(m):
        w = m.group(1)
        repl = MAP.get(w.lower())
        if repl:
            n[0] += 1
            return _case(w, repl)
        return w
    return _RX.sub(sub, s), n[0]


# identifier keys whose VALUES must stay ASCII — never accent these
_SKIP_KEYS = {"slug", "topic", "ref"}


def _fix_body(s: str, c) -> str:
    # only accent text content BETWEEN tags; never touch attribute values (e.g. ref="ex:n5-numeros-...")
    def seg(m):
        fixed, n = _fix(m.group(1))
        c[0] += n
        return ">" + fixed + "<"
    return re.sub(r">([^<>]+)<", seg, s)


def _walk(o, c, key=None):
    if isinstance(o, str):
        if key in _SKIP_KEYS:
            return o                         # identifier — leave ASCII
        if key == "body":
            return _fix_body(o, c)           # protect tag attributes
        s, n = _fix(o)
        c[0] += n
        return s
    if isinstance(o, list):
        return [_walk(x, c, key) for x in o]
    if isinstance(o, dict):
        return {k: _walk(v, c, k) for k, v in o.items()}
    return o


def main() -> int:
    if len(sys.argv) > 1:
        files = [LESSON_DIR / ((a.split(":", 1)[1] if ":" in a else a) + ".json") for a in sys.argv[1:]]
    else:
        files = sorted(LESSON_DIR.glob("*.json"))
    total = 0
    touched = 0
    for f in files:
        if not f.exists():
            continue
        d = json.loads(f.read_text(encoding="utf-8"))
        c = [0]
        nd = _walk(d, c)
        if c[0]:
            f.write_text(json.dumps(nd, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            total += c[0]
            touched += 1
    print(f"restored {total} accented word(s) across {touched} file(s)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
