(function () {
  const out = [];
  document.querySelectorAll('img').forEach(i => {
    const s = i.currentSrc || i.src;
    if (s) out.push(s + ' ' + i.naturalWidth + 'x' + i.naturalHeight);
  });
  document.querySelectorAll('*').forEach(el => {
    const g = getComputedStyle(el).backgroundImage;
    if (g && g.indexOf('url(') >= 0) {
      const u = g.slice(5, -2).replace(/["']/g, '');
      if (u.indexOf('http') === 0) out.push('BG ' + u);
    }
  });
  return JSON.stringify(Array.from(new Set(out)).slice(0, 24));
})()
