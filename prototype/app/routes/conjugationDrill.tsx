import { Form, Link, useActionData, useLoaderData, useNavigation } from "react-router";
import { AppShell } from "~/ui/AppShell";
import { Icon } from "~/ui/Icon";
// ROUND/LEVELS come from the client-safe module — the component renders ROUND, and importing it
// from the .server file pulls the whole bank into the client bundle and fails the build.
import { LEVELS, ROUND, type Level } from "~/lib/drill";
import { bankSize, buildRound, gradeRound } from "~/lib/conjugation.server";

export function meta() {
  return [{ title: "Yomineko — Conjugação" }];
}

function levelOf(v: string | null): Level {
  const lv = (v ?? "").toLowerCase() as Level;
  return LEVELS.includes(lv) ? lv : "n5";
}
/** A fresh round gets a fresh seed; ?seed= keeps one reproducible for support or review. */
function seedFrom(url: URL): string {
  return url.searchParams.get("seed") || String(Date.now() % 100000);
}

export async function loader({ request }: { request: Request }) {
  const url = new URL(request.url);
  const level = levelOf(url.searchParams.get("nivel"));
  const seed = seedFrom(url);
  // `correct` is never in this payload — the answer key stays server-side until grading.
  return { round: buildRound(level, seed), seed, level, sizes: LEVELS.map((l) => ({ level: l, n: bankSize(l) })) };
}

export async function action({ request }: { request: Request }) {
  const fd = await request.formData();
  const level = levelOf(String(fd.get("level") ?? ""));
  const seed = String(fd.get("seed") ?? "");
  const answers: Record<string, string> = {};
  for (const [k, v] of fd.entries()) if (/^q\d+$/.test(k)) answers[k] = String(v);
  // Grading rebuilds the round from (level, seed); the request supplies choices, never the key.
  return { result: gradeRound(level, seed, answers) };
}

export default function ConjugationDrill() {
  const { round, seed, level, sizes } = useLoaderData<typeof loader>();
  const graded = useActionData<typeof action>();
  const nav = useNavigation();
  const result = graded?.result;
  const busy = nav.state !== "idle";

  if (result) {
    return (
      <AppShell active="practice" title="Conjugação">
        <div className="ym-page">
          <h1 className="ym-h1">Resultado</h1>
          <p className="ym-sub">
            <strong>{result.right} de {result.total}</strong> · {result.level.toUpperCase()} · rodada nº {result.seed}
          </p>
          <ol className="ym-list">
            {result.questions.map((q) => (
              <li key={q.key} className={q.correct ? "ym-ok" : "ym-bad"} style={{ marginBottom: ".7rem" }}>
                <span className="ym-jp">{q.prompt}</span> <span className="ym-muted">→ {q.formLabel}</span>
                <div className="ym-muted">
                  Você: <span className="ym-jp">{q.given || "—"}</span>
                  {!q.correct && <> · Correta: <span className="ym-jp">{q.expected}</span></>}
                  {q.kana && <> · {q.kana}</>}
                </div>
              </li>
            ))}
          </ol>
          <div style={{ display: "flex", gap: ".75rem", marginTop: "1.25rem" }}>
            <Link className="ym-btn ym-btn-primary" to={`/pratica/conjugacao?nivel=${result.level}`} reloadDocument>
              <Icon name="refresh" /> Nova rodada
            </Link>
            <Link className="ym-btn" to="/pratica">Voltar à prática</Link>
          </div>
        </div>
      </AppShell>
    );
  }

  return (
    <AppShell active="practice" title="Conjugação">
      <div className="ym-page">
        <h1 className="ym-h1">Conjugação</h1>
        <p className="ym-sub">
          Uma rodada de {ROUND} formas, sorteada do banco. As alternativas erradas são sempre OUTRAS
          formas da mesma palavra, então o que se testa é a forma, não o vocabulário.
        </p>
        <p className="ym-muted">
          {sizes.map((s) => (
            <Link key={s.level} to={`/pratica/conjugacao?nivel=${s.level}`}
                  className={s.level === level ? "ym-chip ym-chip-on" : "ym-chip"}
                  style={{ marginRight: ".5rem" }}>
              {s.level.toUpperCase()} · {s.n.toLocaleString("pt-BR")}
            </Link>
          ))}
        </p>

        <Form method="post">
          <input type="hidden" name="seed" value={seed} />
          <input type="hidden" name="level" value={level} />
          {round.questions.map((q, i) => (
            <fieldset key={q.key} className="ym-q">
              <legend className="ym-muted">Questão {i + 1} · {q.kind === "adjective" ? "adjetivo" : "verbo"}</legend>
              <p className="ym-jp" style={{ fontSize: "1.3rem" }}>
                {q.prompt} <span className="ym-muted" style={{ fontSize: "1rem" }}>→ {q.formLabel}</span>
              </p>
              <div className="ym-choices">
                {q.options.map((opt) => (
                  <label key={opt} className="ym-choice">
                    <input type="radio" name={q.key} value={opt} />
                    <span className="ym-jp">{opt}</span>
                  </label>
                ))}
              </div>
            </fieldset>
          ))}
          <button className="ym-btn ym-btn-primary" type="submit" disabled={busy}>
            <Icon name="done_all" /> {busy ? "Corrigindo…" : "Conferir"}
          </button>
        </Form>
      </div>
    </AppShell>
  );
}
