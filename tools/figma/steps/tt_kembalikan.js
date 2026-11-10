// Section 03 (akun andi). Env TICKET=<id tiket uji yang ditugaskan ke andi>.
// ids: 0 = detail tiket dengan tombol «Kembalikan ke Operator» (TT-01), 1 = form alasan terbuka (TT-02), 2 = hasil kirim (TT-R1; tunggu pesan terlihat), 3 = salinan untuk Alur Demo 10-R2.
module.exports = async ({ page, cap, BASE }) => {
  await page.goto(`${BASE}/front/ticket.form.php?id=${process.env.TICKET}`); await page.waitForLoadState('networkidle');
  await page.waitForSelector('[data-action=show-return]');
  await page.waitForTimeout(800);
  await cap(0);
  await page.click('[data-action=show-return]');
  await page.fill('[data-halosis-section=return] [data-reason]', 'Kendala bandwidth jaringan, bukan perangkat tim ini');
  await page.waitForTimeout(300);
  await cap(1);
  await Promise.all([page.waitForLoadState('networkidle'), page.click('button[data-action=return]')]);
  await page.getByText('Tiket dikembalikan ke antrean validasi Operator.').first().waitFor();
  await page.waitForTimeout(300);
  await cap(2);
  await cap(3); // salinan kedua untuk Alur Demo 10-R2
};
