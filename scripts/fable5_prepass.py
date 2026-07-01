# Deterministic style/QA pre-pass over corpus/ + course/ JSON.
# Pure regex/structure checks that don't need a model. Findings -> prepass.json.
import json, os, re, glob
from collections import Counter

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "research", "derived", "fable5_validation", "prepass.json")

findings = []
def add(det, file, ctx, path, value):
    findings.append({
        "detector": det, "file": file, "slug": ctx, "path": path,
        "value": value if len(value) <= 200 else value[:200] + "...",
    })

EMDASH = re.compile(r"[—―]")
QUANTO_A = re.compile(r"\bquanto\s+(a|à|ao|às|aos)\b", re.IGNORECASE)
PTPT = re.compile(
    r"\b(telem[óo]vel|autocarro|comboio|pequeno-almo[çc]o|casa de banho|ecr[ãa]|"
    r"sanita|autoclismo|frigor[íi]fico|rapariga|raparigas|portagem|utilizador(es)?|"
    r"gajo|vosso|vossa|penso r[áa]pido|rebuçado|paragem|passadeira|"
    r"bilheteira|talho|montra|propina)\b", re.IGNORECASE)
UKEN = re.compile(
    r"\b(colour|flavour|favourite|behaviour|neighbour|honour|humour|programme|"
    r"organis(e|es|ed|ing|ation)|realis(e|es|ed|ing)|recognis(e|es|ed|ing)|"
    r"apologis(e|es|ed|ing)|theatre|centre|litre|whilst|learnt)\b", re.IGNORECASE)
BAD_TOKENS = re.compile(r"\b(undefined|TODO|FIXME|XXX|lorem)\b")
KANA_ONLY = re.compile(r"^[぀-ヿー、。！？，．\s、。！？!?・「」『』ー〜~…\.,]*$")
NON_ASCII = re.compile(r"[^\x00-\x7F]")

def walk(node, file, ctx, path):
    if isinstance(node, dict):
        c = node.get("slug") or node.get("id") or ctx
        for k, v in node.items():
            walk(v, file, c, f"{path}.{k}" if path else k)
        # locale-object completeness (corpus only): dict that has pt-BR or en
        if file.startswith("corpus") and ("pt-BR" in node or "en" in node):
            keys = set(node.keys())
            if keys <= {"pt-BR", "en"} and len(keys) >= 1:
                for want in ("pt-BR", "en"):
                    v = node.get(want)
                    empty = v is None or v == "" or v == []
                    if empty:
                        add("locale-missing-" + want, file, c, path, json.dumps(node, ensure_ascii=False))
    elif isinstance(node, list):
        for i, v in enumerate(node):
            walk(v, file, ctx, f"{path}[{i}]")
    elif isinstance(node, str):
        lk = path.rsplit(".", 1)[-1]
        is_pt = lk == "pt-BR" or ".pt-BR" in path
        is_en = lk == "en" or path.endswith(".en")
        is_authored_text = is_pt or is_en or lk in ("body",)
        if is_authored_text and EMDASH.search(node):
            add("em-dash", file, ctx, path, node)
        if is_pt and PTPT.search(node):
            add("pt-PT-lexicon", file, ctx, path, node)
        if is_en and UKEN.search(node):
            add("uk-english", file, ctx, path, node)
        if is_authored_text and BAD_TOKENS.search(node):
            add("bad-token", file, ctx, path, node)
        if lk in ("kana",) and node and not KANA_ONLY.match(node):
            add("kana-impurity", file, ctx, path, node)
        if lk in ("romaji", "ro") and node and NON_ASCII.search(node):
            add("romaji-non-ascii", file, ctx, path, node)

# natural-translation "Quanto a" check (sentences + readings only, natural field)
def check_natural_translations():
    with open(os.path.join(ROOT, "corpus/sentences/bank.json"), encoding="utf-8") as f:
        bank = json.load(f)
    for s in bank:
        nat = (s.get("translation") or {}).get("pt-BR") or ""
        if QUANTO_A.search(nat):
            add("quanto-a-in-natural", "corpus/sentences/bank.json", s["slug"], "translation.pt-BR", nat)
        if s.get("provenance", {}).get("ai_generated") and s.get("jp", "").rstrip().endswith("。"):
            add("generated-jp-ends-kuten", "corpus/sentences/bank.json", s["slug"], "jp", s["jp"])
    for lv in ("n5", "n4", "n3"):
        with open(os.path.join(ROOT, f"corpus/readings/{lv}.json"), encoding="utf-8") as f:
            for r in json.load(f):
                nat = (r.get("translation") or {}).get("pt-BR") or ""
                if QUANTO_A.search(nat):
                    add("quanto-a-in-natural", f"corpus/readings/{lv}.json", r["slug"], "translation.pt-BR", nat)

files = sorted(glob.glob(os.path.join(ROOT, "corpus", "**", "*.json"), recursive=True)) + \
        sorted(glob.glob(os.path.join(ROOT, "course", "**", "*.json"), recursive=True))
for fp in files:
    rel = os.path.relpath(fp, ROOT).replace("\\", "/")
    if rel.startswith("corpus/strokes"):  # stroke path data, no prose
        continue
    with open(fp, encoding="utf-8") as f:
        try:
            data = json.load(f)
        except Exception as e:
            add("json-parse-error", rel, None, "", str(e)); continue
    walk(data, rel, None, "")
check_natural_translations()

with open(OUT, "w", encoding="utf-8") as f:
    json.dump(findings, f, ensure_ascii=False, indent=1)

counts = Counter(f["detector"] for f in findings)
print("TOTAL:", len(findings))
for det, n in counts.most_common():
    print(f"{det}: {n}")
    for s in [f for f in findings if f["detector"] == det][:3]:
        print("   ", s["file"], s["slug"], s["path"], "|", s["value"][:90])
