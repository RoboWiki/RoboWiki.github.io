<script setup lang="ts">
/**
 * 机器人整机列表（统一外壳版）。
 *
 * 卡片只放「和选型有关」的四项：自由度 / 质量 / 负载 / 续航；
 * URDF、仓库这类链接计数放到底部一行 —— 想进仿真的自然会去找。
 */
import { computed, onMounted, ref } from 'vue'
import ExplorerShell from './ExplorerShell.vue'

interface Robot {
  id: string; model: string; vendor: string; vendor_cn?: string
  subtype?: string; _slug: string
  specs?: Record<string, any>
}

const SUB: Record<string, string> = {
  quadruped: '四足', humanoid: '人形', biped: '双足',
  wheeled: '轮式', wheeled_quadruped: '轮足',
  wheeled_quadruped_inward_knee: '轮足（内膝）',
  arm: '机械臂', other: '其他',
}

const all = ref<Robot[]>([])
const q = ref('')
const sortKey = ref('vendor')
const active = ref<Record<string, string>>({})

onMounted(async () => {
  const r = await fetch(`${import.meta.env.BASE_URL}robots.json`)
  if (r.ok) all.value = (await r.json()).robots || []
})

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
  return [...m.entries()].map(([v, n]) => ({ group: 'sub', value: v, label: SUB[v] || v, count: n }))
})

const num = (v: any) => (typeof v === 'number' ? v : -Infinity)

const rows = computed(() => {
  const kw = q.value.trim().toLowerCase()
  const sub = active.value.sub
  let out = all.value.filter((x) => {
    if (sub && (x.subtype || 'other') !== sub) return false
    if (!kw) return true
    return [x.model, x.vendor, x.vendor_cn, x.subtype]
      .filter(Boolean).join(' ').toLowerCase().includes(kw)
  })
  out = [...out].sort((a, b) => {
    if (sortKey.value === 'dof') return num(b.specs?.dof) - num(a.specs?.dof)
    if (sortKey.value === 'mass') return num(a.specs?.mass_kg) - num(b.specs?.mass_kg)
    if (sortKey.value === 'payload') return num(b.specs?.payload_kg) - num(a.specs?.payload_kg)
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
const repo = (x: Robot) => (x.specs?.repo_urls as string[] | undefined)?.length || 0
</script>

<template>
  <ExplorerShell
    kicker="机器人整机"
    title="部件选完之后，看整机方案。"
    lead="与「机器人部件」平行，不是它的子集。部件比参数，整机看方案：几自由度、带不带算力、电池续航、有没有开源 URDF。"
    search-placeholder="搜型号 / 厂商"
    :facets="facets"
    :sorts="[{ k: 'vendor', label: '按厂商' }, { k: 'dof', label: '按自由度' }, { k: 'mass', label: '按质量' }, { k: 'payload', label: '按负载' }]"
    v-model:sort-key="sortKey"
    v-model:active="active"
    :count="rows.length"
    count-unit="台"
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
          <em class="ex-tag">{{ SUB[x.subtype || 'other'] || x.subtype }}</em>
        </div>
        <p class="ex-sub">{{ x.vendor_cn || x.vendor }}</p>
        <dl class="ex-kv">
          <div><dt>自由度</dt><dd>{{ val(x.specs?.dof) }}</dd></div>
          <div><dt>质量</dt><dd>{{ withUnit(x.specs?.mass_kg, 'kg') }}</dd></div>
          <div><dt>负载</dt><dd>{{ withUnit(x.specs?.payload_kg, 'kg') }}</dd></div>
          <div><dt>续航</dt><dd>{{ withUnit(x.specs?.endurance_h, 'h') }}</dd></div>
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
