// 规格值渲染：对象/对象数组不能直接 JSON.stringify，也不能变成 [object Object]。
// 规则与网页 build_site.py 的 _val 对齐：字典 -> 「k x；」，价格阶梯 -> 「N 件 ¥P」。
function scalar(v) {
  if (v === null || v === undefined || v === '') return ''
  if (typeof v === 'boolean') return v ? '是' : '否'
  return String(v)
}

function text(v) {
  if (v === null || v === undefined || v === '') return ''
  if (typeof v === 'boolean') return v ? '是' : '否'
  if (Array.isArray(v)) {
    if (v.every(x => x && typeof x === 'object' && ('qty' in x || 'price' in x))) {
      return v.map(x => `${x.qty !== undefined ? `${x.qty} 件` : ''}${x.qty !== undefined && x.price !== undefined ? ' ' : ''}${x.price !== undefined ? `¥${x.price}` : ''}`).join('；')
    }
    return v.map(x => (x && typeof x === 'object' ? text(x) : scalar(x))).join('、')
  }
  if (typeof v === 'object') {
    return Object.keys(v).map(k => `${k} ${text(v[k])}`).join('；')
  }
  return String(v)
}

module.exports = { text, scalar }
