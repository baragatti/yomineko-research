# `api_contract.md` — the read API a production app consumes

**Status:** design of record for the read surface. It is *derived from* [`contracts/manifest.json`](../contracts/manifest.json)
and adds nothing the manifest does not already know: every route below is a projection of a manifest
entity, addressed by that entity's `stable_id_field`, validated by that entity's `schema`. Where this
document and the manifest disagree, the manifest wins and this document is the bug.

Written for readiness finding **G5** ("No API contract, and the one consumer bypasses the one we have"),
alongside the W41 rewrite of `prototype/scripts/sync-data.mjs`, which now reads the manifest instead of
hardcoding its own globs. The prototype is the *first* consumer of this contract, not the definition of
it: it ships the whole corpus as bundled JSON because it is a prototype. This document describes the
served version.

**Out of scope.** Physical storage, hosting, auth implementation and the user-state datastore are
**D8/W43**. Everything under §8 is a *logical* contract: shapes, addresses and semantics, no tables.

---

## 1. What the manifest gives, and what this document adds

`contracts/manifest.json` already answers four of the five questions an API needs:

| the manifest says | field | the API uses it for |
|---|---|---|
| where the records live | `files` (glob) | which store backs the collection |
| how they are packed | `packing` — `list` / `single` / `map` | whether the collection is a list or a keyed document |
| what addresses a record | `stable_id_field`, else `natural_key` | the path parameter of the item route |
| which prefix that address wears | `id_namespace` | route-parameter qualification (`食` → `kanji:食`) |
| how many exist | `records` | a served count that can be checked, not guessed |
| which contract validates it | `schema` | the payload schema named on every route below |

The fifth question — *what shape does a learner get* — is the one this document answers: §3 (the
projection), §4 (locale), §5–7 (the routes), §9 (redirects).

**Two entity classes, two halves of the API.** The manifest's 23 `content` entities are the read
surface (§5–7); its 7 `runtime` entities are the write surface (§8), specified by
[`design/user_state.md`](user_state.md). The class is declared in each schema's `x-yomineko` block, so
the API mounts read routes and write routes from the same file without a hand-kept list.

---

## 2. Conventions

**Base and versioning.** `/v1` is the *contract* version — it changes only when a payload shape breaks.
The *data* version is the release identity in §3 and moves on every export; the two are independent.

**Addressing.** Every record is addressed by its prefixed stable id (`kanji:食`, `vocab:1580640`,
`gram:te-hoshii`, `les:n5-saudacoes-01`). Two rules, both from the manifest's `id_convention`:

- The integer `id` present on `capability`, `course`, `exam_item`, `exercise_*`, `family`, `grammar`,
  `kana`, `kanji`, `lesson`, `speak_*`, `topic` and `vocab` is a **storage row number**. It is not
  stable across a rebuild and **must never appear in a URL or a response**. §3 strips it.
- A path parameter carries the identifier without its prefix, because the route already implies the
  namespace: `GET /v1/kanji/食` addresses `kanji:食`. The server qualifies with `id_namespace`; a
  client that sends the full stable id gets the same record. Response bodies always carry the **full**
  stable id, so a client never has to reassemble one.

**Collections.** `GET` on a collection returns

```jsonc
{ "build": { "date": "…", "git_head": "…" },   // §3
  "locale": "pt-BR",                            // §4, the locale actually served
  "total": 2131,                                // matches manifest.entities[].records for an unfiltered list
  "next": "…opaque cursor…" | null,
  "items": [ /* projected records, §3 */ ] }
```

Cursor pagination, never offset: the corpus is re-exported wholesale and an offset would silently skip
records across a build boundary. Default page 50, maximum 200. `total` on an unfiltered list is the
manifest's own `records` count for that entity, which makes a truncated store visible in one request.

**Items.** `GET` on an item returns the projected record itself, not an envelope; the build identity
travels in the `ETag` and `X-Yomineko-Build` headers (§3).

**Errors.** `application/problem+json`: `{ "type", "title", "status", "detail", "instance" }`.
`404` for an id that never existed, `301` + a redirect object for an id that *moved* (§9) — the two are
different facts and the API must not flatten them into one.

**Read-only.** Every route in §5–7 is `GET`. The corpus is built by this repository's pipeline and
reviewed through `research/derived/review_ledger.json`; there is no write path into it from the app.

---

## 3. Release identity, ETags, and the learner projection

### 3.1 The identity

`contracts/manifest.json` carries a `build` block: `date`, `git_head`, and one **content hash per
entity** over the bytes its glob matches. That is the version source for the whole read API.

| header / field | value | meaning |
|---|---|---|
| `X-Yomineko-Build` | `<date>+<git_head[:8]>` | which export this process is serving |
| `ETag` (collection) | `W/"<entity hash>"` | the entity's content hash — a weak validator, because the projection (§3.2, §4) is applied on top |
| `ETag` (item) | `W/"<entity hash>-<stable id>"` | changes when the entity's bytes change |
| `Cache-Control` | `public, max-age=0, must-revalidate` | content is immutable per build but the build moves |

A client sends `If-None-Match` and gets `304` for as long as the entity's bytes are unchanged. Because
the hash is **per entity**, re-exporting the sentence bank does not invalidate a cached kanji page.

`GET /v1/build` returns the whole `build` block plus the per-entity `records` counts — the release
identity as data, for a diagnostics screen and for a client that wants to purge selectively.

This is the *build-level* companion to `research/derived/review_ledger.json`, whose approvals are
anchored per record and per locale (D4). A build identity says which bytes shipped; the ledger says
which of them a human signed off. Neither substitutes for the other.

**The prototype already implements this half.** `prototype/scripts/sync-data.mjs` copies the manifest's
`build` block into `prototype/app/data/_build.json`; `corpus.server.ts` exports it as `build`; and
`scripts/validate/validate_prototype_sync.py` fails when those hashes drift from the manifest. A stale
sync is detectable by hash rather than by file count.

### 3.2 The learner projection

Records carry editorial apparatus a learner has no use for and a paying customer should not be handed.
The default projection **drops**:

| dropped | present on | why |
|---|---|---|
| integer `id` | 14 entities | a storage row number, not an address (§2) |
| `needs_review` | `exam_item`, `exercise_*`, `family`, `grammar`, `lesson`, `reading`, `speak_*` | review state is an editorial fact |
| `layer` | `exam_item`, `exercise_*`, `reading`, `speak_*` | provenance layer A/B/C is an editorial fact |
| `provenance`, `source` | `sentence`, `stroke_*`, `exam_item`, `exercise_*` | attribution belongs in `ATTRIBUTION.md` and on a licence screen, not in every record |
| `level_sources`, `level_agreement` | `grammar`, `kanji`, `vocab` | the consensus evidence behind a level tag (spec §1.5); `level` and `level_confidence` stay |
| answer keys | `exam_item.correct`, `exercise_*.correct` | **§7.3** — never served with the item |

`?fields=full` returns the unprojected record and requires an editorial scope; it is the review tool's
route, not the app's. `?fields=<comma list>` narrows further for list views.

---

## 4. Locale negotiation

Internals are language-agnostic; only content is localized ([`design/i18n.md`](i18n.md)). That splits
cleanly at the API boundary:

- **Never translated:** field names, enum values (`pos`, `inflection`, particle `function_type`, vocab
  `register`, card `kind`, FSRS `state`), stable ids, namespaces, level tags.
- **Always a locale object in storage:** `{"pt-BR": …, "en": …}` — `LocaleText` / `LocaleTextList` in
  `contracts/common.schema.json`.

**Negotiation.** `Accept-Language`, overridden by an explicit `?locale=`; the authenticated learner's
`user.locale` is the default when neither is sent. Resolution order: **requested locale → `pt-BR` →
`en`**, and the locale actually served is echoed in the collection envelope's `locale` field and in a
`Content-Language` header on every response. `pt-BR` is the only fully authored locale; `en` exists as
the Layer-A source and is present on a subset of fields, so an `en` request is a partial fill, not a
second product. A locale that does not exist is **not** a `406`: it resolves to `pt-BR` and says so in
`Content-Language`.

**Shape.** The API returns *resolved strings*, not locale objects — the app should not be re-running
the fallback chain per field. `?locale=*` returns the raw locale objects, for the review tool.

`Vary: Accept-Language` on every response, and the served locale is part of the cache key alongside the
ETag.

---

## 5. Route families — one per content entity

Every row is a manifest entity. `address` is its `stable_id_field` (or `natural_key`, marked †);
`schema` is the file that validates the payload. `?level=` is offered **only** where records actually
carry a `level` field — measured, not assumed.

### 5.1 Corpus layer

| entity | collection | item | address | `?level=` | schema |
|---|---|---|---|---|---|
| `kanji` | `GET /v1/kanji` | `GET /v1/kanji/{char}` | `slug` → `kanji:食` | yes | `kanji.schema.json` |
| `vocab` | `GET /v1/vocab` | `GET /v1/vocab/{id}` | `slug` → `vocab:1580640` | yes | `vocab.schema.json` |
| `grammar` | `GET /v1/grammar` | `GET /v1/grammar/{key}` | `slug` → `gram:te-hoshii` | yes | `grammar.schema.json` |
| `sentence` | `GET /v1/sentences` | `GET /v1/sentences/{id}` | `slug` → `sent:…` | yes | `sentence.schema.json` |
| `reading` | `GET /v1/readings` | `GET /v1/readings/{id}` | `slug` → `read:…` | yes | `reading.schema.json` |
| `family` | `GET /v1/families` | `GET /v1/families/{id}` | `slug` → `grp:godan` | no (has `spans_levels`) | `family.schema.json` |
| `kana` | `GET /v1/kana` | `GET /v1/kana/{id}` | `id` → `kana:hiragana-あ` | no | `kana.schema.json` |
| `kana_family` | `GET /v1/kana/chart` | — (packing `map`) | — | no | `kana_family.schema.json` |
| `conjugation` | — | `GET /v1/vocab/{id}/conjugation` | `slug` → the **vocab** slug | yes | `conjugation.schema.json` |
| `capability` | `GET /v1/capabilities` | `GET /v1/capabilities/{id}` | `id` → `cap:…` | yes | `capability.schema.json` |
| `capability_lesson_map` | `GET /v1/capabilities/lesson-map` | — (packing `map`) | — | no | `capability_lesson_map.schema.json` |
| `stroke_order` | — | `GET /v1/kanji/{char}/strokes?style=outline` | `character` † | no | `stroke_order.schema.json` |
| `stroke_lines` | — | `GET /v1/kanji/{char}/strokes?style=centerline` | `character` † | no | `stroke_lines.schema.json` |
| `stroke_kana` | — | `GET /v1/kana/{char}/strokes` | `char` † | no | `stroke_kana.schema.json` |

`conjugation` is addressed by the **vocab** slug, not by one of its own — its `id_namespace` is
`["vocab"]` and its `slug` field holds `vocab:2820690`. It is a per-vocab table, so it is served as a
sub-resource of the word rather than as a collection of its own.

The three stroke entities are separate manifest rows with separate licences (Kanji Alive CC BY 4.0
outlines, GlyphWiki centrelines, strokesvg OFL+MIT for kana). One route with a `style` parameter, three
schemas, three attributions. Public attributed data: **this is the one payload that may be sent to the
client** for the draw animation.

### 5.2 Courseware layer

The courseware references the corpus by id and never embeds it (spec §2), so these routes return ids,
and `?expand=` (§6.4) is how a client asks for the referenced records in one round trip.

| entity | collection | item | address | schema |
|---|---|---|---|---|
| `course_manifest` | `GET /v1/courses` | — (packing `single`) | — | `course_manifest.schema.json` |
| `course` | — | `GET /v1/courses/{id}` | `id` → `mod:pre-n5` | `course.schema.json` |
| `topic` | `GET /v1/courses/{id}/topics` | `GET /v1/topics/{id}` | `id` → `top:…` | `topic.schema.json` |
| `lesson` | `GET /v1/topics/{id}/lessons` | `GET /v1/lessons/{id}` | `id` → `les:…` | `lesson.schema.json` |
| `speak_path` | `GET /v1/speak` | — (packing `single`) | `id` → `course:…` | `speak_path.schema.json` |
| `speak_unit` | `GET /v1/speak/stages/{slug}/units` | `GET /v1/speak/units/{id}` | `id` → `speak:…` | `speak_unit.schema.json` |

`GET /v1/courses` is the manifest document itself (packing `single`), so it validates against
`course_manifest.schema.json` rather than against a list of `course.schema.json`. Same for
`GET /v1/speak`.

### 5.3 Not served

| entity | why |
|---|---|
| `review_ledger` | editorial. Per-record approval state, `reviewed_by`, `approved_at`. Behind the editorial scope, never on the learner API. Its glob also lives outside `corpus/`+`course/`, which is why `sync-data.mjs` skips it. |
| `exam_item`, `exercise_conjugation`, `exercise_role` | **not as collections** — see §7.3. Items reach a learner only through a sampled paper or drill set, with the answer key withheld. |

---

## 6. Cross-reference routes — the graph, not four lists

Spec §1.7 names four cross-cutting queries as design tests: *"If a reasonable query like these can't be
answered from stored links, the model is incomplete."* Each maps to a route, and each is answered from
edges the corpus actually stores.

### 6.1 The stored edges

| from | field | to |
|---|---|---|
| `kanji` | `example_words`, `example_sentences`, `families`, `components` | `vocab`, `sentence`, `family`, `kanji` |
| `vocab` | `kanji`, `families`, `senses[].pos` | `kanji`, `family` |
| `grammar` | `related`, `families`, `refs` | `grammar`, `family` |
| `sentence` | `grammar`, `tokens[].pos`, `particles[].particle`, `new_items` | `grammar`, corpus items |
| `family` | `members`, `spans_levels` | any entity |
| `lesson` | `needs`, `unlocks` | `kanji`, `vocab`, `grammar`, `lesson` |
| `capability` | `grammar_keys` | `grammar` |

Every edge is a stable id, so every one of these is traversable in both directions from stored data.

### 6.2 The four design tests as routes

| spec §1.7 query | route |
|---|---|
| N5 sentences containing a godan verb from the *daily-routine* family **and** the を particle | `GET /v1/sentences?level=n5&family=grp:godan&family=grp:<daily-routine>&particle=を` |
| every vocab item using the kun-reading た.べる of 食, with its dissected sentences | `GET /v1/kanji/食/vocab?reading=た.べる&expand=sentences` |
| all members of the 言-component kanji family across N5–N4, ordered by frequency | `GET /v1/families/grp:<言>/members?level=n5,n4&sort=freq_rank` |
| every grammar point that contrasts with は, with example sentences | `GET /v1/grammar/gram:<wa>/related?expand=sentences` |

### 6.3 The reverse edges, as first-class routes

| route | answers | schema of the payload |
|---|---|---|
| `GET /v1/kanji/{char}/vocab` | words that use this kanji | `vocab.schema.json` |
| `GET /v1/kanji/{char}/sentences` | its curated examples | `sentence.schema.json` |
| `GET /v1/vocab/{id}/sentences` | sentences containing the headword | `sentence.schema.json` |
| `GET /v1/grammar/{key}/sentences` | sentences tagged with the point | `sentence.schema.json` |
| `GET /v1/grammar/{key}/related` | contrast / confusion set | `grammar.schema.json` |
| `GET /v1/families/{id}/members` | the family's members, any entity | the member's own schema |
| `GET /v1/{entity}/{id}/lessons` | which lessons introduce it (`lesson.unlocks`, reversed) | `lesson.schema.json`, stub projection |
| `GET /v1/lessons/{id}/unlocks` | what the lesson introduces, resolved | the target's own schema |

Every one of these is a stored-link traversal. None is a text search; none needs a field the corpus
does not have.

### 6.4 `?expand=`

`?expand=sentences,vocab,kanji,grammar` inlines referenced records **one level deep**, at the same
projection and locale as the parent. Bounded per reference (default 5, `?expand_limit=` up to 20), so
a lesson page is one request instead of forty and no request can pull the whole bank.

---

## 7. Filters, sorting, and the two collections that are not collections

### 7.1 Filters

`?level=` (repeatable, `n5,n4`), `?family=` (repeatable, AND), `?pos=`, `?register=`, `?particle=`,
`?grammar=`, `?reading=`, `?contains=` (substring of `jp`, sentences only), `?common=true`. All values
are the corpus's own neutral English enums or stable ids — never localized strings, so a filter means
the same thing in every locale.

### 7.2 Sorting

`?sort=` over stored fields only: `freq_rank`, `strokes`, `level`, `order`, `importance_rank`,
`length_band`. Default per entity: course order for courseware, `freq_rank` for kanji and vocab,
`order` for everything with one, stable id otherwise. Ties break on stable id so paging is total.

### 7.3 Exam items and drills

`exam_item` (6,048), `exercise_conjugation` (18,524) and `exercise_role` (5,358) each carry a `correct`
field. They are **not** served as browsable collections, and the item route never returns the answer.

| route | returns |
|---|---|
| `POST /v1/exam/papers` | a sampled paper for a level: item ids, stems, distractors. No `correct`. Payload per item: `exam_item.schema.json` minus the answer key. |
| `POST /v1/exam/papers/{attempt}/grade` | grading happens server-side against the withheld key; the response carries the verdict and, per item, the explanation |
| `POST /v1/drills/conjugation`, `POST /v1/drills/roles` | a sampled drill set for a level, same contract (`exercise_conjugation.schema.json` / `exercise_role.schema.json`, key withheld) |

`POST` because sampling mints an attempt; the underlying data is still read-only. This is the same rule
the prototype already enforces by keeping the banks server-only, and
`scripts/validate/validate_no_client_leak.py` is what proves it holds after a build.

---

## 8. User-state routes — logical only

The 7 `runtime` entities in the manifest have `files: null` and `records: null` because their records
are minted per learner. [`design/user_state.md`](user_state.md) is the authority for their fields;
this section is only their route shape. **Storage is D8/W43** — nothing here picks a database.

| entity | routes | key | schema |
|---|---|---|---|
| `user` | `GET/PATCH /v1/me` | `user_id` → `usr:<opaque>` | `user_state/user.schema.json` |
| `card` | `GET /v1/me/cards`, `GET /v1/me/cards/{card_id}`, `GET /v1/me/queue` | composed: `{user_id}:{deck}:{item}:{kind}` | `user_state/card.schema.json` |
| `review_log` | `POST /v1/me/reviews`, `GET /v1/me/reviews` | `log_id` → `rev:<opaque>` | `user_state/review_log.schema.json` |
| `lesson_progress` | `GET /v1/me/lessons`, `GET/PUT /v1/me/lessons/{les:id}` | `(user_id, lesson)` | `user_state/lesson_progress.schema.json` |
| `exam_attempt` | `POST /v1/exam/papers`, `GET /v1/me/exams`, `GET /v1/me/exams/{attempt_id}` | `attempt_id` → `att:<opaque>-<level>-<n>` | `user_state/exam_attempt.schema.json` |
| `skill_state` | `GET /v1/me/skills`, `GET /v1/me/skills/{cap:id}` | `(user_id, capability)` | `user_state/skill_state.schema.json` |
| `feature_state` | `GET /v1/me/features` | `(user_id, feature)` | `user_state/feature_state.schema.json` |

Notes that are contract, not implementation:

- **`/v1/me` is the only subject.** No route takes a `user_id` path parameter; the subject comes from
  the credential. A learner cannot address another learner.
- **`review_log` is append-only.** `POST` creates, nothing updates or deletes a row. `card` is a cache
  of what FSRS-6 can recompute from the log (`user_state.md` §3), so a `card` is never `PUT` by a
  client — it is a projection the server maintains.
- **A `card_id` parses back deterministically** into `usr`/opaque/`deck`/deck key/item namespace/item
  id/kind (`user_state.md` §2). Refiling a card between decks is a migration, not an edit, and the API
  has no route for it.
- **Composite-key entities have no id in their path.** `lesson_progress` and `skill_state` are keyed by
  `(user_id, X)`, so the route carries `X` and the subject is implicit — which is exactly what the
  manifest's `natural_key` says (`user_id,lesson`, `user_id,capability`).
- **Every write is idempotent under a client-supplied key.** A dropped connection during a review must
  not double-count it.
- **Deletion** follows `user_state.md` §11: the learner's rows go, the corpus does not.

Cross-layer routes read runtime and content together and are named here so no one invents a second
address space for them: `GET /v1/me/queue` (due cards, expanded to their corpus items),
`GET /v1/me/lessons/{id}` (progress + the lesson), `GET /v1/me/skills` (`skill_state` joined to
`capability`).

---

## 9. `deprecated_by` — an id that moved is a redirect, not a 404

A merge retires an address without retiring its content. W08 merged two grammar points (`gram:gp` →
`gram:da-desu`, `gram:gp-152` → `gram:te-hoshii`), kept the losers as `deprecated_by` redirects, and
published the table as `corpus/grammar_deprecated.json` — a flat map from the retired stable id to its
survivor. The 22 vocab redirects approved in A9 land in **W09** and will publish the same way.

**Serving them.** Any item route resolves its address against the entity's redirect table before it
looks in the registry. A hit returns **`301 Moved Permanently`** with a `Location` header *and* a body,
because a client that follows the header silently will never learn that its stored id is stale:

```jsonc
// GET /v1/grammar/gp
// 301, Location: /v1/grammar/da-desu
{ "redirect": {
    "from": "gram:gp",
    "to":   "gram:da-desu",
    "reason": "merged",
    "build": { "date": "…", "git_head": "…" } } }
```

Rules:

- **Redirects chain, and the chain is resolved server-side** to its final target before responding, so
  a client never sees a `301` pointing at another `301`. A cycle is a build-time failure, not a runtime
  one.
- **`410 Gone`** is reserved for an address that was retired with no survivor. Nothing uses it today;
  it exists so that "deleted" and "moved" never collapse into `404`.
- **A collection never returns a deprecated record.** `corpus/grammar_deprecated.json` sits outside the
  `grammar` glob, so `records: 494` is the count of *active* points and the redirect table is not
  double-counted. This is why the redirect table is a sidecar file rather than a flag on the record.
- **User state is migrated, never redirected.** A `card` whose `item` moved is rewritten at migration
  time, on the card and on every `review_log` row that points at it. A stored id must never depend on a
  redirect still existing (`APP_PLAN` sequencing: migrate before minting cards).
- **The redirect table is part of the release identity.** It ships with the build whose merge created
  it, so a client can tell a redirect it has already followed from a new one.

---

## 10. How this contract stays true

The failure mode this document exists to prevent is the one G5 named: the contract and the consumer
agreeing by luck. Four things keep them in step, and all four are already running:

1. **`contracts/manifest.json` is generated**, not hand-kept — `scripts/contracts/build_manifest.py`
   after every export, gated by `scripts/validate/validate_contracts.py` and
   `validate_schema_generation_is_current.py`. A route family that has no manifest row is a route with
   no data behind it.
2. **The consumer reads the manifest.** `prototype/scripts/sync-data.mjs` resolves every glob, honours
   every `packing`, and keys every map by `stable_id_field`/`natural_key`. An empty glob, a record
   count that disagrees with the manifest, or two records sharing an address is a hard error.
3. **The sync is gated by content and by hash.** `scripts/validate/validate_prototype_sync.py`
   re-derives the whole projection from the same manifest and deep-compares it, then asserts that
   `prototype/app/data/_build.json` carries the manifest's `build` block verbatim.
4. **The paid corpus stays server-side.** `scripts/validate/validate_no_client_leak.py` runs after the
   build and searches the client bundle for real corpus strings. §7.3 is a policy; that gate is the
   proof.

**What a served implementation still owes** (not this document's scope, listed so it is not forgotten):
auth and the entitlement check against `user.entitlement`, rate limiting on the expand and filter
routes, and adopting `contracts/types.ts` in the client so the 64 `any`s in the prototype become the
generated types.
