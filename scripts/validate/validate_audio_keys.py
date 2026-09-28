#!/usr/bin/env python3
"""W47 gate: every exported audio key IS plan.py's key for that item, so keys cannot drift.

The export names a clip by the 26-char hash of its synthesis request (design/audio_pipeline.md §3);
the generator writes the file under the same hash. If the export and the plan disagree, a button
points at a file that will never exist. Over the EXPORT (corpus/ + course/), against
scripts/audio/plan.py run on the same tree:

  A1  research/derived/audio/audio_keys.json == plan.expected_keys(tree, tier): a table built before
      the export changed, or by an older plan / config, fails;
  A2  every audio_key on a sentence, vocab, kana record and listening script turn equals the plan's
      key for that record, every record the plan voices carries one, and audio_lang is "ja";
  A3  every lesson's narration[] equals the plan's ordered [{span, audio_lang, audio_key}];
  A4  every key matches ^[a-z2-7]{26}$ (URL- and path-safe, lower case);
  A5  no two different specs share a key (plan.keyed aborts on a collision).

Plant-proved: `--selftest` copies what it reads (and this file + plan.py) into a temp tree, plants
each violation in turn, requires every plant to fail and the untouched copy to pass.
"""
from __future__ import annotations

import glob
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts" / "audio"))
import plan  # noqa: E402  (this tree's plan.py: the fixture's own copy under --selftest)

TABLE = ROOT / "research" / "derived" / "audio" / "audio_keys.json"
JA_KINDS = ("sentence", "vocab", "kana", "listening")


def _load(p: Path):
    return json.loads(p.read_text(encoding="utf-8"))


def exported(root: Path) -> dict:
    """The audio fields the export carries, in the table's shape: kind -> id -> (key, lang)."""
    out: dict = {k: {} for k in plan.TABLE_KINDS}

    def take(kind: str, rid: str, rec: dict) -> None:
        if "audio_key" in rec or "audio_lang" in rec:
            out[kind][rid] = (rec.get("audio_key"), rec.get("audio_lang"))

    for r in _load(root / "corpus/sentences/bank.json"):
        take("sentence", r["slug"], r)
    for p in sorted(glob.glob(str(root / "corpus/vocab/*.json"))):
        for r in _load(Path(p)):
            take("vocab", r["slug"], r)
    for p in sorted(glob.glob(str(root / "corpus/kana/[hk]*.json"))):
        for r in _load(Path(p)):
            take("kana", r["id"], r)
    for p in sorted(glob.glob(str(root / "corpus/exam_banks/*_listening_*.json"))):
        for it in _load(Path(p)):
            for i, turn in enumerate(it.get("script") or []):
                take("listening", f"{it['id']}#script[{i}]", turn)
    for p in sorted(glob.glob(str(root / "course/*/topic-*/lesson-*.json"))):
        les = _load(Path(p))
        if "narration" in les:
            out["narration"][les["id"]] = les["narration"]
    return out


def check(root: Path) -> list[str]:
    fails: list[str] = []
    table = _load(root / "research/derived/audio/audio_keys.json")
    want = plan.expected_keys(root, table.get("tier", "n5"))  # A5: raises on a collision
    for k in plan.TABLE_KINDS:
        if table.get(k) != want[k]:
            diff = {i for i in set(table.get(k) or {}) | set(want[k]) if (table.get(k) or {}).get(i) != want[k].get(i)}
            fails.append(f"A1 table {k}: {len(diff)} entries differ from the plan (e.g. {sorted(diff)[:3]}) — "
                         "run scripts/audio/build_audio_keys.py, then the exporters")
    got = exported(root)
    for k in JA_KINDS:
        w, g = want[k], got[k]
        for rid in sorted(set(w) - set(g))[:5]:
            fails.append(f"A2 {k} {rid}: no audio_key, plan has {w[rid]}")
        for rid in sorted(set(g) - set(w))[:5]:
            fails.append(f"A2 {k} {rid}: audio_key {g[rid][0]!r} the plan does not voice")
        n_miss, n_extra = len(set(w) - set(g)), len(set(g) - set(w))
        if n_miss > 5 or n_extra > 5:
            fails.append(f"A2 {k}: {n_miss} missing, {n_extra} extra in total")
        for rid in sorted(set(w) & set(g)):
            key, lang = g[rid]
            if not isinstance(key, str) or not plan.KEY_RE.match(key):
                fails.append(f"A4 {k} {rid}: malformed audio_key {key!r}")
            elif key != w[rid]:
                fails.append(f"A2 {k} {rid}: audio_key {key} != plan {w[rid]}")
            if lang != "ja":
                fails.append(f"A2 {k} {rid}: audio_lang {lang!r} != 'ja'")
    w, g = want["narration"], got["narration"]
    for lid in sorted(set(w) | set(g)):
        if w.get(lid) == g.get(lid):
            continue
        if lid not in g:
            fails.append(f"A3 {lid}: no narration[], plan has {len(w[lid])} units")
        elif lid not in w:
            fails.append(f"A3 {lid}: narration[] the plan does not voice")
        else:
            bad = next(i for i, (a, b) in enumerate(zip(w[lid] + [None], g[lid] + [None])) if a != b)
            fails.append(f"A3 {lid}: narration[{bad}] {g[lid][bad] if bad < len(g[lid]) else None} != plan "
                         f"{w[lid][bad] if bad < len(w[lid]) else None}")
        for e in g.get(lid) or []:
            if not plan.KEY_RE.match(str(e.get("audio_key"))):
                fails.append(f"A4 {lid}: malformed narration audio_key {e.get('audio_key')!r}")
                break
    return fails


# --------------------------------------------------------------------------- plant proof
FIXTURE = ["corpus/sentences/bank.json", "corpus/vocab", "corpus/grammar", "corpus/readings", "corpus/kanji",
           "corpus/kana", "corpus/exam_banks", "course", "scripts/audio/plan.py",
           "scripts/validate/validate_audio_keys.py", "research/derived/audio/audio_keys.json"]


def _edit(path: Path, fn) -> None:
    data = _load(path)
    fn(data)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")


def _first(records: list, pred):
    return next(r for r in records if pred(r))


def _flip(key: str) -> str:
    return ("a" if key[0] != "a" else "b") + key[1:]


def selftest() -> int:
    tmp = Path(tempfile.mkdtemp(prefix="audio_keys_plant_"))
    pristine = tmp.with_name(tmp.name + "_pristine")
    try:
        for rel in FIXTURE:
            src, dst = ROOT / rel, tmp / rel
            dst.parent.mkdir(parents=True, exist_ok=True)
            (shutil.copytree if src.is_dir() else shutil.copy2)(src, dst)
        table = _load(tmp / "research/derived/audio/audio_keys.json")
        les_id = next(iter(table["narration"]))
        les_path = next(Path(p) for p in glob.glob(str(tmp / "course/*/topic-*/lesson-*.json"))
                        if _load(Path(p))["id"] == les_id)
        turn_id = next(iter(table["listening"]))
        item_id, turn_i = turn_id.split("#script[")[0], int(turn_id.split("#script[")[1][:-1])
        bank_file = next(Path(p) for p in glob.glob(str(tmp / "corpus/exam_banks/*_listening_*.json"))
                         if any(it["id"] == item_id for it in _load(Path(p))))

        def sent(fn):
            return lambda: _edit(tmp / "corpus/sentences/bank.json", fn)

        def set_extra(d):
            _first(d, lambda r: "audio_key" not in r)["audio_key"] = "a" * 26

        def turn_text(d):
            it = _first(d, lambda x: x["id"] == item_id)
            it["script"][turn_i]["text"] = it["script"][turn_i]["text"] + "ね"

        def narr(fn):
            return lambda: _edit(les_path, fn)

        def body(d):
            d["body"] = d["body"].replace("<text>", "<text>Olá. ", 1)

        def reading(d):  # the verified reading of a kanji token is what gets spoken, so it is hashed
            r = _first(d, lambda x: x.get("audio_key") and any(plan.needs_reading(t["surface"]) for t in x["tokens"]))
            _first(r["tokens"], lambda t: plan.needs_reading(t["surface"]))["reading"] += "ア"

        def config():
            p = tmp / "scripts/audio/plan.py"
            p.write_text(p.read_text(encoding="utf-8").replace('"temperature": 0.8', '"temperature": 0.7', 1),
                         encoding="utf-8")

        plants = {
            "sentence key flipped": sent(lambda d: _first(d, lambda r: r.get("audio_key")).update(
                audio_key=_flip(_first(d, lambda r: r.get("audio_key"))["audio_key"]))),
            "sentence key removed": sent(lambda d: [r.pop(f) for r in [_first(d, lambda r: r.get("audio_key"))]
                                                    for f in ("audio_key", "audio_lang")]),
            "key on an unvoiced sentence": sent(set_extra),
            "vocab audio_lang wrong": lambda: _edit(tmp / "corpus/vocab/n5.json", lambda d: _first(
                d, lambda r: r.get("audio_key")).update(audio_lang="pt-BR")),
            "kana key upper-cased": lambda: _edit(tmp / "corpus/kana/hiragana.json", lambda d: _first(
                d, lambda r: r.get("audio_key")).update(audio_key=_first(d, lambda r: r.get("audio_key"))["audio_key"].upper())),
            "listening turn text drifted": lambda: _edit(bank_file, turn_text),
            "narration order swapped": narr(lambda d: d["narration"].insert(0, d["narration"].pop(1))),
            "narration span changed": narr(lambda d: d["narration"][0].update(span="999")),
            "narration dropped": narr(lambda d: d.pop("narration")),
            "lesson prose edited": narr(body),
            "sentence reading drifted": sent(reading),
            "table stale": lambda: _edit(tmp / "research/derived/audio/audio_keys.json", lambda d: d["vocab"].update(
                {next(iter(d["vocab"])): _flip(next(iter(d["vocab"].values())))})),
            "config param changed": config,
        }
        validator = tmp / "scripts/validate/validate_audio_keys.py"

        def run() -> tuple[int, str]:
            p = subprocess.run([sys.executable, str(validator)], capture_output=True, text=True, encoding="utf-8")
            out = (p.stdout + p.stderr).strip().splitlines()
            fail = next((ln for ln in out if "[FAIL]" in ln), out[-1] if out else "")
            return p.returncode, fail.strip()

        rc, last = run()
        ok = rc == 0
        print(f"control (untouched copy): {'PASS' if ok else 'FAIL'} — {last}")
        shutil.copytree(tmp, pristine)
        caught = 0
        for name, plant in plants.items():
            plant()
            rc, last = run()
            caught += rc != 0
            print(f"  plant {name!r}: {'caught' if rc else 'MISSED'} — {last[:140]}")
            shutil.rmtree(tmp)
            shutil.copytree(pristine, tmp)
        print(f"selftest: {caught}/{len(plants)} plants caught, control {'green' if ok else 'RED'}")
        return 0 if ok and caught == len(plants) else 1
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
        shutil.rmtree(pristine, ignore_errors=True)


def main() -> int:
    if "--selftest" in sys.argv:
        return selftest()
    fails = check(ROOT)
    t = _load(TABLE)
    n = {k: (sum(len(v) for v in t[k].values()) if k == "narration" else len(t[k])) for k in plan.TABLE_KINDS}
    for f in fails[:40]:
        print("  [FAIL]", f)
    if fails:
        print(f"audio keys: FAIL {len(fails)} — the export and scripts/audio/plan.py disagree")
        return 1
    print(f"audio keys: 0 FAIL — every exported key is the plan's (tier {t['tier']}: {n})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
