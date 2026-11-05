import { absoluteUrl } from '@/services/api'

const MEDIA_RE =
  /(?:https?:\/\/[^\s<>"']*)?\/api\/v1\/media\/[0-9a-f]{32}(?:[?#][^\s<>"']*)?/gi
const IMAGE_RE =
  /https?:\/\/[^\s<>"'，。；！）】]+?\.(?:png|jpe?g|gif|webp|avif|bmp)(?:\?[^\s<>"'，。；！）】]*)?/gi
const MD_IMAGE_RE = /!\[[^\]]*\]\((https?:\/\/[^)\s]+)\)/g

export type CommentContent = {
  text: string
  images: string[]
}

/**
 * 评论正文是纯文本，图片以 URL 形式写在正文里（含站内 /api/v1/media 链接）。
 * 这里把图片 URL 抽出来单独渲染，正文只留文字，避免长链接撑坏行宽。
 */
export function parseCommentContent(body: string): CommentContent {
  const images: string[] = []
  const push = (url: string) => {
    const abs = absoluteUrl(url)
    if (abs && !images.includes(abs)) images.push(abs)
  }

  let text = String(body || '').replace(MD_IMAGE_RE, (_match, url: string) => {
    push(url)
    return ' '
  })

  const combined = new RegExp(`${MEDIA_RE.source}|${IMAGE_RE.source}`, 'gi')
  text = text.replace(combined, (match) => {
    push(match)
    return ' '
  })

  return {
    text: text.replace(/[ \t]+\n/g, '\n').replace(/\n{3,}/g, '\n\n').trim(),
    images: images.slice(0, 6),
  }
}

export function authorName(author?: { display_name?: string; handle?: string } | null): string {
  return author?.display_name || author?.handle || '匿名'
}

function pad(n: number): string {
  return n < 10 ? `0${n}` : String(n)
}

/** 统一成 YYYY-MM-DD HH:mm，避免 H5 / 小程序 Intl 差异。 */
export function formatTime(iso?: string | null): string {
  if (!iso) return ''
  const date = new Date(iso)
  if (Number.isNaN(date.getTime())) return ''
  return `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())} ${pad(
    date.getHours(),
  )}:${pad(date.getMinutes())}`
}
