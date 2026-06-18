import { useMemo, useState, type ReactNode } from "react";
import { Icon } from "./Icon";

const LEVEL_LABEL: Record<string, string> = { "pre-n5": "pré-N5", n5: "N5", n4: "N4", outros: "Outros" };
const LEVEL_ORDER = ["pre-n5", "n5", "n4", "outros"];

/**
 * Client-side filter for the index/list pages (kanji, vocab, grammar, course). Renders a search box + a
 * level segmented control, and calls `children` with the filtered items. SSR renders the full list (initial
 * state), then this hydrates to enable filtering. Ships no extra data — it filters items already on the page.
 */
export function FilterableList<T>({
  items,
  levelOf,
  searchOf,
  placeholder,
  noun,
  children,
}: {
  items: T[];
  levelOf: (x: T) => string;
  searchOf: (x: T) => string;
  placeholder: string;
  noun: string;
  children: (filtered: T[]) => ReactNode;
}) {
  const [query, setQuery] = useState("");
  const [level, setLevel] = useState("all");

  const levels = useMemo(() => {
    const present = new Set(items.map(levelOf));
    return LEVEL_ORDER.filter((lv) => present.has(lv)).concat([...present].filter((lv) => !LEVEL_ORDER.includes(lv)));
  }, [items, levelOf]);

  const q = query.trim().toLowerCase();
  const filtered = useMemo(
    () => items.filter((x) => (level === "all" || levelOf(x) === level) && (!q || searchOf(x).toLowerCase().includes(q))),
    [items, level, q, levelOf, searchOf]
  );
  const countFor = (lv: string) => (lv === "all" ? items.length : items.filter((x) => levelOf(x) === lv).length);

  return (
    <>
      <div className="ym-filterbar">
        <label className="ym-search">
          <Icon name="search" size={20} />
          <input
            type="search"
            value={query}
            placeholder={placeholder}
            onChange={(e) => setQuery(e.target.value)}
            aria-label="Buscar"
          />
          {query && (
            <button type="button" className="ym-search-clear" aria-label="Limpar busca" onClick={() => setQuery("")}>
              <Icon name="close" size={18} />
            </button>
          )}
        </label>
        {levels.length > 1 && (
          <div className="ym-segmented" role="tablist" aria-label="Filtrar por nível">
            <button type="button" role="tab" aria-selected={level === "all"} className={`ym-seg${level === "all" ? " is-active" : ""}`} onClick={() => setLevel("all")}>
              Todos <span className="ym-seg-n">{countFor("all")}</span>
            </button>
            {levels.map((lv) => (
              <button key={lv} type="button" role="tab" aria-selected={level === lv} className={`ym-seg${level === lv ? " is-active" : ""}`} onClick={() => setLevel(lv)}>
                {LEVEL_LABEL[lv] ?? lv.toUpperCase()} <span className="ym-seg-n">{countFor(lv)}</span>
              </button>
            ))}
          </div>
        )}
      </div>
      <div className="ym-filter-count">{filtered.length} {noun}</div>
      {filtered.length ? children(filtered) : <div className="ym-empty-mini"><Icon name="search_off" size={20} /> Nada encontrado.</div>}
    </>
  );
}
