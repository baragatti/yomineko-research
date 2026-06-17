import React from 'react';
import { StarField, Yomineko, YominekoLogo } from './mascot';
import { LandingDesktop, LandingMobile, LoginMobile, LoginDesktop } from './yomineko-public';
import { DashboardMobile, DashboardDesktop, ProfileMobile, ProfileDesktop } from './yomineko-home';
import { CourseSelectMobile, CourseSelectDesktop, CourseTreeMobile, CourseTreeDesktop } from './yomineko-course';
import { LessonMobile, LessonDesktop } from './yomineko-lesson';
import { ReviewEmptyMobile, ReviewFrontMobile, ReviewBackMobile, ReviewDoneMobile, ReviewDesktop } from './yomineko-review';
import {
  PracticeHubMobile, PracticeHubDesktop,
  HiraganaSession, KatakanaSession, ParticleSession, SentenceBuildSession, ConjugationSession, NumbersSession,
  HiraganaConfig, ParticleConfig, ConjugationConfig, NumbersConfig
} from './yomineko-practice';
import { VocabularyMobile, VocabularyDesktop, KanjiGridMobile, KanjiGridDesktop, KanjiDetailMobile, KanjiTraining } from './yomineko-banks';

/* ============================================================
   Yomineko — design gallery shell
   Pages grouped; each page shows its mobile + desktop versions
   together. Collapsible "Sobre esta tela" notes.
   ============================================================ */

const { useState } = React;

// ---- Collapsible notes panel ----
const NotesPanel = ({ notes }) => {
  const [open, setOpen] = useState(false);
  if (!notes) return null;
  return (
    <div style={{ maxWidth:920, margin:'0 0 24px' }}>
      <button onClick={()=>setOpen(o=>!o)} style={{
        display:'inline-flex', alignItems:'center', gap:8, border:'1px solid #d9cfe9', background:'#fff',
        borderRadius:999, padding:'7px 16px', cursor:'pointer', fontFamily:'"Nunito",sans-serif', fontWeight:700, fontSize:13, color:'#5b4b7c'
      }}>
        <span className="material-symbols-rounded" style={{ fontSize:18 }}>{open?'expand_less':'menu_book'}</span>
        Sobre esta tela
        <span className="material-symbols-rounded" style={{ fontSize:18 }}>{open?'':'expand_more'}</span>
      </button>
      {open && (
        <div style={{ marginTop:12, background:'#fff', border:'1px solid #e7def4', borderRadius:16, padding:'18px 20px', boxShadow:'0 4px 16px rgba(80,50,130,0.06)' }}>
          <p style={{ fontFamily:'"Nunito",sans-serif', fontSize:14.5, lineHeight:1.6, color:'#3a3147', margin:'0 0 12px' }}>{notes.purpose}</p>
          <div style={{ display:'grid', gridTemplateColumns:'repeat(auto-fit, minmax(220px,1fr))', gap:'12px 22px' }}>
            {notes.interactions && (
              <div>
                <div style={{ fontFamily:'"Nunito",sans-serif', fontSize:10.5, fontWeight:800, letterSpacing:'0.1em', textTransform:'uppercase', color:'#9384ad', marginBottom:4 }}>Interações</div>
                <ul style={{ margin:0, paddingLeft:16, fontFamily:'"Nunito",sans-serif', fontSize:12.5, color:'#4a4159', lineHeight:1.6 }}>
                  {notes.interactions.map((it,i)=><li key={i}>{it}</li>)}
                </ul>
              </div>
            )}
            {notes.decluttered && (
              <div>
                <div style={{ fontFamily:'"Nunito",sans-serif', fontSize:10.5, fontWeight:800, letterSpacing:'0.1em', textTransform:'uppercase', color:'#9384ad', marginBottom:4 }}>Movido para toque</div>
                <ul style={{ margin:0, paddingLeft:16, fontFamily:'"Nunito",sans-serif', fontSize:12.5, color:'#4a4159', lineHeight:1.6 }}>
                  {notes.decluttered.map((it,i)=><li key={i}>{it}</li>)}
                </ul>
              </div>
            )}
            {notes.tags && (
              <div>
                <div style={{ fontFamily:'"Nunito",sans-serif', fontSize:10.5, fontWeight:800, letterSpacing:'0.1em', textTransform:'uppercase', color:'#9384ad', marginBottom:4 }}>Variantes</div>
                <div>{notes.tags.map((t,i)=><span key={i} style={{ display:'inline-block', fontFamily:'"Nunito",sans-serif', fontSize:11.5, fontWeight:700, background:'#f1ebfa', color:'#6b5b8a', borderRadius:999, padding:'2px 10px', margin:'0 4px 4px 0' }}>{t}</span>)}</div>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};

// ---- Row of frames with a sub-heading ----
const FrameGroup = ({ title, children }) => (
  <div style={{ marginBottom:8 }}>
    {title && <div style={{ fontFamily:'"Poppins",sans-serif', fontWeight:600, fontSize:15, color:'#6b5b8a', margin:'18px 0 14px', display:'flex', alignItems:'center', gap:8 }}>
      <span className="material-symbols-rounded" style={{ fontSize:18 }}>auto_awesome</span>{title}
    </div>}
    <div style={{ display:'flex', flexWrap:'wrap', gap:40, alignItems:'flex-start' }}>{children}</div>
  </div>
);

// =========================================================
// PAGE REGISTRY — each page shows mobile + desktop together
// =========================================================
const PAGES = [
  { group:"Visão geral", id:"intro", title:"Direção de design", render:()=> <IntroPage/> },
  { group:"Visão geral", id:"changelog", title:"Sobre o protótipo", render:()=> <AboutProto/> },

  // ---- Público ----
  { group:"Público", id:"landing", title:"Landing", tagline:"Página pública. Yomineko em destaque, CTA único: começar.",
    notes:{ purpose:"Vitrine pública do produto. O gato mágico ancora a marca; um só caminho de ação.", tags:["Desktop claro","Mobile claro","Mobile escuro"] },
    render:()=>(<><FrameGroup><LandingMobile theme="light"/><LandingMobile theme="dark"/></FrameGroup><FrameGroup title="Desktop"><LandingDesktop theme="light"/></FrameGroup></>) },
  { group:"Público", id:"login", title:"Login", tagline:"Entrada por e-mail e senha. Sem cadastro automático no MVP.",
    notes:{ purpose:"Autenticação simples. Painel de marca com o mascote no desktop; estado de erro no mobile.", tags:["Mobile claro","Mobile erro","Desktop"] },
    render:()=>(<><FrameGroup><LoginMobile theme="light"/><LoginMobile theme="light" error/><LoginMobile theme="dark"/></FrameGroup><FrameGroup title="Desktop"><LoginDesktop theme="light"/></FrameGroup></>) },

  // ---- Início ----
  { group:"Início", id:"dashboard", title:"Dashboard", tagline:"A âncora diária: o que revisar e a próxima lição, acima da dobra.",
    notes:{ purpose:"Tela inicial. Continuar lição + revisão dominam; práticas e estatísticas abaixo. Yomineko aparece no empty state e como dica no desktop.", interactions:["„Continuar lição' abre o reprodutor.","„Iniciar revisão' abre a sessão SRS.","Cartões de prática levam a cada modo."], tags:["Mobile claro","Mobile escuro","Tudo em dia","Desktop"] },
    render:()=>(<><FrameGroup><DashboardMobile theme="light"/><DashboardMobile theme="dark"/><DashboardMobile theme="light" variant="empty"/></FrameGroup><FrameGroup title="Desktop"><DashboardDesktop theme="light"/></FrameGroup></>) },
  { group:"Início", id:"profile", title:"Perfil & Configurações", tagline:"Meta de estudo por minutos, leitura, aparência e progresso.",
    notes:{ purpose:"Configurações globais + estatísticas. A meta diária agora é em minutos (10/20/30/45).", tags:["Mobile claro","Mobile escuro","Desktop"] },
    render:()=>(<><FrameGroup><ProfileMobile theme="light"/><ProfileMobile theme="dark"/></FrameGroup><FrameGroup title="Desktop"><ProfileDesktop theme="light"/></FrameGroup></>) },

  // ---- Estudo ----
  { group:"Estudo", id:"course-select", title:"Trocar de curso", tagline:"Escolha o curso ativo (N5 → N1). Progresso preservado.",
    notes:{ purpose:"Seleção de curso. Um ativo por vez; trocar não apaga nada.", tags:["Mobile","Desktop"] },
    render:()=>(<><FrameGroup><CourseSelectMobile theme="light"/><CourseSelectMobile theme="dark"/></FrameGroup><FrameGroup title="Desktop"><CourseSelectDesktop theme="light"/></FrameGroup></>) },
  { group:"Estudo", id:"course-tree", title:"Árvore do curso", tagline:"Só o curso ativo. Tópicos em cards full-width, lições dentro. Filtros em modal.",
    notes:{ purpose:"Mapa do curso ativo. Cards de tópico full-width (1 por linha também no desktop). O filtro virou um botão que abre um modal de opções.", interactions:["Botão de filtro abre o modal (estado, ordenação).","Toque na lição abre o reprodutor."], tags:["Mobile","Filtro (modal)","Desktop full-width"] },
    render:()=>(<><FrameGroup><CourseTreeMobile theme="light"/><CourseTreeMobile theme="light" filterOpen/><CourseTreeMobile theme="dark"/></FrameGroup><FrameGroup title="Desktop (cards full-width)"><CourseTreeDesktop theme="light"/></FrameGroup></>) },
  { group:"Estudo", id:"lesson", title:"Lição", tagline:"O reprodutor de lição, limpo. Conteúdo secundário abre ao toque.",
    notes:{
      purpose:"O reprodutor de lição em Material 3. O fluxo principal fica enxuto; análise de frase, kanji, gramática e cultura abrem em folhas só ao toque (bottom sheet no mobile, painel lateral no desktop).",
      interactions:["Ícone ⤳ no exemplo abre a Análise da frase.","Tocar palavra/kanji abre a folha respectiva.","„Ponto de gramática' e „Nota cultural' são linhas que abrem folhas.","Rodapé: Anterior + Concluir e avançar."],
      decluttered:["Análise da frase","Leitura/detalhes de kanji","Notas de gramática","Notas culturais","Detalhe da palavra"],
      tags:["Mobile claro","Mobile escuro","Desktop","5 folhas de toque"]
    },
    render:()=>(<>
      <FrameGroup><LessonMobile theme="light"/><LessonMobile theme="dark"/></FrameGroup>
      <FrameGroup title="Desktop (3 colunas: índice · leitura · contexto)"><LessonDesktop theme="light"/></FrameGroup>
      <FrameGroup title="Folhas que abrem ao toque (mobile)">
        <LessonMobile theme="light" sheet="breakdown"/><LessonMobile theme="light" sheet="word"/>
        <LessonMobile theme="light" sheet="kanji"/><LessonMobile theme="light" sheet="grammar"/><LessonMobile theme="light" sheet="culture"/>
      </FrameGroup>
      <FrameGroup title="Folha como painel lateral (desktop)">
        <LessonDesktop theme="light" sideSheet="breakdown"/><LessonDesktop theme="light" sideSheet="kanji"/>
      </FrameGroup>
    </>) },

  // ---- Revisão ----
  { group:"Revisão (SRS)", id:"review", title:"Revisão", tagline:"Estilo Anki + FSRS-6: a resposta só aparece quando você revela.",
    notes:{ purpose:"Revisão espaçada (FSRS-6). A frente esconde a resposta — é preciso revelar (botão ou Espaço), como no Anki. Só então aparecem De novo/Difícil/Bom/Fácil com os intervalos do FSRS-6.", interactions:["„Mostrar resposta' ou tecla Espaço revela o verso.","1–4 avaliam e agendam o próximo.","P pausa, Esc sai."], tags:["Sem cartões","Frente","Verso","Concluída","Desktop frente+verso"] },
    render:()=>(<>
      <FrameGroup title="Estados (mobile)"><ReviewEmptyMobile theme="light"/><ReviewFrontMobile theme="light"/><ReviewBackMobile theme="light"/><ReviewDoneMobile theme="light"/></FrameGroup>
      <FrameGroup title="Desktop — frente (esconde) → revelar → verso"><ReviewDesktop theme="light" revealed={false}/><ReviewDesktop theme="light" revealed={true}/></FrameGroup>
    </>) },

  // ---- Práticas ----
  { group:"Práticas", id:"practice-hub", title:"Prática — Hub", tagline:"Seis modos focados. Você escolhe o que treinar.",
    notes:{ purpose:"Entrada para os seis drills. Cada um se nutre do que você já aprendeu.", tags:["Mobile","Desktop"] },
    render:()=>(<><FrameGroup><PracticeHubMobile theme="light"/><PracticeHubMobile theme="dark"/></FrameGroup><FrameGroup title="Desktop"><PracticeHubDesktop theme="light"/></FrameGroup></>) },
  { group:"Práticas", id:"practice-config", title:"Prática — Configuração", tagline:"Cada modo tem sua tela de configuração (pool, duração, modo de resposta).",
    notes:{ purpose:"Antes da sessão, cada prática abre uma configuração própria (conforme o guia): famílias de kana, formas verbais, pool por nível, modo cartões/digitar.", interactions:["Hiragana: famílias, duração, cartões vs digitar + auto-confirmar.","Partículas: pool (aprendidas/todas/por nível).","Conjugação: formas (te/ta/nai…) + pool.","Números: alcance + modo."], tags:["Hiragana","Partículas","Conjugação","Números"] },
    render:()=>(<FrameGroup><HiraganaConfig theme="light"/><ParticleConfig theme="light"/><ConjugationConfig theme="light"/><NumbersConfig theme="light"/></FrameGroup>) },
  { group:"Práticas", id:"practice-sessions", title:"Prática — Sessões", tagline:"Um exemplo por modo, com e sem teclado.",
    notes:{ purpose:"Sessões em ação, uma por modo de prática. Onde o modo permite digitar, mostro a versão com teclado na tela (com) e a versão de cartões/blocos (sem). Feedback instantâneo, áudio após responder.", interactions:["Hiragana e Números: cartões (sem teclado) e digitar (com teclado).","Partículas e Construção de frases: toque em chips/blocos (sem teclado).","Conjugação: 4 cartões (sem teclado — evita IME)."], tags:["Hiragana ×2","Katakana","Partículas","Construir","Conjugação","Números ×2"] },
    render:()=>(<>
      <FrameGroup title="Hiragana — sem teclado (cartões): pergunta · acerto · erro">
        <HiraganaSession theme="light" input="cards" state="fresh"/><HiraganaSession theme="light" input="cards" state="correct"/><HiraganaSession theme="light" input="cards" state="wrong"/>
      </FrameGroup>
      <FrameGroup title="Hiragana — com teclado (digitar) · Katakana (cartões)">
        <HiraganaSession theme="light" input="typing" state="fresh"/><KatakanaSession theme="light"/>
      </FrameGroup>
      <FrameGroup title="Partículas · Construir frases · Conjugação (sem teclado)">
        <ParticleSession theme="light"/><SentenceBuildSession theme="light"/><ConjugationSession theme="light"/>
      </FrameGroup>
      <FrameGroup title="Números — sem teclado (cartões) · com teclado (numérico)">
        <NumbersSession theme="light" input="cards"/><NumbersSession theme="light" input="typing"/>
      </FrameGroup>
    </>) },

  // ---- Bancos ----
  { group:"Bancos", id:"vocabulary", title:"Vocabulário", tagline:"Banco de palavras com busca, filtros SRS e detalhe.",
    notes:{ purpose:"Cresce automaticamente das lições. Lista no mobile; tabela + filtros + detalhe no desktop.", tags:["Mobile","Desktop"] },
    render:()=>(<><FrameGroup><VocabularyMobile theme="light"/><VocabularyMobile theme="dark"/></FrameGroup><FrameGroup title="Desktop"><VocabularyDesktop theme="light"/></FrameGroup></>) },
  { group:"Bancos", id:"kanji", title:"Kanji", tagline:"Busca por romaji, separado por N5/N4/Todos, e a página completa com treino.",
    notes:{ purpose:"Grade com busca por romaji e segmentação por nível (Todos/N5/N4). A página completa do kanji traz leituras (com gating de nível), ordem de traços, mnemônica do Yomineko, treino de reconhecimento e palavras. Conteúdo além do nível liberado aparece bloqueado (ajustável em Perfil).", interactions:["Busca aceita romaji (gaku, mizu…).","Segmento Todos/N5/N4 (N4 bloqueado até liberar).","Filtro de estado SRS em modal.","„Treinar' roda um mini-drill de reconhecimento."], decluttered:["Leituras avançadas (bloqueadas até o nível)"], tags:["Grade mobile","Filtro (modal)","Página completa","Grade desktop"] },
    render:()=>(<><FrameGroup><KanjiGridMobile theme="light"/><KanjiGridMobile theme="light" filterOpen/><KanjiDetailMobile theme="light"/></FrameGroup><FrameGroup title="Treinar este kanji (drill com 3 tipos de pergunta)"><KanjiTraining theme="light" q="meaning"/><KanjiTraining theme="light" q="reading"/><KanjiTraining theme="light" q="recall"/></FrameGroup><FrameGroup title="Desktop"><KanjiGridDesktop theme="light"/></FrameGroup></>) },
];

// =========================================================
// INTRO / DIRECTION PAGE
// =========================================================
const IntroPage = () => (
  <div style={{ maxWidth:1000 }}>
    {/* Hero */}
    <div style={{ display:'flex', gap:28, alignItems:'center', background:'linear-gradient(135deg, #f3edff, #ece6fb)', border:'1px solid #e2d8f5', borderRadius:28, padding:'32px 36px', marginBottom:28, position:'relative', overflow:'hidden' }}>
      <div style={{ position:'absolute', inset:0, pointerEvents:'none' }}>
        <div className="ym"><StarField><div style={{ width:'100%', height:200 }}/></StarField></div>
      </div>
      <div className="ym" style={{ flexShrink:0 }}><Yomineko pose="reading" size={170}/></div>
      <div>
        <div style={{ display:'flex', alignItems:'center', gap:10, marginBottom:6 }}>
          <span style={{ fontFamily:'"Poppins",sans-serif', fontWeight:700, fontSize:13, letterSpacing:'0.1em', textTransform:'uppercase', color:'#7C4DFF' }}>Direção de alta fidelidade</span>
        </div>
        <h1 style={{ fontFamily:'"Poppins",sans-serif', fontWeight:600, fontSize:44, margin:'0 0 8px', color:'#2b2440', lineHeight:1.05 }}>Yomineko</h1>
        <p style={{ fontFamily:'"Nunito",sans-serif', fontSize:16, lineHeight:1.6, color:'#52496a', margin:0, maxWidth:560 }}>
          Aprender japonês guiado por um gato mágico e seu grimório. Material 3 (Material You) em roxo suave,
          construído para Flutter — web e mobile. Esta primeira entrega remonta a <b>Lição</b> em alta fidelidade.
        </p>
      </div>
    </div>

    {/* Decisions grid */}
    <div style={{ display:'grid', gridTemplateColumns:'repeat(auto-fit, minmax(240px,1fr))', gap:16 }}>
      {[
        { ic:"palette", t:"Material 3 · roxo suave", d:"Cores tonais a partir de um roxo ametista. Cantos arredondados, superfícies em camadas, sombras suaves. Claro e escuro." },
        { ic:"auto_awesome", t:"Acentos mágicos", d:"Estrelas, brilho do grimório e um gradiente arcano em momentos especiais (CTAs, celebração). Discreto no resto." },
        { ic:"pets", t:"Yomineko, equilibrado", d:"O gato aparece em momentos-chave — vazios, celebração, dicas — e como logo. Nunca atrapalha o estudo." },
        { ic:"text_fields", t:"Poppins + Nunito", d:"Títulos geométricos amigáveis (Poppins), corpo legível (Nunito). Japonês em Noto Sans/Serif JP." },
        { ic:"layers", t:"Mobile + Desktop juntos", d:"Cada página mostra suas versões mobile e desktop lado a lado — não mais separadas no menu." },
        { ic:"touch_app", t:"Lição mais limpa", d:"Análise de frase, kanji, gramática e cultura saem do meio e abrem ao toque (bottom sheet / painel lateral)." },
      ].map((c,i)=>(
        <div key={i} style={{ background:'#fff', border:'1px solid #ece4f8', borderRadius:20, padding:'18px 20px', boxShadow:'0 4px 14px rgba(80,50,130,0.05)' }}>
          <span className="material-symbols-rounded" style={{ fontSize:26, color:'#7C4DFF' }}>{c.ic}</span>
          <div style={{ fontFamily:'"Poppins",sans-serif', fontWeight:600, fontSize:16, color:'#2b2440', margin:'8px 0 4px' }}>{c.t}</div>
          <div style={{ fontFamily:'"Nunito",sans-serif', fontSize:13.5, lineHeight:1.5, color:'#52496a' }}>{c.d}</div>
        </div>
      ))}
    </div>

    {/* palette + type swatches */}
    <div style={{ display:'grid', gridTemplateColumns:'1fr 1fr', gap:16, marginTop:16 }}>
      <div style={{ background:'#fff', border:'1px solid #ece4f8', borderRadius:20, padding:'18px 20px' }}>
        <div style={{ fontFamily:'"Poppins",sans-serif', fontWeight:600, fontSize:15, color:'#2b2440', marginBottom:12 }}>Paleta</div>
        <div style={{ display:'flex', flexWrap:'wrap', gap:8 }}>
          {[["Primary","#6750A4"],["Container","#EADDFF"],["Arcano","#7C4DFF"],["Arcano claro","#B388FF"],["Ouro","#E0A93B"],["Sucesso","#3C6E47"],["Erro","#B3261E"],["Superfície","#FEF7FF"]].map(([n,c],i)=>(
            <div key={i} style={{ textAlign:'center' }}>
              <div style={{ width:64, height:48, borderRadius:12, background:c, border:'1px solid rgba(0,0,0,0.08)' }}/>
              <div style={{ fontFamily:'"Nunito",sans-serif', fontSize:10.5, color:'#6b5b8a', marginTop:4 }}>{n}</div>
            </div>
          ))}
        </div>
      </div>
      <div style={{ background:'#fff', border:'1px solid #ece4f8', borderRadius:20, padding:'18px 20px' }}>
        <div style={{ fontFamily:'"Poppins",sans-serif', fontWeight:600, fontSize:15, color:'#2b2440', marginBottom:12 }}>Tipografia</div>
        <div style={{ fontFamily:'"Poppins",sans-serif', fontWeight:600, fontSize:30, color:'#2b2440' }}>Headline · Poppins</div>
        <div style={{ fontFamily:'"Nunito",sans-serif', fontWeight:500, fontSize:16, color:'#52496a', marginTop:4 }}>Corpo em Nunito — legível, amigável, redondo.</div>
        <div style={{ fontFamily:'"Noto Serif JP",serif', fontSize:24, color:'#2b2440', marginTop:8 }}>日本語 · 学生 · わたしは</div>
      </div>
    </div>

    <div style={{ marginTop:24, display:'flex', alignItems:'center', gap:12, background:'#fff', border:'1px dashed #d9cfe9', borderRadius:16, padding:'16px 20px' }}>
      <span className="material-symbols-rounded" style={{ fontSize:22, color:'#7C4DFF' }}>arrow_forward</span>
      <span style={{ fontFamily:'"Nunito",sans-serif', fontSize:14, color:'#52496a' }}>
        Comece por <b>Lição</b> no menu. Depois de aprovar a direção, remonto todas as outras telas (público, dashboard, curso, revisão, prática, bancos) em mobile + desktop.
      </span>
    </div>
  </div>
);

// About / reviewer guide
const AboutProto = () => (
  <div style={{ maxWidth:880 }}>
    <div style={{ display:'flex', gap:20, alignItems:'center', background:'#fff', border:'1px solid #ece4f8', borderRadius:24, padding:'24px 28px', marginBottom:20 }}>
      <div className="ym" style={{ flexShrink:0 }}><Yomineko pose="wave" size={110}/></div>
      <div>
        <span style={{ display:'inline-flex', alignItems:'center', gap:8, background:'#eafaef', border:'1px solid #bfe6c9', borderRadius:999, padding:'4px 12px', fontFamily:'"Nunito",sans-serif', fontWeight:800, fontSize:12, color:'#2f6b40' }}>
          <span style={{ width:8, height:8, borderRadius:'50%', background:'#3C6E47' }}/> Pronto para avaliação
        </span>
        <h1 style={{ fontFamily:'"Poppins",sans-serif', fontWeight:600, fontSize:30, margin:'8px 0 4px', color:'#2b2440' }}>Sobre este protótipo</h1>
        <p style={{ fontFamily:'"Nunito",sans-serif', fontSize:14.5, lineHeight:1.6, color:'#52496a', margin:0 }}>
          Protótipo de alta fidelidade do Yomineko — app de japonês (N5→N1) em Material 3, pensado para Flutter (web + mobile). Use o menu à esquerda para percorrer cada página; todas têm versões mobile e desktop e a maioria em tema claro e escuro.
        </p>
      </div>
    </div>

    <div style={{ display:'grid', gridTemplateColumns:'1fr 1fr', gap:16 }}>
      <div style={{ background:'#fff', border:'1px solid #ece4f8', borderRadius:18, padding:'18px 20px' }}>
        <div style={{ fontFamily:'"Poppins",sans-serif', fontWeight:600, fontSize:15, color:'#2b2440', marginBottom:10 }}>Como avaliar</div>
        <ul style={{ margin:0, paddingLeft:18, fontFamily:'"Nunito",sans-serif', fontSize:13.5, lineHeight:1.7, color:'#4a4159' }}>
          <li>Navegue pelas páginas no meno — cada uma agrupa mobile + desktop.</li>
          <li>Abra "Sobre esta tela" (no topo de cada página) para o racional.</li>
          <li>Compare claro vs. escuro onde houver os dois frames.</li>
          <li>Repare nos fluxos-chave: lição enxuta, revisão (revelar), práticas com/sem teclado, página de kanji com treino.</li>
        </ul>
      </div>
      <div style={{ background:'#fff', border:'1px solid #ece4f8', borderRadius:18, padding:'18px 20px' }}>
        <div style={{ fontFamily:'"Poppins",sans-serif', fontWeight:600, fontSize:15, color:'#2b2440', marginBottom:10 }}>É um protótipo visual</div>
        <ul style={{ margin:0, paddingLeft:18, fontFamily:'"Nunito",sans-serif', fontSize:13.5, lineHeight:1.7, color:'#4a4159' }}>
          <li>Telas estáticas de alta fidelidade — os botões ainda não navegam.</li>
          <li>Áudio, animações de traços e ink-bloom são indicados, não tocados.</li>
          <li>Conteúdo em pt-BR é real (lições, exercícios, kanji), para avaliar de verdade.</li>
          <li>O alvo de implementação é Flutter/Material — este HTML emula o look.</li>
        </ul>
      </div>
    </div>

    <div style={{ background:'#fff', border:'1px solid #ece4f8', borderRadius:18, padding:'18px 20px', marginTop:16 }}>
      <div style={{ fontFamily:'"Poppins",sans-serif', fontWeight:600, fontSize:15, color:'#2b2440', marginBottom:12 }}>O que está coberto</div>
      <div style={{ display:'flex', flexWrap:'wrap', gap:8 }}>
        {["Landing","Login","Dashboard (3 estados)","Perfil","Trocar de curso","Árvore do curso","Lição + 5 folhas","Revisão SRS (revelar)","6 práticas + configs","Sessões com/sem teclado","Vocabulário","Kanji + treino","Tema claro/escuro","Gating por nível"].map((t,i)=>(
          <span key={i} style={{ fontFamily:'"Nunito",sans-serif', fontSize:12.5, fontWeight:700, background:'#f1ebfa', color:'#6b5b8a', borderRadius:999, padding:'4px 12px' }}>{t}</span>
        ))}
      </div>
    </div>
  </div>
);

// =========================================================
// SHELL
// =========================================================
const Gallery = () => {
  const [cur, setCur] = useState(location.hash.slice(1) || "intro");
  React.useEffect(()=>{
    const f=()=>setCur(location.hash.slice(1)||"intro");
    window.addEventListener("hashchange",f); return ()=>window.removeEventListener("hashchange",f);
  },[]);
  const groups = [...new Set(PAGES.map(p=>p.group))];
  const page = PAGES.find(p=>p.id===cur) || PAGES[0];

  return (
    <div style={{ display:'grid', gridTemplateColumns:'248px 1fr', minHeight:'100vh' }}>
      {/* Sidebar */}
      <aside style={{ background:'#fff', borderRight:'1px solid #e7def4', position:'sticky', top:0, height:'100vh', overflowY:'auto', padding:'20px 0' }}>
        <div style={{ display:'flex', alignItems:'center', gap:10, padding:'0 20px 18px' }}>
          <div className="ym"><YominekoLogo size={36}/></div>
          <div>
            <div style={{ fontFamily:'"Poppins",sans-serif', fontWeight:700, fontSize:20, color:'#2b2440', lineHeight:1 }}>Yomineko</div>
            <div style={{ fontFamily:'"Nunito",sans-serif', fontSize:11, color:'#9384ad' }}>Hi-fi · Material 3</div>
          </div>
        </div>
        {groups.map(g=>(
          <div key={g} style={{ marginBottom:6 }}>
            <div style={{ fontFamily:'"Nunito",sans-serif', fontSize:10.5, fontWeight:800, letterSpacing:'0.1em', textTransform:'uppercase', color:'#9384ad', padding:'8px 20px 4px' }}>{g}</div>
            {PAGES.filter(p=>p.group===g).map(p=>(
              <a key={p.id} href={`#${p.id}`} data-screen-label={p.title} style={{
                display:'flex', alignItems:'center', gap:10, padding:'9px 20px', textDecoration:'none', cursor:'pointer',
                fontFamily:'"Nunito",sans-serif', fontWeight:700, fontSize:14.5,
                color: p.id===cur ? '#fff' : '#3a3147',
                background: p.id===cur ? 'linear-gradient(135deg,#7C4DFF,#6750A4)' : 'transparent',
                borderRadius: p.id===cur ? '0 999px 999px 0' : 0, marginRight: p.id===cur? 12:0
              }}>{p.title}</a>
            ))}
          </div>
        ))}
        <div style={{ padding:'18px 20px 0', fontFamily:'"Nunito",sans-serif', fontSize:11, color:'#9384ad', lineHeight:1.5 }}>
          Protótipo completo · {PAGES.length} páginas · claro + escuro
        </div>
      </aside>

      {/* Main */}
      <main style={{ background:'#ECE7F2', padding:'32px 40px 80px', overflowX:'auto' }}>
        {page.id!=="intro" && (
          <div style={{ marginBottom:18 }}>
            <div style={{ fontFamily:'"Nunito",sans-serif', fontSize:12, fontWeight:800, letterSpacing:'0.08em', textTransform:'uppercase', color:'#9384ad' }}>{page.group}</div>
            <h2 style={{ fontFamily:'"Poppins",sans-serif', fontWeight:600, fontSize:34, margin:'2px 0 4px', color:'#2b2440' }}>{page.title}</h2>
            {page.tagline && <p style={{ fontFamily:'"Nunito",sans-serif', fontSize:15, color:'#52496a', margin:0, maxWidth:720 }}>{page.tagline}</p>}
          </div>
        )}
        {page.notes && <NotesPanel notes={page.notes}/>}
        {page.render()}
      </main>
    </div>
  );
};

export default Gallery;
