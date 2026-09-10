#!/usr/bin/env python3
"""Hard gate: the teacher's review views are current, and no filled review sheet is stranded. W38.

WHY THIS EXISTS
---------------
`research/reports/w38_tooling_report.md` §3 asked for exactly this gate and could not register it,
because `validate_all.py` was being edited by another unit at the time. Two assertions, each closing
a way the review loop quietly stops working:

  **A. The views are current.** `research/review/<registry>/<level>.md` is what a teacher actually
  reads. It is generated from the export by `scripts/export/build_review_views.py`, and every hash
  printed in it is the ledger's live anchor — so a stale view is not merely out of date, it hands
  the teacher anchors that no longer resolve and the sheets built from it are refused as stale. The
  check re-renders every view that is on disk and requires **byte** equality. The level list is
  derived from the files present, not hardcoded, so N4 and N3 views join this gate the day they are
  generated rather than the day someone remembers.

  **B. No sheet is stranded.** A filled `research/review/sheets/*.json` represents a teacher's
  afternoon. It is processed by `scripts/review_apply.py`, which puts approvals and rejections into
  the ledger and edits into a pending table. If nobody runs it, nothing anywhere says so. For every
  sheet carrying at least one verdict, this asserts that its verdicts LANDED: every approve/reject
  address is in `research/derived/review_ledger.json`, and every edit address appears in a table
  under `research/derived/pending/` or in an applied table under `research/derived/repairs/`.
  A blank sheet — what `--template` writes, and what the committed `EXEMPLO-*` sheet is — carries no
  verdict and is not a sheet yet, so it is skipped and SAID to be skipped.

  The pending directory is `research/derived/pending/`, not `research/derived/repairs/pending/`:
  the replay gate owns `repairs/` and fails on any unregistered table there (STATE aj), which is
  the correction W38's own report asked for and W31 applied.

  README.md and `research/review/sheets/**` are hand-written and are never compared against a
  render.

FALSIFIABILITY (plant proof on a copied tree carrying a copy of this validator AND of
`scripts/export/`, because a validator left importing the real repo reads the real tree and passes
falsely — memory: `validator-plant-proof-root`):

    python scripts/validate/validate_review_views.py --selftest

Usage:
    validate_review_views.py [--root PATH] [--selftest]
"""
from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
VIEWS_REL = "research/review"
SHEETS_REL = "research/review/sheets"
LEDGER_REL = "research/derived/review_ledger.json"
PENDING_REL = "research/derived/pending"
REPAIRS_REL = "research/derived/repairs"
MIN_VIEWS = 5


def address(entity, slug, field, locale) -> tuple:
    return (entity or "", slug or "", field or "", locale or "")


def check(root: Path) -> int:
    fails: list[str] = []
    views_dir = root / VIEWS_REL
    if not views_dir.is_dir():
        print(f"[FAIL] no review views under {views_dir}")
        return 1

    # ---- A. every view on disk re-renders byte-identical -------------------------------------
    on_disk = sorted(p for p in views_dir.rglob("*.md")
                     if p.parent.name != "sheets" and p.name != "README.md")
    if len(on_disk) < MIN_VIEWS:
        print(f"[FAIL] {len(on_disk)} review view(s) under {views_dir}, floor is {MIN_VIEWS} — an "
              f"empty or half-generated review tree must never pass")
        return 1
    # LEVELS come from the paths, so a level generated later joins this gate for free. REGISTRIES
    # come from the generator's own list, NOT from the directories present — otherwise deleting a
    # view deletes the check for it, and "the view is gone" is the loudest way for a review loop to
    # stop working. Asking for every registry at the levels on disk means a missing file is reported
    # as missing rather than quietly dropped from the cross product.
    sys.path.insert(0, str(root / "scripts" / "export"))
    import build_review_views                                                   # noqa: E402
    registries = sorted(build_review_views.REGISTRY_BY_NAME)
    levels = sorted({p.stem for p in on_disk})
    rc = build_review_views.main(["--root", str(root), "--check",
                                  "--registry", ",".join(registries),
                                  "--level", ",".join(levels)])
    if rc != 0:
        fails.append(f"{len(on_disk)} view(s) checked: at least one differs from a fresh render "
                     f"(the FAIL lines above name them). Run "
                     f"`python scripts/export/build_review_views.py --level {','.join(levels)}`")
    print(f"views: {len(on_disk)} file(s) over {len(registries)} registr(ies) "
          f"[{', '.join(registries)}] x {len(levels)} level(s) [{', '.join(levels)}]"
          + ("" if rc else " — every one byte-identical to a fresh render"))

    # ---- B. no filled sheet is stranded --------------------------------------------------------
    ledger_p = root / LEDGER_REL
    ledger: set[tuple] = set()
    if ledger_p.is_file():
        doc = json.loads(ledger_p.read_text(encoding="utf-8"))
        for e in doc.get("entries") or []:
            ledger.add(address(e.get("entity"), e.get("slug"), e.get("field"), e.get("locale")))

    tabled: set[tuple] = set()
    tables = 0
    for d in (root / PENDING_REL, root / REPAIRS_REL):
        if not d.is_dir():
            continue
        for p in sorted(d.glob("*.json")):
            try:
                doc = json.loads(p.read_text(encoding="utf-8"))
            except json.JSONDecodeError:
                continue
            rows = doc.get("rows") if isinstance(doc, dict) else doc
            if not isinstance(rows, list):
                continue
            tables += 1
            for r in rows:
                if isinstance(r, dict) and r.get("slug"):
                    tabled.add(address(r.get("entity"), r.get("slug"), r.get("field"),
                                       r.get("locale")))

    sheets = sorted((root / SHEETS_REL).glob("*.json")) if (root / SHEETS_REL).is_dir() else []
    filled = blank = 0
    for p in sheets:
        doc = json.loads(p.read_text(encoding="utf-8"))
        recs = doc.get("records") or []
        verdicts: list[tuple[str, tuple]] = []
        for rec in recs:
            slug = rec.get("id")
            entity = (slug or "").split(":", 1)[0]
            for addr in rec.get("approve") or []:
                verdicts.append(("ledger", _addr(entity, slug, addr)))
            for addr in (rec.get("reject") or {}):
                verdicts.append(("ledger", _addr(entity, slug, addr)))
            for addr in (rec.get("edit") or {}):
                verdicts.append(("table", _addr(entity, slug, addr)))
        if not verdicts:
            blank += 1
            continue
        filled += 1
        stranded = [(kind, a) for kind, a in verdicts
                    if (a not in ledger if kind == "ledger" else a not in tabled)]
        if stranded:
            fails.append(
                f"{p.relative_to(root).as_posix()}: {len(stranded)} of {len(verdicts)} verdict(s) "
                f"never landed — e.g. {stranded[0][1]} is in neither the ledger nor a table. Run "
                f"`python scripts/review_apply.py {p.relative_to(root).as_posix()}`")

    print(f"sheets: {len(sheets)} on disk — {filled} carrying verdicts, {blank} still blank "
          f"(a `--template` sheet is not a sheet yet); ledger {len(ledger)} address(es), "
          f"{tables} table(s) under pending/ + repairs/ holding {len(tabled)} address(es)")

    if fails:
        for f in fails:
            print(f"  [FAIL] {f}")
        print(f"[FAIL] {len(fails)} problem(s)")
        return 1
    print("[OK] every review view is current and no filled sheet is stranded")
    return 0


def _addr(entity: str, slug: str, addr: str) -> tuple:
    """`field@locale` (or a bare `field`, or `*`) -> the (entity, slug, field, locale) tuple the
    ledger and the repair tables both key on. `review_apply.py` builds the same tuple."""
    if "@" in addr:
        field, locale = addr.split("@", 1)
    else:
        field, locale = addr, ""
    return address(entity, slug, field, locale)


# ---------------------------------------------------------------------------------------------
def selftest() -> int:
    tmp = Path(tempfile.mkdtemp(prefix="yomi_views_plant_"))
    root = tmp / "tree"
    for rel in ("corpus", "course", "contracts", "research/review"):
        src = REPO / rel
        if src.is_dir():
            shutil.copytree(src, root / rel, ignore=shutil.ignore_patterns("__pycache__"))
    (root / "research" / "derived").mkdir(parents=True, exist_ok=True)
    for n in ("review_ledger.json",):
        if (REPO / "research" / "derived" / n).is_file():
            shutil.copy2(REPO / "research" / "derived" / n, root / "research" / "derived")
    # The WHOLE of scripts/ goes into the fixture. `build_review_views.py` imports `review_ledger`,
    # which imports `review_queue`, which imports further siblings; copying the transitive closure
    # by hand is a list that rots. Copying the tree is cheap and cannot be wrong, and it is what
    # makes the plant honest: the fixture's validator drives the fixture's generator over the
    # fixture's data, with nothing reaching back into the real repo.
    shutil.copytree(REPO / "scripts", root / "scripts",
                    ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
    shutil.copy2(__file__, root / "scripts" / "validate")
    vp = root / "scripts" / "validate" / Path(__file__).name

    def run() -> int:
        return subprocess.run([sys.executable, str(vp), "--root", str(root)],
                              capture_output=True, text=True, encoding="utf-8",
                              errors="replace").returncode

    def regen() -> None:
        """Rebuild the fixture's views with the fixture's own generator."""
        lv = sorted({p.stem for p in (root / VIEWS_REL).rglob("*.md")
                     if p.parent.name != "sheets" and p.name != "README.md"})
        subprocess.run([sys.executable, str(root / "scripts" / "export" / "build_review_views.py"),
                        "--root", str(root), "--level", ",".join(lv)],
                       capture_output=True, text=True, encoding="utf-8", errors="replace")

    ok = True

    def step(name: str, expect_fail: bool) -> None:
        nonlocal ok
        rc = run()
        good = (rc != 0) if expect_fail else (rc == 0)
        print(f"  {'PASS' if good else 'MISS'}  {name} (exit {rc})")
        ok = ok and good

    view = sorted(p for p in (root / VIEWS_REL).rglob("*.md")
                  if p.parent.name != "sheets" and p.name != "README.md")[0]
    original = view.read_text(encoding="utf-8")
    sheet = sorted((root / SHEETS_REL).glob("*.json"))[0]
    sheet_original = sheet.read_text(encoding="utf-8")

    print("selftest: control")
    step("control (unmutated copy) passes", False)

    print("selftest: plants")
    view.write_text(original.replace("|", "|", 1) + "\n", encoding="utf-8")
    step("one byte appended to a view is CAUGHT", True)
    view.write_text(original, encoding="utf-8")

    view.write_text(original.replace("a", "A", 1), encoding="utf-8")
    step("one character changed inside a view is CAUGHT", True)
    view.write_text(original, encoding="utf-8")

    view.unlink()
    step("a view deleted is CAUGHT", True)
    view.write_text(original, encoding="utf-8")

    doc = json.loads(sheet_original)
    doc["records"][0]["approve"] = [doc["records"][0]["_addresses"][0]]
    sheet.write_text(json.dumps(doc, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    step("a filled sheet with no matching ledger entry is CAUGHT", True)

    # ...and the same sheet stops being stranded once the entry exists. This is the half that keeps
    # the check honest: it must pass again when the work HAS been done, or it is not a gate, it is
    # a permanent failure nobody can clear.
    slug = doc["records"][0]["id"]
    addr = doc["records"][0]["_addresses"][0]
    field, _, locale = addr.partition("@")
    lp = root / LEDGER_REL
    led = json.loads(lp.read_text(encoding="utf-8")) if lp.is_file() else \
        {"schema_version": "1.0", "entries": []}
    entry = {"slug": slug, "entity": slug.split(":", 1)[0], "field": field,
             "content_hash": doc["records"][0]["record_hash"], "status": "approved",
             "reviewed_by": "plant", "approved_at": "2026-09-10"}
    if locale:
        entry["locale"] = locale
    led["entries"].append(entry)
    lp.write_text(json.dumps(led, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    # A ledger entry changes what the views PRINT — every view carries the record's review status
    # beside its live anchor — so the workflow rebuilds them. The coupling is the point: a teacher's
    # verdict that never reaches the view is a verdict the next sheet cannot be built against.
    regen()
    step("the same sheet passes once the ledger carries its verdict and the views are rebuilt",
         False)

    doc["records"][0]["edit"] = {addr: "texto novo do professor"}
    sheet.write_text(json.dumps(doc, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    step("an EDIT with no pending table is CAUGHT", True)

    (root / PENDING_REL).mkdir(parents=True, exist_ok=True)
    (root / PENDING_REL / "plant.json").write_text(json.dumps(
        {"rows": [{"entity": slug.split(":", 1)[0], "slug": slug, "field": field,
                   "locale": locale or None, "old": "x", "new": "texto novo do professor",
                   "why": "plant"}]}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    step("the edit stops being stranded once the pending table exists", False)

    sheet.write_text(sheet_original, encoding="utf-8")
    (root / PENDING_REL / "plant.json").unlink()
    lp.write_text(json.dumps({"schema_version": "1.0", "entries": []},
                             ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    regen()
    step("control again", False)

    for p in sorted((root / VIEWS_REL).rglob("*.md")):
        if p.parent.name != "sheets" and p.name != "README.md":
            p.unlink()
    step("a review tree with no views at all is CAUGHT (floor)", True)

    shutil.rmtree(tmp, ignore_errors=True)
    print("selftest: " + ("all plants caught" if ok else "A PLANT WAS MISSED"))
    return 0 if ok else 1


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", type=Path, default=REPO, help="tree to validate")
    ap.add_argument("--selftest", action="store_true", help="plant proof on a copied tree")
    args = ap.parse_args()
    if args.selftest:
        return selftest()
    return check(args.root.resolve())


if __name__ == "__main__":
    sys.exit(main())
