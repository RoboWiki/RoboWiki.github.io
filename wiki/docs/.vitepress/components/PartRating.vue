<script setup lang="ts">
/**
 * 零件评分：星标 + 分布 + 打分入口。
 *
 * 数据来源有两层，按顺序降级：
 *   1. `GET /api/ratings/{id}` —— 有后端时用实时值（能读到自己打的分）
 *   2. `ratings.json` —— 构建时从库里烤出来的快照，纯静态部署（GitHub Pages）用这个
 *   3. 都没有 → 显示「暂无评分」，**不显示 0 分**（0 分是差评，没评不是）
 *
 * 为什么评分自托管、评论用 giscus：
 *   giscus 只有 reaction，没有 1–5 分档，也无法聚合进排序。
 *   所以「分」进本站库、「话」交给 GitHub —— 分工，不重复。
 */
import { computed, onMounted, ref } from 'vue'
import { withBase } from 'vitepress'

interface Summary {
  count: number
  avg: number | null
  histogram: Record<string, number>
  own_hardware_count: number
  mine: { score: number; own_hardware: boolean; note: string } | null
}

const props = defineProps<{ partId: string }>()

const s = ref<Summary>({
  count: 0, avg: null,
  histogram: { '1': 0, '2': 0, '3': 0, '4': 0, '5': 0 },
  own_hardware_count: 0, mine: null,
})
const live = ref(false)          // 是否连上了后端（连不上就只能读快照）
const hover = ref(0)             // 悬停预览分数
const pick = ref(0)              // 选中的分数
const own = ref(false)
const note = ref('')
const busy = ref(false)
const msg = ref('')
const authOpen = ref(false)
const handle = ref('')
const password = ref('')

function token(): string | null {
  try { return localStorage.getItem('roboselect.token') } catch { return null }
}

const logged = ref(!!token())

const bars = computed(() => {
  const total = s.value.count || 1
  return [5, 4, 3, 2, 1].map(n => ({
    n,
    c: s.value.histogram[String(n)] || 0,
    pct: Math.round(((s.value.histogram[String(n)] || 0) / total) * 100),
  }))
})

async function load() {
  // 1) 先读构建快照（静态部署也能显示）
  try {
    const r = await fetch(withBase('/ratings.json'))
    if (r.ok) {
      const d = await r.json()
      const one = d.parts?.[props.partId]
      if (one) s.value = { ...s.value, ...one, mine: null }
    }
  } catch { /* 没有快照就保持空 */ }

  // 2) 有后端就用实时值（能读到自己打的分）
  try {
    const r = await fetch(`/api/ratings/${encodeURIComponent(props.partId)}`, {
      headers: token() ? { Authorization: `Bearer ${token()}` } : {},
    })
    if (r.ok && (r.headers.get('content-type') || '').includes('json')) {
      const d = await r.json()
      s.value = { count: d.count, avg: d.avg, histogram: d.histogram,
                  own_hardware_count: d.own_hardware_count, mine: d.mine }
      live.value = true
      if (d.mine) { pick.value = d.mine.score; own.value = d.mine.own_hardware; note.value = d.mine.note }
    }
  } catch { /* 静态部署：保持快照 */ }
}

async function doLogin() {
  msg.value = ''
  try {
    const r = await fetch('/api/auth/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ handle: handle.value, password: password.value }),
    })
    const d = await r.json().catch(() => ({}))
    if (!r.ok) throw new Error(typeof d.detail === 'string' ? d.detail : '登录失败')
    localStorage.setItem('roboselect.token', d.access_token)
    logged.value = true
    authOpen.value = false
    msg.value = `已登录：${d.user.display_name}`
    await load()
  } catch (e: any) {
    msg.value = e.message
  }
}

async function submit() {
  if (!pick.value) { msg.value = '先选星数'; return }
  busy.value = true
  msg.value = ''
  try {
    const r = await fetch(`/api/ratings/${encodeURIComponent(props.partId)}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token()}` },
      body: JSON.stringify({ score: pick.value, own_hardware: own.value, note: note.value }),
    })
    const d = await r.json().catch(() => ({}))
    if (!r.ok) throw new Error(typeof d.detail === 'string' ? d.detail : '提交失败')
    s.value = { count: d.count, avg: d.avg, histogram: d.histogram,
                own_hardware_count: d.own_hardware_count, mine: d.mine }
    msg.value = d.created ? '已记录你的评分' : '已更新你的评分'
  } catch (e: any) {
    msg.value = e.message
  } finally {
    busy.value = false
  }
}

onMounted(load)
</script>

<template>
  <div class="rt">
    <div class="rt-head">
      <span class="rt-title">实际使用</span>
      <span v-if="!s.count" class="rt-none">暂无评分</span>
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

    <!-- 打分 -->
    <div v-if="live" class="rt-form">
      <div class="rt-stars" @mouseleave="hover = 0">
        <button v-for="n in 5" :key="n" class="rt-star"
                :class="{ on: n <= (hover || pick) }"
                @mouseenter="hover = n" @click="pick = n"
                :aria-label="`${n} 分`">★</button>
        <span class="rt-pick">{{ pick ? `${pick} / 5` : '点星打分' }}</span>
      </div>

      <label class="rt-own">
        <input type="checkbox" v-model="own" /> 我装过这个件（装机票单独统计）
      </label>
      <input v-model="note" class="rt-note" maxlength="60"
             placeholder="一句话理由（可选）：比如「髋部跑了三个月，温升可接受」" />

      <div class="rt-actions">
        <button class="rt-btn" :disabled="busy || !pick" @click="logged ? submit() : (authOpen = true)">
          {{ logged ? (s.mine ? '更新评分' : '提交评分') : '登录后评分' }}
        </button>
        <span v-if="s.mine" class="rt-mine">我打过 {{ s.mine.score }} 分</span>
      </div>

      <div v-if="authOpen && !logged" class="rt-auth">
        <input v-model="handle" class="rt-in" placeholder="账号（演示：demo1）" />
        <input v-model="password" class="rt-in" type="password" placeholder="密码（演示：roboselect）" />
        <button class="rt-btn" @click="doLogin">登录</button>
      </div>

      <p v-if="msg" class="rt-msg">{{ msg }}</p>
    </div>

    <p v-else-if="!live" class="rt-hint">
      这是<strong>构建时的快照</strong>，静态站没有后端，暂时不能打分。
      评论在下方（GitHub 账号），评分要在有后端的部署上提交。
    </p>

    <p class="rt-hint">
      <strong>评论</strong>在下方，走 GitHub Discussions —— 发言要 GitHub 账号；
      <strong>评分</strong>进本站库，因为它要能聚合、能进排序。
    </p>

    <a class="rt-jump" href="#这一页的讨论">去写评论 ↓</a>
  </div>
</template>

<style scoped>
.rt { font-size: 0.8rem; }
.rt-head { display: flex; align-items: baseline; gap: 0.5rem; margin-bottom: 0.55rem; }
.rt-title { font-weight: 700; font-size: 0.82rem; color: var(--vp-c-text-2); }
.rt-none {
  font-size: 0.7rem; color: var(--vp-c-text-3);
  border: 1px dashed var(--vp-c-divider); border-radius: 999px; padding: 1px 7px;
}

.rt-sum { display: grid; grid-template-columns: 5.5rem minmax(0, 1fr); gap: 0.7rem; align-items: center;
  padding-bottom: 0.6rem; border-bottom: 1px solid var(--vp-c-divider); }
.rt-avg { display: flex; flex-direction: column; }
.rt-avg-n { font-size: 1.7rem; font-weight: 700; line-height: 1.1;
  color: var(--vp-c-text-1); font-variant-numeric: tabular-nums; }
.rt-avg-s { font-size: 0.7rem; color: var(--vp-c-text-3); }

.rt-bars { display: flex; flex-direction: column; gap: 2px; }
.rt-bar-row { display: grid; grid-template-columns: 0.8rem minmax(0, 1fr) 1.4rem;
  gap: 0.35rem; align-items: center; font-size: 0.68rem; color: var(--vp-c-text-3); }
.rt-bar-track { height: 6px; border-radius: 3px; background: var(--vp-c-default-soft); overflow: hidden; }
.rt-bar-fill { display: block; height: 100%; border-radius: 3px; background: var(--vp-c-brand-1); }
.rt-bar-c { text-align: right; font-variant-numeric: tabular-nums; }

.rt-meta { font-size: 0.72rem; color: var(--vp-c-text-3); line-height: 1.7; margin: 0.5rem 0; }

.rt-form { margin-top: 0.6rem; }
.rt-stars { display: flex; align-items: center; gap: 2px; }
.rt-star { font-size: 1.25rem; line-height: 1; background: none; border: none; cursor: pointer;
  color: var(--vp-c-default-soft); padding: 0 1px; transition: color 0.1s; }
.rt-star.on { color: #d97706; }
html.dark .rt-star.on { color: #e0b159; }
.rt-pick { margin-left: 0.5rem; font-size: 0.72rem; color: var(--vp-c-text-3); }

.rt-own { display: flex; align-items: center; gap: 0.35rem; margin: 0.5rem 0 0.35rem;
  font-size: 0.74rem; color: var(--vp-c-text-2); }
.rt-note, .rt-in {
  width: 100%; box-sizing: border-box; font-size: 0.76rem; padding: 0.35rem 0.55rem;
  border: 1px solid var(--vp-c-divider); border-radius: 6px;
  background: var(--vp-c-bg); color: var(--vp-c-text-1); margin-bottom: 0.35rem;
}
.rt-note:focus, .rt-in:focus { outline: none; border-color: var(--vp-c-brand-1); }

.rt-actions { display: flex; align-items: center; gap: 0.6rem; }
.rt-btn {
  font-size: 0.76rem; font-weight: 600; padding: 0.32rem 0.8rem; border-radius: 999px;
  border: 1px solid var(--vp-c-brand-1); background: var(--vp-c-brand-1); color: #fff; cursor: pointer;
}
.rt-btn:disabled { opacity: 0.45; cursor: not-allowed; }
.rt-mine { font-size: 0.7rem; color: var(--vp-c-text-3); }
.rt-auth { margin-top: 0.5rem; padding-top: 0.5rem; border-top: 1px dashed var(--vp-c-divider); }
.rt-msg { font-size: 0.72rem; color: var(--vp-c-brand-1); margin: 0.4rem 0 0; }
.rt-hint { font-size: 0.72rem; color: var(--vp-c-text-3); line-height: 1.7; margin: 0.55rem 0 0; }
.rt-jump { display: inline-block; margin-top: 0.4rem; font-size: 0.74rem;
  font-weight: 600; color: var(--vp-c-brand-1); }
</style>
