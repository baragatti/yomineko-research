#!/usr/bin/env python3
"""Hard gate: every learner-facing locale object in the export is declared, shaped, and as bilingual as
design/i18n.md says it must be (W40; spec: design/i18n.md "validate_locale_parity.py — validator spec").

INPUT is the two scope tables in design/i18n.md, parsed as pipe tables under the headings
"## Corpus layer — `en` REQUIRED" and "## Courseware layer — `en` OPTIONAL" (columns
`entity | field | learner-facing | en required | carries en today | [en_layer |] backfill route`), plus
the exemption ids of the "### The 18 ..." subsection. Not a sidecar: two files would drift. A parse
failure is a validator failure, never a skip. Entity -> files comes from contracts/manifest.json.

A LOCALE OBJECT is a JSON object whose keys are all locale-shaped and include `pt-BR` or `en`
(`{"op": ...}` is not one). `*_layer` siblings and `field_layers` are provenance, not text.

  R1  required row: every instance carries a non-empty `en` (exempt ids suppressed). RATCHETED by
      research/reports/locale_parity_baseline.json: a field fails when its misses RISE above the
      baseline; a baseline entry for a field at 0 misses, or for a field that is not a required row,
      is itself a failure (a stale ratchet row). The backfill drives each entry to 0 and deletes it.
  R2  optional row: never fails; coverage printed as INFO.
  R3  stale scope row: a declared path with zero non-null instances.
  R4  undeclared field: a locale object at a path no row declares.
  R5  shape: keys within the declared locale set (pt-BR, en) and pt-BR present.
  R6  en_layer integrity: a `per-record` row's instances with `en` carry the sibling `<field>_layer`
      (keys within the instance's own locales, values A/B, never C); instances without `en` carry no
      sibling; a constant-layer or courseware row carries no sibling at all.
  R7  exemption liveness: every exempt id still resolves to a record that still lacks `en`.

Exit 1 on any failure. Usage: validate_locale_parity.py [--root PATH] [--list]
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
REPO = Path(__file__).resolve().parents[2]
MAX_REPORT = 20
# The declared locale set. pt-BR is authored, en is the Layer-A source / derived sibling. A new
# locale module is a new entry here and new keys in the data, never a new field.
LOCALES = {"pt-BR", "en"}
LAYERS = {"A", "B", "C"}
LOCALE_KEY = re.compile(r"^[a-z]{2}(-[A-Za-z0-9]+)?$")
H_REQUIRED = "## Corpus layer — `en` REQUIRED"
H_OPTIONAL = "## Courseware layer — `en` OPTIONAL"
H_EXEMPT = "### The 18"


def is_locale_object(v) -> bool:
    return (isinstance(v, dict) and bool(v) and all(isinstance(k, str) and LOCALE_KEY.match(k) for k in v)
            and ("pt-BR" in v or "en" in v))


def section(text: str, heading: str) -> str:
    i = text.find(heading)
    if i < 0:
        raise SystemExit(f"validate_locale_parity: design/i18n.md has no heading {heading!r} (parse failure)")
    j = text.find("\n#", i + len(heading))
    return text[i:j if j >= 0 else len(text)]


def parse_table(sec: str, heading: str) -> list[dict]:
    lines = [ln.strip() for ln in sec.splitlines() if ln.strip().startswith("|")]
    if len(lines) < 3:
        raise SystemExit(f"validate_locale_parity: no pipe table under {heading!r} (parse failure)")
    cols = [c.replace("`", "").strip().lower() for c in lines[0].strip("|").split("|")]
    need = ["entity", "field", "en required"]
    if any(n not in cols for n in need):
        raise SystemExit(f"validate_locale_parity: {heading!r} table lacks columns {need} (got {cols})")
    rows = []
    for ln in lines[2:]:
        cells = [c.strip() for c in ln.strip("|").split("|")]
        if len(cells) != len(cols):
            raise SystemExit(f"validate_locale_parity: malformed row under {heading!r}: {ln}")
        r = dict(zip(cols, cells))
        req = re.sub(r"[*`]", "", r["en required"]).strip().split()[0].lower() if r["en required"] else ""
        if req not in ("yes", "no"):
            raise SystemExit(f"validate_locale_parity: `en required` must lead with yes/no: {ln}")
        layer_cell = re.sub(r"[*`]", "", r.get("en_layer", "")).strip()
        rows.append({"entity": r["entity"].strip("`"), "field": r["field"].strip("`"),
                     "required": req == "yes",
                     "per_record": layer_cell.lower().startswith("per-record")})
    return rows


def parse_exemptions(text: str) -> set[str]:
    sec = section(text, H_EXEMPT)
    out, prefix = set(), None
    for tok in re.findall(r"`(sent:[a-z]+-[0-9a-f]+|-[0-9a-f]+)`", sec):
        if tok.startswith("sent:"):
            prefix = tok.rsplit("-", 1)[0]
            out.add(tok)
        elif prefix:
            out.add(prefix + tok)
    if not out:
        raise SystemExit("validate_locale_parity: no exemption ids parsed (parse failure)")
    return out


def records(root: Path, ent: dict):
    for p in sorted(root.glob(ent["files"])):
        data = json.loads(p.read_text(encoding="utf-8"))
        packing = ent.get("packing", "list")
        if packing == "single":
            recs = [data]
        elif packing == "map":
            recs = [x for v in data.values() for x in (v if isinstance(v, list) else [v])]
        else:
            recs = data
        for i, r in enumerate(recs):
            if isinstance(r, dict):
                yield str(r.get("slug") or r.get("id") or f"{p.name}#{i}"), r


def resolve(node, parts: list[str]):
    """Yield (parent, key, value) for every instance of the dotted path (`a[].b`) under node."""
    head, rest = parts[0], parts[1:]
    is_list = head.endswith("[]")
    key = head[:-2] if is_list else head
    if not isinstance(node, dict) or key not in node:
        return
    val = node[key]
    if is_list:
        for x in val if isinstance(val, list) else []:
            if rest:
                yield from resolve(x, rest)
            else:
                yield node, key, x
    elif rest:
        yield from resolve(val, rest)
    else:
        yield node, key, val


def discover(node, path: str, out: set[str]) -> None:
    if is_locale_object(node):
        out.add(path)
        return
    if isinstance(node, dict):
        for k, v in node.items():
            if k.endswith("_layer") or k == "field_layers":
                continue
            discover(v, f"{path}.{k}" if path else k, out)
    elif isinstance(node, list):
        for x in node:
            discover(x, path + "[]", out)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=str(REPO), help="tree to validate (default: repo root)")
    ap.add_argument("--list", action="store_true", help="print every failure")
    args = ap.parse_args()
    root = Path(args.root).resolve()
    text = (root / "design" / "i18n.md").read_text(encoding="utf-8")
    scope = parse_table(section(text, H_REQUIRED), H_REQUIRED) + parse_table(section(text, H_OPTIONAL), H_OPTIONAL)
    exempt = parse_exemptions(text)
    baseline = json.loads((root / "research" / "reports" / "locale_parity_baseline.json")
                          .read_text(encoding="utf-8"))["misses"]
    ents = {e["entity"]: e for e in json.loads((root / "contracts" / "manifest.json")
                                                .read_text(encoding="utf-8"))["entities"] if e.get("files")}

    fails: list[str] = []
    seen_rows: set[str] = set()
    for r in scope:
        name = f"{r['entity']}.{r['field']}"
        if name in seen_rows:
            fails.append(f"scope: {name} is declared twice")
        seen_rows.add(name)
        if r["entity"] not in ents:
            fails.append(f"R3 {name}: entity {r['entity']!r} is not in contracts/manifest.json")

    recs: dict[str, list[tuple[str, dict]]] = {e: list(records(root, ents[e])) for e in ents}
    found: set[str] = set()
    for e, rs in recs.items():
        paths: set[str] = set()
        for _rid, rec in rs:
            discover(rec, "", paths)
        found |= {f"{e}.{p}" for p in paths}

    # R4: undeclared locale paths
    for p in sorted(found - seen_rows):
        fails.append(f"R4 {p}: a locale object at a path no scope row declares (design/i18n.md)")

    info: list[str] = []
    misses: dict[str, int] = {}
    shape_bad = Counter()
    for r in scope:
        name = f"{r['entity']}.{r['field']}"
        parts = r["field"].split(".")
        n = with_en = 0
        missing_ids: list[str] = []
        for rid, rec in recs.get(r["entity"], []):
            for parent, key, val in resolve(rec, parts):
                sib = parent.get(f"{key}_layer") if isinstance(parent, dict) else None
                if val is None:
                    if sib is not None:
                        fails.append(f"R6 {name} {rid}: `{key}_layer` beside a null field")
                    continue
                n += 1
                if not is_locale_object(val):
                    fails.append(f"R5 {name} {rid}: declared a locale object, found {type(val).__name__}")
                    continue
                bad_keys = set(val) - LOCALES
                if bad_keys or "pt-BR" not in val:
                    shape_bad[name] += 1
                    if shape_bad[name] <= 3:
                        fails.append(f"R5 {name} {rid}: locale keys {sorted(val)} (allowed {sorted(LOCALES)}, "
                                     f"pt-BR required)")
                has_en = bool(str(val.get("en") or "").strip()) if not isinstance(val.get("en"), list) \
                    else bool(val.get("en"))
                with_en += has_en
                # R6
                if r["per_record"]:
                    if has_en:
                        if not isinstance(sib, dict) or not sib:
                            fails.append(f"R6 {name} {rid}: has en but no `{key}_layer`")
                        elif (set(sib) - set(val)) or any(v not in LAYERS - {"C"} for v in sib.values()):
                            fails.append(f"R6 {name} {rid}: `{key}_layer` {sib!r} does not fit {sorted(val)} "
                                         f"(keys within the object's own locales; A/B only)")
                    elif sib is not None:
                        fails.append(f"R6 {name} {rid}: `{key}_layer` present on an instance with no en")
                elif sib is not None:
                    fails.append(f"R6 {name} {rid}: `{key}_layer` present but the row's en_layer is not "
                                 f"per-record")
                if r["required"] and not has_en:
                    if not (rid in exempt and name == "sentence.translation"):
                        missing_ids.append(rid)
        if n == 0:
            fails.append(f"R3 {name}: declared in design/i18n.md but has zero non-null instances (stale scope row)")
            continue
        if r["required"]:
            misses[name] = len(missing_ids)
            allowed = baseline.get(name, 0)
            if len(missing_ids) > allowed:
                fails.append(f"R1 {name}: {len(missing_ids)} instance(s) lack en, baseline allows {allowed}; "
                             f"first: {missing_ids[:MAX_REPORT]}")
            elif len(missing_ids) < allowed:
                info.append(f"ratchet {name}: {len(missing_ids)} misses < baseline {allowed}; lower the baseline")
        else:
            info.append(f"R2 {name}: optional, {with_en}/{n} carry en ({100 * with_en / n:.1f}%)")

    # ratchet hygiene
    required = {f"{r['entity']}.{r['field']}" for r in scope if r["required"]}
    for name, allowed in sorted(baseline.items()):
        if name not in required:
            fails.append(f"ratchet {name}: baseline entry for a field that is not a required scope row")
        elif misses.get(name, 0) == 0 and allowed:
            fails.append(f"ratchet {name}: baseline {allowed} but the field is complete; delete the entry")
        elif allowed == 0:
            fails.append(f"ratchet {name}: a 0 entry is noise; delete it")

    # R7 exemption liveness
    sents = {rid: rec for rid, rec in recs.get("sentence", [])}
    for sid in sorted(exempt):
        rec = sents.get(sid)
        if rec is None:
            fails.append(f"R7 {sid}: exempt in design/i18n.md but no such sentence")
        elif (rec.get("translation") or {}).get("en"):
            fails.append(f"R7 {sid}: exempt in design/i18n.md but now carries an en (stale exemption)")

    total_miss = sum(misses.values())
    print("============== LOCALE PARITY ==============")
    print(f"  scope rows: {sum(r['required'] for r in scope)} required, "
          f"{sum(not r['required'] for r in scope)} optional; {len(found)} locale paths in the export; "
          f"{len(exempt)} named exemptions")
    for name in sorted(misses):
        print(f"  R1 {name:44} misses {misses[name]:>6} / baseline {baseline.get(name, 0):>6}")
    print(f"  required-scope en still missing: {total_miss} (ratcheted)")
    for i in info:
        print(f"  [info] {i}")
    if fails:
        shown = fails if args.list else fails[:MAX_REPORT * 2]
        for f in shown:
            print(f"  [FAIL] {f}")
        if len(fails) > len(shown):
            print(f"  ... {len(fails) - len(shown)} more (--list)")
        print(f"\nvalidate_locale_parity: {len(fails)} FAIL")
        return 1
    print("\nvalidate_locale_parity: ALL OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
