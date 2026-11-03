const api = require('../../utils/api')
const LABELS = {
  density_g_cm3: '密度 (g/cm³)', modulus_GPa: '弹性模量 (GPa)', tensile_MPa: '抗拉强度 (MPa)',
  yield_MPa: '屈服强度 (MPa)', elongation_pct: '断裂延伸率 (%)', hardness: '硬度',
  service_temp_C: '长期工作温度 (°C)', low_temp_C: '低温下限 (°C)', melting_C: '熔点 (°C)',
  thermal_cond_W_mK: '导热系数 (W/(m·K))', cte_um_mK: '线膨胀系数 (µm/(m·K))',
  tolerance_mm: '可达公差 (mm)', surface_ra_um: '表面粗糙度 Ra (µm)',
  layer_height_mm: '层高 (mm)', min_wall_mm: '最小壁厚 (mm)', max_size: '最大尺寸',
  cost_level: '成本档', lead_time: '参考交期', price_level: '价格档',
}
Page({
  data: { item: null, rows: [], error: '', loading: true },
  onLoad(query) { this.id = decodeURIComponent(query.id || ''); this.load() },
  async load() {
    try {
      const r = await api.get('/materials/' + encodeURIComponent(this.id))
      const rows = Object.keys(r.specs || {})
        .filter(k => r.specs[k] !== null && r.specs[k] !== '' && LABELS[k])
        .map(k => ({ label: LABELS[k], value: String(r.specs[k]) }))
      this.setData({ item: r, rows, loading: false })
    } catch (e) { this.setData({ error: e.message, loading: false }) }
  },
  onShareAppMessage() {
    const r = this.data.item || {}
    return { title: `${r.name || '材质'} · RoboWiki`, path: `/pages/material/material?id=${encodeURIComponent(this.id)}` }
  },
})
