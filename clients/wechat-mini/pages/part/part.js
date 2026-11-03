const api = require('../../utils/api')
const LABELS = {
  tau_peak_Nm: '峰值扭矩 (N·m)', tau_rated_Nm: '额定扭矩 (N·m)', gear: '减速比',
  voltage_V: '额定电压 (V)', mass_kg: '质量 (kg)', speed_noload_rpm: '空载转速 (rpm)',
  positions: '位数', pitch_mm: '间距 (mm)', current_rated_A: '额定电流 (A)',
  voltage_rated_V: '电压等级 (V)', iface: '接口', npu_tops: 'NPU (TOPS)',
  range_m: '量程 (m)', depth_range_m: '深度量程 (m)', fov: '视场', fps: '帧率',
  encoder: '编码器', comm: '通信', ip: '防护等级',
}
Page({
  data: { part: null, rows: [], error: '', loading: true },
  onLoad(query) { this.id = decodeURIComponent(query.id || ''); this.load() },
  async load() {
    try {
      const p = await api.get('/parts/' + encodeURIComponent(this.id))
      const rows = Object.keys(p.specs || {})
        .filter(k => p.specs[k] !== null && p.specs[k] !== '' && LABELS[k])
        .slice(0, 24)
        .map(k => ({ label: LABELS[k], value: String(p.specs[k]) }))
      this.setData({ part: p, rows, loading: false })
    } catch (e) { this.setData({ error: e.message, loading: false }) }
  },
  copyUrl() {
    if (!this.data.part) return
    wx.setClipboardData({ data: this.data.part.url || '' })
  },
  onShareAppMessage() {
    const p = this.data.part || {}
    return { title: `${p.vendor || ''} ${p.model || ''} · RoboWiki`, path: `/pages/part/part?id=${encodeURIComponent(this.id)}` }
  },
})
