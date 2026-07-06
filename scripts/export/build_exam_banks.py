#!/usr/bin/env python3
"""JLPT exam-simulator BANKS (roadmap B; owner-approved 2026-07-05). Generates per-level, per-question-type
item banks derived ONLY from verified corpus facts — no AI generation, so Japanese correctness is inherited:
  kanji_reading   (漢字読み)  headword -> pick the correct kana reading         [vocab facts]
  orthography     (表記)      kana -> pick the correct written form            [vocab facts]
  context_fill    (文脈規定)  bank sentence with the target word blanked        [sentence + vocab]
  grammar_form    (文法形式)  bank sentence with the grammar form blanked       [sentence + grammar]
  sentence_order  (並べ替え)  reorder the sentence's tokens                     [sentence tokens]
Distractors are built by RULE (same level + same lexeme class + similar length; never equal to the correct
answer; orthography distractors must not share the stem's reading — i.e. wrong by construction). Deterministic
(stable sorts, no RNG) so re-runs are reproducible; the APP does the per-attempt random pick (see
design/exam_simulator.md). Real JLPT papers are © JEES — format reference only; zero copied text.
Output: corpus/exam_banks/{level}_{type}.json + INDEX.md. Usage: build_exam_banks.py"""
from __future__ import annotations
import json, sqlite3, sys
from pathlib import Path
sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
ROOT = Path(__file__).resolve().parents[2]
DB = ROOT / "db" / "corpus.sqlite"
OUT = ROOT / "corpus" / "exam_banks"
LEVELS = ("n5", "n4", "n3")
ORD = {"n5": 0, "n4": 1, "n3": 2, "n2": 3, "n1": 4}
allowed = lambda slvl, lvl: slvl in ORD and ORD[slvl] <= ORD[lvl]
CAPS = {"kanji_reading": 400, "orthography": 400, "context_fill": 400, "grammar_form": 300, "sentence_order": 300}
HAS_KANJI = lambda s: any("一" <= ch <= "鿿" for ch in s)


def pick_distractors(cands, correct_key, want=3):
    """cands: list of (sort_key, value) pre-ordered by closeness; returns first `want` unique values."""
    out, seen = [], {correct_key}
    for _, v in cands:
        if v in seen:
            continue
        seen.add(v)
        out.append(v)
        if len(out) == want:
            break
    return out


def main() -> int:
    con = sqlite3.connect(DB)
    OUT.mkdir(parents=True, exist_ok=True)
    counts = {}

    vocab = [dict(zip(("id", "hw", "kana", "lex", "lvl"), r)) for r in con.execute(
        "SELECT id,headword,kana,lexeme_type,level FROM vocab WHERE level IN ('n5','n4','n3') AND kana!=''")]
    kana_of = {v["hw"]: v["kana"] for v in vocab}

    # real sentences preferred; verified-generated (passed the §9 gen gates, needs_review) fill thin levels
    sents = {sid: (slug, jp, lvl, ai) for sid, slug, jp, lvl, ai in con.execute(
        "SELECT id,slug,jp,level,COALESCE(ai_generated,0) FROM sentence")}
    svocab: dict = {}
    for sid, vid in con.execute("SELECT sentence_id,vocab_id FROM sentence_vocab"):
        if sid in sents:
            svocab.setdefault(sid, []).append(vid)
    vb_by_id = {v["id"]: v for v in vocab}
    toks: dict = {}
    for sid, surf in con.execute("SELECT sentence_id,surface FROM token WHERE split_mode='C' ORDER BY sentence_id,id"):
        if sid in sents:
            toks.setdefault(sid, []).append(surf)

    def form_strs(forms_json):
        """forms_json entries are plain strings (or occasionally dicts) — normalize."""
        out = []
        try:
            for f in json.loads(forms_json or "[]"):
                fm = (f if isinstance(f, str) else (f.get("form") or "")).strip()
                fm = fm.lstrip("～〜").strip()  # N3 forms are cited as ～うちに; the sentence contains うちに
                if fm and 1 < len(fm) <= 8 and "…" not in fm and "～" not in fm and "-" not in fm:
                    out.append(fm)
        except Exception:
            pass
        return out

    gforms = []  # (level, key, form)
    for key, lvl, forms in con.execute("SELECT key,level,forms_json FROM grammar_point WHERE level IN ('n5','n4','n3')"):
        for fm in form_strs(forms):
            gforms.append((lvl, key, fm))
    sgram: dict = {}
    for sid, gid in con.execute("SELECT sentence_id,grammar_id FROM sentence_grammar"):
        if sid in sents:
            sgram.setdefault(sid, []).append(gid)
    gp = {gid: (key, lvl, forms) for gid, key, lvl, forms in con.execute(
        "SELECT id,key,level,forms_json FROM grammar_point")}

    for lvl in LEVELS:
        lv_vocab = [v for v in vocab if v["lvl"] == lvl and HAS_KANJI(v["hw"]) and v["hw"] != v["kana"]]
        lv_vocab.sort(key=lambda v: (v["kana"], v["hw"]))

        # ---- kanji_reading + orthography ----
        kr, ort = [], []
        for v in lv_vocab:
            pool = [(abs(len(w["kana"]) - len(v["kana"])) * 10 + (0 if w["lex"] == v["lex"] else 5), w)
                    for w in lv_vocab if w["id"] != v["id"]]
            pool.sort(key=lambda t: (t[0], t[1]["kana"]))
            dk = pick_distractors([(s, w["kana"]) for s, w in pool], v["kana"])
            # orthography distractors: same-level kanji words, NOT homophones of the stem (wrong by construction)
            dh = pick_distractors([(s, w["hw"]) for s, w in pool if w["kana"] != v["kana"]], v["hw"])
            if len(dk) == 3:
                kr.append({"id": f"kr:{lvl}:{v['id']}", "level": lvl, "stem": v["hw"], "correct": v["kana"],
                           "distractors": dk, "vocab_id": v["id"], "source": "vocab"})
            if len(dh) == 3:
                ort.append({"id": f"or:{lvl}:{v['id']}", "level": lvl, "stem": v["kana"], "correct": v["hw"],
                            "distractors": dh, "vocab_id": v["id"], "source": "vocab"})

        # ---- context_fill ----
        cf = []
        for sid in sorted(svocab, key=lambda x: (sents[x][3], x)):
            if len(cf) >= CAPS["context_fill"]:
                break
            slug, jp, slvl, ai = sents[sid]
            if not allowed(slvl, lvl):
                continue
            for vid in svocab[sid]:
                v = vb_by_id.get(vid)
                if not v or v["lvl"] != lvl or not HAS_KANJI(v["hw"]) or v["hw"] not in jp:
                    continue
                pool = [(abs(len(w["hw"]) - len(v["hw"])) * 10 + (0 if w["lex"] == v["lex"] else 20), w)
                        for w in lv_vocab if w["id"] != v["id"] and w["hw"] not in jp]
                pool.sort(key=lambda t: (t[0], t[1]["hw"]))
                dh = pick_distractors([(s, w["hw"]) for s, w in pool], v["hw"])
                if len(dh) == 3:
                    cf.append({"id": f"cf:{lvl}:{sid}:{vid}", "level": lvl,
                               "stem": jp.replace(v["hw"], "（　）", 1), "correct": v["hw"],
                               "distractors": dh, "sentence": slug, "vocab_id": vid, "ai": ai,
                               "source": "sentence+vocab"})
                break  # one item per sentence

        # ---- grammar_form ----
        gf = []
        lv_forms = sorted({fm for l2, _, fm in gforms if l2 == lvl})
        for sid in sorted(sgram, key=lambda x: (sents[x][3], x)):
            if len(gf) >= CAPS["grammar_form"]:
                break
            slug, jp, slvl, ai = sents[sid]
            if not allowed(slvl, lvl):
                continue
            for gid in sgram[sid]:
                key, glvl, forms = gp.get(gid, (None, None, None))
                if glvl != lvl or not forms:
                    continue
                fm = next((x for x in form_strs(forms) if x in jp), None)
                if not fm:
                    continue
                dis = [x for x in lv_forms if x != fm and x not in jp][:40]
                dis.sort(key=lambda x: (abs(len(x) - len(fm)), x))
                if len(dis) >= 3:
                    gf.append({"id": f"gf:{lvl}:{sid}", "level": lvl,
                               "stem": jp.replace(fm, "（　）", 1), "correct": fm, "distractors": dis[:3],
                               "sentence": slug, "grammar": key, "ai": ai, "source": "sentence+grammar"})
                break

        # ---- sentence_order ----
        so = []
        for sid in sorted(toks, key=lambda x: (sents[x][3], x)):
            if len(so) >= CAPS["sentence_order"]:
                break
            slug, jp, slvl, ai = sents[sid]
            if slvl != lvl and not (lvl == "n3" and allowed(slvl, lvl)) and not (lvl in ("n5","n4") and slvl == lvl):
                continue
            pieces = [t for t in toks[sid] if t.strip() and t not in "。、！？!?"]
            if 5 <= len(pieces) <= 9:
                so.append({"id": f"so:{lvl}:{sid}", "level": lvl, "pieces": pieces,
                           "answer": "".join(pieces), "sentence": slug, "ai": ai, "source": "sentence-tokens"})

        for name, items in (("kanji_reading", kr), ("orthography", ort), ("context_fill", cf),
                            ("grammar_form", gf), ("sentence_order", so)):
            items = items[:CAPS[name]]
            (OUT / f"{lvl}_{name}.json").write_text(json.dumps(items, ensure_ascii=False), encoding="utf-8")
            counts[f"{lvl}_{name}"] = len(items)

    (OUT / "INDEX.md").write_text(
        "# corpus/exam_banks — JLPT-style question banks (our format)\n\n"
        "Per-level, per-type item banks DERIVED from verified corpus facts (vocab readings, real bank "
        "sentences, grammar forms) — no AI-generated Japanese; distractors are rule-built (same level/lexeme "
        "class, similar length, wrong by construction). Real JLPT papers are © JEES and were used only as "
        "FORMAT reference; zero copied text. The app's exam simulator randomly samples these per attempt — "
        "picker spec: `design/exam_simulator.md`. Item: {id, level, stem, correct, distractors|pieces, source "
        "refs}. Layer B, needs_review.\n\n"
        + "".join(f"- `{k}.json` — {v} items\n" for k, v in sorted(counts.items())), encoding="utf-8")
    con.close()
    print("exam banks ->", counts)
    return 0


if __name__ == "__main__":
    sys.exit(main())
