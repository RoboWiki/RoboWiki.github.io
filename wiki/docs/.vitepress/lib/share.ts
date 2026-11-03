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
