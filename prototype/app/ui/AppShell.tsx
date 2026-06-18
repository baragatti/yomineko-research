import { useEffect, useState } from "react";
import { Link } from "react-router";
import { Icon } from "./Icon";
// @ts-ignore — mascot is pure-SVG JSX
import { YominekoLogo } from "./yomineko/mascot";

const NAV = [
  { id: "home", to: "/", icon: "home", label: "Início" },
  { id: "study", to: "/curso", icon: "auto_stories", label: "Curso" },
  { id: "review", to: "/revisar", icon: "style", label: "Revisar" },
  { id: "practice", to: "/pratica", icon: "target", label: "Prática" },
  { id: "vocab", to: "/vocabulario", icon: "menu_book", label: "Vocabulário" },
  { id: "kanji", to: "/kanji", icon: "translate", label: "Kanji" },
  { id: "profile", to: "/perfil", icon: "person", label: "Perfil" },
] as const;
// bottom nav (mobile has no drawer) — prioritize real content destinations over the "em breve" placeholders
const MOBILE = new Set(["home", "study", "kanji", "vocab", "profile"]);

function ThemeToggle() {
  const [dark, setDark] = useState<boolean | null>(null);
  useEffect(() => {
    setDark(document.body.getAttribute("data-theme") === "dark");
  }, []);
  function toggle() {
    const next = document.body.getAttribute("data-theme") === "dark" ? "light" : "dark";
    document.body.setAttribute("data-theme", next);
    try { localStorage.setItem("ym-theme", next); } catch { /* ignore */ }
    setDark(next === "dark");
  }
  return (
    <button
      className="icon-btn"
      onClick={toggle}
      aria-label="Alternar tema claro e escuro"
      aria-pressed={dark ?? undefined}
      title="Alternar tema"
    >
      <Icon name={dark ? "light_mode" : "dark_mode"} size={22} />
    </button>
  );
}

export function AppShell({
  active,
  title,
  back,
  children,
}: {
  active?: string;
  title?: string;
  back?: string;
  children: React.ReactNode;
}) {
  return (
    <div className="ym-app">
      <a href="#ym-main" className="ym-skip">Pular para o conteúdo</a>
      <aside className="ym-drawer">
        <Link to="/" className="ym-drawer-brand">
          <YominekoLogo size={36} />
          <span>Yomineko</span>
        </Link>
        <nav className="ym-drawer-nav">
          {NAV.map((d) => (
            <Link key={d.id} to={d.to} className={`drawer-item${d.id === active ? " active" : ""}`}>
              <Icon name={d.icon} size={24} fill={d.id === active} />
              {d.label}
            </Link>
          ))}
        </nav>
      </aside>

      <div className="ym-main">
        <header className="ym-topbar">
          {back ? (
            <Link to={back} className="icon-btn ym-topbar-back" aria-label="Voltar">
              <Icon name="arrow_back" size={24} />
              <span className="ym-back-label">Voltar</span>
            </Link>
          ) : (
            <Link to="/" className="ym-topbar-brand">
              <YominekoLogo size={28} />
            </Link>
          )}
          <span className="ym-topbar-title">{title}</span>
          <ThemeToggle />
        </header>

        <main className="ym-content" id="ym-main" tabIndex={-1}>{children}</main>

        <nav className="ym-bottomnav">
          {NAV.filter((d) => MOBILE.has(d.id)).map((d) => (
            <Link key={d.id} to={d.to} className={`navdest${d.id === active ? " active" : ""}`}>
              <span className="nav-ic-wrap">
                <Icon name={d.icon} size={24} fill={d.id === active} />
              </span>
              {d.label}
            </Link>
          ))}
        </nav>
      </div>
    </div>
  );
}
