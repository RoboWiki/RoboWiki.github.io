import type { PartSummary } from '@robowiki/core'

import { api, absoluteUrl } from './api'

export type SpecFact = { key: string; label: string; value: string }

/**
 * 列表走 compact=true 的轻量投影（不返回完整 specs），
 * 详情接口返回完整对象；两者共用这个视图类型。
 */
export type PartView = PartSummary & {
  category_label?: string
  subtype_label?: string
  vendor_cn?: string
  title?: string
  source_tier?: string
  web_path?: string
  price_cny?: number | null
  image_url?: string | null
  key_specs?: SpecFact[]
  rating_count?: number
  rating_avg?: number | null
  derived?: Record<string, unknown>
}

export type PartListResponse = {
  total: number
  limit: number
  offset: number
  items: PartView[]
}

/** GET /parts?limit=20&offset=0&compact=true —— 列表页固定使用 compact 投影。 */
export function listPartCards(params: {
  q?: string
  category?: string
  limit: number
  offset: number
}): Promise<PartListResponse> {
  const query: string[] = []
  if (params.q) query.push(`q=${encodeURIComponent(params.q)}`)
  if (params.category) query.push(`category=${encodeURIComponent(params.category)}`)
  query.push(`limit=${params.limit}`, `offset=${params.offset}`, 'compact=true')
  return api.request<PartListResponse>(`/parts?${query.join('&')}`)
}


function text(value: unknown): string {
  if (value === null || value === undefined) return ''
  if (typeof value === 'boolean') return value ? '是' : '否'
  if (typeof value === 'number') return Number.isFinite(value) ? String(value) : ''
  if (typeof value === 'string') return value
  return ''
}

/** 详情页的关键参数：优先后端挑好的 key_specs，缺失时退回 specs 原始键值。 */
export function partFacts(part: PartView | null): SpecFact[] {
  if (!part) return []
  const given = (part.key_specs || []).filter((f) => f && f.label && f.value)
  if (given.length) return given.slice(0, 8)

  const specs = part.specs || {}
  return Object.entries(specs)
    .filter(([, value]) => ['string', 'number', 'boolean'].includes(typeof value))
    .map(([key, value]) => ({ key, label: key, value: text(value) }))
    .filter((f) => f.value)
    .slice(0, 8)
}

export function partImage(part: PartView | null): string {
  if (!part) return ''
  return absoluteUrl(part.image_url || part.image || '')
}

export function partPrice(part: PartView | null): string {
  if (!part) return ''
  const price = part.price_cny ?? part.price
  if (price === null || price === undefined || !Number.isFinite(Number(price))) return '价格未知'
  return `¥${Number(price).toLocaleString('zh-CN')}`
}

export function partCategoryLabel(part: PartView | null): string {
  if (!part) return ''
  const subtype = part.subtype_label || part.subtypeLabel
  return part.category_label || subtype || part.category || ''
}

/** compact 列表用 rating_avg/rating_count，详情用嵌套 rating 对象。 */
export function partRating(part: PartView | null): { avg: number | null; count: number } {
  if (!part) return { avg: null, count: 0 }
  const count = part.rating_count ?? part.rating?.count ?? 0
  const avg = part.rating_avg ?? part.rating?.avg ?? null
  return { avg: avg === undefined ? null : avg, count }
}

/**
 * 讨论串的 page 键必须与网页一致（VitePress 路径去扩展名），
 * 规则与 clients/wechat-mini 相同，直接使用服务端 web_path。
 */
export function partPageKey(part: PartView | null): string {
  if (!part) return ''
  const web = String(part.web_path || '').replace(/^\/+|\/+$/g, '').replace(/\.html$/, '')
  if (web) return web
  const slug = String(part.id || '').replace(/[^A-Za-z0-9]+/g, '-')
  return `parts/${part.category || 'unknown'}/${slug}`
}
