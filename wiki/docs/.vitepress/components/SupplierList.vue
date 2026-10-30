<script setup lang="ts">
/**
 * 加工与采购（原「供应商」）列表：统一外壳版。
 *
 * 与整机/部件同一套交互：搜索 → 分面（品类 / 细分）→ 卡片 → 详情。
 * 卡片比的是「谁靠谱」：质量、交期、价格档、能不能开票，还有点评原话。
 */
import { computed, onMounted, ref } from 'vue'
import ExplorerShell from './ExplorerShell.vue'

interface Sup {
  id: string; name: string; brand?: string; kind?: 'platform' | 'shop'
  url?: string | null; category?: string | null; fine?: string | null
  process?: string | null; quality?: string | null; punctual?: string | null
  price_level?: string | null; invoice?: string | null; materials?: string | null
  lead?: string | null; notes?: string | null; tier?: string | null
}

const all = ref<Sup[]>([])
const q = ref('')
const sortKey = ref('price')
const active = ref<Record<string, string>>({})
const expanded = ref<string | null>(null)

onMounted(async () => {
  const r = await fetch(`${import.meta.env.BASE_URL}suppliers.json`)
  if (r.ok) all.value = (await r.json()).suppliers || []
})

const hasNote = (s: Sup) => !!s.notes

const facets = computed(() => {
  const cat = new Map<string, number>()
  const fine = new Map<string, number>()
  for (const s of all.value) {
    const c = s.category || '未分类'
    cat.set(c, (cat.get(c) || 0) + 1)
    if (!active.value.cat || active.value.cat === c) {
      const f = s.fine || s.process || '未记工艺'
      fine.set(f, (fine.get(f) || 0) + 1)
    }
  }
  const out = [...cat.entries()].sort((a, b) => b[1] - a[1])
    .map(([v, n]) => ({ group: 'cat', value: v, label: v, count: n }))
  out.push(...[...fine.entries()].sort((a, b) => b[1] - a[1]).slice(0, 10)
    .map(([v, n]) => ({ group: 'fine', value: v, label: v, count: n })))
  return out
})

const PRICE: Record<string, number> = {
  低: 1, 偏低: 2, '中等偏低': 3, 中等: 4, 尚可: 4, '中等偏高': 5, 偏高: 6, 高: 6, 贵: 7,
}

const rows = computed(() => {
  const kw = q.value.trim().toLowerCase()
  let out = all.value.filter((s) => {
    if (active.value.cat && (s.category || '未分类') !== active.value.cat) return false
    if (active.value.fine) {
      const f = s.fine || s.process || '未记工艺'
      if (f !== active.value.fine) return false
    }
    if (!kw) return true
    return [s.name, s.process, s.quality, s.punctual, s.price_level, s.materials, s.notes]
      .filter(Boolean).join(' ').toLowerCase().includes(kw)
  })
  out = [...out].sort((a, b) => {
    if (sortKey.value === 'notes') return (hasNote(b) ? 1 : 0) - (hasNote(a) ? 1 : 0)
    if (sortKey.value === 'name') return a.name.localeCompare(b.name, 'zh')
    return (PRICE[(a.price_level || '').trim()] ?? 99) - (PRICE[(b.price_level || '').trim()] ?? 99)
  })
  return out
})
</script>

<template>
  <ExplorerShell
    kicker="加工与采购"
    title="活找谁做。"
    lead="与部件库同一套交互，但比的是另一件事：加工质量、交货准不准、价格档、能不能开票。数据来自社区整理的实战反馈，不是厂商自述。"
    search-placeholder="搜店名 / 工艺 / 点评关键词"
    :facets="facets"
    :sorts="[{ k: 'price', label: '按价格档' }, { k: 'notes', label: '优先有点评' }, { k: 'name', label: '按名称' }]"
    v-model:sort-key="sortKey"
    v-model:active="active"
    :count="rows.length"
    count-unit="家"
    @update:q="q = $event"
  >
    <template #note>
      质量 / 交期 / 价格 / 发票是<strong>他人实战反馈的转述</strong>，统一标 <code>B</code> 级；
      原表里带学校与姓名的署名已全部去标识。空着就写空着，不用「全能」填空。
    </template>

    <div v-for="s in rows" :key="s.id" class="ex-card">
      <div class="ex-body" style="padding-top:0.75rem">
        <div class="ex-title">
          <a v-if="s.url" :href="s.url" target="_blank" rel="noopener nofollow">{{ s.name }}</a>
          <b v-else>{{ s.name }}</b>
          <em class="ex-tag">{{ s.category || '未分类' }}</em>
          <em v-if="s.fine && s.fine !== s.category" class="ex-tag">{{ s.fine }}</em>
        </div>
        <p class="ex-sub">{{ s.process || '工艺未记' }}</p>
        <dl class="ex-kv">
          <div v-if="s.quality"><dt>质量</dt><dd>{{ s.quality }}</dd></div>
          <div v-if="s.punctual"><dt>交期</dt><dd>{{ s.punctual }}</dd></div>
          <div v-if="s.price_level"><dt>价格</dt><dd>{{ s.price_level }}</dd></div>
          <div v-if="s.invoice"><dt>发票</dt><dd>{{ s.invoice }}</dd></div>
          <div v-if="s.materials"><dt>材料</dt><dd>{{ s.materials }}</dd></div>
          <div v-if="s.lead"><dt>工期</dt><dd>{{ s.lead }}</dd></div>
        </dl>
        <p v-if="hasNote(s)" class="ex-sub" :class="{ 'note-open': expanded === s.id }"
           style="border-left:2px solid var(--vp-c-divider); padding-left:0.55rem; line-height:1.75; cursor:pointer"
           role="button" tabindex="0" :aria-expanded="expanded === s.id" @click="expanded = expanded === s.id ? null : s.id" @keydown.enter.prevent="expanded = expanded === s.id ? null : s.id" @keydown.space.prevent="expanded = expanded === s.id ? null : s.id">
          {{ s.notes }}
        </p>
        <div class="ex-foot">
          <span class="ex-muted" style="font-size:0.7rem">等级 {{ s.tier || '—' }}</span>
          <a v-if="s.url" class="ex-link" :href="s.url" target="_blank" rel="noopener nofollow"
             style="margin-left:auto">店铺 →</a>
        </div>
      </div>
    </div>
  </ExplorerShell>
</template>

<style scoped>
/* 点评默认折叠三行，点开看全文 */
.ex-sub.note-open {
  display: block;
}
.ex-sub:not(.note-open) {
  display: -webkit-box;
  -webkit-line-clamp: 3;
  -webkit-box-orient: vertical;
  overflow: hidden;
}
</style>
