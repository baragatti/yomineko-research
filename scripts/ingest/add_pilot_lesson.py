#!/usr/bin/env python3
"""P6 pilot — author one lesson (〜てください) end-to-end: dense pt-BR body + structured exercises,
referencing the dissected corpus BY ID. Inserts lesson/exercise rows + lesson_introduces /
lesson_sentence / exercise_* links. Idempotent by lesson slug. Run with venv python."""
from __future__ import annotations

import json
import sqlite3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from i18n_text import set_text  # noqa: E402

DB = Path(__file__).resolve().parents[2] / "db" / "corpus.sqlite"

BODY_PT = """\
## A forma て (te) e os pedidos educados

Nesta lição você dá um dos passos mais importantes do N5: a **forma て** (lê-se *te*). Ela é a
"forma conectiva" do verbo — uma engrenagem que liga verbos a dezenas de estruturas. Aqui usamos
o primeiro e mais útil emprego dela: **fazer pedidos educados** com **〜てください** ("faça o favor de…").

### Como se forma a forma て

A forma て depende do grupo do verbo:

- **Verbos ichidan (る)** — tire る e acrescente て: 食べる → 食べ**て**, 出る → 出**て**.
- **Verbos irregulares** — する → し**て**, 来る (くる) → 来**て** (a leitura muda para き).
- **Verbos godan (う)** — seguem o padrão de som da última sílaba:
  - う・つ・る → っ**て**  (例: 乗る → 乗っ**て**)
  - ぬ・ぶ・む → ん**で**  (例: 読む → 読ん**で**)
  - く → い**て** / ぐ → い**で**  (例: 書く → 書い**て**)
  - す → し**て**  (例: 話す → 話し**て**)
  - **Exceção:** 行く → 行っ**て** (e não 行いて).

> 💡 **Vantagem PT:** o っ pequeno (em 乗っ**て**, 行っ**て**) é uma **pausa de uma mora** — bata uma
> palma extra: *no-t-te*. O brasileiro já controla esse "travar" da consoante; só não esqueça de
> dar-lhe o seu tempo.

### O pedido: 〜てください

Forma て + **ください** = um pedido educado, "por favor faça…".

- 電話に**出てください**。 → *"Atenda o telefone, por favor."* (frase `sent:tatoeba-124708`)
- **乗ってください**。 → *"Suba, por favor."* (entrar no ônibus/carro — `sent:tatoeba-146189`)

Repare na partícula: em 電話**に**出る, o **に** marca o **alvo** ("atender *ao* telefone"). O verbo
出る sozinho significa "sair", mas com 電話に passa a "atender". Esse tipo de combinação verbo +
partícula é comum — vale aprender o conjunto.

> ⚠️ **Armadilha PT:** não traduza ください como um verbo no imperativo seco ("faça!"). Em japonês,
> 〜てください já é **educado** — equivale ao nosso "por favor, atenda", não a uma ordem.

### Encadeando ações: 〜てから

A forma て também liga ações em sequência. Com **から**, forma **〜てから** = "**depois de** fazer":

- 電話を**してから**来てください。 → *"Ligue antes de vir, por favor."* (lit. "depois de telefonar,
  venha") — frase `sent:tatoeba-124665`. Aqui aparecem **dois** usos da forma て na mesma frase:
  してから (sequência) e 来て + ください (pedido).

### Ao final desta lição

Você consegue formar a forma て dos três grupos de verbos e fazer pedidos educados do dia a dia —
no telefone, no transporte e em consultas. Nas próximas lições, a mesma forma て abrirá 〜ています
(ação em andamento), 〜てもいい (permissão) e muito mais.
"""

EXERCISES = [
    {"slug": "ex:n5-te-form-01-1", "type": "particle_choice",
     "prompt_pt": "Complete: 電話＿出てください。 (Atenda o telefone, por favor.)",
     "answer": {"choices": ["に", "を", "で"], "correct": "に"},
     "explanation_pt": "電話に出る = 'atender o telefone'. に marca o alvo da ação 出る.",
     "sentence_refs": ["sent:tatoeba-124708"], "item_refs": []},
    {"slug": "ex:n5-te-form-01-2", "type": "recognition",
     "prompt_pt": "O que 〜てください expressa?",
     "answer": {"choices": ["uma ordem ríspida", "um pedido educado", "uma pergunta"],
                "correct": "um pedido educado"},
     "explanation_pt": "〜てください é a forma educada de pedir algo ('por favor, faça…').",
     "sentence_refs": [], "item_refs": []},
    {"slug": "ex:n5-te-form-01-3", "type": "sentence_build",
     "prompt_pt": "Monte o pedido 'Suba, por favor.' com as peças: [ください] [乗っ] [て]",
     "answer": {"order": ["乗っ", "て", "ください"], "text": "乗ってください。"},
     "explanation_pt": "乗る (godan, る) → forma て 乗って; + ください = pedido educado.",
     "sentence_refs": ["sent:tatoeba-146189"], "item_refs": []},
    {"slug": "ex:n5-te-form-01-4", "type": "production",
     "prompt_pt": "Peça educadamente para alguém ATENDER O TELEFONE (use 〜てください).",
     "answer": {"text": "電話に出てください。", "accept": ["電話に出てください", "電話にでてください"]},
     "explanation_pt": "電話に (alvo) + 出る forma て (出て) + ください.",
     "sentence_refs": ["sent:tatoeba-124708"], "item_refs": []},
    {"slug": "ex:n5-te-form-01-5", "type": "cloze",
     "prompt_pt": "Complete a forma て: 書く → 書＿て (escrever).",
     "answer": {"text": "い", "full": "書いて"},
     "explanation_pt": "Verbos godan terminados em く fazem a forma て em いて: 書く → 書いて.",
     "sentence_refs": [], "item_refs": []},
]


def gid(con, key):
    r = con.execute("SELECT id FROM grammar_point WHERE key=?", (key,)).fetchone()
    return r[0] if r else None


def vid(con, hw):
    r = con.execute("SELECT id FROM vocab WHERE headword=?", (hw,)).fetchone()
    return r[0] if r else None


def sid(con, slug):
    r = con.execute("SELECT id FROM sentence WHERE slug=?", (slug,)).fetchone()
    return r[0] if r else None


def main() -> int:
    con = sqlite3.connect(DB)
    con.execute("PRAGMA foreign_keys = ON;")
    cur = con.cursor()
    lslug = "les:n5-te-form-01"
    if cur.execute("SELECT id FROM lesson WHERE slug=?", (lslug,)).fetchone():
        print("[skip] pilot lesson already exists")
        return 0
    topic_id = cur.execute("SELECT id FROM topic WHERE slug='top:n5-te-form'").fetchone()[0]
    cur.execute(
        "INSERT INTO lesson (slug,topic_id,ord,prerequisites,cumulative_known_set,source,created_by,"
        "layer,needs_review) VALUES (?,?,?,?,?,?,?,?,?)",
        (lslug, topic_id, 1, json.dumps([], ensure_ascii=False), None, "ai", "ai", "C", 1))
    lid = cur.lastrowid
    set_text(con, "lesson", lid, "title", "Pedidos educados: a forma て + ください", layer="C")
    set_text(con, "lesson", lid, "objectives",
             ["Formar a forma て dos três grupos de verbos",
              "Fazer pedidos educados com 〜てください",
              "Reconhecer 〜てください em situações reais (telefone, transporte)",
              "Encadear ações com 〜てから"], layer="C")
    set_text(con, "lesson", lid, "body", BODY_PT, layer="C")

    # introduces (items first taught here): grammar te-form + te-kudasai + te-kara; vocab 出る, 乗る, 来る
    for key in ("te-form", "te-kudasai", "te-kara"):
        g = gid(con, key)
        if g:
            cur.execute("INSERT OR IGNORE INTO lesson_introduces (lesson_id,member_type,member_id) "
                        "VALUES (?,?,?)", (lid, "grammar", g))
    for hw in ("出る", "乗る", "来る"):
        v = vid(con, hw)
        if v:
            cur.execute("INSERT OR IGNORE INTO lesson_introduces (lesson_id,member_type,member_id) "
                        "VALUES (?,?,?)", (lid, "vocab", v))
    # featured sentences (BY ID)
    for slug in ("sent:tatoeba-124708", "sent:tatoeba-146189", "sent:tatoeba-124665"):
        s = sid(con, slug)
        if s:
            cur.execute("INSERT OR IGNORE INTO lesson_sentence (lesson_id,sentence_id) VALUES (?,?)", (lid, s))
    # exercises
    for i, ex in enumerate(EXERCISES):
        cur.execute("INSERT INTO exercise (slug,lesson_id,ord,type,answer,needs_review) "
                    "VALUES (?,?,?,?,?,?)",
                    (ex["slug"], lid, i, ex["type"],
                     json.dumps(ex["answer"], ensure_ascii=False), 1))
        eid = cur.lastrowid
        set_text(con, "exercise", eid, "prompt", ex["prompt_pt"], layer="C")
        set_text(con, "exercise", eid, "explanation", ex["explanation_pt"], layer="C")
        for slug in ex.get("sentence_refs", []):
            s = sid(con, slug)
            if s:
                cur.execute("INSERT OR IGNORE INTO exercise_sentence (exercise_id,sentence_id) "
                            "VALUES (?,?)", (eid, s))
    con.commit()
    print(f"pilot lesson {lslug} (id {lid}) authored: {len(EXERCISES)} exercises, "
          f"{cur.execute('SELECT COUNT(*) FROM lesson_sentence WHERE lesson_id=?', (lid,)).fetchone()[0]} "
          f"sentence refs, "
          f"{cur.execute('SELECT COUNT(*) FROM lesson_introduces WHERE lesson_id=?', (lid,)).fetchone()[0]} "
          f"introduces.")
    con.close()
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())
