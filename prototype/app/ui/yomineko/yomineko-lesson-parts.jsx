import React from 'react';
import { Icon } from './m3';
import { Yomineko } from './mascot';
import { playAudio } from '../app/audio';

/* ============================================================
   Yomineko — LESSON page (hi-fi, decluttered)
   Secondary content (sentence breakdown, kanji readings,
   grammar & culture notes, word details) moves to tap-sheets.
   ============================================================ */

// ---------- Lesson content (partícula は) ----------
const LESSON_WA = {
  id: "L020",
  course: "N5",
  topic: "Partículas básicas",
  title: "A partícula は",
  subtitle: "Marcando o tópico da frase",
  estimated: 18,
  progress: 0.45,
  index: 20, total: 25,
};

// ---------- Small building blocks ----------

// Section heading with a subtle grimoire tick
const LHeading = ({ children, n }) => (
  <div style={{ display:'flex', alignItems:'center', gap:10, margin:'22px 20px 8px' }}>
    <span style={{ width:6, height:22, borderRadius:99, background:'var(--primary)' }}/>
    <span className="title-l" style={{ color:'var(--on-surface)' }}>{children}</span>
  </div>
);

const LBody = ({ children }) => (
  <p className="body-l" style={{ color:'var(--on-surface-variant)', margin:'0 20px 12px' }}>{children}</p>
);

// Compact note banner — headline inline, full text on tap
const NoteRow = ({ tone = "info", title, onOpen, hint = "Toque para ler" }) => {
  const map = {
    info:    { ic:"lightbulb",   bg:"var(--primary-container)",   fg:"var(--on-primary-container)" },
    grammar: { ic:"menu_book",   bg:"color-mix(in srgb, var(--magic-1) 14%, var(--surface))", fg:"var(--magic-1)" },
    culture: { ic:"temple_buddhist", bg:"var(--tertiary-container)", fg:"var(--on-tertiary-container)" },
  }[tone];
  return (
    <button onClick={onOpen} className="state" style={{
      display:'flex', alignItems:'center', gap:12, width:'calc(100% - 40px)', margin:'8px 20px',
      background: map.bg, color: map.fg, border:'none', borderRadius:'var(--r-md)', padding:'12px 14px',
      cursor:'pointer', textAlign:'left'
    }}>
      <span className="material-symbols-rounded" style={{ fontSize:22 }}>{map.ic}</span>
      <span style={{ flex:1, minWidth:0 }}>
        <span className="title-s" style={{ display:'block', color:map.fg }}>{title}</span>
        <span className="body-s" style={{ opacity:0.8 }}>{hint}</span>
      </span>
      <span className="material-symbols-rounded" style={{ fontSize:20, opacity:0.7 }}>chevron_right</span>
    </button>
  );
};

// Example sentence — clean; tap opens breakdown
const ExampleCard = ({ jp, reading, pt, onBreakdown, furi = true }) => (
  <div className="card card-filled" style={{ margin:'8px 20px', padding:'16px' }}>
    <div className="jp-serif" style={{ fontSize:24, lineHeight:1.6, color:'var(--on-surface)', textAlign:'center' }}>{jp}</div>
    {furi && <div className="body-s" style={{ textAlign:'center', color:'var(--on-surface-variant)', marginTop:2 }}>{reading}</div>}
    <hr className="divider" style={{ margin:'12px 0' }}/>
    <div style={{ display:'flex', alignItems:'center', justifyContent:'space-between', gap:10 }}>
      <span className="body-m" style={{ color:'var(--on-surface-variant)' }}>{pt}</span>
      <div style={{ display:'flex', gap:4, flexShrink:0 }}>
        <button className="icon-btn" title="Ouvir" onClick={()=>playAudio(jp)}><Icon name="volume_up" size={20}/></button>
        <button className="icon-btn icon-btn-tonal" onClick={onBreakdown} title="Analisar"><Icon name="account_tree" size={20}/></button>
      </div>
    </div>
  </div>
);

// Vocab row — word + reading + meaning + audio; tap opens word sheet
const VocabRow = ({ w, onOpen, last }) => (
  <div className="list-item state" onClick={onOpen} style={{ borderBottom: last? 'none':'1px solid var(--outline-variant)' }}>
    <div style={{ flex:1, minWidth:0 }}>
      <div style={{ display:'flex', alignItems:'baseline', gap:8 }}>
        <span className="jp" style={{ fontSize:20, color:'var(--on-surface)' }}>{w.jp}</span>
        <span className="body-s" style={{ color:'var(--on-surface-variant)' }}>{w.reading}</span>
      </div>
      <div className="body-m" style={{ color:'var(--on-surface-variant)' }}>{w.pt} · <span style={{ opacity:.7 }}>{w.pos}</span></div>
    </div>
    <button className="icon-btn" onClick={(e)=>{e.stopPropagation(); playAudio(w.jp);}} title="Ouvir"><Icon name="volume_up" size={20}/></button>
    <span className="material-symbols-rounded" style={{ fontSize:20, color:'var(--on-surface-variant)' }}>chevron_right</span>
  </div>
);

// ---------- Exercise (inline, Material) ----------
const ExerciseMCQ = () => {
  const opts = ["ha","wa","ba","pa"];
  const answer = 1;
  const [picked, setPicked] = React.useState(null);
  const answered = picked !== null;
  const isRight = picked === answer;
  return (
    <div className="card card-outlined" style={{ margin:'12px 20px', borderColor:'var(--primary)', borderWidth:1, background:'color-mix(in srgb, var(--primary) 4%, var(--surface))' }}>
      <div style={{ display:'flex', alignItems:'center', gap:8, marginBottom:10 }}>
        <span className="pill pill-magic"><Icon name="quiz" size={14}/> Exercício 1</span>
        <span className="body-s" style={{ color:'var(--on-surface-variant)', marginLeft:'auto' }}>toque na resposta</span>
      </div>
      <div className="title-m" style={{ color:'var(--on-surface)', marginBottom:12 }}>Como se pronuncia a partícula は?</div>
      <div style={{ display:'grid', gridTemplateColumns:'1fr 1fr', gap:8 }}>
        {opts.map((o,i)=>{
          let bg='var(--surface)', fg='var(--on-surface)', bd='var(--outline-variant)';
          if (answered && i===answer) { bg='var(--success-container)'; fg='var(--on-success-container)'; bd='var(--success)'; }
          else if (answered && i===picked) { bg='var(--error-container)'; fg='var(--on-error-container)'; bd='var(--error)'; }
          return (
            <button key={i} onClick={()=>{ if(!answered) setPicked(i); }} disabled={answered} className="state" style={{ display:'flex', alignItems:'center', gap:10, border:`1px solid ${bd}`, background:bg, color:fg, borderRadius:'var(--r-md)', padding:'12px 14px', cursor: answered?'default':'pointer', fontFamily:'var(--font-body)', fontWeight:700, fontSize:18 }}>
              <span style={{ width:24, height:24, borderRadius:99, border:`2px solid ${bd}`, display:'inline-flex', alignItems:'center', justifyContent:'center', fontSize:12, fontFamily:'var(--font-body)' }}>{String.fromCharCode(65+i)}</span>
              {o}
            </button>
          );
        })}
      </div>
      {answered && isRight && <div style={{ display:'flex', gap:8, alignItems:'center', marginTop:12, color:'var(--success)' }}><Icon name="check_circle" size={18} fill/><span className="body-m">Correto! は como partícula lê-se „wa'.</span></div>}
      {answered && !isRight && <div style={{ display:'flex', gap:8, alignItems:'center', justifyContent:'space-between', marginTop:12 }}><span style={{ display:'flex', gap:8, alignItems:'center', color:'var(--error)' }}><Icon name="cancel" size={18} fill/><span className="body-m">Quase — a resposta é „wa'.</span></span><button className="btn btn-text btn-sm" onClick={()=>setPicked(null)}>Tentar de novo</button></div>}
    </div>
  );
};

const ExerciseParticle = () => {
  const chips = ["は","の","を","が"];
  const answer = "は";
  const [picked, setPicked] = React.useState(null);
  const answered = picked !== null;
  const isRight = picked === answer;
  const blankBorder = answered ? (isRight ? 'var(--success)' : 'var(--error)') : 'var(--primary)';
  const blankBg = answered ? (isRight ? 'var(--success-container)' : 'var(--error-container)') : 'color-mix(in srgb, var(--primary) 8%, transparent)';
  return (
    <div className="card card-outlined" style={{ margin:'12px 20px', borderColor:'var(--primary)', background:'color-mix(in srgb, var(--primary) 4%, var(--surface))' }}>
      <div style={{ display:'flex', alignItems:'center', gap:8, marginBottom:10 }}>
        <span className="pill pill-magic"><Icon name="quiz" size={14}/> Exercício 2</span>
        <span className="body-s" style={{ color:'var(--on-surface-variant)', marginLeft:'auto' }}>toque na partícula</span>
      </div>
      <div className="body-m" style={{ color:'var(--on-surface-variant)', marginBottom:8 }}>„Quanto a mim, sou brasileiro(a).'</div>
      <div className="card card-filled" style={{ textAlign:'center', padding:'16px' }}>
        <span className="jp-serif" style={{ fontSize:22 }}>わたし </span>
        <span className="jp-serif" style={{ display:'inline-flex', minWidth:48, height:34, border:`2px ${answered?'solid':'dashed'} ${blankBorder}`, borderRadius:8, verticalAlign:'middle', alignItems:'center', justifyContent:'center', background:blankBg, fontSize:20 }}>{answered ? answer : ''}</span>
        <span className="jp-serif" style={{ fontSize:22 }}> ブラジルじん です。</span>
      </div>
      <div style={{ display:'flex', gap:8, justifyContent:'center', flexWrap:'wrap', marginTop:12 }}>
        {chips.map((p,i)=>{
          const sel = picked===p;
          let extra = {};
          if (answered && p===answer) extra = { background:'var(--success-container)', color:'var(--on-success-container)', borderColor:'var(--success)' };
          else if (answered && sel) extra = { background:'var(--error-container)', color:'var(--on-error-container)', borderColor:'var(--error)' };
          return <button key={i} onClick={()=>{ if(!answered) setPicked(p); }} disabled={answered} className={`chip${sel?' selected':''}`} style={{ fontSize:18, fontFamily:'var(--font-jp-serif)', cursor: answered?'default':'pointer', ...extra }}>{p}</button>;
        })}
      </div>
      {answered && <div style={{ display:'flex', gap:8, alignItems:'center', justifyContent:'space-between', marginTop:12 }}>
        <span style={{ display:'flex', gap:6, alignItems:'center', color: isRight?'var(--success)':'var(--error)' }}><Icon name={isRight?'check_circle':'cancel'} size={18} fill/><span className="body-m">{isRight?'Correto! „わたしは…" — quanto a mim.':'A resposta é „は".'}</span></span>
        {!isRight && <button className="btn btn-text btn-sm" onClick={()=>setPicked(null)}>Tentar de novo</button>}
      </div>}
    </div>
  );
};

// ============================================================
// SHEETS (tap-only secondary content)
// ============================================================

// Sheet shell — bottom sheet (mobile) OR side sheet (desktop)
const SheetShell = ({ mode = "bottom", children }) => {
  if (mode === "side") {
    return <div style={{ height:'100%', display:'flex', flexDirection:'column' }}>{children}</div>;
  }
  return (
    <div className="bottom-sheet">
      <div className="sheet-handle"/>
      {children}
    </div>
  );
};

// Sentence breakdown
const BreakdownSheet = ({ mode = "bottom" }) => (
  <SheetShell mode={mode}>
    <div style={{ padding:'0 20px' }}>
      <div style={{ display:'flex', alignItems:'center', justifyContent:'space-between', marginBottom:8 }}>
        <span className="title-l">Análise da frase</span>
        <button className="icon-btn" data-close><Icon name="close" size={22}/></button>
      </div>
      <div className="jp-serif" style={{ fontSize:26, textAlign:'center', margin:'8px 0', color:'var(--on-surface)' }}>わたしは がくせい です。</div>
      <div style={{ display:'flex', gap:8, justifyContent:'center', marginBottom:12 }}>
        <button className="btn btn-tonal btn-sm" onClick={()=>playAudio('わたしは がくせい です。')}><Icon name="volume_up" size={18}/> Frase inteira</button>
        <button className="btn btn-outlined btn-sm"><Icon name="slow_motion_video" size={18}/> Lento ½×</button>
      </div>
      <hr className="divider"/>
      {[
        { surf:"わたし", read:"watashi", pt:"eu", type:"pronome" },
        { surf:"は", read:"wa", pt:"partícula de tópico", type:"partícula" },
        { surf:"がくせい", read:"gakusei", pt:"estudante", type:"substantivo" },
        { surf:"です", read:"desu", pt:"é / sou (cópula polida)", type:"gramática" },
      ].map((s,i)=>(
        <div key={i} className="list-item" style={{ padding:'10px 0' }}>
          <div style={{ minWidth:64 }}>
            <div className="jp-serif" style={{ fontSize:22, color:'var(--on-surface)' }}>{s.surf}</div>
            <div className="body-s" style={{ color:'var(--on-surface-variant)' }}>{s.read}</div>
          </div>
          <div className="list-text">
            <div className="list-headline" style={{ fontSize:14 }}>{s.pt}</div>
            <div className="label-s" style={{ color:'var(--primary)', textTransform:'uppercase' }}>{s.type}</div>
          </div>
          <button className="icon-btn" onClick={()=>playAudio(s.surf)}><Icon name="volume_up" size={20}/></button>
        </div>
      ))}
    </div>
  </SheetShell>
);

// Word sheet
const WordSheet = ({ mode = "bottom" }) => (
  <SheetShell mode={mode}>
    <div style={{ padding:'0 20px' }}>
      <div style={{ display:'flex', alignItems:'flex-start', justifyContent:'space-between' }}>
        <div>
          <span className="pill pill-outline" style={{ marginBottom:6 }}>SUBSTANTIVO</span>
          <div className="jp-serif" style={{ fontSize:40, color:'var(--on-surface)' }}>がくせい</div>
          <div className="body-m" style={{ color:'var(--on-surface-variant)' }}>gakusei · pitch ①</div>
        </div>
        <button className="icon-btn" data-close><Icon name="close" size={22}/></button>
      </div>
      <div className="headline-s" style={{ margin:'8px 0', color:'var(--on-surface)' }}>estudante</div>
      <div style={{ display:'flex', gap:8 }}>
        <button className="btn btn-tonal btn-sm" onClick={()=>playAudio('がくせい')}><Icon name="volume_up" size={18}/> Ouvir</button>
        <button className="btn btn-outlined btn-sm"><Icon name="bookmark_add" size={18}/> Salvar</button>
      </div>
      <hr className="divider" style={{ margin:'16px 0' }}/>
      <div className="label-m" style={{ color:'var(--on-surface-variant)', marginBottom:8 }}>KANJI QUE A COMPÕEM</div>
      <div style={{ display:'flex', gap:10 }}>
        {[{k:"学",m:"estudo"},{k:"生",m:"vida"}].map((x,i)=>(
          <button key={i} data-go="kanjiDetail" className="card card-filled state" style={{ flex:1, textAlign:'center', cursor:'pointer', padding:'12px' }}>
            <div className="jp-serif" style={{ fontSize:40, color:'var(--on-surface)' }}>{x.k}</div>
            <div className="body-s" style={{ color:'var(--on-surface-variant)' }}>{x.m}</div>
          </button>
        ))}
      </div>
    </div>
  </SheetShell>
);

// Kanji sheet — richer; has a clear path to the full kanji screen
const KanjiSheet = ({ mode = "bottom" }) => (
  <SheetShell mode={mode}>
    <div style={{ padding:'0 20px 8px', overflowY: mode==="side"?'auto':'visible', flex: mode==="side"?1:'none' }}>
      <div style={{ display:'flex', alignItems:'center', justifyContent:'space-between', marginBottom:8 }}>
        <span className="pill pill-primary"><Icon name="translate" size={14}/> KANJI</span>
        <button className="icon-btn" data-close><Icon name="close" size={22}/></button>
      </div>
      <div style={{ display:'flex', gap:16, alignItems:'flex-start' }}>
        <div className="jp-serif" style={{ fontSize:96, lineHeight:1, color:'var(--on-surface)' }}>学</div>
        <div style={{ flex:1 }}>
          <div className="headline-s" style={{ color:'var(--on-surface)' }}>estudo, aprender</div>
          <div className="body-m" style={{ color:'var(--on-surface-variant)' }}>がく · まな(ぶ)</div>
          <div style={{ display:'flex', gap:6, flexWrap:'wrap', marginTop:8 }}>
            <span className="pill pill-outline">N5</span>
            <span className="pill pill-outline">8 traços</span>
            <span className="pill pill-outline">grau 1</span>
            <span className="pill pill-success">aprendendo</span>
          </div>
        </div>
      </div>
      <div style={{ display:'flex', gap:6, marginTop:12 }}>
        <button className="btn btn-tonal btn-sm"><Icon name="animation" size={18}/> Ver traços</button>
        <button className="icon-btn icon-btn-tonal"><Icon name="volume_up" size={20}/></button>
        <button className="icon-btn icon-btn-tonal"><Icon name="bookmark_add" size={20}/></button>
      </div>

      {/* stroke order strip */}
      <hr className="divider" style={{ margin:'16px 0 12px' }}/>
      <div className="label-m" style={{ color:'var(--on-surface-variant)', marginBottom:8 }}>ORDEM DOS TRAÇOS</div>
      <div style={{ display:'grid', gridTemplateColumns:'repeat(4, 1fr)', gap:8 }}>
        {[1,2,3,4,5,6,7,8].map(n=>(
          <div key={n} style={{ aspectRatio:'1', borderRadius:'var(--r-sm)', background:'var(--surface-container-high)', display:'flex', alignItems:'center', justifyContent:'center', position:'relative' }}>
            <span className="jp-serif" style={{ fontSize:26, color: n<=8?'var(--on-surface)':'var(--outline)', opacity: 0.25 + n*0.09 }}>学</span>
            <span className="label-s" style={{ position:'absolute', top:4, left:6, color:'var(--on-surface-variant)' }}>{n}</span>
          </div>
        ))}
      </div>

      {/* readings */}
      <hr className="divider" style={{ margin:'16px 0' }}/>
      <div style={{ display:'grid', gridTemplateColumns:'1fr 1fr', gap:12 }}>
        <div className="card card-filled" style={{ padding:'10px 12px' }}><div className="label-m" style={{ color:'var(--on-surface-variant)' }}>音 ON-YOMI</div><div className="jp" style={{ fontSize:18 }}>ガク</div></div>
        <div className="card card-filled" style={{ padding:'10px 12px' }}><div className="label-m" style={{ color:'var(--on-surface-variant)' }}>訓 KUN-YOMI</div><div className="jp" style={{ fontSize:18 }}>まな(ぶ)</div></div>
      </div>

      {/* radicals */}
      <hr className="divider" style={{ margin:'16px 0' }}/>
      <div className="label-m" style={{ color:'var(--on-surface-variant)', marginBottom:6 }}>COMPONENTES</div>
      <div style={{ display:'flex', gap:8 }}>
        <span className="chip"><span className="jp-serif" style={{ fontSize:18 }}>⺍</span> coroa</span>
        <span className="chip"><span className="jp-serif" style={{ fontSize:18 }}>子</span> criança</span>
      </div>

      {/* words */}
      <hr className="divider" style={{ margin:'16px 0' }}/>
      <div className="label-m" style={{ color:'var(--on-surface-variant)', marginBottom:6 }}>APARECE EM</div>
      {[{jp:"学生",r:"がくせい",pt:"estudante"},{jp:"学校",r:"がっこう",pt:"escola"},{jp:"大学",r:"だいがく",pt:"universidade"},{jp:"学ぶ",r:"まなぶ",pt:"aprender"}].map((x,i)=>(
        <div key={i} style={{ display:'flex', justifyContent:'space-between', alignItems:'center', padding:'7px 0', borderTop: i>0?'1px solid var(--outline-variant)':'none' }}>
          <span><span className="jp" style={{ fontSize:16 }}>{x.jp}</span> <span className="body-s" style={{ color:'var(--on-surface-variant)' }}>{x.r}</span></span>
          <span className="body-m" style={{ color:'var(--on-surface-variant)' }}>{x.pt}</span>
        </div>
      ))}

      {/* go to full screen */}
      <button className="btn btn-filled btn-block" style={{ margin:'18px 0 4px' }} data-page="kanjiDetail">
        Abrir página completa do kanji <Icon name="open_in_full" size={18}/>
      </button>
    </div>
  </SheetShell>
);

// Grammar sheet
const GrammarSheet = ({ mode = "bottom" }) => (
  <SheetShell mode={mode}>
    <div style={{ padding:'0 20px' }}>
      <div style={{ display:'flex', alignItems:'center', justifyContent:'space-between', marginBottom:8 }}>
        <span className="pill pill-magic"><Icon name="menu_book" size={14}/> GRAMÁTICA</span>
        <button className="icon-btn" data-close><Icon name="close" size={22}/></button>
      </div>
      <div className="jp-serif" style={{ fontSize:34, color:'var(--on-surface)' }}>～は</div>
      <div className="title-m" style={{ color:'var(--on-surface)' }}>A partícula de tópico (wa)</div>
      <p className="body-l" style={{ color:'var(--on-surface-variant)', marginTop:8 }}>
        は marca o <b>tópico</b> da frase — o „quanto a…' sobre o qual se vai falar. Escreve-se com o kana は mas, como partícula, lê-se <b>„wa'</b>.
      </p>
      <div className="card card-filled" style={{ marginTop:8 }}>
        <div className="label-m" style={{ color:'var(--on-surface-variant)', marginBottom:6 }}>PADRÃO</div>
        <div className="jp-serif" style={{ fontSize:18, color:'var(--on-surface)' }}>[Tópico] は [comentário] です。</div>
      </div>
      <button className="btn btn-tonal btn-block" style={{ marginTop:12 }} data-go="practiceConfig" data-params={JSON.stringify({ mode:'particles' })}><Icon name="target" size={18}/> Praticar partículas</button>
    </div>
  </SheetShell>
);

// Culture sheet
const CultureSheet = ({ mode = "bottom" }) => (
  <SheetShell mode={mode}>
    <div style={{ padding:'0 20px' }}>
      <div style={{ display:'flex', alignItems:'center', justifyContent:'space-between', marginBottom:8 }}>
        <span className="pill" style={{ background:'var(--tertiary-container)', color:'var(--on-tertiary-container)' }}><Icon name="temple_buddhist" size={14}/> CULTURA</span>
        <button className="icon-btn" data-close><Icon name="close" size={22}/></button>
      </div>
      <div className="title-l" style={{ color:'var(--on-surface)' }}>Por que partículas existem?</div>
      <p className="body-l" style={{ color:'var(--on-surface-variant)', marginTop:8 }}>
        O japonês não usa ordem fixa de palavras como o português. As partículas „etiquetam' cada parte da frase — qual é o tópico, o objeto, o destino. Por isso a ordem é flexível e a partícula é essencial: ela carrega o sentido que, em português, viria da posição na frase.
      </p>
      <div style={{ display:'flex', alignItems:'center', gap:12, marginTop:12, padding:'12px', background:'var(--surface-container-high)', borderRadius:'var(--r-md)' }}>
        <Yomineko pose="reading" size={56} glow={false}/>
        <span className="body-m" style={{ color:'var(--on-surface-variant)' }}>„Pense nas partículas como pequenos feitiços que dizem o papel de cada palavra.' — Yomineko</span>
      </div>
    </div>
  </SheetShell>
);

export {
  LESSON_WA, LHeading, LBody, NoteRow, ExampleCard, VocabRow,
  ExerciseMCQ, ExerciseParticle, SheetShell,
  BreakdownSheet, WordSheet, KanjiSheet, GrammarSheet, CultureSheet
};
