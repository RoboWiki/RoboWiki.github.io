const api = require('../../utils/api')
const F = require('../../utils/format')
const L = require('../../utils/labels')

function text(v) {
  if (v === null || v === undefined || v === '') return ''
  if (Array.isArray(v)) return v.join('、')
  if (typeof v === 'object') return JSON.stringify(v)
  return String(v)
}

Page({
  data: {
    item: null,
    rows: [],
    related: [],
    sources: [],
    webUrl: '',
    tierLabel: '',
    tierNote: '',
    tierColor: '',
    version: '',
    loading: true,
    error: '',
  },

  onLoad(query) {
    this.id = decodeURIComponent(query.id || '')
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
      const rows = Object.keys(specs)
        .filter(k => specs[k] !== null && specs[k] !== undefined && specs[k] !== '')
        .map(k => ({ key: k, label: L.materialLabel(k), value: text(specs[k]) }))

      const sources = (r.sources || []).map(s => ({
        url: s.url,
        label: s.kind || '来源',
        checked: s.checked_on || '',
      }))

      this.setData({
        item: r,
        rows,
        related: r.related || [],
        sources,
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

  copyLink() {
    F.copy(this.data.webUrl, '网页链接已复制')
  },

  retry() { this.load() },

  goHome() { wx.reLaunch({ url: '/pages/index/index' }) },

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
