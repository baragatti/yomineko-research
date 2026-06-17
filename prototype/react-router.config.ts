import type { Config } from "@react-router/dev/config";

export default {
  // SSR ONLY. Every route is server-rendered; the corpus data + the tag renderer live
  // in *.server.ts modules that are never bundled to the client. No prerendering to
  // static files (that would dump the content to disk), no SPA fallback.
  ssr: true,
} satisfies Config;
