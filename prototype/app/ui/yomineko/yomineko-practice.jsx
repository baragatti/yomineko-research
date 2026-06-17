import React from 'react';
import { Icon, PhoneFrame, DesktopFrame, PhoneBody, AppBar, NavBar, NavDrawer } from './m3';
import { Yomineko } from './mascot';

/* ============================================================
   Yomineko — PRACTICE: hub + sessions (mobile + desktop)
   ============================================================ */

const PRACTICES = [
  { jp:"ひらがな", t:"Hiragana", d:"Reconhecer os 46 kana e variações.", pool:"aprendidos", ic:"abc", badge:"hoje", mode:"hiragana" },
  { jp:"カタカナ", t:"Katakana", d:"Estrangeirismos e ênfase.", pool:"aprendidos", ic:"abc", mode:"katakana" },
  { jp:"は が を に", t:"Partículas", d:"A partícula certa na lacuna.", pool:"N5", ic:"link", mode:"particles" },
  { jp:"わたしは…", t:"Construir frases", d:"Montar a partir dos blocos.", pool:"N5", ic:"reorder", mode:"sentence" },
  { jp:"食べる→て", t:"Conjugação", d:"Forma て, た, ない e outras.", pool:"verbos", ic:"swap_calls", mode:"conjugation" },
  { jp:"1 2 3 / 人", t:"Números", d:"Cardinais e contadores.", pool:"fixo", ic:"tag", mode:"numbers" },
];

const PracticeHubMobile = ({ theme = "light" }) => (
  <PhoneFrame theme={theme} label="Prática — hub mobile">
    <AppBar title="Prática"/>
    <PhoneBody>
      <div style={{ padding:'4px 16px 8px' }}>
        <div className="body-m" style={{ color:'var(--on-surface-variant)', marginBottom:12 }}>Drills focados. Você escolhe o que treinar — o conteúdo vem das suas lições.</div>
        <div style={{ display:'grid', gridTemplateColumns:'1fr 1fr', gap:10 }}>
          {PRACTICES.map((p,i)=>(
            <button key={i} data-go="practiceConfig" data-params={JSON.stringify({ mode:p.mode })} className="card card-elevated state" style={{ padding:'14px', textAlign:'left', border:'none', cursor:'pointer', position:'relative' }}>
              {p.badge && <span className="pill pill-gold" style={{ position:'absolute', top:-8, right:10, height:20 }}>{p.badge}</span>}
              <div style={{ width:40, height:40, borderRadius:'var(--r-md)', background:'var(--primary-container)', color:'var(--on-primary-container)', display:'flex', alignItems:'center', justifyContent:'center', marginBottom:8 }}><Icon name={p.ic} size={22}/></div>
              <div className="jp" style={{ fontSize:13, color:'var(--on-surface-variant)' }}>{p.jp}</div>
              <div className="title-s" style={{ color:'var(--on-surface)' }}>{p.t}</div>
              <div className="body-s" style={{ color:'var(--on-surface-variant)', marginTop:2 }}>{p.d}</div>
            </button>
          ))}
        </div>
      </div>
    </PhoneBody>
    <NavBar active="practice" badge={{ review:12 }}/>
  </PhoneFrame>
);

const PracticeHubDesktop = ({ theme = "light" }) => (
  <DesktopFrame theme={theme} label="Prática — hub desktop" url="app.yomineko.com/pratica">
    <NavDrawer active="practice" badge={{ review:12 }} drawer={true}/>
    <div style={{ flex:1, overflowY:'auto', padding:'28px 32px' }}>
      <div className="headline-l" style={{ color:'var(--on-surface)', marginBottom:4 }}>Prática</div>
      <div className="body-m" style={{ color:'var(--on-surface-variant)', marginBottom:20 }}>Diferente da revisão, aqui você escolhe a habilidade. O conteúdo vem das suas lições concluídas.</div>
      <div style={{ display:'grid', gridTemplateColumns:'repeat(auto-fit, minmax(300px,1fr))', gap:16, maxWidth:1000 }}>
        {PRACTICES.map((p,i)=>(
          <div key={i} className="card card-elevated" style={{ padding:'20px', position:'relative' }}>
            {p.badge && <span className="pill pill-gold" style={{ position:'absolute', top:14, right:14 }}>{p.badge}</span>}
            <div style={{ display:'flex', gap:14, alignItems:'center' }}>
              <div style={{ width:52, height:52, borderRadius:'var(--r-md)', background:'var(--primary-container)', color:'var(--on-primary-container)', display:'flex', alignItems:'center', justifyContent:'center', flexShrink:0 }}><Icon name={p.ic} size={28}/></div>
              <div>
                <div className="jp" style={{ fontSize:15, color:'var(--on-surface-variant)' }}>{p.jp}</div>
                <div className="title-l" style={{ color:'var(--on-surface)' }}>{p.t}</div>
              </div>
            </div>
            <div className="body-m" style={{ color:'var(--on-surface-variant)', margin:'12px 0' }}>{p.d}</div>
            <div style={{ display:'flex', justifyContent:'space-between', alignItems:'center' }}>
              <span className="label-m" style={{ color:'var(--on-surface-variant)' }}>POOL · {p.pool}</span>
              <button className="btn btn-tonal btn-sm" data-go="practiceConfig" data-params={JSON.stringify({ mode:p.mode })}>Praticar <Icon name="arrow_forward" size={16}/></button>
            </div>
          </div>
        ))}
      </div>
    </div>
  </DesktopFrame>
);

// ---- Session shell ----
const SessTop = ({ done, total }) => (
  <div style={{ flexShrink:0, padding:'8px 16px', display:'flex', alignItems:'center', gap:12 }}>
    <button className="icon-btn"><Icon name="close" size={22}/></button>
    <div className="linear-prog thick" style={{ flex:1 }}><i style={{ width:`${done/total*100}%` }}/></div>
    <span className="label-m" style={{ color:'var(--on-surface-variant)' }}>{done}/{total}</span>
  </div>
);

// ---- On-screen keyboards (for "com teclado" modes) ----
const RomajiKeyboard = ({ typed = "" }) => {
  const rows = [["q","w","e","r","t","y","u","i","o","p"],["a","s","d","f","g","h","j","k","l"],["z","x","c","v","b","n","m"]];
  return (
    <div style={{ flexShrink:0, background:'var(--surface-container-high)', padding:'8px 6px 10px' }}>
      {rows.map((r,ri)=>(
        <div key={ri} style={{ display:'flex', gap:5, justifyContent:'center', marginBottom:5, padding: ri===1?'0 16px':0 }}>
          {ri===2 && <span style={{ flex:'1.4', maxWidth:42 }}/>}
          {r.map((k,ki)=>(
            <span key={ki} style={{ flex:1, maxWidth:34, height:38, borderRadius:6, background:'var(--surface-container-lowest)', boxShadow:'0 1px 0 rgba(0,0,0,0.2)', display:'flex', alignItems:'center', justifyContent:'center', fontFamily:'var(--font-body)', fontWeight:600, fontSize:15, color:'var(--on-surface)' }}>{k}</span>
          ))}
          {ri===2 && <span style={{ flex:'1.4', maxWidth:42, height:38, borderRadius:6, background:'var(--surface-container-lowest)', display:'flex', alignItems:'center', justifyContent:'center' }}><Icon name="backspace" size={18} color="var(--on-surface-variant)"/></span>}
        </div>
      ))}
      <div style={{ display:'flex', gap:5, justifyContent:'center' }}>
        <span style={{ flex:5, height:38, borderRadius:6, background:'var(--surface-container-lowest)', display:'flex', alignItems:'center', justifyContent:'center', fontFamily:'var(--font-body)', fontWeight:600, fontSize:13, color:'var(--on-surface-variant)' }}>espaço</span>
        <span style={{ flex:1.6, height:38, borderRadius:6, background:'var(--primary)', display:'flex', alignItems:'center', justifyContent:'center', color:'var(--on-primary)', fontFamily:'var(--font-body)', fontWeight:700, fontSize:13 }}>enter</span>
      </div>
    </div>
  );
};
const NumPad = () => (
  <div style={{ flexShrink:0, background:'var(--surface-container-high)', padding:'10px 40px 14px' }}>
    {[["1","2","3"],["4","5","6"],["7","8","9"],["","0","⌫"]].map((r,ri)=>(
      <div key={ri} style={{ display:'flex', gap:8, justifyContent:'center', marginBottom:8 }}>
        {r.map((k,ki)=>(
          <span key={ki} style={{ flex:1, height:44, borderRadius:8, background: k?'var(--surface-container-lowest)':'transparent', display:'flex', alignItems:'center', justifyContent:'center', fontFamily:'var(--font-body)', fontWeight:700, fontSize:20, color:'var(--on-surface)' }}>{k}</span>
        ))}
      </div>
    ))}
  </div>
);

// Hiragana session — input: cards | typing ; state: fresh / correct / wrong
const HiraganaSession = ({ theme = "light", state = "fresh", input = "cards" }) => {
  const opts = ["ki","gi","ge","go"];
  const flash = state==="correct" ? "var(--success)" : state==="wrong" ? "var(--error)" : "var(--on-surface)";
  const modeLabel = input==="typing" ? "digitar" : "cartões";
  return (
    <PhoneFrame theme={theme} label={`Hiragana · ${modeLabel} — ${state==="fresh"?"pergunta":state==="correct"?"acerto":"erro"}`}>
      <SessTop done={state==="fresh"?8:9} total={30}/>
      <PhoneBody style={{ display:'flex', flexDirection:'column' }}>
        <div style={{ flex:1, display:'flex', flexDirection:'column', alignItems:'center', justifyContent:'center', padding:'0 20px' }}>
          <span className="label-m" style={{ color:'var(--on-surface-variant)' }}>{input==="typing"?"DIGITE O ROMAJI":"QUAL O ROMAJI?"}</span>
          <div className="jp-serif" style={{ fontSize:120, lineHeight:1, color:flash, margin:'10px 0' }}>ぎ</div>
          {state==="fresh" && input==="cards" && <button className="btn btn-tonal btn-sm"><Icon name="volume_up" size={18}/> Repetir</button>}
          {state==="fresh" && input==="typing" && (
            <div style={{ width:'100%', maxWidth:220, marginTop:8 }}>
              <div className="field field-outlined focused" style={{ textAlign:'center', borderColor:'var(--primary)' }}>
                <input value="gi" readOnly style={{ textAlign:'center', fontSize:24, fontFamily:'var(--font-body)', fontWeight:700 }}/>
              </div>
              <div className="body-s" style={{ color:'var(--on-surface-variant)', textAlign:'center', marginTop:8 }}>auto-confirma ao completar</div>
            </div>
          )}
          {state==="correct" && <div className="title-l" style={{ color:'var(--success)' }}>gi · correto!</div>}
          {state==="wrong" && <div className="body-m" style={{ color:'var(--on-surface-variant)', textAlign:'center' }}>você marcou <b style={{ color:'var(--error)' }}>ge</b> · correto é <b style={{ color:'var(--success)' }}>gi</b></div>}
        </div>
        {state!=="fresh" ? (
          <div style={{ padding:'0 16px 16px' }}><button className="btn btn-filled btn-lg" style={{ width:'100%' }}>Próxima <Icon name="arrow_forward" size={20}/></button></div>
        ) : input==="cards" ? (
          <div style={{ padding:'0 16px 16px', display:'grid', gridTemplateColumns:'1fr 1fr', gap:10 }}>
            {opts.map((o,i)=>(
              <button key={i} className="card card-outlined state" style={{ padding:'16px 0', textAlign:'center', cursor:'pointer', fontFamily:'var(--font-body)', fontWeight:700, fontSize:22, color:'var(--on-surface)' }}>{o}</button>
            ))}
          </div>
        ) : (
          <RomajiKeyboard/>
        )}
      </PhoneBody>
    </PhoneFrame>
  );
};

// Particle session
const ParticleSession = ({ theme = "light" }) => (
  <PhoneFrame theme={theme} label="Partículas — sessão">
    <SessTop done={5} total={20}/>
    <PhoneBody style={{ display:'flex', flexDirection:'column' }}>
      <div style={{ flex:1, padding:'12px 16px' }}>
        <div className="body-m" style={{ color:'var(--on-surface-variant)', textAlign:'center', marginBottom:12 }}>„Eu sou estudante.'</div>
        <div className="card card-elevated" style={{ padding:'24px 16px', textAlign:'center' }}>
          <span className="jp-serif" style={{ fontSize:28 }}>わたし </span>
          <span style={{ display:'inline-flex', width:52, height:38, border:'2px dashed var(--primary)', borderRadius:10, verticalAlign:'middle', background:'color-mix(in srgb, var(--primary) 8%, transparent)' }}/>
          <span className="jp-serif" style={{ fontSize:28 }}> がくせい です。</span>
        </div>
        <div className="label-m" style={{ color:'var(--on-surface-variant)', margin:'18px 0 8px', textAlign:'center' }}>BANCO DE PARTÍCULAS</div>
        <div style={{ display:'flex', gap:10, justifyContent:'center', flexWrap:'wrap' }}>
          {["は","を","の","に","で","が"].map((p,i)=>(
            <button key={i} className={`chip${i===0?' selected':''}`} style={{ fontSize:22, fontFamily:'var(--font-jp-serif)', padding:'4px 16px', height:'auto' }}>{p}</button>
          ))}
        </div>
      </div>
      <div style={{ padding:'0 16px 16px' }}>
        <button className="btn btn-filled btn-lg" style={{ width:'100%' }}>Verificar</button>
      </div>
    </PhoneBody>
  </PhoneFrame>
);

// Conjugation session (correct feedback with rule)
const ConjugationSession = ({ theme = "light" }) => (
  <PhoneFrame theme={theme} label="Conjugação — acerto">
    <SessTop done={5} total={20}/>
    <PhoneBody style={{ display:'flex', flexDirection:'column' }}>
      <div style={{ flex:1, display:'flex', flexDirection:'column', alignItems:'center', justifyContent:'center', padding:'0 20px', textAlign:'center' }}>
        <span className="pill pill-success">CORRETO</span>
        <div className="jp-serif" style={{ fontSize:64, color:'var(--success)', marginTop:12 }}>食べて</div>
        <div className="title-m" style={{ color:'var(--on-surface)' }}>tabete</div>
        <button className="btn btn-tonal btn-sm" style={{ marginTop:8 }}><Icon name="volume_up" size={18}/> Ouvir</button>
        <div className="card card-filled" style={{ marginTop:16, textAlign:'left', width:'100%' }}>
          <span className="label-m" style={{ color:'var(--on-surface-variant)' }}>REGRA</span>
          <div className="body-m" style={{ color:'var(--on-surface-variant)', marginTop:4 }}>Verbos ichidan (Grupo II) formam o <b>て</b> trocando <b className="jp">る</b> por <b className="jp">て</b>: 食べ<b>る</b> → 食べ<b>て</b>.</div>
        </div>
      </div>
      <div style={{ padding:'0 16px 16px' }}>
        <button className="btn btn-filled btn-lg" style={{ width:'100%' }}>Próxima <Icon name="arrow_forward" size={20}/></button>
      </div>
    </PhoneBody>
  </PhoneFrame>
);

// Numbers session — input: cards | typing
const NumbersSession = ({ theme = "light", input = "cards" }) => (
  <PhoneFrame theme={theme} label={`Números · ${input==="typing"?"digitar":"cartões"}`}>
    <SessTop done={6} total={30}/>
    <PhoneBody style={{ display:'flex', flexDirection:'column' }}>
      <div style={{ flexShrink:0, display:'flex', justifyContent:'center', padding:'4px 0' }}>
        <div className="segmented"><button className={`seg${input==="cards"?" selected":""}`}>Cartões</button><button className={`seg${input==="typing"?" selected":""}`}>Digitar</button></div>
      </div>
      <div style={{ flex:1, display:'flex', flexDirection:'column', alignItems:'center', justifyContent:'center', padding:'0 20px' }}>
        <span className="label-m" style={{ color:'var(--on-surface-variant)' }}>{input==="typing"?"DIGITE O NÚMERO":"COMO SE LÊ?"}</span>
        {input==="typing" ? (
          <>
            <div className="jp-serif" style={{ fontSize:44, color:'var(--on-surface)', margin:'10px 0' }}>ろっぴゃく</div>
            <div className="field field-outlined focused" style={{ width:'100%', maxWidth:200, textAlign:'center', borderColor:'var(--primary)' }}><input value="600" readOnly style={{ textAlign:'center', fontSize:28, fontFamily:'var(--font-body)', fontWeight:700 }}/></div>
          </>
        ) : (
          <>
            <div className="display-l" style={{ color:'var(--on-surface)', margin:'8px 0 20px' }}>12</div>
            <div style={{ display:'grid', gridTemplateColumns:'1fr 1fr', gap:10, width:'100%' }}>
              {["じゅうに","にじゅう","じゅういち","じゅうさん"].map((o,i)=>(
                <button key={i} className="card card-outlined state" style={{ padding:'14px 0', textAlign:'center', cursor:'pointer', fontFamily:'var(--font-jp)', fontWeight:500, fontSize:18, color:'var(--on-surface)' }}>{o}</button>
              ))}
            </div>
          </>
        )}
      </div>
      {input==="typing" && <NumPad/>}
    </PhoneBody>
  </PhoneFrame>
);

// Katakana session (cards) — reuses kana drill structure
const KatakanaSession = ({ theme = "light" }) => (
  <PhoneFrame theme={theme} label="Katakana · cartões — pergunta">
    <SessTop done={4} total={30}/>
    <PhoneBody style={{ display:'flex', flexDirection:'column' }}>
      <div style={{ flex:1, display:'flex', flexDirection:'column', alignItems:'center', justifyContent:'center', padding:'0 20px' }}>
        <span className="label-m" style={{ color:'var(--on-surface-variant)' }}>QUAL O ROMAJI?</span>
        <div className="jp-serif" style={{ fontSize:120, lineHeight:1, color:'var(--on-surface)', margin:'10px 0' }}>ネ</div>
        <button className="btn btn-tonal btn-sm"><Icon name="volume_up" size={18}/> Repetir</button>
      </div>
      <div style={{ padding:'0 16px 16px', display:'grid', gridTemplateColumns:'1fr 1fr', gap:10 }}>
        {["ne","re","wa","shi"].map((o,i)=>(
          <button key={i} className="card card-outlined state" style={{ padding:'16px 0', textAlign:'center', cursor:'pointer', fontFamily:'var(--font-body)', fontWeight:700, fontSize:22, color:'var(--on-surface)' }}>{o}</button>
        ))}
      </div>
    </PhoneBody>
  </PhoneFrame>
);

// Sentence construction session (tap blocks)
const SentenceBuildSession = ({ theme = "light" }) => (
  <PhoneFrame theme={theme} label="Construir frases — sessão">
    <SessTop done={3} total={15}/>
    <PhoneBody style={{ display:'flex', flexDirection:'column' }}>
      <div style={{ flex:1, padding:'12px 16px' }}>
        <div className="card card-filled" style={{ padding:'12px 16px', marginBottom:14 }}>
          <span className="label-m" style={{ color:'var(--on-surface-variant)' }}>TRADUZA</span>
          <div className="title-m" style={{ color:'var(--on-surface)' }}>„A senhora Maria é professora.'</div>
        </div>
        {/* answer area */}
        <div style={{ minHeight:64, border:'2px dashed var(--primary)', borderRadius:'var(--r-md)', background:'color-mix(in srgb, var(--primary) 5%, transparent)', padding:'10px', display:'flex', gap:6, flexWrap:'wrap', alignItems:'flex-start' }}>
          <span className="chip selected" style={{ fontFamily:'var(--font-jp)', fontSize:16 }}>マリアさん</span>
          <span className="chip selected" style={{ fontFamily:'var(--font-jp)', fontSize:16 }}>は</span>
        </div>
        <div className="label-m" style={{ color:'var(--on-surface-variant)', margin:'18px 0 8px' }}>BLOCOS</div>
        <div style={{ display:'flex', gap:8, flexWrap:'wrap', justifyContent:'center' }}>
          {["せんせい","です","の","を"].map((b,i)=>(
            <button key={i} className="chip" style={{ fontFamily:'var(--font-jp)', fontSize:16, cursor:'pointer' }}>{b}</button>
          ))}
        </div>
      </div>
      <div style={{ padding:'0 16px 16px', display:'flex', gap:10 }}>
        <button className="btn btn-outlined" style={{ flex:1 }}>Limpar</button>
        <button className="btn btn-filled" style={{ flex:2 }}>Verificar</button>
      </div>
    </PhoneBody>
  </PhoneFrame>
);

// ============================================================
// CONFIG SCREENS (per guide §10)
// ============================================================
const ConfigShell = ({ theme, title, children, cta = "Iniciar prática", mode }) => (
  <PhoneFrame theme={theme} label={`${title} — config`}>
    <AppBar title={title} leading={<button className="icon-btn" data-tab="practice"><Icon name="arrow_back" size={24}/></button>}/>
    <PhoneBody>
      <div style={{ padding:'8px 16px' }}>{children}</div>
    </PhoneBody>
    <div style={{ flexShrink:0, padding:'10px 16px 16px', borderTop:'1px solid var(--outline-variant)' }}>
      <button className="btn btn-magic btn-lg" style={{ width:'100%' }} data-go="practiceSession" data-params={JSON.stringify({ mode })}><Icon name="play_arrow" size={20} fill/> {cta}</button>
    </div>
  </PhoneFrame>
);
const CfgLabel = ({ children }) => <div className="label-m" style={{ color:'var(--on-surface-variant)', margin:'18px 0 10px' }}>{children}</div>;
const CheckRow = ({ label, sub, on }) => (
  <label style={{ display:'flex', alignItems:'center', gap:12, padding:'8px 0', cursor:'pointer' }}>
    <span style={{ width:22, height:22, borderRadius:6, border:`2px solid ${on?'var(--primary)':'var(--outline)'}`, background:on?'var(--primary)':'transparent', display:'flex', alignItems:'center', justifyContent:'center', flexShrink:0 }}>
      {on && <Icon name="check" size={16} color="var(--on-primary)"/>}
    </span>
    <span style={{ flex:1 }}><span className="body-l" style={{ color:'var(--on-surface)' }}>{label}</span>{sub && <span className="body-s" style={{ color:'var(--on-surface-variant)', display:'block' }}>{sub}</span>}</span>
  </label>
);
const RadioRow = ({ label, sub, on }) => (
  <label style={{ display:'flex', alignItems:'center', gap:12, padding:'8px 0', cursor:'pointer' }}>
    <span style={{ width:22, height:22, borderRadius:'50%', border:`2px solid ${on?'var(--primary)':'var(--outline)'}`, display:'flex', alignItems:'center', justifyContent:'center', flexShrink:0 }}>
      {on && <span style={{ width:10, height:10, borderRadius:'50%', background:'var(--primary)' }}/>}
    </span>
    <span style={{ flex:1 }}><span className="body-l" style={{ color:'var(--on-surface)' }}>{label}</span>{sub && <span className="body-s" style={{ color:'var(--on-surface-variant)', display:'block' }}>{sub}</span>}</span>
  </label>
);

const KANA_FAMILIES = [
  { l:"あ-お", k:"vogais", on:true }, { l:"か-こ", k:"K", on:true }, { l:"さ-そ", k:"S", on:true },
  { l:"た-と", k:"T", on:false }, { l:"な-の", k:"N", on:false }, { l:"は-ほ", k:"H", on:false },
  { l:"ま-も", k:"M", on:false }, { l:"や-よ", k:"Y", on:false }, { l:"ら-ろ", k:"R", on:false },
  { l:"わ-ん", k:"W", on:false }, { l:"が-ご", k:"dakuten", on:false }, { l:"ぱ-ぽ", k:"handakuten", on:false },
];

const HiraganaConfig = ({ theme = "light", mode = "hiragana" }) => (
  <ConfigShell theme={theme} title={mode==='katakana'?'Katakana':'Hiragana'} mode={mode}>
    <div className="body-m" style={{ color:'var(--on-surface-variant)' }}>Reconhecimento de kana. Por padrão, só o que você já aprendeu.</div>
    <div style={{ display:'flex', justifyContent:'space-between', alignItems:'center', marginTop:8 }}>
      <CfgLabel>FAMÍLIAS</CfgLabel>
      <div style={{ display:'flex', gap:6 }}><button className="chip" style={{ height:28 }}>Tudo</button><button className="chip selected" style={{ height:28 }}>Aprendidas</button></div>
    </div>
    <div style={{ display:'grid', gridTemplateColumns:'repeat(3,1fr)', gap:8 }}>
      {KANA_FAMILIES.map((f,i)=>(
        <div key={i} className="card card-filled" style={{ padding:'10px 8px', textAlign:'center', border: f.on?'2px solid var(--primary)':'2px solid transparent', cursor:'pointer' }}>
          <div className="jp" style={{ fontSize:16, color:'var(--on-surface)' }}>{f.l}</div>
          <div className="body-s" style={{ color:'var(--on-surface-variant)' }}>{f.k}</div>
        </div>
      ))}
    </div>
    <CfgLabel>DURAÇÃO</CfgLabel>
    <div className="segmented" style={{ width:'100%' }}>
      <button className="seg selected" style={{ flex:1 }}>Rápida · 5 min</button>
      <button className="seg" style={{ flex:1 }}>Pool completa</button>
    </div>
    <CfgLabel>MODO DE RESPOSTA</CfgLabel>
    <RadioRow label="Cartões (4 opções de romaji)" on={true}/>
    <RadioRow label="Digitar romaji" sub="teclado; auto-confirma ao completar" on={false}/>
    <div className="card card-filled" style={{ marginTop:8, display:'flex', alignItems:'center', gap:12, padding:'12px 16px' }}>
      <span className="body-m" style={{ flex:1, color:'var(--on-surface)' }}>Auto-confirmar ao digitar romaji completo</span>
      <div className="switch on"/>
    </div>
  </ConfigShell>
);

const ParticleConfig = ({ theme = "light", mode = "particles" }) => (
  <ConfigShell theme={theme} title={mode==='sentence'?'Construir frases':'Partículas'} mode={mode}>
    <div className="body-m" style={{ color:'var(--on-surface-variant)' }}>Encaixe a partícula correta na lacuna.</div>
    <CfgLabel>POOL</CfgLabel>
    <RadioRow label="Apenas o que aprendi" sub="recomendado" on={true}/>
    <RadioRow label="Todas as partículas" on={false}/>
    <RadioRow label="Por nível" on={false}/>
    <div style={{ display:'flex', gap:8, flexWrap:'wrap', paddingLeft:34, marginTop:4 }}>
      {["N5","N4","N3","N2","N1"].map((n,i)=>(<button key={i} className={`chip${i===0?' selected':''}`} style={{ height:30, opacity:i>1?0.5:1 }}>{n}{i>1 && <Icon name="lock" size={14} className="chip-ic"/>}</button>))}
    </div>
  </ConfigShell>
);

const ConjugationConfig = ({ theme = "light", mode = "conjugation" }) => (
  <ConfigShell theme={theme} title="Conjugação" mode={mode}>
    <div className="body-m" style={{ color:'var(--on-surface-variant)' }}>Verbo no dicionário → forma alvo. 4 opções.</div>
    <CfgLabel>FORMAS</CfgLabel>
    <div style={{ display:'grid', gridTemplateColumns:'1fr 1fr', gap:'0 16px' }}>
      {[["masu",1],["forma て",1],["forma た",1],["forma ない",1],["dicionário",0],["potencial",0],["passiva",0],["causativa",0],["volitiva",0],["cond. ば",0],["cond. たら",0],["imperativo",0]].map(([l,on],i)=>(
        <CheckRow key={i} label={l} on={!!on}/>
      ))}
    </div>
    <CfgLabel>POOL</CfgLabel>
    <RadioRow label="Apenas verbos aprendidos" on={true}/>
    <RadioRow label="Todos os verbos" on={false}/>
  </ConfigShell>
);

const NumbersConfig = ({ theme = "light", mode = "numbers" }) => (
  <ConfigShell theme={theme} title="Números" mode={mode}>
    <div className="body-m" style={{ color:'var(--on-surface-variant)' }}>Sem configuração longa — escolha o alcance e o modo.</div>
    <CfgLabel>ALCANCE</CfgLabel>
    <div style={{ display:'flex', flexWrap:'wrap', gap:8 }}>
      {[["1–10",1],["11–100",1],["100–9999",0],["Contadores 人 枚 本…",0]].map(([l,on],i)=>(
        <button key={i} className={`chip${on?' selected':''}`} style={{ cursor:'pointer' }}>{l}{on?<Icon name="check" size={16} className="chip-ic"/>:null}</button>
      ))}
    </div>
    <CfgLabel>MODO</CfgLabel>
    <div className="segmented" style={{ width:'100%' }}>
      <button className="seg selected" style={{ flex:1 }}>Cartões</button>
      <button className="seg" style={{ flex:1 }}>Digitar</button>
    </div>
  </ConfigShell>
);

export {
  PracticeHubMobile, PracticeHubDesktop,
  HiraganaSession, KatakanaSession, ParticleSession, SentenceBuildSession, ConjugationSession, NumbersSession,
  HiraganaConfig, ParticleConfig, ConjugationConfig, NumbersConfig,
  RomajiKeyboard, NumPad
};
