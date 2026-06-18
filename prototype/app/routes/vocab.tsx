import { Link, useLoaderData } from "react-router";
import { AppShell } from "~/ui/AppShell";
import { FilterableList } from "~/ui/FilterableList";
import { allVocab, locArr } from "~/lib/corpus.server";

export function meta() {
  return [{ title: "Yomineko — Vocabulário" }];
}

interface VocabItem { headword: string; kana: string; romaji: string; level: string; gloss: string }

export async function loader() {
  const items: VocabItem[] = allVocab()
    .map((v: any) => ({
      headword: v.headword,
      kana: v.kana,
      romaji: v.romaji ?? "",
      level: v.level,
      gloss: (v.senses || []).flatMap((s: any) => locArr(s.gloss)).slice(0, 2).join("; "),
    }))
    .sort((a, b) => a.kana.localeCompare(b.kana, "ja"));
  return { items };
}

export default function Vocab() {
  const { items } = useLoaderData<typeof loader>();
  return (
    <AppShell active="vocab" title="Vocabulário">
      <div className="ym-page-wide">
        <h1 className="ym-h1">Vocabulário</h1>
        <p className="ym-sub">{items.length} palavras do corpus.</p>

        <FilterableList
          items={items}
          levelOf={(v) => v.level}
          searchOf={(v) => `${v.headword} ${v.kana} ${v.romaji} ${v.gloss}`}
          placeholder="Buscar por palavra, leitura, romaji ou significado…"
          noun="palavras"
        >
          {(filtered) => (
            <div className="ym-cards">
              {filtered.map((v) => (
                <Link key={v.headword} to={`/vocabulario/${encodeURIComponent(v.headword)}`} className="ym-vocab-row">
                  <ruby className="ym-vocab-hw" lang="ja">{v.headword}<rt>{v.kana}</rt></ruby>
                  <div className="ym-vocab-gloss">{v.gloss}</div>
                </Link>
              ))}
            </div>
          )}
        </FilterableList>
      </div>
    </AppShell>
  );
}
