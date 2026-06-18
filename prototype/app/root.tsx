import { Links, Meta, Outlet, Scripts, ScrollRestoration } from "react-router";
import type { LinksFunction } from "react-router";

import indexCss from "./ui/index.css?url";
import ymCss from "./ui/yomineko/yomineko.css?url";
import ymComponentsCss from "./ui/yomineko/yomineko-components.css?url";
import lessonCss from "./styles/lesson.css?url";

export const links: LinksFunction = () => [
  { rel: "preconnect", href: "https://fonts.googleapis.com" },
  { rel: "preconnect", href: "https://fonts.gstatic.com", crossOrigin: "anonymous" },
  {
    rel: "stylesheet",
    href: "https://fonts.googleapis.com/css2?family=Poppins:wght@400;500;600;700&family=Nunito:wght@400;500;600;700;800&family=Noto+Sans+JP:wght@400;500;700&family=Noto+Serif+JP:wght@500;700&display=swap",
  },
  {
    rel: "stylesheet",
    href: "https://fonts.googleapis.com/css2?family=Material+Symbols+Rounded:opsz,wght,FILL,GRAD@20..48,100..700,0..1,-50..200",
  },
  { rel: "stylesheet", href: indexCss },
  { rel: "stylesheet", href: ymCss },
  { rel: "stylesheet", href: ymComponentsCss },
  { rel: "stylesheet", href: lessonCss },
];

// The token scope (.ym) + theme live on <body>, which persists across client navigations (so dark mode
// sticks) and is not React-controlled for data-theme. This inline script is the FIRST thing in <body>, so it
// sets the theme synchronously before any content paints — no flash, no SSR/client mismatch.
const THEME_BOOT = `(function(){try{document.body.dataset.theme=localStorage.getItem('ym-theme')||'light';}catch(e){document.body.dataset.theme='light';}})();`;

export function Layout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="pt-BR">
      <head>
        <meta charSet="utf-8" />
        <meta name="viewport" content="width=device-width, initial-scale=1" />
        {/* private research prototype — keep it out of search engines */}
        <meta name="robots" content="noindex, nofollow" />
        <Meta />
        <Links />
      </head>
      {/* data-theme is set by the boot script below before paint; React must not fight it on hydration. */}
      <body className="ym" suppressHydrationWarning>
        <script dangerouslySetInnerHTML={{ __html: THEME_BOOT }} />
        {children}
        <ScrollRestoration />
        <Scripts />
      </body>
    </html>
  );
}

export default function App() {
  return <Outlet />;
}

export function ErrorBoundary() {
  return (
    <div style={{ minHeight: "100dvh", display: "grid", placeItems: "center", padding: 24 }}>
      <div className="card card-elevated" style={{ padding: 24, maxWidth: 420, textAlign: "center" }}>
        <div className="title-l" style={{ marginBottom: 8 }}>Algo deu errado</div>
        <div className="body-m" style={{ color: "var(--on-surface-variant)" }}>Tente recarregar a página.</div>
        <a className="btn btn-filled" href="/" style={{ marginTop: 16, display: "inline-flex" }}>Voltar ao início</a>
      </div>
    </div>
  );
}
