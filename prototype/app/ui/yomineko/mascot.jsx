import React from 'react';

/* ============================================================
   YOMINEKO mascot + magical accents (SVG)
   Mystical elegant cat with a glowing grimoire & stars.
   Placeholder-quality but charming & on-brand. Parametric by theme.
   ============================================================ */

// --- Sparkle / four-point star ---
const Sparkle = ({ size = 16, color = "var(--star)", style }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill="none" style={style}>
    <path d="M12 0 C12.8 7 17 11.2 24 12 C17 12.8 12.8 17 12 24 C11.2 17 7 12.8 0 12 C7 11.2 11.2 7 12 0 Z" fill={color}/>
  </svg>
);

// --- A scatter of stars/sparkles used behind hero moments ---
const StarField = ({ children }) => (
  <div style={{ position:'relative' }}>
    <Sparkle size={14} color="var(--magic-2)" style={{ position:'absolute', top:'6%', left:'10%', opacity:.85 }}/>
    <Sparkle size={9}  color="var(--gold-bright)" style={{ position:'absolute', top:'18%', right:'14%', opacity:.9 }}/>
    <Sparkle size={11} color="var(--magic-1)" style={{ position:'absolute', bottom:'14%', left:'16%', opacity:.7 }}/>
    <Sparkle size={7}  color="var(--star)" style={{ position:'absolute', top:'40%', right:'8%', opacity:.8 }}/>
    <Sparkle size={6}  color="var(--magic-2)" style={{ position:'absolute', bottom:'30%', right:'20%', opacity:.6 }}/>
    {children}
  </div>
);

/* ------------------------------------------------------------
   The cat. A slender, mystical purple cat.
   poses: "reading" (with grimoire), "celebrate", "empty"/"sleep", "wave", "peek"
   `glow` toggles the grimoire/aura glow.
   ------------------------------------------------------------ */
const Yomineko = ({ pose = "reading", size = 160, glow = true }) => {
  const w = size, h = size;
  return (
    <svg width={w} height={h} viewBox="0 0 200 200" fill="none" xmlns="http://www.w3.org/2000/svg">
      <defs>
        <radialGradient id="ym-aura" cx="50%" cy="50%" r="50%">
          <stop offset="0%" stopColor="var(--magic-2)" stopOpacity="0.55"/>
          <stop offset="60%" stopColor="var(--magic-1)" stopOpacity="0.18"/>
          <stop offset="100%" stopColor="var(--magic-1)" stopOpacity="0"/>
        </radialGradient>
        <linearGradient id="ym-body" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stopColor="var(--magic-1)"/>
          <stop offset="100%" stopColor="var(--primary)"/>
        </linearGradient>
        <linearGradient id="ym-book" x1="0" y1="0" x2="1" y2="1">
          <stop offset="0%" stopColor="var(--gold-bright)"/>
          <stop offset="100%" stopColor="var(--gold)"/>
        </linearGradient>
        <radialGradient id="ym-page" cx="50%" cy="40%" r="70%">
          <stop offset="0%" stopColor="#FFFDF5"/>
          <stop offset="100%" stopColor="#F3E6C9"/>
        </radialGradient>
      </defs>

      {/* aura glow */}
      {glow && <circle cx="100" cy="105" r="92" fill="url(#ym-aura)"/>}

      {/* ---- tail (curving, with a star tip) ---- */}
      <path d="M62 150 C30 150 26 116 44 104 C52 98 64 102 62 114 C60 124 50 124 50 116"
            stroke="url(#ym-body)" strokeWidth="11" strokeLinecap="round" fill="none"/>
      <g>
        <Sparkle/>
      </g>
      <g transform="translate(40 96)"><path d="M6 0 C6.4 3.5 8.5 5.6 12 6 C8.5 6.4 6.4 8.5 6 12 C5.6 8.5 3.5 6.4 0 6 C3.5 5.6 5.6 3.5 6 0Z" fill="var(--gold-bright)"/></g>

      {/* ---- body ---- */}
      <path d="M66 168 C58 132 64 110 100 110 C136 110 142 132 134 168 C132 176 128 178 122 178 L78 178 C72 178 68 176 66 168 Z"
            fill="url(#ym-body)"/>
      {/* chest marking */}
      <path d="M100 120 C112 120 116 134 112 152 C108 166 92 166 88 152 C84 134 88 120 100 120 Z"
            fill="var(--magic-2)" opacity="0.45"/>

      {/* ---- paws ---- */}
      <ellipse cx="84" cy="176" rx="9" ry="6" fill="var(--magic-2)"/>
      <ellipse cx="116" cy="176" rx="9" ry="6" fill="var(--magic-2)"/>

      {/* ---- grimoire (reading pose) ---- */}
      {pose === "reading" && (
        <g>
          {glow && <ellipse cx="100" cy="158" rx="44" ry="20" fill="var(--magic-glow)"/>}
          <g transform="translate(64 140)">
            {/* book covers */}
            <path d="M0 6 C0 2 2 0 6 2 L36 12 L36 44 L6 34 C2 32 0 30 0 26 Z" fill="url(#ym-book)"/>
            <path d="M72 6 C72 2 70 0 66 2 L36 12 L36 44 L66 34 C70 32 72 30 72 26 Z" fill="url(#ym-book)"/>
            {/* pages */}
            <path d="M6 8 L36 17 L36 40 L6 31 Z" fill="url(#ym-page)"/>
            <path d="M66 8 L36 17 L36 40 L66 31 Z" fill="url(#ym-page)"/>
            {/* glowing rune on page */}
            <circle cx="36" cy="24" r="7" fill="none" stroke="var(--magic-1)" strokeWidth="1.4" opacity="0.85"/>
            <path d="M36 19 L36 29 M31 24 L41 24" stroke="var(--magic-1)" strokeWidth="1.4" opacity="0.85"/>
            <g transform="translate(30 -6)"><path d="M4 0 C4.3 2.4 5.6 3.7 8 4 C5.6 4.3 4.3 5.6 4 8 C3.7 5.6 2.4 4.3 0 4 C2.4 3.7 3.7 2.4 4 0Z" fill="var(--gold-bright)"/></g>
          </g>
        </g>
      )}

      {/* ---- head ---- */}
      <g>
        {/* ears */}
        <path d="M70 78 L60 50 L86 68 Z" fill="url(#ym-body)"/>
        <path d="M130 78 L140 50 L114 68 Z" fill="url(#ym-body)"/>
        <path d="M72 72 L67 57 L80 66 Z" fill="var(--magic-2)" opacity="0.7"/>
        <path d="M128 72 L133 57 L120 66 Z" fill="var(--magic-2)" opacity="0.7"/>
        {/* face */}
        <ellipse cx="100" cy="86" rx="40" ry="36" fill="url(#ym-body)"/>
        {/* little wizard mark / star on forehead */}
        <g transform="translate(94 58)"><path d="M6 0 C6.5 4 8 5.5 12 6 C8 6.5 6.5 8 6 12 C5.5 8 4 6.5 0 6 C4 5.5 5.5 4 6 0Z" fill="var(--gold-bright)"/></g>

        {/* eyes */}
        {pose === "sleep" || pose === "empty" ? (
          <g stroke="#1b1430" strokeWidth="3" strokeLinecap="round">
            <path d="M80 88 q8 6 16 0"/>
            <path d="M104 88 q8 6 16 0"/>
          </g>
        ) : (
          <g>
            <ellipse cx="88" cy="88" rx="7" ry="9" fill="#1b1430"/>
            <ellipse cx="112" cy="88" rx="7" ry="9" fill="#1b1430"/>
            <circle cx="90.5" cy="85" r="2.4" fill="#fff"/>
            <circle cx="114.5" cy="85" r="2.4" fill="#fff"/>
            {/* magic glints */}
            <circle cx="86" cy="91" r="1.3" fill="var(--magic-2)"/>
            <circle cx="110" cy="91" r="1.3" fill="var(--magic-2)"/>
          </g>
        )}

        {/* nose + mouth */}
        <path d="M97 97 L103 97 L100 101 Z" fill="var(--tertiary-container)"/>
        {pose === "celebrate" ? (
          <path d="M92 103 q8 8 16 0" stroke="#1b1430" strokeWidth="2.5" fill="none" strokeLinecap="round"/>
        ) : (
          <path d="M100 101 L100 104 M100 104 q-5 4 -9 1 M100 104 q5 4 9 1" stroke="#1b1430" strokeWidth="2" fill="none" strokeLinecap="round"/>
        )}

        {/* whiskers */}
        <g stroke="var(--magic-2)" strokeWidth="1.6" strokeLinecap="round" opacity="0.8">
          <path d="M70 95 L52 92"/><path d="M70 100 L53 102"/>
          <path d="M130 95 L148 92"/><path d="M130 100 L147 102"/>
        </g>

        {/* cheeks blush for celebrate */}
        {pose === "celebrate" && (
          <g fill="var(--tertiary)" opacity="0.4">
            <ellipse cx="76" cy="98" rx="6" ry="3.5"/>
            <ellipse cx="124" cy="98" rx="6" ry="3.5"/>
          </g>
        )}
      </g>

      {/* celebrate sparkles */}
      {pose === "celebrate" && (
        <g>
          <g transform="translate(40 60)"><Sparkle size={14} color="var(--gold-bright)"/></g>
          <g transform="translate(150 64)"><Sparkle size={12} color="var(--magic-2)"/></g>
          <g transform="translate(150 120)"><Sparkle size={9} color="var(--star)"/></g>
          <g transform="translate(36 116)"><Sparkle size={10} color="var(--magic-1)"/></g>
        </g>
      )}

      {/* wave paw */}
      {pose === "wave" && (
        <g>
          <ellipse cx="146" cy="120" rx="10" ry="13" fill="url(#ym-body)" transform="rotate(20 146 120)"/>
          <ellipse cx="150" cy="112" rx="6" ry="4" fill="var(--magic-2)"/>
        </g>
      )}

      {/* zzz for sleep */}
      {pose === "sleep" && (
        <g fill="var(--magic-2)" fontFamily="var(--font-display)">
          <text x="140" y="60" fontSize="16" fontWeight="700">z</text>
          <text x="152" y="48" fontSize="12" fontWeight="700">z</text>
        </g>
      )}
    </svg>
  );
};

/* --- Compact logo mark: cat head in a squircle with a star --- */
const YominekoLogo = ({ size = 40 }) => (
  <svg width={size} height={size} viewBox="0 0 48 48" fill="none" xmlns="http://www.w3.org/2000/svg">
    <defs>
      <linearGradient id="ym-logo-bg" x1="0" y1="0" x2="1" y2="1">
        <stop offset="0%" stopColor="var(--magic-1)"/>
        <stop offset="100%" stopColor="var(--primary)"/>
      </linearGradient>
    </defs>
    <rect x="2" y="2" width="44" height="44" rx="14" fill="url(#ym-logo-bg)"/>
    {/* ears */}
    <path d="M14 20 L10 9 L21 16 Z" fill="#fff"/>
    <path d="M34 20 L38 9 L27 16 Z" fill="#fff"/>
    {/* face */}
    <ellipse cx="24" cy="25" rx="14" ry="12" fill="#fff"/>
    {/* eyes */}
    <ellipse cx="19" cy="25" rx="2.4" ry="3" fill="var(--primary)"/>
    <ellipse cx="29" cy="25" rx="2.4" ry="3" fill="var(--primary)"/>
    {/* nose */}
    <path d="M22.5 29 L25.5 29 L24 31 Z" fill="var(--tertiary)"/>
    {/* forehead star */}
    <g transform="translate(20.5 15)"><path d="M3.5 0 C3.8 2.2 5.3 3.2 7 3.5 C5.3 3.8 3.8 5.3 3.5 7 C3.2 5.3 1.7 3.8 0 3.5 C1.7 3.2 3.2 2.2 3.5 0Z" fill="var(--gold-bright)"/></g>
  </svg>
);

/* --- Grimoire icon (used as the "magic" motif in headers, dividers) --- */
const GrimoireGlyph = ({ size = 28 }) => (
  <svg width={size} height={size} viewBox="0 0 32 32" fill="none">
    <path d="M5 6 C5 4 7 3 9 4 L16 7 L16 28 L9 25 C7 24 5 23 5 21 Z" fill="var(--gold)"/>
    <path d="M27 6 C27 4 25 3 23 4 L16 7 L16 28 L23 25 C25 24 27 23 27 21 Z" fill="var(--gold-bright)"/>
    <circle cx="16" cy="15" r="4" fill="none" stroke="var(--magic-1)" strokeWidth="1.3"/>
    <path d="M16 11 L16 19 M12 15 L20 15" stroke="var(--magic-1)" strokeWidth="1.3"/>
  </svg>
);

export { Sparkle, StarField, Yomineko, YominekoLogo, GrimoireGlyph };
