#!/usr/bin/env python3
"""Repair the kanji records the QA sweep found wrong on the DATA side, and re-settle the two derived
fields that the example-word selector feeds.

`research/reports/qa_sweep/kanji_records_1.md` reports a flawless Layer-A spine (readings, strokes,
radicals all match KANJIDIC2 exactly) and a pedagogical selection layer that does not hold up. The
selector itself is fixed in `scripts/export/export_corpus.py` — it now ranks at-or-below-level words
first, sinks proper names, dedupes the per-occurrence `vocab_kanji` join and breaks ties on `slug`.
This script fixes what lives in the database rather than in a query:

  1. FOUR learner-facing strings (K11, K13a, K13d):
       kanji:屋  pt-BR meanings dropped "telhado" while the record's own example word 屋根 teaches it,
                 and `en` still leads with "roof" — the only pt-BR list in 280 records that loses a
                 concept its own examples carry.
       kanji:少  pt-BR order did not follow `en` (few/little/scarce), so index-wise the two locales of
                 the same locale-object disagreed about which gloss is which.
       kanji:台  "contador (sufixo p/ máquinas e veículos)" — an English-dictionary abbreviation in
                 pt-BR prose; corpus/vocab/n5.json already writes the same concept out in full.
       kanji:文  `irregular_note` opened lowercase (the only one of 47 that did) and told the learner
                 も is "listado como leitura deste kanji" when も is a NANORI, i.e. exactly the block
                 the record elsewhere describes as name-readings. kanji:木 has the same situation and
                 words it correctly; this now mirrors that wording.

  2. `kanji_reading.example_vocab_ids` brought back in step with the words each record now shows, as a
     delta against `research/derived/kanji_reading_groups.json` (drop a citation whose word left the
     list, attach a newly shown word to the reading the aligner files it under). The grouping is
     DERIVED FROM `example_words` — build_kanji_reading_groups.py aligns whole words against the list
     a record shows — so changing which ten words a record shows invalidates it, and the stored
     grouping went on citing 117 words the new selection no longer shows, which
     validate_kanji_reading_groups fails on, correctly. This is mechanical: no note is rewritten by
     it, so Layer-C prose and its review flags survive (that is the difference between this and
     re-running merge_kanji_reading_notes.py, which rewrites every note from the authoring batch).

  3. FIFTEEN reading notes whose claim about their own group the regrouping made false — see
     NOTE_FIXES. Thirteen said the group was empty above the word that just landed in it; two named
     the single word they held after that word left the record.

  4. `kanji_reading.introduced_at_level` re-derived by the documented rule (see derive_reading_tiers
     in scripts/ingest/reconcile_levels.py, which this calls rather than reimplements).

Run order — the grouping depends on the export, and the export reads the grouping back:

    python scripts/export/export_corpus.py             # new example_words
    python scripts/export/build_kanji_reading_groups.py # re-align them (mechanical)
    python scripts/apply_kanji_record_repairs.py        # this script
    python scripts/export/export_corpus.py             # publish the repaired records

Idempotent: text fixes are matched on their exact current value and skipped once applied, and the two
derived fields are recomputed from scratch, so a second run reports nothing to do.
Usage: apply_kanji_record_repairs.py [--check]
"""
from __future__ import annotations

import argparse
import json
import sqlite3
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / "db" / "corpus.sqlite"
GROUPS = ROOT / "research" / "derived" / "kanji_reading_groups.json"
NOTES_SRC = ROOT / "research" / "derived" / "kanji_reading_notes"
sys.path.insert(0, str(ROOT / "scripts" / "export"))
sys.path.insert(0, str(ROOT / "scripts" / "ingest"))
from export_corpus import EXAMPLE_WORDS_SQL, LEVEL_ORD, UNLEVELED_ORD  # noqa: E402
from reconcile_levels import derive_reading_tiers  # noqa: E402

# (kanji character, localized_text field, exact current value, corrected value, why)
FIXES: list[tuple[str, str, object, object, str]] = [
    (
        "屋", "meanings",
        ["loja", "estabelecimento", "prédio", "-eiro"],
        ["telhado", "loja", "estabelecimento", "prédio", "-eiro"],
        "KANJIDIC2 leads with 'roof' and so does our `en`; 屋根 (やね, telhado) is example_words[1] and "
        "屋上 is [4]. Prepending restores index parity with `en` instead of reordering it.",
    ),
    (
        "少", "meanings",
        ["pouco", "escasso", "poucos"],
        ["poucos", "pouco", "escasso"],
        "`en` is [few, little, scarce]; a locale-object is read index by index, so pt-BR[0] must be "
        "the gloss of en[0].",
    ),
    (
        "台", "meanings",
        ["suporte", "plataforma", "contador (sufixo p/ máquinas e veículos)"],
        ["suporte", "plataforma", "contador (sufixo para máquinas e veículos)"],
        "'p/' is a written abbreviation, not pt-BR prose a learner reads; corpus/vocab/n5.json already "
        "spells the same concept out as 'contador para máquinas e veículos'.",
    ),
    (
        "文", "irregular_note",
        "o único irregular é 文字 (もじ), e ele não é tão irregular assim: o も de 文字 está listado "
        "como leitura deste kanji.",
        "O único irregular é 文字 (もじ), e ele não é tão irregular assim: o も de 文字 é uma forma que "
        "esta entrada só registra entre as leituras de nome próprio (nanori).",
        "も is filed under nanori, so 'listado como leitura deste kanji' sends the learner looking for "
        "it among the readings they were taught. kanji:木 words the identical case correctly and this "
        "mirrors it; the sentence also now opens with a capital like the other 46 notes.",
    ),
]


# (kanji, reading, okurigana, exact current note, corrected note, why)
#
# A reading note is Layer-C prose printed directly above the words filed under that reading, so it is
# the one field that CANNOT be left to drift when the word list changes. Thirteen of these said the
# group was empty and it no longer is (the selector promoted an at-or-below-level word straight into
# it: 平仮名 under 平's ひら, 葉書 under 書's -がき, 大勢 under 大's おお-); two said the opposite, naming
# the single word they held after that word left the list. Each rewrite keeps the sentence the note
# already had about what the reading IS and replaces only the claim about the group, in the wording
# its sibling rows use — 日's ひ already says "vale como palavra sozinha, 日 (ひ)", which is what 原's
# はら needed. Phrases from kanji_align.EMPTY_CLAIMS ("nenhum composto", "sem exemplo", "ficou
# agrupado") are avoided in the notes whose groups now hold something, and required in the two whose
# groups are now empty: that is the exact string set validate_kanji_reading_groups tests.
NOTE_FIXES: list[tuple[str, str, str, str, str, str]] = [
    ("大", "おお-", "",
     "Leitura nativa (kun) que só aparece quando o 大 abre a palavra, e o traço no fim é o que marca "
     "isso. Nenhum vocabulário desta lista ficou agrupado nela: 大きい (おおきい) e 大きな (おおきな) "
     "ficam na leitura おお.きい, que já traz o okurigana きい.",
     "Leitura nativa (kun) que só aparece quando o 大 abre a palavra, e o traço no fim é o que marca "
     "isso: 大勢 (おおぜい), muita gente. Já 大きい (おおきい) e 大きな (おおきな) ficam na leitura "
     "おお.きい, que traz o okurigana きい.",
     "The group now holds 大勢; the contrast with おお.きい stays, since it is what the note is for."),
    ("上", "のぼ", "る",
     "leitura nativa com o okurigana る. Nenhum vocabulário do banco está agrupado nela, então ela "
     "fica sem exemplos aqui.",
     "leitura nativa com o okurigana る, do verbo 上る (のぼる), subir.",
     "上る is n5 and now sits in this group."),
    ("平", "ひら", "",
     "Leitura nativa ひら de 平 sem okurigana. Nenhum composto desta entrada foi agrupado nela.",
     "Leitura nativa ひら de 平 sem okurigana, como em 平仮名 (ひらがな), o silabário hiragana.",
     "平仮名 is n5, was absent from the record entirely, and is the reason a learner meets this "
     "reading."),
    ("正", "まさ", "に",
     "Mesma leitura まさ com o okurigana に, formando 正に. Nenhum composto desta entrada foi agrupado "
     "nesta linha.",
     "Mesma leitura まさ com o okurigana に, formando 正に (まさに), exatamente ou justamente.",
     "正に is now filed here, so the note can gloss it instead of denying it."),
    ("点", "つ", "ける",
     "Leitura nativa つ, listada com o okurigana ける. Nenhum composto desta entrada foi agrupado "
     "nesta linha.",
     "Leitura nativa つ com o okurigana ける, no verbo 点ける (つける), acender a luz ou ligar um "
     "aparelho.",
     "点ける is now filed here."),
    ("点", "つ", "く",
     "Mesma leitura nativa つ com o okurigana く. Nenhum composto desta entrada foi agrupado nesta "
     "linha.",
     "Mesma leitura nativa つ com o okurigana く, no verbo 点く (つく), quando a luz acende ou o "
     "aparelho liga sozinho.",
     "点く is now filed here; the intransitive sense is what separates it from 点ける."),
    ("然", "しか", "し",
     "Mesma leitura nativa com a okurigana し, também sem exemplos listados nesta entrada.",
     "Mesma leitura nativa com o okurigana し, em 然し (しかし), a conjunção mas, quase sempre escrita "
     "só em kana.",
     "然し is now filed here. The article also stops disagreeing with the noun (o okurigana)."),
    ("場", "ジョウ", "",
     "Leitura sino-japonesa: fecha a palavra em todos os compostos do grupo (工場, 市場, 劇場, 農場).",
     "Leitura sino-japonesa: fecha a palavra em todos os compostos do grupo (工場, 会場, 駐車場, "
     "飛行場).",
     "The list named 市場, which this record files under ば, plus 劇場 and 農場, which it does not show "
     "at all. It now names the four words actually in the group."),
    ("日", "-か", "",
     "leitura nativa de fim de palavra (por isso o hífen); nesta lista ela está sem compostos.",
     "leitura nativa de fim de palavra (por isso o hífen), a que conta os dias: ５日 (いつか), cinco "
     "dias ou dia 5.",
     "５日 is now filed here."),
    ("生", "な", "る",
     "base nativa な com o okurigana る; nesta lista ela está sem compostos.",
     "base nativa な com o okurigana る, no verbo 生る (なる), dar fruto.",
     "生る is now filed here."),
    ("書", "-がき", "",
     "Mesma variante sonorizada de sufixo, listada sem separar o き como okurigana. Também ficou sem "
     "palavra de exemplo nesta entrada.",
     "Mesma variante sonorizada de sufixo, listada sem separar o き como okurigana, como em 葉書 "
     "(はがき), cartão-postal.",
     "葉書 is n5 and is exactly what the sonorized suffix form is for."),
    ("度", "タク", "",
     "leitura sino-japonesa rara; este grupo está sem palavras.",
     "leitura sino-japonesa rara, que aparece em 支度 (したく), preparativos.",
     "支度 is now filed here."),
    ("原", "はら", "",
     "Leitura nativa (kun) ligada ao sentido de campo ou planície. Nenhuma palavra ficou listada "
     "neste grupo.",
     "Leitura nativa (kun) ligada ao sentido de campo ou planície: vale como palavra sozinha, 原 "
     "(はら).",
     "The group now holds the single-character word 原 itself, which is how 日's ひ words the same "
     "situation."),
    ("急", "せ", "く",
     "Leitura nativa (kun) せ, bem menos comum. O único exemplo agrupado, 急かす (apressar alguém), "
     "usa essa mesma leitura せ, só que com outro okurigana.",
     "Leitura nativa (kun) せ, bem menos comum. Nenhum composto desta entrada foi agrupado nela.",
     "急かす is no longer among the ten words this record shows, so 'o único exemplo agrupado' now "
     "points at nothing.",
     ),
    ("命", "ミョウ", "",
     "Segunda leitura sino-japonesa, bem mais rara. Neste grupo ela aparece só em 寿命 (じゅみょう), a "
     "expectativa de vida, fechando a palavra.",
     "Segunda leitura sino-japonesa, bem mais rara. Nenhum composto desta entrada foi agrupado nela; "
     "fora desta lista ela aparece em 寿命 (じゅみょう), a expectativa de vida.",
     "寿命 left the ten shown words, so the group is empty and the note has to say so; the word is "
     "still worth naming as where the reading does turn up.",
     ),
]


def apply_note_fixes(con: sqlite3.Connection, apply: bool) -> tuple[int, list[str]]:
    """Write each rewritten note to BOTH layers: `localized_text`, which the exporters read, and
    research/derived/kanji_reading_notes/batch-NN.json, the tracked authoring source that
    merge_kanji_reading_notes.py re-authors the DB from. Writing only the DB would look repaired in the
    exports and be silently reverted by the next merge."""
    done, notes = 0, []
    pending: dict[tuple[str, str, str], str] = {}
    for ch, rd, oku, before, after, _why in NOTE_FIXES:
        row = con.execute(
            "SELECT kr.id, (SELECT value FROM localized_text WHERE entity_type='kanji_reading' "
            "AND entity_id=kr.id AND field='note' AND locale='pt-BR') FROM kanji_reading kr "
            "JOIN kanji k ON k.id=kr.kanji_id WHERE k.character=? AND kr.reading=? "
            "AND COALESCE(kr.okurigana,'')=?", (ch, rd, oku)).fetchone()
        if not row:
            notes.append(f"  [SKIP] {ch} {rd}.{oku}: no such reading row")
            continue
        rid, cur = row
        pending[(ch, rd, oku)] = after
        if cur == after:
            continue
        if cur != before:
            notes.append(f"  [SKIP] {ch} {rd}.{oku}: note is neither the reported text nor the fix")
            continue
        if apply:
            con.execute("INSERT OR REPLACE INTO localized_text "
                        "(entity_type,entity_id,field,locale,value,is_list,layer) "
                        "VALUES ('kanji_reading',?,'note','pt-BR',?,0,'C')", (rid, after))
        done += 1
        notes.append(f"  [FIX ] {ch} {rd}.{oku} note")

    touched = 0
    for f in sorted(NOTES_SRC.glob("batch-*.json")):
        data = json.loads(f.read_text(encoding="utf-8"))
        changed = False
        for e in data.get("entries") or []:
            for r in e.get("readings") or []:
                key = (e.get("character"), r.get("reading"), r.get("okurigana") or "")
                if key in pending and r.get("note_pt") != pending[key]:
                    changed = True
                    touched += 1
                    if apply:
                        r["note_pt"] = pending[key]
                        # The grouping complaint that prompted the rewrite is what the rewrite answers.
                        if "grouping_problem" in r:
                            r["grouping_problem"] = ""
        if changed and apply:
            f.write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")
    if touched:
        notes.append(f"  [FIX ] {touched} note(s) rewritten in the authoring batches")
    return done, notes


def apply_text_fixes(con: sqlite3.Connection, apply: bool) -> tuple[int, list[str]]:
    done, notes = 0, []
    for ch, field, before, after, _why in FIXES:
        row = con.execute("SELECT id FROM kanji WHERE character=?", (ch,)).fetchone()
        if not row:
            notes.append(f"  [SKIP] kanji {ch}: not in the registry")
            continue
        kid = row[0]
        got = con.execute(
            "SELECT value, is_list FROM localized_text WHERE entity_type='kanji' AND entity_id=? "
            "AND field=? AND locale='pt-BR'", (kid, field)).fetchone()
        if not got:
            notes.append(f"  [SKIP] {ch} {field}: no pt-BR value stored")
            continue
        raw, is_list = got
        cur = json.loads(raw) if is_list else raw
        if cur == after:
            continue                                    # already repaired
        if cur != before:
            notes.append(f"  [SKIP] {ch} {field}: current value is neither the reported one nor the "
                         f"fix — left alone: {cur!r}")
            continue
        if apply:
            con.execute("UPDATE localized_text SET value=? WHERE entity_type='kanji' AND entity_id=? "
                        "AND field=? AND locale='pt-BR'",
                        (json.dumps(after, ensure_ascii=False) if is_list else after, kid, field))
        done += 1
        notes.append(f"  [FIX ] {ch} {field}")
    return done, notes


def resync_reading_groups(con: sqlite3.Connection, apply: bool) -> tuple[int, int]:
    """Bring `example_vocab_ids` back in step with the words the records now show — a DELTA, not a
    wholesale overwrite from the artifact.

    Two operations, both forced by the selector change and nothing else:
      DROP a citation whose word the record no longer shows. `example_vocab_ids` is what highlights a
           word inside `example_words`; citing a word that is not in that list highlights nothing and
           is what validate_kanji_reading_groups fails on. This runs over every leveled kanji, not
           just the n5..n3 the artifact covers, so an N2/N1 record whose ids came from the older
           fix_derived pass cannot keep a stale citation either.
      ADD  a newly shown word to the reading the aligner files it under, but ONLY when no reading of
           that kanji cites it yet. お茶 arriving in kanji:茶 with no reading highlighted would teach
           that 茶 is unpredictable there, which is the opposite of true.

    Overwriting each slot with the artifact's list wholesale was the first version of this, and it is
    wrong twice over: it re-orders 152 slots nothing asked to re-order, and it would silently revert
    any hand repair to the grouping (the 裸足-under-た.す family of fixes) back to what the aligner
    says. Never moving a word that is already cited leaves those decisions standing.

    Joins on (kanji_id, reading, okurigana) like merge_kanji_reading_notes does — okurigana is part of
    the key, or 生.きる, 生.かす and 生.ける collapse into one row.
    """
    entries = {e["character"]: e for e in json.loads(GROUPS.read_text(encoding="utf-8"))["entries"]}
    dropped = added = 0
    for kid, ch, level in con.execute("SELECT id, character, level FROM kanji WHERE level IS NOT NULL"):
        rows = con.execute("SELECT id, reading, COALESCE(okurigana,''), example_vocab_ids "
                           "FROM kanji_reading WHERE kanji_id=?", (kid,)).fetchall()
        if not any(r[3] for r in rows) and ch not in entries:
            continue
        shown = {r[2] for r in con.execute(EXAMPLE_WORDS_SQL,
                                           (kid, LEVEL_ORD.get(level, UNLEVELED_ORD)))}
        ids_of = {(r[1], r[2]): (r[0], json.loads(r[3]) if r[3] else []) for r in rows}
        for key, (rid, ids) in list(ids_of.items()):
            keep = [v for v in ids if v in shown]
            if keep != ids:
                dropped += len(ids) - len(keep)
                ids_of[key] = (rid, keep)
        cited = {v for _rid, ids in ids_of.values() for v in ids}
        for r in (entries.get(ch) or {}).get("readings", []):
            key = (r["reading"], r.get("okurigana") or "")
            if key not in ids_of:
                continue
            rid, ids = ids_of[key]
            new = [c["vocab_id"] for c in (r.get("compounds") or [])
                   if c.get("vocab_id") and c["vocab_id"] in shown and c["vocab_id"] not in cited]
            if new:
                ids_of[key] = (rid, ids + new)
                cited.update(new)
                added += len(new)
        for (rid, ids) in ids_of.values():
            cur = con.execute("SELECT example_vocab_ids FROM kanji_reading WHERE id=?",
                              (rid,)).fetchone()[0]
            want = json.dumps(ids, ensure_ascii=False) if ids else None
            if cur == want:
                continue
            if apply:
                con.execute("UPDATE kanji_reading SET example_vocab_ids=? WHERE id=?", (want, rid))
    return dropped, added


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true", help="report what would change, write nothing")
    args = ap.parse_args()
    apply = not args.check
    con = sqlite3.connect(DB)

    fixed, notes = apply_text_fixes(con, apply)
    pruned, added = resync_reading_groups(con, apply)
    fixed_notes, note_log = apply_note_fixes(con, apply)
    for n in notes + note_log:
        print(n)
    if apply:
        con.commit()
    tiers = derive_reading_tiers(con) if apply else -1

    print(f"kanji record repairs ({'APPLIED' if apply else 'check'}): "
          f"text fields {fixed}/{len(FIXES)}, reading notes {fixed_notes}/{len(NOTE_FIXES)}, "
          f"stale group citations dropped {pruned}, "
          f"newly shown words attached to their reading {added}, "
          f"introduced_at_level derived {tiers if apply else 'skipped (--check)'}")
    if apply:
        print("  now re-run: python scripts/export/export_corpus.py")
    con.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
