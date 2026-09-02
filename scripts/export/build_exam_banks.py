#!/usr/bin/env python3
"""JLPT exam-simulator BANKS (roadmap B; owner-approved 2026-07-05). Generates per-level, per-question-type
item banks derived ONLY from verified corpus facts — no AI generation, so Japanese correctness is inherited:
  kanji_reading   (漢字読み)  headword -> pick the correct kana reading         [vocab facts]
  orthography     (表記)      kana -> pick the correct written form            [vocab facts]
  context_fill    (文脈規定)  bank sentence with the target word blanked        [sentence + vocab]
  grammar_form    (文法形式)  bank sentence with the grammar form blanked       [sentence + grammar]
  sentence_order  (並べ替え)  reorder the sentence's tokens                     [sentence tokens]
Distractors are built by RULE (same level + same lexeme class + similar length; never equal to the correct
answer; orthography distractors must not share the stem's reading — i.e. wrong by construction). Among
equally-close candidates the order is a hash of (item, candidate), NOT alphabetical — see `spread()`.
Deterministic (hashed sorts, no RNG) so re-runs are reproducible; the APP does the per-attempt random pick (see
design/exam_simulator.md). Real JLPT papers are © JEES — format reference only; zero copied text.
Output: corpus/exam_banks/{level}_{type}.json + INDEX.md. Usage: build_exam_banks.py"""
from __future__ import annotations
import hashlib, json, sqlite3, sys
from pathlib import Path
sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
# W01: honour --db / $YOMINEKO_DB so a rebuild can target a scratch DB (scripts/dbtarget.py).
import sys as _sys, pathlib as _pl  # noqa: E402
_sys.path.append(str(next(p for p in _pl.Path(__file__).resolve().parents if p.name == "scripts")))
from dbtarget import db_target  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
DB = db_target(ROOT / "db" / "corpus.sqlite")
OUT = ROOT / "corpus" / "exam_banks"
LEVELS = ("n5", "n4", "n3")
ORD = {"n5": 0, "n4": 1, "n3": 2, "n2": 3, "n1": 4}
allowed = lambda slvl, lvl: slvl in ORD and ORD[slvl] <= ORD[lvl]
CAPS = {"kanji_reading": 400, "orthography": 400, "context_fill": 400, "grammar_form": 300, "sentence_order": 300, "text_grammar": 150}
HAS_KANJI = lambda s: any("一" <= ch <= "鿿" for ch in s)


def spread(anchor: str, value: str) -> str:
    """Deterministic per-item tiebreak for equally-close candidates.

    Ties used to break ALPHABETICALLY, which meant the same alphabetically-first words won for every
    single target: 400 n4 kanji_reading items shared just 31 distinct distractors, あがる/あさい/あいだ
    appearing on ~133 questions each. A learner eliminates those from memory after two questions, which
    defeats the point of the bank. Hashing (anchor, value) spreads choices across the whole eligible pool
    while keeping the build reproducible — this file's contract is "deterministic, no RNG", and a hash is
    deterministic; only the *ordering* is arbitrary, which is exactly what a tiebreak should be.
    """
    return hashlib.sha1(f"{anchor}{value}".encode("utf-8")).hexdigest()


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
            kc = sorted(((s, w["kana"]) for s, w in pool), key=lambda t: (t[0], spread(v["hw"], t[1])))
            dk = pick_distractors(kc, v["kana"])
            # orthography distractors: same-level kanji words, NOT homophones of the stem (wrong by construction)
            hc = sorted(((s, w["hw"]) for s, w in pool if w["kana"] != v["kana"]),
                        key=lambda t: (t[0], spread(v["kana"], t[1])))
            dh = pick_distractors(hc, v["hw"])
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
                pool.sort(key=lambda t: (t[0], spread(f"{sid}:{v['hw']}", t[1]["hw"])))
                dh = pick_distractors([(s, w["hw"]) for s, w in pool], v["hw"])
                if len(dh) == 3:
                    cf.append({"id": f"cf:{lvl}:{sid}:{vid}", "level": lvl,
                               "stem": jp.replace(v["hw"], "（　）", 1), "correct": v["hw"],
                               "distractors": dh, "sentence": slug, "vocab_id": vid, "ai_generated": bool(ai),
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
                # NB: this used to slice [:40] BEFORE sorting, i.e. off an alphabetically-sorted
                # lv_forms — so the candidate set was the same 40 forms every time. Sort the full pool.
                dis = [x for x in lv_forms if x != fm and x not in jp]
                dis.sort(key=lambda x: (abs(len(x) - len(fm)), spread(f"{sid}:{fm}", x)))
                if len(dis) >= 3:
                    gf.append({"id": f"gf:{lvl}:{sid}", "level": lvl,
                               "stem": jp.replace(fm, "（　）", 1), "correct": fm, "distractors": dis[:3],
                               "sentence": slug, "grammar": key, "ai_generated": bool(ai), "source": "sentence+grammar"})
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
                           "answer": "".join(pieces), "sentence": slug, "ai_generated": bool(ai), "source": "sentence-tokens"})

        # ---- text_grammar (文章の文法): blank a level-appropriate grammar form inside a READING passage ----
        tg = []
        if con.execute("SELECT name FROM sqlite_master WHERE name='reading'").fetchone():
            for slug, rlvl, jp in con.execute("SELECT slug,level,jp FROM reading ORDER BY slug"):
                if rlvl != lvl or len(tg) >= CAPS["text_grammar"]:
                    continue
                fm = next((x for x in lv_forms if x in jp), None)
                if not fm:
                    continue
                dis = [x for x in lv_forms if x != fm and x not in jp]
                dis.sort(key=lambda x: (abs(len(x) - len(fm)), spread(f"{slug}:{fm}", x)))
                if len(dis) >= 3:
                    tg.append({"id": f"tg:{lvl}:{slug.split(':',1)[1]}", "level": lvl,
                               "stem": jp.replace(fm, "（　）", 1), "correct": fm, "distractors": dis[:3],
                               "reading": slug, "source": "reading+grammar"})

        for name, items in (("kanji_reading", kr), ("orthography", ort), ("context_fill", cf),
                            ("grammar_form", gf), ("sentence_order", so), ("text_grammar", tg)):
            items = items[:CAPS[name]]
            (OUT / f"{lvl}_{name}.json").write_text(json.dumps(items, ensure_ascii=False), encoding="utf-8")
            counts[f"{lvl}_{name}"] = len(items)

    # INDEX covers ALL bank files (deterministic + authored) — glob, don't use only this run's counts,
    # so regenerating the deterministic banks never wipes the authored banks from the listing.
    all_counts = {f.stem: len(json.loads(f.read_text(encoding="utf-8")))
                  for f in sorted(OUT.glob("*_*.json"))}
    (OUT / "INDEX.md").write_text(
        "# corpus/exam_banks — JLPT-style question banks (our format)\n\n"
        "Per-level, per-type item banks DERIVED from verified corpus facts (vocab readings, real bank "
        "sentences, grammar forms) — deterministic types have no AI-generated Japanese; distractors are "
        "rule-built (same level/lexeme class, similar length, wrong by construction). Real JLPT papers are "
        "© JEES and were used only as FORMAT reference; zero copied text. The app's exam simulator randomly "
        "samples these per attempt — picker spec: `design/exam_simulator.md`. Item: {id, level, stem, "
        "correct, distractors|pieces, source refs}. Deterministic types are Layer B; the AUTHORED types "
        "(`paraphrase`, `usage`, `reading_comp`, `listening_*`) are Layer C (authored + adversarially "
        "verified, needs_review). `reading_comp` items reference their passage by `read:` slug — the app "
        "renders the passage from `corpus/readings` (single source of truth). `listening_*` items are "
        "voice-ready TEXT scripts (speaker-tagged turns, `audio: \"pending\"` — spec: `design/listening.md`); "
        "`listening_reply` prompts are REAL bank sentences verbatim (`sentence` ref).\n\n"
        + "".join(f"- `{k}.json` — {v} items\n" for k, v in sorted(all_counts.items())), encoding="utf-8")
    con.close()
    print("exam banks ->", counts)
    return 0


if __name__ == "__main__":
    sys.exit(main())
