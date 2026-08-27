#!/usr/bin/env python3
"""Resolve a courseware `vocab:<headword>` reference to the one vocab record it means.

The courseware layer addresses vocabulary by headword. That reads well and it is what the lessons were
authored against, but a headword is not an address: 93 headwords are shared by 193 records, so
`vocab:人` names both the N5 "pessoa" and an N1 sense, and `vocab:仏` names both "Buda" and "França".
Whichever record a consumer's index happened to load last is the one that won — the prototype's own
headword index silently collapsed 7,401 records into 7,301 keys.

This module resolves each reference to a `vocab:<jmdict_id>` slug, using evidence rather than
preference, and is explicit about how sure it is. In order:

  unique           - the headword belongs to exactly one record. 2,832 of 2,910 headwords in use.
  (sibling filter) - before anything else guesses, drop any candidate that the SAME lesson already
                     unlocks through an explicit row-id ref. The first export of this migration mapped
                     `vocab:得る` in les:n3-conectores-05 onto vocab:1454500 — the record the lesson's
                     own `vocab:1505` row-id ref already names — producing a duplicate unlock and
                     silently dropping the sibling 得る/える from the whole course. The lesson's own
                     ref list is evidence, and it rules that candidate out.
  level            - several records share the headword but only one sits at the level of the lesson
                     doing the unlocking. A lesson teaches a word at its own level.
  introducing_topic- the working index records, per vocab row, WHICH TOPIC introduces it
                     (vocab.introducing_topic_id, written by the placement pass). If exactly one
                     candidate is placed in the unlocking lesson's own topic, that is the record —
                     an exact stored fact, no guess, no review row. An independent audit found six
                     frequency guesses contradicting this field (中/なか vs ちゅう, 年/とし vs ねん…);
                     the field was right in every checked case, so it outranks frequency.
  frequency        - still tied, but the readings differ and our own dissected sentence bank uses one
                     of them clearly more often (金 is かね 46 times and きん once). Corpus evidence,
                     but evidence about usage in general, not about this lesson — flagged for review.
  unresolved       - the candidates read the same, or the bank has never seen the word. Nothing here
                     can decide it; a teacher must. The lowest JMdict entry is used so the export
                     stays deterministic, and the case is written to the review queue.

Decisions are cached per (headword, lesson), so a headword that appears in a lesson's unlocks AND ten
times in its body resolves once and identically, and the review queue gets ONE row per
(headword, lesson) with every occurrence listed in `affects` — the first export deduplicated the
queue by headword alone, which published 20 rows for what were really 38 per-lesson decisions.

`resolve_all` is not needed: the exporter calls resolve() per ref and reads `.review` at the end.
"""
from __future__ import annotations

import sqlite3
from collections import Counter, defaultdict

LEVEL_ORDER = ["pre-n5", "n5", "n4", "n3", "n2", "n1"]


class VocabIdentity:
    def __init__(self, con: sqlite3.Connection) -> None:
        self.con = con
        self.by_headword: dict[str, list[dict]] = defaultdict(list)
        for vid, slug, hw, lvl, kana, itopic in con.execute(
                "SELECT id, slug, headword, level, kana, introducing_topic_id FROM vocab"):
            self.by_headword[hw].append(
                {"slug": slug, "level": lvl, "kana": kana, "topic_id": itopic, "row_id": vid})
        for cands in self.by_headword.values():
            # Deterministic order: the JMdict entry number, so a tie always breaks the same way.
            cands.sort(key=lambda c: c["slug"])

        # slug by row id, for the sibling filter (row-id refs are unambiguous).
        self._slug_of_row: dict[str, str] = {}
        for vid, slug in con.execute("SELECT id, slug FROM vocab"):
            self._slug_of_row[str(vid)] = slug

        # lesson slug -> topic id and -> the set of vocab slugs its NUMERIC unlock refs already claim.
        self._topic_of_lesson: dict[str, int] = {}
        self._claimed: dict[str, set] = defaultdict(set)
        for lslug, topic_id, ref in con.execute(
                "SELECT l.slug, l.topic_id, lu.ref FROM lesson l "
                "LEFT JOIN lesson_unlocks lu ON lu.lesson_id = l.id AND lu.unlock_type = 'vocab'"):
            self._topic_of_lesson[lslug] = topic_id
            if ref and ":" in ref:
                ident = ref.split(":", 1)[1]
                if ident.isascii() and ident.isdigit() and ident in self._slug_of_row:
                    self._claimed[lslug].add(self._slug_of_row[ident])

        self._reading_counts: dict[str, Counter] = {}
        self._decision: dict[tuple, tuple] = {}     # (headword, lesson_slug) -> (slug, how)
        self._review_rows: dict[tuple, dict] = {}   # (headword, lesson_slug) -> review row
        self.review: list[dict] = []                # kept in insertion order for the exporter

    # -- evidence ---------------------------------------------------------------------------------
    def _readings(self, headword: str) -> Counter:
        """How often each reading of this headword appears in the dissected sentence bank."""
        if headword not in self._reading_counts:
            c: Counter = Counter()
            for (rd,) in self.con.execute(
                    "SELECT reading FROM token WHERE surface=? AND reading IS NOT NULL", (headword,)):
                c[rd] += 1
            self._reading_counts[headword] = c
        return self._reading_counts[headword]

    def _note(self, headword: str, lesson_slug, chosen: dict, how: str,
              evidence: str, pool: list, where: str) -> None:
        key = (headword, lesson_slug)
        row = self._review_rows.get(key)
        if row is None:
            row = {
                "headword": headword, "lesson": lesson_slug, "chosen": chosen["slug"],
                "how": how, "needs_review": True, "evidence": evidence,
                "affects": [],
                "candidates": [{"slug": c["slug"], "kana": c["kana"], "level": c["level"]}
                               for c in pool],
            }
            self._review_rows[key] = row
            self.review.append(row)
        if where and where not in row["affects"]:
            row["affects"].append(where)

    # -- resolution -------------------------------------------------------------------------------
    def resolve(self, headword: str, lesson_level: str | None = None,
                lesson_slug: str | None = None, where: str = "unlock") -> tuple[str | None, str]:
        cached = self._decision.get((headword, lesson_slug))
        if cached:
            # A guessed decision gains another `affects` entry; a settled one just repeats.
            key = (headword, lesson_slug)
            if key in self._review_rows and where and where not in self._review_rows[key]["affects"]:
                self._review_rows[key]["affects"].append(where)
            return cached

        result = self._resolve(headword, lesson_level, lesson_slug, where)
        self._decision[(headword, lesson_slug)] = result
        return result

    def _resolve(self, headword: str, lesson_level, lesson_slug, where) -> tuple[str | None, str]:
        cands = self.by_headword.get(headword)
        if not cands:
            return None, "unknown"
        if len(cands) == 1:
            return cands[0]["slug"], "unique"

        # Sibling filter: a candidate the lesson already unlocks by row id cannot be what THIS
        # headword ref means — the author would not unlock one record twice.
        pool = cands
        if lesson_slug and lesson_slug in self._claimed:
            unclaimed = [c for c in pool if c["slug"] not in self._claimed[lesson_slug]]
            if len(unclaimed) == 1:
                return unclaimed[0]["slug"], "sibling"
            if unclaimed:
                pool = unclaimed

        at_level = [c for c in pool if c["level"] == lesson_level] if lesson_level else []
        if len(at_level) == 1:
            return at_level[0]["slug"], "level"
        pool = at_level or pool

        # Placement fact: the topic that introduces the record, per the working index.
        topic = self._topic_of_lesson.get(lesson_slug) if lesson_slug else None
        if topic is not None:
            placed = [c for c in pool if c["topic_id"] == topic]
            if len(placed) == 1:
                return placed[0]["slug"], "introducing_topic"

        counts = self._readings(headword)
        scored = sorted(((counts.get(c["kana"], 0), c) for c in pool), key=lambda t: -t[0])
        if scored[0][0] > 0 and (len(scored) == 1 or scored[0][0] > scored[1][0]):
            winner = scored[0][1]
            self._note(headword, lesson_slug, winner, "frequency",
                       f"reading {winner['kana']} appears {scored[0][0]}x in the sentence bank "
                       f"vs {scored[1][0]}x for {scored[1][1]['kana']}", pool, where)
            return winner["slug"], "frequency"

        chosen = pool[0]
        self._note(headword, lesson_slug, chosen, "unresolved",
                   "candidates share a reading, or the sentence bank has no example — no automatic "
                   "evidence can choose; lowest JMdict entry used so the export is deterministic. "
                   "A teacher must confirm which sense the lesson teaches.", pool, where)
        return chosen["slug"], "unresolved"
