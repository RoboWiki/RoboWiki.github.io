const config = require('../config')

function site() {
  return config.SITE
}

function imageUrl(path) {
  if (!path) return ''
  if (/^https?:\/\//i.test(path)) return path
  return site() + (path.charAt(0) === '/' ? path : '/' + path)
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
  const digits = n >= 1000 ? 0 : n >= 1 ? 2 : 4
  // 低于千元保留到分；千元以上加千分位，和网页价格口径一致。
  const s = String(Number(n.toFixed(digits))).replace(/\B(?=(\d{3})+(?!\d))/g, ',')
  return '¥' + s
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
  if (!p) return site()
  if (p.web_path) return site() + p.web_path
  const slug = partSlug(p)
  if (slug.length < 2) return site() + '/catalog.html'
  return site() + '/parts/' + p.category + '/' + slug + '.html'
}

function sharePartUrl(p) {
  const slug = partSlug(p)
  if (!slug) return ''
  return site() + '/share/parts/' + p.category + '/' + slug + '.json'
}

function materialUrl(r) {
  if (!r) return site()
  if (r.web_path) return site() + r.web_path
  const id = String(r.id || '')
  const slug = r.category === 'process'
    ? 'process-' + id.replace(/^proc-/, '')
    : id.replace(/^mat-/, '')
  return site() + '/materials/' + slug + '.html'
}

/** 静态分享 JSON：标题、参数、来源、data_version、canonical_url 都在里面。
 *  复制链接优先读它的 canonical_url；读不到再退回 API 的 web_path。 */
function shareMaterialUrl(r) {
  if (!r) return ''
  let slug = ''
  if (r.web_path) {
    const m = String(r.web_path).match(/\/materials\/(.+)\.html$/)
    if (m) slug = m[1]
  }
  if (!slug) {
    const id = String(r.id || '')
    if (!id) return ''
    slug = r.category === 'process'
      ? 'process-' + id.replace(/^proc-/, '')
      : id.replace(/^mat-/, '')
  }
  return site() + '/share/materials/' + slug + '.json'
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

module.exports = {
  imageUrl, tier, price, short, date,
  partUrl, sharePartUrl, materialUrl, shareMaterialUrl, copy,
}
