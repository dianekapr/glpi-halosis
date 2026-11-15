// PG-S21/S22 tanpa menulis DB: POST ajax/chat.php?action=message dipalsukan di browser. env AFTER = 'belum' (mode pilihan): klik «Belum terselesaikan» → kartu tawaran laporan 7a. env MODE = 'tidak' (Chatbot::notFound) | 'pilihan' (Chatbot::choices).
// Bentuk respons = Chatbot::ask() (plugins/halosis/src/Chatbot.php ~l.207-216): {ok, chat_id, answer, found, ai, out_of_scope, sources:[{id,name,url}], masked}.
// Teks 'answer' = msgstr id_ID.po dari msgid di Chatbot::notFound()/choices() (dibaca dari berkas .po, bukan diketik ulang). Id/judul artikel = KB asli (glpi_knowbaseitems 15, 3, 2).
const fs = require('fs'), path = require('path');
const po = (msgid) => { const t = fs.readFileSync(path.resolve(__dirname, '../../../plugins/halosis/locales/id_ID.po'), 'utf8'); const i = t.indexOf(`msgid "${msgid}"`); if (i < 0) throw new Error('msgid tak ada: ' + msgid); return t.slice(i).split('\n')[1].replace(/^msgstr "/, '').replace(/"$/, ''); };
module.exports = async ({ page, cap }) => {
  const tidak = process.env.MODE !== 'pilihan';
  const answer = tidak
    ? po('Sorry, I have not found an answer in the Help Center yet. Try other words, or click “Create report” so an officer can help you.')
    : po('Did you mean one of these articles? Open the one that matches, then tell me whether it solves your problem.');
  const sources = tidak ? [] : [[15, 'Akun SSO terkunci setelah salah kata sandi'], [3, 'FASIH: sinkronisasi gagal'], [2, 'Mengatur ulang kata sandi SSO BPS']].map(([id, name]) => ({ id, name, url: `/front/knowbaseitem.form.php?id=${id}` }));
  await page.route('**/ajax/chat.php*', async (route) => {
    if (route.request().method() !== 'POST') return route.continue();
    await route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({ ok: true, chat_id: 999999, answer, found: false, ai: false, out_of_scope: false, sources, masked: false }) });
  });
  const fresh = page.getByRole('button', { name: /Percakapan baru/ }).first();
  if (await fresh.isVisible().catch(() => false)) { await fresh.click(); await page.waitForTimeout(1500); }
  const input = page.locator('[data-chat-form] textarea, [data-chat-form] input[type=text]').first();
  await input.fill(tidak ? 'komputer lambat' : 'kata sandi'); await input.press('Enter');
  await page.getByRole('button', { name: tidak ? /Ya, buat laporan/ : /Masalah terselesaikan/ }).first().waitFor(); await page.waitForTimeout(1500);
  if (!tidak && process.env.AFTER === 'belum') { await page.getByRole('button', { name: /Belum terselesaikan/ }).first().click(); await page.locator('.hc-offer').first().waitFor(); await page.waitForTimeout(800); }
  await cap(0);
};
