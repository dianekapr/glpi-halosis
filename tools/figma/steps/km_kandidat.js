// Section 04 (akun lina). ids: 0 = tab Dijadikan artikel (?status=article), 1 = tab Diabaikan (?status=ignored),
// 2 = editor draf artikel setelah «Jadikan artikel» (pesan asli terlihat). Langkah 2 MENGUBAH data: kandidat pending pertama →
// article + 1 artikel KB draf; pulihkan dengan logs/f2_km_pulih.sh (id artikel dicetak 'KBID=').
module.exports = async ({ page, cap, BASE }) => {
  for (const [i, st] of [[0, 'article'], [1, 'ignored']]) {
    await page.goto(`${BASE}/plugins/halosis/Kandidat?status=${st}`); await page.waitForLoadState('networkidle'); await page.waitForTimeout(600); await cap(i);
  }
  await page.goto(`${BASE}/plugins/halosis/Kandidat`); await page.waitForLoadState('networkidle');
  await Promise.all([page.waitForURL(/knowbaseitem\.form\.php\?id=\d+/, { timeout: 90000 }), page.getByRole('button', { name: 'Jadikan artikel' }).first().click()]);
  await page.waitForLoadState('networkidle');
  console.log('KBID=' + new URL(page.url()).searchParams.get('id'));
  await page.getByText('Draf artikel dibuat').first().waitFor();
  await page.waitForTimeout(400);
  await cap(2);
};
