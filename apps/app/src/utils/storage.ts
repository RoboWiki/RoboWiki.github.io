import Taro from 'virtual:taro/api'

/** 读写字符串列表：兼容直接存数组和旧版本存 JSON 字符串两种情况。 */
export function readStringList(key: string, max: number): string[] {
  let raw: unknown = null
  try {
    raw = Taro.getStorageSync(key)
  } catch {
    return []
  }
  let list: unknown = raw
  if (typeof raw === 'string' && raw.trim()) {
    try {
      list = JSON.parse(raw)
    } catch {
      return []
    }
  }
  if (!Array.isArray(list)) return []
  const seen = new Set<string>()
  const out: string[] = []
  for (const item of list) {
    const value = String(item || '').trim()
    if (!value || seen.has(value)) continue
    seen.add(value)
    out.push(value)
    if (out.length >= max) break
  }
  return out
}

export function writeStringList(key: string, list: string[]): void {
  try {
    if (list.length) Taro.setStorageSync(key, list)
    else Taro.removeStorageSync(key)
  } catch {
    // 存储不可用时不阻断页面。
  }
}

export function readString(key: string): string {
  try {
    const value = Taro.getStorageSync(key)
    return typeof value === 'string' ? value : ''
  } catch {
    return ''
  }
}

export function writeString(key: string, value: string): void {
  try {
    if (value) Taro.setStorageSync(key, value)
    else Taro.removeStorageSync(key)
  } catch {
    // 同上。
  }
}
