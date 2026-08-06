#!/usr/bin/env python3
"""Build the speaking-first course path -> course/speak/. Spec: design/speaking_path.md.

This is a SECOND ORDERING over the existing corpus, not a second corpus: every unit holds corpus IDs
and embeds nothing, so a fix in corpus/vocab reaches both paths. The JLPT path orders by exam
syllabus; this one orders by what a traveller needs to SAY soonest, with word frequency
(vocab.freq_rank, built by scripts/ingest/build_frequency.py) deciding order inside a scenario.

Everything here is mechanical so the path can be rebuilt and diffed:
  * a sentence joins a stage when it contains one of that stage's SEED surface forms (below --
      seeds live in code, not prose, so they cannot drift from what actually ran);
  * candidates are ordered by (new words, then length), which makes the path start itself: with an
      empty known set the only sentences carrying <=1 new word are the one-word chunks (ありがとう,
      すみません, こんにちは), and longer sentences become eligible as the known set grows. No
      hand-seeded "unit 1" is needed;
  * a sentence qualifies only while its new-word load is <= MAX_NEW (i+1);
  * real sentences (ai_generated=0) are preferred over generated ones and the split is reported;
  * a grammar point enters a unit only when one of its forms occurs in that unit's phrases -- the
      learner meets a pattern because they are about to say it.

If a stage runs out of qualifying sentences the unit is emitted SHORT and the shortfall is recorded
in the manifest. A thin stage is a visible data gap to fix by mining more Tatoeba (see
design/speaking_path.md section 6), never something to fill with generated text.

Usage: build_speaking_path.py [--dry-run]
"""
from __future__ import annotations
import argparse, json, re, sqlite3, sys
from collections import Counter
from pathlib import Path
sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
ROOT = Path(__file__).resolve().parents[2]
DB = ROOT / "db" / "corpus.sqlite"
OUT = ROOT / "course" / "speak"

MAX_NEW = 3            # new words a sentence may carry (i+1)
PHRASES_PER_UNIT = 6
UNITS_PER_STAGE = 6
KANJI_PER_UNIT = 6

# Seeds are DICTIONARY forms, matched against token lemma/surface exactly, plus a substring fallback
# for seeds of 4+ characters. Matching raw substrings was the first attempt and it put 夕食はいりません
# ("I don't need dinner") in the greetings stage, because the seed はい occurs inside はいりません.
# (slug, pt-BR title, approx band, seeds)
STAGES: list[tuple[str, str, str, tuple[str, ...]]] = [
    ("arrival", "Chegar e cumprimentar", "pre-n5",
     ("こんにちは", "ありがとう", "すみません", "はい", "いいえ", "お願いします", "はじめまして",
      "さようなら", "ごめんなさい", "おはよう", "こんばんは", "どうも", "失礼します")),
    # NB: seeds must be SPECIFIC to the scenario. ください was a shopping seed and filled the whole
    # stage with 〜てください grammar drills; 行く was a getting_around seed and filled that one with
    # obligation forms. A seed that appears in every other sentence selects for the seed, not the theme.
    ("shopping", "Isto, aquilo, quanto custa", "pre-n5/n5",
     ("いくら", "買う", "円", "店", "これ", "それ", "あれ", "安い", "高い", "お金",
      "財布", "払う", "値段", "売る")),
    ("eating", "Comer e beber fora", "n5",
     ("食べる", "飲む", "おいしい", "レストラン", "注文", "水", "お茶", "ご飯", "肉", "魚",
      "野菜", "メニュー", "コーヒー", "ビール", "朝ご飯", "昼ご飯")),
    ("getting_around", "Chegar aonde você quer", "n5",
     ("どこ", "駅", "左", "右", "近く", "道", "電車", "バス", "タクシー",
      "地図", "切符", "空港", "曲がる", "着く", "橋", "交差点")),
    ("lodging", "Dormir e resolver problemas", "n5",
     ("ホテル", "部屋", "泊まる", "鍵", "予約", "トイレ", "風呂", "シャワー", "荷物", "寝る")),
    ("about_you", "Falar de você", "n5",
     ("名前", "出身", "仕事", "住む", "好き", "趣味", "家族", "日本人", "学生",
      "会社", "友達", "兄弟")),
    ("time_plans", "Quando, que horas, combinar", "n5/n4",
     ("明日", "今日", "時間", "曜日", "約束", "会う", "いつ", "週間", "来年", "予定", "午後",
      "午前", "毎日")),
    ("health", "Emergência e saúde", "n4",
     ("痛い", "病院", "薬", "医者", "熱", "大丈夫", "助ける", "危ない", "怪我", "気分", "風邪")),
    ("past_stories", "Contar o que aconteceu", "n4",
     ("昨日", "初めて", "経験", "旅行", "楽しい", "去年", "ことがある", "思い出")),
    ("politeness", "Pedir, oferecer, agradecer com jeito", "n4",
     ("いただく", "くださる", "よろしい", "申し訳", "恐れ入る", "お世話", "ございます", "伺う")),
    ("opinions", "Dizer o que você acha", "n4/n3",
     ("と思う", "だから", "たぶん", "かもしれない", "方がいい", "はず", "理由", "意見",
      "賛成", "反対")),
    ("real_talk", "Conversa de verdade", "n3",
     ("らしい", "のに", "ながら", "わけ", "みたい", "そうだ", "というのは", "ばかり", "はず")),
]

# Set expressions the analyzer mis-lemmatises, because they are frozen forms rather than live grammar:
# すみません comes back as 住む+ます+ぬ (so the "vocabulary" of an apology is "to live"), ありがとう as
# an adjective stem. A learner meets these as ONE chunk anyway, so they are taught whole: they carry no
# new-word cost and contribute no vocabulary to the known set. That is both pedagogically right and
# immune to the mis-analysis.
CHUNKS = ("すみません", "ありがとう", "こんにちは", "こんばんは", "おはよう", "さようなら",
          "ごめんなさい", "はじめまして", "おやすみ", "いただきます", "ごちそうさま",
          "失礼します", "お願いします", "どういたしまして", "もしもし", "ただいま",
          "おかえり", "いらっしゃいませ", "おめでとう", "お疲れ様")


def jload(s):
    try:
        v = json.loads(s or "[]")
        return v if isinstance(v, list) else []
    except Exception:
        return []


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    con = sqlite3.connect(DB)

    vocab = {vid: {"id": vid, "slug": slug, "hw": hw, "kana": kana, "freq": fr or 10 ** 9,
                   "level": lv or "", "lex": lex or ""}
             for vid, slug, hw, kana, fr, lv, lex in con.execute(
                 "SELECT id,slug,headword,kana,freq_rank,level,lexeme_type FROM vocab")}
    # A sentence is a CHUNK only if it IS the set expression, optionally with a politeness tail. Testing
    # startswith() was wrong: ありがとう、それだけだよ。and ごめんなさい。時間があまりないんです。both
    # begin with a set phrase but are ordinary sentences, and marking them chunks meant they contributed
    # no vocabulary at all — the whole arrival stage reached unit 3 with "0 words learned".
    TAILS = ("", "ございます", "ございました", "です", "でした", "ました")

    def is_chunk(jp: str) -> bool:
        body = jp.rstrip("。！？!?…、")
        return any(body == c + t for c in CHUNKS for t in TAILS)

    sents = {sid: {"id": sid, "slug": slug, "jp": jp, "ai": ai or 0, "level": lv or "",
                   "chunk": is_chunk(jp)}
             for sid, slug, jp, lv, ai in con.execute(
                 "SELECT id,slug,jp,level,COALESCE(ai_generated,0) FROM sentence")}

    # A sentence's vocabulary comes from the DISSECTION (token.vocab_id), not from sentence_vocab.
    # sentence_vocab is substring-derived and therefore lies: すみません。is linked there to 住む AND
    # 隅, and 夕食はいりません to 入る via はい.
    #
    # Token links are per-morpheme, but the dissector still resolves partly by READING, so where several
    # entries share a kana it can pick the wrong one: し (the stem of する) linked to 刷る "to print" in
    # 739 tokens, この to 九 in 428, その to 園 in 146, かかる in 時間がかかる to 罹る "to contract an
    # illness". A learner-facing word list built from those teaches nonsense.
    #
    # Two rejected fixes, recorded so they are not retried:
    #   * Arbitrating by freq_rank is NOT safe. The frequency table matches written forms, so words
    #     normally written in kana score badly, and "prefer the more frequent homophone" swapped
    #     居る -> 入る (543 tokens) and 生る -> 鳴る (233), both wrong.
    #   * Requiring the entry to appear literally in the sentence text is too strict: it drops every
    #     inflected verb, because 行く is written 行き and 来る is written 来て (157 and 146 losses).
    #
    # What actually works: accept the link when the written form matches the token directly (headword ==
    # lemma covers all inflection), and otherwise only when the READING IS UNAMBIGUOUS. する is shared by
    # 刷る and 為る, いる by 居る/入る/要る, この by 此の and 九 — when a kana maps to several entries and
    # the entry's kanji is not on the page, there is no evidence for which word it is, so we decline to
    # teach it. When a kana maps to exactly one entry (くださる -> 下さる) there is nothing to confuse.
    kana_count: Counter = Counter(v["kana"] for v in vocab.values())
    KANJI = re.compile(r"[一-鿿㐀-䶿]")

    def link_ok(v: dict, surface: str, lemma: str) -> bool:
        if v["hw"] == lemma or v["hw"] == surface:
            return True                                  # written form matches, inflection included
        if any(ch in surface for ch in v["hw"] if KANJI.match(ch)):
            return True                                  # its kanji is on the page
        return v["kana"] == lemma and kana_count[v["kana"]] == 1   # unambiguous reading

    sv: dict[int, list[int]] = {}
    dropped: Counter = Counter()
    for sid, vid, surface, lemma in con.execute(
            "SELECT DISTINCT sentence_id,vocab_id,surface,lemma FROM token "
            "WHERE split_mode='C' AND vocab_id IS NOT NULL"):
        if sid not in sents or vid not in vocab:
            continue
        v = vocab[vid]
        if not link_ok(v, surface or "", lemma or ""):
            dropped[v["hw"]] += 1
            continue
        if vid not in sv.setdefault(sid, []):
            sv[sid].append(vid)
    # token surfaces + lemmas per sentence, for exact seed matching
    stok: dict[int, set[str]] = {}
    for sid, surf, lem in con.execute(
            "SELECT sentence_id,surface,lemma FROM token WHERE split_mode='C'"):
        if sid in sents:
            s = stok.setdefault(sid, set())
            s.add(surf)
            if lem:
                s.add(lem)
    sk: dict[int, list[int]] = {}
    for sid, kid in con.execute("SELECT sentence_id,kanji_id FROM sentence_kanji"):
        if sid in sents:
            sk.setdefault(sid, []).append(kid)
    kanji = {kid: ch for kid, ch in con.execute("SELECT id,character FROM kanji")}
    # sentence.pt is empty for all 5,565 rows; the pt-BR translation lives in localized_text.
    ptx = {sid: val for sid, val in con.execute(
        "SELECT entity_id,value FROM localized_text WHERE entity_type='sentence' "
        "AND field='translation' AND locale='pt-BR'")}
    grammar = [{"id": gid, "slug": slug, "key": key, "label": lab or "", "level": lv or "",
                "register": reg or "", "forms": [f for f in jload(forms) if isinstance(f, str)]}
               for gid, slug, key, lab, lv, reg, forms in con.execute(
                   "SELECT id,slug,key,label_pt,level,register,forms_json FROM grammar_point")]

    known: set[int] = set()
    course: list[dict] = []
    shortfall: list[dict] = []
    used: set[int] = set()

    for ord_, (slug, title, band, seeds) in enumerate(STAGES, start=1):
        # stage candidates: a seed must match a whole TOKEN (surface or lemma). Seeds of 4+ chars may
        # also match as a substring, which is how the frozen expressions the analyzer shreds
        # (すみません -> すみ+ませ+ん) still find their sentences without re-admitting はい/はいり.
        def matches(sid: int, jp: str) -> bool:
            toks = stok.get(sid, ())
            return any(k in toks or (len(k) >= 4 and k in jp) for k in seeds)

        cands = [s for sid, s in sents.items() if sid not in used and matches(sid, s["jp"])]
        stage_units: list[dict] = []

        for u in range(1, UNITS_PER_STAGE + 1):
            # re-rank every unit: "new" is relative to the CURRENT known set, which just grew
            scored = []
            for s in cands:
                if s["id"] in used:
                    continue
                words = [] if s["chunk"] else sv.get(s["id"], [])
                if not words and not s["chunk"]:
                    continue
                new = [v for v in words if v not in known]
                if len(new) > MAX_NEW:
                    continue
                # Bucket, not raw count. Sorting by fewest-new (the first attempt) preferred sentences
                # that taught NOTHING, so whole units came out with zero new vocabulary once the early
                # stages had absorbed the common words. i+1 wants exactly 1..MAX_NEW new words:
                #   0 = set phrase, learned whole -> the right way to open the course
                #   1 = teaches 1..MAX_NEW new words -> the normal case
                #   2 = teaches nothing new -> filler, only if a unit cannot be filled otherwise
                bucket = 0 if s["chunk"] else (1 if new else 2)
                scored.append(((s["ai"], bucket,
                                min((vocab[v]["freq"] for v in new), default=10 ** 9),
                                len(s["jp"])), s, new))
            if not scored:
                break
            scored.sort(key=lambda t: t[0])

            picked, new_ids = [], []
            local: set[int] = set()
            for _, s, new in scored:
                if len(picked) >= PHRASES_PER_UNIT:
                    break
                # recompute against words this unit already introduced, so a unit cannot smuggle in
                # 6 x MAX_NEW words at once
                still = [] if s["chunk"] else [v for v in sv.get(s["id"], [])
                                               if v not in known and v not in local]
                if len(still) > MAX_NEW:
                    continue
                picked.append(s)
                local.update(still)
                new_ids.extend(v for v in still if v not in new_ids)
            if not picked:
                break
            # A unit that introduces nothing and teaches no set phrase is the stage telling us it is
            # exhausted. Emitting it would pad the path with review disguised as progress.
            if not local and not any(s["chunk"] for s in picked):
                break
            for s in picked:
                used.add(s["id"])
            known.update(local)

            # A form must be at least 2 characters to count as a pattern. Single-kana forms (く, に,
            # ら, し, さ) occur in almost every Japanese sentence, so matching on them attached the same
            # meaningless "pattern" to 62 of 72 units. Longest match first = most specific.
            jp_all = "".join(s["jp"] for s in picked)
            patterns = []
            for g in grammar:
                hits = [f for f in g["forms"] if len(f) >= 2 and f in jp_all]
                if hits:
                    patterns.append((max(len(h) for h in hits), g))
            patterns.sort(key=lambda t: (-t[0], t[1]["level"], t[1]["key"]))
            patterns = [g for _, g in patterns]
            words_sorted = sorted(new_ids, key=lambda v: (vocab[v]["freq"], vocab[v]["level"]))
            sign = []
            for s in picked:
                for kid in sk.get(s["id"], []):
                    ch = kanji.get(kid)
                    if ch and ch not in sign:
                        sign.append(ch)

            stage_units.append({
                "id": f"speak:{slug}-{u:02d}",
                "schema_version": "1.0",
                "stage": f"speak:{slug}",
                "order": u,
                "title": {"pt-BR": f"{title} — parte {u}"},
                "say_now": [s["slug"] for s in picked],
                "chunk_phrases": [s["slug"] for s in picked if s["chunk"]],
                "untranslated": [s["slug"] for s in picked if not ptx.get(s["id"])],
                "words": [vocab[v]["slug"] for v in words_sorted],
                "patterns": [g["slug"] for g in patterns[:6]],
                "signage_kanji": sign[:KANJI_PER_UNIT],
                "shadowing": [s["slug"] for s in picked],
                "audio": "pending",
                "real_phrases": sum(1 for s in picked if not s["ai"]),
                "cumulative_known_vocab": len(known),
                "layer": "C",
                "needs_review": True,
            })
            if len(picked) < PHRASES_PER_UNIT:
                shortfall.append({"stage": slug, "unit": u, "got": len(picked),
                                  "want": PHRASES_PER_UNIT})

        if len(stage_units) < UNITS_PER_STAGE:
            shortfall.append({"stage": slug, "units": len(stage_units), "want": UNITS_PER_STAGE})
        course.append({"slug": f"speak:{slug}", "order": ord_, "title": {"pt-BR": title},
                       "approx_band": band, "units": stage_units})

    total_u = sum(len(s["units"]) for s in course)
    total_p = sum(len(u["say_now"]) for s in course for u in s["units"])
    total_real = sum(u["real_phrases"] for s in course for u in s["units"])

    if not args.dry_run:
        OUT.mkdir(parents=True, exist_ok=True)
        for stage in course:
            d = OUT / stage["slug"].split(":", 1)[1]
            d.mkdir(exist_ok=True)
            # Clear stale units first. A rebuild that yields FEWER units than the previous run would
            # otherwise leave orphans on disk that no manifest references but the app still ships —
            # a stage that shrank from 6 units to 4 left unit-05/06 behind and the prototype loaded 72
            # units for a 66-unit path.
            keep = {f"unit-{u['order']:02d}.json" for u in stage["units"]}
            for old in d.glob("unit-*.json"):
                if old.name not in keep:
                    old.unlink()
            for u in stage["units"]:
                (d / f"unit-{u['order']:02d}.json").write_text(
                    json.dumps(u, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        (OUT / "course.json").write_text(json.dumps(
            {"id": "course:speak", "schema_version": "1.0",
             "title": {"pt-BR": "Trilha Fala Primeiro"},
             "description": {"pt-BR": "Do zero ao nível ~N3 pela fala: as palavras mais comuns e as "
                                      "frases que você realmente usa, na ordem em que você precisa "
                                      "delas. Não segue a ordem do JLPT."},
             "spec": "design/speaking_path.md",
             "ordering": "survival scenario (primary) + vocab.freq_rank (secondary)",
             "stages": [{k: v for k, v in s.items() if k != "units"} |
                        {"unit_count": len(s["units"]),
                         "unit_ids": [u["id"] for u in s["units"]]} for s in course],
             "totals": {"stages": len(course), "units": total_u, "phrases": total_p,
                        "real_phrases": total_real, "vocab_introduced": len(known)},
             "shortfall": shortfall,
             "layer": "C", "needs_review": True}, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8")

        idx = ["# course/speak — Trilha Fala Primeiro (speaking-first path)", "",
               "A SECOND ORDERING over the same corpus, not a second corpus: every unit holds corpus IDs "
               "(`sent:`, `vocab:`, `gram:`) and embeds nothing. Spec: `design/speaking_path.md`. "
               "Built by `scripts/export/build_speaking_path.py` — rebuildable and diffable.", "",
               "Ordering is **survival scenario** (primary) then **word frequency** (secondary, from "
               "`vocab.freq_rank`). Every stage is a usable stopping point: a learner who stops after "
               "stage 4 can still land, eat, buy and navigate.", "",
               f"**{len(course)} stages · {total_u} units · {total_p} phrases "
               f"({total_real} real / {total_p - total_real} generated) · "
               f"{len(known)} vocabulary items introduced**", "",
               "| # | Stage | Units | Phrases | New words | ≈band |", "|---|---|---|---|---|---|"]
        for s in course:
            ph = sum(len(u["say_now"]) for u in s["units"])
            nw = sum(len(u["words"]) for u in s["units"])
            idx.append(f"| {s['order']} | {s['title']['pt-BR']} | {len(s['units'])} | {ph} | {nw} | "
                       f"{s['approx_band']} |")
        idx += ["", "`say_now` phrases are real human-written bank sentences; set expressions "
                "(ありがとう, すみません) are taught whole as `chunk_phrases` because the analyzer "
                "mis-lemmatises them (すみません → 住む+ます+ぬ) and because that is how a learner meets "
                "them anyway. `signage_kanji` is **recognition only** — this path never asks the learner "
                "to write kanji. `audio: \"pending\"` throughout, awaiting the voice-over pass "
                "(`design/listening.md`).", ""]
        if shortfall:
            idx += ["## Shortfall", "",
                    "Stages the bank cannot yet fill to target. The fix is SELECTION — mining the "
                    "248,705 already-licensed `raw_tatoeba_sentence` rows — not generated filler; see "
                    "`design/speaking_path.md` §6. Recorded here rather than padded over:", ""]
            idx += [f"- `{s['stage']}`: " + (f"only {s['units']} of {s['want']} units"
                                             if "units" in s else
                                             f"unit {s['unit']} has {s['got']}/{s['want']} phrases")
                    for s in shortfall]
            idx.append("")
        (OUT / "INDEX.md").write_text("\n".join(idx), encoding="utf-8")

    if dropped:
        print(f"dropped {sum(dropped.values())} token links not written in their sentence: "
              + ", ".join(f"{k}x{v}" for k, v in dropped.most_common(8)))
    print(f"speaking path: {len(course)} stages, {total_u} units, {total_p} phrases "
          f"({total_real} real / {total_p - total_real} generated), {len(known)} vocab introduced")
    for s in course:
        got = sum(len(u["say_now"]) for u in s["units"])
        real = sum(u["real_phrases"] for u in s["units"])
        print(f"  {s['slug'].split(':')[1]:16s} {len(s['units'])} units, {got:3d} phrases "
              f"({real} real)")
    if shortfall:
        print(f"shortfall entries: {len(shortfall)} (recorded in course.json)")
    con.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
