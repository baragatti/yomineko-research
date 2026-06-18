import { Link, useLoaderData } from "react-router";
import { AppShell } from "~/ui/AppShell";
import { Icon } from "~/ui/Icon";
import { FilterableList } from "~/ui/FilterableList";
import { courseTree } from "~/lib/corpus.server";

export function meta() {
  return [{ title: "Yomineko — Curso" }];
}

interface TopicItem {
  id: string;
  order: number;
  title: string;
  level: string;
  courseId: string;
  courseTitle: string;
  lessonCount: number;
  unlocks: { grammar?: number; vocab?: number; kanji?: number } | null;
}

export async function loader() {
  const courses = courseTree().map((c) => ({
    id: c.id,
    level: c.level,
    title: c.title,
    topics: c.topics.map((t: any) => ({
      id: t.id,
      order: t.order,
      title: t.title,
      lessonCount: t.lessonCount ?? t.lessons.length,
      unlocks: t.unlocks ?? null,
    })),
  }));
  return { courses };
}

function TopicTile({ t }: { t: TopicItem }) {
  return (
    <Link to={`/curso/${encodeURIComponent(t.id)}`} className="ym-tile">
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", gap: 8 }}>
        <div style={{ minWidth: 0 }}>
          <div className="ym-tile-sub" style={{ fontWeight: 700, letterSpacing: ".05em" }}>
            TÓPICO {String(t.order).padStart(2, "0")}
          </div>
          <div className="ym-tile-title">{t.title}</div>
        </div>
        <Icon name="chevron_right" size={20} color="var(--on-surface-variant)" />
      </div>
      <div style={{ display: "flex", gap: 6, marginTop: 12, flexWrap: "wrap" }}>
        <span className="ym-pill">{t.lessonCount} lições</span>
        {t.unlocks?.grammar ? <span className="ym-pill">{t.unlocks.grammar} gramática</span> : null}
        {t.unlocks?.vocab ? <span className="ym-pill">{t.unlocks.vocab} vocab</span> : null}
        {t.unlocks?.kanji ? <span className="ym-pill">{t.unlocks.kanji} kanji</span> : null}
      </div>
    </Link>
  );
}

export default function Course() {
  const { courses } = useLoaderData<typeof loader>();
  const topics: TopicItem[] = courses.flatMap((c) =>
    c.topics.map((t: any): TopicItem => ({ ...t, level: c.level, courseId: c.id, courseTitle: c.title }))
  );
  const topLevel = courses.length ? courses[courses.length - 1].level.toUpperCase() : "N4";

  return (
    <AppShell active="study" title="Curso">
      <div className="ym-page-wide">
        <h1 className="ym-h1">Trilha do curso</h1>
        <p className="ym-sub">Do zero ao {topLevel} — {topics.length} tópicos com dados reais do corpus.</p>

        <FilterableList
          items={topics}
          levelOf={(t) => t.level}
          searchOf={(t) => t.title}
          placeholder="Buscar tópico…"
          noun="tópicos"
        >
          {(filtered) =>
            courses.map((c) => {
              const ts = filtered.filter((t) => t.courseId === c.id);
              if (!ts.length) return null;
              return (
                <section key={c.id}>
                  <h2 className="ym-section-title">{c.title}</h2>
                  <div className="ym-grid" style={{ gridTemplateColumns: "repeat(auto-fill, minmax(280px,1fr))" }}>
                    {ts.map((t) => <TopicTile key={t.id} t={t} />)}
                  </div>
                </section>
              );
            })
          }
        </FilterableList>
      </div>
    </AppShell>
  );
}
