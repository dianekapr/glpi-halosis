// PG-04: ids = [galat wajib isi, hasil Kirim]. Membuat 1 tiket uji (judul "Uji alat Figma (hapus)") — hapus lewat cleanup (catat id di logs/figma_testdata.json).
const { execSync } = require('child_process'), fs = require('fs'), path = require('path');
module.exports = async ({ page, cap, BASE }) => {
  await page.goto(`${BASE}/Form/Render/1`); await page.waitForLoadState('networkidle');
  await page.frameLocator('.tox-edit-area iframe').first().locator('body').click(); await page.keyboard.type('Uji alat Figma: deskripsi kendala');
  await page.getByRole('button', { name: 'Kirim' }).click(); await page.waitForTimeout(2500);
  await cap(0);                                   // galat: Judul wajib diisi (teks GLPI apa adanya)
  await page.locator('input[name=answers_6]').fill('Uji alat Figma (hapus)');
  await page.getByRole('button', { name: 'Kirim' }).click(); await page.waitForTimeout(5000);
  await cap(1);                                   // halaman tiket hasil Kirim
  const ROOT = path.resolve(__dirname, '../../..'), LOG = path.join(ROOT, 'logs/figma_testdata.json');
  const id = execSync(`docker compose exec -T db sh -c 'mysql -N -u"$MYSQL_USER" -p"$MYSQL_PASSWORD" "$MYSQL_DATABASE" 2>/dev/null'`, { cwd: ROOT, input: "SELECT id FROM glpi_tickets WHERE name='Uji alat Figma (hapus)' ORDER BY id DESC LIMIT 1;" }).toString().trim();
  const st = fs.existsSync(LOG) ? JSON.parse(fs.readFileSync(LOG)) : { tickets: [], before: null };
  if (id) { st.tickets.push(+id); fs.writeFileSync(LOG, JSON.stringify(st)); } console.log('tiket uji', id);
};
