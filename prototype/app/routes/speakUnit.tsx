import { useState } from "react";
import { Form, Link, useActionData, useLoaderData } from "react-router";
import { data } from "react-router";
import { AppShell } from "~/ui/AppShell";
import { Icon } from "~/ui/Icon";
// The two pure helpers come from the client-safe module; the component calls them, and importing
// them from the .server file pulls the whole speaking path into the client bundle.
import { checkpointLabel, splitUnitId } from "~/lib/speak";
import { getUnit, gradeCheckpoint, gradeProduction } from "~/lib/speak.server";
import { vocabHref } from "~/lib/ids";

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
  const stage = params.stage ?? "";
  const order = Number(params.unit ?? 1);
  // Two independent blocks on one page, so the submit button says which one to grade. Both are graded
  // server-side against the unit's own data; the page never held either answer key.
  if (fd.get("block") === "production") {
    const answers: Record<string, string> = {};
    for (const [k, v] of fd.entries()) if (/^p\d+$/.test(k)) answers[k] = String(v);
    return { production: gradeProduction(stage, order, answers) };
  }
  const answers: Record<string, string> = {};
  for (const [k, v] of fd.entries()) if (k.startsWith("q:")) answers[k.slice(2)] = String(v);
  return { result: gradeCheckpoint(stage, order, answers) };
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
  const prod = graded?.production;

  return (
    <AppShell active="speak" title={unit.stageTitle}>
      <div className="ym-page">
        <p className="ym-muted">
          <Link to="/cursos/falar">Fala Primeiro</Link> · {unit.stageTitle}
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
                  <Link to={vocabHref(w.slug)}>
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

        {unit.drills.length > 0 && (
          <section className="ym-card">
            <header className="ym-card-h"><strong>O mesmo padrão, outras frases</strong></header>
            <p className="ym-muted">
              Se o padrão só serve para uma frase, ele não é padrão. Leia as três em voz alta.
            </p>
            {unit.drills.map((d) => (
              <div key={d.pattern} style={{ marginBottom: ".9rem" }}>
                <strong>{d.label}</strong>
                <ul className="ym-list ym-list-tight">
                  {d.examples.map((e) => (
                    <li key={e.jp}>
                      <span className="ym-jp" lang="ja">{e.jp}</span>
                      <div className="ym-muted">{e.pt}</div>
                    </li>
                  ))}
                </ul>
              </div>
            ))}
          </section>
        )}

        {unit.production.length > 0 && (
          <section className="ym-card">
            <header className="ym-card-h">
              <strong>Agora você fala</strong>
              {prod && <span className="ym-muted">{prod.right} de {prod.total}</span>}
            </header>
            <p className="ym-muted">
              Frases que você já viu antes. Diga em voz alta primeiro, depois escreva em japonês.
            </p>
            {prod ? (
              <>
                <ol className="ym-list">
                  {prod.items.map((it) => (
                    <li key={it.key} className={it.correct ? "ym-ok" : "ym-bad"}>
                      {it.promptPt}
                      <div className="ym-muted">
                        Você: <span className="ym-jp">{it.given || "—"}</span>
                        {!it.correct && <> · Correta: <span className="ym-jp">{it.expected}</span></>}
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
                <input type="hidden" name="block" value="production" />
                {unit.production.map((p) => (
                  <fieldset key={p.key} className="ym-q">
                    <legend className="ym-muted">Diga em japonês</legend>
                    <p>{p.promptPt}</p>
                    <input className="ym-input" name={p.key} lang="ja" autoComplete="off"
                           placeholder="日本語で" />
                  </fieldset>
                ))}
                <button className="ym-btn ym-btn-primary" type="submit">
                  <Icon name="done_all" /> Conferir
                </button>
              </Form>
            )}
          </section>
        )}

        {unit.fluency && (
          <section className="ym-card">
            <header className="ym-card-h">
              <strong>Fluência</strong>
              <span className="ym-muted">meta: {unit.fluency.seconds}s</span>
            </header>
            <p>{unit.fluency.promptPt}</p>
            <p className="ym-muted">
              Nada novo aqui: tudo isto você já sabe. O objetivo é velocidade, não acerto —
              fale as {unit.fluency.items.length} frases sem parar para pensar.
            </p>
            <ul className="ym-list ym-list-tight">
              {unit.fluency.items.map((e) => (
                <li key={e.jp}>
                  <span className="ym-jp" lang="ja">{e.jp}</span>
                  <div className="ym-muted">{e.pt}</div>
                </li>
              ))}
            </ul>
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
