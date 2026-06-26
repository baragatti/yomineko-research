#!/usr/bin/env python3
"""Re-authoring sampler for VOCAB glosses (license_audit.md D-LIC-1: remove verbatim JMdict (CC BY-SA) glosses).
Senses are DEFINED by their gloss, so we cannot paraphrase per-sense (a paraphrase is still a derivative). Instead
we re-author per VOCAB at the word level: the model is given ONLY facts — headword, kana, POS, example sentences
(jp), and our (already-independent) kanji meanings as hints — NOT the JMdict glosses, and writes the word's own
concise, learner-appropriate core meanings (as senses). Single-sense words ≈ kanji case; multi-sense words get a
short core set (not JMdict's 20-way split). Writes research/derived/reauthor/vocab/batch_*.json.
Usage: reauthor_vocab_sample.py [--levels n5,n4] [--batch 40]"""
from __future__ import annotations
import argparse, json, sqlite3, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "ingest"))
sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
from i18n_text import get_text  # noqa: E402
ROOT = Path(__file__).resolve().parents[2]
DB = ROOT / "db" / "corpus.sqlite"
KANJI_RE = __import__("re").compile(r"[一-鿿]")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--levels", default="n5,n4,n3,n2,n1")
    ap.add_argument("--batch", type=int, default=40)
    args = ap.parse_args()
    levels = [x.strip() for x in args.levels.split(",")]
    c = sqlite3.connect(DB)
    # kanji -> our (re-authored) meanings, as gloss hints for rarer words
    kmean = {}
    for ch in {ch for (hw,) in c.execute("SELECT headword FROM vocab WHERE level IN ({})".format(
            ",".join("?" * len(levels))), levels) for ch in hw if KANJI_RE.match(ch)}:
        r = c.execute("SELECT id FROM kanji WHERE character=?", (ch,)).fetchone()
        if r:
            m = get_text(c, "kanji", r[0], "meanings")
            if m:
                kmean[ch] = m[:3]
    sample = []
    q = ("SELECT id, headword, kana, lexeme_type, verb_class, adj_class FROM vocab "
         "WHERE level IN ({}) ORDER BY common DESC, freq_rank IS NULL, freq_rank".format(",".join("?" * len(levels))))
    for vid, hw, kana, lex, vc, ac in c.execute(q, levels).fetchall():
        pos = [r[0] for r in c.execute(
            "SELECT pos FROM vocab_sense WHERE vocab_id=? ORDER BY sense_order LIMIT 1", (vid,))]
        pos_tags = json.loads(pos[0]) if pos and pos[0] else []
        examples = [r[0] for r in c.execute(
            "SELECT s.jp FROM sentence s JOIN sentence_vocab sv ON sv.sentence_id=s.id WHERE sv.vocab_id=? "
            "ORDER BY s.ai_generated, s.translation_confidence DESC LIMIT 2", (vid,))]
        khints = {ch: kmean[ch] for ch in dict.fromkeys(hw) if ch in kmean}
        sample.append({"id": vid, "headword": hw, "kana": kana, "pos": pos_tags,
                       "lexeme": lex, "verb_class": vc, "adj_class": ac,
                       "examples": examples, "kanji_hints": khints})
    outdir = ROOT / "research" / "derived" / "reauthor" / "vocab"
    outdir.mkdir(parents=True, exist_ok=True)
    for old in outdir.glob("batch_*.json"):
        old.unlink()
    nb = (len(sample) + args.batch - 1) // args.batch
    for b in range(nb):
        (outdir / f"batch_{b:04d}.json").write_text(
            json.dumps(sample[b * args.batch:(b + 1) * args.batch], ensure_ascii=False), encoding="utf-8")
    (outdir / "_sample.json").write_text(json.dumps(sample, ensure_ascii=False), encoding="utf-8")
    print(f"reauthor vocab [{args.levels}]: {len(sample)} vocab -> {nb} batches (batch={args.batch})")
    c.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
