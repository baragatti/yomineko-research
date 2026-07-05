import { useEffect, useId, useRef, useState } from "react";
import { Icon } from "~/ui/Icon";

/* Stroke-order animator for CENTERLINE data — used for kana (strokesvg, Klee One SIL OFL + MIT) AND kanji
   (GlyphWiki KAGE-derived centerlines, permissive).

   Two rendering modes:
   - CLIPPED (kana, when `shadows` present): strokesvg's real model — each stroke has an OUTLINE shape (the
     true Klee One calligraphy) and the fat centerline is CLIPPED to it. Centerlines intentionally overshoot
     (construction geometry, e.g. き/ぎ stroke 4); the clip crops them, so we must reproduce it.
   - PLAIN (kanji lines / no shadows): round-cap centerline strokes.

   Animation: pen = stroke-dashoffset CSS animation (`both` fill — robust on SSR loads); a guide BALL rides
   the same path via CSS motion-path (hidden state lives IN the keyframes); numbered badges appear only around
   their stroke's window. Combos (きゃ) pass per-stroke x-`offsets` composing glyphs in one text-like canvas.
   All geometry derives from the viewBox. Honors prefers-reduced-motion (static, no pen/ball). */
export interface KanaStrokeData {
  viewbox: string;
  strokes: string[];
  shadows?: string[] | null; // per-stroke outline shapes (clip + ghost); '' entries fall back to plain
  offsets?: number[];        // optional per-stroke x-translation (combo composition)
}

interface StartPt { x: number; y: number; n: number; showAt: number; showFor: number }

export function KanaStrokes({ char, data, size = 200 }: { char: string; data: KanaStrokeData; size?: number }) {
  const ref = useRef<SVGSVGElement>(null);
  const uid = useId().replace(/[^a-zA-Z0-9]/g, "");
  const [playKey, setPlayKey] = useState(0);
  const [starts, setStarts] = useState<StartPt[]>([]);
  const vb = data.viewbox.split(/\s+/).map(Number);
  const vbW = vb[2] || 1024, vbH = vb[3] || 1024;
  const u = vbH / 1024; // unit for widths/radii (height-based)
  const SPEED = 0.65 * vbH; // px of path per second, scale-invariant
  const offs = data.offsets || [];
  const shadows = data.shadows || [];
  const width = size, height = Math.round((size * vbH) / vbW);

  useEffect(() => {
    const svg = ref.current;
    if (!svg) return;
    const paths = Array.from(svg.querySelectorAll<SVGPathElement>(".ym-kana-draw"));
    const balls = Array.from(svg.querySelectorAll<SVGCircleElement>(".ym-kana-ball"));
    const reduced = typeof window !== "undefined" &&
      window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    // timeline first (the badges need each stroke's window)
    let t = 250;
    const timeline = paths.map((p) => {
      const len = p.getTotalLength();
      const dur = Math.max(450, (len / SPEED) * 1000);
      const seg = { len, dur, delay: t };
      t += dur + 200;
      return seg;
    });
    setStarts(paths.map((p, i) => {
      // number badge BESIDE the start point (offset opposite the stroke's initial direction) so it never
      // covers a tiny stroke (e.g. the dakuten of が)
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
               showAt: reduced ? -1 : Math.max(0, delay - 350),
               showFor: dur + 700 };
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
      // guard: without offset-path support on SVG (older Safari), an armed ball would blink at the group
      // origin instead of riding the stroke — keep it hidden there.
      const canRide = typeof CSS !== "undefined" && CSS.supports?.("offset-path", "path('M0 0L1 1')");
      if (b && canRide) {
        b.style.offsetPath = `path('${p.getAttribute("d")}')`;
        b.style.animation = `ym-ball-run ${dur}ms ease ${delay}ms both`;
      }
    });
  }, [playKey, char]);

  const tf = (i: number) => (offs[i] ? `translate(${offs[i]},0)` : undefined);
  const clipped = (i: number) => !!shadows[i];
  return (
    <div className="ym-kana-viewer">
      <svg ref={ref} key={`${char}-${playKey}`} viewBox={data.viewbox} width={width} height={height}
           className="ym-kana-svg" role="img" aria-label={`Ordem dos traços de ${char}`}>
        <defs>
          {data.strokes.map((_, i) => clipped(i) ? (
            <clipPath key={i} id={`${uid}c${i}`}><path d={shadows[i]} /></clipPath>
          ) : null)}
        </defs>
        {/* ghost: the true glyph shapes when shadows exist; faint centerlines otherwise */}
        <g className="ym-kana-ghost" style={{ strokeWidth: 72 * u }}>
          {data.strokes.map((d, i) => (
            <g key={i} transform={tf(i)}>
              {clipped(i) ? <path className="ym-kana-ghostfill" d={shadows[i]} /> : <path d={d} />}
            </g>
          ))}
        </g>
        <g style={{ strokeWidth: 80 * u }}>
          {data.strokes.map((d, i) => (
            // ball lives INSIDE the stroke's transform group so its offset-path (path coords) lands right;
            // clipped pens are FAT (the shadow shape defines the visible form, like strokesvg's own viewer)
            <g key={i} transform={tf(i)}>
              <path className="ym-kana-draw" d={d}
                    clipPath={clipped(i) ? `url(#${uid}c${i})` : undefined}
                    style={clipped(i) ? { strokeWidth: 128 * u, strokeLinecap: "butt" } : undefined} />
              <circle className="ym-kana-ball" r={26 * u} />
            </g>
          ))}
        </g>
        <g className="ym-kana-marks">
          {starts.map((s) => (
            /* badge appears only around its stroke's drawing window; reduced-motion keeps them static */
            <g key={s.n} transform={`translate(${s.x},${s.y})`}
               style={s.showAt >= 0
                 ? { opacity: 0, animation: `ym-mark-inout ${s.showFor}ms ease ${s.showAt}ms both` }
                 : undefined}>
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
