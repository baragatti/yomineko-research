import { useEffect, useRef, useState } from "react";
import { Icon } from "~/ui/Icon";

/* Kana stroke-order viewer. Data = our adaptation of strokesvg (Klee One SIL OFL + MIT): per STROKE a list of
   sub-path centerlines (most strokes = 1 path; complex ones like あ's curl = 2). Sub-paths are drawn together
   as one stroke (same timing) with a stroke-dashoffset "pen" animation; a faint ghost shows the full kana. */
export interface KanaStrokeData {
  viewbox: string;
  strokes: string[][];
}

export function KanaStrokes({ char, data, size = 200 }: { char: string; data: KanaStrokeData; size?: number }) {
  const ref = useRef<SVGSVGElement>(null);
  const [playKey, setPlayKey] = useState(0);

  useEffect(() => {
    const svg = ref.current;
    if (!svg) return;
    const byStroke: SVGPathElement[][] = [];
    svg.querySelectorAll<SVGPathElement>(".ym-kana-draw").forEach((p) => {
      const i = Number(p.dataset.stroke);
      (byStroke[i] ||= []).push(p);
    });
    let delay = 0.25;
    for (const paths of byStroke) {
      if (!paths) continue;
      const dur = Math.max(0.45, Math.max(...paths.map((p) => p.getTotalLength())) / 650);
      for (const p of paths) {
        const len = p.getTotalLength();
        p.style.transition = "none";
        p.style.strokeDasharray = String(len);
        p.style.strokeDashoffset = String(len);
        p.getBoundingClientRect(); // force reflow so the transition runs
        p.style.transition = `stroke-dashoffset ${dur}s ease ${delay}s`;
        p.style.strokeDashoffset = "0";
      }
      delay += dur + 0.2;
    }
  }, [playKey, char]);

  return (
    <div className="ym-kana-viewer">
      <svg ref={ref} key={`${char}-${playKey}`} viewBox={data.viewbox} width={size} height={size}
           className="ym-kana-svg" role="img" aria-label={`Ordem dos traços de ${char}`}>
        <g className="ym-kana-ghost">
          {data.strokes.flatMap((sub, i) => sub.map((d, j) => <path key={`g${i}-${j}`} d={d} />))}
        </g>
        <g>
          {data.strokes.flatMap((sub, i) => sub.map((d, j) => (
            <path key={`${i}-${j}`} className="ym-kana-draw" data-stroke={i} d={d} />
          )))}
        </g>
      </svg>
      <button className="ym-btn-text" onClick={() => setPlayKey((k) => k + 1)} aria-label="Reproduzir a ordem dos traços">
        <Icon name="play_arrow" size={16} /> Reproduzir
      </button>
    </div>
  );
}
