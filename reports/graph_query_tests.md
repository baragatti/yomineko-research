# §1.7 cross-cutting graph query tests

_Proves the corpus is one queryable graph (acceptance #10). With the sentence bank still small (P5 in progress), sentence-dependent results are sparse, but every JOIN path resolves._

## Q1 — N5 sentences containing a godan verb (family) AND the を particle
```sql
SELECT DISTINCT s.jp FROM sentence s
JOIN particle p   ON p.sentence_id = s.id AND p.particle = 'を'
JOIN sentence_vocab sv ON sv.sentence_id = s.id
JOIN family_member fm  ON fm.member_type='vocab' AND fm.member_id = sv.vocab_id
JOIN family f          ON f.id = fm.family_id AND f.slug = 'grp:godan'
WHERE s.level = 'n5'
```
**52 rows.** PASS ✓
- 大学を出てから10年になります。
- きのう友達におもしろいニュースを聞きました。
- 今ちょうど橋を渡ってる電車を見て。
- ちょっと暑いのでジャケットを脱ぎます。
- タバコを吸うのって、これが初めて。
- 本当にストーブを消した？
- 鉛筆をなくした。
- そっと階段をのぼった。

## Q2 — vocab using kun-reading た.べる of 食 (+ #dissected sentences)
```sql
SELECT v.headword, (SELECT count(*) FROM sentence_vocab sv WHERE sv.vocab_id=v.id) FROM vocab v WHERE v.id IN (?)
```
**1 rows.** PASS ✓
- 食べる — 89 sentences

## Q3 — 言-component kanji across N5–N4, ordered by frequency
```sql
SELECT k.character, k.level, k.freq_rank FROM kanji_component kc
JOIN kanji k ON k.id = kc.kanji_id
WHERE kc.component = '言' AND k.level IS NOT NULL
ORDER BY k.freq_rank IS NULL, k.freq_rank
```
**6 rows.** PASS ✓
- 言 (n4, freq 83)
- 話 (n5, freq 134)
- 計 (n4, freq 228)
- 語 (n5, freq 301)
- 試 (n4, freq 392)
- 読 (n5, freq 618)

## Q4 — grammar points contrasting with は (+ #example sentences)
```sql
SELECT g2.key, g2.label_pt,
       (SELECT count(*) FROM sentence_grammar sg WHERE sg.grammar_id = g2.id)
FROM grammar_related gr
JOIN grammar_point g1 ON g1.id = gr.grammar_id AND g1.key = 'wa-topic-marker'
JOIN grammar_point g2 ON g2.id = gr.related_grammar_id
WHERE gr.relation = 'contrast'
```
**1 rows.** PASS ✓
- ga — None (8 sentences)

