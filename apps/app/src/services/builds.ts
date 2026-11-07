import type { BuildSummary, SpecFact } from '@robowiki/core'

import { API_ORIGIN, absoluteUrl } from './api'

/** 列表返回 BuildSummary，详情额外带 specs；这里放宽成同一个视图类型。 */
export type BuildView = BuildSummary & { specs?: Record<string, unknown> }

/** specs 里只展示原始标量值；对象 / 数组是派生结构，不当作参数展示。 */
export function specText(value: unknown): string {
  if (value === null || value === undefined) return ''
  if (typeof value === 'boolean') return value ? '是' : '否'
  if (typeof value === 'number') return Number.isFinite(value) ? String(value) : ''
  if (typeof value === 'string') return value.trim()
  return ''
}

export function rawSpecs(build: BuildView | null): SpecFact[] {
  if (!build || !build.specs) return []
  return Object.entries(build.specs)
    .map(([key, value]) => ({ key, label: key, value: specText(value) }))
    .filter((item) => item.value)
}

export function buildFacts(build: BuildView | null): SpecFact[] {
  if (!build) return []
  const given = (build.key_specs || []).filter((item) => item && item.label && item.value)
  return given.length ? given.slice(0, 8) : rawSpecs(build).slice(0, 8)
}

export function buildImage(build: BuildView | null): string {
  if (!build) return ''
  return absoluteUrl(build.image_url || '')
}

export function buildPrice(build: BuildView | null): string {
  if (!build) return ''
  const price = build.price_cny
  if (price === null || price === undefined || !Number.isFinite(Number(price))) return '询价'
  return `¥${Number(price).toLocaleString('zh-CN')}`
}

export function buildSubtype(build: BuildView | null): string {
  if (!build) return ''
  return build.subtype_label || build.subtype || ''
}

/** web_path 是站内相对路径；没有时返回空串，由调用方隐藏入口。 */
export function buildWebUrl(build: BuildView | null): string {
  const path = String(build?.web_path || '').trim()
  if (!path) return ''
  if (/^https?:\/\//i.test(path)) return path
  return `${API_ORIGIN}${path.startsWith('/') ? '' : '/'}${path}`
}
