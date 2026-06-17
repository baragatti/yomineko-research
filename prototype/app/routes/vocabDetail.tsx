import { Link, useLoaderData } from "react-router";
import { data } from "react-router";
import { AppShell } from "~/ui/AppShell";
import { Icon } from "~/ui/Icon";
import { getVocab, getKanji, locArr } from "~/lib/corpus.server";

export function meta({ data: d }: { data: any }) {
  return [{ title: `Yomineko — ${d?.headword ?? "Vocabulário"}` }];
}

export async function loader({ params }: { params: { headword: string } }) {
  const v = getVocab(params.headword);
  if (!v) throw data("Palavra não encontrada", { status: 404 });

  // kanji in the headword that we have entries for
  const kanjiLinks = Array.from(new Set([...(v.headword as string)]))
    .filter((ch) => getKanji(ch))
    .map((ch) => ch);

  return {
    headword: v.headword,
    kana: v.kana,
    romaji: v.romaji,
    level: v.level,
    register: v.register ?? null,
    senses: (v.senses || []).map((s: any) => ({
      pos: s.pos || [],
      gloss: locArr(s.gloss),
      register: s.register ?? null,
    })),
    kanjiLinks,
  };
}

export default function VocabDetail() {
  const v = useLoaderData<typeof loader>();
  return (
    <AppShell active="vocab" title={v.headword} back="/vocabulario">
      <div className="ym-page">
        <div className="ym-breadcrumb">
          <Link to="/vocabulario">Vocabulário</Link> <Icon name="chevron_right" size={14} /> <span>{v.level.toUpperCase()}</span>
        </div>

        <div className="ym-vocab-hero">
          <ruby className="ym-vocab-hero-hw">{v.headword}<rt>{v.kana}</rt></ruby>
          <div className="ym-vocab-hero-romaji">{v.romaji}</div>
          <div style={{ display: "flex", gap: 8, marginTop: 6, flexWrap: "wrap" }}>
            <span className="ym-pill">{v.level.toUpperCase()}</span>
            {v.register && <span className="ym-pill">{v.register}</span>}
          </div>
        </div>

        <div className="ym-section-title">Significados</div>
        <ol className="ym-sense-list">
          {v.senses.map((s, i) => (
            <li key={i} className="ym-sense">
              {s.pos.length > 0 && (
                <div className="ym-sense-pos">
                  {s.pos.map((p: string) => <span key={p} className="ym-tag">{p}</span>)}
                  {s.register && <span className="ym-tag">{s.register}</span>}
                </div>
              )}
              <div className="ym-sense-gloss">{s.gloss.join("; ")}</div>
            </li>
          ))}
        </ol>

        {v.kanjiLinks.length > 0 && (
          <>
            <div className="ym-section-title">Kanji</div>
            <div style={{ display: "flex", gap: 10, flexWrap: "wrap" }}>
              {v.kanjiLinks.map((ch) => (
                <Link key={ch} to={`/kanji/${encodeURIComponent(ch)}`} className="ym-kanji-mini">{ch}</Link>
              ))}
            </div>
          </>
        )}
      </div>
    </AppShell>
  );
}
