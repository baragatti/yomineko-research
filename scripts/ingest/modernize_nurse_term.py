#!/usr/bin/env python3
"""Modernize the dated, gendered 看護婦 (かんごふ, "(female) nurse") to the standard gender-neutral
看護師 (かんごし), the legal/standard term since 2002. Idempotent; safe to re-run after replay_all.

Why a single-entry rename (not a new entry): the corpus DB cross-references vocab by internal id, so the
family membership and sentence links follow the row automatically. They are the SAME concept ("nurse"), one
spelling supersedes the other. Provenance: the N4 level (4/4 consensus) is kept because the same word IS in
those community lists, spelled the dated way 看護婦; this is documented in notes_pt and the row is flagged
needs_review (Layer A/B human sign-off). The 3 AI-generated example sentences linked to this vocab are
modernized in lock-step (surface text + token rows). Run, then export_corpus + export_course.
"""
from __future__ import annotations
import json, sqlite3, sys
from pathlib import Path
sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
DB = Path(__file__).resolve().parents[2] / "db" / "corpus.sqlite"
NOTE = ("Termo neutro e padrão desde 2002. A forma antiga 看護婦 (かんごふ), específica de mulher "
        "(o kanji 婦 significa mulher), ainda aparece em textos mais antigos. O nível N4 vem das listas "
        "de consenso, que registram a grafia antiga 看護婦.")
SENTS = ["sent:gen-358d6c011e6c", "sent:gen-01e31222a647", "sent:gen-c058146d69ad"]


def main() -> int:
    con = sqlite3.connect(DB); cur = con.cursor()
    row = cur.execute("SELECT id, headword FROM vocab WHERE headword IN ('看護師','看護婦')").fetchone()
    if not row:
        print("nurse vocab not found — nothing to do"); return 0
    vid, hw = row
    if hw == "看護師":
        print(f"[idempotent] vocab id {vid} already 看護師 — re-asserting sentences/notes")
    shi = cur.execute("SELECT id FROM kanji WHERE character='師'").fetchone()
    shi_id = shi[0] if shi else None
    # 1) vocab row
    cur.execute("UPDATE vocab SET headword='看護師', kana='かんごし', romaji='kangoshi', "
                "slug='vocab:1928100', jmdict_ref='1928100', notes_pt=?, needs_review=1 WHERE id=?", (NOTE, vid))
    # notes (export reads localized_text entity_type='vocab', field='notes')
    cur.execute("DELETE FROM localized_text WHERE entity_type='vocab' AND entity_id=? AND field='notes'", (vid,))
    cur.execute("INSERT INTO localized_text (entity_type,entity_id,field,locale,value,is_list,layer) "
                "VALUES ('vocab',?,'notes','pt-BR',?,0,'B')", (vid, NOTE))
    # 2) pitch reading
    cur.execute("UPDATE vocab_pitch SET reading='かんごし' WHERE vocab_id=? AND reading='かんごふ'", (vid,))
    # 3) forms
    cur.execute("UPDATE vocab_form SET form='看護師' WHERE vocab_id=? AND form='看護婦'", (vid,))
    cur.execute("UPDATE vocab_form SET form='かんごし' WHERE vocab_id=? AND form='かんごふ'", (vid,))
    # 4) kanji link 婦 -> 師
    if shi_id is not None:
        cur.execute("UPDATE vocab_kanji SET kanji_id=? WHERE vocab_id=? AND position=2", (shi_id, vid))
    # 5) glosses (en column + pt localized_text)
    cur.execute("UPDATE vocab_sense SET gloss_en=?, needs_review=1 WHERE vocab_id=?",
                (json.dumps(["nurse", "registered nurse"], ensure_ascii=False), vid))
    sid_sense = cur.execute("SELECT id FROM vocab_sense WHERE vocab_id=? ORDER BY sense_order LIMIT 1",
                            (vid,)).fetchone()[0]
    pt = json.dumps(["enfermeiro(a)", "profissional de enfermagem"], ensure_ascii=False)
    n = cur.execute("UPDATE localized_text SET value=? WHERE entity_type='vocab_sense' AND entity_id=? "
                    "AND field='gloss' AND locale='pt-BR'", (pt, sid_sense)).rowcount
    if n == 0:
        cur.execute("INSERT INTO localized_text (entity_type,entity_id,field,locale,value,is_list,layer) "
                    "VALUES ('vocab_sense',?,'gloss','pt-BR',?,1,'B')", (sid_sense, pt))
    # 6) the 3 linked AI sentences (surface text + token rows), scoped per sentence_id
    for slug in SENTS:
        sr = cur.execute("SELECT id, jp, kana, romaji FROM sentence WHERE slug=?", (slug,)).fetchone()
        if not sr:
            continue
        sid, jp, kana, romaji = sr
        cur.execute("UPDATE sentence SET jp=?, kana=?, romaji=?, needs_review=1 WHERE id=?",
                    (jp.replace("看護婦", "看護師"), (kana or "").replace("かんごふ", "かんごし"),
                     (romaji or "").replace("kangofu", "kangoshi"), sid))
        cur.execute("UPDATE token SET surface='看護師',lemma='看護師',reading='かんごし',romaji='kangoshi' "
                    "WHERE sentence_id=? AND surface='看護婦'", (sid,))
        cur.execute("UPDATE token SET surface='師',lemma='師',reading='し',romaji='shi' "
                    "WHERE sentence_id=? AND surface='婦'", (sid,))
    con.commit()
    print(f"modernized vocab id {vid} -> 看護師 (かんごし); updated {len(SENTS)} linked sentences. "
          f"Family/links follow id {vid} automatically.")
    con.close(); return 0


if __name__ == "__main__":
    sys.exit(main())
