import { useEffect, useRef, useState } from "react";
import { Icon } from "~/ui/Icon";

/* Stroke-order animator for CENTERLINE data — used for kana (strokesvg, Klee One SIL OFL + MIT) AND kanji
   (GlyphWiki KAGE-derived centerlines, permissive). One clean path per stroke. Animation: each stroke is
   revealed with a stroke-dashoffset "pen" (CSS ANIMATION with `both` fill — robust on SSR page loads) while a
   guide BALL rides the same path via CSS motion-path; numbered markers sit at each stroke's start point.
   Multi-glyph combos (きゃ) pass `offsets`: per-stroke x-translation composing the glyphs side by side in ONE
   canvas, so the small kana keeps its natural text position/size. All geometry derives from the viewBox.
   Honors prefers-reduced-motion (static, no pen/ball). */
export interface KanaStrokeData {
  viewbox: string;
  strokes: string[];
  offsets?: number[]; // optional per-stroke x-translation (combo composition)
}

interface StartPt { x: number; y: number; n: number; hideAt: number }

export function KanaStrokes({ char, data, size = 200 }: { char: string; data: KanaStrokeData; size?: number }) {
  const ref = useRef<SVGSVGElement>(null);
  const [playKey, setPlayKey] = useState(0);
  const [starts, setStarts] = useState<StartPt[]>([]);
  const vb = data.viewbox.split(/\s+/).map(Number);
  const vbW = vb[2] || 1024, vbH = vb[3] || 1024;
  const u = vbH / 1024; // unit for widths/radii (height-based)
  const SPEED = 0.65 * vbH; // px of path per second, scale-invariant
  const offs = data.offsets || [];
  const width = size, height = Math.round((size * vbH) / vbW);

  useEffect(() => {
    const svg = ref.current;
    if (!svg) return;
    const paths = Array.from(svg.querySelectorAll<SVGPathElement>(".ym-kana-draw"));
    const balls = Array.from(svg.querySelectorAll<SVGCircleElement>(".ym-kana-ball"));
    const reduced = typeof window !== "undefined" &&
      window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    // timeline first (the badges need each stroke's finish time to fade out)
    let t = 250;
    const timeline = paths.map((p) => {
      const len = p.getTotalLength();
      const dur = Math.max(450, (len / SPEED) * 1000);
      const seg = { len, dur, delay: t };
      t += dur + 200;
      return seg;
    });
    setStarts(paths.map((p, i) => {
      // place the number BESIDE the start point (offset opposite the stroke's initial direction) so the badge
      // never covers a tiny stroke (e.g. the dakuten of が, where it read as a stray glyph part)
      const { len, dur, delay } = timeline[i];
      const p0 = p.getPointAtLength(0);
      const p1 = p.getPointAtLength(Math.min(40 * u, Math.max(1, len * 0.25)));
      let dx = p0.x - p1.x, dy = p0.y - p1.y;
      const m = Math.hypot(dx, dy) || 1;
      const off = 52 * u;
      dx = (dx / m) * off; dy = (dy / m) * off;
      const vx = vb[0] || 0, vy = vb[1] || 0;
      const cl = (v: number, lo: number, hi: number) => Math.min(hi, Math.max(lo, v));
      return { x: cl(p0.x + dx + (offs[i] || 0), vx + 30 * u, vx + vbW - 30 * u),
               y: cl(p0.y + dy, vy + 30 * u, vy + vbH - 30 * u), n: i + 1,
               hideAt: reduced ? -1 : delay + dur };
    }));
    if (reduced) {
      for (const p of paths) { p.style.animation = "none"; p.style.strokeDasharray = ""; p.style.strokeDashoffset = "0"; }
      return;
    }
    paths.forEach((p, i) => {
      const { len, dur, delay } = timeline[i];
      p.style.strokeDasharray = String(len);
      p.style.setProperty("--ym-len", String(len));
      p.style.animation = `ym-pen-run ${dur}ms ease ${delay}ms both`;
      const b = balls[i];
      if (b) {
        b.style.offsetPath = `path('${p.getAttribute("d")}')`;
        b.style.animation = `ym-ball-run ${dur}ms ease ${delay}ms`;
      }
    });
  }, [playKey, char]);

  const tf = (i: number) => (offs[i] ? `translate(${offs[i]},0)` : undefined);
  return (
    <div className="ym-kana-viewer">
      <svg ref={ref} key={`${char}-${playKey}`} viewBox={data.viewbox} width={width} height={height}
           className="ym-kana-svg" role="img" aria-label={`Ordem dos traços de ${char}`}>
        <g className="ym-kana-ghost" style={{ strokeWidth: 72 * u }}>
          {data.strokes.map((d, i) => <g key={i} transform={tf(i)}><path d={d} /></g>)}
        </g>
        <g style={{ strokeWidth: 80 * u }}>
          {data.strokes.map((d, i) => (
            // ball lives INSIDE the stroke's transform group so its offset-path (path coords) lands right
            <g key={i} transform={tf(i)}>
              <path className="ym-kana-draw" d={d} />
              <circle className="ym-kana-ball" r={26 * u} />
            </g>
          ))}
        </g>
        <g className="ym-kana-marks">
          {starts.map((s) => (
            /* badge guides the upcoming stroke, then fades as soon as that stroke is drawn (the finished
               glyph stays clean, no lingering "starter ball"); reduced-motion (hideAt<0) keeps them static */
            <g key={s.n} transform={`translate(${s.x},${s.y})`}
               style={s.hideAt >= 0 ? { animation: `ym-mark-out 260ms ease ${s.hideAt}ms both` } : undefined}>
              <circle className="ym-kana-mark-bg" r={26 * u} style={{ strokeWidth: 4 * u }} />
              <text className="ym-kana-mark-n" textAnchor="middle" dy={18 * u} style={{ fontSize: 52 * u }}>{s.n}</text>
            </g>
          ))}
        </g>
      </svg>
      <button className="ym-btn-text" onClick={() => setPlayKey((k) => k + 1)} aria-label="Reproduzir a ordem dos traços">
        <Icon name="play_arrow" size={16} /> Reproduzir
      </button>
    </div>
  );
}
