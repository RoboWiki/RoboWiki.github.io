import { useEffect, useMemo, useState } from 'react'

import { Button, ScrollView, Text, View } from '@tarojs/components'
import { useRouter } from '@tarojs/taro'

import { EmptyState, ErrorState } from '@/components/Feedback'
import { api, errorMessage } from '@/services/api'
import {
  partCategoryLabel,
  partFacts,
  partPrice,
  partRating,
  type PartView,
} from '@/services/parts'
import { MAX_COMPARE, readCompare, writeCompare } from '@/utils/compare'
import { openTab } from '@/utils/nav'
import { useThemeMode } from '@/utils/theme'
import './index.css'

function unique(ids: string[]): string[] {
  const seen = new Set<string>()
  const out: string[] = []
  ids.forEach((id) => {
    const value = String(id || '').trim()
    if (!value || seen.has(value)) return
    seen.add(value)
    out.push(value)
  })
  return out.slice(0, MAX_COMPARE)
}

export default function ComparePage() {
  const router = useRouter()
  const theme = useThemeMode()

  const [ids, setIds] = useState<string[]>(() => {
    const fromQuery = decodeURIComponent(router.params?.ids || '')
      .split(',')
      .map((item) => item.trim())
      .filter(Boolean)
    return unique(fromQuery.length ? fromQuery : readCompare())
  })
  const [parts, setParts] = useState<PartView[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [reloadKey, setReloadKey] = useState(0)

  useEffect(() => {
    writeCompare(ids)
    if (!ids.length) {
      setParts([])
      setLoading(false)
      setError('')
      return
    }
    let alive = true
    setLoading(true)
    setError('')
    Promise.all(
      ids.map(async (id) => {
        const part = (await api.getPart(id)) as PartView
        // 评分单独取：评分接口失败不能让整页进错误态。
        const rating = await api.getRating(id).catch(() => null)
        return rating
          ? { ...part, rating_avg: rating.avg ?? null, rating_count: rating.count }
          : part
      }),
    )
      .then((list) => {
        if (alive) setParts((list || []) as PartView[])
      })
      .catch((err) => {
        if (alive) setError(errorMessage(err))
      })
      .finally(() => {
        if (alive) setLoading(false)
      })
    return () => {
      alive = false
    }
  }, [ids, reloadKey])

  const rows = useMemo(() => {
    const map = new Map<string, { key: string; label: string; values: string[] }>()
    parts.forEach((part, index) => {
      partFacts(part).forEach((fact) => {
        let row = map.get(fact.key)
        if (!row) {
          row = {
            key: fact.key,
            label: fact.label || fact.key,
            values: parts.map(() => '—'),
          }
          map.set(fact.key, row)
        }
        row.values[index] = fact.value || '—'
      })
    })
    return Array.from(map.values())
  }, [parts])

  const remove = (id: string) => {
    setIds((prev) => prev.filter((item) => item !== id))
  }

  const clear = () => {
    setIds([])
    setParts([])
    writeCompare([])
  }

  const goPick = () => openTab('/pages/index/index')

  return (
    <View className={`rw-page compare ${theme === 'dark' ? 'dark' : ''}`}>
      <View className="compare__head">
        <View className="rw-row rw-row--between">
          <Text className="rw-title">部件对比</Text>
          {ids.length ? (
            <Text className="rw-link rw-link--tap" onClick={clear}>
              清空
            </Text>
          ) : null}
        </View>
        <Text className="rw-caption">已选 {ids.length} / {MAX_COMPARE} 个部件</Text>
      </View>

      {loading ? (
        <View className="rw-stack">
          <View className="rw-skeleton" style={{ height: '72px' }} />
          <View className="rw-skeleton" style={{ height: '240px' }} />
        </View>
      ) : null}

      {!loading && error ? (
        <ErrorState message={error} onRetry={() => setReloadKey((key) => key + 1)} />
      ) : null}

      {!loading && !error && ids.length === 0 ? (
        <EmptyState
          title="还没有选择部件"
          hint="在部件列表勾选「对比」，最多同时比较 4 个。"
          actionLabel="去部件列表"
          onAction={goPick}
        />
      ) : null}

      {!loading && !error && ids.length === 1 && parts.length === 1 ? (
        <View className="compare__single">
          <Text className="rw-subtitle">
            {parts[0].vendor} {parts[0].model}
          </Text>
          <Text className="rw-caption">
            {partCategoryLabel(parts[0])} · {partPrice(parts[0])}
          </Text>
          <Text className="rw-caption">再选 1 个部件，就能并排看参数差异。</Text>
          <Button className="rw-btn rw-btn--primary" onClick={goPick}>
            再选一个
          </Button>
        </View>
      ) : null}

      {!loading && !error && ids.length >= 2 && parts.length >= 2 ? (
        <ScrollView scrollX className="compare__scroll" showScrollbar={false}>
          <View className="compare__table">
            <View className="compare__row compare__row--head">
              <View className="compare__cell compare__cell--label">字段</View>
              {parts.map((part) => (
                <View className="compare__cell compare__cell--head" key={part.id}>
                  <Text className="compare__model rw-line-clamp-1">{part.model}</Text>
                  <Text className="compare__vendor rw-line-clamp-1">{part.vendor}</Text>
                  <Text
                    className="compare__remove"
                    onClick={() => remove(String(part.id))}
                  >
                    移除
                  </Text>
                </View>
              ))}
            </View>

            <View className="compare__row">
              <View className="compare__cell compare__cell--label">参考价</View>
              {parts.map((part) => (
                <View className="compare__cell" key={`price-${part.id}`}>
                  <Text className="compare__value">{partPrice(part)}</Text>
                </View>
              ))}
            </View>

            <View className="compare__row">
              <View className="compare__cell compare__cell--label">评分</View>
              {parts.map((part) => {
                const rating = partRating(part)
                return (
                  <View className="compare__cell" key={`rating-${part.id}`}>
                    <Text className="compare__value">
                      {rating.count ? `${rating.avg ?? '—'}（${rating.count}）` : '暂无评分'}
                    </Text>
                  </View>
                )
              })}
            </View>

            {rows.map((row) => (
              <View className="compare__row" key={row.key}>
                <View className="compare__cell compare__cell--label">{row.label}</View>
                {row.values.map((value, index) => (
                  <View className="compare__cell" key={`${row.key}-${parts[index]?.id || index}`}>
                    <Text className="compare__value">{value}</Text>
                  </View>
                ))}
              </View>
            ))}
          </View>
        </ScrollView>
      ) : null}

      {!loading && !error && ids.length >= 2 ? (
        <Text className="rw-caption compare__hint">
          左右滑动查看全部列；参数缺失显示 —，表示该部件的原始数据没有这一项。
        </Text>
      ) : null}

      <View className="rw-safe-bottom" />
    </View>
  )
}
