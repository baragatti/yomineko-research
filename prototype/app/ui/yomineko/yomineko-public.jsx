import React from 'react';
import { Icon, PhoneFrame, DesktopFrame, PhoneBody } from './m3';
import { StarField, Yomineko, YominekoLogo } from './mascot';

/* ============================================================
   Yomineko — PUBLIC: Landing + Login (mobile + desktop)
   ============================================================ */

// ---------------- LANDING DESKTOP ----------------
const LandingDesktop = ({ theme = "light" }) => (
  <DesktopFrame theme={theme} label="Landing — desktop" url="yomineko.com">
    <div style={{ flex:1, overflowY:'auto' }}>
      {/* top bar */}
      <div style={{ display:'flex', alignItems:'center', justifyContent:'space-between', padding:'16px 32px' }}>
        <div style={{ display:'flex', alignItems:'center', gap:10 }}>
          <YominekoLogo size={36}/>
          <span style={{ fontFamily:'var(--font-display)', fontWeight:700, fontSize:22, color:'var(--on-surface)' }}>Yomineko</span>
        </div>
        <div style={{ display:'flex', alignItems:'center', gap:8 }}>
          <button className="btn btn-text">Método</button>
          <button className="btn btn-text">Sobre</button>
          <button className="btn btn-filled">Entrar</button>
        </div>
      </div>

      {/* hero */}
      <div style={{ position:'relative', padding:'40px 32px 48px', overflow:'hidden' }}>
        <div style={{ position:'absolute', inset:0, background:'radial-gradient(120% 80% at 80% 0%, color-mix(in srgb, var(--magic-1) 16%, transparent), transparent 60%)' }}/>
        <StarField><div style={{ position:'absolute', inset:0 }}/></StarField>
        <div style={{ position:'relative', display:'grid', gridTemplateColumns:'1.1fr 0.9fr', gap:24, alignItems:'center' }}>
          <div>
            <span className="pill pill-magic" style={{ height:28 }}><Icon name="auto_awesome" size={16}/> N5 → N1 · em português</span>
            <h1 className="display-m" style={{ color:'var(--on-surface)', margin:'14px 0 12px' }}>Aprenda japonês com um gato mágico.</h1>
            <p className="body-l" style={{ color:'var(--on-surface-variant)', maxWidth:480 }}>
              Yomineko te guia do zero à fluência: curso linear, revisão inteligente (FSRS-6) e seis modos de prática. Sem barulho — só você, o gato e o grimório.
            </p>
            <div style={{ display:'flex', gap:12, marginTop:22 }}>
              <button className="btn btn-magic btn-lg">Começar agora <Icon name="arrow_forward" size={20}/></button>
              <button className="btn btn-outlined btn-lg">Ver demonstração</button>
            </div>
          </div>
          <div style={{ display:'flex', justifyContent:'center' }}>
            <div style={{ position:'relative' }}>
              <div style={{ position:'absolute', inset:'-10% -10%', background:'radial-gradient(circle, var(--magic-glow), transparent 70%)', filter:'blur(8px)' }}/>
              <div style={{ position:'relative' }}><Yomineko pose="reading" size={300}/></div>
            </div>
          </div>
        </div>
      </div>

      {/* features */}
      <div style={{ padding:'8px 32px 40px' }}>
        <div style={{ display:'grid', gridTemplateColumns:'repeat(3,1fr)', gap:16 }}>
          {[
            { ic:"auto_stories", t:"Curso linear", d:"Módulo → Tópico → Lição. Avance no seu ritmo, com o caminho sempre claro." },
            { ic:"style", t:"Revisão inteligente", d:"Suas lições viram cartões. O FSRS-6 agenda só o que você precisa rever." },
            { ic:"target", t:"Seis práticas", d:"Hiragana, katakana, partículas, frases, conjugação e números." },
          ].map((f,i)=>(
            <div key={i} className="card card-filled" style={{ padding:'20px' }}>
              <div style={{ width:48, height:48, borderRadius:'var(--r-md)', background:'var(--primary-container)', color:'var(--on-primary-container)', display:'flex', alignItems:'center', justifyContent:'center' }}><Icon name={f.ic} size={26}/></div>
              <div className="title-l" style={{ color:'var(--on-surface)', margin:'12px 0 4px' }}>{f.t}</div>
              <div className="body-m" style={{ color:'var(--on-surface-variant)' }}>{f.d}</div>
            </div>
          ))}
        </div>
      </div>
    </div>
  </DesktopFrame>
);

// ---------------- LANDING MOBILE ----------------
const LandingMobile = ({ theme = "light" }) => (
  <PhoneFrame theme={theme} label="Landing — mobile">
    <div style={{ display:'flex', alignItems:'center', justifyContent:'space-between', padding:'8px 16px', flexShrink:0 }}>
      <div style={{ display:'flex', alignItems:'center', gap:8 }}>
        <YominekoLogo size={30}/>
        <span style={{ fontFamily:'var(--font-display)', fontWeight:700, fontSize:18, color:'var(--on-surface)' }}>Yomineko</span>
      </div>
      <button className="btn btn-text btn-sm">Entrar</button>
    </div>
    <PhoneBody>
      <div style={{ position:'relative', textAlign:'center', padding:'12px 20px 24px' }}>
        <div style={{ position:'absolute', inset:0, background:'radial-gradient(80% 50% at 50% 10%, color-mix(in srgb, var(--magic-1) 18%, transparent), transparent 70%)' }}/>
        <div style={{ position:'relative' }}>
          <Yomineko pose="reading" size={180}/>
          <span className="pill pill-magic" style={{ marginTop:4 }}><Icon name="auto_awesome" size={14}/> N5 → N1 · em português</span>
          <h1 className="headline-l" style={{ color:'var(--on-surface)', margin:'12px 0 8px' }}>Aprenda japonês com um gato mágico.</h1>
          <p className="body-m" style={{ color:'var(--on-surface-variant)' }}>Curso linear, revisão inteligente e seis práticas. Só você, o gato e o grimório.</p>
          <button className="btn btn-magic btn-lg" style={{ width:'100%', marginTop:18 }}>Começar agora <Icon name="arrow_forward" size={20}/></button>
          <button className="btn btn-text" style={{ marginTop:8 }}>Ver demonstração</button>
        </div>
      </div>
      <div style={{ padding:'0 16px 16px', display:'flex', flexDirection:'column', gap:10 }}>
        {[
          { ic:"auto_stories", t:"Curso linear", d:"Avance no seu ritmo." },
          { ic:"style", t:"Revisão inteligente", d:"FSRS-6 agenda por você." },
          { ic:"target", t:"Seis práticas", d:"Kana, partículas, frases…" },
        ].map((f,i)=>(
          <div key={i} className="card card-filled" style={{ display:'flex', gap:12, alignItems:'center' }}>
            <div style={{ width:44, height:44, borderRadius:'var(--r-md)', background:'var(--primary-container)', color:'var(--on-primary-container)', display:'flex', alignItems:'center', justifyContent:'center', flexShrink:0 }}><Icon name={f.ic} size={24}/></div>
            <div>
              <div className="title-s" style={{ color:'var(--on-surface)' }}>{f.t}</div>
              <div className="body-s" style={{ color:'var(--on-surface-variant)' }}>{f.d}</div>
            </div>
          </div>
        ))}
      </div>
    </PhoneBody>
  </PhoneFrame>
);

// ---------------- LOGIN MOBILE ----------------
const LoginMobile = ({ theme = "light", error }) => (
  <PhoneFrame theme={theme} label={`Login${error?" — erro":" — mobile"}`}>
    <PhoneBody>
      <div style={{ padding:'40px 24px 0', display:'flex', flexDirection:'column', alignItems:'center' }}>
        <Yomineko pose={error?"sleep":"wave"} size={120}/>
        <div className="headline-m" style={{ color:'var(--on-surface)', marginTop:8 }}>Yomineko</div>
        <div className="body-m" style={{ color:'var(--on-surface-variant)', marginBottom:24 }}>Bem-vindo de volta</div>

        <div style={{ width:'100%', display:'flex', flexDirection:'column', gap:16 }}>
          <div className={`field field-outlined`}>
            <div className="field-label">E-mail</div>
            <input defaultValue="ana@exemplo.com"/>
          </div>
          <div className={`field field-outlined${error?'':''}`} style={error?{ borderColor:'var(--error)' }:{}}>
            <div className="field-label" style={error?{ color:'var(--error)' }:{}}>Senha</div>
            <input type="password" defaultValue="••••••"/>
          </div>
          {error && <div style={{ display:'flex', gap:6, alignItems:'center', color:'var(--error)' }}><Icon name="error" size={18}/><span className="body-s">E-mail ou senha incorretos.</span></div>}
          <button className="btn btn-filled btn-lg" style={{ width:'100%' }} data-tab="dashboard">Entrar</button>
          <button className="btn btn-text">Esqueci minha senha</button>
        </div>
        <div className="body-s" style={{ color:'var(--on-surface-variant)', marginTop:24, textAlign:'center' }}>Sem conta? Cadastro aberto em breve.</div>
      </div>
    </PhoneBody>
  </PhoneFrame>
);

// ---------------- LOGIN DESKTOP ----------------
const LoginDesktop = ({ theme = "light" }) => (
  <DesktopFrame theme={theme} label="Login — desktop" url="yomineko.com/entrar" h={620}>
    <div style={{ flex:1, display:'grid', gridTemplateColumns:'1fr 1fr' }}>
      {/* left brand panel */}
      <div style={{ position:'relative', background:'linear-gradient(150deg, color-mix(in srgb, var(--magic-1) 22%, var(--surface)), var(--surface))', display:'flex', flexDirection:'column', alignItems:'center', justifyContent:'center', padding:'40px', overflow:'hidden' }}>
        <StarField><div style={{ position:'absolute', inset:0 }}/></StarField>
        <div style={{ position:'relative', textAlign:'center' }}>
          <Yomineko pose="reading" size={240}/>
          <div className="headline-m" style={{ color:'var(--on-surface)', marginTop:8 }}>Yomineko</div>
          <div className="body-l" style={{ color:'var(--on-surface-variant)', maxWidth:280, margin:'4px auto 0' }}>Seu grimório de japonês espera por você.</div>
        </div>
      </div>
      {/* right form */}
      <div style={{ display:'flex', alignItems:'center', justifyContent:'center', padding:'40px' }}>
        <div style={{ width:'100%', maxWidth:360 }}>
          <div className="headline-s" style={{ color:'var(--on-surface)' }}>Entrar</div>
          <div className="body-m" style={{ color:'var(--on-surface-variant)', marginBottom:24 }}>Continue de onde parou.</div>
          <div style={{ display:'flex', flexDirection:'column', gap:16 }}>
            <div className="field field-outlined"><div className="field-label">E-mail</div><input defaultValue="ana@exemplo.com"/></div>
            <div className="field field-outlined"><div className="field-label">Senha</div><input type="password" defaultValue="••••••"/></div>
            <button className="btn btn-filled btn-lg" style={{ width:'100%' }} data-tab="dashboard">Entrar</button>
            <button className="btn btn-text">Esqueci minha senha</button>
          </div>
          <div className="body-s" style={{ color:'var(--on-surface-variant)', marginTop:24, textAlign:'center' }}>Sem conta? Cadastro aberto em breve.</div>
        </div>
      </div>
    </div>
  </DesktopFrame>
);

export { LandingDesktop, LandingMobile, LoginMobile, LoginDesktop };
