import { useEffect, useId, useRef, useState } from "react";
import { Icon } from "~/ui/Icon";

/* Stroke-order animator for CENTERLINE data — kana (strokesvg, Klee One SIL OFL + MIT) AND kanji (GlyphWiki
   KAGE-derived, permissive).

   Rendering modes:
   - CLIPPED (kana, `shadows` present): strokesvg's real model — the fat centerline is CLIPPED to the stroke's
     OUTLINE shape (true Klee One calligraphy). Centerlines intentionally overshoot; the clip crops them.
   - PLAIN (kanji / dots without shadows): round-cap centerline strokes.

   A stroke's centerline may contain SEVERAL subpaths (e.g. あ's curl: main sweep + curl piece). Each subpath
   is rendered as its OWN <path> and animated sequentially inside the stroke's time window — dash patterns
   RESTART at subpath boundaries in real renderers, so a single multi-subpath path can paint its later
   subpaths while "hidden" (the phantom shapes that broke the first clipped deploy).

   Pen = dash-reveal CSS animation with a padded gap (`len (len+4)`, hidden offset len+2): with the boundary
   inside the gap, round linecaps cannot paint their cap-dot at the start point, and a failed animation leaves
   the piece HIDDEN (inline offset) instead of fully drawn. Ball = CSS motion-path with hidden keyframe
   endpoints. Numbered badges appear only around their stroke's window. Combos (きゃ) pass per-stroke
   x-`offsets`. Honors prefers-reduced-motion (static render). */
export interface KanaStrokeData {
  viewbox: string;
  strokes: string[];
  /** per stroke: one shadow per SUB-PIECE (string[]), or a single whole-stroke shadow (legacy string) */
  shadows?: (string[] | string)[] | null;
  offsets?: number[];
}

interface StartPt { x: number; y: number; n: number; showAt: number; showFor: number }

const splitPieces = (d: string) => d.split(/(?=M)/).map((s) => s.trim()).filter(Boolean);

export function KanaStrokes({ char, data, size = 200 }: { char: string; data: KanaStrokeData; size?: number }) {
  const ref = useRef<SVGSVGElement>(null);
  const uid = useId().replace(/[^a-zA-Z0-9]/g, "");
  const [playKey, setPlayKey] = useState(0);
  const [starts, setStarts] = useState<StartPt[]>([]);
  const vb = data.viewbox.split(/\s+/).map(Number);
  const vbW = vb[2] || 1024, vbH = vb[3] || 1024;
  const u = vbH / 1024;
  const SPEED = 0.65 * vbH; // px of path per second
  const offs = data.offsets || [];
  const shadows = data.shadows || [];
  const width = size, height = Math.round((size * vbH) / vbW);
  const pieces = data.strokes.map(splitPieces);

  useEffect(() => {
    const svg = ref.current;
    if (!svg) return;
    const groups = Array.from(svg.querySelectorAll<SVGGElement>("[data-stroke]"));
    const reduced = typeof window !== "undefined" &&
      window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    const canRide = typeof CSS !== "undefined" && CSS.supports?.("offset-path", "path('M0 0L1 1')");

    // per-stroke piece lengths -> stroke timeline
    const info = groups.map((g) => {
      const ps = Array.from(g.querySelectorAll<SVGPathElement>(".ym-kana-draw"));
      const lens = ps.map((p) => p.getTotalLength());
      return { ps, lens, total: lens.reduce((a, b) => a + b, 0) };
    });
    let t = 250;
    const timeline = info.map(({ total }) => {
      const dur = Math.max(450, (total / SPEED) * 1000);
      const seg = { dur, delay: t };
      t += dur + 200;
      return seg;
    });

    setStarts(info.map(({ ps, lens }, i) => {
      const { dur, delay } = timeline[i];
      const p0pt = ps[0].getPointAtLength(0);
      const p1 = ps[0].getPointAtLength(Math.min(40 * u, Math.max(1, lens[0] * 0.25)));
      let dx = p0pt.x - p1.x, dy = p0pt.y - p1.y;
      const m = Math.hypot(dx, dy) || 1;
      dx = (dx / m) * 52 * u; dy = (dy / m) * 52 * u;
      const vx = vb[0] || 0, vy = vb[1] || 0;
      const cl = (v: number, lo: number, hi: number) => Math.min(hi, Math.max(lo, v));
      return { x: cl(p0pt.x + dx + (offs[i] || 0), vx + 30 * u, vx + vbW - 30 * u),
               y: cl(p0pt.y + dy, vy + 30 * u, vy + vbH - 30 * u), n: i + 1,
               showAt: reduced ? -1 : Math.max(0, delay - 350), showFor: dur + 700 };
    }));

    if (reduced) {
      for (const { ps } of info) for (const p of ps) {
        p.style.animation = "none"; p.style.strokeDasharray = ""; p.style.strokeDashoffset = "0";
      }
      return;
    }
    info.forEach(({ ps, lens, total }, i) => {
      const { dur, delay } = timeline[i];
      const balls = Array.from(groups[i].querySelectorAll<SVGCircleElement>(".ym-kana-ball"));
      let acc = 0;
      ps.forEach((p, j) => {
        const len = lens[j];
        const pieceDur = total ? (len / total) * dur : dur;
        const pieceDelay = delay + (total ? (acc / total) * dur : 0);
        acc += len;
        p.style.strokeDasharray = `${len} ${len + 4}`;
        p.style.strokeDashoffset = String(len + 2); // fail-HIDDEN + keeps the dash boundary off the start point
        p.style.setProperty("--ym-len", String(len + 2));
        p.style.animation = `ym-pen-run ${pieceDur}ms linear ${pieceDelay}ms both`;
        const b = balls[j];
        if (b && canRide) {
          b.style.offsetPath = `path('${p.getAttribute("d")}')`;
          b.style.animation = `ym-ball-run ${pieceDur}ms linear ${pieceDelay}ms both`;
        }
      });
    });
  }, [playKey, char]);

  const tf = (i: number) => (offs[i] ? `translate(${offs[i]},0)` : undefined);
  // per-piece shadows (legacy single string = same shadow for every piece of the stroke)
  const shArr = (i: number): string[] => {
    const sh = shadows[i];
    if (!sh) return [];
    return Array.isArray(sh) ? sh : pieces[i].map(() => sh);
  };
  return (
    <div className="ym-kana-viewer">
      <svg ref={ref} key={`${char}-${playKey}`} viewBox={data.viewbox} width={width} height={height}
           className="ym-kana-svg" role="img" aria-label={`Ordem dos traços de ${char}`}>
        <defs>
          {pieces.map((ps, i) => ps.map((_, j) => shArr(i)[j] ? (
            <clipPath key={`${i}_${j}`} id={`${uid}c${i}_${j}`}><path d={shArr(i)[j]} /></clipPath>
          ) : null))}
        </defs>
        {/* ghost: the true glyph shapes when shadows exist; faint centerlines otherwise */}
        <g className="ym-kana-ghost" style={{ strokeWidth: 72 * u }}>
          {data.strokes.map((d, i) => (
            <g key={i} transform={tf(i)}>
              {shArr(i).some(Boolean)
                ? shArr(i).map((sd, j) => sd ? <path key={j} className="ym-kana-ghostfill" d={sd} /> : null)
                : <path d={d} />}
            </g>
          ))}
        </g>
        <g style={{ strokeWidth: 80 * u }}>
          {pieces.map((ps, i) => (
            // one <g> per STROKE; each SUBPATH is its own <path> (dash patterns restart per subpath) clipped
            // to ITS OWN shadow — a shared whole-stroke clip lets the fat pen band paint a DISTANT region of
            // the same stroke early (め's loop "irradiated" at the stroke start). Ball rides inside the same
            // per-piece clip. ROUND caps like strokesvg (butt caps left unpainted notches at tips/joints);
            // the round-cap phantom dot at hidden starts is prevented by the dash-gap padding.
            <g key={i} data-stroke={i} transform={tf(i)}>
              {ps.map((pd, j) => (
                <g key={j} clipPath={shArr(i)[j] ? `url(#${uid}c${i}_${j})` : undefined}
                   style={shArr(i)[j] ? { strokeWidth: 128 * u } : undefined}>
                  <path className="ym-kana-draw" d={pd} />
                  <circle className="ym-kana-ball" r={26 * u} />
                </g>
              ))}
            </g>
          ))}
        </g>
        <g className="ym-kana-marks">
          {starts.map((s) => (
            /* badge appears only around its stroke's window; reduced-motion keeps them static */
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
