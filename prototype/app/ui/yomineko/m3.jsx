import React, { createContext, useContext } from 'react';
import { Yomineko, YominekoLogo } from './mascot';
import { useApp, NAV_TO_SCREEN, reviewDue } from '../app/store';

// When set to 'app', PhoneFrame/DesktopFrame render full-bleed (real app)
// instead of as a device mock-up. Set by the App shell.
export const FrameModeContext = createContext('device');

/* ============================================================
   Yomineko — M3 JSX primitives + themed device frames
   ============================================================ */

// Material Symbols icon (font loaded in HTML)
const Icon = ({ name, size = 24, fill = false, weight = 400, grade = 0, color, style }) => (
  <span className="material-symbols-rounded" style={{
    fontSize: size, lineHeight: 1, color,
    fontVariationSettings: `'FILL' ${fill?1:0}, 'wght' ${weight}, 'GRAD' ${grade}, 'opsz' ${size}`,
    userSelect: 'none', ...style
  }}>{name}</span>
);

// ---- Phone frame (themed) ----
const PhoneFrame = ({ theme = "light", children, label, w = 380, h = 800, app: appProp = false }) => {
  const app = appProp || useContext(FrameModeContext) === 'app';
  if (app) return (
    <div className="ym" data-theme={theme} style={{ width:'100%', height:'100%', background:'var(--surface)', display:'flex', flexDirection:'column', overflow:'hidden' }}>
      {children}
    </div>
  );
  return (
  <div style={{ display:'flex', flexDirection:'column', alignItems:'center', gap:12 }}>
    <div style={{
      width: w, borderRadius: 44, padding: 10,
      background: theme==="dark" ? "#000" : "#1a1426",
      boxShadow: "0 20px 50px rgba(40,20,80,0.28), 0 4px 12px rgba(0,0,0,0.2)",
      position:'relative'
    }}>
      <div className="ym" data-theme={theme} style={{
        width: '100%', height: h, borderRadius: 36, overflow: 'hidden',
        background: 'var(--surface)', position: 'relative',
        display:'flex', flexDirection:'column'
      }}>
        {/* status bar */}
        <div className="ym" data-theme={theme} style={{
          height: 32, flexShrink:0, display:'flex', alignItems:'center', justifyContent:'space-between',
          padding: '0 24px', background:'var(--surface)', color:'var(--on-surface)',
          fontFamily:'var(--font-body)', fontWeight:700, fontSize:13, position:'relative', zIndex:5
        }}>
          <span>9:41</span>
          <div style={{ display:'flex', gap:5, alignItems:'center' }}>
            <Icon name="signal_cellular_alt" size={16}/>
            <Icon name="wifi" size={16}/>
            <Icon name="battery_full" size={16}/>
          </div>
        </div>
        {children}
      </div>
    </div>
    {label && <DeviceLabel icon="smartphone" text={label} theme={theme}/>}
  </div>
  );
};

// ---- Desktop / browser frame (themed) ----
const DesktopFrame = ({ theme = "light", children, label, w = 1180, h = 760, url = "app.yomineko.com", app: appProp = false }) => {
  const app = appProp || useContext(FrameModeContext) === 'app';
  if (app) return (
    <div className="ym" data-theme={theme} style={{ width:'100%', height:'100%', background:'var(--surface)', display:'flex', overflow:'hidden' }}>
      {children}
    </div>
  );
  return (
  <div style={{ display:'flex', flexDirection:'column', alignItems:'center', gap:12 }}>
    <div style={{
      width: w, maxWidth:'100%', borderRadius: 14, overflow:'hidden',
      boxShadow: "0 24px 60px rgba(40,20,80,0.22), 0 4px 12px rgba(0,0,0,0.16)",
      border: '1px solid rgba(0,0,0,0.08)'
    }}>
      {/* chrome */}
      <div className="ym" data-theme={theme} style={{
        height: 44, display:'flex', alignItems:'center', gap:8, padding:'0 16px',
        background: theme==="dark" ? "#2b2930" : "#E6E0EA", flexShrink:0
      }}>
        <div style={{ display:'flex', gap:8 }}>
          <span style={{ width:12, height:12, borderRadius:'50%', background:'#FF5F57' }}/>
          <span style={{ width:12, height:12, borderRadius:'50%', background:'#FEBC2E' }}/>
          <span style={{ width:12, height:12, borderRadius:'50%', background:'#28C840' }}/>
        </div>
        <div className="ym" data-theme={theme} style={{
          marginLeft:16, flex:1, maxWidth:520, height:28, borderRadius:999,
          background:'var(--surface)', color:'var(--on-surface-variant)',
          display:'flex', alignItems:'center', gap:8, padding:'0 14px',
          fontFamily:'var(--font-body)', fontWeight:600, fontSize:13
        }}>
          <Icon name="lock" size={14}/>{url}
        </div>
      </div>
      <div className="ym" data-theme={theme} style={{ height:h, background:'var(--surface)', overflow:'hidden', display:'flex' }}>
        {children}
      </div>
    </div>
    {label && <DeviceLabel icon="desktop_windows" text={label} theme={theme}/>}
  </div>
  );
};

const DeviceLabel = ({ icon, text, theme }) => (
  <div style={{ display:'flex', alignItems:'center', gap:6, fontFamily:'"Nunito",sans-serif', fontWeight:700, fontSize:13, color:'#6b5b8a' }}>
    <span className="material-symbols-rounded" style={{ fontSize:16 }}>{icon}</span>
    {text}
    <span style={{ marginLeft:4, padding:'1px 8px', borderRadius:999, background: theme==="dark"?"#2b2535":"#E4DBF2", color:'#6b5b8a', fontSize:11, textTransform:'uppercase', letterSpacing:'0.06em' }}>{theme==="dark"?"Escuro":"Claro"}</span>
  </div>
);

// ---- Scrollable region inside a phone (fills remaining height) ----
const PhoneBody = ({ children, pad = true, style }) => (
  <div style={{ flex:1, overflowY:'auto', padding: pad? '0 0 8px' : 0, position:'relative', ...style }}>
    {children}
  </div>
);

// ---- M3 App bar ----
const AppBar = ({ title, leading, actions, center, scrolled }) => (
  <div className={`appbar${center?' center':''}${scrolled?' scrolled':''}`} style={{ flexShrink:0 }}>
    {leading || <span style={{ width:8 }}/>}
    <span className="appbar-title">{title}</span>
    {actions}
  </div>
);

// ---- Bottom navigation bar (mobile) ----
const NavBar = ({ active = "study", badge = {} }) => {
  const { goTab } = useApp();
  const badges = { ...badge, review: reviewDue() || null };
  const dests = [
    { id:"home",     icon:"home",        label:"Início" },
    { id:"study",    icon:"auto_stories",label:"Curso" },
    { id:"review",   icon:"style",       label:"Revisar" },
    { id:"practice", icon:"target",      label:"Prática" },
    { id:"profile",  icon:"person",      label:"Perfil" },
  ];
  return (
    <div className="navbar" style={{ flexShrink:0 }}>
      {dests.map(d => (
        <button key={d.id} onClick={()=>goTab(NAV_TO_SCREEN[d.id]||d.id)} className={`navdest${d.id===active?' active':''}`}>
          <span className="nav-ic-wrap">
            <Icon name={d.icon} size={24} fill={d.id===active} className="nav-ic"/>
            {badges[d.id] && <span className="nav-badge">{badges[d.id]}</span>}
          </span>
          {d.label}
        </button>
      ))}
    </div>
  );
};

// ---- Navigation rail / drawer (desktop) ----
const NavDrawer = ({ active = "study", badge = {}, drawer = true }) => {
  const { goTab } = useApp();
  const badges = { ...badge, review: reviewDue() || null };
  const dests = [
    { id:"home",     icon:"home",         label:"Início" },
    { id:"study",    icon:"auto_stories", label:"Curso" },
    { id:"review",   icon:"style",        label:"Revisar" },
    { id:"practice", icon:"target",       label:"Prática" },
    { id:"vocab",    icon:"menu_book",    label:"Vocabulário" },
    { id:"kanji",    icon:"translate",    label:"Kanji" },
    { id:"profile",  icon:"person",       label:"Perfil" },
  ];
  if (!drawer) {
    return (
      <div className="navrail" style={{ flexShrink:0, borderRight:'1px solid var(--outline-variant)' }}>
        <div style={{ marginBottom:8 }}><YominekoLogo size={40}/></div>
        {dests.slice(0,5).map(d => (
          <button key={d.id} onClick={()=>goTab(NAV_TO_SCREEN[d.id]||d.id)} className={`rail-dest${d.id===active?' active':''}`}>
            <span className="nav-ic-wrap">
              <Icon name={d.icon} size={24} fill={d.id===active}/>
              {badges[d.id] && <span className="nav-badge" style={{ position:'absolute', top:0, right:6 }}>{badges[d.id]}</span>}
            </span>
            {d.label}
          </button>
        ))}
        <button onClick={()=>goTab('login')} className="rail-dest" style={{ marginTop:'auto' }}>
          <span className="nav-ic-wrap"><Icon name="logout" size={24}/></span>
          Sair
        </button>
      </div>
    );
  }
  return (
    <div className="navrail drawer" style={{ flexShrink:0, borderRight:'1px solid var(--outline-variant)' }}>
      <div style={{ display:'flex', alignItems:'center', gap:10, padding:'0 12px 16px' }}>
        <YominekoLogo size={36}/>
        <span style={{ fontFamily:'var(--font-display)', fontWeight:700, fontSize:22, color:'var(--on-surface)' }}>Yomineko</span>
      </div>
      {dests.map(d => (
        <button key={d.id} onClick={()=>goTab(NAV_TO_SCREEN[d.id]||d.id)} className={`drawer-item${d.id===active?' active':''}`}>
          <Icon name={d.icon} size={24} fill={d.id===active}/>
          {d.label}
          {badges[d.id] && <span className="nav-badge">{badges[d.id]}</span>}
        </button>
      ))}
      <button onClick={()=>goTab('login')} className="drawer-item" style={{ marginTop:'auto' }}>
        <Icon name="logout" size={24}/>
        Sair
      </button>
    </div>
  );
};

export {
  Icon, PhoneFrame, DesktopFrame, DeviceLabel, PhoneBody, AppBar, NavBar, NavDrawer
};
