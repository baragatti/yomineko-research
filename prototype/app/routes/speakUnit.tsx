import { useState } from "react";
import { Form, Link, useActionData, useLoaderData } from "react-router";
import { data } from "react-router";
import { AppShell } from "~/ui/AppShell";
import { Icon } from "~/ui/Icon";
import { getUnit, gradeCheckpoint, checkpointLabel, splitUnitId } from "~/lib/speak.server";

export function meta({ data: d }: { data?: { unit?: { title?: string } } }) {
  return [{ title: `Yomineko — ${d?.unit?.title ?? "Fala Primeiro"}` }];
}

export async function loader({ params }: { params: { stage?: string; unit?: string } }) {
  const unit = getUnit(params.stage ?? "", Number(params.unit ?? 1));
  if (!unit) throw data("Unidade não encontrada", { status: 404 });
  return { unit };
}

export async function action({ params, request }: { params: { stage?: string; unit?: string }; request: Request }) {
  const fd = await request.formData();
  const answers: Record<string, string> = {};
  for (const [k, v] of fd.entries()) if (k.startsWith("q:")) answers[k.slice(2)] = String(v);
  // Graded server-side against the unit's own checkpoint list; the page never held the answer key.
  return { result: gradeCheckpoint(params.stage ?? "", Number(params.unit ?? 1), answers) };
}

/** Same click-to-assemble widget as the exam paper: no IME typing, answer rides in a hidden input. */
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
                  onClick={() => setPicked([])}>limpar</button>
        )}
      </p>
    </>
  );
}

function href(id: string): string {
  const { stage, order } = splitUnitId(id);
  return `/falar/${stage}/${order}`;
}

export default function SpeakUnit() {
  const { unit } = useLoaderData<typeof loader>();
  const graded = useActionData<typeof action>();
  const result = graded?.result;

  return (
    <AppShell active="speak" title={unit.stageTitle}>
      <div className="ym-page">
        <p className="ym-muted">
          <Link to="/falar">Fala Primeiro</Link> · {unit.stageTitle}
        </p>
        <h1 className="ym-h1">{unit.title}</h1>
        <p className="ym-sub">
          Diga estas frases em voz alta. {unit.knownSoFar} palavras acumuladas até aqui.
        </p>

        <section className="ym-card">
          <header className="ym-card-h"><strong>Fale agora</strong></header>
          <ol className="ym-list">
            {unit.phrases.map((p) => (
              <li key={p.slug} style={{ marginBottom: ".9rem" }}>
                <div className="ym-jp" lang="ja" style={{ fontSize: "1.25rem" }}>{p.jp}</div>
                <div className="ym-muted">{p.romaji}</div>
                <div>{p.pt}</div>
                {p.chunk && (
                  <div className="ym-muted">
                    <Icon name="bookmark" /> expressão fixa — decore inteira, não traduza pedaço a pedaço
                  </div>
                )}
              </li>
            ))}
          </ol>
        </section>

        {unit.words.length > 0 && (
          <section className="ym-card">
            <header className="ym-card-h"><strong>Palavras novas</strong></header>
            <ul className="ym-list ym-list-tight">
              {unit.words.map((w) => (
                <li key={w.slug}>
                  <Link to={`/vocabulario/${encodeURIComponent(w.headword)}`}>
                    <span className="ym-jp">{w.headword}</span>
                  </Link>{" "}
                  <span className="ym-muted">{w.kana} · {w.romaji} · {w.level.toUpperCase()}</span>
                </li>
              ))}
            </ul>
          </section>
        )}

        {unit.patterns.length > 0 && (
          <section className="ym-card">
            <header className="ym-card-h"><strong>Padrões que aparecem aqui</strong></header>
            <ul className="ym-list ym-list-tight">
              {unit.patterns.map((g) => (
                <li key={g.slug}>
                  <Link to={`/gramatica/${g.key}`}>{g.label}</Link>{" "}
                  <span className="ym-muted">{g.level.toUpperCase()}</span>
                </li>
              ))}
            </ul>
          </section>
        )}

        {unit.signage.length > 0 && (
          <section className="ym-card">
            <header className="ym-card-h"><strong>Kanji de placa — só reconhecer</strong></header>
            <p className="ym-jp" style={{ fontSize: "1.5rem" }}>
              {unit.signage.map((ch) => (
                <Link key={ch} to={`/kanji/${encodeURIComponent(ch)}`} style={{ marginRight: ".6rem" }}>
                  {ch}
                </Link>
              ))}
            </p>
            <p className="ym-muted">Nesta trilha você não precisa escrever kanji — só bater o olho e reconhecer.</p>
          </section>
        )}

        {unit.checkpoint.length > 0 && (
          <section className="ym-card">
            <header className="ym-card-h">
              <strong>Checagem</strong>
              {result && <span className="ym-muted">{result.right} de {result.total}</span>}
            </header>
            {result ? (
              <>
                <ol className="ym-list">
                  {result.questions.map((q) => (
                    <li key={q.key} className={q.correct ? "ym-ok" : "ym-bad"}>
                      <span className="ym-jp">{q.prompt}</span>
                      <div className="ym-muted">
                        Você: <strong>{q.given || "—"}</strong>
                        {!q.correct && <> · Correta: <strong>{q.expected}</strong></>}
                      </div>
                    </li>
                  ))}
                </ol>
                <Link className="ym-btn" to={`/falar/${unit.stage}/${unit.order}`} reloadDocument>
                  <Icon name="refresh" /> Tentar de novo
                </Link>
              </>
            ) : (
              <Form method="post">
                {unit.checkpoint.map((q) => (
                  <fieldset key={q.key} className="ym-q">
                    <legend className="ym-muted">{checkpointLabel(q.type)}</legend>
                    {q.prompt && <p className="ym-jp">{q.prompt}</p>}
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
                ))}
                <button className="ym-btn ym-btn-primary" type="submit">
                  <Icon name="done_all" /> Conferir
                </button>
              </Form>
            )}
          </section>
        )}

        <nav style={{ display: "flex", gap: ".75rem", marginTop: "1.25rem" }}>
          {unit.prev && <Link className="ym-btn" to={href(unit.prev)}><Icon name="arrow_back" /> Anterior</Link>}
          {unit.next && <Link className="ym-btn ym-btn-primary" to={href(unit.next)}>Próxima <Icon name="arrow_forward" /></Link>}
        </nav>
      </div>
    </AppShell>
  );
}
