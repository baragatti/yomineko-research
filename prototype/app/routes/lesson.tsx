import { Link, useLoaderData } from "react-router";
import { data } from "react-router";
import { AppShell } from "~/ui/AppShell";
import { Icon } from "~/ui/Icon";
import { CorpusRefLayer } from "~/ui/CorpusRefLayer";
import { LessonExercises } from "~/ui/LessonExercises";
import { getLesson, getTopic, lessonsOfLevel, lessonRef, loc, resolveUnlocks, refSummaries } from "~/lib/corpus.server";
import { renderBody } from "~/lib/render-body.server";

export function meta({ data: d }: { data: any }) {
  return [{ title: `Yomineko — ${d?.title ?? "Lição"}` }];
}

export async function loader({ params }: { params: { lessonId: string } }) {
  const lesson = getLesson(params.lessonId);
  if (!lesson) throw data("Lição não encontrada", { status: 404 });
  const topic = getTopic(lesson.topic);
  const title = loc(lesson.title);

  // prev/next within the level (course order)
  const order = lessonsOfLevel(lesson.level);
  const idx = order.indexOf(lesson.id);

  // RENDER SERVER-SIDE. Only this display HTML is sent — the tagged source + corpus stay on the server.
  // dedupeTitle drops the body's leading heading when it just repeats the page title.
  const bodyHtml = renderBody(lesson.body, lesson.exercises || [], title);

  return {
    id: lesson.id,
    level: lesson.level,
    title,
    objectives: (lesson.objectives || []).map(loc),
    topic: topic ? { id: topic.id, title: loc(topic.title) } : null,
    bodyHtml,
    refData: refSummaries(lesson.body || ""),
    unlocks: resolveUnlocks(lesson),
    prev: lessonRef(idx > 0 ? order[idx - 1] : null),
    next: lessonRef(idx >= 0 && idx < order.length - 1 ? order[idx + 1] : null),
  };
}

const UNLOCK_GROUPS = [
  { key: "kanji", label: "Kanji desta lição", chip: "ym-chip-kanji" },
  { key: "vocab", label: "Vocabulário desta lição", chip: "ym-chip-vocab" },
  { key: "grammar", label: "Gramática desta lição", chip: "ym-chip-grammar" },
] as const;

export default function Lesson() {
  const l = useLoaderData<typeof loader>();
  const hasUnlocks = (l.unlocks.kanji.length + l.unlocks.vocab.length + l.unlocks.grammar.length) > 0;
  return (
    <AppShell active="study" title={l.title} back={l.topic ? `/curso/${encodeURIComponent(l.topic.id)}` : "/curso"}>
      <article className="ym-page">
        <nav className="ym-breadcrumb" aria-label="Trilha">
          <Link to="/curso">Curso</Link>
          <Icon name="chevron_right" size={14} />
          {l.topic && (
            <>
              <Link to={`/curso/${encodeURIComponent(l.topic.id)}`}>{l.topic.title}</Link>
              <Icon name="chevron_right" size={14} />
            </>
          )}
          <span>{l.level.toUpperCase()}</span>
        </nav>

        <h1 className="ym-h1">{l.title}</h1>
        {l.objectives.length > 0 && (
          <div className="ym-note ym-note-tip" style={{ marginBottom: 18 }}>
            <div className="ym-note-head"><Icon name="flag" size={18} /><span>Objetivos</span></div>
            <ul className="ym-list" style={{ margin: 0 }}>
              {l.objectives.map((o: string, i: number) => <li key={i} className="ym-item">{o}</li>)}
            </ul>
          </div>
        )}

        {/* Server-rendered lesson content. Display markup only — no source/data shipped.
            Exercises are interactive via pure CSS (radio + :has), so nothing here needs hydration. */}
        <div className="ym-lesson-body" dangerouslySetInnerHTML={{ __html: l.bodyHtml }} />
        <CorpusRefLayer refData={l.refData} />
        <LessonExercises />

        {hasUnlocks && (
          <section className="ym-unlocks" aria-label="O que esta lição apresenta">
            {UNLOCK_GROUPS.map((g) => {
              const items = l.unlocks[g.key] as { id: string; label: string; href: string }[];
              if (!items.length) return null;
              return (
                <div key={g.key}>
                  <h2 className="ym-section-title">{g.label}</h2>
                  <div className="ym-chip-row">
                    {items.map((it) => (
                      <Link key={it.id} to={it.href} className={`ym-chip ${g.chip}`} lang="ja">{it.label}</Link>
                    ))}
                  </div>
                </div>
              );
            })}
          </section>
        )}

        <nav className="ym-pager" aria-label="Navegação entre lições">
          {l.prev ? (
            <Link to={`/licao/${encodeURIComponent(l.prev.id)}`} className="ym-pager-link ym-pager-prev">
              <Icon name="arrow_back" size={18} />
              <span><small>Anterior</small>{l.prev.title}</span>
            </Link>
          ) : <span />}
          {l.next ? (
            <Link to={`/licao/${encodeURIComponent(l.next.id)}`} className="ym-pager-link ym-pager-next">
              <span><small>Próxima</small>{l.next.title}</span>
              <Icon name="arrow_forward" size={18} />
            </Link>
          ) : <span />}
        </nav>
      </article>
    </AppShell>
  );
}
