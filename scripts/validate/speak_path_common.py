#!/usr/bin/env python3
"""Loaders shared by the three W34 speaking-path gates (strands / spiral / near-duplicates).

Each of `validate_speak_strands.py`, `validate_speak_spiral.py` and `validate_speak_duplicates.py`
walks the same two artifacts — `course/speak/course.json` plus its unit leaves, and the exported
sentence bank — so the walk lives here once. Three copies of it would drift, and the first thing to
drift would be "which units exist", which is the denominator every one of the three ratchets is
measured against.

Two rules this module exists to hold:

  * **The units are enumerated from `course.json`, never from a directory glob.** An orphan
    `unit-*.json` on disk that no stage references is already a hard failure in
    `validate_speaking_path.py`; re-walking the glob here would silently let one into three more
    denominators and quietly move every ratchet.
  * **A missing tree is a failure, not a pass.** `validate_speaking_path.py` returns 0 when
    `course/speak` is absent ("not built"), which is the one shape scripts/validate/README.md calls
    out: a gate whose data vanished must fail rather than certify nothing. `load_course()` raises,
    and each caller reports it as a hard FAIL.

`builder_module()` imports `scripts/export/build_speaking_path.py` for the stage seed lexicons and
R86's punctuation class. That import is deliberate and is the same precedent
`validate_speaking_path.py` set with `pattern_forms`: `design/speaking_path.md` §5 says outright that
the "full seed lexicons live in the builder, not here, so they stay executable rather than drifting
from the prose", so a validator that retyped them would be asserting against its own copy. It is
resolved relative to THIS file rather than `--root`, because `--root` points at a tree under test — a
plant fixture copies this module and must copy `scripts/export/build_speaking_path.py`,
`scripts/export/pattern_forms.py` and `scripts/dbtarget.py` with it.

The import is argv-guarded: `build_speaking_path` evaluates `db_target(...)` at module scope, and
`scripts/dbtarget.py::take_flag` DELETES `--db` / `--out-root` from `sys.argv` in place as a side
effect of that call. Harmless for a validator that declares neither flag, but a validator whose argv
is edited by an import is a trap, so the import runs against a stub argv.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from types import ModuleType

REPO = Path(__file__).resolve().parents[2]
EXPORT_DIR = Path(__file__).resolve().parents[1] / "export"

# design/learning_science.md R77: "tag every unit component with strand ∈ {meaning-input,
# meaning-output, language-focused, fluency}".
STRANDS = ("meaning-input", "meaning-output", "language-focused", "fluency")


def jload(path: Path) -> object:
    return json.loads(path.read_text(encoding="utf-8"))


def load_course(root: Path) -> dict:
    """`course/speak/course.json`. Raises when the path is not built — see the module docstring."""
    p = root / "course" / "speak" / "course.json"
    if not p.exists():
        raise FileNotFoundError(f"{p} does not exist — the speaking path is not built in this tree")
    course = jload(p)
    if not isinstance(course, dict) or not course.get("stages"):
        raise ValueError(f"{p} declares no stages")
    return course


def iter_units(root: Path, course: dict) -> list[dict]:
    """[{stage, order, id, unit}] in course order, one entry per unit_id `course.json` declares.

    A declared unit whose file is missing raises: a gate that silently skipped it would measure a
    smaller path and every ratchet under it would read as an improvement.
    """
    speak = root / "course" / "speak"
    out: list[dict] = []
    for stage in course["stages"]:
        slug = stage["slug"].split(":", 1)[1]
        for uid in stage["unit_ids"]:
            n = int(uid.rsplit("-", 1)[1])
            p = speak / slug / f"unit-{n:02d}.json"
            if not p.exists():
                raise FileNotFoundError(f"{uid}: {p} is declared by course.json and missing")
            out.append({"stage": slug, "order": int(stage["order"]), "id": uid, "unit": jload(p)})
    return out


def load_sentences(root: Path) -> dict[str, dict]:
    """Every exported bank sentence by slug. The export is the source of truth (CLAUDE.md)."""
    sentences: dict[str, dict] = {}
    for p in sorted((root / "corpus" / "sentences").rglob("*.json")):
        data = jload(p)
        if not isinstance(data, list):
            continue
        for s in data:
            if isinstance(s, dict) and s.get("slug"):
                sentences[s["slug"]] = s
    return sentences


_BUILDER: ModuleType | None = None


def builder_module() -> ModuleType:
    """`scripts/export/build_speaking_path.py`, imported for STAGES / SURVIVAL_SEEDS / PUNCT_RE."""
    global _BUILDER
    if _BUILDER is not None:
        return _BUILDER
    if str(EXPORT_DIR) not in sys.path:
        sys.path.insert(0, str(EXPORT_DIR))
    saved = sys.argv[:]
    sys.argv = [saved[0] if saved else "validator"]
    try:
        import build_speaking_path  # noqa: PLC0415  (deliberately late and argv-guarded)
    finally:
        sys.argv = saved
    _BUILDER = build_speaking_path
    return _BUILDER


def stage_seeds() -> dict[str, tuple[str, ...]]:
    """{stage slug: seed lexicon} straight out of the builder's STAGES table."""
    return {slug: seeds for slug, _title, _band, seeds in builder_module().STAGES}


def seed_hit(sentence: dict, terms) -> bool:
    """The builder's own scenario-match rule, re-run over the EXPORT.

    `design/speaking_path.md` §3.2: a seed must match a whole token's LEMMA; seeds of 4+ characters
    may also match as a substring, which is how frozen expressions the analyzer shreds (すみません →
    すみ+ませ+ん) still find their sentences. Matching the SURFACE instead was tried twice and shipped
    both times — raw substring put 夕食はいりません in greetings on the seed はい, and surface matching
    put three footwear sentences there because 履く's te-form tokenises to the surface はい.
    """
    if not sentence:
        return False
    lemmas = {t.get("lemma") for t in (sentence.get("tokens") or [])}
    jp = sentence.get("jp") or ""
    return any(k in lemmas or (len(k) >= 4 and k in jp) for k in terms)


def write_if_changed(path: Path, payload: object) -> bool:
    """Rewrite a work list only on a real content change — a file whose mtime moves every run is
    noise in every diff, and the reader cannot tell a new entry from a re-serialisation."""
    text = json.dumps(payload, ensure_ascii=False, indent=2) + "\n"
    if path.exists() and path.read_text(encoding="utf-8") == text:
        return False
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return True
