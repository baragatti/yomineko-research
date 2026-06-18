#!/usr/bin/env node
/**
 * sync-data — consolidate the research export (../course + ../corpus) into a handful of
 * server-only JSON files under app/data/. The prototype bundles these so it is fully
 * self-contained for deploy (Coolify) and for the copy-back-to-yomineko-prototype workflow.
 *
 * Run from the prototype/ dir:  node scripts/sync-data.mjs
 * It reads from ../course and ../corpus by default; override with YOMINEKO_RESEARCH=<path>.
 *
 * Output (app/data/): courses.json, topics.json, lessons.json, kanji.json, vocab.json,
 * grammar.json, sentences.json, kana.json — keyed by id for O(1) server lookup.
 */
import { promises as fs } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const HERE = path.dirname(fileURLToPath(import.meta.url));
const PROTO = path.resolve(HERE, "..");
const RESEARCH = process.env.YOMINEKO_RESEARCH || path.resolve(PROTO, "..");
const COURSE = path.join(RESEARCH, "course");
const CORPUS = path.join(RESEARCH, "corpus");
const OUT = path.join(PROTO, "app", "data");

const readJson = async (p) => JSON.parse(await fs.readFile(p, "utf8"));
const exists = async (p) => !!(await fs.stat(p).catch(() => null));

async function readCorpusList(sub) {
  // corpus/<sub>/{n5,n4,bank,...}.json — each a list of records; merge into one array
  const dir = path.join(CORPUS, sub);
  if (!(await exists(dir))) return [];
  const files = (await fs.readdir(dir)).filter((f) => f.endsWith(".json"));
  const out = [];
  for (const f of files) {
    const d = await readJson(path.join(dir, f));
    if (Array.isArray(d)) out.push(...d);
    else if (Array.isArray(d?.[sub])) out.push(...d[sub]);
  }
  return out;
}

function indexBy(arr, key) {
  const o = {};
  for (const it of arr) if (it && it[key] != null) o[it[key]] = it;
  return o;
}

async function main() {
  if (!(await exists(COURSE)) || !(await exists(CORPUS))) {
    console.error(`Missing research export. Looked in:\n  ${COURSE}\n  ${CORPUS}\nSet YOMINEKO_RESEARCH.`);
    process.exit(1);
  }
  await fs.mkdir(OUT, { recursive: true });

  // ---- courseware: manifest -> courses -> topics -> lesson leaves ----
  const manifest = await readJson(path.join(COURSE, "manifest.json"));
  const courses = [];
  const topics = {};
  const lessons = {};
  for (const c of manifest.courses) {
    const cdir = path.join(COURSE, c.path.replace(/\/course\.json$/, ""));
    const course = await readJson(path.join(COURSE, c.path));
    const topicStubs = [];
    for (const t of course.topics || []) {
      const tjson = await readJson(path.join(cdir, t.path));
      const lessonStubs = [];
      for (const l of tjson.lessons || []) {
        const leaf = await readJson(path.join(cdir, l.path));
        lessons[leaf.id] = leaf;
        lessonStubs.push({ id: leaf.id, order: leaf.order, title: l.title, description: l.description,
          needs: l.needs, unlocks: l.unlocks });
      }
      topics[t.id] = { id: t.id, level: tjson.level, order: tjson.order, title: tjson.title,
        theme: tjson.theme, objectives: tjson.objectives, unlocks_summary: t.unlocks_summary,
        lessons: lessonStubs };
      topicStubs.push({ id: t.id, order: t.order, title: t.title, theme: t.theme,
        lesson_count: t.lesson_count, unlocks_summary: t.unlocks_summary, lessons: lessonStubs.map((x) => x.id) });
    }
    courses.push({ id: c.id, level: c.level, order: c.order, title: c.title,
      topic_count: c.topic_count, lesson_count: c.lesson_count, overview: course.overview,
      topics: topicStubs });
  }

  // ---- corpus registries ----
  const kanji = indexBy(await readCorpusList("kanji"), "character");
  const vocab = indexBy(await readCorpusList("vocab"), "headword");
  const grammar = indexBy(await readCorpusList("grammar"), "key");
  // sentences: ship the WHOLE bank but SLIM — drop the heavy per-token / per-particle analysis (the UI
  // never shows it), keep the display fields + grammar tags + literal/structure so EVERY detail page can
  // surface example sentences. Server-only (corpus.server imports this); pages render only a handful each,
  // so the no-leak rule still holds. Full slim bank is ~3.5MB.
  // rebuild a SPACE-SEPARATED romaji from the per-token romaji (the bank's `romaji` field is glued together,
  // e.g. "ikuradesuka?"); fall back to the raw field. Tighten spaces before punctuation.
  const spacedRomaji = (s) => {
    const toks = (s.tokens || []).map((t) => t.romaji).filter(Boolean);
    if (!toks.length) return s.romaji || "";
    return toks.join(" ").replace(/\s+([?!,.;:、。？！])/g, "$1").trim();
  };
  // ship the per-token / per-particle breakdown for EVERY sentence, so the word-by-word "Análise" dissection
  // is available wherever a sentence appears (lessons + detail-page examples). It is slimmed (display fields
  // only) and server-only, so it never reaches the client except as the handful of sentences a page renders.
  const pt = (v) => (v && typeof v === "object" ? v["pt-BR"] ?? v.en ?? "" : v ?? "");
  const slimToken = (t) => ({ s: t.surface, r: t.reading, ro: t.romaji, pos: t.pos, gloss: pt(t.gloss), role: pt(t.role) });
  const slimParticle = (p) => ({ p: p.particle, ft: p.function_type, fn: pt(p.function), ex: pt(p.explanation) });
  const slimSentence = (s) => ({
    slug: s.slug, jp: s.jp, kana: s.kana, romaji: spacedRomaji(s),
    translation: s.translation, translation_literal: s.translation_literal,
    structure_explanation: s.structure_explanation, level: s.level, grammar: s.grammar || [],
    tokens: (s.tokens || []).map(slimToken),
    particles: (s.particles || []).map(slimParticle),
  });
  const sentences = {};
  for (const s of await readCorpusList("sentences")) if (s && s.slug) sentences[s.slug] = slimSentence(s);
  let kana = {};
  const kanaFam = path.join(CORPUS, "kana", "families.json");
  if (await exists(kanaFam)) kana = await readJson(kanaFam);

  const write = async (name, data) =>
    fs.writeFile(path.join(OUT, name), JSON.stringify(data) + "\n", "utf8");
  await write("courses.json", courses);
  await write("topics.json", topics);
  await write("lessons.json", lessons);
  await write("kanji.json", kanji);
  await write("vocab.json", vocab);
  await write("grammar.json", grammar);
  await write("sentences.json", sentences);
  await write("kana.json", kana);

  console.log(`synced -> app/data/  courses=${courses.length} topics=${Object.keys(topics).length} ` +
    `lessons=${Object.keys(lessons).length} kanji=${Object.keys(kanji).length} vocab=${Object.keys(vocab).length} ` +
    `grammar=${Object.keys(grammar).length} sentences=${Object.keys(sentences).length}`);
}

main().catch((e) => { console.error(e); process.exit(1); });
