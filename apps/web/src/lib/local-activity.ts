/** 只存在本机的社区辅助数据：发帖草稿 + 最近发言记录。
 *
 * 两条使用约束：
 *  - 不经过后端，也不放任何账号/邮箱等敏感信息，只存标题、链接与时间；
 *  - 所有读写都吞掉异常（无痕模式、配额满、SSR），调用方不需要 try/catch。
 */

const DRAFT_KEY = 'rw-draft:composer'
const ACTIVITY_KEY = 'rw-local-activity'
export const ACTIVITY_EVENT = 'rw:local-activity'
export const ACTIVITY_LIMIT = 20

const store = (): Storage | null => {
  if (typeof window === 'undefined') return null
  try {
    return window.localStorage
  } catch {
    return null
  }
}

const readJSON = <T>(key: string): T | null => {
  try {
    const raw = store()?.getItem(key)
    return raw ? (JSON.parse(raw) as T) : null
  } catch {
    return null
  }
}

const writeJSON = (key: string, value: unknown): boolean => {
  try {
    store()?.setItem(key, JSON.stringify(value))
    return true
  } catch {
    return false
  }
}

const remove = (key: string) => {
  try {
    store()?.removeItem(key)
  } catch {
    // 忽略：清不掉也不该阻断发布流程
  }
}

const str = (v: unknown): string => (typeof v === 'string' ? v : '')
const nullableStr = (v: unknown): string | null =>
  typeof v === 'string' && v.trim() ? v : null

// ── 发帖草稿 ──────────────────────────────────────────────────────────────
export interface ComposerDraft {
  kind: string
  title: string
  body: string
  tags: string[]
  part_id: string | null
  rating: number | null
  use_case: string | null
  own_hardware: boolean
  total_price_cny: number | string | null
  price_scope: string | null
  updated_at: string
}

export type ComposerDraftInput = Omit<ComposerDraft, 'updated_at'>

/** 只保留有意义的字段，避免把整份 antd Form 值写进 localStorage。 */
export function normalizeDraft(values: Record<string, unknown>): ComposerDraftInput {
  const tags = Array.isArray(values.tags)
    ? values.tags.map(t => String(t).trim()).filter(Boolean).slice(0, 20)
    : []
  const price = values.total_price_cny
  return {
    kind: str(values.kind) || 'discussion',
    title: str(values.title).slice(0, 200),
    body: str(values.body).slice(0, 20000),
    tags,
    part_id: nullableStr(values.part_id),
    rating: typeof values.rating === 'number' ? values.rating : null,
    use_case: nullableStr(values.use_case),
    own_hardware: values.own_hardware === true,
    total_price_cny: typeof price === 'number' || typeof price === 'string' ? price : null,
    price_scope: nullableStr(values.price_scope),
  }
}

export function draftHasContent(d: Pick<ComposerDraftInput, 'title' | 'body'>): boolean {
  return d.title.trim().length > 0 || d.body.trim().length > 0
}

/** 草稿为空时直接删掉：不留下一条空壳让下次进来又问一遍。 */
export function saveDraft(input: ComposerDraftInput): void {
  if (!draftHasContent(input)) {
    clearDraft()
    return
  }
  const draft: ComposerDraft = { ...input, updated_at: new Date().toISOString() }
  writeJSON(DRAFT_KEY, draft)
}

export function loadDraft(): ComposerDraft | null {
  const raw = readJSON<Partial<ComposerDraft>>(DRAFT_KEY)
  if (!raw) return null
  const draft: ComposerDraft = {
    ...normalizeDraft(raw as Record<string, unknown>),
    updated_at: str(raw.updated_at) || new Date().toISOString(),
  }
  return draftHasContent(draft) ? draft : null
}

export function clearDraft(): void {
  remove(DRAFT_KEY)
}

// ── 最近发言 ──────────────────────────────────────────────────────────────
export interface LocalActivityItem {
  id: string
  kind: 'post' | 'comment'
  title: string
  href: string
  at: string
}

export type LocalActivityInput = {
  kind: 'post' | 'comment'
  title: string
  href: string
  at?: string
}

const cleanItem = (raw: Partial<LocalActivityItem>): LocalActivityItem | null => {
  const href = str(raw.href)
  const title = str(raw.title).trim()
  if (!href || !title) return null
  const kind = raw.kind === 'comment' ? 'comment' : 'post'
  return {
    id: str(raw.id) || `${kind}:${href}`,
    kind,
    title: title.slice(0, 120),
    href,
    at: str(raw.at) || new Date().toISOString(),
  }
}

export function loadActivity(): LocalActivityItem[] {
  const raw = readJSON<unknown>(ACTIVITY_KEY)
  if (!Array.isArray(raw)) return []
  const seen = new Set<string>()
  const items: LocalActivityItem[] = []
  for (const row of raw) {
    const item = cleanItem((row || {}) as Partial<LocalActivityItem>)
    if (!item || seen.has(item.id)) continue
    seen.add(item.id)
    items.push(item)
    if (items.length >= ACTIVITY_LIMIT) break
  }
  return items
}

const announce = () => {
  if (typeof window !== 'undefined') window.dispatchEvent(new Event(ACTIVITY_EVENT))
}

/** 记录一条本人发言；同一 href 只留最新一条，最多 20 条。 */
export function recordActivity(input: LocalActivityInput): void {
  const item = cleanItem({ ...input, id: `${input.kind}:${input.href}` })
  if (!item) return
  const rest = loadActivity().filter(row => row.id !== item.id)
  writeJSON(ACTIVITY_KEY, [item, ...rest].slice(0, ACTIVITY_LIMIT))
  announce()
}

export function clearActivity(): void {
  remove(ACTIVITY_KEY)
  announce()
}

/** 订阅变化（同页事件 + 其他标签页的 storage 事件），返回取消函数。 */
export function subscribeActivity(cb: () => void): () => void {
  if (typeof window === 'undefined') return () => {}
  const onStorage = (e: StorageEvent) => {
    if (e.key === null || e.key === ACTIVITY_KEY) cb()
  }
  window.addEventListener(ACTIVITY_EVENT, cb)
  window.addEventListener('storage', onStorage)
  return () => {
    window.removeEventListener(ACTIVITY_EVENT, cb)
    window.removeEventListener('storage', onStorage)
  }
}
