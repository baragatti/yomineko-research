import { Link, useLoaderData } from "react-router";
import { data } from "react-router";
import { AppShell } from "~/ui/AppShell";
import { Icon } from "~/ui/Icon";
import { getKanji, getVocab, locArr, lessonsUsing, sentencesForKanji } from "~/lib/corpus.server";
import { SentenceCards } from "~/ui/SentenceCards";

export function meta({ data: d }: { data: any }) {
  return [{ title: `Yomineko — ${d?.character ?? "Kanji"}` }];
}

interface Reading { reading: string; okurigana: string | null; common: boolean; level: string | null }

export async function loader({ params }: { params: { char: string } }) {
  const k = getKanji(params.char);
  if (!k) throw data("Kanji não encontrado", { status: 404 });

  const readings = (k.readings || []) as any[];
  const grp = (type: string): Reading[] =>
    readings
      .filter((r) => r.type === type)
      .map((r) => ({ reading: r.reading, okurigana: r.okurigana ?? null, common: !!r.common, level: r.introduced_at_level ?? null }))
      // readings taught in the course first
      .sort((a, b) => (a.level ? 0 : 1) - (b.level ? 0 : 1));

  return {
    character: k.character,
    level: k.level,
    strokes: k.strokes,
    grade: k.grade ?? null,
    freqRank: k.freq_rank ?? null,
    radical: k.kangxi_radical ?? null,
    levelAgreement: k.level_agreement ?? null,
    components: (k.components || []).filter((c: string) => c !== k.character),
    meanings: locArr(k.meanings),
    notes: locArr(k.notes),
    kun: grp("kun"),
    on: grp("on"),
    nanori: grp("nanori"),
    examples: (k.example_words || []).slice(0, 16).map((w: any) => ({
      headword: w.headword,
      kana: w.kana,
      gloss: locArr(w.gloss)[0] ?? "",
      hasEntry: !!getVocab(w.headword),
    })),
    sentences: sentencesForKanji(k.character, 5),
    lessons: lessonsUsing("kanji", k.character),
  };
}

function ReadingRow({ label, items }: { label: string; items: Reading[] }) {
  if (!items.length) return null;
  return (
    <div className="ym-reading-row">
      <span className="ym-reading-label">{label}</span>
      <div className="ym-reading-list">
        {items.map((r, i) => (
          <span key={i} className={`ym-reading${r.level ? " is-level" : ""}`} lang="ja" title={r.level ? r.level.toUpperCase() : undefined}>
            <span className="ym-reading-main">{r.reading}</span>
            {r.okurigana && <span className="ym-reading-oku">{r.okurigana}</span>}
          </span>
        ))}
      </div>
    </div>
  );
}

export default function KanjiDetail() {
  const k = useLoaderData<typeof loader>();
  return (
    <AppShell active="kanji" title={k.character} back="/kanji">
      <div className="ym-page">
        <nav className="ym-breadcrumb" aria-label="Trilha">
          <Link to="/kanji">Kanji</Link> <Icon name="chevron_right" size={14} /> <span>{k.level.toUpperCase()}</span>
        </nav>

        <div className="ym-kanji-hero ym-card-soft">
          <div className="ym-kanji-hero-char" lang="ja" aria-hidden="true">{k.character}</div>
          <div className="ym-kanji-hero-meta">
            <h1 className="ym-kanji-hero-meaning">{k.meanings.join(" · ")}</h1>
            <div className="ym-pill-row">
              <span className="ym-pill ym-pill-level">{k.level.toUpperCase()}</span>
              <span className="ym-pill">{k.strokes} traços</span>
              {k.grade != null && <span className="ym-pill">grau {k.grade}</span>}
              {k.freqRank != null && <span className="ym-pill">freq. #{k.freqRank}</span>}
              {k.components.length > 0 && <span className="ym-pill" lang="ja">partes: {k.components.join(" ")}</span>}
            </div>
          </div>
        </div>

        {k.notes.length > 0 && (
          <div className="ym-note ym-note-tip" style={{ marginBottom: 4 }}>
            <div className="ym-note-head"><Icon name="lightbulb" size={18} /><span>Dica de memorização</span></div>
            <div className="ym-note-body">{k.notes.map((n: string, i: number) => <p key={i} className="ym-p" style={{ margin: 0 }}>{n}</p>)}</div>
          </div>
        )}

        <h2 className="ym-section-title">Leituras</h2>
        <div className="ym-card-plain">
          <ReadingRow label="kun" items={k.kun} />
          <ReadingRow label="on" items={k.on} />
          {k.nanori.length > 0 && (
            <details className="ym-more ym-reading-more">
              <summary>Leituras de nome (nanori) · {k.nanori.length}</summary>
              <div className="ym-reading-list" style={{ marginTop: 8 }}>
                {k.nanori.map((r, i) => (
                  <span key={i} className="ym-reading" lang="ja"><span className="ym-reading-main">{r.reading}</span></span>
                ))}
              </div>
            </details>
          )}
          <p className="ym-reading-note"><span className="ym-reading is-level"><span className="ym-reading-main">あ</span></span> = leitura ensinada no curso</p>
        </div>

        {k.sentences.length > 0 && (
          <>
            <h2 className="ym-section-title">Frases de exemplo</h2>
            <SentenceCards items={k.sentences} />
          </>
        )}

        {k.examples.length > 0 && (
          <>
            <h2 className="ym-section-title">Palavras de exemplo</h2>
            <div className="ym-grid ym-grid-2">
              {k.examples.map((w: { headword: string; kana: string; gloss: string; hasEntry: boolean }, i: number) => {
                const inner = (
                  <>
                    <ruby className="ym-vocab-hw" lang="ja">{w.headword}<rt>{w.kana}</rt></ruby>
                    <div className="ym-vocab-gloss">{w.gloss}</div>
                  </>
                );
                return w.hasEntry ? (
                  <Link key={i} to={`/vocabulario/${encodeURIComponent(w.headword)}`} className="ym-vocab-row">{inner}</Link>
                ) : (
                  <div key={i} className="ym-vocab-row is-static">{inner}</div>
                );
              })}
            </div>
          </>
        )}

        {k.lessons.length > 0 && (
          <>
            <h2 className="ym-section-title">Aparece em {k.lessons.length} {k.lessons.length === 1 ? "lição" : "lições"}</h2>
            <div className="ym-cards">
              {k.lessons.map((ls) => (
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
