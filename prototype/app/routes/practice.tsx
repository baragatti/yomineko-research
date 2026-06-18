import { AppShell } from "~/ui/AppShell";
import { Icon } from "~/ui/Icon";

export function meta() {
  return [{ title: "Yomineko — Prática" }];
}

// The six practice modes (mockup of the practice hub). These are app features, not corpus rows.
interface PracticeMode { jp: string; t: string; d: string; ic: string; badge?: string }
const PRACTICES: PracticeMode[] = [
  { jp: "ひらがな", t: "Hiragana", d: "Reconhecer os 46 kana e variações.", ic: "abc", badge: "hoje" },
  { jp: "カタカナ", t: "Katakana", d: "Estrangeirismos e ênfase.", ic: "abc" },
  { jp: "は が を に", t: "Partículas", d: "A partícula certa na lacuna.", ic: "link" },
  { jp: "わたしは…", t: "Construir frases", d: "Montar a partir dos blocos.", ic: "reorder" },
  { jp: "食べる → て", t: "Conjugação", d: "Forma て, た, ない e outras.", ic: "swap_calls" },
  { jp: "1 2 3 / 人", t: "Números", d: "Cardinais e contadores.", ic: "tag" },
];

export default function Practice() {
  return (
    <AppShell active="practice" title="Prática">
      <div className="ym-page-wide">
        <h1 className="ym-h1">Prática</h1>
        <p className="ym-sub">
          Você escolhe a habilidade; o conteúdo vem das suas lições. <span className="ym-pill ym-pill-gold">demonstração</span>
        </p>

        <div className="ym-grid" style={{ gridTemplateColumns: "repeat(auto-fill, minmax(260px,1fr))" }}>
          {PRACTICES.map((p) => (
            <button key={p.t} type="button" className="ym-practice-tile">
              {p.badge && <span className="ym-pill ym-pill-gold ym-practice-badge">{p.badge}</span>}
              <div className="ym-practice-ic"><Icon name={p.ic} size={24} /></div>
              <div className="ym-practice-jp" lang="ja">{p.jp}</div>
              <div className="ym-tile-title">{p.t}</div>
              <div className="ym-tile-sub">{p.d}</div>
            </button>
          ))}
        </div>
        <p className="ym-rev-foot">Protótipo: os modos de prática são uma demonstração da interface.</p>
      </div>
    </AppShell>
  );
}
