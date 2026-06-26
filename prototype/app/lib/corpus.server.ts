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
import strokesData from "../data/strokes.json";
import kanaStrokesData from "../data/kanaStrokes.json";

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

/* ---- kana -> romaji (wapuro Hepburn; for compact kanji "names" + readings) ---- */
const ROMAJI_BASE: Record<string, string> = {
  あ: "a", い: "i", う: "u", え: "e", お: "o", か: "ka", き: "ki", く: "ku", け: "ke", こ: "ko",
  が: "ga", ぎ: "gi", ぐ: "gu", げ: "ge", ご: "go", さ: "sa", し: "shi", す: "su", せ: "se", そ: "so",
  ざ: "za", じ: "ji", ず: "zu", ぜ: "ze", ぞ: "zo", た: "ta", ち: "chi", つ: "tsu", て: "te", と: "to",
  だ: "da", ぢ: "ji", づ: "zu", で: "de", ど: "do", な: "na", に: "ni", ぬ: "nu", ね: "ne", の: "no",
  は: "ha", ひ: "hi", ふ: "fu", へ: "he", ほ: "ho", ば: "ba", び: "bi", ぶ: "bu", べ: "be", ぼ: "bo",
  ぱ: "pa", ぴ: "pi", ぷ: "pu", ぺ: "pe", ぽ: "po", ま: "ma", み: "mi", む: "mu", め: "me", も: "mo",
  や: "ya", ゆ: "yu", よ: "yo", ら: "ra", り: "ri", る: "ru", れ: "re", ろ: "ro", わ: "wa", ゐ: "i", ゑ: "e", を: "o", ん: "n",
  ぁ: "a", ぃ: "i", ぅ: "u", ぇ: "e", ぉ: "o", ゃ: "ya", ゅ: "yu", ょ: "yo", ゔ: "vu",
};
const ROMAJI_YOON: Record<string, string> = {
  きゃ: "kya", きゅ: "kyu", きょ: "kyo", ぎゃ: "gya", ぎゅ: "gyu", ぎょ: "gyo", しゃ: "sha", しゅ: "shu", しょ: "sho",
  じゃ: "ja", じゅ: "ju", じょ: "jo", ちゃ: "cha", ちゅ: "chu", ちょ: "cho", にゃ: "nya", にゅ: "nyu", にょ: "nyo",
  ひゃ: "hya", ひゅ: "hyu", ひょ: "hyo", びゃ: "bya", びゅ: "byu", びょ: "byo", ぴゃ: "pya", ぴゅ: "pyu", ぴょ: "pyo",
  みゃ: "mya", みゅ: "myu", みょ: "myo", りゃ: "rya", りゅ: "ryu", りょ: "ryo",
};
const kataToHira = (s: string) => s.replace(/[ァ-ヶ]/g, (c) => String.fromCharCode(c.charCodeAt(0) - 0x60));
export function kanaToRomaji(input: string): string {
  const s = kataToHira(String(input ?? "").replace(/[.・]/g, "").replace(/-/g, ""));
  let out = "";
  for (let i = 0; i < s.length; ) {
    const two = s.slice(i, i + 2);
    if (ROMAJI_YOON[two]) { out += ROMAJI_YOON[two]; i += 2; continue; }
    const c = s[i];
    if (c === "っ") { const nr = ROMAJI_YOON[s.slice(i + 1, i + 3)] || ROMAJI_BASE[s[i + 1]] || ""; if (nr) out += nr[0]; i++; continue; }
    if (c === "ー") { out += out.slice(-1); i++; continue; }
    if (ROMAJI_BASE[c] !== undefined) { out += ROMAJI_BASE[c]; i++; continue; }
    out += c; i++;
  }
  return out;
}
/** compact romaji "name" for a kanji: primary common on-reading, else first common kun base. */
export function kanjiRomaji(k: any): string {
  const rs = (k?.readings || []) as any[];
  const on = rs.find((r) => r.type === "on" && r.common) || rs.find((r) => r.type === "on");
  const kun = rs.find((r) => r.type === "kun" && r.common) || rs.find((r) => r.type === "kun");
  const pick = on || kun;
  return pick ? kanaToRomaji(pick.reading) : "";
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
const strokes = strokesData as Dict;
/** Kanji Alive (CC BY 4.0) stroke-order steps for a kanji, or null if we have none (→ show decomposition). */
export const getStrokes = (ch: string) => (strokes[ch] as
  | { total_strokes: number; viewbox: string; transform: string; steps: string[]; source: string }
  | undefined) ?? null;
const kanaStrokes = kanaStrokesData as Dict;
/** strokesvg (OFL+MIT) per-stroke centerlines for a kana, or null. */
export const getKanaStrokes = (ch: string) => (kanaStrokes[ch] as
  | { viewbox: string; strokes: string[]; kind: string } | undefined) ?? null;
/** the kana syllabary families ({hiragana:[…], katakana:[…]}) for the /kana chart. */
export const kanaFamilies = () => kana as unknown as {
  hiragana: any[]; katakana: any[];
};

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

/* ---- example-sentence lookup for detail pages (server-only; pages render a handful) ---- */
export interface BdToken { s: string; r?: string; ro?: string; pos?: string; gloss?: string; role?: string }
export interface BdParticle { p: string; ft?: string; fn?: string; ex?: string }
export interface SentenceView {
  slug: string; jp: string; romaji: string; pt: string; literal: string; explanation: string;
  tokens: BdToken[]; particles: BdParticle[];
}
/** flat display view of a sentence (callers pass an already-resolved sentence), incl. the breakdown. */
export function sentenceView(s: any): SentenceView {
  return {
    slug: s.slug, jp: s.jp, romaji: s.romaji,
    pt: loc(s.translation), literal: loc(s.translation_literal), explanation: loc(s.structure_explanation),
    tokens: (s.tokens || []) as BdToken[],
    particles: (s.particles || []) as BdParticle[],
  };
}
let _grammarSents: Dict<string[]> | null = null;
function grammarSentIndex(): Dict<string[]> {
  if (_grammarSents) return _grammarSents;
  const idx: Dict<string[]> = {};
  for (const s of Object.values(sentences) as any[]) for (const g of s.grammar || []) (idx[g] ||= []).push(s.slug);
  _grammarSents = idx;
  return idx;
}
const byLenShortFirst = (a: any, b: any) => (a.jp?.length ?? 0) - (b.jp?.length ?? 0);

/** curated example sentences for a kanji (from kanji.example_sentences), shortest first. */
export function sentencesForKanji(ch: string, limit = 5) {
  const k = getKanji(ch);
  const list = (k?.example_sentences || []).map((slug: string) => getSentence(slug)).filter(Boolean);
  list.sort(byLenShortFirst);
  return list.slice(0, limit).map(sentenceView);
}
/** example sentences that use a grammar point (by its tag), shortest first (most beginner-friendly). */
export function sentencesForGrammar(key: string, limit = 5) {
  const list = (grammarSentIndex()[key] || []).map((slug) => getSentence(slug)).filter(Boolean);
  list.sort(byLenShortFirst);
  return list.slice(0, limit).map(sentenceView);
}
/** example sentences that contain a vocab headword, shortest first. */
export function sentencesForVocab(headword: string, limit = 5) {
  const hits: any[] = [];
  for (const s of Object.values(sentences) as any[]) if (s.jp && s.jp.includes(headword)) hits.push(s);
  hits.sort(byLenShortFirst);
  return hits.slice(0, limit).map(sentenceView);
}

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

/* ---- rich summaries for the in-lesson hover tooltip + click modal ---- */
export interface RefReading { r: string; romaji: string }
export interface RefSummary {
  kind: "kanji" | "vocab" | "grammar";
  id: string;
  title: string;
  sub?: string;
  romaji?: string;
  meanings?: string[];
  gloss?: string;
  strokes?: number;
  kun?: RefReading[];
  on?: RefReading[];
  examples?: { hw: string; kana: string; gloss: string }[];
  senses?: { pos: string[]; gloss: string[] }[];
  pattern?: string;
  forms?: { form: string; meaning: string }[];
  explanation?: string;
  href: string;
}
const clip = (s: string, n: number) => (s.length > n ? s.slice(0, n).replace(/\s+\S*$/, "") + "…" : s);

export function refSummary(kind: "kanji" | "vocab" | "grammar", id: string): RefSummary | null {
  if (kind === "kanji") {
    const k = getKanji(id);
    if (!k) return null;
    const rd = (k.readings || []).filter((r: any) => r.common);
    const mk = (type: string): RefReading[] =>
      rd.filter((r: any) => r.type === type).slice(0, 6).map((r: any) => {
        const full = r.reading + (r.okurigana ? "・" + r.okurigana : "");
        return { r: full, romaji: kanaToRomaji(r.reading + (r.okurigana || "")) };
      });
    const meanings = locArr(k.meanings);
    return {
      kind, id, title: k.character, romaji: kanjiRomaji(k), meanings, gloss: meanings.slice(0, 3).join(", "),
      strokes: k.strokes, kun: mk("kun"), on: mk("on"),
      examples: (k.example_words || []).slice(0, 6).map((w: any) => ({ hw: w.headword, kana: w.kana, gloss: locArr(w.gloss)[0] ?? "" })),
      href: `/kanji/${encodeURIComponent(id)}`,
    };
  }
  if (kind === "vocab") {
    const v = getVocab(id);
    if (!v) return null;
    const senses = (v.senses || []).slice(0, 6).map((s: any) => ({ pos: s.pos || [], gloss: locArr(s.gloss) }));
    return {
      kind, id, title: v.headword, sub: v.kana, romaji: v.romaji ?? "",
      gloss: (senses[0]?.gloss || []).slice(0, 3).join(", "), senses,
      href: `/vocabulario/${encodeURIComponent(id)}`,
    };
  }
  const g = getGrammar(id);
  if (!g) return null;
  return {
    kind, id, title: loc(g.label), pattern: g.structure_pattern || "",
    gloss: loc(g.forms?.[0]?.meaning) || loc(g.label) || "",
    forms: (g.forms || []).slice(0, 4).map((f: any) => ({ form: f.form, meaning: loc(f.meaning) })),
    explanation: clip(loc(g.explanation), 260),
    href: `/gramatica/${encodeURIComponent(id)}`,
  };
}

/** rich summaries for every kanji/vocab/grammar ref in a lesson body, keyed by `${kind}:${id}`. */
export function refSummaries(body: string): Record<string, RefSummary> {
  const out: Record<string, RefSummary> = {};
  for (const m of (body || "").matchAll(/<(kanji|vocab|grammar)\s+ref="([^"]+)"/g)) {
    const kind = m[1] as "kanji" | "vocab" | "grammar";
    const id = stripPrefix(m[2]);
    const key = `${kind}:${id}`;
    if (!out[key]) { const s = refSummary(kind, id); if (s) out[key] = s; }
  }
  return out;
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
