#!/usr/bin/env python3
"""The speaking path's content filter: register by rule, plus the owner's blocklist. W31 / A8.

ONE implementation, imported by `build_speaking_path.py` (say_now) and `build_speaking_practice.py`
(production and `drills[].examples`), because the failure PENDING.md A8 describes is a SELECTION
failure and a filter that only guards one of the three selectors guards nothing.

WHY
---
Selection into this path is mechanical — a stage seed matched against a token lemma, then the known
set — so before `sentence.register` existed nothing could tell a polite request from a Bible verse.
The path shipped 心熱けれど肉体は弱し as a production prompt, お前は脳の半分があったら，危ない! as a
drill and 痔があります in `health`. The 2026-09-01 census could only report the damage (645
say_now/production items, 383 with no register signal of any kind) because there was no field to
filter on. W31 put the field in; this is the filter the decision asked for.

TWO MECHANISMS, DELIBERATELY SEPARATE
-------------------------------------
1. **By rule.** Derived, mechanical, and the same everywhere — a value from the D7 set plus the name
   of the rule that produced it (design/schema_v2.md `sentence.register`). Nothing here is a
   judgement about a particular sentence, so it needs no review and cannot rot.
2. **By blocklist.** `design/speak_blocklist.json`, a small reviewed list of individual sentences or
   substrings. A8: *"I build the mechanism; the list is yours."* The file ships EMPTY and the whole
   filter works with it empty; adding an entry is an owner act, never a campaign's.

THE RULE, stated once
---------------------
A sentence may be spoken by a learner on this path only when its register is one of
`neutral` / `polite` / `casual` AND it clears the blocklist. Everything else is out:

  * `vulgar`, `slang`, `dialect` — content and variety. A learner drilling a coarse lexeme or a
    Kansai final does not know they are doing it, which is precisely the harm.
  * `archaic`, `epistolary` — 心熱けれど肉体は弱し and 拝啓 are not utterances anyone says.
  * `formal` — both of its rules are wrong for a speaking drill and for opposite reasons.
    `written-copula` (である) is expository prose, not deference; `keigo` is language the learner
    must RECOGNISE long before producing, and R44 fixes the order model -> recognition -> production,
    so an unmodelled keigo utterance is not a production prompt. Measured cost when this landed: 15
    of 645 say_now/production items, 7 of them in the `politeness` stage, which still keeps 41
    polite and 5 neutral items — the stage teaches keigo through its GRAMMAR points, which this
    filter does not touch.
  * `register IS NULL` (rule `no-signal`) — the residue. Excluded on purpose and this is why the
    field is nullable at all: a residue sentence defaulted to `neutral` would pass this filter
    silently, which is the one failure mode the whole design is arranged to prevent.
  * rule `polite-request-nasai` — 〜なさい. D7 has no `instructional` value and adding a tenth costs
    every consumer for one filter's benefit (design/schema_v2.md, settled), so 立ちなさい is filed
    `polite` and kept out HERE, by the name of the rule that filed it. This is the reason
    `register_rule` is a stored column and not just a line of prose in the evidence string.

Both mechanisms report a REASON per rejected slug, and the builders print the census, so "the path
contains no vulgar sentence" is a measured number rather than a hope.
"""
from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BLOCKLIST = ROOT / "design" / "speak_blocklist.json"

ALLOWED_REGISTERS = ("neutral", "polite", "casual")
EXCLUDED_REGISTERS = {
    "vulgar": "vulgar lexeme or coarse address",
    "slang": "in-group slang",
    "dialect": "regional variety, not standard Japanese",
    "archaic": "classical morphology; nobody says it",
    "epistolary": "letter or formal-notice formula",
    "formal": "written-formal (である) or keigo — recognition material, not a production prompt",
}
EXCLUDED_RULES = {
    "polite-request-nasai": "instructional 〜なさい: addressed downward, no D7 slot, excluded by rule",
}
NO_REGISTER = "no register signal at all (residue) — never defaulted to neutral"


class SpeakFilter:
    """Admissibility of a bank sentence for say_now / production / drills[].examples.

    `registers` maps slug -> (register, register_rule); `texts` maps slug -> jp. Both come from the
    caller's own DB read, so this module opens nothing but the blocklist.
    """

    def __init__(self, registers: dict, texts: dict, blocklist: Path | None = None) -> None:
        self.registers = registers
        self.texts = texts
        self.path = Path(blocklist) if blocklist else BLOCKLIST
        self.entries: list[dict] = []
        self.rejected: Counter = Counter()
        self.rejected_slugs: dict[str, str] = {}
        self._load()

    def _load(self) -> None:
        """An absent file is an EMPTY list, not an error: the mechanism must work before the list
        exists. A malformed one IS an error — a blocklist that silently reads as empty is worse
        than none, because it looks like protection."""
        if not self.path.exists():
            return
        doc = json.loads(self.path.read_text(encoding="utf-8"))
        if not isinstance(doc, dict) or "entries" not in doc:
            raise SystemExit(f"{self.path}: expected an object with an `entries` list")
        for i, e in enumerate(doc["entries"]):
            if not isinstance(e, dict) or not (e.get("sentence") or e.get("contains")):
                raise SystemExit(f"{self.path}: entry {i} must carry `sentence` or `contains`")
            if not e.get("why"):
                raise SystemExit(f"{self.path}: entry {i} carries no `why` — a blocked sentence "
                                 f"without a reason cannot be reviewed or retired")
            self.entries.append(e)

    # -----------------------------------------------------------------------------------------
    def blocklist_hit(self, slug: str) -> str | None:
        jp = self.texts.get(slug) or ""
        for e in self.entries:
            if e.get("sentence") and e["sentence"] == slug:
                return f"blocklist: {e['why']}"
            if e.get("contains") and e["contains"] in jp:
                return f"blocklist ({e['contains']}): {e['why']}"
        return None

    def reject_reason(self, slug: str) -> str | None:
        """None when the sentence may be spoken; otherwise why it may not."""
        reg, rule = self.registers.get(slug, (None, None))
        if reg is None:
            return NO_REGISTER
        if reg in EXCLUDED_REGISTERS:
            return f"register {reg}: {EXCLUDED_REGISTERS[reg]}"
        if reg not in ALLOWED_REGISTERS:
            return f"register {reg}: not an allowed speaking register"
        if rule in EXCLUDED_RULES:
            return f"rule {rule}: {EXCLUDED_RULES[rule]}"
        return self.blocklist_hit(slug)

    def allows(self, slug: str) -> bool:
        why = self.reject_reason(slug)
        if why is None:
            return True
        self.rejected[why.split(":")[0]] += 1
        self.rejected_slugs[slug] = why
        return False

    def census(self) -> str:
        n = len(self.rejected_slugs)
        if not n:
            return (f"content filter: 0 candidates excluded "
                    f"({len(self.entries)} blocklist entr{'y' if len(self.entries) == 1 else 'ies'})")
        detail = ", ".join(f"{k}={v}" for k, v in sorted(self.rejected.items()))
        return (f"content filter: {n} candidate sentence(s) excluded — {detail} "
                f"({len(self.entries)} blocklist entr{'y' if len(self.entries) == 1 else 'ies'})")
