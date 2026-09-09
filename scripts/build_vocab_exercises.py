#!/usr/bin/env python3
"""W20 vocab + grammar half — derive one practice exercise per unpractised (lesson, item) pair.

WHAT THIS IS FOR
----------------
`scripts/validate/validate_practice_coverage.py` asks, per item, "was THIS item asked by the lesson
that unlocks it?". The kanji half of the answer is now zero absent at every level (W20 apply,
`research/reports/w20_apply_report.md`). The vocab and grammar halves are not: 2,303 (lesson, vocab)
pairs and 35 (lesson, grammar) pairs unlock an item, enrol an SRS card for it, and never put it on a
single answer surface.

APP_PLAN §1 says MECHANICAL FIRST: "a script derives everything the registries, the Dissector or the
builders can produce, writes the residue as the work list, and the plan row records the split". This
script is that script. It authors NOTHING free-form:

  * every Japanese string it emits is a bank sentence verbatim, a token surface cut from that
    sentence's own Layer-A dissection, or a registry `headword`/`kana`;
  * every pt-BR string is a fixed template filled with a registry gloss, a grammar label or a bank
    translation. No prose is written per item.

An item a template cannot serve is not guessed at: the pair goes to the RESIDUE with a reason class,
and that residue is the work list a later authoring campaign consumes.

THE TEMPLATES, IN PREFERENCE ORDER
----------------------------------
The order is "closest to real language first". A cloze over a real sentence asks the learner to
retrieve the word in context; a four-option MCQ asks them to recognise it; free production asks them
to write it from a gloss alone, which is the item most likely to be ambiguous.

  (a) V-CLOZE   — a bank sentence that (1) this lesson already renders (`sentence_refs`, body
                  `<sentence ref>`, or an exercise's own refs) or, failing that, (2) is entirely
                  inside the lesson's `cumulative_known_set`: every kanji of the sentence is a known
                  kanji, every token's vocab record and every run-linked vocab record is a known
                  word, and no content token is an unlinked kanji word. The target's own token is
                  blanked at its Sudachi boundary; the prompt is the blanked sentence plus the bank's
                  pt-BR translation. `answer.full` is the sentence verbatim, so
                  `validate_practice_coverage` reads it through the sentence's Layer-A dissection
                  rather than through its own tiler (rule (a) of that gate's docstring).
  (b) V-RECOG   — four options. Stem is the record's pt-BR gloss, key is the spelling `key_form()`
                  picks (NOT the `headword`: see that function), and the three distractors are
                  records from the SAME lesson's known set with the same coarse POS and a different
                  gloss, never a homograph sibling of the key, never a record that shares one of the
                  key's written forms or its kana, and preferring options with the same
                  kanji-or-kana shape as the key so the answer is not visible from across the room.
                  Distractor choice is seeded and load-balanced, so no single word becomes the
                  course's default wrong answer.
  (c) V-PROD    — free production from the gloss. Reached only when (b) cannot be built (fewer than
                  three usable distractors). AMBIGUITY IS MEASURED, not assumed (`disambiguate()`):
                  a production gloss is ambiguous when another record in the same lesson's known set
                  carries the same FIRST gloss, and an ambiguous one gets a hint derived from the
                  record itself (a gloss of its own sense past the ones the stem already shows, or
                  its part of speech when that alone separates it). If it is ambiguous and no hint
                  separates it, the pair goes to the residue rather than shipping a question with two
                  right answers. The same machinery runs over (b) with the whole visible STEM as the
                  key, where the failure is not an unanswerable item but two items reading alike.
  (d) G-CLOZE   — grammar. A bank sentence TAGGED with the point (the tag is the grammar `key`, which
                  is how the coverage gate credits it), rendered by the lesson or inside its known
                  set, with the point's own form blanked. The span comes from the grammar record's
                  `forms[].form` / `structure_pattern` probe segments and must align to token
                  boundaries on both sides, so the blank is a morpheme and not a slice of one.

WHAT THIS SCRIPT REFUSES TO DO
------------------------------
It never emits an item it cannot prove closes the pair. Every candidate is run through the coverage
gate's OWN predicate (imported from `validate_practice_coverage`, not reimplemented) before it is
written: if adding this exercise would not move the target from absent to practised, the template is
rejected and the next one is tried. A pair no template can close is residue.

DETERMINISM. Pure function of the exported tree plus a fixed SEED. Choices that need a tiebreak are
made by a stable BLAKE2b hash of the row's identity, never by `random` state that depends on
iteration order. Re-running on an unchanged tree rewrites byte-identical files, which is what makes
it idempotent: the table is the output, the tree is the input, and nothing is written into `course/`
or `db/` here (`scripts/apply_practice_exercises.py` does that, from the table).

OUTPUT
    research/derived/pending/practice_vocab_exercises.json   the rows, in the kanji table's shape
    research/derived/pending/practice_vocab_residue.json     the pairs no template could serve

Usage: build_vocab_exercises.py [--root PATH] [--out-root PATH] [--limit N] [--stats]
"""
from __future__ import annotations

import argparse
import collections
import hashlib
import json
import re
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts" / "validate"))
import validate_practice_coverage as vpc  # noqa: E402  (the gate's own rule, imported not copied)

LOC = "pt-BR"
SEED = "w20-vocab-practice-2026-09-09"

KANJI_RX = re.compile(r"[一-鿿㐀-䶿]")
# One Japanese letter (not punctuation): used to refuse a "cloze" whose blank eats the sentence.
JP_LETTER_RX = re.compile(r"[぀-ヿ㐀-䶿一-鿿ｦ-ﾟ々〆ー]")
MIN_JP_LEFT = 2
BLANK = "＿＿"
# Sudachi's own coarse tags, as the dissection stores them on each token. A token outside this set
# (particle, auxiliary, punctuation, whitespace) is grammar, never a "word the learner must know".
CONTENT_POS = {"noun", "verb", "i-adjective", "na-adjective", "adverb", "pronoun",
               "adnominal", "conjunction", "interjection", "suffix", "prefix"}
# JMdict POS -> the coarse class a distractor has to share with the key. Finer than this makes the
# pool empty for half the course (v5r vs v5k is not a distinction a learner sees in an MCQ);
# coarser makes a noun a plausible option for a verb, which gives the answer away by shape.
POS_CLASS = {
    "n": "noun", "n-suf": "noun", "n-pref": "noun", "pn": "noun", "num": "noun", "ctr": "noun",
    "adj-no": "noun",
    "adj-i": "adj-i", "adj-ix": "adj-i", "adj-f": "adj-i", "adj-t": "adj-i",
    "adj-na": "adj-na", "adj-pn": "adj-na",
    "adv": "adv", "adv-to": "adv",
    "exp": "exp", "conj": "conj", "int": "int", "suf": "suf", "pref": "pref",
    "prt": "prt", "aux": "aux",
}
POS_LABEL = {"noun": "substantivo", "verb": "verbo", "adj-i": "adjetivo em -i",
             "adj-na": "adjetivo em -na", "adv": "advérbio", "exp": "expressão",
             "conj": "conjunção", "int": "interjeição", "suf": "sufixo", "pref": "prefixo",
             "prt": "partícula", "aux": "auxiliar"}
BRACKET_PAIRS = (("(", ")"), ("（", "）"), ("「", "」"), ("『", "』"), ("[", "]"))
TERMINAL = tuple(".?!:…。？！」』)）\"'")
EX_NUM_RX = re.compile(r"^(.*)-(\d+)$")


def pos_class(tag: str) -> str:
    if tag in POS_CLASS:
        return POS_CLASS[tag]
    if tag.startswith(("v1", "v5", "v2", "vs", "vz", "vk", "vn", "vr")):
        return "verb"
    return tag


def h(*parts: str) -> int:
    """A stable integer for a tuple of identifiers: the only source of 'randomness' in this file."""
    return int.from_bytes(hashlib.blake2b("\x1f".join((SEED,) + parts).encode("utf-8"),
                                          digest_size=8).digest(), "big")


def balanced(text: str) -> bool:
    return all(text.count(a) == text.count(b) for a, b in BRACKET_PAIRS)


def prose_ok(text: str) -> bool:
    """The two prose rules `validate_exercise_contracts` enforces, plus the project's em-dash ban."""
    t = (text or "").strip()
    return bool(t) and balanced(t) and t.endswith(TERMINAL) and "—" not in t and "–" not in t


def kana_only(s: str) -> bool:
    return bool(s) and all("ぁ" <= c <= "ヿ" or c in "ー〜～" for c in s)


def hira(s: str) -> str:
    return "".join(chr(ord(c) - 0x60) if "ァ" <= c <= "ン" else c for c in s or "")


def reading_fits(tok: dict, rec: dict) -> bool:
    """Does this token really READ as the record it is linked to?

    A token's `vocab` link can name a homograph with a different reading, and the smoke run found
    one: 何時ですか。 ("Que horas são?") tokenises 何時 with `reading` なんじ but links to
    vocab:1188760, the record whose kana is いつ, because 何時 is one of that record's written forms.
    Blanking it would have produced a cloze whose answer key is right and whose explanation names
    the wrong word. The reading is the field that can tell them apart, so it is checked:

      * an uninflected token must read exactly as the record's kana;
      * an inflected one (Sudachi filled `inflection`) only has to share a stem with it, which is
        what 食べ (たべ) does with 食べる (たべる) and what なんじ does not do with いつ.
    """
    kana, rd = hira(rec.get("kana") or ""), hira(tok.get("reading") or "")
    if not kana or not rd:
        return (tok.get("surface") or "") in surfaces_of(rec)
    if rd == kana:
        return True
    if tok.get("inflection") or tok.get("inflection_type"):
        n = 0
        while n < min(len(rd), len(kana)) and rd[n] == kana[n]:
            n += 1
        return n >= 1
    return False


# --------------------------------------------------------------------------- registries
def load_vocab_records(root: Path) -> dict[str, dict]:
    out: dict[str, dict] = {}
    for path in sorted(root.glob("corpus/vocab/*.json")):
        for rec in json.loads(path.read_text(encoding="utf-8")):
            out[rec["slug"]] = rec
    return out


def load_grammar_records(root: Path) -> dict[str, dict]:
    out: dict[str, dict] = {}
    for path in sorted(root.glob("corpus/grammar/*.json")):
        for rec in json.loads(path.read_text(encoding="utf-8")):
            out[rec["slug"]] = rec
    return out


def sense_of(rec: dict) -> dict | None:
    """The first sense that actually carries a pt-BR gloss. Prompts are built from this one."""
    for s in rec.get("senses") or []:
        g = (s.get("gloss") or {}).get(LOC) or []
        if g and str(g[0]).strip():
            return s
    return None


def gloss_key(rec: dict) -> str | None:
    """The canonical meaning string, used for the ambiguity and distractor tests."""
    s = sense_of(rec)
    if not s:
        return None
    return str(((s.get("gloss") or {}).get(LOC) or [""])[0]).strip().lower()


def gloss_text(rec: dict) -> str | None:
    """What the learner reads: up to two glosses of that sense, joined. Never more."""
    s = sense_of(rec)
    if not s:
        return None
    g = [str(x).strip() for x in ((s.get("gloss") or {}).get(LOC) or []) if str(x).strip()]
    return ", ".join(g[:2]) if g else None


def coarse_pos(rec: dict) -> str | None:
    s = sense_of(rec)
    if not s or not s.get("pos"):
        return None
    return pos_class(s["pos"][0])


def surfaces_of(rec: dict) -> set[str]:
    out = {f for f in (rec.get("headword"), rec.get("kana")) if f}
    out |= {f["form"] for f in (rec.get("forms") or []) if f.get("form")}
    return out


def key_form(rec: dict, known_kanji: set[str], attested: dict[str, collections.Counter]) -> str | None:
    """The spelling to put in an answer key for THIS lesson, or None if no spelling is usable.

    `headword` is the wrong field for this and the smoke run proved it: JMdict's headword for あの is
    彼の, for ああ it is 嗚呼, for 五日 it is ５日. Keying on it would ask a beginner to write a
    spelling nobody uses, and ５日 is not even one Japanese run, so the coverage gate would not credit
    it. Three mechanical signals decide instead, in order:

      1. ATTESTATION. The spelling this project's own sentence bank uses for this record, counted
         over token surfaces that exactly equal one of its forms. Real usage beats a dictionary
         header, and it is Layer A.
      2. The lesson's KANJI known set. A form carrying a kanji the lesson has not taught is not an
         answer this learner can write, which is the same rule the kanji half's pre-flight held
         itself to ("every Japanese run in the answer key is inside the lesson's cks").
      3. JMdict `is_common`, then a kanji spelling over a kana one, then the order JMdict lists.
    """
    freq = attested.get(rec["slug"]) or collections.Counter()
    usable = []
    for i, f in enumerate(rec.get("forms") or []):
        form = f.get("form")
        if not form or not vpc.JP_RUN_RX.fullmatch(form):
            continue
        if any(("kanji:" + c) not in known_kanji for c in KANJI_RX.findall(form)):
            continue
        usable.append((-freq[form], 0 if f.get("is_common") else 1,
                       1 if f.get("is_kana") else 0, i, form))
    if not usable:
        return None
    return min(usable)[4]


def display(form: str, rec: dict) -> str:
    kana = rec.get("kana") or ""
    return form if form == kana or not kana else f"{form}（{kana}）"


# --------------------------------------------------------------------------- the tree
def load_lessons(root: Path) -> list[dict]:
    manifest = json.loads((root / "course" / "manifest.json").read_text(encoding="utf-8"))
    taught = [c["level"] for c in sorted(manifest["courses"], key=lambda c: c["order"])]
    level_order = {lv: i for i, lv in enumerate(taught)}
    rows = []
    for path in sorted(root.glob("course/*/topic-*/lesson-*.json")):
        d = json.loads(path.read_text(encoding="utf-8"))
        cks = d.get("cumulative_known_set") or {}
        rendered = set(d.get("sentence_refs") or [])
        rendered |= set(re.findall(r'<sentence\s+ref="([^"]+)"', d.get("body") or ""))
        for ex in d.get("exercises") or []:
            rendered |= set(ex.get("sentence_refs") or [])
        rows.append({
            "id": d.get("id", path.stem),
            "level": path.parent.parent.name,
            "topic": d.get("topic"),
            "path": path.relative_to(root).as_posix(),
            "lesson": d,
            "known_kanji": set(cks.get("kanji") or []),
            "known_vocab": set(cks.get("vocab") or []),
            "rendered": rendered,
            "sort": vpc.lesson_sort_key(path, d, level_order),
        })
    rows.sort(key=lambda r: r["sort"])
    return rows


def index_bank(root: Path) -> tuple[dict[str, dict], dict[str, list[str]], dict[str, list[str]],
                                    dict[str, tuple], dict[str, collections.Counter]]:
    bank = json.loads((root / "corpus" / "sentences" / "bank.json").read_text(encoding="utf-8"))
    by_slug = {r["slug"]: r for r in bank}
    by_vocab: dict[str, list[str]] = collections.defaultdict(list)
    by_gram: dict[str, list[str]] = collections.defaultdict(list)
    attested: dict[str, collections.Counter] = collections.defaultdict(collections.Counter)
    need: dict[str, tuple] = {}
    for r in bank:
        for t in r.get("tokens") or []:
            if t.get("vocab"):
                by_vocab[t["vocab"]].append(r["slug"])
                if t.get("surface"):
                    attested[t["vocab"]][t["surface"]] += 1
        for g in r.get("grammar") or []:
            if isinstance(g, str):
                by_gram["gram:" + g].append(r["slug"])
        kj = {"kanji:" + c for c in KANJI_RX.findall(r.get("jp") or "")}
        vs = {t["vocab"] for t in (r.get("tokens") or []) if t.get("vocab")}
        vs |= {v["ref"] for v in (r.get("vocab") or []) if isinstance(v, dict) and v.get("ref")}
        unlinked = any(not t.get("vocab") and t.get("pos") in CONTENT_POS
                       and not kana_only(t.get("surface") or "") for t in (r.get("tokens") or []))
        need[r["slug"]] = (kj, vs, unlinked)
    for k in by_vocab:
        by_vocab[k] = sorted(dict.fromkeys(by_vocab[k]))
    for k in by_gram:
        by_gram[k] = sorted(dict.fromkeys(by_gram[k]))
    return by_slug, by_vocab, by_gram, need, attested


def sentence_ok(sslug: str, row: dict, need: dict) -> bool:
    """Is this sentence safe to print in front of THIS lesson's learner? i+0, both registries.

    A sentence the lesson already renders is exempt: the learner has met it in the body, and the
    gating of that link is `validate_lesson_gating`'s business, not this script's.
    """
    if sslug in row["rendered"]:
        return True
    kj, vs, unlinked = need[sslug]
    return not unlinked and kj <= row["known_kanji"] and vs <= row["known_vocab"]


def rank_sentences(cands: list[str], row: dict, by_slug: dict, need: dict, ref: str) -> list[str]:
    """Deterministic preference: rendered here, then real over generated, then short, then hashed.

    Spec §1.2 prefers a real human sentence over a generated one wherever both exist, so the
    provenance of the bank row is the second key, ahead of length.
    """
    def key(s: str):
        rec = by_slug[s]
        prov = rec.get("provenance") or {}
        return (0 if s in row["rendered"] else 1,
                1 if prov.get("jp_source") == "ai-generated" else 0,
                len(rec.get("jp") or ""),
                h(ref, row["id"], s))
    return sorted([s for s in cands if sentence_ok(s, row, need)], key=key)


def token_spans(rec: dict) -> list[tuple[int, int, dict]]:
    """(start, end, token) for every token, aligned against `jp` by walking it left to right."""
    jp = rec.get("jp") or ""
    out: list[tuple[int, int, dict]] = []
    i = 0
    for t in rec.get("tokens") or []:
        surf = t.get("surface") or ""
        if not surf:
            continue
        j = jp.find(surf, i)
        if j < 0:
            return []                      # a dissection that does not tile its own jp: unusable
        out.append((j, j + len(surf), t))
        i = j + len(surf)
    return out


# --------------------------------------------------------------------------- crediting
class Credit:
    """The coverage gate's own predicate, over ONE candidate exercise.

    Imported behaviour, not a reimplementation: `answer_surfaces`, `fold_sentence`, the tiler and
    `TARGET_REF_RX` all come from `validate_practice_coverage`. If that file's rule changes, this
    generator changes with it and stops emitting items the gate would not credit.
    """

    def __init__(self, root: Path):
        surfaces, longest = vpc.load_vocab(root)
        self.tile = vpc.make_tiler(surfaces, longest)
        self.gram_probes, _labels = vpc.load_grammar(root)
        self.sentences = vpc.load_sentences(root)

    def credits(self, ex: dict, kind: str, ref: str) -> bool:
        answers = vpc.answer_surfaces(ex.get("answer"))
        marked = set(vpc.TARGET_REF_RX.findall(json.dumps(ex.get("prompt"), ensure_ascii=False)))
        cited = {s for s in (ex.get("sentence_refs") or []) if s in self.sentences}
        verbatim = {self.sentences[s][3] for s in cited}
        tiled: set[str] = set()
        for s in answers:
            if vpc.fold_sentence(s) in verbatim:
                continue
            for run in vpc.JP_RUN_RX.findall(s):
                self.tile(run, tiled)
        sent_vocab: set[str] = set()
        sent_gram: set[str] = set()
        for s in cited:
            v, g, _surf, _f = self.sentences[s]
            sent_vocab |= v
            sent_gram |= g
        if kind == "vocab":
            return ref in tiled or ref in marked or ref in sent_vocab
        whole = set(answers)
        text = "".join(run for s in answers for run in vpc.JP_RUN_RX.findall(s))
        return ref in marked or ref in sent_gram or any(
            (len(seg) > 1 and seg in text) or (len(seg) == 1 and seg in whole)
            for seg in (self.gram_probes.get(ref) or set()))


# --------------------------------------------------------------------------- the work list
def work_list(root: Path, rows: list[dict], credit: Credit) -> list[dict]:
    """Every (lesson, item) pair the gate calls ABSENT today, re-derived from the tree.

    Re-derived on purpose: W11a and the W20 kanji apply both changed the counts after the plan row
    was written, and a work list copied from a report is a work list that has already rotted.
    """
    out: list[dict] = []
    for row in rows:
        d = row["lesson"]
        unlocks: dict[str, list[str]] = collections.defaultdict(list)
        for e in d.get("unlocks") or []:
            if e.get("type") in ("vocab", "grammar") and isinstance(e.get("ref"), str):
                unlocks[e["type"]].append(e["ref"])
        if not unlocks:
            continue
        existing = d.get("exercises") or []
        for kind in ("vocab", "grammar"):
            for ref in unlocks[kind]:
                if any(credit.credits(ex, kind, ref) for ex in existing):
                    continue
                out.append({"lesson": row["id"], "level": row["level"], "topic": row["topic"],
                            "path": row["path"], "kind": kind, "ref": ref})
    return out


# --------------------------------------------------------------------------- id allocation
def id_prefix(d: dict) -> str:
    """The `ex:<prefix>-<n>` pattern THIS lesson already uses, with its own numbering continued.

    Not every lesson's exercise prefix is derived from its slug (`les:n3-causa-04` numbers its items
    `ex:causa-04-*`), so the prefix is read off the data and only synthesised when there is none.
    """
    counts: collections.Counter[str] = collections.Counter()
    for ex in d.get("exercises") or []:
        m = EX_NUM_RX.match(ex.get("id") or "")
        if m:
            counts[m.group(1)] += 1
    if counts:
        return counts.most_common(1)[0][0]
    return "ex:" + d.get("id", "").split(":", 1)[-1]


def next_number(d: dict, prefix: str) -> int:
    best = 0
    for ex in d.get("exercises") or []:
        m = EX_NUM_RX.match(ex.get("id") or "")
        if m and m.group(1) == prefix:
            best = max(best, int(m.group(2)))
    return best + 1


# --------------------------------------------------------------------------- templates
def build_cloze(pair: dict, row: dict, rec: dict, by_slug: dict, by_vocab: dict, need: dict,
                kform: str) -> tuple[dict, str, str] | tuple[None, None, str]:
    ref = pair["ref"]
    for sslug in rank_sentences(by_vocab.get(ref, []), row, by_slug, need, ref):
        sent = by_slug[sslug]
        jp = sent.get("jp") or ""
        pt = ((sent.get("translation") or {}).get(LOC) or "").strip()
        if not pt:
            continue
        spans = token_spans(sent)
        hit = next(((a, b, t) for a, b, t in spans
                    if t.get("vocab") == ref and reading_fits(t, rec)), None)
        if hit is None:
            continue
        a, b, tok = hit
        surface = jp[a:b]
        # a blank that swallows the sentence is a production item wearing a cloze's clothes, and a
        # blank one kana wide is a guess (8人孫が＿ます。 asking for い is not vocabulary practice)
        if not surface.strip() or len(JP_LETTER_RX.findall(jp[:a] + jp[b:])) < MIN_JP_LEFT:
            continue
        if len(JP_LETTER_RX.findall(surface)) < 2 and not KANJI_RX.search(surface):
            continue
        blanked = jp[:a] + BLANK + jp[b:]
        prompt = f"Complete a frase: {blanked} ({pt})"
        gl = gloss_text(rec) or ""
        expl = f"A palavra que falta é {display(kform, rec)}: {gl}."
        if surface != kform and surface != rec.get("kana"):
            expl += f" Na frase ela aparece como {surface}."
        if not (prose_ok(prompt) and prose_ok(expl)):
            continue
        ex = {"type": "cloze",
              "prompt": {LOC: prompt},
              "answer": {"text": surface, "full": jp},
              "explanation": {LOC: expl},
              "sentence_refs": [sslug]}
        why = (f"cloze over bank sentence {sslug} "
               f"({'rendered by this lesson' if sslug in row['rendered'] else 'inside the cks'}); "
               f"the target's own token ({surface}, position {tok.get('position')}) is blanked at its "
               f"Sudachi boundary and answer.full is the sentence verbatim, so the coverage gate "
               f"reads it through the sentence's Layer-A dissection")
        return ex, "cloze", why
    return None, None, "no_cks_clean_sentence"


def distractor_pool(pair: dict, row: dict, rec: dict, V: dict, attested: dict) -> list[tuple[str, str]]:
    """(slug, written form) for every option this lesson may legally show beside the key."""
    ref = pair["ref"]
    key_gloss = gloss_key(rec)
    key_pos = coarse_pos(rec)
    key_forms = surfaces_of(rec)
    key_kana = rec.get("kana")
    if not key_pos:
        return []
    pool = []
    for slug in row["known_vocab"]:
        if slug == ref:
            continue
        other = V.get(slug)
        if not other:
            continue
        og = gloss_key(other)
        if not og or og == key_gloss:
            continue
        if coarse_pos(other) != key_pos:
            continue
        if surfaces_of(other) & key_forms:            # a homograph sibling or a written form of the key
            continue
        if key_kana and other.get("kana") == key_kana:  # a homophone: two right-sounding options
            continue
        if not gloss_text(other):
            continue
        # a distractor is on screen, so it obeys the same known-set rule as the key
        form = key_form(other, row["known_kanji"], attested)
        if not form:
            continue
        pool.append((slug, form))
    return sorted(pool)


def build_recognition(pair: dict, row: dict, rec: dict, V: dict, used: collections.Counter,
                      attested: dict, kform: str) -> tuple[dict, str, str] | tuple[None, None, str]:
    ref = pair["ref"]
    gl = gloss_text(rec)
    if not gl or '"' in gl:
        return None, None, "gloss_unusable_in_stem"
    pool = distractor_pool(pair, row, rec, V, attested)
    if len(pool) < 3:
        return None, None, "no_distractor_pool"
    # Two targets in ONE lesson can share a visible stem (赤 and 赤い are both "vermelho", 軍 and
    # 軍隊 are both "exército, forças armadas"). Each MCQ is still answerable, because same-gloss
    # records are never options, but a learner meeting both reads the same question twice. The same
    # record-derived hint the production template uses is appended where the record allows one.
    hint, why_hint = disambiguate(row, rec, V, ref, gloss_text)
    # Seeded ranking, then load balancing: of the 24 best-hashed candidates take the three that have
    # been used least so far. Pure hash ranking is deterministic but makes a handful of common words
    # the course's default wrong answer; the balance pass keeps the same determinism and spreads them.
    # Orthographic parity first: 136 items in the first full run showed the key as the ONLY option
    # written with kanji, which hands the answer over on shape alone. Options that look like the key
    # are preferred, and the pool is only widened when fewer than three of them exist.
    same_shape = [sf for sf in pool if bool(KANJI_RX.search(sf[1])) == bool(KANJI_RX.search(kform))]
    base = same_shape if len(same_shape) >= 3 else pool
    ranked = sorted(base, key=lambda sf: h(ref, row["id"], sf[0]))[:24]
    chosen = sorted(ranked, key=lambda sf: (used[sf[0]], h(ref, row["id"], sf[0])))[:3]
    for s, _f in chosen:
        used[s] += 1
    options = [kform] + [f for _s, f in chosen]
    if len(set(options)) != 4:
        return None, None, "distractor_collides_with_key"
    order = sorted(options, key=lambda o: h(ref, row["id"], "opt", o))
    parts = ", ".join(f"{f} ({gloss_text(V[s])})" for s, f in chosen[:2])
    expl = (f"{display(kform, rec)} significa {gl}. As outras opções são "
            f"{parts} e {chosen[2][1]} ({gloss_text(V[chosen[2][0]])}).")
    stem = f'"{gl}"' + (f" ({hint})" if hint else "")
    prompt = f"Qual destas palavras significa {stem}?"
    if not (prose_ok(prompt) and prose_ok(expl)):
        return None, None, "unbalanced_prose"
    ex = {"type": "recognition",
          "prompt": {LOC: prompt},
          "answer": {"choices": order, "correct": kform},
          "explanation": {LOC: expl},
          "sentence_refs": []}
    why = (f"recognition MCQ: stem is the record's own pt-BR gloss, key is the spelling {kform} "
           f"(attested/common form inside this lesson's kanji known set), and the three distractors "
           f"({', '.join(s for s, _f in chosen)}) are records in this lesson's cumulative_known_set "
           f"with the same coarse POS ({coarse_pos(rec)}) and a different gloss, none of them a "
           f"homograph sibling, a written form of the key or a homophone of it. Stem collision "
           f"inside the known set: {why_hint}"
           + (f"; hint derived from the record itself ({hint})" if hint else ""))
    return ex, "recognition", why


STEM_GLOSSES = 2          # how many glosses `gloss_text` puts in a prompt; a hint must go past them


def disambiguate(row: dict, rec: dict, V: dict, ref: str, keyfn) -> tuple[str | None, str]:
    """Is this prompt ambiguous inside the lesson's known set, and can the RECORD separate it?

    Ambiguity is measured, never assumed: a collision is another record the lesson already knows
    whose `keyfn` value is the same string. Two keys are used, because the two templates fail
    differently. Production is graded against one accepted spelling, so its collision key is the
    FIRST gloss: a learner told "amor, afeto" who writes 愛情 instead of 愛 is marked wrong by a
    question that never told them which one. Recognition is graded against four visible options that
    already exclude every same-gloss record, so its collision key is the whole visible STEM: the
    failure there is not an unanswerable item, it is two items in one lesson reading identically.

    The hint may only come from the record itself (a gloss of its own sense past the ones already in
    the stem, or its part of speech when that alone separates it from every colliding record),
    because inventing a clue is authoring, and this script does not author.
    """
    key = keyfn(rec)
    clash = [s for s in sorted(row["known_vocab"])
             if s != ref and (o := V.get(s)) and keyfn(o) == key]
    if not clash:
        return None, "unique"
    sense = sense_of(rec) or {}
    glosses = [str(x).strip() for x in ((sense.get("gloss") or {}).get(LOC) or []) if str(x).strip()]
    others: set[str] = set()
    for s in clash:
        os_ = sense_of(V[s]) or {}
        others |= {str(x).strip() for x in ((os_.get("gloss") or {}).get(LOC) or [])}
    for g in glosses[STEM_GLOSSES:]:          # past what the stem already shows, or it says nothing
        if g not in others:
            return f"no sentido de {g}", "own_gloss"
    mine = coarse_pos(rec)
    if mine and all(coarse_pos(V[s]) != mine for s in clash) and mine in POS_LABEL:
        return POS_LABEL[mine], "pos"
    return None, "ambiguous"


def build_production(pair: dict, row: dict, rec: dict, V: dict, kform: str
                     ) -> tuple[dict, str, str] | tuple[None, None, str]:
    ref = pair["ref"]
    gl = gloss_text(rec)
    kana = rec.get("kana")
    if not gl or '"' in gl:
        return None, None, "gloss_unusable_in_stem"
    hint, why_hint = disambiguate(row, rec, V, ref, gloss_key)
    if why_hint == "ambiguous":
        return None, None, "ambiguous_gloss_no_hint"
    stem = f'"{gl}"' + (f" ({hint})" if hint else "")
    prompt = f"Escreva em japonês a palavra que significa {stem}."
    accept = list(dict.fromkeys([x for x in (kform, kana) if x]))
    expl = f"A resposta é {display(kform, rec)}: {gl}."
    if not (prose_ok(prompt) and prose_ok(expl)):
        return None, None, "unbalanced_prose"
    ex = {"type": "production",
          "prompt": {LOC: prompt},
          "answer": {"text": kform, "accept": accept},
          "explanation": {LOC: expl},
          "sentence_refs": []}
    why = (f"production from the gloss: no distractor pool of three existed in this lesson's known "
           f"set, so the item is free production. Gloss ambiguity inside the known set: {why_hint}"
           + (f"; hint derived from the record itself ({hint})" if hint else ""))
    return ex, "production", why


def build_grammar_cloze(pair: dict, row: dict, rec: dict, by_slug: dict, by_gram: dict,
                        need: dict, probes: dict) -> tuple[dict, str, str] | tuple[None, None, str]:
    ref = pair["ref"]
    segs = sorted((s for s in (probes.get(ref) or set()) if len(s) > 1), key=lambda s: (-len(s), s))
    if not segs:
        return None, None, "no_probe_segment"
    label = ((rec.get("label") or {}).get(LOC) if isinstance(rec.get("label"), dict) else None) \
        or rec.get("key") or ref
    reason = "no_cks_clean_sentence"
    for sslug in rank_sentences(by_gram.get(ref, []), row, by_slug, need, ref):
        sent = by_slug[sslug]
        jp = sent.get("jp") or ""
        pt = ((sent.get("translation") or {}).get(LOC) or "").strip()
        if not pt:
            continue
        spans = token_spans(sent)
        if not spans:
            continue
        starts = {a for a, _b, _t in spans}
        ends = {b for _a, b, _t in spans}
        for seg in segs:
            at = jp.find(seg)
            while at >= 0:
                rest = jp[:at] + jp[at + len(seg):]
                if at in starts and at + len(seg) in ends and \
                        len(JP_LETTER_RX.findall(rest)) >= MIN_JP_LEFT:
                    blanked = jp[:at] + BLANK + jp[at + len(seg):]
                    prompt = f"Complete a frase: {blanked} ({pt})"
                    # the sentence itself is answer.full and the app reveals it; repeating it here
                    # only produced a 。 followed by a full stop
                    expl = f"O que falta é {seg}: o ponto gramatical desta lição, {label}."
                    if prose_ok(prompt) and prose_ok(expl):
                        ex = {"type": "cloze",
                              "prompt": {LOC: prompt},
                              "answer": {"text": seg, "full": jp},
                              "explanation": {LOC: expl},
                              "sentence_refs": [sslug]}
                        why = (f"grammar cloze over bank sentence {sslug}, which carries this point's "
                               f"own tag; the blanked span {seg} is a probe segment of the record's "
                               f"forms/structure_pattern and aligns to token boundaries on both sides")
                        return ex, "cloze", why
                at = jp.find(seg, at + 1)
        reason = "no_alignable_form_span"
    return None, None, reason


# --------------------------------------------------------------------------- main
def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=str(ROOT), help="exported tree to read (course/, corpus/)")
    ap.add_argument("--out-root", default=None, help="where to write the tables (default: --root)")
    ap.add_argument("--limit", type=int, default=0, help="stop after N pairs (smoke test)")
    ap.add_argument("--stats", action="store_true", help="print the per-reason breakdown")
    args = ap.parse_args()
    root = Path(args.root).resolve()
    out_root = Path(args.out_root).resolve() if args.out_root else root

    V = load_vocab_records(root)
    G = load_grammar_records(root)
    by_slug, by_vocab, by_gram, need, attested = index_bank(root)
    probes, _labels = vpc.load_grammar(root)
    credit = Credit(root)
    rows = load_lessons(root)
    by_lesson = {r["id"]: r for r in rows}

    pairs = work_list(root, rows, credit)
    if args.limit:
        pairs = pairs[:args.limit]
    print(f"work list: {len(pairs)} absent pairs over {len({p['lesson'] for p in pairs})} lessons "
          f"({sum(1 for p in pairs if p['kind'] == 'vocab')} vocab, "
          f"{sum(1 for p in pairs if p['kind'] == 'grammar')} grammar)")

    # id allocation walks the course in order so the numbering a lesson gains is contiguous
    prefix = {r["id"]: id_prefix(r["lesson"]) for r in rows}
    counter = {r["id"]: next_number(r["lesson"], prefix[r["id"]]) for r in rows}
    seen_keys: dict[str, set[tuple[str, str]]] = {
        r["id"]: {(json.dumps(e.get("prompt"), sort_keys=True, ensure_ascii=False),
                   json.dumps(e.get("answer"), sort_keys=True, ensure_ascii=False))
                  for e in (r["lesson"].get("exercises") or [])} for r in rows}
    used_distractor: collections.Counter[str] = collections.Counter()

    out_rows: list[dict] = []
    residue: list[dict] = []
    by_type: collections.Counter[str] = collections.Counter()
    by_reason: collections.Counter[str] = collections.Counter()
    per_lesson_added: collections.Counter[str] = collections.Counter()

    for pair in pairs:
        row = by_lesson[pair["lesson"]]
        attempts: list[str] = []
        ex = kind = why = None
        if pair["kind"] == "vocab":
            rec = V.get(pair["ref"])
            if rec is None:
                residue.append({**pair, "reason": "no_vocab_record", "tried": []})
                by_reason["no_vocab_record"] += 1
                continue
            kform = key_form(rec, row["known_kanji"], attested)
            if kform is None:
                residue.append({**pair, "reason": "key_form_outside_cks", "tried": []})
                by_reason["key_form_outside_cks"] += 1
                continue
            for builder in (
                    lambda: build_cloze(pair, row, rec, by_slug, by_vocab, need, kform),
                    lambda: build_recognition(pair, row, rec, V, used_distractor, attested, kform),
                    lambda: build_production(pair, row, rec, V, kform)):
                ex, kind, why = builder()
                if ex is not None:
                    break
                attempts.append(why or "?")
        else:
            rec = G.get(pair["ref"])
            if rec is None:
                residue.append({**pair, "reason": "no_grammar_record", "tried": []})
                by_reason["no_grammar_record"] += 1
                continue
            ex, kind, why = build_grammar_cloze(pair, row, rec, by_slug, by_gram, need, probes)
            if ex is None:
                attempts.append(why or "?")

        if ex is None:
            reason = attempts[-1] if attempts else "unknown"
            residue.append({**pair, "reason": reason, "tried": attempts})
            by_reason[reason] += 1
            continue

        # the gate's own predicate, on the candidate alone: an item that would not close the pair is
        # not an item, it is a decoration
        if not credit.credits(ex, pair["kind"], pair["ref"]):
            residue.append({**pair, "reason": "template_does_not_credit", "tried": attempts + [kind]})
            by_reason["template_does_not_credit"] += 1
            continue
        key = (json.dumps(ex["prompt"], sort_keys=True, ensure_ascii=False),
               json.dumps(ex["answer"], sort_keys=True, ensure_ascii=False))
        if key in seen_keys[row["id"]]:
            residue.append({**pair, "reason": "duplicate_prompt_in_lesson", "tried": attempts + [kind]})
            by_reason["duplicate_prompt_in_lesson"] += 1
            continue
        seen_keys[row["id"]].add(key)

        eid = f"{prefix[row['id']]}-{counter[row['id']]}"
        counter[row["id"]] += 1
        ex = {"id": eid, **ex}
        out_rows.append({"lesson": row["id"], "targets": [pair["ref"]], "exercise": ex, "why": why})
        by_type[kind] += 1
        per_lesson_added[row["id"]] += 1

    table = {
        "why": "Every vocab and grammar item a lesson unlocks but never practises, given ONE "
               "mechanically generated exercise inside that lesson's own cumulative_known_set. The "
               "vocab + grammar half of the W20 per-item practice campaign (APP_PLAN W20, §6 step "
               "11); the kanji half is research/derived/repairs/practice_kanji_exercises.json.",
        "definition": "One row per generated exercise: {lesson, targets, exercise, why}. `targets` "
                      "names the vocab or grammar record the exercise clears in "
                      "validate_practice_coverage; `exercise` is a complete lesson.schema.json "
                      "exercise object (id, type, prompt, answer, explanation, sentence_refs and "
                      "nothing else); `why` records which template fired and on what evidence. Every "
                      "Japanese string is a bank sentence verbatim, a token surface cut from that "
                      "sentence's Layer-A dissection, or a registry headword/kana; every pt-BR "
                      "string is a fixed template filled with a registry gloss, a grammar label or a "
                      "bank translation. Ids continue each lesson's own numbering as of the tree "
                      "this table was generated against.",
        "generated_by": "scripts/build_vocab_exercises.py (deterministic, seeded, idempotent)",
        "applied_by": "scripts/apply_practice_exercises.py --table "
                      "research/derived/pending/practice_vocab_exercises.json",
        "row_count": len(out_rows),
        "provenance": {
            "layer": "C",
            "source": "derived:w20-vocab-practice",
            "ai_generated": True,
            "needs_review": True,
            "note": "Pedagogy, spec §1.1 Layer C. Generated by template from Layer-A data rather "
                    "than authored, and still awaiting teacher sign-off: the choice of WHICH "
                    "question to ask about a word is a pedagogical claim even when every string in "
                    "it is mechanical. Stated here rather than on each exported exercise because "
                    "the `exercise` entity carries no provenance fields at all today and "
                    "validate_provenance_json rule (e)/(g) is all-or-nothing per entity; every row "
                    "the applier inserts carries needs_review = 1.",
        },
        "id_fixes": [],
        "apply_id_remap": [],
        "exemptions": {"drop": [], "keep": [],
                       "note": "This table changes no practice exemption. The three lessons in "
                               "course/practice_exemptions.json receive at most a retrieval item "
                               "(les:n4-kanji-exame-05, one vocab pair), so none of them gains the "
                               "retrieval+production pair that would make its entry stale."},
        "counts": {"by_type": dict(sorted(by_type.items())),
                   "by_level": dict(sorted(collections.Counter(
                       by_lesson[r["lesson"]]["level"] for r in out_rows).items())),
                   "lessons_touched": len({r["lesson"] for r in out_rows}),
                   "max_added_to_one_lesson": max(per_lesson_added.values(), default=0)},
        "rows": out_rows,
    }
    res = {
        "why": "The (lesson, item) pairs no template in scripts/build_vocab_exercises.py could "
               "serve, with the reason class that stopped each one. This is the authored residue of "
               "the W20 vocab + grammar half: the measured work list a human or an Opus campaign "
               "consumes, and the only part of this unit that is not mechanical.",
        "reason_classes": {
            "no_cks_clean_sentence": "no bank sentence carries this item inside the lesson's "
                                     "cumulative_known_set (usually: no bank sentence carries it at all)",
            "no_alignable_form_span": "a tagged sentence exists but no probe segment of the grammar "
                                      "record's forms/structure_pattern aligns to its token boundaries",
            "no_probe_segment": "the grammar record has no multi-character form or structure_pattern "
                                "to blank",
            "no_distractor_pool": "fewer than three known records share the target's coarse POS with "
                                  "a different gloss",
            "ambiguous_gloss_no_hint": "another record in the same known set carries the same first "
                                       "gloss and nothing in the record separates them",
            "gloss_unusable_in_stem": "the record has no pt-BR gloss usable as a prompt stem",
            "unbalanced_prose": "a filled template failed the prose contract (brackets, terminal "
                                "punctuation, em dash)",
            "duplicate_prompt_in_lesson": "the generated prompt+answer already exists in that lesson",
            "template_does_not_credit": "the generated item did not close the pair under "
                                        "validate_practice_coverage's own predicate",
            "key_form_outside_cks": "every written form of the record carries a kanji this "
                                    "lesson has not taught, or is not one Japanese run",
            "no_vocab_record": "the unlock resolves to no exported vocab record",
            "no_grammar_record": "the unlock resolves to no exported grammar record",
        },
        "generated_by": "scripts/build_vocab_exercises.py",
        "count": len(residue),
        "counts_by_reason": dict(sorted(by_reason.items())),
        "counts_by_reason_and_kind": {
            f"{k}|{r}": n for (k, r), n in sorted(collections.Counter(
                (p["kind"], p["reason"]) for p in residue).items())},
        "pairs": residue,
    }

    outdir = out_root / "research" / "derived" / "pending"
    outdir.mkdir(parents=True, exist_ok=True)
    for name, payload in (("practice_vocab_exercises.json", table),
                          ("practice_vocab_residue.json", res)):
        text = json.dumps(payload, ensure_ascii=False, indent=2) + "\n"
        path = outdir / name
        if not path.exists() or path.read_text(encoding="utf-8") != text:
            path.write_text(text, encoding="utf-8")
            print(f"  wrote {path.relative_to(out_root).as_posix()} ({len(text):,} bytes)")
        else:
            print(f"  {path.relative_to(out_root).as_posix()} unchanged (idempotent)")

    print(f"generated {len(out_rows)} exercises by type {dict(sorted(by_type.items()))}; "
          f"{len(residue)} pairs to residue by reason {dict(sorted(by_reason.items()))}")
    if args.stats:
        print(f"  lessons touched {len({r['lesson'] for r in out_rows})}, most items added to one "
              f"lesson {max(per_lesson_added.values(), default=0)}")
        top = used_distractor.most_common(20)
        print("  20 most reused distractors: " + ", ".join(f"{s}×{n}" for s, n in top))
    return 0


if __name__ == "__main__":
    sys.exit(main())
