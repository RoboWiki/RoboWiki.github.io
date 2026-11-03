<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { withBase } from 'vitepress'
import QRCode from 'qrcode'
import { canonical, findShareEntry, type ShareEntry } from '../lib/share'

const entry = ref<ShareEntry | null>(null)
const copied = ref(false)
const qrEl = ref<HTMLCanvasElement | null>(null)
const drawing = ref(false)

onMounted(async () => {
  // 只有部件/材质页有分享卡；别的页面别拖 165KB 的 share/index.json。
  const p = window.location.pathname
  if (!p.startsWith('/parts/') && !p.startsWith('/materials/')) return
  entry.value = await findShareEntry(p)
})

watch([entry, qrEl], async ([e, el]) => {
  if (!e || !el) return
  await QRCode.toCanvas(el, canonical(e), { width: 132, margin: 1, color: { dark: '#0b1220', light: '#ffffff' } })
}, { immediate: true })

const copyText = computed(() => {
  if (!entry.value) return ''
  return [
    entry.value.title,
    entry.value.summary,
    `${entry.value.data_version} · ${canonical(entry.value)}`,
  ].filter(Boolean).join('\n')
})

async function copy() {
  if (!entry.value) return
  try {
    await navigator.clipboard.writeText(copyText.value)
  } catch {
    const ta = document.createElement('textarea')
    ta.value = copyText.value
    document.body.appendChild(ta)
    ta.select()
    document.execCommand('copy')
    ta.remove()
  }
  copied.value = true
  window.setTimeout(() => (copied.value = false), 1600)
}

async function share() {
  if (!entry.value) return
  const url = canonical(entry.value)
  if (navigator.share) {
    try {
      await navigator.share({ title: entry.value.title, text: entry.value.summary, url })
      return
    } catch {
      /* 用户取消，回退到复制 */
    }
  }
  await copy()
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

    let y = 270
    ctx.fillStyle = '#ffffff'
    ctx.font = `bold 60px ${sans}`
    for (const line of wrap(ctx, e.title, 920).slice(0, 3)) {
      ctx.fillText(line, 80, y)
      y += 78
    }

    const tier = e.source_tier ? `${e.source_tier} 级来源` : '来源待补'
    const checkWord = e.source_tier === 'A' && e.verified ? '已核对' : '最近检查'
    const checked = e.last_checked ? ` · ${checkWord} ${e.last_checked}` : ''
    ctx.fillStyle = '#67e8f9'
    ctx.font = `28px ${sans}`
    ctx.fillText(`${tier}${checked}`, 80, y + 6)
    y += 74

    ctx.fillStyle = '#dbeafe'
    ctx.font = `36px ${sans}`
    for (const line of wrap(ctx, e.summary || '参数与来源见页面', 900).slice(0, 4)) {
      ctx.fillText(line, 80, y)
      y += 54
    }

    const detail = await fetch(withBase(e.json))
      .then((r) => (r.ok ? r.json() : null))
      .catch(() => null)
    const params: { label: string; value: string }[] = detail?.params || []
    if (params.length) {
      y += 46
      ctx.fillStyle = '#94a3b8'
      ctx.font = `26px ${sans}`
      ctx.fillText('关键参数', 80, y)
      y += 78
      params.slice(0, 6).forEach((p, i) => {
        const col = i % 2
        const row = Math.floor(i / 2)
        const x = 80 + col * 470
        const py = y + row * 96
        ctx.strokeStyle = 'rgba(148,163,184,.25)'
        ctx.lineWidth = 2
        ctx.strokeRect(x, py - 44, 430, 72)
        ctx.fillStyle = '#94a3b8'
        ctx.font = `24px ${sans}`
        ctx.fillText(p.label, x + 18, py)
        ctx.fillStyle = '#f8fafc'
        ctx.font = `bold 30px ${sans}`
        const lines = wrap(ctx, p.value, 250)
        const val = lines.length > 1 ? `${lines[0].slice(0, -1)}…` : lines[0] || ''
        ctx.fillText(val, x + 160, py)
      })
      y += Math.ceil(Math.min(params.length, 6) / 2) * 96
    }

    const cases: string[] = detail?.use_cases || []
    if (cases.length) {
      y += 10
      ctx.fillStyle = '#94a3b8'
      ctx.font = `26px ${sans}`
      ctx.fillText('适用场景', 80, y)
      y += 44
      ctx.fillStyle = '#cbd5e1'
      ctx.font = `28px ${sans}`
      const text = cases.slice(0, 4).join(' · ')
      for (const line of wrap(ctx, text, 900).slice(0, 2)) {
        ctx.fillText(line, 80, y)
        y += 42
      }
    }

    y += 26
    ctx.fillStyle = '#94a3b8'
    ctx.font = `28px ${sans}`
    ctx.fillText('数据版本', 80, y)
    ctx.fillStyle = '#e5e7eb'
    ctx.font = `bold 30px ${sans}`
    ctx.fillText(e.data_version, 230, y)
    y += 40

    const qrUrl = await QRCode.toDataURL(canonical(e), { width: 240, margin: 1 })
    const img = await new Promise<HTMLImageElement>((resolve, reject) => {
      const el = new Image()
      el.onload = () => resolve(el)
      el.onerror = reject
      el.src = qrUrl
    })
    ctx.fillStyle = '#ffffff'
    ctx.fillRect(W - 80 - 250, H - 80 - 250, 250, 250)
    ctx.drawImage(img, W - 75 - 240, H - 75 - 240, 240, 240)

    ctx.fillStyle = '#e5e7eb'
    ctx.font = `30px ${sans}`
    const urlLines = wrap(ctx, canonical(e), W - 160 - 270).slice(0, 3)
    urlLines.forEach((line, i) => ctx.fillText(line, 80, H - 150 + i * 40))
    ctx.fillStyle = '#64748b'
    ctx.font = `24px ${sans}`
    ctx.fillText('扫码或输入地址查看来源、实测与兼容信息', 80, H - 70)

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
  <section v-if="entry" class="rw-share" aria-label="分享这个部件">
    <div class="rw-share-head">
      <b>分享这个部件</b>
      <span>{{ entry.data_version }}</span>
    </div>
    <p class="rw-share-text">{{ entry.summary }}</p>
    <div class="rw-share-body">
      <div class="rw-share-actions">
        <button type="button" @click="copy">{{ copied ? '已复制' : '复制卡片' }}</button>
        <button type="button" class="ghost" @click="share">分享</button>
        <button type="button" class="ghost" @click="downloadCard" :disabled="drawing">
          {{ drawing ? '生成中…' : '下载分享卡' }}
        </button>
      </div>
      <canvas ref="qrEl" class="rw-share-qr" aria-label="页面二维码"></canvas>
    </div>
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
</style>
