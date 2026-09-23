# W18b: authored paraphrase / usage assembly

By `scripts/assemble_authored_banks.py` on committed tree `a07e04ddd3b5` (W17 patch applied to a scratch copy). Output: `research/derived/pending/authored_banks_final.json`.

## Inventory

| authored file | take | rows | sha256 |
|---|---|---:|---|
| `alt_batchC/authored-paraphrase-n4-01.json` | alt_batchC | 16 | `3cfb805f2ede` |
| `alt_batchC/authored-paraphrase-n5-01.json` | alt_batchC | 12 | `590a5e50f7d0` |
| `alt_batchC/authored-usage-n4-01.json` | alt_batchC | 16 | `ec14aa47cfaf` |
| `alt_batchC/authored-usage-n5-01.json` | alt_batchC | 12 | `19a07cd4e125` |
| `authored-_candidate_pool.json.json` | primary | 44 | `a87183ca5a7e` |
| `authored-work-paraphrase-n4-01.json.json` | primary | 24 | `b63491b9360e` |
| `authored-work-usage-n5-01.json.json` | primary | 22 | `d3ff876afd8d` |

| verdict file | adjudicated take | bound by | ids | ok | corrected | rejected |
|---|---|---|---:|---:|---:|---:|
| `authored-4.verdict.json` | alt_batchC | meta sha256 ec14aa47cfaf = `alt_batchC/authored-usage-n4-01.json`; 16 row fingerprints match | 16 | 9 | 7 | 0 |
| `authored-5.verdict.json` | primary | `file` field = `authored-_candidate_pool.json.json` | 44 | 31 | 9 | 4 |
| `authored-1.verdict.json` | alt_batchC | the only take covering its ids | 12 | 5 | 4 | 3 |
| `authored-2.verdict.json` | primary | the only take covering its ids | 22 | 17 | 4 | 1 |
| `authored-3.verdict.json` | primary | the only take covering its ids | 24 | 1 | 22 | 1 |
| `authored-0.verdict.json` | alt_batchC | the only take covering its ids | 56 | 49 | 5 | 2 |

## Counts

```json
{
 "authored_rows": 146,
 "distinct_ids": 118,
 "verdict_files": 6,
 "excluded": {
  "rejected": 11,
  "superseded": 27
 },
 "surviving_ids": 108,
 "selected": 30,
 "twins": 12,
 "explanation_names_option_position": [
  "us:n4:1098",
  "us:n4:1226",
  "us:n4:1300",
  "us:n4:1302",
  "us:n4:888",
  "us:n4:923",
  "us:n4:946",
  "us:n4:958",
  "us:n5:286",
  "us:n5:649",
  "us:n5:672"
 ]
}
```

| family:level | need | available | selected |
|---|---:|---:|---:|
| paraphrase:n4 | 11 | 43 | 11 |
| paraphrase:n5 | 7 | 9 | 7 |
| usage:n4 | 12 | 35 | 12 |
| usage:n5 | 0 | 21 | 0 |

Every need met: **yes**.

## Twelve selected items (authored option order: key is A)

**pp:n4:806** (primary, ok)  
stem: ごめんね。明日は朝からパートがあるのよ。 (target パート)  
options: A) アルバイト / B) 試験 / C) 食事 / D) 旅行  
key: A  
explanation: Nessa frase パート é o trabalho de meio período, e アルバイト nomeia o mesmo tipo de trabalho.

**pp:n4:807** (primary, ok)  
stem: この歌を聞くと私の中学校時代を思い出します。 (target 時代)  
options: A) ころ / B) 時間 / C) 教室 / D) 試験  
key: A  
explanation: 中学校時代 é o período em que a pessoa estudou no ginásio, e ころ marca essa mesma época.

**pp:n4:848** (primary, ok)  
stem: 今日はずっと気分がよい。 (target 気分)  
options: A) 気持ち / B) 天気 / C) 電気 / D) 病気  
key: A  
explanation: 気分 aqui é como a pessoa se sente por dentro, e 気持ち ocupa o mesmo lugar com o mesmo sentido.

**pp:n4:1226** (alt_batchC, ok)  
stem: 父は今度の木曜日にアメリカへ出発します。 (target 出発)  
options: A) 出かける / B) 帰る / C) 集まる / D) 休む  
key: A  
explanation: 出発する é pôr-se a caminho de outro lugar, o mesmo que 出かける diz na frase.

**pp:n5:286** (alt_batchC, corrected by authored-1.verdict.json)  
stem: 時間がありますか。 (target 時間)  
options: A) ひま / B) お金 / C) 天気 / D) 電話  
key: A  
explanation: Perguntar 時間がありますか é perguntar se a pessoa tem um tempo livre, e ひま é exatamente esse tempo livre.

**pp:n5:326** (alt_batchC, corrected by authored-1.verdict.json)  
stem: 少し休んだほうがいい。 (target 少し)  
options: A) ちょっと / B) たくさん / C) もっと / D) いつも  
key: A  
explanation: 少し e ちょっと marcam a mesma quantidade pequena, então 少し休む equivale a ちょっと休む.

**pp:n5:598** (alt_batchC, ok)  
stem: 母は毎日うちにいます。 (target 毎日)  
options: A) どの日も / B) どの月も / C) どの年も / D) この日も  
key: A  
explanation: 毎日 quer dizer que nenhum dia fica de fora, e どの日も expressa a mesma ideia.

**pp:n5:599** (alt_batchC, ok)  
stem: 毎年ここに来なきゃ。 (target 毎年)  
options: A) どの年も / B) どの日も / C) どの月も / D) この年も  
key: A  
explanation: 毎年 quer dizer que nenhum ano fica de fora, e どの年も expressa a mesma ideia.

**us:n4:1098** (alt_batchC, ok)  
stem: (usage item) (target 見える)  
options: A) 家が見える。 / B) テレビを見えるのが好きだ。 / C) 電話の音が見える。 / D) 友だちに手紙を見える。  
key: A  
explanation: Só a primeira frase põe em 見える algo que aparece à vista; nas outras o verbo recebe objeto com を ou toma um som como sujeito.

**us:n4:1226** (alt_batchC, ok)  
stem: (usage item) (target 出発)  
options: A) 父は今度の木曜日にアメリカへ出発します。 / B) 毎朝、パンとたまごを出発します。 / C) この本はとても出発です。 / D) へやの電気を出発してからねます。  
key: A  
explanation: Só a primeira frase usa 出発 como partida; nas outras ele ocupa o lugar de 食べる, de um adjetivo e de 消す.

**us:n4:1300** (alt_batchC, ok)  
stem: (usage item) (target 上がる)  
options: A) やがて雨は上がると思う。 / B) へやに入る前に、くつを上がるつもりです。 / C) 本を上がると、先生に見せます。 / D) 先生の話を上がるのはむずかしいです。  
key: A  
explanation: Só a primeira frase usa 上がる com a chuva que para; nas outras o verbo recebe objeto com を no lugar de 脱ぐ, de 取る e de 聞く.

**us:n4:1302** (alt_batchC, ok)  
stem: (usage item) (target 食事)  
options: A) 母が作ってくれた食事をおいしく食べた。 / B) 新しい食事を買って、着てみました。 / C) 駅の前で食事に乗りました。 / D) その食事はとても親切な人です。  
key: A  
explanation: Só a primeira frase come o 食事; nas outras ele vira roupa, veículo e pessoa.

