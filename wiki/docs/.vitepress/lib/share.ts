import { withBase } from 'vitepress'

export type ShareEntry = {
  id: string
  path: string
  url?: string
  json: string
  title: string
  summary: string
  source_tier?: string
  last_checked?: string
  data_version: string
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
