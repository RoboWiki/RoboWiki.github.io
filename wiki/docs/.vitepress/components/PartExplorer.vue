<script setup lang="ts">
/**
 * 部件库：搜索 / 分类 / 厂商 / 排序 / 对比，全在浏览器里跑，没有一个 API 请求。
 *
 * 卡片按「以后要扩到各类机器人部件」来设计：图片 → 品牌型号 → 4 个关键参数 →
 * 价格与优惠 → 平均评分。关键参数按品类取，不是写死关节电机那四个。
 *
 * 术语：卡片上用「转子惯量」而不是 armature —— 对读者友好；但部件页里会写清
 * 它是**折算到输出端**的等效惯量（与电机本体的转子惯量差 N² 倍），口径不丢。
 */
import { computed, nextTick, onMounted, ref, watch } from 'vue'
import { withBase } from 'vitepress'
import catalogData from '../../public/catalog.json'

interface Offer {
  title: string | null
  kind: string | null
  price: number | null
  condition: string | null
  url: string | null
  expires: string | null
  demo: boolean
}

interface Part {
  id: string
  slug: string
  category: string
  subtype: string
  subtypeLabel: string
  vendor: string
  model: string
  tier: string
  verified: boolean
  price: number | null
  image: string | null
  rating: { avg: number | null; count: number }
  offer: Offer | null
  tauPeak: number | null
  tauRated: number | null
  gear: number | null
  mass: number | null
  armature: number | null
  rpm: number | null
  soc: string | null
  npuTops: number | null
  ramGb: number | null
  mcu: string | null
  can: number | null
  iface: string | null
  bits: number | null
  odrHz: number | null
  fps: number | null
  depthRange: string | null
  rangeM: number | null
  od: number | null
  len: number | null
  notes: string
  specs: Record<string, any>
}

const props = withDefaults(defineProps<{ lang?: 'zh' | 'en' }>(), { lang: 'zh' })
const en = computed(() => props.lang === 'en')
/** 只翻界面壳；型号与参数值保持原文。 */
const L = computed(() => en.value
  ? { featured: 'Catalogued', search: 'Search model / brand / type', compare: 'Compare', all: 'All params',
      none: 'No photo yet', count: 'items', sort: 'Sort by', vendor: 'Vendor', type: 'Type',
      sub: 'Subtype', reset: 'Reset' }
  : { featured: '入库', search: '搜型号 / 品牌 / 类型', compare: '对比', all: '全部参数',
      none: '暂无产品图', count: '件', sort: '按', vendor: '厂商', type: '类型',
      sub: '子类', reset: '重置' })

const all = ref<Part[]>(catalogData.parts || [])
const loading = ref(false)
const fail = ref('')

// URL 状态在 onMounted 里读：SSR 与首帧客户端渲染必须一致，
// 否则 GitHub Pages 对每个查询串都吐同一份 HTML 时会 hydration mismatch。
const q = ref('')
//: 精选：白名单来自 public/catalog.json 的 featured.ids（构建时读 data/featured.json）
const featuredIds = ref<Set<string>>(new Set(catalogData.featured?.ids || []))
const featuredOnly = ref(
  typeof localStorage !== 'undefined' && localStorage.getItem('rs.featuredOnly') === '0'
    ? false
    : true,   // 默认开启
)
const hasCuration = computed(() => featuredIds.value.size > 0)
/** 精选清单等于全库时，开关是死控件；直接藏起来，别给一个没用的按钮。 */
const hasRealCuration = computed(() =>
  featuredIds.value.size > 0 && featuredIds.value.size < all.value.length)
const cat = ref('actuator')
const vendor = ref('')
/** 子类（品类内细分，例如连接器的「线对板」、传感器的「ToF」）。
 *  之前只有 sensor 有子类筛选，其余品类只能按厂商筛 —— 型号一多就没法收窄。 */
const subFilter = ref('')
const sort = ref<string>('tau_peak_Nm')
const order = ref<'desc' | 'asc'>('desc')
/** 品类是否被「显式选中」过（点卡片或 URL 带 category）。
#  没选中过时，搜索跨全库——否则 `?q=XT30` 会被默认品类挡成 0 结果。 */
const catPinned = ref(false)
const picked = ref<Part[]>([])
const detail = ref<Part | null>(null)

/** 一页 24 件：326 件一次渲染在低端手机上要卡 1–2 秒，也让人找不到当前位置。 */
const PAGE_SIZE = 24
const page = ref(1)

/* ── 「全部参数」弹窗的键盘契约 ────────────────────────────────────────
   之前只有 role="dialog" aria-modal="true" 这层声明，行为一条都没有：
   打开后焦点还留在遮罩后面的「全部参数」按钮上，Tab 会继续走到背景卡片，
   Esc 不关，关掉之后焦点回到文档开头 —— 键盘/读屏用户进了弹窗就出不来。
   现在：打开即把焦点移到「关闭」上，Tab / Shift+Tab 在面板内循环，
   Esc 关闭，关闭后焦点回到打开它的那个按钮。 */
const panelRef = ref<HTMLElement | null>(null)
const closeBtnRef = ref<HTMLButtonElement | null>(null)
let lastTrigger: HTMLElement | null = null

function openDetail(p: Part, ev?: Event) {
  const t = (ev?.currentTarget as HTMLElement) || (document.activeElement as HTMLElement)
  if (t && typeof t.focus === 'function') lastTrigger = t
  detail.value = p
}

function closeDetail() {
  detail.value = null
}

watch(detail, async (v) => {
  if (typeof document === 'undefined') return
  if (v) {
    await nextTick()
    closeBtnRef.value?.focus()
  } else if (lastTrigger) {
    const back = lastTrigger
    lastTrigger = null
    back.focus()
  }
})

function onPanelKeydown(e: KeyboardEvent) {
  if (e.key === 'Escape') {
    e.preventDefault()
    closeDetail()
    return
  }
  if (e.key !== 'Tab') return
  const panel = panelRef.value
  if (!panel) return
  const focusables = [...panel.querySelectorAll<HTMLElement>(
    'a[href], button:not([disabled]), [tabindex]:not([tabindex="-1"])',
  )].filter(el => el.offsetParent !== null)
  if (!focusables.length) return
  const first = focusables[0]
  const last = focusables[focusables.length - 1]
  const active = document.activeElement as HTMLElement | null
  const inside = !!active && panel.contains(active)
  if (e.shiftKey && (!inside || active === first)) {
    e.preventDefault()
    last.focus()
  } else if (!e.shiftKey && (!inside || active === last)) {
    e.preventDefault()
    first.focus()
  }
}

//: 品类表来自 catalog.json（构建时由 data/taxonomy.json 生成）——
//: 这里只留一份「加载失败时的兜底」，不再硬编码全量。
interface Cat {
  v: string
  t: string
  subtypes?: Record<string, string>
  keys: { k: string; label: string; unit?: string }[]
  sorts: { k: string; label: string }[]
}

const FALLBACK_CATS = [
  { v: 'actuator', t: '关节电机' },
  { v: 'controller_high', t: '上位机' },
  { v: 'controller_low', t: '下位机' },
  { v: 'module', t: '其余模块' },
  { v: 'chip', t: '硬件芯片' },
  { v: 'open_hw', t: '开源硬件' },
]
const CATS = ref<Cat[]>((catalogData.categories?.length ? catalogData.categories : FALLBACK_CATS).map((c: any) => ({
  v: c.id || c.v, t: c.name || c.t, subtypes: c.subtypes || {}, keys: c.keys || [], sorts: c.sorts || [],
})))

//: 排序项按品类来（data/taxonomy.json 的 sorts）。
//: 「按峰值扭矩」对芯片毫无意义 —— 每类该有自己的默认排序。
const FALLBACK_SORTS = [{ k: 'price', label: '价格' }, { k: 'rating', label: '评分' }]

// 数据在构建期由 pipeline 写进 public/catalog.json；这里静态导入，
// 让 VitePress SSG 直接把首屏卡片烘进 HTML——群链接首访客不再看空白页。
onMounted(() => {
  const params = new URLSearchParams(window.location.search)
  const urlCat = params.get('category')?.trim() || ''
  if (urlCat) {
    cat.value = urlCat
    catPinned.value = true
  }
  q.value = params.get('q') || ''
  vendor.value = params.get('vendor') || ''
  subFilter.value = params.get('subtype') || ''
  sort.value = params.get('sort') || 'tau_peak_Nm'
  order.value = (params.get('order') as 'desc' | 'asc') || 'desc'

  if (!CATS.value.some(c => c.v === cat.value)) cat.value = CATS.value[0].v
  if (!sortOpts.value.some(o => o.k === sort.value)) sort.value = defaultSortFor(cat.value)
  syncFiltersUrl()
})

/** 精选开关：白名单没真正收窄全库时，按钮不出现也不生效。 */
function toggleFeatured() {
  if (!hasRealCuration.value) return
  featuredOnly.value = !featuredOnly.value
  try {
    localStorage.setItem('rs.featuredOnly', featuredOnly.value ? '1' : '0')
  } catch { /* 隐私模式下忽略 */ }
}

function setCat(v: string) {
  cat.value = v
  catPinned.value = true
  vendor.value = ''
  subFilter.value = ''
  // 搜索词保留：点品类是「在结果里收窄」，不是重新开始；
  // 要全部清掉用「重置」。
  sort.value = defaultSortFor(v)
  page.value = 1
  syncCategoryUrl()
}

function defaultSortFor(v: string) {
  const m = CATS.value.find(c => c.v === v)
  return m?.sorts?.[0]?.k || 'price'
}

/** 清掉全部筛选，回到默认品类 + 默认排序。空态和工具条都用它。 */
function resetFilters() {
  cat.value = CATS.value[0]?.v || 'actuator'
  catPinned.value = false
  q.value = ''
  vendor.value = ''
  subFilter.value = ''
  sort.value = defaultSortFor(cat.value)
  order.value = 'desc'
  page.value = 1
  syncFiltersUrl()
}

const filtersActive = computed(() =>
  !!q.value.trim() || !!vendor.value || !!subFilter.value || catPinned.value
  || sort.value !== defaultSortFor(cat.value) || order.value !== 'desc')

/** 筛选状态进 URL：刷新、收藏、贴群都能回到同一视图。
 *  只写非默认值，避免分享出一串 `?q=&vendor=&sort=` 噪声。 */
function syncFiltersUrl() {
  if (typeof window === 'undefined') return
  const url = new URL(window.location.href)
  const defaultCat = CATS.value[0]?.v || 'actuator'
  const set = (k: string, v: string, isDefault = false) => {
    if (v && !isDefault) url.searchParams.set(k, v)
    else url.searchParams.delete(k)
  }
  set('category', cat.value, !catPinned.value && cat.value === defaultCat)
  set('q', q.value.trim())
  set('vendor', vendor.value)
  set('subtype', subFilter.value)
  set('sort', sort.value, sort.value === defaultSortFor(cat.value))
  set('order', order.value, order.value === 'desc')
  history.replaceState(history.state, '', url)
}

const syncCategoryUrl = syncFiltersUrl

// 任一变就同步 + 回到第一页：换筛选后还停在第 7 页，看到的是空列表。
watch([cat, q, vendor, subFilter, sort, order, featuredOnly], () => {
  page.value = 1
  syncFiltersUrl()
})

const catCount = (v: string) => all.value.filter(p => p.category === v).length

/** 空列表提示分两种：真没收录，还是收了但筛没了。混成一句会让人以为数据丢了。 */
const emptyText = computed(() => {
  if (subFilter.value
      && !all.value.some(p => p.category === cat.value && p.subtype === subFilter.value)) {
    return '这个子类还没有收录 —— 没有可信来源，宁缺不编'
  }
  if (!catCount(cat.value)) return '这一类还没有收录 —— 没有可信来源，宁缺不编'
  const term = q.value.trim()
  return term ? `没有匹配「${term}」的部件` : '没有符合条件的部件'
})

/** 当前品类的元数据：卡片显示哪些参数、能按什么排序，都来自这里。 */
function metaOf(id: string): Cat | undefined {
  return CATS.value.find(c => c.v === id)
}
const meta = computed(() => metaOf(cat.value))

/** 抽屉里给非核心键补中文标签；核心键的标签来自 taxonomy 的 keys。 */
const EXTRA_LABELS: Record<string, string> = {
  current_basis: '电流口径', contact_resistance_mohm: '接触电阻 (mΩ)',
  insulation_resistance_mohm: '绝缘电阻 (MΩ)', withstand_voltage_V: '耐电压 (V)',
  mating_cycles: '插拔寿命 (次)', temp_range_C: '温度范围', wire_awg: '适用线规',
  lock_type: '锁扣', power_positions: '电源位数', signal_positions: '信号位数',
  signal_current_rated_A: '信号针电流 (A)', contact_layout: '触点布局',
  instantaneous_current_A: '瞬时电流 (A)', impedance_ohm: '阻抗 (Ω)',
  freq_max_ghz: '最高频率 (GHz)', length_m: '长度 (m)', awg: '线规',
  positions_options: '可选位数',
}
function labelFor(k: string, category = cat.value): string {
  return metaOf(category)?.keys.find(x => x.k === k)?.label || EXTRA_LABELS[k] || k
}
const sortOpts = computed(() => {
  const opts = meta.value?.sorts?.length ? meta.value.sorts : FALLBACK_SORTS
  // 全库 0 条评分时，「按评分」排序是死选项；藏起来比给了不排好。
  const anyRating = all.value.some(p => (p.rating?.count || 0) > 0)
  return anyRating ? opts : opts.filter(o => o.k !== 'rating')
})
const vendors = computed(() =>
  [...new Set(all.value.filter(p => p.category === cat.value).map(p => p.vendor))].sort())

/** 品类内的子类筛选项：**所有品类**通用，不再只给传感器开。
 *  0 计数的子类照样列出（虚线），让「以后该收什么」显式可见，而不是假装完整。
 *  做法来自 ccc 分支（Dichen33）。 */
const subtypeOptions = computed(() => {
  const items = Object.entries(meta.value?.subtypes || {}).map(([v, label]) => ({
    v, label: String(label),
    count: all.value.filter(p => p.category === cat.value && p.subtype === v).length,
  }))
  const filled = items.filter(x => x.count).sort((a, b) => b.count - a.count)
  return [...filled, ...items.filter(x => !x.count)]
})

/** 排序取值器：specs 里的键、或内置的 price / rating。
 *  空值统一返回 null，排序时沉底（缺失就是缺失，不该混进比较）。 */
function sortValue(p: Part, k: string): any {
  // 价格排序用公开标价：优惠价要资格，不是人人都能拿到，混进排序会失真。
  if (k === 'price') return p.price ?? p.offer?.price ?? null
  if (k === 'rating') return p.rating?.avg ?? null
  const v = (p as any).specs?.[k]
  return v === undefined || v === '' ? null : v
}

function specText(p: Part): string {
  const specs = p.specs || {}
  return Object.keys(specs).map(k => {
    const v = specs[k]
    if (v === null || v === undefined) return k
    if (Array.isArray(v)) return `${k} ${v.join(' ')}`
    if (typeof v === 'object') return `${k} ${Object.values(v).join(' ')}`
    return `${k} ${v}`
  }).join(' ')
}

/** 多词 AND + 规格/备注命中：搜「48V」「IP67」「谐波」都该有结果。 */
function matchesQuery(p: Part, q: string): boolean {
  const terms = q.toLowerCase().split(/\s+/).filter(Boolean)
  if (!terms.length) return true
  const hay = `${p.model} ${p.vendor} ${(p as any).vendor_cn || ''} ${p.subtypeLabel} ${(p as any).title || ''} ${p.notes || ''} ${specText(p)}`.toLowerCase()
  return terms.every(t => hay.includes(t))
}

/** 跨库搜索时的相关度：型号完全命中 > 前缀 > 包含 > 厂商命中。
 *  全库搜索用的是当前品类（默认关节电机）的参数排序，连接器/芯片的扭矩全是空值，
 *  不按相关度先排，搜 XT30 会先看到一堆扭矩为空的卡片。 */
function relevance(p: Part, q: string): number {
  const terms = q.toLowerCase().split(/\s+/).filter(Boolean)
  const model = p.model.toLowerCase()
  const vendor = p.vendor.toLowerCase()
  let score = 0
  for (const t of terms) {
    if (model === t) score += 100
    else if (model.startsWith(t)) score += 60
    else if (model.includes(t)) score += 40
    else if (vendor.includes(t)) score += 20
    else score += 5
  }
  return score
}

/** 搜索跨全库：没点过品类时，搜型号不被默认品类挡住。 */
const crossSearch = computed(() => !!q.value.trim() && !catPinned.value)

const rows = computed(() => {
  const key = (p: Part) => sortValue(p, sort.value)
  // 精选门：开关打开且白名单非空时才过滤
  const gate = featuredOnly.value && hasCuration.value
  let out = all.value.filter(
    p => (p.category === cat.value || crossSearch.value)
      && (!gate || featuredIds.value.has(p.id))
      && (!vendor.value || p.vendor === vendor.value)
      && (!subFilter.value || p.subtype === subFilter.value)
      && (!q.value || matchesQuery(p, q.value)),
  )
  out = [...out].sort((a, b) => {
    // 全库搜索：先看型号相关度，再按用户选的参数排。
    if (crossSearch.value) {
      const ra = relevance(a, q.value), rb = relevance(b, q.value)
      if (ra !== rb) return rb - ra
    }
    const va = key(a), vb = key(b)
    // null 永远排最后：缺失就是缺失，不该混进排序
    if (va == null && vb == null) return 0
    if (va == null) return 1
    if (vb == null) return -1
    const cmp = typeof va === 'number' ? va - vb : String(va).localeCompare(String(vb), 'zh')
    return order.value === 'desc' ? -cmp : cmp
  })
  return out
})

const pageCount = computed(() => Math.max(1, Math.ceil(rows.value.length / PAGE_SIZE)))
const pageRows = computed(() =>
  rows.value.slice((page.value - 1) * PAGE_SIZE, page.value * PAGE_SIZE))
watch([rows, pageCount], () => {
  if (page.value > pageCount.value) page.value = pageCount.value
})

const listRef = ref<HTMLElement | null>(null)
async function goPage(n: number) {
  page.value = Math.min(Math.max(1, n), pageCount.value)
  await nextTick()
  listRef.value?.scrollIntoView({ block: 'start', behavior: 'smooth' })
}

function num(v: any, d = 3): string {
  if (v == null || v === '') return '—'
  if (typeof v === 'boolean') return v ? '支持' : '否'
  // 嵌套 specs（params / price_tiers）直接 String() 会变成 [object Object]。
  if (Array.isArray(v)) return v.map(x => num(x, d)).join(' / ')
  if (typeof v === 'object') {
    return Object.entries(v).map(([k, x]) => `${k} ${num(x, d)}`).join('；')
  }
  const n = Number(v)
  if (!isFinite(n)) return String(v)
  const a = Math.abs(n)
  // 大整数加千分位（700000 -> 700,000），与详情页 python 端 num() 保持一致；
  // 科学计数法只留给真正的小数。
  if (a >= 1000 && Number.isInteger(n)) return n.toLocaleString('en-US')
  if (a && a < 0.001) return n.toExponential(1)
  return String(Number(n.toFixed(d)))
}

/**
 * 价格格式：按量级选小数位。
 * 芯片动辄 ¥0.1548，四舍五入成整数会变成 ¥0 —— 那是最糟的失真。
 */
function money(v: number | null): string | null {
  if (v == null) return null
  const a = Math.abs(v)
  let digits = 0
  if (a < 1) digits = 4
  else if (a < 10) digits = 2
  else if (a < 100) digits = 1
  const s = v.toFixed(digits).replace(/\.0+$/, '').replace(/(\.\d*[1-9])0+$/, '$1')
  return `¥${Number(s).toLocaleString('en-US', { maximumFractionDigits: digits })}`
}

/** 卡片上的关键参数：按**该卡片自己的品类**取，不是按当前筛选品类。
 *  全库搜索时结果是混合品类，用关节电机的标签套在连接器上会指鹿为马。 */
function chips(p: Part): { k: string; v: string }[] {
  const m = metaOf(p.category)
  const out: { k: string; v: string }[] = []
  for (const key of m?.keys || []) {
    const raw = sortValue(p, key.k)
    if (raw === null || raw === 0 || raw === '') continue
    if (typeof raw === 'boolean') {
      if (raw) out.push({ k: key.label, v: '支持' })
      continue
    }
    const val = typeof raw === 'number' ? num(raw) : String(raw)
    out.push({ k: key.label, v: `${val}${key.unit || ''}` })
    if (out.length >= 6) break
  }
  return out
}

function toggleCompare(p: Part) {
  const i = picked.value.findIndex(x => x.id === p.id)
  if (i >= 0) picked.value.splice(i, 1)
  else if (picked.value.length < 3) picked.value.push(p)
}
const isPicked = (p: Part) => picked.value.some(x => x.id === p.id)

/** 对比表的行跟着所选项的品类走。
 *  之前写死峰值/额定/减速比/惯量 —— 拿两个连接器对比时整张表全是「—」。 */
function specCell(p: Part, k: string, unit = ''): string {
  const v = sortValue(p, k)
  if (v == null || v === '') return '—'
  if (typeof v === 'boolean') return v ? '支持' : '否'
  return `${num(v)}${typeof v === 'number' ? unit : ''}`
}
const compareFields = computed(() => {
  const cats = [...new Set(picked.value.map(p => p.category))]
  const keys: { k: string; label: string; unit?: string }[] = []
  const seen = new Set<string>()
  for (const c of cats) {
    for (const key of metaOf(c)?.keys || []) {
      if (seen.has(key.k)) continue
      seen.add(key.k)
      keys.push(key)
    }
  }
  return [
    ...keys.slice(0, 8).map(key => ({
      t: key.label,
      f: (p: Part) => specCell(p, key.k, key.unit),
    })),
    { t: '价格', f: (p: Part) => money(p.price) ?? '询价' },
    { t: '评分', f: (p: Part) => (p.rating.avg == null ? '暂无' : `${p.rating.avg} (${p.rating.count})`) },
  ]
})
</script>

<template>
  <div class="pd">
    <header class="ex-head" v-if="!en">
      <div class="ex-kicker">机器人部件</div>
      <h1>选部件，先看参数，再看用过的人怎么说。</h1>
      <p class="ex-lead">
        每个部件一页：左边是<strong>官方参数</strong>（带来来源等级与口径），右边是<strong>真实使用者的评分与评价</strong>（评分入口刚开放，暂无量）。
        有优惠条件、有资料链接、能按任意列排序。
      </p>
      <div class="ex-note">
        <span v-if="hasRealCuration"><b>★ 入库</b> 默认全收录；关掉仍可看全部。</span>
        <b>每一行参数都标了来源等级</b>：A 级逐项对过厂商手册，缺的值写 —，不猜。
      </div>
    </header>

    <p v-if="loading" class="pd-muted">加载部件库…</p>
    <p v-else-if="fail" class="pd-muted">{{ fail }}</p>

    <template v-else>

      <!-- 工具条 -->
      <div class="pd-row">
        <input v-model="q" class="pd-input" :placeholder="L.search" aria-label="搜索部件"
               type="search" enterkeyhint="search" autocomplete="off" spellcheck="false"
               @keydown.esc="q = ''" />
        <button v-if="hasRealCuration" class="pd-chip pd-featured"
                :class="{ on: featuredOnly }"
                :aria-pressed="featuredOnly"
                title="只看精选（data/featured.json）"
                @click="toggleFeatured()">
          <span class="pd-star">★</span>{{ L.featured }}
          <span class="pd-n">{{ hasCuration ? featuredIds.size : '未筛选' }}</span>
        </button>

        <select v-model="sort" class="pd-sel" aria-label="排序方式">
          <option v-for="s in sortOpts" :key="s.k" :value="s.k">按{{ s.label }}</option>
        </select>
        <button class="pd-btn" :aria-label="order === 'desc' ? '当前降序，切换为升序' : '当前升序，切换为降序'"
                @click="order = order === 'desc' ? 'asc' : 'desc'">
          {{ order === 'desc' ? '↓ 降序' : '↑ 升序' }}
        </button>
        <button v-if="filtersActive" class="pd-link pd-reset" @click="resetFilters()">{{ L.reset }}</button>
        <span class="pd-count" role="status">
          {{ rows.length }} {{ L.count }}<template v-if="crossSearch"> · 全库</template>
        </span>
      </div>
      <p v-if="crossSearch" class="pd-hint">
        正在全库搜索，点上方品类可收窄范围；卡片的参数标签会跟随各自品类。
      </p>

      <!-- 分类 -->
      <div class="pd-row">
        <button v-for="c in CATS" :key="c.v"
                :class="['pd-chip', cat === c.v && !crossSearch ? 'on' : '', catCount(c.v) ? '' : 'empty']"
                :aria-pressed="cat === c.v && !crossSearch"
                :title="catCount(c.v) ? `${catCount(c.v)} 件` : '还没有收录（没有可信来源，不编数据）'"
                @click="setCat(c.v)">
          {{ c.t }}<span class="pd-n">{{ catCount(c.v) || '—' }}</span>
        </button>
      </div>

      <!-- 子类：所有品类通用；0 计数的子类也留着入口 -->
      <div v-if="subtypeOptions.length" class="pd-row">
        <span class="pd-lab">{{ cat === 'sensor' ? L.type : L.sub }}</span>
        <button v-for="t in subtypeOptions" :key="t.v"
                :class="['pd-chip', 'sm', subFilter === t.v ? 'on' : '', t.count ? '' : 'empty']"
                :aria-pressed="subFilter === t.v"
                :title="t.count ? `${t.count} 件` : '还没有收录（没有可信来源，不编数据）'"
                @click="subFilter = subFilter === t.v ? '' : t.v">
          {{ t.label }}<span class="pd-n">{{ t.count || '—' }}</span>
        </button>
      </div>

      <!-- 厂商：传感器跨品牌横向比才有意义，仍按厂商列；其余品类同理 -->
      <div v-if="cat !== 'sensor' && vendors.length" class="pd-row">
        <span class="pd-lab">{{ L.vendor }}</span>
        <button v-for="v in vendors" :key="v"
                :class="['pd-chip', 'sm', vendor === v ? 'on' : '']"
                :aria-pressed="vendor === v"
                @click="vendor = vendor === v ? '' : v">{{ v }}</button>
      </div>

      <!-- 对比 -->
      <div v-if="picked.length" class="pd-compare">
        <div class="pd-compare-head">
          对比 {{ picked.length }} / 3
          <button class="pd-link" @click="picked = []">清空</button>
        </div>
        <table>
          <tr><th></th><th v-for="p in picked" :key="p.id">{{ p.model }}</th></tr>
          <tr v-for="f in compareFields" :key="f.t">
            <td class="pd-k">{{ f.t }}</td>
            <td v-for="p in picked" :key="p.id">{{ f.f(p) }}</td>
          </tr>
        </table>
      </div>

      <!-- 卡片：不再给整个网格加 aria-live —— 每次输入都重排 311 张卡，
           读屏会把新子树整个念一遍；改成只播报上面的计数（role="status"）。 -->
      <div ref="listRef" class="pd-grid">
        <article v-for="p in pageRows" :key="p.id" class="card">
          <a class="card-img" :href="withBase('/parts/' + p.category + '/' + p.slug)">
            <img v-if="p.image" :src="withBase(p.image)" :alt="p.model" loading="lazy" />
            <!-- 没图就如实说没图。错图（整机宣传图）比没图更糟，所以不做抽象方块充数 -->
            <span v-else class="ph" :aria-label="`暂无${metaOf(p.category)?.t || '部件'}产品图`">
              <svg viewBox="0 0 24 24" width="18" height="18" aria-hidden="true"
                   fill="none" stroke="currentColor" stroke-width="1.6"
                   stroke-linecap="round" stroke-linejoin="round">
                <template v-if="p.category === 'camera'">
                  <path d="M3 7h4l2-3h6l2 3h4v12H3z" /><circle cx="12" cy="13" r="3.4" />
                </template>
                <template v-else-if="p.category === 'lidar'">
                  <circle cx="12" cy="12" r="2" />
                  <path d="M12 4a8 8 0 0 1 8 8M12 20a8 8 0 0 1-8-8" />
                  <path d="M12 7.5a4.5 4.5 0 0 1 4.5 4.5" />
                </template>
                <template v-else-if="p.category === 'controller_high' || p.category === 'controller_low'">
                  <rect x="3" y="5" width="18" height="14" rx="2" />
                  <path d="M7 9h4M7 13h6M16 9v6" />
                </template>
                <template v-else-if="p.category === 'chip'">
                  <rect x="7" y="7" width="10" height="10" rx="1.5" />
                  <path d="M10 3v4M14 3v4M10 17v4M14 17v4M3 10h4M3 14h4M17 10h4M17 14h4" />
                </template>
                <template v-else-if="p.category === 'connector'">
                  <rect x="3" y="8" width="7" height="8" rx="1" />
                  <path d="M10 10h4M10 14h4M14 8v8" />
                  <rect x="17" y="9.5" width="3" height="5" rx="0.6" />
                </template>
                <template v-else-if="p.category === 'actuator'">
                  <circle cx="12" cy="12" r="6.5" /><circle cx="12" cy="12" r="2" />
                </template>
                <template v-else>
                  <path d="M3 7h4l2-3h6l2 3h4v12H3z" /><circle cx="12" cy="13" r="3.4" />
                </template>
              </svg>
              <em>{{ L.none }}</em>
            </span>
            <span :class="['card-tier', p.tier === 'A' ? 'a' : '']">{{ p.tier }}{{ p.verified && p.tier === 'A' ? ' ✓' : '' }}</span>
            <span v-if="p.offer?.price != null" class="card-promo">优惠</span>
          </a>

          <div class="card-body">
            <a class="card-model" :href="withBase('/parts/' + p.category + '/' + p.slug)">{{ p.model }}</a>
            <div class="card-vendor">{{ p.vendor }}<span v-if="p.subtypeLabel"> · {{ p.subtypeLabel }}</span></div>

            <div class="card-chips">
              <span v-for="c in chips(p)" :key="c.k"><b>{{ c.k }}</b>{{ c.v }}</span>
            </div>

            <div class="card-foot">
              <div class="card-price">
                <!-- 原价与优惠价并列，不划掉原价：优惠要资格，不是人人都能用 -->
                <span class="list">{{ money(p.price) ?? '询价' }}</span>
                <template v-if="p.offer?.price != null">
                  <span class="promo">{{ money(p.offer.price) }}</span>
                  <span v-if="p.offer?.condition" class="hint" :title="p.offer.condition">需资格</span>
                </template>
              </div>
              <div class="card-rate">
                <template v-if="p.rating.avg != null">
                  <span class="stars" aria-hidden="true">★</span>{{ p.rating.avg.toFixed(1) }}
                  <span class="cnt">({{ p.rating.count }})</span>
                </template>
                <span v-else class="cnt">暂无评分</span>
              </div>
            </div>

            <div class="card-acts">
              <button class="pd-link" :aria-pressed="isPicked(p)"
                      @click="toggleCompare(p)">{{ isPicked(p) ? '取消对比' : '对比' }}</button>
              <button class="pd-link" @click="openDetail(p, $event)">{{ L.all }}</button>
            </div>
          </div>
        </article>
      </div>

      <!-- 分页：每页 24 件。筛选变化自动回第一页，对比选择跨页保留。 -->
      <nav v-if="pageCount > 1" class="pd-pager" aria-label="分页">
        <button class="pd-btn" :disabled="page <= 1" @click="goPage(page - 1)">上一页</button>
        <span class="pd-page" role="status">第 {{ page }} / {{ pageCount }} 页</span>
        <button class="pd-btn" :disabled="page >= pageCount" @click="goPage(page + 1)">下一页</button>
      </nav>

      <p v-if="!rows.length" class="pd-muted pd-empty" role="status">
        {{ emptyText }}
        <button v-if="filtersActive" class="pd-link" @click="resetFilters()">重置筛选</button>
      </p>

      <!-- 全部参数 -->
      <div v-if="detail" class="pd-modal" role="dialog" aria-modal="true"
           aria-labelledby="pd-detail-title"
           @keydown="onPanelKeydown" @click.self="closeDetail">
        <div ref="panelRef" class="pd-panel" tabindex="-1">
          <div class="pd-panel-head">
            <b id="pd-detail-title">{{ detail.model }}</b>
            <span class="pd-muted">{{ detail.vendor }}</span>
            <button ref="closeBtnRef" class="pd-link" aria-label="关闭" @click="closeDetail">关闭</button>
          </div>
          <table class="pd-specs">
            <tr v-for="(v, k) in detail.specs" :key="k">
              <td class="pd-k">{{ labelFor(k, detail.category) }}</td>
              <td>{{ num(v) }}</td>
            </tr>
          </table>
          <p v-if="detail.offer" class="pd-offer">
            <b>{{ detail.offer.title }}</b> —— {{ detail.offer.condition }}
            <span v-if="detail.offer.expires">（至 {{ detail.offer.expires }}）</span>
          </p>
          <a class="pd-link" :href="withBase('/parts/' + detail.category + '/' + detail.slug)">
            打开部件页（来源 / 选型指标 / 使用建议 / 评分）→
          </a>
        </div>
      </div>
    </template>
  </div>
</template>

<style scoped>
.pd { margin-top: 0.4rem; }
.pd-muted { color: var(--vp-c-text-3); font-size: 0.85rem; }
.pd-row { display: flex; flex-wrap: wrap; align-items: center; gap: 0.4rem; margin-bottom: 0.6rem; }
.pd-input, .pd-sel {
  font-size: 0.82rem; padding: 0.36rem 0.7rem; border-radius: 999px;
  border: 1px solid var(--vp-c-divider); background: var(--vp-c-bg);
  color: var(--vp-c-text-1);
}
.pd-input { width: 200px; }
.pd-input:focus, .pd-sel:focus { border-color: var(--vp-c-brand-1); }
.pd-input:focus-visible, .pd-sel:focus-visible {
  outline: 2px solid var(--vp-c-brand-1); outline-offset: 2px;
}
.pd-btn {
  font-size: 0.8rem; padding: 0.36rem 0.75rem; border-radius: 999px; cursor: pointer;
  border: 1px solid var(--vp-c-divider); background: var(--vp-c-bg); color: var(--vp-c-text-2);
}
.pd-featrow { margin-bottom: 0.15rem; }
.pd-featured { border-color: var(--vp-c-brand-1); color: var(--vp-c-brand-1); font-weight: 700; }
.pd-featured.on { background: var(--vp-c-brand-1); border-color: var(--vp-c-brand-1); color: var(--rw-on-brand); }
.pd-featured.off { opacity: 0.55; cursor: not-allowed; }
.pd-star { margin-right: 0.25rem; font-size: 0.7rem; }
.pd-chip {
  font-size: 0.8rem; padding: 0.3rem 0.7rem; border-radius: 999px; cursor: pointer;
  border: 1px solid var(--vp-c-divider); background: var(--vp-c-bg); color: var(--vp-c-text-2);
}
.pd-chip.sm { font-size: 0.75rem; padding: 0.22rem 0.55rem; }
.pd-chip.on {
  border-color: var(--vp-c-brand-1); background: var(--vp-c-brand-1); color: var(--rw-on-brand); font-weight: 600;
}
.pd-chip.empty { border-style: dashed; color: var(--vp-c-text-3); opacity: 1; }
.pd-n { margin-left: 0.35rem; opacity: 0.6; font-variant-numeric: tabular-nums; }
.pd-sep { width: 1px; height: 18px; background: var(--vp-c-divider); margin: 0 0.25rem; }
.pd-lab {
  font-size: 0.72rem; color: var(--vp-c-text-3); letter-spacing: 0.04em;
  margin: 0 0.1rem 0 0.25rem;
}
.pd-count { margin-left: auto; font-size: 0.78rem; color: var(--vp-c-text-3); }
.pd-hint { margin: -0.2rem 0 0.55rem; font-size: 0.74rem; color: var(--vp-c-text-3); }
.pd-reset { flex: 0 0 auto; padding: 0.36rem 0.4rem; }
.pd-pager {
  display: flex; align-items: center; justify-content: center; gap: 0.6rem;
  margin: 1.1rem 0 0.4rem;
}
.pd-page { font-size: 0.78rem; color: var(--vp-c-text-3); font-variant-numeric: tabular-nums; }
.pd-pager .pd-btn { min-height: 34px; padding: 0.35rem 0.9rem; }
.pd-pager .pd-btn:disabled { opacity: 0.45; cursor: default; }
.pd-empty { padding: 2rem 0; text-align: center; }
.pd-empty .pd-link { margin-left: 0.5rem; }

/* 卡片网格：固定 4 列。auto-fill 在宽屏会排到 6 列，卡片被压得太窄 ——
   参数两列排不下、型号名折行、价格和「优惠需资格」挤成两行。 */
.pd-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 0.85rem;
  /* 翻页后 scrollIntoView 别钻到固定导航下面 */
  scroll-margin-top: 84px;
}
@media (max-width: 1180px) { .pd-grid { grid-template-columns: repeat(3, minmax(0, 1fr)); } }
@media (max-width: 860px)  { .pd-grid { grid-template-columns: repeat(2, minmax(0, 1fr)); } }
@media (max-width: 540px)  { .pd-grid { grid-template-columns: 1fr; } }
.card {
  display: flex; flex-direction: column; overflow: hidden;
  border: 1px solid var(--vp-c-divider); border-radius: 10px;
  background: var(--vp-c-bg);
  transition: transform 0.18s, box-shadow 0.18s, border-color 0.18s;
}
.card:hover {
  transform: translateY(-2px); border-color: var(--vp-c-brand-1);
  box-shadow: 0 10px 24px rgba(0, 0, 0, 0.08);
}
.card-img {
  position: relative; display: flex; align-items: center; justify-content: center;
  height: 112px; background: var(--vp-c-bg-alt);
  border-bottom: 1px solid var(--vp-c-divider);
  /* 托板高度固定，图片/SVG 都不能撑出边界 —— 否则会压到下面的型号名上 */
  overflow: hidden;
}
.card-img img {
  max-height: 96px; max-width: 86%; object-fit: contain; mix-blend-mode: multiply;
}
html.dark .card-img img { mix-blend-mode: normal; background: #fff; border-radius: 4px; padding: 2px; }
/* 占位图按**高度**约束（不是宽度）：SVG 有 viewBox，给定高度后宽度按比例走，
   在 112px 高的托板里永远不会顶出来。按宽度给百分比会算出 136px 高再溢出。 */
.card-img svg { height: 78px; width: auto; max-width: 88%; display: block; }

/* 缺图的占位：图标 + 一句说明，克制到不抢注意力，但比抽象方块能读懂 */
.ph {
  display: flex; flex-direction: column; align-items: center; gap: 3px;
  color: var(--vp-c-text-3);
}
.ph svg { height: 18px; width: auto; max-width: none; opacity: 0.7; }
.ph em { font-size: 0.66rem; font-style: normal; letter-spacing: 0.02em; }
.card-tier {
  position: absolute; top: 6px; right: 6px; font-size: 0.62rem; font-weight: 700;
  padding: 1px 5px; border-radius: 999px;
  background: var(--vp-c-default-soft); color: var(--vp-c-text-2);
}
.card-tier.a { background: var(--vp-c-brand-soft); color: var(--rw-brand-ink); }
.card-promo {
  position: absolute; top: 6px; left: 6px; font-size: 0.62rem; font-weight: 700;
  padding: 1px 5px; border-radius: 999px; background: var(--rw-accent-1); color: var(--rw-on-accent);
}

.card-body { padding: 0.55rem 0.65rem 0.6rem; display: flex; flex-direction: column; gap: 0.28rem; }
.card-model {
  font-size: 0.88rem; font-weight: 700; color: var(--vp-c-text-1); text-decoration: none;
  line-height: 1.3;
}
.card-model:hover { color: var(--vp-c-brand-1); }
.card-vendor { font-size: 0.71rem; color: var(--vp-c-text-3); }

.card-chips { display: grid; grid-template-columns: 1fr 1fr; gap: 2px 6px; margin-top: 0.15rem; }
.card-chips span {
  font-size: 0.68rem; color: var(--vp-c-text-2);
  font-variant-numeric: tabular-nums; white-space: nowrap;
  overflow: hidden; text-overflow: ellipsis;
}
.card-chips b { color: var(--vp-c-text-3); font-weight: 500; margin-right: 3px; }

.card-foot {
  display: flex; align-items: baseline; justify-content: space-between;
  margin-top: 0.4rem; padding-top: 0.4rem; border-top: 1px solid var(--vp-c-divider);
}
.card-price { display: flex; align-items: baseline; gap: 0.35rem; flex-wrap: wrap;
  font-variant-numeric: tabular-nums; }
/* 原价：中性灰，尺寸略小。不做删除线 —— 优惠要资格，原价仍是真实价格 */
.card-price .list { font-size: 0.8rem; color: var(--vp-c-text-2); }
/* 优惠价：琥珀色，最醒目 */
.card-price .promo { font-size: 0.9rem; font-weight: 700; color: var(--rw-accent-1); }
html.dark .card-price .promo { color: var(--rw-accent-1); }
.card-price .hint {
  font-size: 0.62rem; color: var(--rw-accent-1); border: 1px solid currentColor;
  border-radius: 999px; padding: 0 4px; opacity: 0.85;
}
html.dark .card-price .hint { color: var(--rw-accent-1); }
.card-rate { font-size: 0.76rem; color: var(--vp-c-text-1); font-variant-numeric: tabular-nums; }
.card-rate .stars { color: var(--rw-accent-2); margin-right: 2px; }
html.dark .card-rate .stars { color: var(--rw-accent-1); }
.card-rate .cnt { font-size: 0.68rem; color: var(--vp-c-text-3); }

.card-acts { display: flex; gap: 0.7rem; margin-top: 0.15rem; }
/* 「对比 / 全部参数」原来 font-size 11.5px、padding 0 —— 实测 23×24px，
   手指点不准（WCAG 2.5.8 最小 24×24，移动端最好 ≥ 32）。给这两个按钮
   撑出可点区域，文案与位置不动。 */
.card-acts .pd-link {
  display: inline-flex; align-items: center;
  min-height: 28px; padding: 0.15rem 0.4rem; border-radius: 6px;
}
@media (pointer: coarse), (max-width: 640px) {
  .card-acts { gap: 0.4rem; }
  .card-acts .pd-link { min-height: 34px; padding: 0.3rem 0.55rem; font-size: 0.78rem; }
}
.pd-link {
  font-size: 0.72rem; border: none; background: none; padding: 0; cursor: pointer;
  color: var(--vp-c-brand-1); text-decoration: none;
}
.pd-link:hover { text-decoration: underline; }

.pd-compare {
  border: 1px solid var(--vp-c-brand-1); border-radius: 10px; padding: 0.6rem 0.75rem;
  margin-bottom: 0.75rem; background: var(--vp-c-brand-soft); overflow-x: auto;
}
.pd-compare-head {
  display: flex; justify-content: space-between; font-size: 0.8rem; font-weight: 600;
  color: var(--vp-c-brand-1); margin-bottom: 0.35rem;
}
.pd-compare table { border-collapse: collapse; font-size: 0.76rem; width: 100%; }
.pd-compare th, .pd-compare td {
  border: 1px solid var(--vp-c-divider); padding: 3px 8px; text-align: left;
  white-space: nowrap; font-variant-numeric: tabular-nums;
}
.pd-compare th { background: var(--vp-c-bg); }
.pd-k { color: var(--vp-c-text-3); }

.pd-modal {
  position: fixed; inset: 0; background: rgba(0, 0, 0, 0.35); z-index: 60;
  display: flex; align-items: center; justify-content: center; padding: 1rem;
}
.pd-panel {
  background: var(--vp-c-bg); border: 1px solid var(--vp-c-divider); border-radius: 12px;
  padding: 0.95rem 1.05rem; max-width: 560px; width: 100%; max-height: 82vh; overflow: auto;
  box-shadow: 0 18px 44px rgba(0, 0, 0, 0.25);
}
/* 面板只是 tabindex="-1" 的焦点落点，不自带焦点框 */
.pd-panel:focus { outline: none; }
.pd-panel-head { display: flex; align-items: baseline; gap: 0.5rem; margin-bottom: 0.5rem; }
.pd-panel-head b { font-size: 0.95rem; color: var(--vp-c-text-1); }
.pd-panel-head .pd-link { margin-left: auto; }
.pd-specs { border-collapse: collapse; width: 100%; font-size: 0.78rem; }
.pd-specs td { border-bottom: 1px solid var(--vp-c-divider); padding: 3px 6px;
  font-variant-numeric: tabular-nums; }
.pd-offer {
  margin: 0.6rem 0; font-size: 0.76rem; line-height: 1.7;
  color: var(--vp-c-text-2); padding: 0.5rem 0.6rem;
  border-left: 3px solid var(--rw-accent-1); background: var(--vp-c-bg-soft);
}
</style>
