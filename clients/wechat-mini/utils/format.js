const { SITE } = require('../config')

function imageUrl(path) {
  if (!path) return ''
  if (/^https?:\/\//i.test(path)) return path
  return SITE + (path.charAt(0) === '/' ? path : '/' + path)
}

function tier(t) {
  if (t === 'A') return { label: 'A 级', note: '逐项核对过官方资料', color: 'a' }
  if (t === 'B') return { label: 'B 级', note: '公开资料汇编；购买或设计前请回原来源核对', color: 'b' }
  return { label: t ? t + ' 级' : '未分级', note: '来源等级未标注', color: 'c' }
}

function price(v) {
  if (v === null || v === undefined || v === '') return '价格未公布'
  const n = Number(v)
  if (!isFinite(n)) return '价格未公布'
  const digits = n >= 100 ? 0 : n >= 10 ? 1 : n >= 1 ? 2 : 4
  // 只去掉小数末尾的 0；直接对整串 replace 会把 1290 变成 129。
  return '¥' + String(Number(n.toFixed(digits)))
}

function short(text, n) {
  const s = String(text || '').replace(/\s+/g, ' ').trim()
  return s.length > n ? s.slice(0, n) + '…' : s
}

function date(iso) {
  return iso ? String(iso).slice(0, 10) : '—'
}

function partSlug(p) {
  if (p && p.web_path) {
    const m = String(p.web_path).match(/\/parts\/[^/]+\/(.+)\.html$/)
    if (m) return m[1]
  }
  const slug = String((p && p.id) || '').replace(/[^A-Za-z0-9]+/g, '-')
    .replace(/^-+|-+$/g, '').toLowerCase()
  return slug
}

function partUrl(p) {
  if (!p) return SITE
  if (p.web_path) return SITE + p.web_path
  const slug = partSlug(p)
  if (slug.length < 2) return SITE + '/catalog.html'
  return SITE + '/parts/' + p.category + '/' + slug + '.html'
}

function sharePartUrl(p) {
  const slug = partSlug(p)
  if (!slug) return ''
  return SITE + '/share/parts/' + p.category + '/' + slug + '.json'
}

function materialUrl(r) {
  if (!r) return SITE
  const id = String(r.id || '')
  const slug = r.category === 'process'
    ? 'process-' + id.replace(/^proc-/, '')
    : id.replace(/^mat-/, '')
  return SITE + '/materials/' + slug + '.html'
}

function copy(data, okText) {
  return new Promise((resolve) => {
    wx.setClipboardData({
      data: data || '',
      success() {
        wx.showToast({ title: okText || '已复制', icon: 'none' })
        resolve(true)
      },
      fail() { resolve(false) },
    })
  })
}

module.exports = { imageUrl, tier, price, short, date, partUrl, sharePartUrl, materialUrl, copy }
