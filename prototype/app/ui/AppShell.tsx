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
const MOBILE = new Set(["home", "study", "review", "practice", "kanji"]);

function ThemeToggle() {
  function toggle() {
    const el = document.querySelector(".ym") as HTMLElement | null;
    if (!el) return;
    const next = el.getAttribute("data-theme") === "dark" ? "light" : "dark";
    el.setAttribute("data-theme", next);
    try {
      localStorage.setItem("ym-theme", next);
    } catch {
      /* ignore */
    }
  }
  return (
    <button className="icon-btn" onClick={toggle} aria-label="Alternar tema" title="Alternar tema">
      <Icon name="dark_mode" size={22} />
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
    <div className="ym ym-app" data-theme="light">
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
            <Link to={back} className="icon-btn" aria-label="Voltar">
              <Icon name="arrow_back" size={24} />
            </Link>
          ) : (
            <Link to="/" className="ym-topbar-brand">
              <YominekoLogo size={28} />
            </Link>
          )}
          <span className="ym-topbar-title">{title}</span>
          <ThemeToggle />
        </header>

        <main className="ym-content">{children}</main>

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
