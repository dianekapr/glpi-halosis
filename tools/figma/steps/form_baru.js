// PG-04 (FORM=1) / PG-R04 (FORM=2): form kosong, read-only.
module.exports = async ({ page, cap, BASE }) => {
  await page.goto(`${BASE}/Form/Render/${process.env.FORM}`); await page.waitForLoadState('networkidle'); await page.waitForTimeout(1500);
  console.log('judul:', (await page.locator('h1, h2').first().innerText()).trim(), '| perangkat:', await page.getByText('Perangkat pengguna').count());
  await cap(0);
};
