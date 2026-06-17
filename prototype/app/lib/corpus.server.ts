/**
 * corpus.server — the ONLY gateway to the research data. The `.server.ts` suffix guarantees React Router
 * never bundles this (or the JSON it imports) into the client: the dataset + the tagged authoring source
 * exist only on the server. Routes call these helpers in their loaders and return rendered/derived output.
 */
import coursesData from "../data/courses.json";
import topicsData from "../data/topics.json";
import lessonsData from "../data/lessons.json";
import kanjiData from "../data/kanji.json";
import vocabData from "../data/vocab.json";
import grammarData from "../data/grammar.json";
import sentencesData from "../data/sentences.json";
import kanaData from "../data/kana.json";

export const PT = "pt-BR";

/** localized value -> pt-BR string (falls back to en, then raw). */
export function loc(v: unknown): string {
  if (v == null) return "";
  if (typeof v === "string") return v;
  const o = v as Record<string, string>;
  return o[PT] ?? o.en ?? Object.values(o)[0] ?? "";
}
export function locList(v: unknown): string[] {
  if (Array.isArray(v)) return v.map(loc);
  return [];
}
/** locale-object whose values are arrays (e.g. kanji.meanings, vocab gloss) -> pt-BR string[]. */
export function locArr(v: unknown): string[] {
  if (v == null) return [];
  if (Array.isArray(v)) return v.map(loc);
  const o = v as Record<string, unknown>;
  const arr = (o[PT] ?? o.en ?? Object.values(o)[0]) as unknown;
  return Array.isArray(arr) ? (arr as string[]) : [];
}

type Dict<T = any> = Record<string, T>;
export const courses = coursesData as any[];
const topics = topicsData as Dict;
const lessons = lessonsData as Dict;
const kanji = kanjiData as Dict;
const vocab = vocabData as Dict;
const grammar = grammarData as Dict;
const sentences = sentencesData as Dict;
export const kana = kanaData as Dict;

export const getCourse = (level: string) => courses.find((c) => c.level === level);
export const getTopic = (id: string) => topics[id];
export const getLesson = (id: string) => lessons[id];
export const getSentence = (slug: string) => sentences[slug];
export const getKanji = (ch: string) => kanji[ch];
export const getVocab = (hw: string) => vocab[hw];
export const getGrammar = (key: string) => grammar[key];

export const allKanji = () => Object.values(kanji);
export const allVocab = () => Object.values(vocab);
export const allGrammar = () => Object.values(grammar);

/** ordered course/topic/lesson navigation index (for prev/next + breadcrumbs). */
export function courseTree() {
  return courses
    .slice()
    .sort((a, b) => a.order - b.order)
    .map((c) => ({
      id: c.id,
      level: c.level,
      title: loc(c.title),
      topicCount: c.topic_count,
      lessonCount: c.lesson_count,
      topics: (c.topics || []).map((t: any) => ({
        id: t.id,
        order: t.order,
        title: loc(t.title),
        theme: t.theme,
        lessonCount: t.lesson_count,
        unlocks: t.unlocks_summary,
        lessons: (getTopic(t.id)?.lessons || []).map((l: any) => ({
          id: l.id,
          order: l.order,
          title: loc(l.title),
          description: loc(l.description),
        })),
      })),
    }));
}

/** flat ordered lesson list for a level (for prev/next within a course). */
export function lessonsOfLevel(level: string): string[] {
  const c = getCourse(level);
  if (!c) return [];
  const ids: string[] = [];
  for (const t of c.topics || []) for (const lid of getTopic(t.id)?.lessons?.map((l: any) => l.id) || []) ids.push(lid);
  return ids;
}
