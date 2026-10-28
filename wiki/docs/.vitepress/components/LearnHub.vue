<script setup lang="ts">
/**
 * 学习路线首页。
 *
 * 结构：
 *   1. 三条路线（会选型 / 搭得起来 / 进得了仿真）—— 每条是「目标 + 有序步骤」
 *   2. 文章列表 —— 按标签与难度筛
 *   3. 分享与转载 —— 三条底线，单独一页
 *
 * 为什么把路线做成「步骤」而不是「目录」：
 *       新手缺的不是链接集合，而是**顺序**。所以每条路线写明「做完这条你能干什么」，
 *       步骤之间有条件关系，不是并列的阅读清单。
 */
import { computed, onMounted, ref } from 'vue'

interface Step { n: number; text: string; link?: string }
interface Route { id: string; title: string; goal: string; steps: Step[] }
interface Article {
  slug: string; title: string; summary: string
  tags?: string[]; level?: string; minutes?: number
}

const routes = ref<Route[]>([])
const articles = ref<Article[]>([])
const reprint = ref<any>(null)
const tag = ref('')
const level = ref('')

onMounted(async () => {
  const r = await fetch(`${import.meta.env.BASE_URL}learn.json`)
  if (!r.ok) return
  const d = await r.json()
  routes.value = d.routes || []
  articles.value = d.articles || []
  reprint.value = d.reprint || null
})

const allTags = computed(() => {
  const s = new Set<string>()
  for (const a of articles.value) for (const t of a.tags || []) s.add(t)
  return [...s]
})

const shown = computed(() => articles.value.filter((a) => {
  if (tag.value && !(a.tags || []).includes(tag.value)) return false
  if (level.value && a.level !== level.value) return false
  return true
}))
</script>

<template>
  <div class="ex">
    <header class="ex-head">
      <div class="ex-kicker">学习路线</div>
      <h1>从「想做一个机器人」到「能选型、能搭、能进仿真」。</h1>
      <p class="ex-lead">
        这里放三样东西：成体系的路线（有顺序，不是链接堆）、可单独读的文章，以及转载规范。
        所有例子都用部件库里的真型号，数字能回查来源。
      </p>
      <div class="ex-note">
        本站不写「十分钟入门」。一条路线一个目标：读完能做什么，写在每条的标题下面。
      </div>
    </header>

    <!-- 路线 -->
    <section class="lr-routes">
      <div v-for="r in routes" :key="r.id" class="ex-card lr-route">
        <div class="ex-body">
          <div class="ex-title"><b>{{ r.title }}</b></div>
          <p class="ex-sub">{{ r.goal }}</p>
          <ol class="lr-steps">
            <li v-for="s in r.steps" :key="s.n">
              <a v-if="s.link" :href="s.link">{{ s.text }}</a>
              <span v-else>{{ s.text }}</span>
            </li>
          </ol>
        </div>
      </div>
    </section>

    <!-- 文章 -->
    <h2 class="lr-h2">文章</h2>
    <div class="ex-facets">
      <button class="ex-chip" :class="{ on: !tag }" @click="tag = ''">全部</button>
      <button v-for="t in allTags" :key="t" class="ex-chip" :class="{ on: tag === t }" @click="tag = tag === t ? '' : t">
        {{ t }}
      </button>
      <span style="width:0.6rem"></span>
      <button class="ex-chip" :class="{ on: level === '入门' }" @click="level = level === '入门' ? '' : '入门'">入门</button>
      <button class="ex-chip" :class="{ on: level === '进阶' }" @click="level = level === '进阶' ? '' : '进阶'">进阶</button>
    </div>

    <div class="ex-grid">
      <div v-for="a in shown" :key="a.slug" class="ex-card">
        <div class="ex-body">
          <div class="ex-title">
            <a :href="`./learn/${a.slug}.html`">{{ a.title }}</a>
          </div>
          <p class="ex-sub">{{ a.summary }}</p>
          <div class="ex-foot">
            <em v-if="a.level" class="ex-tag">{{ a.level }}</em>
            <em v-for="t in a.tags || []" :key="t" class="ex-tag">{{ t }}</em>
            <span class="ex-muted" style="margin-left:auto; font-size:0.7rem">约 {{ a.minutes }} 分钟</span>
          </div>
        </div>
      </div>
    </div>
    <p v-if="!shown.length" class="ex-empty">这个筛选下还没有文章。</p>

    <!-- 转载 -->
    <section v-if="reprint" class="lr-reprint">
      <h2 class="lr-h2">{{ reprint.title }}</h2>
      <p class="ex-lead">{{ reprint.summary }}</p>
      <ul class="lr-rules">
        <li v-for="(r, i) in reprint.rules" :key="i">{{ r }}</li>
      </ul>
      <p class="ex-sub"><a class="ex-link" :href="reprint.link">完整转载与引用规范 →</a></p>
    </section>
  </div>
</template>

<style scoped>
.lr-routes {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: 0.7rem;
  margin: 0.4rem 0 1.6rem;
}
.lr-route .ex-sub { line-height: 1.8; }
.lr-steps {
  margin: 0.45rem 0 0;
  padding-left: 1.3rem;
  list-style: decimal;
  font-size: 0.78rem;
  line-height: 1.95;
  color: var(--vp-c-text-2);
}
.lr-steps li { padding-left: 0.15rem; }
.lr-steps a { color: var(--vp-c-text-2); text-decoration: none; border-bottom: 1px dashed var(--vp-c-divider); }
.lr-steps a:hover { color: var(--vp-c-brand-1); border-bottom-color: var(--vp-c-brand-1); }
.lr-h2 {
  font-size: 1.05rem;
  font-weight: 700;
  margin: 1.8rem 0 0.5rem;
  border: none;
  padding: 0;
  color: var(--vp-c-text-1);
}
.lr-reprint {
  margin-top: 2rem;
  padding-top: 1.2rem;
  border-top: 1px solid var(--vp-c-divider);
}
.lr-rules {
  margin: 0.5rem 0 0.6rem;
  padding-left: 1.15rem;
  font-size: 0.82rem;
  line-height: 1.95;
  color: var(--vp-c-text-2);
}
</style>
