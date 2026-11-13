#!/usr/bin/env node
// capture: tangkap halaman aplikasi HaloSIS (akun, URL, aksi opsional) ke Figma lewat generate_figma_design.
// captureId didapat dari alat MCP generate_figma_design (satu id = satu tangkapan, sekali pakai).
//   node tools/figma/capture.js --user budi --url /plugins/halosis/Chat --ids <id1>[,<id2>...] [--steps tools/figma/steps/x.js] [--h 900] [--png logs/x.png]
// Tanpa --steps: buka URL lalu tangkap dengan id pertama. Dengan --steps: modul `async ({page, cap, ctx}) => {...}`;
// id 'x' = lewati tangkap ke-i (mis. id sudah terpakai). Panggil `await cap(i)` di titik tangkap ke-i (memakai id ke-i). Frame hasil tangkapan mendarat di halaman Figma sebagai frame level-halaman.
const { chromium } = require('../../tests/e2e/node_modules/playwright-core');
const fs = require('fs'), os = require('os'), path = require('path');
const injectIcons = require('./inject_icons');
const arg = (k, d) => { const i = process.argv.indexOf('--' + k); return i > 0 ? process.argv[i + 1] : d; };
const BASE = process.env.HALOSIS_URL || 'http://localhost:8080';
const user = arg('user'), url = arg('url', '/'), ids = (arg('ids', '')).split(',').filter(Boolean), steps = arg('steps'), H = +arg('h', 900), png = arg('png');
const ENDPOINT = (c) => `https://mcp.figma.com/mcp/capture/${c}/submit?bindVariables=true`;

(async () => {
  const cache = path.join(os.homedir(), 'Library/Caches/ms-playwright');
  const shell = fs.readdirSync(cache).find(d => d.startsWith('chromium_headless_shell'));
  const sub = fs.readdirSync(path.join(cache, shell)).find(d => d.startsWith('chrome-headless-shell'));
  const b = await chromium.launch({ executablePath: path.join(cache, shell, sub, 'chrome-headless-shell') });
  const page = await (await b.newContext({ viewport: { width: 1440, height: H } })).newPage();
  page.setDefaultTimeout(60000);
  await page.goto(BASE + '/');
  await page.fill('#login_name', user); await page.fill('#login_password', 'halosis');
  await Promise.all([page.waitForLoadState('networkidle'), page.click('button[name=submit]')]);
  await page.route('**/*', async r => {  // buang CSP agar skrip tangkap bisa disuntik
    try { const resp = await r.fetch(); const h = { ...resp.headers() }; delete h['content-security-policy']; await r.fulfill({ response: resp, headers: h }); } catch (e) { r.abort().catch(() => {}); }
  });
  const ctx = { shots: [] };
  const cap = async (i) => {
    // sidebar GLPI mengikuti preferensi pengguna fold_menu (DB): buka lewat kelas body saja agar DB tidak berubah; frame Figma memakai sidebar terbuka 240 px
    await page.evaluate(() => document.body.classList.remove('navbar-collapsed')); await page.waitForTimeout(600);
    if (png) await page.screenshot({ path: png.replace(/(\.png)?$/, `_${i}.png`) });
    const ic = await injectIcons(page);
    if (!ids[i] || ids[i] === 'x') { console.log('tanpa id, lewati tangkap', i, JSON.stringify(ic)); return; }
    const js = await (await page.context().request.get('https://mcp.figma.com/mcp/html-to-design/capture.js')).text();
    await page.evaluate(s => { if (!window.figma) { const e = document.createElement('script'); e.textContent = s; document.head.appendChild(e); } }, js);
    await page.waitForTimeout(500);
    // captureForDesign bisa tidak kembali (toolbar tangkap tetap terbuka) walau data sudah terkirim: beri batas 30 dtk lalu lanjut.
    const r = await Promise.race([
      page.evaluate(([c, ep]) => window.figma.captureForDesign({ captureId: c, endpoint: ep, selector: 'body' }), [ids[i], ENDPOINT(ids[i])]),
      new Promise(res => setTimeout(() => res('terkirim (batas waktu 30 dtk, cek status lewat generate_figma_design)'), 30000))]);
    console.log(`tangkap #${i}`, JSON.stringify(ic), JSON.stringify(r));
  };
  try {
    await page.goto(BASE + url); await page.waitForLoadState('networkidle');
    if (steps) await require(path.resolve(steps))({ page, cap, ctx, BASE });
    else await cap(0);
  } finally { await b.close(); }
})().catch(e => { console.error('GAGAL:', e.message); process.exit(1); });
