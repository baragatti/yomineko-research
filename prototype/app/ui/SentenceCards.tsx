interface SentenceView {
  slug: string;
  jp: string;
  romaji: string;
  pt: string;
  literal: string;
  explanation: string;
}

/** Renders example sentences (kanji / vocab / grammar detail pages). Server-rendered, no client JS. */
export function SentenceCards({ items }: { items: SentenceView[] }) {
  if (!items.length) return null;
  return (
    <div className="ym-sent-list">
      {items.map((s) => (
        <div key={s.slug} className="ym-sent ym-sent-card">
          <div className="ym-sent-jp" lang="ja">{s.jp}</div>
          {s.romaji && <div className="ym-sent-romaji">{s.romaji}</div>}
          {s.pt && <div className="ym-sent-pt">{s.pt}</div>}
          {(s.literal || s.explanation) && (
            <details className="ym-sent-more">
              <summary>Análise</summary>
              {s.literal && <p className="ym-sent-literal"><span>Literal:</span> {s.literal}</p>}
              {s.explanation && <p className="ym-sent-expl">{s.explanation}</p>}
            </details>
          )}
        </div>
      ))}
    </div>
  );
}
