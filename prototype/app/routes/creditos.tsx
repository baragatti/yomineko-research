import { AppShell } from "~/ui/AppShell";

export function meta() {
  return [{ title: "Yomineko — Créditos e licenças" }];
}

interface Credit { name: string; what: string; license: string; holder: string; url?: string }
interface Group { title: string; note?: string; items: Credit[] }

const GROUPS: Group[] = [
  {
    title: "Dados linguísticos (fatos)",
    note: "Leituras, classes gramaticais, radicais e a decomposição em partes são fatos, usados com crédito. " +
      "Os significados e traduções são de autoria própria — não reproduzem o texto destes dicionários.",
    items: [
      { name: "JMdict · KANJIDIC2 · KRADFILE/RADKFILE", what: "leituras, POS, radicais e decomposição (fatos)",
        license: "© EDRDG — usado em conformidade com a licença do grupo",
        holder: "Electronic Dictionary Research and Development Group, Monash University",
        url: "https://www.edrdg.org/edrdg/licence.html" },
      { name: "Unicode Unihan", what: "radical Kangxi de cada kanji",
        license: "Unicode License (permissiva)", holder: "© Unicode, Inc.",
        url: "https://www.unicode.org/copyright.html" },
    ],
  },
  {
    title: "Ordem dos traços",
    items: [
      { name: "Kanji alive", what: "ordem de traços dos kanji", license: "CC BY 4.0",
        holder: "© Kanji alive", url: "https://kanjialive.com" },
      { name: "strokesvg · fonte Klee One", what: "ordem de traços do hiragana e katakana",
        license: "código MIT · glifos sob SIL Open Font License (OFL)",
        holder: "© Kyle (strokesvg); fonte Klee One © Fontworks Inc.",
        url: "https://github.com/zhengkyl/strokesvg" },
    ],
  },
  {
    title: "Frases de exemplo",
    items: [
      { name: "Tatoeba", what: "frases de exemplo em japonês", license: "CC BY 2.0 FR",
        holder: "© contribuidores do Projeto Tatoeba", url: "https://tatoeba.org" },
      { name: "JEC Basic Sentence Data", what: "frases básicas de exemplo", license: "CC BY 3.0",
        holder: "© Kurohashi-Kawahara Lab (Univ. de Kyoto) + NICT MASTAR",
        url: "https://nlp.ist.i.kyoto-u.ac.jp/EN/" },
    ],
  },
  {
    title: "Pronúncia e níveis",
    items: [
      { name: "kanjium", what: "acento tonal (pitch accent)", license: "CC BY-SA 4.0",
        holder: "© contribuidores do projeto kanjium", url: "https://github.com/mifunetoshiro/kanjium" },
      { name: "Listas JLPT da comunidade", what: "tags de nível N5–N1 (consenso de ≥3 listas)",
        license: "majoritariamente MIT", holder: "vários projetos open-source" },
    ],
  },
  {
    title: "Ferramentas",
    items: [
      { name: "SudachiPy · SudachiDict", what: "análise morfológica", license: "Apache-2.0",
        holder: "© Works Applications" },
      { name: "jaconv · jmdict-simplified", what: "conversão de kana/romaji e de dados", license: "MIT",
        holder: "© seus autores" },
    ],
  },
];

export default function Creditos() {
  return (
    <AppShell active="creditos" title="Créditos" back="/perfil">
      <div className="ym-page">
        <h1 className="ym-h1">Créditos e licenças</h1>
        <p className="ym-sub">
          O Yomineko se apoia em dados abertos e ferramentas livres. Os significados, traduções, explicações e
          lições são de autoria própria; os recursos abaixo fornecem <em>fatos</em> (leituras, traços, frases
          reais) sob suas respectivas licenças, sempre com o devido crédito.
        </p>
        {GROUPS.map((g) => (
          <section key={g.title} className="ym-credits-group">
            <h2 className="ym-section-title">{g.title}</h2>
            {g.note && <p className="ym-credits-note">{g.note}</p>}
            <div className="ym-cards">
              {g.items.map((c) => (
                <div key={c.name} className="ym-credit">
                  <div className="ym-credit-top">
                    <span className="ym-credit-name">{c.name}</span>
                    <span className="ym-credit-lic">{c.license}</span>
                  </div>
                  <div className="ym-credit-what">{c.what}</div>
                  <div className="ym-credit-holder">
                    {c.holder}
                    {c.url && <> · <a href={c.url} target="_blank" rel="noreferrer noopener" className="ym-credit-link">{c.url.replace(/^https?:\/\//, "")}</a></>}
                  </div>
                </div>
              ))}
            </div>
          </section>
        ))}
      </div>
    </AppShell>
  );
}
