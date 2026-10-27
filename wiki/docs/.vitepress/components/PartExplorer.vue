<script setup lang="ts">
/**
 * 交互式部件检索 —— 全部在浏览器里跑，没有一个 API 请求。
 *
 * 这是对「VitePress 能不能替代选型台」的回答：
 * 目录数据本来就是静态的（构建时由 scripts/build_wiki.py 导出 catalog.json），
 * 排序 / 筛选 / 搜索都是纯客户端计算，静态站完全能做，而且在三件事上更好：
 *   1. 每个型号有独立 URL，能分享、能被搜索引擎收录
 *   2. 没有服务器要养，Pages / 任何静态托管都能跑
 *   3. 首屏一次取完，后续交互零延迟
 *
 * 静态站**做不到**的是要写库的那部分：账号、发帖、投票、后台改数、MCP。
 * 那些才需要 FastAPI。
 */
import { computed, onMounted, ref } from 'vue'
import { withBase } from 'vitepress'

interface Part {
  id: string
  slug: string
  category: string
  subtype: string
  subtypeLabel: string
  vendor: string
  model: string
  tier: string
  verified: boolean
  price: number | null
  image: string | null
  tauPeak: number | null
  tauRated: number | null
  gear: number | null
  mass: number | null
  armature: number | null
  rpm: number | null
  notes: string
  specs: Record<string, any>
}

const all = ref<Part[]>([])
const loading = ref(true)
const fail = ref('')

const q = ref('')
const cat = ref('actuator')
const vendor = ref('')
const sort = ref<'peak' | 'armature' | 'mass' | 'price' | 'vendor'>('peak')
const order = ref<'desc' | 'asc'>('desc')
const picked = ref<Part[]>([])          // 对比（最多 3）
const detail = ref<Part | null>(null)

const CATS = [
  { v: 'actuator', t: '关节电机' },
  { v: 'controller_high', t: '上位机' },
  { v: 'controller_low', t: '下位机' },
  { v: 'sensor', t: '传感器' },
]

const FIELD: Record<string, keyof Part> = {
  peak: 'tauPeak', armature: 'armature', mass: 'mass', price: 'price', vendor: 'vendor',
}

onMounted(async () => {
  try {
    const r = await fetch(withBase('/catalog.json'))
    if (!r.ok) throw new Error(String(r.status))
    all.value = (await r.json()).parts
  } catch (e: any) {
    fail.value = `目录加载失败（${e.message}）`
  } finally {
    loading.value = false
  }
})

const vendors = computed(() =>
  [...new Set(all.value.filter(p => p.category === cat.value).map(p => p.vendor))].sort())

const rows = computed(() => {
  const key = FIELD[sort.value]
  let out = all.value.filter(
    p => p.category === cat.value
      && (!vendor.value || p.vendor === vendor.value)
      && (!q.value || `${p.model} ${p.vendor} ${p.subtypeLabel} ${p.tier}`
        .toLowerCase().includes(q.value.toLowerCase())),
  )
  out = [...out].sort((a, b) => {
    const va = a[key] as any, vb = b[key] as any
    // null 永远排最后：缺失就是缺失，不该混在排序里
    if (va == null && vb == null) return 0
    if (va == null) return 1
    if (vb == null) return -1
    const cmp = typeof va === 'number' ? va - vb : String(va).localeCompare(String(vb), 'zh')
    return order.value === 'desc' ? -cmp : cmp
  })
  return out
})

function num(v: any, d = 3): string {
  if (v == null || v === '') return '—'
  const n = Number(v)
  if (!isFinite(n)) return String(v)
  const a = Math.abs(n)
  if (a && (a < 0.01 || a >= 100000)) return n.toExponential(2)
  return String(Number(n.toFixed(d)))
}

function money(v: number | null) {
  return v == null ? '无报价' : `¥${Math.round(v).toLocaleString('en-US')}`
}

/** 厂商图优先；没有就画一个和真实尺寸有关的示意（静态站里不引 React 组件） */
function glyphBox(p: Part) {
  const w = p.od && p.len ? Math.min(2.6, Math.max(0.5, p.len / p.od)) : 1
  return { h: Math.max(18, Math.min(46, 26 * w)), w: Math.max(28, Math.min(74, 62 / Math.max(0.8, w * 0.9))) }
}

function toggleCompare(p: Part) {
  const i = picked.value.findIndex(x => x.id === p.id)
  if (i >= 0) picked.value.splice(i, 1)
  else if (picked.value.length < 3) picked.value.push(p)
}

function isPicked(p: Part) {
  return picked.value.some(x => x.id === p.id)
}

const COMPARE_FIELDS: { k: keyof Part; t: string }[] = [
  { k: 'tauPeak', t: '峰值 τ N·m' },
  { k: 'tauRated', t: '额定 τ N·m' },
  { k: 'gear', t: '减速比' },
  { k: 'mass', t: '质量 kg' },
  { k: 'armature', t: 'armature kg·m²' },
  { k: 'rpm', t: '空载 rpm' },
  { k: 'price', t: '价格 ¥' },
]
</script>

<template>
  <div class="pd">
    <p v-if="loading" class="pd-muted">加载目录…</p>
    <p v-else-if="fail" class="pd-muted">{{ fail }}</p>

    <template v-else>
      <!-- 工具条 -->
      <div class="pd-bar">
        <input v-model="q" class="pd-input" placeholder="搜型号 / 厂商 / 类型" />
        <select v-model="sort" class="pd-sel">
          <option value="peak">按峰值扭矩</option>
          <option value="armature">按 armature</option>
          <option value="mass">按质量</option>
          <option value="price">按价格</option>
          <option value="vendor">按厂商</option>
        </select>
        <button class="pd-btn" @click="order = order === 'desc' ? 'asc' : 'desc'">
          {{ order === 'desc' ? '↓ 降序' : '↑ 升序' }}
        </button>
        <button v-if="vendor" class="pd-chip on" @click="vendor = ''">{{ vendor }} ✕</button>
        <span class="pd-count">{{ rows.length }} 项</span>
      </div>

      <!-- 分类 + 厂商 -->
      <div class="pd-bar">
        <button v-for="c in CATS" :key="c.v"
                :class="['pd-chip', cat === c.v ? 'on' : '']"
                @click="cat = c.v; vendor = ''; q = ''">
          {{ c.t }}
        </button>
        <span class="pd-sep" />
        <button v-for="v in vendors.slice(0, 12)" :key="v"
                :class="['pd-chip sm', vendor === v ? 'on' : '']"
                @click="vendor = vendor === v ? '' : v">
          {{ v }}
        </button>
      </div>

      <!-- 对比表 -->
      <div v-if="picked.length" class="pd-compare">
        <div class="pd-compare-head">
          对比 {{ picked.length }} / 3
          <button class="pd-link" @click="picked = []">清空</button>
        </div>
        <table>
          <tr><th></th><th v-for="p in picked" :key="p.id">{{ p.model }}</th></tr>
          <tr v-for="f in COMPARE_FIELDS" :key="f.k">
            <td class="pd-k">{{ f.t }}</td>
            <td v-for="p in picked" :key="p.id">
              {{ f.k === 'price' ? money(p.price as any) : num(p[f.k]) }}
            </td>
          </tr>
        </table>
      </div>

      <!-- 卡片 -->
      <div class="pd-grid">
        <article v-for="p in rows" :key="p.id" class="pd-card">
          <div class="pd-img">
            <img v-if="p.image" :src="withBase(p.image)" :alt="p.model" loading="lazy" />
            <svg v-else viewBox="0 0 120 70" width="132" height="77" aria-hidden="true">
              <rect x="8" y="8" width="104" height="54" rx="6"
                    fill="var(--vp-c-bg-soft)" stroke="var(--vp-c-divider)" />
              <rect :x="60 - glyphBox(p).w / 2" :y="35 - glyphBox(p).h / 2"
                    :width="glyphBox(p).w" :height="glyphBox(p).h" rx="5"
                    fill="var(--vp-c-brand-soft)" stroke="var(--vp-c-brand-1)" />
            </svg>
            <span :class="['pd-tier', p.tier === 'A' ? 'a' : '']">{{ p.tier }}{{ p.verified ? ' ✓' : '' }}</span>
            <span class="pd-sub">{{ p.subtypeLabel }}</span>
          </div>

          <div class="pd-body">
            <a class="pd-model" :href="withBase('/parts/' + p.category + '/' + p.slug)">{{ p.model }}</a>
            <div class="pd-vendor">{{ p.vendor }}</div>
            <div class="pd-chips">
              <span v-if="p.tauPeak != null">峰值τ <b>{{ num(p.tauPeak) }}</b></span>
              <span v-if="p.gear != null">N <b>{{ num(p.gear) }}</b></span>
              <span v-if="p.mass != null">m <b>{{ num(p.mass) }}</b></span>
              <span v-if="p.armature != null">J<sub>eq</sub> <b>{{ num(p.armature) }}</b></span>
            </div>
            <div class="pd-foot">
              <span class="pd-price">{{ money(p.price) }}</span>
              <span class="pd-acts">
                <button class="pd-link" @click="toggleCompare(p)">
                  {{ isPicked(p) ? '取消' : '对比' }}
                </button>
                <button class="pd-link" @click="detail = p">明细</button>
              </span>
            </div>
          </div>
        </article>
      </div>

      <!-- 明细 -->
      <div v-if="detail" class="pd-modal" @click.self="detail = null">
        <div class="pd-panel">
          <div class="pd-panel-head">
            <b>{{ detail.model }}</b>
            <span class="pd-muted">{{ detail.vendor }} · {{ detail.subtypeLabel }}</span>
            <button class="pd-link" @click="detail = null">关闭</button>
          </div>
          <table class="pd-specs">
            <tr v-for="(v, k) in detail.specs" :key="k">
              <td class="pd-k">{{ k }}</td>
              <td>{{ num(v) }}</td>
            </tr>
          </table>
          <p class="pd-note">{{ detail.notes }}</p>
        </div>
      </div>
    </template>
  </div>
</template>

<style scoped>
.pd { margin-top: 1rem; }
.pd-muted { color: var(--vp-c-text-3); font-size: 0.85rem; }
.pd-bar { display: flex; flex-wrap: wrap; align-items: center; gap: 0.4rem; margin-bottom: 0.6rem; }
.pd-input, .pd-sel {
  font-size: 0.82rem; padding: 0.35rem 0.6rem; border-radius: 999px;
  border: 1px solid var(--vp-c-divider); background: var(--vp-c-bg); color: var(--vp-c-text-1);
  outline: none;
}
.pd-input { width: 190px; }
.pd-input:focus { border-color: var(--vp-c-brand-1); }
.pd-btn {
  font-size: 0.8rem; padding: 0.35rem 0.7rem; border-radius: 999px; cursor: pointer;
  border: 1px solid var(--vp-c-divider); background: var(--vp-c-bg); color: var(--vp-c-text-2);
}
.pd-chip {
  font-size: 0.8rem; padding: 0.3rem 0.65rem; border-radius: 999px; cursor: pointer;
  border: 1px solid var(--vp-c-divider); background: var(--vp-c-bg); color: var(--vp-c-text-2);
}
.pd-chip.sm { font-size: 0.75rem; padding: 0.2rem 0.5rem; }
.pd-chip.on {
  border-color: var(--vp-c-brand-1); background: var(--vp-c-brand-1); color: #fff; font-weight: 600;
}
.pd-sep { width: 1px; height: 18px; background: var(--vp-c-divider); margin: 0 0.3rem; }
.pd-count { margin-left: auto; font-size: 0.78rem; color: var(--vp-c-text-3); }

.pd-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(190px, 1fr)); gap: 0.7rem; }
.pd-card {
  border: 1px solid var(--vp-c-divider); border-radius: 8px; overflow: hidden;
  background: var(--vp-c-bg); display: flex; flex-direction: column;
  transition: box-shadow 0.2s, transform 0.2s, border-color 0.2s;
}
.pd-card:hover {
  transform: translateY(-2px); border-color: var(--vp-c-brand-1);
  box-shadow: 0 10px 24px rgba(0, 0, 0, 0.09);
}
.pd-img {
  position: relative; height: 96px; display: flex; align-items: center; justify-content: center;
  background: var(--vp-c-bg-alt); border-bottom: 1px solid var(--vp-c-divider);
}
.pd-img img { max-height: 84px; max-width: 88%; object-fit: contain; mix-blend-mode: multiply; }
html.dark .pd-img img { mix-blend-mode: normal; background: #fff; border-radius: 4px; padding: 2px; }
.pd-tier {
  position: absolute; top: 5px; right: 5px; font-size: 0.62rem; font-weight: 700;
  padding: 1px 5px; border-radius: 999px; background: var(--vp-c-default-soft);
  color: var(--vp-c-text-2);
}
.pd-tier.a { background: var(--vp-c-brand-soft); color: var(--vp-c-brand-1); }
.pd-sub { position: absolute; top: 5px; left: 5px; font-size: 0.62rem; color: var(--vp-c-text-3); }
.pd-body { padding: 0.5rem 0.6rem 0.55rem; display: flex; flex-direction: column; gap: 0.2rem; }
.pd-model {
  font-size: 0.86rem; font-weight: 600; color: var(--vp-c-text-1);
  text-decoration: none;
}
a.pd-model:hover { color: var(--vp-c-brand-1); text-decoration: underline; }
.pd-vendor { font-size: 0.72rem; color: var(--vp-c-text-3); }
.pd-chips { display: flex; flex-wrap: wrap; gap: 3px; margin-top: 0.15rem; }
.pd-chips span {
  font-size: 0.66rem; padding: 1px 5px; border-radius: 4px;
  background: var(--vp-c-brand-soft); color: var(--vp-c-brand-1);
}
.pd-chips b { font-variant-numeric: tabular-nums; }
.pd-foot {
  display: flex; align-items: center; justify-content: space-between;
  margin-top: 0.35rem; padding-top: 0.3rem; border-top: 1px solid var(--vp-c-divider);
}
.pd-price { font-size: 0.76rem; color: var(--vp-c-text-1); font-variant-numeric: tabular-nums; }
.pd-acts { display: flex; gap: 0.4rem; }
.pd-link {
  font-size: 0.72rem; border: none; background: none; padding: 0; cursor: pointer;
  color: var(--vp-c-brand-1);
}
.pd-link:hover { text-decoration: underline; }

.pd-compare {
  border: 1px solid var(--vp-c-brand-1); border-radius: 8px; padding: 0.6rem 0.7rem;
  margin-bottom: 0.7rem; background: var(--vp-c-brand-soft); overflow-x: auto;
}
.pd-compare-head {
  display: flex; justify-content: space-between; font-size: 0.8rem; font-weight: 600;
  color: var(--vp-c-brand-1); margin-bottom: 0.35rem;
}
.pd-compare table { border-collapse: collapse; font-size: 0.76rem; width: 100%; }
.pd-compare th, .pd-compare td {
  border: 1px solid var(--vp-c-divider); padding: 3px 8px; text-align: left;
  white-space: nowrap; font-variant-numeric: tabular-nums;
}
.pd-compare th { background: var(--vp-c-bg); }
.pd-k { color: var(--vp-c-text-3); }

.pd-modal {
  position: fixed; inset: 0; background: rgba(0, 0, 0, 0.35); z-index: 60;
  display: flex; align-items: center; justify-content: center; padding: 1rem;
}
.pd-panel {
  background: var(--vp-c-bg); border: 1px solid var(--vp-c-divider); border-radius: 10px;
  padding: 0.9rem 1rem; max-width: 520px; width: 100%; max-height: 80vh; overflow: auto;
  box-shadow: 0 16px 40px rgba(0, 0, 0, 0.25);
}
.pd-panel-head {
  display: flex; align-items: baseline; gap: 0.5rem; margin-bottom: 0.5rem;
}
.pd-panel-head b { font-size: 0.95rem; color: var(--vp-c-text-1); }
.pd-panel-head .pd-link { margin-left: auto; }
.pd-specs { border-collapse: collapse; width: 100%; font-size: 0.78rem; }
.pd-specs td {
  border-bottom: 1px solid var(--vp-c-divider); padding: 3px 6px;
  font-variant-numeric: tabular-nums;
}
.pd-note { font-size: 0.74rem; color: var(--vp-c-text-3); margin-top: 0.6rem; line-height: 1.6; }
</style>
