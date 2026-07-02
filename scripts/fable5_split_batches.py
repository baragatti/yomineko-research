# One-off batch splitter for the Fable 5 validation run.
# Reads corpus JSON (source of truth) and writes compact, validation-focused
# batch files under this scratchpad dir. Nothing here touches the repo.
import json, os, glob

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'research', 'derived', 'fable5_validation', 'batches')

def load(rel):
    with open(os.path.join(ROOT, rel), encoding="utf-8") as f:
        return json.load(f)

def write_batches(kind, items, size):
    d = os.path.join(OUT, kind)
    os.makedirs(d, exist_ok=True)
    paths = []
    for i in range(0, len(items), size):
        p = os.path.join(d, f"{kind}-{i//size:03d}.json")
        with open(p, "w", encoding="utf-8") as f:
            json.dump({"batch": f"{kind}-{i//size:03d}", "items": items[i:i+size]},
                      f, ensure_ascii=False, indent=1)
        paths.append(p)
    return paths

manifest = {}

# ---- kanji (all levels) ----
kanji = []
for lv in ["n5", "n4", "n3", "n2", "n1"]:
    for k in load(f"corpus/kanji/{lv}.json"):
        common = [{"r": r["reading"], "t": r["type"]}
                  for r in (k.get("readings") or []) if r.get("common")]
        kanji.append({
            "slug": k["slug"], "ch": k["character"], "level": k["level"],
            "strokes": k.get("strokes"), "radical": k.get("radical_char"),
            "en": (k.get("meanings") or {}).get("en"),
            "pt": (k.get("meanings") or {}).get("pt-BR"),
            "readings_fact": common[:6],
            "notes": k.get("notes"),
        })
manifest["kanji"] = write_batches("kanji", kanji, 35)

# ---- vocab (all levels) ----
vocab = []
for lv in ["n5", "n4", "n3", "n2", "n1"]:
    for v in load(f"corpus/vocab/{lv}.json"):
        senses = [{
            "pos": s.get("pos"), "misc": s.get("misc") or [],
            "register": s.get("register"),
            "en": (s.get("gloss") or {}).get("en"),
            "pt": (s.get("gloss") or {}).get("pt-BR"),
        } for s in (v.get("senses") or [])]
        vocab.append({
            "slug": v["slug"], "hw": v["headword"], "kana": v["kana"],
            "romaji": v.get("romaji"), "level": v["level"],
            "class": v.get("verb_class") or v.get("adj_class"),
            "senses": senses,
        })
manifest["vocab"] = write_batches("vocab", vocab, 30)

# ---- sentences ----
sents = []
for s in load("corpus/sentences/bank.json"):
    toks = [{
        "s": t["surface"], "r": t.get("reading"),
        "en": (t.get("gloss") or {}).get("en"),
        "pt": (t.get("gloss") or {}).get("pt-BR"),
        "role": (t.get("role") or {}).get("pt-BR"),
        "note": t.get("conjugation_note"),
    } for t in (s.get("tokens") or [])]
    sents.append({
        "slug": s["slug"], "jp": s["jp"], "kana": s.get("kana"),
        "romaji": s.get("romaji"), "level": s.get("level"),
        "gen": bool((s.get("provenance") or {}).get("ai_generated")),
        "en": (s.get("translation") or {}).get("en"),
        "pt": (s.get("translation") or {}).get("pt-BR"),
        "lit_en": (s.get("translation_literal") or {}).get("en"),
        "lit_pt": (s.get("translation_literal") or {}).get("pt-BR"),
        "expl_en": (s.get("structure_explanation") or {}).get("en"),
        "expl_pt": (s.get("structure_explanation") or {}).get("pt-BR"),
        "tokens": toks,
    })
manifest["sentences"] = write_batches("sentences", sents, 15)

# ---- grammar ----
gram = []
for lv in ["n5", "n4", "n3"]:
    for g in load(f"corpus/grammar/{lv}.json"):
        gram.append({
            "slug": g["slug"], "level": g["level"],
            "label_en": (g.get("label") or {}).get("en"),
            "label_pt": (g.get("label") or {}).get("pt-BR"),
            "pattern": g.get("structure_pattern"),
            "register": g.get("register"),
            "caution": g.get("caution"),
            "forms": [{"form": f2.get("form"),
                       "en": (f2.get("meaning") or {}).get("en"),
                       "pt": (f2.get("meaning") or {}).get("pt-BR")}
                      for f2 in (g.get("forms") or [])],
            "expl_en": (g.get("explanation") or {}).get("en"),
            "expl_pt": (g.get("explanation") or {}).get("pt-BR"),
        })
manifest["grammar"] = write_batches("grammar", gram, 10)

# ---- conjugations ----
conj = []
for lv in ["n5", "n4", "n3"]:
    for c in load(f"corpus/conjugations/{lv}.json"):
        conj.append({
            "slug": c["slug"], "hw": c["headword"], "kana": c["kana"],
            "level": c["level"], "kind": c["kind"], "class": c["class"],
            "forms": [{"f": f2["form"], "s": f2["surface"],
                       "k": f2["kana"], "ro": f2.get("romaji")}
                      for f2 in (c.get("conjugations") or [])],
        })
manifest["conjugations"] = write_batches("conjugations", conj, 20)

# ---- readings ----
reads = []
for lv in ["n5", "n4", "n3"]:
    for r in load(f"corpus/readings/{lv}.json"):
        reads.append({
            "slug": r["slug"], "jp": r["jp"], "level": r["level"],
            "lesson": r.get("gated_to_lesson"),
            "tokens": [{"s": t["s"], "r": t["r"], "ro": t.get("ro")}
                       for t in (r.get("tokens") or [])],
            "en": (r.get("translation") or {}).get("en"),
            "pt": (r.get("translation") or {}).get("pt-BR"),
        })
manifest["readings"] = write_batches("readings", reads, 20)

# ---- lessons: just list file paths (agents read the real files) ----
lessons = sorted(glob.glob(os.path.join(ROOT, "course", "**", "lesson-*.json"),
                           recursive=True))
manifest["lesson_files"] = lessons
topics = sorted(glob.glob(os.path.join(ROOT, "course", "**", "topic.json"),
                          recursive=True))
manifest["topic_files"] = topics

with open(os.path.join(OUT, "manifest.json"), "w", encoding="utf-8") as f:
    json.dump(manifest, f, indent=1)

print("kanji", len(kanji), "->", len(manifest["kanji"]), "batches")
print("vocab", len(vocab), "->", len(manifest["vocab"]), "batches")
print("sentences", len(sents), "->", len(manifest["sentences"]), "batches")
print("grammar", len(gram), "->", len(manifest["grammar"]), "batches")
print("conjugations", len(conj), "->", len(manifest["conjugations"]), "batches")
print("readings", len(reads), "->", len(manifest["readings"]), "batches")
print("lessons", len(lessons), "files; topics", len(topics))

# ---- lessons (2 per batch: title/description/objectives/body/exercises) ----
lesson_items = []
for p in sorted(glob.glob(os.path.join(ROOT, "course", "**", "lesson-*.json"), recursive=True)):
    with open(p, encoding="utf-8") as f:
        d = json.load(f)
    lesson_items.append({
        "slug": d["id"], "file": os.path.relpath(p, ROOT).replace("\\", "/"),
        "level": d.get("level"),
        "title": (d.get("title") or {}).get("pt-BR"),
        "description": (d.get("description") or {}).get("pt-BR"),
        "objectives": [(o or {}).get("pt-BR") for o in (d.get("objectives") or [])],
        "body": d.get("body"),
        "exercises": [{
            "id": e.get("id"), "type": e.get("type"),
            "prompt": (e.get("prompt") or {}).get("pt-BR"),
            "answer": e.get("answer"),
            "explanation": (e.get("explanation") or {}).get("pt-BR"),
        } for e in (d.get("exercises") or [])],
    })
manifest["lessons"] = write_batches("lessons", lesson_items, 2)

# ---- topics (10 per batch: title/description) ----
topic_items = []
for p in sorted(glob.glob(os.path.join(ROOT, "course", "**", "topic.json"), recursive=True)):
    with open(p, encoding="utf-8") as f:
        d = json.load(f)
    topic_items.append({
        "slug": d.get("id") or p, "file": os.path.relpath(p, ROOT).replace("\\", "/"),
        "title": (d.get("title") or {}).get("pt-BR"),
        "description": (d.get("description") or {}).get("pt-BR"),
    })
manifest["topics"] = write_batches("topics", topic_items, 10)

with open(os.path.join(OUT, "manifest.json"), "w", encoding="utf-8") as f:
    json.dump(manifest, f, indent=1)
print("lessons", len(lesson_items), "->", len(manifest["lessons"]), "batches;",
      "topics", len(topic_items), "->", len(manifest["topics"]), "batches")
