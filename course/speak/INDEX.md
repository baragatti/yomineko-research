# course/speak — Trilha Fala Primeiro (speaking-first path)

A SECOND ORDERING over the same corpus, not a second corpus: every unit holds corpus IDs (`sent:`, `vocab:`, `gram:`) and embeds nothing. Spec: `design/speaking_path.md`. Built by `scripts/export/build_speaking_path.py` — rebuildable and diffable.

Ordering is **survival scenario** (primary) then **word frequency** (secondary, from `vocab.freq_rank`). Every stage is a usable stopping point: a learner who stops after stage 4 can still land, eat, buy and navigate.

**12 stages · 66 units · 396 phrases (396 real / 0 generated) · 514 vocabulary items introduced**

| # | Stage | Units | Phrases | New words | ≈band |
|---|---|---|---|---|---|
| 1 | Chegar e cumprimentar | 6 | 36 | 36 | pre-n5 |
| 2 | Isto, aquilo, quanto custa | 6 | 36 | 39 | pre-n5/n5 |
| 3 | Comer e beber fora | 6 | 36 | 64 | n5 |
| 4 | Chegar aonde você quer | 6 | 36 | 54 | n5 |
| 5 | Dormir e resolver problemas | 4 | 24 | 34 | n5 |
| 6 | Falar de você | 6 | 36 | 61 | n5 |
| 7 | Quando, que horas, combinar | 6 | 36 | 43 | n5/n4 |
| 8 | Emergência e saúde | 6 | 36 | 41 | n4 |
| 9 | Contar o que aconteceu | 5 | 30 | 33 | n4 |
| 10 | Pedir, oferecer, agradecer com jeito | 6 | 36 | 55 | n4 |
| 11 | Dizer o que você acha | 3 | 18 | 16 | n4/n3 |
| 12 | Conversa de verdade | 6 | 36 | 38 | n3 |

`say_now` phrases are real human-written bank sentences; set expressions (ありがとう, すみません) are taught whole as `chunk_phrases` because the analyzer mis-lemmatises them (すみません → 住む+ます+ぬ) and because that is how a learner meets them anyway. `kanji_recognition` is **recognition only** — this path never asks the learner to write kanji. `audio: "pending"` throughout, awaiting the voice-over pass (`design/listening.md`).

## Shortfall

Stages the bank cannot yet fill to target. The fix is SELECTION — mining the 248,705 already-licensed `raw_tatoeba_sentence` rows — not generated filler; see `design/speaking_path.md` §6. Recorded here rather than padded over:

- `lodging`: only 4 of 6 units
- `past_stories`: only 5 of 6 units
- `opinions`: only 3 of 6 units
