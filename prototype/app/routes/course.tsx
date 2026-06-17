import { Link, useLoaderData } from "react-router";
import { AppShell } from "~/ui/AppShell";
import { Icon } from "~/ui/Icon";
import { courseTree } from "~/lib/corpus.server";

export function meta() {
  return [{ title: "Yomineko — Curso" }];
}

export async function loader() {
  return {
    courses: courseTree().map((c) => ({
      id: c.id,
      level: c.level,
      title: c.title,
      topics: c.topics.map((t) => ({
        id: t.id,
        order: t.order,
        title: t.title,
        lessonCount: t.lessonCount ?? t.lessons.length,
        unlocks: t.unlocks,
      })),
    })),
  };
}

export default function Course() {
  const { courses } = useLoaderData<typeof loader>();
  return (
    <AppShell active="study" title="Curso">
      <div className="ym-page-wide">
        <h1 className="ym-h1">Trilha do curso</h1>
        <p className="ym-sub">Do zero ao N4 — {courses.reduce((n, c) => n + c.topics.length, 0)} tópicos com dados reais do corpus.</p>

        {courses.map((c) => (
          <section key={c.id}>
            <div className="ym-section-title">{c.title}</div>
            <div className="ym-grid" style={{ gridTemplateColumns: "repeat(auto-fill, minmax(280px,1fr))" }}>
              {c.topics.map((t, i) => (
                <Link key={t.id} to={`/curso/${encodeURIComponent(t.id)}`} className="ym-tile">
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
              ))}
            </div>
          </section>
        ))}
      </div>
    </AppShell>
  );
}
