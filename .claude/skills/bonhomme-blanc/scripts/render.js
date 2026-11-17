#!/usr/bin/env node
/* Rendu d'un fichier scène JSON en MP4 (style "bonhomme blanc").
 *
 *   node render.js scene.json -o sortie.mp4 [--audio musique.mp3] [--scale 0.5] [--crf 22]
 *                  [--sheet planche.jpg] [--still 3.5 image.png] [--from 10 --to 20]
 *
 * Prérequis : node, playwright (+ chromium), ffmpeg.                         */
const fs = require('fs');
const path = require('path');
const { spawn, spawnSync } = require('child_process');

const args = process.argv.slice(2);
if (!args.length || args[0].startsWith('-')) {
  console.error('Usage: node render.js scene.json -o out.mp4 [--audio f] [--scale k] [--sheet f.jpg] [--still t f.png] [--from s --to s]');
  process.exit(1);
}
const opt = (name, n = 1) => { const i = args.indexOf(name); return i < 0 ? null : n === 1 ? args[i + 1] : args.slice(i + 1, i + 1 + n); };
const scenePath = path.resolve(args[0]);
const out = path.resolve(opt('-o') || scenePath.replace(/\.json$/, '') + '.mp4');
const scale = parseFloat(opt('--scale') || '1');
const still = opt('--still', 2);
const MIME = { '.png': 'image/png', '.jpg': 'image/jpeg', '.jpeg': 'image/jpeg', '.webp': 'image/webp', '.gif': 'image/gif' };

function loadPlaywright() {
  for (const p of ['playwright', '/opt/node-tools/node_modules/playwright', 'playwright-core']) {
    try { return require(p); } catch (e) { /* suivant */ }
  }
  console.error('Playwright introuvable : npm i -g playwright && npx playwright install chromium'); process.exit(1);
}

(async () => {
  const scene = JSON.parse(fs.readFileSync(scenePath, 'utf8'));
  if (!Array.isArray(scene.scenes) || !scene.scenes.length) throw new Error('Le fichier doit contenir "scenes": [...]');
  // Images de l'utilisateur : intégrées en data-URL (sinon le canvas est "tainted").
  for (const [k, src] of Object.entries(scene.images || {})) {
    if (/^data:/.test(src)) continue;
    const f = path.resolve(path.dirname(scenePath), src);
    const mime = MIME[path.extname(f).toLowerCase()];
    if (!mime || !fs.existsSync(f)) throw new Error(`Image introuvable ou format non géré : ${src}`);
    scene.images[k] = `data:${mime};base64,${fs.readFileSync(f).toString('base64')}`;
  }
  const engine = fs.readFileSync(path.join(__dirname, '..', 'engine', 'engine.js'), 'utf8');
  const { chromium } = loadPlaywright();
  const browser = await chromium.launch();
  const page = await browser.newPage();
  page.on('pageerror', e => { console.error('Erreur moteur :', e.message); });
  await page.setContent('<!doctype html><html><body style="margin:0;background:#000"><canvas id="c"></canvas></body></html>');
  await page.addScriptTag({ content: engine });
  const info = await page.evaluate(s => window.BB.load(s, document.getElementById('c')), scene);
  const types = await page.evaluate(() => window.BB.types);
  const bad = [...new Set(scene.scenes.flatMap(s => (s.elements || []).map(e => e.type)))].filter(t => !types.includes(t));
  if (bad.length) console.warn('⚠ Types inconnus (ignorés) :', bad.join(', '), '\n  Types valides :', types.join(', '));

  if (still) {
    const data = await page.evaluate(([t, fps]) => window.BB.frame(Math.round(t * fps), 0.95), [parseFloat(still[0]), info.fps]);
    fs.writeFileSync(path.resolve(still[1]), Buffer.from(data.split(',')[1], 'base64'));
    console.log('Image :', path.resolve(still[1]));
    await browser.close(); return;
  }

  const f0 = Math.round(parseFloat(opt('--from') || '0') * info.fps);
  const f1 = Math.min(info.frames, Math.round(parseFloat(opt('--to') || String(info.duration)) * info.fps));
  const ow = Math.round(info.width * scale / 2) * 2, oh = Math.round(info.height * scale / 2) * 2;
  const audio = opt('--audio') || (scene.audio ? path.resolve(path.dirname(scenePath), scene.audio) : null);
  const ff = ['-y', '-loglevel', 'error', '-f', 'image2pipe', '-c:v', 'mjpeg', '-framerate', String(info.fps), '-i', '-'];
  if (audio) ff.push('-i', audio, '-c:a', 'aac', '-b:a', '192k', '-shortest');
  ff.push('-vf', `scale=${ow}:${oh}:flags=lanczos`, '-c:v', 'libx264', '-preset', 'medium', '-crf', opt('--crf') || '22', '-maxrate', '6M', '-bufsize', '12M', '-pix_fmt', 'yuv420p', '-movflags', '+faststart', out);
  const proc = spawn('ffmpeg', ff, { stdio: ['pipe', 'inherit', 'inherit'] });
  const done = new Promise((res, rej) => proc.on('close', c => (c === 0 ? res() : rej(new Error('ffmpeg a échoué (code ' + c + ')')))));
  proc.stdin.on('error', () => {});

  const BATCH = 6, t0 = Date.now();
  for (let i = f0; i < f1; i += BATCH) {
    const n = Math.min(BATCH, f1 - i);
    const frames = await page.evaluate(([a, k]) => { const r = []; for (let j = 0; j < k; j++) r.push(window.BB.frame(a + j)); return r; }, [i, n]);
    for (const d of frames) {
      if (!proc.stdin.write(Buffer.from(d.split(',')[1], 'base64'))) await new Promise(r => proc.stdin.once('drain', r));
    }
    if ((i - f0) % (BATCH * 25) === 0) process.stdout.write(`\r${Math.round((i - f0) / (f1 - f0) * 100)} %  `);
  }
  proc.stdin.end(); await done; await browser.close();
  console.log(`\rVidéo : ${out}  (${ow}x${oh}, ${((f1 - f0) / info.fps).toFixed(1)} s, rendu en ${((Date.now() - t0) / 1000).toFixed(0)} s)`);

  const sheet = opt('--sheet');
  if (sheet) {
    const dur = (f1 - f0) / info.fps, cols = 5, step = Math.max(0.5, dur / 20), rows = Math.ceil(Math.ceil(dur / step) / cols);
    const r = spawnSync('ffmpeg', ['-y', '-loglevel', 'error', '-i', out, '-vf', `fps=1/${step},scale=384:-1,tile=${cols}x${rows}`, '-frames:v', '1', '-q:v', '3', path.resolve(sheet)]);
    if (r.status === 0) console.log('Planche contact :', path.resolve(sheet), `(1 vignette / ${step.toFixed(1)} s)`);
  }
})().catch(e => { console.error('\nErreur :', e.message); process.exit(1); });
