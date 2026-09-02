#!/usr/bin/env python3
"""Build the speaking-first course path -> course/speak/. Spec: design/speaking_path.md.

This is a SECOND ORDERING over the existing corpus, not a second corpus: every unit holds corpus IDs
and embeds nothing, so a fix in corpus/vocab reaches both paths. The JLPT path orders by exam
syllabus; this one orders by what a traveller needs to SAY soonest, with word frequency
(vocab.freq_rank, built by scripts/ingest/build_frequency.py) deciding order inside a scenario.

Everything here is mechanical so the path can be rebuilt and diffed:
  * a sentence joins a stage when one of its tokens has a stage SEED as its LEMMA (below -- seeds live
      in code, not prose, so they cannot drift from what actually ran);
  * a stage's SURVIVAL CORE (R87) sorts ahead of the frequency ranking, so the phrases a stage exists
      to teach cannot be crowded out by commoner words;
  * candidates are ordered by (new words, then length), which makes the path start itself: with an
      empty known set the only sentences carrying <=1 new word are the one-word chunks (ありがとう,
      すみません, こんにちは), and longer sentences become eligible as the known set grows. No
      hand-seeded "unit 1" is needed;
  * a sentence qualifies only while its new-word load is <= MAX_NEW (i+1);
  * real sentences (ai_generated=0) are preferred over generated ones and the split is reported;
  * two phrases that differ only in punctuation are ONE phrase (R86), and no stage may draw more than
      BLOCK_CAP phrases from one contiguous run of source ids (R85);
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
from pattern_forms import form_key, matched_length  # noqa: E402  (same directory)
sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
ROOT = Path(__file__).resolve().parents[2]
DB = ROOT / "db" / "corpus.sqlite"
OUT = ROOT / "course" / "speak"

# i+1 budget per SELECTED sentence. Three files carried three numbers — 3 here, "<= 2" in
# design/speaking_path.md section 3, "<= 1" in learning_guidelines.md D.6 — so any auditor written
# against the docs failed every unit this builder emits (learning_science.md R38).
#
# Reconciled at 3, and the DOCS were corrected rather than the code. D.6's "<= 1" governs AUTHORED
# lessons, where the sentence is written to fit the budget. Here we SELECT real human-written sentences
# and cannot rewrite them, so a tighter budget does not make units gentler, it makes them synthetic:
# at 2 the builder ran out of qualifying real sentences and pulled in generated filler, costing the path
# its 100%-real property (394 real + 2 generated) and 62 vocabulary items. Selection over generation
# (spec section 1.2) outranks a round number. The real load control is the per-unit cap below, which
# stops six sentences each carrying MAX_NEW from stacking into one unit.
MAX_NEW = 3
PHRASES_PER_UNIT = 6
UNITS_PER_STAGE = 6
KANJI_PER_UNIT = 6

# R85 (design/speaking_path.md §3.8): no stage may take more than BLOCK_CAP say_now phrases from any
# window of BLOCK_WINDOW consecutive source ids. Tatoeba carries whole textbook exercises as
# consecutive id runs, and one of them — sent:tatoeba-84114..84243, "the room" — filled 25 of lodging's
# 36 slots with third-person descriptions of a room nobody checking into a hotel would ever say.
# Contiguity is the machine-checkable signature of that: a stage drawing half its phrases from one
# 200-id neighbourhood is quoting one exercise, not sampling the language.
BLOCK_CAP = 4
BLOCK_WINDOW = 200

# R86 (§3.9): two bank sentences that differ only in punctuation are ONE phrase to a speaker.
# おはよう！ and おはよう。are the same thing said out loud, and arrival spent 8 of its 36 slots
# teaching four greetings twice. Normalised on this before selection, path-wide.
PUNCT_RE = re.compile(r"[。、！？!?…，,．.・「」『』（）()〜~\s　]")
SRC_RE = re.compile(r"^sent:([a-z]+)-(\d+)$")

# Seeds are DICTIONARY forms, matched against the token LEMMA, plus a substring fallback for seeds of
# 4+ characters. Two earlier attempts are recorded so they are not retried:
#   * raw substring matching put 夕食はいりません ("I don't need dinner") in the greetings stage,
#     because the seed はい occurs inside はいりません;
#   * matching the token SURFACE as well as the lemma looked like the fix and was not. It still put
#     three footwear sentences in greetings (彼は赤いズボンをはいていた, スリッパをはいてください,
#     それより他の靴をはいてみたいのですが) because 履く's te-form is written はいて and tokenises to
#     the SURFACE はい with the lemma はく. A surface is an inflected accident; only the lemma says
#     which word it is.
# (slug, pt-BR title, approx band, seeds)
STAGES: list[tuple[str, str, str, tuple[str, ...]]] = [
    ("arrival", "Chegar e cumprimentar", "pre-n5",
     ("こんにちは", "ありがとう", "すみません", "はい", "いいえ", "お願いします", "はじめまして",
      "さようなら", "ごめんなさい", "おはよう", "こんばんは", "どうも", "失礼します")),
    # NB: seeds must be SPECIFIC to the scenario. ください was a shopping seed and filled the whole
    # stage with 〜てください grammar drills; 行く was a getting_around seed and filled that one with
    # obligation forms. A seed that appears in every other sentence selects for the seed, not the theme.
    # をください, not ください. The bare seed was removed once because it filled the stage with 〜てください
    # drills ("close the door", "wait here") — the polite imperative on a VERB, which is not shopping.
    # をください is the other construction entirely: ask for an OBJECT, それをください, which is the act
    # the stage title names and the thing 36 phrases never taught.
    ("shopping", "Isto, aquilo, quanto custa", "pre-n5/n5",
     ("いくら", "買う", "円", "店", "これ", "それ", "あれ", "安い", "高い", "お金",
      "財布", "払う", "値段", "売る", "をください", "会計", "レジ", "袋", "カード", "現金")),
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

# R87 (§3.7) SURVIVAL CORE. Frequency is the SECONDARY axis and §2 already says scenario wins when they
# conflict; nothing in the code enforced that, so the sort quietly overruled the stage title. shopping is
# the proof: いくらですか？ (sent:tatoeba-5332) matched the いくら seed from the first build, but 幾ら has
# freq_rank 4100, so it lost all 36 slots to commoner words and the stage titled "Isto, aquilo, quanto
# custa" taught あれはキジです ("that is a pheasant") and never a price question — while the same sentence
# was used as a grammar DRILL in four other stages. A term listed here marks the phrases a stage exists to
# teach: they sort ahead of the frequency ranking (but still behind real-over-generated, and still under
# the same i+1 budget as everything else), so a survival phrase can no longer be crowded out by a commoner
# one. Matched exactly like the seeds above: lemma, or substring for 4+ characters.
# Survival terms are PHRASES wherever the bare word is ambiguous, and they are matched the same way as
# the seeds above (lemma, or substring for 4+ characters). Bare いくら was tried first and promoted the
# concessive frame instead of the price question — いくらお礼を言っても言い切れない and
# いくら考えても、わかりません went to the top of shopping-01 — because いくら…ても is a different word
# wearing the same spelling. 円 was tried too and promoted the foreign exchange desk
# (ドルは円に対して下がった). The survival core is the phrase a stage exists to teach, so it is written
# as one; the plain words stay in `seeds` above, where frequency ranks them like anything else.
SURVIVAL_SEEDS: dict[str, tuple[str, ...]] = {
    "shopping": ("いくらですか", "いくらぐらい", "これをください", "それをください", "あれをください",
                 "値段", "会計", "レジ"),
}

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
    # token LEMMAS per sentence, for exact seed matching. Surfaces are deliberately NOT indexed: the
    # surface of a token is whatever inflection the sentence happened to use, so matching it made はい
    # ("yes") select 履く's te-form stem and put three footwear sentences in the greetings stage.
    slem: dict[int, set[str]] = {}
    for sid, surf, lem in con.execute(
            "SELECT sentence_id,surface,lemma FROM token WHERE split_mode='C'"):
        if sid in sents:
            slem.setdefault(sid, set()).add(lem or surf)
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
    used_text: set[str] = set()      # R86: punctuation-normalised jp of every phrase already selected

    for ord_, (slug, title, band, seeds) in enumerate(STAGES, start=1):
        survival = SURVIVAL_SEEDS.get(slug, ())

        # stage candidates: a seed must match a whole token's LEMMA. Seeds of 4+ chars may also match as
        # a substring, which is how the frozen expressions the analyzer shreds (すみません -> すみ+ませ+ん)
        # still find their sentences without re-admitting はい/はいて.
        def seed_hit(sid: int, jp: str, terms) -> bool:
            lems = slem.get(sid, ())
            return any(k in lems or (len(k) >= 4 and k in jp) for k in terms)

        cands = [s for sid, s in sents.items()
                 if sid not in used and seed_hit(sid, s["jp"], seeds)]
        stage_src: list[tuple[str, int]] = []      # R85: (source, id) of this stage's picks
        stage_units: list[dict] = []

        for u in range(1, UNITS_PER_STAGE + 1):
            # re-rank every unit: "new" is relative to the CURRENT known set, which just grew
            scored = []
            for s in cands:
                if s["id"] in used or PUNCT_RE.sub("", s["jp"]) in used_text:
                    continue                                   # R86: same phrase, other punctuation
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
                #   1 = the stage's survival core (R87) -> the phrases the stage exists to teach
                #   2 = teaches 1..MAX_NEW new words -> the normal case
                #   3 = teaches nothing new -> filler, only if a unit cannot be filled otherwise
                if s["chunk"]:
                    bucket = 0
                elif seed_hit(s["id"], s["jp"], survival):
                    bucket = 1
                else:
                    bucket = 2 if new else 3
                # Inside the survival bucket, SHORTEST first rather than commonest-word first: the bare
                # canonical act (いくらですか？) is what the stage owes the learner in its first unit,
                # and ranking survival phrases by frequency again just reintroduces the bug — it put
                # the price question in unit 6, behind 私はこのワープロを手ごろな値段で買った.
                scored.append(((s["ai"], bucket, len(s["jp"]) if bucket == 1 else 0,
                                min((vocab[v]["freq"] for v in new), default=10 ** 9),
                                len(s["jp"])), s, new))
            if not scored:
                break
            scored.sort(key=lambda t: t[0])

            picked, new_ids = [], []
            local: set[int] = set()
            local_text: set[str] = set()
            for _, s, new in scored:
                if len(picked) >= PHRASES_PER_UNIT:
                    break
                text = PUNCT_RE.sub("", s["jp"])
                if text in local_text:
                    continue                                   # R86, within this unit
                # R85: refuse a fifth phrase out of the same contiguous run of source ids.
                m = SRC_RE.match(s["slug"])
                if m:
                    src, num = m.group(1), int(m.group(2))
                    if sum(1 for a, b in stage_src
                           if a == src and abs(b - num) <= BLOCK_WINDOW) >= BLOCK_CAP:
                        continue
                # recompute against words this unit already introduced, so a unit cannot smuggle in
                # 6 x MAX_NEW words at once
                still = [] if s["chunk"] else [v for v in sv.get(s["id"], [])
                                               if v not in known and v not in local]
                if len(still) > MAX_NEW:
                    continue
                picked.append(s)
                local.update(still)
                local_text.add(text)
                if m:
                    stage_src.append((m.group(1), int(m.group(2))))
                new_ids.extend(v for v in still if v not in new_ids)
            if not picked:
                break
            # A unit that introduces nothing and teaches no set phrase is the stage telling us it is
            # exhausted. Emitting it would pad the path with review disguised as progress.
            if not local and not any(s["chunk"] for s in picked):
                break
            for s in picked:
                used.add(s["id"])
                used_text.add(PUNCT_RE.sub("", s["jp"]))
            known.update(local)

            # A form must be at least 2 characters to count as a pattern. Single-kana forms (く, に,
            # ら, し, さ) occur in almost every Japanese sentence, so matching on them attached the same
            # meaningless "pattern" to 62 of 72 units. Longest match first = most specific.
            #
            # Chunk phrases are excluded from the match text. A frozen greeting has no live grammar to
            # teach, but its letters still match forms by substring: arrival/unit-02 is さようなら /
            # すみません / おはようございます and was listing you-ni-you-na, nara and you-da, every one an
            # artifact of ございます and さようなら. A unit of pure set phrases must show no patterns.
            jp_all = "".join(s["jp"] for s in picked if not s["chunk"])
            patterns = []
            for g in grammar:
                # Forms carry textbook placeholders (たり～たりする, お～ください): match their
                # literal pieces in order, never the raw string. See scripts/export/pattern_forms.py.
                hits = [matched_length(f, jp_all) for f in g["forms"] if len(form_key(f)) >= 2]
                hits = [h for h in hits if h]
                if hits:
                    patterns.append((max(hits), g))
            patterns.sort(key=lambda t: (-t[0], t[1]["level"], t[1]["key"]))
            patterns = [g for _, g in patterns]
            # No unit teaches one grammar point twice under two identities: when two candidates'
            # >=2-char form sets are nested (gram:gp {です} inside gram:da-desu {だ,です}), keep the
            # superset record — it is the more complete statement of the same point. Nine units used
            # to drill the copula twice because of exactly this pair.
            def richness(g):
                # canonical survivor on ties: more raw forms first (da-desu {da,desu} beats gp
                # {desu}), then the earlier-taught level, then a stable key order
                return (-len(g["forms"]), g["level"], g["key"])
            # Same grammar point under two identities (gram:gp {desu} vs gram:da-desu {da,desu})
            # must not be drilled twice in one unit: EQUAL effective form sets collapse to the
            # canonical record. Equality ONLY — a strict-subset rule looked right and was wrong:
            # composite patterns list their components as separate forms (wa-yori-desu carries
            # yori AND desu), so subset-dedupe silently ate the standalone copula from every unit
            # that also taught a comparison. Two records are only the same point when they claim
            # the same forms.
            kept: list = []
            for g in patterns:
                fs = {form_key(f) for f in g["forms"] if len(form_key(f)) >= 2}
                replaced = False
                for i, k in enumerate(kept):
                    ks = {form_key(f) for f in k["forms"] if len(form_key(f)) >= 2}
                    if fs and fs == ks:
                        if richness(g) < richness(k):
                            kept[i] = g
                        replaced = True
                        break
                if not replaced:
                    kept.append(g)
            patterns = kept
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
                "title": {"pt-BR": f"{title}, parte {u}"},
                "say_now": [s["slug"] for s in picked],
                "chunk_phrases": [s["slug"] for s in picked if s["chunk"]],
                "untranslated": [s["slug"] for s in picked if not ptx.get(s["id"])],
                "words": [vocab[v]["slug"] for v in words_sorted],
                "patterns": [g["slug"] for g in patterns[:6]],
                # Named `signage_kanji` originally, and design/speaking_path.md described it as
                # "入口 出口 男 女 駅 円 …". It never was: it is every kanji appearing in the unit's
                # phrases, 212 distinct across the path, of which about 18 are classic signage. Renamed to
                # say what it holds. The recognition-only policy is unchanged and still correct.
                "kanji_recognition": sign[:KANJI_PER_UNIT],
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
                "them anyway. `kanji_recognition` is **recognition only** — this path never asks the learner "
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
