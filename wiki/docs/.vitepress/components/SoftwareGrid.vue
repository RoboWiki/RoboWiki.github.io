<script setup lang="ts">
/**
 * 机器人软件列表（统一外壳版）。
 *
 * 之前这页是一张手写 markdown 长页 —— 和站点其它列表不是一个视觉语言，也没法筛。
 * 现在走 ExplorerShell：五层当分面，卡片只答三件事（是什么 / 什么时候用 / 许可与版本）。
 *
 * 数据：public/software.json（pipeline/build_software.py 生成）
 */
import { computed, onMounted, ref } from 'vue'
import ExplorerShell from './ExplorerShell.vue'

interface Item {
  id: string; group: string; name: string; vendor: string
  license: string | null; version: string | null
  repo?: string | null; docs?: string | null; lang?: string | null
  repo_note?: string; concept?: boolean
  what: string; when: string; note?: string
}

interface Group { id: string; name: string; hint?: string }

const items = ref<Item[]>([])
const groups = ref<Group[]>([])
const q = ref('')
const sortKey = ref('group')
const active = ref<Record<string, string>>({})

onMounted(async () => {
  const r = await fetch(`${import.meta.env.BASE_URL}software.json`)
  if (!r.ok) return
  const d = await r.json()
  items.value = d.items || []
  groups.value = d.groups || []
})

const GNAME = computed(() => {
  const m: Record<string, string> = {}
  for (const g of groups.value) m[g.id] = g.name
  return m
})

/** 许可的「宽松度」：商用友好排前面。未知单独一档，不假装它宽松。 */
function licRank(l: string | null): number {
  if (!l) return 2
  if (/Apache|MIT|BSD/.test(l)) return 0
  if (/GPL|AGPL|MPL/.test(l)) return 1
  return 2
}

const facets = computed(() =>
  groups.value.map((g) => ({
    group: 'layer', value: g.id, label: g.name,
    count: items.value.filter((x) => x.group === g.id).length,
  })),
)

const rows = computed(() => {
  const kw = q.value.trim().toLowerCase()
  const layer = active.value.layer
  let out = items.value.filter((x) => {
    if (layer && x.group !== layer) return false
    if (!kw) return true
    return [x.name, x.vendor, x.what, x.when, x.lang, x.license]
      .filter(Boolean).join(' ').toLowerCase().includes(kw)
  })
  const order = groups.value.map((g) => g.id)
  out = [...out].sort((a, b) => {
    if (sortKey.value === 'name') return a.name.localeCompare(b.name, 'en')
    if (sortKey.value === 'license') {
      const d = licRank(a.license) - licRank(b.license)
      return d !== 0 ? d : a.name.localeCompare(b.name, 'en')
    }
    if (sortKey.value === 'version') {
      const av = a.version ? 1 : 0
      const bv = b.version ? 1 : 0
      return bv - av || a.name.localeCompare(b.name, 'en')
    }
    const d = order.indexOf(a.group) - order.indexOf(b.group)
    return d !== 0 ? d : a.name.localeCompare(b.name, 'en')
  })
  return out
})

const licText = (x: Item) => x.license || '未核对'
const licTone = (x: Item) =>
  x.license ? (/GPL|AGPL|MPL/.test(x.license) ? 'copyleft' : 'permissive') : 'unknown'
const verText = (x: Item) => (x.version ? `v${x.version}` : '版本未核对')
const hasLink = (x: Item) => !!x.repo && x.repo.replace(/\/+$/, '') !== 'https://github.com'
</script>

<template>
  <ExplorerShell
    kicker="机器人软件"
    title="从仿真、训练到架构与部署 —— 每一层都决定策略能不能落地。"
    lead="按层、算法与模型架构给「是什么、什么时候该用它、许可与版本」。不做项目大全：清单会漂，判断不会。许可读不到就写「未核对」，这一栏写错比空着糟。"
    search-placeholder="搜名字 / 厂商 / 用途 / 许可"
    :facets="facets"
    :sorts="[
      { k: 'group', label: '按分组' },
      { k: 'name', label: '按名称' },
      { k: 'license', label: '按许可宽松度' },
      { k: 'version', label: '按版本可查' },
    ]"
    v-model:sort-key="sortKey"
    v-model:active="active"
    :count="rows.length"
    count-unit="个"
    @update:q="q = $event"
  >
    <template #note>
      许可与版本取自本地仓库的 LICENSE / pyproject（2026-10-29）；
      <b>标「未核对」的是我们没读到</b>，不是它没有；MLP / MoE 是通用架构，PPO / AMP 是通用算法与方法，都不按单一项目计许可与版本。
    </template>

    <template v-for="x in rows" :key="x.id">
      <article class="ex-card sw-card">
        <div class="sw-head">
          <b>{{ x.name }}</b>
          <em>{{ x.vendor }}</em>
        </div>
        <div class="sw-chips">
          <span class="sw-chip dim">{{ GNAME[x.group] || x.group }}</span>
          <span v-if="x.concept" class="sw-chip dim">{{ x.group === 'method' ? '通用方法' : '架构概念' }}</span>
          <template v-else>
            <span class="sw-chip" :class="licTone(x)">{{ licText(x) }}</span>
            <span class="sw-chip" :class="{ dim: !x.version }">{{ verText(x) }}</span>
          </template>
          <span v-if="x.lang" class="sw-chip dim">{{ x.lang }}</span>
        </div>
        <p class="sw-what">{{ x.what }}</p>
        <p class="sw-when"><b>什么时候用</b>{{ x.when }}</p>
        <p v-if="x.note" class="sw-note">{{ x.note }}</p>
        <div class="sw-foot">
          <a v-if="hasLink(x)" :href="x.repo" target="_blank" rel="noopener">仓库</a>
          <span v-else-if="x.repo_note" class="sw-todo">{{ x.repo_note }}</span>
          <span v-else class="sw-todo">仓库待核</span>
          <a v-if="x.docs" :href="x.docs" target="_blank" rel="noopener">文档</a>
        </div>
      </article>
    </template>
  </ExplorerShell>
</template>

<style scoped>
/* 卡片外框与栅格交给 .ex-grid / .ex-card（整站一致），这里只管内部排版 */
.sw-card { display: flex; flex-direction: column; gap: 0.45rem; }
.sw-head { display: flex; align-items: baseline; gap: 0.45rem; flex-wrap: wrap; }
.sw-head b { font-size: 1.02rem; }
.sw-head em { font-style: normal; font-size: 0.78rem; color: var(--vp-c-text-3); }
.sw-layer {
  margin-left: auto; font-size: 0.72rem; color: var(--vp-c-text-3);
  border: 1px solid var(--vp-c-divider); border-radius: 999px; padding: 0.05rem 0.45rem;
}
.sw-chips { display: flex; flex-wrap: wrap; gap: 0.3rem; }
.sw-chip {
  font-size: 0.72rem; padding: 0.1rem 0.45rem; border-radius: 999px;
  border: 1px solid var(--vp-c-divider); color: var(--vp-c-text-2);
}
.sw-chip.permissive { color: var(--vp-c-brand-1); border-color: var(--vp-c-brand-2); }
.sw-chip.copyleft { color: var(--rw-accent-1); border-color: var(--rw-accent-1); }
.sw-chip.unknown { color: var(--vp-c-text-3); border-style: dashed; }
.sw-chip.dim { color: var(--vp-c-text-3); }
.sw-what { margin: 0; font-size: 0.88rem; line-height: 1.6; }
.sw-when { margin: 0; font-size: 0.84rem; line-height: 1.6; color: var(--vp-c-text-2); }
.sw-when b { color: var(--vp-c-text-1); margin-right: 0.35rem; }
.sw-note { margin: 0; font-size: 0.78rem; line-height: 1.55; color: var(--vp-c-text-3); }
.sw-foot { margin-top: auto; padding-top: 0.35rem; font-size: 0.82rem; display: flex; gap: 0.7rem; }
.sw-foot a { color: var(--vp-c-brand-1); text-decoration: none; }
.sw-foot a:hover { text-decoration: underline; }
.sw-todo { color: var(--vp-c-text-3); }
</style>
