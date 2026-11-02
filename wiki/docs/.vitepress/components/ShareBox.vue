<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { withBase } from 'vitepress'

type ShareEntry = {
  path: string
  json: string
  title: string
  summary: string
  data_version: string
}

const entry = ref<ShareEntry | null>(null)
const copied = ref(false)
let indexPromise: Promise<ShareEntry[]> | null = null

function normalize(path: string) {
  let p = path.replace(/\.html$/, '').replace(/\/+$/, '')
  return p || '/'
}

async function loadIndex(): Promise<ShareEntry[]> {
  if (!indexPromise) {
    indexPromise = fetch(withBase('/share/index.json'))
      .then((r) => (r.ok ? r.json() : []))
      .catch(() => [])
  }
  return indexPromise
}

onMounted(async () => {
  const here = normalize(window.location.pathname)
  const rows = await loadIndex()
  entry.value = rows.find((r) => normalize(r.path) === here) || null
})

const copyText = computed(() => {
  if (!entry.value) return ''
  return [
    entry.value.title,
    entry.value.summary,
    `${entry.value.data_version} · ${window.location.origin}${entry.value.path}`,
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
  const url = `${window.location.origin}${entry.value.path}`
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
</script>

<template>
  <section v-if="entry" class="rw-share" aria-label="分享这个部件">
    <div class="rw-share-head">
      <b>分享这个部件</b>
      <span>{{ entry.data_version }}</span>
    </div>
    <p class="rw-share-text">{{ entry.summary }}</p>
    <div class="rw-share-actions">
      <button type="button" @click="copy">{{ copied ? '已复制' : '复制卡片' }}</button>
      <button type="button" class="ghost" @click="share">分享</button>
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
.rw-share-actions {
  display: flex;
  gap: 0.6rem;
  flex-wrap: wrap;
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
</style>
