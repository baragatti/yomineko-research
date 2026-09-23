#!/usr/bin/env python3
"""CAPABILITY registry + lesson map (roadmap C; owner-approved). Capabilities = the "language features" a
learner unlocks (te-form, particles, conditionals, keigo…) — the fixed list the daily skill-SRS (roadmap D)
schedules against. Deterministic: each capability lists its grammar keys explicitly; any grammar key not in a
curated group falls back to a capability derived from its INTRODUCING TOPIC (theme bucket), so every grammar
point maps somewhere stable. Lessons additionally emit kana/kanji recognition capabilities from their unlocks.

W24 adds a `kind` to every capability and four more kinds (design/courseware_architecture.md):
  vocabulary      cap:vocab:<topic> for every vocab unlock, the topic of the FIRST lesson that unlocks the word
  phonology/study curated lesson lists, read from the authoring table
  script          + cap:romaji-reading (curated, same table)
  exam-readiness  every lesson of top:<level>-revisao -> cap:exam-readiness-<level>
and three fields: `can_do` (Layer C, authored), `lessons` (inverse of lesson_map) and `exam_link` (derived
from the exam banks' own item provenance, or the whole paper for exam-readiness). The authored half lives in
research/derived/repairs/w24_capabilities.json; a derived capability with no authored row, or a can_do quote
that is not an objective of a lesson the capability claims, is a hard failure, never a silent drop.
Output: corpus/capabilities/registry.json + lesson_map.json. Usage: build_capabilities.py"""
from __future__ import annotations
import json, re, sqlite3, sys
from collections import defaultdict
from pathlib import Path
sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
# W01: honour --db / $YOMINEKO_DB so a rebuild can target a scratch DB (scripts/dbtarget.py).
import sys as _sys, pathlib as _pl  # noqa: E402
_sys.path.append(str(next(p for p in _pl.Path(__file__).resolve().parents if p.name == "scripts")))
from dbtarget import db_target  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
DB = db_target(ROOT / "db" / "corpus.sqlite")
OUT = ROOT / "corpus" / "capabilities"

# key -> (pt-BR name, level, [grammar keys])  — curated, explicit (no fuzzy matching)
CAPS: dict[str, tuple[str, str, list[str]]] = {
    "copula": ("Cópula だ/です e negação", "n5", ["da-desu", "janai-dewa-nai", "deshou", "darou", "ndesu"]),
    "topic-subject": ("Tópico は e sujeito が", "n5", ["wa-topic-marker", "ga", "ga-arimasu", "ga-imasu", "wa-ga-wa"]),
    "particles-core": ("Partículas centrais を/に/で/へ", "n5", ["o-wo", "ni", "de-demo".replace("-demo",""), "ni-e", "de", "te-de"]),
    "particles-link": ("Partículas de ligação と/や/も/か", "n5", ["to", "ya", "mo", "ka-ka", "toka-toka", "nado", "matawa"]),
    "particles-range": ("Limites から/まで", "n5", ["kara", "made", "te-kara", "made-ni", "n3-kara-ni-kakete"]),
    "questions": ("Perguntas e interrogativos", "n5", ["ka", "doushite", "douyatte", "donna", "wa-dou-desu-ka", "kai", "ka-dou-ka", "ka-shira", "kana", "n3-kanaa", "n3-kke"]),
    "sentence-final": ("Partículas finais ね/よ/なあ", "n5", ["ne", "yo", "naa", "sa", "n3-n-datte", "n3-nda-mon"]),
    "i-adjectives": ("Adjetivos い", "n5", ["i-adjectives"]),
    "na-adjectives": ("Adjetivos な", "n5", ["na-adjectives", "na"]),
    "adverbs-degree": ("Advérbios de grau e frequência", "n5", ["totemo", "itsumo", "mada", "mou", "sugiru", "sonna-ni", "zenzen-nai", "amari-nai", "nakanaka-nai", "kitto", "zehi", "yatto", "sakki", "kyuu-ni", "n3-mattaku-nai", "n3-kesshite-nai", "n3-metta-ni-nai", "n3-metta-ni-nai-2", "n3-sukoshimo-nai"]),
    "te-form": ("Forma て e usos básicos", "n5", ["te-form", "te-kudasai", "temo-ii-desu", "te-wa-ikenai", "naide", "naide-kudasai", "n3-naide", "n3-zu-ni"]),
    "aspect-teiru": ("Progressivo/estado 〜ている", "n5", ["te-iru", "mada-te-imasen", "te-ita", "teiru-tokoro", "n3-te-iru", "n3-ppanashi"]),
    "aspect-preparation": ("Aspecto: 〜てある/〜ておく/〜てしまう", "n4", ["te-aru", "te-oku", "te-shimau-chau", "n3-chatta", "te-miru", "n3-te-miru"]),
    "aspect-direction": ("Direção da ação 〜ていく/〜てくる", "n4", ["te-iku", "te-kuru"]),
    "desire": ("Desejos 〜たい/〜がほしい", "n5", ["tai", "ga-hoshii", "te-hoshii", "n3-te-hoshii", "tagaru", "gari", "garu-gatteiru", "n3-to-ii-naa"]),
    "invitation-volitional": ("Convites e forma volitiva", "n5", ["masen-ka", "mashou", "mashouka", "ikou-kei-volitional-form", "you-to-omou", "n3-you-to-omou", "n3-you-to-shinai", "n3-uto-shita", "tsumori", "yotei-da", "n3-tsumori-deshita"]),
    "requests-commands": ("Pedidos e ordens", "n5", ["o-kudasai", "o-kudasai-2", "kata", "nasai", "n3-te-goran", "n3-te-kureto", "n3-sete-kudasai", "sasete-kudasai", "te-itadakemasen-ka"]),
    "obligation": ("Obrigação e proibição", "n5", ["naito-ikenai", "nakucha", "nakute-wa-ikenai", "nakute-wa-naranai", "cha-ikenai-ja-ikenai", "naku-temo-ii", "nakereba-ikenai", "nakereba-naranai", "n3-beki-da", "n3-wake-ni-wa-ikanai"]),
    # W24: `temo-ii-desu` is claimed by te-form first (setdefault), so this group only ever holds
    # to-ittemo-ii. The name says what it owns; moving the key out of te-form is an owner call.
    "permission": ("Atenuação com と言ってもいい", "n5", ["temo-ii-desu", "to-ittemo-ii"]),
    "existence-having": ("Existência e posse", "n5", ["ga-arimasu", "ga-imasu"]),
    "movement-purpose": ("Movimento com propósito 〜に行く", "n5", ["ni-iku"]),
    "become-change": ("Mudança de estado なる/〜くする/〜にする", "n5", ["naru", "ni-suru", "ku-suru", "you-ni-naru", "n3-you-ni-natta", "koto-ni-naru", "koto-ni-suru", "n3-koto-ni-natte-iru", "n3-koto-ni-shite-iru"]),
    "comparison": ("Comparações e superlativo", "n5", ["yori", "wa-yori-desu", "yori-hou-ga", "ichiban", "no-naka-de-a-ga-ichiban", "no-naka-de", "hou-ga-ii", "n3-ni-kurabete", "n3-to-iu-yori", "n3-hodo", "n3-ba-hodo", "n3-kurai", "n3-kurai-wa-nai"]),
    "preference-skill": ("Gostos e habilidades (すき/じょうず/へた)", "n5", ["no-ga-suki", "no-ga-jouzu", "no-ga-heta"]),
    "experience": ("Experiência 〜たことがある", "n5", ["ta-koto-ga-aru", "koto-ga-aru"]),
    "potential": ("Forma potencial", "n4", ["koto-ga-dekiru", "rareru", "n3-kirenai", "n3-nai-koto-wa-nai"]),
    "passive": ("Voz passiva", "n4", ["ukemi-kei", "n3-rareta", "n3-ni-yotte"]),
    "causative": ("Causativo e causativo-passivo", "n4", ["saseru", "saserareru"]),
    "conditionals": ("Condicionais と/ば/たら/なら", "n4", ["to", "ba", "tara", "nara", "baai-wa", "tara-dou", "tara-ii-desu-ka", "n3-moshi-tanara", "n3-moshi-temo", "n3-moshimo-nara", "n3-tatoe-temo", "n3-ba-yokatta", "n3-ba-noni", "n3-nai-to", "n3-donna-ni-temo"]),
    "temporal-clauses": ("Orações temporais (とき/まえに/あとで/あいだ/ながら)", "n5", ["toki", "mae-ni", "ato-de", "aida", "aida-ni", "nagara", "koro-goro", "oki-ni", "n3-saichuu-ni", "n3-tabi-ni", "n3-uchi-ni", "n3-ta-totan", "n3-te-hajimete", "n3-tsuide-ni", "ta-tokoro", "ta-bakari", "tokoro", "n3-ta-tokoro", "n3-tokoro-datta"]),
    "reasons": ("Causa e razão (から/ので/し)", "n5", ["kara", "node", "shi", "n3-nazenara", "n3-desu-kara", "n3-okagede", "n3-sei-de", "n3-sono-kekka", "n3-sono-tame-ni", "n3-mono-da".replace("n3-mono-da","n3-da-mono-da")]),
    "contrast-concession": ("Contraste e concessão (けど/でも/のに)", "n5", ["kedo", "keredo-mo", "demo", "shikashi", "noni", "temo", "n3-temo", "sore-demo", "n3-dakedo", "n3-kuse-ni", "n3-to-ittemo", "n3-tokoro-ga", "n3-wari-ni-wa", "n3-ni-shite-wa"]),
    "connectors": ("Conectores de discurso", "n5", ["sore-kara", "soshite", "sore-ni", "n3-sono-ue", "n3-sore-to", "n3-sore-tomo", "n3-tokorode", "n3-tsumari", "matawa", "n3-toku"]),
    "nominalization": ("Nominalização (の/こと)", "n4", ["no", "koto", "n3-no", "n3-koto", "n3-koto-da", "n3-koto-wa-ga", "n3-koto-wa-nai", "nowa-da", "n3-to-iu-no", "n3-to-iu-no-wa", "n3-to-iu-koto-da", "to-iu-koto"]),
    "quotation-report": ("Citação e relato (〜と言う/〜と思う)", "n4", ["to-iu", "to-omou", "to-kiita", "to-iwarete-iva".replace("iva","iru"), "n3-to-iu", "n3-you-ni-iu", "n3-to-iu-to", "n3-ni-yoreba"]),
    "appearance-hearsay": ("Aparência e boato (そう/よう/みたい/らしい)", "n4", ["sou-da-1", "sou-ni-sou-na", "you-da", "you-ni-you-na", "mitai-da", "mitai-na", "mitai-ni", "rashii", "n3-rashii", "n3-mitai-da", "n3-maru-de-you", "ni-mieru", "n3-furi-wo-suru"]),
    "conjecture": ("Conjectura (かもしれない/はず)", "n4", ["kamo-shirenai", "hazu-da", "hazu-ga-nai", "n3-hazu-da", "n3-moshikasuru-to-kamoshirenai", "n3-kanarazushimo-towa-kagiranai", "n3-wake-da", "n3-wake-dewa-nai", "n3-wake-ga-nai", "n3-donna-ni-koto-ka"]),
    "giving-receiving": ("Dar e receber (あげる/くれる/もらう)", "n4", ["te-ageru", "te-kureru", "te-morau", "te-yaru", "n3-ageru", "n3-kawari-ni", "n3-ni-kawatte"]),
    "keigo": ("Linguagem honorífica (敬語)", "n4", ["o-go", "de-gozaimasu", "gozaimasu", "irassharu", "itashimasu", "nasaru", "o-ni-naru", "n3-masu-you-ni"]),
    "transitivity": ("Pares transitivo/intransitivo", "n4", ["tadoushi-jidoushi"]),
    "aspect-phase": ("Início/continuação/fim da ação", "n4", ["hajimeru", "dasu", "owaru", "tsuzukeru", "n3-kake", "n3-tate"]),
    "purpose": ("Finalidade (〜ように/〜ために)", "n4", ["you-ni-suru", "n3-you-ni", "n3-you-ni-2", "n3-you-ni-3", "n3-you-ni-shimashou", "kara-tsukuru"]),
    "emphasis-limits": ("Ênfase e limites (だけ/しか/ばかり/こそ)", "n4", ["dake", "dake-de", "bakari", "n3-bakari", "n3-dake-shika", "n3-shika-nai", "n3-koso", "n3-sae", "n3-mo", "n3-nanka", "n3-nado", "n3-made", "n3-kiri", "n3-ppai", "n3-wa-mochiron-mo", "n3-mama", "n3-mama".replace("n3-mama","mama")]),
    "topics-scope": ("Escopo e referência (について/にとって/に対して)", "n3", ["n3-ni-tsuite", "n3-ni-kanshite", "n3-ni-totte", "n3-ni-taishite", "n3-ni-oite", "n3-to-shite", "n3-to-shitara", "n3-ni-shitemo", "n3-toori"]),
    "suffixes-nuance": ("Sufixos de nuance (〜やすい/〜にくい/〜すぎる)", "n4", ["yasui", "nikui", "zurai", "sugiru", "ga-suru", "ni-ki-ga-tsuku", "sasuga", "ga-hitsuyou", "hitsuyou-ga-aru"]),
}

KANA_CAP = ("kana-reading", "Leitura de kana (hiragana/katakana)", "pre-n5")
KANJI_CAP = ("kanji-recognition", "Reconhecimento de kanji", "n5")

AUTHORED = ROOT / "research" / "derived" / "repairs" / "w24_capabilities.json"
PAPER_DOC = ROOT / "design" / "exam_simulator.md"
BANKS = ROOT / "corpus" / "exam_banks"
KINDS = ("grammar", "script", "vocabulary", "phonology", "exam-readiness", "study-method")
EVIDENCE = ("recognition", "production")
KANJI_SECTIONS = {"kanji_reading", "orthography"}
_PAPER_ROW = re.compile(r"^\|\s*([a-z_]+)\s*\([^)]*\)\s*\|\s*(\d+)\*?\s*\|\s*(\d+)\*?\s*\|\s*(\d+)\*?\s*\|")


def paper_spec(doc: Path = PAPER_DOC) -> dict[str, dict[str, int]]:
    """section -> {level: items per paper}, parsed from the 'Paper structure' table of exam_simulator.md."""
    out: dict[str, dict[str, int]] = {}
    for line in doc.read_text(encoding="utf-8").splitlines():
        m = _PAPER_ROW.match(line)
        if m:
            out[m.group(1)] = {"n5": int(m.group(2)), "n4": int(m.group(3)), "n3": int(m.group(4))}
    if not out:
        raise SystemExit(f"build_capabilities: no paper table parsed from {doc}")
    return out


def lesson_objectives(con: sqlite3.Connection) -> dict[str, list[str]]:
    """lesson slug -> its pt-BR objectives, as the exporter publishes them."""
    out = {}
    for slug, val in con.execute(
            "SELECT l.slug, lt.value FROM lesson l JOIN localized_text lt ON lt.entity_type='lesson' "
            "AND lt.entity_id=l.id AND lt.field='objectives' AND lt.locale='pt-BR'"):
        out[slug] = json.loads(val) if val else []
    return out


def main() -> int:
    con = sqlite3.connect(DB)
    OUT.mkdir(parents=True, exist_ok=True)
    # W08: a grammar point merged into another (grammar_point.deprecated_by, owner decision A3) is not
    # a language feature of its own any more — its capability is the survivor's. Leaving it in would
    # put a key in grammar_keys[] that the exported registry no longer carries, which is exactly what
    # validate_graph_edges.capability_coverage fails on. Guarded on the column so a DB built before
    # scripts/migrate_grammar_merge.py still builds.
    _dep = "deprecated_by" in {r[1] for r in con.execute("PRAGMA table_info(grammar_point)")}
    gkeys = {k: (gid, lvl) for gid, k, lvl in con.execute(
        "SELECT id,key,level FROM grammar_point" + (" WHERE deprecated_by IS NULL" if _dep else ""))}
    key2cap: dict[str, str] = {}
    for cap, (_, _, keys) in CAPS.items():
        for k in keys:
            key2cap.setdefault(k, cap)
    # fallback: introducing topic bucket for unmatched keys (gp-NN and stragglers)
    topic_of = {}
    for k, (gid, lvl) in gkeys.items():
        if k in key2cap:
            continue
        r = con.execute("SELECT t.slug FROM grammar_point g JOIN topic t ON t.id=g.introducing_topic_id "
                        "WHERE g.id=?", (gid,)).fetchone()
        tslug = (r[0] if r and r[0] else f"top:{lvl}-outros").split(":", 1)[1]
        cap = f"topic:{tslug}"
        key2cap[k] = cap
        topic_of.setdefault(cap, (tslug, lvl))

    def title_of(tslug: str) -> str | None:
        r = con.execute("SELECT lt.value FROM topic t JOIN localized_text lt ON lt.entity_type='topic' "
                        "AND lt.entity_id=t.id AND lt.field='title' WHERE t.slug=?", (tslug,)).fetchone()
        return r[0] if r else None

    registry = []
    for cap, (name, lvl, _) in CAPS.items():
        keys = sorted(k for k, c in key2cap.items() if c == cap and k in gkeys)
        if keys:
            registry.append({"id": f"cap:{cap}", "kind": "grammar", "name": {"pt-BR": name}, "level": lvl,
                             "grammar_keys": keys})
    for cap, (tslug, lvl) in sorted(topic_of.items()):
        keys = sorted(k for k, c in key2cap.items() if c == cap)
        registry.append({"id": f"cap:{cap}", "kind": "grammar",
                         "name": {"pt-BR": title_of(f"top:{tslug}") or tslug}, "level": lvl, "grammar_keys": keys})
    for c, kind in ((KANA_CAP, "script"), (KANJI_CAP, "script")):
        registry.append({"id": f"cap:{c[0]}", "kind": kind, "name": {"pt-BR": c[1]}, "level": c[2],
                         "grammar_keys": []})

    # ---- W24: the authored half (can_do + curated lesson lists) ----------------------------------
    authored = {r["id"]: r for r in json.loads(AUTHORED.read_text(encoding="utf-8"))["rows"]}
    for r in authored.values():
        if "lessons" in r:          # curated kinds: phonology, study-method, cap:romaji-reading
            registry.append({"id": r["id"], "kind": r["kind"], "name": r["name"], "level": r["level"],
                             "grammar_keys": []})

    # course order, so "the lesson that unlocks the word" is the FIRST one when a word is unlocked twice
    lessons = con.execute(
        "SELECT l.id, l.slug, t.slug, m.level FROM lesson l JOIN topic t ON t.id=l.topic_id "
        "JOIN course_module m ON m.id=t.module_id ORDER BY m.ord, t.ord, l.ord").fetchall()
    topic_level = {t: lvl for _, _, t, lvl in lessons}
    vocab_topic: dict[str, str] = {}
    unlocks: dict[int, list[tuple[str, str]]] = defaultdict(list)
    for lid, typ, ref in con.execute("SELECT lesson_id, unlock_type, ref FROM lesson_unlocks"):
        unlocks[lid].append((typ, ref))
    for lid, _, tslug, _ in lessons:
        for typ, ref in unlocks[lid]:
            if typ == "vocab":
                vocab_topic.setdefault(ref, tslug)
    vocab_cap = {ref: "cap:vocab:" + t.split(":", 1)[1] for ref, t in vocab_topic.items()}

    # lesson map: capabilities INTRODUCED by each lesson (from its unlocks), plus the W24 rules
    curated: dict[str, set[str]] = defaultdict(set)
    for r in authored.values():
        for les in r.get("lessons") or []:
            curated[les].add(r["id"])
    lesson_map: dict[str, list[str]] = {}
    vocab_caps: dict[str, str] = {}          # cap id -> topic slug
    for lid, slug, tslug, _ in lessons:
        caps = set(curated.get(slug, ()))
        for typ, ref in unlocks[lid]:
            if typ == "grammar":
                k = ref.split(":", 1)[1]
                if k in key2cap:
                    caps.add(f"cap:{key2cap[k]}")
            elif typ == "kana-family":
                caps.add(f"cap:{KANA_CAP[0]}")
            elif typ == "kanji":
                caps.add(f"cap:{KANJI_CAP[0]}")
            elif typ == "vocab":
                caps.add(vocab_cap[ref])
                vocab_caps[vocab_cap[ref]] = vocab_topic[ref]
        m = re.fullmatch(r"top:(n\d)-revisao", tslug)
        if m:
            caps.add(f"cap:exam-readiness-{m.group(1)}")
        if caps:
            lesson_map[slug] = sorted(caps)
    for cid, tslug in sorted(vocab_caps.items()):
        registry.append({"id": cid, "kind": "vocabulary",
                         "name": {"pt-BR": f"Vocabulário: {title_of(tslug) or tslug}"},
                         "level": topic_level[tslug], "grammar_keys": []})
    for cid in sorted({c for caps in lesson_map.values() for c in caps if c.startswith("cap:exam-readiness-")}):
        registry.append({"id": cid, "kind": "exam-readiness", "name": authored[cid]["name"] if cid in authored
                         else {"pt-BR": cid}, "level": cid.rsplit("-", 1)[1], "grammar_keys": []})

    # ---- lessons[] (inverse map) + can_do, refusing anything the table cannot back ----------------
    by_cap: dict[str, list[str]] = defaultdict(list)
    for slug, caps in lesson_map.items():
        for c in caps:
            by_cap[c].append(slug)
    objectives = lesson_objectives(con)
    fails: list[str] = []
    ids = {c["id"] for c in registry}
    for cid in sorted(set(authored) - ids):
        fails.append(f"{cid}: authored row but the build derives no such capability")
    for cap in registry:
        cid = cap["id"]
        cap["lessons"] = sorted(by_cap.get(cid, []))
        a = authored.get(cid)
        if a is None:
            fails.append(f"{cid}: derived capability with no can_do row in {AUTHORED.name}")
            continue
        if a["kind"] != cap["kind"] or a["level"] != cap["level"]:
            fails.append(f"{cid}: table says {a['kind']}/{a['level']}, build derives {cap['kind']}/{cap['level']}")
        for q in a["can_do_derived_from"]:
            if q["lesson"] not in cap["lessons"]:
                fails.append(f"{cid}: can_do quotes {q['lesson']}, which the capability does not claim")
            elif q["objective"] not in objectives.get(q["lesson"], []):
                fails.append(f"{cid}: {q['lesson']} has no objective {q['objective']!r}")
        cap["can_do"] = a["can_do"]
        cap["can_do_evidence"] = a["can_do_evidence"]
        cap["can_do_derived_from"] = a["can_do_derived_from"]
    unmapped = [s for _, s, _, _ in lessons if s not in lesson_map]
    if unmapped:
        fails.append(f"{len(unmapped)} lessons map to no capability: {unmapped[:5]}")

    # ---- exam_link: each bank item's own provenance -> capabilities ------------------------------
    paper = paper_spec()
    sent_keys: dict[str, list[str]] = defaultdict(list)
    for s, k in con.execute("SELECT s.slug, g.key FROM sentence_grammar sg JOIN sentence s ON s.id=sg.sentence_id "
                            "JOIN grammar_point g ON g.id=sg.grammar_id"):
        sent_keys[s].append(k)
    read_lesson = dict(con.execute("SELECT slug, gated_to_lesson FROM reading"))
    hits: dict[str, dict[tuple[str, str], int]] = defaultdict(lambda: defaultdict(int))
    unlinked = 0
    for bank in sorted(BANKS.glob("n[0-9]_*.json")):
        level, section = bank.stem.split("_", 1)
        doc = json.loads(bank.read_text(encoding="utf-8"))
        for it in (doc if isinstance(doc, list) else doc["items"]):
            caps: set[str] = set()
            if it.get("grammar") in key2cap:
                caps.add(f"cap:{key2cap[it['grammar']]}")
            if it.get("vocab") in vocab_cap:
                caps.add(vocab_cap[it["vocab"]])
                if section in KANJI_SECTIONS:
                    caps.add(f"cap:{KANJI_CAP[0]}")
            if it.get("reading"):
                caps.update(lesson_map.get(read_lesson.get(it["reading"]) or "", []))
            if not caps:
                caps = {f"cap:{key2cap[k]}" for k in sent_keys.get(it.get("sentence") or "", []) if k in key2cap}
            caps = {c for c in caps if not c.startswith("cap:exam-readiness-")}
            unlinked += not caps
            for c in caps:
                hits[c][(level, section)] += 1
    for cap in registry:
        cid = cap["id"]
        if cap["kind"] == "exam-readiness":
            lvl = cap["level"]
            rows = [(lvl, sec, n, "paper") for sec, per in paper.items() if (n := per.get(lvl, 0)) > 0
                    and (BANKS / f"{lvl}_{sec}.json").exists()]
        else:
            rows = [(lvl, sec, n, "item-provenance") for (lvl, sec), n in hits.get(cid, {}).items()]
        cap["exam_link"] = [{"level": lvl, "section": sec, "bank": f"corpus/exam_banks/{lvl}_{sec}.json",
                             "items": n, "via": via} for lvl, sec, n, via in sorted(rows)]

    for f in fails[:20]:
        print("  FAIL", f)
    if fails:
        print(f"build_capabilities: {len(fails)} failure(s); nothing written")
        return 1

    # W37. A capability is course semantics (a syllabus grouping plus an authored can_do), Layer C, so
    # it is flagged for a teacher. lesson_map.json is a join of this registry with the lesson unlocks
    # and carries no provenance of its own (validate_provenance_json NO_PROVENANCE says why).
    for cap in registry:
        cap.update({"source": "capability-registry", "created_by": "ai", "layer": "C", "needs_review": True})
    (OUT / "registry.json").write_text(json.dumps(registry, ensure_ascii=False, indent=1), encoding="utf-8")
    (OUT / "lesson_map.json").write_text(json.dumps(lesson_map, ensure_ascii=False, indent=1), encoding="utf-8")
    kinds = defaultdict(int)
    for c in registry:
        kinds[c["kind"]] += 1
    linked = sum(1 for c in registry if c["exam_link"])
    (OUT / "INDEX.md").write_text(
        "# corpus/capabilities — language-feature registry (our format)\n\n"
        "The FIXED capability list the daily skill-SRS schedules against (roadmap C/D). Each capability has a "
        "`kind` (design/courseware_architecture.md): grammar groups map explicit grammar keys (curated groups; "
        "topic-bucket fallback so every grammar point is covered); script, vocabulary, phonology, "
        "exam-readiness and study-method capabilities carry none. `can_do` is the first-person pt-BR "
        "statement (Layer C, needs_review) with the lesson objectives it was written from quoted in "
        "`can_do_derived_from`; `exam_link` says where the exam banks assess it. `lesson_map.json` = "
        "capabilities each lesson INTRODUCES (derived from its unlocks plus the W24 rules), and every lesson "
        "is in it.\n\n"
        f"- registry: {len(registry)} capabilities ("
        + ", ".join(f"{k} {kinds[k]}" for k in KINDS) + ")\n"
        f"- lesson_map: {len(lesson_map)} lessons\n"
        f"- exam_link: {linked} capabilities, {sum(len(c['exam_link']) for c in registry)} rows\n",
        encoding="utf-8")
    unmatched = [k for k in gkeys if k not in key2cap]
    print(f"capabilities: {len(registry)} | lessons mapped: {len(lesson_map)} | unmatched grammar: "
          f"{len(unmatched)} | exam_link rows: {sum(len(c['exam_link']) for c in registry)} on {linked} caps | "
          f"bank items linked to nothing: {unlinked}")
    con.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
