import React, { useState } from 'react';
import { AppProvider, useApp } from './store';
import { useBreakpoint } from './useBreakpoint';
import { FrameModeContext, NavDrawer } from '../yomineko/m3';
import { LoginMobile, LoginDesktop } from '../yomineko/yomineko-public';
import { DashboardMobile, DashboardDesktop, ProfileMobile, ProfileDesktop } from '../yomineko/yomineko-home';
import { CourseSelectMobile, CourseSelectDesktop, CourseTreeMobile, CourseTreeDesktop } from '../yomineko/yomineko-course';
import { LessonMobile, LessonDesktop } from '../yomineko/yomineko-lesson';
import { PracticeHubMobile, PracticeHubDesktop, HiraganaConfig, ParticleConfig, ConjugationConfig, NumbersConfig } from '../yomineko/yomineko-practice';
import { VocabularyMobile, VocabularyDesktop, KanjiGridMobile, KanjiGridDesktop, KanjiDetailMobile } from '../yomineko/yomineko-banks';
import { ReviewApp } from './ReviewApp';
import { SessionApp } from './SessionApp';

const CONFIG_BY_MODE = { hiragana: HiraganaConfig, katakana: HiraganaConfig, particles: ParticleConfig, conjugation: ConjugationConfig, numbers: NumbersConfig, sentence: ParticleConfig };

// Desktop chrome for screens that only have a phone layout: nav drawer on the
// left + the content in a contained, scrollable panel (not a floating phone).
function DesktopShell({ active, width, children }) {
  return (
    <div style={{ height: '100%', display: 'flex', background: 'var(--surface)' }}>
      <NavDrawer active={active} drawer={true} />
      <div style={{ flex: 1, minWidth: 0, display: 'flex', justifyContent: 'center', padding: '24px', overflow: 'hidden', background: 'var(--surface-container-low)' }}>
        <div style={{ width: `min(${width}px, 100%)`, height: '100%', display: 'flex', flexDirection: 'column', overflow: 'hidden', background: 'var(--surface)', borderRadius: 'var(--r-lg)', boxShadow: 'var(--elev-2)' }}>
          {children}
        </div>
      </div>
    </div>
  );
}

function screenNode(screen, params, theme, isDesktop) {
  const p = { theme };
  const shell = (active, width, node) => (isDesktop ? <DesktopShell active={active} width={width}>{node}</DesktopShell> : node);
  switch (screen) {
    case 'login': return isDesktop ? <LoginDesktop {...p} /> : <LoginMobile {...p} />;
    case 'dashboard': return isDesktop ? <DashboardDesktop {...p} /> : <DashboardMobile {...p} />;
    case 'profile': return isDesktop ? <ProfileDesktop {...p} /> : <ProfileMobile {...p} />;
    case 'course': return isDesktop ? <CourseTreeDesktop {...p} /> : <CourseTreeMobile {...p} />;
    case 'courseSelect': return isDesktop ? <CourseSelectDesktop {...p} /> : <CourseSelectMobile {...p} />;
    case 'lesson': return isDesktop ? <LessonDesktop {...p} /> : <LessonMobile {...p} />;
    case 'practice': return isDesktop ? <PracticeHubDesktop {...p} /> : <PracticeHubMobile {...p} />;
    case 'vocab': return isDesktop ? <VocabularyDesktop {...p} /> : <VocabularyMobile {...p} />;
    case 'kanji': return isDesktop ? <KanjiGridDesktop {...p} /> : <KanjiGridMobile {...p} />;
    case 'review': return shell('review', 640, <ReviewApp />);
    case 'practiceConfig': { const C = CONFIG_BY_MODE[params.mode] || HiraganaConfig; return shell('practice', 560, <C {...p} mode={params.mode} />); }
    case 'practiceSession': return shell('practice', 560, <SessionApp mode={params.mode || 'hiragana'} />);
    case 'kanjiTraining': return shell('kanji', 560, <SessionApp mode="kanji" />);
    case 'kanjiDetail': return shell('kanji', 760, <KanjiDetailMobile {...p} />);
    default: return isDesktop ? <DashboardDesktop {...p} /> : <DashboardMobile {...p} />;
  }
}

function parseParams(s) { try { return s ? JSON.parse(s) : {}; } catch { return {}; } }

function AppRoot() {
  const app = useApp();
  const isDesktop = useBreakpoint();
  const [kanjiModal, setKanjiModal] = useState(false);

  const handleClick = (e) => {
    const el = e.target.closest('[data-go],[data-page],[data-tab],[data-back],[data-audio],[data-theme-toggle]');
    if (!el) return;
    if (el.hasAttribute('data-audio')) { app.playAudio(el.getAttribute('data-audio')); return; }
    if (el.hasAttribute('data-theme-toggle')) { app.toggleTheme(); return; }
    if (el.hasAttribute('data-back')) { if (kanjiModal) { setKanjiModal(false); return; } app.back(); return; }
    if (el.hasAttribute('data-tab')) { setKanjiModal(false); app.goTab(el.getAttribute('data-tab')); return; }
    // data-page: always a full page (even on desktop) — used by "Página completa".
    if (el.hasAttribute('data-page')) { setKanjiModal(false); app.navigate(el.getAttribute('data-page'), parseParams(el.getAttribute('data-params'))); return; }
    if (el.hasAttribute('data-go')) {
      const to = el.getAttribute('data-go');
      if (to === 'kanjiDetail' && isDesktop) { setKanjiModal(true); return; }
      setKanjiModal(false);
      app.navigate(to, parseParams(el.getAttribute('data-params')));
      return;
    }
  };

  const node = screenNode(app.screen, app.params, app.theme, isDesktop);

  return (
    <FrameModeContext.Provider value="app">
      <div
        className="ym"
        data-theme={app.theme}
        onClick={handleClick}
        style={{ position: 'fixed', inset: 0, overflow: 'hidden', background: 'var(--surface)' }}
      >
        {node}

        {kanjiModal && (
          <div
            onClick={(e) => { if (e.target === e.currentTarget) setKanjiModal(false); }}
            style={{ position: 'absolute', inset: 0, background: 'var(--scrim)', display: 'flex', alignItems: 'center', justifyContent: 'center', padding: 24, zIndex: 60 }}
          >
            <div style={{ width: 460, maxWidth: '100%', height: '88%', display: 'flex', flexDirection: 'column', overflow: 'hidden', background: 'var(--surface)', borderRadius: 'var(--r-xl)', boxShadow: 'var(--elev-5)' }}>
              <KanjiDetailMobile theme={app.theme} />
            </div>
          </div>
        )}
      </div>
    </FrameModeContext.Provider>
  );
}

export default function App() {
  return (
    <AppProvider>
      <AppRoot />
    </AppProvider>
  );
}
