/**
 * roles.server — the role-identification drill, backed by corpus/exercises/roles (5,911 items).
 *
 * The drill asks which CHUNK of a sentence plays a named grammatical role, and every answer is derived
 * from the particle that closes the chunk rather than judged. That is the whole reason this drill exists
 * instead of the word-order one the practice hub mocks: Japanese word order is flexible, so an
 * auto-graded reassembly item cannot tell the learner which of several correct orders it wanted, while
 * "which part is the direct object" has exactly one answer.
 *
 * Same server-only contract as conjugation.server and exam.server: the bank stays out of the client
 * bundle, a round is sampled here, and `correct` is stripped from the loader payload until grading.
 * A round is identified by (level, seed) and grading REBUILDS it from that pair, so the request supplies
 * choices and never the key.
 */
import bankData from "../data/roleBank.json";

// Re-exported from the client-safe module: the component needs ROUND, and importing it from here
// would pull this entire file (and the 5,358-item bank) into the client bundle. See ~/lib/drill.
export { LEVELS, ROUND, type Level } from "./drill";
import { ROUND, type Level } from "./drill";

interface RawItem {
  id: string; level: string; sentence: string; jp: string; role: string;
  prompt: { "pt-BR"?: string }; correct: string; particle: string | null; distractors: string[];
}
const BANK = bankData as unknown as Record<string, RawItem[]>;

/**
 * What each role is called back to the learner once the answer is revealed. Neutral key -> pt-BR.
 *
 * The ARTICLE is part of the value, not glued on at the call site: `origem` is feminine and every other
 * role here is masculine, so a hardcoded "o " produced "o origem". And the particle is deliberately NOT
 * repeated in the label — the sentence that uses this already prints the particle right after it, which
 * gave "o destino (へ) aqui é へ".
 */
const ROLE_PT: Record<string, string> = {
  topic: "o tópico", subject: "o sujeito", object: "o objeto direto", predicate: "o predicado",
  modifier: "o modificador", from: "a origem", direction: "o destino", until: "o limite",
  also: "a parte marcada por も", than: "o termo de comparação",
};

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

/**
 * Pick ROUND items, ROUND-ROBIN over the roles rather than uniformly over the bank.
 *
 * Uniform sampling is wrong here for two reasons the distribution makes plain. `predicate` is 40% of the
 * N5 bank, so a flat draw gives a round that is mostly one question repeated. And the bank holds up to
 * five items per sentence, so a flat draw can ask about the same sentence twice — at which point the
 * first question has already eliminated an option for the second, and the learner answers by arithmetic
 * instead of by grammar. Both are fixed here: one item per sentence, and the roles take turns.
 */
function pick(bank: RawItem[], rand: () => number): RawItem[] {
  const byRole = new Map<string, RawItem[]>();
  for (const it of bank) {
    const list = byRole.get(it.role);
    if (list) list.push(it); else byRole.set(it.role, [it]);
  }
  const queues = shuffle([...byRole.keys()], rand).map((r) => shuffle(byRole.get(r)!, rand));
  const out: RawItem[] = [];
  const usedSentences = new Set<string>();
  for (let pass = 0; out.length < ROUND && pass < 200; pass++) {
    let progressed = false;
    for (const q of queues) {
      if (out.length >= ROUND) break;
      while (q.length) {
        const it = q.pop()!;
        if (usedSentences.has(it.sentence)) continue;
        usedSentences.add(it.sentence);
        out.push(it);
        progressed = true;
        break;
      }
    }
    if (!progressed) break;   // every queue drained
  }
  return out;
}

export interface DrillQuestion {
  key: string; id: string; jp: string; prompt: string; options: string[];
}
export interface Round { level: Level; seed: number; questions: DrillQuestion[] }

export function buildRound(level: Level, seedInput: string | number): Round {
  const seed = seedOf(seedInput);
  const rand = rng(seed);
  const picked = pick(BANK[level] ?? [], rand);
  return {
    level, seed,
    questions: picked.map((it, i) => ({
      key: `q${i + 1}`,
      id: it.id,
      jp: it.jp,
      prompt: it.prompt["pt-BR"] || "",
      // `correct` is deliberately absent from this payload; grading re-derives it from the bank.
      options: shuffle([it.correct, ...it.distractors], rand),
    })),
  };
}

export interface Graded {
  key: string; jp: string; prompt: string; given: string; expected: string; correct: boolean;
  role: string; roleLabel: string; particle: string | null;
}
/** Grade by REBUILDING the round from (level, seed). The request supplies choices, never the key. */
export function gradeRound(level: Level, seedInput: string | number, answers: Record<string, string>) {
  const round = buildRound(level, seedInput);
  const byId = new Map((BANK[level] ?? []).map((x) => [x.id, x]));
  const questions: Graded[] = round.questions.map((q) => {
    const it = byId.get(q.id);
    const expected = it?.correct ?? "";
    const given = (answers[q.key] ?? "").trim();
    return {
      key: q.key, jp: q.jp, prompt: q.prompt, given, expected,
      correct: !!given && given === expected,
      role: it?.role ?? "", roleLabel: ROLE_PT[it?.role ?? ""] ?? (it?.role ?? ""),
      particle: it?.particle ?? null,
    };
  });
  return { level, seed: round.seed, total: questions.length,
           right: questions.filter((q) => q.correct).length, questions };
}

export function bankSize(level: Level): number {
  return (BANK[level] ?? []).length;
}
