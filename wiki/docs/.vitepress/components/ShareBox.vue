<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { useData, useRoute, withBase } from 'vitepress'
import QRCode from 'qrcode'
import { canonical, findShareEntry, shareImage, shareJsonPath, type ShareEntry } from '../lib/share'

//: 页面 frontmatter 里的分享图（部件=产品图，材质=默认 OG），由 pipeline 写入。
const { page } = useData()
const route = useRoute()

const entry = ref<ShareEntry | null>(null)
/** 刚复制的是哪一项：只用来在按钮上打勾，不再改按钮文案。
 *  之前按钮和读屏状态同时写「已复制」，视觉和读屏都会念两遍。 */
const copied = ref<'link' | 'text' | ''>('')
const status = ref('')
const qrEl = ref<HTMLCanvasElement | null>(null)
const qrFailed = ref(false)
const drawing = ref(false)
/** Web Share API 只在部分浏览器可用；不支持时不显示「系统分享」，避免点了像坏了。 */
const canWebShare = ref(false)
/** 移动端才有系统分享面板（微信/QQ 都在里面）；桌面端只给二维码说明。 */
const isMobile = ref(false)
/** 点过「微信」后高亮二维码区，告诉桌面用户扫码在哪。 */
const wechatHint = ref(false)
let flashTimer: number | undefined
let statusTimer: number | undefined
let loadSeq = 0

async function loadEntry(pathname: string): Promise<ShareEntry | null> {
  // 先直查当前页那张 1KB 的分享卡；找不到再退回 165KB 索引。
  const direct = shareJsonPath(pathname)
  if (direct) {
    try {
      const r = await fetch(withBase(direct))
      if (r.ok) {
        const d = await r.json()
        return {
          id: d.id, path: pathname.replace(/\.html$/, ''), url: d.canonical_url,
          json: direct, title: d.title, summary: d.summary,
          source_tier: d.source_tier, verified: d.verified,
          last_checked: d.last_checked, data_version: d.data_version,
          copy_text: d.copy_text, image_url: d.image_url || null,
        }
      }
    } catch { /* 退回索引 */ }
  }
  return findShareEntry(pathname)
}

async function refreshEntry() {
  const seq = ++loadSeq
  const p = typeof window !== 'undefined' ? window.location.pathname : ''
  if (!p.startsWith('/parts/') && !p.startsWith('/materials/')) {
    entry.value = null
    return
  }
  // 客户端路由连续切换时只认最后一次结果，避免慢请求把旧页数据写回来。
  const next = await loadEntry(p)
  if (seq === loadSeq) entry.value = next
}

onMounted(() => {
  canWebShare.value = typeof navigator.share === 'function'
  isMobile.value = /Android|iPhone|iPad|iPod|Mobile|HarmonyOS/i.test(navigator.userAgent)
  void refreshEntry()
})

// VitePress 的 doc-after 插槽在客户端路由切换时不会重建组件；
// 必须监听当前页面路径，否则分享卡会继续显示上一页的标题和参数。
watch(() => route.path, () => { void refreshEntry() })

watch([entry, qrEl], async ([e, el]) => {
  if (!e || !el) return
  try {
    await QRCode.toCanvas(el, canonical(e), { width: 132, margin: 1, color: { dark: '#0b1220', light: '#ffffff' } })
    qrFailed.value = false
  } catch {
    // 二维码画不出来时，可见的规范链接仍然可用，不能让整块分享功能消失。
    qrFailed.value = true
  }
}, { immediate: true })

const shareNoun = computed(() => (route.path.startsWith('/materials/') ? '材料 / 工艺' : '部件'))

const shareUrl = computed(() => (entry.value ? canonical(entry.value) : ''))

/** 页面自己的分享图；pipeline 在部件页写产品图，材质页写默认 OG。 */
const pageImage = computed(() => {
  const v = page.value?.frontmatter?.image
  return typeof v === 'string' ? v : ''
})

/** QQ pics / 分享图：分享卡产品图 → 页面 frontmatter → 默认 OG，不写死。 */
const shareImageUrl = computed(() => shareImage(entry.value, pageImage.value))

/** QQ / 系统分享的摘要：含来源等级与数据版本；链接由各自的 url 字段带。 */
const shareSummary = computed(() => {
  const e = entry.value
  if (!e) return ''
  const meta = [
    e.source_tier ? `${e.source_tier} 级来源` : '',
    e.verified && e.source_tier === 'A' ? '已核对' : '',
    e.data_version ? `数据 ${e.data_version}` : '',
  ].filter(Boolean).join(' · ')
  return [e.summary, meta].filter(Boolean).join('\n')
})

const copyText = computed(() => {
  if (!entry.value) return ''
  // 优先用构建期生成的 copy_text：它带来源等级与数据版本，比现场拼更稳。
  if (entry.value.copy_text) return entry.value.copy_text
  const e = entry.value
  const source = [
    e.source_tier ? `${e.source_tier} 级来源` : '',
    e.verified && e.source_tier === 'A' ? '已核对' : '',
    e.last_checked ? `最近核对 ${e.last_checked}` : '',
    e.data_version ? `数据 ${e.data_version}` : '',
  ].filter(Boolean).join(' · ')
  return [e.title, e.summary, source, canonical(e)].filter(Boolean).join('\n')
})

/** 先写剪贴板；非 HTTPS / 老浏览器退回 execCommand。返回是否真的成功。 */
async function writeClipboard(text: string): Promise<boolean> {
  if (!text) return false
  try {
    await navigator.clipboard.writeText(text)
    return true
  } catch { /* 继续回退 */ }
  try {
    const ta = document.createElement('textarea')
    ta.value = text
    ta.setAttribute('readonly', '')
    ta.style.position = 'fixed'
    ta.style.opacity = '0'
    document.body.appendChild(ta)
    ta.select()
    const ok = document.execCommand('copy')
    ta.remove()
    return ok
  } catch {
    return false
  }
}

function flash(kind: 'link' | 'text') {
  window.clearTimeout(flashTimer)
  copied.value = kind
  flashTimer = window.setTimeout(() => (copied.value = ''), 1800)
}

/** 读屏播报单独一条：视觉按钮只打勾，不重复写「已复制」。 */
function announce(msg: string) {
  window.clearTimeout(statusTimer)
  status.value = ''
  statusTimer = window.setTimeout(() => (status.value = msg), 40)
}

async function copyLink() {
  if (!entry.value) return
  const ok = await writeClipboard(shareUrl.value)
  if (ok) {
    flash('link')
    announce('链接已复制')
  } else {
    announce('复制失败，请长按上方链接手动复制')
  }
}

async function copyCardText() {
  if (!entry.value) return
  const ok = await writeClipboard(copyText.value)
  if (ok) {
    flash('text')
    announce('分享文案已复制（含型号、来源与数据版本）')
  } else {
    announce('复制失败，请手动选择上方文案')
  }
}

async function share() {
  const e = entry.value
  if (!e) return
  if (navigator.share) {
    try {
      await navigator.share({ title: e.title, text: shareSummary.value, url: shareUrl.value })
      announce('已打开系统分享')
      return
    } catch (err: any) {
      // 用户点取消不是失败，别顺手复制一遍让人以为分享成功了。
      if (err && (err.name === 'AbortError' || err.name === 'NotAllowedError')) return
    }
  }
  await copyLink()
}

/** QQ 官方分享面板，不需要 AppID / 签名，也不会被当成营销外链。
 *  参数照官方 widget：url / title / summary / pics（pics 必须是绝对图片地址）。 */
function shareToQQ() {
  const e = entry.value
  if (!e) return
  const q = new URLSearchParams({
    url: shareUrl.value,
    title: e.title,
    summary: shareSummary.value,
    pics: shareImageUrl.value,
  })
  const win = window.open(
    `https://connect.qq.com/widget/shareqq/index.html?${q.toString()}`,
    '_blank',
    'width=760,height=620',
  )
  if (!win) {
    announce('浏览器拦截了 QQ 分享弹窗，请允许弹窗后重试，或复制链接手动分享')
    return
  }
  try { win.opener = null } catch { /* 个别浏览器不允许改跨域窗口 */ }
  announce('已打开 QQ 分享')
}

/** 微信没有可信的 Web 分享 URL（JS-SDK 需要网站应用 AppID + 签名，先不做）。
 *  移动端走系统分享面板（微信/QQ 可选）；桌面端给二维码和右上角分享说明。 */
async function shareToWeChat() {
  const e = entry.value
  if (!e) return
  if (isMobile.value && canWebShare.value) {
    try {
      await navigator.share({ title: e.title, text: shareSummary.value, url: shareUrl.value })
      announce('已打开系统分享，可选微信或 QQ')
      return
    } catch (err: any) {
      if (err && (err.name === 'AbortError' || err.name === 'NotAllowedError')) return
    }
  }
  wechatHint.value = true
  announce('电脑端请用微信扫二维码；在微信里打开时点右上角 ··· 分享')
}

function wrap(ctx: CanvasRenderingContext2D, text: string, maxWidth: number) {
  const lines: string[] = []
  let line = ''
  for (const ch of Array.from(text)) {
    const next = line + ch
    if (ctx.measureText(next).width > maxWidth && line) {
      // URL 在 / 或 - 处断，别把型号名劈成两半
      const cut = Math.max(line.lastIndexOf('/'), line.lastIndexOf('-'), line.lastIndexOf(' '))
      if (cut > 8) {
        lines.push(line.slice(0, cut + 1))
        line = line.slice(cut + 1) + ch
      } else {
        lines.push(line)
        line = ch
      }
    } else {
      line = next
    }
  }
  if (line) lines.push(line)
  return lines
}

async function downloadCard() {
  const e = entry.value
  if (!e || drawing.value) return
  drawing.value = true
  try {
    const W = 1080, H = 1440
    const canvas = document.createElement('canvas')
    canvas.width = W
    canvas.height = H
    const ctx = canvas.getContext('2d')!
    const sans = '"Noto Sans SC", "PingFang SC", "Microsoft YaHei", sans-serif'

    ctx.fillStyle = '#0b1220'
    ctx.fillRect(0, 0, W, H)
    const grad = ctx.createLinearGradient(0, 0, W, 0)
    grad.addColorStop(0, '#2563eb')
    grad.addColorStop(1, '#06b6d4')
    ctx.fillStyle = grad
    ctx.fillRect(0, 0, W, 14)

    ctx.fillStyle = '#e5e7eb'
    ctx.font = `bold 40px ${sans}`
    ctx.fillText('RoboWiki', 80, 110)
    ctx.fillStyle = '#94a3b8'
    ctx.font = `26px ${sans}`
    ctx.fillText('可核对的机器人硬件目录', 80, 152)

    let y = 250
    ctx.fillStyle = '#ffffff'
    ctx.font = `bold 56px ${sans}`
    for (const line of wrap(ctx, e.title, 920).slice(0, 2)) {
      ctx.fillText(line, 80, y)
      y += 72
    }

    const tier = e.source_tier ? `${e.source_tier} 级来源` : '来源待补'
    const checkWord = e.source_tier === 'A' && e.verified ? '已核对' : '最近检查'
    const checked = e.last_checked ? ` · ${checkWord} ${e.last_checked}` : ''
    ctx.fillStyle = '#67e8f9'
    ctx.font = `28px ${sans}`
    ctx.fillText(`${tier}${checked}`, 80, y + 6)
    y += 62

    ctx.fillStyle = '#dbeafe'
    ctx.font = `34px ${sans}`
    for (const line of wrap(ctx, e.summary || '参数与来源见页面', 900).slice(0, 3)) {
      ctx.fillText(line, 80, y)
      y += 48
    }

    const detail = await fetch(withBase(e.json))
      .then((r) => (r.ok ? r.json() : null))
      .catch(() => null)
    const params: { label: string; value: string }[] = detail?.params || []
    if (params.length) {
      y += 34
      ctx.fillStyle = '#94a3b8'
      ctx.font = `26px ${sans}`
      ctx.fillText('关键参数', 80, y)
      y += 40
      params.slice(0, 6).forEach((p, i) => {
        const col = i % 2
        const row = Math.floor(i / 2)
        const x = 80 + col * 470
        const py = y + row * 88
        ctx.strokeStyle = 'rgba(148,163,184,.25)'
        ctx.lineWidth = 2
        ctx.strokeRect(x, py - 38, 430, 66)
        ctx.fillStyle = '#94a3b8'
        ctx.font = `24px ${sans}`
        ctx.fillText(p.label, x + 18, py)
        ctx.fillStyle = '#f8fafc'
        ctx.font = `bold 30px ${sans}`
        const lines = wrap(ctx, p.value, 240)
        const val = lines.length > 1 ? `${lines[0].slice(0, -1)}…` : lines[0] || ''
        ctx.fillText(val, x + 160, py)
      })
      y += Math.ceil(Math.min(params.length, 6) / 2) * 88
    }

    // 适用场景只占剩下的空间：参数多时收成一行，绝不画到二维码上。
    const cases: string[] = detail?.use_cases || []
    if (cases.length && y < H - 460) {
      y += 30
      ctx.fillStyle = '#94a3b8'
      ctx.font = `26px ${sans}`
      ctx.fillText('适用场景', 80, y)
      y += 42
      ctx.fillStyle = '#cbd5e1'
      ctx.font = `28px ${sans}`
      const text = cases.slice(0, 4).join(' · ')
      const maxLines = params.length >= 5 ? 1 : 2
      for (const line of wrap(ctx, text, 900).slice(0, maxLines)) {
        ctx.fillText(line, 80, y)
        y += 40
      }
    }

    // 数据版本固定在页脚上方的内容区，避免和右侧二维码/左下 URL 叠在一起。
    y = Math.min(y + 30, H - 380)
    ctx.fillStyle = '#94a3b8'
    ctx.font = `28px ${sans}`
    ctx.fillText('数据版本', 80, y)
    ctx.fillStyle = '#e5e7eb'
    ctx.font = `bold 30px ${sans}`
    ctx.fillText(e.data_version || '—', 230, y)

    let qrImg: HTMLImageElement | null = null
    try {
      const qrUrl = await QRCode.toDataURL(canonical(e), { width: 240, margin: 1 })
      qrImg = await new Promise<HTMLImageElement>((resolve, reject) => {
        const el = new Image()
        el.onload = () => resolve(el)
        el.onerror = reject
        el.src = qrUrl
      })
    } catch {
      qrImg = null
    }
    if (qrImg) {
      ctx.fillStyle = '#ffffff'
      ctx.fillRect(W - 80 - 250, H - 80 - 250, 250, 250)
      ctx.drawImage(qrImg, W - 75 - 240, H - 75 - 240, 240, 240)
    }

    ctx.fillStyle = '#e5e7eb'
    ctx.font = `30px ${sans}`
    const urlLines = wrap(ctx, canonical(e), W - 160 - 290).slice(0, 3)
    urlLines.forEach((line, i) => ctx.fillText(line, 80, H - 170 + i * 40))
    ctx.fillStyle = '#64748b'
    ctx.font = `24px ${sans}`
    ctx.fillText('扫码或输入地址查看来源、实测与兼容信息', 80, H - 64)

    const blob = await new Promise<Blob | null>((res) => canvas.toBlob(res, 'image/png'))
    if (!blob) return
    const a = document.createElement('a')
    a.href = URL.createObjectURL(blob)
    a.download = `${e.id || 'part'}-share.png`
    a.click()
    window.setTimeout(() => URL.revokeObjectURL(a.href), 10_000)
  } finally {
    drawing.value = false
  }
}
</script>

<template>
  <section v-if="entry" class="rw-share" :aria-label="`分享这个${shareNoun}`">
    <div class="rw-share-head">
      <b>分享这个{{ shareNoun }}</b>
      <span>{{ entry.data_version }}</span>
    </div>
    <p class="rw-share-text">{{ entry.summary }}</p>
    <div class="rw-share-body">
      <div class="rw-share-actions">
        <button type="button" :class="{ done: copied === 'link' }" @click="copyLink">
          <span v-if="copied === 'link'" class="rw-share-tick" aria-hidden="true">✓</span>
          复制链接
        </button>
        <button type="button" class="ghost" :class="{ done: copied === 'text' }" @click="copyCardText">
          <span v-if="copied === 'text'" class="rw-share-tick" aria-hidden="true">✓</span>
          复制文案
        </button>
        <button type="button" class="ghost" @click="shareToWeChat">微信</button>
        <button type="button" class="ghost" @click="shareToQQ">QQ</button>
        <button v-if="canWebShare" type="button" class="ghost" @click="share">系统分享</button>
        <button type="button" class="ghost" @click="downloadCard" :disabled="drawing">
          {{ drawing ? '生成中…' : '下载分享卡' }}
        </button>
      </div>
      <div class="rw-share-qrbox" :class="{ 'is-hint': wechatHint }">
        <canvas v-show="!qrFailed" ref="qrEl" class="rw-share-qr" role="img" aria-label="页面二维码"></canvas>
        <a v-if="qrFailed" class="rw-share-qr-alt" :href="shareUrl">二维码生成失败，点这里打开</a>
        <a class="rw-share-url" :href="shareUrl" :title="shareUrl">{{ shareUrl }}</a>
        <p class="rw-share-wechat-tip">
          {{ isMobile && canWebShare ? '点「微信」用系统分享，也可扫码转发' : '微信扫码，或在微信里点右上角 ··· 分享' }}
        </p>
      </div>
    </div>
    <span class="rw-share-status" role="status" aria-live="polite">{{ status }}</span>
  </section>
</template>

<style scoped>
.rw-share {
  margin: 2rem 0 1rem;
  padding: 1rem 1.1rem;
  border: 1px solid var(--vp-c-divider);
  border-radius: 12px;
  background: var(--vp-c-bg-soft);
}
.rw-share-head {
  display: flex;
  justify-content: space-between;
  gap: 1rem;
  font-size: 0.85rem;
  color: var(--vp-c-text-2);
}
.rw-share-text {
  margin: 0.5rem 0 0.8rem;
  font-size: 0.95rem;
}
.rw-share-body {
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  gap: 1rem;
  flex-wrap: wrap;
}
.rw-share-actions {
  display: flex;
  gap: 0.6rem;
  flex-wrap: wrap;
}
.rw-share-qr {
  width: 92px;
  height: 92px;
  border-radius: 6px;
  background: #fff;
}
.rw-share-qrbox {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 0.25rem;
  max-width: 260px;
}
.rw-share-url {
  max-width: 100%;
  font-size: 0.68rem;
  line-height: 1.5;
  color: var(--vp-c-text-3);
  text-decoration: none;
  overflow-wrap: anywhere;
}
.rw-share-url:hover { color: var(--vp-c-brand-1); text-decoration: underline; }
.rw-share-qr-alt { font-size: 0.74rem; color: var(--vp-c-brand-1); }
.rw-share-qrbox.is-hint .rw-share-qr {
  box-shadow: 0 0 0 3px var(--vp-c-brand-1);
}
.rw-share-wechat-tip {
  margin: 0.2rem 0 0;
  font-size: 0.7rem;
  line-height: 1.45;
  color: var(--vp-c-text-2);
  text-align: right;
}
.rw-share-tick { margin-right: 0.25rem; font-size: 0.85em; }
.rw-share button.done { box-shadow: inset 0 0 0 2px rgba(255, 255, 255, 0.65); }
.rw-share button.ghost.done { box-shadow: inset 0 0 0 2px currentColor; }
@media (max-width: 560px) {
  .rw-share-qrbox { align-items: flex-start; max-width: 100%; }
  .rw-share-qr { width: 84px; height: 84px; }
  .rw-share-wechat-tip { text-align: left; }
}
.rw-share button {
  border: 1px solid var(--vp-c-brand-1);
  background: var(--vp-c-brand-1);
  color: #fff;
  padding: 0.45rem 0.9rem;
  border-radius: 8px;
  font-size: 0.85rem;
  cursor: pointer;
}
.rw-share button.ghost {
  background: transparent;
  color: var(--vp-c-brand-1);
}
.rw-share button:disabled {
  opacity: 0.5;
  cursor: default;
}
.rw-share-status {
  position: absolute;
  width: 1px; height: 1px;
  padding: 0; margin: -1px;
  overflow: hidden;
  clip: rect(0, 0, 0, 0);
  white-space: nowrap;
  border: 0;
}
</style>
