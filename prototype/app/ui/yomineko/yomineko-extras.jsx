import React from 'react';
import { Icon } from './m3';
import { Yomineko } from './mascot';

/* ============================================================
   Yomineko — shared extras: filter button+sheet, level gating
   ============================================================ */

// A compact filter trigger button (shows active filter)
const FilterButton = ({ label = "Filtros", active, onClick, count }) => (
  <button onClick={onClick} className="chip" style={{ gap:6, borderColor:'var(--outline)', cursor:'pointer' }}>
    <Icon name="tune" size={18} className="chip-ic"/>
    {active || label}
    {count!=null && <span className="pill pill-primary" style={{ height:18, padding:'0 7px', fontSize:11 }}>{count}</span>}
    <Icon name="expand_more" size={18}/>
  </button>
);

// Filter bottom sheet — single or multi select groups
const FilterSheet = ({ title = "Filtrar", groups = [], onClose, centered = false }) => {
  const initial = {};
  groups.forEach((g, gi) => g.options.forEach((o, oi) => { if (o.selected) initial[`${gi}:${oi}`] = true; }));
  const [sel, setSel] = React.useState(initial);
  const toggle = (k) => setSel((s) => ({ ...s, [k]: !s[k] }));
  return (
  <div className="sheet-scrim" style={centered ? { alignItems:'center' } : undefined} onClick={(e)=>{ if (e.target===e.currentTarget && onClose) onClose(); }}>
    <div className={centered ? '' : 'bottom-sheet'} style={centered ? { background:'var(--surface-container-low)', borderRadius:'var(--r-xl)', width:'100%', maxWidth:400, padding:'20px 0 24px', boxShadow:'var(--elev-3)', maxHeight:'82%', overflowY:'auto' } : undefined}>
      {!centered && <div className="sheet-handle"/>}
      <div style={{ padding:'0 20px 8px' }}>
        <div style={{ display:'flex', alignItems:'center', justifyContent:'space-between', marginBottom:8 }}>
          <span className="title-l">{title}</span>
          <button className="icon-btn" onClick={onClose}><Icon name="close" size={22}/></button>
        </div>
        {groups.map((g,gi)=>(
          <div key={gi} style={{ marginBottom:18 }}>
            <div className="label-m" style={{ color:'var(--on-surface-variant)', marginBottom:10 }}>{g.label}</div>
            <div style={{ display:'flex', flexWrap:'wrap', gap:8 }}>
              {g.options.map((o,oi)=>{
                const k = `${gi}:${oi}`; const on = !!sel[k];
                return (
                <button key={oi} onClick={()=>toggle(k)} className={`chip${on?' selected':''}`} style={{ cursor:'pointer' }}>
                  {o.dot && <span style={{ width:10, height:10, borderRadius:'50%', background:o.dot }}/>}
                  {o.label}
                  {on && <Icon name="check" size={16} className="chip-ic"/>}
                </button>
                );
              })}
            </div>
          </div>
        ))}
        <div style={{ display:'flex', gap:10, marginTop:8 }}>
          <button className="btn btn-text" style={{ flex:1 }} onClick={()=>setSel({})}>Limpar</button>
          <button className="btn btn-filled" style={{ flex:2 }} onClick={onClose}>Aplicar</button>
        </div>
      </div>
    </div>
  </div>
  );
};

// Level lock chip — content beyond the user's unlocked level
const LockedLevel = ({ level = "N4" }) => (
  <span className="pill pill-outline" style={{ gap:4, color:'var(--on-surface-variant)' }}>
    <Icon name="lock" size={14}/> {level} bloqueado
  </span>
);

// A "level reveal" row — collapsed advanced reading the user hasn't unlocked
const LockedReadingRow = ({ kind, level = "N4" }) => (
  <div style={{ display:'flex', alignItems:'center', gap:10, padding:'10px 12px', borderRadius:'var(--r-md)', background:'var(--surface-container-high)', opacity:0.7 }}>
    <Icon name="lock" size={18} color="var(--on-surface-variant)"/>
    <span className="body-m" style={{ flex:1, color:'var(--on-surface-variant)' }}>Leitura {kind} avançada</span>
    <span className="pill pill-outline">desbloqueia em {level}</span>
  </div>
);

export { FilterButton, FilterSheet, LockedLevel, LockedReadingRow };
