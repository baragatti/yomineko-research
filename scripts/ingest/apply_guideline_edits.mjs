#!/usr/bin/env node
/**
 * Apply verified, exact-match guideline/phonetics edits to the lesson authoring source
 * (research/derived/lessons/*.json). Deterministic + guarded:
 *  - operates on DECODED field strings (body / exercise prompt / explanation), real quotes
 *  - replace: applies only if `find` occurs EXACTLY ONCE; else skip+log
 *  - insert: places insertText before/after a unique `find` anchor
 *  - defensive: rejects any edit whose new text introduces emoji / em-dash / ≠ / backslash
 * Usage: node scripts/ingest/apply_guideline_edits.mjs <edits.json> [--write]
 */
import { promises as fs } from "node:fs";
import path from "node:path";

const DIR = "research/derived/lessons";
const editsPath = process.argv[2];
const WRITE = process.argv.includes("--write");
const BAD = /[—≠]|\|[\u{1F300}-\u{1FAFF}\u{2600}-\u{27BF}\u{2B00}-\u{2BFF}]/u;

const count = (h, n) => {
  if (!n) return 0;
  let c = 0, p = 0, k;
  while ((k = h.indexOf(n, p)) !== -1) { c++; p = k + n.length; }
  return c;
};

const norm = (s) => (s || "").replace(/^les:/, "");
const map = {};
for (const f of (await fs.readdir(DIR)).filter((x) => x.endsWith(".json"))) {
  const obj = JSON.parse(await fs.readFile(path.join(DIR, f), "utf8"));
  map[norm(obj.slug)] = { file: f, obj, changed: false };
}

const edits = JSON.parse(await fs.readFile(editsPath, "utf8"));
const stat = { applied: 0, skipped: 0, byCat: {}, bySev: {}, skips: [] };

function getField(obj, e) {
  if (e.target === "body") return [obj, "body", obj.body || ""];
  const ex = (obj.exercises || []).find((x) => x.slug === e.exerciseSlug);
  if (!ex) return null;
  const key = e.target === "exercise_prompt" ? "prompt" : "explanation";
  const v = ex[key];
  if (typeof v !== "string") return null;
  return [ex, key, v];
}

for (const e of edits) {
  const entry = map[norm(e.slug)];
  const skip = (why) => { stat.skipped++; stat.skips.push(`${e.slug} [${e.category}/${e.severity}] ${why}: ${JSON.stringify((e.find || "").slice(0, 50))}`); };
  if (!entry) { skip("unknown slug"); continue; }
  const fld = getField(entry.obj, e);
  if (!fld) { skip("field not found"); continue; }
  const [holder, key, cur] = fld;
  const newText = e.kind === "replace" ? e.replace : e.insertText;
  if (newText == null) { skip("no new text"); continue; }
  if (BAD.test(newText)) { skip("new text has banned char"); continue; }
  if (count(cur, e.find) !== 1) { skip(`find not unique (n=${count(cur, e.find)})`); continue; }
  const updated = e.kind === "replace"
    ? cur.replace(e.find, newText)
    : (e.position === "before" ? cur.replace(e.find, newText + e.find) : cur.replace(e.find, e.find + newText));
  holder[key] = updated;
  entry.changed = true;
  stat.applied++;
  stat.byCat[e.category] = (stat.byCat[e.category] || 0) + 1;
  stat.bySev[e.severity] = (stat.bySev[e.severity] || 0) + 1;
}

let files = 0;
for (const slug of Object.keys(map)) {
  const en = map[slug];
  if (en.changed) { files++; if (WRITE) await fs.writeFile(path.join(DIR, en.file), JSON.stringify(en.obj, null, 2) + "\n", "utf8"); }
}
console.log(JSON.stringify({ mode: WRITE ? "write" : "dry", applied: stat.applied, skipped: stat.skipped, filesChanged: files, byCategory: stat.byCat, bySeverity: stat.bySev }, null, 1));
if (stat.skips.length) { console.log("--- SKIPS ---"); stat.skips.slice(0, 60).forEach((s) => console.log("  " + s)); }
