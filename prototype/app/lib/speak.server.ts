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
import { getSentence, sentenceView, allVocab, allGrammar, loc, type SentenceView } from "./corpus.server";

interface RawUnit {
  id: string; stage: string; order: number; title: Record<string, string>;
  say_now: string[]; chunk_phrases: string[]; untranslated: string[];
  words: string[]; patterns: string[]; signage_kanji: string[];
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

export interface SpeakWord { slug: string; headword: string; kana: string; romaji: string; level: string }
export interface SpeakPattern { slug: string; key: string; label: string; level: string }
export interface SpeakUnit {
  id: string; stage: string; stageTitle: string; order: number; title: string;
  phrases: (SentenceView & { chunk: boolean })[];
  words: SpeakWord[]; patterns: SpeakPattern[]; signage: string[];
  knownSoFar: number; prev: string | null; next: string | null;
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
      return v ? { slug, headword: v.headword, kana: v.kana, romaji: v.romaji ?? "",
                   level: v.level ?? "" } : null;
    }).filter(Boolean) as SpeakWord[],
    patterns: u.patterns.map((slug) => {
      const g = grammarBySlug.get(slug);
      return g ? { slug, key: g.key, label: loc(g.label) || g.key, level: g.level ?? "" } : null;
    }).filter(Boolean) as SpeakPattern[],
    signage: u.signage_kanji ?? [],
    knownSoFar: u.cumulative_known_vocab,
    prev: i > 0 ? ORDER[i - 1] : null,
    next: i >= 0 && i < ORDER.length - 1 ? ORDER[i + 1] : null,
  };
}

/** "speak:eating-02" -> { stage: "eating", order: 2 } — for prev/next links. */
export function splitUnitId(id: string): { stage: string; order: number } {
  const body = id.split(":")[1] ?? "";
  const at = body.lastIndexOf("-");
  return { stage: body.slice(0, at), order: Number(body.slice(at + 1)) };
}
