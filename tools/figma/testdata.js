#!/usr/bin/env node
// testdata: buat/hapus tiket uji (data rekaan) agar state aplikasi bisa ditangkap, lalu DIKEMBALIKAN.
//   node tools/figma/testdata.js create <pemohon> "<judul>" [isi]   → mencetak id tiket (dicatat di logs/figma_testdata.json)
//   (env ASSIGN=<akun> → tiket langsung ditugaskan ke akun itu, mis. andi untuk Section 03)
//   node tools/figma/testdata.js cleanup                            → hapus semua tiket yang dicatat + saran/keputusan/antrean notifikasinya
const { execSync } = require('child_process');
const fs = require('fs'), path = require('path');
const BASE = process.env.HALOSIS_URL || 'http://localhost:8080', ROOT = path.resolve(__dirname, '../..');
const LOG = path.join(ROOT, 'logs/figma_testdata.json');
const sql = q => execSync(`docker compose exec -T db sh -c 'mysql -N -u"$MYSQL_USER" -p"$MYSQL_PASSWORD" "$MYSQL_DATABASE" 2>/dev/null'`, { cwd: ROOT, input: q }).toString().trim();
async function api() {
  const auth = 'Basic ' + Buffer.from('glpi:glpi').toString('base64');
  const token = (await (await fetch(`${BASE}/apirest.php/initSession`, { headers: { Authorization: auth } })).json()).session_token;
  const h = { 'Session-Token': token, 'Content-Type': 'application/json' };
  const call = async (m, p, body) => (await fetch(`${BASE}/apirest.php/${p}`, { method: m, headers: h, body: body && JSON.stringify(body) })).json();
  const profiles = await call('GET', 'Profile?range=0-100');
  await call('POST', 'changeActiveProfile', { profiles_id: profiles.find(p => p.name === 'Super-Admin').id });
  const users = Object.fromEntries((await call('GET', 'User?range=0-500')).map(u => [u.name, u.id]));
  return { call, users };
}
const read = () => fs.existsSync(LOG) ? JSON.parse(fs.readFileSync(LOG)) : { tickets: [], before: null };
(async () => {
  const [cmd, who, title, content] = process.argv.slice(2);
  const st = read(); const a = await api();
  if (cmd === 'create') {
    if (!st.before) st.before = { tickets: +sql('SELECT COUNT(*) FROM glpi_tickets;'), chats: +sql('SELECT COUNT(*) FROM glpi_plugin_halosis_chats;') };
    const r = await a.call('POST', 'Ticket', { input: { name: title, content: content || `${title}. Data uji otomatis.`, type: 1, _users_id_requester: a.users[who], ...(process.env.ASSIGN ? { _users_id_assign: a.users[process.env.ASSIGN] } : {}) } });
    st.tickets.push(r.id); fs.writeFileSync(LOG, JSON.stringify(st)); console.log(r.id);
  } else if (cmd === 'cleanup') {
    if (st.tickets.length) {
      const ids = st.tickets.join(',');
      await a.call('DELETE', 'Ticket', { input: st.tickets.map(id => ({ id })), force_purge: true });
      sql(`DELETE FROM glpi_plugin_halosis_decisions WHERE tickets_id IN (${ids});
           DELETE FROM glpi_plugin_halosis_reassignments WHERE tickets_id IN (${ids});
           DELETE FROM glpi_plugin_halosis_triage_retries WHERE tickets_id IN (${ids});
           DELETE FROM glpi_plugin_halosis_suggestions WHERE tickets_id IN (${ids});
           DELETE FROM glpi_plugin_halosis_candidates WHERE source = 'ticket' AND tickets_id IN (${ids});
           DELETE FROM glpi_queuednotifications WHERE itemtype='Ticket' AND items_id IN (${ids});`);
    }
    console.log('sesudah', { tickets: +sql('SELECT COUNT(*) FROM glpi_tickets;'), chats: +sql('SELECT COUNT(*) FROM glpi_plugin_halosis_chats;') }, 'sebelum', st.before);
    fs.writeFileSync(LOG, JSON.stringify({ tickets: [], before: null }));
  }
})().catch(e => { console.error('GAGAL:', e.message); process.exit(1); });
