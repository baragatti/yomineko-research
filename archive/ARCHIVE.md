# Archive — material moved out of the live tree

Nothing here is deleted, and nothing is moved here without an independent audit recorded below. If any
of it needs to come back, restore the directory to its original path and **re-run the full gate**
(`scripts/validate/validate_all.py` and `scripts/validate/validate_contracts.py`) before trusting it —
the live tree has moved on since these files were written.

---

## `course-pre-renumber-2026-06-26/` — 31 topic directories, 223 JSON + 192 MD files

**Moved:** 2026-08-26 · **From:** `course/n3/topic-36…50-*`, `course/n4/topic-20…35-*`
**By:** `scripts/contracts/archive_orphan_topics.py`

### Why

`course/n3` and `course/n4` each held two copies of every topic. When those levels were renumbered
(N4 by +1, N3 by +2) the old directories stayed on disk, so **31 topic ids and 192 lesson ids each
answered to two different files**. That breaks the rule the whole graph rests on — a record has one
stable id (spec §1.7) — and it is why `validate_contracts.py` could not pass: an API cannot resolve
`/lessons/les:n3-conectores-01` when two files claim it.

Every course root points at the *newer* copy. Nothing referenced these directories by path except
generated indexes and the Phase-6 QA inputs under `research/derived/fable5_validation/`, which are
keyed to the old numbering — that mismatch is what caused the corruption described below.

### Independent audit

Audited by a separate agent that recomputed every claim from the repository rather than reviewing the
proposal. Verdict: **SAFE WITH EXCEPTIONS** — the exceptions were fixed before the move.

| # | Check | Result |
|---|---|---|
| 1 | Reachability | 31 unreachable (15 n3 + 16 n4); all 52 referenced `topics[].path` resolve; no broken forward references |
| 2 | Nothing unique lost | 192 lesson ids + 31 topic ids, **0** of which exist only in the archived copy; 0 item ids in `unlocks`/`srs` absent from the live course |
| 3 | Recency | every archived dir last changed 2026-06-26; every live counterpart 2026-08-19 (one 2026-07-05). **0** cases of the archived copy being newer |
| 4 | Content comparison | live is directionally the improvement (+0.26% body, identical exercise count, no block or exercise id present only in the archive) — **but 7 lessons failed, see below** |
| 5 | Inbound references | no script resolves these by path; only generated indexes and the QA inputs mention them |
| 6 | Git status | 415 files, all tracked, none modified or untracked — fully recoverable |

### The exception, and what was done about it

Check 4 found that the live copy was **not** a clean superset. Phase-6 QA had run against *this*
(old) copy and its findings were applied to the renumbered one — and in seven lessons the finding
**text** was pasted into the field instead of the correction it asked for. The title of
`les:n3-conectores-07` on the live site read:

> "Retitle to the actual content, e.g. 'Pessoas, crime e medida: vocabulário da linha は', and update
> the matching `<heading level="2">` at the top of body, which repeats the old title."

Seven lessons were affected (`n3-conectores-07`, `n3-desejos-07`, `n3-estado-07`, `n3-tempo-07`,
`n3-causa-07`, `n3-relato-06`, `n3-perspectiva-05`), across `title`, `description`, `objectives`,
`body` and one exercise prompt. One also carried mojibake — a Cyrillic т and я inside `～にとって` — and
had silently dropped `～にかわって` from its list.

All nine fields were repaired before the move by `scripts/apply_qa_instruction_leaks.py`, which
records the exact before/after and the reasoning for each. The repairs are not blind reverts: where
the reviewer's instruction contained the improvement it was asking for, the improvement was applied
and only the instruction wrapper removed, because restoring the older copy would have discarded the QA
finding.

**Correction (2026-08-26, later the same day):** the first version of that script repaired only
`db/corpus.sqlite` — a git-ignored, regenerable index — so the nine corrupt values survived in the
tracked authoring source (`research/derived/lessons/`) and one loader+export cycle would have
reintroduced them. The script now writes both layers, and a follow-up sweep found the archive-diff
method itself was the blind spot: it could only expose leaked instructions in lessons that HAD an
archived twin. A content-pattern sweep over everything else found more of the same class (an N5
exercise prompt, 35 sentence-bank fields, 10 reading furigana values, 6 grammar fields), all repaired
by `scripts/apply_phase7_content_repairs.py`.

The reverse check found **0** cases of archive-only corruption.

### Known limitation of the archived copies

These files predate two later changes and are **not** self-consistent with the current corpus:

- their vocabulary references use headwords (`vocab:人`), not the published slugs (`vocab:1580640`)
  that the live tree now uses;
- their `needs_review` / `ai_generated` flags ARE the pre-migration integers (`1`/`0`, with
  `ai` as the field name on exam-derived rows) — a whole-tree census reconciled every count, so this
  is a statement, not a hedge.

Restoring one is therefore a migration, not a copy. Re-run the exporters and both gates afterwards.
