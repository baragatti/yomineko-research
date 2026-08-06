import { Link, useLoaderData } from "react-router";
import { AppShell } from "~/ui/AppShell";
import { Icon } from "~/ui/Icon";
import { LEVELS, MINUTES, SECTIONS, bankStats, type Level } from "~/lib/exam.server";

export function meta() {
  return [{ title: "Yomineko — Simulado JLPT" }];
}

export async function loader() {
  // Only aggregate numbers cross the wire here; the bank itself stays on the server.
  return {
    levels: LEVELS.map((lv: Level) => ({
      level: lv,
      minutes: MINUTES[lv],
      questions: SECTIONS.reduce((a, s) => a + s.counts[lv], 0),
      sections: SECTIONS.filter((s) => s.counts[lv] > 0).map((s) => ({
        label: s.label, jp: s.jp, n: s.counts[lv],
      })),
      ...bankStats(lv),
    })),
  };
}

export default function Exam() {
  const { levels } = useLoaderData<typeof loader>();
  return (
    <AppShell active="practice" title="Simulado">
      <div className="ym-page-wide">
        <h1 className="ym-h1">Simulado JLPT</h1>
        <p className="ym-sub">
          Uma prova nova a cada tentativa, sorteada do nosso banco. As questões saem do próprio corpus, então
          tudo que aparece aqui você também encontra nas lições.
        </p>

        <div className="ym-grid" style={{ gridTemplateColumns: "repeat(auto-fill, minmax(300px,1fr))" }}>
          {levels.map((lv) => (
            <article key={lv.level} className="ym-card">
              <header className="ym-card-h">
                <span className="ym-pill ym-pill-gold">{lv.level.toUpperCase()}</span>
                <span className="ym-muted">
                  {lv.questions} questões · {lv.minutes} min
                </span>
              </header>

              <ul className="ym-list ym-list-tight">
                {lv.sections.map((s) => (
                  <li key={s.label}>
                    <span className="ym-jp">{s.jp}</span> {s.label}
                    <span className="ym-muted"> × {s.n}</span>
                  </li>
                ))}
              </ul>

              <p className="ym-muted" style={{ marginTop: ".5rem" }}>
                Banco: {lv.items.toLocaleString("pt-BR")} questões em {lv.types} seções.
              </p>

              <Link className="ym-btn ym-btn-primary" to={`/simulado/${lv.level}`}>
                <Icon name="play_arrow" /> Começar {lv.level.toUpperCase()}
              </Link>
            </article>
          ))}
        </div>

        <p className="ym-muted" style={{ marginTop: "1.25rem" }}>
          A seção de <strong>compreensão auditiva</strong> ainda não entra no simulado: os roteiros já
          existem, mas o áudio está pendente de gravação.
        </p>
      </div>
    </AppShell>
  );
}
