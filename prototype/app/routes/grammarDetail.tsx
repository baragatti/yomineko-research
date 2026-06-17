import { Link, useLoaderData } from "react-router";
import { data } from "react-router";
import { AppShell } from "~/ui/AppShell";
import { Icon } from "~/ui/Icon";
import { getGrammar, loc } from "~/lib/corpus.server";

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
  };
}

function Block({ icon, title, text }: { icon: string; title: string; text: string }) {
  if (!text) return null;
  return (
    <div className="ym-gblock">
      <div className="ym-gblock-head"><Icon name={icon} size={18} /><span>{title}</span></div>
      <p className="ym-gblock-text">{text}</p>
    </div>
  );
}

export default function GrammarDetail() {
  const g = useLoaderData<typeof loader>();
  return (
    <AppShell active="study" title={g.label} back="/gramatica">
      <div className="ym-page">
        <div className="ym-breadcrumb">
          <Link to="/gramatica">Gramática</Link> <Icon name="chevron_right" size={14} /> <span>{g.level.toUpperCase()}</span>
        </div>

        <h1 className="ym-h1">{g.label}</h1>
        {g.pattern && <div className="ym-grammar-pattern ym-grammar-pattern-hero">{g.pattern}</div>}
        {g.register.length > 0 && (
          <div style={{ display: "flex", gap: 8, marginTop: 8, flexWrap: "wrap" }}>
            {g.register.map((r: string) => <span key={r} className="ym-pill">{r}</span>)}
          </div>
        )}

        {g.forms.length > 0 && (
          <>
            <div className="ym-section-title">Formas</div>
            <div className="ym-card-plain">
              {g.forms.map((f, i) => (
                <div key={i} className="ym-form-row">
                  <span className="ym-form-jp">{f.form}</span>
                  <span className="ym-form-meaning">{f.meaning}</span>
                </div>
              ))}
            </div>
          </>
        )}

        <div className="ym-section-title">Explicação</div>
        <div className="ym-prose">
          <Block icon="lightbulb" title="Como funciona" text={g.explanation} />
          <Block icon="build" title="Formação" text={g.formation} />
          <Block icon="psychology" title="Nuance" text={g.nuance} />
          <Block icon="warning" title="Atenção" text={g.caution} />
        </div>

        {g.related.length > 0 && (
          <>
            <div className="ym-section-title">Relacionados</div>
            <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
              {g.related.map((r: any) => (
                <Link key={r.key} to={`/gramatica/${encodeURIComponent(r.key)}`} className="ym-pill ym-pill-link">{r.label}</Link>
              ))}
            </div>
          </>
        )}
      </div>
    </AppShell>
  );
}
