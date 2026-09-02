#!/usr/bin/env python3
"""One place that answers "which corpus.sqlite am I writing?" and "where do exports land?".

Every script that touched `db/corpus.sqlite` used to hardcode `ROOT / "db" / "corpus.sqlite"`, so the
only DB any of them could ever build was the one on this machine. W01 needs to replay the whole chain
into a scratch DB and diff the result against the committed export, which means every step in the
chain has to be redirectable — without changing what happens when a human runs it by hand.

So the rule is: **the default never moves.** `db_target(default)` returns `default` unless something
explicitly asks for another target, in one of two ways:

* `--db PATH` / `--db=PATH` on the command line (consumed here, so a script's own argparse never
  sees an argument it does not declare), or
* the `YOMINEKO_DB` environment variable — which is how `rebuild_index.py` redirects a whole
  subprocess chain without editing anyone's argv.

argv wins over the environment, because a human typing a path means it.

`out_root(default_root)` is the same idea for the exporters: `--out-root PATH` / `$YOMINEKO_OUT_ROOT`
relocates the `corpus/` and `course/` trees they write, so a rebuild can export into a temp tree and
diff it against the committed one instead of overwriting it.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

__all__ = ["db_target", "out_root", "build_date", "take_flag"]


def take_flag(flag: str, argv: list[str] | None = None) -> str | None:
    """Pull `--flag VALUE` / `--flag=VALUE` out of argv and return VALUE (None if absent).

    Removing it is the point: these scripts are called with their own argparse, and an undeclared
    `--db` would abort them. Only the first occurrence is honoured.
    """
    a = sys.argv if argv is None else argv
    for i, tok in enumerate(a):
        if tok == flag and i + 1 < len(a):
            val = a[i + 1]
            del a[i:i + 2]
            return val
        if tok.startswith(flag + "="):
            val = tok[len(flag) + 1:]
            del a[i]
            return val
    return None


def db_target(default: Path | str) -> Path:
    """The sqlite file this process should read/write. `default` unless redirected."""
    val = take_flag("--db")
    if val:
        return Path(val)
    env = os.environ.get("YOMINEKO_DB")
    return Path(env) if env else Path(default)


def out_root(default: Path | str) -> Path:
    """The repo root the exporters write `corpus/` and `course/` under. `default` unless redirected."""
    val = take_flag("--out-root")
    if val:
        return Path(val)
    env = os.environ.get("YOMINEKO_OUT_ROOT")
    return Path(env) if env else Path(default)


def build_date() -> str:
    """The ISO date the exporters stamp into their INDEX.md headers and `"generated"` fields.

    Wall-clock `date.today()` made the export non-reproducible for a silly reason: rebuild it tomorrow
    and fourteen files differ in one token, with nothing wrong. `$YOMINEKO_BUILD_DATE` pins it, which is
    what `validate_index_rebuildable.py` sets (to the date already committed) so the diff measures the
    data and not the calendar. Unset, the behaviour is exactly what it always was.
    """
    import datetime as _dt
    return os.environ.get("YOMINEKO_BUILD_DATE") or _dt.date.today().isoformat()
