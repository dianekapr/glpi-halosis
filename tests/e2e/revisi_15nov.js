// Uji revisi 15 Nov: E4 masking langsung (gelembung pesan diganti teks tersamar dari server, tanpa refresh) dan
// E2 penanda umpan balik "Ditandai tidak membantu" (satu klik, tidak bisa diklik lagi). Baris uji di tabel chats,
// article_uses, dan feedback (id > batas sebelum tes) dihapus kembali; [DEMO] tidak disentuh.
//   node revisi_15nov.js        # butuh docker compose hidup & browser Playwright
const { chromium } = require('playwright-core');
const { execSync } = require('child_process');
const fs = require('fs'), os = require('os'), path = require('path');
const BASE = process.env.HALOSIS_URL || 'http://localhost:8080';
const ROOT = path.resolve(__dirname, '../..');
const sql = (q) => execSync(`docker compose exec -T db sh -c 'mysql -N -u"$MYSQL_USER" -p"$MYSQL_PASSWORD" "$MYSQL_DATABASE" 2>/dev/null'`, { cwd: ROOT, input: q }).toString().trim();
const TABLES = ['chats', 'article_uses', 'feedback'].map(t => `glpi_plugin_halosis_${t}`);
let fail = 0;
const ok = (c, m) => { console.log((c ? 'LULUS ' : 'GAGAL ') + m); if (!c) fail++; };

async function login(browser, user) {
  const page = await (await browser.newContext({ viewport: { width: 1300, height: 900 } })).newPage();
  page.setDefaultTimeout(60000);
  await page.goto(BASE + '/');
  await page.fill('#login_name', user); await page.fill('#login_password', 'halosis');
  await Promise.all([page.waitForLoadState('networkidle'), page.click('button[name=submit]')]);
  return page;
}

(async () => {
  const cache = path.join(os.homedir(), 'Library/Caches/ms-playwright');
  const shell = fs.existsSync(cache) ? fs.readdirSync(cache).find(d => d.startsWith('chromium_headless_shell')) : null;
  const sub = shell && fs.readdirSync(path.join(cache, shell)).find(d => d.startsWith('chrome-headless-shell'));
  const browser = await chromium.launch(sub ? { executablePath: path.join(cache, shell, sub, 'chrome-headless-shell') } : {});
  const before = Object.fromEntries(TABLES.map(t => [t, Number(sql(`select coalesce(max(id),0) from ${t};`))]));
  try {
    // E4
    const budi = await login(browser, 'budi');
    await budi.goto(`${BASE}/plugins/halosis/Chat`); await budi.waitForLoadState('networkidle');
    const input = budi.locator('[data-chat-form] textarea, [data-chat-form] input[type=text]').first();
    // UC-01 3a: tombol Kirim nonaktif saat kosong/spasi, aktif saat ada teks
    const kirim = budi.locator('[data-chat-form] button').first();
    ok(await kirim.isDisabled(), 'UC-01 3a Kirim nonaktif saat kotak kosong');
    await input.fill('   ');
    ok(await kirim.isDisabled(), 'UC-01 3a Kirim nonaktif saat hanya spasi');
    await input.fill('a');
    ok(await kirim.isEnabled(), 'UC-01 3a Kirim aktif saat ada teks');
    await input.fill('');
    await input.fill('lupa sandi SSO, password: RahasiaBanget99 email budi@contoh.go.id');
    await input.press('Enter');
    await budi.waitForFunction(() => document.querySelectorAll('.hc-row-ai .hc-bubble-ai:not(.hc-typing)').length > 0 && !document.querySelector('.hc-typing'));
    const bubble = (await budi.locator('.hc-bubble-user').last().innerText());
    ok(!/RahasiaBanget99|budi@contoh\.go\.id/.test(bubble), `E4 gelembung langsung tersamar tanpa refresh: "${bubble.replace(/\s+/g, ' ').slice(0, 80)}"`);

    // E2
    const rina = await login(browser, 'rina');
    await rina.goto(`${BASE}/plugins/halosis/CariKnowledge?q=reset+password+SSO`); await rina.waitForLoadState('networkidle');
    const box = rina.locator('[data-hf]').first();
    await box.locator('[data-hf-helpful="0"]').click();
    await rina.waitForFunction(() => /Ditandai tidak membantu/.test(document.querySelector('[data-hf]').innerText));
    const txt = (await box.innerText()).replace(/\s+/g, ' ');
    ok(/Ditandai tidak membantu/.test(txt) && !/Ditandai membantu/.test(txt), `E2 penanda tampil: "${txt.slice(0, 120)}"`);
    ok(await box.locator('button:not([disabled])').count() === 0, 'E2 tidak ada tombol yang masih bisa diklik');
    const n = Number(sql(`select count(*) from glpi_plugin_halosis_feedback where id > ${before.glpi_plugin_halosis_feedback};`));
    ok(n === 1, `E2 satu umpan balik tersimpan (${n})`);
  } finally {
    for (const t of TABLES) sql(`delete from ${t} where id > ${before[t]};`);
    await browser.close();
  }
  console.log(fail ? `${fail} GAGAL` : 'SEMUA LULUS');
  process.exit(fail ? 1 : 0);
})();
