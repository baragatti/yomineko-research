/**
 * speak — the speaking-path helpers the COMPONENT calls, deliberately outside `speak.server`.
 *
 * Both are pure string functions with no data behind them, but living in `speak.server` they made the
 * route's default export depend on that module, which pulls the whole speaking path (72 units, 432
 * phrases) into the client bundle. React Router strips server code from `loader`/`action`/`headers`/
 * `middleware` only; the component is client code, and the production build refuses:
 *
 *     Server-only module referenced by client
 *       '~/lib/speak.server' imported by route 'app/routes/speakUnit.tsx'
 *
 * See ~/lib/drill for the same split on the two drill routes. `npm run typecheck` passes either way —
 * the types are fine, and only the bundler knows about the server/client boundary.
 */
const LABEL: Record<string, string> = {
  sentence_order: "Monte a frase",
  context_fill: "Complete a frase",
  kanji_reading: "Como se lê?",
  paraphrase: "Sentido mais próximo",
  usage: "Uso correto",
};
export const checkpointLabel = (t: string) => LABEL[t] ?? t;

/** "speak:eating-02" -> { stage: "eating", order: 2 } — for prev/next links. */
export function splitUnitId(id: string): { stage: string; order: number } {
  const body = id.split(":")[1] ?? "";
  const at = body.lastIndexOf("-");
  return { stage: body.slice(0, at), order: Number(body.slice(at + 1)) };
}
