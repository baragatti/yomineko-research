#!/usr/bin/env python3
"""P6 groundwork — author concise pt-BR topic objectives + module overviews (Layer C, needs_review).
Idempotent (updates). Run with venv python."""
import json
import sqlite3
import sys
from pathlib import Path

DB = Path(__file__).resolve().parents[2] / "db" / "corpus.sqlite"
sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
from i18n_text import set_text  # noqa: E402

OBJ = {
    "top:pre-n5-orientacao": ["Entender como o curso funciona e criar o hábito de revisão espaçada"],
    "top:pre-n5-sons": ["Reconhecer os sons do japonês e as vantagens/armadilhas do português; ter a primeira noção de altura (pitch)"],
    "top:pre-n5-hiragana": ["Ler e escrever todo o hiragana, incluindo dakuten, yōon, っ e vogais longas"],
    "top:pre-n5-katakana": ["Ler e escrever todo o katakana e reconhecer estrangeirismos comuns"],
    "top:pre-n5-pronuncia": ["Produzir o ritmo de mora, o comprimento vocálico, o ん e o devozeamento de です/ます"],
    "top:pre-n5-saudacoes": ["Cumprimentar, agradecer, pedir desculpas e se apresentar em situações básicas"],
    "top:n5-desu-wa": ["Dizer o que algo é e fazer perguntas sim/não com です e a partícula は",
                       "Usar これ/それ/あれ e a partícula の (posse)"],
    "top:n5-perguntas": ["Perguntar o quê/quem/onde/quando com palavras interrogativas e demonstrativos"],
    "top:n5-numeros-tempo": ["Dizer horas, datas e preços; contar objetos com contadores básicos"],
    "top:n5-verbos": ["Descrever ações no presente polido (ます) e reconhecer a forma de dicionário; usar を e が"],
    "top:n5-particulas-lugar": ["Dizer onde algo está, para onde se vai e com quem (で/に/へ/と; ある・いる)"],
    "top:n5-passado": ["Falar de eventos no passado polido e marcar ênfase/confirmação (ね/よ)"],
    "top:n5-adjetivos": ["Descrever pessoas e coisas com adjetivos い e な (presente/passado/negativo)",
                         "Expressar gostos com 好き/上手 + が"],
    "top:n5-comparacoes": ["Comparar coisas (より/一番) e dizer o que se quer (〜たい/〜がほしい)"],
    "top:n5-te-form": ["Formar a forma て e usá-la em pedidos (てください), ações em curso (ています) e permissão"],
    "top:n5-convites": ["Convidar e sugerir (ましょう/ませんか) e falar de habilidade (ことができる)"],
    "top:n5-rotina": ["Descrever a própria rotina usando advérbios de frequência"],
    "top:n5-conectando": ["Justificar (から/ので), contrastar (が/けど) e dar opinião (と思う)"],
    "top:n5-revisao": ["Consolidar o N5 e checar os can-do antes de avançar"],
    "top:n4-forma-simples": ["Usar a forma simples e alternar entre registro casual e polido"],
    "top:n4-oracoes-relativas": ["Descrever substantivos com orações relativas"],
    "top:n4-condicionais": ["Expressar condições e hipóteses (たら/ば/と/なら)"],
    "top:n4-potencial": ["Dizer o que se é capaz de fazer (forma potencial)"],
    "top:n4-volitivo": ["Expressar intenção e planos (volitivo, つもり, 〜ようと思う)"],
    "top:n4-transitividade": ["Escolher o verbo e a partícula corretos entre pares transitivo/intransitivo"],
    "top:n4-dar-receber": ["Falar de dar e receber favores (あげる/くれる/もらう)"],
    "top:n4-experiencia": ["Falar de experiências e mudanças (〜たことがある, なる, 〜ようになる)"],
    "top:n4-obrigacao": ["Expressar obrigação e permissão (〜なければならない, 〜てもいい)"],
    "top:n4-aspecto": ["Nuançar ações (〜てみる, 〜ておく, 〜てしまう)"],
    "top:n4-suposicao": ["Inferir e supor (そう/よう/らしい/みたい, でしょう)"],
    "top:n4-passiva": ["Usar a voz passiva"],
    "top:n4-causativa": ["Usar a causativa e a causativa-passiva"],
    "top:n4-keigo": ["Usar keigo básico (teineigo; introdução a sonkeigo/kenjōgo)"],
    "top:n4-conectores": ["Encadear ideias com conectores avançados (のに, 〜ても, 〜ように)"],
    "top:n4-revisao": ["Consolidar o N4 e checar os can-do"],
}
OVERVIEW = {
    "mod:pre-n5": "Do zero absoluto: ler e escrever os dois silabários (kana), pronunciar com ritmo de mora e se virar em saudações e apresentações.",
    "mod:n5": "Apresentar-se e comunicar-se no registro polido (です/ます) sobre rotina, tempo, dinheiro, compras, comida e direções; ler cerca de 100 kanji.",
    "mod:n4": "Usar a forma simples e o registro casual, orações relativas, condicionais, potencial, dar-e-receber, voz passiva/causativa e keigo básico — suficiente para trabalho e vida no Japão.",
}


def main() -> int:
    con = sqlite3.connect(DB)
    cur = con.cursor()
    nt = 0
    for slug, objs in OBJ.items():
        r = cur.execute("SELECT id FROM topic WHERE slug=?", (slug,)).fetchone()
        if r:
            set_text(con, "topic", r[0], "objectives", objs, layer="C")
            nt += 1
    nm = 0
    for slug, ov in OVERVIEW.items():
        r = cur.execute("SELECT id FROM course_module WHERE slug=?", (slug,)).fetchone()
        if r:
            set_text(con, "course_module", r[0], "overview", ov, layer="C")
            nm += 1
    con.commit()
    print(f"topics objectives set: {nt}/{con.execute('SELECT count(*) FROM topic').fetchone()[0]}; "
          f"module overviews set: {nm}")
    con.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
