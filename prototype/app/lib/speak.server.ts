/**
 * speak.server — the speaking-first path (course/speak). Spec: design/speaking_path.md.
 *
 * Units store corpus IDs and nothing else, which is the whole point of the path being a re-ordering
 * rather than a second corpus. Resolving those IDs is this module's only job; the corpus maps come from
 * corpus.server so both paths read the same data.
 *
 * `.server.ts` keeps it off the client, same as everywhere else.
 */
import speakData from "../data/speakPath.json";
import examBanksData from "../data/examBanks.json";
import { getSentence, sentenceView, allVocab, allGrammar, loc, type SentenceView } from "./corpus.server";

interface RawCheckpoint { id: string; type: string; via: string; distractors?: string[] }
interface RawUnit {
  id: string; stage: string; order: number; title: Record<string, string>;
  say_now: string[]; chunk_phrases: string[]; untranslated: string[];
  words: string[]; patterns: string[]; kanji_recognition: string[];
  checkpoint?: RawCheckpoint[];
  drills?: { pattern: string; examples: string[] }[];
  production?: { prompt_pt: string; answer_key: string; accepted_variants: string[]; sentence: string }[];
  fluency?: { prompt_pt: string; items: string[]; seconds_target: number } | null;
  strands?: Record<string, number>;
  real_phrases: number; cumulative_known_vocab: number;
}
interface RawStage {
  slug: string; order: number; title: Record<string, string>; approx_band: string;
  unit_count: number; unit_ids: string[];
}
const PATH = speakData as unknown as {
  title?: Record<string, string>; description?: Record<string, string>;
  stages: RawStage[]; units: Record<string, RawUnit>;
  totals: { stages?: number; units?: number; phrases?: number; real_phrases?: number;
            vocab_introduced?: number };
  shortfall?: { stage: string; units?: number; want: number; unit?: number; got?: number }[];
};

// The synced vocab/grammar maps are keyed by headword and by grammar key, but units reference SLUGS.
// Build the slug indexes once at module load rather than scanning 7,301 entries per request.
const vocabBySlug = new Map<string, any>();
for (const v of allVocab()) if (v?.slug) vocabBySlug.set(v.slug, v);
const grammarBySlug = new Map<string, any>();
for (const g of allGrammar()) if (g?.slug) grammarBySlug.set(g.slug, g);

/**
 * Checkpoint items are exam-bank rows referenced by id. Index them once so a unit can resolve its
 * handful without scanning 6,048 rows, and note that the unit may OVERRIDE the bank's distractors with
 * ones drawn from the learner's known set (build_speaking_checkpoints.py explains why).
 */
interface BankItem {
  id: string; type?: string; stem?: string; question?: string; target?: string;
  correct?: string; distractors?: string[]; wrong?: string[]; pieces?: string[]; answer?: string;
}
const bankById = new Map<string, BankItem>();
for (const byType of Object.values(examBanksData as unknown as Record<string, Record<string, BankItem[]>>)) {
  for (const rows of Object.values(byType)) for (const it of rows) bankById.set(it.id, it);
}

export interface CheckpointQuestion {
  key: string; type: string; via: string;
  prompt: string; options: string[]; pieces?: string[];
}
export interface SpeakWord { slug: string; headword: string; kana: string; romaji: string; level: string }
export interface SpeakPattern { slug: string; key: string; label: string; level: string }
export interface SpeakDrill { pattern: string; label: string; examples: { jp: string; pt: string }[] }
export interface SpeakProduction { key: string; promptPt: string }
export interface SpeakFluency { promptPt: string; seconds: number; items: { jp: string; pt: string }[] }
export interface SpeakUnit {
  id: string; stage: string; stageTitle: string; order: number; title: string;
  phrases: (SentenceView & { chunk: boolean })[];
  words: SpeakWord[]; patterns: SpeakPattern[]; signage: string[];
  checkpoint: CheckpointQuestion[];
  drills: SpeakDrill[]; production: SpeakProduction[]; fluency: SpeakFluency | null;
  strands: Record<string, number>;
  knownSoFar: number; prev: string | null; next: string | null;
}

/** Grade the production block. Answers arrive as typed Japanese; the key never leaves the server. */
export function gradeProduction(stageKey: string, order: number, answers: Record<string, string>) {
  const id = `speak:${stageKey}-${String(order).padStart(2, "0")}`;
  const u = PATH.units[id];
  const strip = (s: string) => s.replace(/[\s　。、！？!?…，,．.]/g, "");
  const out = (u?.production ?? []).map((p, i) => {
    const given = (answers[`p${i + 1}`] ?? "").trim();
    // accepted_variants already covers punctuation/spacing; strip() is the last-resort comparison so a
    // learner is never failed for a mark their IME did not produce.
    const ok = !!given && (p.accepted_variants.includes(given) || strip(given) === strip(p.answer_key));
    return { key: `p${i + 1}`, promptPt: p.prompt_pt, given, expected: p.answer_key, correct: ok };
  });
  return { total: out.length, right: out.filter((x) => x.correct).length, items: out };
}

// Moved to the client-safe module: the unit page renders these in its component, and importing them
// from here pulls the whole speaking path into the client bundle. See ~/lib/speak.
export { checkpointLabel, splitUnitId } from "./speak";
import { splitUnitId } from "./speak";

/**
 * Deterministic option order. The unit is a fixed page, not a fresh attempt, so the shuffle is keyed on
 * the item id: reloading must not reshuffle (that would look like a different question), and the order
 * must not be "correct answer first", which is what the raw bank gives.
 */
function ordered(id: string, opts: string[]): string[] {
  return opts
    .map((o) => [`${id}${o}`.split("").reduce((h, c) => (Math.imul(h ^ c.charCodeAt(0), 16777619) >>> 0), 2166136261), o] as const)
    .sort((a, b) => a[0] - b[0])
    .map(([, o]) => o);
}

function question(cp: RawCheckpoint, n: number): CheckpointQuestion | null {
  const it = bankById.get(cp.id);
  if (!it) return null;
  const key = `${cp.type}-${n}`;
  if (it.pieces?.length && it.answer) {
    return { key, type: cp.type, via: cp.via, prompt: "", options: [],
             pieces: ordered(cp.id, it.pieces) };
  }
  const correct = it.correct ?? "";
  const wrong = cp.distractors ?? it.distractors ?? it.wrong ?? [];
  const prompt = it.question || it.stem || (it.target ? `「${it.target}」` : "");
  if (!prompt || !correct || wrong.length < 2) return null;
  return { key, type: cp.type, via: cp.via, prompt, options: ordered(cp.id, [correct, ...wrong]) };
}

/** The answer key stays here; the page never receives it. Grading re-resolves from the unit. */
export function gradeCheckpoint(stageKey: string, order: number, answers: Record<string, string>) {
  const id = `speak:${stageKey}-${String(order).padStart(2, "0")}`;
  const u = PATH.units[id];
  const out: { key: string; prompt: string; given: string; expected: string; correct: boolean }[] = [];
  (u?.checkpoint ?? []).forEach((cp, i) => {
    const it = bankById.get(cp.id);
    const q = question(cp, i + 1);
    if (!it || !q) return;
    const expected = it.answer ?? it.correct ?? "";
    const given = (answers[q.key] ?? "").trim();
    const norm = (s: string) => (cp.type === "sentence_order" ? s.replace(/\s+/g, "") : s);
    out.push({ key: q.key, prompt: q.prompt || (q.pieces ?? []).join(" "), given, expected,
               correct: !!given && norm(given) === norm(expected) });
  });
  return { total: out.length, right: out.filter((q) => q.correct).length, questions: out };
}

export const stages = () => PATH.stages.map((s) => ({
  slug: s.slug,
  key: s.slug.split(":")[1],
  order: s.order,
  title: loc(s.title),
  band: s.approx_band,
  unitIds: s.unit_ids,
  units: s.unit_count,
  phrases: s.unit_ids.reduce((a, id) => a + (PATH.units[id]?.say_now.length ?? 0), 0),
  words: s.unit_ids.reduce((a, id) => a + (PATH.units[id]?.words.length ?? 0), 0),
}));

export const pathTotals = () => PATH.totals;
export const pathShortfall = () => PATH.shortfall ?? [];

/** Flat unit order across the whole path — what "next" means when a stage ends. */
const ORDER: string[] = PATH.stages.flatMap((s) => s.unit_ids);

/** Resolve a sentence slug to the pair a drill or fluency list shows. */
function phrase(slug: string): { jp: string; pt: string } | null {
  const s = getSentence(slug);
  if (!s) return null;
  const v = sentenceView(s);
  return { jp: v.jp, pt: v.pt };
}

export function getUnit(stageKey: string, order: number): SpeakUnit | null {
  const id = `speak:${stageKey}-${String(order).padStart(2, "0")}`;
  const u = PATH.units[id];
  if (!u) return null;
  const stage = PATH.stages.find((s) => s.slug === u.stage);
  const chunks = new Set(u.chunk_phrases);
  const i = ORDER.indexOf(id);

  return {
    id,
    stage: stageKey,
    stageTitle: loc(stage?.title ?? {}),
    order: u.order,
    title: loc(u.title),
    phrases: u.say_now
      .map((slug) => {
        const s = getSentence(slug);
        return s ? { ...sentenceView(s), chunk: chunks.has(slug) } : null;
      })
      .filter(Boolean) as (SentenceView & { chunk: boolean })[],
    words: u.words.map((slug) => {
      const v = vocabBySlug.get(slug);
      if (!v) return null;
      // Show the word AS THE PHRASE WRITES IT. Our headwords are JMdict's kanji forms, some of which no
      // one uses: ズボン is headworded 洋袴, なる as 生る, これ as 此れ. Displaying those to a beginner on
      // a recognition-only path is noise. If the headword's kanji is nowhere in this unit's phrases, the
      // learner has not seen that spelling, so lead with the kana.
      const jp = u.say_now.map((s) => getSentence(s)?.jp ?? "").join("");
      const kanji = [...String(v.headword)].filter((c) => /[一-鿿]/.test(c));
      const written = kanji.length > 0 && kanji.every((c) => jp.includes(c));
      return { slug, headword: written || !kanji.length ? v.headword : v.kana,
               kana: v.kana, romaji: v.romaji ?? "", level: v.level ?? "" };
    }).filter(Boolean) as SpeakWord[],
    patterns: u.patterns.map((slug) => {
      const g = grammarBySlug.get(slug);
      return g ? { slug, key: g.key, label: loc(g.label) || g.key, level: g.level ?? "" } : null;
    }).filter(Boolean) as SpeakPattern[],
    signage: u.kanji_recognition ?? [],
    checkpoint: (u.checkpoint ?? []).map((cp, k) => question(cp, k + 1)).filter(Boolean) as CheckpointQuestion[],
    drills: (u.drills ?? []).map((d) => ({
      pattern: d.pattern,
      label: loc(grammarBySlug.get(d.pattern)?.label) || grammarBySlug.get(d.pattern)?.key || d.pattern,
      examples: d.examples.map(phrase).filter(Boolean) as { jp: string; pt: string }[],
    })),
    // The answer key is deliberately NOT in this payload; only the pt-BR prompt crosses the wire.
    production: (u.production ?? []).map((p, i) => ({ key: `p${i + 1}`, promptPt: p.prompt_pt })),
    fluency: u.fluency
      ? { promptPt: u.fluency.prompt_pt, seconds: u.fluency.seconds_target,
          items: u.fluency.items.map(phrase).filter(Boolean) as { jp: string; pt: string }[] }
      : null,
    strands: u.strands ?? {},
    knownSoFar: u.cumulative_known_vocab,
    prev: i > 0 ? ORDER[i - 1] : null,
    next: i >= 0 && i < ORDER.length - 1 ? ORDER[i + 1] : null,
  };
}


