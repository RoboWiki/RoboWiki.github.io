import { useEffect, useMemo, useState } from 'react'

import { Button, Input, Text, Textarea, View } from '@tarojs/components'
import Taro, { useRouter } from '@tarojs/taro'
import { ApiError, type Submission, type User } from '@robowiki/core'

import { api, errorMessage, loadMe } from '@/services/api'
import { partCategoryLabel, type PartView } from '@/services/parts'
import './index.css'

const COMMON_FIELDS: Array<{ key: string; label: string }> = [
  { key: 'price_cny', label: '价格' },
  { key: 'url', label: '官方来源 URL' },
  { key: 'source_tier', label: '来源等级 A/B/C' },
  { key: 'last_checked', label: '最近核对日期' },
  { key: 'notes', label: '备注' },
  { key: 'title', label: '标题' },
  { key: 'vendor', label: '厂商' },
  { key: 'model', label: '型号' },
]

const FIELD_KEY_RE = /^(specs\.)?[A-Za-z0-9_]+$/

/** 与网页 DataFix 同口径：价格是数，其余能转数字就转。 */
function typedValue(field: string, raw: string): string | number {
  if (field === 'source_tier' || field === 'last_checked' || field === 'url') return raw.trim()
  if (field === 'price_cny') {
    const n = Number(raw)
    return Number.isFinite(n) ? n : raw.trim()
  }
  const s = raw.trim()
  return /^-?\d+(\.\d+)?$/.test(s) ? Number(s) : s
}

export default function SubmitPage() {
  const router = useRouter()
  const presetId = decodeURIComponent(router.params?.id || '')

  const [user, setUser] = useState<User | null>(null)
  const [searchInput, setSearchInput] = useState('')
  const [query, setQuery] = useState('')
  const [results, setResults] = useState<PartView[]>([])
  const [searching, setSearching] = useState(false)
  const [part, setPart] = useState<PartView | null>(null)

  const [field, setField] = useState('price_cny')
  const [customField, setCustomField] = useState('')
  const [value, setValue] = useState('')
  const [note, setNote] = useState('')
  const [sourceUrl, setSourceUrl] = useState('')

  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')
  const [done, setDone] = useState<Submission | null>(null)

  useEffect(() => {
    loadMe().then(setUser)
  }, [])

  useEffect(() => {
    if (!presetId) return
    let alive = true
    api
      .getPart(presetId)
      .then((data) => {
        if (!alive) return
        setPart(data as PartView)
        setSearchInput('')
      })
      .catch(() => {
        // 预填 id 失效不拦手选。
      })
    return () => { alive = false }
  }, [presetId])

  useEffect(() => {
    const timer = setTimeout(() => setQuery(searchInput.trim()), 350)
    return () => clearTimeout(timer)
  }, [searchInput])

  useEffect(() => {
    if (!query) {
      setResults([])
      return
    }
    let alive = true
    setSearching(true)
    api
      .listParts({ q: query, limit: 8, compact: true })
      .then((data) => {
        if (alive) setResults((data.items || []) as PartView[])
      })
      .catch(() => {
        if (alive) setResults([])
      })
      .finally(() => {
        if (alive) setSearching(false)
      })
    return () => { alive = false }
  }, [query])

  const fieldChips = useMemo(() => {
    const specKeys = Object.keys(part?.specs || {})
      .filter((key) => key !== 'params' && key !== 'image_url')
      .slice(0, 16)
      .map((key) => ({ key: `specs.${key}`, label: key }))
    return [...COMMON_FIELDS, ...specKeys]
  }, [part])

  const fieldLabel = (key: string) =>
    fieldChips.find((item) => item.key === key)?.label || key

  const pickPart = (item: PartView) => {
    setPart(item)
    setResults([])
    setSearchInput('')
    setQuery('')
    setError('')
  }

  const validate = (): string => {
    if (!part) return '先选择要纠错的部件'
    const key = field === '__custom__' ? customField.trim() : field
    if (!key) return '请填写字段名'
    if (!FIELD_KEY_RE.test(key)) return '字段名只能包含字母、数字、下划线（参数用 specs. 前缀）'
    if (!value.trim()) return '请填写建议的值'
    if (value.trim().length > 4000) return '值最多 4000 字'
    if (note.trim().length < 5) return '请写清依据（至少 5 个字）'
    if (sourceUrl.trim() && !/^https?:\/\/\S+$/i.test(sourceUrl.trim())) {
      return '来源链接需要以 http:// 或 https:// 开头'
    }
    if (key === 'price_cny') {
      if (!/^\d+(\.\d+)?$/.test(value.trim())) return '价格必须是非负数字（不要带 ¥ 或逗号）'
      if (Number(value.trim()) > 10_000_000) return '价格超出合理范围（≤ 1000 万）'
    }
    if (key === 'last_checked' && !/^\d{4}-\d{2}-\d{2}$/.test(value.trim())) {
      return '日期格式为 YYYY-MM-DD'
    }
    if (key === 'source_tier' && !['A', 'B', 'C'].includes(value.trim())) {
      return '来源等级只能是 A / B / C'
    }
    if ((key === 'url') && !/^https?:\/\/\S+$/i.test(value.trim())) {
      return '官方来源需要以 http:// 或 https:// 开头'
    }
    return ''
  }

  const submit = async () => {
    if (busy) return
    setError('')
    const message = validate()
    if (message) {
      setError(message)
      return
    }
    const key = field === '__custom__' ? customField.trim() : field
    setBusy(true)
    try {
      const submission = await api.createSubmission({
        kind: 'part_patch',
        target_id: String(part!.id),
        payload: { [key]: typedValue(key, value) },
        evidence: {
          note: note.trim(),
          ...(sourceUrl.trim() ? { source_url: sourceUrl.trim() } : {}),
        },
      })
      setDone(submission)
      setValue('')
      setNote('')
      setSourceUrl('')
    } catch (err) {
      if (err instanceof ApiError && err.status === 401) {
        setError('登录已失效，请重新登录后再提交')
      } else {
        setError(errorMessage(err))
      }
    } finally {
      setBusy(false)
    }
  }

  const backToPart = () => {
    const pages = Taro.getCurrentPages()
    if (pages.length > 1) {
      Taro.navigateBack()
      return
    }
    if (part) {
      Taro.redirectTo({ url: `/pages/part/index?id=${encodeURIComponent(String(part.id))}` })
    } else {
      Taro.reLaunch({ url: '/pages/index/index' })
    }
  }

  const openLogin = () => {
    Taro.navigateTo({ url: '/pages/login/index' })
  }

  if (!user) {
    return (
      <View className="rw-page submit">
        <View className="rw-stack">
          <Text className="rw-title">投稿纠错</Text>
          <Text className="rw-caption">登录后才能提交参数纠错，提案会进入站务审核队列。</Text>
          <Button className="rw-btn rw-btn--primary" onClick={openLogin}>去登录</Button>
          <Text className="rw-link" onClick={backToPart}>先返回</Text>
        </View>
      </View>
    )
  }

  if (done) {
    return (
      <View className="rw-page submit">
        <View className="submit__done">
          <Text className="rw-title">已提交</Text>
          <Text className="rw-caption">
            提案 #{done.id} 已进入审核队列，结果会以站内通知（和邮件，如已开启）告知。
          </Text>
          <Text className="rw-caption">
            {part ? `${part.vendor} ${part.model} · ${fieldLabel(field === '__custom__' ? customField.trim() : field)}` : ''}
          </Text>
          <Button className="rw-btn rw-btn--primary" onClick={() => setDone(null)}>
            继续纠错
          </Button>
          <Button className="rw-btn" onClick={backToPart}>
            {part ? '返回部件页' : '返回目录'}
          </Button>
        </View>
        <View className="rw-safe-bottom" />
      </View>
    )
  }

  return (
    <View className="rw-page submit">
      <View className="submit__head">
        <Text className="rw-title">投稿纠错</Text>
        <Text className="rw-caption">
          只改一个字段也能提交；依据越具体，审核越快。通过后由数据流水线发布。
        </Text>
      </View>

      {error ? <Text className="rw-error">{error}</Text> : null}

      <View className="submit__section">
        <Text className="rw-subtitle">部件</Text>
        {part ? (
          <View className="rw-list">
            <View className="rw-list__row submit__part">
              <View className="rw-grow">
                <Text className="rw-strong">{part.vendor} {part.model}</Text>
                <Text className="rw-caption submit__line">{partCategoryLabel(part)} · {part.id}</Text>
              </View>
              <Text className="rw-link" onClick={() => setPart(null)}>更换</Text>
            </View>
          </View>
        ) : (
          <>
            <View className="rw-field">
              <Input
                className="rw-input"
                value={searchInput}
                placeholder="搜索厂商 / 型号"
                confirmType="search"
                onInput={(event) => setSearchInput(event.detail.value)}
              />
            </View>
            {searching ? <Text className="rw-caption">正在搜索…</Text> : null}
            {results.length ? (
              <View className="rw-list">
                {results.map((item) => (
                  <View
                    key={item.id}
                    className="rw-list__row rw-list__row--tap submit__part"
                    onClick={() => pickPart(item)}
                  >
                    <View className="rw-grow">
                      <Text className="rw-strong">{item.vendor} {item.model}</Text>
                      <Text className="rw-caption submit__line">
                        {partCategoryLabel(item)} · {item.web_path || item.id}
                      </Text>
                    </View>
                  </View>
                ))}
              </View>
            ) : query && !searching ? (
              <Text className="rw-caption">没有匹配的部件，换个关键词试试。</Text>
            ) : null}
          </>
        )}
      </View>

      <View className="submit__section">
        <Text className="rw-subtitle">字段</Text>
        <View className="submit__chips">
          {fieldChips.map((item) => (
            <View
              key={item.key}
              className={`rw-chip ${field === item.key ? 'rw-chip--active' : ''}`}
              onClick={() => setField(item.key)}
            >
              {item.label}
            </View>
          ))}
          <View
            className={`rw-chip ${field === '__custom__' ? 'rw-chip--active' : ''}`}
            onClick={() => setField('__custom__')}
          >
            其他参数…
          </View>
        </View>
        {field === '__custom__' ? (
          <View className="rw-field">
            <Input
              className="rw-input"
              value={customField}
              placeholder="如 specs.tau_peak_Nm 或 notes"
              onInput={(event) => setCustomField(event.detail.value)}
            />
          </View>
        ) : (
          <Text className="rw-caption">当前字段：{fieldLabel(field)}（{field}）</Text>
        )}
      </View>

      <View className="submit__section">
        <Text className="rw-subtitle">建议的值</Text>
        <View className="rw-field rw-field--textarea">
          <Textarea
            className="rw-textarea"
            value={value}
            maxlength={4000}
            placeholder="写正确的值，例如 1299 或 2026-01-15"
            onInput={(event) => setValue(event.detail.value)}
          />
        </View>
      </View>

      <View className="submit__section">
        <Text className="rw-subtitle">依据 / 说明</Text>
        <View className="rw-field rw-field--textarea">
          <Textarea
            className="rw-textarea"
            value={note}
            maxlength={2000}
            placeholder="手册页码、官方页面截图说明…（至少 5 个字）"
            onInput={(event) => setNote(event.detail.value)}
          />
        </View>
        <View className="rw-field">
          <Input
            className="rw-input"
            value={sourceUrl}
            placeholder="来源链接（可选，http/https）"
            onInput={(event) => setSourceUrl(event.detail.value)}
          />
        </View>
      </View>

      <Button className="rw-btn rw-btn--primary submit__submit" disabled={busy} onClick={submit}>
        {busy ? '提交中…' : '提交纠错'}
      </Button>
      <Text className="rw-caption submit__note">
        每次只提交一个字段；多项修改请分别提交。审核通过后由流水线更新目录。
      </Text>
      <View className="rw-safe-bottom" />
    </View>
  )
}
