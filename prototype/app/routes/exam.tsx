import { Link, useLoaderData } from "react-router";
import { AppShell } from "~/ui/AppShell";
import { Icon } from "~/ui/Icon";
import { LEVELS, MINUTES, PARTS, SECTIONS, GAP_NOTE, bankStats, type Level } from "~/lib/exam.server";

export function meta() {
  return [{ title: "Yomineko — Simulado JLPT" }];
}

export async function loader() {
  // Only aggregate numbers cross the wire here; the bank itself stays on the server.
  return {
    gapNote: GAP_NOTE,
    levels: LEVELS.map((lv: Level) => ({
      level: lv,
      minutes: MINUTES[lv],
      questions: SECTIONS.reduce((a, s) => a + s.counts[lv], 0),
      parts: PARTS.map((p) => ({
        jp: p.jp,
        label: p.label,
        minutes: p.minutes[lv],
        questions: p.types.reduce(
          (a, t) => a + (SECTIONS.find((s) => s.type === t)?.counts[lv] ?? 0), 0),
        sections: p.types
          .map((t) => SECTIONS.find((s) => s.type === t))
          .filter((s): s is NonNullable<typeof s> => !!s && s.counts[lv] > 0)
          .map((s) => ({ label: s.label, jp: s.jp, n: s.counts[lv] })),
      })).filter((p) => p.questions > 0),
      ...bankStats(lv),
    })),
  };
}

export default function Exam() {
  const { levels, gapNote } = useLoaderData<typeof loader>();
  const totalBank = levels.reduce((a, l) => a + l.items, 0);

  return (
    <AppShell active="exam" title="Simulado">
      <div className="ym-page-wide">
        <h1 className="ym-h1">Simulado JLPT</h1>
        <p className="ym-sub">
          Uma prova nova a cada tentativa, montada na hora a partir de {totalBank.toLocaleString("pt-BR")}{" "}
          questões. Tudo o que aparece aqui sai do próprio corpus, então você também encontra nas lições.
        </p>

        <div className="ym-sim-how">
          {[
            { ic: "timer", t: "Cronometrado por parte",
              d: "Cada parte tem o tempo real do exame. O relógio fica na tela o tempo todo." },
            { ic: "lock_clock", t: "Sem voltar atrás",
              d: "Quando o tempo acaba, a parte é entregue como está e não abre de novo." },
            { ic: "free_breakfast", t: "Com intervalo",
              d: "Entre as partes há o intervalo programado do exame, que você pode pular." },
            { ic: "shuffle", t: "Nunca a mesma prova",
              d: "As questões e a ordem das alternativas são sorteadas a cada tentativa." },
          ].map((x) => (
            <div key={x.t} className="ym-sim-how-item">
              <span className="ym-sim-how-ic"><Icon name={x.ic} size={22} /></span>
              <div>
                <div className="ym-sim-how-t">{x.t}</div>
                <div className="ym-sim-how-d">{x.d}</div>
              </div>
            </div>
          ))}
        </div>

        <h2 className="ym-section-title">Escolha o nível</h2>
        <div className="ym-sim-grid">
          {levels.map((lv) => (
            <article key={lv.level} className="ym-sim-card">
              <header className="ym-sim-h">
                <span className="ym-sim-lv">{lv.level.toUpperCase()}</span>
                <div className="ym-sim-meta">
                  <strong>{lv.questions} questões</strong>
                  <span className="ym-muted">{lv.minutes} min de prova, em {lv.parts.length} partes</span>
                </div>
              </header>

              {lv.parts.map((p, i) => (
                <div key={p.jp} className="ym-sim-part">
                  <div className="ym-sim-part-h">
                    <span className="ym-sim-part-n">{i + 1}</span>
                    <span className="ym-jp ym-sim-part-jp">{p.jp}</span>
                    <span className="ym-sim-part-time">{p.minutes} min</span>
                  </div>
                  <div className="ym-sim-part-secs">
                    {p.sections.map((s) => (
                      <span key={s.label} className="ym-sim-sec">
                        {s.label} <b>×{s.n}</b>
                      </span>
                    ))}
                  </div>
                </div>
              ))}

              <footer className="ym-sim-f">
                <span className="ym-muted">
                  banco: {lv.items.toLocaleString("pt-BR")} questões
                </span>
                <Link className="ym-btn ym-btn-primary" to={`/simulado/${lv.level}`}>
                  <Icon name="play_arrow" /> Começar
                </Link>
              </footer>
            </article>
          ))}
        </div>

        <div className="ym-sim-notes">
          <p><Icon name="info" size={16} /> {gapNote}</p>
          <p>
            <Icon name="headphones" size={16} /> A seção de <strong>compreensão auditiva</strong> ainda
            não entra no simulado: os roteiros já existem, mas o áudio está pendente de gravação. Por
            isso a prova aqui é mais curta que a do dia do exame.
          </p>
        </div>
      </div>
    </AppShell>
  );
}
