/* Moteur "Bonhomme Blanc" — animation minimaliste noir & blanc avec halo.
 * Rendu 100 % déterministe : draw(t) dessine l'image exacte de l'instant t.
 * Chargé dans Chromium par scripts/render.js. Aucune dépendance. */
(function () {
  'use strict';
  const FONT = '"Inter Display", Inter, "Helvetica Neue", Arial, sans-serif';
  const TAU = Math.PI * 2;
  let W = 1920, H = 1080, FPS = 30, SCENE = null, TOTAL = 0;
  let main, mc, layer, lc, small, sc2, small2, sc3, tiny, tc, grainTiles = [], dotsTile = null, FILTER_OK = true;
  const IMAGES = {};

  /* ---------- utilitaires ---------- */
  const clamp = (v, a = 0, b = 1) => Math.max(a, Math.min(b, v));
  const lerp = (a, b, k) => a + (b - a) * k;
  const EASE = {
    linear: k => k,
    in: k => k * k * k,
    out: k => 1 - Math.pow(1 - k, 3),
    inOut: k => (k < 0.5 ? 4 * k * k * k : 1 - Math.pow(-2 * k + 2, 3) / 2),
    outBack: k => 1 + 2.70158 * Math.pow(k - 1, 3) + 1.70158 * Math.pow(k - 1, 2),
    inExpo: k => (k <= 0 ? 0 : Math.pow(2, 10 * k - 10)),
    outExpo: k => (k >= 1 ? 1 : 1 - Math.pow(2, -10 * k)),
  };
  const ease = (n, k) => (EASE[n] || EASE.inOut)(clamp(k));
  function rng(seed) {
    let a = (seed * 2654435761) >>> 0;
    return () => {
      a = (a + 0x6d2b79f5) | 0;
      let t = Math.imul(a ^ (a >>> 15), 1 | a);
      t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
      return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
    };
  }
  /* Keyframes : [[t, valeur, "ease"?], ...] — t en secondes depuis le début de la scène. */
  const isKF = v => Array.isArray(v) && v.length > 0 &&
    v.every(i => Array.isArray(i) && typeof i[0] === 'number' && typeof i[1] === 'number');
  function kf(v, t) {
    if (!isKF(v)) return v;
    if (t <= v[0][0]) return v[0][1];
    for (let i = 1; i < v.length; i++) {
      if (t <= v[i][0]) {
        const a = v[i - 1], b = v[i];
        return lerp(a[1], b[1], ease(b[2] || 'inOut', (t - a[0]) / (b[0] - a[0] || 1e-6)));
      }
    }
    return v[v.length - 1][1];
  }
  /* Valeurs texte dans le temps (ex. pose) : [[0,"work"],[3.2,"cheer"]] — changement net. */
  const isSteps = v => Array.isArray(v) && v.length > 0 &&
    v.every(i => Array.isArray(i) && typeof i[0] === 'number' && typeof i[1] === 'string');
  const step = (v, t) => { let r = v[0][1]; for (const i of v) if (t >= i[0]) r = i[1]; return r; };
  const RAW = new Set(['points', 'bars', 'type', 'text', 'label', 'in', 'out']);
  function resolve(e, t) {
    const p = {};
    for (const k in e) p[k] = RAW.has(k) ? e[k] : isSteps(e[k]) ? step(e[k], t) : kf(e[k], t);
    return p;
  }
  const fmt = (v, p) => (p.prefix || '') + Number(v).toLocaleString(SCENE.locale || 'en-US', {
    minimumFractionDigits: p.decimals || 0, maximumFractionDigits: p.decimals || 0,
  }) + (p.suffix || '');
  function countValue(p, t) {
    if (p.value !== undefined) return typeof p.value === 'number' ? fmt(p.value, p) : String(p.value);
    const st = p.start ?? p.at ?? 0, d = p.dur ?? 2;
    return fmt(lerp(p.from ?? 0, p.to ?? 0, ease(p.ease || 'inOut', (t - st) / d)), p);
  }
  function caps(c, s, x, y, size, o = {}) {
    c.save();
    c.font = `${o.weight || 800} ${size}px ${FONT}`;
    c.letterSpacing = (o.spacing ?? 0.16) * size + 'px';
    c.textAlign = o.align || 'center'; c.textBaseline = o.base || 'middle';
    c.fillStyle = o.color || '#fff'; c.globalAlpha *= o.alpha ?? 1;
    if (o.glow) { c.shadowColor = 'rgba(255,255,255,.8)'; c.shadowBlur = o.glow; }
    c.fillText(String(s).toUpperCase(), x, y);
    c.restore();
  }
  const rr = (c, x, y, w, h, r) => { c.beginPath(); c.roundRect(x, y, w, h, r); };
  function halo(c, x, y, r, a) {
    const g = c.createRadialGradient(x, y, 0, x, y, r);
    g.addColorStop(0, `rgba(255,255,255,${a})`); g.addColorStop(1, 'rgba(255,255,255,0)');
    c.fillStyle = g; c.beginPath(); c.arc(x, y, r, 0, TAU); c.fill();
  }

  /* ---------- le bonhomme ---------- */
  /* Origine = pieds. Poses : stand, cheer, work, point, phone, sit, run, fallen. */
  function drawChar(c, p, t) {
    const pose = p.pose || 'stand', ghost = !!p.ghost;
    c.save();
    if (p.facing === -1) c.scale(-1, 1);
    if (p.ring !== false && pose !== 'fallen') {
      c.save(); c.strokeStyle = 'rgba(255,255,255,.45)'; c.lineWidth = 2; c.setLineDash([9, 7]);
      c.beginPath(); c.ellipse(0, 4, 92, 15, 0, 0, TAU); c.stroke(); c.restore();
    }
    const glow = p.glow ?? 0.6;
    if (glow > 0 && !ghost) halo(c, 0, -110, 280, 0.14 * glow);
    const breathe = Math.sin(t * 1.6 + (p.seed || 0)) * 1.5;
    if (p.shake) c.translate(Math.sin(t * 46) * p.shake, Math.cos(t * 39) * p.shake * 0.4);
    if (pose === 'fallen') { c.translate(-115, -66); c.rotate(Math.PI / 2); }
    if (pose === 'work') c.rotate(0.07);
    if (pose === 'run') c.rotate(0.2);
    if (pose === 'phone') c.rotate(0.16);
    c.lineCap = 'round'; c.lineJoin = 'round';
    c.fillStyle = '#fff'; c.strokeStyle = '#fff';
    if (!ghost) { c.shadowColor = 'rgba(255,255,255,.6)'; c.shadowBlur = 16 * glow; }
    const bodyH = pose === 'sit' ? 112 : 150;
    const body = () => {
      c.beginPath();
      if (p.dress) {
        c.moveTo(-112, 0); c.quadraticCurveTo(-58, -40, -34, -96); c.lineTo(-46, -bodyH + 46);
        c.arc(0, -bodyH + 46 + breathe, 46, Math.PI, 0);
        c.lineTo(34, -96); c.quadraticCurveTo(58, -40, 112, 0); c.closePath(); return;
      }
      c.moveTo(-68, 0); c.lineTo(-60, -bodyH + 60);
      c.arc(0, -bodyH + 60 + breathe, 60, Math.PI, 0);
      c.lineTo(68, 0); c.closePath();
    };
    const paint = () => { if (ghost) { c.lineWidth = 4; c.stroke(); } else c.fill(); };
    const arm = (x1, y1, x2, y2) => {
      c.lineWidth = ghost ? 4 : 30; c.beginPath(); c.moveTo(x1, y1); c.lineTo(x2, y2); c.stroke();
    };
    if (pose === 'sit') { c.save(); c.translate(0, -34); }
    if (p.dress && !ghost) {
      c.save(); c.shadowBlur = 0; c.fillStyle = 'rgba(255,255,255,.34)'; c.beginPath();
      c.moveTo(6, -bodyH - 78); c.quadraticCurveTo(-74, -bodyH - 70, -92, -bodyH + 30);
      c.quadraticCurveTo(-100, -90, -78, -50); c.lineTo(-40, -bodyH + 20); c.closePath(); c.fill();
      c.fillStyle = '#fff'; c.beginPath(); c.arc(-36, -bodyH - 62, 17, 0, TAU); c.fill(); c.restore();
    }
    body(); paint();
    c.beginPath(); c.arc(0, -bodyH - 36 + breathe, 40, 0, TAU); paint();
    if (pose === 'sit') {
      c.restore(); c.lineWidth = ghost ? 4 : 36;
      c.beginPath(); c.moveTo(0, -18); c.lineTo(86, -18); c.lineTo(86, 62); c.stroke();
    }
    const sy = -bodyH + 52;
    if (p.bowtie && !ghost) {
      c.save(); c.shadowBlur = 0; c.fillStyle = '#000'; const by = -bodyH + 20;
      c.beginPath(); c.moveTo(0, by); c.lineTo(-20, by - 12); c.lineTo(-20, by + 12); c.closePath();
      c.moveTo(0, by); c.lineTo(20, by - 12); c.lineTo(20, by + 12); c.closePath(); c.fill(); c.restore();
    }
    if (p.book) {
      c.save(); c.shadowBlur = 0; c.fillStyle = '#bdbdbd'; c.strokeStyle = '#000'; c.lineWidth = 3;
      c.translate(0, -bodyH + 84);
      c.beginPath(); c.moveTo(0, -18); c.lineTo(-46, -26); c.lineTo(-46, 16); c.lineTo(0, 24); c.lineTo(46, 16); c.lineTo(46, -26); c.closePath();
      c.fill(); c.stroke(); c.beginPath(); c.moveTo(0, -18); c.lineTo(0, 24); c.stroke(); c.restore();
    }
    if (pose === 'cheer') {
      const w = Math.sin(t * 9) * 0.07;
      arm(-44, sy, -44 - 96 * Math.cos(0.85 + w), sy - 96 * Math.sin(0.85 + w));
      arm(44, sy, 44 + 96 * Math.cos(0.85 - w), sy - 96 * Math.sin(0.85 - w));
    } else if (pose === 'work') {
      arm(30, sy + 2, 205, sy - 22 + Math.sin(t * 14) * 3);
    } else if (pose === 'point') {
      arm(40, sy, 150, sy - 82 + Math.sin(t * 3) * 4);
    } else if (pose === 'phone') {
      arm(34, sy + 6, 96, sy - 52);
      c.save(); c.translate(104, sy - 86); c.rotate(0.25); c.shadowBlur = 30;
      rr(c, -24, -40, 48, 80, 8); c.fillStyle = '#dcdcdc'; c.fill(); c.restore();
    } else if (pose === 'worry') {
      c.lineWidth = 24; const j = Math.sin(t * 20) * 2;
      c.beginPath(); c.moveTo(-40, sy + 6); c.lineTo(-34, sy - 30); c.lineTo(-12 + j, -bodyH - 6); c.stroke();
      c.beginPath(); c.moveTo(40, sy + 6); c.lineTo(34, sy - 30); c.lineTo(12 + j, -bodyH - 6); c.stroke();
    } else if (pose === 'refuse') {
      arm(40, sy, 138, sy - 16); c.beginPath(); c.arc(150, sy - 22, 25, 0, TAU); c.fill();
    } else if (pose === 'give') {
      arm(40, sy + 6, 128, sy + 16);
      c.save(); c.translate(150, sy - 6); c.shadowBlur = 24;
      rr(c, -20, 0, 40, 26, 4); c.fill(); c.lineWidth = 5; c.beginPath(); c.arc(0, -16, 11, 0, TAU); c.stroke();
      c.beginPath(); c.moveTo(-7, -30); c.lineTo(0, -40); c.lineTo(7, -30); c.closePath(); c.fill(); c.restore();
    } else if (pose === 'run') {
      arm(30, sy + 6, 92, sy + 44); c.shadowBlur = 0;
      c.lineWidth = 3; c.globalAlpha *= 0.6;
      for (let i = 0; i < 3; i++) {
        const o = ((t * 2.2 + i * 0.37) % 1) * 60;
        c.beginPath(); c.moveTo(-110 - o, -150 + i * 46); c.lineTo(-190 - o - i * 24, -150 + i * 46); c.stroke();
      }
    }
    if (p.marks && pose !== 'fallen') {
      c.save(); c.shadowBlur = 8; c.strokeStyle = '#fff'; c.lineCap = 'round'; c.globalAlpha *= 0.9;
      const my = -bodyH - 96, pulse = 1 + Math.sin(t * 10) * 0.12;
      if (p.marks === 'shock' || p.marks === 'joy') {
        c.lineWidth = 6; const n = p.marks === 'joy' ? 3 : 5;
        for (let i = 0; i < n; i++) {
          const a = -Math.PI / 2 + (i - (n - 1) / 2) * 0.42, r1 = 62 * pulse, r2 = (p.marks === 'joy' ? 90 : 100) * pulse;
          c.beginPath(); c.moveTo(Math.cos(a) * r1, my + 96 - 36 + Math.sin(a) * r1); c.lineTo(Math.cos(a) * r2, my + 96 - 36 + Math.sin(a) * r2); c.stroke();
        }
      } else if (p.marks === 'sweat') {
        c.fillStyle = '#fff';
        for (let i = 0; i < 2; i++) {
          const f = (t * 0.9 + i * 0.5) % 1;
          c.save(); c.translate(52 + i * 20, my + 30 + f * 46); c.globalAlpha *= 1 - f;
          c.beginPath(); c.moveTo(0, -13); c.quadraticCurveTo(11, 6, 0, 10); c.quadraticCurveTo(-11, 6, 0, -13); c.fill(); c.restore();
        }
      } else if (p.marks === 'scribble') {
        c.lineWidth = 4; c.beginPath();
        for (let i = 0; i < 70; i++) {
          const a = i * 0.42 + t * 5, r = 10 + i * 0.36;
          c.lineTo(Math.cos(a) * r * 1.5, my - 18 + Math.sin(a) * r * 0.6 + i * 0.2);
        }
        c.stroke();
      }
      c.restore();
    }
    c.restore();
  }

  /* ---------- pictogrammes (boîte 100×100 centrée) ---------- */
  function drawIcon(c, name, p, t) {
    c.lineWidth = p.stroke || 7; c.lineCap = 'round'; c.lineJoin = 'round';
    c.strokeStyle = '#fff'; c.fillStyle = '#fff';
    const L = (...a) => { c.beginPath(); c.moveTo(a[0], a[1]); for (let i = 2; i < a.length; i += 2) c.lineTo(a[i], a[i + 1]); };
    switch (name) {
      case 'lock': case 'unlock':
        c.beginPath();
        if (name === 'lock') { c.moveTo(-22, -6); c.lineTo(-22, -24); c.arc(0, -24, 22, Math.PI, 0); c.lineTo(22, -6); }
        else { c.moveTo(-22, -10); c.lineTo(-22, -32); c.arc(0, -32, 22, Math.PI, 0); c.lineTo(22, -24); }
        c.stroke(); rr(c, -36, -8, 72, 56, 10); c.fill();
        c.fillStyle = '#000'; c.beginPath(); c.arc(0, 14, 7, 0, TAU); c.fill(); c.fillRect(-3, 16, 6, 16); break;
      case 'warning':
        L(0, -44, 48, 40, -48, 40); c.closePath(); c.stroke();
        L(0, -14, 0, 12); c.stroke(); c.beginPath(); c.arc(0, 26, 4.5, 0, TAU); c.fill(); break;
      case 'check':
        c.beginPath(); c.arc(0, 0, 42, 0, TAU); c.fill();
        c.strokeStyle = '#000'; c.lineWidth = 9; L(-18, 2, -5, 16, 20, -14); c.stroke(); break;
      case 'cross':
        c.beginPath(); c.arc(0, 0, 42, 0, TAU); c.stroke(); L(-16, -16, 16, 16); c.stroke(); L(16, -16, -16, 16); c.stroke(); break;
      case 'clock': {
        c.beginPath(); c.arc(0, 0, 42, 0, TAU); c.fill(); c.strokeStyle = '#000'; c.lineWidth = 6;
        const a = (p.speed ?? 1) * t * 2;
        L(0, 0, Math.sin(a) * 28, -Math.cos(a) * 28); c.stroke();
        L(0, 0, Math.sin(a / 12) * 18, -Math.cos(a / 12) * 18); c.stroke(); break;
      }
      case 'briefcase':
        rr(c, -42, -22, 84, 60, 8); c.fill(); c.lineWidth = 8; rr(c, -18, -40, 36, 22, 6); c.stroke(); break;
      case 'play':
        c.beginPath(); c.arc(0, 0, 42, 0, TAU); c.fill(); c.fillStyle = '#000';
        L(-12, -20, 22, 0, -12, 20); c.closePath(); c.fill(); break;
      case 'dollar':
        c.save(); c.setLineDash([10, 9]); c.lineWidth = 4; c.beginPath(); c.arc(0, 0, 44, 0, TAU); c.stroke(); c.restore();
        c.font = `800 52px ${FONT}`; c.textAlign = 'center'; c.textBaseline = 'middle'; c.fillText('$', 0, 3); break;
      case 'search':
        c.beginPath(); c.arc(-8, -8, 28, 0, TAU); c.stroke(); L(14, 14, 40, 40); c.stroke(); break;
      case 'battery': {
        rr(c, -46, -24, 84, 48, 8); c.lineWidth = 5; c.stroke(); c.fillRect(42, -10, 8, 20);
        const n = Math.round(clamp(p.level ?? 1) * 4);
        for (let i = 0; i < n; i++) c.fillRect(-38 + i * 18, -16, 13, 32); break;
      }
      case 'people':
        for (const [x, s] of [[-34, 0.75], [34, 0.75], [0, 1]]) {
          c.beginPath(); c.arc(x, -14 * s, 13 * s, 0, TAU); c.fill();
          c.beginPath(); c.moveTo(x - 20 * s, 38); c.lineTo(x - 20 * s, 18 * s + 6);
          c.arc(x, 18 * s + 6, 20 * s, Math.PI, 0); c.lineTo(x + 20 * s, 38); c.closePath(); c.fill();
        } break;
      case 'city':
        c.lineWidth = 4; [[-44, -10, 24], [-16, -42, 26], [14, -24, 28]].forEach(([x, y, w]) => { c.strokeRect(x, y, w, 40 - y); });
        L(-50, 40, 50, 40); c.stroke(); break;
      case 'arrow': L(0, 40, 0, -38); c.stroke(); L(-26, -12, 0, -40, 26, -12); c.stroke(); break;
      case 'heart':
        c.beginPath(); c.moveTo(0, 38); c.bezierCurveTo(-60, -4, -34, -50, 0, -18); c.bezierCurveTo(34, -50, 60, -4, 0, 38); c.fill(); break;
      case 'star':
        c.beginPath();
        for (let i = 0; i < 10; i++) { const r = i % 2 ? 19 : 46, a = -Math.PI / 2 + i * Math.PI / 5; c.lineTo(Math.cos(a) * r, Math.sin(a) * r); }
        c.closePath(); c.fill(); break;
      case 'ring':
        c.lineWidth = 9; c.beginPath(); c.arc(0, 14, 28, 0, TAU); c.stroke();
        c.beginPath(); c.moveTo(-16, -26); c.lineTo(-8, -40); c.lineTo(8, -40); c.lineTo(16, -26); c.lineTo(0, -10); c.closePath(); c.fill(); break;
      case 'flower':
        for (let i = 0; i < 5; i++) { const a = -Math.PI / 2 + i * TAU / 5; c.beginPath(); c.arc(Math.cos(a) * 24, Math.sin(a) * 24, 18, 0, TAU); c.lineWidth = 5; c.stroke(); }
        c.beginPath(); c.arc(0, 0, 9, 0, TAU); c.fill(); break;
      case 'bulb':
        c.beginPath(); c.arc(0, -10, 30, 0, TAU); c.fill(); rr(c, -14, 22, 28, 20, 5); c.fill(); break;
      default:
        c.beginPath(); c.arc(0, 0, 40, 0, TAU); c.stroke();
    }
  }

  /* ---------- éléments ---------- */
  const DRAW = {
    text(c, p) {
      const size = p.size || 120, lines = String(p.text ?? '').split('\n');
      const shown = p._type !== undefined ? Math.ceil(p._type * String(p.text).length) : Infinity;
      c.font = `${p.weight || 900} ${size}px ${FONT}`;
      c.letterSpacing = (p.spacing ?? 0.05) * size + 'px';
      c.textAlign = p.align || 'center'; c.textBaseline = 'middle';
      c.fillStyle = p.color || '#fff';
      c.shadowColor = 'rgba(255,255,255,.7)'; c.shadowBlur = (p.glow ?? 1) * size * 0.1;
      let used = 0;
      lines.forEach((l, i) => {
        let s = p.upper === false ? l : l.toUpperCase();
        if (used + s.length > shown) s = s.slice(0, Math.max(0, shown - used));
        used += l.length + 1;
        const y = (i - (lines.length - 1) / 2) * size * 1.12;
        c.fillText(s, 0, y);
      });
    },
    caption(c, p) { DRAW.text(c, { size: 34, weight: 800, spacing: 0.2, glow: 0.5, ...p }); },
    counter(c, p, t) {
      const size = p.size || 96;
      if (p.label) caps(c, p.label, 0, -size * 0.72, size * 0.24, { spacing: 0.22, alpha: 0.85 });
      c.font = `800 ${size}px ${FONT}`; c.textAlign = 'center'; c.textBaseline = 'middle';
      c.fillStyle = '#fff'; c.shadowColor = 'rgba(255,255,255,.7)'; c.shadowBlur = size * 0.1;
      c.letterSpacing = size * 0.02 + 'px';
      c.fillText(countValue(p, t), 0, 0);
    },
    character(c, p, t) { drawChar(c, p, t); },
    /* Bonhomme + bureau + écran déjà alignés. Origine = pieds du bonhomme. */
    workstation(c, p, t, lt) {
      c.save(); c.translate(118, 0); DRAW.desk(c, { w: 400, h: 132 }); c.restore();
      c.save(); c.translate(318, -132 - 33 - 96); DRAW.monitor(c, { ...p, w: 300, h: 192, content: p.content || 'editor' }, t, lt); c.restore();
      drawChar(c, { ...p, pose: p.pose || 'work' }, t);
    },
    ground(c, p) {
      c.strokeStyle = 'rgba(255,255,255,.42)'; c.lineWidth = 2; c.setLineDash(p.solid ? [] : [16, 11]);
      c.beginPath(); c.moveTo(-W * 2, 0); c.lineTo(W * 3, 0); c.stroke();
    },
    spotlight(c, p) {
      const top = -p.y - 40, tw = p.topWidth || 110, bw = p.width || 440, k = p.power ?? 1;
      const g = c.createLinearGradient(0, top, 0, 0);
      g.addColorStop(0, `rgba(255,255,255,${0.15 * k})`); g.addColorStop(1, `rgba(255,255,255,${0.035 * k})`);
      c.fillStyle = g; c.beginPath();
      c.moveTo(-tw / 2, top); c.lineTo(tw / 2, top); c.lineTo(bw / 2, 0); c.lineTo(-bw / 2, 0); c.closePath(); c.fill();
      c.save(); c.scale(1, 0.12); halo(c, 0, 0, bw * 0.75, 0.22 * k); c.restore();
    },
    desk(c, p) {
      const w = p.w || 430, h = p.h || 150;
      c.strokeStyle = '#fff'; c.lineWidth = 4; c.shadowColor = 'rgba(255,255,255,.6)'; c.shadowBlur = 10;
      c.strokeRect(0, -h, w, 14);
      c.beginPath(); c.moveTo(12, -h + 14); c.lineTo(12, 0); c.moveTo(w - 12, -h + 14); c.lineTo(w - 12, 0); c.stroke();
    },
    monitor(c, p, t, lt) {
      const w = p.w || 340, h = p.h || 210, kind = p.content || 'editor';
      halo(c, 0, 0, w * 0.95, 0.1 * (p.glow ?? 1));
      if (p.stand !== false) {
        c.fillStyle = '#9a9a9a'; c.fillRect(-10, h / 2, 20, 26); c.fillRect(-52, h / 2 + 24, 104, 7);
      }
      rr(c, -w / 2, -h / 2, w, h, 12); c.fillStyle = '#0a0a0a'; c.fill();
      c.save(); c.strokeStyle = '#fff'; c.lineWidth = 5; c.shadowColor = '#fff'; c.shadowBlur = 16 * (p.glow ?? 1); c.stroke(); c.restore();
      c.save(); rr(c, -w / 2 + 5, -h / 2 + 5, w - 10, h - 10, 8); c.clip();
      if (kind === 'editor') {
        c.fillStyle = '#2b2b2b'; c.fillRect(-w * 0.28, -h * 0.4, w * 0.56, h * 0.38);
        c.save(); c.translate(0, -h * 0.21); c.scale(0.36, 0.36); drawIcon(c, 'play', {}, t); c.restore();
        const r = rng(p.seed || 7);
        for (let row = 0; row < 3; row++) {
          let x = -w * 0.44 + r() * 30;
          while (x < w * 0.42) {
            const bw = 22 + r() * 60, g = Math.round(110 + r() * 145);
            c.fillStyle = `rgb(${g},${g},${g})`; c.fillRect(x, h * 0.07 + row * h * 0.13, Math.min(bw, w * 0.44 - x), h * 0.085);
            x += bw + 6 + r() * 16;
          }
        }
        const px = -w * 0.4 + ((t * 0.09) % 1) * w * 0.8;
        c.fillStyle = '#fff'; c.fillRect(px - 1.5, h * 0.03, 3, h * 0.42);
        c.beginPath(); c.moveTo(px - 7, h * 0.02); c.lineTo(px + 7, h * 0.02); c.lineTo(px, h * 0.07); c.fill();
      } else if (kind === 'code') {
        const r = rng(p.seed || 3), n = 9, shown = (lt * 5) % (n + 4);
        for (let i = 0; i < n; i++) {
          const ind = Math.floor(r() * 3) * 22, len = 50 + r() * (w * 0.55);
          if (i < shown) {
            c.fillStyle = i % 3 ? '#bdbdbd' : '#fff';
            c.fillRect(-w * 0.4 + ind, -h * 0.38 + i * h * 0.088, len * clamp(shown - i), 6);
          }
        }
      } else if (kind === 'value') {
        if (p.label) caps(c, p.label, 0, -h * 0.2, h * 0.075, { spacing: 0.2, alpha: 0.8 });
        c.font = `800 ${h * 0.24}px ${FONT}`; c.textAlign = 'center'; c.textBaseline = 'middle';
        c.fillStyle = '#fff'; c.shadowColor = '#fff'; c.shadowBlur = 14;
        c.fillText(countValue(p, t), 0, h * 0.04);
        if (p.loading) {
          c.strokeStyle = '#fff'; c.lineWidth = 3; c.beginPath();
          c.arc(0, h * 0.3, 9, t * 6, t * 6 + 4.2); c.stroke();
        }
      } else if (kind === 'play') {
        c.fillStyle = '#242424'; c.fillRect(-w / 2, -h / 2, w, h);
        c.save(); c.scale(h / 210, h / 210); drawIcon(c, 'play', {}, t); c.restore();
      } else if (kind === 'image' && IMAGES[p.src]) {
        drawCover(c, IMAGES[p.src], -w / 2, -h / 2, w, h, p);
      }
      c.restore();
    },
    progress(c, p) {
      const w = p.w || 640, h = p.h || 28, v = clamp(p.value ?? 0);
      if (p.label) caps(c, p.label, -w / 2, -h / 2 - 20, 17, { align: 'left', spacing: 0.2 });
      if (p.percent !== false) caps(c, Math.round(v * 100) + '%', w / 2, -h / 2 - 20, 17, { align: 'right', spacing: 0.1 });
      rr(c, -w / 2, -h / 2, w, h, h / 2); c.strokeStyle = 'rgba(255,255,255,.75)'; c.lineWidth = 3; c.stroke();
      if (v > 0.01) {
        c.save(); c.shadowColor = '#fff'; c.shadowBlur = 18; c.fillStyle = '#fff';
        rr(c, -w / 2 + 5, -h / 2 + 5, Math.max(h - 10, (w - 10) * v), h - 10, (h - 10) / 2); c.fill(); c.restore();
      }
      if (p.tag) caps(c, p.tag, w / 2 + 26, 0, 15, { align: 'left', alpha: 0.6 });
    },
    chart(c, p, t) {
      const w = p.w || 700, h = p.h || 420;
      c.strokeStyle = 'rgba(255,255,255,.85)'; c.lineWidth = 3;
      c.beginPath(); c.moveTo(0, -h); c.lineTo(0, 0); c.lineTo(w, 0); c.stroke();
      if (p.title) caps(c, p.title, 0, -h - 22, 22, { align: 'left', spacing: 0.2 });
      const bars = p.bars || [], reveal = p.reveal ?? bars.length, grow = p.grow ?? 1;
      bars.forEach((b, i) => {
        const k = clamp(reveal - i); if (k <= 0) return;
        const cx = w * (i + 0.5) / bars.length + (bars.length > 1 ? 0 : 0), bw = Math.min(110, w / bars.length * 0.45);
        const bh = Math.max(7, (b.value || 0) * h * 0.85 * grow);
        c.save(); c.globalAlpha *= k; c.fillStyle = '#fff'; c.shadowColor = '#fff'; c.shadowBlur = 14;
        rr(c, cx - bw / 2, -bh, bw, bh, 3); c.fill(); c.restore();
        c.save(); c.globalAlpha *= k;
        if (b.text) { c.font = `800 46px ${FONT}`; c.textAlign = 'center'; c.fillStyle = '#fff'; c.letterSpacing = '4px'; c.fillText(b.text, cx, -bh - 26); }
        if (b.label) caps(c, b.label, cx, 40, 22, { spacing: 0.2 });
        c.restore();
      });
      if (p.saw) {
        const n = 6, tw = w * 0.11, th = h * 0.11, len = clamp(p.saw) * n;
        c.strokeStyle = 'rgba(255,255,255,.6)'; c.lineWidth = 3; c.beginPath(); c.moveTo(0, 0);
        for (let i = 0; i < n; i++) {
          const k = clamp(len - i); if (k <= 0) break;
          c.lineTo(tw * (i + k), -th * k); if (k >= 1) c.lineTo(tw * (i + 1), 0);
        }
        c.stroke();
      }
      if (p.curve) {
        const pr = clamp(p.curve), K = 5.5, f = k => (Math.exp(K * k) - 1) / (Math.exp(K) - 1);
        c.save(); c.strokeStyle = '#fff'; c.lineWidth = 6; c.lineCap = 'round'; c.shadowColor = '#fff'; c.shadowBlur = 18;
        c.beginPath();
        for (let i = 0; i <= 80; i++) { const k = pr * i / 80; c.lineTo(k * w * 0.72, -f(k) * h * 0.92); }
        c.stroke(); c.restore();
        if (p.rider !== false) {
          c.save(); c.translate(pr * w * 0.72, -f(pr) * h * 0.92); c.scale(0.3, 0.3);
          halo(c, 0, -100, 420, 0.5); drawChar(c, { pose: pr > 0.5 ? 'cheer' : 'stand', ring: false, glow: 1 }, t); c.restore();
        }
      }
    },
    stairs(c, p, t) {
      const n = p.steps || 7, sw = p.stepW || 110, sh = p.stepH || 62, lead = p.lead ?? 150;
      const pts = [[0, 0], [lead, 0]];
      for (let i = 1; i <= n; i++) { pts.push([lead + (i - 1) * sw, -i * sh]); pts.push([lead + i * sw, -i * sh]); }
      DRAW.line(c, { points: pts, progress: p.progress ?? 1, width: 3 });
      if (p.climber !== undefined) {
        const pos = i => (i <= 0 ? [lead - 60, 0] : [lead + (i - 0.5) * sw, -i * sh]);
        const v = clamp(p.climber, 0, n), i = Math.floor(v), f = v - i;
        const a = pos(i), b = pos(Math.min(n, i + 1));
        c.save(); c.translate(lerp(a[0], b[0], f), lerp(a[1], b[1], f) - Math.sin(f * Math.PI) * 34);
        c.scale(0.3, 0.3); drawChar(c, { pose: 'stand', ring: false, glow: 1 }, t); c.restore();
      }
    },
    icon(c, p, t) {
      const s = (p.size || 140) / 100;
      c.save(); c.scale(s, s); c.shadowColor = '#fff'; c.shadowBlur = 14 * (p.glow ?? 1);
      drawIcon(c, p.name, p, t); c.restore();
      if (p.label) caps(c, p.label, 0, (p.size || 140) * 0.5 + 30, 22, { spacing: 0.22 });
    },
    card(c, p, t) {
      const w = p.w || 190, h = p.h || 190;
      rr(c, -w / 2, -h / 2, w, h, p.r ?? 14); c.fillStyle = '#080808'; c.fill();
      c.save(); c.strokeStyle = '#fff'; c.lineWidth = 3.5; c.shadowColor = '#fff'; c.shadowBlur = 12; c.stroke(); c.restore();
      if (p.icon) { c.save(); c.translate(0, -h * 0.12); const s = h * 0.42 / 100; c.scale(s, s); drawIcon(c, p.icon, p, t); c.restore(); }
      if (p.label) caps(c, p.label, 0, h * 0.2, 17, { spacing: 0.22 });
      if (p.tag) {
        c.font = `800 14px ${FONT}`; const tw = c.measureText(p.tag.toUpperCase()).width + 44;
        c.fillStyle = '#fff'; rr(c, -tw / 2, h * 0.3, tw, 26, 3); c.fill();
        caps(c, p.tag, 0, h * 0.3 + 14, 14, { color: '#000', spacing: 0.2 });
      }
    },
    bubble(c, p) {
      const size = p.size || 22; c.font = `800 ${size}px ${FONT}`; c.letterSpacing = size * 0.18 + 'px';
      const txt = String(p.text ?? '...').toUpperCase(), w = c.measureText(txt).width + size * 2, h = size * 2.2;
      c.strokeStyle = '#fff'; c.lineWidth = 3; c.fillStyle = '#050505';
      rr(c, -w / 2, -h / 2, w, h, h * 0.42); c.fill(); c.stroke();
      if (p.tail !== 'none') {
        const d = p.tail === 'right' ? -1 : 1;
        c.beginPath(); c.moveTo(-d * w * 0.18, h / 2 - 1); c.lineTo(-d * w * 0.3, h / 2 + 15); c.lineTo(-d * w * 0.02, h / 2 - 1);
        c.fill(); c.stroke();
        c.fillRect(-d * w * 0.18 - (d < 0 ? 0 : -2) - (d > 0 ? 0 : w * 0.16), h / 2 - 4, w * 0.14, 4);
      }
      caps(c, txt, 0, 1, size, { spacing: 0.18 });
    },
    rings(c, p, t) {
      const n = p.count || 3, R = p.maxR || 320;
      c.lineWidth = p.width || 2;
      for (let i = 0; i < n; i++) {
        const f = p.static ? (i + 1) / n : ((t / (p.period || 2.4) + i / n) % 1);
        c.strokeStyle = `rgba(255,255,255,${p.static ? 0.28 : (1 - f) * 0.5})`;
        c.beginPath(); c.arc(0, 0, Math.max(1, f * R), 0, TAU); c.stroke();
      }
    },
    money(c, p, t) {
      const r = rng(p.seed || 11);
      if ((p.mode || 'rain') === 'pile') {
        const rows = p.rows || 8, tw = 46, th = 30, g = 4, tiles = [];
        for (let row = 0; row < rows; row++) {
          const n = (rows - row) * 2 - 1;
          for (let i = 0; i < n; i++) tiles.push([(i - (n - 1) / 2) * (tw + g), -row * (th + g) - th]);
        }
        const shown = clamp(p.progress ?? 1) * tiles.length;
        c.save(); c.scale(1, 0.1); halo(c, 0, 0, rows * (tw + g) * 1.3, 0.3 * clamp(p.progress ?? 1)); c.restore();
        tiles.forEach(([x, y], i) => {
          const k = clamp(shown - i); if (k <= 0) return;
          c.save(); c.translate(x, y + th / 2 - (1 - k) * 40); c.globalAlpha *= k;
          rr(c, -tw / 2, -th / 2, tw, th, 4); c.fillStyle = '#ececec'; c.fill();
          c.fillStyle = '#111'; c.font = `800 19px ${FONT}`; c.textAlign = 'center'; c.textBaseline = 'middle';
          c.fillText(p.symbol || '$', 0, 1); c.restore();
        });
      } else {
        const w = p.w || 800, h = p.h || 700, n = Math.round((p.count || 40) * clamp(p.intensity ?? 1));
        for (let i = 0; i < n; i++) {
          const bx = r() * w, sp = 260 + r() * 320, ph = r() * (h + 120), rs = (r() - 0.5) * 7, sway = r() * 6;
          const y = ((t * sp + ph) % (h + 120)) - 60, g = Math.round(150 + r() * 105);
          c.save(); c.translate(bx + Math.sin(t * 2 + sway) * 26, y); c.rotate(t * rs + sway);
          c.globalAlpha *= clamp((h - y) / 120) * clamp((y + 60) / 80);
          c.fillStyle = `rgb(${g},${g},${g})`; rr(c, -22, -12, 44, 24, 3); c.fill();
          c.fillStyle = 'rgba(0,0,0,.45)'; c.beginPath(); c.arc(0, 0, 6, 0, TAU); c.fill(); c.restore();
        }
      }
    },
    tiles(c, p) {
      const n = p.count || 7, cols = p.cols || n, w = p.w || 74, h = p.h || 58, g = p.gap ?? 16;
      const pr = p.progress ?? n, tw = cols * w + (cols - 1) * g;
      for (let i = 0; i < n; i++) {
        const x = -tw / 2 + (i % cols) * (w + g), y = Math.floor(i / cols) * (h + g), k = clamp(pr - i);
        if (p.hideEmpty && k <= 0) continue;
        c.save(); c.translate(x + w / 2, y + h / 2); const s = k > 0 && k < 1 ? 1 + (1 - k) * 0.25 : 1; c.scale(s, s);
        rr(c, -w / 2, -h / 2, w, h, 4);
        c.fillStyle = `rgba(255,255,255,${0.1 + 0.16 * k})`; c.fill();
        c.strokeStyle = `rgba(255,255,255,${0.45 + 0.5 * k})`; c.lineWidth = 2.5; c.stroke();
        c.fillStyle = 'rgba(255,255,255,.5)'; c.fillRect(-w / 2, -h / 2, w, 7);
        if (i === p.highlight) halo(c, 0, 0, w * 1.6, 0.55);
        if (k > 0 && p.text !== '') {
          c.globalAlpha *= k; c.font = `800 ${h * 0.36}px ${FONT}`; c.textAlign = 'center'; c.textBaseline = 'middle';
          c.fillStyle = '#fff'; c.letterSpacing = '2px'; c.fillText(p.text ?? '$0', 0, 5);
        }
        c.restore();
      }
    },
    crowd(c, p, t) {
      const n = p.count || 10, g = p.gap || 80, s = p.size || 0.26;
      for (let i = 0; i < n; i++) {
        c.save(); c.translate((i - (n - 1) / 2) * g, 0); c.scale(s, s);
        drawChar(c, { pose: p.pose || 'stand', ring: false, glow: 0, seed: i, marks: p.marks }, t); c.restore();
      }
    },
    window(c, p) {
      const w = p.w || 200, h = p.h || 200;
      c.strokeStyle = 'rgba(255,255,255,.8)'; c.lineWidth = 4; c.strokeRect(-w / 2, -h / 2, w, h);
      c.beginPath(); c.moveTo(0, -h / 2); c.lineTo(0, h / 2); c.moveTo(-w / 2, 0); c.lineTo(w / 2, 0); c.stroke();
      if (p.moon !== false) {
        c.save(); c.translate(w * 0.24, -h * 0.24); c.fillStyle = '#ddd'; c.shadowColor = '#fff'; c.shadowBlur = 16;
        c.beginPath(); c.arc(0, 0, 15, 0.6, 0.6 + Math.PI * 1.2); c.arc(7, -4, 13, 0.6 + Math.PI * 1.1, 0.75, true); c.fill(); c.restore();
      }
    },
    image(c, p) {
      const w = p.w || 520, h = p.h || 320, img = IMAGES[p.src];
      c.save(); rr(c, -w / 2, -h / 2, w, h, p.r ?? 12); c.clip();
      c.fillStyle = '#111'; c.fillRect(-w / 2, -h / 2, w, h);
      if (img) drawCover(c, img, -w / 2, -h / 2, w, h, p);
      c.restore();
      if (p.frame !== false) {
        rr(c, -w / 2, -h / 2, w, h, p.r ?? 12); c.strokeStyle = '#fff'; c.lineWidth = 4;
        c.shadowColor = '#fff'; c.shadowBlur = 16; c.stroke();
      }
    },
    line(c, p) {
      const pts = p.points || [], pr = clamp(p.progress ?? 1);
      let total = 0; const seg = [];
      for (let i = 1; i < pts.length; i++) { const d = Math.hypot(pts[i][0] - pts[i - 1][0], pts[i][1] - pts[i - 1][1]); seg.push(d); total += d; }
      let left = total * pr;
      c.strokeStyle = '#fff'; c.lineWidth = p.width || 4; c.lineJoin = 'round'; c.lineCap = 'round';
      if (p.dash) c.setLineDash([14, 10]);
      c.shadowColor = '#fff'; c.shadowBlur = 8;
      c.beginPath(); if (pts.length) c.moveTo(pts[0][0], pts[0][1]);
      for (let i = 1; i < pts.length && left > 0; i++) {
        const k = Math.min(1, left / (seg[i - 1] || 1));
        c.lineTo(lerp(pts[i - 1][0], pts[i][0], k), lerp(pts[i - 1][1], pts[i][1], k)); left -= seg[i - 1];
      }
      c.stroke();
    },
    /* Arche fleurie. Origine = centre au sol. */
    arch(c, p, t) {
      const w = p.w || 760, h = p.h || 980, r = w / 2, top = -(h - r);
      c.strokeStyle = 'rgba(255,255,255,.85)'; c.lineWidth = 4; c.lineCap = 'round';
      for (const k of [0, 34]) {
        c.beginPath(); c.moveTo(-r + k, 0); c.lineTo(-r + k, top); c.arc(0, top, r - k, Math.PI, 0); c.lineTo(r - k, 0); c.stroke();
      }
      c.lineWidth = 3; c.strokeStyle = 'rgba(255,255,255,.6)';
      for (const d of [-1, 1]) { c.beginPath(); c.moveTo(0, top - r + 20); c.quadraticCurveTo(d * r * 0.42, top - r * 0.5, d * r * 0.76, top - r * 0.6); c.stroke(); }
      for (const [fx, fy, s] of [[0, top - r + 4, 1.15], [-r * 0.74, top - r * 0.66, 0.9], [r * 0.74, top - r * 0.66, 0.9]]) {
        c.save(); c.translate(fx, fy); c.rotate(Math.sin(t * 0.8 + fx) * 0.06); c.scale(s, s);
        c.fillStyle = '#000'; c.beginPath(); c.arc(0, 0, 44, 0, TAU); c.fill(); c.shadowColor = '#fff'; c.shadowBlur = 12;
        drawIcon(c, 'flower', {}, t); c.restore();
      }
    },
    /* Chrono : compte à rebours de `from` à 0, une unité par seconde à partir de `start`. */
    timer(c, p, t) {
      const R = p.r || 150, st = p.start ?? p.at ?? 0, from = p.from ?? 5;
      const el = clamp(t - st, 0, from), n = Math.max(0, from - Math.floor(el)), f = el >= from ? 1 : el % 1;
      c.strokeStyle = '#fff'; c.fillStyle = '#fff'; c.lineWidth = 8; c.lineCap = 'round';
      c.shadowColor = '#fff'; c.shadowBlur = 14;
      c.beginPath(); c.arc(0, 0, R, 0, TAU); c.stroke();
      rr(c, -22, -R - 34, 44, 26, 6); c.fill();
      for (const d of [-1, 1]) { c.save(); c.rotate(d * 0.62); rr(c, -13, -R - 22, 26, 18, 5); c.fill(); c.restore(); }
      c.lineWidth = 4; c.shadowBlur = 0;
      for (let i = 0; i < 12; i++) { const a = i * TAU / 12; c.beginPath(); c.moveTo(Math.cos(a) * R * 0.8, Math.sin(a) * R * 0.8); c.lineTo(Math.cos(a) * R * 0.88, Math.sin(a) * R * 0.88); c.stroke(); }
      c.lineWidth = 12; c.shadowBlur = 20; c.beginPath(); c.arc(0, 0, R * 0.72, -Math.PI / 2, -Math.PI / 2 + TAU * (el / from)); c.stroke();
      const s = 1 + (1 - EASE.outExpo(clamp(f * 3))) * 0.35;
      c.save(); c.scale(s, s); c.font = `900 ${R * 0.78}px ${FONT}`; c.textAlign = 'center'; c.textBaseline = 'middle';
      c.fillText(String(n), 0, R * 0.05); c.restore();
    },
    trafficlight(c, p) {
      const act = Math.round(p.active ?? 0);
      c.strokeStyle = '#fff'; c.lineWidth = 3.5; rr(c, -42, -120, 84, 240, 14); c.fillStyle = '#050505'; c.fill(); c.stroke();
      c.beginPath(); c.moveTo(0, 120); c.lineTo(0, 120 + (p.pole ?? 110)); c.stroke();
      for (let i = 0; i < 3; i++) {
        const y = -74 + i * 74; c.beginPath(); c.arc(0, y, 26, 0, TAU);
        if (i === act) { halo(c, 0, y, 110, 0.5); c.fillStyle = i === 2 ? '#fff' : '#9c9c9c'; c.beginPath(); c.arc(0, y, 26, 0, TAU); c.fill(); }
        else { c.strokeStyle = 'rgba(255,255,255,.7)'; c.lineWidth = 2.5; c.stroke(); }
      }
    },
    shape(c, p) {
      const w = p.w || 100, h = p.h || 100;
      if (p.kind === 'circle') { c.beginPath(); c.arc(0, 0, w / 2, 0, TAU); } else rr(c, -w / 2, -h / 2, w, h, p.r ?? 8);
      if (p.fill) { c.fillStyle = p.fill === true ? '#fff' : p.fill; c.fill(); }
      if (p.stroke !== false) { c.strokeStyle = '#fff'; c.lineWidth = p.width || 3.5; if (p.dash) c.setLineDash([10, 8]); c.shadowColor = '#fff'; c.shadowBlur = 10; c.stroke(); }
    },
  };
  function drawCover(c, img, x, y, w, h, p) {
    const s = Math.max(w / img.width, h / img.height), iw = img.width * s, ih = img.height * s;
    c.save();
    c.filter = p.color ? 'none' : `grayscale(1) contrast(${p.contrast ?? 1.35}) brightness(${p.brightness ?? 0.92})`;
    c.drawImage(img, x + (w - iw) / 2, y + (h - ih) / 2, iw, ih); c.restore();
  }

  /* ---------- rendu d'une image ---------- */
  function sceneAt(t) {
    let acc = 0;
    for (const s of SCENE.scenes) { if (t < acc + s.duration) return [s, t - acc]; acc += s.duration; }
    const last = SCENE.scenes[SCENE.scenes.length - 1]; return [last, last.duration - 1e-4];
  }
  function draw(time) {
    const [sc, t] = sceneAt(time);
    let flash = 0, punch = 0;
    const tr = sc.transition || 'cut';
    if (tr === 'flash') { flash = Math.max(flash, (1 - t / 0.28) * 0.3); punch = Math.max(0, 1 - t / 0.35); }
    (sc.flashes || []).forEach(f => { if (t >= f) flash = Math.max(flash, (1 - (t - f) / 0.28) * 0.3); });

    lc.setTransform(1, 0, 0, 1, 0, 0); lc.clearRect(0, 0, W, H);
    const cam = sc.camera || {};
    const zoom = (kf(cam.zoom, t) ?? 1 + 0.035 * t / sc.duration) * (1 + EASE.in(punch) * 0.07);
    const cx = kf(cam.x, t) ?? W / 2, cy = kf(cam.y, t) ?? H / 2;
    lc.translate(W / 2, H / 2); lc.scale(zoom, zoom); lc.translate(-cx, -cy);

    for (const e of sc.elements || []) {
      const at = e.at ?? 0, until = e.until ?? Infinity;
      if (t < at || t > until) continue;
      const fn = DRAW[e.type]; if (!fn) continue;
      const p = resolve(e, t), lt = t - at, anim = e.in || 'fade';
      const inDur = e.inDur ?? (anim === 'type' ? Math.max(0.3, String(e.text || '').length * 0.045) : anim === 'slam' ? 0.22 : 0.4);
      const ki = at === 0 && anim === 'fade' && tr === 'cut' && e.inDur === undefined ? 1 : clamp(lt / inDur);
      const ko = until === Infinity ? 1 : clamp((until - t) / (e.outDur ?? 0.25));
      let a = (p.alpha ?? 1) * ko, s = p.scale ?? 1, dy = 0, blur = 0;
      if (anim === 'fade') a *= EASE.out(ki);
      else if (anim === 'pop') { s *= lerp(0.55, 1, EASE.outBack(ki)); a *= clamp(ki * 3); }
      else if (anim === 'slam') { s *= lerp(1.55, 1, EASE.outExpo(ki)); a *= clamp(ki * 2.5); blur = (1 - ki) * 22; flash = Math.max(flash, (1 - lt / 0.3) * 0.26); }
      else if (anim === 'up') { dy = (1 - EASE.out(ki)) * 46; a *= EASE.out(ki); }
      else if (anim === 'type') p._type = ki;
      if (e.out === 'blur') blur = Math.max(blur, (1 - ko) * 18);
      if (a <= 0.001) continue;
      lc.save();
      lc.translate(p.x ?? W / 2, (p.y ?? H / 2) + dy); if (p.rot) lc.rotate(p.rot); lc.scale(s, s);
      lc.globalAlpha = a; if (blur > 0.5) lc.filter = `blur(${blur.toFixed(1)}px)`;
      fn(lc, p, t, lt);
      lc.restore();
    }

    /* composition : fond, grille, flash, bloom, calque net, poussières, grain, vignette */
    mc.setTransform(1, 0, 0, 1, 0, 0); mc.globalAlpha = 1; mc.globalCompositeOperation = 'source-over'; mc.filter = 'none';
    mc.fillStyle = '#000'; mc.fillRect(0, 0, W, H);
    const bg = mc.createRadialGradient(W / 2, H * 0.55, 0, W / 2, H * 0.55, Math.max(W, H) * 0.7);
    bg.addColorStop(0, 'rgba(34,34,34,1)'); bg.addColorStop(1, 'rgba(0,0,0,1)');
    mc.globalAlpha = sc.backdrop ?? 0.4; mc.fillStyle = bg; mc.fillRect(0, 0, W, H);
    if (SCENE.dots !== false) { mc.globalAlpha = 0.5; mc.drawImage(dotsTile, 0, 0); }
    if (flash > 0) { mc.globalAlpha = clamp(flash); mc.fillStyle = '#fff'; mc.fillRect(0, 0, W, H); }
    const bloom = SCENE.bloom ?? 1;
    if (bloom > 0) {
      mc.globalCompositeOperation = 'lighter';
      const bw = small.width, bh = small.height;
      if (!FILTER_OK) {
        /* Navigateurs sans ctx.filter (Safari) : flou par réduction/agrandissement. */
        tc.globalCompositeOperation = 'copy'; tc.drawImage(layer, 0, 0, tiny.width, tiny.height);
        mc.imageSmoothingQuality = 'high';
        mc.globalAlpha = 0.4 * bloom; mc.drawImage(tiny, 0, 0, W, H);
        sc2.globalCompositeOperation = 'copy'; sc2.drawImage(layer, 0, 0, bw, bh);
        mc.globalAlpha = 0.18 * bloom; mc.drawImage(small, 0, 0, W, H);
        mc.globalCompositeOperation = 'source-over';
      } else {
      sc2.globalCompositeOperation = 'copy'; sc2.filter = 'none'; sc2.drawImage(layer, 0, 0, bw, bh);
      sc3.globalCompositeOperation = 'copy'; sc3.filter = `blur(${(bw / 110).toFixed(1)}px)`; sc3.drawImage(small, 0, 0);
      mc.imageSmoothingQuality = 'high';
      mc.globalAlpha = 0.3 * bloom; mc.drawImage(small2, 0, 0, W, H);
      sc3.filter = `blur(${(bw / 30).toFixed(1)}px)`; sc3.drawImage(small, 0, 0);
      mc.globalAlpha = 0.15 * bloom; mc.drawImage(small2, 0, 0, W, H);
      mc.globalCompositeOperation = 'source-over';
      }
    }
    mc.globalAlpha = 1; mc.drawImage(layer, 0, 0);
    const r = rng(99); mc.fillStyle = '#fff';
    for (let i = 0; i < 34; i++) {
      const x = (r() * W + time * (r() - 0.5) * 22 + W) % W, y = (r() * H - time * r() * 14 + H * 9) % H;
      mc.globalAlpha = 0.06 + r() * 0.16; mc.beginPath(); mc.arc(x, y, 0.8 + r() * 1.5, 0, TAU); mc.fill();
    }
    const grain = SCENE.grain ?? 1;
    if (grain > 0) {
      const f = Math.round(time * FPS), g = grainTiles[f % grainTiles.length], gr = rng(f + 1);
      const ox = Math.floor(gr() * 512), oy = Math.floor(gr() * 512);
      mc.globalAlpha = 0.5 * grain;
      for (let x = -ox; x < W; x += 512) for (let y = -oy; y < H; y += 512) mc.drawImage(g, x, y);
    }
    mc.globalAlpha = 1;
    const vg = mc.createRadialGradient(W / 2, H / 2, Math.min(W, H) * 0.35, W / 2, H / 2, Math.max(W, H) * 0.72);
    vg.addColorStop(0, 'rgba(0,0,0,0)'); vg.addColorStop(1, 'rgba(0,0,0,.6)');
    mc.fillStyle = vg; mc.fillRect(0, 0, W, H);
    if (tr === 'fade' && t < 0.4) { mc.globalAlpha = 1 - t / 0.4; mc.fillStyle = '#000'; mc.fillRect(0, 0, W, H); mc.globalAlpha = 1; }
    const end = TOTAL - time;
    if (SCENE.fadeOut !== false && end < 0.5) { mc.globalAlpha = clamp(1 - end / 0.5); mc.fillStyle = '#000'; mc.fillRect(0, 0, W, H); mc.globalAlpha = 1; }
  }

  /* ---------- chargement ---------- */
  async function load(scene, canvas) {
    SCENE = scene; FPS = scene.fps || 30;
    const vertical = scene.format === '9:16', square = scene.format === '1:1';
    W = scene.width || (vertical || square ? 1080 : 1920); H = scene.height || (vertical ? 1920 : square ? 1080 : 1080);
    main = canvas; main.width = W; main.height = H; mc = main.getContext('2d');
    layer = document.createElement('canvas'); layer.width = W; layer.height = H; lc = layer.getContext('2d');
    small = document.createElement('canvas'); small.width = Math.round(W / 4); small.height = Math.round(H / 4); sc2 = small.getContext('2d');
    small2 = document.createElement('canvas'); small2.width = small.width; small2.height = small.height; sc3 = small2.getContext('2d');
    tiny = document.createElement('canvas'); tiny.width = Math.round(W / 24); tiny.height = Math.round(H / 24); tc = tiny.getContext('2d');
    try { const probe = document.createElement('canvas').getContext('2d'); probe.filter = 'blur(2px)'; FILTER_OK = probe.filter === 'blur(2px)'; } catch (e) { FILTER_OK = false; }
    TOTAL = scene.scenes.reduce((a, s) => a + s.duration, 0);
    const r = rng(1234); grainTiles = [];
    for (let k = 0; k < 6; k++) {
      const g = document.createElement('canvas'); g.width = g.height = 512;
      const gc = g.getContext('2d'), d = gc.createImageData(512, 512);
      for (let i = 0; i < d.data.length; i += 4) { const v = r() * 255; d.data[i] = d.data[i + 1] = d.data[i + 2] = v; d.data[i + 3] = 20; }
      gc.putImageData(d, 0, 0); grainTiles.push(g);
    }
    dotsTile = document.createElement('canvas'); dotsTile.width = W; dotsTile.height = H;
    const dc = dotsTile.getContext('2d'); dc.fillStyle = 'rgba(255,255,255,.13)';
    for (let x = 24; x < W; x += 48) for (let y = 24; y < H; y += 48) { dc.beginPath(); dc.arc(x, y, 1.3, 0, TAU); dc.fill(); }
    const jobs = Object.entries(scene.images || {}).map(([k, src]) => new Promise(res => {
      const im = new Image(); im.onload = () => { IMAGES[k] = im; res(); }; im.onerror = () => res(); im.src = src;
    }));
    await Promise.all(jobs);
    try { await Promise.all([document.fonts.load(`900 40px ${FONT}`), document.fonts.load(`800 40px ${FONT}`)]); } catch (e) { /* police de secours */ }
    return { width: W, height: H, fps: FPS, duration: TOTAL, frames: Math.round(TOTAL * FPS) };
  }
  function frame(i, quality) { draw(i / FPS); return main.toDataURL('image/jpeg', quality || 0.93); }

  window.BB = { load, draw, frame, types: Object.keys(DRAW) };
})();
