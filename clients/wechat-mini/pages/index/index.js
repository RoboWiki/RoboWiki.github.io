const api = require('../../utils/api')

Page({
  data: {
    tab: 'parts', q: '', items: [], total: 0, loading: false, error: '', version: '',
  },
  onLoad() { this.loadMeta(); this.load() },
  async loadMeta() { try { const m = await api.get('/meta'); this.setData({ version: m.data_version || '' }) } catch (e) {} },
  onSearch(e) { this.setData({ q: e.detail.value }); clearTimeout(this.t); this.t = setTimeout(() => this.load(), 350) },
  switchTab(e) { const tab = e.currentTarget.dataset.tab; if (tab !== this.data.tab) { this.setData({ tab, items: [] }); this.load() } },
  async load() {
    this.setData({ loading: true, error: '' })
    try {
      const q = this.data.q.trim()
      const data = this.data.tab === 'parts'
        ? await api.get('/parts', { q: q || undefined, limit: 30 })
        : await api.get('/materials', { q: q || undefined, limit: 50 })
      this.setData({ items: data.items || [], total: data.total || 0, loading: false })
      getApp().globalData.dataVersion = data.data_version || ''
    } catch (e) {
      this.setData({ loading: false, error: e.message })
    }
  },
  openItem(e) {
    const id = encodeURIComponent(e.currentTarget.dataset.id)
    const page = this.data.tab === 'parts' ? 'part/part' : 'material/material'
    wx.navigateTo({ url: `/pages/${page}?id=${id}` })
  },
  onShareAppMessage() {
    return { title: 'RoboWiki · 机器人硬件目录', path: '/pages/index/index' }
  },
})
