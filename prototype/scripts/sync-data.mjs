#!/usr/bin/env node
/**
 * sync-data — project the research export into prototype/app/data/, DRIVEN BY contracts/manifest.json.
 *
 * Run from prototype/:  node scripts/sync-data.mjs   (npm run sync-data)
 * Reads ../contracts/manifest.json, ../corpus and ../course; override the root with YOMINEKO_RESEARCH.
 *
 * ─── WHY IT READS THE MANIFEST ────────────────────────────────────────────────────────────────
 * This script used to hardcode its own globs (`corpus/<sub>/*.json`) and its own key conventions,
 * so app/data was a SECOND, undocumented address space sitting beside contracts/manifest.json —
 * the two agreed by luck (readiness finding G5). Nothing here decides where data lives any more:
 *
 *   WHERE    each entity's `files` glob, resolved below. Segment-wise `*` and `[...]` / `[!...]`,
 *            the only wildcards the manifest uses; no `**`.
 *   HOW      each entity's `packing` — `list` (the file is an array of records), `single` (the file
 *            IS one record), `map` (the file is a keyed collection, copied through untouched).
 *   ADDRESS  each entity's `stable_id_field`, or its `natural_key` when it has no stable id.
 *            Every map written below is keyed by the FULL value of that field — "kanji:日", never
 *            "日" — because the manifest's id_convention says the prefixed stable id IS the public
 *            address of a record. app/data no longer mints a short key of its own; the app derives
 *            the prefix it needs from `_build.json`'s `namespaces` (see corpus.server.ts).
 *   COUNT    each entity's `records`. An empty glob, a count that disagrees with the manifest, or
 *            two records claiming one address is a HARD ERROR — a sync that quietly ships less than
 *            the corpus holds is exactly the failure this script exists to prevent.
 *   CLASS    the 7 `class: "runtime"` entities (user_state, minted per learner) are skipped BY
 *            CLASS, never by an absent glob, so a content entity whose exporter stopped cannot pass
 *            itself off as runtime.
 *   SCOPE    the app's input tree is the two published data roots, `corpus/` and `course/`. A
 *            content entity whose glob points elsewhere (today: `review_ledger`, under
 *            research/derived/) is out of scope and is reported, not loaded — the prototype must
 *            build from a deploy tree that carries only the two roots.
 *
 * ─── WHAT IT WRITES ──────────────────────────────────────────────────────────────────────────
 * One file per read model the app imports. "keyed by" is always a manifest field, never a
 * convention invented here. `slim` = display fields only (the heavy analyzer output is dropped;
 * see slimSentence / slimReading), which is the sole place a record is narrowed.
 *
 *   file                   manifest entities                value                keyed by
 *   ---------------------  -------------------------------  -------------------  ----------------------
 *   courses.json           course_manifest + course         course + topic stubs course.stable_id_field
 *                          (+ topic, lesson for the stubs)                       ("mod:pre-n5")
 *   topics.json            topic (+ lesson for the stubs)   topic + lesson stubs topic.stable_id_field
 *   lessons.json           lesson                           whole record         lesson.stable_id_field
 *   kanji.json             kanji                            whole record         kanji.stable_id_field
 *   vocab.json             vocab                            whole record         vocab.stable_id_field
 *   grammar.json           grammar                          whole record         grammar.stable_id_field
 *   sentences.json         sentence                         slim record          sentence.stable_id_field
 *   readings.json          reading                          slim record          reading.stable_id_field
 *   strokes.json           stroke_order                     whole record         stroke_order.natural_key
 *   strokeLines.json       stroke_lines                     { strokes }          stroke_lines.natural_key
 *   kanaStrokes.json       stroke_kana                      whole record         stroke_kana.natural_key
 *   kana.json              kana_family                      the map, verbatim    (packing: map)
 *   examBanks.json         exam_item                        level -> type -> []  see EXAM TYPE below
 *   conjugationBank.json   exercise_conjugation             level -> []          record.level
 *   roleBank.json          exercise_role                    level -> []          record.level
 *   speakPath.json         speak_path + speak_unit          path + units map     speak_unit.stable_id_field
 *   _build.json            (the manifest itself)            release identity     —
 *
 * EXAM TYPE is the one facet no record carries: an exam_item has `level` but not `type`. The type is
 * the source basename after `n<digit>_`, which is precisely what the manifest glob
 * `corpus/exam_banks/n[0-9]_*.json` enumerates — so it is read off the file the manifest matched,
 * and every item's own `level` is checked against that same basename.
 *
 * _build.json is the release identity: contracts/manifest.json's `build` block (date, git_head and
 * the per-entity content hashes) copied verbatim, plus the entity->namespace map the app uses to
 * qualify a route parameter into a stable id, plus what each output actually holds. The app can
 * print what it runs, and scripts/validate/validate_prototype_sync.py fails when these hashes drift
 * from the manifest — a stale sync is detectable by hash, not by file count.
 *
 * Everything here is server-only: app/data is imported exclusively from *.server.ts, and
 * scripts/validate/validate_no_client_leak.py enforces that against the built client bundle.
 */
import { promises as fs } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const HERE = path.dirname(fileURLToPath(import.meta.url));
const PROTO = path.resolve(HERE, "..");
const RESEARCH = process.env.YOMINEKO_RESEARCH || path.resolve(PROTO, "..");
const MANIFEST = path.join(RESEARCH, "contracts", "manifest.json");
const OUT = path.join(PROTO, "app", "data");

/** The published data roots the prototype builds from. A content entity outside these is out of scope. */
const DATA_ROOTS = ["corpus/", "course/"];

const readJson = async (p) => JSON.parse(await fs.readFile(p, "utf8"));
const fail = (msg) => { throw new Error(msg); };

/* ------------------------------------------------------------------ manifest glob resolution */

/** One path segment of a manifest glob -> RegExp. Supports `*` and `[...]` / `[!...]`; no `**`. */
function segmentToRegExp(segment) {
  let src = "";
  for (let i = 0; i < segment.length; i++) {
    const c = segment[i];
    if (c === "*") { src += "[^/]*"; continue; }
    if (c === "?") { src += "[^/]"; continue; }
    if (c === "[") {
      let j = i + 1;
      let negated = false;
      if (segment[j] === "!" || segment[j] === "^") { negated = true; j++; }
      let cls = "";
      while (j < segment.length && segment[j] !== "]") { cls += segment[j]; j++; }
      if (j >= segment.length) fail(`unterminated [...] in manifest glob segment "${segment}"`);
      src += `[${negated ? "^" : ""}${cls}]`;
      i = j;
      continue;
    }
    src += c.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
  }
  return new RegExp(`^${src}$`);
}

/** Resolve a manifest `files` glob under `root` into a sorted list of absolute file paths. */
async function resolveGlob(root, glob) {
  let current = [root];
  const segments = glob.split("/");
  for (const segment of segments) {
    const re = segmentToRegExp(segment);
    const next = [];
    for (const dir of current) {
      let entries;
      try { entries = await fs.readdir(dir, { withFileTypes: true }); } catch { continue; }
      for (const e of entries) if (re.test(e.name)) next.push(path.join(dir, e.name));
    }
    current = next;
  }
  return current.sort();
}

/* ------------------------------------------------------------------ manifest-driven loading */

/**
 * Load one content entity exactly as the manifest describes it.
 *
 * Returns { spec, groups, records, map, byId } where `groups` keeps the per-file split (the exam
 * banks need it), `records` is the flat record list for list/single packing, `map` is the verbatim
 * object for map packing, and `byId` is the address index when the entity declares an address.
 */
async function loadEntity(spec) {
  const files = await resolveGlob(RESEARCH, spec.files);
  if (!files.length) fail(`${spec.entity}: manifest glob "${spec.files}" matched no file — an empty content entity is a failure, not an empty entity`);

  const groups = [];
  const records = [];
  let map = null;
  for (const file of files) {
    const data = await readJson(file);
    if (spec.packing === "list") {
      if (!Array.isArray(data)) fail(`${spec.entity}: ${path.relative(RESEARCH, file)} is packed "list" in the manifest but is not an array`);
      groups.push({ file, basename: path.basename(file, ".json"), records: data });
      records.push(...data);
    } else if (spec.packing === "single") {
      if (Array.isArray(data)) fail(`${spec.entity}: ${path.relative(RESEARCH, file)} is packed "single" in the manifest but is an array`);
      groups.push({ file, basename: path.basename(file, ".json"), records: [data] });
      records.push(data);
    } else if (spec.packing === "map") {
      if (Array.isArray(data) || typeof data !== "object" || data === null) fail(`${spec.entity}: ${path.relative(RESEARCH, file)} is packed "map" in the manifest but is not an object`);
      if (map) fail(`${spec.entity}: packing "map" matched ${files.length} files; a keyed collection must be a single file`);
      map = data;
      groups.push({ file, basename: path.basename(file, ".json"), records: [] });
    } else {
      fail(`${spec.entity}: unknown packing "${spec.packing}"`);
    }
  }

  if (spec.records !== null && spec.records !== undefined && spec.packing !== "map" && records.length !== spec.records)
    fail(`${spec.entity}: manifest declares ${spec.records} records, the glob yields ${records.length} — re-run the exporter and scripts/contracts/build_manifest.py`);

  // The address: the stable id when there is one, the natural key when there is not. A composite
  // natural key ("user_id,feature") never occurs on a content entity, but it is not an address here.
  const keyField = spec.stable_id_field || (spec.natural_key && !spec.natural_key.includes(",") ? spec.natural_key : null);
  let byId = null;
  if (keyField && spec.packing !== "map") {
    byId = {};
    for (const r of records) {
      const key = r?.[keyField];
      if (key === undefined || key === null) fail(`${spec.entity}: a record has no "${keyField}" — the manifest says that field is its address`);
      if (key in byId) fail(`${spec.entity}: two records share the address ${JSON.stringify(key)}; an address must be unique`);
      byId[key] = r;
    }
  }
  return { spec, files, groups, records, map, byId, keyField };
}

/* ------------------------------------------------------------------ slimming (the only narrowing) */

/** localized value -> the pt-BR string (falls back to en, then ""). */
const pt = (v) => (v && typeof v === "object" ? v["pt-BR"] ?? v.en ?? "" : v ?? "");

/**
 * A SPACE-SEPARATED romaji rebuilt from the per-token romaji: the bank's own `romaji` is glued
 * together ("ikuradesuka?"). Falls back to the raw field; tightens spaces before punctuation.
 */
const spacedRomaji = (s) => {
  const toks = (s.tokens || []).map((t) => t.romaji).filter(Boolean);
  if (!toks.length) return s.romaji || "";
  return toks.join(" ").replace(/\s+([?!,.;:、。？！])/g, "$1").trim();
};

const slimToken = (t) => ({ s: t.surface, r: t.reading, ro: t.romaji, pos: t.pos, gloss: pt(t.gloss), role: pt(t.role) });
const slimParticle = (p) => ({ p: p.particle, ft: p.function_type, fn: pt(p.function), ex: pt(p.explanation) });

/**
 * Sentences ship WHOLE but SLIM: display fields + grammar tags + the word-by-word dissection the
 * "Análise" panel renders, with the heavy per-token analyzer output dropped. Server-only — a page
 * renders a handful, so the no-leak rule holds.
 */
const slimSentence = (s) => ({
  slug: s.slug, jp: s.jp, kana: s.kana, romaji: spacedRomaji(s),
  translation: s.translation, translation_literal: s.translation_literal,
  structure_explanation: s.structure_explanation, level: s.level, grammar: s.grammar || [],
  tokens: (s.tokens || []).map(slimToken),
  particles: (s.particles || []).map(slimParticle),
});

/** Reading-practice boxes, same contract as sentences: display fields only, server-only. */
const slimReading = (r) => ({
  slug: r.slug, jp: r.jp, title: r.title, translation: r.translation,
  tokens: (r.tokens || []).map((t) => ({ s: t.s, r: t.r, ro: t.ro, pos: t.pos })),
  length_band: r.length_band, source_slugs: r.source_slugs || [],
});

/* ------------------------------------------------------------------ the read model */

/** Records the app counts, per output — the number `_build.json` publishes and the gate re-derives. */
function recordCount(name, value) {
  if (name === "examBanks.json") return Object.values(value).reduce((a, byType) => a + Object.values(byType).reduce((b, items) => b + items.length, 0), 0);
  if (name === "conjugationBank.json" || name === "roleBank.json") return Object.values(value).reduce((a, items) => a + items.length, 0);
  if (name === "speakPath.json") return Object.keys(value.units || {}).length;
  return Array.isArray(value) ? value.length : Object.keys(value).length;
}

/** Group a record list by its own `level` field. */
function byLevel(entity, records) {
  const out = {};
  for (const r of records) {
    if (!r.level) fail(`${entity}: a record has no "level" to group by`);
    (out[r.level] ||= []).push(r);
  }
  return out;
}

function buildReadModel(loaded) {
  const get = (name) => loaded.get(name) || fail(`entity "${name}" is missing from contracts/manifest.json — the app read model depends on it`);
  const out = {};

  // ---- courseware: the manifest's course list joined to course/topic/lesson records BY ID.
  // No path resolution: course_manifest, course and topic all carry the stable id of what they
  // point at, and the three entity tables above are already keyed by exactly that id.
  const courseManifest = get("course_manifest").records[0];
  const courseById = get("course").byId;
  const topicById = get("topic").byId;
  const lessonById = get("lesson").byId;
  const courses = {};
  const topics = {};
  for (const c of courseManifest.courses) {
    const course = courseById[c.id] || fail(`course_manifest points at ${c.id}, which no course record claims`);
    const topicStubs = [];
    for (const t of course.topics || []) {
      const topic = topicById[t.id] || fail(`course ${c.id} points at topic ${t.id}, which no topic record claims`);
      const lessonStubs = [];
      for (const l of topic.lessons || []) {
        const leaf = lessonById[l.id] || fail(`topic ${t.id} points at lesson ${l.id}, which no lesson record claims`);
        lessonStubs.push({ id: leaf.id, order: leaf.order, title: l.title, description: l.description,
          needs: l.needs, unlocks: l.unlocks });
      }
      topics[t.id] = { id: t.id, level: topic.level, order: topic.order, title: topic.title,
        theme: topic.theme, objectives: topic.objectives, unlocks_summary: t.unlocks_summary,
        lessons: lessonStubs };
      topicStubs.push({ id: t.id, order: t.order, title: t.title, theme: t.theme,
        lesson_count: t.lesson_count, unlocks_summary: t.unlocks_summary, lessons: lessonStubs.map((x) => x.id) });
    }
    courses[c.id] = { id: c.id, level: c.level, order: c.order, title: c.title,
      topic_count: c.topic_count, lesson_count: c.lesson_count, overview: course.overview,
      topics: topicStubs };
  }
  out["courses.json"] = courses;
  out["topics.json"] = topics;
  out["lessons.json"] = lessonById;

  // ---- registries, keyed by the manifest's address field, shipped whole.
  out["kanji.json"] = get("kanji").byId;
  out["vocab.json"] = get("vocab").byId;
  out["grammar.json"] = get("grammar").byId;

  // ---- stroke data. Three separate manifest entities, so no shape-sniffing is needed to tell the
  // Kanji Alive outlines (CC BY 4.0, `steps`) from the GlyphWiki centrelines (`strokes`) any more.
  // Public attributed data: a single character's strokes may reach the client for the animation.
  out["strokes.json"] = get("stroke_order").byId;
  out["kanaStrokes.json"] = get("stroke_kana").byId;
  const strokeLines = {};
  for (const [char, rec] of Object.entries(get("stroke_lines").byId)) strokeLines[char] = { strokes: rec.strokes };
  out["strokeLines.json"] = strokeLines;

  // ---- the kana syllabary chart: a keyed collection, copied through as the manifest packs it.
  out["kana.json"] = get("kana_family").map;

  // ---- sentences + readings, slimmed.
  const sentences = {};
  for (const [slug, s] of Object.entries(get("sentence").byId)) sentences[slug] = slimSentence(s);
  out["sentences.json"] = sentences;
  const readings = {};
  for (const [slug, r] of Object.entries(get("reading").byId)) readings[slug] = slimReading(r);
  out["readings.json"] = readings;

  // ---- exam banks: level -> type -> items. `type` is the source basename after "n<digit>_", which
  // is what the manifest glob corpus/exam_banks/n[0-9]_*.json enumerates; each item's own `level`
  // is checked against the same basename, so a misfiled item fails instead of hiding.
  const examBanks = {};
  for (const g of get("exam_item").groups) {
    const m = /^(n[0-9])_(.+)$/.exec(g.basename);
    if (!m) fail(`exam_item: ${g.basename}.json does not match the manifest glob's n<digit>_<type> shape`);
    const [, level, type] = m;
    for (const it of g.records) if (it.level !== level) fail(`exam_item ${it.id}: level "${it.level}" but it is filed in ${g.basename}.json`);
    if (g.records.length) (examBanks[level] ||= {})[type] = g.records;
  }
  out["examBanks.json"] = examBanks;

  // ---- drill banks: grouped by each record's own `level`, no filename parsing. Server-only, same
  // contract as the exam banks: the picker samples per attempt, the answer key never ships.
  out["conjugationBank.json"] = byLevel("exercise_conjugation", get("exercise_conjugation").records);
  out["roleBank.json"] = byLevel("exercise_role", get("exercise_role").records);

  // ---- the speaking-first path: the stage manifest plus every unit, keyed by the unit's stable id
  // and ordered by the stage that claims it. Units hold corpus ids only; the route resolves them
  // against the maps above.
  const speakPath = { ...get("speak_path").records[0] };
  const unitById = get("speak_unit").byId;
  const units = {};
  for (const stage of speakPath.stages || []) {
    for (const id of stage.unit_ids || []) {
      units[id] = unitById[id] || fail(`speak stage ${stage.slug} claims unit ${id}, which no speak_unit record provides`);
    }
  }
  for (const id of Object.keys(unitById)) if (!(id in units)) fail(`speak_unit ${id} is claimed by no stage`);
  speakPath.units = units;
  out["speakPath.json"] = speakPath;

  return out;
}

/* ------------------------------------------------------------------ main */

async function main() {
  const manifest = await readJson(MANIFEST).catch(() => fail(`Missing ${MANIFEST}. Set YOMINEKO_RESEARCH to the research repo root.`));
  await fs.mkdir(OUT, { recursive: true });

  const loaded = new Map();
  const skippedRuntime = [];
  const skippedOutOfTree = [];
  for (const spec of manifest.entities) {
    if (spec.class === "runtime") { skippedRuntime.push(spec.entity); continue; }
    if (spec.class !== "content") fail(`${spec.entity}: unknown class "${spec.class}"`);
    if (!spec.files) fail(`${spec.entity}: class "content" with no files glob`);
    if (!DATA_ROOTS.some((r) => spec.files.startsWith(r))) { skippedOutOfTree.push(spec.entity); continue; }
    loaded.set(spec.entity, await loadEntity(spec));
  }

  const model = buildReadModel(loaded);

  // The release identity the app prints and the sync gate compares against the manifest.
  const namespaces = {};
  for (const spec of manifest.entities) {
    if (Array.isArray(spec.id_namespace) && spec.id_namespace.length === 1) namespaces[spec.entity] = spec.id_namespace[0];
  }
  const outputs = {};
  for (const [name, value] of Object.entries(model)) outputs[name] = { records: recordCount(name, value) };
  const build = {
    note: "Release identity, copied from contracts/manifest.json by scripts/sync-data.mjs. `entities` are that manifest's per-entity content hashes: when they drift from the manifest, app/data is stale. `namespaces` maps an entity to its single id namespace, so a route parameter can be qualified into a stable id without hardcoding the prefix.",
    manifest_schema_version: manifest.schema_version,
    date: manifest.build.date,
    git_head: manifest.build.git_head,
    entities: manifest.build.entities,
    namespaces,
    outputs,
  };

  const write = async (name, data) => fs.writeFile(path.join(OUT, name), JSON.stringify(data) + "\n", "utf8");
  for (const [name, value] of Object.entries(model)) await write(name, value);
  await write("_build.json", build);

  const counts = Object.entries(outputs).map(([n, o]) => `${n.replace(/\.json$/, "")}=${o.records}`).join(" ");
  console.log(`synced -> app/data/  build ${build.date} @ ${build.git_head.slice(0, 8)}`);
  console.log(`  ${loaded.size} content entities read from contracts/manifest.json, ` +
    `${skippedRuntime.length} runtime skipped by class (${skippedRuntime.join(", ")})` +
    (skippedOutOfTree.length ? `, ${skippedOutOfTree.length} outside corpus//course/ (${skippedOutOfTree.join(", ")})` : ""));
  const unused = [...loaded.keys()].filter((e) => !["course_manifest", "course", "topic", "lesson", "kanji", "vocab", "grammar",
    "sentence", "reading", "stroke_order", "stroke_lines", "stroke_kana", "kana_family", "exam_item",
    "exercise_conjugation", "exercise_role", "speak_path", "speak_unit"].includes(e));
  if (unused.length) console.log(`  loaded but not yet consumed by the app: ${unused.join(", ")}`);
  console.log(`  ${counts}`);
}

main().catch((e) => { console.error(e.message || e); process.exit(1); });
