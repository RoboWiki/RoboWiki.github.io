const api = require('../../utils/api')
const F = require('../../utils/format')

const PAGE_SIZE = 20

Page({
  data: {
    tab: 'parts',
    q: '',
    category: '',
    sort: 'featured',
    categories: [{ id: '', label: '全部' }],
    materialGroups: [],
    materialGroup: '',
    materialSort: 'default',
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
      sort: options.sort ? decodeURIComponent(options.sort) : 'featured',
      materialGroup: options.group ? decodeURIComponent(options.group) : '',
      materialSort: options.msort ? decodeURIComponent(options.msort) : 'default',
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
    clearTimeout(this._t)
    if (this.data.tab === 'parts') this._partCategories = this.data.categories
    this.setData({
      tab,
      q: '',
      category: '',
      materialGroup: '',
      materialSort: 'default',
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

  selectSort(e) {
    const sort = e.currentTarget.dataset.sort || 'featured'
    if (sort === this.data.sort) return
    this.setData({ sort, items: [], total: 0 })
    this.load(true)
  },

  selectMaterialGroup(e) {
    const id = e.currentTarget.dataset.id || ''
    if (id === this.data.materialGroup) return
    this.setData({ materialGroup: id, items: [], total: 0 })
    this.load(true)
  },

  selectMaterialSort(e) {
    const sort = e.currentTarget.dataset.sort || 'default'
    if (sort === this.data.materialSort) return
    this.setData({ materialSort: sort, items: [], total: 0 })
    this.load(true)
  },

  sortMaterialRows(rows) {
    const key = this.data.materialSort
    if (key === 'default') return rows
    const field = key === 'density' ? 'density_g_cm3'
      : key === 'modulus' ? 'modulus_GPa'
        : key === 'tensile' ? 'tensile_MPa' : ''
    if (!field) return rows
    return rows.slice().sort((a, b) => {
      const x = Number((a.specs || {})[field])
      const y = Number((b.specs || {})[field])
      if (!isFinite(x) && !isFinite(y)) return 0
      if (!isFinite(x)) return 1
      if (!isFinite(y)) return -1
      return y - x
    })
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
    const cacheKey = `rw:list:${this.data.tab}:${this.data.category}:${this.data.q.trim()}:${this.data.sort}`
    const params = { limit: isParts ? PAGE_SIZE : 100, offset }
    const q = this.data.q.trim()
    if (q) params.q = q
    if (this.data.category) params.category = this.data.category
    if (!isParts && this.data.materialGroup) params.group = this.data.materialGroup
    if (isParts) {
      params.compact = true
      if (this.data.sort === 'price_asc') {
        params.sort = 'price'
        params.order = 'asc'
      } else if (this.data.sort === 'price_desc') {
        params.sort = 'price'
        params.order = 'desc'
      }
    }

    try {
      const d = await api.get(isParts ? '/parts' : '/materials', params)
      if (seq !== this._seq) return
      const rawRows = isParts ? (d.items || []) : this.sortMaterialRows(d.items || [])
      const incoming = rawRows.map(isParts ? this.decoratePart : this.decorateMaterial)
      const patch = {
        total: d.total || 0,
        materialGroups: isParts ? this.data.materialGroups : (d.groups || this.data.materialGroups),
        loading: false,
        loadingMore: false,
        hasMore: (reset ? incoming.length : this.data.items.length + incoming.length) < (d.total || 0),
        error: '',
        version: d.data_version || this.data.version,
      }
      if (reset) patch.items = incoming
      else incoming.forEach((it, i) => { patch[`items[${this.data.items.length + i}]`] = it })
      this.setData(patch)
      try {
        if (reset && incoming.length) {
          wx.setStorageSync(cacheKey, {
            items: incoming,
            total: d.total || 0,
            version: d.data_version || this.data.version,
            savedAt: Date.now(),
          })
        }
      } catch (err) {}
    } catch (e) {
      if (seq !== this._seq) return
      // 接口不通时回退到上次成功数据；群链接用户不该对着空白页发呆。
      let cached = null
      try { cached = wx.getStorageSync(cacheKey) } catch (err) {}
      if (reset && cached && cached.items && cached.items.length) {
        this.setData({
          items: cached.items,
          total: cached.total || cached.items.length,
          version: cached.version || this.data.version,
          loading: false,
          loadingMore: false,
          hasMore: false,
          error: `网络不可用，显示离线数据（${F.date(new Date(cached.savedAt || Date.now()).toISOString())}）`,
        })
        return
      }
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
      ratingAvg: p.rating_avg,
      ratingCount: p.rating_count || 0,
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

  shareQuery() {
    const qs = []
    if (this.data.tab !== 'parts') qs.push('tab=' + encodeURIComponent(this.data.tab))
    if (this.data.q.trim()) qs.push('q=' + encodeURIComponent(this.data.q.trim()))
    if (this.data.category) qs.push('category=' + encodeURIComponent(this.data.category))
    if (this.data.tab === 'materials' && this.data.materialGroup) {
      qs.push('group=' + encodeURIComponent(this.data.materialGroup))
    }
    if (this.data.tab === 'materials' && this.data.materialSort !== 'default') {
      qs.push('msort=' + encodeURIComponent(this.data.materialSort))
    }
    if (this.data.tab === 'parts' && this.data.sort && this.data.sort !== 'featured') {
      qs.push('sort=' + encodeURIComponent(this.data.sort))
    }
    return qs.join('&')
  },

  shareTitle() {
    const where = this.data.tab === 'parts' ? '部件库' : '材质库'
    const q = this.data.q.trim()
    const total = this.data.total || 0
    return `RoboWiki ${where}${q ? ` · ${q}` : ''}${total ? ` · ${total} 条` : ''}`
  },

  noop() {},

  onShareAppMessage(res) {
    // 卡片上的「分享」按钮：把这一条直接发给好友/群，而不是发当前筛选。
    if (res && res.from === 'button' && res.target && res.target.dataset && res.target.dataset.id) {
      const item = this.data.items.find(x => x.id === res.target.dataset.id)
      if (item) {
        const isPart = this.data.tab === 'parts'
        return {
          title: item.title || item.name || 'RoboWiki',
          path: `/pages/${isPart ? 'part/part' : 'material/material'}?id=${encodeURIComponent(item.id)}`,
          imageUrl: item.image || undefined,
        }
      }
    }
    const query = this.shareQuery()
    return {
      title: this.shareTitle(),
      path: '/pages/index/index' + (query ? '?' + query : ''),
    }
  },

  onShareTimeline() {
    const query = this.shareQuery()
    return { title: this.shareTitle(), query: query || undefined }
  },
})
