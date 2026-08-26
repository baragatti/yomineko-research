import { useEffect, useRef, useState } from "react";
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

function mmss(sec: number): string {
  const s = Math.max(0, sec);
  return `${String(Math.floor(s / 60)).padStart(2, "0")}:${String(s % 60).padStart(2, "0")}`;
}

/**
 * 並べ替え, built on the app's existing sentence-assembly component (`.ym-build-*`) with numbered slots
 * added, because the real 大問 is about ORDER and `.ym-build-answer` alone is a free-flowing row with
 * no positions in it.
 *
 * What it does NOT reuse is that component's answer contract. The lesson version carries the correct
 * string in `data-correct` on `.ym-build` so it can mark itself right or wrong on the spot; an exam
 * cannot ship its key to the client. So this shares the tokens and the bank, and the assembled string
 * rides in a hidden input to be graded server-side.
 */
function OrderQuestion({ name, pieces }: { name: string; pieces: string[] }) {
  const [slots, setSlots] = useState<(number | null)[]>(() => pieces.map(() => null));
  const used = new Set(slots.filter((x): x is number => x !== null));
  const sentence = slots.every((x) => x !== null)
    ? slots.map((i) => pieces[i as number]).join("")
    : "";

  // Functional updates, not `slots.slice()` off the render's snapshot. React batches, so two clicks
  // landing in the same tick both computed from the SAME stale array and the second overwrote the
  // first -- placing three blocks quickly left one on the board. `prev` is always the live value.
  function place(i: number) {
    setSlots((prev) => {
      const at = prev.indexOf(null);
      if (at === -1 || prev.includes(i)) return prev;
      const next = prev.slice();
      next[at] = i;
      return next;
    });
  }
  function clear(at: number) {
    setSlots((prev) => {
      const next = prev.slice();
      next[at] = null;
      return next;
    });
  }

  return (
    <>
      <input type="hidden" name={name} value={sentence} />
      <div className="ym-build">
        <div className="ym-build-slots">
          {slots.map((pi, at) => (
            <button
              key={at}
              type="button"
              className={`ym-build-slot${pi === null ? "" : " is-filled"}`}
              onClick={() => pi !== null && clear(at)}
              aria-label={pi === null
                ? `Posição ${at + 1}, vazia`
                : `Posição ${at + 1}: ${pieces[pi]}. Clique para remover.`}
            >
              <span className="ym-build-slot-n">{at + 1}</span>
              <span lang="ja">{pi === null ? "" : pieces[pi]}</span>
            </button>
          ))}
        </div>

        <div className="ym-build-bank">
          {pieces.map((p, i) => (
            <button
              key={`${p}-${i}`}
              type="button"
              className="ym-build-tok"
              lang="ja"
              disabled={used.has(i)}
              onClick={() => place(i)}
            >
              {p}
            </button>
          ))}
        </div>

        <p className="ym-build-preview">
          {sentence
            ? <span className="ym-jp">{sentence}</span>
            : <span className="ym-muted">Coloque cada bloco na posição certa, de 1 a {pieces.length}.</span>}
          {used.size > 0 && (
            <button type="button" className="ym-btn-text"
                    onClick={() => setSlots(pieces.map(() => null))}>
              <Icon name="undo" size={16} /> limpar
            </button>
          )}
        </p>
      </div>
    </>
  );
}

export default function ExamPaper() {
  const { paper, seed } = useLoaderData<typeof loader>();
  const graded = useActionData<typeof action>();
  const nav = useNavigation();
  const result = graded?.result;
  const busy = nav.state !== "idle";

  const formRef = useRef<HTMLFormElement>(null);
  // "part" -> answering; "break" -> the changeover between parts; "sending" -> the paper is in flight.
  const [phase, setPhase] = useState<"part" | "break" | "sending">("part");
  const [partIx, setPartIx] = useState(0);
  const [left, setLeft] = useState(() => (paper.parts[0]?.minutes ?? 0) * 60);
  const part = paper.parts[partIx];
  const isLast = partIx >= paper.parts.length - 1;

  /**
   * One interval drives both the part clock and the break clock. When a part's clock reaches zero the
   * learner does NOT get to finish it: the real exam collects that booklet, so we move on and the part
   * is gone. Its answers survive because every part stays mounted in the form (see below) — leaving a
   * part hides it, it does not discard it.
   */
  useEffect(() => {
    if (phase === "sending") return;
    const t = setInterval(() => setLeft((v) => v - 1), 1000);
    return () => clearInterval(t);
  }, [phase, partIx]);

  useEffect(() => {
    if (left > 0 || phase === "sending") return;
    if (phase === "part") {
      if (isLast) { setPhase("sending"); formRef.current?.requestSubmit(); }
      else { setPhase("break"); setLeft(paper.parts[partIx].gapAfter * 60); }
    } else if (phase === "break") {
      startNextPart();
    }
  }, [left, phase]);

  function startNextPart() {
    const next = partIx + 1;
    setPartIx(next);
    setLeft((paper.parts[next]?.minutes ?? 0) * 60);
    setPhase("part");
    window.scrollTo({ top: 0 });
  }
  function endPart() {
    if (isLast) { setPhase("sending"); formRef.current?.requestSubmit(); return; }
    setPhase("break");
    setLeft(part.gapAfter * 60);
    window.scrollTo({ top: 0 });
  }

  if (result) {
    return (
      <AppShell active="exam" title="Resultado" back="/simulado">
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

  const low = phase === "part" && left <= 60;

  return (
    <AppShell active="exam" title={`Simulado ${paper.level.toUpperCase()}`}>
      <div className="ym-exam">
        <div className={`ym-exam-bar${low ? " is-low" : ""}`}>
          <div className="ym-exam-bar-l">
            <span className="ym-pill ym-pill-gold">{paper.level.toUpperCase()}</span>
            <div>
              <div className="ym-sess-count">Parte {partIx + 1} de {paper.parts.length}</div>
              <div className="ym-jp">{part.jp}</div>
            </div>
          </div>
          <div className="ym-exam-clock" role="timer" aria-live="off">
            <Icon name={phase === "break" ? "hourglass_top" : "schedule"} size={20} />
            {mmss(left)}
          </div>
        </div>

        {phase === "break" && (
          <div className="ym-exam-break">
            <Icon name="free_breakfast" size={40} />
            <h2 className="ym-h2">Intervalo</h2>
            <p className="ym-sub">
              A parte {partIx + 1} foi entregue e não pode mais ser alterada.
            </p>
            <p className="ym-sub">{paper.gapNote}</p>
            <p>
              A seguir: <strong>{paper.parts[partIx + 1]?.label}</strong>{" "}
              <span className="ym-muted">
                ({paper.parts[partIx + 1]?.total} questões · {paper.parts[partIx + 1]?.minutes} min)
              </span>
            </p>
            <button type="button" className="ym-btn ym-btn-primary" onClick={startNextPart}>
              <Icon name="skip_next" /> Pular o intervalo e começar
            </button>
            <p className="ym-muted" style={{ marginTop: 10 }}>
              Ou espere: a próxima parte começa sozinha em {mmss(left)}.
            </p>
          </div>
        )}

        <Form method="post" ref={formRef} hidden={phase === "break"}>
          <input type="hidden" name="seed" value={seed} />

          {/*
            EVERY part stays mounted; only the current one is shown. Unmounting a finished part would
            unmount its inputs, and unmounted inputs do not post — the learner's earlier answers would
            be silently dropped at submit. Hiding keeps them in the form while making them unreachable.
          */}
          {paper.parts.map((pt, i) => (
            <div key={pt.key} hidden={i !== partIx || phase !== "part"}>
              <header>
                <h1 className="ym-h1">{pt.label}</h1>
                <p className="ym-sub">
                  {pt.total} questões · {pt.minutes} minutos · prova nº {paper.seed}
                </p>
              </header>

              {pt.sections.map((sec) => (
                <section key={sec.type} className="ym-exam-sec">
                  <header className="ym-exam-sec-h">
                    <span className="ym-jp">{sec.jp}</span>
                    <strong className="ym-tile-title">{sec.label}</strong>
                    <span className="ym-muted">
                      questões {sec.from}–{sec.from + sec.questions.length - 1}
                    </span>
                  </header>
                  <p className="ym-sub">{sec.hint}</p>

                  {sec.questions.map((q, qi) => (
                    <fieldset key={q.key} className="ym-q">
                      <legend className="ym-seg-n">{sec.from + qi}</legend>
                      {q.passage && <p className="ym-jp ym-passage">{q.passage}</p>}
                      {q.prompt && <p className="ym-q-stem ym-jp">{q.prompt}</p>}
                      {q.focus && !q.prompt.includes(`「${q.focus}」`) && (
                        <p className="ym-muted">
                          Palavra em foco: <strong className="ym-jp">{q.focus}</strong>
                        </p>
                      )}

                      {q.pieces ? (
                        <OrderQuestion name={`q:${q.key}`} pieces={q.pieces} />
                      ) : (
                        /* The lesson component with NO data-correct: it inherits the pill and the
                           neutral selected state, and ships no answer key. `is-stacked` because exam
                           options run to whole sentences. */
                        <fieldset className="ym-ex-choices is-stacked">
                          <legend className="ym-sr-only">Escolha a resposta</legend>
                          {q.options.map((opt, oi) => (
                            <label key={opt} className="ym-ex-choice">
                              <input type="radio" name={`q:${q.key}`} value={opt} />
                              <span className="ym-ex-choice-n">{oi + 1}</span>
                              <span lang="ja">{opt}</span>
                            </label>
                          ))}
                        </fieldset>
                      )}
                    </fieldset>
                  ))}
                </section>
              ))}

              {/* `i`, not the outer partIx: every part renders its own footer, so asking whether the
                  CURRENT part is last labelled part 2's button "Terminar a parte 2" while part 1 was
                  on screen. The last part submits; the others hand over. */}
              <div className="ym-exam-foot">
                <button type="button" className="ym-btn ym-btn-primary" onClick={endPart} disabled={busy}>
                  {i === paper.parts.length - 1
                    ? <><Icon name="done_all" /> {busy ? "Corrigindo…" : "Entregar a prova"}</>
                    : <><Icon name="arrow_forward" /> Terminar a parte {i + 1}</>}
                </button>
                <p className="ym-muted">
                  {i === paper.parts.length - 1
                    ? "Ao entregar, a prova é corrigida e você vê a revisão questão a questão."
                    : "Depois de terminar, esta parte não pode mais ser alterada."}
                </p>
              </div>
            </div>
          ))}
        </Form>
      </div>
    </AppShell>
  );
}
