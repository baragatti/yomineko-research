#!/usr/bin/env python3
"""P6b — author the pré-N5 hiragana FAMILY lessons (rich tagged format) from the kana registry.

Emits research/derived/lessons/les-pre-n5-hiragana-NN.json. Each lesson teaches one gojūon family
("Família do A/KA/SA…"), unlocks that `kana-family`, and (lesson 1) turns on feat:srs-reviews +
deck:kana-hiragana. Currently authors the Família do A exemplar; extend FAMILIES as more are written.
Run with venv python, then load_lessons -> validate_lessons -> export_course.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
OUTDIR = Path(__file__).resolve().parents[2] / "research" / "derived" / "lessons"

A_BODY = """
<heading level="2"><text>Hiragana: a Família do A (あ・い・う・え・お)</text></heading>

<p><text>Bem-vindo à escrita japonesa! O </text><term define="o primeiro dos dois silabários do japonês; cada símbolo representa uma sílaba">hiragana</term><text> começa pelas cinco </text><text weight="bold">vogais</text><text>, que formam a "Família do A". Aprendê-las primeiro destrava todas as outras famílias, porque cada uma é uma consoante combinada com estas mesmas vogais.</text></p>

<note type="l1-advantage"><p><text>As cinco vogais japonesas soam quase como em português: </text><jp>あ</jp><text> = </text><emphasis>a</emphasis><text>, </text><jp>い</jp><text> = </text><emphasis>i</emphasis><text>, </text><jp>う</jp><text> = </text><emphasis>u</emphasis><text>, </text><jp>え</jp><text> = </text><emphasis>e</emphasis><text>, </text><jp>お</jp><text> = </text><emphasis>o</emphasis><text>. A única diferença: o </text><jp>う</jp><text> é mais "seco", sem arredondar os lábios como no "u" de "uva".</text></p></note>

<heading level="3"><text>As cinco vogais</text></heading>
<list ordered="false">
  <item><jp>あ</jp><text> (</text><romaji>a</romaji><text>): como o </text><emphasis>a</emphasis><text> de "casa".</text></item>
  <item><jp>い</jp><text> (</text><romaji>i</romaji><text>): como o </text><emphasis>i</emphasis><text> de "vida".</text></item>
  <item><jp>う</jp><text> (</text><romaji>u</romaji><text>): um </text><emphasis>u</emphasis><text> curto, lábios relaxados (não arredonde).</text></item>
  <item><jp>え</jp><text> (</text><romaji>e</romaji><text>): como o </text><emphasis>e</emphasis><text> de "mesa" (nunca vira "i").</text></item>
  <item><jp>お</jp><text> (</text><romaji>o</romaji><text>): como o </text><emphasis>o</emphasis><text> de "bolo" (nunca vira "u").</text></item>
</list>

<note type="l1-pitfall"><p><text>No fim das palavras, mantenha a vogal cheia: </text><jp>え</jp><text> é sempre </text><emphasis>e</emphasis><text>, não </text><emphasis>i</emphasis><text>; </text><jp>お</jp><text> é sempre </text><emphasis>o</emphasis><text>, não </text><emphasis>u</emphasis><text>. O português costuma "fechar" essas vogais, mas o japonês não.</text></p></note>

<note type="tip"><p><text>Para escrever, siga a ordem dos traços (de cima para baixo, da esquerda para a direita) usando o diagrama numerado. Repita cada símbolo algumas vezes em voz alta enquanto escreve.</text></p></note>

<heading level="3"><text>Hora de praticar</text></heading>
<exercise ref="ex:pre-n5-hiragana-01-1"/>
<exercise ref="ex:pre-n5-hiragana-01-2"/>
<exercise ref="ex:pre-n5-hiragana-01-3"/>
<exercise ref="ex:pre-n5-hiragana-01-4"/>

<checklist>
  <check item-ref="kana:hiragana-a"><text>Reconheço あ・い・う・え・お e seus sons.</text></check>
  <check><text>Pronuncio as cinco vogais com o som cheio (え não vira i, お não vira u).</text></check>
  <check><text>Consigo escrever cada vogal na ordem correta dos traços.</text></check>
</checklist>
""".strip()

A_LESSON = {
    "slug": "les:pre-n5-hiragana-01",
    "topic": "top:pre-n5-hiragana",
    "order": 1,
    "schema_version": "1.0",
    "title": "Hiragana: a Família do A (あいうえお)",
    "description": "As cinco vogais do japonês em hiragana (あいうえお) e como pronunciá-las.",
    "objectives": [
        "Reconhecer e ler あ, い, う, え, お",
        "Pronunciar as cinco vogais com o som cheio (sem fechar え/お)",
        "Escrever cada vogal na ordem correta dos traços",
    ],
    "needs": [],  # first content lesson of the course
    "unlocks": [{"type": "kana-family", "ref": "kana:hiragana-a"}],
    # the very first kana lesson turns on the SRS habit + creates the hiragana deck
    "feature_unlocks": ["feat:srs-reviews"],
    "sentence_refs": [],
    "body": A_BODY,
    "exercises": [
        {"slug": "ex:pre-n5-hiragana-01-1", "type": "recognition",
         "prompt": "Qual hiragana representa o som 'a'?",
         "answer": {"choices": ["あ", "い", "う"], "correct": "あ"},
         "explanation": "あ = a (como em 'casa').", "sentence_refs": [], "item_refs": []},
        {"slug": "ex:pre-n5-hiragana-01-2", "type": "recognition",
         "prompt": "Que som tem え?",
         "answer": {"choices": ["e", "i", "a"], "correct": "e"},
         "explanation": "え = e (som cheio, nunca 'i').", "sentence_refs": [], "item_refs": []},
        {"slug": "ex:pre-n5-hiragana-01-3", "type": "matching",
         "prompt": "Ligue cada hiragana ao seu som.",
         "answer": {"pairs": [["あ", "a"], ["い", "i"], ["う", "u"], ["え", "e"], ["お", "o"]]},
         "explanation": "As cinco vogais da Família do A.", "sentence_refs": [], "item_refs": []},
        {"slug": "ex:pre-n5-hiragana-01-4", "type": "production",
         "prompt": "Escreva o hiragana do som 'o'.",
         "answer": {"text": "お", "accept": ["お"]},
         "explanation": "'o' = お.", "sentence_refs": [], "item_refs": []},
    ],
}

FAMILIES = [A_LESSON]  # extend with KA/SA/… as authored


def main() -> int:
    OUTDIR.mkdir(parents=True, exist_ok=True)
    for rec in FAMILIES:
        slug = rec["slug"].split(":", 1)[1]
        (OUTDIR / f"{slug}.json").write_text(json.dumps(rec, ensure_ascii=False, indent=2) + "\n",
                                             encoding="utf-8")
        print(f"wrote {slug}.json")
    return 0


if __name__ == "__main__":
    sys.exit(main())
