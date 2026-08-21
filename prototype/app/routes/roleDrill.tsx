import { Form, Link, useActionData, useLoaderData, useNavigation } from "react-router";
import { AppShell } from "~/ui/AppShell";
import { Icon } from "~/ui/Icon";
import { LEVELS, ROUND, bankSize, buildRound, gradeRound, type Level } from "~/lib/roles.server";

export function meta() {
  return [{ title: "Yomineko — Papéis na frase" }];
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

export default function RoleDrill() {
  const { round, seed, level, sizes } = useLoaderData<typeof loader>();
  const graded = useActionData<typeof action>();
  const nav = useNavigation();
  const result = graded?.result;
  const busy = nav.state !== "idle";

  if (result) {
    return (
      <AppShell active="practice" title="Papéis na frase">
        <div className="ym-page">
          <h1 className="ym-h1">Resultado</h1>
          <p className="ym-sub">
            <strong>{result.right} de {result.total}</strong> · {result.level.toUpperCase()} · rodada nº {result.seed}
          </p>
          <ol className="ym-list">
            {result.questions.map((q) => (
              <li key={q.key} className={q.correct ? "ym-ok" : "ym-bad"} style={{ marginBottom: ".8rem" }}>
                <span className="ym-jp" lang="ja">{q.jp}</span>
                <div className="ym-muted">{q.prompt}</div>
                <div className="ym-muted">
                  Você: <span className="ym-jp" lang="ja">{q.given || "—"}</span>
                  {!q.correct && <> · Correta: <span className="ym-jp" lang="ja">{q.expected}</span></>}
                  {/* The particle IS the reason, so it is shown rather than the answer alone. */}
                  {q.particle
                    ? <> · quem marca {q.roleLabel} aqui é <span className="ym-jp" lang="ja">{q.particle}</span></>
                    : <> · {q.roleLabel} fecha a frase, sem partícula</>}
                </div>
              </li>
            ))}
          </ol>
          <div style={{ display: "flex", gap: ".75rem", marginTop: "1.25rem" }}>
            <Link className="ym-btn ym-btn-primary" to={`/pratica/papeis?nivel=${result.level}`} reloadDocument>
              <Icon name="refresh" /> Nova rodada
            </Link>
            <Link className="ym-btn" to="/pratica">Voltar à prática</Link>
          </div>
        </div>
      </AppShell>
    );
  }

  return (
    <AppShell active="practice" title="Papéis na frase">
      <div className="ym-page">
        <h1 className="ym-h1">Papéis na frase</h1>
        <p className="ym-sub">
          Em português o papel de cada parte vem da POSIÇÃO. Em japonês vem da PARTÍCULA — e é por isso
          que a ordem pode mudar sem que a frase mude de sentido. Uma rodada de {ROUND} frases reais do
          banco: aponte a parte que faz o papel pedido.
        </p>
        <p className="ym-muted">
          {sizes.map((s) => (
            <Link key={s.level} to={`/pratica/papeis?nivel=${s.level}`}
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
              <legend className="ym-muted">Questão {i + 1}</legend>
              <p className="ym-jp" lang="ja" style={{ fontSize: "1.3rem" }}>{q.jp}</p>
              <p className="ym-muted">{q.prompt}</p>
              <div className="ym-choices">
                {q.options.map((opt) => (
                  <label key={opt} className="ym-choice">
                    <input type="radio" name={q.key} value={opt} />
                    <span className="ym-jp" lang="ja">{opt}</span>
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
