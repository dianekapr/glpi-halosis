// place = swap_nav + rewire (langkah 2) + link. Tempel ke use_figma (isi CFG dulu). Mengambil frame hasil tangkapan (CFG.captured),
//  - target ADA : kosongkan frame lama (ID/nama/posisi tetap), pindahkan isi tangkapan, pasang ulang reaction dari CFG.snapshot.keluar
//                 dengan mencocokkan teks elemen (yang tak cocok dilaporkan di `tidakCocok`)
//  - target null: frame tangkapan jadi frame baru bernama CFG.name di CFG.section pada (x,y)
// swap_nav: buang "Sidebar - Bilah samping" hasil tangkapan → instance komponen peran (varian = garis aktif). nav.type 'sidebar'.
// link: [{teks, ke, dalam?}] → elemen ber-teks itu (tombol/tautan terdekat) diberi ON_CLICK → frame `ke`.
const CFG = {
  pageId: '49:2', captured: '', target: null, name: '', section: '49:6', x: 0, y: 0,
  nav: { type: 'sidebar', component: 'Sidebar · Operator', variant: 'Aktif=Semua tiket' },
  snapshot: null, links: [],
};
const pg = await figma.getNodeByIdAsync(CFG.pageId); await figma.setCurrentPageAsync(pg);
const cap = await figma.getNodeByIdAsync(CFG.captured);
const log = { dipindah: [], tidakCocok: [], link: [], tidakDitemukanLink: [] };
let frame;
if (CFG.target) {
  frame = await figma.getNodeByIdAsync(CFG.target);
  for (const c of [...frame.children]) c.remove();
  for (const c of [...cap.children]) { if (/^Sidebar/.test(c.name)) { c.remove(); continue; } frame.appendChild(c); log.dipindah.push(c.name); }
  frame.resize(cap.width, cap.height); frame.fills = cap.fills; cap.remove();
} else {
  frame = cap; const sec = await figma.getNodeByIdAsync(CFG.section);
  sec.appendChild(frame); frame.x = CFG.x; frame.y = CFG.y; frame.name = CFG.name;
  for (const c of [...frame.children]) if (/^Sidebar/.test(c.name)) c.remove();
}
frame.clipsContent = true;
// swap_nav
if (CFG.nav && CFG.nav.type === 'sidebar') {
  const comps = pg.findAll(n => (n.type === 'COMPONENT_SET' || n.type === 'COMPONENT') && (n.name === CFG.nav.component || (n.parent && n.parent.name === CFG.nav.component)));
  const comp = comps.find(n => n.type === 'COMPONENT' && (n.name === CFG.nav.variant || n.name === CFG.nav.component)) || comps.find(n => n.type === 'COMPONENT');
  const inst = comp.createInstance(); frame.appendChild(inst); inst.name = CFG.nav.component; if ('layoutMode' in frame && frame.layoutMode !== 'NONE') inst.layoutPositioning = 'ABSOLUTE'; inst.x = 0; inst.y = 0; inst.resize(240, frame.height);
  log.nav = comp.name;
}
// pencocokan teks → elemen yang bisa diklik
const clickable = (tn, root) => { let c = tn; while (c.parent && c.parent.id !== root.id) { if (/^(Button|Link|Tab|Nav)/.test(c.parent.name) || c.parent.type === 'INSTANCE') return c.parent; if (c.parent.children && c.parent.children.length > 4) break; c = c.parent; } return tn.parent; };
const find = (root, teks) => { const first = teks.split(' | ')[0]; const tn = root.findAll(n => n.type === 'TEXT' && n.characters.trim() === first)[0]; return tn ? clickable(tn, root) : null; };
if (CFG.snapshot) for (const k of CFG.snapshot.keluar) {
  const el = k.teks ? find(frame, k.teks) : (k.id === CFG.target ? frame : frame.findAll(n => n.name === k.nama && n.name !== 'Button')[0] || null); // tanpa teks (tombol ikon): cocokkan per nama bila unik-bernama
  if (!el) { log.tidakCocok.push(k.teks || k.nama); continue; }
  await el.setReactionsAsync([...(el.reactions || []), ...k.reactions]); log.link.push(`${k.teks.slice(0, 24)} → ${k.reactions.map(r => r.actions.map(a => a.destinationId)).join(',')}`);
}
for (const l of CFG.links) {
  const root = l.dalam ? await figma.getNodeByIdAsync(l.dalam) : frame;
  const el = find(root, l.teks);
  if (!el) { log.tidakDitemukanLink.push(l.teks); continue; }
  const rx = { trigger: { type: 'ON_CLICK' }, actions: [{ type: 'NODE', destinationId: l.ke, navigation: 'NAVIGATE', transition: null, preserveScrollPosition: false }] };
  await el.setReactionsAsync([...(el.reactions || []).filter(r => !(r.actions || []).some(a => a.destinationId === l.ke)), rx]); log.link.push(`${l.teks} → ${l.ke}`);
}
return { frame: frame.id, nama: frame.name, w: frame.width, h: frame.height, ...log };
