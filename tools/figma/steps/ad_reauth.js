// Section 06 (akun dimas), read-only (pratinjau tidak menyimpan). ids: 0 = verifikasi ulang /ReAuth/Prompt (sebelum Pengaturan AI),
// 1 = hasil «Pratinjau dampak SLA» di halaman Pengaturan HaloSIS.
module.exports = async ({ page, cap, BASE }) => {
  await page.goto(`${BASE}/plugins/halosis/front/config.form.php`); await page.waitForLoadState('networkidle');
  // route.fetch() di capture.js mengikuti redirect, jadi URL tetap config.form.php: cek isi halaman, bukan URL
  if (await page.locator('form[action*="ReAuth"]').count() === 0) throw new Error('bukan halaman ReAuth: ' + page.url());
  await page.waitForTimeout(500); await cap(0);
  if (await page.locator('input[type=password]').count() > 0) await page.locator('input[type=password]').first().fill('halosis');
  await Promise.all([page.waitForLoadState('networkidle'), page.locator('form[action*="ReAuth"] button[type=submit]').click()]);
  await page.goto(`${BASE}/plugins/halosis/front/config.form.php`); await page.waitForLoadState('networkidle');
  const sel = page.locator('#halosis_sla_target');
  const val = await sel.locator('option:not([value=""])').first().getAttribute('value');
  await sel.selectOption(val);
  await page.fill('#halosis_sla_number', '8');
  await Promise.all([page.waitForLoadState('networkidle'), page.locator('button[name=preview_sla]').click()]);
  await page.waitForTimeout(800); await cap(1);
};
