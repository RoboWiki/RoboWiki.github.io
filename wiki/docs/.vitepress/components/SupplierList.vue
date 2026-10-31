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
  url?: string | null; has_url?: boolean; category?: string | null; fine?: string | null
  listing?: '红榜' | '黑榜' | null; reason?: string | null; grade?: string | null
  channel?: string | null; reported_at?: string | null
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
  // 榜单放在最上面：红黑榜是这个板块的核心信息，不该埋进品类里
  const board = new Map<string, number>()
  for (const s of all.value) if (s.listing) board.set(s.listing, (board.get(s.listing) || 0) + 1)
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
  const out = [...board.entries()].sort((a, b) => b[1] - a[1])
    .map(([v, n]) => ({ group: 'board', value: v, label: v, count: n }))
  out.push(...[...cat.entries()].sort((a, b) => b[1] - a[1])
    .map(([v, n]) => ({ group: 'cat', value: v, label: v, count: n })))
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
    if (active.value.board && s.listing !== active.value.board) return false
    if (active.value.cat && (s.category || '未分类') !== active.value.cat) return false
    if (active.value.fine) {
      const f = s.fine || s.process || '未记工艺'
      if (f !== active.value.fine) return false
    }
    if (!kw) return true
    return [s.name, s.process, s.quality, s.punctual, s.price_level, s.materials, s.notes]
      .filter(Boolean).join(' ').toLowerCase().includes(kw)
  })
  const BOARD: Record<string, number> = { 黑榜: 0, 红榜: 1 }
  out = [...out].sort((a, b) => {
    if (sortKey.value === 'board')
      return (BOARD[a.listing || ''] ?? 9) - (BOARD[b.listing || ''] ?? 9)
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
    :sorts="[{ k: 'board', label: '红黑榜优先' }, { k: 'price', label: '按价格档' }, { k: 'notes', label: '优先有点评' }, { k: 'name', label: '按名称' }]"
    v-model:sort-key="sortKey"
    v-model:active="active"
    :count="rows.length"
    count-unit="家"
    @update:q="q = $event"
  >
    <template #note>
      来源两张社区表：加工/材料的「供应商名录」与元件电商的「红黑榜」。
      <strong>红黑榜是这一页最硬的信息</strong>：黑榜 26 家按「问题类型」看（假货 / 翻新 / 混卖），
      红榜 32 家按「凭什么推荐」看。「榜单」筛选可直接单挑一类。
      <strong>已脱敏的是爆料人</strong>：填写人、掌柜 ID、店铺链接（带 spm 与 user_number_id 可反查个人）、
      「学校 + 姓名」署名、联系方式一律去掉，日期只到月 —— 商家名与问题描述保持原样，不软化。
      等级：加工/材料 <code>B</code>，单条社区反馈 <code>C</code>（当线索看）。
    </template>

    <div v-for="s in rows" :key="s.id" class="ex-card"
         :class="{ 'is-black': s.listing === '黑榜', 'is-red': s.listing === '红榜' }">
      <div class="ex-body" style="padding-top:0.75rem">
        <div class="ex-title">
          <b>{{ s.name }}</b>
          <em v-if="s.listing" class="ex-tag" :class="s.listing === '黑榜' ? 'tag-bad' : 'tag-good'">{{ s.listing }}</em>
          <em class="ex-tag">{{ s.category || '未分类' }}</em>
          <em v-if="s.fine && s.fine !== s.category" class="ex-tag">{{ s.fine }}</em>
        </div>
        <p class="ex-sub">{{ s.process || '工艺未记' }}</p>
        <p v-if="s.reason" class="ex-sub" style="color:var(--vp-c-text-1)">
          <b>上榜原因</b>：{{ s.reason }}
        </p>
        <dl class="ex-kv">
          <template v-if="s.kind === 'component_shop'">
            <div v-if="s.grade"><dt>成色</dt><dd>{{ s.grade }}</dd></div>
            <div v-if="s.fine"><dt>主营</dt><dd>{{ s.fine }}</dd></div>
            <div v-if="s.channel"><dt>渠道</dt><dd>{{ s.channel }}</dd></div>
            <div v-if="s.reported_at"><dt>收录</dt><dd>{{ s.reported_at }}</dd></div>
          </template>
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
          <span v-if="s.has_url" class="ex-muted" style="margin-left:auto;font-size:0.7rem"
                title="为避免引流与反查，本站不收录店铺链接；需要时请自行按店名搜索">
            有店铺可搜（不收录链接）
          </span>
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

/* 黑榜：左红边 + 淡红底，扫一眼就能挑出来；红榜：淡品牌色底 */
.ex-card.is-black {
  border-left: 3px solid #dc2626;
  background: color-mix(in srgb, #dc2626 4%, var(--vp-c-bg-soft));
}
.ex-card.is-red {
  border-left: 3px solid var(--vp-c-brand-1);
}
/* 红黑榜徽标：黑榜琥珀色（警示，不刺眼），红榜品牌色（推荐） */
.ex-tag.tag-bad { color: #b45309; border-color: #d97706; font-weight: 600; }
.ex-tag.tag-good { color: var(--vp-c-brand-1); border-color: var(--vp-c-brand-2); font-weight: 600; }
</style>
