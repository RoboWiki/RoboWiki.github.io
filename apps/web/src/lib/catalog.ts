import raw from '../../../../wiki/docs/public/catalog.json'

export type CatalogPart = {
  id: string
  category: string
  subtype?: string
  subtypeLabel?: string
  vendor: string
  model: string
  tier?: string
  verified?: boolean
  price?: number | null
  image?: string | null
  rating?: { avg?: number | null; count?: number }
  tauPeak?: number | null
  tauRated?: number | null
  gear?: number | null
  mass?: number | null
  rpm?: number | null
  specs?: Record<string, unknown>
  notes?: string
  featured?: boolean
}

export const catalog = raw as {
  meta: { data_version?: string; generated_at?: string; record_count?: number }
  count: number
  parts: CatalogPart[]
  featured?: { ids?: string[]; updated_at?: string } | string[]
  categories?: { id: string; name: string; count?: number }[]
}

export const parts = catalog.parts

export const categoryLabel = (id: string) =>
  catalog.categories?.find(c => c.id === id)?.name || id

export const featuredParts = (() => {
  const ids = new Set((catalog.featured as any)?.ids || [])
  const picked = parts.filter(p => ids.has(p.id))
  return (picked.length ? picked : parts.filter(p => p.featured)).slice(0, 8)
})()

// catalog.json 的 categories 只有 id/name/subtypes，没有逐品类计数；
// 首页要展示「N 个」，按 parts 现算，避免所有卡片都写 0。
const categoryCounts = parts.reduce((acc, p) => {
  acc.set(p.category, (acc.get(p.category) || 0) + 1)
  return acc
}, new Map<string, number>())

export const topCategories = (catalog.categories || [])
  .map(c => ({ ...c, count: categoryCounts.get(c.id) ?? 0 }))
  .sort((a, b) => b.count - a.count)
  .slice(0, 8)

export function imageUrl(p: CatalogPart): string {
  if (!p.image) return ''
  return p.image.startsWith('http') ? p.image : `https://robowiki.org.cn${p.image}`
}
