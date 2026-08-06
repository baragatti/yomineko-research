import { Link, useLoaderData } from "react-router";
import { data } from "react-router";
import { AppShell } from "~/ui/AppShell";
import { Icon } from "~/ui/Icon";
import { getUnit, splitUnitId } from "~/lib/speak.server";

export function meta({ data: d }: { data?: { unit?: { title?: string } } }) {
  return [{ title: `Yomineko — ${d?.unit?.title ?? "Fala Primeiro"}` }];
}

export async function loader({ params }: { params: { stage?: string; unit?: string } }) {
  const unit = getUnit(params.stage ?? "", Number(params.unit ?? 1));
  if (!unit) throw data("Unidade não encontrada", { status: 404 });
  return { unit };
}

function href(id: string): string {
  const { stage, order } = splitUnitId(id);
  return `/falar/${stage}/${order}`;
}

export default function SpeakUnit() {
  const { unit } = useLoaderData<typeof loader>();

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

        <nav style={{ display: "flex", gap: ".75rem", marginTop: "1.25rem" }}>
          {unit.prev && <Link className="ym-btn" to={href(unit.prev)}><Icon name="arrow_back" /> Anterior</Link>}
          {unit.next && <Link className="ym-btn ym-btn-primary" to={href(unit.next)}>Próxima <Icon name="arrow_forward" /></Link>}
        </nav>
      </div>
    </AppShell>
  );
}
