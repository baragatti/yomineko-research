import React, { useState, useEffect } from 'react';
import { Icon, PhoneBody } from '../yomineko/m3';
import { Yomineko } from '../yomineko/mascot';
import { useApp, setReviewDone, reviewDue, REVIEW_TOTAL } from './store';

/* ============================================================
   Interactive SRS review — front → reveal → rate → next → done.
   Single-column layout; the App contains it on desktop (DesktopShell)
   and shows it fullscreen on mobile. Every state has a top-bar back.
   ============================================================ */

const DECK = [
  { type: 'PALAVRA', front: 'がくせい', reading: 'gakusei', meaning: 'estudante', ex: 'わたしは がくせい です。', exPt: 'Eu sou estudante.' },
  { type: 'KANJI', front: '学', reading: 'ガク · まな(ぶ)', meaning: 'estudo, aprender', ex: '大学 — universidade', exPt: '' },
  { type: 'FRASE', front: 'にほんじん です', reading: 'nihonjin desu', meaning: 'Sou japonês(a).', ex: 'わたしは にほんじん です。', exPt: 'Eu sou japonês(a).' },
];

const RATINGS = [
  { l: 'De novo', iv: '<1m', c: 'var(--error)' },
  { l: 'Difícil', iv: '~3d', c: 'var(--gold)' },
  { l: 'Bom', iv: '~7d', c: 'var(--success)' },
  { l: 'Fácil', iv: '~14d', c: 'var(--primary)' },
];

const TopBar = ({ progress, count, total }) => (
  <div className="appbar" style={{ flexShrink: 0, gap: 8 }}>
    <button className="icon-btn" data-tab="dashboard"><Icon name="arrow_back" size={24} /></button>
    {progress == null
      ? <span className="appbar-title">Revisão</span>
      : <>
          <div className="linear-prog thick" style={{ flex: 1 }}><i style={{ width: `${progress}%` }} /></div>
          <span className="label-m" style={{ color: 'var(--on-surface-variant)', marginRight: 8 }}>{count}/{total}</span>
        </>}
  </div>
);

const CardFace = ({ card, revealed, index, total, onAudio }) => (
  <div className="card card-elevated" style={{ padding: '32px 20px', textAlign: 'center', display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', minHeight: 280 }}>
    <span className="pill pill-outline">{card.type} · {index + 1} de {total}</span>
    <div className="jp-serif" style={{ fontSize: card.front.length > 6 ? 34 : 56, color: 'var(--on-surface)', marginTop: 18 }}>{card.front}</div>
    {!revealed ? (
      <>
        <button className="btn btn-tonal btn-sm" style={{ marginTop: 14 }} onClick={onAudio}><Icon name="volume_up" size={18} /> Ouvir</button>
        <div className="body-s" style={{ color: 'var(--on-surface-variant)', marginTop: 24 }}>Tente lembrar do significado.</div>
      </>
    ) : (
      <>
        <div className="body-m" style={{ color: 'var(--on-surface-variant)', marginTop: 4 }}>{card.reading}</div>
        <hr className="divider" style={{ width: '60%', margin: '18px 0' }} />
        <div className="headline-s" style={{ color: 'var(--primary)' }}>{card.meaning}</div>
        {card.ex && (
          <div className="card card-filled" style={{ marginTop: 14, textAlign: 'left', width: '100%' }}>
            <span className="label-m" style={{ color: 'var(--on-surface-variant)' }}>EXEMPLO</span>
            <div className="jp" style={{ fontSize: 16, marginTop: 4 }}>{card.ex}</div>
            {card.exPt && <div className="body-s" style={{ color: 'var(--on-surface-variant)' }}>{card.exPt}</div>}
          </div>
        )}
      </>
    )}
  </div>
);

const Rating = ({ onRate }) => (
  <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr 1fr', gap: 8 }}>
    {RATINGS.map((r, i) => (
      <button key={i} onClick={() => onRate(i)} className="state" style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 2, padding: '14px 0', borderRadius: 'var(--r-md)', border: 'none', cursor: 'pointer', background: `color-mix(in srgb, ${r.c} 16%, var(--surface))`, color: r.c }}>
        <span className="title-s" style={{ color: r.c }}>{r.l}</span>
        <span className="label-s" style={{ color: r.c, opacity: 0.85 }}>{r.iv}</span>
      </button>
    ))}
  </div>
);

const Frame = ({ children }) => (
  <div style={{ height: '100%', display: 'flex', flexDirection: 'column', background: 'var(--surface)' }}>{children}</div>
);

export function ReviewApp() {
  const { playAudio } = useApp();
  const [idx, setIdx] = useState(0);
  const [revealed, setRevealed] = useState(false);
  const [correct, setCorrect] = useState(0);
  const [done, setDone] = useState(false);
  const [pending, setPending] = useState(() => reviewDue());

  const total = DECK.length;
  const card = DECK[idx];

  const reveal = () => { setRevealed(true); playAudio(card.front); };
  const rate = (r) => {
    if (r >= 2) setCorrect((c) => c + 1);
    if (idx + 1 >= total) { setReviewDone(true); setDone(true); return; }
    setIdx((i) => i + 1);
    setRevealed(false);
  };

  useEffect(() => {
    const onKey = (e) => {
      if (done || pending === 0) return;
      if (e.code === 'Space') { e.preventDefault(); if (!revealed) reveal(); }
      else if (revealed && ['1', '2', '3', '4'].includes(e.key)) rate(Number(e.key) - 1);
    };
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  });

  if (pending === 0 && !done) {
    return (
      <Frame>
        <TopBar />
        <div style={{ flex: 1, display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', textAlign: 'center', padding: '0 32px', maxWidth: 460, margin: '0 auto' }}>
          <Yomineko pose="sleep" size={150} />
          <div className="headline-s" style={{ color: 'var(--on-surface)', marginTop: 8 }}>Nada para revisar hoje</div>
          <div className="body-m" style={{ color: 'var(--on-surface-variant)', marginTop: 6 }}>O grimório está em silêncio. Volte amanhã, com calma — ou pratique um pouco agora.</div>
          <button className="btn btn-magic" style={{ marginTop: 20 }} data-tab="practice"><Icon name="target" size={18} /> Ir para uma prática</button>
          <button className="btn btn-text" style={{ marginTop: 6 }} data-go="lesson">Continuar uma lição</button>
          <button className="btn btn-text" style={{ marginTop: 2, opacity: 0.75 }} onClick={() => { setReviewDone(false); setPending(REVIEW_TOTAL); setIdx(0); setRevealed(false); setCorrect(0); setDone(false); }}><Icon name="refresh" size={16} /> Refazer (demo)</button>
        </div>
      </Frame>
    );
  }

  if (done) {
    const pct = Math.round((correct / total) * 100);
    return (
      <Frame>
        <TopBar />
        <PhoneBody style={{ display: 'flex', flexDirection: 'column' }}>
          <div style={{ flex: 1, display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', textAlign: 'center', padding: '0 28px', maxWidth: 460, margin: '0 auto' }}>
            <div style={{ position: 'relative' }}>
              <div style={{ position: 'absolute', inset: '-20%', background: 'radial-gradient(circle, var(--magic-glow), transparent 70%)' }} />
              <div style={{ position: 'relative' }}><Yomineko pose="celebrate" size={160} /></div>
            </div>
            <div className="headline-m" style={{ color: 'var(--on-surface)', marginTop: 8 }}>Sessão concluída!</div>
            <div className="body-m" style={{ color: 'var(--on-surface-variant)', marginTop: 4 }}>{total} cartões revisados. Yomineko está orgulhoso.</div>
            <div className="card card-filled" style={{ width: '100%', marginTop: 20 }}>
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3,1fr)', gap: 12 }}>
                <div><div className="headline-s" style={{ color: 'var(--primary)' }}>{total}</div><div className="label-m" style={{ color: 'var(--on-surface-variant)' }}>revisados</div></div>
                <div><div className="headline-s" style={{ color: 'var(--success)' }}>{pct}%</div><div className="label-m" style={{ color: 'var(--on-surface-variant)' }}>acertos</div></div>
                <div><div className="headline-s" style={{ color: 'var(--gold)' }}>14→15</div><div className="label-m" style={{ color: 'var(--on-surface-variant)' }}>dias</div></div>
              </div>
            </div>
            <button className="btn btn-filled btn-lg" style={{ width: '100%', marginTop: 18 }} data-tab="dashboard">Voltar ao início</button>
            <button className="btn btn-text" style={{ marginTop: 6 }} data-tab="practice">Praticar mais</button>
          </div>
        </PhoneBody>
      </Frame>
    );
  }

  return (
    <Frame>
      <TopBar progress={(idx / total) * 100} count={idx} total={total} />
      <PhoneBody style={{ display: 'flex', flexDirection: 'column' }}>
        <div style={{ padding: '16px', flex: 1 }}><CardFace card={card} revealed={revealed} index={idx} total={total} onAudio={() => playAudio(card.front)} /></div>
      </PhoneBody>
      <div style={{ flexShrink: 0, padding: '12px 16px 20px' }}>
        {!revealed ? (
          <button className="btn btn-filled btn-lg" style={{ width: '100%' }} onClick={reveal}>Mostrar resposta</button>
        ) : (
          <>
            <div className="body-s" style={{ color: 'var(--on-surface-variant)', textAlign: 'center', marginBottom: 8 }}>Como foi lembrar?</div>
            <Rating onRate={rate} />
          </>
        )}
      </div>
    </Frame>
  );
}
