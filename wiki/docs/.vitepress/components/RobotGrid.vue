<script setup lang="ts">
/**
 * 整机列表（与部件库平行的板块）。
 *
 * 为什么用组件而不是在 markdown 里手写 HTML：
 *   Vue 的模板解析会把 <a> 在遇到块级 <div> 时自动闭合，
 *   「<a> 包整张卡片」这种常见写法会直接编译失败。
 *
 * 「进仿真」按钮：按 YG 要求**留接口不接功能** —— 点了只提示，
 * URDF 链接列在每台的详情页。
 */
import { computed, onMounted, ref } from 'vue'

interface Robot {
  id: string; model: string; vendor: string; vendor_cn?: string
  subtype?: string; _slug: string
  specs?: Record<string, any>
}

const all = ref<Robot[]>([])
const q = ref('')
const sub = ref('')

const SUB: Record<string, string> = {
  quadruped: '四足', humanoid: '人形', biped: '双足',
  wheeled: '轮式', wheeled_quadruped: '轮足',
  wheeled_quadruped_inward_knee: '轮足（内膝）',
  arm: '机械臂', other: '其他',
}

onMounted(async () => {
  const r = await fetch(`${import.meta.env.BASE_URL}robots.json`)
  if (!r.ok) return
  const d = await r.json()
  all.value = d.robots || []
})

const subs = computed(() => {
  const m = new Map<string, number>()
  for (const x of all.value) {
    const k = x.subtype || 'other'
    m.set(k, (m.get(k) || 0) + 1)
  }
  return [...m.entries()]
})

const rows = computed(() => {
  const kw = q.value.trim().toLowerCase()
  return all.value.filter((x) => {
    if (sub.value && (x.subtype || 'other') !== sub.value) return false
    if (!kw) return true
    const hay = [x.model, x.vendor, x.vendor_cn, x.subtype]
      .filter(Boolean).join(' ').toLowerCase()
    return hay.includes(kw)
  })
})

const num = (v: any) => (v === null || v === undefined || v === '') ? '—' : String(v)
/** 值里已含单位（如「0.5 h（6S LiPo）」）就不再追加，避免出现「0.5 h h」 */
function withUnit(v: any, unit: string): string {
  if (v === null || v === undefined || v === '') return '—'
  const t = String(v)
  return /[a-zA-Z\u4e00-\u9fa5]/.test(t) ? t : `${t} ${unit}`
}
const urdf = (x: Robot) => (x.specs?.urdf_urls as string[] | undefined)?.length || 0
const repo = (x: Robot) => (x.specs?.repo_urls as string[] | undefined)?.length || 0
</script>

<template>
  <div class="rg">
    <div class="rg-bar">
      <input v-model="q" class="rg-q" type="search" placeholder="搜型号 / 厂商" />
      <button class="rg-chip" :class="{ on: sub === '' }" @click="sub = ''">全部 {{ all.length }}</button>
      <button v-for="[k, n] in subs" :key="k" class="rg-chip" :class="{ on: sub === k }"
              @click="sub = sub === k ? '' : k">{{ SUB[k] || k }} {{ n }}</button>
    </div>

    <div class="rg-grid">
      <div v-for="x in rows" :key="x.id" class="rc">
        <div class="rc-plate">
          <img v-if="x.specs?.image_url" :src="x.specs.image_url" :alt="x.model" loading="lazy" />
          <span v-else class="rc-ph">暂无产品图</span>
        </div>
        <div class="rc-body">
          <div class="rc-top">
            <a class="rc-name" :href="`./robots/${x._slug}.html`">{{ x.model }}</a>
            <em>{{ SUB[x.subtype || 'other'] || x.subtype }}</em>
          </div>
          <p class="rc-vendor">{{ x.vendor_cn || x.vendor }}</p>
          <dl class="rc-kv">
            <div><dt>自由度</dt><dd>{{ num(x.specs?.dof) }}</dd></div>
            <div><dt>质量</dt><dd>{{ withUnit(x.specs?.mass_kg, 'kg') }}</dd></div>
            <div><dt>负载</dt><dd>{{ withUnit(x.specs?.payload_kg, 'kg') }}</dd></div>
            <div><dt>续航</dt><dd>{{ withUnit(x.specs?.endurance_h, 'h') }}</dd></div>
          </dl>
          <div class="rc-links">
            <span class="rc-sim" title="进仿真接口已留（URDF 链接见详情页），暂未接入">进仿真</span>
            <a v-if="urdf(x)" class="rc-tag" :href="`./robots/${x._slug}.html`">URDF ×{{ urdf(x) }}</a>
            <a v-if="repo(x)" class="rc-tag" :href="`./robots/${x._slug}.html`">仓库 ×{{ repo(x) }}</a>
          </div>
        </div>
      </div>
    </div>

    <p v-if="!rows.length" class="rg-empty">没有匹配的整机。</p>
  </div>
</template>

<style scoped>
.rg { max-width: 1120px; margin: 0 auto; padding: 0 1.5rem 3rem; }
.rg-bar { display: flex; flex-wrap: wrap; gap: .45rem; align-items: center; margin: 1.2rem 0 .9rem; }
.rg-q { flex: 1 1 220px; min-width: 170px; font-size: .82rem; padding: .42rem .7rem;
  border: 1px solid var(--vp-c-divider); border-radius: 8px; background: var(--vp-c-bg);
  color: var(--vp-c-text-1); }
.rg-chip { font-size: .74rem; padding: .3rem .62rem; border-radius: 999px;
  border: 1px solid var(--vp-c-divider); background: var(--vp-c-bg);
  color: var(--vp-c-text-2); cursor: pointer; }
.rg-chip:hover { border-color: var(--vp-c-brand-1); color: var(--vp-c-brand-1); }
.rg-chip.on { background: var(--vp-c-brand-1); border-color: var(--vp-c-brand-1); color: #fff; }
.rg-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(260px, 1fr)); gap: .7rem; }
.rc { border: 1px solid var(--vp-c-divider); border-radius: 12px; overflow: hidden;
  background: var(--vp-c-bg); display: flex; flex-direction: column; }
.rc:hover { border-color: var(--vp-c-brand-1); }
.rc-plate { height: 118px; display: flex; align-items: center; justify-content: center;
  background: var(--vp-c-bg-soft); overflow: hidden; }
.rc-plate img { height: 96px; width: auto; object-fit: contain; }
.rc-ph { font-size: .72rem; color: var(--vp-c-text-3); }
.rc-body { padding: .6rem .75rem .7rem; display: flex; flex-direction: column; gap: .32rem; }
.rc-top { display: flex; align-items: baseline; gap: .4rem; flex-wrap: wrap; }
.rc-name { font-size: .88rem; font-weight: 700; color: var(--vp-c-text-1); }
.rc-name:hover { color: var(--vp-c-brand-1); }
.rc-top em { font-style: normal; font-size: .64rem; padding: 0 6px; border-radius: 999px;
  background: var(--vp-c-brand-soft); color: var(--vp-c-brand-1); }
.rc-vendor { margin: 0; font-size: .72rem; color: var(--vp-c-text-3); }
.rc-kv { margin: 0; display: flex; flex-direction: column; gap: .12rem; font-size: .74rem; }
.rc-kv div { display: flex; justify-content: space-between; gap: .6rem; }
.rc-kv dt { color: var(--vp-c-text-3); }
.rc-kv dd { margin: 0; color: var(--vp-c-text-2); }
.rc-links { display: flex; gap: .35rem; flex-wrap: wrap; margin-top: .25rem; }
.rc-sim { font-size: .7rem; padding: 1px 8px; border-radius: 999px; border: 1px dashed var(--vp-c-divider);
  color: var(--vp-c-text-3); cursor: not-allowed; }
.rc-tag { font-size: .68rem; padding: 1px 7px; border-radius: 999px;
  background: var(--vp-c-bg-soft); color: var(--vp-c-text-2); text-decoration: none; }
.rc-tag:hover { color: var(--vp-c-brand-1); }
.rg-empty { font-size: .8rem; color: var(--vp-c-text-3); margin-top: 1.4rem; }
</style>
