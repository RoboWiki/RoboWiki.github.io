import { useEffect, useMemo, useState } from 'react'
import { api } from '@/lib/api'
import { withBase } from '@/lib/utils'
import { TAG_LABELS, UNIVERSAL_TAGS, categoryTagSet, tagsForCategory } from '@robowiki/content'

/**
 * L0 一点打分：星级 + 使用时长 + 理由标签。
 *
 * 三条设计约束来自调研：
 *  1. 零输入优先——星级点一下就能提交，其余是「必选但一触即达」的单选/多选；
 *  2. 理由必须能聚合——只收白名单标签，自由文本只作为可选补充；
 *  3. 匿名——页面上不展示身份，服务端只按账号去重。
 */
const USAGE = [
  { value: 'long', label: '长期用过', hint: '>6 个月' },
  { value: 'short', label: '短期用过', hint: '<1 个月' },
  { value: 'unboxed', label: '只开箱测过', hint: '' },
]

const TOKEN_KEY = 'roboselect.token'

export default function RatingEditor({ partId, category, onDone }: {
  partId: string
  category?: string | null
  /** submitted：本次提交成功；withdrawn：撤回成功。 */
  onDone?: (result: 'submitted' | 'withdrawn') => void
}) {
  const [signedIn, setSignedIn] = useState<boolean | null>(null)
  const [score, setScore] = useState(0)
  const [usage, setUsage] = useState('')
  const [tags, setTags] = useState<string[]>([])
  const [note, setNote] = useState('')
  const [busy, setBusy] = useState(false)
  const [message, setMessage] = useState<{ kind: 'ok' | 'err'; text: string } | null>(null)
  /** 已存在本人评分：按钮变「修改评分」，并提供撤回。 */
  const [existing, setExisting] = useState(false)
  const [confirming, setConfirming] = useState(false)

  const universalTags = UNIVERSAL_TAGS.map(value => ({ value, label: TAG_LABELS[value] }))
  // 写完评分再引导到长评；社区页按 kind=review + part 过滤，下同。
  const reviewHref = withBase(`/community.html?kind=review&part=${encodeURIComponent(partId)}`)
  const specificKeys = categoryTagSet(category)
  const specificTags = tagsForCategory(category)
    .filter(value => specificKeys.has(value))
    .map(value => ({ value, label: TAG_LABELS[value] || value }))

  useEffect(() => {
    try {
      setSignedIn(Boolean(localStorage.getItem(TOKEN_KEY)))
    } catch {
      setSignedIn(false)
    }
  }, [])

  // 已有评分时预填：从「再打一次分」改成「修改这条评分」。
  useEffect(() => {
    if (!signedIn) return
    let alive = true
    api.getRating(partId).then(summary => {
      if (!alive) return
      const mine = summary.mine
      if (!mine || mine.hidden) return
      setExisting(true)
      setScore(mine.score ?? 0)
      setUsage(mine.usage_level ?? '')
      setTags(Array.isArray(mine.reason_tags) ? mine.reason_tags.slice(0, 3) : [])
      setNote(mine.note ?? '')
    }).catch(() => {
      // 未登录或接口暂时不可用：保持空白打分即可，不打断阅读
    })
    return () => { alive = false }
  }, [partId, signedIn])

  const resetForm = () => {
    setScore(0)
    setUsage('')
    setTags([])
    setNote('')
  }

  const ready = score > 0 && usage !== '' && tags.length > 0
  const hint = useMemo(() => {
    if (score === 0) return '先点星级'
    if (!usage) return '再选用多久'
    if (!tags.length) return '至少选一个理由'
    return ''
  }, [score, usage, tags])

  const toggleTag = (value: string) => {
    setTags(prev => {
      if (prev.includes(value)) return prev.filter(item => item !== value)
      if (prev.length >= 3) return prev
      return [...prev, value]
    })
  }

  const submit = async () => {
    if (!ready || busy) return
    setBusy(true)
    setMessage(null)
    try {
      await api.putRating(partId, {
        score,
        usage_level: usage,
        reason_tags: tags,
        note: note.trim(),
      })
      setExisting(true)
      setMessage({
        kind: 'ok',
        text: existing ? '已更新这条评分。' : '已记录，感谢。你的评分会进入下一次聚合。',
      })
      onDone?.('submitted')
    } catch (error) {
      const text = error instanceof Error ? error.message : '提交失败'
      setMessage({ kind: 'err', text: `没提交成功：${text}` })
    } finally {
      setBusy(false)
    }
  }

  const withdraw = async () => {
    if (busy) return
    setBusy(true)
    setMessage(null)
    try {
      await api.deleteRating(partId)
      setExisting(false)
      setConfirming(false)
      resetForm()
      setMessage({ kind: 'ok', text: '已撤回评分，分数与理由都不再计入聚合。' })
      onDone?.('withdrawn')
    } catch (error) {
      const text = error instanceof Error ? error.message : '撤回失败'
      setMessage({ kind: 'err', text: `没撤回成功：${text}` })
    } finally {
      setBusy(false)
    }
  }

  if (signedIn === null) return null

  if (!signedIn) {
    return (
      <div className="rounded-md border border-line bg-surface-2 p-3">
        <p className="text-xs leading-6 text-ink-3">登录后可以打分：一句话都不用写，点星 + 选两个理由即可。</p>
        <a
          href="/account.html"
          className="mt-2 inline-flex h-8 items-center rounded-md bg-brand px-3 text-xs font-semibold text-brand-fg hover:bg-brand-hover"
        >
          去登录
        </a>
      </div>
    )
  }

  return (
    <div className="rounded-md border border-line bg-surface-2 p-3">
      <div className="flex flex-wrap items-center gap-1">
        <span className="mr-1 text-xs text-ink-3">值不值</span>
        {[1, 2, 3, 4, 5].map(n => (
          <button
            key={n}
            type="button"
            onClick={() => setScore(n)}
            aria-label={`${n} 分`}
            aria-pressed={score === n}
            className={`grid h-8 w-8 place-items-center rounded-sm text-base transition-colors ${
              n <= score ? 'text-warning' : 'text-line-strong hover:text-warning'
            }`}
          >
            ★
          </button>
        ))}
        {score > 0 && <span className="mono ml-1 text-xs text-ink-2">{score}.0</span>}
      </div>

      <div className="mt-2.5 flex flex-wrap items-center gap-1.5">
        <span className="mr-0.5 text-xs text-ink-3">用了多久</span>
        {USAGE.map(item => (
          <button
            key={item.value}
            type="button"
            onClick={() => setUsage(item.value)}
            aria-pressed={usage === item.value}
            className={`inline-flex h-7 items-center rounded-full border px-2.5 text-xs transition-colors ${
              usage === item.value
                ? 'border-brand bg-brand-soft font-medium text-brand'
                : 'border-line bg-surface text-ink-2 hover:border-line-strong'
            }`}
          >
            {item.label}
            {item.hint && <span className="ml-1 text-ink-3">{item.hint}</span>}
          </button>
        ))}
      </div>

      <div className="mt-2.5">
        <div className="flex items-baseline justify-between">
          <span className="text-xs text-ink-3">为什么给这个分（最多 3 个）</span>
          <span className="mono text-xs text-ink-3">{tags.length}/3</span>
        </div>
        <div className="mt-1.5 space-y-1.5">
          <div>
            <span className="text-xs text-ink-3">通用</span>
            <div className="mt-1 flex flex-wrap gap-1">
              {universalTags.map(item => (
                <button
                  key={item.value}
                  type="button"
                  onClick={() => toggleTag(item.value)}
                  aria-pressed={tags.includes(item.value)}
                  className={`inline-flex h-6 items-center rounded-full border px-2 text-xs transition-colors ${
                    tags.includes(item.value)
                      ? 'border-brand bg-brand-soft text-brand'
                      : 'border-line bg-surface text-ink-2 hover:border-line-strong hover:text-ink'
                  }`}
                >
                  {item.label}
                </button>
              ))}
            </div>
          </div>
          {specificTags.length > 0 && (
            <div>
              <span className="text-xs text-ink-3">本品类</span>
              <div className="mt-1 flex flex-wrap gap-1">
                {specificTags.map(item => (
                  <button
                    key={item.value}
                    type="button"
                    onClick={() => toggleTag(item.value)}
                    aria-pressed={tags.includes(item.value)}
                    className={`inline-flex h-6 items-center rounded-full border px-2 text-xs transition-colors ${
                      tags.includes(item.value)
                        ? 'border-brand bg-brand-soft text-brand'
                        : 'border-line bg-surface text-ink-2 hover:border-line-strong hover:text-ink'
                    }`}
                  >
                    {item.label}
                  </button>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>

      <div className="mt-2.5">
        <label htmlFor="rating-note" className="sr-only">补充一句话（可选）</label>
        <input
          id="rating-note"
          value={note}
          onChange={event => setNote(event.target.value)}
          maxLength={200}
          placeholder="补一句（可选）：用在什么机器上、出了什么问题"
          className="h-8 w-full rounded-sm border border-line bg-surface px-2 text-xs text-ink placeholder:text-ink-3 focus:border-brand focus:outline-none"
        />
      </div>

      <div className="mt-2.5 flex flex-wrap items-center gap-2">
        <button
          type="button"
          onClick={submit}
          disabled={!ready || busy}
          className="inline-flex h-8 items-center rounded-md bg-brand px-3 text-xs font-semibold text-brand-fg transition-colors hover:bg-brand-hover disabled:opacity-50"
        >
          {busy ? '提交中…' : existing ? '修改评分' : '提交评分'}
        </button>
        {existing && !confirming && (
          <button
            type="button"
            onClick={() => setConfirming(true)}
            disabled={busy}
            className="inline-flex h-8 items-center rounded-md border border-line bg-surface px-3 text-xs text-ink-2 transition-colors hover:border-danger/50 hover:text-danger disabled:opacity-50"
          >
            撤回评分
          </button>
        )}
        {hint && <span className="text-xs text-ink-3">{hint}</span>}
        <span className="text-xs text-ink-3">匿名展示，只按账号去重</span>
      </div>

      {existing && confirming && (
        <div className="mt-2 rounded-md border border-danger/35 bg-danger-soft px-3 py-2">
          <p role="alert" className="m-0 text-xs leading-5 text-ink-2">
            撤回后这条评分（分数、使用时长、理由和备注）会被删除，不能恢复。确认撤回？
          </p>
          <div className="mt-2 flex flex-wrap items-center gap-2">
            <button
              type="button"
              onClick={withdraw}
              disabled={busy}
              className="inline-flex h-8 items-center rounded-md border border-danger/45 bg-danger-soft px-3 text-xs font-semibold text-danger transition-colors hover:border-danger disabled:opacity-50"
            >
              {busy ? '撤回中…' : '确认撤回'}
            </button>
            <button
              type="button"
              onClick={() => setConfirming(false)}
              disabled={busy}
              className="inline-flex h-8 items-center rounded-md border border-line bg-surface px-3 text-xs text-ink-2 transition-colors hover:border-line-strong hover:text-ink disabled:opacity-50"
            >
              取消
            </button>
          </div>
        </div>
      )}

      {message && (
        <p
          role="status"
          aria-live="polite"
          className={`mt-2 text-xs ${message.kind === 'ok' ? 'text-success' : 'text-danger'}`}
        >
          {message.text}
        </p>
      )}

      {existing && (
        <p className="mt-2 text-xs leading-5 text-ink-3">
          <a
            href={reviewHref}
            className="font-medium text-brand hover:underline"
          >
            写一条完整评价<span aria-hidden="true">→</span>
          </a>
          <span className="ml-1">说说具体机器、场景与踩过的坑。</span>
        </p>
      )}
    </div>
  )
}
