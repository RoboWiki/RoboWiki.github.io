<script setup lang="ts">
/**
 * 零件评分卡：星标汇总 + 分布 + 打分入口。
 *
 * **只有一个打分入口**：GitHub issue 表单。
 *   为什么不给自建打分：那要读者再注册一次账号，而他们本来都有 GitHub。
 *   为什么不用 Discussions 投票：原生 1–5 是好事，但**创建投票只能手点**
 *   （GraphQL 的 createDiscussion 至今不支持 poll），46 个部件没法维护。
 *   Issue Forms 正好：GitHub 身份天然可信、表单结构化、Actions 能自动聚合、
 *   每条评分都能查到作者和依据，也能被维护者关掉。
 *
 * 数据读取三级降级：
 *   1. `GET /api/ratings/{id}` —— 有后端的部署读实时值
 *   2. `ratings.json` —— Actions 从 issue 聚合出来的快照（静态部署用）
 *   3. 都没有 → 「暂无评分」；**不显示 0 分**（0 分是差评，没评不是）
 */
import { computed, onMounted, ref } from 'vue'
import { withBase } from 'vitepress'

interface Summary {
  count: number
  avg: number | null
  histogram: Record<string, number>
  own_hardware_count: number
}

const props = defineProps<{ partId: string }>()

const s = ref<Summary>({
  count: 0, avg: null,
  histogram: { '1': 0, '2': 0, '3': 0, '4': 0, '5': 0 },
  own_hardware_count: 0,
})
const source = ref<'live' | 'snapshot' | 'none'>('none')

/** 打分入口：把部件 id 塞进标题，用户不用手填；表单里也有输入框兜底 */
const ghUrl = computed(() => {
  const title = encodeURIComponent(`[评分] ${props.partId}`)
  return 'https://github.com/RoboWiki/RoboWiki.github.io/issues/new'
    + `?template=rate-part.yml&title=${title}&labels=rating`
})
const ghIssues = 'https://github.com/RoboWiki/RoboWiki.github.io/issues?q=label%3Arating'

const bars = computed(() => {
  const total = s.value.count || 1
  return [5, 4, 3, 2, 1].map(n => ({
    n,
    c: s.value.histogram[String(n)] || 0,
    pct: Math.round(((s.value.histogram[String(n)] || 0) / total) * 100),
  }))
})

async function load() {
  // 1) 构建快照（静态部署唯一来源）
  try {
    const r = await fetch(withBase('/ratings.json'))
    if (r.ok) {
      const one = (await r.json()).parts?.[props.partId]
      if (one) {
        s.value = { count: one.count, avg: one.avg, histogram: one.histogram,
                    own_hardware_count: one.own_hardware_count }
        source.value = 'snapshot'
      }
    }
  } catch { /* 没有快照就继续往下 */ }

  // 2) 有后端就用实时值覆盖（更及时）
  try {
    const r = await fetch(`/api/ratings/${encodeURIComponent(props.partId)}`)
    if (r.ok && (r.headers.get('content-type') || '').includes('json')) {
      const d = await r.json()
      s.value = { count: d.count, avg: d.avg, histogram: d.histogram,
                  own_hardware_count: d.own_hardware_count }
      source.value = 'live'
    }
  } catch { /* 静态部署：保持快照 */ }
}

onMounted(load)
</script>

<template>
  <div class="rt">
    <div class="rt-head">
      <span class="rt-title">实际使用</span>
      <span v-if="!s.count" class="rt-none">暂无评分</span>
      <span v-else-if="source === 'snapshot'" class="rt-tag">快照</span>
    </div>

    <!-- 汇总 -->
    <div class="rt-sum">
      <div class="rt-avg">
        <span class="rt-avg-n">{{ s.avg == null ? '—' : s.avg.toFixed(1) }}</span>
        <span class="rt-avg-s">{{ s.count }} 人打分</span>
      </div>
      <div class="rt-bars">
        <div v-for="b in bars" :key="b.n" class="rt-bar-row">
          <span class="rt-bar-k">{{ b.n }}</span>
          <span class="rt-bar-track"><span class="rt-bar-fill" :style="{ width: b.pct + '%' }" /></span>
          <span class="rt-bar-c">{{ b.c }}</span>
        </div>
      </div>
    </div>

    <p v-if="s.count" class="rt-meta">
      其中 {{ s.own_hardware_count }} 人<strong>装过机</strong>。
      只看均分会把「5 人 5 分」和「1 人 5 分 + 4 人 1 分」看成一样，所以分布也放出来。
    </p>
    <p v-else class="rt-meta">
      还没有人打分。第一条评分由你来写 —— 有实测最好，没有实测也可以打，但请如实勾选。
    </p>

    <!-- 唯一打分入口 -->
    <div class="rt-gh">
      <a class="rt-btn" :href="ghUrl" target="_blank" rel="noopener">去 GitHub 打分</a>
      <a class="rt-gh-link" :href="ghIssues" target="_blank" rel="noopener">看所有评分 →</a>
    </div>

    <p class="rt-hint">
      打分是在 GitHub 上开一条 <strong>issue</strong>（表单，30 秒）：
      需要 GitHub 账号，<strong>一人一件一票</strong>（唯一键 = 你的账号 + 部件 id），
      改主意直接编辑那条 issue。汇总由 Actions 自动跑，所以分数随提交更新 ——
      不是实时，但每一条都能查到是谁、凭什么。
    </p>

    <p class="rt-hint">
      <strong>想写长一点的实测</strong>就写在下方的评论里（GitHub Discussions）。
      评分用来排序，评论用来讲清楚为什么。
    </p>

    <a class="rt-jump" href="#这一页的讨论">去写评论 ↓</a>
  </div>
</template>

<style scoped>
.rt { font-size: 0.8rem; }
.rt-head { display: flex; align-items: center; gap: 0.4rem; margin-bottom: 0.55rem; }
.rt-title { font-weight: 700; font-size: 0.82rem; color: var(--vp-c-text-2); }
.rt-none {
  font-size: 0.7rem; color: var(--vp-c-text-3);
  border: 1px dashed var(--vp-c-divider); border-radius: 999px; padding: 1px 7px;
}
.rt-tag {
  font-size: 0.66rem; color: var(--vp-c-text-3);
  border: 1px solid var(--vp-c-divider); border-radius: 999px; padding: 0 6px;
}

.rt-sum {
  display: grid; grid-template-columns: 5.5rem minmax(0, 1fr); gap: 0.7rem;
  align-items: center; padding-bottom: 0.6rem; border-bottom: 1px solid var(--vp-c-divider);
}
.rt-avg { display: flex; flex-direction: column; }
.rt-avg-n {
  font-size: 1.7rem; font-weight: 700; line-height: 1.1;
  color: var(--vp-c-text-1); font-variant-numeric: tabular-nums;
}
.rt-avg-s { font-size: 0.7rem; color: var(--vp-c-text-3); }

.rt-bars { display: flex; flex-direction: column; gap: 2px; }
.rt-bar-row {
  display: grid; grid-template-columns: 0.8rem minmax(0, 1fr) 1.4rem;
  gap: 0.35rem; align-items: center; font-size: 0.68rem; color: var(--vp-c-text-3);
}
.rt-bar-track { height: 6px; border-radius: 3px; background: var(--vp-c-default-soft);
  overflow: hidden; }
.rt-bar-fill { display: block; height: 100%; border-radius: 3px;
  background: var(--vp-c-brand-1); }
.rt-bar-c { text-align: right; font-variant-numeric: tabular-nums; }

.rt-meta { font-size: 0.72rem; color: var(--vp-c-text-3); line-height: 1.7;
  margin: 0.5rem 0; }

.rt-gh {
  display: flex; align-items: center; gap: 0.6rem; margin-top: 0.55rem;
  padding-top: 0.55rem; border-top: 1px solid var(--vp-c-divider);
}
.rt-btn {
  font-size: 0.76rem; font-weight: 600; padding: 0.32rem 0.8rem;
  border-radius: 999px; border: 1px solid var(--vp-c-brand-1);
  background: var(--vp-c-brand-1); color: #fff; text-decoration: none;
  display: inline-block;
}
.rt-btn:hover { text-decoration: none; opacity: 0.9; }
.rt-gh-link { font-size: 0.72rem; color: var(--vp-c-brand-1); }

.rt-hint { font-size: 0.72rem; color: var(--vp-c-text-3); line-height: 1.7;
  margin: 0.55rem 0 0; }
.rt-jump { display: inline-block; margin-top: 0.4rem; font-size: 0.74rem;
  font-weight: 600; color: var(--vp-c-brand-1); }
</style>
