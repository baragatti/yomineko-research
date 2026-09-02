#!/usr/bin/env python3
"""Repair the per-record gloss defects found by the n5/n4 vocab QA sweep.

Source finding list: `research/reports/qa_sweep/vocab_glosses.md` (19 findings over 1,358 records /
1,947 senses). Every fix below was re-judged against
`research/datasets/jmdict/jmdict-eng-3.6.2+20260608153333.json.zip` and against the record itself before
being written here; where my reading differs from the report's proposed wording the `why` says so.

WHAT THIS SCRIPT DOES NOT DO
  * **F1 — 22 records whose slug points at the wrong JMdict entry.** `vocab:<jmdict_id>` is the published
    address, so re-pointing is a migration across 1,415 `sentence_vocab` links, 766 `token` links and
    5,955 slug occurrences in the committed exports. Documented, with evidence and reference counts, in
    `research/reports/qa_sweep/vocab_identity_queue.md`. Not applied.
  * **F3 / F10 (`headword`), F4 / F5 (`misc_tags` → `register`), F6 (`forms` tags), F9 (romaji).** Each is a
    schema, exporter or convention change rather than a record edit — `headword` is itself an address
    (`lesson_unlocks.ref` is `vocab:<headword>`), `register` is derived from `misc_tags` at export time, and
    the romaji scheme for ー and word-final っ lives in a shared `kana2romaji`. Reasons are recorded in the
    same queue file. Not applied.
  * Level tags (`level`, `level_confidence`, `level_agreement`) — owner decision on the confidence formula.

STORAGE. `db/corpus.sqlite` only, and only three tables:
  * `vocab_sense.gloss_en` / `gloss_pt` (JSON arrays),
  * `localized_text` (`entity_type='vocab_sense'`, `field='gloss'`, `locale='pt-BR'`) which mirrors
    `gloss_pt` byte for byte — the exporter reads the localized row, so both must move together,
  * `vocab.adj_class` (one record).
Exporters are NOT run here; re-run `scripts/export/export_corpus.py` afterwards so the JSON/MD under
`corpus/` catches up (project rule: canonical data is the committed JSON, the SQLite file is an index).

IDEMPOTENT. Every edit names the exact current value. A value that already equals the target is a silent
no-op; a value that matches neither is a LOUD SKIP and is left alone, because a mismatch means something
else moved and this script no longer knows what it is looking at.
Usage: apply_vocab_gloss_repairs.py [--check]
"""
from __future__ import annotations

import argparse
import json
import sqlite3
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
# W01: honour --db / $YOMINEKO_DB so a rebuild can target a scratch DB (scripts/dbtarget.py).
import sys as _sys, pathlib as _pl  # noqa: E402
_sys.path.append(str(next(p for p in _pl.Path(__file__).resolve().parents if p.name == "scripts")))
from dbtarget import db_target  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
DB = db_target(ROOT / "db" / "corpus.sqlite")

Gloss = list[str]

# ---------------------------------------------------------------------------------------------------
# Gloss rewrites: (vocab_id, sense_order, locale, exact current list, corrected list, why)
# locale "en" -> vocab_sense.gloss_en (Layer A paraphrase); "pt" -> gloss_pt + its localized_text row.
# ---------------------------------------------------------------------------------------------------
GLOSS_FIXES: list[tuple[int, int, str, Gloss, Gloss, str]] = [
    # -- F2 (critical): あれ. JMdict 1000580 orders sense 0 "that / that thing", sense 1 "that person".
    (
        41, 0, "en",
        ["that person (distant from both speaker and listener)", "that"],
        ["that", "that thing"],
        "The record merged JMdict sense 1 ('that person') with sense 0's *info* note and dropped sense 0's "
        "own gloss, so the thing-reading vanished. Restore sense 0; the person reading returns as s1.",
    ),
    (
        41, 0, "pt",
        ["aquela pessoa", "aquele (pessoa distante de ambos)"],
        ["aquilo", "aquele (ali)"],
        "No gloss anywhere in the record meant 'aquilo', so a learner drilling これ/それ/あれ was taught that "
        "あれ refers to a person. 261 これ reads 'isto | este' and 358 それ 'isso | esse'; あれ now completes "
        "the row instead of breaking it.",
    ),
    # -- F7 (medium): JMdict's passive phrasing for が-marked adjectives, translated straight into pt-BR.
    (
        203, 0, "pt",
        ["detestado", "que se detesta", "desagradável"],
        ["não gostar de", "detestável", "desagradável"],
        "野菜が嫌いです is 'não gosto de verdura', not 'verdura é detestada'. 'disliked' is a lexicographer's "
        "device for describing a が-adjective in English; carried into pt-BR it inverts the argument "
        "structure the learner has to produce. The file already has the right treatment next door: "
        "322 好き renders the same construction as 'gostar de', so 嫌い mirrors it as 'não gostar de'.",
    ),
    (
        586, 0, "pt",
        ["desejado", "que se quer (ter)"],
        ["querer (ter)", "desejar"],
        "Same defect: 水が欲しい is 'quero água', not 'água é desejada'. JMdict's own sense 0 is "
        "'wanting (to have) / desiring', i.e. active. s1 'querer que (alguém faça)' is already correct and "
        "is left alone.",
    ),
    # -- F8 (medium): どの and どれ carried byte-identical pt, erasing the distinction they exist to teach.
    (
        451, 0, "pt",
        ["qual (entre vários)"],
        ["qual (+ substantivo)", "que (livro, pessoa etc.)"],
        "どの is prenominal (adj-pn in both JMdict and the record's own pos): どの本 = 'qual livro'. The gloss "
        "has to show that it takes a noun, or it is indistinguishable from どれ.",
    ),
    (
        460, 0, "pt",
        ["qual (entre vários)"],
        ["qual deles", "qual (entre vários)"],
        "どれ is a pronoun (pn): どれですか = 'qual deles?'. Leading with 'qual deles' separates the card from "
        "451 どの while keeping the old string as the second gloss. この/これ and その/それ are already "
        "distinguished correctly in the same file, so this was an isolated slip.",
    ),
    # -- F12 (low): 11 records repeated an identical pt string across two senses, defeating the split.
    (
        347, 0, "pt",
        ["lavar roupa", "lavagem de roupa"],
        ["lavagem de roupa", "ato de lavar roupa"],
        "s0 is the noun sense and s1 the する reading; both led with the verb 'lavar roupa', so the split "
        "carried no information. s0 is now nominal only and s1 keeps 'lavar roupa | fazer a lavagem'.",
    ),
    (
        649, 0, "pt",
        ["descanso", "folga", "pausa"],
        ["descanso", "pausa", "intervalo"],
        "'folga' was doing duty in both senses. It belongs to s1 (holiday / day off); s0 is 'rest | break | "
        "time off', which 'intervalo' renders without colliding.",
    ),
    (
        869, 1, "pt",
        ["dormir demais", "perder a hora"],
        ["perder a hora", "dormir além da hora"],
        "s0 (noun) and s1 (する verb) both led with 'dormir demais'. 'perder a hora' is exactly what 寝坊する "
        "means in pt-BR and gives the verbal sense its own leading gloss.",
    ),
    (
        630, 1, "pt",
        ["a outra parte", "o outro lado"],
        ["a outra parte", "o adversário"],
        "'o outro lado' is s0's leading gloss (the physical far side). s1 is JMdict's 'the other party / the "
        "opponent', which 'o adversário' carries without reusing s0's string.",
    ),
    (
        556, 1, "pt",
        ["amplo", "abrangente"],
        ["abrangente", "extenso"],
        "'amplo' is s0's leading gloss (spacious). s1 is the figurative 'broad | extensive'.",
    ),
    (
        230, 0, "pt",
        ["apagar", "desligar"],
        ["desligar", "apagar (luz, fogo)"],
        "pt 'apagar' genuinely covers both senses of 消す, which is why it appeared twice unqualified. "
        "Keeping it in both but disambiguated preserves the truth and still tells the two cards apart.",
    ),
    (
        230, 1, "pt",
        ["apagar", "deletar"],
        ["apagar (o que está escrito)", "deletar"],
        "Other half of the same fix: s1 is JMdict sense 0, 'to erase | to delete | to rub out'.",
    ),
    (
        177, 1, "en",
        ["slight, mild, casual"],
        ["slight", "mild", "casual"],
        "Comma-joined en (F11) on the same sense F12 flags; split here rather than in the bulk block so the "
        "record is repaired in one place.",
    ),
    (
        177, 1, "pt",
        ["leve", "ligeiro", "superficial"],
        ["ligeiro", "superficial", "descontraído"],
        "'leve' is s0, the physical weight sense, and is the only gloss s0 has. s1 is the figurative "
        "'slight | mild | casual'; 'descontraído' renders 'casual', which had no pt gloss at all.",
    ),
    (
        620, 1, "pt",
        ["caminho", "via"],
        ["via", "rumo (de ação)"],
        "'caminho' is s0 (road | street | path). s1 is 'way | course (of action)', where 'rumo (de ação)' "
        "carries the abstract reading that the duplicate was hiding.",
    ),
    (
        839, 1, "pt",
        ["envergonhado", "sem graça"],
        ["tímido", "sem graça"],
        "'envergonhado' is already s0's third gloss. s1 is 'shy | self-conscious' — a disposition, not a "
        "reaction — and pt-BR marks that difference with 'tímido'.",
    ),
    (
        784, 0, "pt",
        ["fundo", "profundo"],
        ["fundo", "profundo (água, buraco)"],
        "'profundo' sat unqualified in both senses. s0 is physical depth (JMdict sense 0 'deep').",
    ),
    (
        784, 1, "pt",
        ["profundo", "intenso"],
        ["profundo (sentimento, sono)", "intenso"],
        "Other half: s1 is JMdict 'profound' plus the intensity reading, so the same pt word is kept but "
        "scoped to the abstract use.",
    ),
    (
        1103, 1, "pt",
        ["longe", "ao longe"],
        ["ao longe", "à distância"],
        "'longe' is s0's leading gloss (the noun, 'far away | faraway place'). s1 is adverbial 'in the "
        "distance', which 'ao longe | à distância' covers on its own.",
    ),
    # -- F14 (low): pt glosses that add or drop meaning relative to their own en.
    (
        1011, 0, "pt",
        ["dança", "dança (tradicional)"],
        ["dança", "o ato de dançar"],
        "JMdict 1546880 is a bare 'dance'. '(tradicional)' invents a restriction 踊り does not carry, and "
        "left the record with the same word twice.",
    ),
    (
        749, 0, "pt",
        ["grosseria", "falta de educação", "descortesia"],
        ["grosseiro", "mal-educado", "grosseria", "falta de educação"],
        "The record is adj_class na_adj and its en leads with two adjectives, but every pt gloss was a noun, "
        "so a learner could not form 失礼な人. Adjectives lead now, the noun reading is kept, and the third "
        "noun ('descortesia', a synonym of the second) goes.",
    ),
    (
        823, 1, "pt",
        ["que pena", "infelizmente"],
        ["que pena", "que decepção"],
        "'infelizmente' is an adverb; 残念 is adj-na / n and never adverbial. 'que decepção' renders "
        "'disappointing' as an exclamation without duplicating s0, which already carries 'decepcionante'.",
    ),
    (
        1198, 0, "pt",
        ["injeção", "picada (vacina)"],
        ["injeção", "aplicação (de vacina)"],
        "In pt-BR 'picada' reads first as an insect bite.",
    ),
    (
        329, 0, "pt",
        ["aquecedor", "estufa"],
        ["aquecedor", "aquecedor a gás ou querosene"],
        "'estufa' in pt-BR is a greenhouse. JMdict gives '(room) heater / stove', i.e. the gas or kerosene "
        "space heater a ストーブ actually is.",
    ),
    (
        1249, 1, "pt",
        ["pegar (doença)", "ser transmitido"],
        ["ser transmitida (doença)", "passar de uma pessoa para outra"],
        "移る is vi with the illness as subject (風邪がうつる). 'pegar (doença)' flips the subject to the "
        "person and reads as transitive, so a learner would produce 風邪をうつる.",
    ),
    (
        1049, 0, "pt",
        ["mulher", "indivíduo do sexo feminino"],
        ["mulher", "pessoa do sexo feminino"],
        "'indivíduo' is clinical register; design/translation_style.md §4 asks for direct, concrete, "
        "beginner-clear pt-BR.",
    ),
    (
        1037, 0, "pt",
        ["homem", "indivíduo do sexo masculino"],
        ["homem", "pessoa do sexo masculino"],
        "Same fix on the mirror record, so the pair stays parallel.",
    ),
    (
        910, 0, "pt",
        ["bebê", "nenê"],
        ["bebê", "neném"],
        "798 赤ちゃん and 910 赤ん坊 are neighbouring records that spelled the same word two ways. 'neném' is "
        "the spelling 798 already uses, so 910 moves rather than both.",
    ),
    # -- F17 (medium): suru-noun records that packed the noun and the する reading into one sense, and let
    #    the en and pt lists drift out of correspondence. 1014 冷房 already has the right two-sense shape.
    (
        1160, 0, "en",
        ["heating", "heater", "to heat (a room)"],
        ["heating", "heater"],
        "JMdict 1419860 is one noun sense, '(indoor) heating'. The verb reading moves to its own sense, "
        "matching 1014 冷房.",
    ),
    (
        1160, 0, "pt",
        ["aquecimento", "calefação", "aquecedor"],
        ["aquecimento", "calefação"],
        "pt[2] was 'aquecedor' — a noun opposite en[2] 'to heat (a room)', and a duplicate of en[1] — so no "
        "gloss anywhere in the record meant *aquecer* and 暖房する had no pt-BR rendering at all.",
    ),
    (
        1141, 0, "en",
        ["broadcast", "broadcasting", "to air", "to broadcast"],
        ["broadcast", "broadcasting"],
        "Four en glosses against three pt, with the noun and verb readings interleaved. The nominal half "
        "stays in s0.",
    ),
    (
        1141, 0, "pt",
        ["transmissão", "transmitir", "ir ao ar"],
        ["transmissão", "difusão"],
        "pt[1] 'transmitir' (verb) sat opposite en[1] 'broadcasting' (noun). Both verbs move to s1; "
        "'difusão' gives the noun sense a second gloss.",
    ),
    (
        1150, 0, "en",
        ["lecture", "to lecture", "to give a lecture"],
        ["lecture"],
        "JMdict 1282260 is a bare noun, 'lecture'. The two verb glosses move to their own sense.",
    ),
    (
        1150, 0, "pt",
        ["palestra", "aula (expositiva)", "dar uma palestra"],
        ["palestra", "aula (expositiva)"],
        "en[1] 'to lecture' (verb) sat opposite pt[1] 'aula (expositiva)' (noun). Splitting the sense fixes "
        "the alignment instead of shuffling glosses inside one list.",
    ),
    # -- F18 (medium): 不味い led with the wrong flavour complaint.
    (
        603, 0, "pt",
        ["sem graça (comida)", "ruim de sabor", "intragável"],
        ["ruim (de gosto)", "horrível (de sabor)", "intragável"],
        "In pt-BR 'sem graça' applied to food means bland — the absence of flavour, which is 味気ない, not "
        "まずい. Sitting at index 0 it is the string a flashcard front and any short-form UI shows, so the "
        "learner's one-word takeaway was the wrong adjective. JMdict's own sense 0 is 'bad(-tasting) | "
        "unpalatable | awful'. 95 美味しい is the mirror entry and leads correctly with 'delicioso'.",
    ),
    # -- F19 (low): three more pt glosses that mistranslate or misdate their own en.
    (
        422, 0, "pt",
        ["loja de departamentos", "magazine"],
        ["loja de departamentos", "grande loja"],
        "'magazine' as a common noun for a department store is dated Brazilian usage that survives mostly "
        "inside brand names; a learner reads the English word and maps デパート to *revista*.",
    ),
    (
        101, 0, "pt",
        ["doces", "guloseimas", "salgadinhos"],
        ["doces", "guloseimas", "balas"],
        "'salgadinhos' are savoury — the one thing none of 'sweets | snacks | candy' covers, and JMdict "
        "1001710 is 'confections / sweets / candy / cake'. The report proposed 'confeitos'; 'balas' renders "
        "the same en[2] 'candy' in the concrete, beginner-clear register translation_style.md §4 asks for.",
    ),
    (
        414, 0, "pt",
        ["fita", "durex"],
        ["fita", "fita adesiva"],
        "'Durex' is a trademark, and it names only the adhesive half of a gloss whose own en covers the "
        "magnetic sense too.",
    ),
]

# ---------------------------------------------------------------------------------------------------
# F11 — one gloss per array element. 36 records comma-joined several glosses inside a single string and
# 50 semicolon-joined them, so a renderer drawing one chip per gloss showed 優しい as a single blob next to
# a neighbour showing three, and gloss-level matching in exercise generation broke. Split on a bare `,`
# or `;` outside parentheses, in both locales.
#
# NOT split (the separator is inside one lexical unit, or a parenthetical qualifies the whole string
# rather than only its last segment) — each of these would lose meaning:
#   231 s1 pt "não, obrigado"          -- one polite refusal
#   1167 s0 pt "ah, sim"               -- one interjection
#   360 s1 en "well, then (parting)"   -- one expression
#   775 s1 en "if (one does), then"    -- one conditional gloss
#   594 s0 en "counter for flat, thin objects (...)"  -- "flat, thin" is one noun phrase
#   1213 s0 en "100,000,000"           -- a numeral
#   400 s2 en "(softening) excuse me, hey"      -- the leading qualifier covers both halves
#   1275 s0 pt "(não) ... de jeito nenhum, nada" -- ditto; "nada" alone loses the negative polarity
#   1274 s0 en/pt "to go, to come (humble)" / "ir, vir (humilde)" -- trailing qualifier covers both
#   1275 s1 en/pt "totally, completely (colloquial, affirmative)" -- ditto
#   176 s0 en/pt  "...(suffix turning an adjective into a verb)"  -- ditto
#   159 s1 en "way of doing, how to (after a verb stem, 〜方)"     -- ditto (the pt IS split: its
#             parenthetical belongs to the first segment only)
#   154 s0 en -- record is queued for identity re-pointing, leave its glosses to that migration
# ---------------------------------------------------------------------------------------------------
SPLIT_WHY = ("Two gloss-list conventions coexisted in the same field: this sense joined several glosses "
             "into one array element while its neighbours used one element each (F11).")

SPLIT_FIXES: list[tuple[int, int, str, Gloss, Gloss]] = [
    (150, 1, "en", ["to draw, to paint"],
     ["to draw", "to paint"]),  # 書く
    (153, 0, "en", ["to hang (up), to put on"],
     ["to hang (up)", "to put on"]),  # 掛ける
    (153, 2, "en", ["to turn on, to play (a device)"],
     ["to turn on", "to play (a device)"]),  # 掛ける
    (153, 3, "en", ["to apply (a lock, brakes), to put on"],
     ["to apply (a lock, brakes)", "to put on"]),  # 掛ける
    (156, 0, "en", ["to lend, to loan"],
     ["to lend", "to loan"]),  # 貸す
    (157, 0, "en", ["wind, breeze"],
     ["wind", "breeze"]),  # 風
    (159, 0, "en", ["person (polite)", "lady, gentleman"],
     ["person (polite)", "lady", "gentleman"]),  # 方
    (159, 1, "pt", ["maneira de (fazer algo), modo de"],
     ["maneira de (fazer algo)", "modo de"]),  # 方
    (160, 0, "en", ["family, household"],
     ["family", "household"]),  # 家族
    (164, 0, "en", ["cup, mug"],
     ["cup", "mug"]),  # カップ
    (165, 0, "en", ["home, household, family"],
     ["home", "household", "family"]),  # 家庭
    (166, 1, "en", ["angle, corner (of an object)"],
     ["angle", "corner (of an object)"]),  # 角
    (167, 0, "en", ["bag, briefcase, satchel"],
     ["bag", "briefcase", "satchel"]),  # 鞄
    (169, 0, "en", ["to put on, to wear (on the head)"],
     ["to put on", "to wear (on the head)"]),  # 被る
    (169, 1, "en", ["to cover oneself with, to pour over oneself"],
     ["to cover oneself with", "to pour over oneself"]),  # 被る
    (173, 0, "en", ["spicy, hot"],
     ["spicy", "hot"]),  # 辛い
    (173, 2, "en", ["harsh, strict"],
     ["harsh", "strict"]),  # 辛い
    (174, 1, "en", ["health, physical condition"],
     ["health", "physical condition"]),  # 体
    (180, 0, "en", ["river, stream"],
     ["river", "stream"]),  # 川
    (182, 0, "en", ["cute, adorable"],
     ["cute", "adorable"]),  # 可愛い
    (182, 1, "en", ["lovely, charming, dear"],
     ["lovely", "charming", "dear"]),  # 可愛い
    (183, 0, "en", ["kanji, Chinese character"],
     ["kanji", "Chinese character"]),  # 漢字
    (187, 0, "en", ["to go out (light, fire), to be turned off"],
     ["to go out (light, fire)", "to be turned off"]),  # 消える
    (187, 1, "en", ["to disappear, to vanish"],
     ["to disappear", "to vanish"]),  # 消える
    (934, 0, "en", ["just (did something); only just"],
     ["just (did something)", "only just"]),  # 許り
    (934, 1, "en", ["only; nothing but; just"],
     ["only", "nothing but", "just"]),  # 許り
    (934, 2, "en", ["about; approximately"],
     ["about", "approximately"]),  # 許り
    (935, 0, "en", ["heart; mind"],
     ["heart", "mind"]),  # 心
    (935, 1, "en", ["spirit; feelings; intention"],
     ["spirit", "feelings", "intention"]),  # 心
    (937, 0, "en", ["to deliver; to send"],
     ["to deliver", "to send"]),  # 届ける
    (937, 1, "en", ["to report; to notify (officially)"],
     ["to report", "to notify (officially)"]),  # 届ける
    (938, 0, "en", ["greeting; salutation"],
     ["greeting", "salutation"]),  # 挨拶
    (938, 1, "en", ["to greet; to say hello"],
     ["to greet", "to say hello"]),  # 挨拶
    (938, 2, "en", ["address; speech (formal remarks)"],
     ["address", "speech (formal remarks)"]),  # 挨拶
    (939, 0, "en", ["scenery; landscape; view"],
     ["scenery", "landscape", "view"]),  # 景色
    (940, 0, "en", ["certain; sure; definite"],
     ["certain", "sure", "definite"]),  # 確か
    (940, 1, "en", ["if I remember right; I believe"],
     ["if I remember right", "I believe"]),  # 確か
    (942, 0, "en", ["groceries; foodstuffs; food items"],
     ["groceries", "foodstuffs", "food items"]),  # 食料品
    (943, 0, "en", ["forest; woods"],
     ["forest", "woods"]),  # 森
    (944, 0, "en", ["within; inside (a limit); less than"],
     ["within", "inside (a limit)", "less than"]),  # 以内
    (945, 0, "en", ["plan; schedule; arrangement"],
     ["plan", "schedule", "arrangement"]),  # 予定
    (945, 1, "en", ["to plan; to schedule; to be due to"],
     ["to plan", "to schedule", "to be due to"]),  # 予定
    (946, 0, "en", ["overcoat; coat"],
     ["overcoat", "coat"]),  # オーバー
    (948, 0, "en", ["stone; rock"],
     ["stone", "rock"]),  # 石
    (949, 0, "en", ["to remember; to recall; to call to mind"],
     ["to remember", "to recall", "to call to mind"]),  # 思い出す
    (951, 0, "en", ["small; fine; tiny"],
     ["small", "fine", "tiny"]),  # 細かい
    (951, 1, "en", ["detailed; minute; thorough"],
     ["detailed", "minute", "thorough"]),  # 細かい
    (952, 0, "en", ["to paint; to coat; to apply (a layer)"],
     ["to paint", "to coat", "to apply (a layer)"]),  # 塗る
    (953, 1, "en", ["master (of a house); landlord"],
     ["master (of a house)", "landlord"]),  # ご主人
    (954, 0, "en", ["rare; unusual; uncommon"],
     ["rare", "unusual", "uncommon"]),  # 珍しい
    (954, 1, "en", ["novel; curious; new"],
     ["novel", "curious", "new"]),  # 珍しい
    (955, 0, "en", ["task; errand; business (to attend to)"],
     ["task", "errand", "business (to attend to)"]),  # 用
    (955, 1, "en", ["use; purpose"],
     ["use", "purpose"]),  # 用
    (956, 0, "en", ["civil servant; public official; government employee"],
     ["civil servant", "public official", "government employee"]),  # 公務員
    (957, 0, "en", ["young lady; (your) daughter"],
     ["young lady", "(your) daughter"]),  # お嬢さん
    (958, 0, "en", ["preparation; arrangements"],
     ["preparation", "arrangements"]),  # 用意
    (958, 1, "en", ["to prepare; to get ready"],
     ["to prepare", "to get ready"]),  # 用意
    (959, 0, "en", ["to look for; to search for; to seek"],
     ["to look for", "to search for", "to seek"]),  # 探す
    (960, 0, "en", ["shape; form; figure"],
     ["shape", "form", "figure"]),  # 形
    (961, 1, "en", ["to drive; to operate (a machine)"],
     ["to drive", "to operate (a machine)"]),  # 運転
    (962, 0, "en", ["completely; entirely; thoroughly"],
     ["completely", "entirely", "thoroughly"]),  # すっかり
    (963, 0, "en", ["announcer; broadcaster"],
     ["announcer", "broadcaster"]),  # アナウンサー
    (964, 0, "en", ["souvenir; gift (brought back from a trip)"],
     ["souvenir", "gift (brought back from a trip)"]),  # お土産
    (965, 0, "en", ["eraser; rubber"],
     ["eraser", "rubber"]),  # 消しゴム
    (966, 0, "en", ["traditional Japanese inn; ryokan"],
     ["traditional Japanese inn", "ryokan"]),  # 旅館
    (967, 0, "en", ["coast; seashore; beach"],
     ["coast", "seashore", "beach"]),  # 海岸
    (968, 0, "en", ["lonely; lonesome"],
     ["lonely", "lonesome"]),  # 寂しい
    (968, 1, "en", ["desolate; deserted; bleak"],
     ["desolate", "deserted", "bleak"]),  # 寂しい
    (969, 0, "en", ["fire; flame"],
     ["fire", "flame"]),  # 火
    (970, 0, "en", ["to raise; to bring up (a child)"],
     ["to raise", "to bring up (a child)"]),  # 育てる
    (970, 1, "en", ["to grow; to cultivate (plants); to nurture"],
     ["to grow", "to cultivate (plants)", "to nurture"]),  # 育てる
    (971, 0, "en", ["miso; fermented soybean paste"],
     ["miso", "fermented soybean paste"]),  # 味噌
    (972, 0, "en", ["celebration; congratulations"],
     ["celebration", "congratulations"]),  # お祝い
    (973, 0, "en", ["vehicle; means of transport; ride"],
     ["vehicle", "means of transport", "ride"]),  # 乗り物
    (1032, 1, "en", ["to relieve oneself (用を足す), to do one's business"],
     ["to relieve oneself (用を足す)", "to do one's business"]),  # 足す
    (1042, 0, "en", ["to fish (with a rod), to catch (fish)"],
     ["to fish (with a rod)", "to catch (fish)"]),  # 釣る
    (1254, 1, "en", ["to introduce, to present (something new)", "to show, to feature"],
     ["to introduce", "to present (something new)", "to show", "to feature"]),  # 紹介
    (1254, 1, "pt", ["apresentar, mostrar (algo novo)", "dar a conhecer"],
     ["apresentar", "mostrar (algo novo)", "dar a conhecer"]),  # 紹介
    (1255, 0, "en", ["but, however"],
     ["but", "however"]),  # けれど
    (1255, 0, "pt", ["mas, porém"],
     ["mas", "porém"]),  # けれど
    (1255, 1, "en", ["although, even though"],
     ["although", "even though"]),  # けれど
    (1255, 1, "pt", ["embora, ainda que"],
     ["embora", "ainda que"]),  # けれど
    (1256, 0, "en", ["ship, boat, vessel"],
     ["ship", "boat", "vessel"]),  # 船
    (1256, 0, "pt", ["navio, barco, embarcação"],
     ["navio", "barco", "embarcação"]),  # 船
    (1257, 0, "en", ["to move, to be in motion"],
     ["to move", "to be in motion"]),  # 動く
    (1257, 0, "pt", ["mover-se, mexer-se"],
     ["mover-se", "mexer-se"]),  # 動く
    (1257, 1, "en", ["to run, to work, to operate (machine)"],
     ["to run", "to work", "to operate (machine)"]),  # 動く
    (1257, 1, "pt", ["funcionar, operar (máquina)"],
     ["funcionar", "operar (máquina)"]),  # 動く
    (1258, 0, "en", ["about, concerning, regarding"],
     ["about", "concerning", "regarding"]),  # 就いて
    (1258, 0, "pt", ["sobre, a respeito de"],
     ["sobre", "a respeito de"]),  # 就いて
    (1259, 0, "pt", ["concerto, show"],
     ["concerto", "show"]),  # コンサート
    (1260, 0, "en", ["insect, bug"],
     ["insect", "bug"]),  # 虫
    (1260, 0, "pt", ["inseto, bicho"],
     ["inseto", "bicho"]),  # 虫
    (1261, 0, "en", ["kind, gentle, nice"],
     ["kind", "gentle", "nice"]),  # 優しい
    (1261, 0, "pt", ["gentil, bondoso, amável"],
     ["gentil", "bondoso", "amável"]),  # 優しい
    (1261, 1, "en", ["tender, gentle, mild"],
     ["tender", "gentle", "mild"]),  # 優しい
    (1261, 1, "pt", ["suave, ameno, delicado"],
     ["suave", "ameno", "delicado"]),  # 優しい
    (1264, 0, "en", ["both, both sides, the two"],
     ["both", "both sides", "the two"]),  # 両方
    (1264, 0, "pt", ["ambos, os dois"],
     ["ambos", "os dois"]),  # 両方
    (1265, 0, "en", ["to get dirty, to become soiled"],
     ["to get dirty", "to become soiled"]),  # 汚れる
    (1265, 0, "pt", ["sujar-se, ficar sujo"],
     ["sujar-se", "ficar sujo"]),  # 汚れる
    (1267, 1, "en", ["to experience, to go through"],
     ["to experience", "to go through"]),  # 経験
    (1267, 1, "pt", ["experimentar, vivenciar, passar por"],
     ["experimentar", "vivenciar", "passar por"]),  # 経験
    (1268, 0, "pt", ["vencer, ganhar"],
     ["vencer", "ganhar"]),  # 勝つ
    (1268, 1, "en", ["to beat, to defeat"],
     ["to beat", "to defeat"]),  # 勝つ
    (1268, 1, "pt", ["derrotar, superar"],
     ["derrotar", "superar"]),  # 勝つ
    (1271, 0, "en", ["to replace, to exchange, to swap"],
     ["to replace", "to exchange", "to swap"]),  # 取り替える
    (1271, 0, "pt", ["trocar, substituir"],
     ["trocar", "substituir"]),  # 取り替える
    (1272, 0, "en", ["to hurry, to rush"],
     ["to hurry", "to rush"]),  # 急ぐ
    (1272, 0, "pt", ["apressar-se, ter pressa"],
     ["apressar-se", "ter pressa"]),  # 急ぐ
    (1273, 0, "en", ["simple, easy"],
     ["simple", "easy"]),  # 簡単
    (1273, 0, "pt", ["simples, fácil"],
     ["simples", "fácil"]),  # 簡単
    (1273, 1, "en", ["brief, quick, light"],
     ["brief", "quick", "light"]),  # 簡単
    (1273, 1, "pt", ["breve, rápido, sucinto"],
     ["breve", "rápido", "sucinto"]),  # 簡単
    (1274, 1, "en", ["to be beaten, to be defeated, to give in"],
     ["to be beaten", "to be defeated", "to give in"]),  # 参る
    (1274, 1, "pt", ["render-se, não aguentar, dar-se por vencido"],
     ["render-se", "não aguentar", "dar-se por vencido"]),  # 参る
    (1275, 0, "en", ["(not) at all, completely (not)"],
     ["(not) at all", "completely (not)"]),  # 全然
    (1276, 0, "en", ["special, particular"],
     ["special", "particular"]),  # 特別
    (1276, 0, "pt", ["especial, particular"],
     ["especial", "particular"]),  # 特別
    (1276, 1, "en", ["especially, particularly"],
     ["especially", "particularly"]),  # 特別
    (1276, 1, "pt", ["especialmente, em especial"],
     ["especialmente", "em especial"]),  # 特別
    (1278, 0, "en", ["to be in time, to make it"],
     ["to be in time", "to make it"]),  # 間に合う
    (1278, 0, "pt", ["chegar a tempo, dar tempo"],
     ["chegar a tempo", "dar tempo"]),  # 間に合う
    (1278, 1, "en", ["to be enough, to do, to suffice"],
     ["to be enough", "to do", "to suffice"]),  # 間に合う
    (1278, 1, "pt", ["ser suficiente, servir, dar para o gasto"],
     ["ser suficiente", "servir", "dar para o gasto"]),  # 間に合う
    (1279, 0, "en", ["to be useful, to come in handy, to help"],
     ["to be useful", "to come in handy", "to help"]),  # 役に立つ
    (1279, 0, "pt", ["ser útil, servir, ajudar"],
     ["ser útil", "servir", "ajudar"]),  # 役に立つ
    (1280, 0, "en", ["to return, to go back, to come back"],
     ["to return", "to go back", "to come back"]),  # 戻る
    (1280, 0, "pt", ["voltar, retornar"],
     ["voltar", "retornar"]),  # 戻る
    (1281, 0, "en", ["research, study"],
     ["research", "study"]),  # 研究
    (1281, 0, "pt", ["pesquisa, estudo"],
     ["pesquisa", "estudo"]),  # 研究
    (1281, 1, "en", ["to research, to study"],
     ["to research", "to study"]),  # 研究
    (1281, 1, "pt", ["pesquisar, estudar"],
     ["pesquisar", "estudar"]),  # 研究
    (1283, 0, "pt", ["grama, capim"],
     ["grama", "capim"]),  # 草
    (1283, 1, "en", ["weed, weeds"],
     ["weed", "weeds"]),  # 草
    (1283, 1, "pt", ["erva, mato"],
     ["erva", "mato"]),  # 草
    (1284, 0, "en", ["to be crowded, to be packed"],
     ["to be crowded", "to be packed"]),  # 込む
    (1284, 0, "pt", ["estar lotado, estar cheio"],
     ["estar lotado", "estar cheio"]),  # 込む
    (1285, 0, "en", ["these days, lately, nowadays"],
     ["these days", "lately", "nowadays"]),  # この頃
    (1285, 0, "pt", ["ultimamente, hoje em dia, atualmente"],
     ["ultimamente", "hoje em dia", "atualmente"]),  # この頃
    (1287, 0, "en", ["to lower, to bring down, to reduce"],
     ["to lower", "to bring down", "to reduce"]),  # 下げる
    (1287, 0, "pt", ["abaixar, baixar, reduzir"],
     ["abaixar", "baixar", "reduzir"]),  # 下げる
    (1287, 1, "en", ["to hang (down), to take away (dishes)"],
     ["to hang (down)", "to take away (dishes)"]),  # 下げる
    (1287, 1, "pt", ["pendurar, retirar (pratos da mesa)"],
     ["pendurar", "retirar (pratos da mesa)"]),  # 下げる
    (1289, 0, "en", ["on the way, midway"],
     ["on the way", "midway"]),  # 途中
    (1289, 0, "pt", ["no caminho, a caminho"],
     ["no caminho", "a caminho"]),  # 途中
    (1289, 1, "en", ["partway through, in the middle (of doing)"],
     ["partway through", "in the middle (of doing)"]),  # 途中
    (1289, 1, "pt", ["no meio (de algo), pela metade"],
     ["no meio (de algo)", "pela metade"]),  # 途中
    (1290, 1, "en", ["to be hospitalized, to be admitted to hospital"],
     ["to be hospitalized", "to be admitted to hospital"]),  # 入院
    (1290, 1, "pt", ["ser internado, dar entrada no hospital"],
     ["ser internado", "dar entrada no hospital"]),  # 入院
    (1291, 0, "en", ["to change (trains, buses), to transfer"],
     ["to change (trains, buses)", "to transfer"]),  # 乗り換える
    (1291, 0, "pt", ["fazer baldeação, trocar (de trem, ônibus)"],
     ["fazer baldeação", "trocar (de trem, ônibus)"]),  # 乗り換える
    (1291, 1, "pt", ["mudar para, trocar por"],
     ["mudar para", "trocar por"]),  # 乗り換える
    (1292, 0, "en", ["to part, to say goodbye, to separate"],
     ["to part", "to say goodbye", "to separate"]),  # 別れる
    (1292, 0, "pt", ["separar-se, despedir-se"],
     ["separar-se", "despedir-se"]),  # 別れる
    (1293, 0, "en", ["safety, security"],
     ["safety", "security"]),  # 安全
    (1293, 1, "en", ["safe, secure"],
     ["safe", "secure"]),  # 安全
    (1358, 1, "en", ["to make (a decision), to choose"],
     ["to make (a decision)", "to choose"]),  # 為る
]

# ---------------------------------------------------------------------------------------------------
# Record-level column fixes: (vocab_id, column, exact current value, corrected value, why)
# ---------------------------------------------------------------------------------------------------
COLUMN_FIXES: list[tuple[int, str, object, object, str]] = [
    (
        368, "adj_class", None, "na_adj",
        "F16. Sweeping all 1,358 n5/n4 records for adj-na / adj-i / adj-ix in any sense pos against the "
        "record-level adj_class returns exactly one mismatch, this record: 大変 has adj-na on s1 and "
        "adj_class null. Its neighbours are consistent (119 大人, 364 大丈夫, 366 大切, 761 大事). "
        "corpus/conjugations/{n5,n4}.json is keyed off adj_class, so 大変 silently dropped out of every "
        "な-adjective drill even though 大変な一日 is standard N5 material.",
    ),
]

# ---------------------------------------------------------------------------------------------------
# Sense reordering: (vocab_id, [(exact current gloss_en of the sense, target sense_order)], why)
# Senses are addressed by their gloss_en so a partially-applied run still recognises them.
# ---------------------------------------------------------------------------------------------------
ORDER_FIXES: list[tuple[int, list[tuple[Gloss, int]], str]] = [
    (
        1055,
        [(["dream (while sleeping)"], 0), (["dream (aspiration, goal)"], 1)],
        "F15. JMdict 1529410 orders the sleeping-dream sense first, and that is the sense an N4 learner "
        "meets first (夢を見る). Both senses are present, so this is an order swap only.",
    ),
    (
        1338,
        [(["back (of the body)"], 0), (["height (of a person)", "stature"], 1)],
        "F13 + F19. 336 背(せい) and 1338 背(せ) are separate, legitimate JMdict entries (1472650 / 2147990) "
        "but 1338 led with the height sense, byte-identical to 336, so the two cards were indistinguishable "
        "and its own distinctive sense sat at s1. JMdict's sense 0 for せ is 'back', so leading with "
        "'costas | dorso' follows Layer A and separates the cards without deleting either.",
    ),
]

# ---------------------------------------------------------------------------------------------------
# New senses: (vocab_id, sense_order, pos, gloss_en, gloss_pt, why). Inserted only when the record does
# not already have a sense at that order, so a second run is a no-op.
# ---------------------------------------------------------------------------------------------------
SENSE_INSERTS: list[tuple[int, int, list[str], Gloss, Gloss, str]] = [
    (
        41, 1, ["pn"], ["that person"], ["aquela pessoa (ali)"],
        "F2. The person reading is real — JMdict 1000580 sense 1 — it was simply occupying sense 0's slot. "
        "It returns here as s1 so nothing is lost by restoring 'aquilo' to s0.",
    ),
    (
        1160, 1, ["n", "vs", "vt"], ["to heat (a room)"], ["aquecer (um ambiente)", "ligar o aquecedor"],
        "F17. Gives 暖房 the two-sense shape its sibling 1014 冷房 already has, and gives 暖房する a pt-BR "
        "rendering for the first time.",
    ),
    (
        1141, 1, ["n", "vs", "vt"], ["to air", "to broadcast"], ["transmitir", "ir ao ar"],
        "F17. The verb glosses that were packed into s0, now aligned en[i] to pt[i].",
    ),
    (
        1150, 1, ["n", "vs", "vt"], ["to lecture", "to give a lecture"], ["dar uma palestra", "dar aula"],
        "F17. Same split; 'dar aula' renders 'to lecture' as a verb, which the packed sense never did.",
    ),
]


def jdump(v: Gloss) -> str:
    """Serialise exactly the way the rest of the index does, so untouched rows stay byte-identical."""
    return json.dumps(v, ensure_ascii=False)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args()
    con = sqlite3.connect(DB)
    con.execute("PRAGMA busy_timeout=60000")

    changed, skipped = 0, []

    def say(label: str, why: str) -> None:
        nonlocal changed
        print(f"  {label}\n     why: {why}")
        changed += 1

    def sense(vid: int, order: int):
        return con.execute(
            "SELECT id,gloss_en,gloss_pt FROM vocab_sense WHERE vocab_id=? AND sense_order=?",
            (vid, order)).fetchone()

    def head(vid: int) -> str:
        r = con.execute("SELECT headword,kana FROM vocab WHERE id=?", (vid,)).fetchone()
        return f"{r[0]}/{r[1]}" if r else "?"

    def write_gloss(sid: int, locale: str, value: Gloss) -> None:
        raw = jdump(value)
        col = "gloss_en" if locale == "en" else "gloss_pt"
        con.execute(f"UPDATE vocab_sense SET {col}=? WHERE id=?", (raw, sid))
        if locale == "pt":
            # localized_text is what the exporter actually reads for pt-BR; keep the two layers equal.
            n = con.execute(
                "UPDATE localized_text SET value=? WHERE entity_type='vocab_sense' AND entity_id=? "
                "AND field='gloss' AND locale='pt-BR'", (raw, sid)).rowcount
            if n != 1:
                raise RuntimeError(f"sense {sid}: expected 1 localized_text pt-BR gloss row, updated {n}")

    def apply_gloss(vid: int, order: int, locale: str, before: Gloss, after: Gloss, why: str) -> None:
        nonlocal changed
        label = f"{vid} {head(vid)} s{order}.{locale}"
        row = sense(vid, order)
        if row is None:
            skipped.append(f"{label}: no sense at that order")
            return
        sid, ge, gp = row
        cur = json.loads((ge if locale == "en" else gp) or "[]")
        if cur == after:
            return                                                   # already repaired
        if cur != before:
            skipped.append(f"{label}: current value {cur!r} matches neither the expected text nor the "
                           f"correction — not touching it")
            return
        say(f"{label}: {jdump(before)} -> {jdump(after)}", why)
        if not args.check:
            write_gloss(sid, locale, after)

    for vid, order, locale, before, after, why in GLOSS_FIXES:
        apply_gloss(vid, order, locale, before, after, why)
    for vid, order, locale, before, after in SPLIT_FIXES:
        apply_gloss(vid, order, locale, before, after, SPLIT_WHY)

    for vid, column, before, after, why in COLUMN_FIXES:
        label = f"{vid} {head(vid)}.{column}"
        row = con.execute(f"SELECT {column} FROM vocab WHERE id=?", (vid,)).fetchone()
        if row is None:
            skipped.append(f"{label}: no such vocab record")
        elif row[0] == after:
            pass
        elif row[0] != before:
            skipped.append(f"{label}: current value {row[0]!r} matches neither — not touching it")
        else:
            say(f"{label}: {before!r} -> {after!r}", why)
            if not args.check:
                con.execute(f"UPDATE vocab SET {column}=? WHERE id=?", (after, vid))

    for vid, wanted, why in ORDER_FIXES:
        label = f"{vid} {head(vid)}.sense_order"
        rows = con.execute("SELECT id,sense_order,gloss_en FROM vocab_sense WHERE vocab_id=?",
                           (vid,)).fetchall()
        by_gloss = {jdump(json.loads(g or "[]")): (sid, order) for sid, order, g in rows}
        missing = [jdump(g) for g, _ in wanted if jdump(g) not in by_gloss]
        if missing:
            skipped.append(f"{label}: no sense with gloss_en {missing[0]} — not reordering")
            continue
        moves = [(by_gloss[jdump(g)][0], target) for g, target in wanted
                 if by_gloss[jdump(g)][1] != target]
        if not moves:
            continue                                                 # already in the target order
        say(f"{label}: " + ", ".join(f"sense {sid} -> order {t}" for sid, t in moves), why)
        if not args.check:
            for sid, target in moves:
                con.execute("UPDATE vocab_sense SET sense_order=? WHERE id=?", (target, sid))

    for vid, order, pos, ge, gp, why in SENSE_INSERTS:
        label = f"{vid} {head(vid)} s{order} (new)"
        if con.execute("SELECT 1 FROM vocab WHERE id=?", (vid,)).fetchone() is None:
            skipped.append(f"{label}: no such vocab record")
            continue
        existing = sense(vid, order)
        if existing is not None:
            if json.loads(existing[1] or "[]") != ge:
                skipped.append(f"{label}: a different sense already occupies that order "
                               f"({existing[1]}) — not inserting")
            continue                                                 # already inserted
        say(f"{label}: {jdump(ge)} / {jdump(gp)}", why)
        if not args.check:
            cur = con.execute(
                "INSERT INTO vocab_sense (vocab_id,sense_order,pos,field_tags,misc_tags,gloss_en,"
                "gloss_pt,needs_review) VALUES (?,?,?,'[]','[]',?,?,1)",
                (vid, order, jdump(pos), jdump(ge), jdump(gp)))
            con.execute(
                "INSERT INTO localized_text (entity_type,entity_id,field,locale,value,is_list,layer) "
                "VALUES ('vocab_sense',?,'gloss','pt-BR',?,1,'B')", (cur.lastrowid, jdump(gp)))

    if not args.check:
        con.commit()
    verb = "would repair" if args.check else "repaired"
    print(f"\n{verb} {changed} field(s)")
    for s in skipped:
        print(f"  ! {s}")
    return 1 if (args.check and changed) else (2 if skipped else 0)


if __name__ == "__main__":
    sys.exit(main())
