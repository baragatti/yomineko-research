import { useEffect } from "react";

/**
 * Interactivity for the lesson exercises that need JS:
 *  - sentence_build (.ym-build): tap pieces from the bank into the answer, then "Verificar".
 *  - matching (.ym-match): tap a term on the left, then its pair on the right.
 * Multiple-choice + cloze/production are pure-CSS (radio / <details>) and need nothing here.
 *
 * Implemented as a single delegated `document` click listener (like CorpusRefLayer) — robust over the
 * dangerouslySetInnerHTML lesson body. The bank / right-column are pre-shuffled server-side; all per-exercise
 * state is read from the DOM (classes), so nothing here depends on querying the body at mount time.
 */
export function LessonExercises() {
  useEffect(() => {
    const onClick = (e: MouseEvent) => {
      const t = e.target as HTMLElement;
      if (!t || !t.closest) return;

      // --- sentence_build: move a piece between bank and answer ---
      const tok = t.closest<HTMLElement>(".ym-build-tok");
      if (tok) {
        const build = tok.closest<HTMLElement>(".ym-build");
        if (!build) return;
        const bank = build.querySelector<HTMLElement>(".ym-build-bank");
        const answer = build.querySelector<HTMLElement>(".ym-build-answer");
        if (!bank || !answer) return;
        (tok.parentElement === bank ? answer : bank).appendChild(tok);
        build.classList.remove("is-correct", "is-wrong");
        const r = build.querySelector<HTMLElement>(".ym-build-result");
        if (r) r.hidden = true;
        return;
      }
      const checkBtn = t.closest<HTMLElement>(".ym-build-check");
      if (checkBtn) {
        const build = checkBtn.closest<HTMLElement>(".ym-build");
        if (!build) return;
        const answer = build.querySelector<HTMLElement>(".ym-build-answer");
        const result = build.querySelector<HTMLElement>(".ym-build-result");
        const expl = build.parentElement?.querySelector<HTMLElement>(".ym-ex-expl");
        const got = Array.from(answer?.querySelectorAll<HTMLElement>(".ym-build-tok") || []).map((x) => x.textContent).join("");
        const ok = got.replace(/\s/g, "") === (build.dataset.correct || "").replace(/\s/g, "");
        build.classList.toggle("is-correct", ok);
        build.classList.toggle("is-wrong", !ok);
        if (result) { result.hidden = false; result.textContent = ok ? "Correto!" : `Quase. Resposta: ${build.dataset.answer || build.dataset.correct || ""}`; }
        if (expl) expl.hidden = false;
        return;
      }
      const resetBtn = t.closest<HTMLElement>(".ym-build-reset");
      if (resetBtn) {
        const build = resetBtn.closest<HTMLElement>(".ym-build");
        if (!build) return;
        const bank = build.querySelector<HTMLElement>(".ym-build-bank");
        const answer = build.querySelector<HTMLElement>(".ym-build-answer");
        const result = build.querySelector<HTMLElement>(".ym-build-result");
        const expl = build.parentElement?.querySelector<HTMLElement>(".ym-ex-expl");
        if (bank && answer) Array.from(answer.querySelectorAll<HTMLElement>(".ym-build-tok")).forEach((x) => bank.appendChild(x));
        build.classList.remove("is-correct", "is-wrong");
        if (result) result.hidden = true;
        if (expl) expl.hidden = true;
        return;
      }

      // --- cloze / production: type-and-check ---
      const checkInput = t.closest<HTMLElement>(".ym-input-check");
      const showAns = t.closest<HTMLElement>(".ym-input-show");
      if (checkInput || showAns) {
        const box = (checkInput || showAns)!.closest<HTMLElement>(".ym-input");
        if (!box) return;
        const field = box.querySelector<HTMLInputElement>(".ym-input-field");
        const result = box.querySelector<HTMLElement>(".ym-input-result");
        const ansEl = box.querySelector<HTMLElement>(".ym-input-answer");
        const expl = box.parentElement?.querySelector<HTMLElement>(".ym-ex-expl");
        if (showAns) {
          if (ansEl) ansEl.hidden = false;
          if (expl) expl.hidden = false;
          if (result) result.hidden = true;
          return;
        }
        let accept: string[] = [];
        try { accept = JSON.parse(box.dataset.accept || "[]"); } catch { accept = []; }
        const val = (field?.value || "").trim().toLowerCase();
        const ok = !!val && accept.includes(val);
        box.classList.toggle("is-correct", ok);
        box.classList.toggle("is-wrong", !ok);
        if (result) { result.hidden = false; result.textContent = ok ? "Correto!" : "Ainda não — tente de novo ou veja a resposta."; }
        if (ok) { if (ansEl) ansEl.hidden = false; if (expl) expl.hidden = false; }
        return;
      }

      // --- matching: tap a left term, then its pair on the right ---
      const item = t.closest<HTMLElement>(".ym-match-item");
      if (item && !item.classList.contains("is-matched")) {
        const m = item.closest<HTMLElement>(".ym-match");
        if (!m) return;
        if (item.dataset.side === "left") {
          m.querySelectorAll(".ym-match-item.is-sel").forEach((x) => x.classList.remove("is-sel"));
          item.classList.add("is-sel");
          return;
        }
        const sel = m.querySelector<HTMLElement>('.ym-match-item.is-sel[data-side="left"]');
        if (!sel) return;
        if (sel.dataset.key === item.dataset.key) {
          sel.classList.add("is-matched");
          item.classList.add("is-matched");
          sel.classList.remove("is-sel");
          const total = m.querySelectorAll('.ym-match-item[data-side="left"]').length;
          const done = m.querySelectorAll('.ym-match-item[data-side="left"].is-matched').length;
          if (done === total) {
            const result = m.parentElement?.querySelector<HTMLElement>(".ym-match-result");
            const expl = m.parentElement?.querySelector<HTMLElement>(".ym-ex-expl");
            if (result) { result.hidden = false; result.textContent = "Tudo certo!"; }
            if (expl) expl.hidden = false;
          }
        } else {
          item.classList.add("is-wrong");
          const bad = item;
          window.setTimeout(() => bad.classList.remove("is-wrong"), 450);
          sel.classList.remove("is-sel");
        }
        return;
      }
    };

    document.addEventListener("click", onClick);
    return () => document.removeEventListener("click", onClick);
  }, []);

  return null;
}
