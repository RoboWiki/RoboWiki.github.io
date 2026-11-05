import { clsx, type ClassValue } from 'clsx'
import { twMerge } from 'tailwind-merge'

export const BASE = import.meta.env.BASE_URL.replace(/\/$/, '')

/** 兼容 GitHub Pages 项目页与 /next/ 预览前缀；外链原样返回。 */
export function withBase(path: string): string {
  if (/^https?:\/\//i.test(path) || path.startsWith('//') || path.startsWith('#')) return path
  return `${BASE}${path.startsWith('/') ? path : `/${path}`}`
}

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

export function formatPrice(v?: number | null): string {
  return v == null ? '询价' : `¥${v.toLocaleString('zh-CN')}`
}

export function partHref(p: { category: string; id: string }): string {
  return withBase(`/parts/${p.category}/${p.id}.html`)
}
