# course/speak — Trilha Fala Primeiro (speaking-first path)

A SECOND ORDERING over the same corpus, not a second corpus: every unit holds corpus IDs (`sent:`, `vocab:`, `gram:`) and embeds nothing. Spec: `design/speaking_path.md`. Built by `scripts/export/build_speaking_path.py` — rebuildable and diffable.

Ordering is **survival scenario** (primary) then **word frequency** (secondary, from `vocab.freq_rank`). Every stage is a usable stopping point: a learner who stops after stage 4 can still land, eat, buy and navigate.

**12 stages · 72 units · 432 phrases (432 real / 0 generated) · 584 vocabulary items introduced**

| # | Stage | Units | Phrases | New words | ≈band |
|---|---|---|---|---|---|
| 1 | Chegar e cumprimentar | 6 | 36 | 38 | pre-n5 |
| 2 | Isto, aquilo, quanto custa | 6 | 36 | 40 | pre-n5/n5 |
| 3 | Comer e beber fora | 6 | 36 | 65 | n5 |
| 4 | Chegar aonde você quer | 6 | 36 | 59 | n5 |
| 5 | Dormir e resolver problemas | 6 | 36 | 55 | n5 |
| 6 | Falar de você | 6 | 36 | 66 | n5 |
| 7 | Quando, que horas, combinar | 6 | 36 | 50 | n5/n4 |
| 8 | Emergência e saúde | 6 | 36 | 39 | n4 |
| 9 | Contar o que aconteceu | 6 | 36 | 43 | n4 |
| 10 | Pedir, oferecer, agradecer com jeito | 6 | 36 | 52 | n4 |
| 11 | Dizer o que você acha | 6 | 36 | 35 | n4/n3 |
| 12 | Conversa de verdade | 6 | 36 | 42 | n3 |

`say_now` phrases are real human-written bank sentences; set expressions (ありがとう, すみません) are taught whole as `chunk_phrases` because the analyzer mis-lemmatises them (すみません → 住む+ます+ぬ) and because that is how a learner meets them anyway. `kanji_recognition` is **recognition only** — this path never asks the learner to write kanji. `audio: "pending"` throughout, awaiting the voice-over pass (`design/listening.md`).
