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

export function partHref(p: { category: string; slug: string }): string {
  return withBase(`/parts/${p.category}/${p.slug}.html`)
}

/** 当前有效的优惠价：优先数值型 price，忽略无标价的活动。 */
export function bestOfferPrice(offers?: Array<Record<string, unknown>> | null): number | null {
  const today = new Date().toISOString().slice(0, 10)
  const prices = (offers ?? [])
    .filter(o => {
      const offer = o as { demo?: boolean; expires?: string | null; price?: unknown }
      return !offer.demo && (!offer.expires || offer.expires >= today)
        && offer.price !== null && offer.price !== undefined
        && Number.isFinite(Number(offer.price))
    })
    .map(o => Number((o as { price?: unknown }).price))
  return prices.length ? Math.min(...prices) : null
}

/** 有优惠价用优惠价，否则用参考价。 */
export function effectivePrice(
  price?: number | null,
  offers?: Array<Record<string, unknown>> | null,
): number | null {
  const offer = bestOfferPrice(offers)
  if (offer !== null) return offer
  return typeof price === 'number' && Number.isFinite(price) ? price : null
}
