// rewire (langkah 1) — read-only. Catat SEMUA reaction keluar (dari dalam frame, kecuali instance navigasi) & masuk (dari luar frame
// menuju frame/turunannya). Simpan hasilnya ke logs/<nama>_rewire.json SEBELUM mengganti frame; hasilnya jadi CFG.snapshot di figma_place.js.
const CFG = { target: '46:289', pageId: '49:2' };
const pg = await figma.getNodeByIdAsync(CFG.pageId); await figma.setCurrentPageAsync(pg);
const t = await figma.getNodeByIdAsync(CFG.target);
const txt = (n) => ('findAll' in n ? n.findAll(x => x.type === 'TEXT').map(x => x.characters.trim()).filter(Boolean).join(' | ') : (n.characters || '')).slice(0, 80);
const inNav = (n) => { let c = n; while (c && c.id !== t.id) { if (c.type === 'INSTANCE' && /^(Sidebar|Navbar)/.test(c.mainComponent ? c.mainComponent.name : c.name)) return true; c = c.parent; } return false; };
const rxs = (n) => (n.reactions || []).map(r => ({ trigger: r.trigger, actions: r.actions || (r.action ? [r.action] : []) }));
const keluar = [];
for (const n of [t, ...t.findAll(x => x.reactions && x.reactions.length)]) {
  if (!n.reactions || !n.reactions.length || (n !== t && inNav(n))) continue;
  keluar.push({ id: n.id, nama: n.name, teks: txt(n), reactions: rxs(n) });
}
const masuk = []; const ids = new Set([t.id, ...t.findAll(() => true).map(x => x.id)]);
for (const n of pg.findAll(x => x.reactions && x.reactions.length)) {
  let top = n; while (top.parent && top.parent.type !== 'SECTION' && top.parent.type !== 'PAGE') top = top.parent;
  if (top.id === t.id) continue;
  for (const r of rxs(n)) for (const a of r.actions) if (a.destinationId && ids.has(a.destinationId)) masuk.push({ dari: n.id, nama: n.name, frame: top.name, ke: a.destinationId, keFrame: a.destinationId === t.id });
}
return { frame: t.name, w: t.width, h: t.height, keluar, masuk };
