/**
 * conjugation.server — the conjugation drill, backed by corpus/exercises/conjugation (18,524 items).
 *
 * The practice hub already had a "Conjugação" tile, but it served a single hardcoded question. This
 * replaces that mock with the real bank.
 *
 * `.server.ts` keeps 18,524 items out of the client bundle: a round is sampled here and only the sampled
 * items reach the loader payload, with the answer key stripped until grading — the same contract
 * exam.server holds.
 *
 * Determinism is the same property too. A round is identified by (level, seed); the same pair always
 * yields the same items in the same order with the same option shuffle, which is what lets grading
 * recompute the round from the seed instead of trusting anything the client sends back.
 */
import bankData from "../data/conjugationBank.json";

export type Level = "n5" | "n4" | "n3";
export const LEVELS: Level[] = ["n5", "n4", "n3"];
export const ROUND = 10;

interface RawItem {
  id: string; level: string; vocab_id: number; headword: string; kind: string; class?: string;
  prompt: string; form: string; form_label?: { "pt-BR"?: string };
  correct: string; kana?: string; romaji?: string; distractors: string[]; example?: string | null;
}
const BANK = bankData as unknown as Record<string, RawItem[]>;

/** mulberry32 — small seeded PRNG, deterministic across runs and platforms. */
function rng(seed: number) {
  let a = seed >>> 0;
  return () => {
    a = (a + 0x6d2b79f5) >>> 0;
    let t = Math.imul(a ^ (a >>> 15), 1 | a);
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}
function shuffle<T>(arr: T[], rand: () => number): T[] {
  const a = arr.slice();
  for (let i = a.length - 1; i > 0; i--) {
    const j = Math.floor(rand() * (i + 1));
    [a[i], a[j]] = [a[j], a[i]];
  }
  return a;
}
export function seedOf(v: string | number): number {
  if (typeof v === "number" && Number.isFinite(v)) return Math.abs(Math.trunc(v)) || 1;
  const s = String(v ?? "");
  let h = 2166136261;
  for (let i = 0; i < s.length; i++) { h ^= s.charCodeAt(i); h = Math.imul(h, 16777619); }
  return (h >>> 0) || 1;
}

export interface DrillQuestion {
  key: string; id: string; prompt: string; formLabel: string; kind: string;
  options: string[]; example?: string;
}
export interface Round { level: Level; seed: number; questions: DrillQuestion[] }

export function buildRound(level: Level, seedInput: string | number): Round {
  const seed = seedOf(seedInput);
  const rand = rng(seed);
  const bank = BANK[level] ?? [];
  const picked = shuffle(bank, rand).slice(0, ROUND);
  return {
    level, seed,
    questions: picked.map((it, i) => ({
      key: `q${i + 1}`,
      id: it.id,
      prompt: it.prompt,
      formLabel: it.form_label?.["pt-BR"] || it.form,
      kind: it.kind,
      // `correct` is deliberately absent from this payload; grading re-derives it from the bank.
      options: shuffle([it.correct, ...it.distractors], rand),
      example: it.example ?? undefined,
    })),
  };
}

export interface Graded {
  key: string; prompt: string; formLabel: string; given: string; expected: string; correct: boolean;
  kana?: string; romaji?: string;
}
/** Grade by REBUILDING the round from (level, seed). The request supplies choices, never the key. */
export function gradeRound(level: Level, seedInput: string | number, answers: Record<string, string>) {
  const round = buildRound(level, seedInput);
  const bank = BANK[level] ?? [];
  const byId = new Map(bank.map((x) => [x.id, x]));
  const questions: Graded[] = round.questions.map((q) => {
    const it = byId.get(q.id);
    const expected = it?.correct ?? "";
    const given = (answers[q.key] ?? "").trim();
    return { key: q.key, prompt: q.prompt, formLabel: q.formLabel, given, expected,
             correct: !!given && given === expected, kana: it?.kana, romaji: it?.romaji };
  });
  return { level, seed: round.seed, total: questions.length,
           right: questions.filter((q) => q.correct).length, questions };
}

export function bankSize(level: Level): number {
  return (BANK[level] ?? []).length;
}
