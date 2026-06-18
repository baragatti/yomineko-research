import { useEffect, useRef, useState } from "react";
import { Link } from "react-router";

/**
 * Interactivity for inline corpus chips (kanji / vocab / grammar) inside server-rendered lesson bodies.
 * - hover / keyboard-focus -> a small tooltip with the reading + gloss (so the learner keeps their place)
 * - click / tap          -> a native <dialog> preview with a "ver detalhes" link
 *
 * It works by event delegation on `document` and a body-appended tooltip node, so it never mutates the
 * React-owned lesson HTML. It ships NO corpus data of its own: everything it shows is already in the page
 * (the chip's data-* attributes are per-lesson display markup). Without JS, chips are plain links.
 */
interface RefData { kind: string; title: string; reading?: string; gloss?: string; href?: string }

const KIND_LABEL: Record<string, string> = { kanji: "Kanji", vocab: "Vocabulário", grammar: "Gramática" };
const SEL = ".ym-chip[data-gloss], .ym-chip[data-reading]";

export function CorpusRefLayer() {
  const [modal, setModal] = useState<RefData | null>(null);
  const dialogRef = useRef<HTMLDialogElement>(null);

  useEffect(() => {
    const tip = document.createElement("div");
    tip.className = "ym-tip";
    tip.setAttribute("role", "tooltip");
    tip.hidden = true;
    document.body.appendChild(tip);
    let current: HTMLElement | null = null;

    const dataOf = (el: HTMLElement): RefData => ({
      kind: el.dataset.kind || "",
      title: el.dataset.title || el.textContent || "",
      reading: el.dataset.reading,
      gloss: el.dataset.gloss,
      href: el.getAttribute("href") || undefined,
    });
    const chipFrom = (t: EventTarget | null): HTMLElement | null =>
      (t instanceof Element ? (t.closest(SEL) as HTMLElement | null) : null);

    function position(el: HTMLElement) {
      const r = el.getBoundingClientRect();
      const tr = tip.getBoundingClientRect();
      let top = r.top - tr.height - 8;
      let below = false;
      if (top < 8) { top = r.bottom + 8; below = true; }
      let left = r.left + r.width / 2 - tr.width / 2;
      left = Math.max(8, Math.min(left, window.innerWidth - tr.width - 8));
      tip.style.top = `${Math.round(top)}px`;
      tip.style.left = `${Math.round(left)}px`;
      tip.dataset.placement = below ? "below" : "above";
    }
    function show(el: HTMLElement) {
      const d = dataOf(el);
      tip.replaceChildren();
      if (d.reading) { const s = document.createElement("span"); s.className = "ym-tip-reading"; s.lang = "ja"; s.textContent = d.reading; tip.appendChild(s); }
      if (d.gloss) { const s = document.createElement("span"); s.className = "ym-tip-gloss"; s.textContent = d.gloss; tip.appendChild(s); }
      if (!tip.childElementCount) return;
      tip.hidden = false;
      current = el;
      position(el);
    }
    const hide = () => { tip.hidden = true; current = null; };

    const canHover = window.matchMedia("(hover: hover)").matches; // skip hover-tooltip on touch (avoids tap flash)
    const onOver = (e: Event) => { if (!canHover) return; const el = chipFrom(e.target); if (el && el !== current) show(el); };
    const onOut = (e: Event) => { const el = chipFrom(e.target); if (el && el === current) hide(); };
    const onFocusIn = (e: Event) => { const el = chipFrom(e.target); if (el) show(el); };
    const onFocusOut = (e: Event) => { const el = chipFrom(e.target); if (el && el === current) hide(); };
    const onScroll = () => { if (current) position(current); };
    const onClick = (e: MouseEvent) => {
      // let the browser handle modified / non-primary clicks (open in new tab, etc.)
      if (e.defaultPrevented || e.button !== 0 || e.metaKey || e.ctrlKey || e.shiftKey || e.altKey) return;
      const el = chipFrom(e.target);
      if (!el) return;
      e.preventDefault();
      hide();
      setModal(dataOf(el));
    };

    document.addEventListener("mouseover", onOver);
    document.addEventListener("mouseout", onOut);
    document.addEventListener("focusin", onFocusIn);
    document.addEventListener("focusout", onFocusOut);
    document.addEventListener("click", onClick);
    window.addEventListener("scroll", onScroll, true);
    window.addEventListener("resize", hide);
    return () => {
      document.removeEventListener("mouseover", onOver);
      document.removeEventListener("mouseout", onOut);
      document.removeEventListener("focusin", onFocusIn);
      document.removeEventListener("focusout", onFocusOut);
      document.removeEventListener("click", onClick);
      window.removeEventListener("scroll", onScroll, true);
      window.removeEventListener("resize", hide);
      tip.remove();
    };
  }, []);

  useEffect(() => {
    const dlg = dialogRef.current;
    if (!dlg) return;
    if (modal && !dlg.open) dlg.showModal();
    else if (!modal && dlg.open) dlg.close();
  }, [modal]);

  return (
    <dialog
      ref={dialogRef}
      className="ym-dialog"
      onClose={() => setModal(null)}
      onClick={(e) => { if (e.target === dialogRef.current) setModal(null); }}
    >
      {modal && (
        <div className="ym-dialog-card">
          <div className="ym-dialog-kind">{KIND_LABEL[modal.kind] || ""}</div>
          <div className="ym-dialog-title" lang="ja">{modal.title}</div>
          {modal.reading && <div className="ym-dialog-reading" lang="ja">{modal.reading}</div>}
          {modal.gloss && <div className="ym-dialog-gloss">{modal.gloss}</div>}
          <div className="ym-dialog-actions">
            {modal.href && (
              <Link to={modal.href} className="btn btn-filled" onClick={() => setModal(null)}>Ver detalhes</Link>
            )}
            <button type="button" className="btn btn-text" onClick={() => setModal(null)}>Fechar</button>
          </div>
        </div>
      )}
    </dialog>
  );
}
