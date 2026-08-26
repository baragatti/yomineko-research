import { Link, useLoaderData } from "react-router";
import { data } from "react-router";
import { AppShell } from "~/ui/AppShell";
import { Icon } from "~/ui/Icon";
import { getKanji, getVocab, locArr, lessonsUsing, sentencesForKanji, kanaToRomaji, getStrokes, getStrokeLines, loc, allVocab } from "~/lib/corpus.server";
import { SentenceCards } from "~/ui/SentenceCards";
import { KanjiStrokes } from "~/ui/KanjiStrokes";
import { vocabHref, idPart } from "~/lib/ids";

export function meta({ data: d }: { data: any }) {
  return [{ title: `Yomineko — ${d?.character ?? "Kanji"}` }];
}

interface Reading { reading: string; okurigana: string | null; romaji: string; common: boolean; level: string | null }

export async function loader({ params }: { params: { char: string } }) {
  const k = getKanji(params.char);
  if (!k) throw data("Kanji não encontrado", { status: 404 });

  const readings = (k.readings || []) as any[];
  const grp = (type: string): Reading[] =>
    readings
      .filter((r) => r.type === type)
      .map((r) => ({ reading: r.reading, okurigana: r.okurigana ?? null, romaji: kanaToRomaji(r.reading + (r.okurigana || "")), common: !!r.common, level: r.introduced_at_level ?? null }))
      // readings taught in the course first
      .sort((a, b) => (a.level ? 0 : 1) - (b.level ? 0 : 1));

  // Per-reading enrichment (roadmap D): keep only readings that carry a note or grouped compounds.
  // 2,218 of the 3,678 notes sit on rare readings with no examples, so listing every reading would
  // bury the handful a learner can act on.
  const vocabById = new Map(allVocab().map((v: any) => [v.id, v]));
  // Require COMPOUNDS, not just a note. Every reading got a note, including the 14 nanori of 日 whose
  // notes correctly say "nenhum vocábulo ficou agrupado nela" — listing those buries ひ and ニチ under
  // a wall of boilerplate. A reading with no example the learner can look at earns no row here.
  const readingDetail = readings
    .filter((r: any) => (r.example_vocab_ids || []).length > 0)
    .map((r: any) => ({
      key: r.reading + (r.okurigana ?? ""),
      reading: r.reading as string,
      okurigana: (r.okurigana ?? null) as string | null,
      type: r.type as string,
      note: r.note ? loc(r.note) : "",
      compounds: ((r.example_vocab_ids || []) as number[])
        .map((id) => vocabById.get(id))
        .filter(Boolean)
        .map((v: any) => ({ headword: v.headword as string, kana: v.kana as string,
                            slug: v.slug as string })),
    }))
    .sort((a, b) => b.compounds.length - a.compounds.length);

  return {
    readingDetail,
    irregularNote: k.irregular_note ? loc(k.irregular_note) : "",
    character: k.character,
    level: k.level,
    strokes: k.strokes,
    grade: k.grade ?? null,
    freqRank: k.freq_rank ?? null,
    radical: k.kangxi_radical ?? null,
    radicalChar: k.radical_char ?? null,
    levelAgreement: k.level_agreement ?? null,
    components: (k.components || []).filter((c: string) => c !== k.character)
      .map((c: string) => ({ c, hasEntry: !!getKanji(c) })),
    strokesData: getStrokes(k.character),
    strokeLines: getStrokeLines(k.character),
    meanings: locArr(k.meanings),
    notes: locArr(k.notes),
    kun: grp("kun"),
    on: grp("on"),
    nanori: grp("nanori"),
    examples: (k.example_words || []).slice(0, 16).map((w: any) => ({
      headword: w.headword,
      kana: w.kana,
      slug: w.slug ?? "",
      gloss: locArr(w.gloss)[0] ?? "",
      // Resolve by slug, not headword — 93 headwords name more than one record.
      hasEntry: !!(w.slug && getVocab(idPart(w.slug))),
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
            {r.romaji && <span className="ym-reading-romaji">{r.romaji}</span>}
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
            </div>
          </div>
        </div>

        {k.notes.length > 0 && (
          <div className="ym-note ym-note-tip" style={{ marginBottom: 4 }}>
            <div className="ym-note-head"><Icon name="lightbulb" size={18} /><span>Dica de memorização</span></div>
            <div className="ym-note-body">{k.notes.map((n: string, i: number) => <p key={i} className="ym-p" style={{ margin: 0 }}>{n}</p>)}</div>
          </div>
        )}

        {(k.strokesData || k.components.length > 0) && (
          <div className="ym-stroke-decomp">
            {(k.strokeLines || k.strokesData) && <KanjiStrokes char={k.character} data={k.strokesData} lines={k.strokeLines} />}
            {k.components.length > 0 && (
              <div className="ym-card-soft ym-decomp">
                <span className="ym-strokes-label">DECOMPOSIÇÃO</span>
                <div className="ym-decomp-parts">
                  {k.components.map((p: { c: string; hasEntry: boolean }, i: number) => p.hasEntry ? (
                    <Link key={i} to={`/kanji/${encodeURIComponent(p.c)}`} className="ym-decomp-part is-link" lang="ja" title="ver este componente">{p.c}</Link>
                  ) : (
                    <span key={i} className="ym-decomp-part" lang="ja">{p.c}</span>
                  ))}
                </div>
                <div className="ym-decomp-hint">
                  peças que compõem este kanji{k.radical != null
                    ? ` · radical ${k.radicalChar ? k.radicalChar + " " : ""}(nº ${k.radical} de 214)`
                    : ""}
                </div>
              </div>
            )}
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
              {k.examples.map((w: { headword: string; kana: string; slug: string; gloss: string; hasEntry: boolean }, i: number) => {
                const inner = (
                  <>
                    <ruby className="ym-vocab-hw" lang="ja">{w.headword}<rt>{w.kana}</rt></ruby>
                    <div className="ym-vocab-gloss">{w.gloss}</div>
                  </>
                );
                return w.hasEntry ? (
                  <Link key={i} to={vocabHref(w.slug)} className="ym-vocab-row">{inner}</Link>
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

        {k.readingDetail.length > 0 && (
          <section className="ym-card" style={{ marginTop: "1rem" }}>
            <header className="ym-card-h"><strong>Cada leitura, e onde ela aparece</strong></header>
            <ul className="ym-list">
              {k.readingDetail.map((r) => (
                <li key={r.key} style={{ marginBottom: ".8rem" }}>
                  <span className="ym-jp" style={{ fontSize: "1.1rem" }}>{r.reading}</span>
                  {r.okurigana && <span className="ym-muted">.{r.okurigana}</span>}{" "}
                  <span className="ym-muted">({r.type})</span>
                  {r.note && <div>{r.note}</div>}
                  {r.compounds.length > 0 && (
                    <div className="ym-muted">
                      {r.compounds.map((c) => (
                        <Link key={c.slug} to={vocabHref(c.slug)}
                              style={{ marginRight: ".7rem" }}>
                          <span className="ym-jp">{c.headword}</span> {c.kana}
                        </Link>
                      ))}
                    </div>
                  )}
                </li>
              ))}
            </ul>
            {k.irregularNote && <p className="ym-muted">{k.irregularNote}</p>}
          </section>
        )}
      </div>
    </AppShell>
  );
}
