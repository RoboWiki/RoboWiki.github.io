import { useCallback, useEffect, useRef, useState } from 'react'

import { Button, Image, Input, ScrollView, Text, View } from 'virtual:taro/components'
import Taro from 'virtual:taro/api'

import { EmptyState, ErrorState, SkeletonRows } from '@/components/Feedback'
import { errorMessage, listCategoryFacets, type CatalogFacet } from '@/services/api'
import {
  listPartCards,
  partFacts,
  partImage,
  partPrice,
  partRating,
  type PartView,
} from '@/services/parts'
import { useThemeMode } from '@/utils/theme'
import './index.css'

const PAGE_SIZE = 20
const CATEGORY = 'equipment'

export default function EquipmentPage() {
  const theme = useThemeMode()
  const [searchInput, setSearchInput] = useState('')
  const [query, setQuery] = useState('')
  const [subtype, setSubtype] = useState('')
  const [facets, setFacets] = useState<CatalogFacet[]>([])
  const [items, setItems] = useState<PartView[]>([])
  const [total, setTotal] = useState(0)
  const [loading, setLoading] = useState(true)
  const [loadingMore, setLoadingMore] = useState(false)
  const [error, setError] = useState('')
  const [reloadKey, setReloadKey] = useState(0)

  const offsetRef = useRef(0)
  const requestIdRef = useRef(0)

  useEffect(() => {
    let alive = true
    listCategoryFacets(CATEGORY)
      .then((list) => {
        if (alive) setFacets(list)
      })
      .catch(() => {
        // 子类 chips 是辅助筛选：取不到时仍可浏览全部设备。
      })
    return () => {
      alive = false
    }
  }, [])

  useEffect(() => {
    const timer = setTimeout(() => setQuery(searchInput.trim()), 350)
    return () => clearTimeout(timer)
  }, [searchInput])

  const loadFirst = useCallback(async () => {
    const requestId = ++requestIdRef.current
    setLoading(true)
    setError('')
    try {
      const res = await listPartCards({
        q: query || undefined,
        category: CATEGORY,
        subtype: subtype || undefined,
        limit: PAGE_SIZE,
        offset: 0,
      })
      if (requestId !== requestIdRef.current) return
      const data = (res.items || []) as PartView[]
      offsetRef.current = data.length
      setItems(data)
      setTotal(res.total || 0)
    } catch (err) {
      if (requestId === requestIdRef.current) setError(errorMessage(err))
    } finally {
      if (requestId === requestIdRef.current) setLoading(false)
    }
  }, [query, subtype])

  useEffect(() => {
    loadFirst()
  }, [loadFirst, reloadKey])

  const loadMore = async () => {
    if (loading || loadingMore || items.length >= total) return
    const requestId = requestIdRef.current
    setLoadingMore(true)
    try {
      const res = await listPartCards({
        q: query || undefined,
        category: CATEGORY,
        subtype: subtype || undefined,
        limit: PAGE_SIZE,
        offset: offsetRef.current,
      })
      if (requestId !== requestIdRef.current) return
      const data = (res.items || []) as PartView[]
      offsetRef.current += data.length
      setItems((prev) => [...prev, ...data])
      setTotal(res.total || 0)
    } catch (err) {
      Taro.showToast({ title: errorMessage(err), icon: 'none' })
    } finally {
      setLoadingMore(false)
    }
  }

  const openPart = (part: PartView) => {
    Taro.navigateTo({ url: `/pages/part/index?id=${encodeURIComponent(String(part.id))}` })
  }

  return (
    <View className={`rw-page equipment ${theme === 'dark' ? 'dark' : ''}`}>
      <View className="equipment__head">
        <Text className="rw-title">设备库</Text>
        <Text className="rw-caption">
          {loading ? '正在加载设备…' : error ? '设备库暂时无法加载' : `共 ${total} 件 · 打印机 / 激光 / 焊台 / 电源 / 仪器 / 工具`}
        </Text>
        <View className="rw-field equipment__search">
          <Input
            className="rw-input"
            value={searchInput}
            placeholder="搜索型号 / 厂商 / 类别"
            confirmType="search"
            onInput={(event) => setSearchInput(event.detail.value)}
            onConfirm={() => setQuery(searchInput.trim())}
          />
          {searchInput ? (
            <Text className="equipment__clear" onClick={() => setSearchInput('')}>
              清除
            </Text>
          ) : null}
        </View>

        <ScrollView scrollX className="rw-chips" showScrollbar={false}>
          <View className="equipment__chips">
            <View
              className={`rw-chip ${subtype ? '' : 'rw-chip--active'}`}
              onClick={() => setSubtype('')}
            >
              全部
            </View>
            {facets.map((item) => (
              <View
                key={item.subtype}
                className={`rw-chip ${subtype === item.subtype ? 'rw-chip--active' : ''}`}
                onClick={() => setSubtype(item.subtype || '')}
              >
                {item.subtype_label || item.subtype}
                <Text className="equipment__chip-count">{item.n}</Text>
              </View>
            ))}
          </View>
        </ScrollView>
      </View>

      {loading ? <SkeletonRows rows={4} /> : null}
      {!loading && error ? (
        <ErrorState message={error} onRetry={() => setReloadKey((key) => key + 1)} />
      ) : null}

      {!loading && !error && items.length === 0 ? (
        <EmptyState
          title={query || subtype ? '没有匹配的设备' : '设备库暂时为空'}
          hint={query || subtype ? '换个关键词，或切回全部类别' : '稍后再来看看'}
        />
      ) : null}

      {!loading && !error && items.length > 0 ? (
        <View className="rw-list equipment__list">
          {items.map((part) => {
            const image = partImage(part)
            const facts = partFacts(part).slice(0, 3)
            const rating = partRating(part)
            return (
              <View
                className="rw-list__row rw-list__row--tap"
                key={part.id}
                onClick={() => openPart(part)}
              >
                {image ? (
                  <Image className="rw-thumb" src={image} mode="aspectFill" />
                ) : (
                  <View className="rw-empty-thumb">{String(part.model || '?').slice(0, 2)}</View>
                )}
                <View className="rw-grow rw-stack" style={{ gap: '4px' }}>
                  <View className="rw-row rw-row--between">
                    <Text className="equipment__name rw-line-clamp-1">
                      {part.vendor} {part.model}
                    </Text>
                    <Text className="equipment__price">{partPrice(part)}</Text>
                  </View>
                  <Text className="rw-caption rw-line-clamp-1">
                    {part.subtype_label || '设备'}
                  </Text>
                  <View className="equipment__facts">
                    {facts.map((fact) => (
                      <Text className="equipment__fact" key={fact.key}>
                        {fact.label} {fact.value}
                      </Text>
                    ))}
                  </View>
                  <Text className="rw-caption">
                    {rating.count ? `★ ${rating.avg ?? '-'}（${rating.count}）` : '暂无评分'}
                  </Text>
                </View>
              </View>
            )
          })}
        </View>
      ) : null}

      {!loading && !error && items.length < total ? (
        <View className="equipment__footer">
          <Button className="rw-btn rw-btn--ghost" onClick={loadMore} disabled={loadingMore}>
            {loadingMore ? '加载中…' : `加载更多（${items.length}/${total}）`}
          </Button>
        </View>
      ) : null}
    </View>
  )
}
