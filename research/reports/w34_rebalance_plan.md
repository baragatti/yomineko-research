# W34 strand rebalance: mechanical plan (not applied)

**Unit w34_rebalance, 2026-09-23.** Files only. Measured on `git HEAD` (`f9de8e2c`) exports plus a
`sqlite3 backup` snapshot of `db/corpus.sqlite`, with `validate_speak_strands.py` /
`speak_path_common.py` and the three sibling speak gates run against a scratch tree. The builder was
re-run only as a scratch copy. Output: `research/derived/pending/w34_rebalance.json` (moves, per-unit
pre/post state, builder rule). Nothing authored: every added item is an existing bank sentence with its
existing pt-BR translation.

## 1. Re-measure after W32/W30

W32/W30 did not move the strand picture: 12/12 stages out of band, path-wide
25.4 / 6.3 / 55.9 / 12.4 (input / output / language-focused / fluency) over 3,404 components against
R78's 15 / 30 / 25 / 30. Each unit is built from the same template (6 say_now + 6 shadowing,
3 production, ~23 language-focused, 6 fluency), so every stage sits in the same place. The gap is
**output (-24 pt) and fluency (-18 pt)**, with language-focused 30 pt over. Input is only 10 pt over.

## 2. Which levers are mechanical, and which are not

| lever | usable? | why |
|---|---|---|
| move say_now phrases between stages | no effect | every stage has the same template, so a phrase moves numerator and denominator together |
| drill examples into production/fluency | **not eligible** | `validate_speaking_path.py` binds production (R44) and fluency (R79a) to say_now phrases of an EARLIER unit; drill examples are not |
| drop drills / kanji / words | not mechanical | deletes language-focused content (R80 drills, the kanji and vocab contract), an owner decision |
| **prior say_now -> more production** | yes | R44-legal by construction, prompt = existing pt-BR translation, variants from `variants()` |
| **prior say_now -> more fluency** | yes | zero-new-token against the unit's known set, same selector |
| fluency item -> production in the same unit | yes, as a swap | the production selector ranks first; the fluency block refills from the rest of the pool |

Every added sentence was already placed as say_now by `build_speaking_path.py`, so it passed
`speak_filter` (register, `polite-request-nasai`, blocklist) at that point. The production selector
checks it again. The stage known sets hold because fluency is zero-new-token by the builder's own
`eligible()` check, and production only draws from phrases taught in earlier units.

## 3. The plan: per-stage caps, with a fluency floor

The only change is to `PRODUCTION_PER_UNIT` / `FLUENCY_PER_UNIT` in `build_speaking_practice.py`.
They become per-stage caps, and the selection order stays the same, so the 213 shipped production
items stay a prefix of each unit's new list. One rule is added. **Production grows only while the
fluency block keeps the item count it has at 3/6.** Without that rule, arrival-02's 6-phrase pool is
eaten whole and the unit loses its fluency block (a `validate_speaking_path` FAIL, caught on the first
pass). The search picked the smallest caps, as the lowest production + fluency sum, that put a stage
in band without moving any (stage, strand) further from budget.

| stage | caps P/F | before in/out/lf/flu (worst) | after in/out/lf/flu (worst) |
|---|---|---|---|
| arrival | 13/9 | 30.1 / 6.3 / 52.3 / 11.3 (27.3) | 26.4 / 16.5 / 45.8 / 11.4 (**20.8, out**) |
| shopping | 17/16 | 27.6 / 6.9 / 51.7 / 13.8 (26.7) | 18.6 / 26.4 / 34.9 / 20.2 (9.9) |
| eating | 15/21 | 25.8 / 6.5 / 54.8 / 12.9 (29.8) | 16.3 / 20.4 / 34.7 / 28.6 (9.7) |
| getting_around | 16/23 | 24.9 / 6.2 / 56.4 / 12.5 (31.4) | 15.4 / 20.5 / 34.8 / 29.4 (9.8) |
| lodging | 17/24 | 24.4 / 6.1 / 57.3 / 12.2 (32.3) | 14.8 / 20.9 / 34.7 / 29.6 (9.7) |
| about_you | 17/26 | 23.9 / 6.0 / 58.1 / 12.0 (33.1) | 14.3 / 20.2 / 34.7 / 30.9 (9.8) |
| time_plans | 15/22 | 25.7 / 6.4 / 55.0 / 12.9 (30.0) | 16.0 / 20.0 / 34.7 / 29.3 (10.0) |
| health | 15/20 | 25.9 / 6.5 / 54.7 / 12.9 (29.7) | 16.6 / 20.7 / 35.0 / 27.6 (10.0) |
| past_stories | 16/23 | 24.7 / 6.2 / 56.7 / 12.4 (31.7) | 15.3 / 20.4 / 35.0 / 29.3 (10.0) |
| politeness | 18/28 | 23.1 / 5.8 / 59.6 / 11.5 (34.6) | 13.5 / 20.2 / 34.8 / 31.5 (9.8) |
| opinions | 15/21 | 25.8 / 6.5 / 54.8 / 12.9 (29.8) | 16.3 / 20.4 / 34.7 / 28.6 (9.7) |
| real_talk | 17/24 | 24.0 / 6.0 / 58.0 / 12.0 (33.0) | 14.8 / 20.9 / 34.8 / 29.5 (9.8) |

**Stages in band: 0 -> 11.** Path-wide: 16.1 / 20.7 / 35.4 / 27.9 over 5,380 components.
Moves: 660 `add_production`, 240 `swap_fluency_to_production`, 1,349 `add_fluency`, and 31
`drop_fluency`. Every one of the 31 dropped items sits in the previous unit's (now larger) block, so
the builder's anti-repeat rule sends it to the back of the queue. Totals: production 213 -> 1,113,
fluency 423 -> 1,501. Offline replay and scratch builder agree on all 72 units.

Gates on the rebuilt scratch tree:

| gate | before (HEAD) | after |
|---|---|---|
| strands R78 | 12/12 out, 0 FAIL | 1/12 out (arrival), 0 FAIL, 48 of 48 (stage, strand) distances shrink |
| spiral R83 fluency reach (arrival / shopping / eating / getting_around / lodging / about_you) | 0 / 20 / 5 / 4 / 0 / 18 | 0 / 70 / 14 / 22 / 50 / 164 |
| spiral late units reached | 6 / 29 / 8 / 13 / 3 / 16 | 6 / 35 / 16 / 25 / 10 / 33 |
| near-duplicates, say_now gate (R86 / §6b) | 21 | 21 (say_now untouched) |
| near-duplicates inside one production list or fluency block (not gated) | 3 | **48** |
| `validate_speaking_path` | 0 FAIL, 1 warn | 0 FAIL, 1 warn (same arrival-02 R79d) |

## 4. What this costs (read before applying)

- **Units grow from ~47 to ~75 components** (range 12 to 92). The balance comes entirely from adding
  retrieval, and none of the language-focused load comes off.
- **Repetition.** On average, 60% of a unit's production list repeats the previous unit's list in the
  same stage, because the selector ranks same-stage phrases by recency. After the change, 1,113
  production items break down as 777 same-stage, 139 on-topic and 197 review.
- **Look-alikes inside a block** go from 3 to 48 pairs (same metric and threshold as
  `validate_speak_duplicates`). The say_now gate does not see them.
- **No margin.** Language-focused lands at 34.7 to 35.0 and three stages sit at exactly 10.0. One more
  drill or checkpoint in any of those stages takes it back out of band. Adding +1 to each cap buys
  margin.

The data show R78 as a component-count ratio can be met, but only by inflating review. Whether R78
should count components or time on task (Nation's four strands are about time) is a design question
for the owner. A cheaper structural lever, fewer kanji_recognition (6 per unit, all language-focused),
is also an owner call, not something to settle mechanically.

## 5. What cannot be balanced without new sentences

- **arrival** (stage 1): out of band on all four strands even at the best caps (worst 20.8). Unit 01
  has no prior phrases. Units 02 to 05 draw only on arrival's own earlier phrases, and few of those are
  zero-new-token, so fluency stays at 31 slots (11.4%). Getting in band would take about **27 more
  production and 57 more fluency slots** that the prior-only rules (R44, R79a) cannot supply in the
  first stage. Closing it needs more short, fully-known arrival phrases taught in units 01 to 03 (new
  sentences, which also add input), or a rule decision for stage 1. W32's pending arrival core
  (`SURVIVAL_CORE_PENDING`) is the natural source.
- **Pool-limited but in band**: shopping-01 to 04 reach cap 17 on production and fall short of 16 on
  fluency (9, 11, 12 and 14). The stage is still in band.
- Every other stage is balanced from existing material alone.

## 6. Drift the apply unit must know about (not caused by this plan)

The live DB has moved past HEAD's export. Re-running the practice builder at the SHIPPED caps against
the snapshot already changes drills or patterns in 8 units (time_plans-03, past_stories-03, opinions-06,
real_talk-01/02/04/05/06). That alone fails 3 strand ratchets (real_talk input 9.0 -> 9.3, time_plans
fluency 17.1 -> 17.2, time_plans language-focused 30.0 -> 30.3) and the spiral drills denominator
(420 -> 417). The plan leaves drills alone. After the rebalance the strand ratchets are clean, but the
spiral denominator FAIL persists until it is re-recorded.

## 7. Apply

Durable form: the per-stage caps and the fluency-floor rule in `build_speaking_practice.py`
(`builder_rule` in the JSON), rebuild, then `--record` all three speak baselines and re-run
`validate_srs_decks.py` (production cards key off say_now, so they are unaffected, but check).
`units[*].precondition` lets a replay refuse on drift. A replay without the builder change is
overwritten by the next export. Everything stays Layer C, `needs_review`.
