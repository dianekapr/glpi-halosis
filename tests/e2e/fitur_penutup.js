// Uji fitur penutup 🟡 (UC-10 pratinjau SLA, FR-04 pola permintaan, UC-04 pemecah seri beban kerja, E19 pengingat
// progres, E15 ringkasan deskripsi) di aplikasi lokal dengan data rekaan. Tiket uji dibuat lewat API (akun glpi),
// diperiksa lewat UI (Chromium headless) & DB (hitungan saja), lalu DIHAPUS beserta Problem pola, baris plugin,
// notifikasi antre, pengingat, dan Catatan perubahan pengaturan. Pengaturan yang diubah dikembalikan.
//
//   cd tests/e2e && npm install && node fitur_penutup.js        # butuh docker compose hidup & browser Playwright
const { chromium } = require('playwright-core');
const { execSync } = require('child_process');
const fs = require('fs'), os = require('os'), path = require('path');

const BASE = process.env.HALOSIS_URL || 'http://localhost:8080';
const PASSWORD = 'halosis';
const ROOT = path.resolve(__dirname, '../..');
const created = [];
const problems = [];

async function api() {
  const auth = 'Basic ' + Buffer.from('glpi:glpi').toString('base64');
  const token = (await (await fetch(`${BASE}/apirest.php/initSession`, { headers: { Authorization: auth } })).json()).session_token;
  const h = { 'Session-Token': token, 'Content-Type': 'application/json' };
  const call = async (method, p, body) => (await fetch(`${BASE}/apirest.php/${p}`, { method, headers: h, body: body && JSON.stringify(body) })).json();
  const profiles = await call('GET', 'Profile?range=0-100');
  await call('POST', 'changeActiveProfile', { profiles_id: profiles.find(p => p.name === 'Super-Admin').id });
  const users = Object.fromEntries((await call('GET', 'User?range=0-500')).map(u => [u.name, u.id]));
  const groups = Object.fromEntries((await call('GET', 'Group?range=0-200')).map(g => [g.name, g.id]));
  return { call, users, groups };
}

async function ticket(a, input) {
  const r = await a.call('POST', 'Ticket', { input: { type: 1, ...input } });
  created.push(r.id);
  return r.id;
}

async function login(browser, user) {
  const page = await (await browser.newContext({ viewport: { width: 1400, height: 1000 } })).newPage();
  page.setDefaultTimeout(60000);
  await page.goto(BASE + '/');
  await page.fill('#login_name', user); await page.fill('#login_password', PASSWORD);
  await Promise.all([page.waitForLoadState('networkidle'), page.click('button[name=submit]')]);
  return page;
}

// Halaman Pengaturan AI meminta konfirmasi ulang (area API key)
async function openConfig(page) {
  await page.goto(`${BASE}/plugins/halosis/front/config.form.php`); await page.waitForLoadState('networkidle');
  if (await page.locator('[data-halosis-config]').count() === 0) {
    // Akun lokal: isi password; akun SSO: cukup konfirmasi
    if (await page.locator('input[type=password]').count() > 0) await page.locator('input[type=password]').first().fill(PASSWORD);
    await Promise.all([page.waitForLoadState('networkidle'), page.locator('form[action*="ReAuth"] button[type=submit]').click()]);
    await page.goto(`${BASE}/plugins/halosis/front/config.form.php`); await page.waitForLoadState('networkidle');
  }
}

async function setIncludeRequests(page, on) {
  await openConfig(page);
  await page.locator('input[name=pattern_include_requests][type=checkbox]').evaluate((el, v) => { el.checked = v; }, on);
  await track(() => Promise.all([page.waitForLoadState('networkidle'), page.locator('button[name=update]').click()]));  // Catatan "pengaturan diubah"
}

function sql(query) {
  return execSync(`docker compose exec -T db sh -c 'mysql -N -u"$MYSQL_USER" -p"$MYSQL_PASSWORD" "$MYSQL_DATABASE" 2>/dev/null'`,
    { cwd: ROOT, input: query }).toString().trim();
}

function cron(task) {
  execSync(`docker compose exec -T glpi php front/cron.php --force ${task}`, { cwd: ROOT, stdio: 'ignore' });
}

// Pembersihan HERMETIK: hanya objek dengan ID yang dicatat tes ini (tiket, SLA/SLM uji, pengingat Catatan, chat) atau
// Problem yang seluruh tiket anggotanya adalah tiket uji. Data lain (termasuk data demo [DEMO]) tidak disentuh.
const slaIds = [], slmIds = [], reminderIds = [];
let chatsBefore = null;
const reminderSet = () => new Set(ids(sql("SELECT id FROM glpi_reminders WHERE name LIKE 'HaloSIS:%';")));
// Catatan audit (Pengingat) yang muncul akibat aksi tes ini dicatat ID-nya: dibuat tes = ada sesudah, tidak ada sebelum
const track = async fn => { const before = reminderSet(); const r = await fn(); for (const id of reminderSet()) if (!before.has(id)) reminderIds.push(id); return r; };
const ids = q => q.split('\n').filter(Boolean).map(Number);
const chatIds = () => new Set(ids(sql('SELECT id FROM glpi_plugin_halosis_chats;')));

async function cleanup(a) {
  const list = created.join(',') || '0';
  if (created.length) {
    // Problem pola yang dibuat tes = Problem yang semua tiket anggotanya adalah tiket uji
    for (const id of ids(sql(`SELECT problems_id FROM glpi_problems_tickets GROUP BY problems_id
                               HAVING SUM(tickets_id NOT IN (${list})) = 0 AND SUM(tickets_id IN (${list})) > 0;`))) {
      problems.push(id);
    }
  }
  if (reminderIds.length) {
    const r = reminderIds.join(',');
    sql(`DELETE FROM glpi_profiles_reminders WHERE reminders_id IN (${r}); DELETE FROM glpi_reminders WHERE id IN (${r});`);
  }
  if (problems.length) {
    const p = problems.join(',');
    await a.call('DELETE', 'Problem', { input: problems.map(id => ({ id })), force_purge: true });
    sql(`DELETE FROM glpi_plugin_halosis_patterns WHERE problems_id IN (${p});
         DELETE FROM glpi_problems_tickets WHERE problems_id IN (${p});
         DELETE FROM glpi_queuednotifications WHERE itemtype = 'Problem' AND items_id IN (${p});`);
  }
  if (created.length) {
    await a.call('DELETE', 'Ticket', { input: created.map(id => ({ id })), force_purge: true });
    sql(`DELETE FROM glpi_plugin_halosis_decisions WHERE tickets_id IN (${list});
         DELETE FROM glpi_plugin_halosis_reassignments WHERE tickets_id IN (${list});
         DELETE FROM glpi_plugin_halosis_triage_retries WHERE tickets_id IN (${list});
         DELETE FROM glpi_plugin_halosis_suggestions WHERE tickets_id IN (${list});
         DELETE FROM glpi_plugin_halosis_progress_reminders WHERE tickets_id IN (${list});
         DELETE FROM glpi_problems_tickets WHERE tickets_id IN (${list});
         DELETE FROM glpi_queuednotifications WHERE itemtype = 'Ticket' AND items_id IN (${list});`);
  }
  if (slaIds.length) await track(() => a.call('DELETE', 'SLA', { input: slaIds.map(id => ({ id })), force_purge: true }));
  if (slmIds.length) await track(() => a.call('DELETE', 'SLM', { input: slmIds.map(id => ({ id })), force_purge: true }));
  if (reminderIds.length) {  // Catatan yang timbul dari penghapusan SLA/SLM uji di atas
    const r = reminderIds.join(',');
    sql(`DELETE FROM glpi_profiles_reminders WHERE reminders_id IN (${r}); DELETE FROM glpi_reminders WHERE id IN (${r});`);
  }
  if (chatsBefore) {
    const baru = [...chatIds()].filter(id => !chatsBefore.has(id));  // chat yang dibuat langkah UI E20/E21
    if (baru.length) {
      const c = baru.join(',');
      sql(`DELETE FROM glpi_plugin_halosis_article_uses WHERE chats_id IN (${c}); DELETE FROM glpi_plugin_halosis_chats WHERE id IN (${c});`);
    }
  }
}

const LONG = [
  'Aplikasi survei gagal sinkron sejak pagi untuk seluruh petugas lapangan di kabupaten.',
  'Kami sudah mencoba menutup dan membuka kembali perangkat di ruangan kantor beberapa kali.',
  'Pesan galat sinkron muncul setiap kali petugas menekan tombol kirim pada aplikasi survei.',
  'Kontak saya uji.pegawai@contoh.go.id atau 081234567890 bila perlu konfirmasi lebih lanjut.',
  'Rapat koordinasi pagi ini berjalan seperti biasa di aula lantai dua bersama seluruh tim.',
  'Beberapa petugas juga melaporkan baterai perangkat cepat habis ketika aplikasi dibuka lama.',
  'Kami membutuhkan data masuk sebelum batas waktu pengiriman minggu ini agar laporan tidak terlambat.',
  'Mohon bantuan agar sinkron aplikasi survei kembali normal secepatnya untuk seluruh petugas.',
].join(' ').repeat(2);

(async () => {
  const cache = path.join(os.homedir(), 'Library/Caches/ms-playwright');
  const shell = fs.existsSync(cache) ? fs.readdirSync(cache).find(d => d.startsWith('chromium_headless_shell')) : null;
  const sub = shell && fs.readdirSync(path.join(cache, shell)).find(d => d.startsWith('chrome-headless-shell'));
  const browser = await chromium.launch(sub ? { executablePath: path.join(cache, shell, sub, 'chrome-headless-shell') } : {});
  const a = await api();
  chatsBefore = chatIds();
  const results = {};
  const run = async (name, fn) => {
    try { results[name] = (await fn()) ? 'LULUS' : 'GAGAL'; } catch (e) { results[name] = 'GAGAL (' + e.message.split('\n')[0].slice(0, 80) + ')'; }
  };

  let dimas = null;
  try {
    dimas = await login(browser, 'dimas');

    await run('UC-10 pratinjau target SLA (tanpa menyimpan)', async () => {
      // Hermetik: SLM + SLA penyelesaian milik tes dan 3 tiket uji yang memakainya; pratinjau hanya menghitung tiket ber-SLA itu.
      // Target baru 1 menit → semua tiket uji (dibuat > 1 menit lalu) jadi terlewati.
      const slm = (await track(() => a.call('POST', 'SLM', { input: { name: 'UJI-E2E SLM' } }))).id; slmIds.push(slm);
      const sla = (await track(() => a.call('POST', 'SLA', { input: { name: 'UJI-E2E SLA TTR', slms_id: slm, type: 0, number_time: 8, definition_time: 'hour' } }))).id; slaIds.push(sla);
      for (const t of ['Uji pratinjau SLA satu', 'Uji pratinjau SLA dua', 'Uji pratinjau SLA tiga']) {
        const id = await ticket(a, { name: t, content: `${t}. Data uji otomatis.`, _users_id_requester: a.users.budi, slas_id_ttr: sla });
        // Aturan tiket menimpa SLA saat dibuat → pasang SLA uji langsung; usia pasti > 1 menit
        sql(`UPDATE glpi_tickets SET slas_id_ttr = ${sla}, date = NOW() - INTERVAL 1 HOUR, time_to_resolve = NOW() + INTERVAL 7 HOUR WHERE id = ${id};`);
      }
      const active = sql(`SELECT COUNT(*) FROM glpi_tickets WHERE is_deleted = 0 AND status < 5 AND slas_id_ttr = ${sla};`);
      const before = sql(`SELECT CONCAT(number_time, definition_time) FROM glpi_slas WHERE id = ${sla};`);
      await openConfig(dimas);
      await dimas.selectOption('#halosis_sla_target', `sla:${sla}`);
      await dimas.fill('#halosis_sla_number', '1'); await dimas.selectOption('select[name=preview_sla_unit]', 'minute');
      await Promise.all([dimas.waitForLoadState('networkidle'), dimas.click('button[name=preview_sla]')]);
      const box = await dimas.locator('[data-halosis-sla-result]').innerText();
      const overdueNew = Number((await dimas.locator('[data-halosis-sla-result] tbody tr:nth-child(2) td:nth-child(4)').innerText()).trim());
      const after = sql(`SELECT CONCAT(number_time, definition_time) FROM glpi_slas WHERE id = ${sla};`);
      return active === '3' && box.includes(`${active} tiket aktif terdampak`) && overdueNew === Number(active) && before === after;
    });

    await run('UC-10 pratinjau aturan SLA (SLA pengganti respons & penyelesaian)', async () => {
      // Aturan SLA menetapkan SLA respons & penyelesaian; jenis SLA pengganti menentukan aksi yang dipratinjau
      const rule = sql(`SELECT r.id FROM glpi_rules r JOIN glpi_ruleactions a ON a.rules_id = r.id
                         WHERE r.is_active = 1 AND a.field = 'slas_id_ttr' ORDER BY r.ranking LIMIT 1;`);
      const [ttr, tto] = [sql('SELECT id FROM glpi_slas WHERE type = 0 ORDER BY id LIMIT 1;'), sql('SELECT id FROM glpi_slas WHERE type = 1 ORDER BY id LIMIT 1;')];
      const labels = [];
      for (const replacement of [ttr, tto]) {
        await dimas.selectOption('#halosis_sla_target', `rule:${rule}`);
        await dimas.selectOption('#halosis_sla_new', replacement);
        await Promise.all([dimas.waitForLoadState('networkidle'), dimas.click('button[name=preview_sla]')]);
        labels.push(await dimas.locator('[data-halosis-sla-result]').innerText());
      }
      return labels.every(t => /tiket aktif terdampak/.test(t)) && labels[0] !== labels[1];
    });

    await run('FR-04 permintaan: mati → tanpa pola; aktif → "Pola permintaan"', async () => {
      for (const [u, t] of [['budi', 'Permintaan akun VPN baru untuk pegawai'], ['siti', 'Permintaan akun VPN baru untuk staf'],
                            ['maya', 'Permintaan akun VPN baru untuk petugas']]) {
        await ticket(a, { name: t, content: `${t}. Data uji otomatis.`, type: 2, _users_id_requester: a.users[u] });
      }
      const ids = created.slice(-3).join(',');
      const linked = () => sql(`SELECT COUNT(DISTINCT problems_id) FROM glpi_problems_tickets WHERE tickets_id IN (${ids});`);
      cron('IncidentPattern');
      const offNone = linked() === '0';
      await setIncludeRequests(dimas, true);
      cron('IncidentPattern');
      const name = sql(`SELECT p.name FROM glpi_problems p JOIN glpi_problems_tickets pt ON pt.problems_id = p.id
                         WHERE pt.tickets_id IN (${ids}) LIMIT 1;`);
      await setIncludeRequests(dimas, false);
      const restored = sql(`SELECT value FROM glpi_configs WHERE context = 'plugin:halosis' AND name = 'pattern_include_requests';`) === '0';
      return offNone && linked() === '1' && name.startsWith('Pola permintaan') && restored;
    });

    await run('UC-04 beban kerja memutus seri (selisih < 5 poin) + alasan di panel', async () => {
      // Hermetik: beban tim dikendalikan tes. Tiket pengintai mengungkap 2 kandidat teratas; tes menambah tiket uji ber-tim
      // kandidat #1 sampai bebannya lebih besar dari kandidat #2, lalu tiket sebenarnya dibuat (semua dibersihkan lewat ID).
      const loadOf = gid => Number(sql(`SELECT COUNT(*) FROM glpi_groups_tickets gt JOIN glpi_tickets t ON t.id = gt.tickets_id
                                        WHERE gt.groups_id = ${gid} AND gt.type = 2 AND t.is_deleted = 0 AND t.status < 5;`));
      const probe = await ticket(a, { name: 'Tidak bisa login aplikasi', content: 'Tidak bisa login aplikasi', _users_id_requester: a.users.budi });
      const pc = JSON.parse(sql(`SELECT candidates FROM glpi_plugin_halosis_suggestions WHERE tickets_id = ${probe};`));
      if (pc.length > 1 && pc[0].groups_id > 0 && pc[1].groups_id > 0 && pc[0].groups_id !== pc[1].groups_id) {
        for (let n = loadOf(pc[1].groups_id) - loadOf(pc[0].groups_id) + 1; n > 0; n--) {
          await ticket(a, { name: 'Uji beban tim', content: 'Data uji otomatis.', _groups_id_assign: pc[0].groups_id, _users_id_requester: a.users.siti });
        }
      }
      const t = await ticket(a, { name: 'Tidak bisa login aplikasi', content: 'Tidak bisa login aplikasi', _users_id_requester: a.users.budi });
      const [candidates, group] = sql(`SELECT candidates, groups_id FROM glpi_plugin_halosis_suggestions WHERE tickets_id = ${t};`).split('\t');
      const c = JSON.parse(candidates);
      const active = gid => Number(sql(`SELECT COUNT(*) FROM glpi_groups_tickets gt JOIN glpi_tickets t ON t.id = gt.tickets_id
                                        WHERE gt.groups_id = ${gid} AND gt.type = 2 AND t.is_deleted = 0 AND t.status < 5;`));
      const tie = c.length > 1 && c[0].groups_id > 0 && c[1].groups_id > 0 && c[0].groups_id !== c[1].groups_id
        && c[0].confidence - c[1].confidence < 5 && active(c[1].groups_id) < active(c[0].groups_id);
      const rina = await login(browser, 'rina');
      await rina.goto(`${BASE}/front/ticket.form.php?id=${t}`); await rina.waitForLoadState('networkidle');
      const shown = await rina.locator('[data-halosis-tiebreak]').count() > 0;
      await rina.context().close();
      if (!tie) throw new Error('data tidak memicu seri (cek beban tim)');
      return shown && Number(group) === c[1].groups_id;
    });

    await run('E19 pengingat progres > 5 hari kerja, sekali per periode', async () => {
      const assign = { _groups_id_assign: a.groups['Tim Jaringan'], _users_id_assign: a.users.dedi, _users_id_requester: a.users.siti };
      const old = await ticket(a, { name: 'VPN putus uji pengingat', content: 'Data uji otomatis.', ...assign });
      const fresh = await ticket(a, { name: 'VPN putus uji tanpa pengingat', content: 'Data uji otomatis.', ...assign });
      // Tanggal dibuat/diambil dimundurkan: 14 hari (> 5 hari kerja) dan 2 hari (≤ 5 hari kerja)
      sql(`UPDATE glpi_tickets SET date = NOW() - INTERVAL 14 DAY, takeintoaccountdate = NOW() - INTERVAL 14 DAY, status = 2 WHERE id = ${old};
           UPDATE glpi_tickets SET date = NOW() - INTERVAL 2 DAY, takeintoaccountdate = NOW() - INTERVAL 2 DAY, status = 2 WHERE id = ${fresh};`);
      const queued = id => Number(sql(`SELECT COUNT(*) FROM glpi_queuednotifications WHERE event = 'halosis_progress' AND items_id = ${id};`));
      cron('ProgressReminder');
      const first = queued(old);
      cron('ProgressReminder');
      return first > 0 && queued(old) === first && queued(fresh) === 0;
    });

    await run('E15 ringkasan 3 kalimat untuk deskripsi > 150 kata (tersamar)', async () => {
      const long = await ticket(a, { name: 'Aplikasi survei gagal sinkron uji ringkasan', content: LONG, _users_id_requester: a.users.budi });
      const short = await ticket(a, { name: 'Printer macet uji ringkasan', content: 'Printer lantai 2 macet, mohon dicek.', _users_id_requester: a.users.budi });
      const rina = await login(browser, 'rina');
      await rina.goto(`${BASE}/front/ticket.form.php?id=${long}`); await rina.waitForLoadState('networkidle');
      const items = await rina.locator('[data-halosis-summary] li').count();
      const text = await rina.locator('[data-halosis-summary]').innerText();
      await rina.goto(`${BASE}/front/ticket.form.php?id=${short}`); await rina.waitForLoadState('networkidle');
      const none = await rina.locator('[data-halosis-summary]').count() === 0;
      await rina.context().close();
      return items === 3 && !text.includes('@contoh.go.id') && !text.includes('081234567890') && none;
    });

    await run('E20 kartu Laporkan masalah & Ajukan permintaan memberi respons terlihat', async () => {
      const budi = await login(browser, 'budi');
      await budi.waitForLoadState('networkidle');
      // Percakapan terbuka dilanjutkan otomatis; mulai yang baru supaya pilihan awal tampil
      const fresh = budi.getByRole('button', { name: /Percakapan baru|New conversation/ }).first();
      if (await fresh.isVisible().catch(() => false)) { await fresh.click(); await budi.waitForTimeout(1500); }
      const tickets = () => Number(sql('SELECT COUNT(*) FROM glpi_tickets;'));
      const before = tickets();
      await budi.getByText('Laporkan masalah').first().click(); await budi.waitForTimeout(500);
      const focused = await budi.evaluate(() => document.activeElement && document.activeElement.matches('[data-chat-form] textarea'));
      const flash = await budi.locator('[data-chat-form].hc-flash').count() === 1;
      const msg = await budi.locator('[data-chat-report-prompt]').innerText();
      await budi.getByText('Laporkan masalah').first().click(); await budi.waitForTimeout(300);
      const once = await budi.locator('[data-chat-report-prompt]').count() === 1;
      const noTicket = tickets() === before;
      // Ajukan permintaan: tautan ke form katalog, dengan penanda klik diterima sebelum pindah halaman
      const card = budi.locator('[data-chat-request]');
      const href = await card.getAttribute('href');
      await budi.evaluate(() => document.querySelector('[data-chat-request]').addEventListener('click', e => e.preventDefault(), true));
      await card.click();
      const loading = await card.evaluate(el => el.classList.contains('hc-loading') && /Membuka formulir/.test(el.innerText));
      await budi.context().close();
      return focused && flash && once && noTicket && /Ceritakan masalah yang Anda alami\. Saya carikan solusinya dulu; bila belum selesai, saya buatkan laporan\./.test(msg)
        && /\/Form\/Render\/\d+/.test(href || '') && loading;
    });

    await run('E21 tautan sumber: artikel KB membuka isi artikel, katalog layanan membuka form kategorinya (tab sama)', async () => {
      const budi = await login(browser, 'budi');
      const fresh = budi.getByRole('button', { name: /Percakapan baru|New conversation/ }).first();
      if (await fresh.isVisible().catch(() => false)) { await fresh.click(); await budi.waitForTimeout(1500); }
      const chatUrl = budi.url();
      const input = budi.locator('[data-chat-form] textarea, [data-chat-form] input[type=text]').first();
      await input.fill('Lupa kata sandi SSO'); await input.press('Enter');
      const kb = budi.locator('a[data-chat-source="kb"]').first();
      const service = budi.locator('a[data-chat-source="service"]').first();
      await kb.waitFor({ timeout: 30000 });
      const answer = await budi.locator('.hc-bubble-ai').last().innerText();
      // Jawaban dari artikel KB, tanpa kalimat judul ganda; layanan sebagai tautan tambahan
      const fromKb = /Berdasarkan artikel/.test(answer) && !/Layanan Akun/.test(answer);
      const label = /Ajukan lewat layanan/.test(await service.innerText());
      const sameTab = await kb.getAttribute('target') === '_self' && await service.getAttribute('target') === '_self';
      const href = await service.getAttribute('href');
      const category = sql("SELECT id FROM glpi_itilcategories WHERE completename LIKE '%SSO / Login%' LIMIT 1;");
      const direct = /\/Form\/Render\/\d+\?[0-9a-f-]+=\d+/.test(href || '') && href.endsWith(`=${category}`);
      const pages = budi.context().pages().length;
      await Promise.all([budi.waitForURL(/\/Form\/Render\//), service.click()]);
      await budi.waitForLoadState('networkidle');
      const formOk = budi.context().pages().length === pages && /SSO \/ Login/.test(await budi.locator('main, body').first().innerText());
      // Kembali ke chat lalu buka artikel KB: isi artikel tampil di tab yang sama
      await budi.goto(chatUrl); await budi.waitForLoadState('networkidle');
      const kbAgain = budi.locator('a[data-chat-source="kb"]').first();
      await kbAgain.waitFor({ timeout: 30000 });
      await Promise.all([budi.waitForLoadState('load'), kbAgain.click()]);
      await budi.waitForLoadState('networkidle');
      const article = /Tunggu 15 menit|Lupa password/.test(await budi.locator('body').innerText());
      await budi.context().close();
      return fromKb && label && sameTab && direct && formOk && article;
    });
  } finally {
    if (dimas) {
      // Pengaturan selalu dikembalikan, juga bila uji FR-04 gagal di tengah
      if (sql(`SELECT value FROM glpi_configs WHERE context = 'plugin:halosis' AND name = 'pattern_include_requests';`) !== '0') {
        await setIncludeRequests(dimas, false).catch(() => {});
      }
      await dimas.context().close();
    }
    await cleanup(a);
    await browser.close();
  }
  let failed = 0;
  for (const [name, result] of Object.entries(results)) { console.log(`${result.padEnd(6)} ${name}`); failed += result.startsWith('LULUS') ? 0 : 1; }
  console.log(`Data uji dihapus: ${created.length} tiket, ${problems.length} Problem pola`);
  process.exit(failed ? 1 : 0);
})().catch(e => { console.error(e.message); process.exit(1); });
