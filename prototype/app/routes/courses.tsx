import { Link, useLoaderData } from "react-router";
import { AppShell } from "~/ui/AppShell";
import { Icon } from "~/ui/Icon";
import { courseTree } from "~/lib/corpus.server";
import { stages, pathTotals } from "~/lib/speak.server";

export function meta() {
  return [{ title: "Yomineko — Cursos" }];
}

/**
 * The two paths through the same corpus, side by side.
 *
 * They are not alternatives in the "pick a difficulty" sense — they are two different ORDERS over the
 * same material, and which one fits depends on why the learner is here. The JLPT path is ordered by the
 * exam syllabus and is what you want if you are sitting a test. Fala Primeiro is ordered by what you
 * need first in a real day (arriving, eating, getting around), so a learner who stops after four stages
 * has still gained something usable. Saying that out loud is the whole job of this page: a chooser that
 * does not explain the choice is just a menu.
 */
export async function loader() {
  const courses = courseTree();
  const topics = courses.reduce((a: number, c: any) => a + c.topics.length, 0);
  const lessons = courses.reduce(
    (a: number, c: any) => a + c.topics.reduce((b: number, t: any) => b + (t.lessonCount ?? t.lessons.length), 0),
    0,
  );
  const st = stages();
  return {
    jlpt: {
      levels: courses.map((c: any) => c.level.toUpperCase()),
      topics,
      lessons,
    },
    speak: {
      stages: st.length,
      ...pathTotals(),
      first: st.slice(0, 4).map((s: any) => s.title),
    },
  };
}

interface PathCardProps {
  to: string;
  eyebrow: string;
  icon: string;
  title: string;
  pitch: string;
  forWhom: string;
  stats: { n: string; of: string }[];
  detail: React.ReactNode;
  cta: string;
}

/** Built from .ym-tile + .ym-stat + .ym-practice-ic, the components the rest of the app already uses. */
function PathCard(p: PathCardProps) {
  return (
    <article className="ym-tile ym-tile-static ym-tile-col">
      <header style={{ display: "flex", alignItems: "center", gap: 12 }}>
        <span className="ym-practice-ic"><Icon name={p.icon} size={24} /></span>
        <div>
          <div className="ym-kicker">{p.eyebrow}</div>
          <h2 className="ym-tile-title" style={{ fontSize: 20 }}>{p.title}</h2>
        </div>
      </header>

      <p className="ym-sub" style={{ margin: 0 }}>{p.pitch}</p>

      <div className="ym-stats-row">
        {p.stats.map((s) => (
          <div key={s.of} className="ym-stat">
            <div className="ym-stat-n">{s.n}</div>
            <div className="ym-stat-label">{s.of}</div>
          </div>
        ))}
      </div>

      <div className="ym-tile-sub">{p.detail}</div>

      <p className="ym-tile-sub" style={{ display: "flex", alignItems: "center", gap: 6, margin: 0 }}>
        <Icon name="person" size={16} /> {p.forWhom}
      </p>

      <Link className="ym-btn ym-btn-primary ym-tile-cta" to={p.to}>
        {p.cta} <Icon name="arrow_forward" size={18} />
      </Link>
    </article>
  );
}

export default function Courses() {
  const { jlpt, speak } = useLoaderData<typeof loader>();
  const top = jlpt.levels.length ? jlpt.levels[jlpt.levels.length - 1] : "N3";

  return (
    <AppShell active="study" title="Cursos">
      <div className="ym-page-wide">
        <h1 className="ym-h1">Cursos</h1>
        <p className="ym-sub">
          Dois caminhos pelo mesmo conteúdo. A diferença não é o nível, é a ORDEM: um segue o programa
          do exame, o outro segue o que você precisa primeiro na vida real. Dá para trocar de caminho
          quando quiser — o vocabulário, os kanji e as frases são os mesmos.
        </p>

        <div className="ym-grid" style={{ gridTemplateColumns: "repeat(auto-fit, minmax(340px,1fr))" }}>
          <PathCard
            to="/cursos/jlpt"
            icon="auto_stories"
            eyebrow="CAMINHO 1 · POR NÍVEL"
            title="Curso JLPT"
            pitch={`Do zero ao ${top}, na ordem do exame. Cada tópico fecha um bloco de gramática, ` +
                   `vocabulário e kanji, e as lições só usam o que você já viu antes.`}
            forWhom="Para quem vai prestar o exame, ou quer a base completa e na ordem."
            stats={[
              { n: String(jlpt.topics), of: "tópicos" },
              { n: String(jlpt.lessons), of: "lições" },
              { n: jlpt.levels.join(" · "), of: "níveis" },
            ]}
            detail={
              <ul className="ym-list ym-list-tight">
                <li>Sequência travada: nada aparece antes de ser ensinado.</li>
                <li>Termina alinhado com o simulado do mesmo nível.</li>
              </ul>
            }
            cta="Ver os tópicos"
          />

          <PathCard
            to="/cursos/falar"
            icon="record_voice_over"
            eyebrow="CAMINHO 2 · POR SITUAÇÃO"
            title="Fala Primeiro"
            pitch={"Do zero até conversar, na ordem em que você precisa das coisas. Cada etapa é um " +
                   "ponto de parada útil por si só."}
            forWhom="Para quem vai viajar, ou quer falar alguma coisa já nas primeiras semanas."
            stats={[
              { n: String(speak.stages), of: "etapas" },
              { n: String(speak.units), of: "unidades" },
              { n: String(speak.phrases), of: "frases reais" },
            ]}
            detail={
              <>
                <p className="ym-muted" style={{ margin: "0 0 6px" }}>Começa por:</p>
                <div className="ym-chip-row">
                  {speak.first.map((t: string) => <span key={t} className="ym-chip">{t}</span>)}
                </div>
              </>
            }
            cta="Ver as etapas"
          />
        </div>

        <p className="ym-muted" style={{ marginTop: "1.5rem" }}>
          As frases dos dois caminhos saem do mesmo banco, de falantes reais. O que muda é a ordem em
          que elas chegam até você.
        </p>
      </div>
    </AppShell>
  );
}
