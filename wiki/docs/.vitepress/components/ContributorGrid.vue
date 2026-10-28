<script setup lang="ts">
/**
 * 贡献者页（版式参考 LocoWiki 的 contributors 页）。
 *
 * 结构：
 *   4 个统计卡（贡献者总数 / 累计贡献次数 / 数据来源 / 快照更新时间）
 *   + 按贡献次数降序的头像卡网格
 *
 * 为什么是「快照」而不是实时请求：
 *   匿名调 GitHub API 每小时只有 60 次，首屏还要多一次网络往返。
 *   快照随构建产物一起发，页面上标明抓取时间 —— 数字有出处，才敢展示。
 */
import { computed, onMounted, ref } from 'vue'

interface Person { login: string; avatar: string | null; url: string | null; contributions: number; bot: boolean; role?: string }
interface Snap {
  repo: string; source: string; updated_at: string
  total: number; total_contributions: number; contributors: Person[]
}

const props = withDefaults(defineProps<{ lang?: 'zh' | 'en' }>(), { lang: 'zh' })
const en = computed(() => props.lang === 'en')

const snap = ref<Snap | null>(null)

onMounted(async () => {
  const r = await fetch(`${import.meta.env.BASE_URL}contributors.json`)
  if (r.ok) snap.value = await r.json()
})

const L = computed(() => en.value
  ? { total: 'Contributors', times: 'Total contributions', src: 'Data source',
      upd: 'Snapshot time', list: 'Contributors', by: 'Sorted by contribution count',
      times_n: 'contributions', maintainer: 'Maintainer', bot: 'Bot',
      empty: 'No snapshot yet — run python tools/fetch_contributors.py' }
  : { total: '贡献者总数', times: '累计贡献次数', src: '数据来源',
      upd: '快照更新时间', list: '贡献者', by: '按贡献次数排序展示',
      times_n: '次贡献', maintainer: '维护者', bot: 'Bot',
      empty: '还没有快照 —— 跑 python tools/fetch_contributors.py' })

const people = computed(() => snap.value?.contributors ?? [])
</script>

<template>
  <div class="cw">
    <p v-if="!snap" class="cw-empty">{{ L.empty }}</p>
    <template v-else>
      <div class="cw-stats">
        <div class="cw-stat"><span>{{ L.total }}</span><b>{{ snap.total }}</b></div>
        <div class="cw-stat"><span>{{ L.times }}</span><b>{{ snap.total_contributions }}</b></div>
        <div class="cw-stat">
          <span>{{ L.src }}</span>
          <a :href="`https://github.com/${snap.repo}/graphs/contributors`" target="_blank" rel="noopener">GitHub Contributors</a>
        </div>
        <div class="cw-stat"><span>{{ L.upd }}</span><b class="mono">{{ snap.updated_at }}</b></div>
      </div>

      <section class="cw-list">
        <header>
          <h2>{{ L.list }}</h2>
          <p>{{ L.by }}</p>
        </header>
        <div class="cw-grid">
          <a v-for="(p, i) in people" :key="p.login" class="cw-card"
             :href="p.url || `https://github.com/${p.login}`" target="_blank" rel="noopener noreferrer">
            <img v-if="p.avatar" class="cw-ava" :src="p.avatar" :alt="p.login" loading="lazy" decoding="async" />
            <div class="cw-txt">
              <div class="cw-login">{{ p.login }}</div>
              <div class="cw-meta">
                <span>{{ p.contributions }} {{ L.times_n }}</span>
                <em v-if="p.role">{{ p.role }}</em>
                <em v-else-if="i === 0 && !p.bot">{{ L.maintainer }}</em>
                <em v-if="p.bot" class="bot">{{ L.bot }}</em>
              </div>
            </div>
          </a>
        </div>
      </section>
    </template>
  </div>
</template>

<style scoped>
.cw { max-width: 900px; margin: 0 auto; padding: 0.4rem 0 3rem; }
.cw-empty { font-size: 0.84rem; color: var(--vp-c-text-3); }
.cw-stats { display: grid; grid-template-columns: repeat(auto-fit, minmax(210px, 1fr));
  gap: 0.7rem; margin: 1.2rem 0 1.6rem; }
.cw-stat { border: 1px solid var(--vp-c-divider); border-radius: 12px; padding: 0.8rem 0.95rem;
  display: flex; flex-direction: column; gap: 0.35rem; background: var(--vp-c-bg); }
.cw-stat span { font-size: 0.72rem; color: var(--vp-c-text-3); }
.cw-stat b { font-size: 1.45rem; font-weight: 800; letter-spacing: -0.02em; color: var(--vp-c-text-1); }
.cw-stat b.mono { font-size: 0.92rem; font-weight: 600; }
.cw-stat a { font-size: 0.9rem; font-weight: 700; color: var(--vp-c-brand-1); }
.cw-list { border: 1px solid var(--vp-c-divider); border-radius: 14px; padding: 1rem 1.1rem 1.2rem; }
.cw-list header h2 { font-size: 0.95rem; font-weight: 700; margin: 0 0 0.25rem; border: none; padding: 0; color: var(--vp-c-text-1); }
.cw-list header p { margin: 0 0 0.9rem; font-size: 0.76rem; color: var(--vp-c-text-3); }
.cw-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(260px, 1fr)); gap: 0.55rem; }
.cw-card { display: flex; align-items: center; gap: 0.7rem; padding: 0.6rem 0.7rem;
  border: 1px solid var(--vp-c-divider); border-radius: 10px; background: var(--vp-c-bg);
  transition: border-color 0.15s, background 0.15s; }
.cw-card:hover { border-color: var(--vp-c-brand-1); background: var(--vp-c-brand-soft); }
.cw-ava { width: 40px; height: 40px; border-radius: 9px; object-fit: cover; flex: none; background: var(--vp-c-default-soft); }
.cw-login { font-size: 0.86rem; font-weight: 700; color: var(--vp-c-brand-1); line-height: 1.3; }
.cw-meta { display: flex; align-items: center; gap: 0.4rem; font-size: 0.72rem; color: var(--vp-c-text-3); margin-top: 0.15rem; }
.cw-meta em { font-style: normal; font-size: 0.64rem; padding: 0 5px; border-radius: 999px;
  background: var(--vp-c-brand-soft); color: var(--vp-c-brand-1); }
.cw-meta em.bot { background: var(--vp-c-default-soft); color: var(--vp-c-text-3); }
</style>
