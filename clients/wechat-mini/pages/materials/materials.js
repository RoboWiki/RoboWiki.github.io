const api = require('../../utils/api')
Page({
  data: { items: [], total: 0, loading: true, error: '' },
  onLoad() { this.load() },
  async load() {
    try {
      const d = await api.get('/materials', { limit: 100 })
      this.setData({ items: d.items || [], total: d.total || 0, loading: false })
    } catch (e) { this.setData({ error: e.message, loading: false }) }
  },
  open(e) { wx.navigateTo({ url: `/pages/material/material?id=${encodeURIComponent(e.currentTarget.dataset.id)}` }) },
  onShareAppMessage() { return { title: 'RoboWiki 材质库', path: '/pages/materials/materials' } },
})
