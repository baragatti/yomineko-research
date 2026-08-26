#!/usr/bin/env python3
"""Resolve a courseware `vocab:<headword>` reference to the one vocab record it means.

The courseware layer addresses vocabulary by headword. That reads well and it is what the lessons were
authored against, but a headword is not an address: 93 headwords are shared by 193 records, so
`vocab:人` names both the N5 "pessoa" and an N1 sense, and `vocab:仏` names both "Buda" and "França".
Whichever record a consumer's index happened to load last is the one that won — the prototype's own
headword index silently collapsed 7,401 records into 7,301 keys.

This module resolves each reference to a `vocab:<jmdict_id>` slug, using evidence rather than
preference, and is explicit about how sure it is. In order:

  unique     - the headword belongs to exactly one record. 2,831 of 2,909 headwords in use.
  level      - several records share the headword but only one sits at the level of the lesson doing
               the unlocking. A lesson teaches a word at its own level, so that is the one it means.
  frequency  - still tied, but the readings differ and our own dissected sentence bank uses one of
               them clearly more often (金 is かね 46 times and きん once). Corpus evidence, but it is
               evidence about usage in general, not about this lesson, so the result is flagged.
  unresolved - the candidates read the same, or the bank has never seen the word. Nothing here can
               decide it; a teacher must. The lowest JMdict entry is used so the export stays
               deterministic, and the case is written to the review queue.

`resolve_all` returns the map plus the review rows, so the caller can both rewrite refs and publish
what still needs a human.
"""
from __future__ import annotations

import sqlite3
from collections import Counter, defaultdict

LEVEL_ORDER = ["pre-n5", "n5", "n4", "n3", "n2", "n1"]


class VocabIdentity:
    def __init__(self, con: sqlite3.Connection) -> None:
        self.con = con
        self.by_headword: dict[str, list[dict]] = defaultdict(list)
        for slug, hw, lvl, kana in con.execute(
                "SELECT slug, headword, level, kana FROM vocab"):
            self.by_headword[hw].append({"slug": slug, "level": lvl, "kana": kana})
        for cands in self.by_headword.values():
            # Deterministic order: the JMdict entry number, so a tie always breaks the same way.
            cands.sort(key=lambda c: c["slug"])
        self._reading_counts: dict[str, Counter] = {}
        self.review: list[dict] = []

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

    # -- resolution -------------------------------------------------------------------------------
    def resolve(self, headword: str, lesson_level: str | None = None,
                lesson_slug: str | None = None) -> tuple[str | None, str]:
        cands = self.by_headword.get(headword)
        if not cands:
            return None, "unknown"
        if len(cands) == 1:
            return cands[0]["slug"], "unique"

        at_level = [c for c in cands if c["level"] == lesson_level] if lesson_level else []
        if len(at_level) == 1:
            return at_level[0]["slug"], "level"
        pool = at_level or cands

        counts = self._readings(headword)
        scored = sorted(((counts.get(c["kana"], 0), c) for c in pool), key=lambda t: -t[0])
        if scored[0][0] > 0 and (len(scored) == 1 or scored[0][0] > scored[1][0]):
            winner = scored[0][1]
            self.review.append({
                "headword": headword, "lesson": lesson_slug, "chosen": winner["slug"],
                "how": "frequency", "needs_review": True,
                "evidence": f"reading {winner['kana']} appears {scored[0][0]}x in the sentence bank "
                            f"vs {scored[1][0]}x for {scored[1][1]['kana']}",
                "candidates": [{"slug": c["slug"], "kana": c["kana"], "level": c["level"]} for c in pool],
            })
            return winner["slug"], "frequency"

        chosen = pool[0]
        self.review.append({
            "headword": headword, "lesson": lesson_slug, "chosen": chosen["slug"],
            "how": "unresolved", "needs_review": True,
            "evidence": "candidates share a reading, or the sentence bank has no example — "
                        "no automatic evidence can choose; lowest JMdict entry used so the export is "
                        "deterministic. A teacher must confirm which sense the lesson teaches.",
            "candidates": [{"slug": c["slug"], "kana": c["kana"], "level": c["level"]} for c in pool],
        })
        return chosen["slug"], "unresolved"
