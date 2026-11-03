const api = require('../../utils/api')
const F = require('../../utils/format')
const L = require('../../utils/labels')
const { text } = require('../../utils/text')

Page({
  data: {
    part: null,
    rows: [],
    derived: [],
    reviews: [],
    offers: [],
    sources: [],
    image: '',
    webUrl: '',
    tierLabel: '',
    tierNote: '',
    tierColor: '',
    priceLabel: '',
    basis: '',
    keySpecs: [],
    version: '',
    rating: null,
    loading: true,
    error: '',
    timelinePreview: false,
  },

  onLoad(query) {
    this.id = decodeURIComponent(query.id || '')
    this.setData({ timelinePreview: Number(query.scene) === 1154 })
    this.load()
  },

  onPullDownRefresh() {
    this.load().then(() => wx.stopPullDownRefresh(), () => wx.stopPullDownRefresh())
  },

  async load() {
    this.setData({ loading: true, error: '' })
    try {
      const p = await api.get('/parts/' + encodeURIComponent(this.id), { posts_kind: 'review', posts_limit: 5 })
      const t = F.tier(p.source_tier)
      const specs = p.specs || {}
      const hidden = ['image_url', 'image_source', 'doc_url', 'doc_pdf',
        'repo_urls', 'repo_license', 'tags', 'coupon', 'fetched_at', 'category_cn']
      const rows = Object.keys(specs)
        .filter(k => !hidden.includes(k))
        .filter(k => specs[k] !== null && specs[k] !== undefined && specs[k] !== '')
        .slice(0, 80)
        .map(k => ({ key: k, label: L.partLabel(k), value: text(specs[k]) }))

      const derived = Object.keys(p.derived || {})
        .filter(k => p.derived[k] !== null && p.derived[k] !== undefined)
        .map(k => ({
          key: k,
          label: L.DERIVED[k] || L.humanize(k),
          value: text(p.derived[k]),
        }))

      const reviews = (p.posts || [])
        .filter(x => x.kind === 'review')
        .slice(0, 3)
        .map(x => ({
          id: x.id,
          title: x.title,
          body: F.short(x.body, 100),
          rating: x.rating,
          score: x.score,
          author: x.author && x.author.display_name,
        }))

      const sources = []
      if (p.url) sources.push({ label: '厂商 / 商品页', url: p.url })
      if (specs.doc_url) sources.push({ label: '官方资料', url: specs.doc_url })
      if (specs.doc_pdf) sources.push({ label: '官方手册 PDF', url: specs.doc_pdf })

      let basis = ''
      if (specs.tau_basis) basis += '扭矩口径：' + (specs.tau_basis === 'peak' ? '峰值' : specs.tau_basis === 'rated' ? '额定' : specs.tau_basis) + '；'
      if (specs.inertia_basis) basis += '惯量口径：' + (specs.inertia_basis === 'rotor' ? '转子侧' : specs.inertia_basis === 'output' ? '输出端' : specs.inertia_basis)

      this.setData({
        part: p,
        rows,
        derived,
        reviews,
        offers: (p.offers || []).filter(o => o.url && o.kind !== 'sponsor').slice(0, 3),
        sources,
        image: F.imageUrl(p.image_url),
        webUrl: F.partUrl(p),
        tierLabel: t.label,
        tierNote: t.note,
        tierColor: t.color,
        priceLabel: F.price(p.price_cny),
        basis,
        keySpecs: (p.key_specs || []).map(x => `${x.label} ${x.value}`),
        version: (getApp().globalData || {}).dataVersion || '',
        loading: false,
      })
      wx.setNavigationBarTitle({ title: p.model || p.title || '部件详情' })
      this.loadRating()
    } catch (e) {
      this.setData({ loading: false, error: e.message })
    }
  },

  async loadRating() {
    try {
      const r = await api.get('/ratings/' + encodeURIComponent(this.id))
      if (!r.count) {
        this.setData({ rating: null })
        return
      }
      const bars = Object.keys(r.histogram || {})
        .map(k => ({ score: k, n: r.histogram[k] || 0 }))
        .sort((a, b) => Number(b.score) - Number(a.score))
      this.setData({ rating: Object.assign({}, r, { bars }) })
    } catch (e) {}
  },

  async copyLink() {
    // web_path 由 API 给出，和站点 slug 同规则；不再为拿 canonical 多等一次 /share 请求。
    F.copy(this.data.webUrl, '网页链接已复制')
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

  copyOffer(e) {
    const url = e.currentTarget.dataset.url
    if (!url) {
      wx.showToast({ title: '该优惠没有可复制链接', icon: 'none' })
      return
    }
    F.copy(url, '优惠链接已复制')
  },

  onImageError() {
    this.setData({ image: '' })
  },

  shareBits() {
    const p = this.data.part || {}
    const bits = [p.model || p.title || '部件']
    if (this.data.priceLabel && this.data.priceLabel !== '价格未公布') bits.push(this.data.priceLabel)
    if (p.source_tier) bits.push(p.source_tier + ' 级')
    if (this.data.keySpecs && this.data.keySpecs.length) bits.push(this.data.keySpecs[0])
    return bits
  },

  onShareAppMessage() {
    return {
      title: this.shareBits().join(' · '),
      path: `/pages/part/part?id=${encodeURIComponent(this.id)}`,
      imageUrl: this.data.image || undefined,
    }
  },

  onShareTimeline() {
    return {
      title: this.shareBits().join(' · '),
      query: `id=${encodeURIComponent(this.id)}`,
    }
  },
})
