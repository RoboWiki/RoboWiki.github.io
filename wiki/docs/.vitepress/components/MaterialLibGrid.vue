<script setup lang="ts">
/**
 * 材质库列表（统一外壳版）。
 *
 * 材料比物理属性与工艺适配，不比品牌；工艺比能力边界。卡片托板用 CSS
 * 材质色块而不是示意图 —— 没有官方型号图时，假图比没图更糟。
 */
import { computed, onMounted, ref } from 'vue'
import ExplorerShell from './ExplorerShell.vue'
import materialsData from '../../public/materials.json'

interface Sup {
  id: string; name: string; category?: string | null; fine?: string | null
  price_level?: string | null; role?: string | null; note?: string | null
}
interface Ref { id: string; name: string; _href: string }
interface Item {
  id: string; category: 'material' | 'process'
  group: string; group_label: string
  family: string; family_label: string
  name: string; name_en?: string | null; model: string
  aliases?: string[]
  notes?: string | null
  applications?: string[]
  specs?: Record<string, any>
  _slug: string; _href: string
  _processes?: Ref[]; _materials?: Ref[]; _suppliers?: Sup[]
}

const all = ref<Item[]>([...materialsData.materials || [], ...materialsData.processes || []])
// URL 状态放 onMounted：SSR 与首帧一致，深链也不会 hydration mismatch。
const q = ref('')
const sortKey = ref('group')
const active = ref<Record<string, string>>({})

onMounted(() => {
  const params = new URLSearchParams(window.location.search)
  q.value = params.get('q') || ''
  const group = params.get('group')
  if (group) active.value = { ...active.value, kind: group }
})

const GROUP_ORDER = ['metal', 'engineering_plastic', 'printing', 'composite', 'elastomer', 'process']
const FAMILY_ORDER = [
  'aluminum', 'titanium', 'alloy_steel', 'stainless_steel', 'magnesium',
  'peek', 'pps', 'pa', 'abs', 'pc_abs', 'pom',
  'pla', 'petg', 'photopolymer',
  'cfrp', 'gfrp', 'uhmwpe',
  'silicone', 'epdm', 'tpu',
  'machining', 'additive', 'molding', 'casting', 'composite',
]

const groupRank = (g: string) => {
  const i = GROUP_ORDER.indexOf(g)
  return i < 0 ? GROUP_ORDER.length : i
}
const familyRank = (f: string) => {
  const i = FAMILY_ORDER.indexOf(f)
  return i < 0 ? FAMILY_ORDER.length : i
}

const facets = computed(() => {
  const g = new Map<string, { label: string; count: number }>()
  for (const x of all.value) {
    const cur = g.get(x.group) || { label: x.group_label || x.group, count: 0 }
    cur.count += 1
    g.set(x.group, cur)
  }
  const kind = [...g.entries()]
    .sort((a, b) => groupRank(a[0]) - groupRank(b[0]))
    .map(([value, v]) => ({ group: 'kind', value, label: v.label, count: v.count }))

  const f = new Map<string, { label: string; count: number }>()
  for (const x of all.value) {
    const cur = f.get(x.family) || { label: x.family_label || x.family, count: 0 }
    cur.count += 1
    f.set(x.family, cur)
  }
  const fam = [...f.entries()]
    .sort((a, b) => familyRank(a[0]) - familyRank(b[0]))
    .map(([value, v]) => ({ group: 'fam', value, label: v.label, count: v.count }))
  return [...kind, ...fam]
})

const asc = (v: any) => (typeof v === 'number' ? v : Infinity)
const desc = (v: any) => (typeof v === 'number' ? v : -Infinity)
const PRICE: Record<string, number> = { 低: 1, '低-中': 1.5, 中: 2, 中高: 3, 高: 4 }

function specValues(specs: Record<string, any> | undefined): string[] {
  if (!specs) return []
  const out: string[] = []
  for (const [k, v] of Object.entries(specs)) {
    if (v === null || v === undefined || v === '') continue
    if (Array.isArray(v)) out.push(`${k} ${v.join(' ')}`)
    else if (typeof v === 'object') out.push(`${k} ${Object.values(v).join(' ')}`)
    else out.push(`${k} ${v}`)
  }
  return out
}

/** 多词 AND：搜「CNC 铝」「PEEK 耐温」都应窄化结果，而不是把整页匹配出去。 */
function matchesQuery(x: Item, kw: string): boolean {
  const terms = kw.split(/\s+/).filter(Boolean)
  if (!terms.length) return true
  const hay = [x.name, x.name_en, x.model, x.group_label, x.family_label,
    ...(x.aliases || []), ...(x.applications || []), x.notes,
    ...specValues(x.specs)].filter(Boolean).join(' ').toLowerCase()
  return terms.every(t => hay.includes(t))
}

const rows = computed(() => {
  const kw = q.value.trim().toLowerCase()
  const kind = active.value.kind
  const fam = active.value.fam
  let out = all.value.filter((x) => {
    if (kind && x.group !== kind) return false
    if (fam && x.family !== fam) return false
    if (!kw) return true
    return matchesQuery(x, kw)
  })
  out = [...out].sort((a, b) => {
    const sa = a.specs || {}
    const sb = b.specs || {}
    if (sortKey.value === 'density') return asc(sa.density_g_cm3) - asc(sb.density_g_cm3)
    if (sortKey.value === 'modulus') return desc(sb.modulus_GPa) - desc(sa.modulus_GPa)
    if (sortKey.value === 'tensile') return desc(sb.tensile_MPa) - desc(sa.tensile_MPa)
    if (sortKey.value === 'temp') return desc(sb.service_temp_C) - desc(sa.service_temp_C)
    if (sortKey.value === 'price')
      return (PRICE[String(sa.price_level || '')] ?? 99) - (PRICE[String(sb.price_level || '')] ?? 99)
    if (sortKey.value === 'name') return a.name.localeCompare(b.name, 'zh')
    return groupRank(a.group) - groupRank(b.group)
      || familyRank(a.family) - familyRank(b.family)
      || a.name.localeCompare(b.name, 'zh')
  })
  return out
})

const val = (v: any) => (v === null || v === undefined || v === '' ? '—' : String(v))
const modLabel = (x: Item) => (x.specs?.modulus_kind === '弯曲' ? '弯曲模量' : '弹性模量')
function wu(v: any, unit: string): string {
  if (v === null || v === undefined || v === '') return '—'
  const t = String(v)
  return /[a-zA-Z\u4e00-\u9fa5]/.test(t) ? t : `${t} ${unit}`
}
function pitch(x: Item): string {
  const t = x.notes || ''
  if (!t) return ''
  const m = String(t).split(/(?<=[。；])/)[0] || String(t)
  return m.replace(/\*\*(.+?)\*\*/g, '$1').trim()
}
const href = (x: Item) => (x.category === 'process' ? `./materials/process-${x._slug}.html` : `./materials/${x._slug}.html`)
const refHref = (r: Ref) => `./materials/${r._href}.html`
const supHref = (x: Item) => `./suppliers.html?mat=${encodeURIComponent(x.id)}`
</script>

<template>
  <ExplorerShell
    kicker="机器人结构材料"
    title="先选材料，再谈结构和工艺。"
    lead="材料比的是物理属性与工艺适配，不是品牌。密度 / 模量 / 抗拉强度直接给 SI 换算，方便进 MuJoCo；形态规格与加工工艺分开看，渠道和价格回链到渠道库。"
    search-placeholder="搜牌号 / 材料 / 工艺 / 应用"
    :facets="facets"
    :sorts="[
      { k: 'group', label: '按分组' }, { k: 'density', label: '按密度（低→高）' },
      { k: 'modulus', label: '按模量' }, { k: 'tensile', label: '按抗拉强度' },
      { k: 'temp', label: '按耐温' }, { k: 'price', label: '按价格档' },
      { k: 'name', label: '按名称' },
    ]"
    v-model:sort-key="sortKey"
    v-model:active="active"
    :count="rows.length"
    count-unit="项"
    empty-text="没有匹配的材料或工艺；换个关键词，或点掉筛选。缺的条目欢迎补数据。"
    @update:q="q = $event"
  >
    <template #note>
      当前 36 条材料/工艺均为 <strong>B 级</strong>典型值，不是厂商认证；热处理状态、纤维方向与批次会改变实际值。
      没有官方型号图时不放示意图 —— 色块只表示材料族，<strong>不冒充产品图</strong>。
    </template>

    <div v-for="x in rows" :key="x.id" class="ex-card">
      <div class="ex-plate mt-plate" :class="`mt-sw-${x.family}`">
        <span class="mt-symbol">{{ x.model }}</span>
        <span class="mt-swlabel">{{ x.group_label }}</span>
      </div>
      <div class="ex-body">
        <div class="ex-title">
          <a :href="href(x)">{{ x.name }}</a>
          <em class="ex-tag">{{ x.family_label }}</em>
          <em class="ex-tag">B 级</em>
        </div>
        <p class="ex-sub">{{ x.name_en || x.group_label }}</p>
        <p v-if="pitch(x)" class="ex-desc">{{ pitch(x) }}</p>

        <dl v-if="x.category === 'material'" class="ex-kv">
          <div><dt>密度</dt><dd>{{ wu(x.specs?.density_g_cm3, 'g/cm³') }}</dd></div>
          <div><dt>{{ modLabel(x) }}</dt><dd>{{ wu(x.specs?.modulus_GPa, 'GPa') }}</dd></div>
          <div><dt>抗拉</dt><dd>{{ wu(x.specs?.tensile_MPa, 'MPa') }}</dd></div>
          <div><dt>耐温</dt><dd>{{ wu(x.specs?.service_temp_C, '°C') }}</dd></div>
        </dl>
        <dl v-else class="ex-kv">
          <div><dt>公差</dt><dd>{{ wu(x.specs?.tolerance_mm, 'mm') }}</dd></div>
          <div><dt>层高</dt><dd>{{ wu(x.specs?.layer_height_mm, 'mm') }}</dd></div>
          <div><dt>成本</dt><dd>{{ val(x.specs?.cost_level) }}</dd></div>
          <div><dt>交期</dt><dd>{{ val(x.specs?.lead_time) }}</dd></div>
        </dl>

        <div class="ex-foot">
          <template v-if="x.category === 'material'">
            <a v-for="p in (x._processes || []).slice(0, 2)" :key="p.id"
               class="ex-pill" :href="refHref(p)">{{ p.name }}</a>
            <span v-if="(x._processes || []).length > 2" class="ex-pill off">
              +{{ (x._processes || []).length - 2 }}
            </span>
            <a v-if="x._suppliers?.length" class="ex-pill" :href="supHref(x)">渠道 ×{{ x._suppliers.length }}</a>
          </template>
          <template v-else>
            <span class="ex-pill off">材料 ×{{ x._materials?.length || 0 }}</span>
            <a v-if="x._suppliers?.length" class="ex-pill" :href="supHref(x)">渠道 ×{{ x._suppliers.length }}</a>
          </template>
          <a class="ex-link" :href="href(x)" style="margin-left:auto">详情 →</a>
        </div>
      </div>
    </div>
  </ExplorerShell>
</template>

<style scoped>
a.ex-pill { text-decoration: none; }
a.ex-pill:hover { border-color: var(--vp-c-brand-2); color: var(--vp-c-brand-1); }
</style>
