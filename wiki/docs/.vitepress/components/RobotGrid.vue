<script setup lang="ts">
/**
 * 机器人整机列表（统一外壳版）。
 *
 * 卡片只放「和选型有关」的四项：自由度 / 质量 / 负载 / 续航；
 * URDF、仓库这类链接计数放到底部一行 —— 想进仿真的自然会去找。
 */
import { computed, onMounted, ref, watch } from 'vue'
import ExplorerShell from './ExplorerShell.vue'

interface Robot {
  id: string; model: string; vendor: string; vendor_cn?: string
  subtype?: string; subtype_label?: string; _slug: string
  specs?: Record<string, any>
}

const SUB: Record<string, string> = {
  quadruped: '四足', humanoid: '人形', biped: '双足',
  wheeled_quadruped: '四轮足',
  wheeled_quadruped_inward_knee: '四轮足·内膝肘',
  infantry: '步兵', sentry: '哨兵', hero: '英雄', engineer: '工程',
  arm: '机械臂', other: '其他',
}

const SUB_ORDER = [
  'quadruped', 'humanoid', 'wheeled_quadruped',
  'wheeled_quadruped_inward_knee', 'biped',
  'infantry', 'sentry', 'hero', 'engineer', 'arm', 'other',
]
/** 这四个兵种先留入口；还没有整机数据时也显示，点了给空列表与投稿提示。 */
const ALWAYS_SUBS = new Set(['infantry', 'sentry', 'hero', 'engineer'])

const all = ref<Robot[]>([])
const q = ref('')
const sortKey = ref('vendor')
const active = ref<Record<string, string>>({})

onMounted(async () => {
  const r = await fetch(`${import.meta.env.BASE_URL}robots.json`)
  if (!r.ok) return
  all.value = (await r.json()).robots || []
  // 预选必须放在挂载后：构建时 SSR 的 DOM 里没有带种类的 chip，
  // 水合阶段设置的选中态补不上 class，直接刷新就会看起来没选中。
  const wanted = new URLSearchParams(window.location.search).get('subtype')?.trim() || ''
  if (!wanted) return
  const ok = facets.value.some((f) => f.group === 'sub' && f.value === wanted)
  if (ok) active.value = { ...active.value, sub: wanted }
  else syncSubtypeUrl('')
})

/** 种类进 URL：从竞赛页点过来时能落到同一栏，刷新也不丢。 */
function syncSubtypeUrl(v: string) {
  if (typeof window === 'undefined') return
  const url = new URL(window.location.href)
  if (v) url.searchParams.set('subtype', v)
  else url.searchParams.delete('subtype')
  history.replaceState(history.state, '', url)
}

watch(() => active.value.sub, (v) => syncSubtypeUrl(v || ''))

function imgUrl(p?: string | null): string {
  if (!p) return ''
  const base = String(import.meta.env.BASE_URL || '/')
  return base.replace(/\/$/, '') + '/' + p.replace(/^\//, '')
}

const facets = computed(() => {
  const m = new Map<string, number>()
  for (const x of all.value) {
    const k = x.subtype || 'other'
    m.set(k, (m.get(k) || 0) + 1)
  }
  const order = [...SUB_ORDER]
  for (const v of m.keys()) if (!order.includes(v)) order.push(v)
  const sub = order
    .filter((v) => m.has(v) || ALWAYS_SUBS.has(v))
    .map((v) => ({ group: 'sub', value: v, label: SUB[v] || v, count: m.get(v) || 0 }))
  const withEco = all.value.filter((x) => eco(x) > 0).length
  sub.push({ group: 'eco', value: 'yes', label: '有开源生态', count: withEco })
  sub.push({ group: 'eco', value: 'no', label: '未收录', count: all.value.length - withEco })
  return sub
})

const num = (v: any) => (typeof v === 'number' ? v : -Infinity)

function matchesSub(x: Robot, sub: string): boolean {
  return (x.subtype || 'other') === sub
}

const rows = computed(() => {
  const kw = q.value.trim().toLowerCase()
  const sub = active.value.sub
  let out = all.value.filter((x) => {
    if (sub && !matchesSub(x, sub)) return false
    const ecoSel = active.value.eco
    if (ecoSel === 'yes' && eco(x) <= 0) return false
    if (ecoSel === 'no' && eco(x) > 0) return false
    if (!kw) return true
    return [x.model, x.vendor, x.vendor_cn, x.subtype_label, x.subtype]
      .filter(Boolean).join(' ').toLowerCase().includes(kw)
  })
  out = [...out].sort((a, b) => {
    if (sortKey.value === 'dof') return num(b.specs?.dof) - num(a.specs?.dof)
    if (sortKey.value === 'mass') return num(a.specs?.mass_kg) - num(b.specs?.mass_kg)
    if (sortKey.value === 'payload') return num(b.specs?.payload_kg) - num(a.specs?.payload_kg)
    if (sortKey.value === 'eco') return eco(b) - eco(a)
    if (sortKey.value === 'price') return price(a) - price(b)
    return (a.vendor_cn || a.vendor).localeCompare(b.vendor_cn || b.vendor, 'zh')
  })
  return out
})

const val = (v: any) => (v === null || v === undefined || v === '' ? '—' : String(v))
function withUnit(v: any, unit: string): string {
  if (v === null || v === undefined || v === '') return '—'
  const t = String(v)
  return /[a-zA-Z\u4e00-\u9fa5]/.test(t) ? t : `${t} ${unit}`
}
const urdf = (x: Robot) => (x.specs?.urdf_urls as string[] | undefined)?.length || 0
const eco = (x: Robot) => (x.specs?.ecosystem_count as number | undefined) || 0
/** 定位：notes 首句（到第一个句号为止），最多两行 —— 数字之外总得有句话 */
function pitch(x: Robot): string {
  const t = (x as any).notes || (x.specs?.pitch as string) || ''
  if (!t) return ''
  const m = String(t).split(/(?<=[。；])/)[0] || String(t)
  // notes 里有 markdown 粗体；卡片是纯文本渲染，会把星号露出来 —— 去掉标记
  return m.replace(/\*\*(.+?)\*\*/g, '$1').trim()
}
const price = (x: Robot) => (typeof (x as any).price_cny === 'number' ? (x as any).price_cny : Infinity)
const repo = (x: Robot) => (x.specs?.repo_urls as string[] | undefined)?.length || 0
</script>

<template>
  <ExplorerShell
    kicker="机器人整机"
    title="部件选完之后，看整机方案。"
    lead="与「机器人部件」平行，不是它的子集。部件比参数，整机看方案与生态：几自由度、带不带算力、以及这台机器在开源世界里有多少现成工程可以借。"
    search-placeholder="搜型号 / 厂商"
    :facets="facets"
    :sorts="[
      { k: 'eco', label: '按开源生态' }, { k: 'vendor', label: '按厂商' },
      { k: 'dof', label: '按自由度' }, { k: 'mass', label: '按质量' },
      { k: 'payload', label: '按负载' }, { k: 'price', label: '按价格' },
    ]"
    v-model:sort-key="sortKey"
    v-model:active="active"
    :count="rows.length"
    count-unit="台"
    empty-text="没有匹配的整机；这类还没收录时，欢迎补型号或复现记录。"
    @update:q="q = $event"
  >
    <template #note>
      <b>进仿真</b> 按钮已留接口但<strong>暂未接入</strong>；每台的 URDF / 仓库链接在详情页，可以直接下载。
    </template>

    <div v-for="x in rows" :key="x.id" class="ex-card">
      <div class="ex-plate">
        <img v-if="x.specs?.image_url" :src="imgUrl(x.specs.image_url)" :alt="x.model" loading="lazy" />
        <span v-else class="ex-ph">暂无产品图</span>
      </div>
      <div class="ex-body">
        <div class="ex-title">
          <a :href="`./robots/${x._slug}.html`">{{ x.model }}</a>
          <em class="ex-tag">{{ x.subtype_label || SUB[x.subtype || 'other'] || x.subtype }}</em>
        </div>
        <p class="ex-sub">{{ x.vendor_cn || x.vendor }}</p>
        <p v-if="pitch(x)" class="ex-desc">{{ pitch(x) }}</p>
        <dl class="ex-kv">
          <div><dt>自由度</dt><dd>{{ val(x.specs?.dof) }}</dd></div>
          <div><dt>质量</dt><dd>{{ withUnit(x.specs?.mass_kg, 'kg') }}</dd></div>
          <div><dt>负载</dt><dd>{{ withUnit(x.specs?.payload_kg, 'kg') }}</dd></div>
          <div :class="{ hi: eco(x) > 0 }"><dt>开源生态</dt><dd>{{ eco(x) ? eco(x) + ' 项' : '—' }}</dd></div>
        </dl>
        <div class="ex-foot">
          <span class="ex-pill off" title="进仿真接口已留（URDF 链接见详情页），暂未接入">进仿真</span>
          <a v-if="urdf(x)" class="ex-pill" :href="`./robots/${x._slug}.html`">URDF ×{{ urdf(x) }}</a>
          <a v-if="repo(x)" class="ex-pill" :href="`./robots/${x._slug}.html`">仓库 ×{{ repo(x) }}</a>
          <a class="ex-link" :href="`./robots/${x._slug}.html`" style="margin-left:auto">详情 →</a>
        </div>
      </div>
    </div>
  </ExplorerShell>
</template>
