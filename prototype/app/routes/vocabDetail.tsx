import { Link, useLoaderData } from "react-router";
import { data } from "react-router";
import { AppShell } from "~/ui/AppShell";
import { Icon } from "~/ui/Icon";
import { getVocab, getKanji, locArr, lessonsUsing, sentencesForVocab } from "~/lib/corpus.server";
import { SentenceCards } from "~/ui/SentenceCards";

export function meta({ data: d }: { data: any }) {
  return [{ title: `Yomineko — ${d?.headword ?? "Vocabulário"}` }];
}

interface Sense { n: number; pos: string[]; gloss: string[]; register: string[] }

const VISIBLE = 6;

export async function loader({ params }: { params: { headword: string } }) {
  const v = getVocab(params.headword);
  if (!v) throw data("Palavra não encontrada", { status: 404 });

  const senses: Sense[] = (v.senses || []).map((s: any, i: number) => ({
    n: i + 1,
    pos: s.pos || [],
    gloss: locArr(s.gloss),
    register: [...(s.register || []), ...(s.field || []), ...(s.misc || [])],
  }));

  // pos is almost always identical across senses — show it once at the top instead of repeating it N times.
  const posSig = (p: string[]) => p.join(",");
  const uniformPos = senses.length > 0 && senses.every((s) => posSig(s.pos) === posSig(senses[0].pos)) ? senses[0].pos : null;

  const kanjiLinks = Array.from(new Set([...(v.headword as string)])).filter((ch) => getKanji(ch));

  return {
    headword: v.headword,
    kana: v.kana,
    romaji: v.romaji,
    level: v.level,
    uniformPos,
    senses,
    kanjiLinks,
    sentences: sentencesForVocab(v.headword, 5),
    lessons: lessonsUsing("vocab", v.headword),
  };
}

function SenseItem({ s, showPos }: { s: Sense; showPos: boolean }) {
  return (
    <li className="ym-sense">
      <span className="ym-sense-n">{s.n}</span>
      <div>
        {(showPos && s.pos.length > 0) || s.register.length > 0 ? (
          <div className="ym-sense-tags">
            {showPos && s.pos.map((p) => <span key={p} className="ym-tag">{p}</span>)}
            {s.register.map((r) => <span key={r} className="ym-tag ym-tag-reg">{r}</span>)}
          </div>
        ) : null}
        <div className="ym-sense-gloss">{s.gloss.join("; ")}</div>
      </div>
    </li>
  );
}

export default function VocabDetail() {
  const v = useLoaderData<typeof loader>();
  const head = v.senses.slice(0, VISIBLE);
  const rest = v.senses.slice(VISIBLE);
  const showPerSensePos = !v.uniformPos;
  return (
    <AppShell active="vocab" title={v.headword} back="/vocabulario">
      <div className="ym-page">
        <nav className="ym-breadcrumb" aria-label="Trilha">
          <Link to="/vocabulario">Vocabulário</Link> <Icon name="chevron_right" size={14} /> <span>{v.level.toUpperCase()}</span>
        </nav>

        <div className="ym-vocab-hero ym-card-soft">
          <h1><ruby className="ym-vocab-hero-hw" lang="ja">{v.headword}<rt>{v.kana}</rt></ruby></h1>
          <div className="ym-vocab-hero-romaji">{v.romaji}</div>
          <div className="ym-pill-row">
            <span className="ym-pill ym-pill-level">{v.level.toUpperCase()}</span>
            {v.uniformPos && v.uniformPos.map((p) => <span key={p} className="ym-pill">{p}</span>)}
          </div>
        </div>

        <h2 className="ym-section-title">{v.senses.length} {v.senses.length === 1 ? "significado" : "significados"}</h2>
        <ol className="ym-sense-list">
          {head.map((s) => <SenseItem key={s.n} s={s} showPos={showPerSensePos} />)}
        </ol>
        {rest.length > 0 && (
          <details className="ym-more">
            <summary>Mostrar mais {rest.length} {rest.length === 1 ? "significado" : "significados"}</summary>
            <ol className="ym-sense-list" start={VISIBLE + 1}>
              {rest.map((s) => <SenseItem key={s.n} s={s} showPos={showPerSensePos} />)}
            </ol>
          </details>
        )}

        {v.sentences.length > 0 && (
          <>
            <h2 className="ym-section-title">Frases de exemplo</h2>
            <SentenceCards items={v.sentences} />
          </>
        )}

        {v.kanjiLinks.length > 0 && (
          <>
            <h2 className="ym-section-title">Kanji</h2>
            <div className="ym-chip-row">
              {v.kanjiLinks.map((ch) => (
                <Link key={ch} to={`/kanji/${encodeURIComponent(ch)}`} className="ym-kanji-mini" lang="ja">{ch}</Link>
              ))}
            </div>
          </>
        )}

        {v.lessons.length > 0 && (
          <>
            <h2 className="ym-section-title">Aparece em {v.lessons.length} {v.lessons.length === 1 ? "lição" : "lições"}</h2>
            <div className="ym-cards">
              {v.lessons.map((ls) => (
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
