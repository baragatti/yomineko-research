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
  /**
   * Print the referenced reading above the question. TRUE only where the stem lives OUTSIDE the passage.
   *
   * 読解 asks a separate question about a text, so the text has to be on the page. 文章の文法 does not: its
   * stem IS the passage with one grammar form replaced by （　）, and the stored passage is that same text
   * unblanked — so showing it restores the blank and hands the learner the answer. Both types carry a
   * `reading` slug, which is why this is declared per SECTION and not inferred from the item.
   */
  showsPassage?: boolean;
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
    hint: "Leia o texto e responda.", counts: { n5: 3, n4: 4, n3: 4 }, showsPassage: true },
];
// Listening is intentionally absent: those banks are voice-ready SCRIPTS with audio: "pending"
// (design/listening.md). The section joins the paper only once the audio exists.

/**
 * The real exam is not one sitting. It is separately-timed PARTS with the papers collected between
 * them, and that shape is most of what makes a mock feel like the test: you cannot bank time from the
 * vocabulary section to spend on reading, and you cannot go back once a part is over.
 *
 * N5/N4/N3 run 言語知識（文字・語彙） first, then 言語知識（文法）・読解. (N1/N2 merge the two, which is
 * why this table stops at N3 — the levels we ship.) 聴解 is a third part in the real exam and is absent
 * here for the same reason it is absent from SECTIONS: the scripts exist, the audio does not.
 */
export interface PartSpec {
  key: string;
  jp: string;
  label: string;
  types: string[];
  minutes: Record<Level, number>;
  /** Scheduled gap AFTER this part, in minutes. See GAP_NOTE. */
  gapAfter?: number;
}
export const PARTS: PartSpec[] = [
  {
    key: "vocab",
    jp: "言語知識（文字・語彙）",
    label: "Conhecimento da língua — escrita e vocabulário",
    types: ["kanji_reading", "orthography", "context_fill", "paraphrase", "usage"],
    minutes: { n5: 20, n4: 25, n3: 30 },
    gapAfter: 20,
  },
  {
    key: "grammar",
    jp: "言語知識（文法）・読解",
    label: "Gramática e compreensão de leitura",
    types: ["grammar_form", "sentence_order", "text_grammar", "reading_comp"],
    minutes: { n5: 40, n4: 55, n3: 70 },
  },
];

/**
 * WHAT THE GAP BETWEEN PARTS IS, AND WHAT IT IS NOT.
 *
 * The section durations above are official and identical across two independent checks of the JEES /
 * jlpt.jp material. The gap is a different kind of number and has to be described honestly, because
 * JEES does not publish one: the word 休憩 appears nowhere in its timetable, and the only figure
 * available is the SCHEDULED GAP between the end of one section and the start of the next -- 20 minutes
 * after 文字・語彙, 30 after 文法・読解. That window is not free time. It covers collecting the booklets,
 * handing out the next ones and reading the instructions, so the actual rest is some unpublished
 * fraction of it.
 *
 * So we model the scheduled gap, at its sourced length, and say in the UI what it is. An earlier version
 * of this file simply asserted a flat 10 minutes, which was a number nobody had measured presented to
 * learners as if it were the real exam's.
 *
 * The gap is always SKIPPABLE. The point of simulating it is rehearsing the interruption -- that part 1
 * is over and cannot be reopened -- not enforcing a wait nobody benefits from at a desk at home.
 *
 * There is also no GLOBAL gap to copy. jlpt.jp publishes section durations and nothing else -- no clock
 * schedule, no break -- and each administering body sets its own: Japan schedules 20 minutes here and
 * never labels it a break, Taiwan 25 (of which 15 is labelled rest), Korea 5. They genuinely disagree,
 * so the UI names the Japan figure as the Japan figure instead of implying a universal one. Brazilian
 * sittings publish no equivalent timetable at all.
 */
export const GAP_NOTE =
  "No exame, entre uma parte e outra as provas são recolhidas e as instruções da parte seguinte são " +
  "lidas, então esse tempo não é todo descanso. A duração muda conforme o país que aplica: no Japão o " +
  "intervalo programado aqui é de 20 minutos, em Taiwan 25 e na Coreia 5.";

/** Scheduled gap after part `i`, in minutes; 0 when the part is the last one we run. */
export function gapAfter(i: number): number {
  return PARTS[i]?.gapAfter ?? 0;
}

/** Total scored minutes for a level (the sum of its parts; excludes the break). */
export const MINUTES: Record<Level, number> =
  LEVELS.reduce((acc, lv) => {
    acc[lv] = PARTS.reduce((a, p) => a + p.minutes[lv], 0);
    return acc;
  }, {} as Record<Level, number>);

/** Which part a section belongs to, so a section can never be silently orphaned. */
export function partOf(type: string): PartSpec | undefined {
  return PARTS.find((p) => p.types.includes(type));
}

interface RawItem {
  id: string; level: string; stem?: string; correct?: string; distractors?: string[];
  pieces?: string[]; answer?: string; question?: string; reading?: string; sentence?: string;
  target?: string; wrong?: string[]; ai_generated?: boolean;
}
const BANKS = examBanksData as unknown as Record<string, Record<string, RawItem[]>>;

/**
 * reading_comp and text_grammar both reference a passage by slug. Resolving it is only ever DISPLAY, and
 * only the sections flagged `showsPassage` want it — see SectionSpec.showsPassage.
 */
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
  passage?: string;         // sections with `showsPassage` (読解) only: the text above the question
  options: string[];        // already shuffled for this attempt
  pieces?: string[];        // sentence_order only
}
export interface PaperSection {
  type: string; label: string; jp: string; hint: string; questions: PaperQuestion[];
  /** 1-based index of this section's first question WITHIN THE PAPER, for continuous numbering. */
  from: number;
}
export interface PaperPart {
  key: string; jp: string; label: string; minutes: number; gapAfter: number; total: number;
  sections: PaperSection[];
}
export interface Paper {
  level: Level; seed: number; minutes: number; total: number; gapNote: string;
  parts: PaperPart[];
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
  // One question per passage, PAPER-wide. 文章の文法 and 読解 draw from the SAME reading pool (every
  // text_grammar passage is also a reading_comp passage), so a guard scoped to one section let the same
  // text be printed twice in one paper — re-reading spent text and burning scarce material. Paper scope
  // is the only scope that holds.
  const seenPassage = new Set<string>();

  // Sections are built in SECTIONS order (which is the real paper's 大問 order) and then grouped into
  // parts, rather than iterating parts and then sections. Keeping one pass means the RNG is consumed in
  // a fixed sequence, so an existing seed still reproduces the same paper it did before parts existed.
  for (const spec of SECTIONS) {
    const want = spec.counts[level];
    if (!want) continue;
    const bank = BANKS[level]?.[spec.type] ?? [];
    if (!bank.length) continue;
    let pool = bank.filter((it) => !exclude.has(it.id));
    if (pool.length < want) pool = bank;                       // no-repeat must never shorten the paper
    // Real-first (design rule 4): prefer items grounded in a real human-written sentence. Provenance is
    // stated, never inferred — every exam item carries an explicit `ai_generated` boolean, written at build
    // time from the sentence it is derived from (an item with no sentence behind it is built straight off
    // Layer-A vocab and carries `false`). The filter keys on that flag alone. It used to read an ABSENT
    // field as "real", which quietly mislabelled the paraphrase and usage banks — those items reproduce a
    // bank sentence verbatim and some of those sentences are generated, so the rule was inert exactly where
    // it mattered. Provenance now lives in the data, so the banks and this picker cannot drift apart again.
    const real = pool.filter((it) => !it.ai_generated);
    const rest = pool.filter((it) => !!it.ai_generated);
    const ordered = [...shuffle(real, rand), ...shuffle(rest, rand)];

    const questions: PaperQuestion[] = [];
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
        passage: spec.showsPassage && it.reading ? readingText(it.reading) : undefined,
        options: p.pieces ? [] : shuffle(p.options, rand),
        pieces: p.pieces ? shuffle(p.pieces, rand) : undefined,
      });
    }
    if (!questions.length) continue;
    sections.push({ type: spec.type, label: spec.label, jp: spec.jp, hint: spec.hint, questions,
                    from: total + 1 });
    total += questions.length;
  }

  const parts: PaperPart[] = [];
  for (const spec of PARTS) {
    const mine = sections.filter((sec) => spec.types.includes(sec.type));
    if (!mine.length) continue;
    parts.push({
      key: spec.key, jp: spec.jp, label: spec.label, minutes: spec.minutes[level],
      gapAfter: spec.gapAfter ?? 0,
      total: mine.reduce((a, sec) => a + sec.questions.length, 0),
      sections: mine,
    });
  }
  // A section that matches no part would vanish from the paper while still counting toward `total`,
  // which would silently change the scoring denominator. Fail loudly instead.
  const placed = parts.reduce((a, p) => a + p.total, 0);
  if (placed !== total) {
    const orphans = sections.filter((sec) => !partOf(sec.type)).map((sec) => sec.type);
    throw new Error(`exam: sections outside every part: ${orphans.join(", ") || "(count mismatch)"}`);
  }

  return { level, seed, minutes: MINUTES[level], total, gapNote: GAP_NOTE, parts };
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

  for (const sec of paper.parts.flatMap((p) => p.sections)) {
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
