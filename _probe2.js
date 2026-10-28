(function () {
  var c = document.querySelector('.part-tags');
  if (!c) return 'no container';
  var cs = getComputedStyle(c);
  var kids = Array.prototype.slice.call(c.children).map(function (k) {
    var r = k.getBoundingClientRect();
    var ks = getComputedStyle(k);
    return {
      t: k.textContent.trim().slice(0, 8),
      w: Math.round(r.width), h: Math.round(r.height),
      x: Math.round(r.x),
      disp: ks.display, jc: ks.justifyContent, flex: ks.flex, alignSelf: ks.alignSelf,
      minW: ks.minWidth, pad: ks.padding, fs: ks.fontSize
    };
  });
  return JSON.stringify({
    container: {
      w: Math.round(c.getBoundingClientRect().width),
      h: Math.round(c.getBoundingClientRect().height),
      display: cs.display, jc: cs.justifyContent, ai: cs.alignItems,
      gap: cs.gap, flexWrap: cs.flexWrap, cls: c.className
    },
    kids: kids
  });
})()
