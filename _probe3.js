(function () {
  var sp = document.querySelector('.part-tags span.part-tag.sub');
  if (!sp) return 'no sub';
  var out = [];
  var sheets = Array.prototype.slice.call(document.styleSheets);
  for (var i = 0; i < sheets.length; i++) {
    var ss = sheets[i];
    var rules = null;
    try { rules = ss.cssRules; } catch (e) { continue; }
    if (!rules) continue;
    for (var j = 0; j < rules.length; j++) {
      var r = rules[j];
      if (!r.selectorText) continue;
      var hit = false;
      try { hit = sp.matches(r.selectorText); } catch (e2) { hit = false; }
      if (!hit) continue;
      var d = r.style;
      if (!d) continue;
      var pad = d.getPropertyValue('padding');
      var mt = d.getPropertyValue('margin-top');
      var ml = d.getPropertyValue('margin-left');
      if (!pad && !mt && !ml) continue;
      out.push((ss.href || 'inline').split('/').pop().slice(0, 26) +
               ' :: ' + r.selectorText + ' { pad=' + pad + ' mt=' + mt + ' ml=' + ml + ' }');
    }
  }
  return JSON.stringify(out);
})()
