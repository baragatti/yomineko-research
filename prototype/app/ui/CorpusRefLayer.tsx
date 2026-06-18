import { useEffect, useRef, useState } from "react";
import { Link } from "react-router";
import { Icon } from "./Icon";
import type { RefSummary } from "~/lib/corpus.server";

/**
 * Interactivity for inline corpus chips inside server-rendered lesson bodies.
 * - hover / keyboard-focus -> a small tooltip (reading + romaji + gloss)
 * - click / tap            -> a rich native <dialog>: readings(+romaji)/strokes/examples (kanji),
 *                             senses (vocab), pattern/forms/explanation (grammar), + "ver detalhes".
 *
 * Rich content comes from `refData` (built server-side per lesson, keyed by `${kind}:${id}`). Event-delegated
 * + body-appended tooltip, so it never mutates the React-owned lesson HTML. Ships only this lesson's refs.
 */
const KIND_LABEL: Record<string, string> = { kanji: "Kanji", vocab: "Vocabulário", grammar: "Gramática" };
const SEL = ".ym-chip[data-ref]";

export function CorpusRefLayer({ refData }: { refData: Record<string, RefSummary> }) {
  const [modal, setModal] = useState<RefSummary | null>(null);
  const dialogRef = useRef<HTMLDialogElement>(null);

  useEffect(() => {
    const tip = document.createElement("div");
    tip.className = "ym-tip";
    tip.setAttribute("role", "tooltip");
    tip.hidden = true;
    document.body.appendChild(tip);
    let current: HTMLElement | null = null;

    const refOf = (el: HTMLElement) => refData[el.dataset.ref || ""];
    const chipFrom = (t: EventTarget | null): HTMLElement | null =>
      t instanceof Element ? (t.closest(SEL) as HTMLElement | null) : null;

    function position(el: HTMLElement) {
      const r = el.getBoundingClientRect();
      const tr = tip.getBoundingClientRect();
      let top = r.top - tr.height - 8;
      let below = false;
      if (top < 8) { top = r.bottom + 8; below = true; }
      let left = Math.max(8, Math.min(r.left + r.width / 2 - tr.width / 2, window.innerWidth - tr.width - 8));
      tip.style.top = `${Math.round(top)}px`;
      tip.style.left = `${Math.round(left)}px`;
      tip.dataset.placement = below ? "below" : "above";
    }
    function show(el: HTMLElement) {
      const d = refOf(el);
      const reading = d ? (d.kind === "kanji" ? (d.romaji || "") : d.kind === "vocab" ? `${d.sub || ""}${d.romaji ? " · " + d.romaji : ""}` : d.pattern || "") : el.dataset.reading || "";
      const gloss = d?.gloss || el.dataset.gloss || "";
      tip.replaceChildren();
      if (reading) { const s = document.createElement("span"); s.className = "ym-tip-reading"; s.lang = "ja"; s.textContent = reading; tip.appendChild(s); }
      if (gloss) { const s = document.createElement("span"); s.className = "ym-tip-gloss"; s.textContent = gloss; tip.appendChild(s); }
      if (!tip.childElementCount) return;
      tip.hidden = false;
      current = el;
      position(el);
    }
    const hide = () => { tip.hidden = true; current = null; };
    const canHover = window.matchMedia("(hover: hover)").matches;

    const onOver = (e: Event) => { if (!canHover) return; const el = chipFrom(e.target); if (el && el !== current) show(el); };
    const onOut = (e: Event) => { const el = chipFrom(e.target); if (el && el === current) hide(); };
    const onFocusIn = (e: Event) => { const el = chipFrom(e.target); if (el) show(el); };
    const onFocusOut = (e: Event) => { const el = chipFrom(e.target); if (el && el === current) hide(); };
    const onScroll = () => { if (current) position(current); };
    const onClick = (e: MouseEvent) => {
      if (e.defaultPrevented || e.button !== 0 || e.metaKey || e.ctrlKey || e.shiftKey || e.altKey) return;
      const el = chipFrom(e.target);
      if (!el) return;
      const d = refOf(el);
      if (!d) return; // no rich data -> let the link navigate
      e.preventDefault();
      hide();
      setModal(d);
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
  }, [refData]);

  useEffect(() => {
    const dlg = dialogRef.current;
    if (!dlg) return;
    if (modal && !dlg.open) dlg.showModal();
    else if (!modal && dlg.open) dlg.close();
  }, [modal]);

  const close = () => setModal(null);

  return (
    <dialog ref={dialogRef} className="ym-dialog" onClose={close} onClick={(e) => { if (e.target === dialogRef.current) close(); }}>
      {modal && (
        <div className="ym-dialog-card">
          <button type="button" className="ym-dialog-x icon-btn" aria-label="Fechar" onClick={close}><Icon name="close" size={20} /></button>
          <div className="ym-dialog-kind">{KIND_LABEL[modal.kind]}</div>
          <div className="ym-dialog-head">
            <span className="ym-dialog-title" lang="ja">{modal.title}</span>
            {modal.sub && <ruby className="ym-dialog-ruby" lang="ja">{modal.title}<rt>{modal.sub}</rt></ruby>}
          </div>
          {(modal.romaji || modal.pattern) && <div className="ym-dialog-romaji" lang="ja">{modal.romaji || modal.pattern}</div>}

          {modal.kind === "kanji" && (
            <>
              <div className="ym-pill-row">
                {modal.strokes != null && <span className="ym-pill">{modal.strokes} traços</span>}
              </div>
              {modal.meanings && modal.meanings.length > 0 && <div className="ym-dialog-gloss">{modal.meanings.join(" · ")}</div>}
              {(modal.kun?.length || modal.on?.length) ? (
                <div className="ym-dialog-readings">
                  {modal.kun && modal.kun.length > 0 && <ReadingLine label="kun" items={modal.kun} />}
                  {modal.on && modal.on.length > 0 && <ReadingLine label="on" items={modal.on} />}
                </div>
              ) : null}
              {modal.examples && modal.examples.length > 0 && (
                <div className="ym-dialog-ex">
                  {modal.examples.slice(0, 4).map((w, i) => (
                    <div key={i} className="ym-dialog-ex-row">
                      <ruby lang="ja">{w.hw}<rt>{w.kana}</rt></ruby>
                      <span>{w.gloss}</span>
                    </div>
                  ))}
                </div>
              )}
            </>
          )}

          {modal.kind === "vocab" && modal.senses && (
            <ol className="ym-dialog-senses">
              {modal.senses.map((s, i) => (
                <li key={i}>
                  {s.pos.length > 0 && <span className="ym-tag">{s.pos.join(" · ")}</span>}
                  <span className="ym-dialog-sense-gloss">{s.gloss.join("; ")}</span>
                </li>
              ))}
            </ol>
          )}

          {modal.kind === "grammar" && (
            <>
              {modal.forms && modal.forms.length > 0 && (
                <div className="ym-dialog-forms">
                  {modal.forms.map((f, i) => (
                    <div key={i} className="ym-dialog-form-row"><span lang="ja">{f.form}</span><span>{f.meaning}</span></div>
                  ))}
                </div>
              )}
              {modal.explanation && <p className="ym-dialog-expl">{modal.explanation}</p>}
            </>
          )}

          <div className="ym-dialog-actions">
            <Link to={modal.href} className="btn btn-filled" onClick={close}>Ver detalhes <Icon name="arrow_forward" size={18} /></Link>
            <button type="button" className="btn btn-text" onClick={close}>Fechar</button>
          </div>
        </div>
      )}
    </dialog>
  );
}

function ReadingLine({ label, items }: { label: string; items: { r: string; romaji: string }[] }) {
  return (
    <div className="ym-dialog-reading-line">
      <span className="ym-reading-label">{label}</span>
      <div className="ym-reading-list">
        {items.map((r, i) => (
          <span key={i} className="ym-reading" lang="ja" title={r.romaji}>
            <span className="ym-reading-main">{r.r}</span>
            <span className="ym-reading-romaji">{r.romaji}</span>
          </span>
        ))}
      </div>
    </div>
  );
}
