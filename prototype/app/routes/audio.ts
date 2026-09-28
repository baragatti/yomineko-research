import { readFile } from "node:fs/promises";
import { AUDIO_KEY, audioFile } from "~/lib/audio.server";

/**
 * GET /audio/:key — a generated clip from the audio store. The key is validated against the 26-char
 * base32 pattern before any path is built (no traversal); absent -> 404. A key names one synthesis
 * request forever, so a found clip is immutable and cached for a year.
 */
export async function loader({ params }: { params: { key?: string } }) {
  const key = params.key ?? "";
  if (!AUDIO_KEY.test(key)) return new Response("Bad audio key", { status: 400 });
  const file = audioFile(key);
  if (!file) return new Response("Not found", { status: 404, headers: { "Cache-Control": "no-store" } });
  const body = await readFile(file.path);
  return new Response(body, {
    headers: {
      "Content-Type": file.type,
      "Content-Length": String(body.byteLength),
      "Cache-Control": "public, max-age=31536000, immutable",
      ETag: `"${key}"`,
    },
  });
}
