// Beranda (/front/central.php) tiap peran, read-only. env TAB = dasbor yang dipilih di <select class=dashboard_select> (mis. Central, Assistance); VIEW = tab «Tampilan Pribadi» dst. yang diklik.
module.exports = async ({ page, cap, BASE }) => {
  await page.goto(`${BASE}/front/central.php`); await page.waitForLoadState('networkidle'); await page.waitForTimeout(1500);
  if (process.env.TAB) { await page.locator('select.dashboard_select').first().selectOption({ label: process.env.TAB }); await page.waitForLoadState('networkidle'); await page.waitForTimeout(2500); }
  if (process.env.VIEW) { await page.getByText(process.env.VIEW, { exact: true }).first().click(); await page.waitForLoadState('networkidle'); await page.waitForTimeout(2500); console.log('Rencana Anda:', await page.getByText('Rencana Anda').count(), '| Pengingat:', await page.getByText(/Pengingat/).count()); }
  await cap(0);
};
