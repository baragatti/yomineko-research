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

/** short {id,title} for a lesson (prev/next labels). */
export function lessonRef(id: string | null): { id: string; title: string } | null {
  if (!id) return null;
  const l = getLesson(id);
  return l ? { id: l.id, title: loc(l.title) } : null;
}

const stripPrefix = (ref: string) => (ref.includes(":") ? ref.split(":", 2)[1] : ref);

/* ---- reverse index: which lessons introduce a given kanji / vocab / grammar (from lesson.unlocks) ---- */
type Edge = { id: string; title: string; order: number; level: string };
let _rev: { kanji: Dict<Edge[]>; vocab: Dict<Edge[]>; grammar: Dict<Edge[]> } | null = null;
function reverseIndex() {
  if (_rev) return _rev;
  const rev = { kanji: {} as Dict<Edge[]>, vocab: {} as Dict<Edge[]>, grammar: {} as Dict<Edge[]> };
  for (const l of Object.values(lessons) as any[]) {
    const edge: Edge = { id: l.id, title: loc(l.title), order: l.order ?? 0, level: l.level };
    for (const u of l.unlocks || []) {
      const bucket = u.type === "kanji" ? rev.kanji : u.type === "vocab" ? rev.vocab : u.type === "grammar" ? rev.grammar : null;
      if (!bucket) continue;
      const key = stripPrefix(u.ref);
      (bucket[key] ||= []).push(edge);
    }
  }
  _rev = rev;
  return rev;
}
/** lessons that introduce this entity, in course order. */
export function lessonsUsing(kind: "kanji" | "vocab" | "grammar", id: string): { id: string; title: string }[] {
  const list = reverseIndex()[kind][id] || [];
  return list.slice().sort((a, b) => a.order - b.order).map((e) => ({ id: e.id, title: e.title }));
}

/** resolve a lesson's `unlocks` into linkable chips grouped by kind (server-side; ships only label+href). */
export function resolveUnlocks(lesson: any) {
  const out = { kanji: [] as any[], vocab: [] as any[], grammar: [] as any[] };
  for (const u of lesson?.unlocks || []) {
    const id = stripPrefix(u.ref);
    if (u.type === "kanji" && getKanji(id)) out.kanji.push({ id, label: id, href: `/kanji/${encodeURIComponent(id)}` });
    else if (u.type === "vocab") {
      const v = getVocab(id);
      if (v) out.vocab.push({ id, label: v.kana || id, sub: id, href: `/vocabulario/${encodeURIComponent(id)}` });
    } else if (u.type === "grammar") {
      const g = getGrammar(id);
      if (g) out.grammar.push({ id, label: g.forms?.[0]?.form || g.structure_pattern || loc(g.label) || id, href: `/gramatica/${encodeURIComponent(id)}` });
    }
  }
  return out;
}
