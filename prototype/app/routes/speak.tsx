import { Link, useLoaderData } from "react-router";
import { AppShell } from "~/ui/AppShell";
import { Icon } from "~/ui/Icon";
import { stages, pathTotals, pathShortfall } from "~/lib/speak.server";

export function meta() {
  return [{ title: "Yomineko — Fala Primeiro" }];
}

export async function loader() {
  return { stages: stages(), totals: pathTotals(), shortfall: pathShortfall() };
}

/**
 * The stage list, built from the same tile the JLPT course uses.
 *
 * It deliberately mirrors `/cursos/jlpt` rather than inventing its own layout: these are two paths
 * through one product, and a learner switching between them should recognise the furniture. The only
 * structural difference is that a stage is numbered by ORDER OF USEFULNESS rather than by level, which
 * the eyebrow says out loud.
 */
export default function Speak() {
  const { stages: st, totals, shortfall } = useLoaderData<typeof loader>();
  const short = new Set(shortfall.map((s) => s.stage));

  return (
    <AppShell active="study" title="Fala Primeiro" back="/cursos">
      <div className="ym-page-wide">
        <div className="ym-breadcrumb">
          <Link to="/cursos">Cursos</Link> <Icon name="chevron_right" size={14} /> <span>Fala Primeiro</span>
        </div>

        <h1 className="ym-h1">Fala Primeiro</h1>
        <p className="ym-sub">
          Do zero até conversar, na ordem em que você precisa das coisas — não na ordem do JLPT. Cada
          etapa é um ponto de parada útil: se você parar na etapa 4, já consegue chegar, comer, comprar
          e se locomover.
        </p>
        <p className="ym-muted" style={{ marginTop: "-12px", marginBottom: "20px" }}>
          {totals.units} unidades · {totals.phrases} frases, todas reais ·{" "}
          {totals.vocab_introduced} palavras, das mais comuns para as menos comuns.
        </p>

        <h2 className="ym-section-title">Etapas, na ordem de utilidade</h2>
        <div className="ym-grid" style={{ gridTemplateColumns: "repeat(auto-fill, minmax(280px,1fr))" }}>
          {st.map((s) => (
            <Link key={s.slug} to={`/falar/${s.key}/1`} className="ym-tile">
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", gap: 8 }}>
                <div style={{ minWidth: 0 }}>
                  <div className="ym-tile-sub" style={{ fontWeight: 700, letterSpacing: ".05em" }}>
                    ETAPA {String(s.order).padStart(2, "0")}
                  </div>
                  <div className="ym-tile-title">{s.title}</div>
                </div>
                <Icon name="chevron_right" size={20} color="var(--on-surface-variant)" />
              </div>
              <div style={{ display: "flex", gap: 6, marginTop: 12, flexWrap: "wrap" }}>
                <span className="ym-pill">{s.units} unidades</span>
                <span className="ym-pill">{s.phrases} frases</span>
                {s.words ? <span className="ym-pill">{s.words} palavras</span> : null}
                {s.band ? <span className="ym-pill">≈{s.band}</span> : null}
              </div>
              {short.has(s.key) && (
                <div className="ym-tile-sub" style={{ marginTop: 8 }}>
                  <Icon name="info" size={14} /> etapa curta — o banco ainda não tem frases reais
                  suficientes para este tema.
                </div>
              )}
            </Link>
          ))}
        </div>

        <p className="ym-muted" style={{ marginTop: "1.5rem" }}>
          As frases são de falantes reais (banco Tatoeba), não geradas. O áudio para praticar em voz
          alta ainda está pendente de gravação.
        </p>
      </div>
    </AppShell>
  );
}
