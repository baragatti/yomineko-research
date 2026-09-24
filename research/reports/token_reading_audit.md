# Token reading audit (measurement only)

> Nothing was applied. Inputs: the HEAD bank (`corpus/sentences/bank.json` @ `087fa123`), a sqlite3 backup-API snapshot of `db/corpus.sqlite`, `token_link_audit.json` (relink/unlink rows minus the mechanical sample's `exclude_patterns`) and the `token_link_rulings-*.json` resolved by their `.verdict.json`. The only repo files this unit writes are this report and `research/derived/pending/token_reading_audit.json`.

## 0. Answer

| | count |
|---|---:|
| token rows (one per token whose stored reading is wrong in context) | **310** |
| mechanical (rule-certain) | **295** |
| review (needs a human) | **15** |
| sentences touched | 286 (272 with mechanical rows only) |
| token romaji that change | 310 (neighbour tokens whose romaji changes at the boundary: 0) |
| rows with A-mode sub-tokens to re-split | 2 (by hand: 0) |
| unresolved rows (`new_reading` holds `\|`) | 0 |
| I2 / I3 held before on the touched sentences | 285/286 / 285/286 |
| I2 / I3 after re-deriving kana and romaji from the tokens | 286/286 / 286/286 |
| replay guard on the DB snapshot (token still has surface + old reading) | 310/310 match |
| dismissed candidates / link suspects (reading right, link wrong) | 9 / 21 |

By rule:

| rule | mechanical | review |
|---|---:|---:|
| `counter` | 131 | 3 |
| `nani` | 85 | 0 |
| `verified-link` | 61 | 4 |
| `nani-itsu` | 5 | 5 |
| `number-digitwise` | 5 | 2 |
| `juu-throughout` | 5 | 0 |
| `ruling-text` | 3 | 0 |
| `verified-pattern` | 0 | 1 |

The 何 rows are the biggest single word (85 of 85 are stored なん where the context is なに: 何か ×32, 何も ×15, 何が ×11, 何を ×9, bare 何？ ×6, 何+verb ×3 …). The counter rows are mostly Sudachi reading full-width digits one by one (２０ にれい, １００ いちれいれい, １９６０ いちきゅうろくれい) and missing sound changes (一分 いちふん, 一週間 いちしゅうかん, 九時 きゅうじ, ２つ ふつつ, ２本 にぽん, 四人 よんにん).

## 1. How the candidates were found

1. **Rules first** (`nani`, `nani-itsu`, `counter`, `number-digitwise`, `juu-throughout`). They look only at the token and its neighbours, never at the link, so they catch errors the link audit could not see.
2. **Link vs stored reading.** Every linked kanji/digit token (23,116) was compared with its record's kana (JMdict kana forms included; rendaku only after a content word, sokuon at the end, okurigana aligned for inflected forms). A mismatch is a reading row **only when the link itself was verified** (a token_link ruling, or the `karada-written-身体` census). Every unverified mismatch turned out to be the reverse, a right reading on a wrong link, and is listed as a link suspect, not a row: 行っ→行う ×5, 入っ in 気に入る, 空い→開く, 側 そば, 後 のち in 晴れ後曇り, 一 ひと in 一月 (ひとつき), 熱 あつ in 心熱けれど. One exception, 何時まで開いてますか (ひらい), fails exactly like the verified 開く[あく] rulings and is a `verified-pattern` review row.
3. **Rulings as tie-breakers.** When a verified ruling on the same token names the proposed reading, a review row is upgraded. When it names the stored reading, the row is dropped (何にする なん). Rulings that call the stored reading equally valid are dismissed: 昨夜 さくや ×8 stays さくや, and the fact that the registry has no さくや kana is a registry gap.
4. **Census of the siblings.** The verified pairs (米 べい, 種 しゅ, 開く ひらく, 年 ねん, 方 ほう, 金 きん, 数 すう, 下 もと, 市場 しじょう …) were checked across the whole bank. The siblings outside the rulings are right in their own context (金の時計 きん, 法の下で もと, 市場の２０% しじょう, 花が開く ひらく, 年に一度 ねん, 〜た方がいい ほう). None was added.

**tatoeba-8672817** (一日または二日ください). Its stored 一/いち 日/にち and 二/ふつ 日/か are right: いちにち または ふつか. The problem there is the link (二 → 二[に]), so no reading row.

## 2. What a fix moves

**Sentence kana and romaji (I2/I3).** Each touched sentence gets `kana_new` = concat(new C readings), and `romaji_new` = concat(token romaji). Token romaji is recomputed with `corpus_romaji()` (the house romanizer in `scripts/fable5_sentences_render_diff.py`) only for the changed token, and for its left neighbour when their shared boundary changes; every other token keeps its stored value. 0 neighbour tokens change. One sentence already had the corrected kana at sentence level while its token disagreed (sent:gen-9f80f08cc644), so there the fix repairs a standing I2/I3 break.

| consumer | what moves |
|---|---|
| lesson bodies, `<sentence show="furigana">` | 13 display pairs in 10 lessons render the new reading as furigana (no file edit, the renderer reads token readings) |
| lesson SRS card examples | 45 cards use an affected sentence as their example. None of them teaches the old reading's record, so the furigana changes and the card stays valid |
| lesson exercises citing an affected sentence | 18 citations; none stores the old reading as kana |
| listening / TTS | 3 `listening_reply` items speak an affected sentence (lr:n3:tatoeba-9979575, lr:n4:tatoeba-2552450, lr:n5:tatoeba-2633467), all `audio: pending`: the voice-over must read the new kana. 27 speak units cite affected sentences (say_now[] 12, shadowing[] 12, srs 12, fluency 15, production[] 8, drills[] 2), also `audio: pending` |
| speak production keys | **28 `accepted_variants` strings** in 7 units are copies of the OLD sentence kana (えいがはいつからですか, たいちゅうのきんにくがいたいです, このへやにごれいにんは…). After the fix they reject the right answer until `build_speaking_path.py` is re-run |
| exam items on affected sentences | 24 (n3_context_fill 4, n3_grammar_form 4, n3_listening_reply 1, n3_sentence_order 2, n4_context_fill 2, n4_grammar_form 5, n4_listening_reply 1, n4_sentence_order 1, n5_context_fill 2, n5_listening_reply 1, n5_sentence_order 1). Keys are written forms, not readings, except: |
| &nbsp;&nbsp;`reading_link_ok` flip | `cf:n5:3820:1341` (sent:tatoeba-2633467, 何飲みたい？) is keyed on vocab:2846738 何[なん]; after the fix the token reads なに and `exam_rules.reading_link_ok` rejects it, so the next `build_exam_banks.py` drops or rekeys it |
| `kanji_reading` items | 12 items have a stem this audit re-reads (下, 体, 市場, 年, 数, 方, 米, 金, 鳥). Their keys come from the vocab record, not the token; 12/12 keys already equal the corrected reading (いちば, かず, かた, かね, からだ, こめ, した, とし, とり) and 0 cite an affected sentence. Nothing moves |
| items that cite the old reading's record next to a re-read sentence | 3: `cf:n5:3820:1341` cites vocab:2846738 何[なん] but sent:tatoeba-2633467 now reads なに; `cj:n3:2400:polite` cites vocab:1365860 辛い[つらい] but sent:gen-9f80f08cc644 now reads からい; `cj:n4:820:masu` cites vocab:1202440 開く[ひらく] but sent:gen-4e4cde4d126f now reads あき |
| token links after the fix | 16 rows leave the token on a record that no longer reads that way: vocab:1188760 何時[いつ] ×10, vocab:1160790 一[いち] ×4, vocab:2083100 日[にち] ×1, vocab:1464250 日中[にっちゅう] ×1. No same-headword sibling reads the new way (no 何時[なんじ], 一[ひと], 一日中 record), so these are registry/link follow-ups, not blockers |
| kanji registry `example_sentences` | 165 references to affected sentences; kanji-level lists, not bound to a reading |

## 3. Review rows

| sentence#pos | surface | stored → proposed | why review |
|---|---|---|---|
| sent:tatoeba-11709247#0 | 308 | さんれいはち → さんびゃくはち | 308+便: counter table (plain) -> さんびゃくはち+びん; may be an identifier read digit by digit |
| sent:tatoeba-1171888#0 | 何時 | なんどき → なんじ | translation: 'how late are you open?' / 'fica aberto até que horas?' |
| sent:tatoeba-1171888#2 | 開い | ひらい → あい | bank link vocab:1586270 開く[あく] fails exactly like the verified rulings on this record; kanji core 開 reads ひら here; recor |
| sent:tatoeba-123906#2 | 何時 | いつ → なんじ | translation: 'when does it arrive?' / 'a que horas é a chegada?' |
| sent:tatoeba-142966#3 | 何時 | いつ → なんじ | translation: 'what is the right time?' / 'que horas são exatamente?' |
| sent:tatoeba-146221#2 | 綿 | わた → めん | ruling-verified link vocab:1533330 綿[めん]; surface is the record's written form; record reads めん |
| sent:tatoeba-172526#1 | 何時 | いつ → なんじ | translation: 'have you got the time?' / 'você sabe que horas são?' |
| sent:tatoeba-183844#0 | 管 | かん → くだ | ruling-verified link vocab:2868440 管[くだ]; surface is the record's written form; record reads くだ |
| sent:tatoeba-186679#4 | １１９ | いちいちきゅう → ひゃくじゅうきゅう | １１９ read digit by digit (いちいちきゅう) before 'に'; identifier context |
| sent:tatoeba-186687#4 | １１９ | いちいちきゅう → ひゃくじゅうきゅう | １１９+番: counter table (plain) -> ひゃくじゅうきゅう+ばん; may be an identifier read digit by digit |
| sent:tatoeba-186715#5 | １１９ | いちいちきゅう → ひゃくじゅうきゅう | １１９+番: counter table (plain) -> ひゃくじゅうきゅう+ばん; may be an identifier read digit by digit |
| sent:tatoeba-189309#2 | 何時 | いつ → なんじ | translation: 'when does the movie start?' / 'o filme começa a que horas?' |
| sent:tatoeba-210733#3 | 玩具 | がんぐ → おもちゃ | ruling-verified link vocab:1217070 玩具[おもちゃ]; surface is the record's written form; record reads おもちゃ |
| sent:tatoeba-78961#3 | １００３ | いちれいれいさん → せんさん | １００３ read digit by digit (いちれいれいさん) before 'です'; identifier context |
| sent:tatoeba-79393#3 | 他 | た → ほか | ruling-verified link vocab:1203260 他[ほか]; surface is the record's written form; record reads ほか |

## 4. 30 samples

| class | rule | sentence#pos | jp | token | stored → new | romaji |
|---|---|---|---|---|---|---|
| review | counter | sent:tatoeba-186687#4 | 火事の際は１１９番に電話してください。 | １１９ | いちいちきゅう → ひゃくじゅうきゅう | ichiichikyuu → hyakujuukyuu |
| mechanical | counter | sent:tatoeba-74146#7 | それが高1の時だから17年が経ちました。 | 17 | いちなな → じゅうなな | ichinana → juunana |
| mechanical | counter | sent:tatoeba-109862#2 | 彼は一分の差で電車に乗り遅れた。 | 一 | いち → いっ | ichi → ip |
| mechanical | counter | sent:tatoeba-161911#2 | 私は６０ページ読んだが、一方彼は１０ページしか読んでいない。 | ６０ | ろくれい → ろくじゅっ | rokurei → rokujup |
| mechanical | counter | sent:tatoeba-4891#0 | 一週間でどれほどのことが学べるか、自分でもびっくりするはずだよ！ | 一 | いち → いっ | ichi → is |
| mechanical | counter | sent:tatoeba-235574#0 | ２０年とは長い年月だ。 | ２０ | にれい → にじゅう | nirei → nijuu |
| mechanical | counter | sent:tatoeba-79185#4 | 郵便は１日１回配達される。 | １ | いち → いっ | ichi → ik |
| mechanical | counter | sent:tatoeba-12096683#0 | 10月生まれです。 | 10 | いちれい → じゅう | ichirei → juu |
| mechanical | counter | sent:tatoeba-160196#7 | 私はその犬に肉を２切れやった。 | ２ | に → ふた | ni → futa |
| mechanical | nani | sent:tatoeba-85041#5 | 不平を言う理由は何も無い。 | 何 | なん → なに | nan → nani |
| mechanical | nani | sent:tatoeba-188146#0 | 何かいい知恵がないものかね。 | 何 | なん → なに | nan → nani |
| mechanical | nani | sent:tatoeba-1192382#6 | 水道の水おかしいよ。何かいい匂いがする。 | 何 | なん → なに | nan → nani |
| mechanical | nani | sent:tatoeba-187926#0 | 何か深刻なことなのですか。 | 何 | なん → なに | nan → nani |
| mechanical | nani | sent:tatoeba-187939#0 | 何か食べるものがほしい。 | 何 | なん → なに | nan → nani |
| mechanical | nani | sent:tatoeba-9979575#0 | 何か聞こえる？ | 何 | なん → なに | nan → nani |
| mechanical | nani | sent:tatoeba-170380#5 | 妻がいないと何かと不自由だ。 | 何 | なん → なに | nan → nani |
| review | verified-link | sent:tatoeba-183844#0 | 管から水が吹き出した。 | 管 | かん → くだ | kan → kuda |
| mechanical | verified-link | sent:gen-60bf9693e167#2 | 傘の柄が壊れた | 柄 | がら → え | gara → e |
| mechanical | verified-link | sent:tatoeba-3496750#0 | 開きそうにないわ。 | 開き | ひらき → あき | hiraki → aki |
| mechanical | verified-link | sent:tatoeba-125513#2 | 庭に種をまきました。 | 種 | しゅ → たね | shu → tane |
| mechanical | verified-link | sent:tatoeba-10206910#2 | 全ては金次第だよ。 | 金 | きん → かね | kin → kane |
| mechanical | verified-link | sent:tatoeba-148447#2 | 酒は米で作ります。 | 米 | べい → こめ | bei → kome |
| mechanical | verified-link | sent:gen-46f095053830#6 | ここを押せばドアが開く | 開く | ひらく → あく | hiraku → aku |
| review | nani-itsu | sent:tatoeba-172526#1 | 今何時か分かりますか。 | 何時 | いつ → なんじ | itsu → nanji |
| mechanical | nani-itsu | sent:tatoeba-8587104#0 | 何時なのか見当もつかない。 | 何時 | いつ → なんじ | itsu → nanji |
| review | number-digitwise | sent:tatoeba-78961#3 | 予約番号は１００３です。 | １００３ | いちれいれいさん → せんさん | ichireireisan → sensan |
| mechanical | number-digitwise | sent:tatoeba-10674421#2 | 市場の２０%を占めています。 | ２０ | にれい → にじゅう | nirei → nijuu |
| mechanical | juu-throughout | sent:tatoeba-211346#4 | その銀行は国中いたるところに支店を持っています。 | 中 | ちゅう → じゅう | chuu → juu |
| mechanical | ruling-text | sent:gen-09a4a8300a89#2 | 先生に直に話した | 直 | ちょく → じか | choku → jika |
| review | verified-pattern | sent:tatoeba-1171888#2 | 何時まで開いてますか。 | 開い | ひらい → あい | hirai → ai |

## 5. Dismissed

- sent:gen-438f1c965463#0 昨夜 (stored さくや): verified ruling says the stored reading is also valid: keep: 昨夜 'last night' is written the same for ゆうべ and さくや; the ゆうべ record is the meaning in context and no さくや record exists (token reading shoul
- sent:gen-f96ffb89a13e#0 昨夜 (stored さくや): verified ruling says the stored reading is also valid: keep 昨夜[ゆうべ]: same word and meaning (last night); ゆうべ is a valid reading of the text and no さくや record exists
- sent:gen-fb1205e26730#0 昨夜 (stored さくや): verified ruling says the stored reading is also valid: 昨夜 = last night; same lexeme whether read ゆうべ or さくや, keep 昨夜 record
- sent:tatoeba-156690#2 昨夜 (stored さくや): verified ruling says the stored reading is also valid: keep: 昨夜 'last night' is written the same for ゆうべ and さくや; the ゆうべ record is the meaning in context and no さくや record exists (token reading shoul
- sent:tatoeba-169606#0 昨夜 (stored さくや): verified ruling says the stored reading is also valid: 昨夜 = last night; both ゆうべ and さくや are valid readings of the same word and there is no さくや record: keep
- sent:tatoeba-169685#0 昨夜 (stored さくや): verified ruling says the stored reading is also valid: 昨夜 'last night': the registry record 昨夜/ゆうべ is the same word (さくや is an alternate reading with no own record); the link stands
- sent:tatoeba-169713#0 昨夜 (stored さくや): verified ruling says the stored reading is also valid: keep 昨夜[ゆうべ]: same word and meaning (last night); ゆうべ is a valid reading of the text and no さくや record exists
- sent:tatoeba-8728875#0 昨夜 (stored さくや): verified ruling says the stored reading is also valid: keep: 昨夜 'last night' is written the same for ゆうべ and さくや; the ゆうべ record is the meaning in context and no さくや record exists (token reading shoul
- sent:tatoeba-232235#2 何 (stored なん): rule nani proposed なに but the verified ruling keeps なん: 何にする "what will you have" (なんにする) is read なん; 何[なん] record

## 6. Limits

- Unlinked tokens are checked only by the rules. A kanji token with no record and a wrong reading that no rule and no ruling covers is not found.
- 何+で (なんで/なにで), 何駅, 十分 without 'minutes' in the translation, and 一日 without a date signal are left as stored on purpose.
- 〜中 じゅう is limited to 体/家/国/部屋/一日/世界/日本/町/学校/一年/一晩. 午前中 and 授業中 are ちゅう and are not touched.
- The counter table accepts both forms where both are standard (はちほん/はっぽん, じゅっ/じっ, ななねん/しちねん). 時 and 月 take only しち for 7 and く for 9.
- ruling text is parsed for the reading it names; the rows it upgraded or dropped carry the ruling in `ruling`.
