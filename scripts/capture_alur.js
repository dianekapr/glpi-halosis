// Tangkap screenshot bukti alur alternatif (peta alur Figma, titik "Belum ada layar") UC-01 … UC-05.
// Mengikuti reports/cara_memicu_alur_alternatif.md. Viewport 1440×900, deviceScaleFactor 2.
//
//   node scripts/capture_alur.js --uc UC-01,UC-02,UC-03,UC-05
//
// Hasil: reports/shots/alur/<UC>_<alur>[_<langkah>].png dan reports/shots/alur/hasil.json (status per tangkapan).
// PERINGATAN: skrip MENGUBAH data (tiket, chat, log, sakelar fitur; layanan halosis-ai dimatikan sebentar).
// Jalankan HANYA di demo, lalu pulihkan: scripts/demo_snapshot.sh pulihkan backup/demo-20261115-080525
const { execSync } = require('child_process');
const fs = require('fs'), os = require('os'), path = require('path');
const { chromium } = require(path.resolve(__dirname, '../tests/e2e/node_modules/playwright-core'));

const BASE = process.env.HALOSIS_URL || 'http://localhost:8080';
const ROOT = path.resolve(__dirname, '..');
const OUT = path.join(ROOT, 'reports/shots/alur');
const PASSWORD = 'halosis';
const arg = process.argv.indexOf('--uc');
const WANT = new Set((arg > 0 ? process.argv[arg + 1] : 'UC-01,UC-02,UC-03,UC-05').split(',').map(s => s.trim()));
fs.mkdirSync(OUT, { recursive: true });
const resultsFile = path.join(OUT, 'hasil.json');
const results = fs.existsSync(resultsFile) ? JSON.parse(fs.readFileSync(resultsFile, 'utf8')) : {};
const sleep = ms => new Promise(r => setTimeout(r, ms));

const sh = c => execSync(c, { cwd: ROOT, stdio: 'pipe' }).toString();
const aiHealthy = () => fetch('http://localhost:8001/health').then(r => r.ok).catch(() => false);
async function startAi() { sh('docker compose start halosis-ai'); for (let i = 0; i < 90 && !(await aiHealthy()); i++) await sleep(1000); }
const stopAi = () => sh('docker compose stop halosis-ai');

async function newPage(browser, user) {
  const ctx = await browser.newContext({ viewport: { width: 1440, height: 900 }, deviceScaleFactor: 2 });
  const p = await ctx.newPage(); p.setDefaultTimeout(45000);
  await p.goto(BASE + '/');
  await p.fill('#login_name', user); await p.fill('#login_password', PASSWORD);
  await Promise.all([p.waitForLoadState('networkidle'), p.click('button[name=submit]')]);
  return p;
}
async function shot(p, name, note) {
  await sleep(700);
  await p.screenshot({ path: path.join(OUT, name + '.png') });
  results[name] = { status: 'ok', note: note || '' }; console.log('OK    ', name);
}
function skip(name, why) { results[name] = { status: 'lewat', note: why }; console.log('LEWAT ', name, '-', why); }
async function step(name, fn) {
  try { await fn(); } catch (e) { skip(name, 'gagal: ' + e.message.split('\n')[0].slice(0, 120)); }
}

// ---- Chat (budi)
const input = p => p.locator('[data-chat-form] textarea').first();
async function openChat(p) {
  await p.goto(`${BASE}/plugins/halosis/Chat`); await p.waitForLoadState('networkidle');
  const fresh = p.locator('[data-chat-new]').first();
  if (await fresh.isVisible().catch(() => false)) { await fresh.click(); await p.waitForTimeout(1500); }
}
async function ask(p, text) {
  const n = await p.locator('.hc-row-ai .hc-bubble-ai:not(.hc-typing)').count();
  await input(p).fill(text); await input(p).press('Enter');
  await p.waitForFunction(c => document.querySelectorAll('.hc-row-ai .hc-bubble-ai:not(.hc-typing)').length > c && !document.querySelector('.hc-typing'), n, { timeout: 45000 });
  await p.waitForTimeout(800);
}
const btn = (p, re) => p.getByRole('button', { name: re }).first();

// ---- Admin: sakelar fitur (dimas)
async function openConfig(p) {
  await p.goto(`${BASE}/plugins/halosis/front/config.form.php`); await p.waitForLoadState('networkidle');
  if (await p.locator('[data-halosis-config]').count() === 0) {
    if (await p.locator('input[type=password]').count() > 0) await p.locator('input[type=password]').first().fill(PASSWORD);
    await Promise.all([p.waitForLoadState('networkidle'), p.locator('form[action*="ReAuth"] button[type=submit]').click()]);
    await p.goto(`${BASE}/plugins/halosis/front/config.form.php`); await p.waitForLoadState('networkidle');
  }
}
async function setFeature(browser, key, on) {
  const p = await newPage(browser, 'dimas');
  await openConfig(p);
  await p.locator(`input[name=feature_${key}][type=checkbox]`).evaluate((el, v) => { el.checked = v; }, on);
  await Promise.all([p.waitForLoadState('networkidle'), p.locator('button[name=update]').click()]);
  await p.context().close();
}

// ---- API GLPI (tiket uji)
async function api() {
  const auth = 'Basic ' + Buffer.from('glpi:glpi').toString('base64');
  const token = (await (await fetch(`${BASE}/apirest.php/initSession`, { headers: { Authorization: auth } })).json()).session_token;
  const h = { 'Session-Token': token, 'Content-Type': 'application/json' };
  const call = async (m, u, b) => (await fetch(`${BASE}/apirest.php/${u}`, { method: m, headers: h, body: b && JSON.stringify(b) })).json();
  const profiles = await call('GET', 'Profile?range=0-100');
  await call('POST', 'changeActiveProfile', { profiles_id: profiles.find(p => p.name === 'Super-Admin').id });
  const users = Object.fromEntries((await call('GET', 'User?range=0-500')).map(u => [u.name, u.id]));
  return { call, users };
}
async function makeTicket(a, title) {
  const r = await a.call('POST', 'Ticket', { input: { name: title, content: `${title}. Data uji capture.`, type: 1, _users_id_requester: a.users.budi } });
  return r.id;
}
async function openTicket(p, id) { await p.goto(`${BASE}/front/ticket.form.php?id=${id}`); await p.waitForLoadState('networkidle'); await p.locator('#halosis-triase-body, [data-action=generate]').first().waitFor().catch(() => {}); }

// ---- UC-01
async function uc01(browser) {
  const p = await newPage(browser, 'budi');
  await step('UC-01_normal_9', async () => {
    await openChat(p); await ask(p, 'Lupa kata sandi SSO');
    await btn(p, /Masalah terselesaikan/).click(); await p.waitForTimeout(1500);
    await shot(p, 'UC-01_normal_9', 'Terima kasih, percakapan berakhir');
  });
  await step('UC-01_3a', async () => {
    await openChat(p); await input(p).fill('');
    if (!(await p.locator('[data-chat-form] button').first().isDisabled())) throw new Error('Kirim tidak nonaktif');
    await shot(p, 'UC-01_3a', 'Kotak kosong, tombol Kirim nonaktif');
  });
  await step('UC-01_4b', async () => {
    await openChat(p);
    await p.route('**/ajax/chat.php*', r => r.abort());
    await input(p).fill('Lupa kata sandi SSO'); await input(p).press('Enter');
    await p.getByText(/sedang tidak tersedia/i).first().waitFor(); await p.waitForTimeout(800);
    await shot(p, 'UC-01_4b', 'Request chat diputus (page.route abort)');
    await p.unroute('**/ajax/chat.php*');
  });
  await step('UC-01_5a', async () => {
    await openChat(p); await ask(p, 'Cuaca di Bali besok pagi');
    await btn(p, /Ya, buat laporan/).waitFor();
    await shot(p, 'UC-01_5a', 'Kartu tawaran laporan');
    await btn(p, /Ya, buat laporan/).click(); await p.waitForTimeout(800);
    await shot(p, 'UC-01_5a_S1_form', 'Form laporan dengan ringkasan terlampir');
    await p.locator('form.hc-report input.hc-input').fill('Uji capture alur alternatif UC-01');
    await p.locator('form.hc-report button[type=submit]').click(); await p.waitForTimeout(2500);
    await shot(p, 'UC-01_5a_S1', 'Laporan sudah dibuat');
    fs.copyFileSync(path.join(OUT, 'UC-01_5a_S1.png'), path.join(OUT, 'UC-03_1a_S1.png'));
    fs.copyFileSync(path.join(OUT, 'UC-01_5a_S1_form.png'), path.join(OUT, 'UC-03_1a_S1_form.png'));
    results['UC-03_1a_S1'] = { status: 'ok', note: 'Salinan UC-01_5a_S1 (alur sama: Ya, buat laporan → Kirim)' };
    results['UC-03_1a_S1_form'] = { status: 'ok', note: 'Salinan UC-01_5a_S1_form (judul terisi + ringkasan)' };
  });
  await step('UC-01_5c', async () => {
    await openChat(p); await ask(p, 'Cara mengajukan cuti');
    await shot(p, 'UC-01_5c', 'Diarahkan ke unit terkait');
  });
  await step('UC-01_7a', async () => {
    await openChat(p); await ask(p, 'Lupa kata sandi SSO');
    await btn(p, /Belum terselesaikan/).click(); await btn(p, /Ya, buat laporan/).waitFor();
    await shot(p, 'UC-01_7a', 'Kartu laporan setelah Belum terselesaikan');
    await btn(p, /Ya, buat laporan/).click(); await p.waitForTimeout(800);
    await p.locator('form.hc-report input.hc-input').fill('Uji capture alur 7a UC-01');
    await p.locator('form.hc-report button[type=submit]').click(); await p.waitForTimeout(2500);
    await shot(p, 'UC-01_7a_S1', 'Laporan sudah dibuat');
  });
  await step('UC-01_7b', async () => {
    await openChat(p); await ask(p, 'Lupa kata sandi SSO');
    await btn(p, /Belum terselesaikan/).click(); await btn(p, /Tidak, terima kasih/).waitFor();
    await btn(p, /Tidak, terima kasih/).click(); await p.waitForTimeout(1500);
    await shot(p, 'UC-01_7b', 'Percakapan diakhiri; kotak ketik terkunci');
    await p.reload(); await p.waitForLoadState('networkidle'); await p.waitForTimeout(1500);
    await shot(p, 'UC-01_3c', 'Muat ulang: percakapan sudah selesai, kotak ketik terkunci');
  });
  await step('UC-01_3b', async () => {
    await openChat(p);
    for (let i = 1; i <= 20; i++) { await ask(p, 'Lupa kata sandi SSO'); }
    await ask(p, 'Lupa kata sandi SSO');
    await shot(p, 'UC-01_3b', 'Pesan ke-21: percakapan terlalu panjang');
  });
  await p.context().close();

  await step('UC-01_1a', async () => {
    await setFeature(browser, 'chat', false);
    try {
      const b = await newPage(browser, 'budi');
      await b.goto(`${BASE}/plugins/halosis/Chat`); await b.waitForLoadState('networkidle');
      await b.getByText(/Asisten Sedang Tidak Tersedia/i).first().waitFor();
      await shot(b, 'UC-01_1a', 'Sakelar chat dimatikan');
      await b.context().close();
    } finally { await setFeature(browser, 'chat', true); }
  });
}

// ---- UC-02
async function uc02(browser) {
  const p = await newPage(browser, 'rina');
  const q = t => `${BASE}/plugins/halosis/CariKnowledge?q=${encodeURIComponent(t)}`;
  await step('UC-02_S1a', async () => {
    await p.goto(q('zzqx')); await p.waitForLoadState('networkidle');
    await shot(p, 'UC-02_S1a', 'Pengetahuan tidak ditemukan');
  });
  await step('UC-02_5a', async () => {
    await p.goto(q('Cuaca di Bali besok pagi')); await p.waitForLoadState('networkidle');
    await shot(p, 'UC-02_5a', 'Tanpa hasil di atas ambang');
  });
  await step('UC-02_S1b', async () => {
    await p.goto(q('reset password SSO')); await p.waitForLoadState('networkidle');
    await p.locator('[data-hf-helpful="0"]').first().click();
    await p.waitForFunction(() => /Ditandai tidak membantu/.test(document.querySelector('[data-hf]').innerText));
    await shot(p, 'UC-02_S1b', 'Umpan balik tersimpan + penanda Ditandai tidak membantu');
  });
  await step('UC-02_3a', async () => {
    stopAi();
    try {
      await p.goto(q('reset password SSO')); await p.waitForLoadState('networkidle');
      await p.getByText(/tidak dapat dihubungi/i).first().waitFor();
      await shot(p, 'UC-02_3a', 'Layanan AI dimatikan');
    } finally { await startAi(); }
  });
  await p.context().close();
}

// ---- UC-03 & UC-05 (tiket uji lewat API; satu tiket per skenario)
async function uc03_05(browser, want) {
  const a = await api();
  const rina = await newPage(browser, 'rina');
  if (want.has('UC-03')) {
    await step('UC-03_1b', async () => {
      await rina.goto(`${BASE}/front/ticket.form.php?id=0`); await rina.waitForLoadState('networkidle');
      await shot(rina, 'UC-03_1b', 'Form Tambah tiket (Pemohon, Sumber permintaan, Judul, Deskripsi) — belum diisi');
    });
    await step('UC-03_6a', async () => {
      await setFeature(browser, 'triage', false);
      let id;
      try { id = await makeTicket(a, 'Printer lantai 3 tidak mau mencetak'); await sleep(3000); } finally { await setFeature(browser, 'triage', true); }
      await openTicket(rina, id);
      await rina.getByText(/Belum ada saran AI/).first().waitFor();
      await shot(rina, 'UC-03_6a', 'Sakelar triase dimatikan saat tiket dibuat');
      if (want.has('UC-05')) await step('UC-05_3a', async () => {
        await rina.locator('[data-action=generate]').click(); await rina.getByText(/Saran AI dibuat/).first().waitFor({ timeout: 40000 });
        await shot(rina, 'UC-05_3a', 'Setelah klik Buat saran AI');
      });
    });
  }
  if (want.has('UC-05')) {
    const fresh = async t => { const id = await makeTicket(a, t); await sleep(7000); return id; };
    await step('UC-05_S1b', async () => {
      const id = await fresh('Wi-Fi ruang rapat lantai 2 sering putus');
      await openTicket(rina, id);
      await rina.locator('[data-action=show-modify]').click();
      await rina.fill('#halosis-modify-reason', 'abc'); await rina.waitForTimeout(300);
      if (!(await rina.locator('[data-action=modify]').isDisabled())) throw new Error('tombol tidak nonaktif');
      await shot(rina, 'UC-05_S1b', 'Alasan <5 karakter: Terapkan perubahan nonaktif');
      // S-1a pada tiket sama: nilai sama dengan saran
      await rina.fill('#halosis-modify-reason', 'Nilai sengaja dibiarkan sama'); await rina.waitForTimeout(300);
      await rina.locator('[data-action=modify]').click(); await rina.getByText(/Nilainya sama dengan saran/).first().waitFor();
      await shot(rina, 'UC-05_S1a', 'Nilai sama dengan saran: gunakan tombol Terima');
    });
    await step('UC-05_5d', async () => {
      const id = await fresh('Aplikasi FASIH tidak bisa login');
      const r2 = await newPage(browser, 'rina');
      await openTicket(rina, id); await openTicket(r2, id);
      await rina.locator('[data-action=accept]').click(); await rina.waitForTimeout(2500);
      await r2.locator('[data-action=accept]').click(); await r2.getByText(/Saran ini sudah diputuskan/).first().waitFor();
      await shot(r2, 'UC-05_5d', 'Dua sesi: sesi kedua mencoba memutuskan saran yang sudah diputuskan');
      await r2.context().close();
    });
    await step('UC-05_5c', async () => {
      const id = await fresh('Komputer kantor sangat lambat');
      await openTicket(rina, id);
      await rina.locator('[data-action=accept]').click(); await rina.waitForTimeout(2500);
      await openTicket(rina, id);
      await rina.locator('.timeline-buttons .dropdown-toggle-split, .main-actions .dropdown-toggle-split').first().click();
      await rina.waitForTimeout(500);
      await rina.locator('.dropdown-menu.show').getByText(/solusi/i).first().click(); await rina.waitForTimeout(2000);
      const ed = rina.frameLocator('form:has(button[name=add]) iframe').first().locator('body');
      await ed.click(); await ed.type('Sudah dibersihkan dan dioptimalkan, uji capture.');
      await shot(rina, 'UC-05_5c_form', 'Form Tambah solusi');
      await rina.locator('button[name=add]').first().click(); await rina.waitForLoadState('networkidle'); await rina.waitForTimeout(2000);
      await shot(rina, 'UC-05_5c', 'Setelah solusi disimpan: Dipecahkan');
    });
  }
  await rina.context().close();
}

(async () => {
  const cache = path.join(os.homedir(), 'Library/Caches/ms-playwright');
  const shell = fs.existsSync(cache) ? fs.readdirSync(cache).find(d => d.startsWith('chromium_headless_shell')) : null;
  const sub = shell && fs.readdirSync(path.join(cache, shell)).find(d => d.startsWith('chrome-headless-shell'));
  const browser = await chromium.launch(sub ? { executablePath: path.join(cache, shell, sub, 'chrome-headless-shell') } : {});
  try {
    if (WANT.has('UC-01')) await uc01(browser);
    if (WANT.has('UC-02')) await uc02(browser);
    if (WANT.has('UC-03') || WANT.has('UC-05')) await uc03_05(browser, WANT);
  } finally {
    await browser.close();
    if (!(await aiHealthy())) await startAi();
    fs.writeFileSync(resultsFile, JSON.stringify(results, null, 1));
  }
})().catch(e => { console.error(e.message); process.exit(1); });
