// ganti = snapshot (rewire 1) + place (swap_nav + rewire 2) dalam SATU panggilan use_figma, per pasangan [target, tangkapan].
// Sidebar baru = instance dari komponen peran yang SAMA dengan sidebar frame lama (varian aktif tetap). Reaction keluar dipasang ulang
// dengan mencocokkan teks (kemunculan ke-N ↔ simpul teks ke-N). Hasil ringkas: {terpasang, tidakCocok, masukKeDalam}.
const PAIRS = []; // [['128:2','333:6242'], ...]
const pg = await figma.getNodeByIdAsync('49:2'); await figma.setCurrentPageAsync(pg);
const txt = (n) => ('findAll' in n ? n.findAll(x => x.type === 'TEXT').map(x => x.characters.trim()).filter(Boolean).join(' | ') : (n.characters || '')).slice(0, 80);
const rxs = (n) => (n.reactions || []).map(r => ({ trigger: r.trigger, actions: r.actions || (r.action ? [r.action] : []) }));
const isNav = (x) => x.type === 'INSTANCE' && /^(Sidebar|Navbar)/.test(x.mainComponent ? x.mainComponent.name : x.name);
const clickable = (tn, root) => { let c = tn; while (c.parent && c.parent.id !== root.id) { if (/^(Button|Link|Tab|Nav)/.test(c.parent.name) || c.parent.type === 'INSTANCE') return c.parent; if (c.parent.children && c.parent.children.length > 4) break; c = c.parent; } return tn.parent; };
const allRx = pg.findAll(x => x.reactions && x.reactions.length);
const out = [];
for (const [tid, cid] of PAIRS) {
  const t = await figma.getNodeByIdAsync(tid), cap = await figma.getNodeByIdAsync(cid);
  const inNav = (n) => { let c = n; while (c && c.id !== t.id) { if (isNav(c)) return true; c = c.parent; } return false; };
  // rewire 1
  const keluar = [];
  for (const n of [t, ...t.findAll(x => x.reactions && x.reactions.length)]) { if (!n.reactions.length || (n !== t && inNav(n))) continue; keluar.push({ id: n.id, nama: n.name, teks: txt(n), reactions: rxs(n) }); }
  const inner = new Set(t.findAll(() => true).map(x => x.id));
  const masuk = []; for (const n of allRx) { let top = n; while (top.parent && top.parent.type !== 'SECTION' && top.parent.type !== 'PAGE') top = top.parent; if (top.id === t.id) continue;
    for (const r of rxs(n)) for (const a of r.actions) if (a.destinationId && (a.destinationId === t.id || inner.has(a.destinationId))) masuk.push({ dari: n.id, ke: a.destinationId }); }
  const sb = t.children.find(isNav); const mc = sb && sb.mainComponent; const sbw = sb ? sb.width : 240, sbn = sb ? sb.name : "";
  // ganti isi
  for (const c of [...t.children]) c.remove();
  for (const c of [...cap.children]) { if (/^Sidebar/.test(c.name)) { c.remove(); continue; } t.appendChild(c); }
  t.resize(cap.width, cap.height); t.fills = cap.fills; cap.remove(); t.clipsContent = true;
  // rewire 2 (sebelum sidebar dipasang agar teks sidebar tidak ikut cocok)
  const byText = new Map(); for (const x of t.findAll(n => n.type === 'TEXT')) { const k = x.characters.trim(); if (!byText.has(k)) byText.set(k, []); byText.get(k).push(x); }
  const used = new Map(); const tidakCocok = []; let terpasang = 0;
  for (const k of keluar) {
    let el = null;
    if (k.id === tid) el = t;
    else if (k.teks) { const first = k.teks.split(' | ')[0]; const list = byText.get(first) || []; const i = used.get(first) || 0; used.set(first, i + 1); const tn = list[i] || list[list.length - 1]; el = tn ? clickable(tn, t) : null; }
    else el = t.findAll(n => n.name === k.nama && n.name !== 'Button')[0] || null;
    if (!el) { tidakCocok.push(k.teks || k.nama); continue; }
    await el.setReactionsAsync([...(el.reactions || []), ...k.reactions]); terpasang++;
  }
  // swap_nav
  let navNama = null;
  if (mc) { const inst = mc.createInstance(); t.appendChild(inst); inst.name = sbn; if (t.layoutMode && t.layoutMode !== 'NONE') inst.layoutPositioning = 'ABSOLUTE'; inst.x = 0; inst.y = 0; inst.resize(sbw || 240, t.height); navNama = mc.name; }
  out.push({ id: tid, nama: t.name, w: Math.round(t.width), h: Math.round(t.height), keluar: keluar.length, terpasang, tidakCocok: tidakCocok.slice(0, 12), nTidakCocok: tidakCocok.length, masuk: masuk.length, masukKeDalam: masuk.filter(m => m.ke !== tid).length, nav: navNama });
}
return out;
