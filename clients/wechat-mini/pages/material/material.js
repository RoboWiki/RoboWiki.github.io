const api = require('../../utils/api')
const F = require('../../utils/format')
const L = require('../../utils/labels')
const { text } = require('../../utils/text')

function formatForms(forms) {
  if (!Array.isArray(forms) || !forms.length) return ''
  return forms.map(f => {
    if (!f || typeof f !== 'object') return text(f)
    const spec = f.spec ? `：${text(f.spec)}` : ''
    const note = f.note ? `（${text(f.note)}）` : ''
    return `${text(f.form)}${spec}${note}`
  }).join('；')
}

function safeDecode(v) {
  try { return decodeURIComponent(v || '') } catch (e) { return String(v || '') }
}

Page({
  data: {
    item: null,
    rows: [],
    related: [],
    sources: [],
    formsText: '',
    prosText: '',
    consText: '',
    suppliers: [],
    webUrl: '',
    tierLabel: '',
    tierNote: '',
    tierColor: '',
    version: '',
    loading: true,
    error: '',
    timelinePreview: false,
  },

  onLoad(query) {
    this.id = safeDecode(query.id)
    this.setData({ timelinePreview: Number(query.scene) === 1154 })
    this.load()
  },

  onPullDownRefresh() {
    this.load().then(() => wx.stopPullDownRefresh(), () => wx.stopPullDownRefresh())
  },

  async load() {
    this.setData({ loading: true, error: '' })
    try {
      const r = await api.get('/materials/' + encodeURIComponent(this.id))
      const t = F.tier(r.source_tier)
      const specs = r.specs || {}
      const hidden = ['image_url', 'image_source', 'doc_url', 'doc_pdf',
        'repo_urls', 'repo_license', 'tags', 'coupon', 'fetched_at', 'category_cn']
      const rows = Object.keys(specs)
        .filter(k => k !== 'modulus_kind' && !hidden.includes(k))
        .filter(k => specs[k] !== null && specs[k] !== undefined && specs[k] !== '')
        .map(k => ({
          key: k,
          label: k === 'modulus_GPa' && specs.modulus_kind === '弯曲'
            ? '弯曲模量 (GPa)'
            : L.materialLabel(k),
          value: text(specs[k]),
        }))

      const sources = (r.sources || []).map(s => ({
        url: s.url,
        label: s.kind || '来源',
        checked: s.checked_on || '',
      }))
      if (specs.doc_url && !sources.some(s => s.url === specs.doc_url)) {
        sources.unshift({ url: specs.doc_url, label: '官方资料', checked: '' })
      }
      const suppliers = (r.suppliers || []).map((s, i) => ({
        key: `${s.supplier_id || s.name || s.id || 'supplier'}-${i}`,
        name: s.name || s.supplier_id || s.id || '供应商',
        role: s.role || '',
        note: s.note || '',
      }))

      this.setData({
        item: r,
        rows,
        related: r.related || [],
        sources,
        formsText: formatForms(r.forms),
        prosText: text(r.pros),
        consText: text(r.cons),
        suppliers,
        webUrl: F.materialUrl(r),
        tierLabel: t.label,
        tierNote: t.note,
        tierColor: t.color,
        version: r.data_version || (getApp().globalData || {}).dataVersion || '',
        loading: false,
      })
      wx.setNavigationBarTitle({ title: r.name || '材料 / 工艺' })
    } catch (e) {
      this.setData({ loading: false, error: e.message })
    }
  },

  async copyLink() {
    // 与网页分享卡同一份 JSON：canonical_url / data_version / copy_text 不另拼。
    const r = this.data.item || {}
    let url = this.data.webUrl
    try {
      const json = F.shareMaterialUrl(r)
      if (json) {
        const share = await api.getUrl(json)
        if (share && share.canonical_url) url = share.canonical_url
      }
    } catch (e) {}
    F.copy(url, '网页链接已复制')
  },

  retry() { this.load() },

  goHome() {
    const pages = getCurrentPages()
    if (pages.length > 1) wx.navigateBack()
    else wx.reLaunch({ url: '/pages/index/index' })
  },

  copySource(e) {
    F.copy(e.currentTarget.dataset.url, '来源链接已复制')
  },

  openRelated(e) {
    wx.navigateTo({ url: `/pages/material/material?id=${encodeURIComponent(e.currentTarget.dataset.id)}` })
  },

  onShareAppMessage() {
    const r = this.data.item || {}
    return {
      title: `${r.name || '材质'} · RoboWiki`,
      path: `/pages/material/material?id=${encodeURIComponent(this.id)}`,
    }
  },

  onShareTimeline() {
    const r = this.data.item || {}
    return {
      title: `${r.name || '材质'} · RoboWiki`,
      query: `id=${encodeURIComponent(this.id)}`,
    }
  },
})
