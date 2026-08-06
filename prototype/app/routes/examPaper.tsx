import { useState } from "react";
import { Form, Link, useLoaderData, useActionData, useNavigation } from "react-router";
import { AppShell } from "~/ui/AppShell";
import { Icon } from "~/ui/Icon";
import { LEVELS, buildPaper, gradePaper, type Level } from "~/lib/exam.server";

export function meta({ params }: { params: { level?: string } }) {
  return [{ title: `Yomineko — Simulado ${(params.level ?? "").toUpperCase()}` }];
}

function levelOf(v?: string): Level {
  const lv = (v ?? "").toLowerCase() as Level;
  return LEVELS.includes(lv) ? lv : "n5";
}
/** A fresh attempt gets a fresh seed; ?seed= keeps a paper reproducible (support/review, rule 5). */
function seedFrom(url: URL): string {
  return url.searchParams.get("seed") || String(Date.now() % 100000);
}

export async function loader({ params, request }: { params: { level?: string }; request: Request }) {
  const level = levelOf(params.level);
  const seed = seedFrom(new URL(request.url));
  const paper = buildPaper(level, seed);
  // `correct` is never part of this payload — the answer key stays server-side until grading.
  return { paper, seed };
}

export async function action({ params, request }: { params: { level?: string }; request: Request }) {
  const level = levelOf(params.level);
  const fd = await request.formData();
  const seed = String(fd.get("seed") ?? "");
  const answers: Record<string, string> = {};
  for (const [k, v] of fd.entries()) {
    if (k.startsWith("q:")) answers[k.slice(2)] = String(v);
  }
  // Grading rebuilds the paper from (level, seed): the request supplies choices, never the key.
  return { result: gradePaper(level, seed, answers) };
}

/**
 * 並べ替え: click the blocks in order. The assembled string rides in a hidden input, so the answer still
 * arrives through the normal form POST — no IME typing required, and no client-side answer checking.
 */
function OrderQuestion({ name, pieces }: { name: string; pieces: string[] }) {
  const [picked, setPicked] = useState<number[]>([]);
  const used = new Set(picked);
  const sentence = picked.map((i) => pieces[i]).join("");
  return (
    <>
      <input type="hidden" name={name} value={sentence} />
      <div className="ym-choices">
        {pieces.map((p, i) => (
          <button key={`${p}-${i}`} type="button" className="ym-chip"
                  disabled={used.has(i)} onClick={() => setPicked([...picked, i])}>
            <span className="ym-jp">{p}</span>
          </button>
        ))}
      </div>
      <p className="ym-jp" style={{ marginTop: ".5rem" }}>
        {sentence || <span className="ym-muted">Clique nos blocos para montar a frase.</span>}
        {picked.length > 0 && (
          <button type="button" className="ym-btn ym-btn-ghost" style={{ marginLeft: ".75rem" }}
                  onClick={() => setPicked([])}>
            <Icon name="undo" /> limpar
          </button>
        )}
      </p>
    </>
  );
}

export default function ExamPaper() {
  const { paper, seed } = useLoaderData<typeof loader>();
  const graded = useActionData<typeof action>();
  const nav = useNavigation();
  const result = graded?.result;
  const busy = nav.state !== "idle";

  if (result) {
    return (
      <AppShell active="exam" title="Resultado">
        <div className="ym-page-wide">
          <h1 className="ym-h1">Resultado — {result.level.toUpperCase()}</h1>
          <p className="ym-sub">
            <strong>{result.right} de {result.total}</strong> ({result.percent}%) · prova nº {result.seed}
          </p>

          <div className="ym-grid" style={{ gridTemplateColumns: "repeat(auto-fill, minmax(220px,1fr))" }}>
            {result.perSection.map((s) => (
              <div key={s.type} className="ym-card ym-card-tight">
                <strong>{s.label}</strong>
                <div className="ym-muted">{s.right} / {s.of}</div>
              </div>
            ))}
          </div>

          <h2 className="ym-h2" style={{ marginTop: "1.5rem" }}>Revisão</h2>
          <ol className="ym-list">
            {result.questions.map((q) => (
              <li key={q.key} className={q.correct ? "ym-ok" : "ym-bad"}>
                <div className="ym-jp">{q.prompt}</div>
                <div className="ym-muted">
                  Sua resposta: <strong>{q.given || "—"}</strong>
                  {!q.correct && <> · Correta: <strong>{q.expected}</strong></>}
                </div>
              </li>
            ))}
          </ol>

          <div style={{ display: "flex", gap: ".75rem", marginTop: "1.25rem" }}>
            <Link className="ym-btn ym-btn-primary" to={`/simulado/${result.level}`} reloadDocument>
              <Icon name="refresh" /> Nova prova
            </Link>
            <Link className="ym-btn" to="/simulado">Trocar de nível</Link>
          </div>
        </div>
      </AppShell>
    );
  }

  let n = 0;
  return (
    <AppShell active="exam" title={`Simulado ${paper.level.toUpperCase()}`}>
      <div className="ym-page-wide">
        <h1 className="ym-h1">Simulado {paper.level.toUpperCase()}</h1>
        <p className="ym-sub">
          {paper.total} questões · tempo sugerido {paper.minutes} min · prova nº {paper.seed}
        </p>

        <Form method="post">
          <input type="hidden" name="seed" value={seed} />
          {paper.sections.map((sec) => (
            <section key={sec.type} className="ym-card" style={{ marginBottom: "1.25rem" }}>
              <header className="ym-card-h">
                <span className="ym-jp">{sec.jp}</span>
                <strong>{sec.label}</strong>
              </header>
              <p className="ym-muted">{sec.hint}</p>

              {sec.questions.map((q) => {
                n += 1;
                return (
                  <fieldset key={q.key} className="ym-q">
                    <legend className="ym-muted">Questão {n}</legend>
                    {q.passage && <p className="ym-jp ym-passage">{q.passage}</p>}
                    {q.prompt && <p className="ym-jp">{q.prompt}</p>}
                    {q.focus && !q.prompt.includes(`「${q.focus}」`) && (
                      <p className="ym-muted">
                        Palavra em foco: <strong className="ym-jp">{q.focus}</strong>
                      </p>
                    )}

                    {q.pieces ? (
                      <OrderQuestion name={`q:${q.key}`} pieces={q.pieces} />
                    ) : (
                      <div className="ym-choices">
                        {q.options.map((opt) => (
                          <label key={opt} className="ym-choice">
                            <input type="radio" name={`q:${q.key}`} value={opt} />
                            <span className="ym-jp">{opt}</span>
                          </label>
                        ))}
                      </div>
                    )}
                  </fieldset>
                );
              })}
            </section>
          ))}

          <button className="ym-btn ym-btn-primary" type="submit" disabled={busy}>
            <Icon name="done_all" /> {busy ? "Corrigindo…" : "Entregar prova"}
          </button>
        </Form>
      </div>
    </AppShell>
  );
}
