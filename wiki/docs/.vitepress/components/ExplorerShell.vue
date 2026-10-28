<script setup lang="ts">
/**
 * 三类列表共用的外壳：整机 / 部件 / 加工采购。
 *
 * 这三页本质是同一件事 —— 「一堆东西，按维度筛，看卡片，进详情」。
 * 外壳只负责版式与状态，卡片内容由调用方用 slot 决定，
 * 因为「怎么比」三页确实不同（部件比扭矩，整机比负载，加工商比交期）。
 *
 * 样式全在 theme/explorer.css 的 .ex-* 里 —— 改那里，三页一起变。
 */
import { computed, ref } from 'vue'

interface Facet {
  /** 分组键：同一组内互斥 */
  group: string
  value: string
  label: string
  count?: number
}

const props = withDefaults(defineProps<{
  kicker?: string
  title: string
  lead?: string
  note?: string
  searchPlaceholder?: string
  /** 分面：按 group 分行显示，组内单选 */
  facets?: Facet[]
  /** 排序项 */
  sorts?: { k: string; label: string }[]
  sortKey?: string
  count?: number
  countUnit?: string
  /** 没有任何数据时的提示 */
  emptyText?: string
}>(), {
  countUnit: '条',
  emptyText: '没有匹配的结果，换个关键词或点掉筛选。',
})

const emit = defineEmits<{
  (e: 'update:q', v: string): void
  (e: 'update:sortKey', v: string): void
  (e: 'select-facet', payload: { group: string; value: string }): void
}>()

const q = ref('')
const active = defineModel<Record<string, string>>('active', { default: () => ({}) })

/** 按 group 分组，保持传入顺序 */
const groups = computed(() => {
  const m = new Map<string, Facet[]>()
  for (const f of props.facets || []) {
    if (!m.has(f.group)) m.set(f.group, [])
    m.get(f.group)!.push(f)
  }
  return [...m.entries()]
})

function pick(f: Facet) {
  const cur = active.value?.[f.group]
  const next = { ...(active.value || {}) }
  if (cur === f.value) delete next[f.group]
  else next[f.group] = f.value
  active.value = next
  emit('select-facet', { group: f.group, value: f.value === cur ? '' : f.value })
}

function onSearch(e: Event) {
  q.value = (e.target as HTMLInputElement).value
  emit('update:q', q.value)
}
</script>

<template>
  <div class="ex">
    <header class="ex-head">
      <div v-if="kicker" class="ex-kicker">{{ kicker }}</div>
      <h1>{{ title }}</h1>
      <p v-if="lead" class="ex-lead">{{ lead }}</p>
      <div v-if="note" class="ex-note"><slot name="note">{{ note }}</slot></div>
    </header>

    <div class="ex-bar">
      <input class="ex-search" type="search" :placeholder="searchPlaceholder || '搜索'"
             :value="q" @input="onSearch" />
      <slot name="bar" />
      <select v-if="sorts && sorts.length" class="ex-sel"
              :value="sortKey" @change="emit('update:sortKey', ($event.target as HTMLSelectElement).value)">
        <option v-for="s in sorts" :key="s.k" :value="s.k">{{ s.label }}</option>
      </select>
      <span class="ex-count">{{ count ?? 0 }} {{ countUnit }}</span>
    </div>

    <div v-for="[group, items] in groups" :key="group" class="ex-facets">
      <button class="ex-chip" :class="{ on: !active?.[group] }" @click="active = { ...(active || {}), [group]: '' }">
        全部
      </button>
      <button v-for="f in items" :key="group + f.value" class="ex-chip"
              :class="{ on: active?.[group] === f.value, empty: f.count === 0 }"
              @click="pick(f)">
        {{ f.label }}<span v-if="f.count !== undefined" class="n">{{ f.count }}</span>
      </button>
    </div>
    <slot name="facets-extra" />

    <div class="ex-grid">
      <slot />
    </div>
    <p v-if="!count" class="ex-empty">{{ emptyText }}</p>
  </div>
</template>
