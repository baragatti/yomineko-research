import React from 'react';
import { Icon, PhoneFrame, DesktopFrame, PhoneBody, AppBar, NavBar, NavDrawer } from './m3';
import { Yomineko } from './mascot';
import { FilterButton, FilterSheet, LockedReadingRow } from './yomineko-extras';
import { playAudio } from '../app/audio';
import { StrokeOrder } from '../app/StrokeOrder';

/* ============================================================
   Yomineko — BANKS: Vocabulary + Kanji grid + Kanji detail
   ============================================================ */

const VOCAB = [
  { jp:"わたし", r:"watashi", pt:"eu", pos:"pron.", srs:"mature" },
  { jp:"がくせい", r:"gakusei", pt:"estudante", pos:"subst.", srs:"learning" },
  { jp:"せんせい", r:"sensei", pt:"professor(a)", pos:"subst.", srs:"review" },
  { jp:"ほん", r:"hon", pt:"livro", pos:"subst.", srs:"young" },
  { jp:"がっこう", r:"gakkō", pt:"escola", pos:"subst.", srs:"young" },
  { jp:"ぎんこう", r:"ginkō", pt:"banco", pos:"subst.", srs:"new" },
  { jp:"げんき", r:"genki", pt:"saudável", pos:"adj.", srs:"review" },
  { jp:"これ", r:"kore", pt:"isto", pos:"pron.", srs:"mature" },
];
const KANJI = ["一二三四五六七八九十人学生本日月火水木金".split(""), "気時行見".split("")].flat();
const SRS_COLOR = { new:"var(--outline)", learning:"var(--gold)", young:"var(--magic-1)", review:"var(--primary)", mature:"var(--success)" };
const SRS_LABEL = { new:"novo", learning:"aprendendo", young:"jovem", review:"revisão", mature:"maduro" };

const SrsDot = ({ s, size = 10 }) => (
  <span style={{ width:size, height:size, borderRadius:'50%', background: s==="new"?'transparent':SRS_COLOR[s], border: s==="new"?`2px solid ${SRS_COLOR[s]}`:'none', display:'inline-block', flexShrink:0 }}/>
);

// ---------------- VOCABULARY ----------------
const VocabularyMobile = ({ theme = "light" }) => {
  const [filterOpen, setFilterOpen] = React.useState(false);
  return (
  <PhoneFrame theme={theme} label="Vocabulário — mobile">
    <AppBar title="Vocabulário"/>
    <PhoneBody>
      <div style={{ padding:'4px 16px 8px' }}>
        <div className="field field-filled" style={{ display:'flex', alignItems:'center', gap:10, borderRadius:'var(--r-full)', borderBottom:'none', background:'var(--surface-container-highest)' }}>
          <Icon name="search" size={20} color="var(--on-surface-variant)"/>
          <input placeholder="buscar palavra, leitura, tradução…"/>
        </div>
        <div style={{ display:'flex', gap:8, alignItems:'center', margin:'12px 0 4px' }}>
          <FilterButton label="Estado SRS" count={2} onClick={()=>setFilterOpen(true)}/>
          <span className="body-s" style={{ color:'var(--on-surface-variant)' }}>142 palavras</span>
        </div>
      </div>
      <div>
        {VOCAB.map((w,i)=>(
          <div key={i} className="list-item state" style={{ borderTop: i>0?'1px solid var(--outline-variant)':'none' }}>
            <SrsDot s={w.srs} size={12}/>
            <div className="list-text">
              <div style={{ display:'flex', gap:8, alignItems:'baseline' }}>
                <span className="jp" style={{ fontSize:18, color:'var(--on-surface)' }}>{w.jp}</span>
                <span className="body-s" style={{ color:'var(--on-surface-variant)' }}>{w.r}</span>
              </div>
              <div className="body-m" style={{ color:'var(--on-surface-variant)' }}>{w.pt} · {w.pos}</div>
            </div>
            <button className="icon-btn" onClick={()=>playAudio(w.jp)}><Icon name="volume_up" size={20}/></button>
          </div>
        ))}
      </div>
    </PhoneBody>
    <NavBar active="study" badge={{ review:12 }}/>
    {filterOpen && <FilterSheet title="Filtrar vocabulário" onClose={()=>setFilterOpen(false)} groups={[
      { label:"ESTADO SRS", options:[
        {label:"Novas",dot:"var(--outline)"},{label:"Aprendendo",dot:"#E0A93B",selected:true},
        {label:"Jovens",dot:"#7C4DFF"},{label:"Em revisão",dot:"#6750A4",selected:true},{label:"Maduras",dot:"#3C6E47"}] },
      { label:"TIPO", options:[{label:"Substantivos"},{label:"Verbos"},{label:"Adjetivos"},{label:"Pronomes"}] },
    ]}/>}
  </PhoneFrame>
  );
};

const VocabularyDesktop = ({ theme = "light" }) => (
  <DesktopFrame theme={theme} label="Vocabulário — desktop" url="app.yomineko.com/vocabulario">
    <NavDrawer active="vocab" badge={{ review:12 }} drawer={true}/>
    <div style={{ flex:1, overflowY:'auto', padding:'28px 32px' }}>
      <div className="headline-l" style={{ color:'var(--on-surface)', marginBottom:4 }}>Vocabulário</div>
      <div className="body-m" style={{ color:'var(--on-surface-variant)', marginBottom:18 }}>142 palavras · cresce automaticamente das lições concluídas.</div>
      <div style={{ display:'grid', gridTemplateColumns:'200px minmax(0, 1fr) 300px', gap:20, alignItems:'flex-start' }}>
        <div>
          <div className="label-m" style={{ color:'var(--on-surface-variant)', marginBottom:8 }}>ESTADO SRS</div>
          <div className="card card-filled" style={{ padding:'8px' }}>
            {[["Todas",142,null],["Novas",8,"new"],["Aprendendo",12,"learning"],["Jovens",22,"young"],["Em revisão",64,"review"],["Maduras",36,"mature"]].map(([l,n,s],i)=>(
              <div key={i} style={{ display:'flex', alignItems:'center', gap:8, padding:'8px 10px', borderRadius:'var(--r-sm)', background:i===0?'var(--secondary-container)':'transparent' }}>
                {s ? <SrsDot s={s}/> : <span style={{ width:10 }}/>}
                <span className="body-m" style={{ flex:1, color:'var(--on-surface)' }}>{l}</span>
                <span className="label-m" style={{ color:'var(--on-surface-variant)' }}>{n}</span>
              </div>
            ))}
          </div>
        </div>
        <div>
          <div className="field field-outlined" style={{ display:'flex', alignItems:'center', gap:10, borderRadius:'var(--r-full)', marginBottom:14 }}>
            <Icon name="search" size={20} color="var(--on-surface-variant)"/><input placeholder="buscar…"/>
          </div>
          <table style={{ width:'100%', borderCollapse:'collapse', tableLayout:'fixed' }}>
            <thead><tr style={{ textAlign:'left' }}>
              {["","Palavra","Leitura","Tradução","Tipo","Revisão"].map((h,i)=>(<th key={i} style={{ padding:'8px', fontFamily:'var(--font-body)', fontWeight:700, fontSize:11, letterSpacing:'0.06em', textTransform:'uppercase', color:'var(--on-surface-variant)', borderBottom:'1px solid var(--outline-variant)', width: i===0?28:(i===1?64:'auto') }}>{h}</th>))}
            </tr></thead>
            <tbody>
              {VOCAB.map((w,i)=>(
                <tr key={i} style={{ borderBottom:'1px solid var(--outline-variant)', background:i===2?'var(--secondary-container)':'transparent' }}>
                  <td style={{ padding:'10px 8px' }}><SrsDot s={w.srs} size={12}/></td>
                  <td style={{ padding:'10px 8px' }}><span className="jp" style={{ fontSize:18 }}>{w.jp}</span></td>
                  <td style={{ padding:'10px 8px' }}><span className="body-m" style={{ color:'var(--on-surface-variant)' }}>{w.r}</span></td>
                  <td style={{ padding:'10px 8px' }}><span className="body-m" style={{ color:'var(--on-surface)' }}>{w.pt}</span></td>
                  <td style={{ padding:'10px 8px' }}><span className="body-s" style={{ color:'var(--on-surface-variant)' }}>{w.pos}</span></td>
                  <td style={{ padding:'10px 8px' }}><span className="body-s" style={{ color:'var(--on-surface-variant)' }}>{w.srs==="new"?"hoje":w.srs==="learning"?"em 4h":w.srs==="review"?"em 9 dias":"em 4 meses"}</span></td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <div>
          <div className="label-m" style={{ color:'var(--on-surface-variant)', marginBottom:8 }}>SELECIONADA</div>
          <div className="card card-elevated">
            <span className="pill pill-outline">SUBSTANTIVO</span>
            <div className="jp-serif" style={{ fontSize:38, color:'var(--on-surface)', marginTop:6 }}>せんせい</div>
            <div className="body-m" style={{ color:'var(--on-surface-variant)' }}>sensei</div>
            <div className="headline-s" style={{ color:'var(--primary)', margin:'8px 0' }}>professor(a)</div>
            <div style={{ display:'flex', gap:8 }}>
              <button className="btn btn-tonal btn-sm" onClick={()=>playAudio('せんせい')}><Icon name="volume_up" size={18}/> Ouvir</button>
              <button className="btn btn-outlined btn-sm" data-go="kanjiDetail"><Icon name="open_in_full" size={16}/> Detalhes</button>
            </div>
            <hr className="divider" style={{ margin:'14px 0' }}/>
            <div className="label-m" style={{ color:'var(--on-surface-variant)', marginBottom:6 }}>EXEMPLO</div>
            <div className="jp" style={{ fontSize:15 }}>たなかさんは <b style={{ color:'var(--primary)' }}>せんせい</b> です。</div>
            <div className="body-s" style={{ color:'var(--on-surface-variant)' }}>O Sr. Tanaka é professor.</div>
          </div>
        </div>
      </div>
    </div>
  </DesktopFrame>
);

// ---------------- KANJI GRID ----------------
const kanjiSrs = (i) => ["mature","mature","review","review","young","young","young","new","new","new","review","learning","learning","young","young","young","new","new","new","new","new","new","new","new"][i] || "new";

const KanjiGridMobile = ({ theme = "light", filterOpen: filterOpenProp }) => {
  const [filterOpen, setFilterOpen] = React.useState(!!filterOpenProp);
  return (
  <PhoneFrame theme={theme} label={filterOpen?"Kanji — filtro":"Kanji — grade mobile"}>
    <AppBar title="Kanji"/>
    <PhoneBody>
      <div style={{ padding:'4px 16px 8px' }}>
        <div className="field field-filled" style={{ display:'flex', alignItems:'center', gap:10, borderRadius:'var(--r-full)', borderBottom:'none', background:'var(--surface-container-highest)' }}>
          <Icon name="search" size={20} color="var(--on-surface-variant)"/>
          <input placeholder="buscar por romaji: gaku, mizu, hi…"/>
        </div>
        {/* level segmentation */}
        <div className="segmented" style={{ width:'100%', marginTop:12 }}>
          <button className="seg selected" style={{ flex:1, justifyContent:'center' }}>Todos · 27</button>
          <button className="seg" style={{ flex:1, justifyContent:'center' }}>N5 · 27</button>
          <button className="seg" style={{ flex:1, justifyContent:'center', opacity:0.6 }}><Icon name="lock" size={14}/> N4</button>
        </div>
        <div style={{ display:'flex', alignItems:'center', gap:8, marginTop:10 }}>
          <FilterButton label="Estado SRS" onClick={()=>setFilterOpen(true)}/>
          <span className="body-s" style={{ color:'var(--on-surface-variant)' }}>18 aprendidos · 9 a desbloquear</span>
        </div>
      </div>
      <div style={{ padding:'0 16px', display:'grid', gridTemplateColumns:'repeat(5,1fr)', gap:8 }}>
        {KANJI.slice(0,20).map((k,i)=>(
          <div key={i} data-go="kanjiDetail" className="card card-elevated state" style={{ aspectRatio:'1', display:'flex', flexDirection:'column', alignItems:'center', justifyContent:'center', cursor:'pointer', padding:0, gap:4 }}>
            <span className="jp-serif" style={{ fontSize:30, color:'var(--on-surface)' }}>{k}</span>
            <SrsDot s={kanjiSrs(i)} size={8}/>
          </div>
        ))}
        {Array.from({length:5}).map((_,i)=>(
          <div key={`l${i}`} className="card card-filled" style={{ aspectRatio:'1', display:'flex', alignItems:'center', justifyContent:'center', opacity:0.4 }}>
            <Icon name="lock" size={20} color="var(--outline)"/>
          </div>
        ))}
      </div>
      <div style={{ textAlign:'center', padding:'14px', color:'var(--on-surface-variant)' }} className="body-s">18 de 100 do N5 · cinza = ainda não estudado</div>
    </PhoneBody>
    <NavBar active="study" badge={{ review:12 }}/>
    {filterOpen && <FilterSheet title="Filtrar kanji" onClose={()=>setFilterOpen(false)} groups={[
      { label:"NÍVEL JLPT", options:[{label:"Todos",selected:true},{label:"N5"},{label:"N4 (bloqueado)"}] },
      { label:"ESTADO SRS", options:[
        {label:"Novo",dot:"var(--outline)"},{label:"Aprendendo",dot:"#E0A93B",selected:true},
        {label:"Jovem",dot:"#7C4DFF"},{label:"Revisão",dot:"#6750A4"},{label:"Maduro",dot:"#3C6E47"}] },
      { label:"ORDENAR", options:[{label:"Frequência",selected:true},{label:"Traços"},{label:"Recentes"}] },
    ]}/>}
  </PhoneFrame>
  );
};

// ---------------- KANJI PAGE (full, complete) ----------------
const KanjiDetailMobile = ({ theme = "light" }) => (
  <PhoneFrame theme={theme} label="Kanji — página completa">
    <AppBar title="学" leading={<button className="icon-btn" data-tab="kanji"><Icon name="arrow_back" size={24}/></button>} actions={<button className="icon-btn"><Icon name="bookmark" size={22} fill/></button>}/>
    <PhoneBody>
      {/* hero */}
      <div style={{ textAlign:'center', padding:'8px 16px 16px', position:'relative' }}>
        <div style={{ position:'absolute', inset:'0 0 auto 0', height:160, background:'radial-gradient(60% 100% at 50% 0%, color-mix(in srgb, var(--magic-1) 12%, transparent), transparent)' }}/>
        <div style={{ position:'relative' }}>
          <div className="jp-serif" style={{ fontSize:120, lineHeight:1.1, color:'var(--on-surface)' }}>学</div>
          <div className="headline-s" style={{ color:'var(--on-surface)' }}>estudo, aprender</div>
          <div style={{ display:'flex', gap:6, justifyContent:'center', flexWrap:'wrap', marginTop:10 }}>
            <span className="pill pill-primary">N5</span><span className="pill pill-outline">8 traços</span>
            <span className="pill pill-outline">freq. #88</span><span className="pill pill-success"><Icon name="style" size={14}/> revisão em 1 dia</span>
          </div>
        </div>
      </div>

      <div style={{ padding:'0 16px 16px', display:'flex', flexDirection:'column', gap:12 }}>
        {/* primary actions */}
        <div style={{ display:'flex', gap:8 }}>
          <button className="btn btn-tonal" style={{ flex:1 }}><Icon name="animation" size={18}/> Ver traços</button>
          <button className="icon-btn icon-btn-tonal" onClick={()=>playAudio('がく')}><Icon name="volume_up" size={20}/></button>
        </div>

        {/* readings (with level gating) */}
        <div className="card card-filled">
          <div className="label-m" style={{ color:'var(--on-surface-variant)', marginBottom:10 }}>LEITURAS</div>
          <div style={{ display:'grid', gridTemplateColumns:'1fr 1fr', gap:12, marginBottom:10 }}>
            <div className="card card-outlined" style={{ padding:'10px 12px' }}>
              <div className="label-m" style={{ color:'var(--primary)' }}>音 ON-YOMI</div>
              <div className="jp" style={{ fontSize:20 }}>ガク</div>
              <div className="body-s" style={{ color:'var(--on-surface-variant)' }}>gaku</div>
            </div>
            <div className="card card-outlined" style={{ padding:'10px 12px' }}>
              <div className="label-m" style={{ color:'var(--primary)' }}>訓 KUN-YOMI</div>
              <div className="jp" style={{ fontSize:20 }}>まな(ぶ)</div>
              <div className="body-s" style={{ color:'var(--on-surface-variant)' }}>mana(bu)</div>
            </div>
          </div>
          <LockedReadingRow kind="rara" level="N4"/>
          <div className="body-s" style={{ color:'var(--on-surface-variant)', marginTop:8, display:'flex', gap:6, alignItems:'center' }}>
            <Icon name="info" size={16}/> Mostramos só leituras do seu nível. Mude em Perfil › Nível de conteúdo.
          </div>
        </div>

        {/* stroke order practice (real KanjiVG animation) */}
        <StrokeOrder char="学" />

        {/* mnemonic */}
        <div className="card" style={{ background:'color-mix(in srgb, var(--magic-1) 8%, var(--surface))', border:'1px solid color-mix(in srgb, var(--magic-1) 25%, transparent)' }}>
          <div style={{ display:'flex', gap:12, alignItems:'flex-start' }}>
            <Yomineko pose="reading" size={56} glow={false}/>
            <div>
              <div className="label-m" style={{ color:'var(--magic-1)', marginBottom:2 }}>MNEMÔNICA DO YOMINEKO</div>
              <div className="body-m" style={{ color:'var(--on-surface)' }}>Uma <b>criança</b> (子) sob uma <b>coroa</b> de conhecimento (⺍) — quem estuda usa a coroa do saber.</div>
            </div>
          </div>
        </div>

        {/* example words */}
        <div className="card card-filled">
          <div className="label-m" style={{ color:'var(--on-surface-variant)', marginBottom:6 }}>APARECE EM (palavras aprendidas)</div>
          {[{jp:"学生",r:"がくせい",pt:"estudante"},{jp:"学校",r:"がっこう",pt:"escola"},{jp:"大学",r:"だいがく",pt:"universidade"},{jp:"学ぶ",r:"まなぶ",pt:"aprender"}].map((x,i)=>(
            <div key={i} className="list-item" style={{ padding:'8px 0', minHeight:0, borderTop:i>0?'1px solid var(--outline-variant)':'none' }}>
              <div className="list-text"><span className="jp" style={{ fontSize:16 }}>{x.jp}</span> <span className="body-s" style={{ color:'var(--on-surface-variant)' }}>{x.r}</span></div>
              <span className="body-m" style={{ color:'var(--on-surface-variant)' }}>{x.pt}</span>
              <button className="icon-btn" style={{ width:32, height:32 }} onClick={()=>playAudio(x.jp)}><Icon name="volume_up" size={18}/></button>
            </div>
          ))}
        </div>
      </div>
    </PhoneBody>
  </PhoneFrame>
);

const KanjiGridDesktop = ({ theme = "light" }) => {
  const srsOf = (i) => ["mature","mature","review","review","young","young","young","new","new","new","review","learning","learning","young","young","young","new","new","new","new","new","new","new","new"][i] || "new";
  const [filterOpen, setFilterOpen] = React.useState(false);
  return (
    <DesktopFrame theme={theme} label="Kanji — desktop" url="app.yomineko.com/kanji">
      <NavDrawer active="kanji" badge={{ review:12 }} drawer={true}/>
      <div style={{ flex:1, overflowY:'auto', padding:'28px 32px' }}>
        <div className="headline-l" style={{ color:'var(--on-surface)', marginBottom:4 }}>Kanji</div>
        <div className="body-m" style={{ color:'var(--on-surface-variant)', marginBottom:18 }}>27 de 100 do N5 · busca por romaji, separado por nível.</div>
        <div style={{ display:'grid', gridTemplateColumns:'1fr 340px', gap:24, alignItems:'flex-start' }}>
          <div>
            <div style={{ display:'flex', gap:12, marginBottom:14, alignItems:'center' }}>
              <div className="field field-outlined" style={{ display:'flex', alignItems:'center', gap:10, borderRadius:'var(--r-full)', flex:1 }}>
                <Icon name="search" size={20} color="var(--on-surface-variant)"/><input placeholder="buscar por romaji: gaku, mizu, hi…"/>
              </div>
              <div className="segmented">
                <button className="seg selected">Todos · 27</button>
                <button className="seg">N5</button>
                <button className="seg" style={{ opacity:0.6 }}><Icon name="lock" size={14}/> N4</button>
              </div>
              <FilterButton label="SRS" onClick={()=>setFilterOpen(true)}/>
            </div>
            <div style={{ display:'grid', gridTemplateColumns:'repeat(auto-fill, minmax(72px,1fr))', gap:10 }}>
              {KANJI.map((k,i)=>(
                <div key={i} data-go="kanjiDetail" className={`card ${i===11?'card-elevated':'card-filled'} state`} style={{ aspectRatio:'1', display:'flex', flexDirection:'column', alignItems:'center', justifyContent:'center', cursor:'pointer', gap:4, border: i===11?'2px solid var(--primary)':'none' }}>
                  <span className="jp-serif" style={{ fontSize:32, color:'var(--on-surface)' }}>{k}</span>
                  <SrsDot s={srsOf(i)} size={8}/>
                </div>
              ))}
            </div>
          </div>
          <div>
            <div className="label-m" style={{ color:'var(--on-surface-variant)', marginBottom:8 }}>学 — selecionado</div>
            <div className="card card-elevated" style={{ textAlign:'center' }}>
              <div className="jp-serif" style={{ fontSize:96, lineHeight:1, color:'var(--on-surface)' }}>学</div>
              <div className="title-l" style={{ color:'var(--on-surface)', marginTop:4 }}>estudo, aprender</div>
              <div className="body-m" style={{ color:'var(--on-surface-variant)' }}>ガク · まな(ぶ)</div>
              <div style={{ display:'flex', gap:8, justifyContent:'center', marginTop:12 }}>
                <button className="btn btn-tonal btn-sm" style={{ flex:1 }}><Icon name="animation" size={18}/> Ver traços</button>
              </div>
              <button className="btn btn-filled btn-block" style={{ marginTop:8 }} data-page="kanjiDetail">Página completa <Icon name="open_in_full" size={16}/></button>
              <hr className="divider" style={{ margin:'14px 0' }}/>
              <div style={{ display:'grid', gridTemplateColumns:'repeat(4,1fr)', gap:6 }}>
                {[1,2,3,4,5,6,7,8].map(n=>(
                  <div key={n} style={{ aspectRatio:'1', borderRadius:'var(--r-sm)', background:'var(--surface-container-highest)', display:'flex', alignItems:'center', justifyContent:'center' }}>
                    <span className="jp-serif" style={{ fontSize:22, opacity:0.25+n*0.09 }}>学</span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      </div>
    {filterOpen && <FilterSheet centered title="Filtrar kanji" onClose={()=>setFilterOpen(false)} groups={[
      { label:"NÍVEL JLPT", options:[{label:"Todos",selected:true},{label:"N5"},{label:"N4 (bloqueado)"}] },
      { label:"ESTADO SRS", options:[{label:"Novo",dot:"var(--outline)"},{label:"Aprendendo",dot:"#E0A93B",selected:true},{label:"Jovem",dot:"#7C4DFF"},{label:"Revisão",dot:"#6750A4"},{label:"Maduro",dot:"#3C6E47"}] },
    ]}/>}
    </DesktopFrame>
  );
};

// ---------------- KANJI TRAINING (focused drill for one kanji) ----------------
const KanjiTraining = ({ theme = "light", q = "meaning" }) => {
  const prompts = {
    meaning: { label:"SIGNIFICADO", big:<div className="jp-serif" style={{ fontSize:96, color:'var(--on-surface)' }}>学</div>, ask:"Qual o significado?", opts:["estudo","montanha","água","pessoa"], ans:0 },
    reading: { label:"LEITURA (ON)", big:<div className="jp-serif" style={{ fontSize:96, color:'var(--on-surface)' }}>学</div>, ask:"Como se lê (on-yomi)?", opts:["ガク","セイ","スイ","ジン"], ans:0 },
    recall:  { label:"RECONHECER", big:<div className="headline-m" style={{ color:'var(--on-surface)' }}>estudo, aprender</div>, ask:"Qual kanji?", opts:["生","学","本","字"], ans:1, jp:true },
  }[q];
  return (
    <PhoneFrame theme={theme} label={`Treinar kanji · ${q==="meaning"?"significado":q==="reading"?"leitura":"reconhecer"}`}>
      <SessTop done={q==="meaning"?1:q==="reading"?2:3} total={6}/>
      <div style={{ flexShrink:0, textAlign:'center', padding:'2px 0 6px' }}>
        <span className="pill pill-magic"><Icon name="fitness_center" size={14}/> TREINANDO 学</span>
      </div>
      <PhoneBody style={{ display:'flex', flexDirection:'column' }}>
        <div style={{ flex:1, display:'flex', flexDirection:'column', alignItems:'center', justifyContent:'center', padding:'0 20px', textAlign:'center' }}>
          <span className="label-m" style={{ color:'var(--on-surface-variant)' }}>{prompts.label}</span>
          <div style={{ margin:'14px 0 8px' }}>{prompts.big}</div>
          <div className="title-m" style={{ color:'var(--on-surface)' }}>{prompts.ask}</div>
        </div>
        <div style={{ padding:'0 16px 16px', display:'grid', gridTemplateColumns:'1fr 1fr', gap:10 }}>
          {prompts.opts.map((o,i)=>(
            <button key={i} className="card card-outlined state" style={{ padding:'16px 0', textAlign:'center', cursor:'pointer', fontFamily: prompts.jp?'var(--font-jp-serif)':'var(--font-body)', fontWeight:700, fontSize: prompts.jp?28:(o.length>3?16:20), color:'var(--on-surface)', border: i===prompts.ans?'2px solid var(--success)':'1px solid var(--outline-variant)' }}>{o}</button>
          ))}
        </div>
      </PhoneBody>
    </PhoneFrame>
  );
};

export {
  VocabularyMobile, VocabularyDesktop, KanjiGridMobile, KanjiGridDesktop, KanjiDetailMobile, KanjiTraining
};
