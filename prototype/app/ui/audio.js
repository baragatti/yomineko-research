/* ============================================================
   Japanese audio via the browser's built-in speech synthesis (ja-JP).
   Why not pre-rendered mp3: free keyless TTS endpoints (Google
   translate_tts, tts.quest, StreamElements) rate-limit bulk requests
   and return duplicate/placeholder clips — which produced the "same
   audio for everything" bug. The OS ja-JP voice gives correct, distinct
   pronunciation for every word/phrase, with no external runtime call.
   (For guaranteed offline mp3s, wire a paid TTS key — see README.)
   ============================================================ */

let jaVoice = null;

function pickVoice() {
  try {
    const vs = window.speechSynthesis.getVoices();
    jaVoice =
      vs.find((v) => /ja[-_]?JP/i.test(v.lang)) ||
      vs.find((v) => /^ja\b/i.test(v.lang)) ||
      vs.find((v) => /japanese|日本/i.test(v.name)) ||
      null;
  } catch { /* ignore */ }
}

if (typeof window !== 'undefined' && 'speechSynthesis' in window) {
  pickVoice();
  try { window.speechSynthesis.onvoiceschanged = pickVoice; } catch { /* ignore */ }
}

export function playAudio(text) {
  if (!text || typeof window === 'undefined' || !('speechSynthesis' in window)) return;
  try {
    const synth = window.speechSynthesis;
    synth.cancel(); // stop whatever is playing so each tap is its own clip
    if (!jaVoice) pickVoice();
    // spaces in our JP strings are only for furigana readability — drop them
    const u = new SpeechSynthesisUtterance(String(text).replace(/[\s　]+/g, ''));
    u.lang = 'ja-JP';
    u.rate = 0.9;
    if (jaVoice) u.voice = jaVoice;
    synth.speak(u);
  } catch { /* ignore */ }
}
