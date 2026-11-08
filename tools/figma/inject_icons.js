// inject_icons: ganti glyph webfont Tabler (<i class="ti ti-xxx">, kosong saat ditangkap ke Figma) dengan SVG inline.
// Dipanggil otomatis oleh capture.js sebelum tangkap. Sumber SVG: @tabler/icons (jsDelivr, versi dikunci).
const VER = '3.19.0';
const cache = {};
module.exports = async function injectIcons(page) {
  const names = await page.evaluate(() => [...new Set([...document.querySelectorAll('.ti')]
    .map(e => (e.className.match(/\bti-([a-z0-9-]+)/) || [])[1]).filter(Boolean))]);
  const svgs = {}, missing = [];
  for (const n of names) {
    if (!(n in cache)) {
      let r = await fetch(`https://cdn.jsdelivr.net/npm/@tabler/icons@${VER}/icons/outline/${n}.svg`);
      if (!r.ok && /-filled$/.test(n)) r = await fetch(`https://cdn.jsdelivr.net/npm/@tabler/icons@${VER}/icons/filled/${n.replace(/-filled$/, '')}.svg`);
      cache[n] = r.ok ? await r.text() : null;
    }
    if (cache[n]) svgs[n] = cache[n]; else missing.push(n);
  }
  await page.evaluate((svgs) => {
    const st = document.createElement('style');
    st.textContent = '.ti::before{content:none!important}.ti{display:inline-flex;align-items:center;justify-content:center}';
    document.head.appendChild(st);
    document.querySelectorAll('.ti').forEach(e => {
      const n = (e.className.match(/\bti-([a-z0-9-]+)/) || [])[1];
      if (!n || !svgs[n]) return;
      const px = Math.round(parseFloat(getComputedStyle(e).fontSize)) || 16;
      e.innerHTML = svgs[n].replace(/width="24"/, `width="${px}"`).replace(/height="24"/, `height="${px}"`);
    });
  }, svgs);
  return { diganti: Object.keys(svgs).length, tidakAda: missing };
};
