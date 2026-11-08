// PG-S21/S22: env Q = pertanyaan ('komputer lambat' → tidak ditemukan; 'kata sandi' → pilihan artikel). Klik "Tidak, terima kasih", tangkap chat (kartu tutup, percakapan terbuka). Membuat 1 chat uji (dihapus lewat logs/figma_chat_cleanup.sh).
module.exports = async ({ page, cap }) => {
  const fresh = page.getByRole('button', { name: /Percakapan baru/ }).first();
  if (await fresh.isVisible().catch(() => false)) { await fresh.click(); await page.waitForTimeout(1500); }
  const input = page.locator('[data-chat-form] textarea, [data-chat-form] input[type=text]').first();
  await input.fill(process.env.Q); await input.press('Enter');
  const no = page.getByRole('button', { name: /Tidak, terima kasih/ }); await no.first().waitFor(); await page.waitForTimeout(1500);
  await no.first().click(); await page.waitForTimeout(1500);
  await cap(0);
};
