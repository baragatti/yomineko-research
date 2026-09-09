#!/usr/bin/env python3
"""W13b Derive — build the mechanical half of the mined-N3 Layer-B, and nothing else.

Reads the three W13b inputs and emits one file per batch under
`research/derived/n3_mined/layerb_derived/`, in EXACTLY the shape
`scripts/ingest/ingest_mined_stages.py` reads (`sentences[]`, token/particle rows keyed by the C-token
`position` from `dissect.Dissector.skeleton()`).

WHAT IS DERIVED HERE, and what is deliberately left empty:

  token `gloss_pt`      derived for 99.1 % of content tokens. `gloss_origin` says how:
                          bank-modal   the modal pt-BR gloss the bank already uses for the same
                                       (surface, lemma, pos_coarse) — 75.3 %
                          registry     '; '.join of the first three pt-BR glosses of the linked vocab's
                                       sense[0] — 23.9 % (the only sense convention the schema carries;
                                       lessons store no sense pointer)
                          rule-numeral a bare numeral rendered in pt-BR digits by rule, added here
                        `gloss_status` says how far to trust it: `unique-accept` (the key had exactly one
                        candidate), `ambiguous-verify` (more than one; a reviewer rules per lemma) or
                        `author` (nothing fired).

  token `role_pt`       NOT emitted. The residue carries a `role_pt_hint` (the bank's modal role for the
                        same surface) and it is frequently FALSE in a new sentence: 靴 comes back
                        "objeto direto" inside この靴は…, where it is the topic. role_pt is optional to
                        the validator, so a hint that is wrong that often goes into the work lists as a
                        hint and never into the corpus payload.

  particle `function_pt` the bank's modal short label for the (particle, function_type) pair — 99.89 %.

  particle `explanation_pt`
                        REQUIRED by validate.py, and mostly authored. The residue report's §3 proposes a
                        parameterised template over `build_sentence_patterns.role_of()`. Implemented, but
                        NOT over all 8,466 role-bearing particles: `role_of()` returns deliberately
                        NON-COMMITTAL roles for に / で / と / から-case / の-nominalizer / が-conjunctive
                        ("ni-phrase", "de-phrase", …) precisely because the corpus does not carry the
                        distinction, and rendering those into Portuguese would either be vacuous or claim
                        a sense the data does not have. build_sentence_patterns' own docstring records
                        three drills that shipped wrong for exactly that reason. So the template fires
                        only where the role is committal AND a structural guard confirms the shape:
                          は/binding     when it attaches to a nominal (kills では / には / とは)
                          が/case        when it attaches to a nominal
                          を/case        when it attaches to a nominal and a verb follows in the clause
                          の/case        when nominal on both sides
                          て/conjunctive when it attaches to a verbal and something follows
                        plus four context-free sentence-final pairs whose bank texts genuinely repeat
                        (measured on the bank: か 50.6 %, よ 92.9 %, ね 90.0 % of explanations name no
                        Japanese beyond the particle itself). Everything else is
                        `explanation_status: "author"`. な/sentence-final and の/sentence-final are
                        excluded on purpose: each is two different particles wearing one label
                        (proibição vs ênfase; pergunta vs explicativo).

  `structure_explanation_pt`
                        NEVER derived. The bank's 5,889 structure paragraphs are 5,889 distinct strings;
                        there is no precedent to inherit. The slot is emitted null with
                        `structure_status: "author"`, plus `clause_structure_predicted` — a 72.3 %-accurate
                        surface classifier, carried ONLY to batch the authoring work by sentence shape.

Nothing in this file writes to the database or to `corpus/`. The DB is opened only to run the Dissector;
pass `--db` at a copy.

Usage:
    python scripts/derive_layerb.py --db <copy.sqlite> [--skeletons cache.jsonl] [--batch-size 150]
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from collections import Counter
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]

ROOT = Path(__file__).resolve().parents[1]
MINED = ROOT / "research" / "derived" / "n3_mined"
OUT_DIR = MINED / "layerb_derived"

NOMINAL = {"名詞", "代名詞", "数詞", "接尾辞"}
VERBAL = {"動詞", "形容詞", "形状詞", "助動詞"}
PUNCT = {"補助記号"}


# --------------------------------------------------------------------------------------- identity
def sentence_key(row: dict) -> str:
    """The stable key for a mined sentence, in both the derived batches and the ingest.

    Real rows key on the Tatoeba id, because that is what the existing 324 authored batches use and what
    `sent:tatoeba-<id>` is built from. The 26 generated rows have `tatoeba_id: ""` — keying them on that
    collapses all 26 onto one key (blocker 1 of the residue report), so they key on the same hash the
    bank already uses for generated sentences: sha1(jp)[:12], slug `sent:gen-<hash>`.
    """
    tid = row.get("tatoeba_id")
    if not row.get("generated") and tid not in (None, ""):
        return str(tid)
    return "gen-" + hashlib.sha1(row["jp"].encode("utf-8")).hexdigest()[:12]


def sentence_slug(key: str) -> str:
    return f"sent:{key}" if key.startswith("gen-") else f"sent:tatoeba-{key}"


# ------------------------------------------------------------------------------------ numeral rule
MULT = {"万": 10_000, "億": 100_000_000, "兆": 1_000_000_000_000}
NUM_BODY = re.compile(r"^([0-9]+)([万億兆]?)$")


def numeral_gloss(surface: str) -> str | None:
    """pt-BR rendering of a bare arabic numeral, with or without a 万/億/兆 multiplier.

    Covers the bare numerals in the token residue (50, 12, 30万, 500万, 2020 …). Deliberately narrow: it
    fires only on a surface that is digits, optionally closed by one multiplier character. Anything with
    a counter, a kanji numeral or a mixed reading falls through to the author list rather than risking a
    wrong number.
    """
    s = surface.translate(str.maketrans("０１２３４５６７８９", "0123456789")).replace(",", "")
    m = NUM_BODY.match(s)
    if not m:
        return None
    n = int(m.group(1)) * MULT.get(m.group(2), 1)
    if n >= 1_000_000 and n % 1_000_000 == 0:
        q = n // 1_000_000
        return f"{q} milhão" if q == 1 else f"{q} milhões"
    if n >= 1_000 and n % 1_000 == 0:
        return f"{n // 1_000} mil"
    return f"{n:,}".replace(",", ".") if n >= 10_000 else str(n)


# ------------------------------------------------------------------------- clause-structure predictor
COND = ("たら", "なら", "れば", "けれ")
CAUSE = ("から", "ので")
TIME = ("とき", "時", "あと", "後", "前")


def predict_clause_structure(tokens: list[dict]) -> str:
    """The residue report's §4(a) surface classifier, retuned: 72.3 % against the bank's 5,825 labels.

    A BATCHING KEY, not data. It never reaches the corpus; it only groups the 4,223 authoring jobs by
    sentence shape so one instruction covers a run of them. Rule ORDER is the report's; three of the
    tests were tightened after scoring the literal reading of the report against the bank (63.5 %):

      * `fragment` was firing on every sentence closed by a sentence-final particle (…ですね, …だよ),
        because the last token is then a 助詞. The trailing run of punctuation and sentence-final
        particles is now stripped before the predicate test. Worth 177 sentences on its own.
      * `question` missed every question written with ？ and no か. Both now count.
      * `cause` and `subordinate-time` were matching から / ため / 前 / 後 as SUBSTRINGS, so 東京から
        (origin), 目の前 (a place) and 午後 (a time of day) all read as clause markers. They now test
        tokens, with the part of speech that makes the reading a clause link.
    """
    joined = "".join(t["surface"] for t in tokens)
    real = [t for t in tokens if t["pos_coarse"] not in PUNCT]
    # the predicate test ignores what trails the predicate: punctuation and sentence-final particles
    tail = list(real)
    while tail and (tail[-1].get("particle_function") == "sentence-final"
                    or tail[-1].get("pos_fine") == "終助詞"):
        tail.pop()

    if any(t["surface"] in ("か", "？", "?") and (t.get("particle_function") == "sentence-final"
                                                 or t["pos_coarse"] in PUNCT) for t in tokens):
        return "question"
    if any(t.get("inflection") == "imperative" for t in tokens) or "ください" in joined \
            or "下さい" in joined or "なさい" in joined:
        return "imperative"
    if "と言" in joined or "と思" in joined or "という" in joined:
        return "quote"
    if any(s in joined for s in COND):
        return "conditional"
    if any(t["surface"] in CAUSE and t.get("pos_fine") == "接続助詞" for t in tokens) \
            or any(t["surface"] in ("ため", "為") and t["pos_coarse"] == "名詞" for t in tokens):
        return "cause"
    if any(t["surface"] in TIME and t["pos_coarse"] == "名詞" for t in tokens):
        return "subordinate-time"
    if any(t.get("pos_fine") == "接続助詞" for t in tokens):
        return "coordinate"
    if any(t["surface"] == "は" and t.get("pos_fine") == "係助詞" for t in tokens):
        return "topic-comment"
    if not tail or tail[-1]["pos_coarse"] not in VERBAL:
        return "fragment"
    return "simple"


# -------------------------------------------------------------------------------- particle template
CONTEXT_FREE = {
    ("か", "sentence-final"):
        "か no fim transforma a frase em pergunta.",
    ("よ", "sentence-final"):
        "よ no fim passa a informação ao ouvinte com ênfase, como quem diz 'olha' ou 'viu'.",
    ("ね", "sentence-final"):
        "ね no fim suaviza a afirmação e pede a concordância de quem ouve, como o nosso 'né?'.",
    ("わ", "sentence-final"):
        "わ no fim suaviza a afirmação e dá um tom expressivo, tradicionalmente associado à fala "
        "feminina, sem mudar o sentido literal.",
}


def _left_chunk(tokens: list[dict], i: int) -> str | None:
    """The contiguous run of non-particle, non-punctuation tokens that the particle at i closes."""
    buf = []
    j = i - 1
    while j >= 0:
        t = tokens[j]
        if t["pos_coarse"] in PUNCT or t["pos_coarse"] == "助詞":
            break
        buf.append(t["surface"])
        j -= 1
    return "".join(reversed(buf)) or None


def _prev(tokens: list[dict], i: int) -> dict | None:
    return tokens[i - 1] if i > 0 else None


def _next(tokens: list[dict], i: int) -> dict | None:
    for t in tokens[i + 1:]:
        if t["pos_coarse"] not in PUNCT:
            return t
    return None


def _verb_in_clause(tokens: list[dict], i: int) -> dict | None:
    """The nearest following verbal token, stopping at a comma (a clause boundary)."""
    for t in tokens[i + 1:]:
        if t["pos_coarse"] in PUNCT:
            return None
        if t["pos_coarse"] in ("動詞", "形容詞", "形状詞"):
            return t
    return None


def particle_template(tokens: list[dict], i: int, particle: str, ft: str | None) -> str | None:
    """The templated pt-BR explanation, or None when the pair/shape is not covered (then: author).

    Every sentence produced here is true by construction from the dissection: it names the tokens the
    particle actually stands between and the role the (particle, function_type) pair actually assigns.
    It claims nothing about meaning that the corpus does not already record.
    """
    key = (particle, ft or "")
    if key in CONTEXT_FREE:
        return CONTEXT_FREE[key]

    prev, nxt = _prev(tokens, i), _next(tokens, i)
    chunk = _left_chunk(tokens, i)

    if key == ("は", "binding"):
        if not chunk or not prev or prev["pos_coarse"] not in NOMINAL:
            return None      # では / には / とは / 〜てはいけない: a different は, authored
        return (f"は apresenta {chunk} como o tópico da frase, ou seja, o assunto sobre o qual se faz a "
                f"afirmação seguinte.")

    if key == ("が", "case"):
        if not chunk or not prev or prev["pos_coarse"] not in NOMINAL:
            return None
        v = _verb_in_clause(tokens, i)
        if v:
            return (f"が marca {chunk} como o sujeito de {v['lemma']}, isto é, quem faz ou de quem se diz "
                    f"o que o predicado exprime.")
        return f"が marca {chunk} como o sujeito daquilo que se afirma em seguida."

    if key == ("を", "case"):
        v = _verb_in_clause(tokens, i)
        if not chunk or not prev or prev["pos_coarse"] not in NOMINAL or not v \
                or v["pos_coarse"] != "動詞":
            return None
        return (f"を marca {chunk} como o objeto direto de {v['lemma']}, ou seja, aquilo sobre o que a "
                f"ação recai.")

    if key == ("の", "case"):
        if not chunk or not prev or not nxt or prev["pos_coarse"] not in NOMINAL \
                or nxt["pos_coarse"] not in NOMINAL:
            return None
        # the modifier is the whole left chunk, not just the token の touches: 十頭の牛 modifies with
        # 十頭, not with 頭
        return (f"の liga {chunk} a {nxt['surface']} e junta os dois num bloco só, em que "
                f"{nxt['surface']} é o núcleo e {chunk} o modificador.")

    if key == ("て", "conjunctive"):
        if not prev or prev["pos_coarse"] not in ("動詞", "形容詞", "助動詞") or not nxt:
            return None
        # the lemma, so an auxiliary reads as いる rather than as the bare stem い it appears as
        right = nxt.get("lemma") or nxt["surface"]
        return (f"て liga {prev['lemma']} ao que vem depois ({right}) e encadeia os dois dentro "
                f"da mesma frase.")

    return None


# ------------------------------------------------------------------------------------------- inputs
def load_rows() -> list[dict]:
    rows = []
    for name, gen in (("accepted.json", False), ("generated.json", True)):
        for r in json.loads((MINED / name).read_text(encoding="utf-8"))["rows"]:
            if r.get("reject"):
                continue
            r = dict(r)
            r["generated"] = gen or bool(r.get("generated"))
            rows.append(r)
    return rows


def load_skeletons(rows: list[dict], db: Path | None, cache: Path | None) -> dict[str, dict]:
    """Skeletons by sentence key. Uses the cache when it covers the input; otherwise runs the Dissector."""
    by_jp: dict[str, dict] = {}
    if cache and cache.exists():
        for line in cache.read_text(encoding="utf-8").splitlines():
            if line.strip():
                sk = json.loads(line)
                by_jp[sk["jp"]] = sk
    missing = [r for r in rows if r["jp"] not in by_jp]
    if missing:
        if not db:
            raise SystemExit(f"{len(missing)} sentences have no cached skeleton and no --db was given")
        sys.path.insert(0, str(ROOT / "scripts" / "ingest"))
        sys.path.insert(0, str(ROOT / "scripts"))
        from dissect import Dissector           # noqa: PLC0415
        diss = Dissector(db)
        for r in missing:
            sk = diss.skeleton(r["jp"])
            by_jp[r["jp"]] = {"jp": r["jp"], "tokens": sk["tokens"], "particles": sk["particles"]}
        if cache:
            with cache.open("w", encoding="utf-8") as fh:
                for sk in by_jp.values():
                    fh.write(json.dumps(sk, ensure_ascii=False) + "\n")
    return {sentence_key(r): by_jp[r["jp"]] for r in rows}


ORIGIN = {"bank": "bank-modal", "registry-sense0": "registry"}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", type=Path, default=None, help="a COPY of corpus.sqlite (Dissector input)")
    ap.add_argument("--skeletons", type=Path, default=None, help="jsonl cache of dissector skeletons")
    ap.add_argument("--batch-size", type=int, default=150)
    ap.add_argument("--out", type=Path, default=OUT_DIR)
    args = ap.parse_args()

    rows = load_rows()
    residue = json.loads((MINED / "layerb_residue.json").read_text(encoding="utf-8"))
    res_by_jp = {s["jp"]: s for s in residue["sentences"]}
    skel = load_skeletons(rows, args.db, args.skeletons)
    print(f"{len(rows)} sentences, {len(skel)} skeletons, {len(res_by_jp)} residue records")

    stats: Counter = Counter()
    template_by_pair: Counter = Counter()
    author_by_pair: Counter = Counter()
    out_sentences = []

    for r in rows:
        key = sentence_key(r)
        sk = skel[key]
        res = res_by_jp.get(r["jp"], {})
        toks = sk["tokens"]

        # -------- tokens
        tokens_out = []
        for rt in res.get("tokens", []):
            gloss, origin = rt.get("gloss_pt"), ORIGIN.get(rt.get("gloss_source"))
            if gloss:
                status = rt.get("confidence") or "ambiguous-verify"
            else:
                num = numeral_gloss(rt["surface"])
                if num is not None:
                    gloss, origin, status = num, "rule-numeral", "unique-accept"
                else:
                    origin, status = None, "author"
            stats[f"token:{status}"] += 1
            if origin:
                stats[f"origin:{origin}"] += 1
            # lemma + pos ride along so a per-(lemma, pos) ruling can be applied to this row later
            # without re-reading the residue; the ingest ignores keys it does not know.
            row = {"position": rt["position"], "lemma": rt.get("lemma"), "pos": rt.get("pos"),
                   "gloss_status": status, "gloss_origin": origin}
            if gloss:
                row["gloss_pt"] = gloss
            tokens_out.append(row)

        # -------- particles
        particles_out = []
        for rp in res.get("particles", []):
            pos = rp["position"]
            i = next((n for n, t in enumerate(toks) if t["position"] == pos), None)
            ft = rp.get("function_type")
            expl = particle_template(toks, i, rp["particle"], ft) if i is not None else None
            pair = f"{rp['particle']}/{ft}"
            if expl:
                template_by_pair[pair] += 1
                stats["particle:template"] += 1
            else:
                author_by_pair[pair] += 1
                stats["particle:author"] += 1
            if not rp.get("function_pt"):
                stats["particle:function_author"] += 1
            particles_out.append({
                "position": pos,
                "particle": rp["particle"],
                "function_type": ft,
                "function_pt": rp.get("function_pt"),
                "function_status": "bank-modal" if rp.get("function_pt") else "author",
                "explanation_pt": expl,
                "explanation_status": "template" if expl else "author",
            })

        cs = predict_clause_structure(toks)
        stats[f"clause:{cs}"] += 1
        out_sentences.append({
            "key": key,
            "tatoeba_id": r.get("tatoeba_id") if not key.startswith("gen-") else None,
            "slug": sentence_slug(key),
            "generated": bool(r.get("generated")),
            "jp": r["jp"],
            "lesson": r.get("lesson"),
            "targets": r.get("targets") or ([r["target"]] if r.get("target") else []),
            "clause_structure_predicted": cs,
            "tokens": tokens_out,
            "particles": particles_out,
            "structure_explanation_pt": None,
            "structure_status": "author",
        })
        stats["sentences"] += 1

    # -------- emit
    args.out.mkdir(parents=True, exist_ok=True)
    for f in args.out.glob("batch-*.json"):
        f.unlink()
    n = args.batch_size
    batches = [out_sentences[i:i + n] for i in range(0, len(out_sentences), n)]
    for bi, chunk in enumerate(batches, 1):
        (args.out / f"batch-{bi:02d}.json").write_text(
            json.dumps({"batch": bi, "unit": "W13b", "kind": "derived (mechanical) mined Layer-B",
                        "sentences": chunk}, ensure_ascii=False, indent=1), encoding="utf-8")
    summary = {
        "unit": "W13b",
        "generated_by": "scripts/derive_layerb.py",
        "inputs": ["research/derived/n3_mined/accepted.json",
                   "research/derived/n3_mined/generated.json",
                   "research/derived/n3_mined/layerb_residue.json"],
        "batches": len(batches),
        "batch_size": n,
        "counts": dict(sorted(stats.items())),
        "particle_template_by_pair": dict(template_by_pair.most_common()),
        "particle_author_by_pair": dict(author_by_pair.most_common(40)),
    }
    (args.out / "_summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=1),
                                            encoding="utf-8")
    print(json.dumps(summary["counts"], ensure_ascii=False, indent=1))
    print(f"wrote {len(batches)} batches to {args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
