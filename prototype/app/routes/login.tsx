import { Link } from "react-router";
import { Icon } from "~/ui/Icon";
import { StarField, Yomineko, YominekoLogo } from "~/ui/yomineko/mascot";

export function meta() {
  return [{ title: "Yomineko — Entrar" }];
}

const FEATURES = [
  { ic: "auto_stories", t: "Curso linear", d: "Módulo, tópico e lição. Avance no seu ritmo, com o caminho sempre claro." },
  { ic: "style", t: "Revisão inteligente", d: "Suas lições viram cartões e a revisão agenda só o que você precisa rever." },
  { ic: "target", t: "Seis práticas", d: "Hiragana, katakana, partículas, frases, conjugação e números." },
];

export default function Login() {
  return (
    <div className="ym ym-public" data-theme="light">
      <header className="ym-public-top">
        <div className="ym-public-brand">
          <YominekoLogo size={34} />
          <span>Yomineko</span>
        </div>
        <Link to="/" className="btn btn-filled">Entrar</Link>
      </header>

      <section className="ym-public-hero">
        <StarField><div className="ym-public-hero-bg" /></StarField>
        <div className="ym-public-hero-grid">
          <div className="ym-public-hero-copy">
            <span className="ym-pill ym-pill-primary"><Icon name="auto_awesome" size={15} /> N5 → N4 · em português</span>
            <h1 className="ym-public-h1">Aprenda japonês com um gato mágico.</h1>
            <p className="ym-public-lead">
              Yomineko te guia do zero ao N4 com um curso linear, revisão inteligente e prática.
              Conteúdo real do corpus de pesquisa, em português.
            </p>
            <div className="ym-public-cta">
              <Link to="/" className="btn btn-filled btn-lg">Começar agora <Icon name="arrow_forward" size={20} /></Link>
              <Link to="/curso" className="btn btn-tonal btn-lg">Ver o curso</Link>
            </div>
          </div>
          <div className="ym-public-hero-art">
            <Yomineko pose="reading" size={280} />
          </div>
        </div>
      </section>

      <section className="ym-public-features">
        {FEATURES.map((f) => (
          <div key={f.t} className="ym-tile">
            <div className="ym-public-feat-ic"><Icon name={f.ic} size={26} /></div>
            <div className="ym-tile-title" style={{ marginTop: 12 }}>{f.t}</div>
            <div className="ym-tile-sub" style={{ marginTop: 4 }}>{f.d}</div>
          </div>
        ))}
      </section>

      <footer className="ym-public-footer">
        Protótipo de pesquisa · conteúdo não público · noindex
      </footer>
    </div>
  );
}
