import { Link, useLoaderData } from "react-router";
import { data } from "react-router";
import { AppShell } from "~/ui/AppShell";
import { Icon } from "~/ui/Icon";
import { getTopic, loc } from "~/lib/corpus.server";

export function meta({ data: d }: { data: any }) {
  return [{ title: `Yomineko — ${d?.title ?? "Tópico"}` }];
}

export async function loader({ params }: { params: { topicId: string } }) {
  const t = getTopic(params.topicId);
  if (!t) throw data("Tópico não encontrado", { status: 404 });
  return {
    id: t.id,
    level: t.level,
    title: loc(t.title),
    theme: t.theme,
    objectives: (t.objectives || []).map(loc),
    lessons: (t.lessons || []).map((l: any) => ({
      id: l.id,
      order: l.order,
      title: loc(l.title),
      description: loc(l.description),
    })),
  };
}

export default function Topic() {
  const t = useLoaderData<typeof loader>();
  return (
    <AppShell active="study" title={t.title} back="/curso">
      <div className="ym-page">
        <div className="ym-breadcrumb">
          <Link to="/curso">Curso</Link> <Icon name="chevron_right" size={14} /> <span>{t.level.toUpperCase()}</span>
        </div>
        <h1 className="ym-h1">{t.title}</h1>
        {t.objectives.length > 0 && (
          <ul className="ym-list" style={{ marginBottom: 18 }}>
            {t.objectives.map((o: string, i: number) => (
              <li key={i} className="ym-item">{o}</li>
            ))}
          </ul>
        )}

        <h2 className="ym-section-title">{t.lessons.length} lições</h2>
        <div className="ym-cards">
          {t.lessons.map((l: any) => (
            <Link key={l.id} to={`/licao/${encodeURIComponent(l.id)}`} className="ym-tile">
              <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
                <Icon name="play_circle" size={24} color="var(--primary)" />
                <div style={{ flex: 1, minWidth: 0 }}>
                  <div style={{ display: "flex", gap: 8, alignItems: "baseline" }}>
                    <span className="ym-tile-sub" style={{ fontWeight: 700 }}>{String(l.order).padStart(2, "0")}</span>
                    <span className="ym-tile-title" style={{ fontSize: 16 }}>{l.title}</span>
                  </div>
                  {l.description && <div className="ym-tile-sub" style={{ marginTop: 2 }}>{l.description}</div>}
                </div>
                <Icon name="chevron_right" size={20} color="var(--on-surface-variant)" />
              </div>
            </Link>
          ))}
        </div>
      </div>
    </AppShell>
  );
}
