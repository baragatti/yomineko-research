"""Plan the voice units from the export (design/audio_pipeline.md §2-§3). Torch-free, read-only.

`plan_units(repo)` returns every unit the export needs, deduplicated by (lang, voice class, normalised
text), each with its consumers (record ids with a JSON-path suffix), its tier, the text to synthesise
(kana for Japanese) and the expected phonetic reading the ASR check compares against.

Tiers follow the consumer, not the sentence label: n5 = pre-N5 + N5 records, then n4, speak, n3.

The synthesis config and the key live HERE too (design §3.3), so the repo's Python computes the
same 26-char key the generator will write, with no GPU and no torch:

  python plan.py                      counts per tier/kind + self-checks
  python plan.py --tier n5 --out F    every unit up to the tier as JSONL {key, spec, kind, tier, ...}
"""
from __future__ import annotations

import base64
import collections
import glob
import hashlib
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

# --- synthesis config (the pins; every field that reaches the spec changes every key) --------------
BASE_REPO, BASE_REV = "ResembleAI/chatterbox", "5bb1f6ee58e50c3b8d408bc82a6d3740c2db6e18"
CONFIG_DEFAULTS = {
    "models": {
        "ja": {"name": "chatterbox-mtl-v3", "language_id": "ja", "t3_repo": BASE_REPO, "t3_revision": BASE_REV,
               "t3_file": "t3_mtl23ls_v3.safetensors",
               "t3_sha256": "5abca8321ede76f8e61f1cc0d19aea6c946b28871017ce8726f8a69203f05953",
               "s3gen_file": "s3gen.pt",
               "s3gen_sha256": "9b9ff07e60b20c136e2b1b3d7563a24604e8d2c4c267888d1ee929dd0151d2a3"},
        "pt-BR": {"name": "chatterbox-mtl-v3-pt-br", "language_id": "pt",
                  "t3_repo": "ResembleAI/Chatterbox-Multilingual-pt-br",
                  "t3_revision": "b3952f18bc2eaa72b9bd7c17d2c4653bcad4770d", "t3_file": "t3_pt_br.safetensors",
                  "t3_sha256": "074aaf65255eb9cb960288f7cc72e09d3b5008f6e0b14868c0d4e5b0bd7cbb6c",
                  "s3gen_file": "s3gen_v3.pt",
                  "s3gen_sha256": "f7abce4b196dae2d08d9296cbebc6521b046079577643b42a19a03499d08721e"},
    },
    "params": {"exaggeration": 0.5, "cfg_weight": 0.5, "temperature": 0.8, "repetition_penalty": 1.2,
               "min_p": 0.05, "top_p": 1.0},
    # Pinned from the gfx1201 benchmark on this stack (ROCm 7.2.1, torch 2.9.1; yomineko-audio/bench.json):
    # bf16 T3 + fp16 flow + fp16 HiFiGAN passed the same 23/30 QA clips as the stock fp32 path at RTF 0.35
    # vs 1.66 (fp32 GEMM runs at 1.8 TFLOPS on this card, bf16 at 77). MIOpen off (native conv) and the
    # static KV cache were each faster with no QA change. torch.compile is not used: no Triton for ROCm
    # on Windows (TritonMissing), so it cannot be benchmarked here.
    "precision": {"t3": "bf16", "flow": "fp16", "hift": "fp16", "miopen": False, "static_kv": True},
    "batch": 8,  # bench: batch 8 RTF 0.35; 16 and 30 were slower (0.80, 0.81), KV traffic dominates
    "batch_kv_budget": 25000,
    "norm": {"ja": "ja-1", "pt-BR": "pt-1"},
    "post": "p1",
    # Pilot voices: the model vendor's own per-language conditioning prompts (female), no third-party
    # recording and no clone. Replaced by consented voices before shipping (a new voice id = new keys).
    "voices": {"ja-word": "ja-pilot-f1@1", "ja-sentence": ["ja-pilot-f1@1"], "ja-M1": "ja-pilot-f1@1",
               "ja-M2": "ja-pilot-f1@1", "ja-F1": "ja-pilot-f1@1", "ja-F2": "ja-pilot-f1@1",
               "ja-N": "ja-pilot-f1@1", "pt-narrator": "pt-pilot-f1@1"},
    "asr_model": "openai/whisper-large-v3",
    "max_takes": 3,
    "opus_bitrate": "32k",
}
VOICES_DEFAULTS = {
    "ja-pilot-f1@1": {
        "lang": "ja", "role": "pilot (all ja classes until consented voices exist)", "gender": "female",
        "file": "voices/res_ja_f.flac",
        "reference_clip_sha256": "62b1b53f8b185a1df9e0086a3eee7f6447f3bbcba5154466e993458270f66e8a",
        "source": "Resemble AI's default ja prompt of the official Chatterbox Multilingual demo "
                  "(HF Space ResembleAI/Chatterbox-Multilingual-TTS@c612a942 -> "
                  "storage.googleapis.com/chatterbox-demo-samples/mtl_prompts/ja/ja_prompts1.flac, identical to ja_f.flac)",
        "consent_ref": None, "licence": "model-bundled demo voice; no consent record; PILOT ONLY, replace before shipping",
        "created": "2026-09-27", "status": "pilot"},
    "pt-pilot-f1@1": {
        "lang": "pt-BR", "role": "pilot pt-narrator", "gender": "female", "file": "voices/res_pt_br_f2.wav",
        "reference_clip_sha256": "b74124fa87356241316d2d55b8f9dfea1da57f08325f63e9198e33f755659482",
        "source": "Resemble AI's default prompt of the official pt-BR Language Pack demo "
                  "(HF Space ResembleAI/Chatterbox-Multilingual-TTS-pt-br@9e515821 -> "
                  "storage.googleapis.com/chatterbox-demo-samples/mtl-v3-single-language-prompts/pt-br/pt_br_f2.wav)",
        "consent_ref": None, "licence": "model-bundled demo voice; no consent record; PILOT ONLY, replace before shipping",
        "created": "2026-09-27", "status": "pilot"},
}


# --- keys (design §3.3) -----------------------------------------------------------------------------
KEY_RE = re.compile(r"^[a-z2-7]{26}$")


def canonical(spec: dict) -> bytes:
    return json.dumps(spec, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def key_of(spec: dict) -> str:
    return base64.b32encode(hashlib.sha256(canonical(spec)).digest()).decode("ascii").lower().rstrip("=")[:26]


def seed_of(spec: dict) -> int:
    return int.from_bytes(hashlib.sha256(canonical(spec)).digest()[:8], "big")


def base_of(spec: dict) -> str:
    """Identity of the utterance across takes: the key of the spec without `take`."""
    s = json.loads(json.dumps(spec))
    s["params"].pop("take", None)
    return key_of(s)


def model_id(m: dict) -> str:
    return f"{m['name']}@{m['t3_sha256'][:12]}.{m['s3gen_sha256'][:12]}"


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


def voice_for(u: Unit, cfg: dict) -> str:
    v = cfg["voices"][u.vclass]
    if isinstance(v, list):  # sentence pool: the choice depends on the text only (design §5)
        v = v[int.from_bytes(hashlib.sha256(u.text.encode("utf-8")).digest()[:8], "big") % len(v)]
    return v


def build_spec(u: Unit, cfg: dict = CONFIG_DEFAULTS, take: int = 1) -> dict:
    p = cfg["precision"]
    params = {**cfg["params"], "precision": f"t3{p['t3']}.flow{p['flow']}.hift{p['hift']}", "take": take}
    return {"v": 1, "kind": "tts", "lang": u.lang, "norm": cfg["norm"][u.lang], "text": u.text,
            "voice": voice_for(u, cfg), "model": model_id(cfg["models"][u.lang]), "params": params,
            "post": cfg["post"]}


class Planner:
    def __init__(self, repo: Path):
        self.repo = repo
        self.units: dict[tuple, Unit] = {}
        self.errors: list[str] = []
        self.ctier: dict[str, str] = {}  # consumer -> its own tier
        self.spans: dict[str, str] = {}  # narration consumer -> element path of its block ("3", "5.1")
        self.sentence_uid: dict[str, tuple] = {}  # bank slug -> its ja-sentence unit
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
    def add(self, kind, lang, vclass, text, display, expected, reading_source, consumer, tier) -> tuple | None:
        text = norm_ja(text) if lang == "ja" else norm_pt(text)
        if lang == "ja":
            if text.startswith(("〜", "~")):
                return None  # pattern fragment: not voiced (§3.1 step 6)
            if not text or KANJI_RE.search(text) or re.search(r"[0-9]", text):
                self.errors.append(f"{consumer}: unresolved text {text!r}")
                return None
        elif not re.search(r"\w", text):
            return None
        key = (lang, vclass, text)
        u = self.units.get(key)
        if u is None:
            u = self.units[key] = Unit(kind, lang, vclass, text, display, expected, reading_source)
        u.consumers.add(consumer)
        u.tiers.add(tier)
        self.ctier[consumer] = min(self.ctier.get(consumer, tier), tier, key=TIERS.index)
        return key

    # japanese sources
    def sentence(self, slug: str, consumer: str, tier: str, vclass: str = "ja-sentence") -> None:
        r = self.bank.get(slug)
        if r is None:
            self.errors.append(f"{consumer}: unknown sentence {slug}")
            return
        text = "".join(kata2hira(t["reading"]) if needs_reading(t["surface"]) else t["surface"]
                       for t in r["tokens"] if t.get("split_mode") == "C")
        uid = self.add("sentence", "ja", vclass, text, r["jp"], r["kana"], "tokens", consumer, tier)
        if uid and vclass == "ja-sentence":
            self.sentence_uid[slug] = uid

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
        # The span of a unit is the element path (child indices over ELEMENTS only, joined by ".") of
        # the block whose runs it voices: "3" = the 4th top-level element, "5.1" = its 2nd child. ""
        # is the body root (a top-level <sentence>/<reading>). The prototype walks the same path.
        span = [""]

        def cid():
            c = f"{lid}#narration[{seq[0]}]"
            seq[0] += 1
            self.spans[c] = span[0]
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

        def inline(el, path=""):
            outer, span[0] = span[0], path
            for i, c in enumerate(el):
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
                    inline(c, f"{path}.{i}" if path else str(i))
                    flush()
                elif tag == "sentence":
                    flush()
                    self.sentence(c.get("ref"), cid(), tier)
                elif tag == "reading":
                    flush()
                    self._passage(c.get("ref"), cid(), tier)
                # romaji, kanji chips, break, exercise, stroke, image, divider: not narrated
            flush()
            span[0] = outer

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


def keyed(pl: Planner, cfg: dict = CONFIG_DEFAULTS) -> dict[tuple, str]:
    """uid -> key. Aborts on a collision: two different canonical specs under one key (design §4.3)."""
    out: dict[tuple, str] = {}
    seen: dict[str, bytes] = {}
    for uid, u in pl.units.items():
        s = build_spec(u, cfg)
        k, c = key_of(s), canonical(s)
        if seen.setdefault(k, c) != c:
            raise SystemExit(f"KEY COLLISION {k}: two different specs")
        out[uid] = k
    return out


NARRATION_RE = re.compile(r"^(les:[^#]+)#narration\[(\d+)\]$")
LISTEN_TURN_RE = re.compile(r"#script\[\d+\]$")
TABLE_KINDS = ("sentence", "vocab", "kana", "listening", "narration")


def expected_keys(repo: Path, tier: str = "n5") -> dict:
    """The audio_key table the export carries for every voiceable item up to `tier` (W47).

    sentence: bank slug -> key, when the sentence's unit is in the tier (a sentence has no tier of its
    own; it takes its lowest consumer's). vocab / kana: record id -> key. listening: `<item>#script[i]`
    -> key. narration: lesson id -> ordered [{span, audio_lang, audio_key}]. All but sentences go by the
    consumer's own tier, so an N4 lesson never gets a partial narration list."""
    pl = plan_units(repo)
    keys = keyed(pl)
    upto = TIERS[: TIERS.index(tier) + 1]
    t: dict = {k: {} for k in TABLE_KINDS}
    for slug, uid in pl.sentence_uid.items():
        if pl.units[uid].tier in upto:
            t["sentence"][slug] = keys[uid]
    narr: dict[str, list] = collections.defaultdict(list)
    for uid, u in pl.units.items():
        for c in u.consumers:
            if pl.ctier[c] not in upto:
                continue
            if c.startswith(("vocab:", "kana:")) and "#" not in c:
                t["vocab" if c.startswith("vocab:") else "kana"][c] = keys[uid]
            elif LISTEN_TURN_RE.search(c):
                t["listening"][c] = keys[uid]
            elif m := NARRATION_RE.match(c):
                narr[m[1]].append((int(m[2]), {"span": pl.spans[c], "audio_lang": u.lang, "audio_key": keys[uid]}))
    t["narration"] = {lid: [e for _, e in sorted(v, key=lambda x: x[0])] for lid, v in narr.items()}
    return {"tier": tier, **{k: dict(sorted(t[k].items())) for k in TABLE_KINDS}}


if __name__ == "__main__":
    import argparse

    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", default=str(Path(__file__).resolve().parents[2]))
    ap.add_argument("--tier", choices=TIERS, default="n5")
    ap.add_argument("--out", help="write every unit up to --tier as JSONL (key, spec, consumers, ...)")
    a = ap.parse_args()
    pl = plan_units(Path(a.repo))
    if a.out:
        keys = keyed(pl)
        upto = TIERS[: TIERS.index(a.tier) + 1]
        rows: dict[str, dict] = {}  # one row per key: two voice classes with one voice share a spec
        for uid, u in pl.units.items():
            if u.tier in upto:
                r = rows.setdefault(keys[uid], {"key": keys[uid], "spec": build_spec(u), "kind": u.kind,
                                                "tier": u.tier, "display": u.display,
                                                "reading_source": u.reading_source, "consumers": []})
                r["consumers"] = sorted(set(r["consumers"]) | u.consumers)
        with open(a.out, "w", encoding="utf-8") as f:
            for k in sorted(rows):
                f.write(json.dumps(rows[k], ensure_ascii=False) + "\n")
        print(f"{len(rows)} keys up to tier {a.tier} -> {a.out}")
        raise SystemExit(0)
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
