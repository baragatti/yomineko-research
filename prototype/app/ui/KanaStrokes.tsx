import { useEffect, useRef, useState } from "react";
import { Icon } from "~/ui/Icon";

/* Stroke-order animator for CENTERLINE data — used for kana (strokesvg, Klee One SIL OFL + MIT) AND kanji
   (GlyphWiki KAGE-derived centerlines, permissive). One clean path per stroke. Animation: each stroke is
   revealed with a stroke-dashoffset "pen" while a guide BALL rides the same path via CSS motion-path
   (offset-path + keyframes; compositor-driven, no rAF, so it stays in sync even in throttled tabs); numbered
   markers sit at each stroke's start point. All geometry sizes derive from the viewBox so the same component
   serves the 1024-box kana and the 200-box kanji. Honors prefers-reduced-motion (static, no pen/ball). */
export interface KanaStrokeData {
  viewbox: string;
  strokes: string[];
}

interface StartPt { x: number; y: number; n: number }

export function KanaStrokes({ char, data, size = 200 }: { char: string; data: KanaStrokeData; size?: number }) {
  const ref = useRef<SVGSVGElement>(null);
  const [playKey, setPlayKey] = useState(0);
  const [starts, setStarts] = useState<StartPt[]>([]);
  const box = Number(data.viewbox.split(/\s+/)[3]) || 1024; // viewBox height -> unit for all widths
  const u = box / 1024;
  const SPEED = 0.65 * box; // px of path per second, scale-invariant

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
      for (const p of paths) { p.style.animation = "none"; p.style.strokeDasharray = ""; p.style.strokeDashoffset = "0"; }
      return;
    }
    // Pen + ball are BOTH CSS animations (not transitions): `both` fill holds the hidden/start state through
    // the delay with no reflow trick, so it's robust on SSR hydration (a transition armed during the initial
    // paint can be coalesced away -> strokes appeared without the drawing motion on full page loads).
    let delay = 250;
    paths.forEach((p, i) => {
      const len = p.getTotalLength();
      const dur = Math.max(450, (len / SPEED) * 1000);
      p.style.strokeDasharray = String(len);
      p.style.setProperty("--ym-len", String(len));
      p.style.animation = `ym-pen-run ${dur}ms ease ${delay}ms both`;
      const b = balls[i];
      if (b) {
        b.style.offsetPath = `path('${p.getAttribute("d")}')`;
        b.style.animation = `ym-ball-run ${dur}ms ease ${delay}ms`;
      }
      delay += dur + 200;
    });
  }, [playKey, char]);

  return (
    <div className="ym-kana-viewer">
      <svg ref={ref} key={`${char}-${playKey}`} viewBox={data.viewbox} width={size} height={size}
           className="ym-kana-svg" role="img" aria-label={`Ordem dos traços de ${char}`}>
        <g className="ym-kana-ghost" style={{ strokeWidth: 72 * u }}>
          {data.strokes.map((d, i) => <path key={i} d={d} />)}
        </g>
        <g style={{ strokeWidth: 80 * u }}>
          {data.strokes.map((d, i) => <path key={i} className="ym-kana-draw" d={d} />)}
        </g>
        <g className="ym-kana-marks">
          {starts.map((s) => (
            <g key={s.n} transform={`translate(${s.x},${s.y})`}>
              <circle className="ym-kana-mark-bg" r={34 * u} style={{ strokeWidth: 4 * u }} />
              <text className="ym-kana-mark-n" textAnchor="middle" dy={24 * u} style={{ fontSize: 68 * u }}>{s.n}</text>
            </g>
          ))}
        </g>
        {data.strokes.map((_, i) => <circle key={i} className="ym-kana-ball" r={26 * u} />)}
      </svg>
      <button className="ym-btn-text" onClick={() => setPlayKey((k) => k + 1)} aria-label="Reproduzir a ordem dos traços">
        <Icon name="play_arrow" size={16} /> Reproduzir
      </button>
    </div>
  );
}
