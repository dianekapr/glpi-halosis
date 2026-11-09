// Tanya (env Q), tunggu jawaban + sumber, tangkap. Membuat 1 chat uji (hapus: logs/f3_chat_pulih.sh).
module.exports = async ({ page, cap }) => {
  const fresh = page.getByRole('button', { name: /Percakapan baru/ }).first();
  if (await fresh.isVisible().catch(() => false)) { await fresh.click(); await page.waitForTimeout(1500); }
  const input = page.locator('[data-chat-form] textarea, [data-chat-form] input[type=text]').first();
  await input.fill(process.env.Q); await input.press('Enter');
  await page.locator('.hc-source').first().waitFor({ timeout: 60000 }).catch(() => {});
  await page.getByText(/Apakah jawaban ini membantu/).first().waitFor({ timeout: 60000 }).catch(() => {});
  await page.waitForTimeout(1500);
  console.log('sumber:', JSON.stringify(await page.$$eval('.hc-source', a => a.map(x => [x.textContent.trim(), x.getAttribute('href')]))));
  await cap(0);
};
