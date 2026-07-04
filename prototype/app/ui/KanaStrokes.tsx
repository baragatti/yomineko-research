import { useEffect, useRef, useState } from "react";
import { Icon } from "~/ui/Icon";

/* Kana stroke-order viewer. Data = our adaptation of strokesvg (Klee One SIL OFL + MIT): one clean centerline
   per stroke. Animation: each stroke is revealed with a stroke-dashoffset "pen" while a guide BALL rides the
   same path via CSS motion-path (offset-path + keyframes; compositor-driven, no rAF, so it stays in sync with
   the pen even in throttled tabs); numbered markers sit at each stroke's start point. Client island only —
   public attributed data. Honors prefers-reduced-motion (static render, no pen/ball). */
export interface KanaStrokeData {
  viewbox: string;
  strokes: string[];
}

interface StartPt { x: number; y: number; n: number }

export function KanaStrokes({ char, data, size = 200 }: { char: string; data: KanaStrokeData; size?: number }) {
  const ref = useRef<SVGSVGElement>(null);
  const [playKey, setPlayKey] = useState(0);
  const [starts, setStarts] = useState<StartPt[]>([]);

  useEffect(() => {
    const svg = ref.current;
    if (!svg) return;
    const paths = Array.from(svg.querySelectorAll<SVGPathElement>(".ym-kana-draw"));
    const balls = Array.from(svg.querySelectorAll<SVGCircleElement>(".ym-kana-ball"));
    setStarts(paths.map((p, i) => {
      const pt = p.getPointAtLength(0);
      return { x: pt.x, y: pt.y, n: i + 1 };
    }));
    const reduced = typeof window !== "undefined" &&
      window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    if (reduced) {
      for (const p of paths) { p.style.transition = "none"; p.style.strokeDasharray = ""; p.style.strokeDashoffset = "0"; }
      return;
    }
    let delay = 250;
    paths.forEach((p, i) => {
      const len = p.getTotalLength();
      const dur = Math.max(450, (len / 650) * 1000);
      // pen: reveal the stroke
      p.style.transition = "none";
      p.style.strokeDasharray = String(len);
      p.style.strokeDashoffset = String(len);
      p.getBoundingClientRect(); // reflow so the transition runs
      p.style.transition = `stroke-dashoffset ${dur}ms ease ${delay}ms`;
      p.style.strokeDashoffset = "0";
      // ball: ride the same path in the same window (CSS motion-path keyframes; see .ym-kana-ball)
      const b = balls[i];
      if (b) {
        b.style.offsetPath = `path('${p.getAttribute("d")}')`;
        b.style.animation = "none";
        b.getBoundingClientRect();
        b.style.animation = `ym-ball-run ${dur}ms ease ${delay}ms both`;
        b.style.animationFillMode = "none"; // invisible (opacity 0 base) outside its window
      }
      delay += dur + 200;
    });
  }, [playKey, char]);

  return (
    <div className="ym-kana-viewer">
      <svg ref={ref} key={`${char}-${playKey}`} viewBox={data.viewbox} width={size} height={size}
           className="ym-kana-svg" role="img" aria-label={`Ordem dos traços de ${char}`}>
        <g className="ym-kana-ghost">{data.strokes.map((d, i) => <path key={i} d={d} />)}</g>
        <g>{data.strokes.map((d, i) => <path key={i} className="ym-kana-draw" d={d} />)}</g>
        <g className="ym-kana-marks">
          {starts.map((s) => (
            <g key={s.n} transform={`translate(${s.x},${s.y})`}>
              <circle className="ym-kana-mark-bg" r="34" />
              <text className="ym-kana-mark-n" textAnchor="middle" dy="24">{s.n}</text>
            </g>
          ))}
        </g>
        {data.strokes.map((_, i) => <circle key={i} className="ym-kana-ball" r="26" />)}
      </svg>
      <button className="ym-btn-text" onClick={() => setPlayKey((k) => k + 1)} aria-label="Reproduzir a ordem dos traços">
        <Icon name="play_arrow" size={16} /> Reproduzir
      </button>
    </div>
  );
}
