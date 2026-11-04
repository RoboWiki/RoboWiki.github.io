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
 * 两个打分入口，按部署形态分工：
 *   · 主站（有后端）：站内 1–5 分，一人一件一票，可改可撤（/api/v1/ratings）
 *   · 静态镜像 / 需要四维与工况：GitHub issue 表单（读不用账号，写要 GitHub）
 *
 * 两个数据源，先快照后实时：
 *   · 构建期快照 `ratings.json`：镜像端唯一来源，也是主站的兜底
 *   · /api/v1/ratings/{id}：主站实时值，探活通过才请求；站内还没票时不覆盖快照
 * 读不到就显示「暂无评分」，绝不当成 0 分。
 */
import { computed, onMounted, ref } from 'vue'
import { withBase } from 'vitepress'
import { RadioGroupItem, RadioGroupRoot } from 'reka-ui'
import { ApiError, apiAvailable, apiErrorMessage, apiFetch, isConnectivityError, isMirror, MIRROR_READONLY_NOTE } from '../lib/api'
import { getToken } from '../lib/auth'

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
  /** 贝叶斯收缩后的排序分；只用于排序，不当作「真实均分」展示 */
  rank_score?: number | null
}

interface Mine {
  score: number
  own_hardware: boolean
  note: string
  /** 对应的评价帖被站务隐藏时，这票不计入公开聚合（Rating 本身仍在） */
  hidden?: boolean
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
const source = ref<'snapshot' | 'live' | 'none'>('none')
const apiUp = ref<boolean | null>(null)
const loggedIn = ref(false)
const score = ref(0)
const own = ref(false)
const note = ref('')
const submitting = ref(false)
const ratingError = ref('')
const ratingNotice = ref('')
const mine = ref<Mine | null>(null)

const loginHref = computed(() => {
  const path = typeof window !== 'undefined' ? window.location.pathname : '/'
  return `/login?redirect=${encodeURIComponent(path)}`
})

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

/** 方向键 / Home / End：焦点已经被 roving focus 移到目标格，这里把那一格选中。
 *  reka-ui 自己的「按方向键即选中」是 keydown → focus → setTimeout(click)，
 *  快速按下并松开时 keyup 可能先到，选中会被吞掉；补一条不依赖时序的路径。 */
function onStarKey(evt: KeyboardEvent) {
  if (!['ArrowUp', 'ArrowDown', 'ArrowLeft', 'ArrowRight', 'Home', 'End'].includes(evt.key)) return
  const el = document.activeElement as HTMLElement | null
  const v = Number(el?.getAttribute('value'))
  if (Number.isInteger(v) && v >= 1 && v <= 5) score.value = v
}

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
}

/**
 * 合并站内实时聚合。
 *
 * 后端 /ratings 现在与快照/排序共用 rating_stats.aggregate，会带
 * dims_avg / dims_n / usage_count。站内 1–5 分不收集四维与工况，这些字段
 * 是 null；**不能用 null 覆盖掉 GitHub issue 快照里已有的维度**，否则
 * 页面上「站内多了一票 → 四维整块消失」。缺失时保留快照值。
 */
function mergeLive(d: any) {
  s.value = {
    ...s.value,
    ...d,
    dims_avg: d.dims_avg ?? s.value.dims_avg ?? null,
    dims_n: d.dims_n ?? s.value.dims_n ?? null,
    usage_count: d.usage_count ?? s.value.usage_count ?? null,
    // 后端 n=0 时 low_sample=true；有票时以接口为准
    low_sample: typeof d.low_sample === 'boolean'
      ? d.low_sample : (d.count > 0 && d.count < 3),
  }
  source.value = 'live'
}

async function loadLive() {
  apiUp.value = await apiAvailable()
  loggedIn.value = !!getToken()
  if (!apiUp.value) return
  try {
    const d = await apiFetch<any>(`/ratings/${encodeURIComponent(props.partId)}`)
    mine.value = d.mine || null
    if (mine.value) {
      score.value = mine.value.score
      own.value = mine.value.own_hardware
      note.value = mine.value.note || ''
    }
    // 站内还没有票时保留 GitHub 快照，避免把已有评价显示成 0。
    if (d.count > 0 || !s.value.count) mergeLive(d)
  } catch (e) {
    // 断网/主站不可达：保留构建快照（镜像端就是这样工作的）
    if (isMirror() && isConnectivityError(e)) source.value = s.value.count ? 'snapshot' : 'none'
    // 失败不清 token：GET 评分公开，401 只可能是服务端异常配置
  }
}

async function submitRating() {
  ratingError.value = ''
  ratingNotice.value = ''
  if (!getToken()) { ratingError.value = '请先登录再打分'; return }
  if (!score.value) { ratingError.value = '请选择 1–5 分'; return }
  submitting.value = true
  try {
    const d = await apiFetch<any>(`/ratings/${encodeURIComponent(props.partId)}`, {
      method: 'POST',
      body: JSON.stringify({ score: score.value, own_hardware: own.value, note: note.value.trim() }),
    })
    loggedIn.value = true
    mine.value = d.mine || null
    mergeLive(d)
    ratingNotice.value = mine.value?.hidden
      ? '评分已保存；对应评价帖已被隐藏，暂不计入公开均分'
      : mine.value ? '已更新你的评分' : '评分已记录'
  } catch (e: any) {
    if (e instanceof ApiError && e.status === 401) {
      loggedIn.value = false
      ratingError.value = '登录已过期，请重新登录'
      return
    }
    ratingError.value = apiErrorMessage(e, '评分失败，请稍后重试')
  } finally {
    submitting.value = false
  }
}

async function removeRating() {
  ratingError.value = ''
  ratingNotice.value = ''
  submitting.value = true
  try {
    await apiFetch(`/ratings/${encodeURIComponent(props.partId)}`, { method: 'DELETE' })
    mine.value = null
    score.value = 0
    own.value = false
    note.value = ''
    ratingNotice.value = '已撤销评分'
    await loadLive()
  } catch (e: any) {
    if (e instanceof ApiError && e.status === 404) {
      // 已经没有这票，按成功处理
      mine.value = null
      score.value = 0
      ratingNotice.value = '已撤销评分'
      return
    }
    if (e instanceof ApiError && e.status === 401) {
      loggedIn.value = false
      ratingError.value = '登录已过期，请重新登录'
      return
    }
    ratingError.value = apiErrorMessage(e, '撤销失败，请稍后重试')
  } finally {
    submitting.value = false
  }
}

onMounted(async () => {
  await load()
  await loadLive()
})
</script>

<template>
  <div id="评分" class="rt">
    <div class="rt-head">
      <span class="rt-title">实际使用</span>
      <span v-if="!s.count" class="rt-none">暂无评分</span>
      <span v-else-if="s.low_sample" class="rt-warn" title="样本少于 3 条时不显示确定结论">样本不足</span>
      <span v-else-if="source === 'live'" class="rt-tag">站内实时</span>
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

    <!-- 主站：站内账号直接打分；静态镜像：保留 GitHub 表单 -->
    <div v-if="apiUp" class="rt-live">
      <div class="rt-live-head">站内评分</div>
      <template v-if="loggedIn">
        <!--
          星数是**单选组**，不是一排开关：role=radiogroup + role=radio + aria-checked，
          左右方向键可切换，Tab 只停在选中那一格（roving tabindex）。
          用 reka-ui 的 RadioGroup 而不是自己拿 <button aria-pressed> 冒充 ——
          后者在屏幕阅读器里会被念成「切换按钮」，也拿不到方向键行为。
        -->
        <RadioGroupRoot v-model="score" class="rt-stars" orientation="horizontal"
          aria-label="评分（1–5 分）" :disabled="submitting" @keydown="onStarKey">
          <RadioGroupItem v-for="n in 5" :key="n" :value="n" type="button" class="rt-star"
            :class="{ on: score >= n }" :aria-label="`${n} 分`">{{ n }}</RadioGroupItem>
        </RadioGroupRoot>
        <label class="rt-own">
          <input v-model="own" type="checkbox" /> 我装过机（这条评分来自真实使用）
        </label>
        <label class="rt-note-label" for="rt-note">一句话理由（可选）</label>
        <input id="rt-note" v-model="note" class="rt-note" maxlength="200"
          placeholder="一句话理由（可选）" />
        <div class="rt-live-actions">
          <button type="button" class="rt-btn" :disabled="!score || submitting" @click="submitRating">
            {{ submitting ? '提交中…' : mine ? '更新评分' : '提交评分' }}
          </button>
          <button v-if="mine" type="button" class="rt-ghost" :disabled="submitting" @click="removeRating">撤销</button>
          <span v-if="mine" class="rt-mine">你已打分 {{ mine.score }} 分</span>
        </div>
        <p v-if="mine?.hidden" class="rt-hidden" role="status">
          你的评分对应评价帖已被站务隐藏，这票暂不计入公开均分；评价恢复后会重新计入。
        </p>
        <p v-if="ratingError" class="rt-err" role="alert">{{ ratingError }}</p>
        <p v-if="ratingNotice" class="rt-ok" role="status">{{ ratingNotice }}</p>
      </template>
      <p v-else class="rt-hint">
        站内评分需要登录 · <a :href="loginHref">登录 / 注册</a>（不需要 GitHub 账号）。
      </p>
    </div>

    <!-- GitHub 表单：静态镜像的主入口；主站保留作多维评分入口 -->
    <div class="rt-gh">
      <a class="rt-btn" :href="ghUrl" target="_blank" rel="noopener"
        title="在 GitHub 上开一条评分 issue（表单约 1 分钟）">{{ apiUp ? '多维评分（GitHub）' : '写评价' }}</a>
      <a class="rt-gh-link" :href="ghIssues" target="_blank" rel="noopener">看所有评价 →</a>
    </div>

    <p v-if="!apiUp" class="rt-hint">
      <template v-if="s.count"><strong>{{ isMirror() ? MIRROR_READONLY_NOTE : '主站服务暂时不可达，这里显示构建快照' }}</strong>。<br /></template>
      在 GitHub 上开一条 <strong>issue</strong>（表单，约 1 分钟）：三项必填（总分 / 是否用过 / 一句话理由），分维度选填。
      <strong>一人一件一票</strong>，改主意就编辑那条 issue。汇总由 Actions 自动跑：不是实时，但每一条都能查到是谁、凭什么。
    </p>

    <p class="rt-hint">
      <strong>想写长一点的实测</strong>就写在下面的讨论里。
      评分用来排序，讨论用来讲清楚为什么。
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
  font-size: 0.66rem; color: var(--rw-accent-1);
  border: 1px solid var(--rw-accent-2); border-radius: 999px; padding: 0 6px;
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

.rt-live {
  margin-top: 0.8rem; padding: 0.75rem 0.8rem;
  border: 1px solid var(--vp-c-divider); border-radius: 10px;
  background: var(--vp-c-bg);
}
.rt-live-head { font-size: 0.78rem; font-weight: 700; color: var(--vp-c-text-2); margin-bottom: 0.5rem; }
.rt-stars { display: flex; gap: 0.3rem; }
.rt-stars button {
  width: 2.5rem; height: 2.5rem; border-radius: 8px; cursor: pointer;
  border: 1px solid var(--vp-c-divider); background: transparent;
  color: var(--vp-c-text-2); font-size: 0.85rem; font-weight: 700;
}
.rt-stars button.on { background: var(--vp-c-brand-1); border-color: var(--vp-c-brand-1); color: var(--rw-on-brand); }
.rt-stars button:focus-visible { outline: 2px solid var(--vp-c-brand-1); outline-offset: 2px; }
.rt-stars button:disabled { opacity: 0.55; cursor: default; }
.rt-own { display: flex; align-items: center; gap: 0.4rem; margin: 0.55rem 0; font-size: 0.76rem; color: var(--vp-c-text-2); }
.rt-note-label { display: block; font-size: 0.72rem; color: var(--vp-c-text-3); margin-bottom: 0.2rem; }
.rt-note {
  width: 100%; box-sizing: border-box; padding: 0.5rem 0.6rem;
  border: 1px solid var(--vp-c-divider); border-radius: 8px;
  background: var(--vp-c-bg); color: var(--vp-c-text-1); font: inherit; font-size: 0.8rem;
}
.rt-live-actions { display: flex; align-items: center; gap: 0.6rem; margin-top: 0.55rem; flex-wrap: wrap; }
.rt-ghost {
  min-height: 36px; padding: 0.3rem 0.7rem; border-radius: 7px; cursor: pointer;
  border: 1px solid var(--vp-c-divider); background: transparent; color: var(--vp-c-text-2);
}
.rt-mine { font-size: 0.72rem; color: var(--vp-c-text-3); }
.rt-err { margin: 0.5rem 0 0; font-size: 0.74rem; color: var(--rw-danger); }
.rt-ok { margin: 0.5rem 0 0; font-size: 0.74rem; color: var(--rw-link); }
.rt-hidden {
  margin: 0.5rem 0 0; font-size: 0.72rem; line-height: 1.7;
  color: var(--vp-c-text-3);
}

.rt-gh { display: flex; align-items: center; gap: 0.6rem; margin-top: 0.8rem; }
.rt-btn {
  display: inline-block; font-size: 0.76rem; font-weight: 600;
  padding: 0.3rem 0.7rem; border-radius: 7px;
  background: var(--vp-c-brand-1); color: var(--rw-on-brand); text-decoration: none;
}
.rt-btn:hover { opacity: 0.9; }
.rt-gh-link { font-size: 0.72rem; color: var(--rw-link); text-decoration: none; }
.rt-gh-link:hover { text-decoration: underline; }

.rt-hint { margin: 0.5rem 0 0; font-size: 0.7rem; line-height: 1.85; color: var(--vp-c-text-3); }
.rt-jump { display: inline-block; margin-top: 0.5rem; font-size: 0.72rem; color: var(--rw-link); }
</style>
