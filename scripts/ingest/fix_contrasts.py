#!/usr/bin/env python3
"""Fix the contrast_pair families + grammar_related: the earlier fuzzy LIKE match linked wrong
grammar points (は→'janai-dewa-nai', etc.). Rebuild with EXACT keys. Also add a particle_set family.
Idempotent. Run with venv python.

W11c: these three families are built through `familylib.recompute()` like every other derived
family. They used to have their own `fam()` helper, which wrote `spans_levels` as the literal
`["n5","n4"]` on INSERT and never touched it again on the UPDATE path. That is how the column came
to say `["n5","n4"]` in db/corpus.sqlite while `corpus/families/families.json` published `["n5"]`
for all three: the exporter derives the span from the members (export_corpus.py `_member_span`), the
column did not, and no gate compared them. `recompute()` is the single definition of "rewrite one
derived family in place", `member_levels()` the single definition of the span, and going through
both is what makes the two layers agree by construction rather than by luck. The English label and
governing rule move into the table here for the same reason `build_families.py` carries both
locales: the values used to arrive from a translation campaign whose inputs are `.gitignore`d, so a
from-scratch rebuild produced a family with no `en` anchor at all.
"""
from __future__ import annotations


import sqlite3
import sys
from pathlib import Path

# W01: honour --db / $YOMINEKO_DB so a rebuild can target a scratch DB (scripts/dbtarget.py).
import sys as _sys, pathlib as _pl  # noqa: E402
_sys.path.append(str(next(p for p in _pl.Path(__file__).resolve().parents if p.name == "scripts")))
from dbtarget import db_target  # noqa: E402
from familylib import member_levels, recompute  # noqa: E402

DB = db_target(Path(__file__).resolve().parents[2] / "db" / "corpus.sqlite")
sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]

PAIRS = [
    ("grp:wa-vs-ga", "は (tópico) × が (sujeito)", "は (topic) vs. が (subject)",
     ["wa-topic-marker", "ga"],
     "は marca o tópico/o já conhecido; が marca o sujeito/a informação nova.",
     "は marks the topic / what is already known; が marks the subject / the new information."),
    ("grp:ni-vs-de", "に × で (lugar)", "に vs. で (place)", ["ni", "de"],
     "に = lugar de existência/destino/tempo; で = lugar onde a AÇÃO acontece / meio.",
     "に = place of existence/destination/time; で = place where the ACTION happens / means."),
]
# W11b stage 3 — the family_related seed. `family_related(family_id, related_family_id, relation)`
# has existed as columns since 001_init.sql; nothing ever wrote a row, the exporter emitted no
# `related` field, and `contracts/family.schema.json` did not declare the property. So
# design/schema_v2.md §C's ONE concrete example edge —
#
#     group_related: {grp:wa-vs-ga, grp:particles-core, relation:"sub_family"}
#
# with both endpoints live in the shipped data, was the single most checkable promise the spec made
# and the data never kept. These two edges need no authoring: a contrast between two core particles
# is a narrower view of the core-particle set, which is what `sub_family` means. Everything else is
# authoring and belongs with `grammar.related[]` in one pass (W39), because the same knowledge
# answers both and splitting it across two passes guarantees they disagree.
#
# The conjugation-class parent the rebuild report also sketched (`grp:conjugation-classes`, six
# sub_family children) is NOT seeded here: it would require publishing a family with no members of
# its own, which every other gate and the prototype read as a defect, and inventing a record to
# exercise a field is a worse trade than shipping the field with two honest edges.
RELATED = [
    ("grp:wa-vs-ga", "grp:particles-core", "sub_family"),
    ("grp:ni-vs-de", "grp:particles-core", "sub_family"),
]

PARTICLE_SET = ("grp:particles-core", "Partículas essenciais", "Essential particles",
                ["wa-topic-marker", "ga", "o-wo", "ni", "de", "gp-27", "mo", "mo"],
                "As partículas de caso e tópico que cobrem ~90% do uso (は も の を が で に へ と から まで).",
                "The case and topic particles that cover ~90% of usage (は も の を が で に へ と から まで).")


def kid(con, key):
    r = con.execute("SELECT id FROM grammar_point WHERE key=?", (key,)).fetchone()
    return r[0] if r else None


def fam(con, cur, slug, ftype, label_pt, label_en, rank, rule_pt, rule_en, gids):
    """One derived family, through the shared spine — members, template text and the member-derived
    `spans_levels`, all rewritten in place. The sort key is the position in the builder's own key
    list, so `intra_order` and `is_core` come out exactly as the hand-rolled loop produced them."""
    members = [("grammar", g, i) for i, g in enumerate(gids)]
    return recompute(con, cur, slug, ftype, rank, members, member_levels(con, members),
                     label_pt, label_en, rule_pt, rule_en)


def main() -> int:
    con = sqlite3.connect(DB)
    cur = con.cursor()
    cur.execute("DELETE FROM grammar_related WHERE relation='contrast'")
    n_rel = 0
    for slug, label_pt, label_en, keys, rule_pt, rule_en in PAIRS:
        gids = [g for g in (kid(con, k) for k in keys) if g]
        fam(con, cur, slug, "contrast_pair", label_pt, label_en, 3, rule_pt, rule_en, gids)
        for a in gids:
            for b in gids:
                if a != b:
                    cur.execute("INSERT OR IGNORE INTO grammar_related (grammar_id,related_grammar_id,relation) "
                                "VALUES (?,?,?)", (a, b, "contrast"))
                    n_rel += cur.rowcount
    # particle_set
    slug, label_pt, label_en, keys, rule_pt, rule_en = PARTICLE_SET
    gids = []
    for k in dict.fromkeys(keys):
        g = kid(con, k)
        if g and g not in gids:
            gids.append(g)
    fam(con, cur, slug, "particle_set", label_pt, label_en, 2, rule_pt, rule_en, gids)
    # ---- family_related (W11b stage 3) ---------------------------------------------------------
    # Recomputed, not appended: the seed set is small and declarative, so the table is rewritten
    # from RELATED every run. Both endpoints must be live families or the edge is refused loudly —
    # a redirect target is not an endpoint.
    fid_of = {s: i for s, i in cur.execute(
        "SELECT slug, id FROM family WHERE deprecated_by IS NULL")}
    cur.execute("DELETE FROM family_related")
    for a, b, relation in RELATED:
        if a not in fid_of or b not in fid_of:
            raise SystemExit(f"fix_contrasts: family_related edge {a} -> {b} names a family that is "
                             f"not live; the seed set and the builders disagree")
        cur.execute("INSERT OR IGNORE INTO family_related (family_id,related_family_id,relation) "
                    "VALUES (?,?,?)", (fid_of[a], fid_of[b], relation))
    con.commit()
    print(f"contrast pairs fixed; grammar_related contrast links: {n_rel}; particle_set members: {len(gids)}")
    print(f"family_related edges: {len(RELATED)}")
    # verify
    for r in con.execute("SELECT g1.key,g2.key FROM grammar_related gr JOIN grammar_point g1 ON g1.id=gr.grammar_id "
                         "JOIN grammar_point g2 ON g2.id=gr.related_grammar_id WHERE gr.relation='contrast'"):
        print("  ", r)
    con.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
