import { Link, useLoaderData } from "react-router";
import { data } from "react-router";
import type { ReactNode } from "react";
import { AppShell } from "~/ui/AppShell";
import { Icon } from "~/ui/Icon";
import { getGrammar, loc, lessonsUsing } from "~/lib/corpus.server";

export function meta({ data: d }: { data: any }) {
  return [{ title: `Yomineko — ${d?.label ?? "Gramática"}` }];
}

export async function loader({ params }: { params: { key: string } }) {
  const g = getGrammar(params.key);
  if (!g) throw data("Ponto gramatical não encontrado", { status: 404 });

  const related = (g.related || [])
    .map((r: any) => {
      const k = typeof r === "string" ? r : r.key;
      const rg = getGrammar(k);
      return rg ? { key: k, label: loc(rg.label) } : null;
    })
    .filter(Boolean);

  return {
    key: g.key,
    label: loc(g.label),
    pattern: g.structure_pattern ?? "",
    level: g.level,
    register: g.register || [],
    forms: (g.forms || []).map((f: any) => ({ form: f.form, meaning: loc(f.meaning) })),
    explanation: loc(g.explanation),
    formation: loc(g.formation),
    nuance: loc(g.nuance),
    caution: loc(g.caution),
    related,
    lessons: lessonsUsing("grammar", g.key),
  };
}

// runs of Japanese script inside pt-BR prose -> set apart (JP font + subtle tint), matching the lesson body.
const CJK = /[぀-ヿ㐀-鿿々〆ーｦ-ﾟ]+/;
function withJa(text: string): ReactNode[] {
  return text
    .split(/([぀-ヿ㐀-鿿々〆ーｦ-ﾟ]+)/)
    .filter(Boolean)
    .map((part, i) => (CJK.test(part) ? <span key={i} className="ym-ja" lang="ja">{part}</span> : <span key={i}>{part}</span>));
}

function Block({ icon, title, text }: { icon: string; title: string; text: string }) {
  if (!text) return null;
  return (
    <div className="ym-gblock">
      <div className="ym-gblock-head"><Icon name={icon} size={18} /><span>{title}</span></div>
      <p className="ym-gblock-text">{withJa(text)}</p>
    </div>
  );
}

export default function GrammarDetail() {
  const g = useLoaderData<typeof loader>();
  return (
    <AppShell active="study" title={g.label} back="/gramatica">
      <div className="ym-page">
        <nav className="ym-breadcrumb" aria-label="Trilha">
          <Link to="/gramatica">Gramática</Link> <Icon name="chevron_right" size={14} /> <span>{g.level.toUpperCase()}</span>
        </nav>

        <div className="ym-grammar-hero ym-card-soft">
          <h1 className="ym-grammar-hero-title">{withJa(g.label)}</h1>
          {g.pattern && <div className="ym-grammar-pattern" lang="ja">{g.pattern}</div>}
          {g.register.length > 0 && (
            <div className="ym-pill-row">
              {g.register.map((r: string) => <span key={r} className="ym-pill">{r}</span>)}
            </div>
          )}
        </div>

        {g.forms.length > 0 && (
          <>
            <h2 className="ym-section-title">Formas</h2>
            <div className="ym-card-plain">
              {g.forms.map((f, i) => (
                <div key={i} className="ym-form-row">
                  <span className="ym-form-jp" lang="ja">{f.form}</span>
                  <span className="ym-form-meaning">{withJa(f.meaning)}</span>
                </div>
              ))}
            </div>
          </>
        )}

        <h2 className="ym-section-title">Explicação</h2>
        <div className="ym-prose">
          <Block icon="lightbulb" title="Como funciona" text={g.explanation} />
          <Block icon="build" title="Formação" text={g.formation} />
          <Block icon="psychology" title="Nuance" text={g.nuance} />
          <Block icon="warning" title="Atenção" text={g.caution} />
        </div>

        {g.related.length > 0 && (
          <>
            <h2 className="ym-section-title">Relacionados</h2>
            <div className="ym-chip-row">
              {g.related.map((r: any) => (
                <Link key={r.key} to={`/gramatica/${encodeURIComponent(r.key)}`} className="ym-pill ym-pill-link">{withJa(r.label)}</Link>
              ))}
            </div>
          </>
        )}

        {g.lessons.length > 0 && (
          <>
            <h2 className="ym-section-title">Aparece em {g.lessons.length} {g.lessons.length === 1 ? "lição" : "lições"}</h2>
            <div className="ym-cards">
              {g.lessons.map((ls) => (
                <Link key={ls.id} to={`/licao/${encodeURIComponent(ls.id)}`} className="ym-linkrow">
                  <Icon name="play_circle" size={20} color="var(--primary)" />
                  <span>{ls.title}</span>
                  <Icon name="chevron_right" size={18} color="var(--on-surface-variant)" />
                </Link>
              ))}
            </div>
          </>
        )}
      </div>
    </AppShell>
  );
}
