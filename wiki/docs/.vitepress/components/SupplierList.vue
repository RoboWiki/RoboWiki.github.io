<script setup lang="ts">
/**
 * 供应商列表（与部件库完全分开）。
 *
 * 为什么不做成部件卡片：
 *   部件比参数（扭矩/惯量/接口），供应商比「谁靠谱」（质量/交期/价格/发票）。
 *   字段、排序、评价方式都不同，复用同一套卡片只会两头别扭。
 *
 * 数据来自 public/suppliers.json（构建时由 data/suppliers.json 生成）。
 * 定性描述原样展示，不折算星级 —— 「稳定，精度高」变成 4.5 分是编造精度。
 */
import { computed, onMounted, ref } from 'vue'

interface Sup {
  id: string
  name: string
  brand: string
  kind: 'platform' | 'shop'
  url: string | null
  process: string | null
  process_tag: string | null
  quality: string | null
  punctual: string | null
  price_level: string | null
  invoice: string | null
  materials: string | null
  lead: string | null
  moq: string | null
  notes: string | null
  tier: string | null
}

const all = ref<Sup[]>([])
const q = ref('')
const tag = ref('')
const kind = ref<'' | 'platform' | 'shop'>('')
const only = ref(false)      // 只看有点评的
const open = ref<string | null>(null)

onMounted(async () => {
  const r = await fetch(`${import.meta.env.BASE_URL}suppliers.json`)
  if (!r.ok) return
  const d = await r.json()
  all.value = d.suppliers || []
})

const tags = computed(() => {
  const m = new Map<string, number>()
  for (const s of all.value) {
    const t = s.process_tag || '未记工艺'
    m.set(t, (m.get(t) || 0) + 1)
  }
  return [...m.entries()].sort((a, b) => b[1] - a[1])
})

const hasNote = (s: Sup) => !!s.notes && !s.notes.includes('未附点评')

const rows = computed(() => {
  const kw = q.value.trim().toLowerCase()
  return all.value.filter((s) => {
    if (kind.value && s.kind !== kind.value) return false
    if (only.value && !hasNote(s)) return false
    if (tag.value && (s.process_tag || '未记工艺') !== tag.value) return false
    if (!kw) return true
    const hay = [s.name, s.process, s.quality, s.punctual, s.price_level,
                 s.notes, s.materials].filter(Boolean).join(' ').toLowerCase()
    return hay.includes(kw)
  })
})

const PRICE_ORDER: Record<string, number> = {
  低: 1, 偏低: 2, '中等偏低': 3, 中等: 4, 尚可: 4, '中等偏高': 5, 偏高: 6, 高: 6, 贵: 7,
}

function priceRank(s: Sup) {
  return PRICE_ORDER[(s.price_level || '').trim()] ?? 99
}

const sorted = computed(() =>
  [...rows.value].sort((a, b) => {
    // 平台在前（资料更全），其余按价格档次从低到高
    if (a.kind !== b.kind) return a.kind === 'platform' ? -1 : 1
    return priceRank(a) - priceRank(b)
  }),
)

const QUALITY_GOOD = ['稳定，精度高', '精度高', '稳定，精度好', '稳定，精度一般']
</script>

<template>
  <div class="sup">
    <div class="sup-bar">
      <input v-model="q" class="sup-q" type="search" placeholder="搜店名 / 工艺 / 点评关键词" />
      <button class="sup-btn" :class="{ on: kind === 'platform' }" @click="kind = kind === 'platform' ? '' : 'platform'">自营平台</button>
      <button class="sup-btn" :class="{ on: kind === 'shop' }" @click="kind = kind === 'shop' ? '' : 'shop'">淘宝店铺</button>
      <button class="sup-btn" :class="{ on: only }" @click="only = !only">只看有点评</button>
      <span class="sup-count">{{ sorted.length }} 家</span>
    </div>

    <div class="sup-tags">
      <button class="sup-tag" :class="{ on: tag === '' }" @click="tag = ''">全部工艺</button>
      <button v-for="[t, n] in tags" :key="t" class="sup-tag" :class="{ on: tag === t }"
              @click="tag = tag === t ? '' : t">{{ t }} {{ n }}</button>
    </div>

    <div class="sup-grid">
      <article v-for="s in sorted" :key="s.id" class="sc" :class="{ plat: s.kind === 'platform' }">
        <div class="sc-head">
          <a v-if="s.url" :href="s.url" target="_blank" rel="noopener nofollow" class="sc-name">{{ s.name }}</a>
          <span v-else class="sc-name">{{ s.name }}</span>
          <span class="sc-kind">{{ s.kind === 'platform' ? '自营平台' : '店铺' }}</span>
        </div>
        <p class="sc-proc">{{ s.process || '工艺未记' }}</p>
        <dl class="sc-kv">
          <div v-if="s.quality"><dt>质量</dt><dd>{{ s.quality }}</dd></div>
          <div v-if="s.punctual"><dt>交期</dt><dd>{{ s.punctual }}</dd></div>
          <div v-if="s.price_level"><dt>价格</dt><dd>{{ s.price_level }}</dd></div>
          <div v-if="s.invoice"><dt>发票</dt><dd>{{ s.invoice }}</dd></div>
          <div v-if="s.materials"><dt>材料</dt><dd>{{ s.materials }}</dd></div>
          <div v-if="s.lead"><dt>工期</dt><dd>{{ s.lead }}</dd></div>
        </dl>
        <p v-if="hasNote(s)" class="sc-note" :class="{ open: open === s.id }" @click="open = open === s.id ? null : s.id">
          {{ s.notes }}
        </p>
        <p v-else class="sc-none">名录未附点评</p>
      </article>
    </div>

    <p v-if="!sorted.length" class="sup-empty">没有匹配的供应商，换个关键词或点掉筛选。</p>
  </div>
</template>

<style scoped>
.sup { max-width: 1120px; margin: 0 auto; padding: 0 1.5rem 3rem; }
.sup-bar { display: flex; flex-wrap: wrap; gap: 0.5rem; align-items: center; margin: 1.4rem 0 0.7rem; }
.sup-q { flex: 1 1 220px; min-width: 180px; font-size: 0.82rem; padding: 0.42rem 0.7rem;
  border: 1px solid var(--vp-c-divider); border-radius: 8px; background: var(--vp-c-bg); color: var(--vp-c-text-1); }
.sup-btn, .sup-tag { font-size: 0.74rem; padding: 0.3rem 0.62rem; border-radius: 999px;
  border: 1px solid var(--vp-c-divider); background: var(--vp-c-bg); color: var(--vp-c-text-2); cursor: pointer; }
.sup-btn:hover, .sup-tag:hover { border-color: var(--vp-c-brand-1); color: var(--vp-c-brand-1); }
.sup-btn.on, .sup-tag.on { background: var(--vp-c-brand-1); border-color: var(--vp-c-brand-1); color: #fff; }
.sup-count { font-size: 0.74rem; color: var(--vp-c-text-3); margin-left: auto; }
.sup-tags { display: flex; flex-wrap: wrap; gap: 0.4rem; margin-bottom: 1rem; }
.sup-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(300px, 1fr)); gap: 0.7rem; }
.sc { border: 1px solid var(--vp-c-divider); border-radius: 12px; padding: 0.8rem 0.9rem;
  background: var(--vp-c-bg); display: flex; flex-direction: column; gap: 0.4rem; }
.sc.plat { border-color: var(--vp-c-brand-1); background: var(--vp-c-brand-soft); }
.sc-head { display: flex; align-items: baseline; gap: 0.45rem; flex-wrap: wrap; }
.sc-name { font-size: 0.9rem; font-weight: 700; color: var(--vp-c-text-1); }
a.sc-name:hover { color: var(--vp-c-brand-1); }
.sc-kind { font-size: 0.64rem; padding: 0 6px; border-radius: 999px;
  background: var(--vp-c-default-soft); color: var(--vp-c-text-3); }
.sc-proc { margin: 0; font-size: 0.76rem; color: var(--vp-c-text-2); line-height: 1.6; }
.sc-kv { margin: 0.1rem 0 0; display: grid; grid-template-columns: auto 1fr; gap: 0.15rem 0.5rem; font-size: 0.74rem; }
.sc-kv div { display: contents; }
.sc-kv dt { color: var(--vp-c-text-3); }
.sc-kv dd { margin: 0; color: var(--vp-c-text-2); }
.sc-note { margin: 0.2rem 0 0; font-size: 0.75rem; line-height: 1.75; color: var(--vp-c-text-2);
  border-left: 2px solid var(--vp-c-divider); padding-left: 0.6rem; cursor: pointer;
  display: -webkit-box; -webkit-line-clamp: 3; -webkit-box-orient: vertical; overflow: hidden; }
.sc-note.open { display: block; }
.sc-none { margin: 0.2rem 0 0; font-size: 0.72rem; color: var(--vp-c-text-3); }
.sup-empty { font-size: 0.8rem; color: var(--vp-c-text-3); margin-top: 1.5rem; }
</style>
