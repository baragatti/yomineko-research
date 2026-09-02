/**
 * exam.server — the JLPT exam-simulator picker. Implements design/exam_simulator.md.
 *
 * The `.server.ts` suffix keeps the 6,048-item bank out of the client bundle: a paper is sampled here and
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
  // 聴解. Declared with its real per-paper counts (design/listening.md) so the paper knows what a
  // complete sitting is, and gated at BUILD time by `hasAudio` — see `playable` and `sectionsFor`.
  // Before W19 these five were simply absent from this table, which meant the app could not even
  // describe the section it was missing, and `scorePaper`'s 聴解 得点区分 had nothing to be the
  // denominator of.
  { type: "listening_task", label: "Compreensão da tarefa", jp: "課題理解",
    hint: "Ouça a conversa e escolha o que a pessoa faz em seguida.", counts: { n5: 7, n4: 8, n3: 6 } },
  { type: "listening_point", label: "Compreensão de pontos", jp: "ポイント理解",
    hint: "Ouça a pergunta, depois a conversa, e escolha a resposta.", counts: { n5: 6, n4: 7, n3: 6 } },
  { type: "listening_gist", label: "Compreensão geral", jp: "概要理解",
    hint: "Ouça e escolha do que se trata.", counts: { n5: 0, n4: 0, n3: 3 } },
  { type: "listening_say", label: "Expressão oral", jp: "発話表現",
    hint: "Veja a situação e escolha o que dizer.", counts: { n5: 5, n4: 5, n3: 4 } },
  { type: "listening_reply", label: "Resposta imediata", jp: "即時応答",
    hint: "Ouça a fala e escolha a resposta.", counts: { n5: 6, n4: 8, n3: 9 } },
];
// PYTHON-SIDE MIRRORS of this table: `PAPER_COUNTS` in scripts/validate/validate_exam_banks.py (the
// nine non-listening rows) and `LISTENING_PAPER_COUNTS` in validate_exam_level_gate.py (the five
// added here). Change a count in one place and change it in all three in the same commit.

/** The five 聴解 types, in paper order. One list, so nothing has to re-derive it from a prefix. */
export const LISTENING_TYPES = [
  "listening_task", "listening_point", "listening_gist", "listening_say", "listening_reply",
] as const;
export type ListeningType = (typeof LISTENING_TYPES)[number];
export function isListening(type: string): type is ListeningType {
  return (LISTENING_TYPES as readonly string[]).includes(type);
}

/**
 * The real exam is not one sitting. It is separately-timed PARTS with the papers collected between
 * them, and that shape is most of what makes a mock feel like the test: you cannot bank time from the
 * vocabulary section to spend on reading, and you cannot go back once a part is over.
 *
 * N5/N4/N3 run 言語知識（文字・語彙） first, then 言語知識（文法）・読解, then 聴解. (N1/N2 merge the first
 * two, which is why this table stops at N3 — the levels we ship.)
 *
 * All three parts are DECLARED. Whether a part RUNS is decided per level by `partsFor`, which drops a
 * part whose sections cannot be filled — so 聴解 is described here, and stays out of every paper until
 * its items have audio, instead of being invisible to the app that is supposed to simulate it.
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
    gapAfter: 30,
  },
  {
    key: "listening",
    jp: "聴解",
    label: "Compreensão auditiva",
    types: [...LISTENING_TYPES],
    minutes: { n5: 30, n4: 35, n3: 40 },
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
  "intervalo programado é de 20 minutos depois da primeira parte e 30 depois da segunda; em Taiwan o " +
  "primeiro é de 25 e na Coreia, de 5.";

/** Which part a section belongs to, so a section can never be silently orphaned. */
export function partOf(type: string): PartSpec | undefined {
  return PARTS.find((p) => p.types.includes(type));
}

export interface ScriptTurn { speaker: string; text: string }
/** One record as it sits in a bank file. Exported for study mode, which reads the banks directly. */
export interface ExamBankItem {
  id: string; level: string; stem?: string; correct?: string; distractors?: string[];
  pieces?: string[]; answer?: string; question?: string; reading?: string; sentence?: string;
  target?: string; wrong?: string[]; ai_generated?: boolean;
  /**
   * The corpus records the item was cut from, by stable id. `vocab` is the headword slug (kr/or/cf/
   * pp/us carry one); `grammar` is the point key (gf only — 文章の文法 items name their passage, not a
   * point). Study mode's level gate reads both: an item is inside a lesson's known set only when the
   * word and the point it drills were already introduced.
   */
  vocab?: string; vocab_id?: string; grammar?: string;
  /** 聴解 only: the ordered spoken turns, and the audio ref — "pending" until the scripts are voiced. */
  script?: ScriptTurn[]; audio?: string;
  /**
   * sentence_order only, and EMPTY IN EVERY ITEM TODAY (readiness G9). Japanese scrambling means a
   * second ordering is often equally correct; the QA sweeps proved 45 such items across the three
   * levels. `accepted` is where the bank regeneration records those alternates, as piece arrays.
   */
  accepted?: string[][];
  /**
   * sentence_order only. All 871 `answer` strings have their punctuation stripped, so the "correct
   * sentence" shown at review is not well-formed written Japanese (G9 again). When the regeneration
   * carries the punctuated form, review prints THAT and grading still uses the stripped `answer`.
   */
  answer_display?: string;
  /** Study mode prints this under the answer when the item carries one. No item does today. */
  explanation?: string;
}
const BANKS = examBanksData as unknown as Record<string, Record<string, ExamBankItem[]>>;

/**
 * THE AUDIO-PRESENT CHECK, and why it is a filter over items rather than a flag on the section.
 *
 * The five 聴解 banks are voice-ready TEXT scripts carrying `audio: "pending"` (design/listening.md);
 * the owner voices them in W35 and flips the field to a file ref, item by item. So "does listening
 * exist yet" is not one boolean — it is a per-item fact, and it will be true for some items before it
 * is true for all of them. A section joins the paper only when enough of ITS items are playable to
 * fill it; anything less would hand the learner a short 大問 and quietly change the denominator that
 * `scorePaper` divides by.
 */
function hasAudio(it: ExamBankItem): boolean {
  return typeof it.audio === "string" && it.audio !== "" && it.audio !== "pending";
}
/** A bank reduced to the items a paper may actually use. Non-listening banks pass through whole. */
export function playable(bank: ExamBankItem[], type: string): ExamBankItem[] {
  return isListening(type) ? bank.filter(hasAudio) : bank;
}

/**
 * The sections a paper at this level can actually run: a positive per-paper count AND a bank deep
 * enough to fill it. Today that is the nine non-listening types at every level — identical to what
 * shipped before W19 — and the five listening rows drop out on the audio check, so the paper stays
 * honest until the audio lands instead of advertising a section it cannot print.
 */
export function sectionsFor(level: Level): SectionSpec[] {
  return SECTIONS.filter((s) => {
    const want = s.counts[level];
    if (!want) return false;
    return playable(BANKS[level]?.[s.type] ?? [], s.type).length >= want;
  });
}
/** The parts that hold at least one runnable section, in paper order. */
export function partsFor(level: Level): PartSpec[] {
  const live = new Set(sectionsFor(level).map((s) => s.type));
  return PARTS.filter((p) => p.types.some((t) => live.has(t)));
}
/** Scored minutes a paper at this level actually runs — the runnable parts only, break excluded. */
export function minutesFor(level: Level): number {
  return partsFor(level).reduce((a, p) => a + p.minutes[level], 0);
}
/** The full real-exam duration, listening included, for saying what the simulation is short of. */
export function fullMinutesFor(level: Level): number {
  return PARTS.reduce((a, p) => a + p.minutes[level], 0);
}
/**
 * Scored minutes per level. Computed from the RUNNABLE parts, so the level picker can never advertise
 * a duration the paper does not run. Defined after BANKS because it now depends on the audio check.
 */
export const MINUTES: Record<Level, number> =
  LEVELS.reduce((acc, lv) => {
    acc[lv] = minutesFor(lv);
    return acc;
  }, {} as Record<Level, number>);

/** Scheduled gap after the `i`-th RUNNABLE part of a level, in minutes; 0 after the last one. */
export function gapAfter(level: Level, i: number): number {
  const parts = partsFor(level);
  return i >= parts.length - 1 ? 0 : parts[i]?.gapAfter ?? 0;
}

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
  script?: ScriptTurn[];    // 聴解 only: the spoken turns, speaker-tagged
  audio?: string;           // 聴解 only: the audio ref; absent means the script stands in for it
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
export function presentItem(it: ExamBankItem, type: string):
    { prompt: string; focus?: string; options: string[]; pieces?: string[];
      script?: ScriptTurn[]; audio?: string } | null {
  if (it.pieces?.length && it.answer) {
    return { prompt: "", options: [], pieces: it.pieces };
  }
  const correct = it.correct ?? "";
  const distractors = it.distractors ?? it.wrong ?? [];
  // 発話表現 and 即時応答 are genuinely 3-option 大問 (one key + TWO distractors); the other listening
  // subsections and every reading one are 4-option. A flat `< 2` floor covers both.
  if (!correct || distractors.length < 2) return null;

  if (isListening(type)) {
    const script = (it.script ?? []).filter((t) => t && t.text);
    if (!script.length) return null;      // a listening item with no turns has nothing to play or read
    return { prompt: it.question || LISTENING_QUESTION[type as ListeningType],
             options: [correct, ...distractors], script, audio: it.audio };
  }

  if (!it.stem && !it.question && it.target) {          // usage
    return { prompt: `Em qual frase 「${it.target}」 está usada corretamente?`,
             focus: it.target, options: [correct, ...distractors] };
  }
  const prompt = it.question || it.stem || "";
  if (!prompt) return null;
  return { prompt, focus: it.target, options: [correct, ...distractors] };
}

/**
 * The question a 聴解 大問 asks when the item does not carry one, which is the case for ALL 110
 * `listening_say` + `listening_reply` items: design/listening.md states outright that `question` is
 * empty for `ls:`/`lr:` because "the format IS the question". `present` used to read that empty string
 * through `it.question || it.stem || ""` and return null, so the day audio landed those two whole 大問
 * would have come back empty, been dropped by `if (!questions.length) continue`, and shortened the
 * paper without tripping the `placed !== total` guard (readiness G3 — a verified latent bug, fixed
 * here before the audio it was waiting for).
 *
 * These five are the exam's own standard framing formulas, which design/listening.md §5 records as
 * generic conventions rather than protected expression.
 */
const LISTENING_QUESTION: Record<ListeningType, string> = {
  listening_task: "この後、どうしますか。",
  listening_point: "何と言っていますか。",
  listening_gist: "何について話していますか。",
  listening_say: "何と言いますか。",
  listening_reply: "何と答えますか。",
};

/** The correct answer for an item, whatever its shape — the string grading compares against. */
export function answerOf(it: ExamBankItem): string {
  return it.answer ?? it.correct ?? "";
}
/**
 * What REVIEW prints as the right answer. Identical to `answerOf` except for a sentence_order item
 * that carries `answer_display`: every stored `answer` has had its punctuation stripped, so review
 * has always shown a sentence that is not well-formed written Japanese (readiness G9). Grading keeps
 * using the stripped form; only the printed string changes, and only when the bank supplies one.
 */
export function displayAnswerOf(it: ExamBankItem): string {
  return it.answer_display || answerOf(it);
}
/**
 * Every ordering that counts as right. `answer` first, then any alternate the bank declares in
 * `accepted` (piece arrays, joined the way the widget joins them). No item carries `accepted` today,
 * so this is exactly today's behaviour until the regeneration fills it — which is the point: the
 * grader stops being the thing that has to change when the data learns about ambiguity.
 */
export function acceptedAnswersOf(it: ExamBankItem): string[] {
  const out = [answerOf(it)];
  for (const alt of it.accepted ?? []) {
    if (Array.isArray(alt) && alt.length) out.push(alt.join(""));
  }
  return out.filter(Boolean);
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
  for (const spec of sectionsFor(level)) {
    const want = spec.counts[level];
    if (!want) continue;
    // `playable`, not the raw bank: the audio check has to bite BEFORE the no-repeat fallback below,
    // or a starved listening section would "fall back to the full bank" and pull in silent items.
    const bank = playable(BANKS[level]?.[spec.type] ?? [], spec.type);
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
      const p = presentItem(it, spec.type);
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
        // `script` is deliberately NOT carried. The exam never shows the transcript
        // (design/listening.md), and "the route does not render it" is not good enough — anything in
        // the loader payload is readable in the browser, and the script contains the answer's whole
        // context. `playable` guarantees every listening item that got this far HAS audio, so the
        // recording is the stem. The transcript belongs to study mode and to post-answer review.
        audio: p.audio,
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
  // There is no gap after the paper. 言語知識（文法）・読解 carries a scheduled 30 only because 聴解
  // follows it in the real exam; while listening cannot run, that part IS the end of the sitting.
  if (parts.length) parts[parts.length - 1].gapAfter = 0;
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
      const it = itemFor(level, sec.type, q);
      const given = (answers[q.key] ?? "").trim();
      // sentence_order is assembled from chips, so whitespace is an artefact of the widget, not an answer.
      const norm = (s: string) => (sec.type === "sentence_order" ? s.replace(/\s+/g, "") : s);
      // Every ACCEPTABLE ordering, not just the stored one. Japanese scrambling makes a second order
      // right often enough that exact equality marks correct answers wrong (readiness G9); the bank
      // declares those in `accepted`. Empty everywhere today, so this is today's behaviour verbatim.
      const acceptable = it ? acceptedAnswersOf(it) : [];
      const ok = !!given && acceptable.some((a) => norm(given) === norm(a));
      if (ok) right++;
      questions.push({ key: q.key, type: sec.type, prompt: q.prompt || (q.pieces || []).join(" "),
                       given, expected: it ? displayAnswerOf(it) : "", correct: ok });
    }
    perSection.push({ type: sec.type, label: sec.label, right, of: sec.questions.length });
  }
  const total = paper.total;
  const rightTotal = perSection.reduce((a, s) => a + s.right, 0);
  return { level, seed, total, right: rightTotal,
           percent: total ? Math.round((rightTotal / total) * 100) : 0, perSection, questions };
}

/**
 * Recover the bank record behind a question. buildPaper deliberately does NOT carry `correct` into the
 * payload (that would ship the answer key to the client), so grading re-derives it from the bank. The
 * lookup goes through the item id on the SERVER-rebuilt paper — never an id echoed back by the request.
 */
function itemFor(level: Level, type: string, q: PaperQuestion): ExamBankItem | undefined {
  return (BANKS[level]?.[type] ?? []).find((x) => x.id === q.id);
}

/**
 * Bank sizes, for the level picker — counted over the sections that can actually RUN, and over the
 * playable items in them. Counting the whole bank would advertise the 239 silent listening scripts as
 * questions the learner can be asked today.
 */
export function bankStats(level: Level): { types: number; items: number } {
  const b = BANKS[level] ?? {};
  const types = sectionsFor(level).map((s) => s.type);
  return { types: types.length,
           items: types.reduce((a, t) => a + playable(b[t] ?? [], t).length, 0) };
}

/* ============================================================================================
   JLPT SCORING MODEL — design/exam_scoring.md
   ============================================================================================

   The JLPT does not report a percentage. It reports a total plus a small number of 得点区分
   (scoring sections), and it fails a candidate who clears the total but misses ONE section's
   minimum. `gradePaper` above returns raw right/total/percent per design/exam_simulator.md §6 and
   is unchanged; everything here is additive.

   THE HONEST LIMIT, restated where the code is so nobody has to go and find the doc: real scaled
   scores come from an item-response-theory model over each candidate's answer PATTERN. The
   raw→scaled mapping is unpublished, non-linear and re-fitted per sitting, so no scaled score can
   be reproduced outside JEES. What `scorePaper` computes is a HOUSE APPROXIMATION — a linear map of
   raw section percent onto the official scaled range — and it is labelled as one in the data
   (`approximation: true`) and in the pt-BR the learner reads. Sources and dates: exam_scoring.md §3.
*/

/** A 得点区分. N4/N5 merge language knowledge with reading; N1–N3 keep them apart. */
export type ScoringSectionKey = "language_knowledge" | "reading" | "language_reading" | "listening";
export interface ScoringSectionSpec {
  key: ScoringSectionKey;
  label: string;
  jp: string;
  /** The official scaled range's top: 120 for the merged N4/N5 section, 60 for every other. */
  max: number;
  /** 基準点 — the sectional pass mark. 31.67% of `max` at every level and every section. */
  minimum: number;
  /** Which of our 大問 score into this 得点区分. */
  types: readonly string[];
}
export interface ScoringModel {
  /** 合格点 — the overall pass mark, out of 180. */
  passMark: number;
  sections: readonly ScoringSectionSpec[];
}

const WRITTEN_TYPES = [
  "kanji_reading", "orthography", "context_fill", "paraphrase", "usage",
  "grammar_form", "sentence_order", "text_grammar",
] as const;
const LISTENING_SECTION: ScoringSectionSpec = {
  key: "listening", label: "Compreensão auditiva", jp: "聴解",
  max: 60, minimum: 19, types: LISTENING_TYPES,
};

/**
 * The per-level model. Two shapes, and the N3 one is the trap: 文章の文法 is SAT inside the
 * 文法・読解 booklet but SCORES as grammar, so it belongs to language_knowledge and only 読解 goes to
 * reading. jlpt.jp's test-section → scoring-section correspondence table is what says so
 * (exam_scoring.md §1, §6).
 *
 * N1/N2 are absent because this app ships N5–N3; the shape they would take is the n3 one, and adding
 * them is adding rows here — never a change to anything that reads this table (spec §1.6).
 */
export const SCORING_MODEL: Record<Level, ScoringModel> = {
  n5: {
    passMark: 80,
    sections: [
      { key: "language_reading", label: "Conhecimento da língua e leitura",
        jp: "言語知識（文字・語彙・文法）・読解", max: 120, minimum: 38,
        types: [...WRITTEN_TYPES, "reading_comp"] },
      LISTENING_SECTION,
    ],
  },
  n4: {
    passMark: 90,
    sections: [
      { key: "language_reading", label: "Conhecimento da língua e leitura",
        jp: "言語知識（文字・語彙・文法）・読解", max: 120, minimum: 38,
        types: [...WRITTEN_TYPES, "reading_comp"] },
      LISTENING_SECTION,
    ],
  },
  n3: {
    passMark: 95,
    sections: [
      { key: "language_knowledge", label: "Conhecimento da língua",
        jp: "言語知識（文字・語彙・文法）", max: 60, minimum: 19, types: WRITTEN_TYPES },
      { key: "reading", label: "Compreensão de leitura", jp: "読解",
        max: 60, minimum: 19, types: ["reading_comp"] },
      LISTENING_SECTION,
    ],
  },
};
/** Every level's total range is 0–180, whatever the section split. */
export const SCALED_TOTAL_MAX = 180;

export interface ScoredSection {
  key: ScoringSectionKey;
  label: string;
  jp: string;
  max: number;
  minimum: number;
  /** False when the paper contained no question scoring into this 得点区分 (today: listening). */
  attempted: boolean;
  right: number;
  of: number;
  /** Raw percent, rounded — the only number here that is not an estimate. */
  rawPercent: number;
  /** The house approximation. Null when the section was not attempted; null is not zero. */
  scaled: number | null;
  meetsMinimum: boolean;
}
/**
 * `incomplete` is not a hedge, it is the real rule: a candidate who does not sit every test section
 * is failed and no results are issued. Printing "aprovado" off a paper with no 聴解 would be a
 * fabrication, and printing "reprovado" would blame the learner for our missing audio.
 */
export type Verdict = "pass" | "fail" | "incomplete";
export interface ScoreReport {
  level: Level;
  sections: ScoredSection[];
  /** Sum of the attempted sections' approximations. */
  scaledTotal: number;
  /** 180 — what a complete sitting is worth, always. */
  scaledMax: number;
  /** What the sections actually sat were worth (120 today, 180 once listening runs). */
  attemptedMax: number;
  passMark: number;
  meetsPassMark: boolean;
  allSectionsMeetMinimum: boolean;
  verdict: Verdict;
  /** The 得点区分 the paper could not test. Non-empty means `verdict === "incomplete"`. */
  missing: ScoringSectionKey[];
  /** Structural: this is never a JLPT score. Consumers must not drop it when they render. */
  approximation: true;
  /** The one-line pt-BR the UI is required to print next to the number. */
  note: string;
}

const SCALED_NOTE =
  "Pontuação estimada. O JLPT calcula a nota por um modelo estatístico a partir do padrão de " +
  "respostas, não pela contagem de acertos, e essa conta não é pública — então aqui a porcentagem " +
  "de acertos é convertida linearmente para a faixa oficial. Serve para comparar suas tentativas e " +
  "achar a seção fraca; não serve para prever o resultado real.";

/**
 * The house approximation, in one line: raw section percent, linearly onto the official range.
 * See exam_scoring.md §5, including the known bias (a linear map hands out 0s and 180s the real
 * model does not produce) and why no correction is applied.
 */
function approximateScaled(right: number, of: number, max: number): number {
  return of > 0 ? Math.round((max * right) / of) : 0;
}

/** Turn a graded paper into the JLPT-shaped report. Pure — grading already happened. */
export function scoreOf(result: Result): ScoreReport {
  const model = SCORING_MODEL[result.level];
  const byType = new Map(result.perSection.map((s) => [s.type, s]));

  const sections: ScoredSection[] = model.sections.map((spec) => {
    let right = 0;
    let of = 0;
    for (const t of spec.types) {
      const got = byType.get(t);
      if (!got) continue;
      right += got.right;
      of += got.of;
    }
    const attempted = of > 0;
    const scaled = attempted ? approximateScaled(right, of, spec.max) : null;
    return {
      key: spec.key, label: spec.label, jp: spec.jp, max: spec.max, minimum: spec.minimum,
      attempted, right, of,
      rawPercent: attempted ? Math.round((right / of) * 100) : 0,
      scaled,
      meetsMinimum: scaled !== null && scaled >= spec.minimum,
    };
  });

  const missing = sections.filter((s) => !s.attempted).map((s) => s.key);
  const scaledTotal = sections.reduce((a, s) => a + (s.scaled ?? 0), 0);
  const attemptedMax = sections.reduce((a, s) => a + (s.attempted ? s.max : 0), 0);
  const meetsPassMark = scaledTotal >= model.passMark;
  const allSectionsMeetMinimum = sections.every((s) => s.meetsMinimum);

  return {
    level: result.level,
    sections,
    scaledTotal,
    scaledMax: SCALED_TOTAL_MAX,
    attemptedMax,
    passMark: model.passMark,
    meetsPassMark,
    allSectionsMeetMinimum,
    verdict: missing.length
      ? "incomplete"
      : meetsPassMark && allSectionsMeetMinimum ? "pass" : "fail",
    missing,
    approximation: true,
    note: SCALED_NOTE,
  };
}

export interface ScoredResult extends Result {
  score: ScoreReport;
}
/**
 * Grade AND score. `gradePaper` is kept exactly as it was — raw right/total/percent, one point per
 * item — so every existing caller and the `total_raw` / `total_possible` contract in
 * design/user_state.md §7 are untouched; this wraps it.
 */
export function scorePaper(level: Level, seedInput: string | number, answers: Record<string, string>,
                           exclude: Set<string> = new Set()): ScoredResult {
  const result = gradePaper(level, seedInput, answers, exclude);
  return { ...result, score: scoreOf(result) };
}

/* ============================================================================================
   THE ATTEMPT RECORD — design/user_state.md §7 (`exam_attempt`)
   ============================================================================================

   LOGICAL ONLY. Nothing here persists: the physical store waits on owner decision D8 (APP_PLAN §4,
   delivered by W43). What this section does deliver is the two picker rules that were declared in
   design/exam_simulator.md and never implemented (readiness G5): rule 5, seed = (userId, level,
   attemptNo), and rule 2, the no-repeat window, which had a parameter in `buildPaper`'s signature
   that no caller ever passed.

   W26 has since published `contracts/user_state/exam_attempt.schema.json`, so the authority is no
   longer only design/user_state.md §7 — it is the schema, and these types mirror it field for field,
   snake_case included. The two things §7 reserved for this unit are now filled rather than null:
   `scaled` (the house approximation of §5 of design/exam_scoring.md) and `passed` — which stays null
   anyway whenever the verdict is `incomplete`, because a paper missing a whole 得点区分 has no
   pass/fail to report. If schema and design ever disagree, §7 wins and both the schema and this file
   change; nothing here may drift silently from the published contract.
*/

/** §7: `full` is a whole paper, `section` one 大問, `study` the known-set-filtered practice mode. */
export type AttemptMode = "full" | "section" | "study";
/** §7: bumped when selection, option shuffle or section fill changes, so old attempts still reproduce. */
export const SEED_ALGORITHM = "paper-v1";

/*
 * FIELD NAMES ARE THE CONTRACT'S, NOT THIS FILE'S. `contracts/user_state/exam_attempt.schema.json`
 * landed after the first draft of this block was written in camelCase, and a runtime record that
 * has to serialise to a published schema does not get to spell its keys differently — the rename
 * would then live in whatever writes the row, which is precisely where it would rot. So these are
 * snake_case, field for field with the schema (and with `ExamAttempt` in `contracts/types.ts`),
 * which is also how every other synced record in this app is spelled.
 */
export interface ExamAttemptItem {
  item: string;                 // exam item StableId
  /** One of the fourteen types in SECTIONS — the schema's `$defs/section` enum. */
  section: string;
  position: number;             // 1-based, in presentation order
  /** The SHUFFLED order actually shown — what makes rule 5 checkable against what was on screen. */
  presented_options: string[];
  /** The schema allows null for "left blank"; this app writes "" for it, which is the same fact. */
  answer_given: string;
  correct: boolean;
  correct_answer: string;
  response_ms: number | null;
}
export interface ExamAttemptSection {
  section: string;
  raw: number;
  possible: number;
  minimum_met: boolean;
}
/** §7's `scaled` object. Null on the attempt until W19 — which is this unit, so it is filled now. */
export interface ExamAttemptScaled {
  score: number;
  max: number;
  pass_mark: number;
  sectional_minima_met: boolean;
}
export interface ExamAttempt {
  attempt_id: string;           // att:<user opaque>-<level>-<attempt no.>
  user_id: string;
  level: Level;
  attempt_no: number;           // >= 1
  seed: string;                 // the canonical serialization, STORED not recomputed (§7)
  seed_algorithm: string;
  started_at: string;           // ISO 8601
  submitted_at: string | null;  // null = in progress
  mode: AttemptMode;
  time_limit_seconds: number;
  elapsed_seconds: number;
  items: ExamAttemptItem[];
  sections: ExamAttemptSection[];
  total_raw: number;
  total_possible: number;
  scaled: ExamAttemptScaled | null;
  /** §7: null until `scaled` exists — and still null when the verdict is `incomplete`. */
  passed: boolean | null;
}

/**
 * The canonical seed serialization, and the reason it is a named function: §7 stores the seed string
 * rather than recomputing it, so that changing THIS line is a visible event instead of silently
 * regenerating a different paper under an old attempt number.
 */
export function attemptSeed(userId: string, level: Level, attemptNo: number): string {
  return `${userId}|${level}|${attemptNo}`;
}
/** `att:<user opaque>-<level>-<attempt no.>` — derivable from the seed, no counter needed (§7). */
export function attemptId(userId: string, level: Level, attemptNo: number): string {
  return `att:${userId}-${level}-${attemptNo}`;
}

/** design/exam_simulator.md rule 2: exclude items answered in the last N attempts of that level. */
export const NO_REPEAT_ATTEMPTS = 3;
/**
 * The no-repeat window, as a set of item ids. Rule 2 has existed in `buildPaper`'s signature since
 * the picker was written and no caller ever passed it; this is the function that produces the
 * argument. Starvation is NOT handled here — `buildPaper` falls back to the full bank when honouring
 * the window would shorten a section, because a short paper changes the scoring denominator.
 */
export function noRepeatExclude(history: readonly ExamAttempt[], level: Level,
                                window: number = NO_REPEAT_ATTEMPTS): Set<string> {
  const recent = history
    .filter((a) => a.level === level && a.mode === "full" && !!a.submitted_at)
    .sort((a, b) => b.attempt_no - a.attempt_no)
    .slice(0, window);
  const out = new Set<string>();
  for (const a of recent) for (const it of a.items) out.add(it.item);
  return out;
}

/**
 * Build the attempt record for a finished paper. IN-MEMORY: the caller holds it, and nothing in this
 * repo writes it anywhere (D8). Kept here rather than in a route so that the day a store exists, the
 * shape it stores is the shape design/user_state.md §7 declared.
 */
export function recordAttempt(input: {
  userId: string; level: Level; attemptNo: number; mode: AttemptMode;
  paper: Paper; result: ScoredResult;
  startedAt: string; submittedAt: string; elapsedSeconds: number;
}): ExamAttempt {
  const { userId, level, attemptNo, mode, paper, result } = input;
  const questions = paper.parts.flatMap((p) => p.sections).flatMap((sec) => sec.questions);
  const graded = new Map(result.questions.map((g) => [g.key, g]));
  // A 大問's "minimum met" is its 得点区分's, not its own — the JLPT has no per-大問 minimum.
  const minimumMet = new Map<string, boolean>();
  for (const s of result.score.sections) {
    const spec = SCORING_MODEL[level].sections.find((x) => x.key === s.key);
    for (const t of spec?.types ?? []) minimumMet.set(t, s.meetsMinimum);
  }

  return {
    attempt_id: attemptId(userId, level, attemptNo),
    user_id: userId,
    level,
    attempt_no: attemptNo,
    seed: attemptSeed(userId, level, attemptNo),
    seed_algorithm: SEED_ALGORITHM,
    started_at: input.startedAt,
    submitted_at: input.submittedAt,
    mode,
    time_limit_seconds: paper.minutes * 60,
    elapsed_seconds: input.elapsedSeconds,
    items: questions.map((q, i) => {
      const g = graded.get(q.key);
      return {
        item: q.id,
        section: q.type,
        position: i + 1,
        presented_options: q.pieces ?? q.options,
        answer_given: g?.given ?? "",
        correct: !!g?.correct,
        correct_answer: g?.expected ?? "",
        response_ms: null,       // per-question timing is not measured yet
      };
    }),
    sections: result.perSection.map((s) => ({
      section: s.type, raw: s.right, possible: s.of, minimum_met: minimumMet.get(s.type) ?? false,
    })),
    total_raw: result.right,
    total_possible: result.total,
    scaled: {
      score: result.score.scaledTotal,
      max: result.score.scaledMax,
      pass_mark: result.score.passMark,
      sectional_minima_met: result.score.allSectionsMeetMinimum,
    },
    // §7: "Null until `scaled` exists." It also stays null while the verdict is `incomplete` — a
    // paper missing a whole 得点区分 has no pass/fail to report, per exam_scoring.md §6.
    passed: result.score.verdict === "incomplete" ? null : result.score.verdict === "pass",
  };
}
