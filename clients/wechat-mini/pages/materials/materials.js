const api = require('../../utils/api')
const F = require('../../utils/format')

const PAGE_SIZE = 20

Page({
  data: {
    q: '',
    category: '',
    categories: [
      { id: '', label: '全部' },
      { id: 'material', label: '材料' },
      { id: 'process', label: '工艺' },
    ],
    items: [],
    total: 0,
    loading: true,
    loadingMore: false,
    hasMore: false,
    error: '',
    version: '',
  },

  onLoad(options = {}) {
    this._seq = 0
    this.setData({
      q: options.q ? decodeURIComponent(options.q) : '',
      category: options.category ? decodeURIComponent(options.category) : '',
    })
    this.load(true)
  },

  onPullDownRefresh() {
    this.load(true).then(() => wx.stopPullDownRefresh(), () => wx.stopPullDownRefresh())
  },

  onReachBottom() {
    if (this.data.hasMore && !this.data.loadingMore) this.load(false)
  },

  onSearch(e) {
    this.setData({ q: e.detail.value })
    clearTimeout(this._t)
    this._t = setTimeout(() => this.load(true), 350)
  },

  onSearchConfirm() { clearTimeout(this._t); this.load(true) },

  clearSearch() { clearTimeout(this._t); this.setData({ q: '' }); this.load(true) },

  selectCategory(e) {
    const id = e.currentTarget.dataset.id || ''
    if (id === this.data.category) return
    this.setData({ category: id })
    this.load(true)
  },

  async load(reset) {
    const seq = ++this._seq
    if (reset) this.setData({ loading: true, error: '' })
    else this.setData({ loadingMore: true })

    const params = { limit: PAGE_SIZE, offset: reset ? 0 : this.data.items.length }
    const q = this.data.q.trim()
    if (q) params.q = q
    if (this.data.category) params.category = this.data.category

    try {
      const d = await api.get('/materials', params)
      if (seq !== this._seq) return
      const incoming = (d.items || []).map(r => {
        const t = F.tier(r.source_tier)
        return {
          id: r.id,
          name: r.name,
          category: r.category,
          source_tier: r.source_tier,
          glyph: (r.name || '?').slice(0, 1),
          subline: [r.group_label, r.family_label].filter(Boolean).join(' · '),
          tierLabel: t.label,
          tierColor: t.color,
        }
      })
      const patch = {
        total: d.total || 0,
        loading: false,
        loadingMore: false,
        hasMore: (reset ? incoming.length : this.data.items.length + incoming.length) < (d.total || 0),
        version: d.data_version || this.data.version,
        error: '',
      }
      if (reset) patch.items = incoming
      else incoming.forEach((it, i) => { patch[`items[${this.data.items.length + i}]`] = it })
      this.setData(patch)
    } catch (e) {
      if (seq !== this._seq) return
      this.setData({ loading: false, loadingMore: false, hasMore: false, error: e.message })
    }
  },

  open(e) {
    wx.navigateTo({ url: `/pages/material/material?id=${encodeURIComponent(e.currentTarget.dataset.id)}` })
  },

  onShareAppMessage() {
    const qs = []
    if (this.data.q.trim()) qs.push('q=' + encodeURIComponent(this.data.q.trim()))
    if (this.data.category) qs.push('category=' + encodeURIComponent(this.data.category))
    const query = qs.join('&')
    return {
      title: 'RoboWiki 材质库 · 材料与加工工艺',
      path: '/pages/materials/materials' + (query ? '?' + query : ''),
    }
  },

  onShareTimeline() {
    return { title: 'RoboWiki 材质库 · 材料与加工工艺' }
  },
})
