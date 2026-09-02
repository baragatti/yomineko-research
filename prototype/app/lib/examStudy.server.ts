/**
 * examStudy.server — the untimed, immediate-feedback mode over the exam banks, filtered to what one
 * lesson has actually taught. Implements the "Study mode" paragraph of design/exam_simulator.md and
 * closes readiness gap G7 (`exams_simulations.md`): "Nothing in prototype/app/routes/ reads the exam
 * banks except the two simulator routes."
 *
 * WHY IT IS A SEPARATE FILE FROM exam.server.
 * Exam mode and study mode disagree about the one thing exam.server is built around. A paper never
 * ships its answer key (grading rebuilds the paper server-side from the seed); study mode's whole
 * point is that the learner sees right/wrong the instant they answer, which means the key IS in the
 * page — the same pure-CSS `data-correct` contract the lesson exercises already use. Keeping the two
 * in one module would put a "sometimes ship the key" branch inside the file whose comment promises it
 * never does. So: exam.server owns presentation and answers, this file owns selection and feedback.
 *
 * THE FILTER IS THE LEVEL GATE, PORTED.
 * scripts/validate/validate_exam_level_gate.py defines level-appropriateness as: every kanji, every
 * vocabulary item and every grammar point that an item's LEARNER-VISIBLE Japanese requires is inside
 * the taught set. That validator applies it at the end of a level; study mode applies exactly the
 * same predicate at an arbitrary lesson's `cumulative_known_set`. One definition, two call sites —
 * see `insideKnownSet` for the dimension-by-dimension port and for the one dimension the app's data
 * cannot carry.
 */
import examBanksData from "../data/examBanks.json";
import lessonsData from "../data/lessons.json";
import sentencesData from "../data/sentences.json";
import readingsData from "../data/readings.json";
import {
  LEVELS, SECTIONS, isListening, playable, presentItem, displayAnswerOf, seedOf,
  type ExamBankItem, type Level, type ScriptTurn,
} from "./exam.server";
import { loc } from "./corpus.server";

const BANKS = examBanksData as unknown as Record<string, Record<string, ExamBankItem[]>>;

interface LessonRecord {
  id: string;
  level?: string;
  /**
   * A LOCALE OBJECT in the synced data (`{"pt-BR": "..."}`), never a bare string — the corpus is
   * multi-locale by design (design/i18n.md) and typing this as `string` renders `[object Object]`
   * at best and throws in SSR at worst. `loc()` is the one reader.
   */
  title?: Record<string, string>;
  cumulative_known_set?: Record<string, string[]>;
}
const LESSONS = lessonsData as unknown as Record<string, LessonRecord>;

interface SentenceRecord { jp?: string; translation?: Record<string, string>; grammar?: string[] }
const SENTENCES = sentencesData as unknown as Record<string, SentenceRecord>;
const READINGS = readingsData as unknown as Record<string, { jp?: string }>;

/** CJK ideographs: Unified, Extension A, compatibility. Kana and punctuation are not gated. */
const KANJI_RE = /[㐀-䶿一-鿿豈-﫿]/g;

/**
 * Exam items address grammar by the bare key ("tai"); a `cumulative_known_set` holds slugs
 * ("gram:tai"). readiness G13 — normalise into slug space rather than "fixing" either side here.
 */
function gramSlug(ref: string): string {
  return ref.startsWith("gram:") ? ref : `gram:${ref}`;
}

export interface KnownSet {
  kanji: ReadonlySet<string>;
  vocab: ReadonlySet<string>;
  grammar: ReadonlySet<string>;
}
function knownSetOf(lesson: LessonRecord): KnownSet {
  const cks = lesson.cumulative_known_set ?? {};
  return {
    kanji: new Set(cks.kanji ?? []),
    vocab: new Set(cks.vocab ?? []),
    grammar: new Set(cks.grammar ?? []),
  };
}

/** Every Japanese string this item puts in front of a learner. Mirrors the validator's `visible_jp`. */
function visibleJp(it: ExamBankItem, type: string): string[] {
  const out: string[] = [];
  for (const v of [it.stem, it.question, it.correct, it.answer, it.target]) {
    if (v) out.push(v);
  }
  for (const list of [it.distractors, it.wrong, it.pieces]) {
    for (const v of list ?? []) if (v) out.push(v);
  }
  for (const turn of it.script ?? []) if (turn?.text) out.push(turn.text);
  // reading_comp prints the passage above the question; text_grammar's stem IS the passage, so
  // adding it there would double-count the same characters (validator's note, kept).
  if (type === "reading_comp" && it.reading) {
    const jp = READINGS[it.reading]?.jp;
    if (jp) out.push(jp);
  }
  return out;
}

/**
 * The level-gate predicate, at an arbitrary known-set.
 *
 *   kanji   — every ideograph in the visible strings must be `kanji:<c>` in the known set.
 *   vocab   — the item's own `vocab` slug (kr/or/cf/pp/us name their word).
 *   grammar — the item's own `grammar` key (gf/tg) plus the `grammar[]` tags of the sentence its
 *             `sentence` ref names. 「一人で行くしかない」 is an N5 sentence_order item built on しかない,
 *             which the course does not teach until N3; the sentence's own dissection is what says so.
 *   passage — a passage-backed item whose passage does not resolve cannot be proven teachable.
 *
 * ONE DIMENSION IS MISSING HERE AND IT IS THE DATA'S FAULT, NOT A SHORTCUT. The validator also checks
 * every `tokens[].vocab` slug of the source sentence (20,490 of the corpus bank's 49,756 tokens carry
 * one). The app's synced `sentences.json` is a rendered view whose tokens keep only surface / reading
 * / romaji / pos / gloss / role — the vocab slug is dropped in export, so there is nothing here to
 * check against, and re-deriving it by matching surfaces to headwords would be exactly the re-guess
 * the validator refuses to make. Consequence, stated rather than hidden: this filter is slightly MORE
 * PERMISSIVE than the gate — it can admit an item whose source sentence contains an untaught
 * kana-only word. (An untaught word written in kanji is still caught, by the kanji dimension.) The
 * fix is a sync that carries `tokens[].vocab`, which is not this unit's to make.
 */
function insideKnownSet(it: ExamBankItem, type: string, known: KnownSet): boolean {
  for (const s of visibleJp(it, type)) {
    for (const c of s.match(KANJI_RE) ?? []) {
      if (!known.kanji.has(`kanji:${c}`)) return false;
    }
  }
  if (it.vocab && !known.vocab.has(it.vocab)) return false;

  const src = it.sentence ? SENTENCES[it.sentence] : undefined;
  if (it.sentence && !src) return false;   // unresolvable source: its grammar cannot be proven taught
  const grammarRefs: string[] = [];
  if (it.grammar) grammarRefs.push(it.grammar);
  for (const g of src?.grammar ?? []) grammarRefs.push(g);
  for (const g of grammarRefs) {
    if (!known.grammar.has(gramSlug(g))) return false;
  }

  if ((type === "reading_comp" || type === "text_grammar") &&
      (!it.reading || !READINGS[it.reading])) return false;

  return true;
}

/** mulberry32, same generator exam.server uses — a study set is reproducible from its lesson id. */
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

export interface StudyOption { text: string; correct: boolean }
export interface StudyItem {
  id: string;
  type: string;
  label: string;
  jp: string;
  level: string;
  prompt: string;
  focus?: string;
  passage?: string;
  script?: ScriptTurn[];
  audio?: string;
  /** 聴解. Decided here so the page never has to import this module to ask (see `isOrdering`). */
  listening: boolean;
  /** 並べ替え: the page shows chips and reveals the order instead of grading a choice. */
  ordering: boolean;
  /** Shuffled, and carrying the key: immediate feedback is the mode's whole point. */
  options: StudyOption[];
  /** sentence_order: the pieces, shuffled. Study mode reveals the assembled answer instead of grading. */
  pieces?: string[];
  /** What the learner is shown as correct — punctuated when the bank carries that form. */
  answer: string;
  /** The item's own explanation. No bank item carries one today; the field is honoured when they do. */
  explanation?: string;
  /** Layer-B fact, not an explanation: the sentence the item was built on, and its pt-BR. */
  source?: { jp: string; pt: string };
}
export interface StudyTypeCount { type: string; label: string; jp: string; n: number }
export interface StudySet {
  lesson: { id: string; title: string; level: string };
  known: { kanji: number; vocab: number; grammar: number };
  /** How many bank items in total sit inside this lesson's known set. */
  eligible: number;
  /** Eligible count per 大問, in paper order — the honest picture of what this lesson can drill. */
  byType: StudyTypeCount[];
  items: StudyItem[];
  offset: number;
  limit: number;
}

export const STUDY_PAGE = 12;

/**
 * Every bank item inside a lesson's known set, in paper-section order then bank order.
 *
 * Listening is filtered by `playable` for the same reason a paper filters it: without audio a 聴解
 * item is not a listening exercise, it is a reading exercise wearing one's clothes, and drilling it
 * that way teaches the wrong skill. Once the audio lands they appear here automatically.
 */
function eligibleItems(known: KnownSet, levels: readonly Level[]): Map<string, ExamBankItem[]> {
  const out = new Map<string, ExamBankItem[]>();
  for (const spec of SECTIONS) {
    const pool: ExamBankItem[] = [];
    for (const lv of levels) {
      for (const it of playable(BANKS[lv]?.[spec.type] ?? [], spec.type)) {
        if (insideKnownSet(it, spec.type, known)) pool.push(it);
      }
    }
    if (pool.length) out.set(spec.type, pool);
  }
  return out;
}

/** The levels a lesson may draw from: its own and everything below it. cks is cumulative anyway. */
function levelsUpTo(level: string): Level[] {
  const order: Level[] = ["n5", "n4", "n3"];
  const i = order.indexOf(level as Level);
  return i === -1 ? [] : order.slice(0, i + 1);
}

export function studySet(lessonId: string, offset = 0, limit = STUDY_PAGE): StudySet | null {
  const lesson = LESSONS[lessonId];
  if (!lesson) return null;
  const known = knownSetOf(lesson);
  const levels = levelsUpTo(lesson.level ?? "");
  const pools = eligibleItems(known, levels.length ? levels : LEVELS);

  const byType: StudyTypeCount[] = [];
  const ordered: { spec: (typeof SECTIONS)[number]; it: ExamBankItem }[] = [];
  for (const spec of SECTIONS) {
    const pool = pools.get(spec.type) ?? [];
    if (!pool.length) continue;
    byType.push({ type: spec.type, label: spec.label, jp: spec.jp, n: pool.length });
    for (const it of pool) ordered.push({ spec, it });
  }

  // Stable per lesson: the same lesson always deals the same order, so "page 2" means something and
  // a learner can come back to where they were without any stored state.
  const rand = rng(seedOf(lessonId));
  const deck = shuffle(ordered, rand);
  const page = deck.slice(Math.max(0, offset), Math.max(0, offset) + limit);

  const items: StudyItem[] = [];
  for (const { spec, it } of page) {
    const p = presentItem(it, spec.type);
    if (!p) continue;
    const itemRand = rng(seedOf(it.id));
    const src = it.sentence ? SENTENCES[it.sentence] : undefined;
    items.push({
      id: it.id,
      type: spec.type,
      label: spec.label,
      jp: spec.jp,
      level: it.level,
      prompt: p.prompt,
      focus: p.focus,
      passage: spec.showsPassage && it.reading ? READINGS[it.reading]?.jp : undefined,
      // Study mode SHOWS the script: design/listening.md allows the transcript here and forbids it in
      // the exam. A `playable` item has audio, so the script is the transcript beside the recording.
      script: p.script,
      audio: p.audio,
      listening: isListening(spec.type),
      ordering: isOrdering(spec.type),
      options: p.pieces
        ? []
        : shuffle(p.options, itemRand).map((text) => ({ text, correct: text === it.correct })),
      pieces: p.pieces ? shuffle(p.pieces, itemRand) : undefined,
      answer: displayAnswerOf(it),
      explanation: it.explanation,
      source: src?.jp
        ? { jp: src.jp, pt: loc(src.translation) }
        : undefined,
    });
  }

  return {
    lesson: { id: lesson.id, title: loc(lesson.title) || lesson.id, level: lesson.level ?? "" },
    known: { kanji: known.kanji.size, vocab: known.vocab.size, grammar: known.grammar.size },
    eligible: ordered.length,
    byType,
    items,
    offset: Math.max(0, offset),
    limit,
  };
}

/**
 * The lesson that ends a level — its `cumulative_known_set` IS "everything taught by the end of that
 * level", which is the exact set the level gate measures against. Used as the default entry point
 * into study mode from the simulator's level picker.
 */
export function lastLessonOfLevel(level: string): { id: string; title: string } | null {
  let best: LessonRecord | null = null;
  let bestSize = -1;
  for (const lesson of Object.values(LESSONS)) {
    if (lesson.level !== level) continue;
    const size = (lesson.cumulative_known_set?.vocab ?? []).length;
    if (size > bestSize) { best = lesson; bestSize = size; }
  }
  return best ? { id: best.id, title: loc(best.title) || best.id } : null;
}

/**
 * Is this item type graded by assembling chips rather than picking an option?
 *
 * NOT exported, and that is the point. A route's COMPONENT may not call into this module: React
 * Router strips `loader`/`action` from the client build and then tree-shakes, so a helper used in
 * JSX keeps the whole module — and this one has three bank files in its import graph. The component
 * gets `ordering` / `listening` as booleans on each item instead, decided here, on the server.
 */
function isOrdering(type: string): boolean {
  return type === "sentence_order";
}
