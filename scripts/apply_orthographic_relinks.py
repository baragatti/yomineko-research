#!/usr/bin/env python3
"""W12 — link bank sentences to the vocabulary records they already contain under another spelling.

WHY THIS EXISTS
---------------
`research/reports/readiness/content_coverage_levels.md` §2.4 measured that 788 of the 1,545
zero-coverage vocabulary records DO occur in the sentence bank and were simply never linked to — an
orthography/tokenisation miss, not missing content. The offenders it named are counters (一つ, 二つ,
５日), okurigana and kana/kanji twins (詰らない/つまらない, 許り/ばかり, 其れに/それに) and function
words the dissector's per-token linker never had a chance at, because Sudachi cuts them into two
morphemes (一+つ, それ+に, お+茶) and `token.vocab_id` is a per-token column.

THE MATCH IS BY LEMMA **AND** READING, NEVER BY SUBSTRING
---------------------------------------------------------
The audit's 788 was measured with a substring test, and a substring test is fiction at this scale:
区/く "occurs" in 1,783 bank sentences because く ends every adverbial adjective, 家/け in 754, 中/ちゅう
in 157. That is the tiling problem `validate_practice_coverage.py` had to solve and the reason
`validate_sentence_coverage.py` refuses to guess. So every rule here is anchored on Sudachi's own
token boundaries and must agree on BOTH the written form and the reading:

  kana-exact          one token: its lemma (or surface) is a registered form of the record — headword,
                      kana, `vocab_form`, or a JMdict kanji/kana element of `vocab:<ent_seq>` — and its
                      realized reading is a registered kana form. 程/ほど, 丈/だけ, 個/こ, 枚/まい.
  kana-function-word  as above, but JMdict files the word as a noun/adverb while Sudachi tags the token
                      a particle (程 is ["n","adv"]). Allowed only when the JMdict entry carries `uk`
                      (usually written in kana) and the kana form is two morae or more. That flag is
                      what keeps 科/可/課 — all read か, none of them `uk` — out of the question
                      particle か, which is what an unguarded POS map does.
  inflected-stem      one inflecting token whose lemma is a registered form and whose REALIZED reading
                      agrees with a registered kana reading up to the final mora (ぶた→打つ/ぶつ,
                      よし→止す/よす). This is the rule that separates 行った read いっ (行く) from
                      行なった read おこなっ (行う): Sudachi lemmatises both as 行う, and only the reading
                      tells them apart. Same discriminator W11 settled the homographs with.
  run-reading         a run of 2..5 CONTIGUOUS C tokens whose concatenated surface is a registered form
                      and whose concatenated reading is a registered kana reading. This is the counter
                      and compound case: 一+つ = 一つ/ひとつ, ５+日 = ５日/いつか, お+茶 = お茶/おちゃ,
                      それ+に = 其れに/それに.
  run-kana-surface    as run-reading, but the run is written in kana and it is the SPELLING that matches
                      the kana form — は realizes as わ, so 「では」 reads でわ and only the spelling can
                      carry the identity.

FOUR GUARDS, EACH ONE PAID FOR BY A FALSE POSITIVE IT CAUGHT
-------------------------------------------------------------
  unique candidate    a token is linked only when exactly ONE record in the whole registry matches it.
                      位/くらい names two JMdict entries at two levels and あたり names 辺り and 当たり;
                      nothing here can pick between them and preferring the under-covered one would be
                      a bias, not evidence. 21 tokens and 78 runs are dropped for this.
  kana is the normal
  spelling            a kana spelling standing in for a kanji headword is only that word when JMdict
                      says so — the `uk` misc flag, or an entry whose every kanji element is marked
                      rare/search-only/outdated/irregular (其れから is `sK`, 如何して is `rK`). Without
                      it the run い+た (いる + た) reads as 板/いた and 64 progressive-past clauses
                      become "board"; 板 has a plain kanji element and neither signal. 12 runs are
                      dropped here.
  no all-function
  runs                a run of nothing but particles and auxiliaries is an adjacency, not a word.
                      Sudachi already decided で+も, で+は, だ+から are two morphemes; the merged
                      spelling coinciding with a conjunction entry is a coincidence in 47 of 49
                      でも cases (小さな子どもでも…, いつでも…). 3,893 runs are dropped for this, and
                      the honest consequence is that でも, では and だから stay short: the bank holds
                      no token of the CONJUNCTION.
  no run starts on
  a particle          a word does not begin with a case particle or an auxiliary. と+お in
                      「コーヒーとお茶と…」 otherwise reads as 十/とお and claims the span お茶 needed.
  no productive
  kana verb runs      a kana run containing an inflected verb is where a productive reading competes
                      with a lexicalised one — 嘘をついて is つく+て, not について; そうして is そう+する+て,
                      not the conjunction. Only a record JMdict files as an inflectable content word
                      (adj-i / adj-na / v*) survives: つまらない does, 就いて (exp) and 然うして (conj)
                      do not. 56 runs are dropped.

WHERE THE LINK IS WRITTEN
-------------------------
Both places `scripts/ingest/persist_dissection.py` writes them, so the link survives a rebuild:

  token.vocab_id     on the run's ANCHOR — the first token of the verified span that carries no vocab
                     yet, chosen against the tree in hand rather than pinned in the row (the same span
                     anchors on 県 here and on 下 in a manifest replay). A token already linked is
                     never re-pointed: re-pointing is a migration (`scripts/migrate_vocab_repoint.py`)
                     and W11 had just finished settling which sibling each ambiguous reference means.
                     15 runs whose every token was already taken (１０日 is １０→一〇 plus 日→日) are
                     dropped at derivation, and a row that finds no free anchor in some other tree is
                     reported and skipped, not forced.
  sentence_vocab     `INSERT OR IGNORE`, with the provenance columns
                     `scripts/ingest/build_sentence_vocab.py` added: `link_rule='ortho'` and a
                     `reading_verified` computed per row exactly as that script computes it.

It deliberately does NOT call `persist_dissection.recompute_all_levels()`. That function derives
`sentence.level` from `sentence_vocab` ∪ `sentence_kanji`, and re-deriving sentence levels is a
separate reviewed decision with its own export diff — never a side effect of repairing a link. The
same prohibition is written at the top of `build_sentence_vocab.py`.

FIFTH GUARD (W13 apply): NO BARE ONE-KANA FUNCTION WORD
-------------------------------------------------------
  bare function
  word            a SINGLE token Sudachi tags a particle or an auxiliary is claimed only when the
                  kana form it matches on is two kana or more. This is the same measure the
                  `kana-function-word` rule already applies to a POS-mismatched link, extended to
                  the single-token `kana-exact` rule, and it is what separates the two cases that
                  look alike:

                    だけ, ばかり, など, ほど — words a learner meets AS words, 2-4 kana, 88 links in
                                              the applied N5/N4 table and every one of them wanted;
                    で                      — one kana, the plain case particle, `vocab:2028980`,
                                              which the course files at N3.

                  Without it the N3 pass links EVERY で token in the bank (780 of them) to that
                  record, and a bank sentence an N5 lesson renders then carries an N3 vocabulary
                  reference: 33 more lesson<->sentence pairs over the frozen i+1 budget in
                  `research/reports/lesson_sentence_baseline.json`. A one-kana particle spelled で is
                  not an ORTHOGRAPHIC variant of anything -- it is spelled exactly as the record is,
                  and the reason the dissector never linked it is that its per-token linker
                  deliberately leaves case particles alone. Re-linking it is not this campaign's
                  repair; it is a decision about whether particle occurrences count towards a
                  vocabulary floor at all, which belongs to whoever sets the floor.

SCOPE: N5 AND N4 (default), N3 UNDER --scope
--------------------------------------------
The default scope is the taught records at n5/n4 that sit under the >=3 sentence floor: 663 links over
63 records, 57 of which cross the floor. `--scope n3 --table <path>` runs the SAME rules over the N3
records, writing a second table, and that half was deliberately deferred by W12 to the W13 apply --
both because the N3 pass must run AFTER the 4,223 mined N3 sentences are in the bank (it reads the
current coverage to decide which records are short) and because W12 measured it linking every で to
`vocab:2028980`, which the fifth guard above now refuses.

Two tables rather than one because the REPLAY order needs them apart: the N5/N4 table applies before
the W13 ingest (manifest step 114) and the N3 table cannot, since none of its sentences exist yet.

THE HOLD LIST
-------------
`held[]` in the table carries rows the derivation produced and this campaign deliberately does NOT
apply, each with its reason. It exists because a link is not free: a bank sentence that gains a
vocabulary edge gains it for every lesson that RENDERS that sentence, and a lesson may only introduce
so many unknown items above what it has taught (`validate_lesson_gating.py` check D, budgets 0/1/2/2
by level, ceiling frozen in `research/reports/lesson_sentence_baseline.json`). Eleven N3 links pushed
eleven lesson<->sentence pairs over that ceiling; they are held rather than applied, because raising
the ceiling to make a mechanical relink fit would spend a curriculum guarantee on a link nobody asked
for. They are not lost — they are listed, with the pair they would break, for the W14 lesson-sentence
re-selection, which is the unit that decides which sentence a lesson shows.

A hold is addressed by (sentence slug, vocab slug) and SURVIVES `--derive`: the flag re-reads the
current table's `held[]` before it un-applies anything, so re-deriving cannot quietly re-admit a link
a human held. Only `rows[]` is applied and only `rows[]` is what `validate_repairs_applied.py`
asserts; `held[]` is documentation with an address.

Idempotent: every write is `UPDATE … WHERE vocab_id IS NULL` or `INSERT OR IGNORE`, so a second run
reports 0 changes. Run the exporters afterwards.

Usage: apply_orthographic_relinks.py [--derive] [--check] [--db PATH] [--out-root PATH]
                                    [--scope n5,n4|n3] [--table PATH]
       --derive  re-derives the table from the index and rewrites it (the rule, re-runnable)
       --check   verify only, write nothing
       --scope   which record levels the derivation targets (default n5,n4)
       --table   which tracked table to derive/apply (default research/derived/repairs/
                 orthographic_relinks.json; the N3 half lives in orthographic_relinks_n3.json)
"""
from __future__ import annotations

import argparse
import json
import sqlite3
import sys
from collections import defaultdict
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
# W01: honour --db / $YOMINEKO_DB so a rebuild can target a scratch DB (scripts/dbtarget.py).
import sys as _sys, pathlib as _pl  # noqa: E402
_sys.path.append(str(next(p for p in _pl.Path(__file__).resolve().parents if p.name == "scripts")))
from dbtarget import db_target, out_root  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
DB = db_target(ROOT / "db" / "corpus.sqlite")
OUT = out_root(ROOT)
TABLE = ROOT / "research" / "derived" / "repairs" / "orthographic_relinks.json"
TABLE_N3 = ROOT / "research" / "derived" / "repairs" / "orthographic_relinks_n3.json"

FLOOR = 3
MAXW = 5                                   # longest span in tokens; relink_vocab.py's window
SCOPE_LEVELS = ("n5", "n4")
FUNCTION_POS = {"particle", "auxiliary"}
SKIP_POS = {"punctuation", "whitespace", None}
INFLECTING = {"verb", "i-adjective", "auxiliary", "na-adjective"}
UK_POS_RELAX = {"particle", "suffix", "auxiliary", "adverb", "conjunction"}
LINK_RULE = "ortho"

# Sudachi's coarse POS -> the JMdict part-of-speech tags that may name the same word. A veto only:
# an unknown token POS vetoes nothing, and a record with no sense POS recorded vetoes nothing.
TOK2JM = {
    "verb": {"v1", "v1-s", "v5u", "v5k", "v5g", "v5s", "v5t", "v5n", "v5b", "v5m", "v5r", "v5r-i",
             "v5aru", "v5k-s", "v5u-s", "vk", "vs", "vs-s", "vs-i", "vz", "vn", "vr", "vi", "vt",
             "aux-v", "exp"},
    "i-adjective": {"adj-i", "adj-ix", "aux-adj", "exp"},
    "na-adjective": {"adj-na", "adj-no", "adj-t", "adj-f", "n", "exp"},
    "noun": {"n", "n-suf", "n-pref", "n-t", "ctr", "num", "pn", "adj-no", "adj-na", "adj-t", "vs",
             "exp", "adv", "adv-to", "unc"},
    "pronoun": {"pn", "n", "exp", "adj-no"},
    "adverb": {"adv", "adv-to", "n", "exp", "adj-no", "adj-na", "conj"},
    "particle": {"prt", "exp", "conj", "aux", "cop"},
    "conjunction": {"conj", "exp", "adv", "adv-to", "prt", "n"},
    "adnominal": {"adj-pn", "exp", "adj-no"},
    "interjection": {"int", "exp", "n"},
    "prefix": {"pref", "n-pref", "exp"},
    "suffix": {"suf", "n-suf", "ctr", "exp"},
    "auxiliary": {"aux", "aux-v", "aux-adj", "cop", "prt", "exp", "adj-i"},
}
INFLECTABLE_JM = ("adj-i", "adj-ix", "adj-na")

KATA_A, KATA_Z = 0x30A1, 0x30F6


def hira(s: str) -> str:
    """Katakana -> hiragana. `token.reading` is stored in hiragana; `vocab.kana` keeps katakana for
    loanwords, so the two are only comparable after normalisation (build_sentence_vocab.py's rule)."""
    if not s:
        return ""
    return "".join(chr(ord(c) - 0x60) if KATA_A <= ord(c) <= KATA_Z else c for c in s)


def kana_only(s: str) -> bool:
    return bool(s) and all("ぁ" <= c <= "ゟ" or "ァ" <= c <= "ヿ" or c == "ー"
                           for c in s)


# ---------------------------------------------------------------------------------------------
# The registry side: every written form a record owns, and every kana reading it owns.
# ---------------------------------------------------------------------------------------------
class Registry:
    def __init__(self, con: sqlite3.Connection) -> None:
        self.rec: dict[int, dict] = {}
        self.surfaces: dict[int, set[str]] = defaultdict(set)
        self.readings: dict[int, set[str]] = defaultdict(set)
        self.pos: dict[int, set[str]] = defaultdict(set)
        ent2vid: dict[int, list[int]] = defaultdict(list)
        for vid, slug, hw, kana, lvl in con.execute(
                "SELECT id,slug,headword,kana,level FROM vocab"):
            self.rec[vid] = {"id": vid, "slug": slug, "headword": hw, "kana": kana, "level": lvl}
            if hw:
                self.surfaces[vid].add(hw)
                if kana_only(hw):
                    self.readings[vid].add(hira(hw))
            if kana:
                self.surfaces[vid].add(kana)
                self.readings[vid].add(hira(kana))
            try:
                ent2vid[int(str(slug).split(":", 1)[1])].append(vid)
            except (ValueError, IndexError):
                pass
        for vid, form, is_kana in con.execute("SELECT vocab_id,form,is_kana FROM vocab_form"):
            if vid in self.rec and form:
                self.surfaces[vid].add(form)
                if is_kana or kana_only(form):
                    self.readings[vid].add(hira(form))
        # JMdict's own kanji/kana element lists for vocab:<ent_seq> — the Layer-A form inventory the
        # registry columns only summarise (許り also spells 許, １０日 also spells 十日 and 一〇日).
        for ent, form, is_kana in con.execute("SELECT ent_seq,form,is_kana FROM raw_jmdict_form"):
            for vid in ent2vid.get(ent, ()):
                if form:
                    self.surfaces[vid].add(form)
                    if is_kana or kana_only(form):
                        self.readings[vid].add(hira(form))
        for vid, pj in con.execute("SELECT vocab_id,pos FROM vocab_sense"):
            if vid in self.rec and pj:
                try:
                    for tag in json.loads(pj):
                        self.pos[vid].add(tag)
                except (ValueError, TypeError):
                    pass
        # "usually written in kana" lives only in the raw JMdict payload; vocab_sense.misc_tags was
        # ingested empty. It is Layer A and it is the guard the kana rules rest on. TWO signals, both
        # from JMdict itself: the `uk` misc flag (程/ほど, 丈/だけ), and — for the ateji class JMdict
        # does not bother flagging — an entry whose EVERY kanji element is marked rare, search-only,
        # outdated or irregular (其れから is `sK`, 其れでは is `sK`, 如何して is `rK`). Both mean the
        # kana IS the normal spelling. 板/いた has a plain kanji element and neither signal, which is
        # exactly why い+た does not become "board".
        RARE_KANJI = {"rK", "sK", "oK", "iK"}
        self.uk: set[int] = set()
        for ent, data in con.execute("SELECT ent_seq,data FROM raw_jmdict_entry"):
            if not data or ent not in ent2vid:
                continue
            try:
                doc = json.loads(data)
            except ValueError:
                continue
            kanji = doc.get("kanji") or []
            kana_normal = (
                any("uk" in (s.get("misc") or []) for s in doc.get("sense") or [])
                or (bool(kanji) and all(set(k.get("tags") or []) & RARE_KANJI for k in kanji)))
            if kana_normal:
                self.uk.update(ent2vid.get(ent, ()))
        self.by_surface: dict[str, set[int]] = defaultdict(set)
        for vid, forms in self.surfaces.items():
            for f in forms:
                self.by_surface[f].add(vid)
        self.by_slug = {r["slug"]: vid for vid, r in self.rec.items()}

    def pos_ok(self, tok_pos: str | None, vid: int) -> bool:
        allowed = TOK2JM.get(tok_pos or "")
        if allowed is None:
            return True
        cls = self.pos.get(vid)
        return True if not cls else bool(cls & allowed)

    def inflectable_content_word(self, vid: int) -> bool:
        return any(c.startswith("v") or c in INFLECTABLE_JM for c in self.pos.get(vid, ()))


def taught_below_floor(con: sqlite3.Connection, reg: Registry, root: Path,
                       scope: tuple[str, ...] = SCOPE_LEVELS) -> dict[int, int]:
    """vocab row id -> its current sentence count, for taught n5/n4 records under the floor.

    TAUGHT is read from the exported course leaves, the same published slug space
    validate_sentence_coverage.py measures; COUNTED is `token.vocab_id`, the link that survives the
    export as `tokens[].vocab` and the only thing that gate counts.
    """
    cover: dict[int, set[int]] = defaultdict(set)
    for sid, vid in con.execute("SELECT sentence_id,vocab_id FROM token WHERE vocab_id IS NOT NULL"):
        cover[vid].add(sid)
    out: dict[int, int] = {}
    for path in sorted(root.glob("course/**/lesson-*.json")):
        lesson = json.loads(path.read_text(encoding="utf-8"))
        for u in lesson.get("unlocks") or []:
            if u.get("type") != "vocab":
                continue
            vid = reg.by_slug.get(u.get("ref"))
            if vid is None or reg.rec[vid]["level"] not in scope:
                continue
            if len(cover[vid]) < FLOOR:
                out[vid] = len(cover[vid])
    return out


# ---------------------------------------------------------------------------------------------
def derive(con: sqlite3.Connection, root: Path,
           scope: tuple[str, ...] = SCOPE_LEVELS) -> tuple[list[dict], dict[str, int]]:
    reg = Registry(con)
    targets = taught_below_floor(con, reg, root, scope)
    tokens: dict[int, list[dict]] = defaultdict(list)
    for tid, sid, pos_i, surf, lemma, reading, tpos, vid in con.execute(
            "SELECT id,sentence_id,position,surface,lemma,reading,pos,vocab_id FROM token "
            "WHERE split_mode='C' ORDER BY sentence_id, position"):
        tokens[sid].append({"id": tid, "position": pos_i, "surface": surf, "lemma": lemma,
                            "reading": reading, "pos": tpos, "vocab_id": vid})
    slug_of = {sid: slug for sid, slug in con.execute("SELECT id,slug FROM sentence")}
    stats: dict[str, int] = defaultdict(int)
    rows: list[dict] = []

    def emit(sid, span, vid, rule):
        r = reg.rec[vid]
        anchor = next(t for t in span if t["vocab_id"] is None)
        rows.append({
            "sentence": slug_of[sid],
            "anchor_position": anchor["position"],
            "span": [t["position"] for t in span],
            "span_surfaces": [t["surface"] for t in span],
            "surface": "".join(t["surface"] or "" for t in span),
            "lemma": "+".join(t["lemma"] or "" for t in span),
            "reading": "".join(t["reading"] or "" for t in span),
            "pos": "+".join(t["pos"] or "" for t in span),
            "vocab": r["slug"], "headword": r["headword"], "kana": r["kana"], "level": r["level"],
            "rule": rule,
        })
        stats[rule] += 1

    for sid, toks in tokens.items():
        used: set[int] = set()
        n = len(toks)
        for w in range(MAXW, 1, -1):                       # longest match first
            for i in range(0, n - w + 1):
                if any(j in used for j in range(i, i + w)):
                    continue
                span = toks[i:i + w]
                if any(t["pos"] in SKIP_POS for t in span):
                    continue
                if all(t["pos"] in FUNCTION_POS for t in span):
                    stats["skip:all-function-words"] += 1
                    continue
                # A word does not BEGIN with a case particle or an auxiliary. Without this, と+お in
                # 「コーヒーとお茶と…」 reads as 十/とお, claims the span, and takes お茶 with it.
                if span[0]["pos"] in FUNCTION_POS:
                    stats["skip:run-starts-on-a-particle"] += 1
                    continue
                surf = "".join(t["surface"] or "" for t in span)
                if len(surf) < 2:
                    continue
                cands = reg.by_surface.get(surf)
                if not cands:
                    continue
                rd = hira("".join(t["reading"] or "" for t in span))
                spelling = hira(surf) if kana_only(surf) else None
                hits = []
                for vid in cands:
                    rs = reg.readings.get(vid) or set()
                    if rd and rd in rs:
                        hits.append((vid, "run-reading"))
                    elif spelling and spelling in rs:
                        hits.append((vid, "run-kana-surface"))
                if not hits:
                    continue
                # LONGEST MATCH WINS, and it wins even when this script cannot use it. A span whose
                # concatenation is a registered dictionary form is claimed here whatever happens next,
                # so a shorter sub-run can never take it: それ+で+は names 其れでは/それでは, and before
                # this line the `uk` guard dropped that window and the two-token fallback それ+で then
                # linked six 「それでは」 clauses to 其れで/それで — the wrong word, and the right one
                # (vocab:1406050, N5, zero sentences) left short by its own occurrences.
                for j in range(i, i + w):
                    used.add(j)
                if len(hits) > 1:
                    stats["skip:ambiguous-run"] += 1
                    continue
                vid, rule = hits[0]
                if vid not in targets:
                    stats["skip:out-of-scope-run"] += 1
                    continue
                if (kana_only(surf) and not kana_only(reg.rec[vid]["headword"] or "")
                        and vid not in reg.uk):
                    stats["skip:kana-run-not-uk"] += 1
                    continue
                if (kana_only(surf)
                        and any(t["pos"] == "verb" and t["surface"] != t["lemma"] for t in span)
                        and not reg.inflectable_content_word(vid)):
                    stats["skip:productive-kana-verb-run"] += 1
                    continue
                if all(t["vocab_id"] is not None for t in span):
                    stats["skip:no-free-anchor"] += 1
                    continue
                emit(sid, span, vid, rule)
        for i, t in enumerate(toks):
            if i in used or t["vocab_id"] is not None or t["pos"] in SKIP_POS:
                continue
            R = hira(t["reading"] or "")
            surf, lemma = t["surface"] or "", t["lemma"] or ""
            cands = reg.by_surface.get(lemma, set()) | reg.by_surface.get(surf, set())
            if not cands:
                continue
            spelling = hira(surf) if kana_only(surf) else None
            hits = []
            for vid in cands:
                rs = reg.readings.get(vid) or set()
                if not rs:
                    continue
                if R and R in rs:
                    rule = "kana-exact"
                elif spelling and spelling in rs:
                    rule = "run-kana-surface"
                elif t["pos"] in INFLECTING and R and any(
                        len(k) >= 2 and R.startswith(k[:-1]) and abs(len(R) - len(k)) <= 3
                        for k in rs):
                    rule = "inflected-stem"
                else:
                    continue
                if not reg.pos_ok(t["pos"], vid):
                    relaxed = (t["pos"] in UK_POS_RELAX and vid in reg.uk
                               and any(len(k) >= 2 and (R == k or spelling == k) for k in rs))
                    if not relaxed:
                        continue
                    rule = "kana-function-word"
                hits.append((vid, rule))
            if not hits:
                continue
            if len(hits) > 1:
                stats["skip:ambiguous-token"] += 1
                continue
            vid, rule = hits[0]
            if vid not in targets:
                continue
            if (kana_only(surf) and not kana_only(reg.rec[vid]["headword"] or "")
                    and vid not in reg.uk):
                stats["skip:kana-token-not-uk"] += 1
                continue
            # W13 apply, guard 5. A bare ONE-KANA function word is not an orthographic variant of
            # anything -- it is spelled exactly as the record is. See the docstring: this keeps
            # だけ / ばかり / など / ほど and refuses で.
            if t["pos"] in FUNCTION_POS and not any(
                    len(k) >= 2 and (R == k or spelling == k) for k in reg.readings.get(vid, ())):
                stats["skip:bare-one-kana-function-word"] += 1
                continue
            emit(sid, [t], vid, rule)

    rows.sort(key=lambda r: (r["sentence"], r["anchor_position"]))
    return rows, dict(sorted(stats.items()))


def write_table(rows: list[dict], stats: dict, table: Path = TABLE,
                scope: tuple[str, ...] = SCOPE_LEVELS,
                held: list[dict] | None = None) -> None:
    lifted = defaultdict(int)
    for r in rows:
        lifted[r["level"]] += 1
    doc = {
        "what_this_is": "W12 orthographic relink. One row per (sentence, token span) that names a "
                        f"taught {'/'.join(scope)} vocabulary record under the >=3 sentence "
                        f"floor under a "
                        "different orthography. Derived by scripts/apply_orthographic_relinks.py "
                        "--derive from db/corpus.sqlite + the exported course tree; applied by the "
                        "same script. Addressed by sentence SLUG and token POSITION, never by row id.",
        "match_rule": "lemma (or surface) is a registered form of the record — headword, kana, "
                      "vocab_form, or a JMdict kanji/kana element — AND the realized reading is a "
                      "registered kana reading. Never a substring match.",
        "scope": f"taught vocab at {'/'.join(scope)} under the floor",
        "derivation_counters": stats,
        "links_by_level": dict(sorted(lifted.items())),
        "row_count": len(rows),
        "held_count": len(held or []),
        "held": held or [],
        "rows": rows,
    }
    table.parent.mkdir(parents=True, exist_ok=True)
    table.write_text(json.dumps(doc, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")


def load_held(table: Path = TABLE) -> dict[tuple[str, str], str]:
    """{(sentence slug, vocab slug): reason} — links derived but deliberately not applied.

    Read BEFORE `--derive` un-applies anything, so a re-derivation cannot re-admit a held link.
    """
    if not table.is_file():
        return {}
    doc = json.loads(table.read_text(encoding="utf-8"))
    return {(h["sentence"], h["vocab"]): h.get("hold_reason", "") for h in doc.get("held", [])}


def load_table(table: Path = TABLE) -> list[dict]:
    doc = json.loads(table.read_text(encoding="utf-8"))
    if doc.get("row_count") != len(doc["rows"]):
        raise SystemExit(f"{table.name}: row_count {doc.get('row_count')} != {len(doc['rows'])} rows")
    return doc["rows"]


# ---------------------------------------------------------------------------------------------
def apply(con: sqlite3.Connection, rows: list[dict], write: bool) -> int:
    reg = Registry(con)
    sid_of = {slug: sid for sid, slug in con.execute("SELECT id,slug FROM sentence")}
    by_pos: dict[tuple[int, int], dict] = {}
    for tid, sid, pos_i, surf, reading, vid in con.execute(
            "SELECT id,sentence_id,position,surface,reading,vocab_id FROM token WHERE split_mode='C'"):
        by_pos[(sid, pos_i)] = {"id": tid, "surface": surf, "reading": reading, "vocab_id": vid}
    problems: list[str] = []
    tok_writes = sv_writes = already = no_anchor = 0
    cur = con.cursor()
    for i, r in enumerate(rows):
        addr = f"row {i}: {r['sentence']} @{r['anchor_position']} {r['surface']!r} -> {r['vocab']}"
        sid = sid_of.get(r["sentence"])
        if sid is None:
            problems.append(f"{addr}: no such sentence in the index")
            continue
        vid = reg.by_slug.get(r["vocab"])
        if vid is None:
            problems.append(f"{addr}: {r['vocab']} names no vocab record")
            continue
        rec = reg.rec[vid]
        if (rec["headword"], rec["kana"]) != (r["headword"], r["kana"]):
            problems.append(f"{addr}: the registry has {rec['headword']}/{rec['kana']}, the row "
                            f"recorded {r['headword']}/{r['kana']} — the record moved under the row")
            continue
        span = [by_pos.get((sid, p)) for p in r["span"]]
        if any(t is None for t in span):
            problems.append(f"{addr}: the span {r['span']} is not a C-token run in this index")
            continue
        if [t["surface"] for t in span] != r["span_surfaces"]:
            problems.append(f"{addr}: span surfaces {[t['surface'] for t in span]!r} != the row's "
                            f"{r['span_surfaces']!r} — the dissection moved under the row")
            continue
        if "".join(t["reading"] or "" for t in span) != r["reading"]:
            problems.append(f"{addr}: span reading "
                            f"{''.join(t['reading'] or '' for t in span)!r} != the row's {r['reading']!r}")
            continue
        # The ANCHOR is chosen against the tree in hand, not pinned to the row. `anchor_position`
        # records what the derivation picked here; in a manifest replay the same span can have a
        # different token free — 県下 anchors on 県 in this index and on 下 in a replay, because the
        # replay links 県/けん where nine months of ad-hoc scripts had left it unlinked. Pinning the
        # position turned that into 44 false failures. What is exact-matched is the SPAN (its
        # surfaces and its reading) and the record; which token of a verified span carries the id is
        # an implementation detail, and a token already linked is still never re-pointed.
        preferred = by_pos[(sid, r["anchor_position"])]
        free = [t for t in ([preferred] + span) if t["vocab_id"] in (None, vid)]
        if not free:
            no_anchor += 1
            continue
        anchor = free[0]
        # reading_verified, computed exactly as build_sentence_vocab.py computes it: does an anchor's
        # realized reading agree EXACTLY with a dictionary reading of the record?
        rd = hira(r["reading"])
        spelling = hira(r["surface"]) if kana_only(r["surface"]) else None
        verified = 1 if (rd in reg.readings.get(vid, set())
                         or (spelling and spelling in reg.readings.get(vid, set()))) else 0
        if anchor["vocab_id"] is None:
            if write:
                cur.execute("UPDATE token SET vocab_id=? WHERE id=? AND vocab_id IS NULL",
                            (vid, anchor["id"]))
                tok_writes += cur.rowcount
            else:
                tok_writes += 1
        else:
            already += 1
        if write:
            cur.execute("INSERT OR IGNORE INTO sentence_vocab "
                        "(sentence_id,vocab_id,link_rule,reading_verified) VALUES (?,?,?,?)",
                        (sid, vid, LINK_RULE, verified))
            sv_writes += cur.rowcount
        else:
            if not con.execute("SELECT 1 FROM sentence_vocab WHERE sentence_id=? AND vocab_id=?",
                               (sid, vid)).fetchone():
                sv_writes += 1
    if problems:
        for p in problems[:20]:
            print(f"  [FAIL] {p}")
        if len(problems) > 20:
            print(f"  … and {len(problems) - 20} more")
        raise SystemExit(f"apply_orthographic_relinks: {len(problems)} row(s) do not match the index")
    print(f"  {len(rows)} rows verified against the index")
    if no_anchor:
        print(f"  {no_anchor} row(s) had no free token in the span in THIS tree and were skipped — "
              f"the span is verified, but every token in it already carries another record and this "
              f"script does not re-point")
    print(f"  token.vocab_id: {tok_writes} written, {already} already linked")
    print(f"  sentence_vocab: {sv_writes} inserted (link_rule={LINK_RULE!r})")
    return tok_writes + sv_writes


def undo(con: sqlite3.Connection, rows: list[dict]) -> int:
    """Remove exactly what this table wrote, so `--derive` can re-measure a clean index.

    The derivation reads the CURRENT coverage to decide which records are short and which tokens are
    free, so re-deriving over an applied table measures a tree this campaign has already changed and
    silently shrinks to whatever is left. `--derive` therefore un-applies first. Only rows of this
    table are touched, and only the link they made: a token in the span carrying the row's record,
    and the `sentence_vocab` row this script's own `link_rule` stamped.
    """
    sid_of = {slug: sid for sid, slug in con.execute("SELECT id,slug FROM sentence")}
    by_slug = {slug: vid for vid, slug in con.execute("SELECT id,slug FROM vocab")}
    cur, n = con.cursor(), 0
    for r in rows:
        sid, vid = sid_of.get(r["sentence"]), by_slug.get(r["vocab"])
        if sid is None or vid is None:
            continue
        for pos in r["span"]:
            cur.execute("UPDATE token SET vocab_id=NULL WHERE sentence_id=? AND position=? "
                        "AND split_mode='C' AND vocab_id=?", (sid, pos, vid))
            n += cur.rowcount
        cur.execute("DELETE FROM sentence_vocab WHERE sentence_id=? AND vocab_id=? AND link_rule=?",
                    (sid, vid, LINK_RULE))
        n += cur.rowcount
    con.commit()
    print(f"  --derive: un-applied {n} write(s) from the previous table before re-measuring")
    return n


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--derive", action="store_true",
                    help="un-apply the current table, re-derive it from the index, rewrite it")
    ap.add_argument("--check", action="store_true", help="verify only, write nothing")
    ap.add_argument("--scope", default=",".join(SCOPE_LEVELS),
                    help="record levels the derivation targets (default n5,n4)")
    ap.add_argument("--table", type=Path, default=None,
                    help="tracked table to derive/apply (default the n5/n4 one; --scope n3 "
                         "defaults to orthographic_relinks_n3.json)")
    ap.add_argument("--db", default=None, help=argparse.SUPPRESS)
    args = ap.parse_args()
    scope = tuple(x for x in args.scope.replace(" ", "").split(",") if x)
    table = args.table or (TABLE_N3 if scope == ("n3",) else TABLE)
    db = Path(args.db) if args.db else DB
    con = sqlite3.connect(db)
    con.execute("PRAGMA foreign_keys=ON")
    print(f"apply_orthographic_relinks: {db} | scope {scope} | table {table.name}")
    if args.derive:
        holds = load_held(table)          # read BEFORE undo: the hold list outlives the derivation
        if table.is_file():
            undo(con, load_table(table))
        rows, stats = derive(con, OUT, scope)
        kept, held, seen = [], [], set()
        for r in rows:
            reason = holds.get((r["sentence"], r["vocab"]))
            if reason is None:
                kept.append(r)
            else:
                held.append(dict(r, hold_reason=reason))
                seen.add((r["sentence"], r["vocab"]))
        # A hold the derivation does not produce TODAY is carried forward unchanged, never dropped.
        # Dropping it silently un-holds the link the next time the derivation does produce it, which
        # is exactly what happened once here: a run over a half-applied index found 206 candidates
        # instead of 476 and rewrote a 37-entry hold list down to 6.
        prior = {(h["sentence"], h["vocab"]): h for h in
                 (json.loads(table.read_text(encoding="utf-8")).get("held") or [])
                 } if table.is_file() else {}
        for k, h in prior.items():
            if k not in seen:
                held.append(h)
        held.sort(key=lambda h: (h["sentence"], h["anchor_position"]))
        stats["held:i+1-budget"] = len(held)
        write_table(kept, stats, table, scope, held)
        print(f"  derived {len(kept)} links ({len(held)} held) -> {table.relative_to(ROOT)}")
        for k, v in stats.items():
            print(f"    {k}: {v}")
        rows = kept
    rows = load_table(table)
    changed = apply(con, rows, write=not args.check)
    if args.check:
        print(f"  --check: {changed} write(s) WOULD be made")
    else:
        con.commit()
        print(f"  committed ({changed} write(s))")
    con.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
