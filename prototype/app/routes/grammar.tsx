import { Link, useLoaderData } from "react-router";
import { AppShell } from "~/ui/AppShell";
import { allGrammar, loc } from "~/lib/corpus.server";

export function meta() {
  return [{ title: "Yomineko — Gramática" }];
}

export async function loader() {
  const items = allGrammar()
    .map((g: any) => ({
      key: g.key,
      label: loc(g.label),
      pattern: g.structure_pattern ?? "",
      level: g.level,
    }))
    .sort((a, b) => a.label.localeCompare(b.label, "pt-BR"));

  const groups = ["n5", "n4"].map((lvl) => ({ level: lvl, items: items.filter((g) => g.level === lvl) }));
  const other = items.filter((g) => g.level !== "n5" && g.level !== "n4");
  if (other.length) groups.push({ level: "outros", items: other });

  return { groups, total: items.length };
}

export default function Grammar() {
  const { groups, total } = useLoaderData<typeof loader>();
  return (
    <AppShell active="study" title="Gramática">
      <div className="ym-page-wide">
        <h1 className="ym-h1">Gramática</h1>
        <p className="ym-sub">{total} pontos gramaticais do corpus.</p>

        {groups.map((g) =>
          g.items.length === 0 ? null : (
            <section key={g.level}>
              <div className="ym-section-title">{g.level === "outros" ? "Outros" : g.level.toUpperCase()} · {g.items.length}</div>
              <div className="ym-cards">
                {g.items.map((it) => (
                  <Link key={it.key} to={`/gramatica/${encodeURIComponent(it.key)}`} className="ym-tile">
                    <div className="ym-tile-title">{it.label}</div>
                    {it.pattern && <div className="ym-grammar-pattern">{it.pattern}</div>}
                  </Link>
                ))}
              </div>
            </section>
          )
        )}
      </div>
    </AppShell>
  );
}
