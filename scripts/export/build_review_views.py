#!/usr/bin/env python3
"""W38 — human-readable `.md` review views, one file per (registry, level), for a named teacher.

WHY THIS EXISTS (readiness finding G9)
--------------------------------------
`validate_md_views.py` guarantees a byte-identical `.md` beside all 322 lesson JSONs. `corpus/` got
`INDEX.md` and nothing else — and every `INDEX.md` is a *listing*: one line per record, a headword
and a comma-joined gloss. A teacher asked to approve a gloss, a kanji note or a grammar explanation
had to open raw JSON, find the record by slug, and read `{"pt-BR": …}` by eye. Review throughput is
the whole M6 bottleneck, so the missing artifact is not another index — it is the text itself, in
the order a learner meets it, with everything an approval needs printed next to it.

WHAT A VIEW CONTAINS, PER RECORD
--------------------------------
    * the **stable id** (the published address; the integer `id` never appears — contracts/README.md)
    * the **Japanese with its reading** (headword + kana + romaji, kanji + on/kun, sentence + kana)
    * the **learner-facing fields in pt-BR, in full**, each with its **layer** (A/B/C) and the
      record's `needs_review`. Nothing reviewable is truncated: a view that elides the text a
      teacher is approving turns an approval into a signature on unread prose.
    * the **sentences that use it**, so a gloss is judged against the Japanese it has to serve
    * the **current ledger status** of every reviewable address (W06)
    * the **content hash** of every reviewable address, so a verdict can be written straight into a
      review sheet without a second tool (`scripts/review_apply.py`)

THE ADDRESSES A VIEW OFFERS ARE EXACTLY THE ADDRESSES THE LEDGER CAN HONOUR
--------------------------------------------------------------------------
Every hash printed here is computed by calling `review_ledger.live_anchor(record, field, locale)` —
the same function the exporter's stamp and `validate_review_ledger.py` call. A field `live_anchor`
cannot resolve is NOT offered as a review target; it is printed as context instead. That is what
stops this file from inventing an address the gate would later call *unresolvable*, which is the
one ledger state that is a hard failure (design/review_ledger.md).

ORDER
-----
Course order: module → topic → lesson → the position inside the lesson that first introduces the
record. A record no lesson introduces sorts after the ones that are taught, by id. That is the
sequence a learner meets the material in, which is the only order in which a reviewer can judge
whether an explanation assumes something not yet taught.

DETERMINISM
-----------
Byte-identical on a second run over an unchanged tree: no wall-clock date, no dict iteration
without a sort, no hash-seed-dependent set ordering. `--check` re-renders into memory and diffs
against what is on disk, which is the whole of the future suite gate (see the W38 report).

Reads:  corpus/**, course/**, contracts/manifest.json, research/derived/review_ledger.json.
        NEVER db/corpus.sqlite — the DB is the regenerable index, the export is the source of truth.
Writes: research/review/<registry>/<level>.md

Usage:
    python scripts/export/build_review_views.py                    # every registry, level n5
    python scripts/export/build_review_views.py --level all
    python scripts/export/build_review_views.py --registry vocab,kanji --level n5
    python scripts/export/build_review_views.py --check            # exit 1 if any view is stale
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any, Callable, Iterable, Iterator, Sequence

sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]

_SCRIPTS = Path(__file__).resolve().parents[1]
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))

# The anchor is computed in exactly one place (design/review_ledger.md). Importing it here is what
# makes a hash printed in a view joinable by the exporter's stamp and by the gate.
from dbtarget import take_flag  # noqa: E402
from review_ledger import (  # noqa: E402
    Entry, hashes_join, ledger_path, live_anchor, read_entries,
)
from review_queue import is_locale_object, one_line  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
OUT_REL = "research/review"

LEVELS: tuple[str, ...] = ("pre-n5", "n5", "n4", "n3", "n2", "n1")
LEVEL_LABEL: dict[str, str] = {"pre-n5": "pré-N5", "n5": "N5", "n4": "N4", "n3": "N3",
                               "n2": "N2", "n1": "N1", "speak": "Fala Primeiro"}
UNPLACED = 10**9  # course position of a record no lesson introduces

# Layer legend, printed in every view. Values are neutral English (CLAUDE.md: enums are language
# agnostic); the gloss beside them is the teacher's pt-BR.
LAYER_GLOSS: dict[str, str] = {
    "A": "fato de dataset (JMdict, KANJIDIC2, Tatoeba) — não se reescreve aqui",
    "B": "derivado e verificado por máquina contra a camada A",
    "C": "pedagogia autorada — é aqui que a revisão humana decide",
}

CJK = range(0x4E00, 0x9FFF + 1)


# ==================================================================================================
# small helpers
# ==================================================================================================
def load_json(path: Path) -> Any:
    with path.open(encoding="utf-8") as fh:
        return json.load(fh)


def code(text: object) -> str:
    return f"`{text}`"


def quote_block(text: str) -> list[str]:
    """A reviewable string, printed in full, as a markdown blockquote. Newlines inside the value
    become blockquote continuations so a multi-paragraph explanation stays one visual unit."""
    lines = str(text).replace("\r\n", "\n").split("\n")
    return [f"> {ln}" if ln.strip() else ">" for ln in lines]


def esc_cell(text: object) -> str:
    return one_line(str(text), 160).replace("|", "\\|")


def is_kanji(ch: str) -> bool:
    return ord(ch) in CJK


def needs_review_of(rec: dict[str, Any]) -> bool | None:
    """`needs_review` sits at the record root everywhere except `sentence`, which keeps it inside
    `provenance`. None means the export never carried the flag at all — vocab, kanji and family
    hold theirs only in the working index (readiness G4; W05 is what exports them)."""
    value = rec.get("needs_review")
    if value is None:
        value = (rec.get("provenance") or {}).get("needs_review")
    return value if isinstance(value, bool) else None


# ==================================================================================================
# course order — "which lesson does a learner meet this in?"
# ==================================================================================================
class CourseOrder:
    """Position of every published slug in the linear course, plus a readable label for it."""

    def __init__(self) -> None:
        self.pos: dict[str, int] = {}
        self.lesson_of: dict[str, str] = {}
        self.lesson_pos: dict[str, int] = {}
        self.lesson_title: dict[str, str] = {}
        self.also_used_by: dict[str, list[str]] = {}
        # The speak path is a SECOND ordering over the same corpus, not a place in the JLPT course,
        # so its stages get their own rank: `speak:arrival` is stage 1, not whatever sorts first
        # alphabetically (course/speak/course.json).
        self.stage_rank: dict[str, int] = {}
        self.stage_title: dict[str, str] = {}
        self.lesson_level: dict[str, str] = {}

    def _see(self, slug: object, index: int, lesson_id: str) -> None:
        if not isinstance(slug, str) or ":" not in slug:
            return
        if slug not in self.pos:
            self.pos[slug] = index
            self.lesson_of[slug] = lesson_id
        elif self.lesson_of.get(slug) != lesson_id:
            others = self.also_used_by.setdefault(slug, [])
            if lesson_id not in others:
                others.append(lesson_id)

    def position(self, slug: str | None) -> int:
        return self.pos.get(slug or "", UNPLACED)

    def where(self, slug: str) -> str:
        """`les:n5-… (Título) [+3 lições]` — the lesson that INTRODUCES it, then how many others
        put it in front of a learner. Naming only the first would hide reuse; naming all of them
        would print 84 ids beside every core N5 word."""
        first = self.lesson_of.get(slug)
        if not first:
            return "—"
        title = self.lesson_title.get(first, "")
        extra = len(self.also_used_by.get(slug, ()))
        head = f"{code(first)}" + (f" — {title}" if title else "")
        return head + (f" [+{extra} lição(ões)]" if extra else "")


def build_course_order(root: Path) -> CourseOrder:
    order = CourseOrder()
    outline_path = root / "course" / "outline.json"
    module_rank: dict[str, int] = {}
    topic_rank: dict[str, tuple[int, int]] = {}
    if outline_path.is_file():
        for module in load_json(outline_path):
            m_order = int(module.get("order") or 0)
            module_rank[module.get("level") or ""] = m_order
            for topic in module.get("topics") or ():
                topic_rank[topic.get("slug") or ""] = (m_order, int(topic.get("order") or 0))

    lessons: list[tuple[tuple[int, int, int, str], dict[str, Any]]] = []
    for path in sorted(root.glob("course/*/topic-*/lesson-*.json")):
        rec = load_json(path)
        rank = topic_rank.get(rec.get("topic") or "",
                              (module_rank.get(rec.get("level") or "", 99), 99))
        lessons.append(((rank[0], rank[1], int(rec.get("order") or 0), str(rec.get("id"))), rec))
    lessons.sort(key=lambda pair: pair[0])

    for index, (_key, rec) in enumerate(lessons):
        lesson_id = str(rec.get("id"))
        order.lesson_pos[lesson_id] = index
        order.lesson_title[lesson_id] = (rec.get("title") or {}).get("pt-BR", "")
        order.lesson_level[lesson_id] = str(rec.get("level") or "")
        order.pos.setdefault(lesson_id, index)
        order.lesson_of.setdefault(lesson_id, lesson_id)
        for unlock in rec.get("unlocks") or ():
            if isinstance(unlock, dict):
                order._see(unlock.get("ref"), index, lesson_id)
        for card in (rec.get("srs") or {}).get("introduces_cards") or ():
            if isinstance(card, dict):
                order._see(card.get("item"), index, lesson_id)
        for ref in rec.get("sentence_refs") or ():
            order._see(ref, index, lesson_id)
        for ex in rec.get("exercises") or ():
            if isinstance(ex, dict):
                for ref in ex.get("sentence_refs") or ():
                    order._see(ref, index, lesson_id)

    speak_course = root / "course" / "speak" / "course.json"
    if speak_course.is_file():
        for stage in load_json(speak_course).get("stages") or ():
            if isinstance(stage, dict) and isinstance(stage.get("slug"), str):
                order.stage_rank[stage["slug"]] = int(stage.get("order") or 0)
                order.stage_title[stage["slug"]] = (stage.get("title") or {}).get("pt-BR", "")
    return order


# ==================================================================================================
# sentence index — "which sentences would a learner see this in?"
# ==================================================================================================
class SentenceIndex:
    def __init__(self) -> None:
        self.by_slug: dict[str, dict[str, Any]] = {}
        self.uses: dict[str, list[str]] = {}

    def _add(self, key: str, slug: str) -> None:
        bucket = self.uses.setdefault(key, [])
        if slug not in bucket:
            bucket.append(slug)

    def render(self, key: str, limit: int = 4) -> list[str]:
        slugs = self.uses.get(key) or []
        out: list[str] = []
        for slug in slugs[:limit]:
            rec = self.by_slug.get(slug) or {}
            pt = (rec.get("translation") or {}).get("pt-BR", "")
            out.append(f"- {code(slug)} {rec.get('jp', '')} — {pt}")
        if len(slugs) > limit:
            out.append(f"- _(+{len(slugs) - limit} outras frases)_")
        return out or ["- _(nenhuma frase no banco usa este item)_"]


def build_sentence_index(root: Path) -> SentenceIndex:
    index = SentenceIndex()
    path = root / "corpus" / "sentences" / "bank.json"
    if not path.is_file():
        return index
    for rec in load_json(path):
        slug = rec.get("slug")
        if not isinstance(slug, str):
            continue
        index.by_slug[slug] = rec
        for link in rec.get("vocab") or ():
            if isinstance(link, dict):
                index._add(str(link.get("ref")), slug)
        for key in rec.get("grammar") or ():
            if isinstance(key, str):
                index._add(key if ":" in key else f"gram:{key}", slug)
        for ch in dict.fromkeys(str(rec.get("jp", ""))):
            if is_kanji(ch):
                index._add(f"kanji:{ch}", slug)
    return index


# ==================================================================================================
# the ledger, as a per-target verdict lookup
# ==================================================================================================
class LedgerView:
    def __init__(self, entries: Iterable[Entry]) -> None:
        self.by_slug: dict[str, list[Entry]] = {}
        self.count = 0
        for entry in entries:
            self.by_slug.setdefault(entry.slug, []).append(entry)
            self.count += 1

    def status(self, rec: dict[str, Any], slug: str, field: str, locale: str | None,
               anchor: str) -> str:
        """pt-BR verdict line for one reviewable address. `—` means nobody has ruled on it."""
        best: str | None = None
        for entry in self.by_slug.get(slug, ()):
            if entry.field not in (field, "*"):
                continue
            if entry.locale is not None and entry.locale != locale:
                continue
            entry_anchor = anchor
            if entry.field == "*" and field != "*":
                entry_anchor, _how = live_anchor(rec, "*", None)  # type: ignore[assignment]
            if entry_anchor and hashes_join(entry_anchor, entry.content_hash):
                verdict = "aprovado" if entry.status == "approved" else "rejeitado"
                note = f" — {one_line(entry.note, 90)}" if entry.note else ""
                return f"**{verdict}** por {entry.reviewed_by} em {entry.approved_at}{note}"
            best = ("desatualizado — o texto mudou depois do parecer de "
                    f"{entry.reviewed_by} ({entry.approved_at}); precisa de nova leitura")
        return best or "—"


# ==================================================================================================
# registries
# ==================================================================================================
class Registry:
    """One reviewable registry: where its records live, how to head them, and which of their fields
    are review TARGETS (an address `live_anchor` resolves) as opposed to printed context."""

    def __init__(self, name: str, entity: str, title: str, files: Sequence[str],
                 fields: Sequence[tuple[str, str]],
                 head: Callable[[dict[str, Any]], tuple[str, list[str]]],
                 context: Callable[[dict[str, Any], "Ctx"], list[str]],
                 level_of: Callable[[dict[str, Any]], str] | None = None,
                 position: Callable[[dict[str, Any], CourseOrder], int] | None = None,
                 layer_of: Callable[[dict[str, Any], str, str | None], str] | None = None,
                 packing: str = "list") -> None:
        self.name = name
        self.entity = entity
        self.title = title
        self.files = tuple(files)
        self.fields = tuple(fields)          # (field, default layer) in the order a teacher reads
        self.head = head
        self.context = context
        self.level_of = level_of or (lambda rec: str(rec.get("level") or "(sem nível)"))
        self.position = position or (lambda rec, order: order.position(address_of(rec)))
        self.layer_of = layer_of
        self.packing = packing

    def records(self, root: Path) -> Iterator[dict[str, Any]]:
        for pattern in self.files:
            for path in sorted(root.glob(pattern)):
                data = load_json(path)
                if self.packing == "single":
                    if isinstance(data, dict):
                        yield data
                elif isinstance(data, list):
                    for rec in data:
                        if isinstance(rec, dict):
                            yield rec

    def layer(self, rec: dict[str, Any], field: str, locale: str | None, default: str) -> str:
        if self.layer_of is not None:
            return self.layer_of(rec, field, locale)
        declared = rec.get("layer")
        return str(declared) if isinstance(declared, str) and declared else default


class Ctx:
    """What every context renderer needs and nothing else."""

    def __init__(self, order: CourseOrder, sentences: SentenceIndex) -> None:
        self.order = order
        self.sentences = sentences


def address_of(rec: dict[str, Any]) -> str:
    """The published address, exactly as validate_review_ledger.py resolves it."""
    for field in ("slug", "id"):
        val = rec.get(field)
        if isinstance(val, str) and ":" in val:
            return val
    return ""


# --- heads ----------------------------------------------------------------------------------------
def head_vocab(rec: dict[str, Any]) -> tuple[str, list[str]]:
    head = rec.get("headword", "")
    kana = rec.get("kana", "")
    romaji = rec.get("romaji", "")
    line = f"- **Japonês:** {head}" + (f" · leitura {kana}" if kana else "")
    line += f" · romaji *{romaji}*" if romaji else ""
    bits = [line]
    pos = sorted({p for s in rec.get("senses") or () for p in (s.get("pos") or ())})
    meta = [f"classe {', '.join(pos)}" if pos else "",
            f"registro `{rec['register']}`" if rec.get("register") else "",
            f"JMdict {rec.get('jmdict_ref')}" if rec.get("jmdict_ref") else ""]
    bits.append("- **Ficha:** " + " · ".join(m for m in meta if m))
    return head, bits


def head_kanji(rec: dict[str, Any]) -> tuple[str, list[str]]:
    char = rec.get("character", "")
    on = [r.get("reading") for r in rec.get("readings") or () if r.get("type") == "on"]
    kun = [r.get("reading") for r in rec.get("readings") or () if r.get("type") == "kun"]
    bits = [f"- **Japonês:** {char} · on {'、'.join(map(str, on)) or '—'} · "
            f"kun {'、'.join(map(str, kun)) or '—'}",
            f"- **Ficha:** {rec.get('strokes', '?')} traços · radical {rec.get('radical_char', '?')}"
            f" · frequência {rec.get('freq_rank', '—')}"]
    return char, bits


def head_grammar(rec: dict[str, Any]) -> tuple[str, list[str]]:
    label = (rec.get("label") or {}).get("pt-BR", rec.get("key", ""))
    bits = [f"- **Padrão:** {rec.get('structure_pattern', '—')}"]
    registers = rec.get("register") or []
    if registers:
        bits.append(f"- **Registro:** {', '.join(map(str, registers))}")
    return str(label), bits


def head_sentence(rec: dict[str, Any]) -> tuple[str, list[str]]:
    prov = rec.get("provenance") or {}
    bits = [f"- **Japonês:** {rec.get('jp', '')}",
            f"- **Leitura:** {rec.get('kana', '')} · romaji *{rec.get('romaji', '')}*",
            f"- **Procedência:** jp `{prov.get('jp_source', '?')}` · pt `{prov.get('pt_source', '?')}`"
            f" · gerada por IA: {'sim' if prov.get('ai_generated') else 'não'}"]
    return str(rec.get("jp", "")), bits


def head_family(rec: dict[str, Any]) -> tuple[str, list[str]]:
    label = (rec.get("label") or {}).get("pt-BR", rec.get("slug", ""))
    members = rec.get("members") or []
    bits = [f"- **Tipo:** `{rec.get('type', '?')}` · {len(members)} membro(s) · "
            f"níveis {', '.join(rec.get('spans_levels') or []) or '—'}"]
    sample = "、".join(str(m.get("ref")) for m in members[:12] if isinstance(m, dict))
    bits.append(f"- **Membros (amostra):** {sample or '—'}"
                + (f" _(+{len(members) - 12})_" if len(members) > 12 else ""))
    return str(label), bits


def head_reading(rec: dict[str, Any]) -> tuple[str, list[str]]:
    title = (rec.get("title") or {}).get("pt-BR", rec.get("slug", ""))
    bits = [f"- **Preso à lição:** {code(rec.get('gated_to_lesson', '—'))}",
            f"- **Procedência:** `{rec.get('source', '?')}` · gerado por IA: "
            f"{'sim' if rec.get('ai_generated') else 'não'}"]
    return str(title), bits


def head_exam(rec: dict[str, Any]) -> tuple[str, list[str]]:
    stem = rec.get("stem") or rec.get("prompt") or rec.get("script") or ""
    bits = [f"- **Enunciado:** {one_line(str(stem), 300)}",
            f"- **Resposta:** {rec.get('correct', '—')} · distratores: "
            f"{', '.join(map(str, rec.get('distractors') or [])) or '—'}",
            f"- **Derivado de:** `{rec.get('source', '?')}`"]
    return one_line(str(stem), 60), bits


def head_speak(rec: dict[str, Any]) -> tuple[str, list[str]]:
    title = (rec.get("title") or {}).get("pt-BR", rec.get("id", ""))
    bits = [f"- **Etapa:** {code(rec.get('stage', '—'))} · unidade {rec.get('order', '?')}"]
    return str(title), bits


def ctx_stage_line(rec: dict[str, Any], ctx: Ctx) -> str:
    stage = str(rec.get("stage") or "")
    rank = ctx.order.stage_rank.get(stage)
    title = ctx.order.stage_title.get(stage, "")
    if rank is None:
        return "—"
    return f"etapa {rank} — {title} (trilha Fala Primeiro, ordenação própria)"


# --- contexts -------------------------------------------------------------------------------------
def ctx_uses(key: str, ctx: Ctx, heading: str = "Frases que usam este item") -> list[str]:
    return [f"- **{heading}:**", *[f"  {ln}" for ln in ctx.sentences.render(key)]]


def ctx_vocab(rec: dict[str, Any], ctx: Ctx) -> list[str]:
    out: list[str] = []
    if rec.get("kanji"):
        out.append(f"- kanji do headword: {'、'.join(map(str, rec['kanji']))}")
    out.extend(ctx_uses(address_of(rec), ctx))
    return out


def ctx_kanji(rec: dict[str, Any], ctx: Ctx) -> list[str]:
    out: list[str] = []
    if rec.get("components"):
        out.append(f"- componentes: {'、'.join(map(str, rec['components']))}")
    out.extend(ctx_uses(address_of(rec), ctx))
    return out


def ctx_grammar(rec: dict[str, Any], ctx: Ctx) -> list[str]:
    out = [f"- forma **{f.get('form')}** — {(f.get('meaning') or {}).get('pt-BR', '—')}"
           for f in rec.get("forms") or () if isinstance(f, dict)]
    out.extend(ctx_uses(address_of(rec), ctx, "Frases que ilustram o ponto"))
    return out


def ctx_sentence(rec: dict[str, Any], ctx: Ctx) -> list[str]:
    """Deliberately NOT the dissection: that is a review target below and printing it twice makes
    the file half again as long for nothing. What belongs here is what the dissection does not say —
    which grammar point the sentence carries, and which lessons put it in front of a learner."""
    out: list[str] = []
    grammar = [str(g) for g in rec.get("grammar") or ()]
    out.append("- gramática: " + (", ".join(code(f"gram:{g}" if ":" not in g else g)
                                            for g in grammar) or "—"))
    out.append("- vocabulário ligado: "
               + (", ".join(code(v.get("ref")) for v in (rec.get("vocab") or ())[:10]
                            if isinstance(v, dict)) or "—")
               + (f" _(+{len(rec.get('vocab') or []) - 10})_"
                  if len(rec.get("vocab") or []) > 10 else ""))
    if rec.get("tags"):
        out.append("- tags: " + ", ".join(map(str, rec["tags"])))
    others = ctx.order.also_used_by.get(address_of(rec)) or []
    if others:
        out.append("- também usada em: " + ", ".join(code(o) for o in others[:8])
                   + (f" _(+{len(others) - 8})_" if len(others) > 8 else ""))
    return out


def ctx_family(rec: dict[str, Any], ctx: Ctx) -> list[str]:
    out: list[str] = []
    for member in (rec.get("members") or ())[:20]:
        if isinstance(member, dict):
            out.append(f"- {member.get('member_type')} {code(member.get('slug') or member.get('ref'))}"
                       f" — {member.get('ref')}"
                       + (f" · {member.get('note')}" if member.get("note") else ""))
    total = len(rec.get("members") or ())
    if total > 20:
        out.append(f"- _(+{total - 20} membros)_")
    return out


def ctx_reading(rec: dict[str, Any], ctx: Ctx) -> list[str]:
    out = [f"- {line}" for line in rec.get("sentences") or ()]
    if rec.get("source_slugs"):
        out.append("- frases de origem: " + ", ".join(code(s) for s in rec["source_slugs"][:8]))
    return out


def ctx_exam(rec: dict[str, Any], ctx: Ctx) -> list[str]:
    out: list[str] = []
    for key in ("sentence", "vocab", "kanji", "grammar", "reading_ref"):
        if rec.get(key):
            out.append(f"- {key}: {code(rec[key])}")
    sent = rec.get("sentence")
    if isinstance(sent, str):
        out.extend(ctx.sentences.render(sent) if sent in ctx.sentences.uses
                   else [f"- {code(sent)} {(ctx.sentences.by_slug.get(sent) or {}).get('jp', '')}"
                         f" — {((ctx.sentences.by_slug.get(sent) or {}).get('translation') or {}).get('pt-BR', '')}"])
    return out


def ctx_speak(rec: dict[str, Any], ctx: Ctx) -> list[str]:
    out: list[str] = []
    for slug in (rec.get("say_now") or ())[:8]:
        sentence = ctx.sentences.by_slug.get(str(slug)) or {}
        out.append(f"- {code(slug)} {sentence.get('jp', '')} — "
                   f"{(sentence.get('translation') or {}).get('pt-BR', '')}")
    for prod in rec.get("production") or ():
        if isinstance(prod, dict):
            out.append(f"- produção: {prod.get('prompt_pt')} → {prod.get('answer_key')}")
    return out


# --- layer resolution -----------------------------------------------------------------------------
def layer_vocab(rec: dict[str, Any], field: str, locale: str | None) -> str:
    if field == "notes":
        return "C"
    if field == "senses":
        return "A+B"       # en glosses are JMdict (A); pt-BR are ours (B); one aggregate address
    return "A+B"


def layer_kanji(rec: dict[str, Any], field: str, locale: str | None) -> str:
    if field in ("notes", "irregular_note"):
        return "C"
    if field == "meanings":
        return "A" if locale == "en" else "B"
    if field == "readings":
        return "A+C"       # the reading itself is KANJIDIC2 (A); the note beside it is ours (C)
    return "B"


def layer_sentence(rec: dict[str, Any], field: str, locale: str | None) -> str:
    prov = rec.get("provenance") or {}
    generated = bool(prov.get("ai_generated"))
    if field == "jp":
        return "B" if generated else "A"
    if field == "translation":
        return ("B" if generated else "A") if locale == "en" else "B"
    if field == "structure_explanation":
        return "C"
    return "B"


REGISTRIES: tuple[Registry, ...] = (
    Registry("vocab", "vocab", "Vocabulário", ("corpus/vocab/*.json",),
             (("senses", "A+B"), ("notes", "C")), head_vocab, ctx_vocab, layer_of=layer_vocab),
    Registry("kanji", "kanji", "Kanji", ("corpus/kanji/*.json",),
             (("meanings", "B"), ("readings", "A+C"), ("notes", "C"), ("irregular_note", "C")),
             head_kanji, ctx_kanji, layer_of=layer_kanji),
    Registry("grammar", "grammar", "Gramática", ("corpus/grammar/*.json",),
             (("label", "C"), ("explanation", "C"), ("formation", "C"), ("nuance", "C"),
              ("caution", "C"), ("forms", "C")),
             head_grammar, ctx_grammar, layer_of=lambda rec, f, lc: "C"),
    Registry("sentences", "sentence", "Frases", ("corpus/sentences/bank.json",),
             (("jp", "A"), ("translation", "B"), ("translation_literal", "B"),
              ("structure_explanation", "C"), ("dissection", "B")),
             head_sentence, ctx_sentence, layer_of=layer_sentence),
    Registry("families", "family", "Famílias e grupos", ("corpus/families/families.json",),
             (("label", "C"), ("description", "C"), ("governing_rule", "C")),
             head_family, ctx_family),
    Registry("readings", "reading", "Textos de leitura", ("corpus/readings/*.json",),
             (("title", "C"), ("jp", "C"), ("translation", "C")),
             head_reading, ctx_reading),
    Registry("exams", "exam_item", "Itens de exame", ("corpus/exam_banks/n[0-9]_*.json",),
             (("stem", "B"), ("explanation", "C"), ("script", "C")),
             head_exam, ctx_exam),
    Registry("speak", "speak_unit", "Trilha Fala Primeiro", ("course/speak/*/unit-*.json",),
             (("title", "C"),), head_speak, ctx_speak, packing="single",
             level_of=lambda rec: "speak"),
)
REGISTRY_BY_NAME = {r.name: r for r in REGISTRIES}


def family_level(rec: dict[str, Any]) -> str:
    spans = rec.get("spans_levels") or []
    return str(spans[0]) if spans else "(sem nível)"


def family_levels(rec: dict[str, Any]) -> list[str]:
    return [str(lv) for lv in (rec.get("spans_levels") or [])] or ["(sem nível)"]


def levels_of(registry: Registry, rec: dict[str, Any],
              order: CourseOrder | None = None) -> list[str]:
    """Which view files a record belongs in.

    Usually its own level, with two deliberate exceptions:

    * a **family** spans levels and appears in each — a teacher working N5 must see the godan class
      even though it also carries N4 and N3 members;
    * a **sentence** appears in the level of every lesson that puts it in front of a learner, not
      only in its own grade. `review_queue.in_n5_slice` already draws the N5 slice that way, and for
      the same reason: a bank sentence graded n3 that an N5 lesson displays is N5 work, and a
      teacher who never sees it cannot approve the lesson that shows it.
    """
    if registry.name == "families":
        return family_levels(rec)
    own = registry.level_of(rec)
    if registry.name == "sentences" and order is not None:
        slug = address_of(rec)
        lessons = [order.lesson_of.get(slug), *(order.also_used_by.get(slug) or ())]
        extra = {order.lesson_level.get(les or "", "") for les in lessons}
        return sorted({own, *(lv for lv in extra if lv)},
                      key=lambda lv: (LEVELS.index(lv) if lv in LEVELS else 99, lv))
    return [own]


def position_of(registry: Registry, rec: dict[str, Any], order: CourseOrder) -> int:
    if registry.name == "readings":
        return order.position(rec.get("gated_to_lesson"))
    if registry.name == "exams":
        candidates = [order.position(rec[k]) for k in
                      ("sentence", "vocab", "kanji", "grammar", "reading_ref")
                      if isinstance(rec.get(k), str)]
        return min(candidates) if candidates else UNPLACED
    if registry.name == "families":
        members = [order.position(m.get("slug")) for m in rec.get("members") or ()
                   if isinstance(m, dict) and isinstance(m.get("slug"), str)]
        return min(members) if members else UNPLACED
    if registry.name == "speak":
        return UNPLACED
    return order.position(address_of(rec))


def anchor_slug(registry: Registry, rec: dict[str, Any], order: CourseOrder) -> str:
    """Which slug answers "where does a learner meet this?".

    An exam item, a reading box and a family are never themselves unlocked by a lesson, so asking
    the course where THEY live returns nothing and the teacher loses the one piece of context that
    orders the file. Each of them borrows the address of the earliest thing it is about.
    """
    if registry.name == "readings":
        return str(rec.get("gated_to_lesson") or "")
    if registry.name == "exams":
        refs = [rec[k] for k in ("sentence", "vocab", "kanji", "grammar", "reading_ref")
                if isinstance(rec.get(k), str)]
        return min(refs, key=lambda r: (order.position(r), r)) if refs else ""
    if registry.name == "families":
        slugs = [m["slug"] for m in rec.get("members") or ()
                 if isinstance(m, dict) and isinstance(m.get("slug"), str)]
        return min(slugs, key=lambda r: (order.position(r), r)) if slugs else ""
    return address_of(rec)


def sort_key(registry: Registry, rec: dict[str, Any], order: CourseOrder) -> tuple[Any, ...]:
    if registry.name == "speak":
        stage = str(rec.get("stage") or "")
        return (order.stage_rank.get(stage, 99), stage, int(rec.get("order") or 0),
                address_of(rec))
    return (position_of(registry, rec, order), address_of(rec))


# ==================================================================================================
# rendering one record
# ==================================================================================================
def targets_of(registry: Registry, rec: dict[str, Any]) -> list[tuple[str, str | None, str, Any]]:
    """Every reviewable address on this record, as (field, locale, anchor, value).

    A candidate field is offered ONLY when `review_ledger.live_anchor` resolves it. Anything else is
    context: printing a hash the gate cannot recompute would manufacture an unresolvable approval.
    """
    out: list[tuple[str, str | None, str, Any]] = []
    for field, _default in registry.fields:
        value = rec.get(field)
        if field == "dissection":
            for locale in ("pt-BR", "en"):
                anchor, _how = live_anchor(rec, field, locale)
                if anchor:
                    out.append((field, locale, anchor, None))
            continue
        if is_locale_object(value):
            for locale in sorted(value):
                anchor, _how = live_anchor(rec, field, locale)
                if anchor:
                    out.append((field, locale, anchor, value[locale]))
            continue
        anchor, _how = live_anchor(rec, field, None)
        if anchor:
            out.append((field, None, anchor, value))
    record_anchor, _how = live_anchor(rec, "*", None)
    if record_anchor:
        out.append(("*", None, record_anchor, None))
    return out


def render_senses(senses: Any) -> list[str]:
    """The vocab `senses` aggregate as a table. Every key the anchor hashes has a column, so the
    table and `sha_json(senses)` describe the same object — a prettier rendering, never a smaller
    one. (An approval here covers ALL senses of the word at once: `senses` is the finest address
    `live_anchor` resolves today. The W38 report records what a per-sense address would cost.)"""
    rows = ["| # | pt-BR | en | classe | registro | `needs_review` |", "|--:|---|---|---|---|---|"]
    for sense in senses or ():
        gloss = sense.get("gloss") or {}
        rows.append(
            f"| {sense.get('order')} | **{esc_cell(', '.join(gloss.get('pt-BR') or []) or '—')}** "
            f"| {esc_cell(', '.join(gloss.get('en') or []) or '—')} "
            f"| {esc_cell(', '.join(sense.get('pos') or []) or '—')} "
            f"| {esc_cell(sense.get('register') or '—')} "
            f"| {'sim' if sense.get('needs_review') else 'não'} |")
        for extra in ("misc", "field"):
            if sense.get(extra):
                rows.append(f"| | _{extra}:_ {esc_cell(', '.join(sense[extra]))} | | | | |")
    return rows


def render_readings(readings: Any) -> list[str]:
    """The kanji `readings` aggregate as a table: the reading is KANJIDIC2 (layer A) and the note
    beside it is ours (layer C), and they share one anchor because they share one field."""
    rows = ["| leitura | tipo | comum | nota (pt-BR) | exemplos | `needs_review` |",
            "|---|---|---|---|---|---|"]
    for reading in readings or ():
        note = (reading.get("note") or {}).get("pt-BR", "")
        rows.append(
            f"| {esc_cell(reading.get('reading'))} | {esc_cell(reading.get('type'))} "
            f"| {'sim' if reading.get('common') else 'não'} | {esc_cell(note or '—')} "
            f"| {esc_cell(', '.join(reading.get('example_vocab') or []) or '—')} "
            f"| {'sim' if reading.get('needs_review') else 'não'} |")
    return rows


STRUCT_RENDERERS: dict[tuple[str, str], Callable[[Any], list[str]]] = {
    ("vocab", "senses"): render_senses,
    ("kanji", "readings"): render_readings,
}


def render_value(field: str, locale: str | None, value: Any, rec: dict[str, Any],
                 registry_name: str = "") -> list[str]:
    """The reviewable value, in full. Prose is quoted verbatim; a structured value is printed as the
    canonical JSON its hash is taken over, so what the teacher reads is what the anchor covers."""
    if field == "*":
        return ["> _(o registro inteiro, como impresso acima)_"]
    renderer = STRUCT_RENDERERS.get((registry_name, field))
    if renderer is not None and value is not None:
        return renderer(value)
    if field == "dissection":
        rows = ["| token | leitura | glosa | papel |", "|---|---|---|---|"]
        for tok in rec.get("tokens") or ():
            gloss = (tok.get("gloss") or {}).get(locale or "pt-BR")
            role = (tok.get("role") or {}).get(locale or "pt-BR")
            if gloss or role:
                rows.append(f"| {esc_cell(tok.get('surface'))} | {esc_cell(tok.get('reading'))} "
                            f"| {esc_cell(gloss or '—')} | {esc_cell(role or '—')} |")
        for par in rec.get("particles") or ():
            expl = (par.get("explanation") or {}).get(locale or "pt-BR")
            if expl:
                rows.append(f"| {esc_cell(par.get('particle'))} | _(partícula)_ | "
                            f"{esc_cell(expl)} | {esc_cell((par.get('function') or {}).get(locale or 'pt-BR', '—'))} |")
        return rows if len(rows) > 2 else ["> _(sem dissecação neste idioma)_"]
    if isinstance(value, str):
        return quote_block(value)
    return ["```json", json.dumps(value, ensure_ascii=False, indent=1, sort_keys=True), "```"]


def render_record(index: int, registry: Registry, rec: dict[str, Any], ctx: Ctx,
                  ledger: LedgerView) -> list[str]:
    slug = address_of(rec)
    label, head_bits = registry.head(rec)
    out: list[str] = [f"## {index}. {code(slug)} — {label}", ""]
    out.extend(head_bits)
    anchor = anchor_slug(registry, rec, ctx.order)
    where = ctx_stage_line(rec, ctx) if registry.name == "speak" else ctx.order.where(anchor)
    if anchor and anchor != slug and where != "—" and not anchor.startswith("les:"):
        where += f" _(via {code(anchor)})_"
    out.append(f"- **Onde entra no curso:** {where}")
    needs = needs_review_of(rec)
    if needs is None:
        needs_txt = "não declarado no export (a marca vive só no índice SQLite — W05)"
    else:
        needs_txt = "sim" if needs else "não"
    out.append(f"- **Precisa de revisão (`needs_review`):** {needs_txt}")
    out.append("")

    context = registry.context(rec, ctx)
    if context:
        out.append("<details><summary>Contexto (não é alvo de parecer)</summary>")
        out.append("")
        out.extend(context)
        out.append("")
        out.append("</details>")
        out.append("")

    for field, locale, anchor, value in targets_of(registry, rec):
        layer = registry.layer(rec, field, locale, dict(registry.fields).get(field, "C"))
        addr = field if locale is None else f"{field}@{locale}"
        out.append(f"### `{addr}` · camada {layer} · hash `{anchor[:16]}`")
        out.append("")
        out.append(f"_Ledger:_ {ledger.status(rec, slug, field, locale, anchor)}")
        out.append("")
        out.extend(render_value(field, locale, value, rec, registry.name))
        out.append("")
    return out


# ==================================================================================================
# rendering one view file
# ==================================================================================================
def render_view(registry: Registry, level: str, records: list[dict[str, Any]], ctx: Ctx,
                ledger: LedgerView, build: dict[str, Any]) -> str:
    lines: list[str] = []
    lvl = LEVEL_LABEL.get(level, level)
    lines.append(f"# Revisão — {registry.title} · {lvl}")
    lines.append("")
    lines.append(f"_Gerado por `scripts/export/build_review_views.py` a partir do export "
                 f"(`corpus/` + `course/`), entidade `{registry.entity}`. **Não edite este arquivo** "
                 f"— ele é regerado e conferido byte a byte. Para registrar um parecer, preencha "
                 f"uma ficha: `research/review/README.md`._")
    lines.append("")
    if build:
        lines.append(f"_Build `{build.get('git_head', '?')[:12]}` de {build.get('date', '?')} "
                     f"(`contracts/manifest.json`)._")
        lines.append("")

    n_targets = sum(len(targets_of(registry, rec)) for rec in records)
    flagged = sum(1 for rec in records if needs_review_of(rec))
    lines.append(f"**{len(records)} registro(s) · {n_targets} endereço(s) de parecer · "
                 f"{flagged} marcado(s) `needs_review` no export.**")
    lines.append("")
    lines.append("Ordem: a mesma em que o aluno encontra o material no curso (módulo → tópico → "
                 "lição). Registros que nenhuma lição apresenta vêm depois, por id.")
    lines.append("")
    if registry.name == "sentences":
        lines.append("Este arquivo traz as frases **classificadas** neste nível e também as de "
                     "outro nível que uma lição deste nível mostra ao aluno — quem revisa a lição "
                     "precisa ver o que ela exibe.")
    elif registry.name == "families":
        lines.append("Uma família aparece no arquivo de cada nível que ela atravessa.")
    lines.append("")
    lines.append("**Camadas:** " + " · ".join(f"**{k}** = {v}" for k, v in
                                              sorted(LAYER_GLOSS.items())) + ".")
    lines.append("")
    lines.append("Cada bloco `### campo@idioma` é um **endereço de parecer**: o `hash` ao lado dele "
                 "é o conteúdo exato que você está lendo. Copie id, campo e hash para a ficha; se o "
                 "texto mudar depois, o hash muda e o parecer antigo aparece como _desatualizado_.")
    lines.append("")
    lines.append("---")
    lines.append("")

    for i, rec in enumerate(records, start=1):
        lines.extend(render_record(i, registry, rec, ctx, ledger))
        lines.append("---")
        lines.append("")

    if not records:
        lines.append("_Nenhum registro deste nível nesta entidade._")
        lines.append("")
    return "\n".join(lines).rstrip("\n") + "\n"


# ==================================================================================================
# main
# ==================================================================================================
def build_all(root: Path, registries: Sequence[Registry], levels: Sequence[str],
              ledger_file: Path | None = None) -> dict[str, str]:
    order = build_course_order(root)
    sentences = build_sentence_index(root)
    ctx = Ctx(order, sentences)

    entries, _errors = read_entries(ledger_file or ledger_path(root))
    ledger = LedgerView(entries)

    build: dict[str, Any] = {}
    manifest = root / "contracts" / "manifest.json"
    if manifest.is_file():
        build = (load_json(manifest).get("build") or {})

    views: dict[str, str] = {}
    for registry in registries:
        buckets: dict[str, list[dict[str, Any]]] = {}
        for rec in registry.records(root):
            for level in levels_of(registry, rec, order):
                buckets.setdefault(level, []).append(rec)
        for level in levels:
            if level not in buckets:
                continue  # a registry writes a file only for the levels it actually holds
            records = sorted(buckets.get(level, []), key=lambda r: sort_key(registry, r, order))
            views[f"{registry.name}/{level}.md"] = render_view(
                registry, level, records, ctx, ledger, build)
    return views


def resolve_levels(raw: str, registries: Sequence[Registry]) -> list[str]:
    if raw == "all":
        levels = list(LEVELS)
    else:
        levels = [tok.strip() for tok in raw.split(",") if tok.strip()]
    if any(r.name == "speak" for r in registries) and "speak" not in levels:
        levels.append("speak")
    return levels


def main(argv: Sequence[str] | None = None) -> int:
    # Consumed BEFORE argparse (scripts/dbtarget.take_flag), the way validate_review_ledger.py does
    # it, so a proof can point this generator and the gate at the same ledger copy. The default
    # never moves: no flag, no env, and it is <root>/research/derived/review_ledger.json.
    ledger_override = take_flag("--review-ledger") or os.environ.get("YOMINEKO_REVIEW_LEDGER")
    parser = argparse.ArgumentParser(description=(__doc__ or "").splitlines()[0])
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--out", type=Path, default=None,
                        help=f"where the views land (default: <root>/{OUT_REL})")
    parser.add_argument("--level", default="n5",
                        help="comma-separated levels, or `all` (default: n5)")
    parser.add_argument("--registry", default="all",
                        help="comma-separated registry names, or `all` "
                             f"({', '.join(r.name for r in REGISTRIES)})")
    parser.add_argument("--check", action="store_true",
                        help="re-render and diff against disk; exit 1 on any drift")
    args = parser.parse_args(argv)

    root: Path = args.root
    out_dir: Path = args.out or (root / OUT_REL)

    if args.registry == "all":
        registries = list(REGISTRIES)
    else:
        names = [tok.strip() for tok in args.registry.split(",") if tok.strip()]
        unknown = [n for n in names if n not in REGISTRY_BY_NAME]
        if unknown:
            print(f"unknown registry: {', '.join(unknown)}", file=sys.stderr)
            return 2
        registries = [REGISTRY_BY_NAME[n] for n in names]

    levels = resolve_levels(args.level, registries)
    views = build_all(root, registries, levels,
                      Path(ledger_override) if ledger_override else None)

    if args.check:
        drift: list[str] = []
        for rel, text in sorted(views.items()):
            path = out_dir / rel
            if not path.is_file():
                drift.append(f"{OUT_REL}/{rel} is missing")
            elif path.read_text(encoding="utf-8") != text:
                drift.append(f"{OUT_REL}/{rel} differs from a fresh render")
        for line in drift:
            print(f"FAIL: {line}")
        print(f"build_review_views --check: {len(views)} view(s), {len(drift)} stale")
        return 1 if drift else 0

    written = 0
    for rel, text in sorted(views.items()):
        path = out_dir / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        if path.is_file() and path.read_text(encoding="utf-8") == text:
            continue
        path.write_text(text, encoding="utf-8", newline="\n")
        written += 1
    total = sum(len(t.encode("utf-8")) for t in views.values())
    print(f"review views: {len(views)} file(s) under {OUT_REL}/ "
          f"({written} rewritten, {total / 1024:.0f} KiB total)")
    for rel in sorted(views):
        print(f"  {OUT_REL}/{rel}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
