#!/usr/bin/env python3
"""Align a word's KANA across its KANJI, so each kanji is credited with the sound it actually lends.

WHY THIS EXISTS. `build_kanji_reading_groups.py` decided which reading a compound belongs to by asking
"does this reading appear in the word's kana, in a plausible position?" That question is answerable
without ever looking at the other kanji, and it is the wrong question. It produced, and needed a
separate patch for, each of:

    一人   ひとり     ひと credited to 人, but 人 sounds り there and ひと belongs to 一
    三味線 しゃみせん   み credited to 三, but 三 sounds しゃ and み belongs to 味
    誕生日 たんじょうび  う credited to 生, but 生 sounds じょう there
    立場   たちば      た credited to 立, but 立 sounds たち
    売り切れる うりきれる れる credited to 売, but that れる is 切れる's

Every one of those is the same mistake: a substring of the kana was claimed by a kanji that is not
making that sound, because nothing checked whether the REST of the word could still be accounted for.
That is a constraint the whole word imposes, so it has to be solved over the whole word.

WHAT THIS DOES. Given a headword and its kana, find an assignment of one contiguous kana span to each
kanji such that the spans, interleaved with the headword's literal kana, reconstruct the reading exactly:

    誕生日 / たんじょうび  ->  誕:たん  生:じょう  日:び
    売り切れる / うりきれる ->  売:う  [り]  切:き  [れる]
    硝子 / がらす          ->  no assignment exists, because す is not among 子's readings after
                              がら fails for 硝  ->  the word is 熟字訓/ateji and belongs in `irregular`

Sound changes are allowed on each span (rendaku, handakuten, 促音便) through `variants`, and an
alignment that needs fewer of them scores higher, so 存's ソン is preferred over ゾン-via-rendaku when
both would fit. On/kun consistency scores too: 音読み compounds read all-on far more often than mixed,
which is what separates 気's real キ from a spurious kun き.

WHAT IT DELIBERATELY DOES NOT DO. It does not pick between two readings that share a bare form -- 痛い
and 痛む both give 痛 the span いた. Alignment fixes the SPAN; choosing among the okurigana slots that
share it is a separate question, and `build_kanji_reading_groups` answers it with the okurigana
shared-prefix and consonant-row scoring it already had.

Every kanji in the word that our registry knows must resolve. One it does not know may absorb any span,
because we have no readings to check it against and refusing on that basis would discard the word for a
reason that is about our coverage rather than about the word.
"""
from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
LEVELS = ("n5", "n4", "n3", "n2", "n1")

VOICED = {"か": "が", "き": "ぎ", "く": "ぐ", "け": "げ", "こ": "ご", "さ": "ざ", "し": "じ",
          "す": "ず", "せ": "ぜ", "そ": "ぞ", "た": "だ", "ち": "ぢ", "つ": "づ", "て": "で",
          "と": "ど", "は": "ば", "ひ": "び", "ふ": "ぶ", "へ": "べ", "ほ": "ぼ"}
PLOSIVE = {"は": "ぱ", "ひ": "ぴ", "ふ": "ぷ", "へ": "ぺ", "ほ": "ぽ"}
KATA = {chr(c): chr(c - 0x60) for c in range(0x30A1, 0x30F7)}
KANA_RANGE = set("ぁぃぅぇぉゃゅょっー぀ゕゖ") | {chr(c) for c in range(0x3041, 0x3097)} | \
             {chr(c) for c in range(0x30A1, 0x30FB)} | {"ー"}
ITERATION = "々"      # 踊り字: repeats the PREVIOUS kanji (時々 = 時+時), so it is neither kana nor a
                      # character with readings of its own. Treating it as kana made it demand a literal
                      # 々 in the reading, which no reading contains, and 15 reduplications (偶々, 元々,
                      # 別々, 堂々, 少々, 広々, 時々, 様々, 次々, 段々, 種々, 等々, 精々, 色々, 若々しい)
                      # all failed to align and fell to `irregular`.


@lru_cache(maxsize=1)
def no_kun_kanji() -> frozenset[str]:
    """Kanji that Kanji Alive records with NO kun reading, as a second opinion on KANJIDIC.

    KANJIDIC lists a kun き for 気, and it is an artifact: Kanji Alive gives 気 kunyomi n/a and onyomi
    キ、ケ, and the 常用漢字表 assigns it only キ and ケ. Left to itself the aligner filed 気, 気持ち and
    気づく under that phantom kun while 病気, 天気 and 元気 went to the real ON キ -- the same syllable
    split across two groups with no difference a learner could see or use.

    Used as a TIEBREAK, never as a deletion. KANJIDIC is Layer A and we do not overwrite it; a reading
    it lists stays listed. What this changes is which slot wins when a kun and an on reading match the
    same span equally well, which is exactly the case where KANJIDIC alone has nothing to say.
    344 of the 1,235 kanji Kanji Alive covers are in this position.
    """
    path = ROOT / "research" / "datasets" / "kanjialive" / "ka_data.csv"
    if not path.exists():
        return frozenset()
    import csv
    out = set()
    with path.open(encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            ch = (row.get("kanji") or "").strip()
            kun = (row.get("kunyomi_ja") or "").strip().lower()
            if ch and kun in ("", "n/a", "na"):
                out.add(ch)
    return frozenset(out)


def hira(s: str) -> str:
    return "".join(KATA.get(c, c) for c in s or "")


def bare(reading: str) -> str:
    """KANJIDIC2 decorations: '-び' bound form, '書.く' okurigana split."""
    r = (reading or "").replace("-", "").replace("‐", "")
    if "." in r:
        r = r.split(".", 1)[0]
    return hira(r)


def variants(r: str) -> list[str]:
    """The sound changes a reading undergoes inside a compound, unchanged form first."""
    out = [r]
    if r and r[0] in VOICED:
        out.append(VOICED[r[0]] + r[1:])          # rendaku: ひ -> び in 誕生日
    if r and r[0] in PLOSIVE:
        out.append(PLOSIVE[r[0]] + r[1:])         # handakuten: ハイ -> ぱい in 一杯
    if len(r) > 1 and r.endswith(("つ", "ち", "く", "き")):
        out.append(r[:-1] + "っ")                 # 促音便: シュツ -> しゅっ in 出発
    if r:
        # Gemination can also be ADDED after a reading rather than replacing its final mora: 切手 is
        # きって, where 切 lends き and the っ geminates 手's consonant. Substitution alone turned a
        # one-mora reading into a bare っ (き -> "" + っ), which matched nothing and lost 切手, 切符 and
        # 小切手 to `irregular`.
        out.append(r + "っ")
    return [x for x in out if x]


ROWS = ("あいうえお", "かきくけこがぎぐげご", "さしすせそざじずぜぞ", "たちつてとだぢづでど",
        "なにぬねの", "はひふへほばびぶべぼぱぴぷぺぽ", "まみむめも", "やゆよ", "らりるれろ", "わをん")
_ROW_OF = {c: i for i, r in enumerate(ROWS) for c in r}


def row_of(c: str) -> int | None:
    """Which kana row a mora belongs to. A Japanese verb inflects WITHIN its row (済ます / 済ませ,
    痛む / 痛み), which is what lets an okurigana be recognised as a form of another."""
    return _ROW_OF.get(c)


U_TO_I = {"う": "い", "く": "き", "ぐ": "ぎ", "す": "し", "つ": "ち", "ぬ": "に",
          "ぶ": "び", "む": "み", "る": "り"}


def masu_stem(oku: str) -> str:
    """The 連用形 of an okurigana ending, which is the form a compound NOUN absorbs.

    A compound noun routinely drops the okurigana its verb would write AND uses the masu-stem rather
    than the dictionary form: 割り引き -> 割引 (わりびき), 取り引き -> 取引, 受け付け -> 受付, 貸し出し ->
    貸出, 待ち合い室 -> 待合室, 植え木 -> 植木. Absorbing the dictionary okurigana alone gives 割 the span
    わる, which is not in わりびき, so every one of those fell to `irregular`.

    五段 shifts the final mora from the う-row to the い-row (る -> り); 一段 simply drops the る.
    """
    if not oku:
        return ""
    if oku.endswith(("える", "ける", "せる", "てる", "ねる", "べる", "める", "れる", "げる", "でる",
                     "きる", "しる", "ちる", "にる", "びる", "みる", "りる", "いる", "ぜる", "じる")):
        return oku[:-1]                            # 一段: 受ける -> 受け, 植える -> 植え
    last = oku[-1]
    return oku[:-1] + U_TO_I[last] if last in U_TO_I else ""


# Phrases a note uses to say a word's reading belongs to the WHOLE word rather than to this kanji.
# A heuristic, not a definition: two good notes were nearly refused for describing 熟字訓 accurately in
# plain pt-BR ("a leitura pertence à palavra inteira, não ao kanji sozinho") without using the word
# "irregular", which reads better than the keyword would have.
JUKUJIKUN_MARKERS = ("irregular", "exceç", "excec", "熟字訓", "não segue", "nao segue",
                     "palavra inteira", "palavra toda", "não ao kanji", "nao ao kanji", "conjunto")


def named_compounds(text: str, known: set[str], character: str, citation: str = "") -> set[str]:
    """Which of `known` a note actually NAMES, as opposed to appearing to.

    Two ways a naive scan sees a claim that is not there, both found by running it over real notes:

      SUBSTRING. 八's note says "nesta lista ela esta em お八つ". A regex anchored on the first kanji
      pulls 八つ out of お八つ, and 八つ is a different word filed under a different reading, so the note
      appears to cite an absent compound while naming only the one it is filed under. Any headword that
      occurs solely inside a LONGER known headword present in the text is dropped.

      CITATION FORM. 回's -まわ.る note says "quando 回る fecha uma palavra composta". 回る there is the
      name of the reading, not a claim about what is in the group -- the note goes on to say the group
      is empty. A word equal to the reading's own citation form (the kanji plus its okurigana) is
      therefore not a membership claim.
    """
    hits = {w for w in known if w and w in text}
    hits = {w for w in hits
            if not any(other != w and w in other and other in hits for other in hits)}
    if citation:
        hits.discard(citation)
    hits.discard(character)
    return hits


# Phrases that assert a reading group holds nothing. Deliberately grouping-specific: a bare scan for
# "vazio" flags 空's kun note (the reading MEANS empty) and 腹's フク note (空腹 is an empty stomach).
EMPTY_CLAIMS = ("ficou agrupad", "foi agrupad", "ficaram agrupad", "foram agrupad",
                "não recebeu nenhum exemplo", "nao recebeu nenhum exemplo",
                "sem exemplo", "nenhum composto", "nenhum vocabul", "nenhuma palavra",
                "lista desta leitura está vazia", "lista desta leitura esta vazia",
                "não há exemplo", "nao ha exemplo", "nenhum exemplo")


def claims_empty(text: str) -> bool:
    """Does this note assert that its reading group holds nothing?"""
    return any(t in text.lower() for t in EMPTY_CLAIMS)


def explains_placement(text: str, destination: str, current: str = "") -> bool:
    """Does this note say where a compound it names actually belongs?

    Naming a compound that is NOT in this reading's group is legitimate, and often the most useful
    thing the note can do -- 気's kun き is far clearer for saying "em 病気, 天気 e 元気 quem aparece e
    a leitura sino-japonesa キ" than for pretending those words are unrelated. What is not legitimate
    is listing it as an example OF THIS READING, which is failure mode F1.

    `destination` and `current` are full slot labels ("な.い", "キ."). When the two share a bare reading
    and differ only in okurigana, naming the reading proves nothing -- it is the same string the slot
    is already called -- so the note must name the FULL destination label. That circularity let a note
    on 亡's な.き- pass while presenting 亡くなる and 亡くす as its examples, when both live in な.い:
    the test asked whether "な" appeared, and of course it did.

    Treating every mention as a defect is the opposite failure, and refused 35 of 63 otherwise-good
    notes, each of which was explaining exactly where the word had gone.
    """
    if destination == "(irregular)":
        return any(t in text.lower() for t in JUKUJIKUN_MARKERS)
    if not destination:
        return False
    d_read = destination.split(".", 1)[0]
    c_read = (current or "").split(".", 1)[0]
    if c_read and d_read == c_read:
        # SIBLING SLOTS, same bare reading, different okurigana. A note here cannot mislead about the
        # thing the grouping exists to answer -- which READING the word uses -- because the answer is
        # identical either way; at worst it is imprecise about the okurigana slot. And the prose that
        # names a sibling is almost always doing the most useful thing available: 乗's の.せる says
        # "Em relação a 乗る muda só o okurigana", 映's うつ.す the same for 映る.
        #
        # Demanding the sibling's full label refused all four of those. The cases where a sibling
        # mention WAS a real defect -- 亡's な.き- presenting 亡くなる as its example, 重's bare おも
        # opening "O exemplo desta lista é 重たい" -- are both empty groups, and the emptiness gates
        # catch them for what they actually are: a note that does not say its group is empty.
        return True
    return d_read in text


def is_kanji(ch: str) -> bool:
    return not (ch in KANA_RANGE or ch.isascii())


class Aligner:
    """Holds the reading inventory for every kanji the corpus knows, across all five levels."""

    def __init__(self, entries: list[dict] | None = None) -> None:
        if entries is None:
            entries = []
            for lv in LEVELS:
                p = ROOT / "corpus" / "kanji" / f"{lv}.json"
                if p.exists():
                    entries += json.loads(p.read_text(encoding="utf-8"))
        self.readings: dict[str, list[dict]] = {}
        for k in entries:
            ch = k.get("character")
            if not ch:
                continue
            rows = []
            for r in k.get("readings") or []:
                # NANORI are name-readings. Letting them align ordinary words is how 明日 (あした) got
                # credited to 日's あ nanori instead of being recognised as the 熟字訓 it is.
                if (r.get("type") or "").lower() == "nanori":
                    continue
                b = bare(r.get("reading"))
                if b:
                    oku = hira(r.get("okurigana") or "").replace("-", "").replace("‐", "")
                    rows.append({"reading": r.get("reading"), "bare": b, "okurigana": oku,
                                 "type": (r.get("type") or "").lower(),
                                 "common": bool(r.get("common"))})
            self.readings[ch] = rows

    def spans_for(self, ch: str, kana: str, at: int) -> list[tuple[int, dict, int]]:
        """(end_index, reading_row, penalty) for every reading of `ch` that fits `kana` at `at`.

        penalty is 0 for the reading as written and 1 when a sound change was needed, so an alignment
        that takes 存 as ソン outscores the one that takes it as ゾン through rendaku.
        """
        out = []
        for row in self.readings.get(ch, ()):
            for i, v in enumerate(variants(row["bare"])):
                if v and kana.startswith(v, at):
                    out.append((at + len(v), row, 0 if i == 0 else 1))
            # 送り仮名の省略. A compound noun routinely drops okurigana the verb would write, and the
            # kanji then carries that sound itself: 立ち場 -> 立場 (たちば), 押し入れ -> 押入れ (おしいれ),
            # 取り引き -> 取引. So a kun reading may also span bare+okurigana, at a penalty so the plain
            # reading still wins wherever both fit. The headword's own literal kana keeps this from
            # over-firing: in 持ち the ち is written, so a 持=もち span leaves that literal ち with
            # nothing to match and the alignment dies on its own.
            oku = row["okurigana"]
            if oku and row["type"] == "kun":
                for form in (oku, masu_stem(oku)):
                    if not form:
                        continue
                    for i, v in enumerate(variants(row["bare"] + form)):
                        if v and kana.startswith(v, at):
                            out.append((at + len(v), row, 2 if i == 0 else 3))
        return out

    def align(self, headword: str, kana: str) -> list[dict] | None:
        """Best assignment of kana spans to the kanji of `headword`, or None if none exists.

        Returns one row per HEADWORD CHARACTER: {char, kana, is_kanji, reading?} -- literal kana in the
        headword get a row too, so a caller can see exactly which tail belongs to which kanji.
        """
        kana = hira(kana or "")
        hw = headword or ""
        if not hw or not kana:
            return None
        best: list[tuple[int, list[dict]]] = []

        def walk(i: int, at: int, acc: list[dict], score: int, unresolved: int = 0) -> None:
            if i == len(hw):
                if at == len(kana):
                    best.append((score, list(acc)))
                return
            if len(best) > 400:                    # pathological safety valve; never hit in practice
                return
            ch = hw[i]
            if ch == ITERATION:
                # 踊り字 repeats the previous kanji, and the repeat is usually voiced (時々 ときどき,
                # 様々 さまざま), which `variants` already covers.
                prev_ch = next((a["char"] for a in reversed(acc) if a["is_kanji"]), None)
                if prev_ch is None:
                    return
                for end, row, pen in self.spans_for(prev_ch, kana, at):
                    walk(i + 1, end,
                         acc + [{"char": ch, "kana": kana[at:end], "is_kanji": True, "reading": row}],
                         score + 4 - pen)
                return
            if ch in ("ヶ", "ヵ"):
                # Small ヶ/ヵ in a counter is not kana at all: it is an abbreviation of 箇 and reads か
                # (or が after voicing) -- ヶ月 is かげつ. Normalising it as katakana demanded a literal
                # ゖ in the reading, which never appears.
                for v in ("か", "が"):
                    if kana.startswith(v, at):
                        walk(i + 1, at + 1,
                             acc + [{"char": ch, "kana": v, "is_kanji": False}], score)
                return
            if not is_kanji(ch):
                # Literal kana in the headword must appear literally in the reading. ー is allowed to
                # correspond to a long vowel spelled out (ケーキ / けえき), so it is not required.
                c = hira(ch)
                if c == "ー":
                    if at < len(kana):
                        walk(i + 1, at + 1, acc + [{"char": ch, "kana": kana[at], "is_kanji": False}],
                             score, unresolved)
                    walk(i + 1, at, acc + [{"char": ch, "kana": "", "is_kanji": False}], score,
                         unresolved)
                    return
                if kana.startswith(c, at):
                    walk(i + 1, at + len(c),
                         acc + [{"char": ch, "kana": c, "is_kanji": False}], score, unresolved)
                return
            options = self.spans_for(ch, kana, at)
            if options:
                for end, row, pen in options:
                    bonus = 6 - pen * 2 + (2 if row["common"] else 0)
                    if row["type"] == "kun" and ch in no_kun_kanji():
                        bonus -= 5      # KANJIDIC lists a kun Kanji Alive does not recognise
                    prev = next((a for a in reversed(acc) if a["is_kanji"]), None)
                    if prev is not None and prev.get("reading"):
                        # 音訓 consistency: a kanji compound is overwhelmingly all-on or all-kun, and
                        # mixed readings (重箱読み / 湯桶読み) are the marked case. This is what keeps
                        # 病気 / 天気 / 空気 on 気's ON reading instead of a look-alike kun.
                        bonus += 2 if prev["reading"]["type"] == row["type"] else 0
                    walk(i + 1, end,
                         acc + [{"char": ch, "kana": kana[at:end], "is_kanji": True, "reading": row}],
                         score + bonus, unresolved)
            if ch not in self.readings:
                # A kanji we hold no readings for cannot be checked, so it may take any non-empty span.
                # Refusing here would drop the word for a gap in OUR coverage rather than anything
                # about the word. A kanji we DO know must resolve — that is what sends 硝子 (がらす,
                # where 子 would have to sound す after 硝 fails) to `irregular`, correctly.
                for end in range(at + 1, len(kana) + 1):
                    walk(i + 1, end,
                         acc + [{"char": ch, "kana": kana[at:end], "is_kanji": True}], score,
                         unresolved)
                return
            if unresolved == 0:
                # ONE kanji may go unexplained, heavily penalised and marked. All-or-nothing alignment
                # punished the wrong character: 日本 (にほん) failed only because 日's に is listed in
                # this corpus as a nanori, and 本 -- which contributes ほん, the plain ON reading, with
                # no sound change at all -- lost its single most common N5 example to `irregular`.
                # A kanji that DID resolve still gets credit; the one that did not is excluded by
                # span_of, so 日 still shows 日本 as irregular, which is correct for 日.
                #
                # Capped at one so genuine 熟字訓 keep failing: 今日, 明日, 昨日 and 硝子 have no
                # per-kanji account on EITHER side and must stay in `irregular`.
                # The unresolved span must still be a PLAUSIBLE truncation: it has to share its first
                # mora with one of this kanji's readings. Without that test, partial alignment rescues
                # the very 熟字訓 it was capped to protect -- 明日 (あした) aligned as 明:あ + 日:した and
                # filed 明日 under 明's あ.かり, when あした belongs to the whole word and to no reading
                # of either kanji. 日本 passes because 日's span に opens にち; 明日 fails because no
                # reading of 日 begins with し.
                firsts = {row["bare"][0] for row in self.readings.get(ch, ()) if row["bare"]}
                for v in list(firsts):
                    if v in VOICED:
                        firsts.add(VOICED[v])
                    if v in PLOSIVE:
                        firsts.add(PLOSIVE[v])
                for end in range(at + 1, len(kana) + 1):
                    if kana[at] not in firsts:
                        continue
                    walk(i + 1, end,
                         acc + [{"char": ch, "kana": kana[at:end], "is_kanji": True,
                                 "unresolved": True}],
                         score - 40, unresolved + 1)

        walk(0, 0, [], 0)
        if not best:
            return None
        best.sort(key=lambda t: -t[0])
        return best[0][1]

    def span_of(self, headword: str, kana: str, target: str, occurrence: int = 0) -> dict | None:
        """The aligned span for one occurrence of `target` in `headword`, plus its trailing okurigana.

        `okurigana` is the literal kana the headword writes immediately after that kanji — the thing a
        reading's own okurigana has to be judged against. It stops at the next kanji, so 売り切れる gives
        売 the okurigana り and not りきれる.
        """
        rows = self.align(headword, kana)
        if rows is None:
            return None
        seen = -1
        for i, row in enumerate(rows):
            if row["char"] != target or not row["is_kanji"]:
                continue
            seen += 1
            if seen != occurrence:
                continue
            if row.get("unresolved"):
                # This kanji is the one the alignment could not account for, so it has no reading to
                # be filed under even though the rest of the word resolved.
                return None
            oku = ""
            for nxt in rows[i + 1:]:
                if nxt["is_kanji"]:
                    break
                oku += nxt["kana"]
            return {"span": row["kana"], "okurigana": oku,
                    "reading": row.get("reading"), "alignment": rows}
        return None


@lru_cache(maxsize=1)
def default() -> Aligner:
    return Aligner()
