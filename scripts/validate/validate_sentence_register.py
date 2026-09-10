#!/usr/bin/env python3
"""Hard gate: `sentence.register` is exactly what the derivation produces on the tree being validated.

WHY THIS EXISTS
---------------
`register` is the field the speaking path filters on (PENDING.md A8, design/schema_v2.md
`sentence.register`). A wrong value there is not a cosmetic defect: `neutral` on a vulgar sentence
puts it in a production prompt, and `null` rounded up to `neutral` does the same thing silently —
which is why the field is nullable in the first place. So the value cannot be allowed to become
free-standing data that someone edits by hand, or that a later ingest writes with a different rule.

The derivation (`scripts/derive_sentence_register_v2.py`) is deterministic and costs about a second
over the whole bank, so this validator simply RE-DERIVES and compares. It is the same contract
`validate_lesson_gating.py` check C4 puts on `needs[]`: the stored edge must be exactly what the
builder derives from the tree being validated, so the field cannot drift from the rule it came from.

WHAT IT CHECKS
--------------
Reads the committed export (`corpus/sentences/bank.json`), never `db/corpus.sqlite`.

  A  ENUM. Every sentence carries a `register_rule` from the closed set below and a `register` that
     is either NULL or one of the nine D7 values. `register` is NULL **if and only if** the rule is
     `no-signal` — a rule with no value, or a value with no rule, means one of the two writers ran
     and the other did not.

  B  DERIVATION. `derive_sentence_register_v2.py --root <the tree being validated>` is run over that
     tree's own bank and grammar registry, and every sentence's stored (register, register_rule)
     must equal what comes back. Note what this covers beyond a hand edit: the derivation reads
     `corpus/grammar/*.json`, so changing a grammar point's `register` and NOT re-deriving fails
     here — the exact coupling W31's own apply had to sequence by hand.

  C  RESIDUE RATCHET. The count of NULL registers, per level, against
     `scripts/validate/sentence_register_baseline.json`. SHRINK-ONLY: a level may lose residue
     (someone authored a value, or a fragment gained a predicate) and may never gain it. Growth is
     a failure, and so is a level appearing that the baseline does not know. `--record` re-records
     it, and a re-record is a deliberate act that belongs in a report with its cause.

  FLOOR. Fewer than MIN_SENTENCES sentences, or a bank with no register at all, FAILS. An empty or
  half-exported tree must never pass (scripts/validate/README.md, "empty input FAILS").

WHAT IT DOES NOT CHECK
----------------------
That the tracked table `research/derived/repairs/sentence_register.json` matches the export — that
is `validate_repairs_applied.py`'s job, and two gates re-implementing one rule is a defect this
suite has already paid for once (README, "two gates disagreeing about the same rows").

FALSIFIABILITY (plant proof, run on a copied tree carrying copies of this validator AND both
`derive_sentence_register*.py`, because a validator left importing the real repo reads the real tree
and passes falsely):

    python scripts/validate/validate_sentence_register.py --selftest

Usage:
    validate_sentence_register.py [--root PATH] [--all] [--record] [--selftest]
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
from collections import Counter
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
BASELINE = HERE / "sentence_register_baseline.json"
MAX_REPORT = 25
MIN_SENTENCES = 5000

D7 = ("neutral", "polite", "casual", "formal", "vulgar", "archaic", "epistolary", "dialect", "slang")
# design/schema_v2.md `sentence.register_rule`. Locale-neutral, closed; a new rule name joins the
# schema and this tuple in the same change, never one of them alone.
RULES = (
    "plain-predicate", "polite-predicate", "polite-request", "polite-request-nasai",
    "polite-nonfinal", "polite-set-phrase", "soft-final", "casual-marker", "grammar-register",
    "keigo", "written-copula", "bungo-inflection", "classical-final", "jmdict-arch", "jmdict-vulg",
    "vulgar-lexeme", "rough-address", "jmdict-dialect", "dialect-marker", "jmdict-slang",
    "slang-lexeme", "epistolary-formula", "no-signal",
)


def die(msg: str) -> int:
    print(f"[FAIL] {msg}")
    return 1


def load_bank(root: Path) -> list[dict]:
    p = root / "corpus" / "sentences" / "bank.json"
    if not p.exists():
        raise SystemExit(f"[FAIL] no sentence bank at {p}")
    recs = json.loads(p.read_text(encoding="utf-8"))
    if not isinstance(recs, list) or not recs:
        raise SystemExit(f"[FAIL] {p} carries no sentences — empty input must never pass")
    return recs


def rederive(root: Path, derive: Path, cache: str | None) -> dict[str, tuple]:
    """{slug: (register, rule)} from a fresh derivation over `root`. Bank only."""
    out = Path(tempfile.mkdtemp(prefix="yomi_reg_")) / "derived.json"
    cmd = [sys.executable, str(derive), "--root", str(root), "--out", str(out),
           "--skip-w13", "--quiet"]
    if cache:
        cmd += ["--jmdict-cache", cache]
    r = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
    if r.returncode != 0 or not out.exists():
        raise SystemExit(f"[FAIL] the derivation would not run over {root}:\n"
                         f"{(r.stderr or r.stdout or '').strip()[:2000]}")
    doc = json.loads(out.read_text(encoding="utf-8"))
    shutil.rmtree(out.parent, ignore_errors=True)
    return {x["key"]: (x["register"], x["rule"]) for x in doc["rows"] if x["set"] == "bank"}


def check(root: Path, show_all: bool, record: bool, cache: str | None) -> int:
    bank = load_bank(root)
    print(f"bank: {len(bank)} sentences (root {root})")
    if len(bank) < MIN_SENTENCES:
        return die(f"{len(bank)} sentences, floor is {MIN_SENTENCES}")

    fails: list[str] = []
    classes: Counter = Counter()

    def fail(cls: str, msg: str) -> None:
        classes[cls] += 1
        if show_all or classes[cls] <= MAX_REPORT:
            fails.append(f"  [{cls}] {msg}")

    # ---- A. enum ------------------------------------------------------------------------------
    have_any = 0
    for s in bank:
        slug = s.get("slug")
        if "register" not in s or "register_rule" not in s:
            fail("field-absent", f"{slug}: the export carries no register/register_rule field")
            continue
        reg, rule = s["register"], s["register_rule"]
        if reg is not None:
            have_any += 1
        if reg is not None and reg not in D7:
            fail("register-not-in-D7", f"{slug}: register {reg!r} is not one of {D7}")
        if rule not in RULES:
            fail("rule-not-in-enum", f"{slug}: register_rule {rule!r} is not a known rule name")
        if (reg is None) != (rule == "no-signal"):
            fail("null-rule-mismatch",
                 f"{slug}: register {reg!r} with rule {rule!r} — NULL and `no-signal` are the same "
                 f"claim and must agree")
    if not have_any:
        return die("no sentence in the export carries a register — empty input must never pass")

    # ---- B. the derivation --------------------------------------------------------------------
    derive = root / "scripts" / "derive_sentence_register_v2.py"
    if not derive.exists():
        derive = REPO / "scripts" / "derive_sentence_register_v2.py"
    derived = rederive(root, derive, cache)
    print(f"        re-derived {len(derived)} rows with {derive}")
    missing = [s["slug"] for s in bank if s.get("slug") not in derived]
    if missing:
        fail("not-derivable", f"{len(missing)} sentence(s) the derivation does not produce a row "
                              f"for, e.g. {missing[:3]}")
    for s in bank:
        slug = s.get("slug")
        if slug not in derived or "register_rule" not in s:
            continue
        want = derived[slug]
        got = (s["register"], s["register_rule"])
        if got != want:
            fail("derivation-mismatch",
                 f"{slug}: stored {got[0]!r}/{got[1]!r}, the derivation on this tree says "
                 f"{want[0]!r}/{want[1]!r} — {s.get('jp', '')[:40]}")

    # ---- C. residue ratchet -------------------------------------------------------------------
    residue: Counter = Counter()
    for s in bank:
        if s.get("register") is None and "register" in s:
            residue[s.get("level") or "?"] += 1
    total = sum(residue.values())
    if record:
        BASELINE.write_text(json.dumps(
            {"what_this_is": "W31. Sentences with no mechanical register signal (register NULL, "
                             "rule `no-signal`), per level. SHRINK-ONLY: a level may lose residue "
                             "and may never gain it. Re-record only with a stated cause in a "
                             "report — scripts/validate/README.md.",
             "total": total, "per_level": dict(sorted(residue.items()))},
            ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(f"        recorded residue baseline: {total} ({dict(sorted(residue.items()))})")
    elif BASELINE.exists():
        base = json.loads(BASELINE.read_text(encoding="utf-8"))["per_level"]
        for lv, n in sorted(residue.items()):
            b = base.get(lv)
            if b is None:
                fail("residue-level-unknown",
                     f"level {lv!r} has {n} residue sentence(s) and is not in the baseline")
            elif n > b:
                fail("residue-grew", f"level {lv}: {n} residue sentences, baseline {b} — the "
                                     f"ratchet is shrink-only")
        shrunk = {lv: (base[lv], residue.get(lv, 0)) for lv in base
                  if residue.get(lv, 0) < base[lv]}
        print(f"        residue {total} (baseline {sum(base.values())})"
              + (f"; SHRUNK at {shrunk} — re-record with --record" if shrunk else ""))
    else:
        return die(f"no residue baseline at {BASELINE} — run once with --record")

    if fails:
        print("\n".join(fails))
        more = {c: n for c, n in classes.items() if n > MAX_REPORT and not show_all}
        if more:
            print(f"  ... {more} further failure(s) not shown (--all)")
        return die(f"{sum(classes.values())} problem(s) across {len(classes)} class(es): "
                   f"{dict(classes)}")
    dist = Counter((s.get("register") or "null") for s in bank)
    print(f"[OK] register + register_rule agree with the derivation on every sentence; "
          f"{dict(dist.most_common())}")
    return 0


# ---------------------------------------------------------------------------------------------
def selftest() -> int:
    """Plant violations in a copied tree and require each to be caught."""
    cache = os.path.join(tempfile.gettempdir(), "yomineko_jmdict_misc.json")
    tmp = Path(tempfile.mkdtemp(prefix="yomi_reg_plant_"))
    root = tmp / "tree"
    (root / "corpus" / "sentences").mkdir(parents=True)
    (root / "corpus" / "grammar").mkdir(parents=True)
    (root / "scripts" / "validate").mkdir(parents=True)
    shutil.copy2(REPO / "corpus" / "sentences" / "bank.json", root / "corpus" / "sentences")
    for p in (REPO / "corpus" / "grammar").glob("*.json"):
        shutil.copy2(p, root / "corpus" / "grammar")
    # The validator AND the scripts it drives are copied into the fixture. A validator left reading
    # the real repo passes falsely (memory: validator-plant-proof-root).
    shutil.copy2(__file__, root / "scripts" / "validate")
    for n in ("derive_sentence_register.py", "derive_sentence_register_v2.py"):
        shutil.copy2(REPO / "scripts" / n, root / "scripts")
    shutil.copy2(BASELINE, root / "scripts" / "validate" / BASELINE.name)
    vp = root / "scripts" / "validate" / Path(__file__).name
    bankp = root / "corpus" / "sentences" / "bank.json"
    original = bankp.read_text(encoding="utf-8")
    gram = {p.name: p.read_text(encoding="utf-8") for p in (root / "corpus" / "grammar").glob("*.json")}

    def run() -> int:
        r = subprocess.run([sys.executable, str(vp), "--root", str(root),
                            "--jmdict-cache", cache],
                           capture_output=True, text=True, encoding="utf-8", errors="replace")
        return r.returncode

    def restore() -> None:
        bankp.write_text(original, encoding="utf-8")
        for n, t in gram.items():
            (root / "corpus" / "grammar" / n).write_text(t, encoding="utf-8")

    def mutate(fn) -> None:
        recs = json.loads(original)
        fn(recs)
        bankp.write_text(json.dumps(recs, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    ok = True

    def step(name: str, expect_fail: bool) -> None:
        nonlocal ok
        rc = run()
        good = (rc != 0) if expect_fail else (rc == 0)
        print(f"  {'PASS' if good else 'MISS'}  {name} (exit {rc})")
        ok = ok and good

    print("selftest: control")
    step("control (unmutated copy) passes", False)

    def first_with(recs, pred):
        return next(r for r in recs if pred(r))

    print("selftest: plants")
    mutate(lambda rs: first_with(rs, lambda r: r["register"] == "casual").__setitem__("register", "neutral"))
    step("a casual sentence re-labelled neutral is CAUGHT", True)
    restore()

    mutate(lambda rs: rs[0].__setitem__("register", "informal"))
    step("a value outside the D7 set is CAUGHT", True)
    restore()

    mutate(lambda rs: rs[0].__setitem__("register_rule", "vibes"))
    step("a rule name outside the enum is CAUGHT", True)
    restore()

    mutate(lambda rs: first_with(rs, lambda r: r["register"] is None).__setitem__("register", "neutral"))
    step("residue rounded up to neutral is CAUGHT", True)
    restore()

    mutate(lambda rs: first_with(rs, lambda r: r["register"] is not None).__setitem__("register", None))
    step("a value blanked (residue grows) is CAUGHT", True)
    restore()

    mutate(lambda rs: [r.pop("register_rule", None) for r in rs])
    step("the field dropped from every record is CAUGHT", True)
    restore()

    mutate(lambda rs: rs.__setitem__(slice(None), rs[:10]))
    step("a bank cut to 10 sentences is CAUGHT (floor)", True)
    restore()

    # The coupling that matters: change a grammar point's register and do NOT re-derive. The point
    # has to be one that actually DECIDES a sentence — the promotion only fires where the predicate
    # said nothing (rule `grammar-register`), so editing a point nothing hangs on proves nothing.
    deciders: set[str] = set()
    tbl = REPO / "research" / "derived" / "repairs" / "sentence_register.json"
    if tbl.exists():
        for r in json.loads(tbl.read_text(encoding="utf-8"))["rows"]:
            if r.get("set") == "bank" and r.get("rule") == "grammar-register":
                for sig in r.get("signals") or []:
                    if sig.startswith("grammar register "):
                        deciders.add(sig[len("grammar register "):].split("=")[0])
    changed = None
    for n, t in gram.items():
        recs = json.loads(t)
        for it in recs:
            if it.get("key") in deciders:
                it["register"] = ["polite"]
                changed = it.get("key")
                break
        if changed:
            (root / "corpus" / "grammar" / n).write_text(
                json.dumps(recs, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            break
    if changed:
        step(f"grammar point {changed!r} re-tagged without re-deriving is CAUGHT", True)
    else:
        ok = False
        print("  MISS  no grammar point decides a sentence in this fixture — the coupling plant "
              "could not be built, which is itself a finding")
    restore()

    step("control again", False)
    shutil.rmtree(tmp, ignore_errors=True)
    print("selftest: " + ("all plants caught" if ok else "A PLANT WAS MISSED"))
    return 0 if ok else 1


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", type=Path, default=REPO, help="tree to validate")
    ap.add_argument("--all", action="store_true", help="print every failure, not the first "
                                                       f"{MAX_REPORT} per class")
    ap.add_argument("--record", action="store_true", help="re-record the residue baseline")
    ap.add_argument("--jmdict-cache", default=None)
    ap.add_argument("--selftest", action="store_true", help="plant proof on a copied tree")
    args = ap.parse_args()
    if args.selftest:
        return selftest()
    return check(args.root.resolve(), args.all, args.record, args.jmdict_cache)


if __name__ == "__main__":
    sys.exit(main())
