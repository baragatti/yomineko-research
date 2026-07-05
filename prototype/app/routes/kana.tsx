import { useState } from "react";
import { useLoaderData } from "react-router";
import { AppShell } from "~/ui/AppShell";
import { KanaStrokes } from "~/ui/KanaStrokes";
import { kanaFamilies, getKanaStrokes } from "~/lib/corpus.server";

export function meta() {
  return [{ title: "Yomineko — Kana (ordem dos traços)" }];
}

interface Cell { char: string; romaji: string; has: boolean }
interface Row { row: string; order: number; label: string; type: string; members: Cell[] }

export async function loader() {
  const fam = kanaFamilies();
  const strokes: Record<string, { viewbox: string; strokes: string[]; shadows?: string[] }> = {};
  const build = (rows: any[]): Row[] =>
    (rows || []).map((r) => ({
      row: r.row, order: r.order ?? 0, label: r.label?.["pt-BR"] ?? r.row, type: r.type ?? "base",
      members: (r.members || []).map((m: any) => {
        // combos (きゃ…) have no single glyph: resolve each COMPONENT char's strokes instead
        const comps = [...(m.char as string)];
        let has = true;
        for (const ch of comps) {
          const s = getKanaStrokes(ch);
          if (s) strokes[ch] = { viewbox: s.viewbox, strokes: s.strokes, shadows: (s as any).shadows ?? undefined };
          else has = false;
        }
        return { char: m.char, romaji: m.romaji, has };
      }),
    }));
  return { hiragana: build(fam.hiragana), katakana: build(fam.katakana), strokes };
}

function Grid({ rows, sel, onSel }: { rows: Row[]; sel: string; onSel: (c: string) => void }) {
  return (
    <div className="ym-kana-grid">
      {rows.map((r) => (
        <div key={r.row} className={`ym-kana-row${r.type !== "base" ? " is-extra" : ""}`}>
          {r.members.map((m) => (
            <button key={m.char} className={`ym-kana-cell${m.char === sel ? " is-sel" : ""}${m.has ? "" : " is-nostroke"}`}
                    onClick={() => onSel(m.char)} aria-pressed={m.char === sel}>
              <span className="ym-kana-cell-char" lang="ja">{m.char}</span>
              <span className="ym-kana-cell-romaji">{m.romaji}</span>
            </button>
          ))}
        </div>
      ))}
    </div>
  );
}

export default function Kana() {
  const d = useLoaderData<typeof loader>();
  const [kind, setKind] = useState<"hiragana" | "katakana">("hiragana");
  const [sel, setSel] = useState("あ");
  const rows = kind === "hiragana" ? d.hiragana : d.katakana;
  // a selection may be a combo (きゃ): compose the component glyphs into ONE canvas (like real text) via
  // per-stroke x-offsets, so the small kana keeps its natural size/position and the pen flows き -> ゃ.
  const selComps = [...sel].map((ch) => ({ ch, data: d.strokes[ch] })).filter((c) => c.data);
  const selOk = selComps.length === [...sel].length && selComps.length > 0;
  const selData: { viewbox: string; strokes: string[]; shadows?: string[]; offsets?: number[] } | null = !selOk ? null
    : selComps.length === 1 ? selComps[0].data
    : {
        viewbox: `0 0 ${1024 * selComps.length} 1024`,
        strokes: selComps.flatMap((c) => c.data.strokes),
        // per-stroke shadows aligned with strokes ('' where a component has none -> unclipped fallback)
        shadows: selComps.flatMap((c) => c.data.shadows ?? c.data.strokes.map(() => "")),
        offsets: selComps.flatMap((c, i) => c.data.strokes.map(() => i * 1024)),
      };
  const selRomaji = rows.flatMap((r) => r.members).find((m) => m.char === sel)?.romaji ?? "";

  return (
    <AppShell active="kana" title="Kana" back="/curso">
      <div className="ym-page">
        <h1 className="ym-h1">Kana — ordem dos traços</h1>
        <p className="ym-sub">Toque em um caractere para ver como escrevê-lo, traço a traço.</p>

        <div className="ym-kana-tabs">
          <button className={`ym-seg${kind === "hiragana" ? " is-on" : ""}`} onClick={() => { setKind("hiragana"); setSel("あ"); }}>Hiragana</button>
          <button className={`ym-seg${kind === "katakana" ? " is-on" : ""}`} onClick={() => { setKind("katakana"); setSel("ア"); }}>Katakana</button>
        </div>

        <div className="ym-kana-layout">
          <div className="ym-kana-stage ym-card-soft">
            {selData ? (
              <>
                <div className="ym-kana-combo">
                  <KanaStrokes char={sel} data={selData} size={selComps.length > 1 ? 300 : 200} />
                </div>
                <div className="ym-kana-stage-meta"><span lang="ja" className="ym-kana-stage-char">{sel}</span><span className="ym-kana-stage-romaji">{selRomaji}</span></div>
                <div className="ym-strokes-cred">traços: strokesvg · Klee One (OFL) · MIT</div>
              </>
            ) : (
              <p className="ym-sub">Sem dados de traço para este caractere.</p>
            )}
          </div>
          <Grid rows={rows} sel={sel} onSel={setSel} />
        </div>
      </div>
    </AppShell>
  );
}
