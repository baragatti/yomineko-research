interface BdToken { s: string; r?: string; ro?: string; pos?: string; gloss?: string; role?: string }
interface BdParticle { p: string; ft?: string; fn?: string; ex?: string }
interface SentenceView {
  slug: string;
  jp: string;
  romaji: string;
  pt: string;
  literal: string;
  explanation: string;
  tokens?: BdToken[];
  particles?: BdParticle[];
}

const PUNCT = /^[、。・，．？！「」『』（）\s]+$/;

function Breakdown({ tokens, particles }: { tokens: BdToken[]; particles: BdParticle[] }) {
  const toks = tokens.filter((t) => t.s && !PUNCT.test(t.s));
  if (!toks.length && !particles.length) return null;
  return (
    <>
      {toks.length > 0 && (
        <div className="ym-bd">
          <div className="ym-bd-label">Palavra por palavra</div>
          {toks.map((t, i) => (
            <div key={i} className="ym-bd-tok">
              <span className="ym-bd-jp" lang="ja">{t.s}</span>
              {(t.r || t.ro) && <span className="ym-bd-read" lang="ja">{[t.r, t.ro].filter(Boolean).join(" · ")}</span>}
              {t.gloss && <span className="ym-bd-gloss">{t.gloss}</span>}
              {t.role && <span className="ym-bd-role">{t.role}</span>}
            </div>
          ))}
        </div>
      )}
      {particles.length > 0 && (
        <div className="ym-bd-parts">
          <div className="ym-bd-label">Partículas</div>
          {particles.map((p, i) => (
            <div key={i} className="ym-bd-part">
              <span className="ym-chip ym-chip-grammar" lang="ja">{p.p}</span>
              {p.ft && <span className="ym-tag">{p.ft}</span>}
              <span className="ym-bd-pexpl">{p.ex || p.fn || ""}</span>
            </div>
          ))}
        </div>
      )}
    </>
  );
}

/** Renders example sentences (kanji / vocab / grammar detail pages). Server-rendered, no client JS. */
export function SentenceCards({ items }: { items: SentenceView[] }) {
  if (!items.length) return null;
  return (
    <div className="ym-sent-list">
      {items.map((s) => {
        const hasBreakdown = (s.tokens?.length || 0) + (s.particles?.length || 0) > 0;
        return (
          <div key={s.slug} className="ym-sent ym-sent-card">
            <div className="ym-sent-jp" lang="ja">{s.jp}</div>
            {s.romaji && <div className="ym-sent-romaji">{s.romaji}</div>}
            {s.pt && <div className="ym-sent-pt">{s.pt}</div>}
            {(s.literal || s.explanation || hasBreakdown) && (
              <details className="ym-sent-more">
                <summary>Análise</summary>
                {hasBreakdown && <Breakdown tokens={s.tokens || []} particles={s.particles || []} />}
                {s.literal && <p className="ym-sent-literal"><span>Literal:</span> {s.literal}</p>}
                {s.explanation && <p className="ym-sent-expl">{s.explanation}</p>}
              </details>
            )}
          </div>
        );
      })}
    </div>
  );
}
