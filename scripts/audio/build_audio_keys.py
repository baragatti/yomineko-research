"""Write research/derived/audio/audio_keys.json, the tracked table of audio keys the exporters publish (W47).

The key is plan.py's: the 26-char content hash of the exact synthesis request (design/audio_pipeline.md
§3), so the export names the very file the generator writes, whether or not it exists yet. Torch-free,
no GPU. The table is read by export_corpus.py (sentence, vocab), build_kana.py (kana),
build_listening_bank.py (listening turns) and export_course.py (lesson narration);
scripts/validate/validate_audio_keys.py fails when the table or the export drifts from the plan.

Run after any export change that touches voiced text, then re-run those exporters:
  python scripts/audio/build_audio_keys.py [--tier n5]
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from plan import TABLE_KINDS, TIERS, expected_keys  # noqa: E402

REPO = HERE.parents[1]
OUT = REPO / "research" / "derived" / "audio" / "audio_keys.json"
DOC = ("audio_key per voiceable item up to `tier`, computed by scripts/audio/plan.py from the export "
       "(design/audio_pipeline.md §3). sentence/vocab/kana: record id -> key (lang ja). listening: "
       "'<item>#script[i]' -> key (lang ja). narration: lesson id -> ordered [{span, audio_lang, audio_key}], "
       "span = the element path of the body block the unit voices. Regenerate with "
       "scripts/audio/build_audio_keys.py; never edit by hand.")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--tier", choices=TIERS, default="n5")
    a = ap.parse_args()
    t = expected_keys(REPO, a.tier)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps({"_doc": DOC, **t}, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    counts = {k: (sum(len(v) for v in t[k].values()) if k == "narration" else len(t[k])) for k in TABLE_KINDS}
    print(f"audio keys up to {a.tier}: {counts} -> {OUT.relative_to(REPO).as_posix()}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
