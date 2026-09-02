#!/usr/bin/env python3
"""Give every reading box a real title, replacing the exported placeholder `Leitura` / `Reading`.

Source audit: `research/reports/qa_sweep/readings_quality.md`, finding A1 — the title authoring pass
stopped half-way, so 146 of the 286 boxes still carry the literal placeholder that `build_readings.py`
inserts (`"Leitura"` / `"Reading"`, ingest/build_readings.py line ~142). A title renders above the
passage in the lesson UI, so every untitled box is indistinguishable from every other one, and a
reviewer cannot tell "not yet titled" from "deliberately untitled".

The 286 titles below were authored one box at a time from the box's OWN `jp` + `translation_pt`: short
(2-6 words), concrete, about what that passage actually says, never generic, never revealing the answer
to an exercise, no terminal period, no em dash (design/translation_style.md). `title_en` is a plain
English equivalent in sentence case, not a second translation of the Japanese.

STORAGE MODEL. Reading boxes live ONLY in `db/corpus.sqlite` (`reading` table; `title_pt` / `title_en`
are plain columns, NOT `localized_text` rows). `corpus/readings/*.json` and
`prototype/app/data/readings.json` are REGENERATED from it and are never edited here. This script runs
no exporter — run `scripts/export/export_readings.py` afterwards to publish.

NEVER OVERWRITES A REAL TITLE. A field is written only when its current value is NULL, empty, or the
exact placeholder. A box already carrying a different real title (the 140 the earlier pass did title,
plus anything a later pass wrote) is SKIPPED LOUDLY with both values printed, and nothing is written for
it — deciding between two authored titles is a content call, not a mechanical one. Because the check is
per column, a box whose pt title landed but whose en title is still `Reading` gets only the en half.

CROSS-BATCH DUPLICATE CHECK. Titles were authored in batches, so two boxes can end up with the same
pt-BR title without either batch noticing. Before writing anything the script projects the FINAL state
of all 286 titles (what it is about to write, plus what every box it will not touch already holds) and
refuses to apply any title that would collide with another box's; the collision is reported with both
slugs so the later one can be re-qualified from its own passage. A duplicate that already exists between
two untouched boxes is reported as a warning.

WHAT THE FIRST RUN FOUND (2026-09-02) — read this before assuming the script has work to do. By the
time it was first run, NO box was still a placeholder in `db/corpus.sqlite`: another pass had already
titled the 146 the export still shows as `Leitura`, without leaving a script behind. So the first run
wrote NOTHING. Of the 286 titles below, 223 were already in the DB byte for byte; 63 differed and were
skipped as real titles (19 differ in pt-BR, 61 in en, 44 in en only). 9 of the 63 are titles the earlier
authoring pass had already committed to `corpus/readings/*.json`; the other 54 reached the DB after that
export and exist nowhere durable. Choosing between the two wordings is a content call for whoever owns
the title pass — this script will not make it. One collision survives that decision:
`read:n5-adjetivos-05-01` and `read:n4-volitivo-05-01` both read "Só dando uma olhada", which is exactly
what the duplicate check below exists to prevent; the batch here resolves it (`Estou só olhando` for the
N5 box) but cannot apply it without overwriting a real title.

Idempotent: a field whose value already equals the intended title is a no-op, so a second run reports
0 changes. Usage: apply_reading_titles.py [--check]
"""
from __future__ import annotations

import argparse
import sqlite3
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]

ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / "db" / "corpus.sqlite"

# What build_readings.py writes when it has no title. Only these are overwritable.
PLACEHOLDER = {"Leitura", "Reading"}

# (reading slug, title_pt, title_en) — one row per box, in course order (N5, N4, N3).
TITLES: tuple[tuple[str, str, str], ...] = (
    ("read:n5-adjetivos-04-01", "Aonde você está indo", "Where are you headed"),
    ("read:n5-adjetivos-05-01", "Estou só olhando", "I'm just looking"),
    ("read:n5-adjetivos-06-01", "Beleza, vamos nessa", "All right, let's go"),
    ("read:n5-adjetivos-07-01", "De onde você veio", "Where did you come from"),
    ("read:n5-adjetivos-08-01", "Quanto tempo você ficou lá", "How long you stayed there"),
    ("read:n5-comparacoes-04-01", "Quanto falta até o green", "How far to the green"),
    ("read:n5-comparacoes-05-01", "Vamos à praia, sem desculpa", "To the beach, no excuses"),
    ("read:n5-comparacoes-06-01", "Preciso mesmo ir", "Do I really have to go"),
    ("read:n5-conectando-04-01", "Bati numa árvore", "I hit a tree"),
    ("read:n5-conectando-05-01", "Mil pessoas no local", "A thousand people there"),
    ("read:n5-conectando-06-01", "Com um carro dá para ir", "With a car we can get there"),
    ("read:n5-conectando-07-01", "Só água e uma pausa", "Just water and a break"),
    ("read:n5-convites-04-01", "Um convite para o shopping", "An invitation to the mall"),
    ("read:n5-convites-05-01", "A caminho da escola", "On the way to school"),
    ("read:n5-convites-06-01", "Vinho ou maçã", "Wine or apple"),
    ("read:n5-desu-wa-04-01", "Tudo graças a você", "All thanks to you"),
    ("read:n5-desu-wa-05-01", "Um oi e um obrigado", "A hello and a thank you"),
    ("read:n5-numeros-tempo-04-01", "A culpa é sua", "It's your fault"),
    ("read:n5-numeros-tempo-05-01", "Obrigado e adeus", "Thanks and goodbye"),
    ("read:n5-numeros-tempo-06-01", "Bom dia duas vezes", "Good morning twice"),
    ("read:n5-numeros-tempo-07-01", "Alô e boas-vindas", "Hello and welcome"),
    ("read:n5-particulas-lugar-04-01", "Quem quer pizza", "Who wants pizza"),
    ("read:n5-particulas-lugar-05-01", "Ketchup e chave reserva", "Ketchup and a spare key"),
    ("read:n5-particulas-lugar-06-01", "Você tem um tempinho", "Do you have a minute"),
    ("read:n5-particulas-lugar-07-01", "Que maneiro", "That is so cool"),
    ("read:n5-particulas-lugar-08-01", "Quantos anos e quanto custa", "How old and how much"),
    ("read:n5-passado-04-01", "Que dureza", "That is rough"),
    ("read:n5-passado-05-01", "E você, o que faria", "And you, what would you do"),
    ("read:n5-perguntas-04-01", "O que era aquilo", "What was that"),
    ("read:n5-perguntas-05-01", "Despedida com alfinetada", "A goodbye with a jab"),
    ("read:n5-perguntas-06-01", "Boa noite e obrigado", "Good night and thanks"),
    ("read:n5-rotina-03-01", "Um biscoito enquanto espera", "A cookie while you wait"),
    ("read:n5-rotina-04-01", "Como você veio para a escola", "How you got to school"),
    ("read:n5-te-form-03-01", "O gato na cadeira", "The cat on the chair"),
    ("read:n5-te-form-04-01", "Procurando uma bola", "Looking for a ball"),
    ("read:n5-te-form-05-01", "Chegou a hora de sair", "Time to head out"),
    ("read:n5-te-form-06-01", "Sem zoar, vamos logo", "No teasing, let's go"),
    ("read:n5-te-form-07-01", "Que tipo de prova é essa", "What kind of test is it"),
    ("read:n5-te-form-08-01", "Preciso sair, mas antes", "I have to go, but first"),
    ("read:n5-verbos-03-01", "Tentei fazer dieta", "I tried to diet"),
    ("read:n5-verbos-04-01", "Vamos indo então", "Let's get going"),
    ("read:n5-verbos-05-01", "Atrás de um clipe", "Hunting for a paper clip"),
    ("read:n5-verbos-06-01", "Estou em casa", "I am at home"),
    ("read:n4-aspecto-01-01", "Quando começar, quando voltar", "When to start, when to come back"),
    ("read:n4-aspecto-02-01", "Lá fora vai clareando", "It is getting brighter outside"),
    ("read:n4-aspecto-03-01", "Lá vai o ônibus", "There goes the bus"),
    ("read:n4-aspecto-04-01", "Vou tentar mais uma vez", "I will try one more time"),
    ("read:n4-aspecto-05-01", "Acabei de chegar agora", "I just got here"),
    ("read:n4-aspecto-06-01", "Meu pai voltou do exterior", "My father is back from abroad"),
    ("read:n4-aspecto-07-01", "Fácil de ler, difícil de responder", "Easy to read, hard to answer"),
    ("read:n4-causativa-01-01", "O plano do meu pai", "My father's plan for me"),
    ("read:n4-causativa-02-01", "Um tempo para pensar", "Time to think it over"),
    ("read:n4-causativa-03-01", "Conselhos antes da chuva", "Advice before the rain"),
    ("read:n4-condicionais-01-01", "Qual violão é o seu", "Which guitar is yours"),
    ("read:n4-condicionais-02-01", "Que tal parar de fumar", "Why not quit smoking"),
    ("read:n4-condicionais-03-01", "Quero ser um adulto admirável", "I want to become a fine adult"),
    ("read:n4-condicionais-04-01", "Você devia ter ligado", "You should have called"),
    ("read:n4-condicionais-05-01", "Tomara que a gente se veja", "Hope we can meet again"),
    ("read:n4-condicionais-06-01", "Basta escrever o nome", "Just write your name"),
    ("read:n4-condicionais-07-01", "Onde fica o terminal sul", "Where is the south terminal"),
    ("read:n4-condicionais-08-01", "Perguntei como se faz", "I asked how it is made"),
    ("read:n4-conectores-01-01", "Primeiro, vamos comer", "Let us eat first"),
    ("read:n4-conectores-02-01", "Quero voltar nesta cafeteria", "I want to come back to this café"),
    ("read:n4-conectores-03-01", "Por exemplo, este kanji", "For example, this kanji"),
    ("read:n4-conectores-04-01", "Do outono para o inverno", "From autumn into winter"),
    ("read:n4-conectores-05-01", "Mesmo assim, há riscos", "Even so, there are risks"),
    ("read:n4-conectores-06-01", "O tempo continuou ruim", "The weather stayed bad"),
    ("read:n4-conectores-07-01", "O trabalho de hoje acabou", "Today's work is done"),
    ("read:n4-dar-receber-01-01", "Vou dar uma bronca nele", "I will give him a scolding"),
    ("read:n4-dar-receber-02-01", "Liga a TV pra mim", "Turn on the TV for me"),
    ("read:n4-dar-receber-03-01", "Quero que você veja este vídeo", "I want you to watch this video"),
    ("read:n4-dar-receber-04-01", "Obrigado por me escutar", "Thank you for listening"),
    ("read:n4-experiencia-01-01", "Você poderia acender a luz", "Could you turn on the light"),
    ("read:n4-experiencia-02-01", "Aos poucos, vou lembrando", "Little by little, it comes back"),
    ("read:n4-experiencia-03-01", "Que bom te encontrar aqui", "Glad to see you here"),
    ("read:n4-experiencia-04-01", "O vinho vem da uva", "Wine comes from grapes"),
    ("read:n4-experiencia-05-01", "Um ônibus a cada 15 minutos", "A bus every fifteen minutes"),
    ("read:n4-experiencia-06-01", "Amigos desde então", "Friends ever since"),
    ("read:n4-forma-simples-01-01", "Como seria bom ter um carro", "How nice to have a car"),
    ("read:n4-forma-simples-02-01", "Menino ou menina", "A boy or a girl"),
    ("read:n4-forma-simples-03-01", "Só resta um dia", "Only one day left"),
    ("read:n4-forma-simples-04-01", "Por volta das dez", "Around ten o'clock"),
    ("read:n4-forma-simples-05-01", "Fresco para julho", "Cool for July"),
    ("read:n4-forma-simples-06-01", "Um banco debaixo da árvore", "A bench under the tree"),
    ("read:n4-forma-simples-07-01", "Meu pai saiu agorinha", "My father went out just now"),
    ("read:n4-keigo-01-01", "Cumprimentos e um prato especial", "Greetings and a special dish"),
    ("read:n4-keigo-02-01", "Conversar tomando um chá", "Talking over a cup of tea"),
    ("read:n4-keigo-03-01", "Deixe os livros como estão", "Leave the books as they are"),
    ("read:n4-keigo-04-01", "A que horas o senhor sai", "What time will you be leaving"),
    ("read:n4-keigo-05-01", "Aviso antes do café da manhã", "A notice before breakfast"),
    ("read:n4-keigo-06-01", "Espere na linha, por favor", "Please hold the line"),
    ("read:n4-obrigacao-01-01", "Quando os olhos falam", "When the eyes do the talking"),
    ("read:n4-obrigacao-02-01", "O pai vai ficar bem", "Dad will be fine"),
    ("read:n4-obrigacao-03-01", "Doente, mas sempre alegre", "Sick but always cheerful"),
    ("read:n4-obrigacao-04-01", "Acordar cedo e chegar às sete", "Up early, there by seven"),
    ("read:n4-obrigacao-05-01", "Melhor ter começado mais cedo", "Should have started sooner"),
    ("read:n4-oracoes-relativas-01-01", "A gripe e a chuva forte", "The flu and the heavy rain"),
    ("read:n4-oracoes-relativas-02-01", "Foi treze ou trinta", "Was that thirteen or thirty"),
    ("read:n4-oracoes-relativas-03-01", "Faço isso por conta própria", "I'll handle it myself"),
    ("read:n4-oracoes-relativas-04-01", "A gente conversa depois", "We'll talk later"),
    ("read:n4-oracoes-relativas-05-01", "A vida é assim mesmo", "That's just how life goes"),
    ("read:n4-oracoes-relativas-06-01", "Eu não devia ter falado", "I should have kept quiet"),
    ("read:n4-oracoes-relativas-07-01", "Não zombe das pessoas", "Don't make fun of people"),
    ("read:n4-passiva-01-01", "Flores cortadas murcham logo", "Cut flowers wilt fast"),
    ("read:n4-passiva-02-01", "Quem inventou o telefone", "Who invented the telephone"),
    ("read:n4-passiva-03-01", "Vou contar uma história", "Let me tell you a story"),
    ("read:n4-passiva-04-01", "Nada que a loja não venda", "Nothing that shop doesn't sell"),
    ("read:n4-potencial-01-01", "Até criança lê este livro", "Even a child can read it"),
    ("read:n4-potencial-02-01", "Não leia enquanto come", "Don't read while you eat"),
    ("read:n4-potencial-03-01", "Dá pra ouvir tudo perfeitamente", "I can hear it all clearly"),
    ("read:n4-potencial-04-01", "Um livro é como um amigo", "A book is like a friend"),
    ("read:n4-revisao-01-01", "Contar ou não para a mãe", "Whether to tell mom"),
    ("read:n4-revisao-02-01", "Quando nos vemos de novo", "When can we meet again"),
    ("read:n4-revisao-03-01", "A escola fica a dez minutos", "A ten minute walk to school"),
    ("read:n4-suposicao-01-01", "Ouvi falar daquele lámen", "Word about that ramen shop"),
    ("read:n4-suposicao-02-01", "Parece que vem chuva à noite", "Looks like rain tonight"),
    ("read:n4-suposicao-03-01", "Quero ser igual a você", "I want to be like you"),
    ("read:n4-suposicao-04-01", "Será que dá um descontinho", "Any chance of a discount"),
    ("read:n4-suposicao-05-01", "Tem cinema aqui perto", "Any movie theater nearby"),
    ("read:n4-suposicao-06-01", "O mar visto lá do alto", "The sea from the mountaintop"),
    ("read:n4-suposicao-07-01", "É só você aparecer", "I just want you to come"),
    ("read:n4-suposicao-08-01", "O ônibus deve chegar logo", "The bus should be along soon"),
    ("read:n4-transitividade-01-01", "Eu abri a porta", "I opened the door"),
    ("read:n4-transitividade-02-01", "Sentados perto do fogo", "Sitting by the fire"),
    ("read:n4-transitividade-03-01", "Finalmente parei de fumar", "I finally quit smoking"),
    ("read:n4-transitividade-04-01", "Telefono amanhã de manhã", "A call tomorrow morning"),
    ("read:n4-transitividade-05-01", "Tem um gambá na varanda", "A skunk on the porch"),
    ("read:n4-volitivo-01-01", "Vamos parar por hoje", "Let's call it a day"),
    ("read:n4-volitivo-02-01", "O Ano-Novo está logo aí", "New Year's just around the corner"),
    ("read:n4-volitivo-03-01", "Não conheço bem esta região", "I'm new around here"),
    ("read:n4-volitivo-04-01", "São duas coisas diferentes", "Two different things"),
    ("read:n4-volitivo-05-01", "Só dando uma olhada", "Just looking around"),
    ("read:n4-volitivo-06-01", "Abra os olhos e levante", "Open your eyes and stand up"),
    ("read:n4-volitivo-07-01", "Falar japonês sempre que der", "Speaking Japanese whenever I can"),
    ("read:n3-causa-01-01", "A árvore me salvou da chuva", "The tree saved me from the rain"),
    ("read:n3-causa-02-01", "A gravidade dá peso às coisas", "Gravity gives things their weight"),
    ("read:n3-causa-03-01", "Como se chama esse rio", "What is this river called"),
    ("read:n3-causa-04-01", "A gente ia muito ao cinema", "We used to go to the movies"),
    ("read:n3-causa-05-01", "Qual gravata você vai escolher", "Which tie will you pick"),
    ("read:n3-causa-05-02", "O problema é falta de dinheiro", "The problem is a money shortage"),
    ("read:n3-causa-06-01", "Até quando o senhor fica aqui", "How long are you staying"),
    ("read:n3-causa-06-02", "Um bom lugar para jantar", "A good place for dinner"),
    ("read:n3-causa-07-01", "Em caso de incêndio, ligue 119", "In case of fire, call 119"),
    ("read:n3-causa-07-02", "Onde eu deixo a bandeja", "Where do I leave the tray"),
    ("read:n3-causa-08-01", "Preciso saber até amanhã", "I need to know by tomorrow"),
    ("read:n3-causa-08-02", "Faz quanto tempo o ônibus saiu", "How long ago the bus left"),
    ("read:n3-concessao-01-01", "No mínimo trinta mil ienes", "Thirty thousand yen at the least"),
    ("read:n3-concessao-02-01", "Trabalhei domingo, folguei hoje", "Worked Sunday, off today"),
    ("read:n3-concessao-03-01", "Mais amigo do que professor", "More a friend than a teacher"),
    ("read:n3-concessao-04-01", "Jovem para a idade que tem", "Young for her age"),
    ("read:n3-concessao-05-01", "Ouvi meus pais cochichando", "I heard my parents whispering"),
    ("read:n3-concessao-05-02", "O bebê nasceu no caminho", "The baby was born on the way"),
    ("read:n3-concessao-06-01", "De quem é esse dicionário", "Whose dictionary is this"),
    ("read:n3-concessao-06-02", "Neste país, camelo é essencial", "In this country, camels are essential"),
    ("read:n3-concessao-07-01", "Quatro mil línguas no mundo", "Four thousand languages in the world"),
    ("read:n3-concessao-07-02", "Aperte o botão, a porta abre", "Press the button, the door opens"),
    ("read:n3-conectores-01-01", "A pé ou de carro", "On foot or by car"),
    ("read:n3-conectores-02-01", "Me mandaram folgar hoje", "They told me to take today off"),
    ("read:n3-conectores-03-01", "Essa rua está em obras", "That street is under construction"),
    ("read:n3-conectores-04-01", "Planejar e executar são coisas diferentes", "Planning and doing are different things"),
    ("read:n3-conectores-05-01", "Que altura tem o Mont Blanc", "How tall is Mont Blanc"),
    ("read:n3-conectores-05-02", "Meu pai parte na quinta", "My father leaves on Thursday"),
    ("read:n3-conectores-06-01", "Me manda o mapa por fax", "Send me the map by fax"),
    ("read:n3-conectores-06-02", "A gasolina está quase acabando", "The gas is almost out"),
    ("read:n3-conectores-07-01", "Nenhum dos jogos era divertido", "None of the games were fun"),
    ("read:n3-conectores-07-02", "Comer antes de sair", "Eat before going out"),
    ("read:n3-conectores-08-01", "Que tal molho inglês", "How about Worcestershire sauce"),
    ("read:n3-conectores-08-02", "As duas estradas se cruzam ali", "The two roads cross there"),
    ("read:n3-conjectura-01-01", "Será que o tempo aguenta", "Will the weather hold"),
    ("read:n3-conjectura-02-01", "Eu não nasci ontem", "I was not born yesterday"),
    ("read:n3-conjectura-03-01", "Lá fora parece verão", "It feels like summer outside"),
    ("read:n3-conjectura-04-01", "Fingindo que estou pensando", "Pretending to think"),
    ("read:n3-conjectura-05-01", "Pássaros voando para o sul", "Birds flying south"),
    ("read:n3-conjectura-05-02", "Está frio, abotoe o casaco", "It is cold, button your coat"),
    ("read:n3-conjectura-06-01", "O sapato aperta, o pé inchou", "Tight shoes, swollen feet"),
    ("read:n3-conjectura-06-02", "Eu ia estudar medicina lá fora", "I was going to study medicine abroad"),
    ("read:n3-conjectura-07-01", "Esqui é meu esporte favorito", "Skiing is my favorite sport"),
    ("read:n3-conjectura-07-02", "O preço da gasolina só sobe", "Gas prices keep going up"),
    ("read:n3-desejos-01-01", "Tomara que você melhore logo", "I hope you get better soon"),
    ("read:n3-desejos-02-01", "Se eu renascesse, seria pássaro", "If I were reborn, a bird"),
    ("read:n3-desejos-03-01", "Começar pelo visual", "Starting with the look"),
    ("read:n3-desejos-04-01", "Eu devia ter continuado o balé", "I should have kept up ballet"),
    ("read:n3-desejos-05-01", "Pra ser instantâneo, é bom", "Not bad for instant food"),
    ("read:n3-desejos-05-02", "Sessenta pontos para passar", "Sixty points to pass"),
    ("read:n3-desejos-06-01", "Vou ganhar essa partida de tênis", "I will win this tennis match"),
    ("read:n3-desejos-06-02", "Não posso te ver hoje", "I can't see you tonight"),
    ("read:n3-desejos-07-01", "Dinheiro guardado para o verão", "Money saved for summer"),
    ("read:n3-desejos-07-02", "A bicicleta de cinquenta mil ienes", "The fifty-thousand-yen bicycle"),
    ("read:n3-deveres-01-01", "Dá uma olhada no mapa", "Take a look at the map"),
    ("read:n3-deveres-02-01", "O que eu devia ter feito", "What I should have done"),
    ("read:n3-deveres-03-01", "Nunca é tarde para aprender", "Never too old to learn"),
    ("read:n3-deveres-04-01", "Procure o motorista de ontem", "Find yesterday's driver"),
    ("read:n3-deveres-05-01", "Minha mãe e o meio período", "My mother and the part-time job"),
    ("read:n3-deveres-05-02", "Sábado não, domingo", "Not Saturday, Sunday"),
    ("read:n3-deveres-06-01", "Uns ganham, outros perdem", "Some win, some lose"),
    ("read:n3-deveres-06-02", "Um menino nasceu no mês passado", "A boy born last month"),
    ("read:n3-enfase-01-01", "Agora é a hora de agir", "Now is the time to act"),
    ("read:n3-enfase-02-01", "Ele deu roupas e ainda dinheiro", "He gave clothes and money too"),
    ("read:n3-enfase-03-01", "Nem gentil, nem estudioso", "Neither kind nor scholarly"),
    ("read:n3-enfase-04-01", "A oportunidade raramente bate duas vezes", "Opportunity seldom knocks twice"),
    ("read:n3-enfase-05-01", "Andar a cavalo com a Vera", "Horseback riding with Vera"),
    ("read:n3-enfase-05-02", "Devolver o livro até terça", "The book due on Tuesday"),
    ("read:n3-enfase-06-01", "O carro quebrou no caminho", "The car broke down"),
    ("read:n3-enfase-06-02", "Alergia a poeira doméstica", "Allergic to house dust"),
    ("read:n3-enfase-07-01", "Mal saí de casa e choveu", "It rained the moment I left"),
    ("read:n3-enfase-07-02", "Bill levou o irmão ao zoológico", "Taking his brother to the zoo"),
    ("read:n3-estado-01-01", "Almoço pronto todos os dias", "Lunch made every day"),
    ("read:n3-estado-02-01", "Não precisa terminar até amanhã", "No need to finish by tomorrow"),
    ("read:n3-estado-03-01", "Saí com o aquecedor ligado", "I left the heater on"),
    ("read:n3-estado-04-01", "Porta aberta, água correndo", "Door open, water running"),
    ("read:n3-estado-04-02", "Você deixou a luz acesa", "You left the lights on"),
    ("read:n3-estado-05-01", "Piloto, igual ao meu pai", "A pilot, like my father"),
    ("read:n3-estado-05-02", "Aquele lugar tem uma história", "That place has a story"),
    ("read:n3-estado-06-01", "Não pode ser diamante de verdade", "That can't be a real diamond"),
    ("read:n3-estado-06-02", "A porta que se abriu sozinha", "The door that opened by itself"),
    ("read:n3-estado-07-01", "Meu pai ensina inglês", "My father teaches English"),
    ("read:n3-estado-07-02", "A escola começa às 8h10", "School starts at 8:10"),
    ("read:n3-estado-08-01", "Uma coisa de cada vez", "One thing at a time"),
    ("read:n3-estado-08-02", "A televisão disse que vai chover", "The TV says it will rain"),
    ("read:n3-estrutura-01-01", "Um dia você vai me esquecer", "Someday you'll forget about me"),
    ("read:n3-estrutura-02-01", "Coisas demais na cabeça", "Too much on my mind"),
    ("read:n3-estrutura-03-01", "Confundido com o próprio irmão", "Mistaken for his own brother"),
    ("read:n3-estrutura-04-01", "Escalo montanhas porque elas estão lá", "I climb mountains because they're there"),
    ("read:n3-estrutura-04-02", "Segura firme, senão você cai", "Hold tight or you'll fall"),
    ("read:n3-estrutura-05-01", "Uma hora de matemática e sono", "An hour of math and sleepiness"),
    ("read:n3-estrutura-05-02", "Escuro aí, claro aqui", "Dark there, still light here"),
    ("read:n3-estrutura-06-01", "No verão nadávamos naquele rio", "Summers swimming in the river"),
    ("read:n3-estrutura-06-02", "Um presente para a minha esposa", "A gift for my wife"),
    ("read:n3-intencao-01-01", "Escrever com a mão esquerda", "Writing with the left hand"),
    ("read:n3-intencao-02-01", "Encontro marcado para as sete", "The meeting set for seven"),
    ("read:n3-intencao-03-01", "Fale mais alto, por favor", "Please speak a little louder"),
    ("read:n3-intencao-04-01", "A criança finalmente aprendeu a andar", "The child finally learned to walk"),
    ("read:n3-intencao-04-02", "Uma música da época da escola", "A song from my school days"),
    ("read:n3-intencao-05-01", "Aonde todo mundo vai tão cedo", "Where's everyone going so early"),
    ("read:n3-intencao-05-02", "Tenha confiança, você consegue", "Have confidence, you can do it"),
    ("read:n3-intencao-06-01", "Olha quanta manga naquela árvore", "Look at all those mangoes"),
    ("read:n3-intencao-06-02", "Escrever melhor, sete horas, sem dinheiro", "Write better, seven o'clock, no money"),
    ("read:n3-intencao-07-01", "Pão, saias longas e um passeio", "Bread, skirts and a bus tour"),
    ("read:n3-intencao-07-02", "Esperando as férias de verão", "Waiting for summer vacation"),
    ("read:n3-limites-01-01", "Quanto tempo ainda falta", "How much longer it takes"),
    ("read:n3-limites-02-01", "Só isso e nada mais", "Only this and nothing more"),
    ("read:n3-limites-03-01", "Nada mais divertido que viajar", "Nothing more fun than traveling"),
    ("read:n3-limites-04-01", "O quanto eu te amo", "How much I love you"),
    ("read:n3-limites-04-02", "Maior nem sempre é melhor", "Bigger is not always better"),
    ("read:n3-limites-05-01", "Uma professora e outra chance", "A teacher and another chance"),
    ("read:n3-limites-05-02", "Do som alto ao céu azul", "From loud stereo to blue sky"),
    ("read:n3-limites-06-01", "Sem TV e sem sono", "No TV and no sleep"),
    ("read:n3-limites-06-02", "Comida, dinheiro e nove horas", "Food, money and nine o'clock"),
    ("read:n3-limites-07-01", "Se chover, o jogo não sai", "If it rains, no match"),
    ("read:n3-limites-07-02", "Que tal dar uma festa", "How about throwing a party"),
    ("read:n3-perspectiva-01-01", "Sobre árvores e sobre gente", "About trees and about people"),
    ("read:n3-perspectiva-02-01", "Segundo o jornal, vem tufão", "A typhoon, says the paper"),
    ("read:n3-perspectiva-03-01", "Só o tique-taque do relógio", "Only the ticking of the clock"),
    ("read:n3-perspectiva-04-01", "Roupa folgada e lentes de contato", "Loose clothes and contact lenses"),
    ("read:n3-perspectiva-04-02", "A árvore que ficava sozinha", "The tree that was often alone"),
    ("read:n3-perspectiva-05-01", "O senhor da quitanda", "The man at the greengrocer's"),
    ("read:n3-perspectiva-05-02", "Pimentões, camisa preta e horários", "Peppers, black shirt, opening hours"),
    ("read:n3-perspectiva-06-01", "Uma passadinha na loja", "A quick stop at the shop"),
    ("read:n3-perspectiva-06-02", "Ah, minha calça branca nova", "Oh, my new white pants"),
    ("read:n3-perspectiva-07-01", "Rosas, lírios e outras flores", "Roses, lilies and other flowers"),
    ("read:n3-perspectiva-07-02", "Você devia ter me escutado", "You should have listened to me"),
    ("read:n3-relato-01-01", "Se for para escolher, carne", "Beef, if I had to choose"),
    ("read:n3-relato-02-01", "O dicionário e o tufão", "The dictionary and the typhoon"),
    ("read:n3-relato-03-01", "Soube que você comprou casa", "I heard you bought a house"),
    ("read:n3-relato-04-01", "Cantora famosa, médico ruim", "Famous singer, bad doctor"),
    ("read:n3-relato-04-02", "Será que já tomei o remédio", "Did I take my medicine"),
    ("read:n3-relato-05-01", "Lavando o carro desde cedo", "Washing the car since morning"),
    ("read:n3-relato-05-02", "Sem gasolina no meio do caminho", "Out of gas halfway there"),
    ("read:n3-relato-06-01", "Esqueci de pôr filme na câmera", "Forgot to load the camera"),
    ("read:n3-relato-06-02", "A febre subiu num instante", "The fever spiked in an instant"),
    ("read:n3-relato-07-01", "É a primeira vez que fumo", "My first time smoking"),
    ("read:n3-relato-07-02", "Fugi do incêndio sem nada", "I fled the fire with nothing"),
    ("read:n3-revisao-01-01", "Ninguém sabe tudo neste mundo", "Nobody knows everything in this world"),
    ("read:n3-tempo-01-01", "Ficar até os fogos de artifício", "Staying for the fireworks"),
    ("read:n3-tempo-02-01", "Já que você vai, aproveita", "While you're out there"),
    ("read:n3-tempo-03-01", "O ônibus acabou de sair", "The bus has just left"),
    ("read:n3-tempo-04-01", "Carta de amor em inglês", "A love letter in English"),
    ("read:n3-tempo-04-02", "Convite para o cinema", "An invitation to the movies"),
    ("read:n3-tempo-05-01", "Meu tio está hospedado em casa", "My uncle is staying with us"),
    ("read:n3-tempo-05-02", "Cachorro que come peixe cru", "A dog that eats raw fish"),
    ("read:n3-tempo-06-01", "Não dê comida aos animais", "Don't feed the animals"),
    ("read:n3-tempo-06-02", "Planeje antes de começar", "Plan before you begin"),
    ("read:n3-tempo-07-01", "Correr até enxergar a luz", "Running until a light appears"),
    ("read:n3-tempo-07-02", "Eu detesto cenoura", "I really hate carrots"),
    ("read:n3-tempo-08-01", "Perdido nesta cidade", "Lost in this town"),
    ("read:n3-tempo-08-02", "Falta uma semana para as férias", "One week until summer vacation"),
)


def is_placeholder(value: str | None) -> bool:
    """True when the column holds nothing a learner could read as a title."""
    return value is None or not value.strip() or value.strip() in PLACEHOLDER


def lint(rows: tuple[tuple[str, str, str], ...]) -> list[str]:
    """House-style guards on the authored titles themselves, checked before touching the DB."""
    problems: list[str] = []
    seen: dict[str, str] = {}
    for slug, pt, en in rows:
        for lang, value in (("pt", pt), ("en", en)):
            label = f"{slug}.title_{lang}"
            if not value.strip():
                problems.append(f"{label}: empty")
            if value != value.strip():
                problems.append(f"{label}: leading/trailing whitespace")
            if value.endswith("."):
                problems.append(f"{label}: terminal period")
            if "—" in value or "–" in value:
                problems.append(f"{label}: dash (design/translation_style.md forbids it)")
            if value.strip() in PLACEHOLDER:
                problems.append(f"{label}: still the placeholder")
        if len(pt.split()) > 7:
            problems.append(f"{slug}.title_pt: {len(pt.split())} words — titles are 2-6")
        if pt in seen:
            problems.append(f"{slug}.title_pt duplicates {seen[pt]}: {pt!r}")
        seen[pt] = slug
    return problems


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true", help="report what would change; write nothing")
    args = ap.parse_args()

    problems = lint(TITLES)
    if problems:
        print("authored titles fail the style guards — nothing written:")
        for p in problems:
            print(f"  ! {p}")
        return 2

    con = sqlite3.connect(DB)
    con.execute("PRAGMA busy_timeout=60000")
    current = {slug: (pt, en) for slug, pt, en in
               con.execute("SELECT slug, title_pt, title_en FROM reading")}

    skipped: list[str] = []
    # slug -> (columns to write, intended pt, intended en); only boxes we may legally touch.
    planned: dict[str, tuple[list[str], str, str]] = {}

    for slug, pt, en in TITLES:
        if slug not in current:
            skipped.append(f"{slug}: no such reading row")
            continue
        cur_pt, cur_en = current[slug]
        cols: list[str] = []
        for col, cur, want in (("title_pt", cur_pt, pt), ("title_en", cur_en, en)):
            if (cur or "") == want:
                continue                                   # already carries this exact title
            if is_placeholder(cur):
                cols.append(col)
            else:
                skipped.append(f"{slug}.{col}: already carries a real title — not touching it\n"
                               f"      keeping:  {cur}\n      not applying: {want}")
        # The two columns are judged independently, so a box whose pt title was authored elsewhere but
        # whose en title is still `Reading` gets the en half filled and the pt half left alone.
        if cols:
            planned[slug] = (cols, pt, en)

    # -- cross-batch duplicate check over the PROJECTED final state of all 286 titles --
    final_pt: dict[str, str] = {}
    for slug, (cur_pt, _cur_en) in current.items():
        final_pt[slug] = cur_pt or ""
    intended_pt = {slug: pt for slug, (cols, pt, _en) in planned.items() if "title_pt" in cols}
    final_pt.update(intended_pt)

    owner: dict[str, str] = {}
    order = [slug for slug, _pt, _en in TITLES] + [s for s in sorted(current) if
                                                   s not in {t[0] for t in TITLES}]
    for slug in order:
        value = final_pt.get(slug, "")
        if not value or value in PLACEHOLDER:
            continue
        if value in owner:
            first = owner[value]
            if slug in intended_pt:
                # We are the later one. Hold BOTH halves back, not just the pt: the two titles are one
                # authored pair, re-qualifying the passage will rewrite both, and a box left with a real
                # en title over a placeholder pt one reads as a bug rather than as pending work.
                del planned[slug]
                skipped.append(f"{slug}: title_pt would duplicate {first} ({value!r}) — box left "
                               f"untitled; re-qualify it from its own passage")
            else:
                skipped.append(f"{slug}.title_pt duplicates {first} ({value!r}) — pre-existing, "
                               f"neither box was touched")
            continue
        owner[value] = slug

    changed = 0
    for slug in [s for s, _pt, _en in TITLES if s in planned]:
        cols, pt, en = planned[slug]
        values = {"title_pt": pt, "title_en": en}
        for col in cols:
            print(f"  {slug}.{col} <- {values[col]}")
            if not args.check:
                con.execute(f"UPDATE reading SET {col}=? WHERE slug=?", (values[col], slug))
            changed += 1

    if not args.check:
        con.commit()
    con.close()

    verb = "would title" if args.check else "titled"
    print(f"\n{verb} {changed} field(s) across {len(planned)} box(es); "
          f"{len(TITLES)} titles offered, {len(current)} reading rows in the DB")
    for s in skipped:
        print(f"  ! {s}")
    return 1 if (args.check and changed) else (2 if skipped else 0)


if __name__ == "__main__":
    sys.exit(main())
