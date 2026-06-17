import React, { useState, useRef, useEffect } from 'react';
import { Icon, PhoneBody } from '../yomineko/m3';
import { Yomineko } from '../yomineko/mascot';
import { useApp } from './store';

/* ============================================================
   Interactive practice session.
   Card mode (MCQ / chips / tap-build) AND typed mode (real input,
   native keyboard) for kana + numbers, with right/wrong feedback.
   ============================================================ */

const MODES = {
  hiragana: {
    title: 'Hiragana', label: 'QUAL O ROMAJI?', kind: 'kana', typable: true,
    questions: [
      { jp: 'ぎ', romaji: ['gi'], opts: ['ki', 'gi', 'ge', 'go'], ans: 1 },
      { jp: 'ね', romaji: ['ne'], opts: ['ne', 're', 'wa', 'me'], ans: 0 },
      { jp: 'む', romaji: ['mu'], opts: ['nu', 'mu', 'mo', 'ru'], ans: 1 },
      { jp: 'を', romaji: ['wo', 'o'], opts: ['o', 'wo', 'no', 'so'], ans: 1 },
      { jp: 'ふ', romaji: ['fu', 'hu'], opts: ['fu', 'tsu', 'te', 'ha'], ans: 0 },
    ],
  },
  katakana: {
    title: 'Katakana', label: 'QUAL O ROMAJI?', kind: 'kana', typable: true,
    questions: [
      { jp: 'ネ', romaji: ['ne'], opts: ['ne', 're', 'wa', 'shi'], ans: 0 },
      { jp: 'ソ', romaji: ['so'], opts: ['n', 'so', 'tsu', 'ri'], ans: 1 },
      { jp: 'ツ', romaji: ['tsu'], opts: ['shi', 'tsu', 'n', 'so'], ans: 1 },
      { jp: 'リ', romaji: ['ri'], opts: ['ri', 'so', 'n', 'wa'], ans: 0 },
      { jp: 'メ', romaji: ['me'], opts: ['nu', 'me', 'mo', 'ta'], ans: 1 },
    ],
  },
  numbers: {
    title: 'Números', label: 'COMO SE LÊ?', kind: 'number', typable: true,
    questions: [
      { digit: '12', kana: 'じゅうに', opts: ['じゅうに', 'にじゅう', 'じゅういち', 'じゅうさん'], ans: 0 },
      { digit: '600', kana: 'ろっぴゃく', opts: ['ろっぴゃく', 'さんびゃく', 'ろくじゅう', 'はっぴゃく'], ans: 0 },
      { digit: '7', kana: 'なな', opts: ['なな', 'く', 'し', 'ろく'], ans: 0 },
      { digit: '100', kana: 'ひゃく', opts: ['ひゃく', 'せん', 'じゅう', 'まん'], ans: 0 },
    ],
  },
  conjugation: {
    title: 'Conjugação', label: 'FORMA て', kind: 'mcq',
    questions: [
      { big: '食べる', sub: '→ forma て', opts: ['食べて', '食べた', '食べない', '食べます'], ans: 0, audio: 'たべて', jpOpts: true },
      { big: '飲む', sub: '→ forma て', opts: ['飲んで', '飲みて', '飲んだ', '飲まて'], ans: 0, audio: 'のんで', jpOpts: true },
      { big: '行く', sub: '→ forma て', opts: ['行って', '行きて', '行くて', '行いて'], ans: 0, audio: 'いって', jpOpts: true },
    ],
  },
  kanji: {
    title: 'Treinar 学', label: 'SIGNIFICADO', kind: 'mcq',
    questions: [
      { big: '学', opts: ['estudo', 'montanha', 'água', 'pessoa'], ans: 0, audio: 'がく' },
      { big: '学', sub: 'on-yomi', opts: ['ガク', 'セイ', 'スイ', 'ジン'], ans: 0, audio: 'がく', jpOpts: true },
      { big: '本', opts: ['livro', 'árvore', 'sol', 'pessoa'], ans: 0, audio: 'ほん' },
    ],
  },
  particles: {
    title: 'Partículas', label: 'A PARTÍCULA CERTA', kind: 'particle',
    questions: [
      { pre: 'わたし', post: ' がくせい です。', opts: ['は', 'を', 'の', 'に'], ans: 0, audio: 'わたしは がくせい です', pt: '„Eu sou estudante.’' },
      { pre: 'ほん', post: ' よみます。', opts: ['を', 'は', 'が', 'で'], ans: 0, audio: 'ほんを よみます', pt: '„Leio um livro.’' },
      { pre: 'がっこう', post: ' いきます。', opts: ['に', 'を', 'は', 'の'], ans: 0, audio: 'がっこうに いきます', pt: '„Vou para a escola.’' },
    ],
  },
  sentence: {
    title: 'Construir frases', label: 'MONTE A FRASE', kind: 'build',
    questions: [
      { pt: '„A senhora Maria é professora.’', answer: ['マリアさん', 'は', 'せんせい', 'です'], pool: ['です', 'の', 'マリアさん', 'せんせい', 'は', 'を'], audio: 'マリアさんは せんせい です' },
      { pt: '„Eu sou estudante.’', answer: ['わたし', 'は', 'がくせい', 'です'], pool: ['がくせい', 'を', 'わたし', 'は', 'です', 'に'], audio: 'わたしは がくせい です' },
    ],
  },
};

const norm = (s) => (s || '').trim().toLowerCase();

const SessTop = ({ done, total, extra }) => (
  <div style={{ flexShrink: 0, padding: '10px 16px 4px', display: 'flex', alignItems: 'center', gap: 12 }}>
    <button className="icon-btn" data-tab="practice"><Icon name="close" size={22} /></button>
    <div className="linear-prog thick" style={{ flex: 1 }}><i style={{ width: `${(done / total) * 100}%` }} /></div>
    <span className="label-m" style={{ color: 'var(--on-surface-variant)' }}>{done}/{total}</span>
  </div>
);

const InputToggle = ({ input, setInput }) => (
  <div style={{ flexShrink: 0, display: 'flex', justifyContent: 'center', padding: '4px 0' }}>
    <div className="segmented">
      <button className={`seg${input === 'cards' ? ' selected' : ''}`} onClick={() => setInput('cards')}>Cartões</button>
      <button className={`seg${input === 'typing' ? ' selected' : ''}`} onClick={() => setInput('typing')}>Digitar</button>
    </div>
  </div>
);

const DonePane = ({ correct, total, title }) => (
  <PhoneBody style={{ display: 'flex', flexDirection: 'column' }}>
    <div style={{ flex: 1, display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', textAlign: 'center', padding: '0 28px' }}>
      <div style={{ position: 'relative' }}>
        <div style={{ position: 'absolute', inset: '-20%', background: 'radial-gradient(circle, var(--magic-glow), transparent 70%)' }} />
        <div style={{ position: 'relative' }}><Yomineko pose="celebrate" size={150} /></div>
      </div>
      <div className="headline-m" style={{ color: 'var(--on-surface)', marginTop: 8 }}>Prática concluída!</div>
      <div className="body-m" style={{ color: 'var(--on-surface-variant)', marginTop: 4 }}>{title} · {correct}/{total} corretas</div>
      <button className="btn btn-filled btn-lg" style={{ width: '100%', marginTop: 20 }} data-tab="practice">Voltar às práticas</button>
      <button className="btn btn-text" style={{ marginTop: 6 }} data-tab="dashboard">Ir para o início</button>
    </div>
  </PhoneBody>
);

// ---------- card / chip session (kana cards, numbers cards, mcq, particle) ----------
function CardSession({ mode, input, setInput }) {
  const cfg = MODES[mode];
  const { playAudio } = useApp();
  const [idx, setIdx] = useState(0);
  const [picked, setPicked] = useState(null);
  const [correct, setCorrect] = useState(0);
  const [done, setDone] = useState(false);

  const total = cfg.questions.length;
  const q = cfg.questions[idx];
  const answered = picked !== null;
  const isRight = picked === q.ans;
  const isParticle = cfg.kind === 'particle';
  const isNumber = cfg.kind === 'number';
  const audioOf = (qq) => qq.audio || qq.kana || qq.jp || qq.big;
  const stimulus = isNumber ? q.digit : (q.jp || q.big);

  const choose = (i) => {
    if (answered) return;
    setPicked(i);
    if (i === q.ans) setCorrect((c) => c + 1);
    playAudio(audioOf(q));
  };
  const next = () => {
    if (idx + 1 >= total) { setDone(true); return; }
    setIdx((i) => i + 1); setPicked(null);
  };

  if (done) return (<><SessTop done={total} total={total} /><DonePane correct={correct} total={total} title={cfg.title} /></>);

  const optColor = (i) => {
    if (!answered) return { bg: 'var(--surface)', bd: 'var(--outline-variant)', fg: 'var(--on-surface)' };
    if (i === q.ans) return { bg: 'var(--success-container)', bd: 'var(--success)', fg: 'var(--on-success-container)' };
    if (i === picked) return { bg: 'var(--error-container)', bd: 'var(--error)', fg: 'var(--on-error-container)' };
    return { bg: 'var(--surface)', bd: 'var(--outline-variant)', fg: 'var(--on-surface-variant)' };
  };

  return (
    <>
      <SessTop done={idx} total={total} />
      {cfg.typable && <InputToggle input={input} setInput={setInput} />}
      <PhoneBody style={{ display: 'flex', flexDirection: 'column' }}>
        <div style={{ flex: 1, display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', padding: '0 20px', textAlign: 'center' }}>
          <span className="label-m" style={{ color: 'var(--on-surface-variant)' }}>{cfg.label}</span>
          {isParticle ? (
            <>
              <div className="body-m" style={{ color: 'var(--on-surface-variant)', margin: '6px 0 10px' }}>{q.pt}</div>
              <div className="card card-elevated" style={{ padding: '22px 16px', width: '100%' }}>
                <span className="jp-serif" style={{ fontSize: 26 }}>{q.pre} </span>
                <span style={{ display: 'inline-flex', minWidth: 50, height: 36, border: '2px dashed var(--primary)', borderRadius: 10, verticalAlign: 'middle', alignItems: 'center', justifyContent: 'center', background: 'color-mix(in srgb, var(--primary) 8%, transparent)' }} className="jp-serif">{answered ? q.opts[q.ans] : ''}</span>
                <span className="jp-serif" style={{ fontSize: 26 }}>{q.post}</span>
              </div>
            </>
          ) : (
            <>
              <div className={isNumber ? 'display-l' : 'jp-serif'} style={{ fontSize: isNumber ? undefined : (String(stimulus).length > 2 ? 56 : 96), lineHeight: 1.1, color: answered ? (isRight ? 'var(--success)' : 'var(--on-surface)') : 'var(--on-surface)', margin: '8px 0' }}>{stimulus}</div>
              {q.sub && <div className="title-m" style={{ color: 'var(--on-surface-variant)' }}>{q.sub}</div>}
              <button className="btn btn-tonal btn-sm" style={{ marginTop: 6 }} onClick={() => playAudio(audioOf(q))}><Icon name="volume_up" size={18} /> Ouvir</button>
            </>
          )}
          {answered && (
            <div className="body-m" style={{ marginTop: 14, display: 'flex', gap: 6, alignItems: 'center', color: isRight ? 'var(--success)' : 'var(--error)' }}>
              {isRight ? <><Icon name="check_circle" size={18} fill /> Correto!</> : <>Resposta correta: <b>{q.opts[q.ans]}</b></>}
            </div>
          )}
        </div>

        {!answered ? (
          <div style={{ padding: '0 16px 16px', display: 'grid', gridTemplateColumns: isParticle ? '1fr 1fr 1fr 1fr' : '1fr 1fr', gap: 10 }}>
            {q.opts.map((o, i) => {
              const c = optColor(i);
              const jpOpt = q.jpOpts || isParticle || isNumber;
              return (
                <button key={i} onClick={() => choose(i)} className="card card-outlined state" style={{ padding: isParticle ? '14px 0' : '16px 0', textAlign: 'center', cursor: 'pointer', fontFamily: jpOpt ? 'var(--font-jp-serif)' : 'var(--font-body)', fontWeight: 700, fontSize: isParticle ? 22 : (o.length > 3 ? 18 : 22), color: c.fg, border: `1px solid ${c.bd}`, background: c.bg }}>{o}</button>
              );
            })}
          </div>
        ) : (
          <div style={{ padding: '0 16px 16px' }}>
            <button className="btn btn-filled btn-lg" style={{ width: '100%' }} onClick={next}>{idx + 1 >= total ? 'Concluir' : 'Próxima'} <Icon name="arrow_forward" size={20} /></button>
          </div>
        )}
      </PhoneBody>
    </>
  );
}

// ---------- typed session (kana → romaji, number → digit) ----------
function TypedSession({ mode, input, setInput }) {
  const cfg = MODES[mode];
  const { playAudio } = useApp();
  const [idx, setIdx] = useState(0);
  const [typed, setTyped] = useState('');
  const [status, setStatus] = useState(null); // 'ok' | 'no'
  const [correct, setCorrect] = useState(0);
  const [done, setDone] = useState(false);
  const ref = useRef(null);

  const total = cfg.questions.length;
  const q = cfg.questions[idx];
  const isNumber = cfg.kind === 'number';
  const prompt = isNumber ? q.kana : q.jp;            // typing always shows the JP, you type the answer
  const accepted = isNumber ? [q.digit] : q.romaji;
  const audioOf = isNumber ? q.kana : q.jp;

  useEffect(() => { if (!status && ref.current) ref.current.focus(); }, [idx, status]);

  const confirm = (val) => {
    if (status) return;
    const ok = accepted.map(norm).includes(norm(val));
    setStatus(ok ? 'ok' : 'no');
    if (ok) setCorrect((c) => c + 1);
    playAudio(audioOf);
  };
  const onChange = (e) => {
    const v = e.target.value;
    setTyped(v);
    if (!status && accepted.map(norm).includes(norm(v))) confirm(v);
  };
  const next = () => {
    if (idx + 1 >= total) { setDone(true); return; }
    setIdx((i) => i + 1); setTyped(''); setStatus(null);
  };

  if (done) return (<><SessTop done={total} total={total} /><DonePane correct={correct} total={total} title={cfg.title} /></>);

  const borderC = status === 'ok' ? 'var(--success)' : status === 'no' ? 'var(--error)' : 'var(--primary)';

  return (
    <>
      <SessTop done={idx} total={total} />
      <InputToggle input={input} setInput={setInput} />
      <PhoneBody style={{ display: 'flex', flexDirection: 'column' }}>
        <div style={{ flex: 1, display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', padding: '0 20px', textAlign: 'center' }}>
          <span className="label-m" style={{ color: 'var(--on-surface-variant)' }}>{isNumber ? 'DIGITE O NÚMERO' : 'DIGITE O ROMAJI'}</span>
          <div className="jp-serif" style={{ fontSize: isNumber ? 48 : 96, lineHeight: 1.1, color: 'var(--on-surface)', margin: '10px 0' }}>{prompt}</div>
          <div className={`field field-outlined${status ? '' : ' focused'}`} style={{ width: '100%', maxWidth: 220, textAlign: 'center', borderColor: borderC }}>
            <input
              ref={ref}
              value={typed}
              onChange={onChange}
              onKeyDown={(e) => { if (e.key === 'Enter') confirm(typed); }}
              readOnly={!!status}
              inputMode={isNumber ? 'numeric' : 'text'}
              autoCapitalize="none" autoCorrect="off" spellCheck={false}
              placeholder={isNumber ? '123' : 'romaji'}
              style={{ textAlign: 'center', fontSize: 28, fontFamily: 'var(--font-body)', fontWeight: 700, color: borderC }}
            />
          </div>
          {!status && <div className="body-s" style={{ color: 'var(--on-surface-variant)', marginTop: 8 }}>auto-confirma ao completar · Enter</div>}
          {status === 'ok' && <div className="body-m" style={{ marginTop: 12, display: 'flex', gap: 6, alignItems: 'center', color: 'var(--success)' }}><Icon name="check_circle" size={18} fill /> Correto!</div>}
          {status === 'no' && <div className="body-m" style={{ marginTop: 12, color: 'var(--error)' }}>Resposta correta: <b>{accepted[0]}</b></div>}
          <button className="btn btn-tonal btn-sm" style={{ marginTop: 14 }} onClick={() => playAudio(audioOf)}><Icon name="volume_up" size={18} /> Ouvir</button>
        </div>
        <div style={{ padding: '0 16px 16px' }}>
          {!status ? (
            <button className="btn btn-filled btn-lg" style={{ width: '100%' }} onClick={() => confirm(typed)} disabled={!typed}>Verificar</button>
          ) : (
            <button className="btn btn-filled btn-lg" style={{ width: '100%' }} onClick={next}>{idx + 1 >= total ? 'Concluir' : 'Próxima'} <Icon name="arrow_forward" size={20} /></button>
          )}
        </div>
      </PhoneBody>
    </>
  );
}

// ---------- tap-to-build sentence session ----------
function BuildSession({ mode }) {
  const cfg = MODES[mode];
  const { playAudio } = useApp();
  const [idx, setIdx] = useState(0);
  const [chosen, setChosen] = useState([]);
  const [status, setStatus] = useState(null);
  const [correct, setCorrect] = useState(0);
  const [done, setDone] = useState(false);

  const total = cfg.questions.length;
  const q = cfg.questions[idx];

  const add = (poolIdx) => { if (status) return; setChosen((c) => [...c, poolIdx]); };
  const removeAt = (k) => { if (status) return; setChosen((c) => c.filter((_, i) => i !== k)); };
  const check = () => {
    const built = chosen.map((k) => q.pool[k]);
    const ok = built.length === q.answer.length && built.every((b, i) => b === q.answer[i]);
    setStatus(ok ? 'ok' : 'no');
    if (ok) { setCorrect((c) => c + 1); playAudio(q.audio); }
  };
  const next = () => {
    if (idx + 1 >= total) { setDone(true); return; }
    setIdx((i) => i + 1); setChosen([]); setStatus(null);
  };

  if (done) return (<><SessTop done={total} total={total} /><DonePane correct={correct} total={total} title={cfg.title} /></>);

  return (
    <>
      <SessTop done={idx} total={total} />
      <PhoneBody style={{ display: 'flex', flexDirection: 'column' }}>
        <div style={{ flex: 1, padding: '12px 16px' }}>
          <div className="card card-filled" style={{ padding: '12px 16px', marginBottom: 14 }}>
            <span className="label-m" style={{ color: 'var(--on-surface-variant)' }}>TRADUZA</span>
            <div className="title-m" style={{ color: 'var(--on-surface)' }}>{q.pt}</div>
          </div>
          <div style={{ minHeight: 64, border: `2px dashed ${status === 'no' ? 'var(--error)' : 'var(--primary)'}`, borderRadius: 'var(--r-md)', background: 'color-mix(in srgb, var(--primary) 5%, transparent)', padding: '10px', display: 'flex', gap: 6, flexWrap: 'wrap', alignItems: 'flex-start' }}>
            {chosen.map((k, i) => (
              <button key={i} onClick={() => removeAt(i)} className="chip selected" style={{ fontFamily: 'var(--font-jp)', fontSize: 16, cursor: 'pointer', border: 'none' }}>{q.pool[k]}</button>
            ))}
          </div>
          {status && (
            <div className="body-m" style={{ marginTop: 12, textAlign: 'center', display: 'flex', gap: 6, justifyContent: 'center', alignItems: 'center', color: status === 'ok' ? 'var(--success)' : 'var(--error)' }}>
              {status === 'ok' ? <><Icon name="check_circle" size={18} fill /> Correto!</> : <span>Ordem certa: <span className="jp">{q.answer.join(' ')}</span></span>}
            </div>
          )}
          <div className="label-m" style={{ color: 'var(--on-surface-variant)', margin: '18px 0 8px' }}>BLOCOS</div>
          <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap', justifyContent: 'center' }}>
            {q.pool.map((b, i) => (
              <button key={i} onClick={() => add(i)} disabled={chosen.includes(i)} className="chip" style={{ fontFamily: 'var(--font-jp)', fontSize: 16, cursor: 'pointer', opacity: chosen.includes(i) ? 0.3 : 1 }}>{b}</button>
            ))}
          </div>
        </div>
        <div style={{ padding: '0 16px 16px', display: 'flex', gap: 10 }}>
          {!status ? (
            <>
              <button className="btn btn-outlined" style={{ flex: 1 }} onClick={() => setChosen([])}>Limpar</button>
              <button className="btn btn-filled" style={{ flex: 2 }} onClick={check} disabled={!chosen.length}>Verificar</button>
            </>
          ) : (
            <button className="btn btn-filled btn-lg" style={{ flex: 1 }} onClick={next}>{idx + 1 >= total ? 'Concluir' : 'Próxima'} <Icon name="arrow_forward" size={20} /></button>
          )}
        </div>
      </PhoneBody>
    </>
  );
}

export function SessionApp({ mode = 'hiragana' }) {
  const cfg = MODES[mode] || MODES.hiragana;
  const [input, setInput] = useState('cards');
  let body;
  if (cfg.kind === 'build') body = <BuildSession key={mode} mode={mode} />;
  else if (cfg.typable && input === 'typing') body = <TypedSession key={mode + '-t'} mode={mode} input={input} setInput={setInput} />;
  else body = <CardSession key={mode + '-c'} mode={mode} input={input} setInput={setInput} />;
  return (
    <div style={{ height: '100%', display: 'flex', flexDirection: 'column', background: 'var(--surface)' }}>
      {body}
    </div>
  );
}
