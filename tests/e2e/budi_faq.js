// Sebagai pegawai (budi, UI): id artikel KB yang tampil di Tanya Jawab (FAQ) dan id yang bisa dibuka. Keluaran JSON, hanya id.
//   KB_IDS=1,2,3 node budi_faq.js [pengguna]   (bawaan budi; KB_IDS = id yang dicoba dibuka)
const { chromium } = require('playwright-core');
const fs = require('fs'), os = require('os'), path = require('path');
const BASE = process.env.HALOSIS_URL || 'http://localhost:8080';
const ID_LINK = 'a[href*="knowbaseitem.form.php?id="], a[href*="helpdesk.faq.php?id="]';

(async () => {
  const cache = path.join(os.homedir(), 'Library/Caches/ms-playwright');
  const shell = fs.existsSync(cache) ? fs.readdirSync(cache).find(d => d.startsWith('chromium_headless_shell')) : null;
  const sub = shell && fs.readdirSync(path.join(cache, shell)).find(d => d.startsWith('chrome-headless-shell'));
  const browser = await chromium.launch(sub ? { executablePath: path.join(cache, shell, sub, 'chrome-headless-shell') } : {});
  const page = await (await browser.newContext()).newPage();
  page.setDefaultTimeout(60000);
  await page.goto(BASE + '/');
  await page.fill('#login_name', process.argv[2] || 'budi'); await page.fill('#login_password', 'halosis');
  await Promise.all([page.waitForLoadState('networkidle'), page.click('button[name=submit]')]);
  const ids = new Set();
  const collect = async (p) => { for (const h of await p.$$eval(ID_LINK, as => as.map(a => a.getAttribute('href')))) ids.add(Number(h.match(/id=(\d+)/)[1])); };
  await page.goto(BASE + '/front/helpdesk.faq.php'); await page.waitForLoadState('networkidle');
  if (process.env.DEBUG_URL) console.error(page.url(), (await page.innerText('body')).slice(0, 800));
  await collect(page);
  // kategori di pohon: buka tiap tautan kategori satu kali
  const cats = await page.$$eval('a[href*="knowbaseitemcategories_id"]', as => [...new Set(as.map(a => a.getAttribute('href')))]);
  for (const href of cats) {
    const p2 = await page.context().newPage(); await p2.goto(new URL(href, BASE).href); await p2.waitForLoadState('networkidle');
    await collect(p2); await p2.close();
  }
  const open = [];
  for (const id of (process.env.KB_IDS || '').split(',').filter(Boolean).map(Number)) {
    await page.goto(`${BASE}/front/helpdesk.faq.php?id=${id}`); await page.waitForLoadState('networkidle');
    const body = await page.innerText('body');
    if (!/tidak\s+memiliki|not\s+have\s+the\s+right|akses\s+ditolak|Access\s+denied|Item\s+not\s+found|tidak\s+ditemukan/i.test(body) && /helpdesk.faq/.test(page.url())) open.push(id);
  }
  console.log(JSON.stringify({ faq: [...ids].sort((a, b) => a - b), buka: open }));
  await browser.close();
})();
