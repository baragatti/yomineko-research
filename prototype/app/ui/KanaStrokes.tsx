import { useEffect, useRef, useState } from "react";
import { Icon } from "~/ui/Icon";

/* Kana stroke-order viewer. Data = our adaptation of strokesvg (Klee One SIL OFL + MIT): one clean centerline
   per stroke, drawn sequentially with a stroke-dashoffset "pen" animation; a faint ghost shows the full kana. */
export interface KanaStrokeData {
  viewbox: string;
  strokes: string[];
}

export function KanaStrokes({ char, data, size = 200 }: { char: string; data: KanaStrokeData; size?: number }) {
  const ref = useRef<SVGSVGElement>(null);
  const [playKey, setPlayKey] = useState(0);

  useEffect(() => {
    const svg = ref.current;
    if (!svg) return;
    let delay = 0.25;
    for (const p of Array.from(svg.querySelectorAll<SVGPathElement>(".ym-kana-draw"))) {
      const len = p.getTotalLength();
      p.style.transition = "none";
      p.style.strokeDasharray = String(len);
      p.style.strokeDashoffset = String(len);
      p.getBoundingClientRect(); // force reflow so the transition runs
      const dur = Math.max(0.45, len / 650);
      p.style.transition = `stroke-dashoffset ${dur}s ease ${delay}s`;
      p.style.strokeDashoffset = "0";
      delay += dur + 0.2;
    }
  }, [playKey, char]);

  return (
    <div className="ym-kana-viewer">
      <svg ref={ref} key={`${char}-${playKey}`} viewBox={data.viewbox} width={size} height={size}
           className="ym-kana-svg" role="img" aria-label={`Ordem dos traços de ${char}`}>
        <g className="ym-kana-ghost">{data.strokes.map((d, i) => <path key={i} d={d} />)}</g>
        <g>{data.strokes.map((d, i) => <path key={i} className="ym-kana-draw" d={d} />)}</g>
      </svg>
      <button className="ym-btn-text" onClick={() => setPlayKey((k) => k + 1)} aria-label="Reproduzir a ordem dos traços">
        <Icon name="play_arrow" size={16} /> Reproduzir
      </button>
    </div>
  );
}
