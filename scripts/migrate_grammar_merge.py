#!/usr/bin/env python3
"""W08 / owner decision A3 — merge duplicate-identity grammar points WITHOUT losing content.

`research/reports/grammar_identity_merges.md` found seven grammar records that collide on their
`forms[].form` set. Two of the collisions are the SAME point registered twice, under two identities,
unlocked by the SAME lesson — so a learner is issued two SRS cards for one pattern and the graph
carries two addresses for one thing:

    gram:gp      {です}     -> gram:da-desu    (one copula, two identities)
    gram:gp-152  {てほしい} -> gram:te-hoshii  (same point, same lesson)

The other five collisions are NOT merged here. `gp-36`/`te-iru` and `gp-63`/`gp-115` are genuinely
different points whose collision is manufactured by a wrong `forms[0]`; `gp-100`/`gp-118`,
`gp-103`/`n3-sukoshimo-nai` and the three `ように` records are UNTRIAGED. This script merges only
what the report proved, and says so loudly for everything it declines (see MERGES / DECLINED).

WHAT "NO CONTENT LOSS" MEANS HERE, CONCRETELY
---------------------------------------------
1. **Nothing is deleted.** The loser's `grammar_point` row stays, with every field it had, and gains
   `deprecated_by = '<survivor slug>'`. `archive/ARCHIVE.md` sets the convention: records are retired,
   never removed, so an audit can still read what was merged away.
2. **Every loser field and JSON column is diffed against the survivor** before any edge moves. What
   the survivor lacks is APPENDED to it, element by element, and recorded:
     * list columns  (`forms_json`, `register_json`, `usage_contexts_json`, `nuance_tags_json`)
       -> missing members appended, in the loser's order, after the survivor's own;
     * map columns   (`level_sources`, `refs.level_sources`, `refs.also_known_as`,
                      `localized_text(form_meanings)`) -> missing keys/members merged in;
     * `formation_steps_json.variants` -> a variant is appended when no survivor variant shares its
       (base, step-chain) signature. `example` is deliberately NOT part of the signature: two variants
       that differ only in the example word are the same RULE, and appending the second one would trip
       `validate_grammar_formation.py` check 4 (duplicate variant);
     * scalars (`structure_pattern`, `caution`, `steps_unavailable`, …) -> copied only when the
       survivor's is empty, and otherwise reported as covered (when the survivor's value contains the
       loser's, modulo the decorative `～`) or salvaged;
     * `level_agreement` / `level_confidence` are RECOMPUTED from the merged `level_sources`, because
       merging two source sets genuinely raises the agreement (both merges go to 3/3).
3. **Free prose is salvaged, not concatenated.** `explanation`, `formation`, `nuance` and `label` are
   learner-facing pt-BR under a written style contract (`design/translation_style.md`). Machine-gluing
   two independently authored explanations produces duplicated, part-contradictory text — the exact
   defect `research/reports/qa_sweep/` exists to catch. So a prose field whose survivor value is
   non-empty is written VERBATIM into the merge ledger under `salvage`, the survivor is marked
   `needs_review = 1`, and a human folds it in. `--append-prose` forces the literal concatenation for
   an owner who wants it anyway. A prose field the survivor does NOT have is copied outright — that
   would be real loss.

WHAT MOVES
----------
    sentence_grammar   loser link -> survivor link, or dropped when the sentence already carries the
                       survivor (a re-point would collide on the primary key)
    sentence.tags      the loser key rewritten to the survivor key, de-duplicated, order kept
    lesson_unlocks     BOTH merges unlock loser and survivor from the SAME lesson, so the loser's
                       unlock is a duplicate: it is DROPPED, not re-pointed, and recorded as such.
                       (If a future merge's lesson unlocked only the loser, it re-points instead.)
    lesson_introduces  same rule
    lesson_needs       same rule
    family_member      re-pointed to the survivor at the LOSER's intra_order when the survivor is not
                       already in that family — that is how `gram:te-hoshii` inherits
                       `grp:gram-n4-volitivo`. Dropped when the survivor is already a member.
    exercise_item      re-pointed, or dropped when the survivor is already on that exercise
    grammar_related    re-pointed both directions; self-relations and duplicates dropped
    lesson.cumulative_known_set   the stored "what the learner knows by here" set (281 lessons carry
                       `gram:gp`, 157 carry `gram:gp-152`). export_course.py RE-DERIVES this from
                       lesson_unlocks instead of reading the column, so the published course is right
                       the moment the unlock moves — but `ingest/build_readings.py` and
                       `ingest/mine_n3_targets.py` gate on the stored copy, and a retired address
                       sitting in it would let a later builder treat it as a known item.
    research/derived/lessons/*.json   the AUTHORING SOURCE. `archive/ARCHIVE.md` records a repair that
                       wrote only the DB and left the authoring queue carrying the old values, where
                       "one loader+export cycle would have reintroduced them". Both layers move here:
                       `unlocks[]`, `needs[]`, `exercises[].item_refs[]` and the `<grammar ref=…>` /
                       `<check item-ref=…>` addresses inside `body`.

WHAT DOES **NOT** MOVE, AND WHY
-------------------------------
    corpus/**, course/**   regenerated by the exporters; editing them here would be undone by the next
                       export and is forbidden by CLAUDE.md's data-format rule.
    design/grammar_placement.json   the loser's row stays. It is a hand-maintained design input that
                       says which topic a grammar KEY is placed in, and the loser's record still
                       exists — deprecated, but present, and still placed in that topic. Deleting the
                       row would make `scripts/ingest/place_items.py` leave the record unplaced on a
                       rebuild, which is a different corpus, not a cleaner one.
    research/derived/repairs/*.json  historical evidence. A later migration does not get to rewrite a
                       campaign's ledger. See the `superseded` note in scripts/validate/README.md.

USAGE
    migrate_grammar_merge.py               dry run: prints the whole plan, writes nothing
    migrate_grammar_merge.py --apply       applies it (idempotent; a second run is a no-op)
    migrate_grammar_merge.py --check       verifies the merge IS applied; exit 1 if it is not
    migrate_grammar_merge.py --db PATH     target another sqlite (scripts/dbtarget.py)
    migrate_grammar_merge.py --root PATH   target another checkout for the authoring-source rewrite
    migrate_grammar_merge.py --apply --append-prose   also concatenate the salvaged prose (off by
                                           default; see point 3 above)
"""
from __future__ import annotations

import argparse
import json
import sqlite3
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
# W01: honour --db / $YOMINEKO_DB so a rebuild can target a scratch DB (scripts/dbtarget.py).
_sys_scripts = next(p for p in Path(__file__).resolve().parents if p.name == "scripts")
sys.path.append(str(_sys_scripts))
from dbtarget import db_target, take_flag  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]


# ==================================================================================================
# The table. One row per merge; everything else in this file is generic machinery over it.
# `expect` is an EXACT precondition, measured on the pre-merge index and re-measured before any write:
# if the graph is not the shape the report described, this script refuses rather than guessing.
# ==================================================================================================
MERGES: list[dict] = [
    {
        "loser": "gp",
        "winner": "da-desu",
        "verdict": "MERGE",
        "why": ("One copula registered twice. `gp` is the です half of `da-desu` {だ, です}: same "
                "topic (top:n5-desu-wa), same family (grp:gram-n5-desu-wa), same lesson "
                "(les:n5-desu-wa-01) unlocks both, and all six of `gp`'s sentences already carry "
                "`da-desu` too. grammar_identity_merges.md §2.1."),
        "expect": {"sentence_grammar": 6, "sentence_grammar_overlap": 6, "sentence_tags": 0,
                   "lesson_unlocks": 1, "lesson_unlocks_dup": 1, "lesson_introduces": 1,
                   "lesson_introduces_dup": 1, "lesson_needs": 0,
                   "family_member": 1, "family_member_dup": 1, "exercise_item": 1,
                   "exercise_item_dup": 0, "grammar_related": 0,
                   "cumulative_known_set": 281},
    },
    {
        "loser": "gp-152",
        "winner": "te-hoshii",
        "verdict": "MERGE",
        "why": ("Same point, same form 〜てほしい, same topic (top:n4-dar-receber), same lesson "
                "(les:n4-dar-receber-03) unlocks both and issues two SRS cards for one pattern. "
                "`gp-152` additionally carried authoring commentary leaked into learner-facing pt-BR; "
                "`grammar_record_repairs.json` already removed it (4 rows), so the leak is not a "
                "reason to prefer either record today — the duplicate identity is. §2.4."),
        "expect": {"sentence_grammar": 5, "sentence_grammar_overlap": 0, "sentence_tags": 5,
                   "lesson_unlocks": 1, "lesson_unlocks_dup": 1, "lesson_introduces": 1,
                   "lesson_introduces_dup": 1, "lesson_needs": 0,
                   "family_member": 1, "family_member_dup": 0, "exercise_item": 1,
                   "exercise_item_dup": 0, "grammar_related": 0,
                   "cumulative_known_set": 157},
    },
]

# Collisions this script deliberately does NOT merge. Printed on every run so the residue stays visible.
DECLINED: list[tuple[str, str]] = [
    ("gram:gp-36 / gram:te-iru",
     "KEEP BOTH — relative clause (Verb[た・ている] + Noun) vs the ている aspect. The collision is a "
     "wrong forms[] on gp-36, not one point. §2.2."),
    ("gram:gp-63 / gram:gp-115",
     "KEEP BOTH — passive vs potential. The collision is manufactured by a wrong gp-115.forms[0]. §2.3."),
    ("gram:gp-100 / gram:gp-118  {しかない}", "UNTRIAGED — no evidence pass has been run. §3.4."),
    ("gram:gp-103 / gram:n3-sukoshimo-nai  {すこしもない}",
     "UNTRIAGED — cross-level near-duplicate; merging across N4/N3 is an owner decision. §3.4."),
    ("gram:n3-you-ni / n3-you-ni-2 / n3-you-ni-3  {～ように}",
     "UNTRIAGED — three-way collision; needs a sense split before any merge. §3.4."),
    ("gram:n3-te-iru vs te-iru, gram:n3-te-hoshii vs te-hoshii",
     "NOT MERGED — the ～ prefix hides them from the forms index and both pairs are already co-listed "
     "inside one capability, so an N3 extension of an N5/N4 point is defensible. Untriaged. §3.4."),
]

# Closed vocabularies, so an APPEND can never widen an enum by accident. Sources are named because a
# copy that drifts from its owner is worse than no check at all.
USAGE_CONTEXTS = {"spoken", "written", "business", "casual-friends", "formal-email", "academic",
                  "announcement", "literary"}                    # validate_grammar_formation.CONTEXTS
NUANCE_TAGS = {"emphasis", "softening", "conjecture", "obligation", "permission", "prohibition",
               "hearsay", "comparison", "cause", "condition", "concession", "intention", "desire",
               "request", "experience", "change-of-state", "continuation", "completion", "politeness",
               "humility", "honorific"}                          # validate_grammar_formation.NUANCE
REGISTERS = {"casual", "colloquial", "dated", "feminine", "formal", "honorific", "humble", "literary",
             "masculine", "neutral", "plain", "polite", "slang", "written"}  # contracts/grammar.schema
FORMATION_OPS = {"to-te-form", "to-masu-stem", "to-nai-stem", "to-ta-form", "to-dictionary",
                 "to-volitional", "to-potential", "to-passive", "to-causative", "to-conditional-ba",
                 "to-adverbial", "to-attributive", "nominalize", "append", "replace-ending",
                 "drop-final-ru", "none"}                        # validate_grammar_formation.OPS
FORMATION_BASES = {"verb", "i-adjective", "na-adjective", "noun", "clause", "any"}

LIST_COLUMNS = {"forms_json": None, "register_json": REGISTERS,
                "usage_contexts_json": USAGE_CONTEXTS, "nuance_tags_json": NUANCE_TAGS}
SCALAR_COLUMNS = ("structure_pattern", "register", "caution", "steps_unavailable", "label_pt",
                  "explanation_pt", "formation_pt", "nuance_pt", "source", "created_by", "layer")
PROSE_FIELDS = ("label", "explanation", "formation", "nuance")
LOCALES = ("pt-BR", "en")

LEDGER = "research/derived/grammar_merge_ledger.json"


# ==================================================================================================
# helpers
# ==================================================================================================
def jloads(s, default=None):
    if s in (None, ""):
        return default
    try:
        return json.loads(s)
    except (json.JSONDecodeError, TypeError):
        return default


def jdumps(o) -> str:
    return json.dumps(o, ensure_ascii=False)


def norm(s: str | None) -> str:
    """A structure_pattern / form with its decorative wave dashes and spaces removed.

    `gram:gp`'s pattern is `です` and `gram:da-desu`'s is `だ / です`; `gp-152`'s is `～てほしい` and
    `te-hoshii`'s is `てほしい`. Containment on the raw strings would miss both.
    """
    return (s or "").replace("～", "").replace("〜", "").replace(" ", "").replace("　", "")


def variant_sig(v: dict) -> str:
    """A formation variant's identity: base + step chain. `example` is presentation, not rule."""
    steps = [(s.get("base"), s.get("op"), s.get("token")) for s in (v.get("steps") or [])]
    return jdumps([v.get("base"), steps])


def file_indent(raw: str, default: int = 2) -> int:
    """The indent width a JSON file was written with, read off its first indented line."""
    for line in raw.split("\n")[1:]:
        n = len(line) - len(line.lstrip(" "))
        if n and line.strip():
            return n
    return default


def grow(con: sqlite3.Connection, key: str) -> sqlite3.Row:
    r = con.execute("SELECT * FROM grammar_point WHERE key=?", (key,)).fetchone()
    if r is None:
        die(f"no grammar_point with key {key!r} — the index is not the one this migration was written "
            f"against. Refusing to guess.")
    return r


def die(msg: str) -> None:
    print(f"REFUSED: {msg}")
    raise SystemExit(2)


def has_column(con: sqlite3.Connection, table: str, col: str) -> bool:
    return any(r[1] == col for r in con.execute(f"PRAGMA table_info({table})"))


# ==================================================================================================
# content-loss check
# ==================================================================================================
def diff_content(con: sqlite3.Connection, L: sqlite3.Row, W: sqlite3.Row) -> dict:
    """Every loser field/JSON column against the survivor's.

    Returns {"append": {column: new_value}, "localized": [...], "salvage": [...], "covered": [...],
             "refused": [...]} — `append` is what will be written onto the survivor.
    """
    out: dict = {"append": {}, "localized": [], "salvage": [], "covered": [], "refused": []}

    # --- list columns -----------------------------------------------------------------------------
    for col, vocab in LIST_COLUMNS.items():
        lv, wv = jloads(L[col], []) or [], jloads(W[col], []) or []
        missing = [x for x in lv if x not in wv]
        if not missing:
            out["covered"].append(f"{col}: loser adds nothing ({lv!r} ⊆ {wv!r})")
            continue
        bad = [x for x in missing if vocab is not None and x not in vocab]
        if bad:
            out["refused"].append(f"{col}: {bad!r} is outside the closed vocabulary; NOT appended "
                                  f"(an append must never widen an enum). Salvaged in the ledger.")
            missing = [x for x in missing if x not in bad]
        if missing:
            out["append"][col] = jdumps(wv + missing)
            out["covered"].append(f"{col}: appended {missing!r} -> {wv + missing!r}")

    # --- level_sources (map) + the agreement it implies --------------------------------------------
    lsrc, wsrc = jloads(L["level_sources"], {}) or {}, jloads(W["level_sources"], {}) or {}
    if isinstance(lsrc, dict) and isinstance(wsrc, dict):
        missing = {k: v for k, v in lsrc.items() if k not in wsrc}
        if missing:
            merged = {**wsrc, **missing}
            out["append"]["level_sources"] = jdumps(merged)
            agree = sum(1 for v in merged.values() if v == W["level"])
            out["append"]["level_agreement"] = f"{agree}/{len(merged)}"
            out["append"]["level_confidence"] = round(agree / len(merged), 4)
            out["covered"].append(
                f"level_sources: merged {missing!r} -> {merged!r}; level_agreement "
                f"{W['level_agreement']!r} -> {out['append']['level_agreement']!r}")
        else:
            out["covered"].append("level_sources: loser adds nothing")

    # --- references_json (map with a list inside) ---------------------------------------------------
    lref, wref = jloads(L["references_json"], {}) or {}, jloads(W["references_json"], {}) or {}
    if isinstance(lref, dict) and isinstance(wref, dict):
        new = dict(wref)
        notes = []
        aka = list(new.get("also_known_as") or [])
        for cand in list(lref.get("also_known_as") or []) + [lref.get("label_en")]:
            if cand and cand not in aka and cand != new.get("label_en"):
                aka.append(cand)
                notes.append(cand)
        if notes:
            new["also_known_as"] = aka
        rs = dict(new.get("level_sources") or {})
        add = {k: v for k, v in (lref.get("level_sources") or {}).items() if k not in rs}
        if add:
            rs.update(add)
            new["level_sources"] = rs
        if notes or add:
            out["append"]["references_json"] = jdumps(new)
            out["covered"].append(f"refs: also_known_as += {notes!r}, level_sources += {add!r}")
        else:
            out["covered"].append("refs: loser adds nothing")

    # --- formation_steps_json.variants --------------------------------------------------------------
    lfs, wfs = jloads(L["formation_steps_json"]), jloads(W["formation_steps_json"])
    lvars = (lfs or {}).get("variants") or []
    wvars = (wfs or {}).get("variants") or []
    have = {variant_sig(v) for v in wvars}
    add_vars, refused_vars = [], []
    for v in lvars:
        sig = variant_sig(v)
        if sig in have:
            continue
        bases = {v.get("base")} | {s.get("base") for s in (v.get("steps") or []) if s.get("base")}
        ops = {s.get("op") for s in (v.get("steps") or [])}
        if not bases <= FORMATION_BASES or not ops <= FORMATION_OPS:
            refused_vars.append((v, f"off-enum base/op {sorted(bases - FORMATION_BASES)!r} "
                                    f"{sorted(ops - FORMATION_OPS)!r}"))
            continue
        if any(s.get("op") in ("append", "replace-ending") and not s.get("token")
               for s in (v.get("steps") or [])):
            refused_vars.append((v, "an append/replace-ending step with no token is a silent no-op "
                                    "(validate_grammar_formation check 5)"))
            continue
        add_vars.append(v)
        have.add(sig)
    if add_vars:
        if W["steps_unavailable"]:
            out["refused"].append(
                f"formation_steps: survivor carries steps_unavailable={W['steps_unavailable']!r}; "
                f"appending steps beside a WITHHELD reason trips validate_grammar_formation check 3. "
                f"{len(add_vars)} variant(s) salvaged in the ledger instead.")
            out["salvage"].append({"field": "formation_steps.variants", "value": add_vars,
                                   "why": "survivor has a withheld-steps reason"})
        else:
            out["append"]["formation_steps_json"] = jdumps({**(wfs or {}),
                                                            "variants": wvars + add_vars})
            out["covered"].append(
                f"formation_steps: appended {len(add_vars)} variant(s) "
                f"{[v.get('example') for v in add_vars]!r} (signature = base + step chain; `example` "
                f"is not part of it, so two variants differing only in the example word stay one rule)")
    for v, why in refused_vars:
        out["refused"].append(f"formation_steps variant {v.get('example')!r}: {why}")
        out["salvage"].append({"field": "formation_steps.variants", "value": [v], "why": why})
    if not add_vars and not refused_vars:
        out["covered"].append("formation_steps: every loser variant already has a survivor variant "
                              "with the same (base, step chain)")

    # --- scalar columns -----------------------------------------------------------------------------
    for col in SCALAR_COLUMNS:
        lv, wv = L[col], W[col]
        if lv in (None, "") or lv == wv:
            continue
        if wv in (None, ""):
            out["append"][col] = lv
            out["covered"].append(f"{col}: survivor was empty; copied loser value {lv!r}")
        elif norm(str(lv)) and norm(str(lv)) in norm(str(wv)):
            out["covered"].append(f"{col}: {lv!r} is already inside survivor {wv!r}")
        elif col in ("register",) and lv in (jloads(W["register_json"], []) or []):
            out["covered"].append(f"{col}: {lv!r} carried by the survivor's register list")
        elif col in ("source", "created_by", "layer"):
            out["covered"].append(f"{col}: provenance of the loser row, not content; not merged "
                                  f"({lv!r} vs {wv!r})")
        else:
            out["salvage"].append({"field": col, "value": lv, "why": "survivor has its own value; "
                                                                    "picking between them is authoring"})

    # --- localized_text ------------------------------------------------------------------------------
    lloc = {(r["field"], r["locale"]): r for r in con.execute(
        "SELECT field,locale,value,is_list,layer FROM localized_text "
        "WHERE entity_type='grammar_point' AND entity_id=?", (L["id"],))}
    wloc = {(r["field"], r["locale"]): r for r in con.execute(
        "SELECT field,locale,value,is_list,layer FROM localized_text "
        "WHERE entity_type='grammar_point' AND entity_id=?", (W["id"],))}
    for (field, locale), lr in sorted(lloc.items()):
        wr = wloc.get((field, locale))
        lval = lr["value"]
        if lval in (None, ""):
            continue
        if wr is None or wr["value"] in (None, ""):
            out["localized"].append({"field": field, "locale": locale, "value": lval,
                                     "is_list": lr["is_list"], "layer": lr["layer"],
                                     "mode": "copy", "why": "survivor had nothing here"})
            continue
        if wr["value"] == lval:
            out["covered"].append(f"localized {field}/{locale}: identical")
            continue
        if field == "form_meanings":
            lm, wm = jloads(lval, {}) or {}, jloads(wr["value"], {}) or {}
            missing = {k: v for k, v in lm.items() if k not in wm}
            if missing:
                out["localized"].append({"field": field, "locale": locale,
                                         "value": jdumps({**wm, **missing}), "is_list": 1,
                                         "layer": wr["layer"], "mode": "merge-map",
                                         "why": f"forms {list(missing)!r} had no survivor gloss"})
            else:
                out["covered"].append(
                    f"localized form_meanings/{locale}: every form the loser glossed is glossed by "
                    f"the survivor ({sorted(lm)!r}); the wording differs and is salvaged")
                out["salvage"].append({"field": f"{field}/{locale}", "value": lval,
                                       "why": "same form keys, different wording"})
            continue
        if field in PROSE_FIELDS:
            out["salvage"].append({"field": f"{field}/{locale}", "value": lval,
                                   "why": "learner-facing prose; both records are authored, and "
                                          "gluing them is authoring, not migration"})
        else:
            out["salvage"].append({"field": f"{field}/{locale}", "value": lval,
                                   "why": "unrecognised localized field"})
    return out


# ==================================================================================================
# edges
# ==================================================================================================
def plan_edges(con: sqlite3.Connection, L: sqlite3.Row, W: sqlite3.Row) -> dict:
    lid, wid = L["id"], W["id"]
    lslug, wslug = L["slug"], W["slug"]
    lkey, wkey = L["key"], W["key"]
    p: dict = {}

    have = {r[0] for r in con.execute("SELECT sentence_id FROM sentence_grammar WHERE grammar_id=?", (wid,))}
    mine = [r[0] for r in con.execute("SELECT sentence_id FROM sentence_grammar WHERE grammar_id=?", (lid,))]
    p["sentence_grammar"] = {"repoint": [s for s in mine if s not in have],
                             "drop_dup": [s for s in mine if s in have]}

    tags = []
    for sid, slug, tj in con.execute("SELECT id, slug, tags FROM sentence WHERE tags LIKE ?",
                                     (f'%"{lkey}"%',)):
        cur = jloads(tj, []) or []
        if lkey not in cur:
            continue
        new, seen = [], set()
        for t in cur:
            t2 = wkey if t == lkey else t
            if t2 not in seen:
                seen.add(t2)
                new.append(t2)
        tags.append((sid, slug, cur, new))
    p["sentence_tags"] = tags

    wl = {r[0] for r in con.execute("SELECT lesson_id FROM lesson_unlocks WHERE ref=?", (wslug,))}
    ml = [r[0] for r in con.execute("SELECT lesson_id FROM lesson_unlocks WHERE ref=?", (lslug,))]
    p["lesson_unlocks"] = {"repoint": [x for x in ml if x not in wl],
                           "drop_dup": [x for x in ml if x in wl]}

    wi = {r[0] for r in con.execute(
        "SELECT lesson_id FROM lesson_introduces WHERE member_type='grammar' AND member_id=?", (wid,))}
    mi = [r[0] for r in con.execute(
        "SELECT lesson_id FROM lesson_introduces WHERE member_type='grammar' AND member_id=?", (lid,))]
    p["lesson_introduces"] = {"repoint": [x for x in mi if x not in wi],
                              "drop_dup": [x for x in mi if x in wi]}

    wn = {(r[0], r[1]) for r in con.execute("SELECT lesson_id, need_type FROM lesson_needs WHERE ref=?", (wslug,))}
    mn = [(r[0], r[1]) for r in con.execute("SELECT lesson_id, need_type FROM lesson_needs WHERE ref=?", (lslug,))]
    p["lesson_needs"] = {"repoint": [x for x in mn if x not in wn],
                         "drop_dup": [x for x in mn if x in wn]}

    wf = {r[0] for r in con.execute(
        "SELECT family_id FROM family_member WHERE member_type='grammar' AND member_id=?", (wid,))}
    mf = [(r[0], r[1], r[2], r[3]) for r in con.execute(
        "SELECT family_id, intra_order, is_core, note_pt FROM family_member "
        "WHERE member_type='grammar' AND member_id=?", (lid,))]
    p["family_member"] = {"repoint": [x for x in mf if x[0] not in wf],
                          "drop_dup": [x for x in mf if x[0] in wf]}

    we = {r[0] for r in con.execute(
        "SELECT exercise_id FROM exercise_item WHERE member_type='grammar' AND member_id=?", (wid,))}
    me = [r[0] for r in con.execute(
        "SELECT exercise_id FROM exercise_item WHERE member_type='grammar' AND member_id=?", (lid,))]
    p["exercise_item"] = {"repoint": [x for x in me if x not in we],
                          "drop_dup": [x for x in me if x in we]}

    rel_out = [(r[0], r[1]) for r in con.execute(
        "SELECT related_grammar_id, relation FROM grammar_related WHERE grammar_id=?", (lid,))]
    rel_in = [(r[0], r[1]) for r in con.execute(
        "SELECT grammar_id, relation FROM grammar_related WHERE related_grammar_id=?", (lid,))]
    p["grammar_related"] = {"out": rel_out, "in": rel_in}
    p["lesson_bodies"] = plan_lesson_bodies(con, lslug, wslug)
    p["cumulative_known_set"] = plan_cumulative(con, lslug, wslug)
    return p


def plan_lesson_bodies(con: sqlite3.Connection, lslug: str, wslug: str) -> list[tuple]:
    """`<grammar ref="…"/>` and `<check item-ref="…">` inside the AUTHORED lesson body.

    The body a learner reads is `localized_text(lesson, body, <locale>)`, not `lesson.body_pt`, and
    `export_course.py` renders it verbatim. Leave the loser's address in it and `audit_export_refs`
    reports "body <grammar ref='gram:gp'/> not in exported corpus" while `validate_lesson_gating`
    reports the same reference as never unlocked — the body would cite a record the course no longer
    publishes. Only the ADDRESS moves; not one word of the pt-BR prose is touched.
    """
    out = []
    for eid, field, locale, val in con.execute(
            "SELECT entity_id, field, locale, value FROM localized_text "
            "WHERE entity_type='lesson' AND field='body' AND value LIKE ?", (f'%"{lslug}"%',)):
        new = val
        hits = 0
        for attr in ("ref", "item-ref"):
            needle = f'{attr}="{lslug}"'
            hits += new.count(needle)
            new = new.replace(needle, f'{attr}="{wslug}"')
        if hits and new != val:
            slug = con.execute("SELECT slug FROM lesson WHERE id=?", (eid,)).fetchone()
            out.append((eid, field, locale, new, slug[0] if slug else str(eid), hits))
    return out


def plan_cumulative(con: sqlite3.Connection, lslug: str, wslug: str) -> list[tuple]:
    """`lesson.cumulative_known_set["grammar"]` — the stored "known by here" set.

    A pure derivation of `lesson_unlocks` (ingest/load_lessons.recompute_cumulative), and
    export_course.py RE-DERIVES it at export time rather than reading this column — so the published
    course tree is correct the moment the unlock row moves, with or without this. The stored copy is
    not: `ingest/build_readings.py` selects its candidate sentences against it and
    `ingest/mine_n3_targets.py` measures its i+1 budget against it, both by membership. Leaving a
    retired slug there means a later builder counts a record the registry no longer publishes as
    something the learner knows.

    Both merges unlock loser and survivor from the SAME lesson, so the survivor is already in every
    set the loser is in and the loser's entry is simply DROPPED — which is exactly what a recompute
    would produce once the unlock row is gone. The in-place rewrite is the safety net for a future
    merge whose lesson unlocked only the loser.
    """
    out = []
    for lid, slug, raw in con.execute(
            "SELECT id, slug, cumulative_known_set FROM lesson WHERE cumulative_known_set LIKE ?",
            (f'%"{lslug}"%',)):
        cks = jloads(raw)
        if not isinstance(cks, dict):
            continue
        g = list(cks.get("grammar") or [])
        if lslug not in g:
            continue
        if wslug in g:
            new_g, how = [x for x in g if x != lslug], "dropped"
        else:
            new_g, how = [wslug if x == lslug else x for x in g], "rewritten in place"
        out.append((lid, slug, jdumps({**cks, "grammar": new_g}), how))
    return out


def check_preconditions(name: str, plan: dict, expect: dict) -> list[str]:
    got = {
        "sentence_grammar": len(plan["sentence_grammar"]["repoint"]) + len(plan["sentence_grammar"]["drop_dup"]),
        "sentence_grammar_overlap": len(plan["sentence_grammar"]["drop_dup"]),
        "sentence_tags": len(plan["sentence_tags"]),
        "lesson_unlocks": len(plan["lesson_unlocks"]["repoint"]) + len(plan["lesson_unlocks"]["drop_dup"]),
        "lesson_unlocks_dup": len(plan["lesson_unlocks"]["drop_dup"]),
        "lesson_introduces": len(plan["lesson_introduces"]["repoint"]) + len(plan["lesson_introduces"]["drop_dup"]),
        "lesson_introduces_dup": len(plan["lesson_introduces"]["drop_dup"]),
        "lesson_needs": len(plan["lesson_needs"]["repoint"]) + len(plan["lesson_needs"]["drop_dup"]),
        "family_member": len(plan["family_member"]["repoint"]) + len(plan["family_member"]["drop_dup"]),
        "family_member_dup": len(plan["family_member"]["drop_dup"]),
        "exercise_item": len(plan["exercise_item"]["repoint"]) + len(plan["exercise_item"]["drop_dup"]),
        "exercise_item_dup": len(plan["exercise_item"]["drop_dup"]),
        "grammar_related": len(plan["grammar_related"]["out"]) + len(plan["grammar_related"]["in"]),
        "cumulative_known_set": len(plan["cumulative_known_set"]),
    }
    return [f"{name}: {k} is {got[k]}, the migration was written against {v}"
            for k, v in expect.items() if got.get(k) != v]


def apply_edges(con: sqlite3.Connection, L: sqlite3.Row, W: sqlite3.Row, plan: dict) -> None:
    lid, wid, lslug, wslug = L["id"], W["id"], L["slug"], W["slug"]
    for sid in plan["sentence_grammar"]["drop_dup"]:
        con.execute("DELETE FROM sentence_grammar WHERE grammar_id=? AND sentence_id=?", (lid, sid))
    for sid in plan["sentence_grammar"]["repoint"]:
        con.execute("UPDATE sentence_grammar SET grammar_id=? WHERE grammar_id=? AND sentence_id=?",
                    (wid, lid, sid))
    for sid, _slug, _cur, new in plan["sentence_tags"]:
        con.execute("UPDATE sentence SET tags=? WHERE id=?", (jdumps(new), sid))
    for lesson_id in plan["lesson_unlocks"]["drop_dup"]:
        con.execute("DELETE FROM lesson_unlocks WHERE lesson_id=? AND ref=?", (lesson_id, lslug))
    for lesson_id in plan["lesson_unlocks"]["repoint"]:
        con.execute("UPDATE lesson_unlocks SET ref=? WHERE lesson_id=? AND ref=?",
                    (wslug, lesson_id, lslug))
    for lesson_id in plan["lesson_introduces"]["drop_dup"]:
        con.execute("DELETE FROM lesson_introduces WHERE lesson_id=? AND member_type='grammar' "
                    "AND member_id=?", (lesson_id, lid))
    for lesson_id in plan["lesson_introduces"]["repoint"]:
        con.execute("UPDATE lesson_introduces SET member_id=? WHERE lesson_id=? AND "
                    "member_type='grammar' AND member_id=?", (wid, lesson_id, lid))
    for lesson_id, need_type in plan["lesson_needs"]["drop_dup"]:
        con.execute("DELETE FROM lesson_needs WHERE lesson_id=? AND need_type=? AND ref=?",
                    (lesson_id, need_type, lslug))
    for lesson_id, need_type in plan["lesson_needs"]["repoint"]:
        con.execute("UPDATE lesson_needs SET ref=? WHERE lesson_id=? AND need_type=? AND ref=?",
                    (wslug, lesson_id, need_type, lslug))
    for fid, *_ in plan["family_member"]["drop_dup"]:
        con.execute("DELETE FROM family_member WHERE family_id=? AND member_type='grammar' AND "
                    "member_id=?", (fid, lid))
    for fid, *_ in plan["family_member"]["repoint"]:
        con.execute("UPDATE family_member SET member_id=? WHERE family_id=? AND member_type='grammar' "
                    "AND member_id=?", (wid, fid, lid))
    for eid in plan["exercise_item"]["drop_dup"]:
        con.execute("DELETE FROM exercise_item WHERE exercise_id=? AND member_type='grammar' AND "
                    "member_id=?", (eid, lid))
    for eid in plan["exercise_item"]["repoint"]:
        con.execute("UPDATE exercise_item SET member_id=? WHERE exercise_id=? AND "
                    "member_type='grammar' AND member_id=?", (wid, eid, lid))
    for other, relation in plan["grammar_related"]["out"]:
        con.execute("DELETE FROM grammar_related WHERE grammar_id=? AND related_grammar_id=? AND "
                    "relation=?", (lid, other, relation))
        if other != wid:
            con.execute("INSERT OR IGNORE INTO grammar_related(grammar_id, related_grammar_id, "
                        "relation) VALUES (?,?,?)", (wid, other, relation))
    for other, relation in plan["grammar_related"]["in"]:
        con.execute("DELETE FROM grammar_related WHERE grammar_id=? AND related_grammar_id=? AND "
                    "relation=?", (other, lid, relation))
        if other != wid:
            con.execute("INSERT OR IGNORE INTO grammar_related(grammar_id, related_grammar_id, "
                        "relation) VALUES (?,?,?)", (other, wid, relation))
    for lid, _slug, new, _how in plan["cumulative_known_set"]:
        con.execute("UPDATE lesson SET cumulative_known_set=? WHERE id=?", (new, lid))
    for eid, field, locale, new, _slug, _hits in plan["lesson_bodies"]:
        con.execute("UPDATE localized_text SET value=? WHERE entity_type='lesson' AND entity_id=? "
                    "AND field=? AND locale=?", (new, eid, field, locale))


# ==================================================================================================
# authoring source — research/derived/lessons/*.json
# ==================================================================================================
def rewrite_authoring(root: Path, merges: list[dict], apply: bool) -> list[dict]:
    """Re-point the loader's own inputs, so the next loader+export cycle cannot reintroduce the loser."""
    changes: list[dict] = []
    lessons = root / "research" / "derived" / "lessons"
    if not lessons.is_dir():
        print(f"  ! no {lessons} — authoring source not rewritten")
        return changes
    lmap = {m["loser"]: m["winner"] for m in merges}
    for path in sorted(lessons.glob("*.json")):
        raw = path.read_text(encoding="utf-8")
        if not any(k in raw for k in lmap):
            continue
        doc = json.loads(raw)
        acts: list[str] = []

        for lk, wk in lmap.items():
            lslug, wslug = f"gram:{lk}", f"gram:{wk}"

            for listname in ("unlocks", "needs", "feature_unlocks"):
                items = doc.get(listname)
                if not isinstance(items, list):
                    continue
                has_w = any(isinstance(i, dict) and i.get("ref") == wslug for i in items)
                kept = []
                for i in items:
                    if isinstance(i, dict) and i.get("ref") == lslug:
                        if has_w:
                            acts.append(f"{listname}: dropped duplicate {lslug} ({wslug} already there)")
                            continue
                        i = {**i, "ref": wslug}
                        has_w = True
                        acts.append(f"{listname}: {lslug} -> {wslug}")
                    kept.append(i)
                doc[listname] = kept

            for n, ex in enumerate(doc.get("exercises") or []):
                refs = ex.get("item_refs")
                if not isinstance(refs, list):
                    continue
                has_w = any(isinstance(r, dict) and r.get("ref") == wk for r in refs)
                kept = []
                for r in refs:
                    if isinstance(r, dict) and r.get("ref") == lk and r.get("type") == "grammar":
                        if has_w:
                            acts.append(f"exercises[{n}].item_refs: dropped duplicate {lk}")
                            continue
                        r = {**r, "ref": wk}
                        has_w = True
                        acts.append(f"exercises[{n}].item_refs: {lk} -> {wk}")
                    kept.append(r)
                ex["item_refs"] = kept

            body = doc.get("body")
            if isinstance(body, str):
                for attr in ("ref", "item-ref"):
                    needle = f'{attr}="{lslug}"'
                    n = body.count(needle)
                    if n:
                        body = body.replace(needle, f'{attr}="{wslug}"')
                        acts.append(f'body: {n}x {attr}="{lslug}" -> "{wslug}"')
                doc["body"] = body

        # Nothing may be left addressing a loser. A silent survivor here is how the archived repair
        # got reintroduced, so this is a hard stop rather than a warning.
        after = json.dumps(doc, ensure_ascii=False)
        for lk in lmap:
            for stray in (f'"gram:{lk}"', f'ref="gram:{lk}"', f'"ref": "{lk}"'):
                if stray in after:
                    die(f"{path.name} still carries {stray} after the rewrite — an address shape this "
                        f"script does not know about. Fix the rewrite, do not ship a half-migration.")
        if acts:
            changes.append({"file": path.relative_to(root).as_posix(), "actions": acts})
            if apply:
                # Re-serialise in the file's OWN format. json.dumps' defaults would reindent all ~380
                # lines and (on Windows) rewrite every ending to CRLF, so the diff a reviewer reads
                # would be the whole file instead of the four addresses that moved — and the next
                # reader could not tell a migration from a reformat. newline="\n" is not cosmetic:
                # these files are read back by scripts/ingest/load_lessons.py and compared by
                # validate_index_rebuildable.py byte for byte.
                path.write_text(json.dumps(doc, ensure_ascii=False, indent=file_indent(raw)) + "\n",
                                encoding="utf-8", newline="\n")
    return changes


# ==================================================================================================
def is_applied(con: sqlite3.Connection, m: dict) -> bool:
    if not has_column(con, "grammar_point", "deprecated_by"):
        return False
    r = con.execute("SELECT deprecated_by FROM grammar_point WHERE key=?", (m["loser"],)).fetchone()
    return bool(r and r[0])


def main() -> int:
    dbpath = db_target(ROOT / "db" / "corpus.sqlite")
    root_override = take_flag("--root")
    root = Path(root_override) if root_override else ROOT
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--apply", action="store_true", help="write the merge (default: dry run)")
    ap.add_argument("--check", action="store_true", help="verify the merge is applied; exit 1 if not")
    ap.add_argument("--append-prose", action="store_true",
                    help="also concatenate salvaged prose onto the survivor (off by default)")
    args = ap.parse_args()

    con = sqlite3.connect(dbpath)
    con.execute("PRAGMA busy_timeout=60000")
    con.row_factory = sqlite3.Row

    print(f"db   : {dbpath}")
    print(f"root : {root}")
    print(f"mode : {'--check' if args.check else ('--apply' if args.apply else 'dry run')}")
    print()
    print("NOT MERGED (same defect class, deliberately out of scope):")
    for what, why in DECLINED:
        print(f"  - {what}\n      {why}")
    print()

    # ---- --check ---------------------------------------------------------------------------------
    if args.check:
        bad = []
        for m in MERGES:
            L = grow(con, m["loser"])
            W = grow(con, m["winner"])
            if not is_applied(con, m):
                bad.append(f"{m['loser']}: grammar_point.deprecated_by is not set")
                continue
            if L["deprecated_by"] != W["slug"]:
                bad.append(f"{m['loser']}: deprecated_by is {L['deprecated_by']!r}, expected {W['slug']!r}")
            for table, where in (("sentence_grammar", "grammar_id=?"),
                                 ("lesson_introduces", "member_type='grammar' AND member_id=?"),
                                 ("family_member", "member_type='grammar' AND member_id=?"),
                                 ("exercise_item", "member_type='grammar' AND member_id=?")):
                n = con.execute(f"SELECT COUNT(*) FROM {table} WHERE {where}", (L["id"],)).fetchone()[0]
                if n:
                    bad.append(f"{m['loser']}: {n} row(s) still in {table}")
            n = con.execute("SELECT COUNT(*) FROM lesson_unlocks WHERE ref=?", (L["slug"],)).fetchone()[0]
            if n:
                bad.append(f"{m['loser']}: {n} lesson_unlocks row(s) still point at {L['slug']}")
            n = con.execute("SELECT COUNT(*) FROM sentence WHERE tags LIKE ?",
                            (f'%"{m["loser"]}"%',)).fetchone()[0]
            if n:
                bad.append(f"{m['loser']}: {n} sentence(s) still tagged {m['loser']!r}")
            n = con.execute("SELECT COUNT(*) FROM lesson WHERE cumulative_known_set LIKE ?",
                            (f'%"{L["slug"]}"%',)).fetchone()[0]
            if n:
                bad.append(f"{m['loser']}: {n} lesson(s) still carry {L['slug']} in the stored "
                           f"cumulative_known_set")
            for _e, _f, loc_, _new, slug_, hits_ in plan_lesson_bodies(con, L["slug"], W["slug"]):
                bad.append(f"{m['loser']}: lesson body {slug_} [{loc_}] still carries {hits_} "
                           f"{L['slug']} address(es)")
        stray = rewrite_authoring(root, MERGES, apply=False)
        for c in stray:
            bad.append(f"authoring source not migrated: {c['file']} — {c['actions']}")
        if bad:
            print("NOT APPLIED:")
            for b in bad:
                print(f"  FAIL {b}")
            return 1
        print("OK — every merge in MERGES is applied, in the DB and in the authoring source.")
        return 0

    # ---- plan / apply ----------------------------------------------------------------------------
    ledger: dict = {"generated_by": "scripts/migrate_grammar_merge.py",
                    "what_this_is": (
                        "Owner decision A3 (W08): duplicate-identity grammar points merged with no "
                        "content loss. The loser row is never deleted — it keeps every field it had "
                        "and gains grammar_point.deprecated_by. `appended` is what this migration "
                        "wrote onto the survivor; `salvage` is loser content a machine must not fold "
                        "in on its own, kept verbatim for the teacher-review loop; `refused` is what "
                        "the migration declined to append, with the reason."),
                    "declined_collisions": [{"pair": w, "why": y} for w, y in DECLINED],
                    "merges": []}

    todo = [m for m in MERGES if not is_applied(con, m)]
    done = [m for m in MERGES if is_applied(con, m)]
    for m in done:
        print(f"SKIP {m['loser']} -> {m['winner']}: already merged (deprecated_by is set). "
              f"Nothing to do; this script is idempotent.")
    if not todo:
        # The DB is done, but the authoring source is a separate layer with its own failure mode:
        # `archive/ARCHIVE.md` records a repair that wrote only the DB and left the queue carrying
        # the old values, where "one loader+export cycle would have reintroduced them". So a re-run
        # still re-proves (and, with --apply, heals) research/derived/lessons/ before it exits.
        stray = rewrite_authoring(root, MERGES, apply=args.apply)
        for c in stray:
            print(f"  authoring {c['file']}")
            for a in c["actions"]:
                print(f"      {a}")
        print("\nNothing to apply." if not stray else
              "\nDB already merged; the authoring source still carried the loser and was "
              "re-pointed." if args.apply else
              "\nDB already merged but the authoring source has NOT been re-pointed — run --apply.")
        return 0

    if args.apply and not has_column(con, "grammar_point", "deprecated_by"):
        con.execute("ALTER TABLE grammar_point ADD COLUMN deprecated_by TEXT")
        print("schema: grammar_point.deprecated_by added (TEXT, survivor slug; NULL = live record)")

    failures: list[str] = []
    for m in todo:
        L, W = grow(con, m["loser"]), grow(con, m["winner"])
        print("=" * 98)
        print(f"MERGE {L['slug']} (id {L['id']}) -> {W['slug']} (id {W['id']})   [{m['verdict']}]")
        print(f"  why: {m['why']}")
        content = diff_content(con, L, W)
        plan = plan_edges(con, L, W)
        # A PARTIAL index (validate_index_rebuildable --quick reconstructs the grammar family only)
        # has empty lesson / sentence / exam tables, so every row-count expectation written
        # against the real index is out of scope there — the plan functions simply find no rows
        # to move. Preconditions are a drift check for the REAL index and the full rebuild, both
        # of which populate every table; a partial index is recognised by its empty lesson table.
        expect = m["expect"]
        if con.execute("SELECT COUNT(*) FROM lesson").fetchone()[0] == 0:
            print(f"  {m['loser']}: partial index (no lessons) — preconditions out of scope")
            expect = {}
        pre = check_preconditions(m["loser"], plan, expect)
        if pre:
            for line in pre:
                print(f"  PRECONDITION FAILED: {line}")
            failures += pre
            continue

        print("  -- content-loss check ------------------------------------------------------------")
        for line in content["covered"]:
            print(f"     ok      {line}")
        for col, val in content["append"].items():
            print(f"     APPEND  grammar_point.{col} = {str(val)[:160]}")
        for loc in content["localized"]:
            print(f"     APPEND  localized_text {loc['field']}/{loc['locale']} ({loc['mode']}): "
                  f"{loc['why']}")
        for s in content["salvage"]:
            print(f"     SALVAGE {s['field']}: {s['why']}")
        for r in content["refused"]:
            print(f"     REFUSED {r}")
        print("  -- edges -------------------------------------------------------------------------")
        print(f"     sentence_grammar  repoint {len(plan['sentence_grammar']['repoint'])}, "
              f"drop-as-duplicate {len(plan['sentence_grammar']['drop_dup'])}")
        print(f"     sentence.tags     rewrite {len(plan['sentence_tags'])}")
        print(f"     lesson_unlocks    repoint {len(plan['lesson_unlocks']['repoint'])}, "
              f"DROP duplicate unlock {len(plan['lesson_unlocks']['drop_dup'])} "
              f"(same lesson already unlocks {W['slug']})")
        print(f"     lesson_introduces repoint {len(plan['lesson_introduces']['repoint'])}, "
              f"drop-as-duplicate {len(plan['lesson_introduces']['drop_dup'])}")
        print(f"     lesson_needs      repoint {len(plan['lesson_needs']['repoint'])}, "
              f"drop-as-duplicate {len(plan['lesson_needs']['drop_dup'])}")
        print(f"     family_member     repoint {[f[0] for f in plan['family_member']['repoint']]}, "
              f"drop-as-duplicate {[f[0] for f in plan['family_member']['drop_dup']]}")
        print(f"     exercise_item     repoint {len(plan['exercise_item']['repoint'])}, "
              f"drop-as-duplicate {len(plan['exercise_item']['drop_dup'])}")
        print(f"     grammar_related   out {len(plan['grammar_related']['out'])}, "
              f"in {len(plan['grammar_related']['in'])}")
        cks_plan = plan["cumulative_known_set"]
        cks_how = {h for *_x, h in cks_plan}
        print(f"     cumulative_known_set {len(cks_plan)} lesson(s) {sorted(cks_how)} "
              f"(stored copy only; export_course.py re-derives it from lesson_unlocks)")
        for _eid, _f, loc_, _new, slug_, hits_ in plan["lesson_bodies"]:
            print(f"     lesson body       {slug_} [{loc_}]: {hits_} address(es) re-pointed "
                  f"(prose untouched)")

        entry = {
            "loser": L["slug"], "loser_key": L["key"], "winner": W["slug"], "winner_key": W["key"],
            "verdict": m["verdict"], "why": m["why"],
            "appended": {k: v for k, v in content["append"].items()},
            "appended_localized": content["localized"],
            "covered": content["covered"],
            "salvage": content["salvage"],
            "refused": content["refused"],
            "edges": {
                "sentence_grammar_repointed": len(plan["sentence_grammar"]["repoint"]),
                "sentence_grammar_dropped_as_duplicate": len(plan["sentence_grammar"]["drop_dup"]),
                "sentence_tags_rewritten": [t[1] for t in plan["sentence_tags"]],
                "lesson_unlocks_dropped_as_duplicate": len(plan["lesson_unlocks"]["drop_dup"]),
                "lesson_unlocks_repointed": len(plan["lesson_unlocks"]["repoint"]),
                "lesson_introduces_dropped_as_duplicate": len(plan["lesson_introduces"]["drop_dup"]),
                "lesson_introduces_repointed": len(plan["lesson_introduces"]["repoint"]),
                "family_member_repointed": [f[0] for f in plan["family_member"]["repoint"]],
                "family_member_dropped_as_duplicate": [f[0] for f in plan["family_member"]["drop_dup"]],
                "exercise_item_repointed": len(plan["exercise_item"]["repoint"]),
                "exercise_item_dropped_as_duplicate": len(plan["exercise_item"]["drop_dup"]),
                "lesson_body_addresses_repointed": {b[4]: b[5] for b in plan["lesson_bodies"]},
                "cumulative_known_set_lessons": len(plan["cumulative_known_set"]),
            },
        }
        ledger["merges"].append(entry)

        if not args.apply:
            continue

        for col, val in content["append"].items():
            con.execute(f"UPDATE grammar_point SET {col}=? WHERE id=?", (val, W["id"]))
        for loc in content["localized"]:
            con.execute(
                "INSERT INTO localized_text(entity_type, entity_id, field, locale, value, is_list, layer) "
                "VALUES ('grammar_point',?,?,?,?,?,?) "
                "ON CONFLICT(entity_type, entity_id, field, locale) DO UPDATE SET value=excluded.value",
                (W["id"], loc["field"], loc["locale"], loc["value"], loc["is_list"], loc["layer"]))
        if args.append_prose:
            for s in content["salvage"]:
                if "/" not in s["field"]:
                    continue
                field, locale = s["field"].split("/", 1)
                if field not in PROSE_FIELDS:
                    continue
                cur = con.execute(
                    "SELECT value FROM localized_text WHERE entity_type='grammar_point' AND "
                    "entity_id=? AND field=? AND locale=?", (W["id"], field, locale)).fetchone()
                merged = f"{cur[0]} {s['value']}" if cur and cur[0] else s["value"]
                con.execute(
                    "INSERT INTO localized_text(entity_type, entity_id, field, locale, value, is_list, layer) "
                    "VALUES ('grammar_point',?,?,?,?,0,'C') "
                    "ON CONFLICT(entity_type, entity_id, field, locale) DO UPDATE SET value=excluded.value",
                    (W["id"], field, locale, merged))
                print(f"     APPENDED PROSE into {field}/{locale} (--append-prose)")
        apply_edges(con, L, W, plan)
        # The survivor now carries merged content that a human has not read. It goes back into the
        # teacher-review queue (CLAUDE.md 1.8) rather than inheriting the loser's sign-off.
        con.execute("UPDATE grammar_point SET needs_review=1 WHERE id=?", (W["id"],))
        con.execute("UPDATE grammar_point SET deprecated_by=? WHERE id=?", (W["slug"], L["id"]))
        print(f"  retired: {L['slug']}.deprecated_by = {W['slug']}  (row KEPT, nothing deleted)")

    if failures:
        con.rollback()
        die("preconditions failed; nothing was written:\n    " + "\n    ".join(failures))

    print("=" * 98)
    changes = rewrite_authoring(root, MERGES, apply=args.apply)
    for c in changes:
        print(f"  authoring {c['file']}")
        for a in c["actions"]:
            print(f"      {a}")
    ledger["authoring_source"] = changes

    if args.apply:
        con.commit()
        out = root / LEDGER
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(ledger, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
        print(f"\nledger: {LEDGER}")
        print("applied. Re-export corpus/ and course/: export_corpus.py drops the deprecated rows "
              "from the published registry and writes the redirect to corpus/grammar_deprecated.json "
              "(registered in design/generated_artifacts.json); build_capabilities.py drops the "
              "retired keys from corpus/capabilities/registry.json.")
    else:
        print("\ndry run — nothing written. Re-run with --apply.")
    con.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
