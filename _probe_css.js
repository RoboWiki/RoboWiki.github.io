(function () {
  var sp = document.querySelector('.part-tags span.part-tag');
  if (!sp) return 'no span';
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
      var keys = ['display', 'padding', 'font-size', 'line-height', 'height',
                  'min-height', 'border-radius', 'align-items', 'flex', 'white-space'];
      var kv = [];
      for (var k = 0; k < keys.length; k++) {
        var v = d.getPropertyValue(keys[k]);
        if (v) kv.push(keys[k] + '=' + v);
      }
      if (!kv.length) continue;
      var name = (ss.href || 'inline').split('/').pop().slice(0, 28);
      out.push(name + ' :: ' + r.selectorText + ' { ' + kv.join('; ') + ' }');
    }
  }
  return JSON.stringify(out.slice(0, 16));
})()
