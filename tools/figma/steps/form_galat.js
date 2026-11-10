// PG-R02: kirim form Laporkan Masalah TANPA judul → galat "Judul wajib diisi". Tidak membuat tiket (read-only).
module.exports = async ({ page, cap, BASE }) => {
  await page.goto(`${BASE}/Form/Render/1`); await page.waitForLoadState('networkidle');
  await page.frameLocator('.tox-edit-area iframe').first().locator('body').click(); await page.keyboard.type('Uji alat Figma: deskripsi kendala');
  await page.getByRole('button', { name: 'Kirim' }).click(); await page.waitForTimeout(2500);
  console.log('galat:', await page.getByText(/wajib|required/i).count(), '| url:', page.url());
  await cap(0);
};
