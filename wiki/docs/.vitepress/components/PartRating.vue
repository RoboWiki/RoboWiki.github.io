<script setup lang="ts">
/**
 * 实际使用评分卡 v2。
 *
 * 改了什么（对比 v1 只有一个总分）：
 *   1. **四维分数**：参数可信度 / 做工 / 文档与支持 / 性价比 —— 总分说不清哪里好
 *   2. **样本量直说**：n < 3 显示「样本不足」，不给一个看起来很确定的均分
 *   3. **装过机的单独均分**：这是最有参考价值的那个数，单独摆出来
 *   4. **使用工况**：用了多久、什么负载、什么批量 —— 决定这条评价对你有不有用
 *   5. **分布图**：「5 人 5 分」和「1 人 5 分 + 4 人 1 分」不能只看均分
 *
 * 打分入口仍然只有一个：GitHub issue 表单。
 *   读者本来就有 GitHub 账号，为打分再注册一次是不必要的门槛；
 *   Issue Forms 还自带身份可信、结构化、Actions 可聚合、可被维护者关闭。
 *   一人一件一票：唯一键 = issue 作者 + 部件 id，改主意就编辑原 issue。
 *
 * 数据降级：后端实时值 → 构建快照 → 「暂无评分」（绝不当成 0 分）。
 */
import { computed, onMounted, ref } from 'vue'
import { withBase } from 'vitepress'

interface Dims { spec_trust?: number; build?: number; docs?: number; value?: number; compat?: number }

interface Summary {
  count: number
  avg: number | null
  histogram: Record<string, number>
  own_hardware_count: number
  own_hardware_avg?: number | null
  dims_avg?: Dims | null
  dims_n?: Record<string, number> | null
  usage_count?: Record<string, Record<string, number>> | null
  low_sample?: boolean
}

const props = defineProps<{
  partId: string
  /** 该品类关心的维度，来自 taxonomy 的 rating_dims（build 时传入） */
  dims?: string[]
}>()

const empty: Summary = {
  count: 0, avg: null,
  histogram: { '1': 0, '2': 0, '3': 0, '4': 0, '5': 0 },
  own_hardware_count: 0,
}
const s = ref<Summary>({ ...empty })
const source = ref<'live' | 'snapshot' | 'none'>('none')

/** 全部可能的维度；具体渲染哪些由 props.dims 决定 */
const DIM_ALL: Record<string, { label: string; hint: string }> = {
  value: { label: '性价比', hint: '同等能力下贵不贵' },
  build: { label: '做工', hint: '外壳、端子、背隙、装配一致性' },
  docs: { label: '文档与支持', hint: '手册、SDK、固件、厂家回复' },
  spec_trust: { label: '参数可信度', hint: '标称数字与实际是否对得上' },
  compat: { label: '兼容与生态', hint: '驱动、固件、社区资料好不好接' },
}

const USAGE_LABEL: Record<string, Record<string, string>> = {
  duration: { '<1个月': '<1 月', '1-3个月': '1–3 月', '3-12个月': '3–12 月', '>1年': '>1 年' },
  load: { 轻载测试: '轻载', 常规: '常规', 满载连续: '满载连续' },
  batch: { 单件样机: '单件', 小批量: '小批量', 量产: '量产' },
}

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

const dims = computed(() => {
  const want = props.dims?.length ? props.dims : Object.keys(DIM_ALL)
  return want
    .filter(k => DIM_ALL[k])
    .map(k => ({
      key: k,
      ...DIM_ALL[k],
      v: (s.value.dims_avg as any)?.[k] ?? null,
      n: (s.value.dims_n as any)?.[k] ?? 0,
    }))
    .filter(d => d.v != null)
})

const usageRows = computed(() => {
  const uc = s.value.usage_count || {}
  return (['duration', 'load', 'batch'] as const)
    .filter(k => uc[k])
    .map(k => ({
      key: k,
      label: k === 'duration' ? '用了多久' : k === 'load' ? '负载' : '批量',
      items: Object.entries(uc[k]).map(([v, c]) => ({
        text: USAGE_LABEL[k][v] || v, c,
      })),
    }))
})

async function load() {
  try {
    const r = await fetch(withBase('/ratings.json'))
    if (r.ok) {
      const one = (await r.json()).parts?.[props.partId]
      if (one) {
        s.value = { ...empty, ...one }
        source.value = 'snapshot'
      }
    }
  } catch { /* 没有快照就继续 */ }

  try {
    const r = await fetch(`/api/ratings/${encodeURIComponent(props.partId)}`)
    if (r.ok && (r.headers.get('content-type') || '').includes('json')) {
      const d = await r.json()
      s.value = { ...empty, ...d }
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
      <span v-else-if="s.low_sample" class="rt-warn" title="样本少于 3 条时不显示确定结论">样本不足</span>
      <span v-else-if="source === 'snapshot'" class="rt-tag">快照</span>
    </div>

    <!-- 汇总：总分 + 分布 -->
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

    <!-- 装过机的单独均分 -->
    <p v-if="s.count" class="rt-meta">
      其中 <strong>{{ s.own_hardware_count }}</strong> 人装过机<template v-if="s.own_hardware_avg != null">，
      他们给的均分是 <strong>{{ s.own_hardware_avg.toFixed(1) }}</strong></template>。
      只看均分会把「5 人 5 分」和「1 人 5 分 + 4 人 1 分」看成一样，所以分布也放出来。
    </p>
    <p v-else class="rt-meta">
      还没有人打分。第一条评价由你来写 —— 有实测最好；没有实测也可以写，但请如实勾选「装过机」。
    </p>

    <!-- 四维 -->
    <div v-if="dims.length" class="rt-dims">
      <div v-for="d in dims" :key="d.key" class="rt-dim">
        <span class="rt-dim-k" :title="d.hint">{{ d.label }}</span>
        <span class="rt-dim-track"><span class="rt-dim-fill" :style="{ width: (d.v! / 5 * 100) + '%' }" /></span>
        <span class="rt-dim-v">{{ d.v!.toFixed(1) }}<em v-if="d.n < s.count">/{{ d.n }}</em></span>
      </div>
      <p class="rt-dims-note">
        只显示这个品类该看的维度（不同品类关心的不一样）；分母是填了该项的样本数，见斜杠后的数字。
        有人只打总分没打分维度，那一票不进维度均值 —— 不补 0，也不猜。
      </p>
    </div>

    <!-- 工况 -->
    <div v-if="usageRows.length" class="rt-usage">
      <div v-for="u in usageRows" :key="u.key" class="rt-usage-row">
        <span class="rt-usage-k">{{ u.label }}</span>
        <span class="rt-usage-v">
          <em v-for="it in u.items" :key="it.text">{{ it.text }} {{ it.c }}</em>
        </span>
      </div>
    </div>

    <!-- 唯一打分入口 -->
    <div class="rt-gh">
      <a class="rt-btn" :href="ghUrl" target="_blank" rel="noopener" title="在 GitHub 上开一条评分 issue（表单约 1 分钟）">写评价</a>
      <a class="rt-gh-link" :href="ghIssues" target="_blank" rel="noopener">看所有评价 →</a>
    </div>

    <p class="rt-hint">
      在 GitHub 上开一条 <strong>issue</strong>（表单，约 1 分钟）：三项必填（总分 / 是否用过 / 一句话理由），分维度选填。
      <strong>一人一件一票</strong>（唯一键 = 你的账号 + 部件 id），改主意就编辑那条 issue，
      不会被算成两票。汇总由 Actions 自动跑：不是实时，但每一条都能查到是谁、凭什么。
    </p>

    <p class="rt-hint">
      <strong>想写长一点的实测</strong>就写在下面的评论里（GitHub Discussions）。
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
.rt-warn {
  font-size: 0.66rem; color: #b45309;
  border: 1px solid #f59e0b; border-radius: 999px; padding: 0 6px;
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
.rt-bar-row { display: flex; align-items: center; gap: 0.4rem; }
.rt-bar-k { width: 0.7rem; font-size: 0.68rem; color: var(--vp-c-text-3); }
.rt-bar-track {
  flex: 1; height: 4px; border-radius: 2px; background: var(--vp-c-bg-soft); overflow: hidden;
}
.rt-bar-fill { display: block; height: 100%; background: var(--vp-c-brand-1); }
.rt-bar-c { width: 1.4rem; text-align: right; font-size: 0.68rem; color: var(--vp-c-text-3); }

.rt-meta { margin: 0.55rem 0 0; font-size: 0.74rem; line-height: 1.8; color: var(--vp-c-text-2); }

/* 四维 */
.rt-dims { margin-top: 0.7rem; display: flex; flex-direction: column; gap: 0.3rem; }
.rt-dim { display: flex; align-items: center; gap: 0.45rem; }
.rt-dim-k { width: 5.2rem; font-size: 0.72rem; color: var(--vp-c-text-2); }
.rt-dim-track {
  flex: 1; height: 6px; border-radius: 3px; background: var(--vp-c-bg-soft); overflow: hidden;
}
.rt-dim-fill { display: block; height: 100%; background: var(--vp-c-brand-1); opacity: 0.85; }
.rt-dim-v {
  width: 2.6rem; text-align: right; font-size: 0.72rem;
  color: var(--vp-c-text-1); font-variant-numeric: tabular-nums;
}
.rt-dim-v em { font-style: normal; color: var(--vp-c-text-3); font-size: 0.64rem; }
.rt-dims-note { margin: 0.2rem 0 0; font-size: 0.68rem; line-height: 1.7; color: var(--vp-c-text-3); }

/* 工况 */
.rt-usage { margin-top: 0.55rem; display: flex; flex-direction: column; gap: 0.2rem; }
.rt-usage-row { display: flex; gap: 0.45rem; align-items: baseline; }
.rt-usage-k { width: 4.2rem; font-size: 0.7rem; color: var(--vp-c-text-3); }
.rt-usage-v { display: flex; flex-wrap: wrap; gap: 0.3rem; }
.rt-usage-v em {
  font-style: normal; font-size: 0.68rem; padding: 0 6px; border-radius: 999px;
  background: var(--vp-c-bg-soft); color: var(--vp-c-text-2);
}

.rt-gh { display: flex; align-items: center; gap: 0.6rem; margin-top: 0.8rem; }
.rt-btn {
  display: inline-block; font-size: 0.76rem; font-weight: 600;
  padding: 0.3rem 0.7rem; border-radius: 7px;
  background: var(--vp-c-brand-1); color: #fff; text-decoration: none;
}
.rt-btn:hover { opacity: 0.9; }
.rt-gh-link { font-size: 0.72rem; color: var(--vp-c-brand-1); text-decoration: none; }
.rt-gh-link:hover { text-decoration: underline; }

.rt-hint { margin: 0.5rem 0 0; font-size: 0.7rem; line-height: 1.85; color: var(--vp-c-text-3); }
.rt-jump { display: inline-block; margin-top: 0.5rem; font-size: 0.72rem; color: var(--vp-c-brand-1); }
</style>
