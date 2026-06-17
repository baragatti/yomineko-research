import { Link, useLoaderData } from "react-router";
import { AppShell } from "~/ui/AppShell";
import { Icon } from "~/ui/Icon";
import { courseTree, lessonsOfLevel } from "~/lib/corpus.server";

export function meta() {
  return [{ title: "Yomineko — Início" }];
}

export async function loader() {
  const tree = courseTree();
  const active = tree.find((c) => c.level === "n5") ?? tree[0];
  const firstLesson = lessonsOfLevel(active?.level)[0] ?? null;
  return {
    courses: tree.map((c) => ({
      id: c.id,
      level: c.level,
      title: c.title,
      topicCount: c.topicCount,
      lessonCount: c.lessonCount,
    })),
    active: active ? { level: active.level, title: active.title, firstLesson } : null,
    totals: {
      lessons: tree.reduce((n, c) => n + c.lessonCount, 0),
      topics: tree.reduce((n, c) => n + c.topicCount, 0),
    },
  };
}

export default function Home() {
  const { courses, active, totals } = useLoaderData<typeof loader>();
  return (
    <AppShell active="home" title="Início">
      <div className="ym-page">
        <h1 className="ym-h1">こんにちは 👋</h1>
        <p className="ym-sub">Seu protótipo Yomineko com o conteúdo real do corpus de pesquisa.</p>

        {active && (
          <div className="ym-tile" style={{ background: "var(--primary-container)", borderColor: "transparent" }}>
            <div className="ym-pill ym-pill-primary">CURSO ATIVO</div>
            <div className="ym-tile-title" style={{ marginTop: 6 }}>{active.title}</div>
            <div style={{ display: "flex", gap: 10, marginTop: 14, flexWrap: "wrap" }}>
              {active.firstLesson && (
                <Link to={`/licao/${encodeURIComponent(active.firstLesson)}`} className="btn btn-filled">
                  Começar a primeira lição <Icon name="arrow_forward" size={18} />
                </Link>
              )}
              <Link to="/curso" className="btn btn-tonal">Ver o curso</Link>
            </div>
          </div>
        )}

        <div className="ym-section-title">Estatísticas do corpus</div>
        <div className="ym-grid" style={{ gridTemplateColumns: "repeat(auto-fit, minmax(140px,1fr))" }}>
          <Stat icon="auto_stories" n={totals.lessons} label="lições" />
          <Stat icon="category" n={totals.topics} label="tópicos" />
          <Stat icon="school" n={courses.length} label="módulos" />
        </div>

        <div className="ym-section-title">Módulos</div>
        <div className="ym-cards">
          {courses.map((c) => (
            <Link key={c.id} to="/curso" className="ym-tile">
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", gap: 8 }}>
                <div>
                  <div className="ym-tile-title">{c.title}</div>
                  <div className="ym-tile-sub">{c.topicCount} tópicos · {c.lessonCount} lições</div>
                </div>
                <Icon name="chevron_right" size={22} color="var(--on-surface-variant)" />
              </div>
            </Link>
          ))}
        </div>
      </div>
    </AppShell>
  );
}

function Stat({ icon, n, label }: { icon: string; n: number; label: string }) {
  return (
    <div className="ym-tile" style={{ textAlign: "center" }}>
      <Icon name={icon} size={26} color="var(--primary)" />
      <div className="ym-h1" style={{ fontSize: 28, marginTop: 4 }}>{n}</div>
      <div className="ym-tile-sub">{label}</div>
    </div>
  );
}
