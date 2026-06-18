import { Link, useLoaderData } from "react-router";
import { AppShell } from "~/ui/AppShell";
import { allKanji, locArr, kanjiRomaji } from "~/lib/corpus.server";

export function meta() {
  return [{ title: "Yomineko — Kanji" }];
}

export async function loader() {
  const items = allKanji()
    .map((k: any) => ({
      character: k.character,
      level: k.level,
      strokes: k.strokes,
      romaji: kanjiRomaji(k),
      meaning: locArr(k.meanings)[0] ?? "",
    }))
    .sort((a, b) => (a.strokes ?? 99) - (b.strokes ?? 99) || a.character.localeCompare(b.character));

  const groups = ["n5", "n4"].map((lvl) => ({
    level: lvl,
    items: items.filter((k) => k.level === lvl),
  }));
  const other = items.filter((k) => k.level !== "n5" && k.level !== "n4");
  if (other.length) groups.push({ level: "outros", items: other });

  return { groups, total: items.length };
}

export default function Kanji() {
  const { groups, total } = useLoaderData<typeof loader>();
  return (
    <AppShell active="kanji" title="Kanji">
      <div className="ym-page-wide">
        <h1 className="ym-h1">Kanji</h1>
        <p className="ym-sub">{total} kanji do corpus, ordenados por número de traços.</p>

        {groups.map((g) =>
          g.items.length === 0 ? null : (
            <section key={g.level}>
              <h2 className="ym-section-title">
                {g.level === "outros" ? "Outros" : g.level.toUpperCase()} · {g.items.length}
              </h2>
              <div className="ym-kanji-grid">
                {g.items.map((k) => (
                  <Link key={k.character} to={`/kanji/${encodeURIComponent(k.character)}`} className="ym-kanji-cell" title={k.meaning}>
                    <span className="ym-kanji-cell-char" lang="ja">{k.character}</span>
                    <span className="ym-kanji-cell-romaji">{k.romaji}</span>
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
