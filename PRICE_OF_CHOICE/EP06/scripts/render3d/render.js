// Renders illustrations from the shared 3D world.
// usage: node render.js <outDir> <jobsJson>   jobs: [{id, shot, w, h, params, frames}]
const { chromium } = require('playwright');
const fs = require('fs'), path = require('path');
(async () => {
  const [outDir, jobsFile] = process.argv.slice(2);
  const jobs = JSON.parse(fs.readFileSync(jobsFile, 'utf8'));
  const b = await chromium.launch({ args: ['--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist'] });
  const page = await b.newPage();
  page.on('console', m => { if (m.type() === 'error') console.log('[page]', m.text()); });
  page.on('pageerror', e => console.log('[pageerror]', e.message));
  await page.setContent('<html><body style="margin:0;background:#000"></body></html>');
  await page.addScriptTag({ path: path.join(__dirname, 'node_modules/three/build/three.min.js') });
  await page.addScriptTag({ path: path.join(__dirname, 'scene.js') });
  await page.addScriptTag({ path: path.join(__dirname, 'shots.js') });
  await page.evaluate(() => {
    window.renderJob = (shotId, w, h, t, params) => {
      const S = window.SHOTS[shotId]; const P = window.PRICE;
      let canvas = window._cv;
      if (!canvas || canvas.width !== w || canvas.height !== h) {
        if (window._r) window._r.dispose();
        canvas = document.createElement('canvas'); canvas.width = w; canvas.height = h; window._cv = canvas;
        const r = new THREE.WebGLRenderer({ canvas, antialias: true, preserveDrawingBuffer: true });
        r.setPixelRatio(1); r.setSize(w, h, false);
        r.shadowMap.enabled = true; r.shadowMap.type = THREE.PCFSoftShadowMap;
        r.toneMapping = THREE.ACESFilmicToneMapping; r.toneMappingExposure = 1.15; r.outputColorSpace = THREE.SRGBColorSpace;
        window._r = r;
      }
      const W = S.ref ? { scene: new THREE.Scene(), objs: {} } : P.buildWorld();
      W.p = params || {};
      if (!W.scene.background) W.scene.background = new THREE.Color('#05070a');
      const cam = S.make(W, t, w / h);
      window._r.render(W.scene, cam);
      const meta = {};
      if (W.screen) meta.screen = window.screenQuad(W.screen, cam, w, h);
      if (W.screens) meta.screens = W.screens.map(sc => window.screenQuad(sc, cam, w, h)); // EP05: dozens of phone screens
      if (W.quad) meta.quad = window.screenQuad(W.quad.obj, cam, w, h, W.quad.hw, W.quad.hh); // EP04: any flat surface (the mirror text)
      // free GPU memory (EP03: the mirror's render target too)
      W.scene.traverse(o => { if (o.name === 'mirrorReflector' && o.dispose) o.dispose(); });
      W.scene.traverse(o => { if (o.geometry) o.geometry.dispose(); if (o.material) [].concat(o.material).forEach(m => { if (m.map) m.map.dispose(); m.dispose(); }); });
      return { url: canvas.toDataURL('image/png'), meta };
    };
  });
  const metaPath = path.join(outDir, 'meta.json');
  const allMeta = fs.existsSync(metaPath) ? JSON.parse(fs.readFileSync(metaPath, 'utf8')) : {};
  for (const j of jobs) {
    const frames = j.frames || 1; const t0 = Date.now();
    const dir = frames > 1 ? path.join(outDir, j.id) : outDir; fs.mkdirSync(dir, { recursive: true });
    for (let f = 0; f < frames; f++) {
      const t = frames > 1 ? f / (frames - 1) : 0;
      const prm = Object.assign({}, j.params || {}); if (j.pkey) prm[j.pkey] = t; // EP03: animate a parameter instead of t
      const res = await page.evaluate(([s, w, h, t, p]) => window.renderJob(s, w, h, t, p), [j.shot, j.w, j.h, t, prm]);
      const file = frames > 1 ? path.join(dir, `f${String(f).padStart(4, '0')}.png`) : path.join(dir, `${j.id}.png`);
      fs.writeFileSync(file, Buffer.from(res.url.split(',')[1], 'base64'));
      if (f === 0) allMeta[j.id] = Object.assign({ shot: j.shot, w: j.w, h: j.h, frames }, res.meta);
    }
    console.log(`${j.id}: ${frames} frame(s) ${((Date.now() - t0) / 1000).toFixed(1)}s`);
  }
  fs.writeFileSync(metaPath, JSON.stringify(allMeta, null, 1));
  await b.close();
})();
