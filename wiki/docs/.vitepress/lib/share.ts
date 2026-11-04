import { withBase } from 'vitepress'

export type ShareEntry = {
  id: string
  path: string
  url?: string
  json: string
  title: string
  summary: string
  source_tier?: string
  verified?: boolean
  last_checked?: string
  data_version: string
  copy_text?: string
  /** 构建期写好的产品图绝对地址；材质页为 null，由页面 frontmatter 退回默认 OG。 */
  image_url?: string | null
}

/** 没有产品图的页面（材质/工艺/目录页）共用的默认分享图。 */
export const DEFAULT_SHARE_IMAGE = '/og-default.png'

/**
 * 分享图绝对地址：分享卡产品图 → 页面 frontmatter.image → 默认 OG。
 *
 * QQ 的 pics 只认绝对地址；构建期 share JSON 里已经是绝对地址，
 * 页面 frontmatter 写的是根相对路径，这里按 canonical 的 origin 补齐。
 */
export function shareImage(e: ShareEntry | null, pageImage = ''): string {
  const raw = (e?.image_url || pageImage || DEFAULT_SHARE_IMAGE).trim()
  if (/^https?:\/\//i.test(raw)) return raw
  let origin = ''
  try {
    origin = e ? new URL(canonical(e)).origin : window.location.origin
  } catch {
    origin = typeof window !== 'undefined' ? window.location.origin : ''
  }
  return origin ? `${origin}/${raw.replace(/^\/+/, '')}` : raw
}

/** 详情页分享卡的直查路径：/parts/<cat>/<slug>.html → /share/parts/<cat>/<slug>.json */
export function shareJsonPath(pathname: string): string | null {
  const part = pathname.match(/^\/parts\/([^/]+)\/([^/]+)\.html$/)
  if (part) return `/share/parts/${part[1]}/${part[2]}.json`
  const material = pathname.match(/^\/materials\/([^/]+)\.html$/)
  if (material) return `/share/materials/${material[1]}.json`
  return null
}

export function normalize(path: string) {
  const p = path.replace(/\.html$/, '').replace(/\/+$/, '')
  return p || '/'
}

export function canonical(e: ShareEntry) {
  return e.url || `${window.location.origin}${e.path}`
}

let indexPromise: Promise<ShareEntry[]> | null = null

export function loadShareIndex(): Promise<ShareEntry[]> {
  if (!indexPromise) {
    indexPromise = fetch(withBase('/share/index.json'))
      .then((r) => (r.ok ? r.json() : []))
      .catch(() => [])
  }
  return indexPromise
}

export async function findShareEntry(path: string): Promise<ShareEntry | null> {
  const here = normalize(path)
  const rows = await loadShareIndex()
  return rows.find((r) => normalize(r.path) === here) || null
}
