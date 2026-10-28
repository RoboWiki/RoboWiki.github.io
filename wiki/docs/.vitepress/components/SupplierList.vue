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
  url: string | null
  process: string | null
  category: string | null
  fine: string | null
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

const props = withDefaults(defineProps<{ lang?: 'zh' | 'en' }>(), { lang: 'zh' })
const en = computed(() => props.lang === 'en')
const L = computed(() => en.value
  ? { search: 'Search shop / process / review', allcat: 'All categories',
      allfine: 'All types', notesOnly: 'With reviews', count: 'suppliers',
      noNotes: 'No review in the directory', empty: 'No supplier matched. Try another keyword.',
      q: 'Quality', lead: 'Lead time', price: 'Price', inv: 'Invoice', mat: 'Materials' }
  : { search: '搜店名 / 工艺 / 点评关键词', allcat: '全部品类',
      allfine: '全部细分', notesOnly: '只看有点评', count: '家',
      noNotes: '名录未附点评', empty: '没有匹配的供应商，换个关键词或点掉筛选。',
      q: '质量', lead: '交期', price: '价格', inv: '发票', mat: '材料' })

const all = ref<Sup[]>([])
const q = ref('')
const tag = ref('')
const cat = ref('')
const kind = ref<'' | 'shop'>('')
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
    if (cat.value && (s.category || '未分类') !== cat.value) continue
    const t = s.fine || s.process_tag || '其他/未记'
    m.set(t, (m.get(t) || 0) + 1)
  }
  return [...m.entries()].sort((a, b) => b[1] - a[1])
})

//: 大类来自名录表里的分类列（机械加工 / 螺钉 / 标准件 / 轴承 / 电子 / 传感器 …）
const cats = computed(() => {
  const m = new Map<string, number>()
  for (const s of all.value) {
    const c = s.category || '未分类'
    m.set(c, (m.get(c) || 0) + 1)
  }
  return [...m.entries()].sort((a, b) => b[1] - a[1])
})

function setCat(c: string) {
  cat.value = cat.value === c ? '' : c
  tag.value = ''      // 切大类时清掉细分，避免出现 0 结果
}

const hasNote = (s: Sup) => !!s.notes && !s.notes.includes('未附点评')

const rows = computed(() => {
  const kw = q.value.trim().toLowerCase()
  return all.value.filter((s) => {
    if (only.value && !hasNote(s)) return false
    if (cat.value && (s.category || '未分类') !== cat.value) return false
    if (tag.value && (s.fine || s.process_tag || '其他/未记') !== tag.value) return false
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
    // 只按价格档次从低到高；没有实证的「知名平台」不享受置顶
    return priceRank(a) - priceRank(b)
  }),
)

const QUALITY_GOOD = ['稳定，精度高', '精度高', '稳定，精度好', '稳定，精度一般']
</script>

<template>
  <div class="sup">
    <div class="sup-bar">
      <input v-model="q" class="sup-q" type="search" :placeholder="L.search" />
      <button class="sup-btn" :class="{ on: only }" @click="only = !only">{{ L.notesOnly }}</button>
      <span class="sup-count">{{ sorted.length }} {{ L.count }}</span>
    </div>

    <div class="sup-cats">
      <button class="sup-tag" :class="{ on: cat === '' }" @click="setCat('')">{{ L.allcat }}</button>
      <button v-for="[c, n] in cats" :key="c" class="sup-tag" :class="{ on: cat === c, main: true }"
              @click="setCat(c)">{{ c }} {{ n }}</button>
    </div>

    <div class="sup-tags">
      <button class="sup-tag" :class="{ on: tag === '' }" @click="tag = ''">{{ L.allfine }}</button>
      <button v-for="[t, n] in tags" :key="t" class="sup-tag" :class="{ on: tag === t }"
              @click="tag = tag === t ? '' : t">{{ t }} {{ n }}</button>
    </div>

    <div class="sup-grid">
      <article v-for="s in sorted" :key="s.id" class="sc">
        <div class="sc-head">
          <a v-if="s.url" :href="s.url" target="_blank" rel="noopener nofollow" class="sc-name">{{ s.name }}</a>
          <span v-else class="sc-name">{{ s.name }}</span>
          <span class="sc-kind">{{ s.category || '未分类' }}</span>
          <span v-if="s.fine && s.fine !== s.category" class="sc-kind">{{ s.fine }}</span>
        </div>
        <p class="sc-proc">{{ s.process || '工艺未记' }}</p>
        <dl class="sc-kv">
          <div v-if="s.quality"><dt>{{ L.q }}</dt><dd>{{ s.quality }}</dd></div>
          <div v-if="s.punctual"><dt>{{ L.lead }}</dt><dd>{{ s.punctual }}</dd></div>
          <div v-if="s.price_level"><dt>{{ L.price }}</dt><dd>{{ s.price_level }}</dd></div>
          <div v-if="s.invoice"><dt>{{ L.inv }}</dt><dd>{{ s.invoice }}</dd></div>
          <div v-if="s.materials"><dt>{{ L.mat }}</dt><dd>{{ s.materials }}</dd></div>
          <div v-if="s.lead"><dt>工期</dt><dd>{{ s.lead }}</dd></div>
        </dl>
        <p v-if="hasNote(s)" class="sc-note" :class="{ open: open === s.id }" @click="open = open === s.id ? null : s.id">
          {{ s.notes }}
        </p>
        <p v-else class="sc-none">{{ L.noNotes }}</p>
      </article>
    </div>

    <p v-if="!sorted.length" class="sup-empty">{{ L.empty }}</p>
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
.sup-cats { display: flex; flex-wrap: wrap; gap: 0.4rem; margin-bottom: 0.45rem; }
.sup-tags { display: flex; flex-wrap: wrap; gap: 0.4rem; margin-bottom: 1rem; }
.sup-tag.main { font-weight: 600; }
.sup-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(300px, 1fr)); gap: 0.7rem; }
.sc { border: 1px solid var(--vp-c-divider); border-radius: 12px; padding: 0.8rem 0.9rem;
  background: var(--vp-c-bg); display: flex; flex-direction: column; gap: 0.4rem; }
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
