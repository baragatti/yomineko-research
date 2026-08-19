#!/usr/bin/env python3
"""Re-author the 6 escalated sent:gen- sentences: RE-DISSECT, never a one-field patch.

Round 2 refused these as one-field rows and was right. A sentence record is internally consistent by
construction: jp, kana and romaji concatenate from the token array, the particles array and structure
paragraph describe that exact wording, and both translations were written against it. Writing `jp` alone
leaves every one of those describing a sentence that no longer exists.

So this deletes and re-persists through persist_dissection.persist(), which regenerates kana, romaji,
tokens and particles from the new Japanese via the Dissector. Layer-B that the old record already
carried (token glosses, roles, conjugation notes, particle explanations) is carried across BY SURFACE,
since most tokens are untouched by these edits. What cannot be carried is reported as a gap rather than
invented.

The six defects, all of which the records were TEACHING and not merely containing:
  686faf1ec51d  で with an existence predicate; its structure paragraph and particles[0] both stated
                that で marks the place where existence happens. Moves to に.
  aef805c4840d  third-person 〜たい. Moves the desire to the speaker (私), which keeps the record's
                declared target 476 習う. Writing 習いたがっている would import 〜たがる, a form this
                record does not teach and its token array does not carry.
  cb6562f41e17  私のお兄さん - you do not use お〜さん for your own family to an outsider. Moves the
                brother to a friend's family, which keeps target 122 お兄さん; swapping to 兄 would
                delete the very entry the sentence exists to demonstrate.
  b2ed6e8bb267  外国に輸入 against a translation that already says "do exterior". Moves に to から, so
                the Japanese finally agrees with its own stored pt-BR rather than the other way round.
  8cc2f196d1e9  毛 for head hair. Moves it to a cat, keeping target 1063 毛.
  b7b28dfc0928  以下 written in kana inside the very gp-93 sentence that teaches 以下. Kanji restored;
                this changes no reading, so kana and romaji are unchanged.

Every substituted word is a registered n5 entry already attested as a token in the bank (私 690,
友達 454, 猫 492), so nothing here introduces vocabulary the course does not teach.

Usage: apply_escalated_sentences.py [--apply]
"""
from __future__ import annotations
import argparse, json, sqlite3, sys
from collections import Counter
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts" / "ingest"))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "ingest"))
sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts" / "ingest"))
SRC = ROOT / "research" / "derived" / "qa_queues" / "round3" / "escalated_sentences.json"
DB = ROOT / "db" / "corpus.sqlite"
GAPS = ROOT / "research" / "derived" / "escalated_layerb_gaps.json"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args()
    rows = [r for r in json.loads(SRC.read_text(encoding="utf-8"))["rows"] if r["verdict"] == "fix"]
    con = sqlite3.connect(DB)

    from dissect import Dissector
    from persist_dissection import persist
    diss = Dissector(DB)

    # Bank-wide fallback. The words these edits introduce (私, 友達, 猫, 以下, に, から) are all already
    # glossed on other sentences, so the missing Layer-B is SELECTED from the bank rather than authored.
    # That keeps the house voice and avoids inventing pedagogy for elementary vocabulary.
    def common(entity: str, join: str, field: str) -> dict[str, str]:
        out: dict[str, dict[str, int]] = {}
        for surf, val in con.execute(
                f"SELECT t.{join}, l.value FROM {entity} t JOIN localized_text l "
                f"ON l.entity_type='{entity}' AND l.entity_id=t.id "
                f"WHERE l.field=? AND l.locale='pt-BR' AND l.value IS NOT NULL", (field,)):
            out.setdefault(surf, {}).setdefault(val, 0)
            out[surf][val] += 1
        return {k: max(v, key=v.get) for k, v in out.items() if v}

    BANK_GLOSS = common("token", "surface", "gloss")
    BANK_ROLE = common("token", "surface", "role")
    BANK_PFUNC = common("particle", "particle", "function")
    BANK_PEXPL = common("particle", "particle", "explanation")

    gaps, stats = [], Counter()
    for r in rows:
        slug = r["id"]
        old = con.execute("SELECT id,jp,level,en FROM sentence WHERE slug=?", (slug,)).fetchone()
        if not old:
            print(f"  SKIP {slug}: not in bank"); continue
        sid, old_jp, level, en = old
        if r.get("current") and r["current"] != old_jp:
            print(f"  SKIP {slug}: stored jp does not match the anchor"); continue

        # harvest the old Layer-B, keyed by token surface
        keep_tok: dict[str, dict] = {}
        for tid, surf in con.execute("SELECT id,surface FROM token WHERE sentence_id=? AND "
                                     "split_mode='C' ORDER BY position", (sid,)):
            lb = {}
            for field, key in (("gloss", "gloss_pt"), ("role", "role_pt"),
                               ("conjugation_note", "conjugation_note_pt")):
                v = con.execute("SELECT value FROM localized_text WHERE entity_type='token' AND "
                                "entity_id=? AND field=? AND locale='pt-BR'", (tid, field)).fetchone()
                if v and v[0]:
                    lb[key] = v[0]
            if lb:
                keep_tok[surf] = lb
        keep_par: dict[str, dict] = {}
        for pid, particle in con.execute("SELECT id,particle FROM particle WHERE sentence_id=?", (sid,)):
            lb = {}
            for field, key in (("function", "function_pt"), ("explanation", "explanation_pt")):
                v = con.execute("SELECT value FROM localized_text WHERE entity_type='particle' AND "
                                "entity_id=? AND field=? AND locale='pt-BR'", (pid, field)).fetchone()
                if v and v[0]:
                    lb[key] = v[0]
            if lb:
                keep_par[particle] = lb

        new_jp = r["jp"]
        sk = diss.skeleton(new_jp)
        if r.get("kana") and sk["kana"] != r["kana"]:
            print(f"  NOTE {slug}: dissector kana {sk['kana']!r} != supplied {r['kana']!r}")
        def tok_lb(t):
            lb = dict(keep_tok.get(t["surface"], {}))
            if not lb.get("gloss_pt") and BANK_GLOSS.get(t["surface"]):
                lb["gloss_pt"] = BANK_GLOSS[t["surface"]]
                stats["gloss_from_bank"] += 1
            if not lb.get("role_pt") and BANK_ROLE.get(t["surface"]):
                lb["role_pt"] = BANK_ROLE[t["surface"]]
            return lb

        def par_lb(p):
            lb = dict(keep_par.get(p["particle"], {}))
            if not lb.get("explanation_pt") and BANK_PEXPL.get(p["particle"]):
                lb["explanation_pt"] = BANK_PEXPL[p["particle"]]
                stats["particle_from_bank"] += 1
            if not lb.get("function_pt") and BANK_PFUNC.get(p["particle"]):
                lb["function_pt"] = BANK_PFUNC[p["particle"]]
            return lb

        tokens = {t["position"]: tok_lb(t) for t in sk["tokens"]}
        particles = {p["position"]: par_lb(p) for p in sk["particles"]}

        missing_t = [t["surface"] for t in sk["tokens"]
                     if t["pos_coarse"] in {"名詞", "動詞", "形容詞", "副詞", "形状詞", "連体詞",
                                            "代名詞", "感動詞", "接続詞"}
                     and not tokens.get(t["position"], {}).get("gloss_pt")]
        missing_p = [p["particle"] for p in sk["particles"]
                     if not particles.get(p["position"], {}).get("explanation_pt")]
        if missing_t or missing_p:
            gaps.append({"slug": slug, "jp": new_jp, "tokens_without_gloss": missing_t,
                         "particles_without_explanation": missing_p})
        stats["reauthored"] += 1
        stats["carried_tokens"] += sum(1 for v in tokens.values() if v)
        stats["gap_tokens"] += len(missing_t)
        stats["gap_particles"] += len(missing_p)

        if args.apply:
            for tbl in ("sentence_vocab", "sentence_kanji", "sentence_grammar"):
                con.execute(f"DELETE FROM {tbl} WHERE sentence_id=?", (sid,))
            for etype, q in (("token", "SELECT id FROM token WHERE sentence_id=?"),
                             ("particle", "SELECT id FROM particle WHERE sentence_id=?")):
                ids = [x[0] for x in con.execute(q, (sid,))]
                if ids:
                    con.execute(f"DELETE FROM localized_text WHERE entity_type='{etype}' AND "
                                f"entity_id IN ({','.join('?' * len(ids))})", ids)
            con.execute("DELETE FROM particle WHERE sentence_id=?", (sid,))
            con.execute("DELETE FROM token WHERE sentence_id=?", (sid,))
            con.execute("DELETE FROM localized_text WHERE entity_type='sentence' AND entity_id=?", (sid,))
            con.execute("DELETE FROM sentence WHERE id=?", (sid,))
            con.commit()
            persist(con, diss, {
                "slug": slug, "jp": new_jp, "en": en, "level": level,
                "pt": r.get("pt"), "pt_literal": r.get("pt_literal"),
                "structure_explanation_pt": r.get("structure_explanation_pt"),
                "tokens": tokens, "particles": particles,
                "jp_source": "generated", "ai_generated": 1,
                "tags": ["reauthored"], "translation_confidence": 0.8,
            })

    GAPS.write_text(json.dumps(
        {"note": "Layer-B slots the re-dissection could not carry across by surface. These are the "
                 "genuinely NEW words the edits introduced; they need authoring before the gate "
                 "accepts these six at dissection_tier full.",
         "gaps": gaps}, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"escalated re-author ({'APPLIED' if args.apply else 'dry-run'}): {dict(stats)}")
    print(f"Layer-B gaps -> {GAPS.relative_to(ROOT)}")
    for g in gaps:
        print(f"   {g['slug']}: tokens {g['tokens_without_gloss']} particles "
              f"{g['particles_without_explanation']}")
    con.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
