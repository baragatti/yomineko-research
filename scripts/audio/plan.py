"""Plan the voice units from the export (design/audio_pipeline.md §2-§3). Torch-free, read-only.

`plan_units(repo)` returns every unit the export needs, deduplicated by (lang, voice class, normalised
text), each with its consumers (record ids with a JSON-path suffix), its tier, the text to synthesise
(kana for Japanese) and the expected phonetic reading the ASR check compares against.

Tiers follow the consumer, not the sentence label: n5 = pre-N5 + N5 records, then n4, speak, n3.
"""
from __future__ import annotations

import glob
import json
import re
import unicodedata
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from pathlib import Path

TIERS = ("n5", "n4", "speak", "n3")
LEVEL_TIER = {"pre-n5": "n5", "n5": "n5", "n4": "n4", "n3": "n3"}
KANJI_RE = re.compile(r"[㐀-䶿一-鿿豈-﫿々〆ヶ]")
DIGIT_LATIN_RE = re.compile(r"[0-9A-Za-z０-９Ａ-Ｚａ-ｚ]")
CJK_RUN_RE = re.compile(r"[぀-ヿ㐀-䶿一-鿿々〆〜～ー]+")
JA_DROP = str.maketrans("", "", "「」『』（）()[]\"'“”‘’・")
PT_DROP = str.maketrans("", "", "\"'“”‘’«»()[]")
SMALL = set("ゃゅょぁぃぅぇぉゎ")
UNVOICED_GLYPHS = {"っ", "ッ", "ー"}  # sokuon / chouon have no sound on their own


def kata2hira(s: str) -> str:
    return "".join(chr(ord(c) - 0x60) if "ァ" <= c <= "ヶ" else c for c in s)


def needs_reading(surface: str) -> bool:
    return bool(KANJI_RE.search(surface) or DIGIT_LATIN_RE.search(surface))


def norm_ja(text: str) -> str:
    """norm ja-1 (design §3.1 steps 1-5)."""
    t = unicodedata.normalize("NFKC", text)
    t = re.sub(r"\s+", "", t).translate(JA_DROP)
    if t.endswith(("。", ".")):
        t = t[:-1]
    return t


def norm_pt(text: str) -> str:
    """norm pt-1 (design §3.1), plus: leading symbols left over from cutting a sentence around an inline
    Japanese chip (", …", "= …", ": …") are dropped; they are not spoken."""
    t = unicodedata.normalize("NFKC", text)
    t = re.sub(r"\s+", " ", t).strip().translate(PT_DROP).strip()
    t = re.sub(r"^[^\w¿¡]+", "", t)
    if t.endswith(".") and not t.endswith(".."):
        t = t[:-1].rstrip()
    return t


# --- phonetic readings (shared with the ASR check) --------------------------------------------------
_TOK = None


def _tokenizer():
    global _TOK
    if _TOK is None:
        from sudachipy import dictionary, tokenizer
        _TOK = (dictionary.Dictionary(dict="full").create(), tokenizer.Tokenizer.SplitMode.C)
    return _TOK


_KDIG = "〇一二三四五六七八九"


def num_kanji(n: int) -> str:
    """Arabic integer -> kanji numeral (1000 -> 千, 10000 -> 一万, 2026 -> 二千二十六)."""
    def small(m: int) -> str:
        s = ""
        for v, ch in ((1000, "千"), (100, "百"), (10, "十")):
            d, m = divmod(m, v)
            if d:
                s += ("" if d == 1 else _KDIG[d]) + ch
        return s + (_KDIG[m] if m else "")
    if n == 0:
        return "零"
    s = ""
    for v, ch in ((10**12, "兆"), (10**8, "億"), (10**4, "万")):
        d, n = divmod(n, v)
        if d:
            s += small(d) + ch
    return s + small(n)


def kanji_numerals(text: str) -> str:
    return re.sub(r"\d[\d,]*", lambda m: num_kanji(int(m.group().replace(",", ""))), text)


def sudachi(text: str) -> tuple[str, str]:
    """(synthesis kana, phonetic hiragana) for untokenised Japanese, SplitMode C, full dict (§3.2).
    Arabic numerals become kanji numerals first so the dictionary resolves counters (5日 -> 五日 -> いつか)."""
    tok, mode = _tokenizer()
    synth, phon = [], []
    for m in tok.tokenize(kanji_numerals(unicodedata.normalize("NFKC", text)), mode):
        s, pos = m.surface(), m.part_of_speech()
        rd = kata2hira(m.reading_form() or s)
        synth.append(rd if needs_reading(s) else s)
        if pos[0] in ("補助記号", "空白"):
            continue
        if pos[0] == "助詞" and s in ("は", "へ"):
            rd = {"は": "わ", "へ": "え"}[s]
        phon.append(rd)
    return "".join(synth), "".join(phon)


VOWEL_OF = {}
for _row, _v in (("あかさたなはまやらわがざだばぱぁゃゎ", "あ"), ("いきしちにひみりぎじぢびぴぃ", "い"),
                 ("うくすつぬふむゆるぐずづぶぷぅゅ", "う"), ("えけせてねへめれげぜでべぺぇ", "え"),
                 ("おこそとのほもよろをごぞどぼぽぉょ", "お")):
    for _c in _row:
        VOWEL_OF[_c] = _v


def canon(h: str) -> str:
    """Canonical phonetic hiragana for comparison: both sides go through the same folding."""
    h = kata2hira(unicodedata.normalize("NFKC", h))
    h = "".join(c for c in h if "ぁ" <= c <= "ゖ" or c == "ー")
    h = h.replace("を", "お").replace("ぢ", "じ").replace("づ", "ず")
    out: list[str] = []
    for c in h:
        prev = VOWEL_OF.get(out[-1]) if out else None
        if c == "ー":
            if prev:
                out.append(prev)
            continue
        if c == "う" and prev == "お":
            c = "お"
        elif c == "い" and prev == "え":
            c = "え"
        out.append(c)
    return "".join(out)


def morae(h: str) -> int:
    return sum(1 for c in canon(h) if c not in SMALL)


# --- units --------------------------------------------------------------------------------------
@dataclass
class Unit:
    kind: str
    lang: str
    vclass: str
    text: str  # synthesis text, normalised (this is hashed)
    display: str
    expected: str  # ja: phonetic hiragana; pt: the normalised text
    reading_source: str
    consumers: set = field(default_factory=set)
    tiers: set = field(default_factory=set)

    @property
    def tier(self) -> str:
        return min(self.tiers, key=TIERS.index)

    @property
    def uid(self) -> tuple:
        return (self.lang, self.vclass, self.text)


class Planner:
    def __init__(self, repo: Path):
        self.repo = repo
        self.units: dict[tuple, Unit] = {}
        self.errors: list[str] = []
        self.bank = {r["slug"]: r for r in self._load("corpus/sentences/bank.json")}
        self.bank_by_jp = {norm_ja(r["jp"]): r for r in self.bank.values()}
        self.vocab = {}
        for lvl in ("n5", "n4", "n3"):
            for r in self._load(f"corpus/vocab/{lvl}.json"):
                self.vocab[r["slug"]] = r
        self.grammar = {}
        for p in sorted(glob.glob(str(repo / "corpus/grammar/*.json"))):
            for r in json.loads(Path(p).read_text(encoding="utf-8")):
                self.grammar[r["slug"]] = r
        self.readings = {}
        for lvl in ("n5", "n4", "n3"):
            for r in self._load(f"corpus/readings/{lvl}.json"):
                self.readings[r["slug"]] = r

    def _load(self, rel: str):
        return json.loads((self.repo / rel).read_text(encoding="utf-8"))

    # core add
    def add(self, kind, lang, vclass, text, display, expected, reading_source, consumer, tier) -> None:
        text = norm_ja(text) if lang == "ja" else norm_pt(text)
        if lang == "ja":
            if text.startswith(("〜", "~")):
                return  # pattern fragment: not voiced (§3.1 step 6)
            if not text or KANJI_RE.search(text) or re.search(r"[0-9]", text):
                self.errors.append(f"{consumer}: unresolved text {text!r}")
                return
        elif not re.search(r"\w", text):
            return
        key = (lang, vclass, text)
        u = self.units.get(key)
        if u is None:
            u = self.units[key] = Unit(kind, lang, vclass, text, display, expected, reading_source)
        u.consumers.add(consumer)
        u.tiers.add(tier)

    # japanese sources
    def sentence(self, slug: str, consumer: str, tier: str, vclass: str = "ja-sentence") -> None:
        r = self.bank.get(slug)
        if r is None:
            self.errors.append(f"{consumer}: unknown sentence {slug}")
            return
        text = "".join(kata2hira(t["reading"]) if needs_reading(t["surface"]) else t["surface"]
                       for t in r["tokens"] if t.get("split_mode") == "C")
        self.add("sentence", "ja", vclass, text, r["jp"], r["kana"], "tokens", consumer, tier)

    def word(self, kana: str, display: str, consumer: str, tier: str, kind: str = "word", src: str = "vocab") -> None:
        self.add(kind, "ja", "ja-word", kana, display, sudachi(kana)[1], src, consumer, tier)

    def ja_text(self, text: str, consumer: str, tier: str, vclass: str, kind: str, reading: str | None = None) -> None:
        """Untokenised Japanese: a verified bank sentence if the text is one, else SudachiPy (§3.2)."""
        hit = self.bank_by_jp.get(norm_ja(text))
        if hit is not None and reading is None:
            if vclass == "ja-word":  # keep the class; the text resolution comes from the verified tokens
                text_k = "".join(kata2hira(t["reading"]) if needs_reading(t["surface"]) else t["surface"]
                                 for t in hit["tokens"] if t.get("split_mode") == "C")
                self.add(kind, "ja", vclass, text_k, text, hit["kana"], "tokens", consumer, tier)
            else:
                self.sentence(hit["slug"], consumer, tier, vclass)
            return
        if reading:
            self.add(kind, "ja", vclass, reading, text, sudachi(reading)[1], "attr", consumer, tier)
            return
        synth, phon = sudachi(text)
        src = "kana" if not needs_reading(text) else "sudachi"
        self.add(kind, "ja", vclass, synth, text, phon, src, consumer, tier)

    # --- walkers ------------------------------------------------------------------------------
    def plan(self) -> "Planner":
        self._vocab_records()
        self._kanji()
        self._kana()
        self._lessons()
        self._listening()
        self._speak()
        return self

    def _vocab_records(self):
        for slug, r in self.vocab.items():
            self.word(r["kana"], r["headword"], slug, LEVEL_TIER[r["level"]])

    def _kanji(self):
        for lvl in ("n5", "n4", "n3"):
            for k in self._load(f"corpus/kanji/{lvl}.json"):
                for i, ew in enumerate(k.get("example_words") or []):
                    v = self.vocab.get(ew.get("slug"))
                    kana = v["kana"] if v else ew["kana"]
                    self.word(kana, ew["headword"], f"{k['slug']}#example_words[{i}]", LEVEL_TIER[lvl])
                for i, s in enumerate(k.get("example_sentences") or []):
                    slug = s if isinstance(s, str) else s.get("slug") or s.get("sentence")
                    self.sentence(slug, f"{k['slug']}#example_sentences[{i}]", LEVEL_TIER[lvl])

    def _kana(self):
        for f in ("hiragana", "katakana"):
            for e in self._load(f"corpus/kana/{f}.json"):
                if e["char"] not in UNVOICED_GLYPHS:
                    self.word(e["char"], e["char"], e["id"], "n5", kind="kana", src="kana")

    def _lessons(self):
        for p in sorted(glob.glob(str(self.repo / "course/*/topic-*/lesson-*.json"))):
            les = json.loads(Path(p).read_text(encoding="utf-8"))
            tier = LEVEL_TIER.get(les["level"])
            if tier is None:
                continue
            raw = json.dumps({k: v for k, v in les.items() if k != "body"}, ensure_ascii=False)
            for slug in sorted(set(re.findall(r"sent:[\w\-]+", raw))):
                self.sentence(slug, les["id"], tier)
            self._narration(les["id"], les["body"], tier)

    def _narration(self, lid: str, body: str, tier: str):
        root = ET.fromstring(f"<root>{body}</root>")
        seq = [0]  # running index into narration[]

        def cid():
            c = f"{lid}#narration[{seq[0]}]"
            seq[0] += 1
            return c

        buf: list[str] = []

        def flush():
            text = "".join(buf)
            buf.clear()
            for part in re.split(f"({CJK_RUN_RE.pattern})", text):
                if not part.strip():
                    continue
                if CJK_RUN_RE.fullmatch(part):
                    self.ja_text(part, cid(), tier, "ja-word", "inline")
                    continue
                for sent in re.split(r"(?<=[.!?…])\s+", part):
                    if re.search(r"\w", norm_pt(sent)):
                        self.add("narration", "pt-BR", "pt-narrator", sent, sent, norm_pt(sent), "text", cid(), tier)

        def inline(el):
            for c in el:
                if c.get("speak") == "false":
                    continue
                tag = c.tag
                if tag in ("text", "term", "emphasis"):
                    buf.append("".join(c.itertext()))
                elif tag == "jp":
                    flush()
                    self.ja_text("".join(c.itertext()), cid(), tier, "ja-word", "inline", c.get("reading"))
                elif tag == "ruby":
                    flush()
                    self.ja_text(c.get("base", ""), cid(), tier, "ja-word", "inline", c.get("reading"))
                elif tag == "vocab":
                    flush()
                    v = self.vocab.get(c.get("ref"))
                    if v:
                        self.word(v["kana"], v["headword"], cid(), tier)
                elif tag == "grammar":
                    flush()
                    g = self.grammar.get(c.get("ref"))
                    form = unicodedata.normalize("NFKC", (g.get("forms") or [{}])[0].get("form", "")) if g else ""
                    if form and not form.startswith(("~", "〜")) and "/" not in form:
                        self.ja_text(form, cid(), tier, "ja-word", "inline")
                elif tag in ("p", "item", "check", "heading", "note", "list", "checklist"):
                    flush()
                    inline(c)
                    flush()
                elif tag == "sentence":
                    flush()
                    self.sentence(c.get("ref"), cid(), tier)
                elif tag == "reading":
                    flush()
                    self._passage(c.get("ref"), cid(), tier)
                # romaji, kanji chips, break, exercise, stroke, image, divider: not narrated
            flush()

        inline(root)

    def _passage(self, slug: str, consumer: str, tier: str):
        r = self.readings.get(slug)
        if r is None:
            self.errors.append(f"{consumer}: unknown reading {slug}")
            return
        sents, cur = [], []
        for t in r["tokens"]:
            cur.append(t)
            if t["s"] in ("。", "？", "！", "?", "!"):
                sents.append(cur)
                cur = []
        if cur:
            sents.append(cur)
        for i, toks in enumerate(sents):
            text = "".join(kata2hira(t["r"]) if needs_reading(t["s"]) else t["s"] for t in toks)
            phon = "".join(t["r"] for t in toks if t.get("pos") != "punctuation")
            display = "".join(t["s"] for t in toks)
            self.add("passage", "ja", "ja-sentence", text, display, phon, "tokens", f"{slug}#sentences[{i}]", tier)

    def _listening(self):
        for p in sorted(glob.glob(str(self.repo / "corpus/exam_banks/*_listening_*.json"))):
            name = Path(p).stem
            lvl, kind = name.split("_listening_")
            tier = LEVEL_TIER[lvl]
            for it in json.loads(Path(p).read_text(encoding="utf-8")):
                iid = it["id"]
                for i, turn in enumerate(it.get("script") or []):
                    self.ja_text(turn["text"], f"{iid}#script[{i}]", tier, f"ja-{turn['speaker']}", "listen")
                if it.get("question"):
                    self.ja_text(it["question"], f"{iid}#question", tier, "ja-N", "listen")
                if kind in ("reply", "say", "gist"):
                    self.ja_text(it["correct"], f"{iid}#correct", tier, "ja-N", "listen")
                    for j, d in enumerate(it.get("distractors") or []):
                        self.ja_text(d, f"{iid}#distractors[{j}]", tier, "ja-N", "listen")
                if it.get("sentence"):
                    self.sentence(it["sentence"], iid, tier)

    def _speak(self):
        for p in sorted(glob.glob(str(self.repo / "course/speak/*/unit-*.json"))):
            u = json.loads(Path(p).read_text(encoding="utf-8"))
            for field_ in ("say_now", "shadowing", "chunk_phrases"):
                for i, ref in enumerate(u.get(field_) or []):
                    if isinstance(ref, str) and ref.startswith("sent:"):
                        self.sentence(ref, f"{u['id']}#{field_}[{i}]", "speak")
                    elif isinstance(ref, str):
                        self.ja_text(ref, f"{u['id']}#{field_}[{i}]", "speak", "ja-sentence", "listen")


def plan_units(repo: Path) -> Planner:
    return Planner(repo).plan()


if __name__ == "__main__":
    import collections
    import sys

    pl = plan_units(Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).resolve().parents[2])
    c = collections.Counter((u.tier, u.kind) for u in pl.units.values())
    for k in sorted(c, key=lambda k: (TIERS.index(k[0]), k[1])):
        print(*k, c[k])
    chars = collections.Counter()
    for u in pl.units.values():
        chars[(u.tier, u.lang)] += len(u.text)
    print(dict(chars))
    print("errors", len(pl.errors), pl.errors[:10])
    # self-check of the phonetic folding
    assert canon("オトーサン") == canon("おとうさん") == "おとおさん"
    assert canon("せんせい") == "せんせえ" and canon("を") == "お"
    assert norm_ja("「わかりました。」") == "わかりました" and norm_pt("Olá, tudo bem.") == "Olá, tudo bem"
    assert norm_pt(", = Sou ruim.") == "Sou ruim" and num_kanji(2000) == "二千" and num_kanji(10000) == "一万"
    assert sudachi("5日に来ます")[0].startswith("いつか"), sudachi("5日に来ます")
