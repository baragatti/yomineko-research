import React, { createContext, useContext, useState, useCallback } from 'react';
import { playAudio as playAudioImpl } from './audio';

/* ============================================================
   App store — navigation stack + theme + audio.
   Mock router: a simple screen stack (push / pop / tab-reset).
   ============================================================ */

const DEFAULT = {
  screen: 'login', params: {},
  canBack: false,
  navigate: () => {},
  goTab: () => {},
  back: () => {},
  theme: 'light',
  setTheme: () => {},
  toggleTheme: () => {},
  playAudio: () => {},
};

const AppCtx = createContext(DEFAULT);

export function useApp() {
  return useContext(AppCtx);
}

// Review pending count, persisted in sessionStorage (clears when the tab closes).
export const REVIEW_TOTAL = 3;
export function reviewDue() {
  try { return sessionStorage.getItem('ym-review-done') ? 0 : REVIEW_TOTAL; } catch { return REVIEW_TOTAL; }
}
export function setReviewDone(done) {
  try {
    if (done) sessionStorage.setItem('ym-review-done', '1');
    else sessionStorage.removeItem('ym-review-done');
  } catch { /* ignore */ }
}

// nav-destination id (from NavBar / NavDrawer) -> screen id
export const NAV_TO_SCREEN = {
  home: 'dashboard',
  study: 'course',
  review: 'review',
  practice: 'practice',
  vocab: 'vocab',
  kanji: 'kanji',
  profile: 'profile',
};

function readTheme() {
  try { return localStorage.getItem('ym-theme') || 'light'; } catch { return 'light'; }
}

export function AppProvider({ children }) {
  const [stack, setStack] = useState([{ screen: 'login', params: {} }]);
  const [theme, setThemeState] = useState(readTheme);

  const cur = stack[stack.length - 1];

  const navigate = useCallback((screen, params = {}) => {
    setStack((s) => [...s, { screen, params }]);
  }, []);

  // top-level tab switch: reset the stack so Back doesn't crawl through tabs
  const goTab = useCallback((screen, params = {}) => {
    setStack([{ screen, params }]);
  }, []);

  const back = useCallback(() => {
    setStack((s) => (s.length > 1 ? s.slice(0, -1) : s));
  }, []);

  const setTheme = useCallback((t) => {
    setThemeState(t);
    try { localStorage.setItem('ym-theme', t); } catch { /* ignore */ }
  }, []);

  const toggleTheme = useCallback(() => {
    setThemeState((t) => {
      const next = t === 'dark' ? 'light' : 'dark';
      try { localStorage.setItem('ym-theme', next); } catch { /* ignore */ }
      return next;
    });
  }, []);

  const value = {
    screen: cur.screen,
    params: cur.params,
    canBack: stack.length > 1,
    navigate,
    goTab,
    back,
    theme,
    setTheme,
    toggleTheme,
    playAudio: playAudioImpl,
  };

  return <AppCtx.Provider value={value}>{children}</AppCtx.Provider>;
}
