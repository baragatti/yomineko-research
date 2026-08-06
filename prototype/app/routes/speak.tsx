import { Link, useLoaderData } from "react-router";
import { AppShell } from "~/ui/AppShell";
import { Icon } from "~/ui/Icon";
import { stages, pathTotals, pathShortfall } from "~/lib/speak.server";

export function meta() {
  return [{ title: "Yomineko — Trilha Fala Primeiro" }];
}

export async function loader() {
  return { stages: stages(), totals: pathTotals(), shortfall: pathShortfall() };
}

export default function Speak() {
  const { stages: st, totals, shortfall } = useLoaderData<typeof loader>();
  const short = new Set(shortfall.map((s) => s.stage));

  return (
    <AppShell active="speak" title="Fala Primeiro">
      <div className="ym-page-wide">
        <h1 className="ym-h1">Trilha Fala Primeiro</h1>
        <p className="ym-sub">
          Do zero até conversar, na ordem em que você precisa das coisas — não na ordem do JLPT.
          Cada etapa é um ponto de parada útil: se você parar na etapa 4, já consegue chegar, comer,
          comprar e se locomover.
        </p>
        <p className="ym-muted">
          {totals.units} unidades · {totals.phrases} frases (todas reais, tiradas do banco) ·{" "}
          {totals.vocab_introduced} palavras, das mais comuns para as menos comuns.
        </p>

        <ol className="ym-grid" style={{ gridTemplateColumns: "repeat(auto-fill, minmax(290px,1fr))" }}>
          {st.map((s) => (
            <li key={s.slug} className="ym-card">
              <header className="ym-card-h">
                <span className="ym-pill">{s.order}</span>
                <strong>{s.title}</strong>
              </header>
              <p className="ym-muted">
                {s.units} unidades · {s.phrases} frases · {s.words} palavras novas · ≈{s.band}
              </p>
              {short.has(s.key) && (
                <p className="ym-muted">
                  <Icon name="info" /> etapa curta — o banco ainda não tem frases reais suficientes
                  para este tema.
                </p>
              )}
              <Link className="ym-btn ym-btn-primary" to={`/falar/${s.key}/1`}>
                <Icon name="record_voice_over" /> Começar
              </Link>
            </li>
          ))}
        </ol>

        <p className="ym-muted" style={{ marginTop: "1.25rem" }}>
          As frases são de falantes reais (banco Tatoeba), não geradas. O áudio para praticar em voz
          alta ainda está pendente de gravação.
        </p>
      </div>
    </AppShell>
  );
}
