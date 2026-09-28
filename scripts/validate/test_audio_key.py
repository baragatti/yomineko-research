#!/usr/bin/env python3
"""W47 unit test of the audio key (scripts/audio/plan.py, design/audio_pipeline.md §3.3).

  K1 same request -> same key (and key order in the spec does not matter);
  K2 any field change -> a different key: every top-level field and every param, one at a time;
  K3 URL- and path-safe: ^[a-z2-7]{26}$, unchanged by URL quoting, case-insensitive-FS safe;
  K4 pinned vector: canonicalisation cannot change silently (it would re-key every clip);
  K5 no collision over the whole plan (every tier), and the collision check itself fires.
"""
from __future__ import annotations

import copy
import sys
import urllib.parse
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts" / "audio"))
import plan  # noqa: E402

fails: list[str] = []


def ok(cond: bool, msg: str) -> None:
    if not cond:
        fails.append(msg)


u = plan.Unit("sentence", "ja", "ja-sentence", "きょうはいちがついつかだ", "今日は１月５日だ", "", "tokens")
spec = plan.build_spec(u)
key = plan.key_of(spec)

# K1
ok(plan.key_of(plan.build_spec(u)) == key, "K1 same unit, different key")
ok(plan.key_of(dict(reversed(list(spec.items())))) == key, "K1 key depends on dict order")
ok(plan.key_of(copy.deepcopy(spec)) == key, "K1 deep copy re-keys")

# K2
for field, new in (("v", 2), ("kind", "human"), ("lang", "pt-BR"), ("norm", "ja-2"), ("text", u.text + "ね"),
                   ("voice", "ja-m1@1"), ("model", spec["model"] + "x"), ("post", "p2")):
    s = copy.deepcopy(spec)
    s[field] = new
    ok(plan.key_of(s) != key, f"K2 changing {field} kept the key")
for p in spec["params"]:
    s = copy.deepcopy(spec)
    s["params"][p] = s["params"][p] + 1 if isinstance(s["params"][p], (int, float)) else s["params"][p] + "x"
    ok(plan.key_of(s) != key, f"K2 changing params.{p} kept the key")
ok(plan.key_of(plan.build_spec(u, take=2)) != key, "K2 a retake kept the key")
ok(plan.base_of(plan.build_spec(u, take=2)) == plan.base_of(spec), "K2 base_of must ignore the take")

# K3
ok(bool(plan.KEY_RE.match(key)) and len(key) == 26, f"K3 malformed key {key!r}")
ok(urllib.parse.quote(key, safe="") == key and key == key.lower(), "K3 key not URL-safe / not lower case")

# K4 (re-pin only on a deliberate change to canonical() or key_of(): it re-keys every clip). The value
# was cross-checked with an independent Node implementation (sha256 -> RFC 4648 base32, lower, 26).
PINNED = plan.key_of({"v": 1, "kind": "tts", "lang": "ja", "norm": "ja-1", "text": "きょうはいちがついつかだ",
                      "voice": "ja-f1@1", "model": "chatterbox-mtl-v3@0",
                      "params": {"exaggeration": 0.5, "cfg_weight": 0.5, "temperature": 0.8, "take": 1},
                      "post": "p1"})
ok(PINNED == "un3jg2igda6ziv7yuhvxrqqsze", f"K4 pinned vector moved: {PINNED}")

# K5
pl = plan.plan_units(ROOT)
keys = plan.keyed(pl)
specs = {plan.canonical(plan.build_spec(x)) for x in pl.units.values()}
ok(len(set(keys.values())) == len(specs), f"K5 {len(specs)} distinct specs but {len(set(keys.values()))} keys")
real_key_of = plan.key_of
plan.key_of = lambda s: "a" * 26  # every spec on one key: the check must abort
try:
    plan.keyed(pl)
    ok(False, "K5 keyed() did not abort on a collision")
except SystemExit:
    pass
finally:
    plan.key_of = real_key_of

for f in fails:
    print("  [FAIL]", f)
print(f"audio key: {'FAIL ' + str(len(fails)) if fails else '0 FAIL'} — K1-K5 over {len(keys)} planned units, "
      f"{len(specs)} distinct specs")
sys.exit(1 if fails else 0)
