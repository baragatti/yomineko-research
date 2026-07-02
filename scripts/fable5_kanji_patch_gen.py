# Build a clean patch (slug -> new en/pt meaning lists) from the confirmed
# phase-1 findings. Clean list-edit cases are resolved mechanically; anything
# prose-like or non-matching goes to `manual` for human/model resolution.
# Output: research/derived/fable5_validation/phase1_kanji_patch.json
import json, os, re, sys

sys.stdout.reconfigure(encoding="utf-8")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
VAL = os.path.join(ROOT, "research", "derived", "fable5_validation")

with open(os.path.join(VAL, "phase1_kanji.json"), encoding="utf-8") as f:
    findings = [x for x in json.load(f)["findings"] if x["verdict"] == "confirmed"]

current = {}
for lv in ["n5", "n4", "n3", "n2", "n1"]:
    with open(os.path.join(ROOT, "corpus", "kanji", f"{lv}.json"), encoding="utf-8") as f:
        for k in json.load(f):
            current[k["slug"]] = {
                "id": k["id"], "level": lv,
                "en": list(k["meanings"]["en"]), "pt": list(k["meanings"]["pt-BR"]),
            }

PROSE = re.compile(r"delete|remove|drop|keep|move|instead|should|\bor\b", re.IGNORECASE)

def split_list(s):
    return [p.strip() for p in s.split(",") if p.strip()]

patch = {}      # slug -> {"en": [...]} / {"pt": [...]} (only changed fields)
manual = []     # findings needing hand resolution
applied_log = []

def dedupe(seq):
    out = []
    for x in seq:
        if x not in out:
            out.append(x)
    return out

for f in findings:
    slug, field, cur, fix = f["slug"], f["field"], (f["current"] or "").strip(), (f["fix"] or "").strip()
    if slug not in current or field not in ("en", "pt"):
        manual.append({**f, "reason": "unknown slug or non-meaning field"})
        continue
    lst = patch.get(slug, {}).get(field) or list(current[slug][field])
    joined = ", ".join(lst)
    if PROSE.search(fix) or len(fix) > 90:
        manual.append({**f, "reason": "prose fix"})
        continue
    if cur == joined:                      # whole-list replacement
        new = dedupe(split_list(fix))
    elif cur in lst:                       # single-element replacement
        i = lst.index(cur)
        new = dedupe(lst[:i] + split_list(fix) + lst[i + 1:])
    else:
        # try element-substring: cur matches exactly one element loosely
        hits = [i for i, x in enumerate(lst) if cur and (cur == x or cur in x)]
        if len(hits) == 1:
            i = hits[0]
            new = dedupe(lst[:i] + split_list(fix) + lst[i + 1:])
        else:
            manual.append({**f, "reason": f"current not found in list ({joined!r})"})
            continue
    if not new:
        manual.append({**f, "reason": "empty result"})
        continue
    patch.setdefault(slug, {})[field] = new
    applied_log.append({"slug": slug, "field": field, "old": lst, "new": new,
                        "severity": f["severity"]})

out = {"patch": patch, "manual": manual, "log": applied_log}
with open(os.path.join(VAL, "phase1_kanji_patch.json"), "w", encoding="utf-8") as f:
    json.dump(out, f, ensure_ascii=False, indent=1)

print(f"auto-resolved: {len(applied_log)} field-edits on {len(patch)} kanji; manual: {len(manual)}")
for m in manual:
    print("MANUAL:", m["slug"], m["field"], "|", m["reason"], "| cur:", m["current"][:70], "| fix:", m["fix"][:90])
