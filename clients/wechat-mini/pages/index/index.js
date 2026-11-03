const api = require('../../utils/api')
const F = require('../../utils/format')

const PAGE_SIZE = 20

Page({
  data: {
    tab: 'parts',
    q: '',
    category: '',
    categories: [{ id: '', label: '全部' }],
    items: [],
    total: 0,
    loading: false,
    loadingMore: false,
    error: '',
    version: '',
    partCount: 0,
    materialCount: 0,
    hasMore: false,
  },

  onLoad(options = {}) {
    this._seq = 0
    const tab = options.tab === 'materials' ? 'materials' : 'parts'
    this.setData({
      tab,
      q: options.q ? decodeURIComponent(options.q) : '',
      category: options.category ? decodeURIComponent(options.category) : '',
      categories: this.categoriesFor(tab),
    })
    this.loadMeta()
    this.loadCatalog()
    this.load(true)
  },

  onPullDownRefresh() {
    this.loadMeta()
    this.loadCatalog()
    this.load(true).then(() => wx.stopPullDownRefresh(), () => wx.stopPullDownRefresh())
  },

  onReachBottom() {
    if (this.data.hasMore && !this.data.loading && !this.data.loadingMore) this.load(false)
  },

  async loadMeta() {
    try {
      const [meta, mm] = await Promise.all([
        api.get('/meta'),
        api.get('/materials/meta'),
      ])
      this.setData({
        version: meta.data_version || '',
        materialCount: mm.total || 0,
      })
    } catch (e) {}
  },

  async loadCatalog() {
    try {
      const c = await api.get('/catalog')
      const counts = {}
      ;(c.facets || []).forEach(f => { counts[f.category] = (counts[f.category] || 0) + f.n })
      const cats = Object.keys(c.categories || {})
        .filter(id => counts[id])
        .map(id => ({ id, label: c.categories[id], n: counts[id] }))
      this._partCategories = [{ id: '', label: '全部' }].concat(cats)
      this.setData({
        partCount: c.total || 0,
        categories: this.data.tab === 'parts'
          ? this._partCategories
          : this.data.categories,
      })
    } catch (e) {}
  },

  categoriesFor(tab) {
    if (tab === 'materials') {
      return [
        { id: '', label: '全部' },
        { id: 'material', label: '材料' },
        { id: 'process', label: '工艺' },
      ]
    }
    return this._partCategories || [{ id: '', label: '全部' }]
  },

  switchTab(e) {
    const tab = e.currentTarget.dataset.tab
    if (tab === this.data.tab) return
    if (this.data.tab === 'parts') this._partCategories = this.data.categories
    this.setData({
      tab,
      category: '',
      categories: this.categoriesFor(tab),
      items: [],
      total: 0,
      error: '',
    })
    this.load(true)
  },

  selectCategory(e) {
    const id = e.currentTarget.dataset.id || ''
    if (id === this.data.category) return
    this.setData({ category: id, items: [], total: 0 })
    this.load(true)
  },

  onSearch(e) {
    const q = e.detail.value
    this.setData({ q })
    clearTimeout(this._t)
    this._t = setTimeout(() => this.load(true), 350)
  },

  onSearchConfirm() {
    clearTimeout(this._t)
    this.load(true)
  },

  clearSearch() {
    clearTimeout(this._t)
    this.setData({ q: '' })
    this.load(true)
  },

  async load(reset) {
    const seq = ++this._seq
    if (reset) this.setData({ loading: true, error: '' })
    else this.setData({ loadingMore: true })

    const isParts = this.data.tab === 'parts'
    const offset = reset ? 0 : this.data.items.length
    const params = { limit: PAGE_SIZE, offset }
    const q = this.data.q.trim()
    if (q) params.q = q
    if (this.data.category) params.category = this.data.category
    if (isParts) params.compact = true

    try {
      const d = await api.get(isParts ? '/parts' : '/materials', params)
      if (seq !== this._seq) return
      const incoming = (d.items || []).map(isParts ? this.decoratePart : this.decorateMaterial)
      const patch = {
        total: d.total || 0,
        loading: false,
        loadingMore: false,
        hasMore: (reset ? incoming.length : this.data.items.length + incoming.length) < (d.total || 0),
        error: '',
        version: d.data_version || this.data.version,
      }
      if (reset) patch.items = incoming
      else incoming.forEach((it, i) => { patch[`items[${this.data.items.length + i}]`] = it })
      this.setData(patch)
    } catch (e) {
      if (seq !== this._seq) return
      this.setData({
        loading: false,
        loadingMore: false,
        error: e.message,
        hasMore: false,
      })
    }
  },

  decoratePart(p) {
    const t = F.tier(p.source_tier)
    return {
      id: p.id,
      title: p.title,
      category: p.category,
      category_label: p.category_label,
      source_tier: p.source_tier,
      image: F.imageUrl(p.image_url),
      glyph: (p.category_label || p.title || 'R').slice(0, 1),
      subline: [p.vendor, p.model, p.category_label].filter(Boolean).join(' · '),
      priceLabel: F.price(p.price_cny),
      tierLabel: t.label,
      tierColor: t.color,
      verifiedLabel: p.verified && p.source_tier === 'A' ? '已核对' : '',
    }
  },

  decorateMaterial(r) {
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
  },

  openItem(e) {
    const id = encodeURIComponent(e.currentTarget.dataset.id)
    const page = this.data.tab === 'parts' ? 'part/part' : 'material/material'
    wx.navigateTo({ url: `/pages/${page}?id=${id}` })
  },

  onImageError(e) {
    const i = Number(e.currentTarget.dataset.index)
    if (!isNaN(i)) this.setData({ [`items[${i}].image`]: '' })
  },

  onShareAppMessage() {
    const qs = []
    if (this.data.tab !== 'parts') qs.push('tab=' + encodeURIComponent(this.data.tab))
    if (this.data.q.trim()) qs.push('q=' + encodeURIComponent(this.data.q.trim()))
    if (this.data.category) qs.push('category=' + encodeURIComponent(this.data.category))
    const query = qs.join('&')
    return {
      title: 'RoboWiki · 机器人硬件目录',
      path: '/pages/index/index' + (query ? '?' + query : ''),
    }
  },

  onShareTimeline() {
    return { title: 'RoboWiki · 机器人硬件目录' }
  },
})
