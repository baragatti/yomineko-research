import { Link, useLoaderData } from "react-router";
import { AppShell } from "~/ui/AppShell";
import { Icon } from "~/ui/Icon";
import {
  LEVELS, SCORING_MODEL, GAP_NOTE, bankStats, fullMinutesFor, minutesFor, partsFor, sectionsFor,
  type Level,
} from "~/lib/exam.server";
import { lastLessonOfLevel } from "~/lib/examStudy.server";

export function meta() {
  return [{ title: "Yomineko — Simulado JLPT" }];
}

export async function loader() {
  // Only aggregate numbers cross the wire here; the bank itself stays on the server.
  //
  // Everything below is built from `sectionsFor` / `partsFor` — the RUNNABLE shape of the paper —
  // rather than the declared tables. Reading the declared ones would advertise a 90-minute N5 with
  // 聴解 in it and then hand the learner a 60-minute paper without one.
  return {
    gapNote: GAP_NOTE,
    levels: LEVELS.map((lv: Level) => {
      const secs = sectionsFor(lv);
      const model = SCORING_MODEL[lv];
      return {
        level: lv,
        minutes: minutesFor(lv),
        fullMinutes: fullMinutesFor(lv),
        questions: secs.reduce((a, s) => a + s.counts[lv], 0),
        parts: partsFor(lv).map((p) => ({
          jp: p.jp,
          label: p.label,
          minutes: p.minutes[lv],
          questions: p.types.reduce(
            (a, t) => a + (secs.find((s) => s.type === t)?.counts[lv] ?? 0), 0),
          sections: p.types
            .map((t) => secs.find((s) => s.type === t))
            .filter((s): s is NonNullable<typeof s> => !!s && s.counts[lv] > 0)
            .map((s) => ({ label: s.label, jp: s.jp, n: s.counts[lv] })),
        })).filter((p) => p.questions > 0),
        passMark: model.passMark,
        // The 得点区分 the paper cannot test today. Named, so the page says which one is missing.
        missing: model.sections
          .filter((s) => !s.types.some((t) => secs.some((x) => x.type === t)))
          .map((s) => ({ label: s.label, jp: s.jp, max: s.max })),
        study: lastLessonOfLevel(lv),
        ...bankStats(lv),
      };
    }),
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

        <div className="ym-grid" style={{ gridTemplateColumns: "repeat(auto-fit, minmax(250px,1fr))",
                                          margin: "4px 0 26px" }}>
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
            <div key={x.t} className="ym-quick ym-tile-static">
              <span className="ym-quick-ic"><Icon name={x.ic} size={22} /></span>
              <div>
                <div className="ym-quick-t">{x.t}</div>
                <div className="ym-quick-d">{x.d}</div>
              </div>
            </div>
          ))}
        </div>

        <h2 className="ym-section-title">Escolha o nível</h2>
        <div className="ym-grid" style={{ gridTemplateColumns: "repeat(auto-fit, minmax(320px,1fr))" }}>
          {levels.map((lv) => (
            <article key={lv.level} className="ym-tile ym-tile-static ym-tile-col">
              <header style={{ display: "flex", alignItems: "center", gap: 12 }}>
                <span className="ym-practice-ic" style={{ fontFamily: "var(--font-display)",
                                                          fontWeight: 700, fontSize: 18 }}>
                  {lv.level.toUpperCase()}
                </span>
                <div>
                  <div className="ym-tile-title">{lv.questions} questões</div>
                  <div className="ym-tile-sub">
                    {lv.minutes} min de prova, em {lv.parts.length} partes
                  </div>
                </div>
              </header>

              {lv.parts.map((p, i) => (
                <div key={p.jp} className="ym-card-plain">
                  <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
                    <span className="ym-seg-n">{i + 1}</span>
                    <span className="ym-jp" style={{ flex: 1, minWidth: 0, fontWeight: 600 }}>{p.jp}</span>
                    <span className="ym-pill ym-pill-primary">{p.minutes} min</span>
                  </div>
                  <div className="ym-chip-row">
                    {p.sections.map((s) => (
                      <span key={s.label} className="ym-chip">{s.label} ×{s.n}</span>
                    ))}
                  </div>
                </div>
              ))}

              <p className="ym-tile-sub">
                Nota de corte oficial: <strong>{lv.passMark} de 180</strong>, e cada seção tem um
                mínimo próprio.{" "}
                {lv.missing.length > 0 && (
                  <>
                    Como {lv.missing.map((m) => m.label.toLowerCase()).join(" e ")} ainda não entra na
                    prova, o resultado aqui sai como <strong>incompleto</strong> — sem aprovado nem
                    reprovado.
                  </>
                )}
              </p>

              <footer style={{ display: "flex", alignItems: "center", justifyContent: "space-between",
                               gap: 10, marginTop: "auto", flexWrap: "wrap" }}>
                <span className="ym-tile-sub">
                  banco: {lv.items.toLocaleString("pt-BR")} questões
                </span>
                <span style={{ display: "flex", gap: 8 }}>
                  {lv.study && (
                    <Link className="ym-btn" to={`/simulado/estudo/${lv.study.id}`}>
                      <Icon name="school" /> Estudar
                    </Link>
                  )}
                  <Link className="ym-btn ym-btn-primary" to={`/simulado/${lv.level}`}>
                    <Icon name="play_arrow" /> Começar
                  </Link>
                </span>
              </footer>
            </article>
          ))}
        </div>

        <div className="ym-cards" style={{ marginTop: 22, gap: 8 }}>
          <p className="ym-tile-sub" style={{ display: "flex", gap: 8 }}>
            <Icon name="info" size={16} /> {gapNote}
          </p>
          <p className="ym-tile-sub" style={{ display: "flex", gap: 8 }}>
            <Icon name="headphones" size={16} /> A seção de <strong>compreensão auditiva</strong> ainda
            não entra no simulado: os roteiros já existem, mas o áudio está pendente de gravação. Por
            isso a prova aqui é mais curta que a do dia do exame.
          </p>
        </div>
      </div>
    </AppShell>
  );
}
