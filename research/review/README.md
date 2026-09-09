# Revisão do corpus — guia do professor

Esta pasta é onde você lê o material do curso e onde registra o que aprovou, o que quer corrigir e o
que precisa ser refeito. Uma página, do começo ao fim.

---

## 1. Onde está o material

Uma pasta por registro, um arquivo por nível:

| pasta | o que tem dentro |
|---|---|
| `vocab/` | palavras: leitura, romaji, sentidos em pt-BR e em inglês |
| `kanji/` | kanji: traços, radical, significados, leituras on/kun e as notas de cada leitura |
| `grammar/` | pontos gramaticais: rótulo, explicação, formação, nuance, formas |
| `sentences/` | frases do banco: japonês, leitura, tradução, tradução literal, explicação da estrutura e a dissecação token a token |
| `readings/` | textos curtos de leitura presos a uma lição |
| `exams/` | itens de prova (enunciado, resposta, distratores) |
| `families/` | famílias e grupos (classes de conjugação, pares de contraste, conjuntos temáticos) |
| `speak/` | unidades da trilha Fala Primeiro |

Os arquivos são **gerados**. Não edite nenhum deles: a próxima geração apaga o que você escreveu.
O que você escreve vai numa **ficha** (seção 3).

Para regerar depois de uma mudança no corpus:

```bash
python scripts/export/build_review_views.py --level n5
```

---

## 2. Como ler uma view

Os registros aparecem **na ordem em que o aluno os encontra no curso** — módulo, tópico, lição. É de
propósito: só nessa ordem dá para perceber que uma explicação usa algo que ainda não foi ensinado.

Cada registro tem:

* um título com o **id** entre crases (`vocab:1005110`) — esse id é o endereço permanente do
  registro, é ele que você copia para a ficha;
* o **japonês com a leitura**;
* **onde entra no curso** (a lição que apresenta o item);
* se o registro está marcado como **`needs_review`**;
* um bloco recolhido de **contexto** — frases que usam o item, membros de uma família, gramática
  ligada. Contexto é para você julgar melhor; não é alvo de parecer;
* e depois, um bloco por **endereço de parecer**.

Um bloco de parecer é assim:

```
### `explanation@pt-BR` · camada C · hash `ee45e1b06df2e2fe`

_Ledger:_ —

> São as duas formas da cópula japonesa, a palavrinha que liga o sujeito…
```

* **`explanation@pt-BR`** é o endereço: campo + idioma. É exatamente isso que você copia.
* **camada** diz de onde veio o conteúdo e quanto ele depende de você:
  * **A** — fato de dataset (JMdict, KANJIDIC2, Tatoeba). Não se reescreve aqui; se estiver errado,
    o problema é de ligação, não de redação — use `reject` e explique.
  * **B** — derivado por máquina e conferido contra a camada A (traduções, glosas, dissecação).
  * **C** — **pedagogia autorada**. É aqui que a sua leitura decide. Priorize C.
* **hash** é a impressão digital do texto que está impresso ali. É o que garante que o seu parecer
  vale para *esse* texto e não para o que estiver no lugar dele daqui a um mês.
* **_Ledger:_** mostra o parecer que já existe para aquele endereço: `—` (ninguém avaliou),
  **aprovado**/**rejeitado** com nome e data, ou **desatualizado** (alguém aprovou, o texto mudou
  depois, precisa de nova leitura).

O último bloco de cada registro é `*`: aprovar `*` é aprovar o registro inteiro de uma vez.

---

## 3. Como preencher uma ficha

Peça uma ficha em branco já endereçada — ela vem com os ids e os hashes prontos:

```bash
python scripts/review_apply.py --template grammar n5 --only-flagged --limit 40
# escreve research/review/sheets/n5-grammar.json
```

Abra o arquivo e preencha. Exemplo completo (`research/review/sheets/EXEMPLO-n5-grammar.json` tem
uma versão em branco pronta para copiar):

```json
{
  "schema_version": "1.0",
  "sheet_id": "n5-grammar-01",
  "reviewed_by": "teacher:ana",
  "reviewed_at": "2026-09-09",
  "records": [
    {
      "id": "gram:da-desu",
      "record_hash": "214761a689ba9caf",
      "approve": ["explanation@pt-BR", "label@pt-BR"],
      "edit":    {"formation@pt-BR": "Substantivo + です／だ: 先生です／先生だ. …"},
      "reject":  {"nuance@pt-BR": "mistura だ com である; precisa ser reescrito do zero"},
      "note":    "opcional; fica registrado junto com a aprovação"
    }
  ]
}
```

Três vereditos, e cada endereço aceita **um só**:

| veredito | quando usar | o que acontece |
|---|---|---|
| `approve` | o texto está certo e você assina embaixo | vira uma aprovação no ledger, presa ao hash |
| `edit` | você sabe exatamente como o texto deve ficar | vira uma linha de correção rastreada, com o texto atual e o seu |
| `reject` | está errado, mas consertar não é questão de redigir de novo | vira uma rejeição no ledger, com o seu motivo |

Regras que a ferramenta cobra:

* **`reviewed_by` e `reviewed_at` são obrigatórios.** Uma aprovação anônima não é uma revisão.
* **`record_hash` é obrigatório em cada registro.** Copie do bloco `*` da view (ou deixe o que o
  `--template` colocou).
* **`edit` só vale em campo de texto.** Coisas como `senses`, `readings` e `forms` são estruturas;
  reescrever à mão vira erro de digitação disfarçado de decisão. Nesses casos use `reject` com o
  motivo, e uma campanha reconstrói.
* **Se algo mudou desde que a view foi gerada, a ficha inteira é recusada.** Não é rigor por rigor:
  se o corpus foi reescrito embaixo de você, os seus pareceres foram formados sobre um texto que
  talvez não esteja mais lá. Regere a view, releia, refaça a ficha.

---

## 4. O que acontece depois

```bash
python scripts/review_apply.py --sheet research/review/sheets/n5-grammar-01.json --check   # confere
python scripts/review_apply.py --sheet research/review/sheets/n5-grammar-01.json           # grava
```

* As **aprovações e rejeições** entram em `research/derived/review_ledger.json`. O exportador carimba
  `review_status` só nos registros cujo parecer continua válido (o hash ainda bate); quando o texto
  muda depois, o parecer aparece como *desatualizado* e volta para a fila. Nada expira por tempo.
* As **edições** viram uma tabela em `research/derived/repairs/pending/<sheet_id>.json`, com o texto
  antigo e o novo lado a lado. **Ela não é aplicada na hora**: aplicar mexe no banco e é outro passo,
  feito por quem cuida da base. O comando aparece impresso no final da execução.
* Rodar a mesma ficha duas vezes não duplica nada.

Para ver o que ainda falta revisar:

```bash
python scripts/review_queue.py --subtract research/derived/review_ledger.json
```

---

## 5. Por onde começar

Pelo N5, e dentro do N5 pela **camada C** — explicações de gramática, títulos e textos de leitura,
enunciados de prova. É onde a leitura humana muda mais o resultado. As camadas A e B já passam por
verificação automática contra os datasets; o que elas precisam de você é o olho para o caso em que a
máquina acertou a regra e errou o ensino.
