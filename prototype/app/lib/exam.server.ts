/**
 * exam.server — the JLPT exam-simulator picker. Implements design/exam_simulator.md.
 *
 * The `.server.ts` suffix keeps the 6,166-item bank out of the client bundle: a paper is sampled here and
 * only the sampled items are serialised into the loader payload, with `correct` stripped until grading.
 *
 * Determinism is the core property. A paper is identified by (level, seed); the same pair always yields
 * the same items in the same order with the same option shuffle. That is what lets grading recompute the
 * paper from the seed instead of trusting anything the client sends back, and it makes any attempt
 * reproducible for support/review.
 */
import examBanksData from "../data/examBanks.json";
import readingsData from "../data/readings.json";

export type Level = "n5" | "n4" | "n3";
export const LEVELS: Level[] = ["n5", "n4", "n3"];

/** Section order + per-level counts, mirroring the real Language-Knowledge + Reading paper. */
export interface SectionSpec {
  type: string;
  label: string;
  jp: string;
  hint: string;
  counts: Record<Level, number>;
}
export const SECTIONS: SectionSpec[] = [
  { type: "kanji_reading", label: "Leitura de kanji", jp: "漢字読み",
    hint: "Escolha a leitura correta da palavra sublinhada.", counts: { n5: 7, n4: 7, n3: 8 } },
  { type: "orthography", label: "Escrita", jp: "表記",
    hint: "Escolha como a palavra se escreve.", counts: { n5: 5, n4: 5, n3: 6 } },
  { type: "context_fill", label: "Vocabulário no contexto", jp: "文脈規定",
    hint: "Escolha a palavra que completa a frase.", counts: { n5: 6, n4: 8, n3: 11 } },
  { type: "paraphrase", label: "Equivalente", jp: "言い換え類義",
    hint: "Escolha a alternativa de sentido mais próximo.", counts: { n5: 3, n4: 4, n3: 5 } },
  { type: "usage", label: "Uso", jp: "用法",
    hint: "Escolha a frase em que a palavra é usada corretamente.", counts: { n5: 0, n4: 4, n3: 5 } },
  { type: "grammar_form", label: "Gramática", jp: "文法形式",
    hint: "Escolha a forma que completa a frase.", counts: { n5: 9, n4: 8, n3: 13 } },
  { type: "sentence_order", label: "Ordenar a frase", jp: "並べ替え",
    hint: "Monte a frase na ordem correta.", counts: { n5: 4, n4: 4, n3: 5 } },
  { type: "text_grammar", label: "Gramática no texto", jp: "文章の文法",
    hint: "Escolha a forma que completa o texto.", counts: { n5: 2, n4: 3, n3: 4 } },
  { type: "reading_comp", label: "Compreensão de leitura", jp: "読解",
    hint: "Leia o texto e responda.", counts: { n5: 3, n4: 4, n3: 4 } },
];
// Listening is intentionally absent: those banks are voice-ready SCRIPTS with audio: "pending"
// (design/listening.md). The section joins the paper only once the audio exists.

/** Minutes allowed, per design/exam_simulator.md (Language Knowledge + Reading session). */
export const MINUTES: Record<Level, number> = { n5: 60, n4: 80, n3: 100 };

interface RawItem {
  id: string; level: string; stem?: string; correct?: string; distractors?: string[];
  pieces?: string[]; answer?: string; question?: string; reading?: string; sentence?: string;
  target?: string; wrong?: string[]; ai?: number;
}
const BANKS = examBanksData as unknown as Record<string, Record<string, RawItem[]>>;

/** reading_comp / text_grammar reference their passage by slug; resolve it for display. */
const READINGS = readingsData as unknown as Record<string, { jp?: string }>;
function readingText(slug: string): string | undefined {
  return READINGS[slug]?.jp;
}

/** mulberry32 — small, fast, seeded PRNG. Deterministic across runs and platforms. */
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
/** Stable string hash so a text seed ("abc") and a numeric one behave the same. */
export function seedOf(v: string | number): number {
  if (typeof v === "number" && Number.isFinite(v)) return Math.abs(Math.trunc(v)) || 1;
  const s = String(v ?? "");
  let h = 2166136261;
  for (let i = 0; i < s.length; i++) {
    h ^= s.charCodeAt(i);
    h = Math.imul(h, 16777619);
  }
  return (h >>> 0) || 1;
}

export interface PaperQuestion {
  key: string;              // stable within the paper: "<section>-<n>"
  id: string;               // bank item id — the handle grading uses, re-derived server-side
  type: string;
  prompt: string;           // the stem / question shown to the learner
  focus?: string;           // the word under test (paraphrase / usage), shown highlighted
  passage?: string;         // reading_comp + text_grammar: the text above the question
  options: string[];        // already shuffled for this attempt
  pieces?: string[];        // sentence_order only
}
export interface PaperSection {
  type: string; label: string; jp: string; hint: string; questions: PaperQuestion[];
}
export interface Paper {
  level: Level; seed: number; minutes: number; total: number; sections: PaperSection[];
}

/**
 * Pull an item's display fields. The banks are not uniform — four distinct shapes:
 *   stem + correct + distractors    kanji_reading, orthography, context_fill, grammar_form, text_grammar
 *   question + correct + distractors  reading_comp (stem lives in the referenced passage)
 *   target + correct + wrong        usage — no stem at all; the options ARE whole sentences
 *   pieces + answer                 sentence_order
 * `usage` needs its prompt synthesised, which is why a naive `question || stem` read dropped the entire
 * section.
 */
function present(it: RawItem): { prompt: string; focus?: string; options: string[]; pieces?: string[] } | null {
  if (it.pieces?.length && it.answer) {
    return { prompt: "", options: [], pieces: it.pieces };
  }
  const correct = it.correct ?? "";
  const distractors = it.distractors ?? it.wrong ?? [];
  if (!correct || distractors.length < 2) return null;

  if (!it.stem && !it.question && it.target) {          // usage
    return { prompt: `Em qual frase 「${it.target}」 está usada corretamente?`,
             focus: it.target, options: [correct, ...distractors] };
  }
  const prompt = it.question || it.stem || "";
  if (!prompt) return null;
  return { prompt, focus: it.target, options: [correct, ...distractors] };
}

/** The correct answer for an item, whatever its shape. */
function answerOf(it: RawItem): string {
  return it.answer ?? it.correct ?? "";
}

/**
 * Build a paper. `exclude` carries ids seen in the learner's recent attempts (design rule 2, no-repeat
 * window); when honouring it would starve a section we fall back to the full bank rather than emit a
 * short paper — a shorter paper would silently change the scoring denominator.
 */
export function buildPaper(level: Level, seedInput: string | number, exclude: Set<string> = new Set()): Paper {
  const seed = seedOf(seedInput);
  const rand = rng(seed);
  const sections: PaperSection[] = [];
  let total = 0;

  for (const spec of SECTIONS) {
    const want = spec.counts[level];
    if (!want) continue;
    const bank = BANKS[level]?.[spec.type] ?? [];
    if (!bank.length) continue;
    let pool = bank.filter((it) => !exclude.has(it.id));
    if (pool.length < want) pool = bank;                       // no-repeat must never shorten the paper
    // Real-first (design rule 4): prefer items grounded in a real bank sentence. `ai` marks a generated
    // one; the banks that carry no `ai` field at all (kanji_reading, orthography, usage…) are built
    // straight off Layer-A vocab, so a missing field means real, not unknown.
    const real = pool.filter((it) => !it.ai);
    const rest = pool.filter((it) => !!it.ai);
    const ordered = [...shuffle(real, rand), ...shuffle(rest, rand)];

    const questions: PaperQuestion[] = [];
    const seenPassage = new Set<string>();
    for (const it of ordered) {
      if (questions.length >= want) break;
      // One question per passage: two items off the same text give away each other's context.
      if (it.reading) {
        if (seenPassage.has(it.reading)) continue;
        seenPassage.add(it.reading);
      }
      const p = present(it);
      if (!p) continue;
      questions.push({
        key: `${spec.type}-${questions.length + 1}`,
        id: it.id,
        type: spec.type,
        prompt: p.prompt,
        focus: p.focus,
        passage: it.reading ? readingText(it.reading) : undefined,
        options: p.pieces ? [] : shuffle(p.options, rand),
        pieces: p.pieces ? shuffle(p.pieces, rand) : undefined,
      });
    }
    if (!questions.length) continue;
    sections.push({ type: spec.type, label: spec.label, jp: spec.jp, hint: spec.hint, questions });
    total += questions.length;
  }
  return { level, seed, minutes: MINUTES[level], total, sections };
}

export interface Graded {
  key: string; type: string; prompt: string; given: string; expected: string; correct: boolean;
}
export interface Result {
  level: Level; seed: number; total: number; right: number; percent: number;
  perSection: { type: string; label: string; right: number; of: number }[];
  questions: Graded[];
}

/**
 * Grade an attempt by REBUILDING the paper from (level, seed) and comparing. Nothing authoritative comes
 * from the request: the client only supplies its chosen strings, so a tampered payload cannot invent a
 * different answer key.
 */
export function gradePaper(level: Level, seedInput: string | number, answers: Record<string, string>,
                           exclude: Set<string> = new Set()): Result {
  const paper = buildPaper(level, seedInput, exclude);
  const seed = paper.seed;
  const questions: Graded[] = [];
  const perSection: Result["perSection"] = [];

  for (const sec of paper.sections) {
    let right = 0;
    for (const q of sec.questions) {
      const expected = expectedFor(level, sec.type, q);
      const given = (answers[q.key] ?? "").trim();
      // sentence_order is assembled from chips, so whitespace is an artefact of the widget, not an answer.
      const norm = (s: string) => (sec.type === "sentence_order" ? s.replace(/\s+/g, "") : s);
      const ok = !!given && norm(given) === norm(expected);
      if (ok) right++;
      questions.push({ key: q.key, type: sec.type, prompt: q.prompt || (q.pieces || []).join(" "),
                       given, expected, correct: ok });
    }
    perSection.push({ type: sec.type, label: sec.label, right, of: sec.questions.length });
  }
  const total = paper.total;
  const rightTotal = perSection.reduce((a, s) => a + s.right, 0);
  return { level, seed, total, right: rightTotal,
           percent: total ? Math.round((rightTotal / total) * 100) : 0, perSection, questions };
}

/**
 * Recover a question's expected answer. buildPaper deliberately does NOT carry `correct` into the payload
 * (that would ship the answer key to the client), so grading re-derives it from the bank. The lookup goes
 * through the item id on the SERVER-rebuilt paper — never an id echoed back by the request.
 */
function expectedFor(level: Level, type: string, q: PaperQuestion): string {
  const it = (BANKS[level]?.[type] ?? []).find((x) => x.id === q.id);
  return it ? answerOf(it) : "";
}

/** Bank sizes, for the level picker. */
export function bankStats(level: Level): { types: number; items: number } {
  const b = BANKS[level] ?? {};
  const types = Object.keys(b).filter((t) => SECTIONS.some((s) => s.type === t && s.counts[level] > 0));
  return { types: types.length, items: types.reduce((a, t) => a + (b[t]?.length ?? 0), 0) };
}
