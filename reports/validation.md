# Validation report

_Phase P2 — level reconciliation._

## Lists used (≥3 each — PLAN_REVIEW D1/D2)
- kanji lists: {}
- vocab lists: {'elzup': 1386, 'openanki': 1386, 'bluskyo': 1349, 'jlptvocabapi': 1294}

## Reconciliation results
- kanji leveled: — by level {}
- vocab promoted: 1359 by level {'n4': 653, 'n5': 706}
- per-reading tiers seeded (heuristic, needs_review): 1633

## Kanji level disagreements across lists (0)
_Assigned the earliest voted level; review these._


## Vocab list entries unmatched in JMdict (66)
_Mostly affixes/counters/grammar-like/multiword; route to grammar or handle in P4. Sample (first 80):_

- [elzup/n5] お酒
- [elzup/n5] お皿
- [elzup/n5] 伯母さん; 叔母さん
- [elzup/n5] テープレコーダー
- [elzup/n5] ～屋
- [elzup/n5] ゆっくりと
- [elzup/n5] ラジオカセ
- [elzup/n4] 建て
- [elzup/n4] いくら～ても
- [elzup/n4] お祭り
- [elzup/n4] おいでになる
- [elzup/n4] ～(に) よると
- [elzup/n4] お子さん
- [elzup/n4] お見舞い
- [elzup/n4] もうすぐ
- [elzup/n4] 真中
- [elzup/n4] おかげ
- [openanki/n5] お酒
- [openanki/n5] お皿
- [openanki/n5] 伯母さん; 叔母さん
- [openanki/n5] テープレコーダー
- [openanki/n5] ～屋
- [openanki/n5] ゆっくりと
- [openanki/n5] ラジオカセ
- [openanki/n4] 建て
- [openanki/n4] いくら～ても
- [openanki/n4] お祭り
- [openanki/n4] おいでになる
- [openanki/n4] ～(に) よると
- [openanki/n4] お子さん
- [openanki/n4] お見舞い
- [openanki/n4] もうすぐ
- [openanki/n4] 真中
- [openanki/n4] お陰
- [bluskyo/n5] お酒
- [bluskyo/n5] お皿
- [bluskyo/n5] 伯母さん
- [bluskyo/n5] 叔母さん
- [bluskyo/n5] テープレコーダー
- [bluskyo/n5] 見る 観る
- [bluskyo/n5] ゆっくりと
- [bluskyo/n5] ラジオカセット
- [bluskyo/n4] おいでになる
- [bluskyo/n4] おかげ
- [bluskyo/n4] お祭り
- [bluskyo/n4] お見舞い
- [bluskyo/n4] 堅
- [bluskyo/n4] 硬
- [bluskyo/n4] 降り出す
- [bluskyo/n4] 真中
- [bluskyo/n4] もうすぐ
- [bluskyo/n4] 泳ぎ方
- [jlptvocabapi/n5] テープレコーダー
- [jlptvocabapi/n5] お皿
- [jlptvocabapi/n5] お酒
- [jlptvocabapi/n5] ゆっくりと
- [jlptvocabapi/n5] 見る  観る
- [jlptvocabapi/n5] 伯母さん / 叔母さん
- [jlptvocabapi/n4] 真中
- [jlptvocabapi/n4] もうすぐ
- [jlptvocabapi/n4] お祭り
- [jlptvocabapi/n4] お見舞い
- [jlptvocabapi/n4] 降り出す
- [jlptvocabapi/n4] おかげ
- [jlptvocabapi/n4] おいでになる
- [jlptvocabapi/n4] 泳ぎ方

---
## Sentence validation (§7)

Validated 5 sentences — **0 errors, 3 warnings**, 2 clean.
- sentence 1 `電話に出てください。`:
  - **warn**: sentence level n5 below max component level
- sentence 2 `乗ってください。`:
  - **warn**: sentence level n5 below max component level
- sentence 3 `電話をしてから来てください。`:
  - **warn**: sentence level n5 below max component level

---
## Sentence validation (§7)

Validated 5 sentences — **0 errors, 0 warnings**, 5 clean.

---
## Sentence validation (§7)

Validated 5 sentences — **0 errors, 0 warnings**, 5 clean.

---
## Sentence validation (§7)

Validated 19 sentences — **0 errors, 3 warnings**, 17 clean.
- sentence 13 `うれしさで舞い上がっています。`:
  - **warn**: lemma うれしさ not in JMdict-common (may be in full)
  - **warn**: lemma 舞い上がる not in JMdict-common (may be in full)
- sentence 15 `大学を出てから10年になります。`:
  - **warn**: lemma 10 not in JMdict-common (may be in full)

---
## Sentence validation (§7)

Validated 19 sentences — **0 errors, 3 warnings**, 17 clean.
- sentence 13 `うれしさで舞い上がっています。`:
  - **warn**: lemma うれしさ not in JMdict-common (may be in full)
  - **warn**: lemma 舞い上がる not in JMdict-common (may be in full)
- sentence 15 `大学を出てから10年になります。`:
  - **warn**: lemma 10 not in JMdict-common (may be in full)

---
## Sentence validation (§7)

Validated 35 sentences — **1 errors, 4 warnings**, 31 clean.
- sentence 13 `うれしさで舞い上がっています。`:
  - **warn**: lemma うれしさ not in JMdict-common (may be in full)
  - **warn**: lemma 舞い上がる not in JMdict-common (may be in full)
- sentence 15 `大学を出てから10年になります。`:
  - **warn**: lemma 10 not in JMdict-common (may be in full)
- sentence 30 `人をあざわらうのはよくない。`:
  - **warn**: lemma あざわらう not in JMdict-common (may be in full)
- sentence 31 `今日はむしろ外出したくない。`:
  - **error**: content token 'ない' missing gloss (Layer B)

---
## Sentence validation (§7)

Validated 35 sentences — **0 errors, 4 warnings**, 32 clean.
- sentence 13 `うれしさで舞い上がっています。`:
  - **warn**: lemma うれしさ not in JMdict-common (may be in full)
  - **warn**: lemma 舞い上がる not in JMdict-common (may be in full)
- sentence 15 `大学を出てから10年になります。`:
  - **warn**: lemma 10 not in JMdict-common (may be in full)
- sentence 30 `人をあざわらうのはよくない。`:
  - **warn**: lemma あざわらう not in JMdict-common (may be in full)

---
## Sentence validation (§7)

Validated 59 sentences — **1 errors, 4 warnings**, 55 clean.
- sentence 13 `うれしさで舞い上がっています。`:
  - **warn**: lemma うれしさ not in JMdict-common (may be in full)
  - **warn**: lemma 舞い上がる not in JMdict-common (may be in full)
- sentence 15 `大学を出てから10年になります。`:
  - **warn**: lemma 10 not in JMdict-common (may be in full)
- sentence 30 `人をあざわらうのはよくない。`:
  - **warn**: lemma あざわらう not in JMdict-common (may be in full)
- sentence 58 `ありがとう。これでけっこうです。`:
  - **error**: content token 'ありがとう' missing gloss (Layer B)

---
## Sentence validation (§7)

Validated 59 sentences — **0 errors, 4 warnings**, 56 clean.
- sentence 13 `うれしさで舞い上がっています。`:
  - **warn**: lemma うれしさ not in JMdict-common (may be in full)
  - **warn**: lemma 舞い上がる not in JMdict-common (may be in full)
- sentence 15 `大学を出てから10年になります。`:
  - **warn**: lemma 10 not in JMdict-common (may be in full)
- sentence 30 `人をあざわらうのはよくない。`:
  - **warn**: lemma あざわらう not in JMdict-common (may be in full)

---
## Sentence validation (§7)

Validated 63 sentences — **0 errors, 3 warnings**, 60 clean.
- sentence 12 `大学を出てから10年になります。`:
  - **warn**: lemma 10 not in JMdict-common (may be in full)
- sentence 20 `１１時になっているよ。`:
  - **warn**: lemma 11 not in JMdict-common (may be in full)
- sentence 35 `人をあざわらうのはよくない。`:
  - **warn**: lemma あざわらう not in JMdict-common (may be in full)

---
## Sentence validation (§7)

Validated 95 sentences — **0 errors, 10 warnings**, 87 clean.
- sentence 12 `大学を出てから10年になります。`:
  - **warn**: lemma 10 not in JMdict-common (may be in full)
- sentence 20 `１１時になっているよ。`:
  - **warn**: lemma 11 not in JMdict-common (may be in full)
- sentence 35 `人をあざわらうのはよくない。`:
  - **warn**: lemma あざわらう not in JMdict-common (may be in full)
- sentence 77 `とりあえず、あたりさわりのない話をしておいたよ。`:
  - **warn**: lemma あたりさわり not in JMdict-common (may be in full)
- sentence 79 `１万円でたりる？`:
  - **warn**: lemma 1万 not in JMdict-common (may be in full)
- sentence 81 `ログアウトするんじゃなかったよ。`:
  - **warn**: lemma ログアウト not in JMdict-common (may be in full)
- sentence 83 `10ヶ国語を話せたらどんなにかっこいいだろう！`:
  - **warn**: lemma 10 not in JMdict-common (may be in full)
  - **warn**: lemma 話せる not in JMdict-common (may be in full)
- sentence 91 `５月は４月のあとにくる。`:
  - **warn**: lemma 5 not in JMdict-common (may be in full)
  - **warn**: lemma 4 not in JMdict-common (may be in full)

---
## Sentence validation (§7)

Validated 135 sentences — **0 errors, 15 warnings**, 123 clean.
- sentence 12 `大学を出てから10年になります。`:
  - **warn**: lemma 10 not in JMdict-common (may be in full)
- sentence 20 `１１時になっているよ。`:
  - **warn**: lemma 11 not in JMdict-common (may be in full)
- sentence 35 `人をあざわらうのはよくない。`:
  - **warn**: lemma あざわらう not in JMdict-common (may be in full)
- sentence 77 `とりあえず、あたりさわりのない話をしておいたよ。`:
  - **warn**: lemma あたりさわり not in JMdict-common (may be in full)
- sentence 79 `１万円でたりる？`:
  - **warn**: lemma 1万 not in JMdict-common (may be in full)
- sentence 81 `ログアウトするんじゃなかったよ。`:
  - **warn**: lemma ログアウト not in JMdict-common (may be in full)
- sentence 83 `10ヶ国語を話せたらどんなにかっこいいだろう！`:
  - **warn**: lemma 10 not in JMdict-common (may be in full)
  - **warn**: lemma 話せる not in JMdict-common (may be in full)
- sentence 91 `５月は４月のあとにくる。`:
  - **warn**: lemma 5 not in JMdict-common (may be in full)
  - **warn**: lemma 4 not in JMdict-common (may be in full)
- sentence 111 `ここに座ってトムを待つことにするよ。`:
  - **warn**: lemma トム not in JMdict-common (may be in full)
- sentence 112 `やっぱりべーラと乗馬しに行くことにするよ。`:
  - **warn**: lemma べ not in JMdict-common (may be in full)
  - **warn**: lemma ラ not in JMdict-common (may be in full)
- sentence 118 `猫もしゃくしも外国へ行きたがる。`:
  - **warn**: lemma しゃくし not in JMdict-common (may be in full)
- sentence 133 `５０００円ばかりもっている。`:
  - **warn**: lemma 5000 not in JMdict-common (may be in full)

---
## Sentence validation (§7)

Validated 177 sentences — **0 errors, 19 warnings**, 162 clean.
- sentence 12 `大学を出てから10年になります。`:
  - **warn**: lemma 10 not in JMdict-common (may be in full)
- sentence 20 `１１時になっているよ。`:
  - **warn**: lemma 11 not in JMdict-common (may be in full)
- sentence 35 `人をあざわらうのはよくない。`:
  - **warn**: lemma あざわらう not in JMdict-common (may be in full)
- sentence 77 `とりあえず、あたりさわりのない話をしておいたよ。`:
  - **warn**: lemma あたりさわり not in JMdict-common (may be in full)
- sentence 79 `１万円でたりる？`:
  - **warn**: lemma 1万 not in JMdict-common (may be in full)
- sentence 81 `ログアウトするんじゃなかったよ。`:
  - **warn**: lemma ログアウト not in JMdict-common (may be in full)
- sentence 83 `10ヶ国語を話せたらどんなにかっこいいだろう！`:
  - **warn**: lemma 10 not in JMdict-common (may be in full)
  - **warn**: lemma 話せる not in JMdict-common (may be in full)
- sentence 91 `５月は４月のあとにくる。`:
  - **warn**: lemma 5 not in JMdict-common (may be in full)
  - **warn**: lemma 4 not in JMdict-common (may be in full)
- sentence 111 `ここに座ってトムを待つことにするよ。`:
  - **warn**: lemma トム not in JMdict-common (may be in full)
- sentence 112 `やっぱりべーラと乗馬しに行くことにするよ。`:
  - **warn**: lemma べ not in JMdict-common (may be in full)
  - **warn**: lemma ラ not in JMdict-common (may be in full)
- sentence 118 `猫もしゃくしも外国へ行きたがる。`:
  - **warn**: lemma しゃくし not in JMdict-common (may be in full)
- sentence 133 `５０００円ばかりもっている。`:
  - **warn**: lemma 5000 not in JMdict-common (may be in full)
- sentence 153 `１度に２つの事をしようと思うな。`:
  - **warn**: lemma 1度 not in JMdict-common (may be in full)
  - **warn**: lemma 2 not in JMdict-common (may be in full)
- sentence 165 `やぶへびを出すな。`:
  - **warn**: lemma やぶへび not in JMdict-common (may be in full)
- sentence 166 `おくびにも出すな。`:
  - **warn**: lemma おくび not in JMdict-common (may be in full)

---
## Sentence validation (§7)

Validated 226 sentences — **1 errors, 21 warnings**, 208 clean.
- sentence 12 `大学を出てから10年になります。`:
  - **warn**: lemma 10 not in JMdict-common (may be in full)
- sentence 20 `１１時になっているよ。`:
  - **warn**: lemma 11 not in JMdict-common (may be in full)
- sentence 35 `人をあざわらうのはよくない。`:
  - **warn**: lemma あざわらう not in JMdict-common (may be in full)
- sentence 77 `とりあえず、あたりさわりのない話をしておいたよ。`:
  - **warn**: lemma あたりさわり not in JMdict-common (may be in full)
- sentence 79 `１万円でたりる？`:
  - **warn**: lemma 1万 not in JMdict-common (may be in full)
- sentence 81 `ログアウトするんじゃなかったよ。`:
  - **warn**: lemma ログアウト not in JMdict-common (may be in full)
- sentence 83 `10ヶ国語を話せたらどんなにかっこいいだろう！`:
  - **warn**: lemma 10 not in JMdict-common (may be in full)
  - **warn**: lemma 話せる not in JMdict-common (may be in full)
- sentence 91 `５月は４月のあとにくる。`:
  - **warn**: lemma 5 not in JMdict-common (may be in full)
  - **warn**: lemma 4 not in JMdict-common (may be in full)
- sentence 111 `ここに座ってトムを待つことにするよ。`:
  - **warn**: lemma トム not in JMdict-common (may be in full)
- sentence 112 `やっぱりべーラと乗馬しに行くことにするよ。`:
  - **warn**: lemma べ not in JMdict-common (may be in full)
  - **warn**: lemma ラ not in JMdict-common (may be in full)
- sentence 118 `猫もしゃくしも外国へ行きたがる。`:
  - **warn**: lemma しゃくし not in JMdict-common (may be in full)
- sentence 133 `５０００円ばかりもっている。`:
  - **warn**: lemma 5000 not in JMdict-common (may be in full)
- sentence 153 `１度に２つの事をしようと思うな。`:
  - **warn**: lemma 1度 not in JMdict-common (may be in full)
  - **warn**: lemma 2 not in JMdict-common (may be in full)
- sentence 165 `やぶへびを出すな。`:
  - **warn**: lemma やぶへび not in JMdict-common (may be in full)
- sentence 166 `おくびにも出すな。`:
  - **warn**: lemma おくび not in JMdict-common (may be in full)
- sentence 186 `これは父に気に入ってもらう。`:
  - **error**: particle て missing explanation
- sentence 198 `OKかどうか聞いてみた。`:
  - **warn**: lemma OK not in JMdict-common (may be in full)
- sentence 210 `母さんはロックはぴんとこないという。`:
  - **warn**: lemma ぴん not in JMdict-common (may be in full)

---
## Sentence validation (§7)

Validated 226 sentences — **0 errors, 21 warnings**, 209 clean.
- sentence 12 `大学を出てから10年になります。`:
  - **warn**: lemma 10 not in JMdict-common (may be in full)
- sentence 20 `１１時になっているよ。`:
  - **warn**: lemma 11 not in JMdict-common (may be in full)
- sentence 35 `人をあざわらうのはよくない。`:
  - **warn**: lemma あざわらう not in JMdict-common (may be in full)
- sentence 77 `とりあえず、あたりさわりのない話をしておいたよ。`:
  - **warn**: lemma あたりさわり not in JMdict-common (may be in full)
- sentence 79 `１万円でたりる？`:
  - **warn**: lemma 1万 not in JMdict-common (may be in full)
- sentence 81 `ログアウトするんじゃなかったよ。`:
  - **warn**: lemma ログアウト not in JMdict-common (may be in full)
- sentence 83 `10ヶ国語を話せたらどんなにかっこいいだろう！`:
  - **warn**: lemma 10 not in JMdict-common (may be in full)
  - **warn**: lemma 話せる not in JMdict-common (may be in full)
- sentence 91 `５月は４月のあとにくる。`:
  - **warn**: lemma 5 not in JMdict-common (may be in full)
  - **warn**: lemma 4 not in JMdict-common (may be in full)
- sentence 111 `ここに座ってトムを待つことにするよ。`:
  - **warn**: lemma トム not in JMdict-common (may be in full)
- sentence 112 `やっぱりべーラと乗馬しに行くことにするよ。`:
  - **warn**: lemma べ not in JMdict-common (may be in full)
  - **warn**: lemma ラ not in JMdict-common (may be in full)
- sentence 118 `猫もしゃくしも外国へ行きたがる。`:
  - **warn**: lemma しゃくし not in JMdict-common (may be in full)
- sentence 133 `５０００円ばかりもっている。`:
  - **warn**: lemma 5000 not in JMdict-common (may be in full)
- sentence 153 `１度に２つの事をしようと思うな。`:
  - **warn**: lemma 1度 not in JMdict-common (may be in full)
  - **warn**: lemma 2 not in JMdict-common (may be in full)
- sentence 165 `やぶへびを出すな。`:
  - **warn**: lemma やぶへび not in JMdict-common (may be in full)
- sentence 166 `おくびにも出すな。`:
  - **warn**: lemma おくび not in JMdict-common (may be in full)
- sentence 198 `OKかどうか聞いてみた。`:
  - **warn**: lemma OK not in JMdict-common (may be in full)
- sentence 210 `母さんはロックはぴんとこないという。`:
  - **warn**: lemma ぴん not in JMdict-common (may be in full)
