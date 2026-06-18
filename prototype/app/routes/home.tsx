import { Link, useLoaderData } from "react-router";
import { AppShell } from "~/ui/AppShell";
import { Icon } from "~/ui/Icon";
// @ts-ignore — mascot is pure-SVG JSX
import { Yomineko } from "~/ui/yomineko/mascot";
import { courseTree, lessonsOfLevel, lessonRef } from "~/lib/corpus.server";

export function meta() {
  return [{ title: "Yomineko — Início" }];
}

export async function loader() {
  const tree = courseTree();
  const active = tree[0]; // first course in order = the real starting point (derived, not hardcoded)
  const firstId = active ? lessonsOfLevel(active.level)[0] ?? null : null;
  return {
    courses: tree.map((c) => ({ id: c.id, level: c.level, title: c.title, topicCount: c.topicCount, lessonCount: c.lessonCount })),
    active: active ? { level: active.level, title: active.title, lesson: lessonRef(firstId) } : null,
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
        <div className="ym-kicker"><ruby className="ym-jp" lang="ja">こんにちは<rt>konnichiwa</rt></ruby></div>
        <h1 className="ym-h1">Bem-vindo de volta</h1>
        <p className="ym-sub">Seu protótipo Yomineko com o conteúdo real do corpus de pesquisa.</p>

        {active && (
          <div className="ym-home-hero">
            <div className="ym-home-hero-art" aria-hidden="true"><Yomineko pose="reading" size={132} /></div>
            <div className="ym-home-hero-body">
              <div className="ym-pill ym-pill-primary">CONTINUAR</div>
              <div className="ym-home-hero-title">{active.lesson?.title ?? active.title}</div>
              <div className="ym-home-hero-sub">{active.title}</div>
              <div className="ym-home-hero-cta">
                {active.lesson && (
                  <Link to={`/licao/${encodeURIComponent(active.lesson.id)}`} className="btn btn-filled">
                    <Icon name="play_arrow" size={20} fill /> Começar a lição
                  </Link>
                )}
                <Link to="/curso" className="btn btn-tonal">Ver o curso</Link>
              </div>
            </div>
          </div>
        )}

        <h2 className="ym-section-title">Continue treinando</h2>
        <div className="ym-grid" style={{ gridTemplateColumns: "repeat(auto-fit, minmax(160px,1fr))" }}>
          <Link to="/revisar" className="ym-quick"><div className="ym-quick-ic"><Icon name="style" size={22} /></div><div><div className="ym-quick-t">Revisar</div><div className="ym-quick-d">Cartões de hoje</div></div></Link>
          <Link to="/pratica" className="ym-quick"><div className="ym-quick-ic"><Icon name="target" size={22} /></div><div><div className="ym-quick-t">Praticar</div><div className="ym-quick-d">Seis modos</div></div></Link>
          <Link to="/kanji" className="ym-quick"><div className="ym-quick-ic"><Icon name="translate" size={22} /></div><div><div className="ym-quick-t">Kanji</div><div className="ym-quick-d">Explorar</div></div></Link>
        </div>

        <h2 className="ym-section-title">Estatísticas do corpus</h2>
        <div className="ym-grid" style={{ gridTemplateColumns: "repeat(auto-fit, minmax(140px,1fr))" }}>
          <Stat icon="auto_stories" n={totals.lessons} label="lições" />
          <Stat icon="category" n={totals.topics} label="tópicos" />
          <Stat icon="school" n={courses.length} label="módulos" />
        </div>

        <h2 className="ym-section-title">Módulos</h2>
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
    <div className="ym-stat">
      <div className="ym-stat-ic"><Icon name={icon} size={22} /></div>
      <div className="ym-stat-n">{n}</div>
      <div className="ym-stat-label">{label}</div>
    </div>
  );
}
