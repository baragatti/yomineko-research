#!/usr/bin/env python3
"""P6b — repair mechanically-broken tags in authored lesson bodies (conservative, stack-based).

Authors occasionally typo a CLOSING tag — most often writing </jp> where they meant </text> in a run of
inline siblings: `<text> e </jp>`. That single wrong close corrupts the parser stack, so every following
sibling <text> looks NESTED, cascading into dozens of "<text> may not contain <text>" / "stray </jp>" /
"mismatched </p>" errors from ONE typo. This pass walks the body as a tag stream with an explicit stack and
fixes ONLY provable mismatches:
  - close tag == top of stack            -> keep (correct).
  - close tag != top, both inline-leaf   -> the author meant to close the OPEN one: emit </top> (corrects
    </jp> -> </text>, etc.). This is the common typo.
  - close tag appears DEEPER in the stack -> emit closers for the unclosed inner tags, then close it
    (repairs overlap/missing-close).
  - close tag not on the stack at all     -> truly stray: drop it.
Valid bodies have no mismatches, so they pass through byte-identical (idempotent). Run after
normalize_lesson_refs / dedupe_unlocks and before load_lessons. Usage:
  repair_lesson_bodies.py              # all research/derived/lessons/*.json
  repair_lesson_bodies.py <slug...>    # only the named lessons
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
ROOT = Path(__file__).resolve().parents[2]
LESSON_DIR = ROOT / "research" / "derived" / "lessons"
INLINE_LEAF = {"text", "jp", "romaji", "emphasis", "term"}
# self-closing element names (also detected by the "/>" syntax regardless of name)
SELF_CLOSE = {"grammar", "vocab", "kanji", "sentence", "exercise", "break"}
# of those, the INLINE ones that may legitimately sit beside <text> as siblings (sentence/exercise are block)
INLINE_SELF_CLOSE = {"grammar", "vocab", "kanji", "break"}
TOKEN = re.compile(r"<(/?)([a-zA-Z][\w-]*)((?:\s[^>]*?)?)(/?)>")


def repair_body(body: str) -> tuple[str, int]:
    # stack holds [name, reopen] — `reopen` is the inline-leaf to re-open after this tag closes
    # (set when an inline tag interrupts an open inline-leaf, e.g. <text>..<emphasis>..</emphasis>..</text>).
    out: list[str] = []
    stack: list[list] = []
    fixes = 0
    pos = 0
    names = lambda: [s[0] for s in stack]  # noqa: E731

    def _reopen(top: list) -> None:
        nonlocal fixes
        if top[1]:
            out.append(f"<{top[1]}>")
            stack.append([top[1], None])
            fixes += 1

    def emit_text(seg: str) -> None:
        """Emit a text run; if it sits in a NON-inline context (bare), wrap the non-whitespace in <text>."""
        nonlocal fixes
        if not seg:
            return
        if stack and stack[-1][0] in INLINE_LEAF:
            out.append(seg)  # already inside <text>/<jp>/… — fine
            return
        stripped = seg.strip()
        if not stripped:
            out.append(seg)  # whitespace-only formatting between block tags — leave as-is
            return
        lead = seg[:len(seg) - len(seg.lstrip())]
        trail = seg[len(seg.rstrip()):]
        out.append(f"{lead}<text>{stripped}</text>{trail}")
        fixes += 1

    for m in TOKEN.finditer(body):
        emit_text(body[pos:m.start()])  # text before the tag (wrap if bare)
        pos = m.end()
        slash, name, _attrs, selfslash = m.group(1), m.group(2), m.group(3), m.group(4)
        raw = m.group(0)
        if slash:  # closing tag </name>
            if stack and stack[-1][0] == name:
                _reopen2 = stack.pop()
                out.append(raw)
                _reopen(_reopen2)
            elif stack and stack[-1][0] in INLINE_LEAF and name in INLINE_LEAF:
                # typo'd inline close — close the actually-open inline tag instead
                top = stack.pop()
                out.append(f"</{top[0]}>")
                fixes += 1
                _reopen(top)
            elif name in names():
                # overlap/missing close — close inner unclosed tags first, then this one
                while stack and stack[-1][0] != name:
                    out.append(f"</{stack.pop()[0]}>")
                    fixes += 1
                if stack:
                    stack.pop()
                out.append(raw)
            else:
                # truly stray close (no matching open) — drop it
                fixes += 1
        elif selfslash or name in SELF_CLOSE:  # self-closing
            if name in INLINE_SELF_CLOSE and stack and stack[-1][0] in INLINE_LEAF:
                # self-closing inline (e.g. <vocab/>) sitting INSIDE an open inline-leaf — split around it
                top = stack.pop()
                out.append(f"</{top[0]}>")
                fixes += 1
                out.append(raw)
                stack.append([top[0], top[1]])  # reopen the inline-leaf for the following content
                out.append(f"<{top[0]}>")
                fixes += 1
            else:
                out.append(raw)
        else:  # opening tag
            if name in INLINE_LEAF and stack and stack[-1][0] in INLINE_LEAF:
                # inline nested in inline — split: close the parent, reopen it after this tag closes
                parent = stack.pop()
                out.append(f"</{parent[0]}>")
                fixes += 1
                stack.append([name, parent[0]])
                out.append(raw)
            else:
                stack.append([name, None])
                out.append(raw)
    emit_text(body[pos:])
    # close anything still open (defensive; usually empty)
    while stack:
        out.append(f"</{stack.pop()[0]}>")
        fixes += 1
    result = "".join(out)
    # drop empty <text></text> introduced by a reopen with no following content (exact, no whitespace eaten)
    result = result.replace("<text></text>", "")
    return result, fixes


def main() -> int:
    if len(sys.argv) > 1:
        files = [LESSON_DIR / ((a.split(":", 1)[1] if ":" in a else a) + ".json") for a in sys.argv[1:]]
    else:
        files = sorted(LESSON_DIR.glob("*.json"))
    total = 0
    touched = 0
    for f in files:
        if not f.exists():
            print(f"  skip (missing) {f.name}")
            continue
        d = json.loads(f.read_text(encoding="utf-8"))
        new_body, fixes = repair_body(d.get("body", "") or "")
        if fixes:
            d["body"] = new_body
            f.write_text(json.dumps(d, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            print(f"  {d.get('slug', f.stem)}: {fixes} tag fix(es)")
            total += fixes
            touched += 1
    print(f"repaired {total} tag issue(s) across {touched} file(s)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
