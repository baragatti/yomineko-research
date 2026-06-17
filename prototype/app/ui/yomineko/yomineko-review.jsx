import React from 'react';
import { Icon, PhoneFrame, DesktopFrame, PhoneBody, AppBar, NavBar, NavDrawer } from './m3';
import { Yomineko } from './mascot';

/* ============================================================
   Yomineko — REVIEW (SRS): empty, front, back, done (mobile + desktop)
   ============================================================ */

const ReviewSessionHeaderM = ({ done = 4, total = 12 }) => (
  <div style={{ flexShrink:0, padding:'8px 16px', display:'flex', alignItems:'center', gap:12 }}>
    <button className="icon-btn"><Icon name="close" size={22}/></button>
    <div className="linear-prog thick" style={{ flex:1 }}><i style={{ width:`${done/total*100}%` }}/></div>
    <span className="label-m" style={{ color:'var(--on-surface-variant)' }}>{done}/{total}</span>
  </div>
);

const RatingButtons = ({ big }) => (
  <div style={{ display:'grid', gridTemplateColumns:'1fr 1fr 1fr 1fr', gap:8 }}>
    {[
      { l:"De novo", iv:"<1m", c:"var(--error)" },
      { l:"Difícil", iv:"~3d", c:"var(--gold)" },
      { l:"Bom", iv:"~7d", c:"var(--success)" },
      { l:"Fácil", iv:"~14d", c:"var(--primary)" },
    ].map((r,i)=>(
      <button key={i} className="state" style={{ display:'flex', flexDirection:'column', alignItems:'center', gap:2, padding: big?'14px 0':'10px 0', borderRadius:'var(--r-md)', border:'none', cursor:'pointer', background:`color-mix(in srgb, ${r.c} 16%, var(--surface))`, color:r.c }}>
        <span className="title-s" style={{ color:r.c }}>{r.l}</span>
        <span className="label-s" style={{ color:r.c, opacity:0.85 }}>{r.iv}</span>
      </button>
    ))}
  </div>
);

const RevCardFace = ({ revealed }) => (
  <div className="card card-elevated" style={{ padding:'32px 20px', textAlign:'center', display:'flex', flexDirection:'column', alignItems:'center', justifyContent:'center', minHeight:280 }}>
    <span className="pill pill-outline">PALAVRA · 4 de 12</span>
    <div className="jp-serif" style={{ fontSize:56, color:'var(--on-surface)', marginTop:18 }}>がくせい</div>
    {!revealed ? (
      <>
        <button className="btn btn-tonal btn-sm" style={{ marginTop:14 }}><Icon name="volume_up" size={18}/> Ouvir</button>
        <div className="body-s" style={{ color:'var(--on-surface-variant)', marginTop:24 }}>Tente lembrar do significado.</div>
      </>
    ) : (
      <>
        <div className="body-m" style={{ color:'var(--on-surface-variant)', marginTop:4 }}>gakusei</div>
        <hr className="divider" style={{ width:'60%', margin:'18px 0' }}/>
        <div className="headline-s" style={{ color:'var(--primary)' }}>estudante</div>
        <div className="card card-filled" style={{ marginTop:14, textAlign:'left', width:'100%' }}>
          <span className="label-m" style={{ color:'var(--on-surface-variant)' }}>EXEMPLO</span>
          <div className="jp" style={{ fontSize:16, marginTop:4 }}>わたしは <b style={{ color:'var(--primary)' }}>がくせい</b> です。</div>
          <div className="body-s" style={{ color:'var(--on-surface-variant)' }}>Eu sou estudante.</div>
        </div>
      </>
    )}
  </div>
);

const ReviewEmptyMobile = ({ theme = "light" }) => (
  <PhoneFrame theme={theme} label="Revisão — sem cartões">
    <AppBar title="Revisão"/>
    <PhoneBody>
      <div style={{ display:'flex', flexDirection:'column', alignItems:'center', justifyContent:'center', height:'100%', textAlign:'center', padding:'0 32px' }}>
        <Yomineko pose="sleep" size={150}/>
        <div className="headline-s" style={{ color:'var(--on-surface)', marginTop:8 }}>Nada para revisar hoje</div>
        <div className="body-m" style={{ color:'var(--on-surface-variant)', marginTop:6 }}>O grimório está em silêncio. Volte amanhã, com calma — ou pratique um pouco agora.</div>
        <button className="btn btn-magic" style={{ marginTop:20 }}><Icon name="target" size={18}/> Ir para uma prática</button>
        <button className="btn btn-text" style={{ marginTop:6 }}>Continuar uma lição</button>
      </div>
    </PhoneBody>
    <NavBar active="review"/>
  </PhoneFrame>
);

const ReviewFrontMobile = ({ theme = "light" }) => (
  <PhoneFrame theme={theme} label="Revisão — frente">
    <ReviewSessionHeaderM/>
    <PhoneBody style={{ display:'flex', flexDirection:'column' }}>
      <div style={{ padding:'16px', flex:1 }}><RevCardFace revealed={false}/></div>
    </PhoneBody>
    <div style={{ flexShrink:0, padding:'12px 16px 20px' }}>
      <button className="btn btn-filled btn-lg" style={{ width:'100%' }}>Mostrar resposta</button>
    </div>
  </PhoneFrame>
);

const ReviewBackMobile = ({ theme = "light" }) => (
  <PhoneFrame theme={theme} label="Revisão — verso">
    <ReviewSessionHeaderM/>
    <PhoneBody style={{ display:'flex', flexDirection:'column' }}>
      <div style={{ padding:'16px', flex:1 }}><RevCardFace revealed={true}/></div>
    </PhoneBody>
    <div style={{ flexShrink:0, padding:'12px 16px 20px' }}>
      <div className="body-s" style={{ color:'var(--on-surface-variant)', textAlign:'center', marginBottom:8 }}>Como foi lembrar?</div>
      <RatingButtons big/>
    </div>
  </PhoneFrame>
);

const ReviewDoneMobile = ({ theme = "light" }) => (
  <PhoneFrame theme={theme} label="Revisão — concluída">
    <PhoneBody>
      <div style={{ display:'flex', flexDirection:'column', alignItems:'center', justifyContent:'center', height:'100%', textAlign:'center', padding:'0 28px' }}>
        <div style={{ position:'relative' }}>
          <div style={{ position:'absolute', inset:'-20%', background:'radial-gradient(circle, var(--magic-glow), transparent 70%)' }}/>
          <div style={{ position:'relative' }}><Yomineko pose="celebrate" size={170}/></div>
        </div>
        <div className="headline-m" style={{ color:'var(--on-surface)', marginTop:8 }}>Sessão concluída!</div>
        <div className="body-m" style={{ color:'var(--on-surface-variant)', marginTop:4 }}>12 cartões revisados. Yomineko está orgulhoso.</div>
        <div className="card card-filled" style={{ width:'100%', marginTop:20 }}>
          <div style={{ display:'grid', gridTemplateColumns:'repeat(3,1fr)', gap:12 }}>
            <div><div className="headline-s" style={{ color:'var(--primary)' }}>12</div><div className="label-m" style={{ color:'var(--on-surface-variant)' }}>revisados</div></div>
            <div><div className="headline-s" style={{ color:'var(--success)' }}>92%</div><div className="label-m" style={{ color:'var(--on-surface-variant)' }}>acertos</div></div>
            <div><div className="headline-s" style={{ color:'var(--gold)' }}>14→15</div><div className="label-m" style={{ color:'var(--on-surface-variant)' }}>dias</div></div>
          </div>
        </div>
        <button className="btn btn-filled btn-lg" style={{ width:'100%', marginTop:18 }}>Voltar ao início</button>
        <button className="btn btn-text" style={{ marginTop:6 }}>Praticar mais</button>
      </div>
    </PhoneBody>
  </PhoneFrame>
);

// ---------------- DESKTOP REVIEW ----------------
const ReviewDesktop = ({ theme = "light", revealed = false }) => (
  <DesktopFrame theme={theme} label={`Revisão — desktop ${revealed?"(verso)":"(frente)"}`} url="app.yomineko.com/revisar">
    <NavDrawer active="review" badge={{ review:12 }} drawer={false}/>
    <div style={{ flex:1, display:'flex', flexDirection:'column', overflowY:'auto' }}>
      <div style={{ padding:'24px 32px 0', display:'flex', justifyContent:'space-between', alignItems:'center' }}>
        <div>
          <div className="headline-m" style={{ color:'var(--on-surface)' }}>Revisão de hoje</div>
          <div className="body-m" style={{ color:'var(--on-surface-variant)' }}>12 cartões · agendados pelo FSRS-6 · ~5 min</div>
        </div>
        <button className="btn btn-outlined"><Icon name="pause" size={18}/> Pausar</button>
      </div>
      <div style={{ flex:1, display:'grid', gridTemplateColumns:'minmax(0,640px) 280px', gap:28, padding:'24px 32px', justifyContent:'center', alignItems:'flex-start' }}>
        <div>
          <div style={{ display:'flex', alignItems:'center', gap:10, marginBottom:12 }}>
            <span className="label-m" style={{ color:'var(--on-surface-variant)' }}>4 / 12</span>
            <div className="linear-prog thick" style={{ flex:1 }}><i style={{ width:'33%' }}/></div>
          </div>
          <RevCardFace revealed={revealed}/>
          {!revealed ? (
            <div style={{ marginTop:16, display:'flex', flexDirection:'column', alignItems:'center', gap:8 }}>
              <button className="btn btn-filled btn-lg" style={{ width:'100%' }}>Mostrar resposta</button>
              <span className="body-s" style={{ color:'var(--on-surface-variant)' }}>ou pressione <b>Espaço</b></span>
            </div>
          ) : (
            <div style={{ marginTop:16 }}><RatingButtons big/></div>
          )}
        </div>
        <div>
          <div className="label-m" style={{ color:'var(--on-surface-variant)', marginBottom:8 }}>ATALHOS</div>
          <div className="card card-filled" style={{ marginBottom:16 }}>
            {[["Espaço","mostrar resposta"],["1","de novo (<1m)"],["2","difícil (~3d)"],["3","bom (~7d)"],["4","fácil (~14d)"],["P","pausar"],["Esc","sair"]].map(([k,v],i)=>(
              <div key={i} style={{ display:'flex', justifyContent:'space-between', alignItems:'center', padding:'6px 0' }}>
                <span style={{ fontFamily:'var(--font-body)', fontWeight:700, fontSize:11, border:'1px solid var(--outline)', borderRadius:6, padding:'1px 8px', color:'var(--on-surface-variant)' }}>{k}</span>
                <span className="body-m" style={{ color:'var(--on-surface-variant)' }}>{v}</span>
              </div>
            ))}
          </div>
          <div className="label-m" style={{ color:'var(--on-surface-variant)', marginBottom:8 }}>NA FILA</div>
          {[["ぎんこう","palavra"],["学","kanji"],["にほんじん です","frase"]].map(([w,t],i)=>(
            <div key={i} className="card card-filled" style={{ marginBottom:6, padding:'8px 12px', display:'flex', justifyContent:'space-between', alignItems:'center', opacity:0.7 }}>
              <span className="jp" style={{ fontSize:t==="frase"?13:16 }}>{w}</span>
              <span className="pill pill-outline">{t}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  </DesktopFrame>
);

export {
  ReviewEmptyMobile, ReviewFrontMobile, ReviewBackMobile, ReviewDoneMobile, ReviewDesktop,
  RatingButtons, RevCardFace
};
