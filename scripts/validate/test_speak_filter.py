#!/usr/bin/env python3
"""W31 (A8) — the speaking path's content filter, proved on a fixture. Behaviour test + plant proof.

Two halves, because the filter has two halves.

**The mechanism** (`scripts/export/speak_filter.py`), against a hand-built fixture: the register
rules, the rule-name rule (〜なさい), the residue rule (NULL is never rounded up), and the blocklist
in every state it can be in — absent, empty, one entry by slug, one entry by substring, malformed.
The empty and absent cases matter most: the list is the OWNER'S (PENDING.md A8, "I build the
mechanism; the list is yours"), the file ships empty, and a mechanism that only works once someone
fills it in is a mechanism nobody can trust before they do.

**The gate**, end to end: `validate_speaking_path.py` re-run over a copied tree whose
`design/speak_blocklist.json` carries ONE entry naming a sentence a shipped unit actually uses. That
must FAIL. The fixture carries its own copy of the validator AND of `scripts/export/`, because a
validator left importing the real repo reads the real tree and passes falsely (that mistake has
already cost this project one invalid plant proof — see scripts/validate/README.md, "Falsifiability").

Exits 1 on any failure. No arguments, touches nothing outside a temp directory.
"""
from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
sys.path.insert(0, str(REPO / "scripts" / "export"))

FAILS: list[str] = []


def check(name: str, ok: bool, detail: str = "") -> None:
    print(f"  {'PASS' if ok else 'FAIL'}  {name}" + (f" — {detail}" if detail and not ok else ""))
    if not ok:
        FAILS.append(name)


def write_list(path: Path, entries: list) -> None:
    path.write_text(json.dumps({"what_this_is": "fixture", "entries": entries},
                               ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def mechanism(tmp: Path) -> None:
    from speak_filter import SpeakFilter, ALLOWED_REGISTERS, EXCLUDED_REGISTERS, EXCLUDED_RULES

    regs = {
        "sent:a": ("neutral", "plain-predicate"),
        "sent:b": ("polite", "polite-predicate"),
        "sent:c": ("casual", "soft-final"),
        "sent:d": ("formal", "keigo"),
        "sent:e": ("formal", "written-copula"),
        "sent:f": ("vulgar", "vulgar-lexeme"),
        "sent:g": ("archaic", "bungo-inflection"),
        "sent:h": ("dialect", "dialect-marker"),
        "sent:i": ("slang", "slang-lexeme"),
        "sent:j": (None, "no-signal"),
        "sent:k": ("polite", "polite-request-nasai"),
        "sent:l": ("epistolary", "epistolary-formula"),
    }
    texts = {"sent:a": "犬が走る", "sent:b": "これはペンです", "sent:c": "行くよ",
             "sent:d": "伺います", "sent:e": "犬は動物である", "sent:f": "ちくしょう",
             "sent:g": "心熱けれど肉体は弱し", "sent:h": "おおきに", "sent:i": "めっちゃいい",
             "sent:j": "調子はどう", "sent:k": "立ちなさい", "sent:l": "拝啓",
             "sent:m": "痔があります"}

    bl = tmp / "empty.json"
    write_list(bl, [])
    f = SpeakFilter(regs, texts, blocklist=bl)
    check("the three allowed registers pass with an empty blocklist",
          all(f.allows(s) for s in ("sent:a", "sent:b", "sent:c")))
    for slug, label in (("sent:d", "formal/keigo"), ("sent:e", "formal/written-copula"),
                        ("sent:f", "vulgar"), ("sent:g", "archaic"), ("sent:h", "dialect"),
                        ("sent:i", "slang"), ("sent:l", "epistolary")):
        check(f"{label} is excluded by rule", not f.allows(slug))
    check("register NULL (residue) is excluded, never rounded up to neutral", not f.allows("sent:j"))
    check("〜なさい is excluded by its RULE NAME while staying filed `polite`",
          not f.allows("sent:k") and regs["sent:k"][0] in ALLOWED_REGISTERS)
    check("a slug the corpus does not know is excluded, not admitted by default",
          not f.allows("sent:zz"))
    check("the census reports every exclusion", len(f.rejected_slugs) == 10,
          f"{len(f.rejected_slugs)} rejected")
    check("the rule vocabulary is the one the schema names",
          set(EXCLUDED_REGISTERS) == {"vulgar", "slang", "dialect", "archaic", "epistolary",
                                      "formal"}
          and set(EXCLUDED_RULES) == {"polite-request-nasai"})

    missing = tmp / "does-not-exist.json"
    f2 = SpeakFilter(regs, texts, blocklist=missing)
    check("an ABSENT blocklist reads as empty and the register rules still apply",
          f2.allows("sent:a") and not f2.allows("sent:f") and f2.entries == [])

    one = tmp / "one_slug.json"
    write_list(one, [{"sentence": "sent:a", "why": "fixture: one entry, by slug"}])
    f3 = SpeakFilter(regs, texts, blocklist=one)
    check("ONE entry by slug excludes exactly that sentence",
          not f3.allows("sent:a") and f3.allows("sent:b") and f3.allows("sent:c"))
    check("the blocklist reason reaches the caller",
          "one entry, by slug" in (f3.reject_reason("sent:a") or ""))

    sub = tmp / "one_sub.json"
    write_list(sub, [{"contains": "痔", "why": "fixture: a topic, not a sentence"}])
    regs2 = dict(regs, **{"sent:m": ("polite", "polite-predicate")})
    f4 = SpeakFilter(regs2, texts, blocklist=sub)
    check("ONE entry by substring excludes every sentence carrying it",
          not f4.allows("sent:m") and f4.allows("sent:b"))

    bad = tmp / "bad.json"
    bad.write_text(json.dumps({"entries": [{"sentence": "sent:a"}]}), encoding="utf-8")
    try:
        SpeakFilter(regs, texts, blocklist=bad)
        check("an entry with no `why` is refused", False, "it was accepted")
    except SystemExit:
        check("an entry with no `why` is refused", True)
    bad.write_text(json.dumps(["sent:a"]), encoding="utf-8")
    try:
        SpeakFilter(regs, texts, blocklist=bad)
        check("a malformed blocklist is refused, never read as empty", False, "it was accepted")
    except SystemExit:
        check("a malformed blocklist is refused, never read as empty", True)

    real = json.loads((REPO / "design" / "speak_blocklist.json").read_text(encoding="utf-8"))
    check("the shipped design/speak_blocklist.json is valid and EMPTY (the list is the owner's)",
          isinstance(real.get("entries"), list) and real["entries"] == [],
          f"{len(real.get('entries') or [])} entries")


def gate_plant(tmp: Path) -> None:
    """One blocklist entry naming a sentence a shipped unit uses -> validate_speaking_path FAILS."""
    root = tmp / "tree"
    (root / "corpus").mkdir(parents=True)
    for d in ("sentences", "vocab", "grammar", "exam_banks"):
        shutil.copytree(REPO / "corpus" / d, root / "corpus" / d)
    shutil.copytree(REPO / "course" / "speak", root / "course" / "speak")
    # The validator and everything it imports live INSIDE the fixture, or the plant reads the real
    # repo and passes falsely (memory: validator-plant-proof-root).
    shutil.copytree(REPO / "scripts" / "export", root / "scripts" / "export",
                    ignore=shutil.ignore_patterns("__pycache__"))
    (root / "scripts" / "validate").mkdir(parents=True)
    shutil.copy2(REPO / "scripts" / "validate" / "validate_speaking_path.py",
                 root / "scripts" / "validate")
    (root / "design").mkdir()
    vp = root / "scripts" / "validate" / "validate_speaking_path.py"
    blp = root / "design" / "speak_blocklist.json"

    def run() -> int:
        return subprocess.run([sys.executable, str(vp), "--root", str(root)],
                              capture_output=True, text=True, encoding="utf-8",
                              errors="replace").returncode

    write_list(blp, [])
    check("control: the shipped tree passes with an empty blocklist", run() == 0)

    course = json.loads((root / "course" / "speak" / "course.json").read_text(encoding="utf-8"))
    st = course["stages"][0]
    key = st["slug"].split(":", 1)[1]
    n = int(st["unit_ids"][0].rsplit("-", 1)[1])
    unit = json.loads((root / "course" / "speak" / key / f"unit-{n:02d}.json")
                      .read_text(encoding="utf-8"))
    victim = unit["say_now"][0]
    write_list(blp, [{"sentence": victim, "why": "fixture: one entry, naming a shipped phrase"}])
    check(f"ONE blocklist entry naming a shipped say_now phrase ({victim}) is CAUGHT", run() != 0)

    bank = {s["slug"]: s for s in
            json.loads((root / "corpus" / "sentences" / "bank.json").read_text(encoding="utf-8"))}
    jp = bank[victim]["jp"]
    write_list(blp, [{"contains": jp[:4], "why": "fixture: a substring of a shipped phrase"}])
    check(f"ONE substring entry matching a shipped phrase ({jp[:4]}) is CAUGHT", run() != 0)

    write_list(blp, [])
    check("control again, after the entries are removed", run() == 0)

    # And the register half of the gate: hand-edit a shipped sentence's register to a value the
    # path may not carry. The builder is not re-run, so only the gate can catch this.
    bankp = root / "corpus" / "sentences" / "bank.json"
    recs = json.loads(bankp.read_text(encoding="utf-8"))
    for r in recs:
        if r["slug"] == victim:
            r["register"], r["register_rule"] = "vulgar", "vulgar-lexeme"
    bankp.write_text(json.dumps(recs, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    check("a shipped phrase re-labelled `vulgar` is CAUGHT", run() != 0)


def main() -> int:
    tmp = Path(tempfile.mkdtemp(prefix="yomi_speakfilter_"))
    try:
        print("mechanism (scripts/export/speak_filter.py):")
        mechanism(tmp)
        print("gate plant (validate_speaking_path.py on a copied tree):")
        gate_plant(tmp)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    if FAILS:
        print(f"[FAIL] {len(FAILS)} case(s): {FAILS}")
        return 1
    print("[OK] speak content filter: mechanism and gate both proved, blocklist works empty")
    return 0


if __name__ == "__main__":
    sys.exit(main())
