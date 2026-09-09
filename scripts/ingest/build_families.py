#!/usr/bin/env python3
"""P4 — the structural, CLASS-derived families (spec §5.6, acceptance #9).

Derives, with zero authoring, from Layer-A fields alone: the six conjugation/adjective classes
(`vocab.verb_class` / `vocab.adj_class`, both JMdict POS) and the counter set
(`vocab.lexeme_type`). Labels and governing rules are short pt-BR Layer-C stubs (needs_review).

W11b — THIS SCRIPT USED TO BE "IDEMPOTENT" BY REFUSING TO RUN
-------------------------------------------------------------
It opened with `if COUNT(*) FROM family > 0: skip`, so after its single successful run it was a
no-op forever. It executed once, before the N3 registries arrived and before several placement
passes moved the course, and the layer froze there: the conjugation classes covered n5/n4 only, at
514 memberships against the 1,167 records their own JMdict class matches
(`research/reports/family_layer_rebuild.md` §2.5, §2.6).

It now RECOMPUTES through `scripts/familylib.py`. Every family whose slug this builder generates is
rewritten in place, and a slug it used to generate but no longer does is RETIRED via
`family.deprecated_by` rather than deleted, because a family slug is a published address.
Idempotence is now "running it twice gives the same answer", which is the property the export and
`scripts/validate/validate_index_rebuildable.py` need; the old kind was "running it twice does
nothing", which is how the layer went stale in silence.

The scope is read from `course_module.level` — the levels the project actually teaches — so the
classes widen to N2/N1 the day those courses exist, with no edit here (CLAUDE.md §1.6).

OWNER DECISION D14 — THE KANJI-COMPONENT FAMILIES ARE GONE
-----------------------------------------------------------
This builder used to materialize one family per kanji component appearing in >= 4 leveled kanji. It
was a CACHE of `kanji_component`, the table `kanji.components` is exported from, and nothing kept it
warm: 0 of 51 still equalled the derived set and 4,868 memberships were missing. `design/schema_v2.md`
§C answers the component query directly — `kanji_component JOIN kanji ORDER BY freq_rank` — so the
cache was never load-bearing. APP_PLAN D14 drops it. The 51 slugs are retired with
`deprecated_by = "kanji.components"`, which is where the answer lives; a component "family" page is
a view over that field, not a second copy of it that can drift.

Run with venv python.
"""
from __future__ import annotations

import sqlite3
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
# W01: honour --db / $YOMINEKO_DB so a rebuild can target a scratch DB (scripts/dbtarget.py).
import sys as _sys, pathlib as _pl  # noqa: E402
_sys.path.append(str(next(p for p in _pl.Path(__file__).resolve().parents if p.name == "scripts")))
from dbtarget import db_target  # noqa: E402
from familylib import member_levels, recompute, retire_unbuilt, taught_levels  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
DB = db_target(ROOT / "db" / "corpus.sqlite")

# slug, rank, label pt-BR, label en, governing rule pt-BR, governing rule en, column, value
CONJ = [
    ("grp:godan", 1, "Verbos godan (う)", "Godan verbs (う)",
     "Verbos do grupo I: a última sílaba está na coluna -u (く, む, る, す…) e muda de coluna "
     "conforme a forma (negativa →あ, ます →い, vontade →お etc.).",
     "Group I verbs: the last syllable is in the -u column (く, む, る, す…) and shifts column "
     "according to the form (negative →あ, ます →い, volitional →お, etc.).",
     "verb_class", "godan"),
    ("grp:ichidan", 2, "Verbos ichidan (る)", "Ichidan verbs (る)",
     "Verbos do grupo II: terminam em -eru/-iru e conjugam tirando る e acrescentando a "
     "terminação (食べる→食べます, 食べない, 食べて).",
     "Group II verbs: end in -eru/-iru and conjugate by dropping る and adding the ending "
     "(食べる→食べます, 食べない, 食べて).",
     "verb_class", "ichidan"),
    ("grp:suru-irregular", 6, "Verbo irregular する", "Irregular verb する",
     "する e os compostos 〜する são irregulares (し-, さ-, せ-); base de muitos verbos a partir "
     "de substantivos (勉強する).",
     "する and the 〜する compounds are irregular (し-, さ-, せ-); they form the basis of many "
     "verbs derived from nouns (勉強する).",
     "verb_class", "suru_irregular"),
    ("grp:kuru-irregular", 7, "Verbo irregular 来る", "Irregular verb 来る",
     "来る é irregular: a leitura muda na flexão, 来(く)る → 来(き)ます → 来(こ)ない.",
     "来る is irregular: the reading changes in conjugation, 来(く)る → 来(き)ます → 来(こ)ない.",
     "verb_class", "kuru_irregular"),
    ("grp:i-adj", 4, "Adjetivos い", "i-adjectives",
     "Adjetivos terminados em い conjugam no próprio adjetivo (高い→高くない→高かった); não usam です "
     "para negar/passar ao passado.",
     "い-adjectives conjugate on the adjective itself (高い→高くない→高かった); they do not use "
     "です to negate or form the past.",
     "adj_class", "i_adj"),
    ("grp:na-adj", 5, "Adjetivos な", "na-adjectives",
     "Adjetivos な comportam-se como substantivos: usam な antes do substantivo e だ/です para "
     "tempo/negação (静かな, 静かじゃない).",
     "な-adjectives behave like nouns: they use な before the noun and だ/です for "
     "tense/negation (静かな, 静かじゃない).",
     "adj_class", "na_adj"),
]

# `grp:counters` stays a `function_set` after W11b's rename of the topic buckets. The rename freed
# that type from the 46 families that were only ever "the grammar of topic N"; what is left in it is
# a genuine functional grouping with a real governing rule, derived from `vocab.lexeme_type`. The
# authored communicative-function families of W39 join it here.
COUNTERS = ("grp:counters", "function_set", 8, "Contadores (助数詞)", "Counters (助数詞)",
            "O contador é escolhido pela forma/categoria do objeto; muitos sofrem rendaku "
            "(本: いっぽん/さんぼん). Fallback nativo ひとつ–とお para 1–9.",
            "The counter is chosen by the object's shape/category; many undergo rendaku "
            "(本: いっぽん/さんぼん). The native fallback ひとつ–とお for 1–9.")

# Owner decision D14: the materialized component families are a cache of `kanji.components` and are
# retired, not rebuilt. The redirect names the store that answers the question instead of a family.
COMPONENT_PREFIX = "grp:kanji-comp-"
COMPONENT_SUCCESSOR = "kanji.components"


def main() -> int:
    con = sqlite3.connect(DB)
    con.execute("PRAGMA foreign_keys = ON;")
    cur = con.cursor()
    levels = taught_levels(con)
    ph = ",".join("?" * len(levels))
    built: set = set()

    # ---- conjugation + adjective classes -------------------------------------------------------
    for slug, rank, label_pt, label_en, rule_pt, rule_en, col, val in CONJ:
        rows = con.execute(
            f"SELECT id, freq_rank FROM vocab WHERE {col}=? AND level IN ({ph})",
            (val, *levels)).fetchall()
        members = [("vocab", vid, freq) for vid, freq in rows]
        recompute(con, cur, slug, "conjugation_class", rank, members, member_levels(con, members),
                  label_pt, label_en, rule_pt, rule_en)
        built.add(slug)

    # ---- counters ------------------------------------------------------------------------------
    slug, ftype, rank, label_pt, label_en, rule_pt, rule_en = COUNTERS
    rows = con.execute(
        f"SELECT id, freq_rank FROM vocab WHERE lexeme_type='counter' AND level IN ({ph})",
        tuple(levels)).fetchall()
    members = [("vocab", vid, freq) for vid, freq in rows]
    recompute(con, cur, slug, ftype, rank, members, member_levels(con, members),
              label_pt, label_en, rule_pt, rule_en)
    built.add(slug)

    # ---- D14: retire the component cache, and anything else this builder stopped deriving --------
    retired = retire_unbuilt(cur, exact=set(), prefixes=(COMPONENT_PREFIX,), built=built,
                             successor=COMPONENT_SUCCESSOR)

    con.commit()
    nf = con.execute("SELECT COUNT(*) FROM family WHERE deprecated_by IS NULL").fetchone()[0]
    nm = con.execute("SELECT COUNT(*) FROM family_member").fetchone()[0]
    ndep = con.execute("SELECT COUNT(*) FROM family WHERE deprecated_by IS NOT NULL").fetchone()[0]
    print(f"taught levels: {levels}")
    print(f"class families rebuilt: {len(built)}; newly retired this run: {retired}")
    print(f"families live: {nf} (deprecated {ndep}); memberships now: {nm}")
    con.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
