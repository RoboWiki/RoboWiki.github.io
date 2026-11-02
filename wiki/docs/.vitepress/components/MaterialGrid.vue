<script setup lang="ts">
/**
 * 竞赛模块的「现有材料」卡片组。
 *
 * 之前是三列表格（材料 / 讲什么 / 什么时候读），长描述会把表格撑出横向滚动条。
 * 改成和软件库一致的卡片：标题 + 标签 + 讲什么 + 什么时候读 + 阅读入口。
 */
interface Item {
  title: string
  href: string
  meta?: string
  tags?: string[]
  what: string
  when: string
}

withDefaults(defineProps<{ items: Item[]; whenLabel?: string }>(), {
  whenLabel: '什么时候读',
})
</script>

<template>
  <div class="mat-grid">
    <a
      v-for="x in items"
      :key="x.href"
      class="mat-card"
      :href="x.href"
      :target="x.href.startsWith('http') ? '_blank' : undefined"
      :rel="x.href.startsWith('http') ? 'noopener' : undefined"
    >
      <div class="mat-head">
        <b>{{ x.title }}</b>
        <em v-if="x.meta">{{ x.meta }}</em>
      </div>
      <div v-if="x.tags?.length" class="mat-chips">
        <span v-for="t in x.tags" :key="t" class="mat-chip">{{ t }}</span>
      </div>
      <p class="mat-what">{{ x.what }}</p>
      <p class="mat-when"><b>{{ whenLabel }}</b>{{ x.when }}</p>
      <span class="mat-more">{{ x.href.startsWith('http') ? '打开原文 ↗' : '阅读全文 →' }}</span>
    </a>
  </div>
</template>

<style scoped>
.mat-grid {
  display: grid;
  gap: 0.8rem;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  margin: 0.9rem 0 1.4rem;
}
.mat-card {
  display: flex;
  flex-direction: column;
  gap: 0.45rem;
  border: 1px solid var(--vp-c-divider);
  border-radius: 12px;
  padding: 0.95rem 1rem;
  background: var(--vp-c-bg-soft);
  text-decoration: none;
  transition: border-color 0.15s;
}
.mat-card:hover { border-color: var(--vp-c-brand-1); text-decoration: none; }
.mat-head { display: flex; align-items: baseline; gap: 0.45rem; flex-wrap: wrap; }
.mat-head b { font-size: 1rem; line-height: 1.4; color: var(--vp-c-text-1); }
.mat-head em { font-style: normal; font-size: 0.74rem; color: var(--vp-c-text-3); }
.mat-chips { display: flex; flex-wrap: wrap; gap: 0.3rem; }
.mat-chip {
  font-size: 0.72rem;
  padding: 0.1rem 0.45rem;
  border-radius: 999px;
  border: 1px solid var(--vp-c-divider);
  color: var(--vp-c-text-3);
}
.mat-what { margin: 0; font-size: 0.86rem; line-height: 1.65; color: var(--vp-c-text-1); }
.mat-when { margin: 0; font-size: 0.82rem; line-height: 1.65; color: var(--vp-c-text-2); }
.mat-when b { color: var(--vp-c-text-1); margin-right: 0.35rem; }
.mat-more { margin-top: auto; padding-top: 0.35rem; font-size: 0.8rem; font-weight: 600; color: var(--vp-c-brand-1); }
</style>
