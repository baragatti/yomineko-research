import { useEffect } from "react";

/**
 * W47 play buttons. A button carries its clip keys in `data-audio-key` (space-separated, played in
 * order); ONE delegated click listener (<AudioClicks/>, mounted in root) plays them from /audio/:key.
 * The same markup comes from <PlayButton> in React pages and from playButtonHtml() in the
 * server-rendered lesson body, so both get the same behaviour with no per-button hydration.
 * Loaders pass only keys whose clip exists, so a button is never rendered for a missing file.
 */
export type AudioLang = "ja" | "pt-BR";

const KEY = /^[a-z2-7]{26}$/;
const label = (lang: AudioLang) => (lang === "ja" ? "Ouvir em japonês" : "Ouvir");

export function PlayButton({ audioKey, lang }: { audioKey: string | readonly string[]; lang: AudioLang }) {
  const keys = typeof audioKey === "string" ? audioKey : audioKey.join(" ");
  return (
    <button type="button" className="ym-play" data-audio-key={keys} data-audio-lang={lang}
            aria-label={label(lang)} title={label(lang)}>
      <span className="material-symbols-rounded" aria-hidden="true" translate="no">volume_up</span>
    </button>
  );
}

/** The same button as an HTML string, for server-rendered markup. Keys are validated, so nothing to escape. */
export function playButtonHtml(keys: readonly string[], lang: AudioLang): string {
  const ok = keys.filter((k) => KEY.test(k));
  if (!ok.length) return "";
  return `<button type="button" class="ym-play" data-audio-key="${ok.join(" ")}" data-audio-lang="${lang}" ` +
    `aria-label="${label(lang)}" title="${label(lang)}"><span class="material-symbols-rounded" aria-hidden="true" ` +
    `translate="no">volume_up</span></button>`;
}

let current: { audio: HTMLAudioElement; button: HTMLElement } | null = null;

function stop(): void {
  if (!current) return;
  current.audio.pause();
  current.button.classList.remove("is-playing");
  current = null;
}

/** Play the keys in order; a second click on the playing button stops it. */
function play(button: HTMLElement, keys: readonly string[]): void {
  const again = current?.button === button;
  stop();
  if (again || !keys.length) return;
  const audio = new Audio();
  let i = 0;
  const next = (): void => {
    if (current?.audio !== audio) return;
    if (i >= keys.length) return stop();
    audio.src = `/audio/${keys[i++]}`;
    audio.play().catch(() => { if (current?.audio === audio) stop(); });
  };
  audio.addEventListener("ended", next);
  audio.addEventListener("error", () => { if (current?.audio === audio) stop(); });
  current = { audio, button };
  button.classList.add("is-playing");
  next();
}

/** Mount once (root): plays any [data-audio-key] button, including ones inside server-rendered HTML. */
export function AudioClicks(): null {
  useEffect(() => {
    const onClick = (e: MouseEvent): void => {
      const target = e.target instanceof Element ? e.target : null;
      const button = target?.closest<HTMLElement>("[data-audio-key]");
      if (!button) return;
      e.preventDefault();
      e.stopPropagation();
      play(button, (button.dataset.audioKey ?? "").split(/\s+/).filter((k) => KEY.test(k)));
    };
    document.addEventListener("click", onClick);
    return () => { document.removeEventListener("click", onClick); stop(); };
  }, []);
  return null;
}
