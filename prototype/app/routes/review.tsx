import { Link, useLoaderData } from "react-router";
import { AppShell } from "~/ui/AppShell";
import { Icon } from "~/ui/Icon";
import { getVocab, allVocab, locArr, sentencesForVocab } from "~/lib/corpus.server";

export function meta() {
  return [{ title: "Yomineko — Revisar" }];
}

// A demonstration of the spaced-repetition review flow, using a real corpus word + example sentence.
export async function loader() {
  const v = getVocab("学生") ?? allVocab().find((x: any) => x.senses?.length) ?? allVocab()[0];
  const ex = sentencesForVocab(v.headword, 1)[0] ?? null;
  return {
    word: {
      headword: v.headword,
      kana: v.kana,
      romaji: v.romaji ?? "",
      gloss: locArr(v.senses?.[0]?.gloss).slice(0, 3).join(", "),
      href: `/vocabulario/${encodeURIComponent(v.headword)}`,
    },
    example: ex,
  };
}

const RATINGS = [
  { l: "De novo", iv: "< 1 min", c: "var(--error)" },
  { l: "Difícil", iv: "~ 3 dias", c: "var(--gold)" },
  { l: "Bom", iv: "~ 7 dias", c: "var(--success)" },
  { l: "Fácil", iv: "~ 14 dias", c: "var(--primary)" },
] as const;

export default function Review() {
  const { word, example } = useLoaderData<typeof loader>();
  return (
    <AppShell active="review" title="Revisar">
      <div className="ym-page">
        <div className="ym-rev-head">
          <div>
            <h1 className="ym-h1" style={{ marginBottom: 2 }}>Revisão de hoje</h1>
            <p className="ym-sub" style={{ margin: 0 }}>Revisão espaçada (FSRS) das suas lições. <span className="ym-pill ym-pill-gold">demonstração</span></p>
          </div>
          <div className="ym-rev-progress"><i style={{ width: "8%" }} /></div>
        </div>

        <div className="ym-rev-card">
          <span className="ym-pill">PALAVRA · 1 de 12</span>
          <div className="ym-rev-front" lang="ja">{word.kana}</div>
          <button type="button" className="btn btn-tonal btn-sm" disabled><Icon name="volume_up" size={18} /> Ouvir</button>

          <details className="ym-rev-reveal">
            <summary>Mostrar resposta</summary>
            <div className="ym-rev-romaji">{word.romaji}</div>
            <div className="ym-rev-meaning">{word.gloss}</div>
            {example && (
              <div className="ym-sent ym-sent-card" style={{ textAlign: "left", marginTop: 16 }}>
                <div className="ym-sent-jp" lang="ja">{example.jp}</div>
                {example.romaji && <div className="ym-sent-romaji">{example.romaji}</div>}
                {example.pt && <div className="ym-sent-pt">{example.pt}</div>}
              </div>
            )}
            <Link to={word.href} className="btn btn-text btn-sm" style={{ marginTop: 12 }}>Ver no dicionário <Icon name="arrow_forward" size={16} /></Link>
          </details>
        </div>

        <div className="ym-rev-ratings">
          {RATINGS.map((r) => (
            <button key={r.l} type="button" className="ym-rev-rate" style={{ background: `color-mix(in srgb, ${r.c} 14%, var(--surface))`, color: r.c }}>
              <span className="ym-rev-rate-l">{r.l}</span>
              <span className="ym-rev-rate-iv">{r.iv}</span>
            </button>
          ))}
        </div>
        <p className="ym-rev-foot">Protótipo: os cartões e o agendamento são uma demonstração do fluxo de revisão.</p>
      </div>
    </AppShell>
  );
}
