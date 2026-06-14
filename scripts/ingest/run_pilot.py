#!/usr/bin/env python3
"""P5 pilot — persist 5 hand-authored, real-Tatoeba te-form dissections (Layer B) + validate.

Pilot topic: top:n5-te-form. Selection-over-generation: all 5 sentences are real Tatoeba
sentences chosen within the topic's cumulative known-set (i+1). The Japanese skeleton is from
SudachiPy (Layer A); the pt-BR translation/glosses/particle explanations below are authored
(Layer B, needs_review). This proves the end-to-end pipeline + schema + the §6 dissection shape.
"""
from __future__ import annotations

import sqlite3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
from dissect import Dissector  # noqa: E402
from persist_dissection import persist  # noqa: E402

DB = Path(__file__).resolve().parents[2] / "db" / "corpus.sqlite"

PILOT = [
    {
        "slug": "sent:tatoeba-124708", "jp": "電話に出てください。", "jp_source": "tatoeba:124708",
        "en": "Please answer the phone.", "level": "n5", "translation_confidence": 0.95,
        "pt": "Atenda o telefone, por favor.",
        "pt_literal": "Telefone–(ao)–atender(forma て)–faça o favor.",
        "structure_explanation_pt": (
            "Pedido educado com 〜てください ('faça o favor de…'). O verbo 出る (でる, sair) ganha um "
            "sentido especial com 電話に: 電話に出る = 'atender o telefone'. A partícula に marca o alvo. "
            "Para pedir, usa-se a forma て do verbo (出て) seguida de ください."),
        "tags": ["te-form", "requests", "telefone", "cotidiano"],
        "tokens": {
            0: {"role_pt": "alvo da ação", "gloss_pt": "telefone"},
            2: {"role_pt": "verbo principal", "gloss_pt": "atender (lit. 'sair'; com 電話に = 'atender o telefone')",
                "conjugation_note_pt": "forma て de 出る (でる, ichidan): 出る→出て"},
            4: {"role_pt": "auxiliar de pedido", "gloss_pt": "(faça o) favor de…",
                "conjugation_note_pt": "〜てください: pedido educado"},
        },
        "particles": {
            1: {"function_pt": "alvo/ponto de contato",
                "explanation_pt": "に marca o que se atende: 電話に出る = 'atender ao telefone' (に indica o alvo da ação)."},
            3: {"function_pt": "conector da forma て",
                "explanation_pt": "A forma て (出て) liga o verbo ao auxiliar ください, formando o pedido educado."},
        },
        "grammar_keys": ["te-form", "てください"],
    },
    {
        "slug": "sent:tatoeba-146189", "jp": "乗ってください。", "jp_source": "tatoeba:146189",
        "en": "Please get in.", "level": "n5", "translation_confidence": 0.9,
        "pt": "Suba, por favor. (entre no veículo)",
        "pt_literal": "Embarcar(forma て)–faça o favor.",
        "structure_explanation_pt": (
            "Pedido com 〜てください. 乗る (のる) = subir/embarcar (em ônibus, carro, trem). O veículo, "
            "quando dito, leva a partícula に (バスに乗る). Repare no っ: a forma て dos verbos godan "
            "terminados em る é 〜って (乗る→乗って)."),
        "tags": ["te-form", "requests", "transporte", "cotidiano"],
        "new_items": ["kanji:乗"],
        "tokens": {
            0: {"role_pt": "verbo principal", "gloss_pt": "suba / entre (em veículo)",
                "conjugation_note_pt": "forma て de 乗る (のる, godan): 乗る→乗って"},
            2: {"role_pt": "auxiliar de pedido", "gloss_pt": "por favor",
                "conjugation_note_pt": "〜てください"},
        },
        "particles": {
            1: {"function_pt": "conector da forma て",
                "explanation_pt": "乗って (forma て de 乗る) + ください = 'suba, por favor'. O っ é a forma て "
                                   "dos verbos godan em る."},
        },
        "grammar_keys": ["te-form", "てください"],
    },
    {
        "slug": "sent:tatoeba-124665", "jp": "電話をしてから来てください。", "jp_source": "tatoeba:124665",
        "en": "Please phone me before you come.", "level": "n5", "translation_confidence": 0.92,
        "pt": "Ligue antes de vir, por favor.",
        "pt_literal": "Telefone(objeto)–fazer(forma て)–depois de–vir(forma て)–faça o favor.",
        "structure_explanation_pt": (
            "Dois usos da forma て. 1) 〜てから = 'depois de [fazer]': 電話をしてから = 'depois de telefonar'. "
            "2) 〜てください = pedido: 来てください = 'venha, por favor'. 電話をする = telefonar (する com o "
            "objeto 電話を). 来る é irregular: a forma て é 来て (leitura き)."),
        "tags": ["te-form", "requests", "sequência", "telefone"],
        "tokens": {
            0: {"role_pt": "objeto de する", "gloss_pt": "telefone (telefonema)"},
            2: {"role_pt": "verbo (fazer)", "gloss_pt": "fazer (電話をする = 'telefonar')",
                "conjugation_note_pt": "forma て de する (irregular): する→して"},
            5: {"role_pt": "verbo principal", "gloss_pt": "vir",
                "conjugation_note_pt": "forma て de 来る (くる, irregular): 来る→来て (leitura muda para き)"},
            7: {"role_pt": "auxiliar de pedido", "gloss_pt": "por favor",
                "conjugation_note_pt": "〜てください"},
        },
        "particles": {
            1: {"function_pt": "objeto direto",
                "explanation_pt": "を marca 電話 como objeto de する: 電話をする = 'fazer um telefonema / telefonar'."},
            3: {"function_pt": "forma て (em 〜てから)",
                "explanation_pt": "A forma て de する (して) combina com から no padrão 〜てから = 'depois de fazer'."},
            4: {"function_pt": "'depois de' (sequência)",
                "explanation_pt": "〜てから liga as duas ações em ordem: primeiro telefonar, depois vir."},
            6: {"function_pt": "conector da forma て (pedido)",
                "explanation_pt": "来て + ください = pedido educado 'venha'."},
        },
        "grammar_keys": ["te-form", "てください", "てから"],
    },
    {
        "slug": "sent:tatoeba-97802", "jp": "彼らはチェスをしています。", "jp_source": "tatoeba:97802",
        "en": "They are playing chess.", "level": "n5", "translation_confidence": 0.95,
        "pt": "Eles estão jogando xadrez.",
        "pt_literal": "Eles(tópico)–xadrez(objeto)–fazer(forma て)–estar(polido) → estão fazendo.",
        "structure_explanation_pt": (
            "〜ています indica ação em progresso ('estar fazendo'). Forma-se com a forma て do verbo + います "
            "(de いる). チェスをする = 'jogar xadrez' (する com objeto を). 彼ら = 'eles' (彼 'ele' + sufixo "
            "plural ら). は marca o tópico."),
        "tags": ["te-form", "progressivo", "ています", "lazer"],
        "tokens": {
            0: {"role_pt": "tópico (com ら e は)", "gloss_pt": "ele (com ら: 'eles')"},
            1: {"role_pt": "sufixo de plural", "gloss_pt": "sufixo de plural (pessoas): 彼ら = 'eles'"},
            3: {"role_pt": "objeto", "gloss_pt": "xadrez"},
            5: {"role_pt": "verbo (fazer)", "gloss_pt": "fazer (チェスをする = 'jogar xadrez')",
                "conjugation_note_pt": "forma て de する: して"},
            7: {"role_pt": "auxiliar progressivo", "gloss_pt": "estar (auxiliar de 〜ている)",
                "conjugation_note_pt": "いる na forma polida います → しています = 'estão jogando'"},
        },
        "particles": {
            2: {"function_pt": "tópico",
                "explanation_pt": "は marca 彼ら ('eles') como tópico: 'Quanto a eles, …'."},
            4: {"function_pt": "objeto direto",
                "explanation_pt": "を marca チェス como objeto de する: チェスをする = 'jogar xadrez'."},
            6: {"function_pt": "conector da forma て (em 〜ている)",
                "explanation_pt": "して + います = しています: forma て + いる cria o aspecto progressivo."},
        },
        "grammar_keys": ["te-form", "ています", "ている"],
    },
    {
        "slug": "sent:tatoeba-83013", "jp": "母は外出しています。", "jp_source": "tatoeba:83013",
        "en": "My mother is out.", "level": "n5", "translation_confidence": 0.9,
        "pt": "Minha mãe está fora (saiu).",
        "pt_literal": "Mãe(tópico)–sair(forma て)–estar(polido) → está fora.",
        "structure_explanation_pt": (
            "Aqui 〜ています indica ESTADO resultante, não ação em progresso: 外出している = 'estar fora "
            "(por ter saído)'. 外出する = 'sair (de casa)'. Mesmo padrão 〜ている, sentido de estado. 母 = "
            "'(minha) mãe' — em japonês usa-se 母 para a própria mãe."),
        "tags": ["te-form", "ています", "estado", "família"],
        "new_items": ["kanji:母"],
        "tokens": {
            0: {"role_pt": "tópico", "gloss_pt": "(minha) mãe"},
            2: {"role_pt": "raiz de する", "gloss_pt": "saída de casa (外出する = 'sair')"},
            3: {"role_pt": "verbo (fazer)", "gloss_pt": "fazer (外出する = 'sair')",
                "conjugation_note_pt": "forma て de する: して"},
            5: {"role_pt": "auxiliar (estado)", "gloss_pt": "estar (auxiliar de 〜ている)",
                "conjugation_note_pt": "います → しています; aqui = estado resultante ('está fora')"},
        },
        "particles": {
            1: {"function_pt": "tópico",
                "explanation_pt": "は marca 母 ('minha mãe') como tópico."},
            4: {"function_pt": "conector da forma て (em 〜ている)",
                "explanation_pt": "外出して + います: 〜ています aqui indica ESTADO resultante ('está fora'), "
                                  "não ação em progresso."},
        },
        "grammar_keys": ["te-form", "ています", "ている"],
    },
]


def main() -> int:
    con = sqlite3.connect(DB)
    con.execute("PRAGMA foreign_keys = ON;")
    diss = Dissector()
    ids = []
    for rec in PILOT:
        sid = persist(con, diss, rec)
        ids.append(sid)
        print(f"  persisted {rec['slug']} -> id {sid}")
    print(f"pilot: {len(ids)} dissected sentences persisted (te-form).")
    con.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
