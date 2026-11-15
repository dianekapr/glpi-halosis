// Tangkap screenshot bukti alur alternatif (peta alur Figma, titik "Belum ada layar") UC-01 … UC-10.
// Mengikuti reports/cara_memicu_alur_alternatif.md. Viewport 1440×900, deviceScaleFactor 2.
//
//   node scripts/capture_alur.js --uc UC-01,UC-02,UC-03,UC-05
//   node scripts/capture_alur.js --uc UC-06,UC-07,UC-08,UC-09,UC-10
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

// ---- Pembantu UC-06 … UC-10
const TEAM = 'Tim Aplikasi Statistik';  // tim akun `andi`
async function teamTicket(a, title, status) {
  const id = await makeTicket(a, title);
  const groups = await a.call('GET', 'Group?range=0-100');
  await a.call('POST', 'Group_Ticket', { input: { tickets_id: id, groups_id: groups.find(g => g.name === TEAM).id, type: 2 } });
  if (status) await a.call('PUT', `Ticket/${id}`, { input: { status } });
  return id;
}
const editor = (p, form) => p.frameLocator(`form:has(${form}) iframe`).first().locator('body');

// ---- UC-06 (andi = Tim Teknis; dedi = tim lain)
async function uc06(browser) {
  const a = await api();
  const andi = await newPage(browser, 'andi');
  await step('UC-06_normal_3', async () => {
    const id = await teamTicket(a, 'Aplikasi FASIH tidak bisa sinkron data');
    await openTicket(andi, id);
    await Promise.all([andi.waitForLoadState('networkidle'), andi.locator('button[form^=addme_as_assign]').click()]); await andi.waitForTimeout(1500);
    await shot(andi, 'UC-06_normal_3', 'andi menambahkan dirinya sebagai penanggung jawab + Simpan');
  });
  await step('UC-06_2b', async () => {
    const id = await teamTicket(a, 'Aplikasi FASIH lambat saat input');
    const dedi = await newPage(browser, 'dedi');
    await openTicket(dedi, id);
    if (await dedi.locator('[data-action=show-return]').isVisible().catch(() => false)) throw new Error('tombol Kembalikan tampil untuk dedi');
    await shot(dedi, 'UC-06_2b', 'dedi (tim lain) membuka tiket tim andi: tombol Kembalikan ke Operator tidak tampil');
    await dedi.context().close();
  });
  await step('UC-06_S1', async () => {
    const id = await teamTicket(a, 'Aplikasi FASIH gagal unggah dokumen');
    await openTicket(andi, id);
    await andi.locator('select[name=status]').first().evaluate(el => { el.value = '4'; el.dispatchEvent(new Event('change', { bubbles: true })); });
    await Promise.all([andi.waitForLoadState('networkidle'), andi.locator('button[name=update]').first().click()]);
    await andi.waitForTimeout(1500);
    await shot(andi, 'UC-06_S1', 'Status Tertunda (SLA dijeda) setelah Simpan');
  });
  await step('UC-06_normal_7', async () => {
    const id = await teamTicket(a, 'Aplikasi FASIH tidak bisa login SSO');
    await openTicket(andi, id);
    await andi.locator('.main-actions .dropdown-toggle-split, .timeline-buttons .dropdown-toggle-split').first().click(); await andi.waitForTimeout(500);
    await andi.locator('.dropdown-menu.show').getByText(/solusi/i).first().click(); await andi.waitForTimeout(2000);
    const ed = editor(andi, 'button[name=add]'); await ed.click(); await ed.type('Cache sesi dibersihkan, uji capture.');
    await andi.locator('button[name=add]').first().click(); await andi.waitForLoadState('networkidle'); await andi.waitForTimeout(2000);
    await shot(andi, 'UC-06_normal_7', 'Solusi disimpan: status Dipecahkan, SLA, kandidat pengetahuan');
  });
  await andi.context().close();
  await step('UC-06_4a', async () => {
    const p = await newPage(browser, 'andi');
    stopAi();
    try {
      await p.goto(`${BASE}/plugins/halosis/CariKnowledge?q=${encodeURIComponent('reset password SSO')}`); await p.waitForLoadState('networkidle');
      await p.getByText(/tidak dapat dihubungi/i).first().waitFor();
      await shot(p, 'UC-06_4a', 'Layanan AI dimatikan: hanya hasil kata kunci');
    } finally { await startAi(); await p.context().close(); }
  });
}

// ---- UC-07 (budi = pemohon)
async function uc07(browser) {
  const a = await api();
  const budi = await newPage(browser, 'budi');
  await step('UC-07_3a', async () => {
    const id = await teamTicket(a, 'Printer lantai 2 macet', 2);
    await openTicket(budi, id);
    await budi.locator('.answer-action, button:has-text("Balas")').first().click(); await budi.waitForTimeout(1500);
    const ed = editor(budi, 'button[name=add]'); await ed.click(); await ed.type('Masalah masih terjadi sejak pagi ini.');
    await budi.locator('button[name=add]').first().click(); await budi.waitForLoadState('networkidle'); await budi.waitForTimeout(2000);
    await shot(budi, 'UC-07_3a', 'Keterangan tambahan terkirim pada tiket belum Dipecahkan');
  });
  await step('UC-07_5b', async () => {
    const id = await teamTicket(a, 'Email tidak bisa terkirim');
    await a.call('POST', 'ITILSolution', { input: { itemtype: 'Ticket', items_id: id, content: 'Solusi uji capture.' } });
    await openTicket(budi, id);
    await budi.locator('button[name=add_reopen]').first().click(); await budi.waitForLoadState('networkidle'); await budi.waitForTimeout(1500);
    await shot(budi, 'UC-07_5b', 'Tolak tanpa komentar: alasan wajib diisi, solusi tidak ditolak');
  });
  await budi.context().close();
}

// ---- UC-08
async function uc08(browser) {
  await step('UC-08_normal_5', async () => {
    const p = await newPage(browser, 'rina');  // banner tampil di Beranda untuk pemegang hak triase
    await p.goto(`${BASE}/front/central.php`); await p.waitForLoadState('networkidle');
    await p.locator('.halosis-pattern-banner').first().waitFor({ timeout: 8000 });
    await shot(p, 'UC-08_normal_5', 'Dasbor: banner Pola insiden terdeteksi');
    await p.context().close();
  });
  await step('UC-08_6a', async () => {
    const p = await newPage(browser, 'andi');
    await p.goto(`${BASE}/plugins/halosis/Dashboard`); await p.waitForLoadState('networkidle');
    await shot(p, 'UC-08_6a', 'andi membuka alamat Kinerja AI langsung: akses ditolak');
    await p.context().close();
  });
}

// ---- UC-09 (lina = Knowledge Manager)
async function uc09(browser) {
  const a = await api();
  const kand = (p, q = '') => p.goto(`${BASE}/plugins/halosis/Kandidat${q}`).then(() => p.waitForLoadState('networkidle'));
  const lina = await newPage(browser, 'lina');
  await step('UC-09_3a', async () => {  // tab "Perlu ditinjau" kosong (sebelum ada artikel jatuh tempo)
    await kand(lina, '?status=review');
    await lina.getByText(/Tidak ada artikel yang perlu ditinjau/).first().waitFor({ timeout: 8000 });
    await shot(lina, 'UC-09_3a', 'Tab Perlu ditinjau kosong (teks sebenarnya: "Tidak ada artikel yang perlu ditinjau."; "Belum ada kandidat di sini." hanya di tab kandidat)');
  });
  // Artikel jatuh tempo: tidak ada jalur UI/API/seed (date_mod diisi GLPI saat ini; kb_review_months min. 1 bulan).
  // Atas izin pengguna: SATU UPDATE date_mod artikel FAQ tertua (dipulihkan lewat demo_snapshot.sh pulihkan).
  await step('UC-09_S1a', async () => {
    sh(`docker compose exec -T db sh -c 'mysql -u"$MYSQL_USER" -p"$MYSQL_PASSWORD" "$MYSQL_DATABASE" -e "UPDATE glpi_knowbaseitems SET date_mod = DATE_SUB(NOW(), INTERVAL 8 MONTH) WHERE id = (SELECT id FROM (SELECT MIN(id) id FROM glpi_knowbaseitems WHERE is_faq = 1) t)" 2>/dev/null'`);
    await kand(lina, '?status=review');
    if (!(await lina.locator('[data-hk-review]').count())) throw new Error('tab Perlu ditinjau kosong (tidak ada artikel jatuh tempo tinjau)');
    const f = lina.locator('[data-hk-review]').first();
    await f.locator('input[type=date]').fill('2020-01-01'); await f.locator('button[type=submit]').click();
    await lina.getByText(/setelah hari ini/i).first().waitFor(); await shot(lina, 'UC-09_S1a', 'Tanggal tinjau di masa lalu ditolak: Pilih tanggal tinjau setelah hari ini.');
  });
  await step('UC-09_S1', async () => {
    await kand(lina, '?status=review');
    if (!(await lina.locator('[data-hk-review]').count())) throw new Error('tab Perlu ditinjau kosong (tidak ada artikel jatuh tempo tinjau)');
    const f = lina.locator('[data-hk-review]').first();
    const d = new Date(Date.now() + 90 * 864e5).toISOString().slice(0, 10);
    await f.locator('input[type=date]').fill(d); await f.locator('button[type=submit]').click();
    await lina.getByText(/Tanggal tinjau berikutnya tersimpan/i).first().waitFor({ timeout: 8000 });
    await shot(lina, 'UC-09_S1', 'Tanggal tinjau berikutnya tersimpan.');
  });
  await step('UC-09_4b', async () => {
    await kand(lina, '?status=pending');
    const id = await lina.locator('[data-hk-toggle]').first().getAttribute('data-id');
    const l2 = await newPage(browser, 'lina'); await kand(l2, '?status=pending');
    for (const [pg, text] of [[lina, 'Diabaikan karena uji capture'], [l2, 'Diabaikan karena uji capture']]) {
      await pg.locator(`[data-hk-toggle][data-id="${id}"]`).click();
      await pg.fill(`#hk-reason-${id}`, text);
      await pg.locator(`form[data-hk-ignore][data-id="${id}"] button[type=submit]`).click(); await pg.waitForTimeout(2000);
    }
    await shot(l2, 'UC-09_4b', 'Dua sesi: sesi kedua memutuskan kandidat yang sudah diputuskan');
    await l2.context().close();
  });
  await step('UC-09_1a', async () => {
    stopAi();
    try { await kand(lina, '?status=pending'); await lina.getByText(/tidak dapat dihubungi/i).first().waitFor();
      await shot(lina, 'UC-09_1a', 'Layanan AI dimatikan: kandidat tiket tetap tampil + pemberitahuan'); }
    finally { await startAi(); }
  });
  // artikel dari kandidat (S-2, 5a, 7a, normal 7, 8a)
  let article = null;
  await step('UC-09_S2', async () => {
    await kand(lina, '?status=pending');
    const btn = lina.locator('[data-hk-action=article]').first();
    await Promise.all([lina.waitForURL(/knowbaseitem/i, { timeout: 20000 }), btn.click()]);
    await lina.waitForLoadState('networkidle'); await lina.waitForTimeout(1500);
    article = lina.url();
    await shot(lina, 'UC-09_S2', 'Draf artikel tersimpan dari kandidat');
  });
  await step('UC-09_7a', async () => {  // daftar KB: draf tanpa target bertanda ikon mata-coret ("Item ini belum diterbitkan")
    await lina.goto(`${BASE}/front/knowbaseitem.php?unpublished=1`); await lina.waitForLoadState('networkidle');  // = tombol "Tampilkan yang belum diterbitkan"
    const hit = lina.locator('.not-published');
    await hit.first().waitFor({ timeout: 8000 });
    await hit.first().scrollIntoViewIfNeeded(); await hit.first().hover().catch(() => {});
    await shot(lina, 'UC-09_7a', 'Daftar artikel: draf bertanda "Item ini belum diterbitkan"');
  });
  // Terbitkan: Sunting → centang FAQ ("Tambahkan ke Tanya Jawab") → Simpan
  const faqPublish = async pg => {  // menu ⋮ di sebelah tombol Sunting (bukan menu pohon di sisi kiri)
    const dots = pg.locator('xpath=(//*[self::a or self::button][contains(normalize-space(.),"Sunting")]/following::*[self::a or self::button][.//i[contains(@class,"ti-dots-vertical")]])[1]');
    await dots.click({ timeout: 5000 }); await pg.waitForTimeout(400);
    const menu = pg.locator('.dropdown-menu.show:has-text("Tanya Jawab")').last();
    await menu.getByText('Tambahkan ke Tanya Jawab (FAQ)').click(); await pg.waitForTimeout(2500);
    if (!(await menu.locator('input[type=checkbox]').nth(1).isChecked().catch(() => false)) && !(await pg.getByText(/Tanya Jawab|FAQ/i).count())) throw new Error('FAQ tidak aktif');
  };
  await step('UC-09_normal_7', async () => {
    await lina.goto(article); await lina.waitForLoadState('networkidle');
    await faqPublish(lina);
    await shot(lina, 'UC-09_normal_7', 'Artikel diterbitkan lewat Tambahkan ke Tanya Jawab (FAQ)');
  });
  await step('UC-09_8a', async () => {
    await kand(lina, '?status=pending');
    const btn = lina.locator('[data-hk-action=article]').first();
    await Promise.all([lina.waitForURL(/knowbaseitem/i, { timeout: 20000 }), btn.click()]); await lina.waitForLoadState('networkidle');
    stopAi();
    try { await faqPublish(lina); await lina.reload(); await lina.waitForLoadState('networkidle'); await lina.getByText(/Gagal memperbarui indeks/i).first().waitFor({ timeout: 8000 });
      await shot(lina, 'UC-09_8a', 'Layanan AI mati saat menerbitkan: gagal memperbarui indeks, indeks lama dipakai'); }
    finally { await startAi(); }
  });
  skip('UC-09_5a', 'dijalankan terpisah: node scripts/capture_alur.js --uc UC-09_5a (mengaktifkan LLM sementara lewat .env)');
  results.__article = article;
  await lina.context().close();
}

// ---- UC-09 5a: LLM lokal (Ollama qwen2.5:3b) diaktifkan sementara lewat .env; .env dikembalikan + halosis-ai di-restart
async function uc09_5a(browser) {
  const envFile = path.join(ROOT, '.env'), orig = fs.readFileSync(envFile, 'utf8');
  const tags = await (await fetch('http://localhost:11434/api/tags')).json().catch(() => ({ models: [] }));
  if (!(tags.models || []).some(m => m.name === 'qwen2.5:3b')) return skip('UC-09_5a', 'dilewati: Ollama/qwen2.5:3b tidak ada');
  fs.writeFileSync(envFile, orig.replace(/\n*$/, '\n') + 'LLM_PROVIDER=openai\nLLM_BASE_URL=http://host.docker.internal:11434/v1\nLLM_MODEL=qwen2.5:3b\n');
  try {
    sh('docker compose up -d --force-recreate halosis-ai'); await sleep(3000); for (let i = 0; i < 90 && !(await aiHealthy()); i++) await sleep(1000);
    const lina = await newPage(browser, 'lina');
    await step('UC-09_5a', async () => {
      await lina.goto(`${BASE}/plugins/halosis/Kandidat?status=pending`); await lina.waitForLoadState('networkidle');
      const b = lina.locator('[data-hk-action=article]').first();
      await Promise.all([lina.waitForURL(/knowbaseitem/i, { timeout: 120000 }), b.click()]);
      await lina.waitForLoadState('networkidle'); await lina.waitForTimeout(1500);
      await shot(lina, 'UC-09_5a', 'Draf disusun AI (qwen2.5:3b), wajib ditinjau');
    });
    await lina.context().close();
  } finally {
    fs.writeFileSync(envFile, orig);
    sh('docker compose up -d --force-recreate halosis-ai'); await sleep(3000); for (let i = 0; i < 90 && !(await aiHealthy()); i++) await sleep(1000);
  }
}

// ---- UC-10
async function uc10(browser) {
  await step('UC-10_1a', async () => {
    const p = await newPage(browser, 'rina');
    await p.goto(`${BASE}/plugins/halosis/front/config.form.php`); await p.waitForLoadState('networkidle');
    await shot(p, 'UC-10_1a', 'rina membuka alamat Pengaturan AI langsung: akses ditolak');
    await p.context().close();
  });
  const p = await newPage(browser, 'dimas');
  await openConfig(p);
  await step('UC-10_6a', async () => {
    await p.locator('button[name=preview_sla]').click(); await p.waitForLoadState('networkidle');
    await p.getByText(/Pilih SLA atau aturan SLA/i).first().waitFor();
    await p.getByText(/Pilih SLA atau aturan SLA/i).first().scrollIntoViewIfNeeded();
    await shot(p, 'UC-10_6a', 'Pratinjau SLA tanpa memilih SLA/target');
  });
  await openConfig(p);
  await step('UC-10_8a', async () => {
    const orig = await p.locator('input[name=service_url]').inputValue();
    await p.fill('input[name=service_url]', 'ftp://x');
    await Promise.all([p.waitForLoadState('networkidle'), p.locator('button[name=update]').click()]);
    await p.getByText(/harus diawali http/i).first().waitFor();
    await shot(p, 'UC-10_8a', 'URL layanan AI ftp://x ditolak');
    await openConfig(p);
    if ((await p.locator('input[name=service_url]').inputValue()) !== orig) throw new Error('URL efektif berubah');
  });
  await step('UC-10_8b', async () => {
    await openConfig(p);
    await p.locator('input[name=api_key]').fill('');
    await Promise.all([p.waitForLoadState('networkidle'), p.locator('button[name=update]').click()]);
    await shot(p, 'UC-10_8b', 'API key dikosongkan lalu Simpan: nilai lama tetap dipakai');
  });
  await step('UC-10_normal_8', async () => {
    await openConfig(p);
    await Promise.all([p.waitForLoadState('networkidle'), p.locator('button[name=update]').click()]);
    await p.getByText(/berhasil disimpan/i).first().waitFor();
    await shot(p, 'UC-10_normal_8', 'Konfigurasi (nilai sama) berhasil disimpan');
  });
  await p.context().close();
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
    if (WANT.has('UC-06')) await uc06(browser);
    if (WANT.has('UC-07')) await uc07(browser);
    if (WANT.has('UC-08')) await uc08(browser);
    if (WANT.has('UC-09')) await uc09(browser);
    if (WANT.has('UC-09_5a')) await uc09_5a(browser);
    if (WANT.has('UC-10')) await uc10(browser);
  } finally {
    await browser.close();
    if (!(await aiHealthy())) await startAi();
    fs.writeFileSync(resultsFile, JSON.stringify(results, null, 1));
  }
})().catch(e => { console.error(e.message); process.exit(1); });
