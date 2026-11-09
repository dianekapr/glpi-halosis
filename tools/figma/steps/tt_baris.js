// Section 03 (akun andi), hanya-baca. ids: 0 = detail tiket (TT-R2), 1 = detail Masalah (TT-R3),
// 2 = hasil Cari daftar Masalah (TT-R4), 3 = hasil Cari pengetahuan (TT-R5). Env: TICKET, PROBLEM, Q.
module.exports = async ({ page, cap, BASE }) => {
  const go = async (u) => { await page.goto(BASE + u); await page.waitForLoadState('networkidle'); await page.waitForTimeout(1200); };
  await go(`/front/ticket.form.php?id=${process.env.TICKET}`); await cap(0);
  await go(`/front/problem.form.php?id=${process.env.PROBLEM}`); await cap(1);
  await go(`/front/problem.php?criteria%5B0%5D%5Bfield%5D=1&criteria%5B0%5D%5Bsearchtype%5D=contains&criteria%5B0%5D%5Bvalue%5D=${encodeURIComponent(process.env.PQ || 'SSO')}&search=Cari`); await cap(2);
  await go('/plugins/halosis/CariKnowledge');
  await page.fill('#halosis-cari-q', process.env.Q || 'FASIH tidak dapat sinkronisasi');
  await Promise.all([page.waitForLoadState('networkidle'), page.click('button[type=submit].btn-primary')]);
  await page.waitForTimeout(3500); await cap(3);
};
