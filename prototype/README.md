# Yomineko Prototype (SSR)

A server-rendered prototype that drives the original Yomineko UI design system with **real corpus data**
from this research project (213 lessons, full N5/N4 corpus). Built with **React Router v7 (framework mode,
SSR-only)** so the private corpus is never shipped to the browser.

> This lives inside `yomineko-research/prototype` for development. When we want to publish, we copy it back
> into the standalone `yomineko-prototype` repo and deploy from there (see **Copy-back workflow** below).

---

## Why SSR-only (the hard requirement)

The corpus is private, paid content. It must not be fetchable/scrapable from the browser. So:

- **`ssr: true`, no SPA, no prerender** (`react-router.config.ts`). Every page is rendered on the server.
- **All corpus access is in `*.server.ts` modules** (`app/lib/corpus.server.ts`, `app/lib/render-body.server.ts`).
  React Router's build *guarantees* `.server` modules (and the JSON they import) never enter the client bundle.
- **No API, no JSON endpoints, no static corpus files.** There is nothing to `fetch`.
- **Lesson bodies are rendered to display HTML on the server.** The tagged authoring source
  (`<heading>`, `<sentence ref=…>`, `<vocab ref=…>`, etc.) and the corpus internals never reach the client —
  only the final styled markup does.

Build-time proof (run after `npm run build`):

```
build/client  ~465 KB   # no corpus — class names + UI chrome only
build/server  ~10.8 MB  # corpus JSON is bundled HERE, server-side only
```

Searching `build/client` for corpus sentences / translations / data JSON returns nothing. The only
content-like strings in the client are CSS class selectors and the prototype's own UI copy.

---

## Project layout

```
app/
  root.tsx               document shell (fonts, CSS, theme boot, noindex)
  routes.ts              route table
  routes/                home, course, topic, lesson, kanji(+detail),
                         vocab(+detail), grammar(+detail), login, soon, health
  lib/
    corpus.server.ts     ONLY gateway to the data (server-only)
    render-body.server.ts tagged-body -> display-HTML renderer (server-only)
  ui/
    AppShell.tsx         responsive shell (drawer + topbar + bottom nav)
    Icon.tsx             Material Symbols icon
    yomineko/            design system CSS + mascot SVGs (reused from original)
  styles/lesson.css      SSR shell + lesson-body + content-component styles
  data/                  generated corpus snapshot (committed, see sync-data)
scripts/sync-data.mjs    consolidates ../corpus + ../course -> app/data/*.json
Dockerfile               SSR Node runtime (react-router-serve)
```

`app/data/` is committed (not git-ignored) so the prototype is self-contained for Coolify. Re-generate it
whenever the corpus changes (see below).

---

## Develop

```bash
npm install
npm run sync-data     # rebuild app/data/*.json from ../corpus + ../course
npm run dev           # http://localhost:3000
npm run build         # production build (client + server bundles)
npm run start         # serve the production build (PORT/HOST from env)
```

`npm run sync-data` reads the corpus/courseware under the research repo and writes a consolidated,
**reference-filtered** snapshot into `app/data/` (only sentences actually referenced by a lesson are
included, keeping the snapshot ~2 MB instead of ~21 MB).

---

## Copy-back workflow (deploy)

We develop here, then mirror into the standalone `yomineko-prototype` repo for deployment. Coolify must keep
working with **only Dockerfile changes** (no server/Coolify config changes) — the container still listens on
port **80** and exposes `/health`.

1. In this folder, finish + verify: `npm run sync-data && npm run build` (and a quick `npm run start` smoke test).
2. Copy the app into the standalone repo, **replacing** its old Vite/SPA source:
   - `app/`, `public/`, `scripts/`
   - `package.json`, `package-lock.json`, `react-router.config.ts`, `vite.config.ts`, `tsconfig.json`
   - `Dockerfile`, `.dockerignore`
   - Remove the old static-build leftovers there: `index.html`, `src/`, `sws.toml`, `dist/`.
3. Commit + push the standalone repo (only when explicitly asked). Coolify rebuilds from the new Dockerfile:
   it now runs an SSR Node process instead of static-web-server, same port 80, same health check.

Keep `app/data/` committed in the standalone repo so the deployed image is self-contained.

---

## Notes / prototype shortcuts

- Auth is cosmetic: `/entrar` is a landing page; "Entrar" just enters the app. No real login.
- `revisar` / `pratica` / `perfil` are "em breve" placeholders (the interactive games from the original
  prototype are client-only and carry no corpus data; they can be ported as hydrated islands later).
- Route loaders/components use a few `any`s for the loader payloads; these can be tightened with React
  Router's generated `Route.*` types (`npm run typecheck` runs `react-router typegen && tsc`).
- `app/ui/{App,ReviewApp,SessionApp,store,useBreakpoint}.jsx` are carried over from the original prototype
  for reference and are **not** imported by any route (excluded from the build).
