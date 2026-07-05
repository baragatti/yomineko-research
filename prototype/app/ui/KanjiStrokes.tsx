import { useEffect, useRef, useState } from "react";
import { Icon } from "~/ui/Icon";
import { KanaStrokes } from "~/ui/KanaStrokes";

/* Production kanji stroke-order viewer.
   PREFERRED: per-stroke CENTERLINES (GlyphWiki KAGE-derived, permissive) -> the full pen+ball+numbers
   animation via the shared KanaStrokes animator.
   FALLBACK: Kanji Alive (CC BY 4.0) cumulative filled-outline steps rendered progressively (no per-stroke
   geometry exists in that source). Either way only the single kanji on the page reaches the client. */
export interface StrokeData {
  total_strokes: number;
  viewbox: string;
  transform: string;
  steps: string[];
  source: string;
}
export interface StrokeLines {
  strokes: string[];
}

export function KanjiStrokes({ char, data, lines }: { char: string; data?: StrokeData | null; lines?: StrokeLines | null }) {
  if (lines && lines.strokes?.length) {
    return (
      <div className="ym-card-soft ym-strokes">
        <div className="ym-strokes-head"><span className="ym-strokes-label">ORDEM DOS TRAÇOS</span></div>
        <KanaStrokes char={char} data={{ viewbox: "-12 -12 224 224", strokes: lines.strokes }} size={220} />
        <div className="ym-strokes-cred">traços: GlyphWiki (uso livre)</div>
      </div>
    );
  }
  if (!data) return null;
  return <KanjiStrokesOutline char={char} data={data} />;
}

function KanjiStrokesOutline({ char, data }: { char: string; data: StrokeData }) {
  const N = data.steps.length;
  const [idx, setIdx] = useState(N - 1); // default: full glyph
  const [playing, setPlaying] = useState(false);
  const timer = useRef<ReturnType<typeof setInterval> | null>(null);

  useEffect(() => {
    if (!playing) return;
    timer.current = setInterval(() => {
      setIdx((i) => {
        if (i >= N - 1) { setPlaying(false); return N - 1; }
        return i + 1;
      });
    }, 620);
    return () => { if (timer.current) clearInterval(timer.current); };
  }, [playing, N]);

  const play = () => { setIdx(0); setPlaying(true); };
  const step = (d: number) => { setPlaying(false); setIdx((i) => Math.min(N - 1, Math.max(0, i + d))); };

  return (
    <div className="ym-card-soft ym-strokes">
      <div className="ym-strokes-head">
        <span className="ym-strokes-label">ORDEM DOS TRAÇOS</span>
        <button className="ym-btn-text" onClick={play} aria-label="Animar a ordem dos traços">
          <Icon name="play_arrow" size={16} /> Animar
        </button>
      </div>
      <div className="ym-strokes-stage">
        <svg viewBox={data.viewbox} className="ym-strokes-svg" role="img"
             aria-label={`Ordem dos traços do kanji ${char}`}>
          <g transform={data.transform}>
            <path d={data.steps[N - 1]} className="ym-stroke-ghost" />
            <path d={data.steps[Math.max(0, idx)]} className="ym-stroke-active" />
          </g>
        </svg>
      </div>
      <div className="ym-strokes-ctrl">
        <button className="ym-icon-btn" onClick={() => step(-1)} aria-label="Traço anterior" disabled={idx <= 0}>
          <Icon name="chevron_left" size={20} />
        </button>
        <span className="ym-strokes-count">traço {Math.max(1, idx + 1)} / {data.total_strokes}</span>
        <button className="ym-icon-btn" onClick={() => step(1)} aria-label="Próximo traço" disabled={idx >= N - 1}>
          <Icon name="chevron_right" size={20} />
        </button>
      </div>
      <div className="ym-strokes-cred">traços: Kanji alive · CC BY 4.0</div>
    </div>
  );
}
