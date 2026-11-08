// OP-R4 (form Ubah terbuka) lalu OP-R5 (hasil Terapkan perubahan). Env: TICKET=<id>. Akun rina. ids: id OP-R4, id OP-R5.
module.exports = async ({ page, cap, BASE }) => {
  await page.goto(`${BASE}/front/ticket.form.php?id=${process.env.TICKET}`); await page.waitForLoadState('networkidle');
  await page.waitForSelector('[data-action=show-modify]');
  await page.click('[data-action=show-modify]');
  const sel = page.locator('#halosis-urgency'), cur = await sel.inputValue();
  const other = (await sel.locator('option').evaluateAll(os => os.map(o => o.value))).find(v => v && v !== cur);
  await sel.selectOption(other);
  await page.fill('#halosis-modify-reason', 'Urgensi dikoreksi sesuai dampak layanan');
  await page.waitForTimeout(300);
  await cap(0);
  await Promise.all([page.waitForLoadState('networkidle'), page.click('[data-action=modify]')]);
  await page.waitForTimeout(2500);
  await cap(1);
};
