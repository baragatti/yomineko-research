/**
 * render-body.server — turn a corpus lesson `body` (our tagged authoring format) into a self-contained HTML
 * string, SERVER-SIDE ONLY. The tagged source, the parser, and the corpus never reach the client; the route
 * sends only this rendered display markup. Adapted from japorongo-front's ContentRender/ComponentMap idea
 * (tag -> renderer) but emitting an opaque HTML string instead of a hydrated React tree.
 */
import { getSentence, getKanji, getVocab, getGrammar, loc } from "./corpus.server";

const esc = (s: string) =>
  String(s ?? "").replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;");

const TOKEN = /<(\/?)([a-zA-Z][\w-]*)((?:\s[^>]*?)?)(\/?)>/g;

function parseAttrs(s: string): Record<string, string> {
  const out: Record<string, string> = {};
  for (const m of s.matchAll(/([\w-]+)="([^"]*)"/g)) out[m[1]] = m[2];
  return out;
}

interface Node { name: string; attrs: Record<string, string>; children: (Node | string)[]; }

function parse(body: string): (Node | string)[] {
  const root: Node = { name: "#root", attrs: {}, children: [] };
  const stack: Node[] = [root];
  let pos = 0;
  let m: RegExpExecArray | null;
  TOKEN.lastIndex = 0;
  const top = () => stack[stack.length - 1];
  while ((m = TOKEN.exec(body))) {
    const text = body.slice(pos, m.index);
    if (text) top().children.push(text);
    pos = TOKEN.lastIndex;
    const [, slash, name, attrStr, selfSlash] = m;
    if (slash) {
      for (let i = stack.length - 1; i > 0; i--) {
        if (stack[i].name === name) { stack.length = i; break; }
      }
    } else if (selfSlash || ["sentence", "exercise", "grammar", "vocab", "kanji", "break"].includes(name)) {
      top().children.push({ name, attrs: parseAttrs(attrStr), children: [] });
    } else {
      const node: Node = { name, attrs: parseAttrs(attrStr), children: [] };
      top().children.push(node);
      stack.push(node);
    }
  }
  if (pos < body.length) top().children.push(body.slice(pos));
  return root.children;
}

const NOTE: Record<string, { ic: string; label: string }> = {
  "l1-advantage": { ic: "lightbulb", label: "Vantagem para você" },
  "l1-pitfall": { ic: "report", label: "Cuidado" },
  tip: { ic: "tips_and_updates", label: "Dica" },
  warning: { ic: "warning", label: "Atenção" },
  culture: { ic: "public", label: "Cultura" },
  example: { ic: "menu_book", label: "Exemplo" },
};

function ruby(surface: string, reading: string): string {
  if (!reading || reading === surface) return `<span class="ym-jp">${esc(surface)}</span>`;
  return `<ruby class="ym-jp">${esc(surface)}<rt>${esc(reading)}</rt></ruby>`;
}

function renderSentence(slug: string, mode: string): string {
  const s = getSentence(slug);
  if (!s) return "";
  const pt = loc(s.translation);
  const jp = esc(s.jp);
  const romaji = s.romaji ? `<div class="ym-sent-romaji">${esc(s.romaji)}</div>` : "";
  return (
    `<div class="ym-sent ym-sent-${esc(mode || "featured")}">` +
    `<div class="ym-sent-jp" lang="ja">${jp}</div>` +
    romaji +
    (pt ? `<div class="ym-sent-pt">${esc(pt)}</div>` : "") +
    `</div>`
  );
}

function chip(kind: "kanji" | "vocab" | "grammar", ref: string): string {
  const id = ref.includes(":") ? ref.split(":", 2)[1] : ref;
  let label = id;
  let href = "";
  if (kind === "kanji") {
    label = id;
    if (getKanji(id)) href = `/kanji/${encodeURIComponent(id)}`;
  } else if (kind === "vocab") {
    label = getVocab(id)?.kana || id;
    if (getVocab(id)) href = `/vocabulario/${encodeURIComponent(id)}`;
  } else if (kind === "grammar") {
    const g = getGrammar(id);
    label = g?.forms?.[0]?.form || g?.structure_pattern || loc(g?.label) || id;
    if (g) href = `/gramatica/${encodeURIComponent(id)}`;
  }
  const inner = esc(label);
  if (href) return `<a class="ym-chip ym-chip-${kind}" lang="ja" href="${esc(href)}">${inner}</a>`;
  return `<span class="ym-chip ym-chip-${kind}" lang="ja">${inner}</span>`;
}

function renderExercise(ref: string, exById: Record<string, any>): string {
  const id = ref.includes(":") ? ref.split(":", 2)[1] : ref;
  const ex = exById[`ex:${id}`] || exById[ref] || exById[id];
  if (!ex) return "";
  const prompt = esc(loc(ex.prompt));
  const ans = ex.answer || {};
  let opts = "";
  if (Array.isArray(ans.choices)) {
    opts =
      `<div class="ym-ex-choices">` +
      ans.choices
        .map((c: string) => `<span class="ym-ex-choice${c === ans.correct ? " is-correct" : ""}">${esc(c)}</span>`)
        .join("") +
      `</div>`;
  } else if (ans.full) {
    opts = `<div class="ym-ex-answer" lang="ja">${esc(ans.full)}</div>`;
  } else if (Array.isArray(ans.order)) {
    opts = `<div class="ym-ex-answer" lang="ja">${esc(ans.text || ans.order.join(""))}</div>`;
  } else if (ans.text) {
    opts = `<div class="ym-ex-answer">${esc(ans.text)}</div>`;
  }
  const expl = ex.explanation ? `<div class="ym-ex-expl">${esc(loc(ex.explanation))}</div>` : "";
  return (
    `<div class="ym-ex" data-type="${esc(ex.type)}">` +
    `<div class="ym-ex-head"><span class="material-symbols-rounded">quiz</span><span>Exercício</span></div>` +
    `<div class="ym-ex-prompt">${prompt}</div>${opts}${expl}</div>`
  );
}

function emit(nodes: (Node | string)[], exById: Record<string, any>): string {
  let out = "";
  for (const n of nodes) {
    if (typeof n === "string") { out += esc(n); continue; }
    const kids = () => emit(n.children, exById);
    switch (n.name) {
      case "heading": out += `<h${n.attrs.level === "3" ? 3 : 2} class="ym-h${n.attrs.level === "3" ? 3 : 2}">${kids()}</h${n.attrs.level === "3" ? 3 : 2}>`; break;
      case "p": out += `<p class="ym-p">${kids()}</p>`; break;
      case "text": out += n.attrs.weight === "bold" ? `<strong>${kids()}</strong>` : kids(); break;
      case "emphasis": out += `<em>${kids()}</em>`; break;
      case "romaji": out += `<span class="ym-romaji">${kids()}</span>`; break;
      case "term": out += `<span class="ym-term" title="${esc(n.attrs.define || "")}">${kids()}</span>`; break;
      case "jp": out += ruby(n.children.map((c) => (typeof c === "string" ? c : "")).join(""), n.attrs.reading || ""); break;
      case "note": {
        const meta = NOTE[n.attrs.type] || { ic: "info", label: "Nota" };
        out += `<div class="ym-note ym-note-${esc(n.attrs.type || "info")}"><div class="ym-note-head"><span class="material-symbols-rounded">${meta.ic}</span><span>${esc(meta.label)}</span></div><div class="ym-note-body">${kids()}</div></div>`;
        break;
      }
      case "list": out += `<ul class="ym-list">${kids()}</ul>`; break;
      case "item": out += `<li class="ym-item">${kids()}</li>`; break;
      case "checklist": out += `<div class="ym-checklist"><div class="ym-checklist-head"><span class="material-symbols-rounded">checklist</span><span>O que você consegue fazer agora</span></div>${kids()}</div>`; break;
      case "check": out += `<div class="ym-check"><span class="material-symbols-rounded ym-check-ic">check_circle</span><span class="ym-check-text">${kids()}</span></div>`; break;
      case "sentence": out += renderSentence(n.attrs.ref, n.attrs.mode || "featured"); break;
      case "exercise": out += renderExercise(n.attrs.ref, exById); break;
      case "grammar": out += chip("grammar", n.attrs.ref); break;
      case "vocab": out += chip("vocab", n.attrs.ref); break;
      case "kanji": out += chip("kanji", n.attrs.ref); break;
      case "break": out += "<br/>"; break;
      default: out += kids();
    }
  }
  return out;
}

/** Render a lesson body (tagged source) to a display-HTML string. Server-only. */
export function renderBody(body: string, exercises: any[] = []): string {
  const exById: Record<string, any> = {};
  for (const ex of exercises) if (ex?.id) exById[ex.id] = ex;
  return `<div class="ym-body">${emit(parse(body || ""), exById)}</div>`;
}
