/**
 * render-body.server — turn a corpus lesson `body` (our tagged authoring format) into a self-contained HTML
 * string, SERVER-SIDE ONLY. The tagged source, the parser, and the corpus never reach the client; the route
 * sends only this rendered display markup. Adapted from japorongo-front's ContentRender/ComponentMap idea
 * (tag -> renderer) but emitting an opaque HTML string instead of a hydrated React tree.
 */
import { getSentence, getReading, getKanji, getVocab, getGrammar, loc, locArr, kanaToRomaji } from "./corpus.server";

const esc = (s: string) =>
  String(s ?? "").replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;");

// runs of Japanese script (kana, kanji, CJK marks) — used to set them apart inside pt-BR prose.
const CJK = /[぀-ヿ㐀-鿿々〆ーｦ-ﾟ々〆ヶ]+/g;
const escJa = (s: string) => esc(s).replace(CJK, (m) => `<span class="ym-ja" lang="ja">${m}</span>`);

// decorative Material Symbols glyph — hidden from assistive tech (the adjacent label carries meaning).
const msIcon = (name: string) => `<span class="material-symbols-rounded" aria-hidden="true">${name}</span>`;

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
    } else if (selfSlash || ["sentence", "reading", "exercise", "grammar", "vocab", "kanji", "break"].includes(name)) {
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

// Japanese unit -> ruby + audio-ready marker (data-say carries the spoken form for future TTS).
function ruby(surface: string, reading: string): string {
  if (!reading || reading === surface) return `<span class="ym-jp ym-say" data-say="${esc(surface)}" lang="ja">${esc(surface)}</span>`;
  // a phrase-length reading (e.g. a whole example sentence) as furigana-over a long string is cramped and
  // unreadable — render it as the text with the reading on a small caption line beneath instead.
  if (reading.length >= 7) {
    return `<span class="ym-jp ym-jp-phrase ym-say" data-say="${esc(reading)}" lang="ja">${esc(surface)}<small class="ym-jp-read">${esc(reading)}</small></span>`;
  }
  return `<ruby class="ym-jp ym-say" data-say="${esc(reading)}" lang="ja">${esc(surface)}<rt>${esc(reading)}</rt></ruby>`;
}

const PUNCT = /^[、。・，．？！「」『』（）\s]+$/;
// word-by-word breakdown + particle functions (from the sentence's per-token analysis)
function renderBreakdown(s: any): string {
  let out = "";
  const toks = (s.tokens || []).filter((t: any) => t.s && !PUNCT.test(t.s));
  if (toks.length) {
    out +=
      `<div class="ym-bd"><div class="ym-bd-label">Palavra por palavra</div><div class="ym-bd-list">` +
      toks
        .map((t: any) => {
          const read = [t.r, t.ro].filter(Boolean).join(" · ");
          return (
            `<div class="ym-bd-tok">` +
            `<span class="ym-bd-jp" lang="ja">${esc(t.s)}</span>` +
            (read ? `<span class="ym-bd-read" lang="ja">${esc(read)}</span>` : "") +
            (t.gloss ? `<span class="ym-bd-gloss">${esc(t.gloss)}</span>` : "") +
            (t.role ? `<span class="ym-bd-role">${esc(t.role)}</span>` : "") +
            `</div>`
          );
        })
        .join("") +
      `</div></div>`;
  }
  const parts = (s.particles || []).filter((p: any) => p.p);
  if (parts.length) {
    out +=
      `<div class="ym-bd-parts"><div class="ym-bd-label">Partículas</div>` +
      parts
        .map(
          (p: any) =>
            `<div class="ym-bd-part"><span class="ym-chip ym-chip-grammar" lang="ja">${esc(p.p)}</span>` +
            (p.ft ? `<span class="ym-tag">${esc(p.ft)}</span>` : "") +
            `<span class="ym-bd-pexpl">${escJa(p.ex || p.fn || "")}</span></div>`
        )
        .join("") +
      `</div>`;
  }
  return out;
}

function renderSentence(slug: string, mode: string): string {
  const s = getSentence(slug);
  if (!s) return "";
  const pt = loc(s.translation);
  const jp = esc(s.jp);
  const romaji = s.romaji ? `<div class="ym-sent-romaji">${esc(s.romaji)}</div>` : "";
  const lit = loc(s.translation_literal);
  const expl = loc(s.structure_explanation);
  const breakdown = renderBreakdown(s);
  const more =
    lit || expl || breakdown
      ? `<details class="ym-sent-more"><summary>Análise</summary>` +
        breakdown +
        (lit ? `<p class="ym-sent-literal"><span>Literal:</span> ${escJa(lit)}</p>` : "") +
        (expl ? `<p class="ym-sent-expl">${escJa(expl)}</p>` : "") +
        `</details>`
      : "";
  return (
    `<div class="ym-sent ym-sent-${esc(mode || "featured")}">` +
    `<div class="ym-sent-jp" lang="ja">${jp}</div>` +
    romaji +
    (pt ? `<div class="ym-sent-pt">${esc(pt)}</div>` : "") +
    more +
    `</div>`
  );
}

// reading-practice box: a short SELECTED passage (real bank text, all i+0 for this lesson) rendered with
// per-token furigana (kanji-bearing tokens only), a learner-toggleable furigana switch (pure CSS, scoped per
// box via :has), an optional romaji line, and a click-to-reveal pt-BR translation. Server-rendered HTML only.
const KANJI_RE = /[一-鿿々〆ヶ]/;
// furigana for one token: place the reading over the KANJI core only, leaving shared leading kana (お…) and
// trailing okurigana (…く, …い) plain — so 行く→行(い)く, not 行く(いく). Falls back to whole-token ruby when
// the surface is a single kanji block (日本語) or can't be cleanly split.
function tokenRuby(s: string, r: string): string {
  if (!r || r === s || !KANJI_RE.test(s)) return esc(s);
  let pre = 0;
  while (pre < s.length && pre < r.length && s[pre] === r[pre] && !KANJI_RE.test(s[pre])) pre++;
  let suf = 0;
  while (suf < s.length - pre && suf < r.length - pre &&
         s[s.length - 1 - suf] === r[r.length - 1 - suf] && !KANJI_RE.test(s[s.length - 1 - suf])) suf++;
  const sMid = s.slice(pre, s.length - suf);
  const rMid = r.slice(pre, r.length - suf);
  if (!sMid || !rMid) return esc(s);
  return esc(s.slice(0, pre)) + `<ruby>${esc(sMid)}<rt>${esc(rMid)}</rt></ruby>` + esc(s.slice(s.length - suf));
}
function readingRuby(tokens: any[]): string {
  return (tokens || []).map((t: any) => (t?.s ? tokenRuby(String(t.s), String(t.r ?? "")) : "")).join("");
}
function renderReading(slug: string, show: string): string {
  const r = getReading(slug);
  if (!r) return "";
  const furi = readingRuby(r.tokens || []);
  const pt = loc(r.translation);
  const wantRomaji = show === "romaji" || show === "both";
  const romajiLine = wantRomaji
    ? `<div class="ym-reading-romaji">${esc((r.tokens || []).map((t: any) => t.ro).filter(Boolean).join(" "))}</div>`
    : "";
  // furigana toggle = a visually-hidden checkbox that is a SIBLING of the text, flipped by its <label> in the
  // head and read by the `~` combinator in CSS. This is the universally-supported pure-CSS toggle (no JS, no
  // :has() — whose dynamic :checked invalidation is unreliable across engines). One id per box.
  const id = "ym-furi-" + slug.replace(/[^a-zA-Z0-9]+/g, "-");
  return (
    `<div class="ym-reading">` +
    `<input type="checkbox" id="${id}" class="ym-reading-furi" checked>` +
    `<div class="ym-reading-head">${msIcon("auto_stories")}<span class="ym-reading-label">Leia em japonês</span>` +
    `<label class="ym-reading-furi-toggle" for="${id}"><span class="ym-reading-furi-box"></span>` +
    `<span>Furigana</span></label></div>` +
    `<div class="ym-reading-jp" lang="ja">${furi}</div>` +
    romajiLine +
    (pt
      ? `<details class="ym-reading-trans"><summary>${msIcon("translate")}<span>Ver tradução</span></summary>` +
        `<p class="ym-reading-pt">${esc(pt)}</p></details>`
      : "") +
    `</div>`
  );
}

function chip(kind: "kanji" | "vocab" | "grammar", ref: string): string {
  const id = ref.includes(":") ? ref.split(":", 2)[1] : ref;
  let text = id; // visible chip text
  let title = id; // modal heading
  let reading = "";
  let gloss = "";
  let href = "";
  if (kind === "kanji") {
    const k = getKanji(id);
    text = id; title = id;
    if (k) {
      reading = [...new Set((k.readings || []).filter((r: any) => r.common).map((r: any) => r.reading))].slice(0, 5).join("、");
      gloss = locArr(k.meanings).slice(0, 3).join(", ");
      href = `/kanji/${encodeURIComponent(id)}`;
    }
  } else if (kind === "vocab") {
    const v = getVocab(id);
    text = v?.kana || id; title = v?.headword || id;
    if (v) {
      reading = v.romaji || "";
      gloss = locArr(v.senses?.[0]?.gloss).slice(0, 3).join(", ");
      href = `/vocabulario/${encodeURIComponent(id)}`;
    }
  } else if (kind === "grammar") {
    const g = getGrammar(id);
    text = g?.forms?.[0]?.form || g?.structure_pattern || loc(g?.label) || id;
    title = loc(g?.label) || text;
    if (g) {
      reading = g.structure_pattern || "";
      gloss = loc(g.forms?.[0]?.meaning) || loc(g.label) || "";
      href = `/gramatica/${encodeURIComponent(id)}`;
    }
  }
  // data-ref is the lookup key into the lesson's refData (rich tooltip + modal). Keep title/reading/gloss as
  // a no-rich-data fallback so the tooltip still works if a summary is missing.
  const data =
    ` data-ref="${esc(kind + ":" + id)}" data-kind="${kind}" data-title="${esc(title)}"` +
    (reading ? ` data-reading="${esc(reading)}"` : "") +
    (gloss ? ` data-gloss="${esc(gloss)}"` : "");
  const inner = esc(text);
  if (href) return `<a class="ym-chip ym-chip-${kind}" lang="ja" href="${esc(href)}"${data}>${inner}</a>`;
  return `<span class="ym-chip ym-chip-${kind}" lang="ja"${data}>${inner}</span>`;
}

// deterministic shuffle (seeded by the exercise id) so the bank/right-column order is stable and baked into
// the server-rendered HTML — the client uses that exact string, so there is no hydration mismatch.
function hashStr(s: string): number {
  let h = 2166136261;
  for (let i = 0; i < s.length; i++) { h ^= s.charCodeAt(i); h = Math.imul(h, 16777619); }
  return h >>> 0;
}
function seededShuffle<T>(arr: T[], seedStr: string): T[] {
  let seed = hashStr(seedStr) || 1;
  const rnd = () => { seed = (seed * 1664525 + 1013904223) >>> 0; return seed / 4294967296; };
  for (let i = arr.length - 1; i > 0; i--) { const j = Math.floor(rnd() * (i + 1)); [arr[i], arr[j]] = [arr[j], arr[i]]; }
  return arr;
}

const EX_META: Record<string, { ic: string; label: string }> = {
  recognition: { ic: "quiz", label: "Escolha a resposta" },
  particle_choice: { ic: "quiz", label: "Escolha a partícula" },
  matching: { ic: "link", label: "Ligue os pares" },
  sentence_build: { ic: "reorder", label: "Monte a frase" },
  cloze: { ic: "edit", label: "Complete" },
  production: { ic: "edit_note", label: "Responda" },
};

function renderExercise(ref: string, exById: Record<string, any>): string {
  const id = ref.includes(":") ? ref.split(":", 2)[1] : ref;
  const ex = exById[`ex:${id}`] || exById[ref] || exById[id];
  if (!ex) return "";
  const ans = ex.answer || {};
  const meta = EX_META[ex.type] || { ic: "quiz", label: "Exercício" };
  const explText = ex.explanation ? escJa(loc(ex.explanation)) : "";
  const explVisible = explText ? `<div class="ym-ex-expl">${explText}</div>` : "";
  const explHidden = explText ? `<div class="ym-ex-expl" hidden>${explText}</div>` : "";

  let body = "";
  if (Array.isArray(ans.choices)) {
    // Pure-CSS quiz (radio + :has). Answer + explanation hidden until a choice is picked. Works without JS.
    const group = `exq-${esc(id)}`;
    body =
      `<fieldset class="ym-ex-choices"><legend class="ym-sr-only">Escolha a resposta</legend>` +
      ans.choices
        .map((c: string) => `<label class="ym-ex-choice"><input type="radio" name="${group}" data-correct="${c === ans.correct ? "true" : "false"}"><span lang="ja">${esc(c)}</span></label>`)
        .join("") +
      `</fieldset>` + explVisible;
  } else if (ex.type === "sentence_build" && Array.isArray(ans.order)) {
    // tap-to-build: the island shuffles the bank, the learner taps pieces into the answer, then "Verificar".
    const correct = ans.order.join("");
    const toks = seededShuffle([...ans.order], id).map((t: string) => `<button type="button" class="ym-build-tok" lang="ja">${esc(t)}</button>`).join("");
    body =
      `<div class="ym-build" data-correct="${esc(correct)}" data-answer="${esc(ans.text || correct)}">` +
      `<div class="ym-build-answer" role="list" aria-label="Sua resposta"></div>` +
      `<div class="ym-build-bank">${toks}</div>` +
      `<div class="ym-build-actions"><button type="button" class="btn btn-filled btn-sm ym-build-check">Verificar</button><button type="button" class="btn btn-text btn-sm ym-build-reset">Limpar</button></div>` +
      `<div class="ym-build-result" hidden></div></div>` + explHidden;
  } else if (ex.type === "matching" && Array.isArray(ans.pairs)) {
    // tap-to-match: tap a term on the left, then its match on the right. The island shuffles the right column.
    const left = ans.pairs.map((p: string[], i: number) => `<button type="button" class="ym-match-item" data-side="left" data-key="${i}">${esc(p[0])}</button>`).join("");
    const right = seededShuffle<{ i: number; r: string }>(ans.pairs.map((p: string[], i: number) => ({ i, r: p[1] })), id)
      .map((x) => `<button type="button" class="ym-match-item" data-side="right" data-key="${x.i}">${esc(x.r)}</button>`).join("");
    body =
      `<div class="ym-match"><div class="ym-match-col">${left}</div><div class="ym-match-col ym-match-right">${right}</div></div>` +
      `<div class="ym-match-result" hidden></div>` + explHidden;
  } else if (ans.text || ans.full || Array.isArray(ans.accept)) {
    // cloze / production -> type-and-check input. Accepts the kana answer OR its romaji (no IME needed).
    const answerText = ans.text || ans.full || "";
    const accepts = (ans.accept && ans.accept.length ? ans.accept : [answerText]).filter(Boolean);
    const all = Array.from(new Set([...accepts, ...accepts.map((a: string) => kanaToRomaji(a))].map((x) => String(x).toLowerCase())));
    body =
      `<div class="ym-input" data-accept="${esc(JSON.stringify(all))}">` +
      `<div class="ym-input-row"><input type="text" class="ym-input-field" placeholder="Digite a resposta (kana ou romaji)" autocomplete="off" autocapitalize="off" autocorrect="off" spellcheck="false">` +
      `<button type="button" class="btn btn-filled btn-sm ym-input-check">Verificar</button></div>` +
      `<button type="button" class="ym-input-show">Ver resposta</button>` +
      `<div class="ym-input-result" hidden></div>` +
      `<div class="ym-input-answer" hidden>Resposta: <b lang="ja">${esc(answerText)}</b></div>` +
      `</div>` + explHidden;
  } else {
    // fallback -> click-to-reveal
    const a = Array.isArray(ans.order) ? ans.order.join("") : "";
    body = `<details class="ym-ex-reveal"><summary>Mostrar resposta</summary>` + (a ? `<div class="ym-ex-answer" lang="ja">${esc(a)}</div>` : "") + explText + `</details>`;
  }

  return (
    `<div class="ym-ex" data-type="${esc(ex.type)}">` +
    `<div class="ym-ex-head">${msIcon(meta.ic)}<span>${esc(meta.label)}</span></div>` +
    `<div class="ym-ex-prompt">${escJa(loc(ex.prompt))}</div>${body}</div>`
  );
}

const nodeName = (n: Node | string | undefined) => (n && typeof n !== "string" ? n.name : "");
const nodeStr = (n: Node | string | undefined) => (n == null ? "" : typeof n === "string" ? n : nodeText(n));

function emit(nodes: (Node | string)[], exById: Record<string, any>): string {
  let out = "";
  for (let idx = 0; idx < nodes.length; idx++) {
    const n = nodes[idx];
    if (typeof n === "string") { out += escJa(n); continue; }
    // enrich the "kana(lê-se romaji)" pattern into a ruby (kana with the reading on top).
    if (n.name === "jp" && !n.attrs.reading) {
      const n1 = nodes[idx + 1], n2 = nodes[idx + 2], n3 = nodes[idx + 3];
      const t3 = nodeStr(n3);
      // n3 is a plain-text node beginning with ")" (it usually also carries the sentence's continuation)
      const n3Plain = typeof n3 === "string" || (!!n3 && typeof n3 !== "string" && n3.name === "text" && n3.children.every((c) => typeof c === "string"));
      if (/^\s*\(lê-se\s*$/.test(nodeStr(n1)) && nodeName(n2) === "romaji" && n3Plain && /^\s*\)/.test(t3)) {
        out += ruby(n.children.map((c) => (typeof c === "string" ? c : "")).join(""), nodeStr(n2).trim());
        out += escJa(t3.replace(/^\s*\)/, "")); // keep whatever follows the ")"
        idx += 3;
        continue;
      }
    }
    const kids = () => emit(n.children, exById);
    switch (n.name) {
      case "heading": out += `<h${n.attrs.level === "3" ? 3 : 2} class="ym-h${n.attrs.level === "3" ? 3 : 2}">${kids()}</h${n.attrs.level === "3" ? 3 : 2}>`; break;
      case "p": out += `<p class="ym-p">${kids()}</p>`; break;
      case "text": out += n.attrs.weight === "bold" ? `<strong>${kids()}</strong>` : kids(); break;
      case "emphasis": out += `<em>${kids()}</em>`; break;
      case "romaji": {
        // a pronounceable sound unit (e.g. the vowels a/i/u/e/o) -> a distinct, audio-ready chip (not italic)
        const t = n.children.map((c) => (typeof c === "string" ? c : "")).join("");
        out += `<span class="ym-say ym-say-romaji" data-say="${esc(t)}" lang="ja">${esc(t)}</span>`;
        break;
      }
      case "term": out += `<span class="ym-term" title="${esc(n.attrs.define || "")}">${kids()}</span>`; break;
      case "jp": out += ruby(n.children.map((c) => (typeof c === "string" ? c : "")).join(""), n.attrs.reading || ""); break;
      case "note": {
        const meta = NOTE[n.attrs.type] || { ic: "info", label: "Nota" };
        out += `<div class="ym-note ym-note-${esc(n.attrs.type || "info")}"><div class="ym-note-head">${msIcon(meta.ic)}<span>${esc(meta.label)}</span></div><div class="ym-note-body">${kids()}</div></div>`;
        break;
      }
      case "list": out += `<ul class="ym-list">${kids()}</ul>`; break;
      case "item": out += `<li class="ym-item">${kids()}</li>`; break;
      case "checklist": out += `<div class="ym-checklist"><div class="ym-checklist-head">${msIcon("checklist")}<span>O que você consegue fazer agora</span></div>${kids()}</div>`; break;
      case "check": out += `<div class="ym-check"><span class="material-symbols-rounded ym-check-ic" aria-hidden="true">check_circle</span><span class="ym-check-text">${kids()}</span></div>`; break;
      case "sentence": out += renderSentence(n.attrs.ref, n.attrs.mode || "featured"); break;
      case "reading": out += renderReading(n.attrs.ref, n.attrs.show || "furigana"); break;
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

const norm = (s: string) => s.replace(/<[^>]+>/g, "").replace(/\s+/g, " ").trim().toLowerCase();
function nodeText(n: Node | string): string {
  if (typeof n === "string") return n;
  return n.children.map(nodeText).join("");
}

/**
 * Render a lesson body (tagged source) to a display-HTML string. Server-only.
 * `dedupeTitle`: drop a leading <heading> that just repeats the page title (true for ~73% of lessons).
 */
export function renderBody(body: string, exercises: any[] = [], dedupeTitle?: string): string {
  const exById: Record<string, any> = {};
  for (const ex of exercises) if (ex?.id) exById[ex.id] = ex;
  let nodes = parse(body || "");
  if (dedupeTitle) {
    const firstIdx = nodes.findIndex((n) => typeof n !== "string" || n.trim() !== "");
    const first = nodes[firstIdx];
    if (first && typeof first !== "string" && first.name === "heading" && norm(nodeText(first)) === norm(dedupeTitle)) {
      nodes = nodes.slice(firstIdx + 1);
    }
  }
  return `<div class="ym-body">${emit(nodes, exById)}</div>`;
}
