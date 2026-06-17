import { Link, useLoaderData } from "react-router";
import { AppShell } from "~/ui/AppShell";
import { allVocab, locArr } from "~/lib/corpus.server";

export function meta() {
  return [{ title: "Yomineko — Vocabulário" }];
}

export async function loader() {
  const items = allVocab()
    .map((v: any) => ({
      headword: v.headword,
      kana: v.kana,
      level: v.level,
      gloss: (v.senses || []).flatMap((s: any) => locArr(s.gloss)).slice(0, 2).join("; "),
    }))
    .sort((a, b) => a.kana.localeCompare(b.kana, "ja"));

  const groups = ["n5", "n4"].map((lvl) => ({ level: lvl, items: items.filter((v) => v.level === lvl) }));
  return { groups, total: items.length };
}

export default function Vocab() {
  const { groups, total } = useLoaderData<typeof loader>();
  return (
    <AppShell active="vocab" title="Vocabulário">
      <div className="ym-page-wide">
        <h1 className="ym-h1">Vocabulário</h1>
        <p className="ym-sub">{total} palavras do corpus.</p>

        {groups.map((g) =>
          g.items.length === 0 ? null : (
            <section key={g.level}>
              <div className="ym-section-title">{g.level.toUpperCase()} · {g.items.length}</div>
              <div className="ym-cards">
                {g.items.map((v) => (
                  <Link key={v.headword} to={`/vocabulario/${encodeURIComponent(v.headword)}`} className="ym-vocab-row">
                    <div>
                      <ruby className="ym-vocab-hw">{v.headword}<rt>{v.kana}</rt></ruby>
                    </div>
                    <div className="ym-vocab-gloss">{v.gloss}</div>
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
