import { useState, useEffect } from 'react';

/* true when the viewport is desktop-sized (>= 900px). Reactive to resize. */
export function useBreakpoint(query = '(min-width: 900px)') {
  const get = () => (typeof window !== 'undefined' ? window.matchMedia(query).matches : false);
  const [matches, setMatches] = useState(get);

  useEffect(() => {
    const mq = window.matchMedia(query);
    const update = () => setMatches(mq.matches);
    mq.addEventListener('change', update);
    // Fallback: some embedded/headless viewports don't emit matchMedia
    // change events on resize — listen to window resize too.
    window.addEventListener('resize', update);
    update();
    return () => {
      mq.removeEventListener('change', update);
      window.removeEventListener('resize', update);
    };
  }, [query]);

  return matches;
}
