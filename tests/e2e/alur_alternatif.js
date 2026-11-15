// Uji alur alternatif use case (dokumen hal. 129–141) di aplikasi lokal, dengan data rekaan. Tiket uji dibuat lewat API
// (akun glpi), dijalankan lewat UI (Chromium headless), lalu DIHAPUS beserta baris plugin & notifikasi antrenya.
// Hanya mencetak LULUS/GAGAL per alur, tanpa isi tiket.
//
//   cd tests/e2e && npm install && node alur_alternatif.js        # butuh docker compose hidup & browser Playwright
//
// Alur: UC-01 4a / UC-02 5a (solusi tidak ditemukan → tawaran laporan), UC-02 mode pilihan (tawaran laporan tetap ada), UC-03 4a (judul < 5 karakter ditolak),
// UC-04 1a (layanan AI berhenti → tiket tersimpan tanpa saran, tombol "Buat saran AI"; layanan dinyalakan lagi),
// UC-05 S-2 (Tolak, alasan wajib), UC-05 S-1 (Ubah, alasan wajib), UC-06 2a (Kembalikan ke operator),
// UC-06 S-1 (status Menunggu), UC-07 5a (Refuse → tiket dibuka kembali), UC-09 5a (Jadikan artikel → draf tanpa target; LLM_PROVIDER=none → templat).
// UC-04 1a menghentikan container halosis-ai sebentar (docker compose stop/start).
const { chromium } = require('playwright-core');
const { execSync } = require('child_process');
const fs = require('fs'), os = require('os'), path = require('path');

const BASE = process.env.HALOSIS_URL || 'http://localhost:8080';
const PASSWORD = 'halosis';
const ROOT = path.resolve(__dirname, '../..');
const TEAM_MEMBER = { 'Tim Aplikasi Statistik': 'andi', 'Tim Identitas & Akses': 'fajar', 'Tim Jaringan': 'dedi', 'Tim Perangkat': 'rudi' };
const created = [];
const articles = [];  // [kandidat, artikel] dari UC-09 5a: artikel dihapus, kandidat dikembalikan ke "pending"
let started = null;  // waktu DB saat uji mulai (dipakai asersi UC-03)
let chatsBefore = null;  // ID chat sebelum uji: pembersihan hanya menghapus chat ber-ID baru

async function api() {
  const auth = 'Basic ' + Buffer.from('glpi:glpi').toString('base64');
  const token = (await (await fetch(`${BASE}/apirest.php/initSession`, { headers: { Authorization: auth } })).json()).session_token;
  const h = { 'Session-Token': token, 'Content-Type': 'application/json' };
  const call = async (method, p, body) => (await fetch(`${BASE}/apirest.php/${p}`, { method, headers: h, body: body && JSON.stringify(body) })).json();
  const profiles = await call('GET', 'Profile?range=0-100');
  await call('POST', 'changeActiveProfile', { profiles_id: profiles.find(p => p.name === 'Super-Admin').id });
  const users = Object.fromEntries((await call('GET', 'User?range=0-500')).map(u => [u.name, u.id]));
  return { call, users };
}

async function ticket(a, requester, title) {
  const r = await a.call('POST', 'Ticket', { input: { name: title, content: `${title}. Data uji otomatis.`, type: 1, _users_id_requester: a.users[requester] } });
  created.push(r.id);
  return r.id;
}

async function login(browser, user) {
  const page = await (await browser.newContext({ viewport: { width: 1400, height: 1000 } })).newPage();
  page.setDefaultTimeout(60000);  // halaman pertama sesudah layanan AI dinyalakan ulang (UC-04) bisa lambat
  await page.goto(BASE + '/');
  await page.fill('#login_name', user); await page.fill('#login_password', PASSWORD);
  await Promise.all([page.waitForLoadState('networkidle'), page.click('button[name=submit]')]);
  return page;
}

async function openTicket(page, id) {
  // Sekali ulang: navigasi pertama sesudah container dihentikan (UC-04) kadang macet di Docker Desktop
  for (let attempt = 1; ; attempt++) {
    try {
      await page.goto(`${BASE}/front/ticket.form.php?id=${id}`, { timeout: 30000 }); await page.waitForLoadState('networkidle');
      return;
    } catch (e) {
      if (attempt >= 2) throw e;
    }
  }
}

const body = async (page) => page.locator('body').innerText();

function sql(query) {
  return execSync(`docker compose exec -T db sh -c 'mysql -N -u"$MYSQL_USER" -p"$MYSQL_PASSWORD" "$MYSQL_DATABASE" 2>/dev/null'`,
    { cwd: ROOT, input: query }).toString().trim();
}

const aiHealthy = async () => fetch('http://localhost:8001/health').then(r => r.ok).catch(() => false);

function compose(args) {
  execSync(`docker compose ${args}`, { cwd: ROOT, stdio: 'ignore' });
}

async function startAi() {
  compose('start halosis-ai');
  for (let i = 0; i < 60 && !(await aiHealthy()); i++) await new Promise(r => setTimeout(r, 1000));
}

async function cleanup(a) {
  for (const [candidate, article] of articles) {
    await a.call('DELETE', `KnowbaseItem/${article}`, { input: { id: article }, force_purge: true });
    sql(`DELETE FROM glpi_plugin_halosis_kb_reviews WHERE knowbaseitems_id = ${article};
         UPDATE glpi_plugin_halosis_candidates SET status = 'pending', knowbaseitems_id = 0, users_id = 0, date_decision = NULL
          WHERE id = ${candidate};`);
  }
  if (chatsBefore) {
    // Hermetik: hanya percakapan dengan ID baru (tidak ada sebelum uji) yang dihapus; data demo tidak tersentuh.
    // Termasuk tiket yang dibuat lewat chat (UC-03); tiket tsb. ikut dihapus di bawah
    const baru = sql('SELECT id FROM glpi_plugin_halosis_chats;').split('\n').filter(Boolean).map(Number).filter(id => !chatsBefore.has(id));
    if (baru.length) {
      const c = baru.join(',');
      for (const id of sql(`SELECT tickets_id FROM glpi_plugin_halosis_chats WHERE id IN (${c}) AND tickets_id > 0;`).split('\n').filter(Boolean)) {
        created.push(Number(id));
      }
      sql(`DELETE FROM glpi_plugin_halosis_article_uses WHERE chats_id IN (${c}); DELETE FROM glpi_plugin_halosis_chats WHERE id IN (${c});`);
    }
  }
  if (created.length === 0) return;
  const ids = created.join(',');
  await a.call('DELETE', 'Ticket', { input: created.map(id => ({ id })), force_purge: true });
  sql(`DELETE FROM glpi_plugin_halosis_decisions WHERE tickets_id IN (${ids});
       DELETE FROM glpi_plugin_halosis_reassignments WHERE tickets_id IN (${ids});
       DELETE FROM glpi_plugin_halosis_triage_retries WHERE tickets_id IN (${ids});
       DELETE FROM glpi_plugin_halosis_suggestions WHERE tickets_id IN (${ids});
       DELETE FROM glpi_plugin_halosis_candidates WHERE source = 'ticket' AND tickets_id IN (${ids});
       DELETE FROM glpi_queuednotifications WHERE itemtype='Ticket' AND items_id IN (${ids});`);
}

(async () => {
  const cache = path.join(os.homedir(), 'Library/Caches/ms-playwright');
  const shell = fs.existsSync(cache) ? fs.readdirSync(cache).find(d => d.startsWith('chromium_headless_shell')) : null;
  const sub = shell && fs.readdirSync(path.join(cache, shell)).find(d => d.startsWith('chrome-headless-shell'));
  const browser = await chromium.launch(sub ? { executablePath: path.join(cache, shell, sub, 'chrome-headless-shell') } : {});
  const a = await api();
  started = sql('SELECT NOW();');
  chatsBefore = new Set(sql('SELECT id FROM glpi_plugin_halosis_chats;').split('\n').filter(Boolean).map(Number));
  const results = {};
  const run = async (name, fn) => {
    try { results[name] = (await fn()) ? 'LULUS' : 'GAGAL'; } catch (e) { results[name] = 'GAGAL (' + e.message.split('\n')[0].slice(0, 80) + ')'; }
  };

  try {
    await run('UC-01 4a / UC-02 5a solusi tidak ditemukan → tawaran laporan', async () => {
      const p = await login(browser, 'budi');
      // Percakapan terbuka dilanjutkan otomatis (30 menit); mulai yang baru supaya pilihan awal tampil
      const fresh = p.getByRole('button', { name: /Percakapan baru|New conversation/ }).first();
      if (await fresh.isVisible().catch(() => false)) { await fresh.click(); await p.waitForTimeout(1500); }
      await p.getByText('Laporkan masalah').first().click(); await p.waitForTimeout(500);
      const input = p.locator('[data-chat-form] textarea, [data-chat-form] input[type=text]').first();
      await input.fill('Cuaca di Bali besok pagi'); await input.press('Enter');  // mode tidak-ditemukan
      await p.locator('.hc-source').or(p.getByRole('button', { name: /Ya, buat laporan/ })).first().waitFor({ timeout: 30000 }).catch(() => {});
      const ok = await p.locator('.hc-source').count() === 0 && await p.getByRole('button', { name: /Ya, buat laporan/ }).count() > 0;
      await p.context().close(); return ok;
    });

    await run('UC-02 5b mode pilihan: "Apakah jawaban ini membantu?"; "Belum terselesaikan" → kartu laporan', async () => {
      const p = await login(browser, 'budi');
      const fresh = p.getByRole('button', { name: /Percakapan baru|New conversation/ }).first();
      if (await fresh.isVisible().catch(() => false)) { await fresh.click(); await p.waitForTimeout(1500); }
      await p.getByText('Laporkan masalah').first().click(); await p.waitForTimeout(500);
      const input = p.locator('[data-chat-form] textarea, [data-chat-form] input[type=text]').first();
      await input.fill('Kursi kantor saya patah'); await input.press('Enter');
      const notYet = p.getByRole('button', { name: /Belum terselesaikan/ }).first();
      await notYet.waitFor({ timeout: 30000 }).catch(() => {});
      // Perilaku baru (B1): kartu laporan langsung tidak tampil di mode pilihan; baru muncul setelah "Belum terselesaikan"
      const noDirect = await p.getByRole('button', { name: /Ya, buat laporan/ }).count() === 0;
      await notYet.click();
      const offer = p.getByRole('button', { name: /Ya, buat laporan/ }).first();
      await offer.waitFor({ timeout: 10000 }).catch(() => {});
      const ok = noDirect && await offer.isVisible();
      await p.context().close(); return ok;
    });

    await run('UC-03 4a judul laporan < 5 karakter ditolak', async () => {
      const p = await login(browser, 'budi');
      const fresh = p.getByRole('button', { name: /Percakapan baru|New conversation/ }).first();
      if (await fresh.isVisible().catch(() => false)) { await fresh.click(); await p.waitForTimeout(1500); }
      await p.getByText('Laporkan masalah').first().click(); await p.waitForTimeout(500);
      const input = p.locator('[data-chat-form] textarea, [data-chat-form] input[type=text]').first();
      await input.fill('Kursi kantor saya patah'); await input.press('Enter'); await p.waitForTimeout(6000);
      const notYet = p.getByRole('button', { name: /Belum terselesaikan/ }).first();   // 5b: kartu laporan setelah "Belum terselesaikan"
      if (await notYet.isVisible().catch(() => false)) { await notYet.click(); await p.waitForTimeout(500); }
      await p.getByRole('button', { name: /Ya, buat laporan/ }).first().click(); await p.waitForTimeout(500);
      const title = p.locator('form.hc-report input.hc-input');
      await title.fill('abc');
      const browserBlocks = !(await title.evaluate(el => el.checkValidity()));
      // Validasi server juga menolak (form dikirim tanpa validasi peramban)
      await p.locator('form.hc-report').evaluate(f => { f.noValidate = true; });
      await p.locator('form.hc-report button[type=submit]').click(); await p.waitForTimeout(2000);
      const serverRejects = /minimal 5 karakter|at least 5 characters/.test(await body(p)) && await p.locator('form.hc-report').count() === 1;
      await p.context().close();
      const made = sql(`SELECT COUNT(*) FROM glpi_plugin_halosis_chats WHERE users_id = ${a.users.budi} AND date_creation >= '${started}' AND tickets_id > 0;`);
      return browserBlocks && serverRejects && made === '0';
    });

    const [t1, t2, t3, t4, t5] = [
      await ticket(a, 'budi', 'FASIH gagal sinkron uji tolak'), await ticket(a, 'budi', 'FASIH gagal sinkron uji ubah'),
      await ticket(a, 'siti', 'FASIH gagal sinkron uji kembalikan'), await ticket(a, 'budi', 'FASIH gagal sinkron uji refuse'),
      await ticket(a, 'siti', 'FASIH gagal sinkron uji menunggu'),
    ];
    const rina = await login(browser, 'rina');

    await run('UC-04 1a layanan AI berhenti → tiket tanpa saran, tombol "Buat saran AI"', async () => {
      compose('stop halosis-ai');
      let t0, saved, noSuggestion, button;
      try {
        t0 = await ticket(a, 'budi', 'FASIH gagal sinkron uji AI mati');
        saved = (await a.call('GET', `Ticket/${t0}`)).id === t0;
        noSuggestion = sql(`SELECT COUNT(*) FROM glpi_plugin_halosis_suggestions WHERE tickets_id = ${t0};`) === '0';
        await openTicket(rina, t0);
        button = await rina.locator('[data-action=generate]').isVisible();
      } finally {
        await startAi();
      }
      // Setelah layanan hidup lagi, tombol menghasilkan saran
      await rina.click('[data-action=generate]'); await rina.waitForTimeout(4000);
      const recovered = sql(`SELECT COUNT(*) FROM glpi_plugin_halosis_suggestions WHERE tickets_id = ${t0};`) !== '0';
      return saved && noSuggestion && button && recovered && await aiHealthy();
    });

    await run('UC-05 S-2 Tolak (alasan wajib)', async () => {
      await openTicket(rina, t1);
      await rina.click('[data-action=show-reject]');
      await rina.fill('#halosis-reject-reason', 'abc');
      const blocked = await rina.locator('[data-action=reject]').isDisabled();
      await rina.fill('#halosis-reject-reason', 'Bukan masalah FASIH, uji otomatis');
      await rina.click('[data-action=reject]'); await rina.waitForTimeout(2000);
      await openTicket(rina, t1);
      return blocked && /Ditolak/.test(await body(rina));
    });

    await run('UC-05 S-1 Ubah (alasan wajib)', async () => {
      await openTicket(rina, t2);
      await rina.click('[data-action=show-modify]');
      const sel = rina.locator('#halosis-urgency');
      const current = await sel.inputValue();
      const other = (await sel.locator('option').evaluateAll(os => os.map(o => o.value))).find(v => v && v !== current);
      await sel.selectOption(other);
      const blocked = await rina.locator('[data-action=modify]').isDisabled();
      await rina.fill('#halosis-modify-reason', 'Urgensi dikoreksi, uji otomatis');
      await rina.click('[data-action=modify]'); await rina.waitForTimeout(2000);
      await openTicket(rina, t2);
      return blocked && /Diubah/.test(await body(rina));
    });

    await run('UC-06 2a Kembalikan ke operator (salah tim)', async () => {
      await openTicket(rina, t3);
      await rina.click('[data-action=accept]'); await rina.waitForTimeout(2000);
      const groups = await a.call('GET', `Ticket/${t3}/Group_Ticket`);
      const assigned = Array.isArray(groups) ? groups.find(g => g.type === 2) : null;
      if (!assigned) return false;
      const name = (await a.call('GET', `Group/${assigned.groups_id}`)).name;
      const tech = TEAM_MEMBER[name];
      if (!tech) throw new Error('tim tanpa akun uji');
      const p = await login(browser, tech);
      await openTicket(p, t3);
      await p.click('[data-action=show-return]');
      await p.fill('#halosis-return-reason', 'Salah tim, uji otomatis');
      await p.click('[data-action=return]'); await p.waitForTimeout(2000);
      await p.context().close();
      const t = await a.call('GET', `Ticket/${t3}`);
      const left = await a.call('GET', `Ticket/${t3}/Group_Ticket`);
      return t.status === 1 && !(Array.isArray(left) && left.some(g => g.type === 2));
    });

    await run('UC-06 S-1 status Menunggu', async () => {
      await openTicket(rina, t5);
      await rina.click('[data-action=accept]'); await rina.waitForTimeout(2000);
      const groups = await a.call('GET', `Ticket/${t5}/Group_Ticket`);
      const assigned = Array.isArray(groups) ? groups.find(g => g.type === 2) : null;
      if (!assigned) return false;
      const tech = TEAM_MEMBER[(await a.call('GET', `Group/${assigned.groups_id}`)).name];
      if (!tech) throw new Error('tim tanpa akun uji');
      const p = await login(browser, tech);
      await openTicket(p, t5);
      await p.locator('select[name=status]').first().evaluate(el => { el.value = '4'; el.dispatchEvent(new Event('change', { bubbles: true })); });
      await Promise.all([p.waitForLoadState('networkidle'), p.locator('button[name=update]').first().click()]);
      await p.waitForTimeout(1000);
      await p.context().close();
      return (await a.call('GET', `Ticket/${t5}`)).status === 4;
    });

    await run('UC-07 5a Refuse dengan alasan → dibuka kembali', async () => {
      await openTicket(rina, t4);
      await rina.click('[data-action=accept]'); await rina.waitForTimeout(2000);
      await a.call('POST', 'ITILSolution', { input: { itemtype: 'Ticket', items_id: t4, content: 'Solusi uji otomatis.' } });
      const p = await login(browser, 'budi');
      await openTicket(p, t4);
      const editor = p.frameLocator('form:has(button[name=add_reopen]) iframe').first().locator('body');
      await editor.click(); await editor.type('Masih gagal sinkron, uji otomatis');
      await p.locator('button[name=add_reopen]').first().click();
      await p.waitForLoadState('networkidle'); await p.waitForTimeout(1500);
      await p.context().close();
      const t = await a.call('GET', `Ticket/${t4}`);
      return [2, 3].includes(t.status);
    });
    await rina.context().close();

    await run('UC-09 5a Jadikan artikel → draf tanpa target', async () => {
      const p = await login(browser, 'lina');
      await p.goto(`${BASE}/plugins/halosis/Kandidat`); await p.waitForLoadState('networkidle');
      const btn = p.locator('[data-hk-action=article]').first();
      const candidate = Number(await btn.getAttribute('data-id'));
      await Promise.all([p.waitForURL(/knowbaseitem/i, { timeout: 15000 }), btn.click()]);
      await p.context().close();
      const article = Number(sql(`SELECT knowbaseitems_id FROM glpi_plugin_halosis_candidates WHERE id = ${candidate} AND status = 'article';`) || 0);
      if (!article) return false;
      articles.push([candidate, article]);
      const targets = sql(`SELECT (SELECT COUNT(*) FROM glpi_entities_knowbaseitems WHERE knowbaseitems_id = ${article})
                                + (SELECT COUNT(*) FROM glpi_knowbaseitems_profiles WHERE knowbaseitems_id = ${article})
                                + (SELECT COUNT(*) FROM glpi_groups_knowbaseitems WHERE knowbaseitems_id = ${article})
                                + (SELECT COUNT(*) FROM glpi_knowbaseitems_users WHERE knowbaseitems_id = ${article});`);
      return targets === '0';
    });

    await run('UC-09 5a LLM_PROVIDER=none → draf memakai templat, tanpa label AI', async () => {
      const r = await fetch('http://localhost:8001/kandidat/draf', { method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ judul: 'Uji', masalah: 'Data uji otomatis', solusi: 'Data uji otomatis', sumber: [] }) });
      if (!r.ok || (await r.json()).draf !== null) return false;
      const article = articles.at(-1)?.[1];
      if (!article) return false;
      const answer = sql(`SELECT answer FROM glpi_knowbaseitems WHERE id = ${article};`);
      return /Draf dari Kandidat|Draft from Knowledge candidates/i.test(answer) && !answer.includes('Disusun AI');
    });
  } finally {
    await cleanup(a);
    await browser.close();
  }
  let failed = 0;
  for (const [name, result] of Object.entries(results)) { console.log(`${result.padEnd(6)} ${name}`); failed += result.startsWith('LULUS') ? 0 : 1; }
  console.log(`Data uji dihapus: ${created.length} tiket, ${articles.length} artikel draf`);
  process.exit(failed ? 1 : 0);
})().catch(e => { console.error(e.message); process.exit(1); });
