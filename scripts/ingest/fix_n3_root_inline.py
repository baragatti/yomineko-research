#!/usr/bin/env python3
"""Fix two systematic body issues from N3 lesson authoring:
  (1) <emphasis> (or other inline) nested inside <text> -> make it a sibling;
  (2) inline elements (<jp>/<text>/<term>/<vocab>/<kanji>/<emphasis>) sitting at the BODY ROOT ->
      wrap each newline-separated run in a <p> block.
Only lessons that actually exhibit a problem are rewritten (no reformatting of clean lessons). Idempotent.
Usage: fix_n3_root_inline.py"""
from __future__ import annotations
import json, re, sys
from pathlib import Path
sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
ROOT = Path(__file__).resolve().parents[2]
LDIR = ROOT / "research" / "derived" / "lessons"

BLOCK = {"heading", "p", "list", "note", "exercise", "checklist"}
INLINE = {"jp", "text", "term", "vocab", "kanji", "emphasis", "grammar", "romaji"}
TAGNAME = re.compile(r"</?([a-zA-Z][\w-]*)")


def tagname(tag: str) -> str:
    m = TAGNAME.match(tag)
    return m.group(1) if m else ""


def unnest_emphasis(body: str) -> str:
    """Pull <emphasis>...</emphasis> out of any <text>...</text> that wrongly contains it."""
    def fix(m: re.Match) -> str:
        inner = m.group(1)
        if "<emphasis>" not in inner:
            return m.group(0)
        parts = re.split(r"(<emphasis>.*?</emphasis>)", inner)
        out = []
        for p in parts:
            if not p:
                continue
            if p.startswith("<emphasis>"):
                out.append(p)
            else:
                out.append(f"<text>{p}</text>")
        return "".join(out)
    return re.sub(r"<text>(.*?)</text>", fix, body)


def split_top(body: str):
    """Yield (kind, raw) top-level tokens: kind 'el' (a balanced element) or 'ws' (text between)."""
    out = []
    i, n = 0, len(body)
    while i < n:
        if body[i] == "<":
            j = body.index(">", i)
            tag = body[i:j + 1]
            name = tagname(tag)
            if tag.endswith("/>") or tag.startswith("</"):
                out.append(("el", tag)); i = j + 1
            else:
                depth, k = 1, j + 1
                while k < n and depth > 0:
                    if body[k] == "<":
                        jj = body.index(">", k)
                        t2 = body[k:jj + 1]
                        nm2 = tagname(t2)
                        if t2.endswith("/>"):
                            pass
                        elif t2.startswith("</"):
                            if nm2 == name:
                                depth -= 1
                        else:
                            if nm2 == name:
                                depth += 1
                        k = jj + 1
                    else:
                        k += 1
                out.append(("el", body[i:k])); i = k
        else:
            j = body.find("<", i)
            if j == -1:
                j = n
            out.append(("ws", body[i:j])); i = j
    return out


def wrap_root_inline(body: str) -> tuple[str, bool]:
    toks = split_top(body)
    has_root_inline = any(k == "el" and tagname(t) in INLINE for k, t in toks)
    if not has_root_inline:
        return body, False
    out_parts: list[str] = []
    para: list[str] = []
    pending_ws = ""

    def flush():
        if para:
            out_parts.append("<p>" + "".join(para).strip() + "</p>")
            para.clear()

    for kind, txt in toks:
        if kind == "ws":
            pending_ws = txt
            continue
        name = tagname(txt)
        if name in BLOCK:
            flush()
            out_parts.append(txt)
            pending_ws = ""
        else:
            if para and "\n" in pending_ws:
                flush()
            if para and pending_ws and "\n" not in pending_ws:
                para.append(pending_ws)
            para.append(txt)
            pending_ws = ""
    flush()
    return "\n".join(out_parts), True


def main() -> int:
    nfix = 0
    for f in sorted(LDIR.glob("n3-*.json")):
        obj = json.loads(f.read_text(encoding="utf-8"))
        body = obj.get("body", "")
        b1 = unnest_emphasis(body)
        b2, wrapped = wrap_root_inline(b1)
        if b2 != body:
            obj["body"] = b2
            f.write_text(json.dumps(obj, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            nfix += 1
    print(f"fixed root-inline / nested-emphasis in {nfix} N3 lessons")
    return 0


if __name__ == "__main__":
    sys.exit(main())
