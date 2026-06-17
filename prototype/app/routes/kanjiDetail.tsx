import { Link, useLoaderData } from "react-router";
import { data } from "react-router";
import { AppShell } from "~/ui/AppShell";
import { Icon } from "~/ui/Icon";
import { getKanji, getVocab, locArr } from "~/lib/corpus.server";

export function meta({ data: d }: { data: any }) {
  return [{ title: `Yomineko — ${d?.character ?? "Kanji"}` }];
}

export async function loader({ params }: { params: { char: string } }) {
  const k = getKanji(params.char);
  if (!k) throw data("Kanji não encontrado", { status: 404 });

  const readings = (k.readings || []) as any[];
  const grp = (type: string) =>
    readings.filter((r) => r.type === type).map((r) => ({ reading: r.reading, common: !!r.common, level: r.introduced_at_level }));

  return {
    character: k.character,
    level: k.level,
    strokes: k.strokes,
    components: k.components || [],
    meanings: locArr(k.meanings),
    kun: grp("kun"),
    on: grp("on"),
    examples: (k.example_words || []).slice(0, 12).map((w: any) => ({
      headword: w.headword,
      kana: w.kana,
      gloss: locArr(w.gloss)[0] ?? "",
      hasEntry: !!getVocab(w.headword),
    })),
  };
}

function ReadingRow({ label, items }: { label: string; items: { reading: string; common: boolean }[] }) {
  if (!items.length) return null;
  return (
    <div className="ym-reading-row">
      <span className="ym-reading-label">{label}</span>
      <div className="ym-reading-list">
        {items.map((r, i) => (
          <span key={i} className={`ym-pill${r.common ? " ym-pill-primary" : ""}`}>{r.reading}</span>
        ))}
      </div>
    </div>
  );
}

export default function KanjiDetail() {
  const k = useLoaderData<typeof loader>();
  return (
    <AppShell active="kanji" title={k.character} back="/kanji">
      <div className="ym-page">
        <div className="ym-breadcrumb">
          <Link to="/kanji">Kanji</Link> <Icon name="chevron_right" size={14} /> <span>{k.level.toUpperCase()}</span>
        </div>

        <div className="ym-kanji-hero">
          <div className="ym-kanji-hero-char">{k.character}</div>
          <div className="ym-kanji-hero-meta">
            <div className="ym-kanji-hero-meaning">{k.meanings.join(" · ")}</div>
            <div style={{ display: "flex", gap: 8, marginTop: 8, flexWrap: "wrap" }}>
              <span className="ym-pill">{k.strokes} traços</span>
              <span className="ym-pill">{k.level.toUpperCase()}</span>
              {k.components.length > 1 && <span className="ym-pill">partes: {k.components.join(" ")}</span>}
            </div>
          </div>
        </div>

        <div className="ym-section-title">Leituras</div>
        <div className="ym-card-plain">
          <ReadingRow label="kun" items={k.kun} />
          <ReadingRow label="on" items={k.on} />
        </div>

        {k.examples.length > 0 && (
          <>
            <div className="ym-section-title">Palavras de exemplo</div>
            <div className="ym-cards">
              {k.examples.map((w, i) => {
                const inner = (
                  <>
                    <div>
                      <ruby className="ym-vocab-hw">{w.headword}<rt>{w.kana}</rt></ruby>
                    </div>
                    <div className="ym-vocab-gloss">{w.gloss}</div>
                  </>
                );
                return w.hasEntry ? (
                  <Link key={i} to={`/vocabulario/${encodeURIComponent(w.headword)}`} className="ym-vocab-row">{inner}</Link>
                ) : (
                  <div key={i} className="ym-vocab-row">{inner}</div>
                );
              })}
            </div>
          </>
        )}
      </div>
    </AppShell>
  );
}
