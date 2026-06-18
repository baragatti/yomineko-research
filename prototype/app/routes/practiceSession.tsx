import { Link, useLoaderData } from "react-router";
import { data } from "react-router";
import { AppShell } from "~/ui/AppShell";
import { Icon } from "~/ui/Icon";

export function meta({ data: d }: { data: any }) {
  return [{ title: `Yomineko — ${d?.title ?? "Prática"}` }];
}

interface Choice { text: string; correct?: boolean }
interface ModeMock {
  title: string;
  ic: string;
  promptLabel: string;
  question: string;
  questionLang: "ja" | "pt";
  choices: Choice[];
  answerNote: string;
}

const MODES: Record<string, ModeMock> = {
  hiragana: {
    title: "Hiragana", ic: "abc", promptLabel: "Qual é o som deste hiragana?", question: "あ", questionLang: "ja",
    choices: [{ text: "a", correct: true }, { text: "o" }, { text: "ya" }, { text: "wa" }],
    answerNote: "あ = a. A primeira das cinco vogais.",
  },
  katakana: {
    title: "Katakana", ic: "abc", promptLabel: "Qual é o som deste katakana?", question: "カ", questionLang: "ja",
    choices: [{ text: "ka", correct: true }, { text: "ke" }, { text: "ko" }, { text: "ku" }],
    answerNote: "カ = ka. O katakana costuma aparecer em estrangeirismos.",
  },
  particles: {
    title: "Partículas", ic: "link", promptLabel: "Qual partícula completa a frase?", question: "わたし ＿ がくせいです。", questionLang: "ja",
    choices: [{ text: "は", correct: true }, { text: "を" }, { text: "に" }, { text: "が" }],
    answerNote: "は marca o tópico: 'quanto a mim, sou estudante'.",
  },
  sentence: {
    title: "Construir frases", ic: "reorder", promptLabel: "Qual é a ordem correta de 'Eu sou estudante.'?", question: "わたし · は · がくせい · です", questionLang: "ja",
    choices: [{ text: "わたしはがくせいです", correct: true }, { text: "わたしをがくせいです" }, { text: "がくせいはわたしです" }],
    answerNote: "Tópico (わたしは) + complemento (がくせい) + です no fim.",
  },
  conjugation: {
    title: "Conjugação", ic: "swap_calls", promptLabel: "Qual é a forma て de 食べる?", question: "食べる → ？", questionLang: "ja",
    choices: [{ text: "食べて", correct: true }, { text: "食べた" }, { text: "食べない" }, { text: "食べります" }],
    answerNote: "Verbos ichidan: troca る por て → 食べて.",
  },
  numbers: {
    title: "Números", ic: "tag", promptLabel: "Como se lê o número 7?", question: "7", questionLang: "pt",
    choices: [{ text: "なな", correct: true }, { text: "よん" }, { text: "きゅう" }, { text: "ろく" }],
    answerNote: "7 = なな (nana). Também existe しち (shichi).",
  },
};

export async function loader({ params }: { params: { mode: string } }) {
  const mock = MODES[params.mode];
  if (!mock) throw data("Prática não encontrada", { status: 404 });
  return { mode: params.mode, ...mock };
}

export default function PracticeSession() {
  const m = useLoaderData<typeof loader>();
  return (
    <AppShell active="practice" title={m.title} back="/pratica">
      <div className="ym-page">
        <div className="ym-sess-top">
          <Link to="/pratica" className="icon-btn" aria-label="Sair da prática"><Icon name="close" size={22} /></Link>
          <div className="ym-sess-prog"><i style={{ width: "20%" }} /></div>
          <span className="ym-sess-count">1 / 5</span>
        </div>

        <div className="ym-pill ym-pill-gold" style={{ marginBottom: 14 }}>demonstração</div>

        <div className="ym-ex ym-sess-card">
          <div className="ym-ex-head"><Icon name={m.ic} size={18} /><span>{m.title}</span></div>
          <div className="ym-ex-prompt">{m.promptLabel}</div>
          <div className="ym-sess-q" lang={m.questionLang}>{m.question}</div>
          <fieldset className="ym-ex-choices">
            <legend className="ym-sr-only">Escolha</legend>
            {m.choices.map((c, i) => (
              <label key={i} className="ym-ex-choice">
                <input type="radio" name="psess" data-correct={c.correct ? "true" : "false"} />
                <span lang="ja">{c.text}</span>
              </label>
            ))}
          </fieldset>
          <div className="ym-ex-expl">{m.answerNote}</div>
        </div>

        <div className="ym-sess-actions">
          <button type="button" className="btn btn-filled" disabled>Próxima <Icon name="arrow_forward" size={18} /></button>
        </div>
        <p className="ym-rev-foot">Protótipo: esta sessão de prática é uma demonstração da interface.</p>
      </div>
    </AppShell>
  );
}
