// verify (tempel ke use_figma; read-only). Mengecek per Section: lintas peran, menggantung, self-link; dan keterjangkauan Alur Demo 01→12.
// Ubah CFG.sections bila perlu. Hasil: {sections:{nama:{frames,reactions,lintas,menggantung,selfLink}}, alurDemo:{...}}
const CFG = { sections: ['01 Pegawai', '02 Operator'], alur: 'Alur Demo', izinLintas: ['Login'], pageId: '49:2' };
const pg = await figma.getNodeByIdAsync(CFG.pageId); await figma.setCurrentPageAsync(pg);
const secOf = async (n) => { let c = n; while (c && c.type !== 'SECTION') c = c.parent; return c; };
const topOf = (n) => { let c = n; while (c.parent && c.parent.type !== 'SECTION' && c.parent.type !== 'PAGE') c = c.parent; return c; };
const destsOf = (n) => (n.reactions || []).flatMap(r => (r.actions || (r.action ? [r.action] : []))).map(a => a && a.destinationId).filter(x => x !== undefined);
async function scan(section) {
  const res = { frames: section.children.length, reactions: 0, lintas: [], menggantung: [], selfLink: [] };
  const nodes = section.findAll(n => n.reactions && n.reactions.length);
  for (const n of nodes) for (const d of destsOf(n)) {
    res.reactions++;
    const label = `${topOf(n).name.slice(0, 22)} / ${n.name.slice(0, 24)}`;
    if (!d) { res.menggantung.push(label); continue; }
    const dn = await figma.getNodeByIdAsync(d);
    if (!dn) { res.menggantung.push(label + ' →hilang'); continue; }
    const ds = await secOf(dn);
    if (!ds || ds.id !== section.id) { if (!(ds && CFG.izinLintas.some(x => ds.name.includes(x)))) res.lintas.push(`${label} → ${ds ? ds.name : '?'}`); }
    else if (topOf(dn).id === topOf(n).id) res.selfLink.push(label);
  }
  return res;
}
const out = { sections: {} };
for (const name of CFG.sections) { const s = pg.children.find(c => c.type === 'SECTION' && c.name === name); out.sections[name] = s ? await scan(s) : 'tidak ada'; }
// Alur Demo: BFS dari frame berawalan "01" lewat reaction; setiap frame berawalan 02..12 harus terjangkau
const ad = pg.children.find(c => c.type === 'SECTION' && c.name === CFG.alur);
const num = {}; for (const f of ad.children) { const m = f.name.match(/^(\d{2})\b/); if (m) num[m[1]] = f; }
const seen = new Set(), q = [num['01']];
while (q.length) { const f = q.shift(); if (!f || seen.has(f.id)) continue; seen.add(f.id);
  for (const n of [f, ...f.findAll(x => x.reactions && x.reactions.length)]) for (const d of destsOf(n)) { if (!d) continue; const dn = await figma.getNodeByIdAsync(d); if (dn) { const t = topOf(dn); if (!seen.has(t.id)) q.push(t); } } }
out.alurDemo = { frameBernomor: Object.keys(num).sort(), terjangkau: Object.keys(num).filter(k => seen.has(num[k].id)).sort(), tidakTerjangkau: Object.keys(num).filter(k => !seen.has(num[k].id)).sort(), totalTerjangkauBFS: seen.size };
return out;
