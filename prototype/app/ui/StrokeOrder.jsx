import React, { useEffect, useRef, useState, useMemo } from 'react';
import { Icon } from '../yomineko/m3';
import gaku from '../yomineko/kanji/05b66.svg?raw';
import hon from '../yomineko/kanji/0672c.svg?raw';

/* ============================================================
   Animated kanji stroke order (KanjiVG paths, drawn sequentially).
   Self-contained card with an "Animar" replay button.
   ============================================================ */

const SVGS = { '学': gaku, '本': hon };

export function StrokeOrder({ char = '学', size = 220 }) {
  const ref = useRef(null);
  const [playKey, setPlayKey] = useState(0);
  const raw = SVGS[char] || gaku;
  // drop the XML declaration / DOCTYPE / license comment, keep the <svg> element
  const svg = useMemo(() => raw.slice(raw.indexOf('<svg')), [raw]);

  useEffect(() => {
    const root = ref.current;
    if (!root) return;
    const svgEl = root.querySelector('svg');
    if (svgEl) { svgEl.setAttribute('width', '100%'); svgEl.setAttribute('height', '100%'); }
    root.querySelectorAll('text').forEach((t) => { t.style.display = 'none'; });
    const paths = [...root.querySelectorAll('path')];
    let delay = 0.15;
    paths.forEach((p) => {
      const len = p.getTotalLength();
      p.style.stroke = 'var(--on-surface)';
      p.style.fill = 'none';
      p.style.strokeWidth = '4.5';
      p.style.transition = 'none';
      p.style.strokeDasharray = `${len}`;
      p.style.strokeDashoffset = `${len}`;
      p.getBoundingClientRect(); // force reflow so the transition runs
      const dur = Math.max(0.35, len / 90);
      p.style.transition = `stroke-dashoffset ${dur}s ease ${delay}s`;
      p.style.strokeDashoffset = '0';
      delay += dur + 0.12;
    });
  }, [svg, playKey]);

  return (
    <div className="card card-filled">
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 10 }}>
        <span className="label-m" style={{ color: 'var(--on-surface-variant)' }}>ORDEM DOS TRAÇOS</span>
        <button className="btn btn-text btn-sm" onClick={() => setPlayKey((k) => k + 1)}>
          <Icon name="play_arrow" size={16} /> Animar
        </button>
      </div>
      <div style={{ display: 'flex', justifyContent: 'center' }}>
        <div
          key={playKey}
          ref={ref}
          style={{ width: size, height: size, background: 'var(--surface-container-high)', borderRadius: 'var(--r-md)' }}
          dangerouslySetInnerHTML={{ __html: svg }}
        />
      </div>
      <button className="btn btn-outlined btn-block" style={{ marginTop: 12 }}>
        <Icon name="draw" size={18} /> Praticar escrita (v1.1)
      </button>
    </div>
  );
}
