import React from 'react';
import { Icon, PhoneFrame, DesktopFrame, PhoneBody, AppBar, NavBar, NavDrawer } from './m3';
import { Yomineko } from './mascot';
import { FilterButton, FilterSheet } from './yomineko-extras';

/* ============================================================
   Yomineko — COURSE: course select + course tree (mobile + desktop)
   ============================================================ */

const COURSES = [
  { id:"n5", t:"N5 — Fundamentos", sub:"Hiragana, katakana, ~100 kanji, ~800 palavras", prog:0.42, state:"active", topics:5, lessons:25 },
  { id:"n4", t:"N4 — Bases Intermediárias", sub:"Forma て, adjetivos, polidez básica", prog:0, state:"available", topics:7, lessons:32 },
  { id:"n3", t:"N3 — Conversação Cotidiana", sub:"Construções complexas, leitura ampliada", prog:0, state:"locked", topics:9, lessons:48 },
  { id:"n2", t:"N2 — Avançado", sub:"Texto jornalístico, registro", prog:0, state:"locked", topics:11, lessons:62 },
  { id:"n1", t:"N1 — Fluência", sub:"Material acadêmico e literário", prog:0, state:"locked", topics:12, lessons:78 },
];

const TOPICS = [
  { t:"Hiragana — Vogais", done:5, total:5, lessons:[
    { n:"01", t:"あ い う え お", s:"done" }, { n:"02", t:"Prática de vogais", s:"done" },
  ]},
  { t:"Hiragana — Família K", done:3, total:5, lessons:[
    { n:"06", t:"か き く け こ", s:"done" }, { n:"07", t:"Prática com K", s:"done" },
    { n:"08", t:"Dakuten が ぎ ぐ", s:"done" }, { n:"09", t:"Leitura: diálogos", s:"available" },
    { n:"10", t:"Revisão", s:"locked" },
  ]},
  { t:"Partículas básicas", done:1, total:4, lessons:[
    { n:"20", t:"A partícula は", s:"in_progress" }, { n:"21", t:"A partícula の", s:"locked" },
    { n:"22", t:"A partícula か", s:"locked" }, { n:"23", t:"Apresentações", s:"locked" },
  ]},
];

const CourseCardYm = ({ c }) => {
  const active = c.state==="active", locked = c.state==="locked";
  return (
    <div className="card card-elevated" style={{ opacity: locked?0.6:1, borderLeft: active?'4px solid var(--primary)':'none', padding:'16px' }}>
      <div style={{ display:'flex', justifyContent:'space-between', alignItems:'flex-start', gap:8 }}>
        <div style={{ flex:1 }}>
          <div style={{ display:'flex', gap:6, marginBottom:4 }}>
            {active && <span className="pill pill-primary">ATIVO</span>}
            {c.state==="available" && <span className="pill">DISPONÍVEL</span>}
            {locked && <span className="pill pill-outline"><Icon name="lock" size={14}/> BLOQUEADO</span>}
          </div>
          <div className="title-l" style={{ color:'var(--on-surface)' }}>{c.t}</div>
          <div className="body-s" style={{ color:'var(--on-surface-variant)', marginTop:2 }}>{c.sub}</div>
        </div>
      </div>
      <div style={{ display:'flex', alignItems:'center', gap:10, marginTop:12 }}>
        <div className="linear-prog" style={{ flex:1 }}><i style={{ width:`${c.prog*100}%` }}/></div>
        <span className="label-m" style={{ color:'var(--on-surface-variant)' }}>{Math.round(c.prog*100)}%</span>
      </div>
      <div style={{ display:'flex', justifyContent:'space-between', alignItems:'center', marginTop:12 }}>
        <div style={{ display:'flex', gap:6 }}>
          <span className="pill pill-outline">{c.topics} tópicos</span>
          <span className="pill pill-outline">{c.lessons} lições</span>
        </div>
        {active && <button className="btn btn-tonal btn-sm" data-tab="course">Continuar</button>}
        {c.state==="available" && <button className="btn btn-filled btn-sm" data-tab="course">Ativar</button>}
        {locked && <span className="body-s" style={{ color:'var(--on-surface-variant)' }}>conclua o anterior</span>}
      </div>
    </div>
  );
};

// ---- Course select ----
const CourseSelectMobile = ({ theme = "light" }) => (
  <PhoneFrame theme={theme} label="Trocar de curso — mobile">
    <AppBar title="Cursos" leading={<button className="icon-btn" data-tab="course"><Icon name="arrow_back" size={24}/></button>}/>
    <PhoneBody>
      <div style={{ padding:'4px 16px 8px' }}>
        <div className="body-m" style={{ color:'var(--on-surface-variant)', marginBottom:12 }}>Apenas um curso ativo por vez. Trocar mantém todo o progresso.</div>
        <div style={{ display:'flex', flexDirection:'column', gap:12 }}>
          {COURSES.map(c=><CourseCardYm key={c.id} c={c}/>)}
        </div>
      </div>
    </PhoneBody>
    <NavBar active="study" badge={{ review:12 }}/>
  </PhoneFrame>
);

const CourseSelectDesktop = ({ theme = "light" }) => (
  <DesktopFrame theme={theme} label="Trocar de curso — desktop" url="app.yomineko.com/cursos">
    <NavDrawer active="study" badge={{ review:12 }} drawer={true}/>
    <div style={{ flex:1, overflowY:'auto', padding:'28px 32px' }}>
      <div className="headline-l" style={{ color:'var(--on-surface)', marginBottom:4 }}>Trocar de curso</div>
      <div className="body-m" style={{ color:'var(--on-surface-variant)', marginBottom:20 }}>Apenas um curso ativo por vez. Trocar mantém todo o progresso.</div>
      <div style={{ display:'grid', gridTemplateColumns:'repeat(auto-fit, minmax(360px,1fr))', gap:16, maxWidth:900 }}>
        {COURSES.map(c=><CourseCardYm key={c.id} c={c}/>)}
      </div>
    </div>
  </DesktopFrame>
);

// ---- Lesson status leading icon ----
const LessonStatusIcon = ({ s }) => {
  const map = {
    done:        { ic:"check_circle", c:"var(--primary)", fill:true },
    in_progress: { ic:"timelapse", c:"var(--primary)", fill:false },
    available:   { ic:"play_circle", c:"var(--on-surface)", fill:false },
    locked:      { ic:"lock", c:"var(--outline)", fill:false },
  }[s];
  return <Icon name={map.ic} size={24} fill={map.fill} color={map.c}/>;
};

const TopicCardYm = ({ topic, idx }) => {
  const status = topic.done===topic.total ? "Concluído" : topic.done>0 ? "Em andamento" : "Não iniciado";
  const pill = topic.done===topic.total ? "pill-success" : topic.done>0 ? "pill-primary" : "pill-outline";
  return (
    <div className="card card-elevated" style={{ padding:0, overflow:'hidden' }}>
      <div style={{ display:'flex', justifyContent:'space-between', alignItems:'center', padding:'14px 16px' }}>
        <div>
          <div style={{ display:'flex', gap:8, alignItems:'center', marginBottom:2 }}>
            <span className="label-m" style={{ color:'var(--on-surface-variant)' }}>TÓPICO {String(idx+1).padStart(2,"0")}</span>
            <span className={`pill ${pill}`}>{status}</span>
          </div>
          <div className="title-m" style={{ color:'var(--on-surface)' }}>{topic.t}</div>
        </div>
        <div style={{ textAlign:'right' }}>
          <div className="title-l" style={{ color:'var(--on-surface)' }}>{topic.done}<span className="body-s" style={{ color:'var(--on-surface-variant)' }}>/{topic.total}</span></div>
        </div>
      </div>
      <div className="linear-prog" style={{ borderRadius:0 }}><i style={{ width:`${topic.done/topic.total*100}%` }}/></div>
      <div>
        {topic.lessons.map((l,i)=>(
          <div key={i} className="list-item" data-go={l.s!=="locked" ? "lesson" : undefined} style={{ minHeight:52, cursor: l.s!=="locked"?'pointer':'default', opacity: l.s==="locked"?0.55:1, borderTop: i>0?'1px solid var(--outline-variant)':'none' }}>
            <LessonStatusIcon s={l.s}/>
            <div className="list-text">
              <div style={{ display:'flex', gap:8, alignItems:'baseline' }}>
                <span className="body-s" style={{ color:'var(--on-surface-variant)' }}>{l.n}</span>
                <span className="list-headline">{l.t}</span>
              </div>
            </div>
            {l.s!=="locked" && <Icon name="chevron_right" size={20} color="var(--on-surface-variant)"/>}
          </div>
        ))}
      </div>
    </div>
  );
};

const CourseTreeMobile = ({ theme = "light", filterOpen: filterOpenProp }) => {
  const [filterOpen, setFilterOpen] = React.useState(!!filterOpenProp);
  return (
  <PhoneFrame theme={theme} label={filterOpen?"Árvore — filtro":"Árvore do curso — mobile"}>
    <AppBar title="Curso"/>
    <PhoneBody>
      {/* active course banner */}
      <div style={{ padding:'4px 16px 8px' }}>
        <div className="card" style={{ padding:'14px 16px', background:'linear-gradient(135deg, color-mix(in srgb, var(--magic-1) 14%, var(--surface-container-low)), var(--surface-container-low))', boxShadow:'var(--elev-1)' }}>
          <div style={{ display:'flex', justifyContent:'space-between', alignItems:'flex-start' }}>
            <div>
              <span className="label-m" style={{ color:'var(--primary)' }}>CURSO ATIVO</span>
              <div className="title-l" style={{ color:'var(--on-surface)' }}>N5 — Fundamentos</div>
            </div>
            <button className="btn btn-tonal btn-sm" data-go="courseSelect"><Icon name="swap_horiz" size={18}/> Trocar</button>
          </div>
          <div style={{ display:'flex', alignItems:'center', gap:10, marginTop:10 }}>
            <div className="linear-prog" style={{ flex:1 }}><i style={{ width:'42%' }}/></div>
            <span className="label-m" style={{ color:'var(--on-surface-variant)' }}>42%</span>
          </div>
        </div>
      </div>
      <div style={{ padding:'0 16px 8px', display:'flex', gap:8, alignItems:'center' }}>
        <FilterButton active="Todos" count={3} onClick={()=>setFilterOpen(true)}/>
        <span className="body-s" style={{ color:'var(--on-surface-variant)' }}>3 tópicos</span>
      </div>
      <div style={{ padding:'0 16px', display:'flex', flexDirection:'column', gap:14 }}>
        {TOPICS.map((t,i)=><TopicCardYm key={i} topic={t} idx={i}/>)}
      </div>
      <div style={{ height:12 }}/>
    </PhoneBody>
    <NavBar active="study" badge={{ review:12 }}/>
    {filterOpen && <FilterSheet title="Filtrar tópicos" onClose={()=>setFilterOpen(false)} groups={[
      { label:"ESTADO", options:[{label:"Todos",selected:true},{label:"Em andamento"},{label:"Concluídos"},{label:"Bloqueados"}] },
      { label:"ORDENAR", options:[{label:"Ordem do curso",selected:true},{label:"Menos progresso"}] },
    ]}/>}
  </PhoneFrame>
  );
};

const CourseTreeDesktop = ({ theme = "light" }) => {
  const [filterOpen, setFilterOpen] = React.useState(false);
  return (
  <DesktopFrame theme={theme} label="Árvore do curso — desktop" url="app.yomineko.com/curso">
    <NavDrawer active="study" badge={{ review:12 }} drawer={true}/>
    <div style={{ flex:1, overflowY:'auto', padding:'28px 32px' }}>
      <div className="card" style={{ padding:'18px 20px', marginBottom:20, background:'linear-gradient(135deg, color-mix(in srgb, var(--magic-1) 12%, var(--surface-container-low)), var(--surface-container-low))', boxShadow:'var(--elev-1)' }}>
        <div style={{ display:'flex', justifyContent:'space-between', alignItems:'center' }}>
          <div>
            <span className="label-m" style={{ color:'var(--primary)' }}>CURSO ATIVO</span>
            <div style={{ display:'flex', alignItems:'baseline', gap:14 }}>
              <span className="headline-s" style={{ color:'var(--on-surface)' }}>N5 — Fundamentos</span>
              <span className="body-m" style={{ color:'var(--on-surface-variant)' }}>5 tópicos · 25 lições · 42%</span>
            </div>
            <div className="linear-prog" style={{ marginTop:8, maxWidth:480 }}><i style={{ width:'42%' }}/></div>
          </div>
          <div style={{ display:'flex', gap:8 }}>
            <button className="btn btn-outlined" data-go="courseSelect"><Icon name="swap_horiz" size={18}/> Trocar de curso</button>
            <button className="btn btn-filled" data-go="lesson">Continuar <Icon name="arrow_forward" size={18}/></button>
          </div>
        </div>
      </div>
      <div style={{ display:'flex', alignItems:'center', gap:12, marginBottom:14 }}>
        <FilterButton active="Todos" count={3} onClick={()=>setFilterOpen(true)}/>
        <span className="body-s" style={{ color:'var(--on-surface-variant)' }}>mostrando 3 de 5 tópicos</span>
      </div>
      <div style={{ display:'flex', flexDirection:'column', gap:16, width:'100%', maxWidth:1100, margin:'0 auto' }}>
        {TOPICS.map((t,i)=><TopicCardYm key={i} topic={t} idx={i}/>)}
      </div>
    </div>
    {filterOpen && <FilterSheet centered title="Filtrar tópicos" onClose={()=>setFilterOpen(false)} groups={[
      { label:"ESTADO", options:[{label:"Todos",selected:true},{label:"Em andamento"},{label:"Concluídos"},{label:"Bloqueados"}] },
      { label:"ORDENAR", options:[{label:"Ordem do curso",selected:true},{label:"Menos progresso"}] },
    ]}/>}
  </DesktopFrame>
  );
};

export {
  CourseSelectMobile, CourseSelectDesktop, CourseTreeMobile, CourseTreeDesktop,
  CourseCardYm, TopicCardYm, LessonStatusIcon
};
