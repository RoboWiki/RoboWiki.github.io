import raw from '@/data/catalog.json'
import siteMeta from '@/data/site-meta.json'

export type PartBuild = {
  id: string
  slug: string
  name: string
  model?: string
  vendor?: string
  url: string
}

export type CatalogPart = {
  id: string
  slug: string
  category: string
  subtype?: string
  subtypeLabel?: string
  vendor: string
  model: string
  tier?: string
  verified?: boolean
  price?: number | null
  image?: string | null
  builds?: PartBuild[]
  rating?: { avg?: number | null; count?: number }
  offers?: Array<Record<string, unknown>>
  offer?: Record<string, unknown> | null
  tauPeak?: number | null
  tauRated?: number | null
  gear?: number | null
  mass?: number | null
  rpm?: number | null
  od?: number | null
  len?: number | null
  soc?: string | null
  npuTops?: number | null
  ramGb?: number | null
  mcu?: string | null
  can?: number | null
  iface?: string | null
  bits?: number | null
  odrHz?: number | null
  fps?: number | null
  depthRange?: number | null
  rangeM?: number | null
  specs?: Record<string, unknown>
  notes?: string
  featured?: boolean
}

export type CategoryGroup = { key: string; label: string; slugs: string[] }

export const catalog = raw as {
  meta: { data_version?: string; generated_at?: string; record_count?: number }
  count: number
  parts: CatalogPart[]
  groups?: Record<string, CategoryGroup[]>
  featured?: { ids?: string[]; updated_at?: string } | string[]
  categories?: { id: string; name: string; hint?: string; subtypes?: Record<string, string> }[]
}

export const dataVersion = siteMeta.data_version || catalog.meta?.data_version || ''
export const parts = catalog.parts
export const categoryGroups = catalog.groups || {}

export const categoryLabel = (id: string) =>
  catalog.categories?.find(c => c.id === id)?.name || id

export const featuredParts = (() => {
  const ids = ((catalog.featured as any)?.ids || []) as string[]
  const byId = new Map(parts.map(p => [p.id, p]))
  const picked = ids.map(id => byId.get(id)).filter((p): p is CatalogPart => Boolean(p))
  return (picked.length ? picked : parts.filter(p => p.featured)).slice(0, 8)
})()

const categoryCounts = parts.reduce((acc, p) => {
  acc.set(p.category, (acc.get(p.category) || 0) + 1)
  return acc
}, new Map<string, number>())

export const topCategories = (catalog.categories || [])
  // 设备库独立成页，部件库的分类入口不再包含 equipment
  .filter(c => c.id !== 'equipment')
  .map(c => ({ ...c, count: categoryCounts.get(c.id) ?? 0 }))
  .sort((a, b) => b.count - a.count)
  .slice(0, 8)

/** 产品图随站点一起发布在 public/parts，同源引用即可。 */
export function imageUrl(p: CatalogPart): string {
  const value = String(p.image || '').trim()
  if (!value) return ''
  return /^(https?:)?\/\//i.test(value) ? value : value.startsWith('/') ? value : `/${value}`
}
