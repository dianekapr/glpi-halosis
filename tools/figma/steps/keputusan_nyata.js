// Hasil keputusan SUNGGUHAN (menulis DB: gunakan tiket uji dari testdata.js, lalu `testdata.js cleanup`). env TICKET, ACTION=accept|reject|modify. Akun rina.
// Setelah reload, pesan flash GLPI «Keputusan disimpan… Buka tiket» asli dipertahankan tampil lalu ditangkap.
module.exports = async ({ page, cap, BASE }) => {
  const T = process.env.TICKET, A = process.env.ACTION;
  await page.goto(`${BASE}/front/ticket.form.php?id=${T}`); await page.waitForLoadState('networkidle'); await page.waitForTimeout(800);
  const panel = page.locator('[data-halosis-triase]').first();
  if (A === 'accept') await panel.locator('button[data-action=accept]').click();
  else {
    await panel.locator(`button[data-action=show-${A}]`).click();
    if (A === 'modify') { const sel = page.locator('#halosis-urgency'), cur = await sel.inputValue(); const o = (await sel.locator('option').evaluateAll(os => os.map(x => x.value))).find(v => v && v !== cur); await sel.selectOption(o); }
    await panel.locator('textarea[data-reason]:visible').first().fill('Alasan keputusan petugas sesuai kondisi tiket'); await page.waitForTimeout(300);
    await panel.locator(`button[data-action=${A}]`).click();
  }
  await page.waitForNavigation({ waitUntil: 'load' }).catch(() => {}); await page.waitForLoadState('networkidle'); await page.waitForTimeout(1200);
  const msg = await page.getByText(/Keputusan disimpan/).count(); console.log('flash «Keputusan disimpan» terlihat:', msg);
  await cap(0);
};
