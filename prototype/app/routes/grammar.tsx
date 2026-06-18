import { Link, useLoaderData } from "react-router";
import { AppShell } from "~/ui/AppShell";
import { FilterableList } from "~/ui/FilterableList";
import { allGrammar, loc } from "~/lib/corpus.server";

export function meta() {
  return [{ title: "Yomineko — Gramática" }];
}

interface GrammarItem { key: string; label: string; pattern: string; level: string }

export async function loader() {
  const items: GrammarItem[] = allGrammar()
    .map((g: any) => ({
      key: g.key,
      label: loc(g.label),
      pattern: g.structure_pattern ?? "",
      level: g.level,
    }))
    .sort((a, b) => a.label.localeCompare(b.label, "pt-BR"));
  return { items };
}

export default function Grammar() {
  const { items } = useLoaderData<typeof loader>();
  return (
    <AppShell active="study" title="Gramática">
      <div className="ym-page-wide">
        <h1 className="ym-h1">Gramática</h1>
        <p className="ym-sub">{items.length} pontos gramaticais do corpus.</p>

        <FilterableList
          items={items}
          levelOf={(g) => g.level}
          searchOf={(g) => `${g.label} ${g.pattern} ${g.key}`}
          placeholder="Buscar por ponto gramatical ou padrão…"
          noun="pontos"
        >
          {(filtered) => (
            <div className="ym-grid" style={{ gridTemplateColumns: "repeat(auto-fill, minmax(260px,1fr))" }}>
              {filtered.map((it) => (
                <Link key={it.key} to={`/gramatica/${encodeURIComponent(it.key)}`} className="ym-tile">
                  <div className="ym-tile-title">{it.label}</div>
                  {it.pattern && <div className="ym-grammar-pattern" lang="ja">{it.pattern}</div>}
                </Link>
              ))}
            </div>
          )}
        </FilterableList>
      </div>
    </AppShell>
  );
}
