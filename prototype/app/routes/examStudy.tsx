import { Link, useLoaderData } from "react-router";
import { data } from "react-router";
import { AppShell } from "~/ui/AppShell";
import { Icon } from "~/ui/Icon";
import { STUDY_PAGE, studySet } from "~/lib/examStudy.server";

export function meta({ data: d }: { data: { set?: { lesson?: { title?: string } } } | undefined }) {
  return [{ title: `Yomineko — Estudo: ${d?.set?.lesson?.title ?? "simulado"}` }];
}

/**
 * Study mode over the exam banks: untimed, one page at a time, right/wrong the instant you answer.
 *
 * The feedback is the lesson exercises' pure-CSS contract (`data-correct` on each radio, revealed by
 * `:has()` in lesson.css) — no JavaScript, nothing to hydrate, and it works with the page's first
 * paint. That means the answer key IS in this page, which is the deliberate difference from
 * `examPaper.tsx`: an exam withholds the key and grades on the server, a study drill cannot.
 */
export async function loader({ params, request }: {
  params: { lessonId?: string }; request: Request;
}) {
  const url = new URL(request.url);
  const offset = Math.max(0, Number(url.searchParams.get("de") ?? 0) || 0);
  const set = studySet(params.lessonId ?? "", offset, STUDY_PAGE);
  if (!set) throw data("Lição não encontrada", { status: 404 });
  return { set };
}

export default function ExamStudy() {
  const { set } = useLoaderData<typeof loader>();
  const next = set.offset + set.limit;
  const prev = Math.max(0, set.offset - set.limit);
  const to = (n: number) => `/simulado/estudo/${set.lesson.id}?de=${n}`;

  return (
    <AppShell active="exam" title="Modo estudo" back="/simulado">
      <div className="ym-page">
        <h1 className="ym-h1">Modo estudo</h1>
        <p className="ym-sub">
          Questões do banco do simulado, sem cronômetro e com a resposta na hora. Só aparecem as que
          cabem no que a lição <strong>{set.lesson.title}</strong> já ensinou: todo kanji, toda palavra
          e todo ponto gramatical da questão está dentro do conjunto acumulado dessa lição.
        </p>

        <div className="ym-card-plain" style={{ marginBottom: 18 }}>
          <div className="ym-chip-row">
            <span className="ym-chip">{set.known.kanji} kanji</span>
            <span className="ym-chip">{set.known.vocab} palavras</span>
            <span className="ym-chip">{set.known.grammar} pontos de gramática</span>
            <span className="ym-pill ym-pill-primary">
              {set.eligible.toLocaleString("pt-BR")} questões disponíveis
            </span>
          </div>
          {set.byType.length > 0 && (
            <div className="ym-chip-row" style={{ marginTop: 8 }}>
              {set.byType.map((t) => (
                <span key={t.type} className="ym-chip">{t.label} ×{t.n}</span>
              ))}
            </div>
          )}
        </div>

        {set.items.length === 0 && (
          <div className="ym-card ym-card-tight">
            <strong>Nada para praticar aqui ainda.</strong>
            <p className="ym-muted">
              Nenhuma questão do banco cabe inteira no que esta lição ensinou até agora — basta um
              kanji ou uma palavra que ainda não apareceu para a questão ficar de fora. Volte depois
              de avançar mais algumas lições.
            </p>
          </div>
        )}

        {set.items.map((q, i) => (
          <div key={q.id} className="ym-ex">
            <div className="ym-ex-head">
              <Icon name="school" size={18} />
              <span>{q.label}</span>
              <span className="ym-jp" style={{ fontWeight: 400 }}>{q.jp}</span>
              <span className="ym-pill">{q.level.toUpperCase()}</span>
            </div>

            {q.passage && <p className="ym-jp ym-passage">{q.passage}</p>}

            {/* 聴解 in study mode: the recording plus its transcript. design/listening.md allows the
                script here and forbids it in the exam, and no listening item reaches this page at all
                until it has audio. */}
            {q.audio && (
              <audio controls preload="none" src={q.audio} className="ym-study-audio">
                <track kind="captions" />
              </audio>
            )}
            {q.listening && q.script && (
              <details className="ym-reading-trans">
                <summary><Icon name="subtitles" size={16} /> transcrição</summary>
                <div className="ym-reading-pt">
                  {q.script.map((t, ti) => (
                    <p key={ti} className="ym-jp"><strong>{t.speaker}:</strong> {t.text}</p>
                  ))}
                </div>
              </details>
            )}

            {q.prompt && <div className="ym-ex-prompt ym-jp">{q.prompt}</div>}
            {q.focus && !q.prompt.includes(`「${q.focus}」`) && (
              <p className="ym-muted">
                Palavra em foco: <strong className="ym-jp">{q.focus}</strong>
              </p>
            )}

            {q.ordering ? (
              <>
                <div className="ym-chip-row">
                  {(q.pieces ?? []).map((p, pi) => (
                    <span key={`${p}-${pi}`} className="ym-build-tok" lang="ja">{p}</span>
                  ))}
                </div>
                <details className="ym-reading-trans" style={{ marginTop: 10 }}>
                  <summary><Icon name="visibility" size={16} /> ver a ordem correta</summary>
                  <p className="ym-jp ym-ex-answer">{q.answer}</p>
                </details>
              </>
            ) : (
              <fieldset className="ym-ex-choices is-stacked">
                <legend className="ym-sr-only">Escolha a resposta</legend>
                {q.options.map((o, oi) => (
                  <label key={o.text} className="ym-ex-choice">
                    <input type="radio" name={`s${set.offset}-${i}`}
                           data-correct={o.correct ? "true" : "false"} />
                    <span className="ym-ex-choice-n">{oi + 1}</span>
                    <span lang="ja">{o.text}</span>
                  </label>
                ))}
              </fieldset>
            )}

            {/* Revealed by CSS once a choice is picked. `explanation` is the item's own, when it has
                one; no bank item does today, so what a learner usually gets is the source sentence —
                a Layer-B fact, labelled as such, never presented as an explanation. */}
            <div className="ym-ex-expl">
              <div>Resposta: <strong className="ym-jp ym-ex-answer">{q.answer}</strong></div>
              {q.explanation && <p>{q.explanation}</p>}
              {!q.explanation && q.source && (
                <p>
                  Frase de origem: <span className="ym-jp">{q.source.jp}</span>
                  {q.source.pt && <> — {q.source.pt}</>}
                </p>
              )}
            </div>
          </div>
        ))}

        <div style={{ display: "flex", gap: ".75rem", marginTop: "1.25rem", flexWrap: "wrap" }}>
          {set.offset > 0 && (
            <Link className="ym-btn" to={to(prev)}><Icon name="arrow_back" /> Anteriores</Link>
          )}
          {next < set.eligible && (
            <Link className="ym-btn ym-btn-primary" to={to(next)}>
              <Icon name="arrow_forward" /> Próximas {Math.min(set.limit, set.eligible - next)}
            </Link>
          )}
          <Link className="ym-btn" to="/simulado">Voltar ao simulado</Link>
        </div>

        <p className="ym-rev-foot">
          {set.eligible > 0 && (
            <>Questões {set.offset + 1}–{Math.min(next, set.eligible)} de {set.eligible}. </>
          )}
          Este modo não conta como prova: não é cronometrado e não vale nota.
        </p>
      </div>
    </AppShell>
  );
}
