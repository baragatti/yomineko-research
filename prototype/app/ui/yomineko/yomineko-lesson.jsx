import React from 'react';
import { Icon, PhoneFrame, DesktopFrame, PhoneBody, NavDrawer } from './m3';
import { Yomineko } from './mascot';
import {
  LESSON_WA, LHeading, LBody, NoteRow, ExampleCard, VocabRow,
  ExerciseMCQ, ExerciseParticle, BreakdownSheet, WordSheet, KanjiSheet, GrammarSheet, CultureSheet
} from './yomineko-lesson-parts';
import { playAudio } from '../app/audio';

/* ============================================================
   Yomineko — LESSON screens (mobile + desktop) assembled
   ============================================================ */

// Shared lesson content flow (used by both mobile & desktop bodies)
const LessonFlow = ({ openSheet }) => (
  <>
    <LHeading>O que é o tópico?</LHeading>
    <LBody>
      Em português dizemos „<i>quanto a mim</i>, eu sou brasileiro'. Em japonês, marcar esse „quanto a' é tão
      comum que existe uma partícula só para isso: <b className="jp">は</b>.
    </LBody>
    <NoteRow tone="info" title="は é escrito „ha', mas lê-se „wa' como partícula"
             hint="Toque para entender por quê" onOpen={()=>openSheet("grammar")} />

    <LHeading>Estrutura básica</LHeading>
    <ExampleCard jp="わたしは がくせい です。" reading="watashi wa gakusei desu"
                 pt="Quanto a mim, sou estudante." onBreakdown={()=>openSheet("breakdown")} />
    <ExampleCard jp="やまださんは せんせい です。" reading="Yamada-san wa sensei desu"
                 pt="O Sr. Yamada é professor." onBreakdown={()=>openSheet("breakdown")} />

    <button onClick={()=>openSheet("grammar")} className="list-item state" style={{
      margin:'8px 20px', width:'calc(100% - 40px)', background:'color-mix(in srgb, var(--magic-1) 8%, var(--surface))',
      borderRadius:'var(--r-md)', border:'1px solid color-mix(in srgb, var(--magic-1) 30%, transparent)', cursor:'pointer'
    }}>
      <span className="list-leading" style={{ background:'color-mix(in srgb, var(--magic-1) 18%, transparent)', color:'var(--magic-1)' }}>
        <Icon name="menu_book" size={22}/>
      </span>
      <div className="list-text">
        <div className="list-headline">Ponto de gramática · <span className="jp">～は</span></div>
        <div className="list-support">Como e quando usar o tópico</div>
      </div>
      <span className="material-symbols-rounded" style={{ color:'var(--on-surface-variant)' }}>chevron_right</span>
    </button>

    <LHeading>Negando</LHeading>
    <LBody>Para negar, troque <b className="jp">です</b> por <b className="jp">じゃありません</b> (fala) ou <b className="jp">ではありません</b> (formal).</LBody>
    <ExampleCard jp="わたしは アメリカじん じゃありません。" reading="watashi wa amerikajin ja arimasen"
                 pt="Eu não sou americano(a)." onBreakdown={()=>openSheet("breakdown")} />

    <NoteRow tone="culture" title="Por que o japonês precisa de partículas?"
             hint="Nota cultural · toque para ler" onOpen={()=>openSheet("culture")} />

    <LHeading>Vocabulário</LHeading>
    <div className="card card-elevated" style={{ margin:'8px 20px', padding:'4px 0' }}>
      {[
        { jp:"わたし", reading:"watashi", pt:"eu", pos:"pron." },
        { jp:"がくせい", reading:"gakusei", pt:"estudante", pos:"subst." },
        { jp:"せんせい", reading:"sensei", pt:"professor(a)", pos:"subst." },
        { jp:"ほん", reading:"hon", pt:"livro", pos:"subst." },
      ].map((w,i,a)=>(
        <VocabRow key={i} w={w} last={i===a.length-1} onOpen={()=>openSheet(i===1?"word":"word")} />
      ))}
    </div>

    <LHeading>Pratique agora</LHeading>
    <ExerciseMCQ state="fresh" />
    <ExerciseParticle />
  </>
);

// ---------------- MOBILE ----------------
const LessonMobile = ({ theme = "light", sheet: sheetProp = null }) => {
  const L = LESSON_WA;
  const [sheet, setSheet] = React.useState(sheetProp);
  return (
    <PhoneFrame theme={theme} label="Lição — mobile">
      {/* Lesson top app bar */}
      <div className="appbar" style={{ flexShrink:0, paddingRight:8 }}>
        <button className="icon-btn" data-tab="course"><Icon name="arrow_back" size={24}/></button>
        <div style={{ flex:1, minWidth:0 }}>
          <div className="label-m" style={{ color:'var(--on-surface-variant)', textTransform:'uppercase' }}>{L.course} · {L.topic}</div>
          <div className="title-m" style={{ color:'var(--on-surface)', whiteSpace:'nowrap', overflow:'hidden', textOverflow:'ellipsis' }}>{L.title}</div>
        </div>
        <button className="icon-btn" title="Furigana"><Icon name="subtitles" size={22}/></button>
        <button className="icon-btn"><Icon name="more_vert" size={22}/></button>
      </div>
      {/* Listen + progress bar */}
      <div style={{ flexShrink:0, padding:'4px 16px 12px', display:'flex', alignItems:'center', gap:12 }}>
        <button className="btn btn-magic btn-sm" onClick={()=>playAudio('わたしは がくせい です。')}><Icon name="play_arrow" size={18} fill/> Ouvir lição</button>
        <div className="linear-prog" style={{ flex:1 }}><i style={{ width:`${L.progress*100}%` }}/></div>
        <span className="label-m" style={{ color:'var(--on-surface-variant)' }}>{Math.round(L.progress*100)}%</span>
      </div>

      <PhoneBody style={{ paddingBottom:96 }}>
        <LessonFlow openSheet={setSheet} />
        <div style={{ height:8 }}/>
      </PhoneBody>

      {/* Sticky bottom action bar */}
      <div style={{ flexShrink:0, padding:'10px 16px 16px', background:'var(--surface-container-low)', borderTop:'1px solid var(--outline-variant)', display:'flex', gap:10, alignItems:'center' }}>
        <button className="btn btn-outlined" data-tab="course"><Icon name="arrow_back" size={18}/> Anterior</button>
        <button className="btn btn-filled" style={{ flex:1 }} data-tab="course">Concluir e avançar <Icon name="arrow_forward" size={18}/></button>
      </div>

      {/* Sheet overlay */}
      {sheet && (
        <div className="sheet-scrim" onClick={(e)=>{ if(e.target===e.currentTarget || e.target.closest('[data-close]')) setSheet(null); }}>
          {sheet==="breakdown" && <BreakdownSheet/>}
          {sheet==="word" && <WordSheet/>}
          {sheet==="kanji" && <KanjiSheet/>}
          {sheet==="grammar" && <GrammarSheet/>}
          {sheet==="culture" && <CultureSheet/>}
        </div>
      )}
    </PhoneFrame>
  );
};

// ---------------- DESKTOP ----------------
const LessonDesktop = ({ theme = "light", sideSheet: sideSheetProp = null }) => {
  const L = LESSON_WA;
  const [sideSheet, setSideSheet] = React.useState(sideSheetProp);
  const outline = [
    { l:"O que é o tópico", done:true, on:false },
    { l:"Estrutura básica", done:false, on:true },
    { l:"Negando", done:false, on:false },
    { l:"Vocabulário", done:false, on:false },
    { l:"Pratique agora", done:false, on:false },
  ];
  return (
    <DesktopFrame theme={theme} label="Lição — desktop" url="app.yomineko.com/curso/licao/L020">
      <NavDrawer active="study" badge={{ review: 12 }} drawer={false} />
      <div style={{ flex:1, display:'flex', minWidth:0, position:'relative' }}>
        {/* Left outline rail */}
        <div style={{ width:240, flexShrink:0, borderRight:'1px solid var(--outline-variant)', padding:'24px 16px', overflowY:'auto' }}>
          <button className="btn btn-text btn-sm" data-tab="course" style={{ marginBottom:14, paddingLeft:0 }}><Icon name="arrow_back" size={18}/> Voltar ao curso</button>
          <div className="label-m" style={{ color:'var(--on-surface-variant)', marginBottom:8 }}>NESTA LIÇÃO</div>
          {outline.map((o,i)=>(
            <div key={i} style={{ display:'flex', alignItems:'center', gap:10, padding:'8px 10px', borderRadius:'var(--r-full)', background:o.on?'var(--secondary-container)':'transparent', color:o.on?'var(--on-secondary-container)':'var(--on-surface-variant)', marginBottom:2 }}>
              <span className="material-symbols-rounded" style={{ fontSize:18, color:o.done?'var(--primary)':'inherit' }}>{o.done?'check_circle':'radio_button_unchecked'}</span>
              <span className="body-m" style={{ fontWeight:700 }}>{o.l}</span>
            </div>
          ))}
          <hr className="divider" style={{ margin:'16px 0' }}/>
          <button className="btn btn-magic btn-block" onClick={()=>playAudio('わたしは がくせい です。')}><Icon name="play_arrow" size={18} fill/> Ouvir lição</button>
          <div style={{ display:'flex', gap:8, marginTop:10 }}>
            <button className="chip"><Icon name="subtitles" size={16} className="chip-ic"/> 振 Furigana</button>
          </div>
        </div>

        {/* Center reading column */}
        <div style={{ flex:1, minWidth:0, overflowY:'auto' }}>
          <div style={{ maxWidth:720, margin:'0 auto', padding:'28px 0 40px' }}>
            <div style={{ padding:'0 20px' }}>
              <div className="label-m" style={{ color:'var(--on-surface-variant)', textTransform:'uppercase' }}>{L.course} · {L.topic}</div>
              <div className="headline-l" style={{ color:'var(--on-surface)', marginTop:2 }}>{L.title}</div>
              <div className="title-m" style={{ color:'var(--on-surface-variant)', fontWeight:600 }}>{L.subtitle}</div>
              <div style={{ display:'flex', alignItems:'center', gap:12, marginTop:14 }}>
                <div className="linear-prog thick" style={{ flex:1, maxWidth:320 }}><i style={{ width:`${L.progress*100}%` }}/></div>
                <span className="label-m" style={{ color:'var(--on-surface-variant)' }}>{Math.round(L.progress*100)}% · ~{L.estimated} min</span>
              </div>
            </div>
            <LessonFlow openSheet={setSideSheet} />

            {/* Desktop bottom nav */}
            <div style={{ display:'flex', gap:12, alignItems:'center', margin:'24px 20px 0', padding:'16px', background:'var(--surface-container-low)', borderRadius:'var(--r-lg)' }}>
              <button className="btn btn-outlined" data-tab="course"><Icon name="arrow_back" size={18}/> Anterior</button>
              <span className="body-m" style={{ color:'var(--on-surface-variant)', textAlign:'center', flex:1 }}>Lição {L.index} de {L.total} · {L.topic}</span>
              <button className="btn btn-filled btn-lg" data-tab="course">Concluir e avançar <Icon name="arrow_forward" size={20}/></button>
            </div>
          </div>
        </div>

        {/* Right context rail */}
        <div style={{ width:300, flexShrink:0, borderLeft:'1px solid var(--outline-variant)', padding:'24px 16px', overflowY:'auto' }}>
          <div className="label-m" style={{ color:'var(--on-surface-variant)', marginBottom:8 }}>VOCÊ VAI APRENDER</div>
          <div className="card card-filled" style={{ marginBottom:12, padding:'12px' }}>
            <div className="title-s" style={{ color:'var(--on-surface)', marginBottom:8 }}>4 palavras novas</div>
            {["わたし","がくせい","せんせい","ほん"].map((w,i)=>(
              <div key={i} style={{ display:'flex', justifyContent:'space-between', alignItems:'center', padding:'5px 0', borderTop:i>0?'1px solid var(--outline-variant)':'none' }}>
                <span className="jp" style={{ fontSize:16 }}>{w}</span>
                <button className="icon-btn" style={{ width:32, height:32 }} onClick={()=>playAudio(w)}><Icon name="volume_up" size={18}/></button>
              </div>
            ))}
          </div>
          <div className="card card-filled" style={{ padding:'12px' }}>
            <div className="title-s" style={{ color:'var(--on-surface)', marginBottom:8 }}>2 pontos de gramática</div>
            <div style={{ display:'flex', justifyContent:'space-between', alignItems:'center', padding:'5px 0' }}>
              <span className="jp" style={{ fontSize:16 }}>～は</span><span className="pill pill-magic">NOVO</span>
            </div>
            <div style={{ display:'flex', justifyContent:'space-between', alignItems:'center', padding:'5px 0', borderTop:'1px solid var(--outline-variant)' }}>
              <span className="jp" style={{ fontSize:16 }}>～です</span><span className="pill pill-outline">revisão</span>
            </div>
          </div>
          <div style={{ marginTop:16, display:'flex', flexDirection:'column', alignItems:'center', textAlign:'center', gap:6 }}>
            <Yomineko pose="reading" size={96}/>
            <span className="body-s" style={{ color:'var(--on-surface-variant)' }}>Yomineko está estudando com você.</span>
          </div>
        </div>

        {/* Desktop side sheet (M3) */}
        {sideSheet && (
          <div onClick={(e)=>{ if(e.target.closest('[data-close]')) setSideSheet(null); }} style={{ position:'absolute', top:0, right:0, bottom:0, width:400, background:'var(--surface-container-low)', borderLeft:'1px solid var(--outline-variant)', boxShadow:'var(--elev-2)', display:'flex', flexDirection:'column' }}>
            <div style={{ flex:1, overflowY:'auto', padding:'20px 0 24px' }}>
              {sideSheet==="breakdown" && <BreakdownSheet mode="side"/>}
              {sideSheet==="grammar" && <GrammarSheet mode="side"/>}
              {sideSheet==="kanji" && <KanjiSheet mode="side"/>}
              {sideSheet==="word" && <WordSheet mode="side"/>}
              {sideSheet==="culture" && <CultureSheet mode="side"/>}
            </div>
          </div>
        )}
      </div>
    </DesktopFrame>
  );
};

export { LessonFlow, LessonMobile, LessonDesktop };
