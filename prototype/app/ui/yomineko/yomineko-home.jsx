import React from 'react';
import { Icon, PhoneFrame, DesktopFrame, PhoneBody, AppBar, NavBar, NavDrawer } from './m3';
import { Yomineko, YominekoLogo } from './mascot';
import { reviewDue } from '../app/store';

/* ============================================================
   Yomineko — HOME: Dashboard + Profile (mobile + desktop)
   ============================================================ */

// ---- shared bits ----
const StatTile = ({ n, l, ic, go }) => {
  const Tag = go ? 'button' : 'div';
  return (
  <Tag {...(go ? { 'data-go': go } : {})} className="card card-filled state" style={{ padding:'12px', textAlign:'center', border:'none', width:'100%', cursor: go ? 'pointer' : 'default' }}>
    <Icon name={ic} size={20} color="var(--primary)"/>
    <div className="headline-s" style={{ color:'var(--on-surface)', marginTop:2 }}>{n}</div>
    <div className="label-m" style={{ color:'var(--on-surface-variant)' }}>{l}</div>
  </Tag>
  );
};

const PracticeTile = ({ jp, t, badge, mode }) => (
  <button data-go="practiceConfig" data-params={JSON.stringify({ mode })} className="card card-elevated state" style={{ padding:'12px', textAlign:'left', cursor:'pointer', position:'relative', border:'none' }}>
    {badge && <span className="pill pill-gold" style={{ position:'absolute', top:-8, right:8, height:20 }}>{badge}</span>}
    <div className="jp" style={{ fontSize:15, color:'var(--on-surface-variant)' }}>{jp}</div>
    <div className="title-s" style={{ color:'var(--on-surface)', marginTop:2 }}>{t}</div>
  </button>
);

const ContinueCard = ({ compact }) => (
  <div className="card" style={{ padding:0, overflow:'hidden', borderRadius:'var(--r-lg)', background:'linear-gradient(135deg, color-mix(in srgb, var(--magic-1) 16%, var(--surface-container-low)), var(--surface-container-low))', boxShadow:'var(--elev-1)' }}>
    <div style={{ padding:'16px' }}>
      <span className="label-m" style={{ color:'var(--primary)' }}>CONTINUAR DE ONDE PAROU</span>
      <div className="body-s" style={{ color:'var(--on-surface-variant)', marginTop:6 }}>N5 · Partículas básicas</div>
      <div className="title-l" style={{ color:'var(--on-surface)', marginTop:2 }}>A partícula は</div>
      <div style={{ display:'flex', alignItems:'center', gap:10, marginTop:12 }}>
        <div className="linear-prog" style={{ flex:1 }}><i style={{ width:'45%' }}/></div>
        <span className="label-m" style={{ color:'var(--on-surface-variant)' }}>45%</span>
      </div>
      <button className="btn btn-magic" style={{ marginTop:14, width:'100%' }} data-go="lesson"><Icon name="play_arrow" size={20} fill/> Continuar lição</button>
    </div>
  </div>
);

const ReviewCard = ({ empty }) => {
  const due = reviewDue();
  const isEmpty = empty || due === 0;
  return (
  <div className="card card-filled" style={{ padding:'16px' }}>
    {!isEmpty ? (
      <>
        <div style={{ display:'flex', alignItems:'center', justifyContent:'space-between' }}>
          <span className="label-m" style={{ color:'var(--on-surface-variant)' }}>REVISAR HOJE</span>
          <span className="pill pill-error">{due} devidos</span>
        </div>
        <div style={{ display:'flex', alignItems:'flex-end', gap:8, marginTop:6 }}>
          <span className="display-s" style={{ color:'var(--primary)' }}>{due}</span>
          <span className="body-m" style={{ color:'var(--on-surface-variant)', marginBottom:8 }}>cartões aguardando</span>
        </div>
        <div style={{ display:'flex', gap:6, marginTop:6, flexWrap:'wrap' }}>
          <span className="pill pill-outline">1 palavra</span>
          <span className="pill pill-outline">1 kanji</span>
          <span className="pill pill-outline">1 frase</span>
        </div>
        <button className="btn btn-filled" style={{ marginTop:14, width:'100%' }} data-go="review">Iniciar revisão</button>
      </>
    ) : (
      <div style={{ textAlign:'center', padding:'8px 0' }}>
        <Yomineko pose="sleep" size={92}/>
        <div className="title-l" style={{ color:'var(--on-surface)', marginTop:4 }}>Tudo em dia!</div>
        <div className="body-m" style={{ color:'var(--on-surface-variant)', marginTop:2 }}>Yomineko também está descansando.<br/>Volte amanhã — ou pratique um pouco.</div>
        <button className="btn btn-tonal" style={{ marginTop:12 }} data-tab="practice"><Icon name="target" size={18}/> Praticar</button>
      </div>
    )}
  </div>
  );
};

// ---------------- DASHBOARD MOBILE ----------------
const DashboardMobile = ({ theme = "light", variant = "default" }) => (
  <PhoneFrame theme={theme} label={`Dashboard — ${variant==="empty"?"tudo em dia":"mobile"}`}>
    <div className="appbar" style={{ flexShrink:0 }}>
      <div style={{ marginLeft:8 }}><YominekoLogo size={34}/></div>
      <div style={{ flex:1, marginLeft:10 }}>
        <div className="body-s" style={{ color:'var(--on-surface-variant)' }}>Bom dia,</div>
        <div className="title-m" style={{ color:'var(--on-surface)' }}>Ana</div>
      </div>
      <div className="pill pill-gold" style={{ height:32, gap:4 }}><Icon name="local_fire_department" size={18} fill/> 14</div>
      <button className="icon-btn"><Icon name="notifications" size={22}/></button>
    </div>

    <PhoneBody style={{ padding:'4px 0 8px' }}>
      <div style={{ padding:'0 16px', display:'flex', flexDirection:'column', gap:14 }}>
        <ContinueCard/>
        <ReviewCard empty={variant==="empty"}/>

        <div>
          <div style={{ display:'flex', alignItems:'center', justifyContent:'space-between', margin:'0 0 8px' }}>
            <span className="title-m" style={{ color:'var(--on-surface)' }}>Praticar</span>
            <button className="btn btn-text btn-sm" data-tab="practice">Ver tudo</button>
          </div>
          <div style={{ display:'grid', gridTemplateColumns:'1fr 1fr', gap:8 }}>
            <PracticeTile jp="ひらがな" t="Hiragana" badge="hoje" mode="hiragana"/>
            <PracticeTile jp="カタカナ" t="Katakana" mode="katakana"/>
            <PracticeTile jp="は が を" t="Partículas" mode="particles"/>
            <PracticeTile jp="食べる→て" t="Conjugação" mode="conjugation"/>
          </div>
        </div>

        <div style={{ display:'grid', gridTemplateColumns:'repeat(4,1fr)', gap:8 }}>
          <StatTile n="142" l="palavras" ic="menu_book" go="vocab"/>
          <StatTile n="27" l="kanji" ic="translate" go="kanji"/>
          <StatTile n="7" l="lições" ic="school"/>
          <StatTile n="14" l="dias" ic="local_fire_department"/>
        </div>
      </div>
    </PhoneBody>
    <NavBar active="home" badge={{ review: variant==="empty"?null:12 }}/>
  </PhoneFrame>
);

// ---------------- DASHBOARD DESKTOP ----------------
const DashboardDesktop = ({ theme = "light" }) => (
  <DesktopFrame theme={theme} label="Dashboard — desktop" url="app.yomineko.com">
    <NavDrawer active="home" badge={{ review:12 }} drawer={true}/>
    <div style={{ flex:1, overflowY:'auto', padding:'28px 32px' }}>
      <div style={{ display:'flex', alignItems:'center', justifyContent:'space-between', marginBottom:20 }}>
        <div>
          <div className="body-m" style={{ color:'var(--on-surface-variant)' }}>Bom dia,</div>
          <div className="headline-l" style={{ color:'var(--on-surface)' }}>Ana</div>
        </div>
        <div style={{ display:'flex', alignItems:'center', gap:12 }}>
          <div className="pill pill-gold" style={{ height:36 }}><Icon name="local_fire_department" size={20} fill/> 14 dias</div>
          <div style={{ width:44, height:44, borderRadius:'50%', background:'var(--primary-container)', color:'var(--on-primary-container)', display:'flex', alignItems:'center', justifyContent:'center', fontFamily:'var(--font-display)', fontWeight:600, fontSize:18 }}>A</div>
        </div>
      </div>

      <div style={{ display:'grid', gridTemplateColumns:'1.4fr 1fr', gap:20, alignItems:'flex-start' }}>
        <div style={{ display:'flex', flexDirection:'column', gap:16 }}>
          <div style={{ display:'grid', gridTemplateColumns:'1fr 1fr', gap:16 }}>
            <ContinueCard/>
            <ReviewCard/>
          </div>
          <div className="label-m" style={{ color:'var(--on-surface-variant)' }}>SUAS ESTATÍSTICAS</div>
          <div style={{ display:'grid', gridTemplateColumns:'repeat(4,1fr)', gap:12 }}>
            <StatTile n="142" l="palavras" ic="menu_book"/>
            <StatTile n="27" l="kanji" ic="translate"/>
            <StatTile n="7" l="lições" ic="school"/>
            <StatTile n="3h12m" l="tempo" ic="schedule"/>
          </div>
        </div>

        <div>
          <div style={{ display:'flex', alignItems:'center', gap:12, marginBottom:12, padding:'14px', borderRadius:'var(--r-lg)', background:'linear-gradient(135deg, color-mix(in srgb, var(--magic-1) 14%, var(--surface)), var(--surface))', border:'1px solid var(--outline-variant)' }}>
            <Yomineko pose="wave" size={72}/>
            <div>
              <div className="title-s" style={{ color:'var(--on-surface)' }}>Yomineko diz:</div>
              <div className="body-s" style={{ color:'var(--on-surface-variant)' }}>„Três lições e você termina o tópico de partículas. Vamos?'</div>
            </div>
          </div>
          <div className="label-m" style={{ color:'var(--on-surface-variant)', margin:'4px 0 8px' }}>PRÁTICAS</div>
          <div style={{ display:'flex', flexDirection:'column', gap:8 }}>
            {[["ひらがな","Hiragana","hoje","hiragana"],["カタカナ","Katakana",null,"katakana"],["は が を","Partículas",null,"particles"],["わたしは…","Construir frases",null,"sentence"],["食べる→て","Conjugação",null,"conjugation"],["1 2 3","Números",null,"numbers"]].map(([jp,t,b,mode],i)=>(
              <button key={i} data-go="practiceConfig" data-params={JSON.stringify({ mode })} className="list-item card card-filled state" style={{ borderRadius:'var(--r-md)', cursor:'pointer', border:'none', minHeight:52, position:'relative' }}>
                <span className="jp" style={{ fontSize:15, color:'var(--on-surface-variant)', minWidth:84 }}>{jp}</span>
                <span className="title-s" style={{ flex:1, color:'var(--on-surface)' }}>{t}</span>
                {b && <span className="pill pill-gold" style={{ height:20 }}>{b}</span>}
                <Icon name="chevron_right" size={20} color="var(--on-surface-variant)"/>
              </button>
            ))}
          </div>
        </div>
      </div>
    </div>
  </DesktopFrame>
);

// ---------------- PROFILE ----------------
const SettingRowM = ({ label, control }) => (
  <div style={{ display:'flex', alignItems:'center', gap:12, padding:'12px 16px', minHeight:56 }}>
    <span className="body-l" style={{ flex:1, color:'var(--on-surface)' }}>{label}</span>
    {control}
  </div>
);
const SegMinutes = ({ sel = 1 }) => (
  <div className="segmented" style={{ width:'100%' }}>
    {["10","20","30","45"].map((m,i)=>(
      <button key={i} className={`seg${i===sel?' selected':''}`} style={{ flex:1 }}>{m} min</button>
    ))}
  </div>
);

const ProfileMobile = ({ theme = "light" }) => (
  <PhoneFrame theme={theme} label="Perfil — mobile">
    <AppBar title="Perfil" leading={<button className="icon-btn" data-tab="dashboard"><Icon name="arrow_back" size={24}/></button>} actions={<button className="icon-btn" data-tab="login"><Icon name="logout" size={22}/></button>}/>
    <PhoneBody>
      <div style={{ padding:'8px 16px' }}>
        <div className="card card-filled" style={{ display:'flex', alignItems:'center', gap:14, marginBottom:16 }}>
          <div style={{ width:56, height:56, borderRadius:'50%', background:'var(--primary)', color:'var(--on-primary)', display:'flex', alignItems:'center', justifyContent:'center', fontFamily:'var(--font-display)', fontWeight:600, fontSize:24 }}>A</div>
          <div style={{ flex:1 }}>
            <div className="title-l" style={{ color:'var(--on-surface)' }}>Ana Souza</div>
            <div className="body-s" style={{ color:'var(--on-surface-variant)' }}>ana@exemplo.com</div>
          </div>
          <button className="icon-btn"><Icon name="edit" size={20}/></button>
        </div>

        <div className="label-m" style={{ color:'var(--on-surface-variant)', margin:'4px 8px 6px' }}>ESTUDO</div>
        <div className="card card-filled" style={{ padding:0, marginBottom:16 }}>
          <div style={{ padding:'12px 16px' }}>
            <div className="body-l" style={{ color:'var(--on-surface)', marginBottom:8 }}>Meta de estudo por dia</div>
            <SegMinutes sel={1}/>
          </div>
          <hr className="divider divider-inset"/>
          <div style={{ padding:'12px 16px' }}>
            <div className="body-l" style={{ color:'var(--on-surface)', marginBottom:2 }}>Nível de conteúdo</div>
            <div className="body-s" style={{ color:'var(--on-surface-variant)', marginBottom:10 }}>Limita kanji, leituras e práticas ao que você liberou.</div>
            <div className="segmented" style={{ width:'100%' }}>
              <button className="seg selected" style={{ flex:1 }}>N5</button>
              <button className="seg" style={{ flex:1 }}>N4</button>
              <button className="seg" style={{ flex:1, opacity:0.5 }}><Icon name="lock" size={14}/> N3</button>
            </div>
          </div>
          <hr className="divider divider-inset"/>
          <SettingRowM label="Idioma da interface" control={<span className="body-m" style={{ color:'var(--on-surface-variant)' }}>Português ▾</span>}/>
          <hr className="divider divider-inset"/>
          <SettingRowM label="Notificações diárias" control={<div className="switch on"/>}/>
        </div>

        <div className="label-m" style={{ color:'var(--on-surface-variant)', margin:'4px 8px 6px' }}>LEITURA</div>
        <div className="card card-filled" style={{ padding:0, marginBottom:16 }}>
          <SettingRowM label="Furigana" control={<span className="body-m" style={{ color:'var(--on-surface-variant)' }}>Ao tocar ▾</span>}/>
          <hr className="divider divider-inset"/>
          <SettingRowM label="Romaji visível" control={<div className="switch"/>}/>
          <hr className="divider divider-inset"/>
          <SettingRowM label="Tema escuro" control={<div data-theme-toggle className={`switch${theme==="dark"?" on":""}`}/>}/>
        </div>

        <div className="label-m" style={{ color:'var(--on-surface-variant)', margin:'4px 8px 6px' }}>PROGRESSO</div>
        <div className="card card-filled">
          <div style={{ display:'grid', gridTemplateColumns:'repeat(3,1fr)', gap:12, marginBottom:14 }}>
            <StatTile n="14" l="dias" ic="local_fire_department"/>
            <StatTile n="142" l="palavras" ic="menu_book"/>
            <StatTile n="312" l="revisões" ic="style"/>
          </div>
          <div className="label-m" style={{ color:'var(--on-surface-variant)', marginBottom:6 }}>ÚLTIMOS 30 DIAS</div>
          <div style={{ display:'grid', gridTemplateColumns:'repeat(15,1fr)', gap:3 }}>
            {Array.from({length:30}).map((_,i)=>(
              <div key={i} style={{ aspectRatio:'1', borderRadius:3, background: i<24 ? `color-mix(in srgb, var(--primary) ${30+ (i%5)*16}%, transparent)` : 'var(--surface-container-highest)' }}/>
            ))}
          </div>
        </div>
      </div>
    </PhoneBody>
    <NavBar active="profile"/>
  </PhoneFrame>
);

const ProfileDesktop = ({ theme = "light" }) => (
  <DesktopFrame theme={theme} label="Perfil — desktop" url="app.yomineko.com/perfil">
    <NavDrawer active="profile" badge={{ review:12 }} drawer={true}/>
    <div style={{ flex:1, overflowY:'auto', padding:'28px 32px' }}>
      <div className="headline-l" style={{ color:'var(--on-surface)', marginBottom:4 }}>Perfil</div>
      <div className="body-m" style={{ color:'var(--on-surface-variant)', marginBottom:20 }}>Suas configurações afetam todas as telas.</div>
      <div style={{ display:'grid', gridTemplateColumns:'1fr 1fr', gap:20, alignItems:'flex-start' }}>
        <div>
          <div className="card card-filled" style={{ display:'flex', alignItems:'center', gap:14, marginBottom:16 }}>
            <div style={{ width:64, height:64, borderRadius:'50%', background:'var(--primary)', color:'var(--on-primary)', display:'flex', alignItems:'center', justifyContent:'center', fontFamily:'var(--font-display)', fontWeight:600, fontSize:28 }}>A</div>
            <div style={{ flex:1 }}>
              <div className="title-l" style={{ color:'var(--on-surface)' }}>Ana Souza</div>
              <div className="body-s" style={{ color:'var(--on-surface-variant)' }}>ana@exemplo.com · membro desde nov/2025</div>
            </div>
            <button className="btn btn-outlined btn-sm">Editar</button>
          </div>
          <div className="label-m" style={{ color:'var(--on-surface-variant)', margin:'4px 0 6px' }}>ESTUDO</div>
          <div className="card card-filled" style={{ padding:'16px', marginBottom:16 }}>
            <div className="body-l" style={{ color:'var(--on-surface)', marginBottom:8 }}>Meta de estudo por dia</div>
            <SegMinutes sel={1}/>
            <hr className="divider" style={{ margin:'14px 0' }}/>
            <div className="body-l" style={{ color:'var(--on-surface)', marginBottom:8 }}>Nível de conteúdo <span className="body-s" style={{ color:'var(--on-surface-variant)' }}>— limita kanji, leituras e práticas</span></div>
            <div className="segmented" style={{ width:'100%' }}>
              <button className="seg selected" style={{ flex:1, justifyContent:'center' }}>N5</button>
              <button className="seg" style={{ flex:1, justifyContent:'center' }}>N4</button>
              <button className="seg" style={{ flex:1, justifyContent:'center', opacity:0.5 }}><Icon name="lock" size={14}/> N3</button>
            </div>
            <hr className="divider" style={{ margin:'14px 0' }}/>
            <div style={{ display:'flex', justifyContent:'space-between', alignItems:'center' }}><span className="body-l">Limite diário de revisões</span><span className="body-m" style={{ color:'var(--on-surface-variant)' }}>100 ▾</span></div>
          </div>
          <div className="label-m" style={{ color:'var(--on-surface-variant)', margin:'4px 0 6px' }}>LEITURA & APARÊNCIA</div>
          <div className="card card-filled" style={{ padding:0 }}>
            <SettingRowM label="Furigana" control={<span className="body-m" style={{ color:'var(--on-surface-variant)' }}>Ao tocar ▾</span>}/>
            <hr className="divider divider-inset"/>
            <SettingRowM label="Romaji visível" control={<div className="switch"/>}/>
            <hr className="divider divider-inset"/>
            <SettingRowM label="Tema escuro" control={<div data-theme-toggle className={`switch${theme==="dark"?" on":""}`}/>}/>
          </div>
        </div>
        <div>
          <div className="label-m" style={{ color:'var(--on-surface-variant)', margin:'4px 0 6px' }}>PROGRESSO</div>
          <div className="card card-filled" style={{ marginBottom:16 }}>
            <div style={{ display:'grid', gridTemplateColumns:'repeat(3,1fr)', gap:12 }}>
              <StatTile n="14" l="dias" ic="local_fire_department"/>
              <StatTile n="142" l="palavras" ic="menu_book"/>
              <StatTile n="27" l="kanji" ic="translate"/>
              <StatTile n="7" l="lições" ic="school"/>
              <StatTile n="3h12m" l="tempo" ic="schedule"/>
              <StatTile n="312" l="revisões" ic="style"/>
            </div>
          </div>
          <div className="label-m" style={{ color:'var(--on-surface-variant)', margin:'4px 0 6px' }}>ATIVIDADE · 90 DIAS</div>
          <div className="card card-filled">
            <div style={{ display:'grid', gridTemplateColumns:'repeat(30,1fr)', gap:3 }}>
              {Array.from({length:90}).map((_,i)=>{
                const on = Math.random()>0.32; const lvl = Math.floor(Math.random()*3)+1;
                return <div key={i} style={{ aspectRatio:'1', borderRadius:2, background: on ? `color-mix(in srgb, var(--primary) ${lvl*28}%, transparent)` : 'var(--surface-container-highest)' }}/>;
              })}
            </div>
          </div>
        </div>
      </div>
    </div>
  </DesktopFrame>
);

export {
  DashboardMobile, DashboardDesktop, ProfileMobile, ProfileDesktop,
  StatTile, PracticeTile, ContinueCard, ReviewCard
};
