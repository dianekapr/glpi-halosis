// Uji UI chat sebagai pegawai (budi) vs /chat langsung: sumber teratas harus sama. Hanya teks; tanpa screenshot.
// Per pertanyaan: judul chip sumber di UI, apakah chip bisa dibuka budi, judul sumber teratas dari /chat (layanan AI).
//   node uji_chat_budi.js "pertanyaan 1" "pertanyaan 2" ...     atau  KASUS=1 node uji_chat_budi.js  (8 kasus PoC)
const { chromium } = require('playwright-core');
const fs = require('fs'), os = require('os'), path = require('path');
const BASE = process.env.HALOSIS_URL || 'http://localhost:8080';
const AI = process.env.HALOSIS_AI_URL || 'http://localhost:8001';

(async () => {
  let questions = process.argv.slice(2);
  if (process.env.KASUS) questions = JSON.parse(fs.readFileSync(path.resolve(__dirname, '../../ai/scripts/kasus_retrieval_poc.json'), 'utf8')).kasus.map(k => k.pertanyaan);
  const cache = path.join(os.homedir(), 'Library/Caches/ms-playwright');
  const shell = fs.existsSync(cache) ? fs.readdirSync(cache).find(d => d.startsWith('chromium_headless_shell')) : null;
  const sub = shell && fs.readdirSync(path.join(cache, shell)).find(d => d.startsWith('chrome-headless-shell'));
  const browser = await chromium.launch(sub ? { executablePath: path.join(cache, shell, sub, 'chrome-headless-shell') } : {});
  const page = await (await browser.newContext({ viewport: { width: 1300, height: 900 } })).newPage();
  page.setDefaultTimeout(60000);
  await page.goto(BASE + '/');
  await page.fill('#login_name', 'budi'); await page.fill('#login_password', 'halosis');
  await Promise.all([page.waitForLoadState('networkidle'), page.click('button[name=submit]')]);
  const result = [];
  for (const q of questions) {
    await page.goto(`${BASE}/plugins/halosis/Chat`); await page.waitForLoadState('networkidle');
    const fresh = page.locator('[data-chat-new]').first();
    if (await fresh.isVisible().catch(() => false)) { await fresh.click(); await page.waitForTimeout(800); }
    const input = page.locator('[data-chat-form] textarea, [data-chat-form] input[type=text]').first();
    const before = await page.locator('.hc-row-ai .hc-bubble-ai').count();
    await input.fill(q); await input.press('Enter');
    await page.waitForFunction((n) => document.querySelectorAll('.hc-row-ai .hc-bubble-ai:not(.hc-typing)').length > n && !document.querySelector('.hc-typing'), before, { timeout: 60000 });
    const bubble = page.locator('.hc-row-ai .hc-bubble-ai:not(.hc-typing)').last();
    const chips = await bubble.locator('a.hc-source').evaluateAll(as => as.map(a => ({ title: a.innerText.trim(), href: a.getAttribute('href') })));
    const answer = (await bubble.innerText()).replace(/\s+/g, ' ').slice(0, 90);
    const opened = [];
    for (const c of chips) {
      const p2 = await page.context().newPage();
      await p2.goto(new URL(c.href, BASE).href); await p2.waitForLoadState('networkidle');
      const body = await p2.innerText('body');
      opened.push(!/izin untuk melakukan|tidak\s+memiliki hak/i.test(body) && body.includes(c.title.slice(0, 20)));
      await p2.close();
    }
    const direct = await (await fetch(`${AI}/chat`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ pertanyaan: q, riwayat: [] }) })).json();
    result.push({
      q, ui: chips.map(c => c.title), ui_bisa_dibuka: opened,
      direct: direct.ditemukan ? direct.sumber.map(s => `${s.sumber} ${s.judul} (${s.skor})`) : [`tidak ditemukan (${direct.mode})`],
      sama: direct.ditemukan ? JSON.stringify(chips.map(c => c.title.toLowerCase())) === JSON.stringify(direct.sumber.map(s => s.judul.toLowerCase())) : chips.length === 0,
      jawaban_ui: answer,
    });
  }
  console.log(JSON.stringify(result, null, 1));
  await browser.close();
})();
