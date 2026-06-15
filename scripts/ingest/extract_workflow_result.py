#!/usr/bin/env python3
"""Extract a dissection workflow's `.output` result array into a clean batch_*_result.json.

A Workflow's .output file holds the returned JS value (a JSON array of {layerB, verdict}). This robustly
locates that array (whole-file json.loads first, else first balanced [...] span), writes it out, and prints a
content-appropriateness scan (sex/violence/etc. keyword flags in the pt translation) so we can drop unsavory
real-source sentences before they enter a learner corpus. Usage:
  extract_workflow_result.py <output_file> <out_json>
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]

# pt-BR keywords that make a sentence inappropriate / off-tone for a learner corpus (creepy, sexual,
# graphic-violence). Conservative: flags for human review, does not auto-delete.
FLAG = re.compile(
    r"\b(saia|seios|peito|pelad[oa]|sexo|sexual|transar|trepar|esp(?:iar|iou|reit)|"
    r"assédio|assediar|estupr|assassin|suicíd|prostitu|bunda|nádegas|íntim[oa]s?|"
    r"tarad[oa]|pervertid|encarando as mulheres)", re.IGNORECASE)


def main() -> int:
    out_file, out_json = sys.argv[1], sys.argv[2]
    text = Path(out_file).read_text(encoding="utf-8")
    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        i = text.index("[")
        depth = 0
        for j in range(i, len(text)):
            if text[j] == "[":
                depth += 1
            elif text[j] == "]":
                depth -= 1
                if depth == 0:
                    data = json.loads(text[i:j + 1])
                    break
        else:
            print("could not locate JSON array", file=sys.stderr)
            return 1
    if isinstance(data, dict) and isinstance(data.get("result"), list):
        data = data["result"]  # Workflow wraps the returned array under .result
    if not isinstance(data, list):
        print(f"expected list, got {type(data)}", file=sys.stderr)
        return 1
    Path(out_json).write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    faithful = sum(1 for d in data if (d.get("verdict") or {}).get("faithful") is not False)
    print(f"extracted {len(data)} items -> {out_json} ({faithful} faithful)")
    print("--- content flags (review before persist) ---")
    flagged = 0
    for d in data:
        lb = d.get("layerB") or {}
        pt = lb.get("pt") or ""
        if FLAG.search(pt):
            flagged += 1
            print(f"  {lb.get('slug')}: {pt}")
    print(f"--- {flagged} flagged of {len(data)} ---")
    return 0


if __name__ == "__main__":
    sys.exit(main())
