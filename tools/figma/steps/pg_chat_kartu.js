// PG-00: klik kartu «Laporkan masalah» → tangkap (kotak fokus + pesan asisten). id 0. Membuat 0 chat baru bila tak ada kiriman.
module.exports = async ({ page, cap }) => {
  const fresh = page.getByRole('button', { name: /Percakapan baru/ }).first();
  if (await fresh.isVisible().catch(() => false)) { await fresh.click(); await page.waitForTimeout(1500); }
  await page.locator('[data-chat-focus]').first().click();
  await page.waitForSelector('[data-chat-report-prompt]'); await page.waitForTimeout(400);
  await cap(0);
};
