/**
 * drill — the pieces of a drill round that the COMPONENT needs, deliberately not in a `.server` module.
 *
 * React Router strips `loader`, `action`, `headers` and `middleware` from the client bundle, so a route
 * may freely import server-only code for those. The default export is client code and may not. Both
 * drill routes rendered `Uma rodada de {ROUND} …` in the component while importing ROUND from
 * `*.server`, which drags the whole server module — and with it the 18,524-item conjugation bank and the
 * 5,358-item role bank — into the client graph. Vite refuses, and the production build fails:
 *
 *     Server-only module referenced by client
 *       '~/lib/conjugation.server' imported by route 'app/routes/conjugationDrill.tsx'
 *
 * `npm run typecheck` does not catch this, because the types are perfectly valid; only the bundler
 * knows about the server/client boundary. So these constants live here, in a plain module both sides
 * can import, and the `.server` files import them from here rather than defining them.
 */
export type Level = "n5" | "n4" | "n3";
export const LEVELS: Level[] = ["n5", "n4", "n3"];

/** Questions per round. Shared by both drills, and rendered in both components. */
export const ROUND = 10;
