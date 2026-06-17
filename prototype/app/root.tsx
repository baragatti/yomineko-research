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

// Apply the saved theme to the .ym shell before paint (avoids a flash). The shell carries class "ym".
const THEME_BOOT = `(function(){try{var t=localStorage.getItem('ym-theme')||'light';document.addEventListener('DOMContentLoaded',function(){var e=document.querySelector('.ym');if(e)e.setAttribute('data-theme',t);});var o=new MutationObserver(function(){var e=document.querySelector('.ym');if(e){e.setAttribute('data-theme',t);o.disconnect();}});o.observe(document.documentElement,{childList:true,subtree:true});}catch(e){}})();`;

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
        <script dangerouslySetInnerHTML={{ __html: THEME_BOOT }} />
      </head>
      <body>
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
    <div className="ym" data-theme="light" style={{ minHeight: "100dvh", display: "grid", placeItems: "center", padding: 24 }}>
      <div className="card card-elevated" style={{ padding: 24, maxWidth: 420, textAlign: "center" }}>
        <div className="title-l" style={{ marginBottom: 8 }}>Algo deu errado</div>
        <div className="body-m" style={{ color: "var(--on-surface-variant)" }}>Tente recarregar a página.</div>
        <a className="btn btn-filled" href="/" style={{ marginTop: 16, display: "inline-flex" }}>Voltar ao início</a>
      </div>
    </div>
  );
}
