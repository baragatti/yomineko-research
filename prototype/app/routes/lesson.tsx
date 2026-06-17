import { Link, useLoaderData } from "react-router";
import { data } from "react-router";
import { AppShell } from "~/ui/AppShell";
import { Icon } from "~/ui/Icon";
import { getLesson, getTopic, lessonsOfLevel, loc } from "~/lib/corpus.server";
import { renderBody } from "~/lib/render-body.server";

export function meta({ data: d }: { data: any }) {
  return [{ title: `Yomineko — ${d?.title ?? "Lição"}` }];
}

export async function loader({ params }: { params: { lessonId: string } }) {
  const lesson = getLesson(params.lessonId);
  if (!lesson) throw data("Lição não encontrada", { status: 404 });
  const topic = getTopic(lesson.topic);

  // prev/next within the level (course order)
  const order = lessonsOfLevel(lesson.level);
  const idx = order.indexOf(lesson.id);
  const prev = idx > 0 ? order[idx - 1] : null;
  const next = idx >= 0 && idx < order.length - 1 ? order[idx + 1] : null;

  // RENDER SERVER-SIDE. Only this display HTML is sent — the tagged source + corpus stay on the server.
  const bodyHtml = renderBody(lesson.body, lesson.exercises || []);

  return {
    id: lesson.id,
    level: lesson.level,
    title: loc(lesson.title),
    objectives: (lesson.objectives || []).map(loc),
    topic: topic ? { id: topic.id, title: loc(topic.title) } : null,
    exerciseCount: (lesson.exercises || []).length,
    bodyHtml,
    prev,
    next,
  };
}

export default function Lesson() {
  const l = useLoaderData<typeof loader>();
  return (
    <AppShell active="study" title={l.title} back={l.topic ? `/curso/${encodeURIComponent(l.topic.id)}` : "/curso"}>
      <div className="ym-page">
        <div className="ym-breadcrumb">
          <Link to="/curso">Curso</Link>
          <Icon name="chevron_right" size={14} />
          {l.topic && (
            <>
              <Link to={`/curso/${encodeURIComponent(l.topic.id)}`}>{l.topic.title}</Link>
              <Icon name="chevron_right" size={14} />
            </>
          )}
          <span>{l.level.toUpperCase()}</span>
        </div>

        <h1 className="ym-h1">{l.title}</h1>
        {l.objectives.length > 0 && (
          <div className="ym-note ym-note-tip" style={{ marginBottom: 18 }}>
            <div className="ym-note-head"><Icon name="flag" size={18} /><span>Objetivos</span></div>
            <ul className="ym-list" style={{ margin: 0 }}>
              {l.objectives.map((o: string, i: number) => <li key={i} className="ym-item">{o}</li>)}
            </ul>
          </div>
        )}

        {/* Server-rendered lesson content. Display markup only — no source/data shipped. */}
        <div dangerouslySetInnerHTML={{ __html: l.bodyHtml }} />

        <div style={{ display: "flex", justifyContent: "space-between", gap: 12, marginTop: 32 }}>
          {l.prev ? (
            <Link to={`/licao/${encodeURIComponent(l.prev)}`} className="btn btn-tonal">
              <Icon name="arrow_back" size={18} /> Anterior
            </Link>
          ) : <span />}
          {l.next ? (
            <Link to={`/licao/${encodeURIComponent(l.next)}`} className="btn btn-filled">
              Próxima <Icon name="arrow_forward" size={18} />
            </Link>
          ) : <span />}
        </div>
      </div>
    </AppShell>
  );
}
