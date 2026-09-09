#!/usr/bin/env python3
"""Behaviour cases for `scripts/review_apply.py` — the teacher-verdict flow-back (W38).

Every case runs the real CLI as a subprocess against a FIXTURE TREE built in a temp directory from
records copied out of the live export, with `--root` and `--review-ledger` pointed at the fixture.
The committed ledger is never written and the committed corpus is never read for output: a test
that shares a ledger with the project cannot tell "the script recorded the approval" from "somebody
else's approval was already there" (memory: validator plant-proof root).

CASES
  1  template        `--template grammar n5` emits one row per record with a record hash and the
                     exact address list the view offers
  2  approve         one approval becomes one ledger entry, anchored to `live_anchor`
  3  idempotent      the same sheet twice adds nothing the second time
  4  edit            an edit becomes a repair row under research/derived/repairs/pending/ carrying
                     the EXACT current text as `old`, and nothing enters the ledger
  5  reject          a rejection is a ledger entry with status `rejected` and the reason as its note
  6  stale hash      a record rewritten under the teacher refuses the WHOLE sheet: exit 2, ledger
                     byte-identical, no table
  7  unknown id      an id no record carries refuses the sheet: exit 2, nothing written
  8  no DB           the run leaves `db/corpus.sqlite` untouched and creates nothing at $YOMINEKO_DB
  9  gate            `validate_review_ledger.py --root <fixture>` is green over what case 2 and 5
                     wrote — an entry this script produces can never be *unresolvable*

Usage: test_review_apply.py   — exits non-zero on any failure.
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "scripts"))
from review_ledger import live_anchor  # noqa: E402

REVIEW_APPLY = REPO / "scripts" / "review_apply.py"
LEDGER_REL = "research/derived/review_ledger.json"
PENDING_REL = "research/derived/repairs/pending"
EMPTY_LEDGER = {"schema_version": "1.0",
                "note": "fixture ledger for test_review_apply.py", "entries": []}


# --------------------------------------------------------------------------------------------------
def build_fixture(tmp: Path) -> tuple[Path, list[dict[str, Any]], dict[str, Any]]:
    """A tree with three real grammar records and one real sentence. Real records, because a
    hand-written stub would let a shape change in the export pass this test unnoticed."""
    root = tmp / "tree"
    (root / "corpus" / "grammar").mkdir(parents=True)
    (root / "corpus" / "sentences").mkdir(parents=True)
    (root / "research" / "derived").mkdir(parents=True)
    (root / "contracts").mkdir(parents=True)

    grammar = json.loads((REPO / "corpus" / "grammar" / "n5.json").read_text(encoding="utf-8"))[:3]
    (root / "corpus" / "grammar" / "n5.json").write_text(
        json.dumps(grammar, ensure_ascii=False, indent=1), encoding="utf-8")

    bank = json.loads((REPO / "corpus" / "sentences" / "bank.json").read_text(encoding="utf-8"))[:1]
    (root / "corpus" / "sentences" / "bank.json").write_text(
        json.dumps(bank, ensure_ascii=False, indent=1), encoding="utf-8")

    shutil.copy2(REPO / "contracts" / "manifest.json", root / "contracts" / "manifest.json")
    write_ledger(root, EMPTY_LEDGER)
    return root, grammar, bank[0]


def write_ledger(root: Path, payload: dict[str, Any]) -> None:
    (root / LEDGER_REL).write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
                                   encoding="utf-8")


def read_ledger(root: Path) -> dict[str, Any]:
    return json.loads((root / LEDGER_REL).read_text(encoding="utf-8"))


def rec_hash(rec: dict[str, Any]) -> str:
    anchor, _how = live_anchor(rec, "*", None)
    return str(anchor)


def sheet_path(root: Path, name: str, payload: dict[str, Any]) -> Path:
    path = root / "sheets" / f"{name}.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def run(root: Path, *args: str, db_probe: Path | None = None) -> subprocess.CompletedProcess:
    env = dict(os.environ)
    env["PYTHONIOENCODING"] = "utf-8"
    if db_probe is not None:
        # Any sqlite3.connect() on the default target would create this file. It must not exist
        # afterwards: this script is not a DB writer and must never become one by accident.
        env["YOMINEKO_DB"] = str(db_probe)
    return subprocess.run(
        [sys.executable, str(REVIEW_APPLY), "--root", str(root),
         "--review-ledger", str(root / LEDGER_REL), *args],
        capture_output=True, text=True, encoding="utf-8", env=env, cwd=str(REPO))


# --------------------------------------------------------------------------------------------------
def main() -> int:
    fails: list[str] = []

    def check(name: str, ok: bool, detail: str = "") -> None:
        if not ok:
            fails.append(f"{name}: {detail}")

    with tempfile.TemporaryDirectory(prefix="w38-review-apply-") as tmpdir:
        tmp = Path(tmpdir)
        root, grammar, sentence = build_fixture(tmp)
        target = grammar[0]
        slug = target["slug"]
        db_probe = tmp / "never-created.sqlite"
        real_db = REPO / "db" / "corpus.sqlite"
        db_before = (real_db.stat().st_size, real_db.stat().st_mtime_ns) if real_db.is_file() else None

        # --- 1: template -------------------------------------------------------------------------
        out = run(root, "--template", "grammar", "n5", "--out", str(root / "sheets" / "tpl.json"),
                  db_probe=db_probe)
        check("1 template", out.returncode == 0, out.stderr or out.stdout)
        tpl_path = root / "sheets" / "tpl.json"
        if tpl_path.is_file():
            tpl = json.loads(tpl_path.read_text(encoding="utf-8"))
            check("1 template rows", len(tpl["records"]) == 3, f"{len(tpl['records'])} rows")
            first = tpl["records"][0]
            check("1 template hash", rec_hash(
                next(g for g in grammar if g["slug"] == first["id"])).startswith(
                    first["record_hash"]),
                f"{first['record_hash']} does not prefix the live record hash")
            check("1 template addresses", "explanation@pt-BR" in first["_addresses"],
                  f"addresses were {first['_addresses'][:6]}")
        else:
            check("1 template file", False, "no sheet written")

        # --- 2: approve --------------------------------------------------------------------------
        approve = {"schema_version": "1.0", "sheet_id": "case-approve",
                   "reviewed_by": "teacher:fixture", "reviewed_at": "2026-09-09",
                   "records": [{"id": slug, "record_hash": rec_hash(target)[:16],
                                "approve": ["explanation@pt-BR"], "note": "lida e conferida"}]}
        out = run(root, "--sheet", str(sheet_path(root, "approve", approve)), db_probe=db_probe)
        check("2 approve exit", out.returncode == 0, out.stderr or out.stdout)
        entries = read_ledger(root)["entries"]
        check("2 approve entry", len(entries) == 1, f"{len(entries)} entries")
        if entries:
            entry = entries[0]
            want, _how = live_anchor(target, "explanation", "pt-BR")
            check("2 approve anchor", entry["content_hash"] == want, entry["content_hash"])
            check("2 approve status", entry["status"] == "approved", entry["status"])
            check("2 approve locale", entry.get("locale") == "pt-BR", str(entry.get("locale")))
            check("2 approve who", entry["reviewed_by"] == "teacher:fixture", entry["reviewed_by"])

        # --- 3: idempotence ----------------------------------------------------------------------
        out = run(root, "--sheet", str(root / "sheets" / "approve.json"), db_probe=db_probe)
        check("3 idempotent exit", out.returncode == 0, out.stderr or out.stdout)
        check("3 idempotent count", len(read_ledger(root)["entries"]) == 1,
              f"{len(read_ledger(root)['entries'])} entries after a second run")
        check("3 idempotent says so", "já existia" in out.stdout, out.stdout)

        # --- 4: edit -----------------------------------------------------------------------------
        old_text = target["formation"]["pt-BR"]
        edit = {"schema_version": "1.0", "sheet_id": "case-edit",
                "reviewed_by": "teacher:fixture", "reviewed_at": "2026-09-09",
                "records": [{"id": slug, "record_hash": rec_hash(target)[:16],
                             "edit": {"formation@pt-BR": old_text + " (ajuste do professor)"},
                             "note": "faltava o caso do adjetivo-i"}]}
        before = len(read_ledger(root)["entries"])
        out = run(root, "--sheet", str(sheet_path(root, "edit", edit)), db_probe=db_probe)
        check("4 edit exit", out.returncode == 0, out.stderr or out.stdout)
        table = root / PENDING_REL / "case-edit.json"
        check("4 edit table", table.is_file(), "no repair table written")
        if table.is_file():
            rows = json.loads(table.read_text(encoding="utf-8"))
            check("4 edit rows", len(rows) == 1, f"{len(rows)} rows")
            check("4 edit exact old", rows[0]["old"] == old_text, "old is not the live text")
            check("4 edit new", rows[0]["new"].endswith("(ajuste do professor)"), rows[0]["new"][:40])
            check("4 edit why is the teacher's", rows[0]["why"] == "faltava o caso do adjetivo-i",
                  rows[0]["why"])
            check("4 edit addressing", set(rows[0]) >= {"entity", "slug", "field", "locale",
                                                        "old", "new", "why"},
                  f"row keys {sorted(rows[0])}")
        check("4 edit leaves ledger alone", len(read_ledger(root)["entries"]) == before,
              "an edit must not approve anything")
        check("4 edit not applied", "Nada foi aplicado" in out.stdout, out.stdout)

        # --- 5: reject ---------------------------------------------------------------------------
        reject = {"schema_version": "1.0", "sheet_id": "case-reject",
                  "reviewed_by": "teacher:fixture", "reviewed_at": "2026-09-09",
                  "records": [{"id": slug, "record_hash": rec_hash(target)[:16],
                               "reject": {"label@pt-BR": "o rótulo mistura os dois registros"}}]}
        out = run(root, "--sheet", str(sheet_path(root, "reject", reject)), db_probe=db_probe)
        check("5 reject exit", out.returncode == 0, out.stderr or out.stdout)
        rejected = [e for e in read_ledger(root)["entries"] if e["status"] == "rejected"]
        check("5 reject entry", len(rejected) == 1, f"{len(rejected)} rejections")
        if rejected:
            check("5 reject reason", rejected[0].get("note", "").startswith("o rótulo"),
                  str(rejected[0].get("note")))

        # --- 6: stale hash -----------------------------------------------------------------------
        ledger_bytes = (root / LEDGER_REL).read_bytes()
        stale = {"schema_version": "1.0", "sheet_id": "case-stale",
                 "reviewed_by": "teacher:fixture", "reviewed_at": "2026-09-09",
                 "records": [
                     {"id": slug, "record_hash": "deadbeefdeadbeef",
                      "approve": ["nuance@pt-BR"]},
                     {"id": grammar[1]["slug"], "record_hash": rec_hash(grammar[1])[:16],
                      "approve": ["label@pt-BR"]}]}
        out = run(root, "--sheet", str(sheet_path(root, "stale", stale)), db_probe=db_probe)
        check("6 stale exit 2", out.returncode == 2, f"exit {out.returncode}")
        check("6 stale explains", "STALE" in out.stdout, out.stdout)
        check("6 stale wrote nothing", (root / LEDGER_REL).read_bytes() == ledger_bytes,
              "the ledger moved on a refused sheet")
        check("6 stale no table", not (root / PENDING_REL / "case-stale.json").exists(),
              "a refused sheet still produced a repair table")

        # --- 7: unknown id -----------------------------------------------------------------------
        unknown = {"schema_version": "1.0", "sheet_id": "case-unknown",
                   "reviewed_by": "teacher:fixture", "reviewed_at": "2026-09-09",
                   "records": [{"id": "gram:nao-existe-mesmo", "record_hash": "aaaaaaaaaaaa",
                                "approve": ["label@pt-BR"]}]}
        out = run(root, "--sheet", str(sheet_path(root, "unknown", unknown)), db_probe=db_probe)
        check("7 unknown exit 2", out.returncode == 2, f"exit {out.returncode}")
        check("7 unknown explains", "no record in the export" in out.stdout, out.stdout)
        check("7 unknown wrote nothing", (root / LEDGER_REL).read_bytes() == ledger_bytes,
              "the ledger moved on an unknown id")

        # --- 8: no DB ----------------------------------------------------------------------------
        check("8 no db created", not db_probe.exists(),
              f"{db_probe} was created — review_apply.py opened a database")
        if db_before is not None:
            db_after = (real_db.stat().st_size, real_db.stat().st_mtime_ns)
            check("8 committed db untouched", db_after == db_before, "db/corpus.sqlite changed")

        # --- 9: the gate accepts what we wrote ---------------------------------------------------
        gate = subprocess.run(
            [sys.executable, str(REPO / "scripts" / "validate" / "validate_review_ledger.py"),
             "--root", str(root), "--review-ledger", str(root / LEDGER_REL)],
            capture_output=True, text=True, encoding="utf-8", cwd=str(REPO),
            env={**os.environ, "PYTHONIOENCODING": "utf-8"})
        check("9 gate green", gate.returncode == 0,
              (gate.stdout or "") + (gate.stderr or ""))

    print(f"test_review_apply: 9 cases, {len(fails)} FAIL")
    for line in fails:
        print(f"  [FAIL] {line}")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
