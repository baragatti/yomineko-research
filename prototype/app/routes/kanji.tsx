import { Link, useLoaderData } from "react-router";
import { AppShell } from "~/ui/AppShell";
import { FilterableList } from "~/ui/FilterableList";
import { allKanji, locArr, kanjiRomaji, kanaToRomaji } from "~/lib/corpus.server";

export function meta() {
  return [{ title: "Yomineko — Kanji" }];
}

interface KanjiItem { character: string; level: string; strokes: number; romaji: string; meaning: string; search: string }

export async function loader() {
  const items: KanjiItem[] = allKanji()
    .map((k: any) => {
      const meanings = locArr(k.meanings);
      const readings = (k.readings || []) as any[];
      // searchable across the character, every reading (kana + romaji), and the meanings
      const search = [
        k.character,
        ...readings.map((r) => r.reading),
        ...readings.map((r) => kanaToRomaji(r.reading)),
        ...meanings,
      ].join(" ");
      return {
        character: k.character,
        level: k.level,
        strokes: k.strokes ?? 99,
        romaji: kanjiRomaji(k),
        meaning: meanings[0] ?? "",
        search,
      };
    })
    .sort((a, b) => a.strokes - b.strokes || a.character.localeCompare(b.character));
  return { items };
}

export default function Kanji() {
  const { items } = useLoaderData<typeof loader>();
  return (
    <AppShell active="kanji" title="Kanji">
      <div className="ym-page-wide">
        <h1 className="ym-h1">Kanji</h1>
        <p className="ym-sub">{items.length} kanji do corpus, ordenados por número de traços.</p>

        <FilterableList
          items={items}
          levelOf={(k) => k.level}
          searchOf={(k) => k.search}
          placeholder="Buscar por kanji, romaji ou significado…"
          noun="kanji"
        >
          {(filtered) => (
            <div className="ym-kanji-grid">
              {filtered.map((k) => (
                <Link key={k.character} to={`/kanji/${encodeURIComponent(k.character)}`} className="ym-kanji-cell" title={k.meaning}>
                  <span className="ym-kanji-cell-char" lang="ja">{k.character}</span>
                  <span className="ym-kanji-cell-romaji">{k.romaji}</span>
                </Link>
              ))}
            </div>
          )}
        </FilterableList>
      </div>
    </AppShell>
  );
}
