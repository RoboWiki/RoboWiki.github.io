import { useEffect, useId, useState } from 'react'

export type RangeValue = [number, number]

type Props = {
  label: string
  unit?: string
  min: number
  max: number
  step: number
  value: RangeValue
  onChange: (next: RangeValue) => void
}

const clamp = (v: number, lo: number, hi: number) => Math.min(hi, Math.max(lo, v))

export const formatSpecNumber = (v: number): string =>
  Number.isInteger(v) ? String(v) : String(parseFloat(v.toPrecision(4)))

export default function RangeFilter({ label, unit = '', min, max, step, value, onChange }: Props) {
  const id = useId()
  const lo = clamp(value[0], min, max)
  const hi = clamp(value[1], min, max)
  const span = max - min || 1
  const pct = (v: number) => ((v - min) / span) * 100
  const [loText, setLoText] = useState(formatSpecNumber(lo))
  const [hiText, setHiText] = useState(formatSpecNumber(hi))

  useEffect(() => setLoText(formatSpecNumber(lo)), [lo])
  useEffect(() => setHiText(formatSpecNumber(hi)), [hi])

  const commit = (nextLo: number, nextHi: number) => {
    const a = clamp(nextLo, min, max)
    const b = clamp(nextHi, min, max)
    onChange(a <= b ? [a, b] : [b, a])
  }

  const commitText = (which: 'lo' | 'hi') => {
    const text = which === 'lo' ? loText : hiText
    const n = Number(text)
    if (text.trim() === '' || !Number.isFinite(n)) {
      if (which === 'lo') setLoText(formatSpecNumber(lo))
      else setHiText(formatSpecNumber(hi))
      return
    }
    commit(which === 'lo' ? n : lo, which === 'hi' ? n : hi)
  }

  return (
    <div className="min-w-0">
      <div className="flex items-baseline justify-between gap-2">
        <label htmlFor={`${id}-lo`} className="text-[12px] font-medium text-ink-2">{label}</label>
        <span className="mono tabular text-[11px] text-ink-3">
          {formatSpecNumber(lo)}–{formatSpecNumber(hi)}{unit}
        </span>
      </div>
      <div className="rw-rangewrap">
        <span className="rw-rangetrack" aria-hidden="true" />
        <span
          className="rw-rangefill"
          aria-hidden="true"
          style={{ left: `${pct(lo)}%`, right: `${100 - pct(hi)}%` }}
        />
        <input
          id={`${id}-lo`}
          type="range"
          min={min}
          max={max}
          step={step}
          value={lo}
          onChange={event => commit(Number(event.target.value), hi)}
          aria-label={`${label}最小值`}
          className="rw-range"
        />
        <input
          type="range"
          min={min}
          max={max}
          step={step}
          value={hi}
          onChange={event => commit(lo, Number(event.target.value))}
          aria-label={`${label}最大值`}
          className="rw-range"
        />
      </div>
      <div className="mt-1.5 flex items-center gap-1.5">
        <input
          type="number"
          inputMode="decimal"
          min={min}
          max={max}
          step="any"
          value={loText}
          onChange={event => setLoText(event.target.value)}
          onBlur={() => commitText('lo')}
          onKeyDown={event => { if (event.key === 'Enter') commitText('lo') }}
          aria-label={`${label}最小值输入`}
          className="mono tabular h-7 w-full min-w-0 rounded-md border border-line bg-surface px-2 text-[12px] text-ink"
        />
        <span aria-hidden="true" className="text-[11px] text-ink-3">–</span>
        <input
          type="number"
          inputMode="decimal"
          min={min}
          max={max}
          step="any"
          value={hiText}
          onChange={event => setHiText(event.target.value)}
          onBlur={() => commitText('hi')}
          onKeyDown={event => { if (event.key === 'Enter') commitText('hi') }}
          aria-label={`${label}最大值输入`}
          className="mono tabular h-7 w-full min-w-0 rounded-md border border-line bg-surface px-2 text-[12px] text-ink"
        />
      </div>
    </div>
  )
}
