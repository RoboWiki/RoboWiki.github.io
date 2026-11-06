import { useEffect, useState } from 'react'
import { api } from '@/lib/api'
import type { ReproductionSummary } from '@robowiki/core'

/**
 * 方案复现记录：成 / 部分成 / 没成。
 *
 * 方案的「评价」不该是 5 星——同一套结构换个人装，差别在能不能装出来，
 * 以及为了装出来改了什么。所以这里收三态结论 + 改动说明。
 */
const OUTCOMES = [
  { value: 'success', label: '装出来了', hint: '照原方案', tone: 'text-success border-success/40 bg-success-soft' },
  { value: 'partial', label: '部分成功', hint: '改了东西', tone: 'text-warning border-warning/40 bg-warning-soft' },
  { value: 'failed', label: '没成', hint: '卡住了', tone: 'text-danger border-danger/40 bg-danger-soft' },
] as const

const TOKEN_KEY = 'roboselect.token'

export default function ReproductionPanel({ buildId }: { buildId: string }) {
  const [data, setData] = useState<ReproductionSummary | null>(null)
  const [failed, setFailed] = useState(false)
  const [signedIn, setSignedIn] = useState(false)
  const [outcome, setOutcome] = useState<'success' | 'partial' | 'failed' | ''>('')
  const [changes, setChanges] = useState('')
  const [note, setNote] = useState('')
  const [busy, setBusy] = useState(false)
  const [message, setMessage] = useState<{ kind: 'ok' | 'err'; text: string } | null>(null)

  const load = () => {
    api.getReproductions(buildId)
      .then(result => { setData(result); setFailed(false) })
      .catch(() => setFailed(true))
  }

  useEffect(() => {
    try {
      setSignedIn(Boolean(localStorage.getItem(TOKEN_KEY)))
    } catch {
      setSignedIn(false)
    }
    load()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [buildId])

  useEffect(() => {
    if (data?.mine?.outcome) {
      setOutcome(data.mine.outcome)
      setChanges(data.mine.changes ?? '')
      setNote(data.mine.note ?? '')
    }
  }, [data?.mine?.outcome, data?.mine?.changes, data?.mine?.note])

  const submit = async () => {
    if (!outcome || busy) return
    setBusy(true)
    setMessage(null)
    try {
      const result = await api.recordReproduction(buildId, {
        outcome,
        changes: changes.trim(),
        note: note.trim(),
      })
      setData(result)
      setMessage({ kind: 'ok', text: result.created ? '已记录，感谢。' : '已更新你的复现结论。' })
    } catch (error) {
      const text = error instanceof Error ? error.message : '提交失败'
      setMessage({ kind: 'err', text: `没提交成功：${text}` })
    } finally {
      setBusy(false)
    }
  }

  const total = data?.total ?? 0
  const rowStatus = failed ? '读数失败，稍后再试' : total === 0 ? '还没有人记录复现结果' : `${total} 人记录过`

  return (
    <section className="card p-5 sm:p-6" aria-labelledby="reproduction">
      <div className="flex flex-wrap items-baseline justify-between gap-2">
        <h2 id="reproduction" className="text-base font-bold tracking-tight text-ink">复现记录</h2>
        <span className="text-xs text-ink-3">{rowStatus}</span>
      </div>

      {total > 0 && (
        <dl className="mt-3 grid grid-cols-3 gap-px overflow-hidden rounded-md border border-line bg-line">
          {OUTCOMES.map(item => (
            <div key={item.value} className="bg-surface px-3 py-2.5">
              <dt className="text-[11px] text-ink-3">{item.label}</dt>
              <dd className="mono tabular mt-0.5 text-lg font-bold text-ink">{data?.[item.value] ?? 0}</dd>
            </div>
          ))}
        </dl>
      )}

      {!signedIn ? (
        <div className="mt-3 rounded-md border border-line bg-surface-2 p-3">
          <p className="text-[12px] leading-6 text-ink-3">
            装过这台机器？登录后一句话记录结果（成功 / 部分成功 / 没成），比点赞有用。
          </p>
          <a
            href="/app/#/pages/login/index"
            className="mt-2 inline-flex h-8 items-center rounded-md border border-line bg-surface px-3 text-[12px] font-medium text-ink hover:border-line-strong"
          >
            去登录
          </a>
        </div>
      ) : (
        <div className="mt-3 rounded-md border border-line bg-surface-2 p-3">
          <div className="flex flex-wrap gap-1.5">
            {OUTCOMES.map(item => (
              <button
                key={item.value}
                type="button"
                onClick={() => setOutcome(item.value)}
                aria-pressed={outcome === item.value}
                className={`inline-flex h-8 items-center gap-1 rounded-full border px-3 text-[12px] transition-colors ${
                  outcome === item.value ? item.tone : 'border-line bg-surface text-ink-2 hover:border-line-strong'
                }`}
              >
                {item.label}
                <span className="text-[10px] opacity-70">{item.hint}</span>
              </button>
            ))}
          </div>

          <label htmlFor="repro-changes" className="mt-2.5 block text-[11px] text-ink-3">
            相对原方案改了什么（可选）
          </label>
          <input
            id="repro-changes"
            value={changes}
            onChange={event => setChanges(event.target.value)}
            maxLength={200}
            placeholder="例：换了减速比 1:9，舵机换成 20kg 款"
            className="mt-1 h-8 w-full rounded-sm border border-line bg-surface px-2 text-[12px] text-ink placeholder:text-ink-3 focus:border-brand focus:outline-none"
          />

          <label htmlFor="repro-note" className="mt-2 block text-[11px] text-ink-3">说明（可选）</label>
          <input
            id="repro-note"
            value={note}
            onChange={event => setNote(event.target.value)}
            maxLength={500}
            placeholder="卡在哪一步、缺什么件"
            className="mt-1 h-8 w-full rounded-sm border border-line bg-surface px-2 text-[12px] text-ink placeholder:text-ink-3 focus:border-brand focus:outline-none"
          />

          <div className="mt-2.5 flex items-center gap-2">
            <button
              type="button"
              onClick={submit}
              disabled={!outcome || busy}
              className="inline-flex h-8 items-center rounded-md bg-brand px-3 text-[12px] font-semibold text-brand-fg hover:bg-brand-hover disabled:opacity-50"
            >
              {busy ? '提交中…' : data?.mine ? '更新结论' : '记录结果'}
            </button>
            {!outcome && <span className="text-[11px] text-ink-3">先选一个结论</span>}
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
      )}
    </section>
  )
}
