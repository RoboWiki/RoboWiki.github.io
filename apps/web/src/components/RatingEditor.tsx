import { useEffect, useMemo, useState } from 'react'
import { api } from '@/lib/api'

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

const TAGS = [
  { value: 'good_value', label: '性价比高' },
  { value: 'better_than_spec', label: '比标称好' },
  { value: 'overstated', label: '参数虚标' },
  { value: 'heat', label: '发热/功耗' },
  { value: 'build_quality', label: '做工问题' },
  { value: 'docs_missing', label: '文档缺失' },
  { value: 'shipping', label: '发货/售后' },
  { value: 'not_recommend', label: '不推荐' },
  { value: 'encoder_drift', label: '编码器漂移' },
  { value: 'backlash', label: '背隙大' },
  { value: 'fake_chip', label: '假货/翻新' },
  { value: 'hard_to_solder', label: '封装难焊' },
  { value: 'calibration', label: '标定困难' },
  { value: 'drift', label: '漂移' },
  { value: 'lighting', label: '受光照影响' },
]

const TOKEN_KEY = 'roboselect.token'

export default function RatingEditor({ partId, onDone }: { partId: string; onDone?: () => void }) {
  const [signedIn, setSignedIn] = useState<boolean | null>(null)
  const [score, setScore] = useState(0)
  const [usage, setUsage] = useState('')
  const [tags, setTags] = useState<string[]>([])
  const [note, setNote] = useState('')
  const [busy, setBusy] = useState(false)
  const [message, setMessage] = useState<{ kind: 'ok' | 'err'; text: string } | null>(null)

  useEffect(() => {
    try {
      setSignedIn(Boolean(localStorage.getItem(TOKEN_KEY)))
    } catch {
      setSignedIn(false)
    }
  }, [])

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
      setMessage({ kind: 'ok', text: '已记录，感谢。你的评分会进入下一次聚合。' })
      setScore(0)
      setUsage('')
      setTags([])
      setNote('')
      onDone?.()
    } catch (error) {
      const text = error instanceof Error ? error.message : '提交失败'
      setMessage({ kind: 'err', text: `没提交成功：${text}` })
    } finally {
      setBusy(false)
    }
  }

  if (signedIn === null) return null

  if (!signedIn) {
    return (
      <div className="rounded-md border border-line bg-surface-2 p-3">
        <p className="text-[12px] leading-6 text-ink-3">登录后可以打分：一句话都不用写，点星 + 选两个理由即可。</p>
        <a
          href="/app/#/pages/login/index"
          className="mt-2 inline-flex h-8 items-center rounded-md bg-brand px-3 text-[12px] font-semibold text-brand-fg hover:bg-brand-hover"
        >
          去登录
        </a>
      </div>
    )
  }

  return (
    <div className="rounded-md border border-line bg-surface-2 p-3">
      <div className="flex flex-wrap items-center gap-1">
        <span className="mr-1 text-[12px] text-ink-3">值不值</span>
        {[1, 2, 3, 4, 5].map(n => (
          <button
            key={n}
            type="button"
            onClick={() => setScore(n)}
            aria-label={`${n} 分`}
            aria-pressed={score === n}
            className={`grid h-8 w-8 place-items-center rounded-sm text-[16px] transition-colors ${
              n <= score ? 'text-warning' : 'text-line-strong hover:text-warning'
            }`}
          >
            ★
          </button>
        ))}
        {score > 0 && <span className="mono ml-1 text-[12px] text-ink-2">{score}.0</span>}
      </div>

      <div className="mt-2.5 flex flex-wrap items-center gap-1.5">
        <span className="mr-0.5 text-[12px] text-ink-3">用了多久</span>
        {USAGE.map(item => (
          <button
            key={item.value}
            type="button"
            onClick={() => setUsage(item.value)}
            aria-pressed={usage === item.value}
            className={`inline-flex h-7 items-center rounded-full border px-2.5 text-[11px] transition-colors ${
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
          <span className="text-[12px] text-ink-3">为什么给这个分（最多 3 个）</span>
          <span className="mono text-[10px] text-ink-3">{tags.length}/3</span>
        </div>
        <div className="mt-1.5 flex flex-wrap gap-1">
          {TAGS.map(item => (
            <button
              key={item.value}
              type="button"
              onClick={() => toggleTag(item.value)}
              aria-pressed={tags.includes(item.value)}
              className={`inline-flex h-6 items-center rounded-full border px-2 text-[11px] transition-colors ${
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

      <div className="mt-2.5">
        <label htmlFor="rating-note" className="sr-only">补充一句话（可选）</label>
        <input
          id="rating-note"
          value={note}
          onChange={event => setNote(event.target.value)}
          maxLength={200}
          placeholder="补一句（可选）：用在什么机器上、出了什么问题"
          className="h-8 w-full rounded-sm border border-line bg-surface px-2 text-[12px] text-ink placeholder:text-ink-3 focus:border-brand focus:outline-none"
        />
      </div>

      <div className="mt-2.5 flex flex-wrap items-center gap-2">
        <button
          type="button"
          onClick={submit}
          disabled={!ready || busy}
          className="inline-flex h-8 items-center rounded-md bg-brand px-3 text-[12px] font-semibold text-brand-fg transition-colors hover:bg-brand-hover disabled:opacity-50"
        >
          {busy ? '提交中…' : '提交评分'}
        </button>
        {hint && <span className="text-[11px] text-ink-3">{hint}</span>}
        <span className="text-[11px] text-ink-3">匿名展示，只按账号去重</span>
      </div>

      {message && (
        <p
          role="status"
          aria-live="polite"
          className={`mt-2 text-[11px] ${message.kind === 'ok' ? 'text-success' : 'text-danger'}`}
        >
          {message.text}
        </p>
      )}
    </div>
  )
}
