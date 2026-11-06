import { readStringList, writeStringList } from './storage'

export const COMPARE_KEY = 'rw.app.compare'
export const MAX_COMPARE = 4

export function readCompare(): string[] {
  return readStringList(COMPARE_KEY, MAX_COMPARE)
}

export function writeCompare(ids: string[]): void {
  writeStringList(COMPARE_KEY, ids.slice(0, MAX_COMPARE))
}
