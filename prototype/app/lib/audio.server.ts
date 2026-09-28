/**
 * audio.server — find a generated clip in the audio store (W47, design/audio_pipeline.md §4.2).
 *
 * The export carries every voiceable item's `audio_key` (the content hash of its synthesis request,
 * scripts/audio/plan.py) whether or not the clip exists yet. Loaders pass a key to the page only when
 * `playable()` finds its file, so a play button appears exactly when the generator has written the
 * clip — checked on every request, no rebuild. Server-only: the store path never reaches the client.
 */
import { existsSync, readFileSync, statSync } from "node:fs";
import path from "node:path";

/** 26 chars of lower-case RFC 4648 base32: URL-, path- and case-insensitive-FS safe; no traversal. */
export const AUDIO_KEY = /^[a-z2-7]{26}$/;

const STORE = process.env.YOMINEKO_AUDIO_STORE || "C:/Users/WiseWolf/yomineko-audio/store";

export interface AudioFile { path: string; type: string }

// The generator's layout first (opus/<k[:2]>/<k>.opus, masters/<k[:2]>/<k>.flac), then a flat store.
const candidates = (k: string): readonly AudioFile[] => [
  { path: path.join(STORE, "opus", k.slice(0, 2), `${k}.opus`), type: "audio/ogg; codecs=opus" },
  { path: path.join(STORE, `${k}.opus`), type: "audio/ogg; codecs=opus" },
  { path: path.join(STORE, "masters", k.slice(0, 2), `${k}.flac`), type: "audio/flac" },
  { path: path.join(STORE, `${k}.flac`), type: "audio/flac" },
];

// A clip that passed only on a retake lives under a new key; the generator's aliases.json maps the
// take-1 key (the one the export carries) to it. Re-read when the file changes.
let aliases: { mtimeMs: number; map: Readonly<Record<string, string>> } = { mtimeMs: -1, map: {} };
function alias(key: string): string | undefined {
  const file = path.join(STORE, "aliases.json");
  try {
    const { mtimeMs } = statSync(file);
    if (mtimeMs !== aliases.mtimeMs) {
      const parsed: unknown = JSON.parse(readFileSync(file, "utf8"));
      const map: Record<string, string> = {};
      if (parsed && typeof parsed === "object") {
        for (const [k, v] of Object.entries(parsed)) if (typeof v === "string" && AUDIO_KEY.test(v)) map[k] = v;
      }
      aliases = { mtimeMs, map };
    }
  } catch {
    aliases = { mtimeMs: -1, map: {} };
  }
  return aliases.map[key];
}

/** The file for a key, or null. Never touches the disk for a string that is not a key. */
export function audioFile(key: string): AudioFile | null {
  if (!AUDIO_KEY.test(key)) return null;
  for (const k of [key, alias(key)]) {
    if (!k) continue;
    const hit = candidates(k).find((c) => existsSync(c.path));
    if (hit) return hit;
  }
  return null;
}

/** The key when its clip exists, else undefined: what a loader hands the page. */
export function playable(key: unknown): string | undefined {
  return typeof key === "string" && audioFile(key) ? key : undefined;
}
