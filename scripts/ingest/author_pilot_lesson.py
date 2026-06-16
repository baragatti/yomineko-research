#!/usr/bin/env python3
"""Generate the REFERENCE pilot lesson JSON in the frozen rich-tagged format (design/lesson_schema.md v1).

Emits research/derived/lessons/les-n5-te-form-01.json — the durable authoring source loaded by load_lessons.py.
This is the worked example bulk authoring (workflow agents) mimics: tagged body (no bare text), corpus refs by
id, inline exercise refs, ending <checklist>. Run once; the JSON it writes is the source of truth thereafter.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
OUT = Path(__file__).resolve().parents[2] / "research" / "derived" / "lessons" / "les-n5-te-form-01.json"

BODY = """
<heading level="2"><text>A forma て e os pedidos educados</text></heading>

<p><text>Nesta lição você dá um dos passos mais importantes do N5: a </text><grammar ref="gram:te-form"/><text> (lê-se </text><emphasis>te</emphasis><text>). Ela é a </text><term define="forma que liga o verbo a pedidos, ações em sequência, estados e dezenas de outras estruturas">forma conectiva</term><text> do verbo. Aqui usamos o emprego mais útil dela: fazer </text><text weight="bold">pedidos educados</text><text> com </text><grammar ref="gram:te-kudasai"/><text>.</text></p>

<heading level="3"><text>Como se forma a forma て</text></heading>
<p><text>A forma て depende do grupo do verbo:</text></p>
<list ordered="false">
  <item><text weight="bold">Verbos ichidan (る): </text><text>tire </text><jp>る</jp><text> e acrescente </text><jp>て</jp><text>: </text><jp reading="たべる">食べる</jp><text> → </text><jp reading="たべて">食べて</jp><text>, </text><vocab ref="vocab:出る"/><text> → </text><jp reading="でて">出て</jp><text>.</text></item>
  <item><text weight="bold">Verbos irregulares: </text><jp reading="する">する</jp><text> → </text><jp reading="して">して</jp><text>; </text><vocab ref="vocab:来る"/><text> → </text><jp reading="きて">来て</jp><text> (a leitura muda para </text><jp>き</jp><text>).</text></item>
  <item><text weight="bold">Verbos godan (う): </text><text>seguem o som da última sílaba: </text><jp>う・つ・る</jp><text> → </text><jp>って</jp><text> (</text><vocab ref="vocab:乗る"/><text> → </text><jp reading="のって">乗って</jp><text>); </text><jp>ぬ・ぶ・む</jp><text> → </text><jp>んで</jp><text>; </text><jp>く</jp><text> → </text><jp>いて</jp><text>; </text><jp>す</jp><text> → </text><jp>して</jp><text>.</text></item>
  <item><text weight="bold">Exceção: </text><jp reading="いく">行く</jp><text> → </text><jp reading="いって">行って</jp><text> (e não 行いて).</text></item>
</list>

<note type="l1-advantage"><p><text>O </text><jp>っ</jp><text> pequeno (em </text><jp reading="のって">乗って</jp><text>, </text><jp reading="いって">行って</jp><text>) é uma pausa de </text><text weight="bold">uma mora</text><text>; bata uma palma extra: </text><emphasis>no-t-te</emphasis><text>. O brasileiro já controla esse "travar" da consoante; só não esqueça de dar-lhe o seu tempo.</text></p></note>

<heading level="3"><text>O pedido: 〜てください</text></heading>
<p><text>Forma て + </text><jp>ください</jp><text> = um pedido educado, "por favor, faça…".</text></p>
<sentence ref="sent:tatoeba-124708" show="furigana" mode="featured" audio="true"/>
<sentence ref="sent:tatoeba-146189" show="furigana" mode="card"/>
<p><text>Repare na partícula: em </text><jp reading="でんわにでる">電話に出る</jp><text>, o </text><jp>に</jp><text> marca o </text><text weight="bold">alvo</text><text> ("atender </text><emphasis>ao</emphasis><text> telefone"). O verbo </text><vocab ref="vocab:出る"/><text> sozinho significa "sair", mas com </text><jp>電話に</jp><text> passa a "atender". Vale aprender o conjunto verbo + partícula.</text></p>

<note type="l1-pitfall"><p><text>Não traduza </text><jp>ください</jp><text> como um imperativo seco ("faça!"). Em japonês, </text><grammar ref="gram:te-kudasai"/><text> já é </text><text weight="bold">educado</text><text>; equivale ao nosso "por favor, atenda", não a uma ordem.</text></p></note>

<heading level="3"><text>Hora de praticar</text></heading>
<exercise ref="ex:n5-te-form-01-1"/>
<exercise ref="ex:n5-te-form-01-2"/>
<exercise ref="ex:n5-te-form-01-3"/>
<exercise ref="ex:n5-te-form-01-4"/>
<exercise ref="ex:n5-te-form-01-5"/>

<checklist>
  <check item-ref="gram:te-form"><text>Sei formar a forma て dos três grupos de verbos.</text></check>
  <check item-ref="gram:te-kudasai"><text>Consigo fazer um pedido educado com 〜てください.</text></check>
  <check><text>Reconheço 〜てください em situações reais (telefone, transporte).</text></check>
</checklist>
""".strip()

REC = {
    "slug": "les:n5-te-form-01",
    "topic": "top:n5-te-form",
    "order": 1,
    "schema_version": "1.0",
    "title": "Pedidos educados: a forma て + ください",
    "objectives": [
        "Formar a forma て dos três grupos de verbos",
        "Fazer pedidos educados com 〜てください",
        "Reconhecer 〜てください em situações reais (telefone, transporte)",
    ],
    "description": "Forma a forma て dos três grupos de verbos e faz pedidos educados com 〜てください.",
    # needs = prerequisites unlocked by EARLIER lessons (none yet — this is the lone pilot). In the full course
    # the て-form lesson would `need` the verbs + ます-form from earlier lessons.
    "needs": [],
    # unlocks = what this lesson FIRST teaches (introduce-once). Namespaced refs (unlock_enums.json).
    # 出る/来る are pre-taught elsewhere; they appear here only as referenced example chips, not unlocks.
    "unlocks": [
        {"type": "grammar", "ref": "gram:te-form"},
        {"type": "grammar", "ref": "gram:te-kudasai"},
        {"type": "vocab", "ref": "vocab:乗る"},
    ],
    "feature_unlocks": ["feat:conjugation-drill"],  # te-form is the first big conjugation → unlock the drill
    "sentence_refs": ["sent:tatoeba-124708", "sent:tatoeba-146189"],
    "body": BODY,
    "exercises": [
        {"slug": "ex:n5-te-form-01-1", "type": "particle_choice",
         "prompt": "Complete: 電話＿出てください。 (Atenda o telefone, por favor.)",
         "answer": {"choices": ["に", "を", "で"], "correct": "に"},
         "explanation": "電話に出る = 'atender o telefone'. に marca o alvo da ação 出る.",
         "sentence_refs": ["sent:tatoeba-124708"], "item_refs": [{"type": "grammar", "ref": "te-kudasai"}]},
        {"slug": "ex:n5-te-form-01-2", "type": "recognition",
         "prompt": "O que 〜てください expressa?",
         "answer": {"choices": ["uma ordem ríspida", "um pedido educado", "uma pergunta"],
                    "correct": "um pedido educado"},
         "explanation": "〜てください é a forma educada de pedir algo ('por favor, faça…').",
         "sentence_refs": [], "item_refs": []},
        {"slug": "ex:n5-te-form-01-3", "type": "sentence_build",
         "prompt": "Monte o pedido 'Suba, por favor.' com as peças: [ください] [乗っ] [て]",
         "answer": {"order": ["乗っ", "て", "ください"], "text": "乗ってください。"},
         "explanation": "乗る (godan, る) → forma て 乗って; + ください = pedido educado.",
         "sentence_refs": ["sent:tatoeba-146189"], "item_refs": [{"type": "vocab", "ref": "乗る"}]},
        {"slug": "ex:n5-te-form-01-4", "type": "production",
         "prompt": "Peça educadamente para alguém ATENDER O TELEFONE (use 〜てください).",
         "answer": {"text": "電話に出てください。", "accept": ["電話に出てください", "電話にでてください"]},
         "explanation": "電話に (alvo) + 出る forma て (出て) + ください.",
         "sentence_refs": ["sent:tatoeba-124708"], "item_refs": [{"type": "vocab", "ref": "出る"}]},
        {"slug": "ex:n5-te-form-01-5", "type": "cloze",
         "prompt": "Complete a forma て: 書く → 書＿て (escrever).",
         "answer": {"text": "い", "full": "書いて"},
         "explanation": "Verbos godan terminados em く fazem a forma て em いて: 書く → 書いて.",
         "sentence_refs": [], "item_refs": []},
    ],
}


def main() -> int:
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(REC, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {OUT.relative_to(OUT.parents[3])}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
