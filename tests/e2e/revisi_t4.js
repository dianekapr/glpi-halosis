// Uji perbaikan Tugas 4 (K-02, K-05, K-13, K-24) di aplikasi lokal dengan data rekaan. Tiket & percakapan uji dihapus
// setelah uji. Hanya mencetak LULUS/GAGAL.
//
//   cd tests/e2e && node revisi_t4.js        # butuh docker compose hidup & browser Playwright (CH=chrome: Chrome sistem)
const { chromium } = require('playwright-core');
const { execSync } = require('child_process');
const fs = require('fs'), os = require('os'), path = require('path');

const BASE = process.env.HALOSIS_URL || 'http://localhost:8080';
const PASSWORD = 'halosis';
const ROOT = path.resolve(__dirname, '../..');
const created = [];
const candidates = [];
let started = null;

function sql(query) {
  return execSync(`docker compose exec -T db sh -c 'mysql -N -u"$MYSQL_USER" -p"$MYSQL_PASSWORD" "$MYSQL_DATABASE" 2>/dev/null'`,
    { cwd: ROOT, input: query }).toString().trim();
}

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

async function login(browser, user) {
  const page = await (await browser.newContext({ viewport: { width: 1400, height: 1000 } })).newPage();
  page.setDefaultTimeout(60000);
  await page.goto(BASE + '/');
  await page.fill('#login_name', user); await page.fill('#login_password', PASSWORD);
  await Promise.all([page.waitForLoadState('networkidle'), page.click('button[name=submit]')]);
  return page;
}

const body = async (page) => page.locator('body').innerText();

async function cleanup(a) {
  if (started) sql(`DELETE FROM glpi_forms_destinations_answerssets_formdestinationitems WHERE forms_answerssets_id IN
                      (SELECT id FROM glpi_forms_answerssets WHERE date_creation >= '${started}');
                    DELETE FROM glpi_forms_answerssets WHERE date_creation >= '${started}';`);
  if (candidates.length) sql(`DELETE FROM glpi_plugin_halosis_candidates WHERE id IN (${candidates.join(',')});`);
  if (started) sql(`DELETE FROM glpi_plugin_halosis_chats WHERE users_id = ${a.users.budi} AND date_creation >= '${started}';`);
  if (created.length === 0) return;
  const ids = created.join(',');
  await a.call('DELETE', 'Ticket', { input: created.map(id => ({ id })), force_purge: true });
  sql(`DELETE FROM glpi_plugin_halosis_decisions WHERE tickets_id IN (${ids});
       DELETE FROM glpi_plugin_halosis_triage_retries WHERE tickets_id IN (${ids});
       DELETE FROM glpi_plugin_halosis_suggestions WHERE tickets_id IN (${ids});
       DELETE FROM glpi_plugin_halosis_candidates WHERE source = 'ticket' AND tickets_id IN (${ids});
       DELETE FROM glpi_queuednotifications WHERE itemtype='Ticket' AND items_id IN (${ids});`);
}

(async () => {
  const cache = path.join(os.homedir(), 'Library/Caches/ms-playwright');
  const shell = fs.existsSync(cache) ? fs.readdirSync(cache).find(d => d.startsWith('chromium_headless_shell')) : null;
  const sub = shell && fs.readdirSync(path.join(cache, shell)).find(d => d.startsWith('chrome-headless-shell'));
  const browser = await chromium.launch(process.env.CH ? { channel: process.env.CH }
    : (sub ? { executablePath: path.join(cache, shell, sub, 'chrome-headless-shell') } : {}));
  const a = await api();
  started = sql('SELECT NOW();');
  const results = {};
  const run = async (name, fn) => {
    try { results[name] = (await fn()) ? 'LULUS' : 'GAGAL'; } catch (e) { results[name] = 'GAGAL (' + e.message.split('\n')[0].slice(0, 120) + ')'; }
  };

  try {
    await run('K-05 form katalog berbahasa Indonesia, Judul wajib, tiket terbuat', async () => {
      const p = await login(browser, 'budi');
      await p.goto(`${BASE}/ServiceCatalog`); await p.waitForLoadState('networkidle');
      const catalog = await body(p);
      if (!/Laporkan Masalah/.test(catalog) || !/Ajukan Permintaan/.test(catalog) || /Report an issue|Request a service/.test(catalog)) return false;
      await p.goto(`${BASE}/Form/Render/1`); await p.waitForLoadState('networkidle');
      const form = await body(p);
      if (!['Urgensi', 'Kategori', 'Judul', 'Deskripsi', 'Lampiran', 'Kirim'].every(l => form.includes(l))) return false;
      if (/\b(Title|Attachments|Submit|Urgency)\b/.test(form)) return false;
      const before = sql('SELECT COUNT(*) FROM glpi_tickets;');
      const description = p.locator('[contenteditable=true], .tox-edit-area iframe').first();
      const frame = p.frameLocator('.tox-edit-area iframe').first();
      await frame.locator('body').click().catch(() => description.click());
      await p.keyboard.type('Uji K-05: deskripsi kendala');
      await p.getByRole('button', { name: 'Kirim' }).click(); await p.waitForTimeout(2500);
      const blocked = sql('SELECT COUNT(*) FROM glpi_tickets;') === before;
      await p.locator('input[name=answers_6]').fill('Uji K-05 judul laporan');
      await p.getByRole('button', { name: 'Kirim' }).click(); await p.waitForTimeout(5000);
      const id = sql(`SELECT id FROM glpi_tickets WHERE name = 'Uji K-05 judul laporan' ORDER BY id DESC LIMIT 1;`);
      if (id) created.push(Number(id));
      // Sesudah Kirim, GLPI langsung membuka tiket yang baru dibuat
      const done = /Uji K-05 judul laporan/.test(await body(p)) && /\bBaru\b/.test(await body(p));
      await p.context().close();
      return blocked && Boolean(id) && done;
    });

    await run('K-24 label artikel diterjemahkan', async () => {
      const p = await login(browser, 'lina');
      await p.goto(`${BASE}/front/knowbaseitem.form.php`); await p.waitForLoadState('networkidle');
      const placeholder = await p.locator('[data-placeholder]').first().getAttribute('data-placeholder');
      const article = sql(`SELECT id FROM glpi_knowbaseitems WHERE is_faq = 1 ORDER BY id LIMIT 1;`);
      await p.goto(`${BASE}/front/knowbaseitem.form.php?id=${article}`); await p.waitForLoadState('networkidle');
      const share = await p.getByText('Bagikan', { exact: true }).count();
      await p.locator('button[title="Tindakan lain"]').last().click(); await p.waitForTimeout(800);
      const page = await p.content();
      await p.context().close();
      return placeholder === 'Artikel tanpa judul' && share > 0 && page.includes('Tambahkan ke Tanya Jawab (FAQ)')
        && !page.includes('Add to FAQ');
    });

    const helped = async () => {
      const p = await login(browser, 'sri');
      await p.goto(`${BASE}/plugins/halosis/Dashboard`); await p.waitForLoadState('networkidle');
      const n = (await body(p)).match(/Terbantu tanpa tiket\s+(\d+)/)?.[1];
      await p.context().close();
      return n;
    };
    const helpedBefore = await helped();

    await run('K-02 "Tidak, terima kasih": solusi tidak ditemukan → tetap terbuka; belum terselesaikan → berakhir', async () => {
      const p = await login(browser, 'budi');
      await p.goto(`${BASE}/plugins/halosis/Chat`); await p.waitForLoadState('networkidle');
      const fresh = p.getByRole('button', { name: /Percakapan baru/ }).first();
      if (await fresh.isVisible().catch(() => false)) { await fresh.click(); await p.waitForTimeout(1500); }
      const input = p.locator('[data-chat-form] textarea, [data-chat-form] input[type=text]').first();
      const lastChat = () => sql(`SELECT status, IFNULL(rating, 'null') FROM glpi_plugin_halosis_chats
                                   WHERE users_id = ${a.users.budi} AND date_creation >= '${started}' ORDER BY id DESC LIMIT 1;`).split('\t');
      const no = p.getByRole('button', { name: /Tidak, terima kasih/ });

      // Solusi tidak ditemukan: kartu tertutup, percakapan tetap terbuka
      await p.getByText('Laporkan masalah').first().click(); await p.waitForTimeout(500);
      await input.fill('Kursi kantor saya patah'); await input.press('Enter');
      await no.first().waitFor(); await no.first().click(); await p.waitForTimeout(1000);
      const stillOpen = lastChat()[0] === 'open' && await input.isEnabled() && await no.count() === 0
        && !/Percakapan diakhiri/.test(await body(p));

      // Pertanyaan berikutnya di percakapan yang sama: solusi ada tetapi gagal
      await input.fill('Bagaimana mengatasi FASIH gagal sinkronisasi?'); await input.press('Enter');
      await p.getByRole('button', { name: 'Belum terselesaikan' }).last().click();
      await no.first().click(); await p.waitForTimeout(1500);
      const ended = /Percakapan diakhiri/.test(await body(p)) && await input.isDisabled();
      const [status, rating] = lastChat();
      await p.goto(`${BASE}/plugins/halosis/ChatHistory`); await p.waitForLoadState('networkidle');
      const badge = /Berakhir tanpa laporan/.test(await body(p));
      await p.context().close();
      return stillOpen && ended && status === 'resolved' && rating === 'null' && badge;
    });

    await run('K-02 percakapan yang ditolak tidak dihitung "Terbantu tanpa tiket"', async () => {
      const after = await helped();
      return helpedBefore !== undefined && after === helpedBefore;
    });

    await run('K-13 tugas terjadwal membuat kandidat tanpa membuka halaman', async () => {
      const ticket = await a.call('POST', 'Ticket', { input: { name: 'Uji K-13 sinkron kandidat', content: 'Uji K-13 masalah rekaan untuk kandidat', type: 1 } });
      created.push(ticket.id);
      await a.call('POST', 'ITILSolution', { input: { itemtype: 'Ticket', items_id: ticket.id, content: 'Solusi rekaan yang cukup panjang untuk kandidat pengetahuan.' } });
      sql(`UPDATE glpi_crontasks SET lastrun = NULL WHERE name = 'KnowledgeCandidates';`);
      execSync(`docker compose exec -T glpi php front/cron.php --force KnowledgeCandidates --allow-superuser`, { cwd: ROOT, stdio: 'ignore' });
      const id = sql(`SELECT id FROM glpi_plugin_halosis_candidates WHERE source = 'ticket' AND tickets_id = ${ticket.id};`);
      if (id) candidates.push(Number(id));
      const log = sql(`SELECT COUNT(*) FROM glpi_crontasklogs l JOIN glpi_crontasks c ON c.id = l.crontasks_id
                        WHERE c.name = 'KnowledgeCandidates' AND l.date >= '${started}';`);
      return Boolean(id) && Number(log) > 0;
    });
  } finally {
    await cleanup(a);
    await browser.close();
  }
  let failed = 0;
  for (const [name, result] of Object.entries(results)) { console.log(`${result.padEnd(6)} ${name}`); failed += result.startsWith('LULUS') ? 0 : 1; }
  console.log(`Data uji dihapus: ${created.length} tiket`);
  process.exit(failed ? 1 : 0);
})().catch(e => { console.error(e.message); process.exit(1); });
