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
      none: 'No photo yet', count: 'items', sort: 'Sort by', vendor: 'Vendor', type: 'Type' }
  : { featured: '入库', search: '搜型号 / 品牌 / 类型', compare: '对比', all: '全部参数',
      none: '暂无产品图', count: '件', sort: '按', vendor: '厂商', type: '类型' })

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
const typeFilter = ref('')
const sort = ref<string>('tau_peak_Nm')
const order = ref<'desc' | 'asc'>('desc')
/** 品类是否被「显式选中」过（点卡片或 URL 带 category）。
#  没选中过时，搜索跨全库——否则 `?q=XT30` 会被默认品类挡成 0 结果。 */
const catPinned = ref(false)
const picked = ref<Part[]>([])
const detail = ref<Part | null>(null)

/** 这些品类按「类型 / 功能」筛选，不按厂商：传感器按测量类型，
 *  模块与开源硬件按功能（CAN / 电源管理 / 分电 / 超级电容 / 扩展板）
 *  —— 同类跨厂商横向比才有意义。 */
const TYPE_FILTER_CATS = new Set(['sensor', 'module', 'open_hw'])
const typeFiltered = computed(() => TYPE_FILTER_CATS.has(cat.value))

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
  vendor.value = typeFiltered.value ? '' : (params.get('vendor') || '')
  typeFilter.value = params.get('subtype') || ''
  sort.value = params.get('sort') || 'tau_peak_Nm'
  order.value = (params.get('order') as 'desc' | 'asc') || 'desc'

  if (!CATS.value.some(c => c.v === cat.value)) cat.value = CATS.value[0].v
  if (!sortOpts.value.some(o => o.k === sort.value)) sort.value = defaultSortFor(cat.value)
  syncFiltersUrl()
})

/** 换品类时重置筛选与排序。
 *  「按峰值扭矩」对芯片/雷达毫无意义 —— 默认排序应该跟着品类走。 */
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
  typeFilter.value = ''
  q.value = ''
  sort.value = defaultSortFor(v)
  syncCategoryUrl()
}

function defaultSortFor(v: string) {
  const m = CATS.value.find(c => c.v === v)
  return m?.sorts?.[0]?.k || 'price'
}

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
  set('subtype', typeFilter.value)
  set('sort', sort.value, sort.value === defaultSortFor(cat.value))
  set('order', order.value, order.value === 'desc')
  history.replaceState(history.state, '', url)
}

const syncCategoryUrl = syncFiltersUrl

// 任一变就同步：比在每个 handler 里各写一遍更难漏。
watch([cat, q, vendor, typeFilter, sort, order], syncFiltersUrl)

const catCount = (v: string) => all.value.filter(p => p.category === v).length

/** 空列表提示分两种：真没收录，还是收了但筛没了。混成一句会让人以为数据丢了。 */
const emptyText = computed(() => {
  const typeEmpty = typeFiltered.value && !!typeFilter.value
    && !all.value.some(p => p.category === cat.value && p.subtype === typeFilter.value)
  return typeEmpty || !catCount(cat.value)
    ? '这一类还没有收录 —— 没有可信来源，宁缺不编'
    : '没有符合条件的部件'
})

/** 当前品类的元数据：卡片显示哪些参数、能按什么排序，都来自这里。 */
const meta = computed(() => CATS.value.find(c => c.v === cat.value))
const catName = computed(() => meta.value?.t || '部件')

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
function labelFor(k: string): string {
  return meta.value?.keys.find(x => x.k === k)?.label || EXTRA_LABELS[k] || k
}
const sortOpts = computed(() => {
  const opts = meta.value?.sorts?.length ? meta.value.sorts : FALLBACK_SORTS
  // 全库 0 条评分时，「按评分」排序是死选项；藏起来比给了不排好。
  const anyRating = all.value.some(p => (p.rating?.count || 0) > 0)
  return anyRating ? opts : opts.filter(o => o.k !== 'rating')
})
const vendors = computed(() =>
  [...new Set(all.value.filter(p => p.category === cat.value).map(p => p.vendor))].sort())

/** 传感器按**类型**、模块按**功能**筛选，不按厂商：同类跨厂商横向比才有意义。
 *  0 计数的类型照样列出（虚线），让「以后该收什么」显式可见，而不是假装完整。
 *  做法来自 ccc 分支（Dichen33）。 */
const typeOptions = computed(() => {
  if (!typeFiltered.value) return []
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
  if (k === 'price') return p.offer?.price ?? p.price ?? null
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

const rows = computed(() => {
  const key = (p: Part) => sortValue(p, sort.value)
  // 精选门：开关打开且白名单非空时才过滤
  const gate = featuredOnly.value && hasCuration.value
  let out = all.value.filter(
    p => (p.category === cat.value || (!!q.value && !catPinned.value))
      && (!gate || featuredIds.value.has(p.id))
      && (!vendor.value || p.vendor === vendor.value)
      && (!typeFilter.value || p.subtype === typeFilter.value)
      && (!q.value || matchesQuery(p, q.value)),
  )
  out = [...out].sort((a, b) => {
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

function num(v: any, d = 3): string {
  if (v == null || v === '') return '—'
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

/** 卡片上的 4 个关键参数 —— 按品类取，不是写死关节电机那四个 */
/** 卡片上的关键参数：完全按品类定义渲染（4–6 个），不再写 if-else 分支。
 *  加品类只需要在 data/taxonomy.json 里写 keys。 */
function chips(p: Part): { k: string; v: string }[] {
  const out: { k: string; v: string }[] = []
  for (const key of meta.value?.keys || []) {
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

const COMPARE_FIELDS: { t: string; f: (p: Part) => string }[] = [
  { t: '峰值扭矩', f: p => num(p.tauPeak) },
  { t: '额定扭矩', f: p => num(p.tauRated) },
  { t: '减速比', f: p => num(p.gear) },
  { t: '质量', f: p => num(p.mass) },
  { t: '转子惯量', f: p => num(p.armature) },
  { t: '空载转速', f: p => num(p.rpm) },
  { t: '价格', f: p => money(p.offer?.price ?? p.price) ?? '询价' },
  { t: '评分', f: p => (p.rating.avg == null ? '暂无' : `${p.rating.avg} (${p.rating.count})`) },
]
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
        <input v-model="q" class="pd-input" :placeholder="L.search" aria-label="搜索部件" />
      <button v-if="hasRealCuration" class="pd-chip pd-featured"
              :class="{ on: featuredOnly }"
              title="只看精选（data/featured.json）"
              @click="toggleFeatured()">
        <span class="pd-star">★</span>{{ L.featured }}
        <span class="pd-n">{{ hasCuration ? featuredIds.size : '未筛选' }}</span>
      </button>

        <select v-model="sort" class="pd-sel" aria-label="排序方式">
          <option v-for="s in sortOpts" :key="s.k" :value="s.k">按{{ s.label }}</option>
        </select>
        <button class="pd-btn" @click="order = order === 'desc' ? 'asc' : 'desc'">
          {{ order === 'desc' ? '↓ 降序' : '↑ 升序' }}
        </button>
        <span class="pd-sep" />
        <span class="pd-lab">{{ typeFiltered ? L.type : L.vendor }}</span>
        <template v-if="typeFiltered">
          <button v-for="t in typeOptions" :key="t.v"
                  :class="['pd-chip', 'sm', typeFilter === t.v ? 'on' : '', t.count ? '' : 'empty']"
                  :title="t.count ? `${t.count} 件` : '还没有收录（没有可信来源，不编数据）'"
                  @click="typeFilter = typeFilter === t.v ? '' : t.v">
            {{ t.label }}<span class="pd-n">{{ t.count || '—' }}</span>
          </button>
        </template>
        <template v-else>
          <button v-for="v in vendors" :key="v"
                  :class="['pd-chip', 'sm', vendor === v ? 'on' : '']"
                  @click="vendor = vendor === v ? '' : v">{{ v }}</button>
        </template>
        <span class="pd-count" role="status">{{ rows.length }} {{ L.count }}</span>
      </div>

      <!-- 分类 -->
      <div class="pd-row">
        <button v-for="c in CATS" :key="c.v"
                :class="['pd-chip', cat === c.v ? 'on' : '', catCount(c.v) ? '' : 'empty']"
                :title="catCount(c.v) ? `${catCount(c.v)} 件` : '还没有收录（没有可信来源，不编数据）'"
                @click="setCat(c.v)">
          {{ c.t }}<span class="pd-n">{{ catCount(c.v) || '—' }}</span>
        </button>
      </div>

      <!-- 对比 -->
      <div v-if="picked.length" class="pd-compare">
        <div class="pd-compare-head">
          对比 {{ picked.length }} / 3
          <button class="pd-link" @click="picked = []">清空</button>
        </div>
        <table>
          <tr><th></th><th v-for="p in picked" :key="p.id">{{ p.model }}</th></tr>
          <tr v-for="f in COMPARE_FIELDS" :key="f.t">
            <td class="pd-k">{{ f.t }}</td>
            <td v-for="p in picked" :key="p.id">{{ f.f(p) }}</td>
          </tr>
        </table>
      </div>

      <!-- 卡片：不再给整个网格加 aria-live —— 每次输入都重排 311 张卡，
           读屏会把新子树整个念一遍；改成只播报上面的计数（role="status"）。 -->
      <div class="pd-grid">
        <article v-for="p in rows" :key="p.id" class="card">
          <a class="card-img" :href="withBase('/parts/' + p.category + '/' + p.slug)">
            <img v-if="p.image" :src="withBase(p.image)" :alt="p.model" loading="lazy" />
            <!-- 没图就如实说没图。错图（整机宣传图）比没图更糟，所以不做抽象方块充数 -->
            <span v-else class="ph" :aria-label="`暂无${catName}产品图`">
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
                <template v-else-if="p.category === 'open_hw'">
                  <rect x="4" y="5" width="16" height="14" rx="2" />
                  <path d="M13 8l-4 5h3l-1 3 4-5h-3z" />
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
              <button class="pd-link" @click="toggleCompare(p)">{{ isPicked(p) ? '取消对比' : '对比' }}</button>
              <button class="pd-link" @click="openDetail(p, $event)">{{ L.all }}</button>
            </div>
          </div>
        </article>
      </div>

      <p v-if="!rows.length" class="pd-muted" role="status" style="padding:2rem 0;text-align:center">
        {{ emptyText }}
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
              <td class="pd-k">{{ labelFor(k) }}</td>
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
.pd-chip.empty { border-style: dashed; color: var(--vp-c-text-3); }
.pd-n { margin-left: 0.35rem; opacity: 0.6; font-variant-numeric: tabular-nums; }
.pd-sep { width: 1px; height: 18px; background: var(--vp-c-divider); margin: 0 0.25rem; }
.pd-lab {
  font-size: 0.72rem; color: var(--vp-c-text-3); letter-spacing: 0.04em;
  margin: 0 0.1rem 0 0.25rem;
}
.pd-count { margin-left: auto; font-size: 0.78rem; color: var(--vp-c-text-3); }

/* 卡片网格：固定 4 列。auto-fill 在宽屏会排到 6 列，卡片被压得太窄 ——
   参数两列排不下、型号名折行、价格和「优惠需资格」挤成两行。 */
.pd-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 0.85rem;
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
