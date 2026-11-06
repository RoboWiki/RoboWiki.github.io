import { readStringList, writeStringList } from './storage'

const RECENT_KEY = 'rw.app.recent'
const MAX_RECENT = 5

export function readRecent(): string[] {
  return readStringList(RECENT_KEY, MAX_RECENT)
}

/** 最近浏览只存部件 id；重复访问提到最前，最多 5 个。 */
export function touchRecent(id: string): void {
  const value = String(id || '').trim()
  if (!value) return
  const next = [value, ...readRecent().filter((item) => item !== value)].slice(0, MAX_RECENT)
  writeStringList(RECENT_KEY, next)
}
