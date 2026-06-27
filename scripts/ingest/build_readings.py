#!/usr/bin/env python3
"""Build in-lesson reading-practice boxes (design/reading_practice.md) by SELECTION from the verified bank
(§5.1 — highest trust: real Tatoeba/JEC sentences, human EN, our re-authored pt-BR, dissected, furigana from
Layer-A readings). For each eligible lesson it picks i+0 sentences (every kanji+vocab already in the lesson's
cumulative_known_set — HARD gate, max_new=0), prefers ones that USE the lesson's newly-introduced grammar
(theme/relevance) and REAL (non-AI) ones, assembles them into a `reading` record, and wires `<reading ref>` +
reading_refs into the lesson body (additive, before the checklist). Idempotent. No generation.
Usage: build_readings.py [--dry-run]"""
from __future__ import annotations
import argparse, json, re, sqlite3, sys
from pathlib import Path
sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
ROOT = Path(__file__).resolve().parents[2]
DB = ROOT / "db" / "corpus.sqlite"
LESSONS = ROOT / "research" / "derived" / "lessons"

# density ramp (§6): per lesson -> list of box sizes (#sentences). position p in 0..1 within the level.
def plan_for(level: str, p: float) -> list[int]:
    if level == "n5":
        if p < 0.45:
            return []                      # 0 before ~topic 5
        return [3] if p > 0.85 else [2]    # ramp 0 -> ~1, 2-3 sentences
    if level == "n4":
        return [4]                         # ~1 box, short paragraph
    if level == "n3":
        return [5] if p < 0.5 else [6, 6]  # first half 1; midpoint+ 2 boxes, longer
    return []


READING_BLOCK = re.compile(r'\s*<heading level="3"><text>Leitura</text></heading>(\s*<reading ref="[^"]+"\s*/>)+', re.S)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    c = sqlite3.connect(DB)
    kid_by_char = {ch: i for i, ch in c.execute("SELECT id,character FROM kanji")}
    vid_by_hw: dict = {}
    for i, hw in c.execute("SELECT id,headword FROM vocab"):
        vid_by_hw.setdefault(hw, i)
    skanji: dict = {}
    svocab: dict = {}
    for sid, kid in c.execute("SELECT sentence_id,kanji_id FROM sentence_kanji"):
        skanji.setdefault(sid, set()).add(kid)
    for sid, vid in c.execute("SELECT sentence_id,vocab_id FROM sentence_vocab"):
        svocab.setdefault(sid, set()).add(vid)
    sgrammar: dict = {}
    for sid, gid in c.execute("SELECT sentence_id,grammar_id FROM sentence_grammar"):
        sgrammar.setdefault(sid, set()).add(gid)
    # sentence display data
    sent = {}
    for sid, slug, jp, ai, conf, en in c.execute(
            "SELECT id,slug,jp,ai_generated,translation_confidence,en FROM sentence"):
        sent[sid] = {"slug": slug, "jp": jp, "ai": ai or 0, "conf": conf or 0, "en": en or "",
                     "len": len(jp), "nkanji": sum(1 for ch in jp if ch in kid_by_char)}
    # pt/en sentence translations (localized_text) + tokens
    SLpt = {eid: v for eid, v in c.execute(
        "SELECT entity_id,value FROM localized_text WHERE entity_type='sentence' AND field='translation' AND locale='pt-BR'")}
    SLen = {eid: v for eid, v in c.execute(
        "SELECT entity_id,value FROM localized_text WHERE entity_type='sentence' AND field='translation' AND locale='en'")}
    toks: dict = {}
    for sid, surf, rdg, romaji, pos in c.execute(
            "SELECT sentence_id,surface,reading,romaji,pos FROM token WHERE split_mode='C' ORDER BY sentence_id, id"):
        toks.setdefault(sid, []).append({"s": surf, "r": rdg, "ro": romaji, "pos": pos})

    c.execute("""CREATE TABLE IF NOT EXISTS reading (
        slug TEXT PRIMARY KEY, level TEXT, gated_to_lesson TEXT, theme_topic TEXT, title_pt TEXT, title_en TEXT,
        jp TEXT, tokens TEXT, translation_pt TEXT, translation_en TEXT, uses TEXT, length_band TEXT,
        source_slugs TEXT, ai_generated INT DEFAULT 0, needs_review INT DEFAULT 1, layer TEXT DEFAULT 'B')""")
    if not args.dry_run:
        c.execute("DELETE FROM reading")   # rebuild

    # lessons in order, with level + topic + cumulative known set + introduced grammar
    lessons = []
    for lid, slug, ordv, topic_id, ks in c.execute(
            "SELECT id,slug,ord,topic_id,cumulative_known_set FROM lesson WHERE cumulative_known_set!='' ORDER BY ord"):
        m = re.match(r"les:(pre-n5|n5|n4|n3|n2|n1)-", slug)
        lessons.append({"id": lid, "slug": slug, "ord": ordv, "topic": topic_id, "ks": ks,
                        "level": m.group(1) if m else "?"})
    # level position
    by_level: dict = {}
    for L in lessons:
        by_level.setdefault(L["level"], []).append(L)
    used_globally: set = set()
    out_readings = []
    lesson_refs: dict = {}
    for level, ls in by_level.items():
        n = len(ls)
        for idx, L in enumerate(ls):
            p = idx / max(1, n - 1)
            sizes = plan_for(level, p)
            if not sizes:
                continue
            k = json.loads(L["ks"])
            kk = {kid_by_char[x[6:]] for x in (k.get("kanji") or []) if x[6:] in kid_by_char}
            vv = {vid_by_hw[x[6:]] for x in (k.get("vocab") or []) if x[6:] in vid_by_hw}
            intro_gram = {gid for (gid,) in c.execute(
                "SELECT member_id FROM lesson_introduces WHERE lesson_id=? AND member_type='grammar'", (L["id"],))}
            # candidates: i+0, not yet used; score: themed (uses intro grammar) + real + shorter-for-low-levels
            cands = []
            for sid, sd in sent.items():
                if skanji.get(sid, set()) <= kk and svocab.get(sid, set()) <= vv and 4 <= sd["len"] <= 60:
                    themed = 1 if (sgrammar.get(sid, set()) & intro_gram) else 0
                    cands.append((sid, themed, sd))
            # prefer: unused, themed, real, confidence; mild length pref (short for n5, mid for n3)
            target_len = {"n5": 14, "n4": 22, "n3": 30}.get(level, 22)
            cands.sort(key=lambda t: (t[0] in used_globally, -t[1], t[2]["ai"], -t[2]["conf"],
                                      abs(t[2]["len"] - target_len)))
            refs = []
            bi = 0
            for size in sizes:
                chosen = []
                for sid, themed, sd in cands:
                    if sid in used_globally and len(used_globally) < len(sent) - 50:
                        continue
                    if any(sid == cs for cs, _, _ in chosen):
                        continue
                    chosen.append((sid, themed, sd))
                    if len(chosen) >= size:
                        break
                if len(chosen) < max(1, size - 1):
                    continue                       # not enough material; skip this box
                bi += 1
                slug = f"read:{L['slug'][4:]}-{bi:02d}"
                jp = "".join(sd["jp"] for _, _, sd in chosen)
                tk = []
                for sid, _, _ in chosen:
                    tk.extend(toks.get(sid, []))
                tpt = " ".join((SLpt.get(sid) or "") for sid, _, _ in chosen).strip()
                ten = " ".join((sent[sid]["en"] or SLen.get(sid) or "") for sid, _, _ in chosen).strip()
                uses_k = sorted({kk2 for sid, _, _ in chosen for kk2 in skanji.get(sid, set())})
                uses_v = sorted({vv2 for sid, _, _ in chosen for vv2 in svocab.get(sid, set())})
                band = "short" if size <= 2 else ("paragraph" if size <= 5 else "long")
                for sid, _, _ in chosen:
                    used_globally.add(sid)
                rec = (slug, level, L["slug"], L["topic"], "Leitura", "Reading", jp,
                       json.dumps(tk, ensure_ascii=False), tpt, ten,
                       json.dumps({"kanji": uses_k, "vocab": uses_v}, ensure_ascii=False), band,
                       json.dumps([sd["slug"] for _, _, sd in chosen], ensure_ascii=False), 0, 1, "B")
                if not args.dry_run:
                    c.execute("INSERT OR REPLACE INTO reading (slug,level,gated_to_lesson,theme_topic,title_pt,"
                              "title_en,jp,tokens,translation_pt,translation_en,uses,length_band,source_slugs,"
                              "ai_generated,needs_review,layer) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)", rec)
                refs.append(slug)
                out_readings.append(slug)
            if refs:
                lesson_refs[L["slug"]] = refs
    if not args.dry_run:
        c.commit()
    c.close()
    # wire <reading ref> + reading_refs into lesson JSON (additive, before <checklist>)
    wired = 0
    for slug, refs in lesson_refs.items():
        fp = LESSONS / (slug[4:] + ".json")
        if not fp.exists():
            continue
        d = json.loads(fp.read_text(encoding="utf-8"))
        body = d.get("body", "")
        body = READING_BLOCK.sub("", body)        # idempotent: drop old block
        block = '<heading level="3"><text>Leitura</text></heading>' + "".join(
            f'<reading ref="{r}"/>' for r in refs)
        if "<checklist>" in body:
            body = body.replace("<checklist>", block + "<checklist>", 1)
        else:
            body = body + block
        d["body"] = body
        d["reading_refs"] = refs
        if not args.dry_run:
            fp.write_text(json.dumps(d, ensure_ascii=False, indent=2), encoding="utf-8")
        wired += 1
    print(f"readings ({'dry-run' if args.dry_run else 'built'}): {len(out_readings)} boxes across {wired} lessons")
    return 0


if __name__ == "__main__":
    sys.exit(main())
