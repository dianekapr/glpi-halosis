// swap_nav Pegawai — tempel ke use_figma (isi CFG dulu). Dipanggil SETELAH figma_place.js (atau pada frame yang sudah berisi tangkapan).
// 1. Buang header hasil tangkapan (CFG.buang = nama/regex anak-frame teratas yang tingginya ≤ 80 px di y≈0, mis. "Header"/"Navbar"/"Top"),
//    dan instance "Navbar · Pegawai" lama bila ada.
// 2. Pasang instance komponen 88:3 di (0,0), lebar 1440, ABSOLUTE bila frame auto-layout.
// 3. Garis aktif: Rectangle tiap menu diwarnai oranye (0.95,0.55,0.30) hanya untuk CFG.aktif; lainnya putih (1,1,1) = tak terlihat.
// 4. Reaction menu: tiap menu NAVIGATE ke frame Section 01 (CFG.tujuan); menu aktif tidak diberi reaction (self-link 0).
//    Chip/BPS/Avatar: reaction disalin dari instance acuan CFG.acuan (mis. PG-01 141:3179) bila ada, dicocokkan per nama.
// Menu: 'Tanya HaloSIS' | 'Buat laporan' | 'Laporan saya' | 'Tanya Jawab (FAQ)' | 'Riwayat percakapan'
const CFG = {
  pageId: '49:2', frame: '', aktif: 'Laporan saya', buang: /^(Header|Navbar|Top|Banner)/i, acuan: '141:3179',
  tujuan: { 'Tanya HaloSIS': '153:3533', 'Buat laporan': '133:2', 'Laporan saya': '159:3533', 'Tanya Jawab (FAQ)': '132:2', 'Riwayat percakapan': '138:2' },
};
const pg = await figma.getNodeByIdAsync(CFG.pageId); await figma.setCurrentPageAsync(pg);
const frame = await figma.getNodeByIdAsync(CFG.frame);
const comp = await figma.getNodeByIdAsync('88:3');
const log = { dibuang: [], aktif: CFG.aktif, reaction: [] };
// 1. buang header tangkapan & navbar lama (cari sampai 3 tingkat dalam, hanya yang lebar penuh & tinggi ≤ 80)
let induk = null, urut = -1;
for (const n of frame.findAll(x => x.parent && x.width >= 1200 && x.height <= 80 && x.y <= 2 && (x.type !== 'INSTANCE' || (x.mainComponent && x.mainComponent.id === '88:3')) && (CFG.buang.test(x.name) || x.type === 'INSTANCE'))) {
  if (n.removed) continue; if (!induk) { induk = n.parent; urut = induk.children.indexOf(n); } log.dibuang.push(n.name + ' ' + n.id); n.remove();
}
// 2. pasang instance: menggantikan header tangkapan di induk & urutan yang sama (isi di bawahnya ikut naik ke y=56); tanpa header → ABSOLUTE di (0,0)
const inst = comp.createInstance(); inst.name = 'Navbar · Pegawai';
if (induk) { induk.insertChild(urut, inst); inst.resize(1440, 56); if ('layoutMode' in induk && induk.layoutMode !== 'NONE') inst.layoutSizingHorizontal = 'FIXED'; }
else { frame.appendChild(inst); if ('layoutMode' in frame && frame.layoutMode !== 'NONE') inst.layoutPositioning = 'ABSOLUTE'; inst.x = 0; inst.y = 0; inst.resize(1440, 56); }
// 3+4. garis aktif & reaction
const acuan = CFG.acuan ? await figma.getNodeByIdAsync(CFG.acuan) : null;
const WHITE = [{ type: 'SOLID', color: { r: 1, g: 1, b: 1 } }], ORANGE = [{ type: 'SOLID', color: { r: 0.95, g: 0.55, b: 0.30 } }];
for (const item of inst.findOne(n => n.name === 'Menu').children) {
  const nama = item.name.replace(/^Nav: /, ''); const rect = item.findOne(n => n.type === 'RECTANGLE');
  if (rect) rect.fills = nama === CFG.aktif ? ORANGE : WHITE;
  const dest = nama === CFG.aktif ? null : CFG.tujuan[nama];
  await item.setReactionsAsync(dest ? [{ trigger: { type: 'ON_CLICK' }, actions: [{ type: 'NODE', destinationId: dest, navigation: 'NAVIGATE', transition: null, preserveScrollPosition: false }] }] : []);
  log.reaction.push(nama + (dest ? ' → ' + dest : ' (aktif)'));
}
if (acuan) for (const nm of ['Chip Pegawai', 'BPS (struktur pohon)', 'Avatar']) {
  const src = acuan.findOne(n => n.name === nm), dst = inst.findOne(n => n.name === nm);
  if (src && dst && src.reactions.length) { await dst.setReactionsAsync(src.reactions); log.reaction.push(nm + ' (salin dari acuan)'); }
}
return { frame: frame.id, instance: inst.id, ...log };
