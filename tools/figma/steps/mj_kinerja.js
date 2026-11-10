// Section 05 (akun sri), read-only. ids: 0 = Kinerja AI ?weeks=4, 1 = ?weeks=12, 2 = «Tampilkan sebagai tabel» terbuka (?weeks=12).
module.exports = async ({ page, cap, BASE }) => {
  for (const [i, w] of [[0, 4], [1, 12]]) { await page.goto(`${BASE}/plugins/halosis/Dashboard?weeks=${w}&group=0&category=0`); await page.waitForLoadState('networkidle'); await page.waitForTimeout(1200); await cap(i); }
  await page.getByText('Tampilkan sebagai tabel').first().click(); await page.waitForTimeout(600); await cap(2);
};
