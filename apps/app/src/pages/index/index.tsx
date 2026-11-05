import { useCallback, useEffect, useRef, useState } from 'react'

import { Button, Image, Input, ScrollView, Text, View } from '@tarojs/components'
import Taro, { useDidShow } from '@tarojs/taro'
import type { User } from '@robowiki/core'

import { EmptyState, ErrorState, SkeletonRows } from '@/components/Feedback'
import { cachedUser, errorMessage, listCategories, type CatalogFacet } from '@/services/api'
import {
  listPartCards,
  partCategoryLabel,
  partFacts,
  partImage,
  partPrice,
  partRating,
  type PartView,
} from '@/services/parts'
import './index.css'

const PAGE_SIZE = 20

export default function IndexPage() {
  const [searchInput, setSearchInput] = useState('')
  const [query, setQuery] = useState('')
  const [category, setCategory] = useState('')
  const [categories, setCategories] = useState<CatalogFacet[]>([])
  const [items, setItems] = useState<PartView[]>([])
  const [total, setTotal] = useState(0)
  const [loading, setLoading] = useState(true)
  const [loadingMore, setLoadingMore] = useState(false)
  const [error, setError] = useState('')
  const [reloadKey, setReloadKey] = useState(0)
  const [user, setUser] = useState<User | null>(cachedUser())

  const offsetRef = useRef(0)
  const requestIdRef = useRef(0)

  useDidShow(() => {
    setUser(cachedUser())
  })

  useEffect(() => {
    let alive = true
    listCategories()
      .then((list) => {
        if (alive) setCategories(list)
      })
      .catch(() => {
        // 品类 chips 是辅助入口：/catalog 失败时退回“全部”，不阻断目录。
      })
    return () => {
      alive = false
    }
  }, [])

  // 输入防抖：停止输入 350ms 后才真正请求，避免每个字符打一次 API。
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
        category: category || undefined,
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
  }, [query, category])

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
        category: category || undefined,
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

  const openLogin = () => {
    Taro.navigateTo({ url: '/pages/login/index' })
  }

  const hasFilter = Boolean(query || category)

  return (
    <View className="rw-page index">
      <View className="index__head">
        <View className="rw-row rw-row--between">
          <Text className="rw-title">部件目录</Text>
          {user ? (
            <Text className="rw-caption">{user.display_name || user.handle}</Text>
          ) : (
            <Text className="rw-link" onClick={openLogin}>
              登录
            </Text>
          )}
        </View>
        <Text className="rw-caption">{loading ? '正在加载目录…' : `共 ${total} 个部件`}</Text>

        <View className="rw-field index__search">
          <Input
            className="rw-input"
            value={searchInput}
            placeholder="搜索型号 / 厂商"
            confirmType="search"
            onInput={(event) => setSearchInput(event.detail.value)}
            onConfirm={() => setQuery(searchInput.trim())}
          />
          {searchInput ? (
            <Text className="index__clear" onClick={() => setSearchInput('')}>
              清除
            </Text>
          ) : null}
        </View>

        <ScrollView scrollX className="rw-chips" showScrollbar={false}>
          <View className="index__chips">
            <View
              className={`rw-chip ${category ? '' : 'rw-chip--active'}`}
              onClick={() => setCategory('')}
            >
              全部
            </View>
            {categories.map((item) => (
              <View
                key={item.category}
                className={`rw-chip ${category === item.category ? 'rw-chip--active' : ''}`}
                onClick={() => setCategory(item.category)}
              >
                {item.category_label}
              </View>
            ))}
          </View>
        </ScrollView>
      </View>

      {loading ? <SkeletonRows rows={6} /> : null}

      {!loading && error ? (
        <ErrorState message={error} onRetry={() => setReloadKey((key) => key + 1)} />
      ) : null}

      {!loading && !error && items.length === 0 ? (
        <EmptyState
          title={hasFilter ? '没有匹配的部件' : '目录暂时为空'}
          hint={hasFilter ? '换个关键词，或切回全部品类' : '稍后再来看看'}
          actionLabel={hasFilter ? '清除筛选' : undefined}
          onAction={
            hasFilter
              ? () => {
                  setSearchInput('')
                  setQuery('')
                  setCategory('')
                }
              : undefined
          }
        />
      ) : null}

      {!loading && !error && items.length > 0 ? (
        <View className="rw-list index__list">
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
                  <Image className="rw-thumb" src={image} mode="aspectFill" lazyLoad />
                ) : (
                  <View className="rw-empty-thumb">{String(part.model || '?').slice(0, 2)}</View>
                )}
                <View className="rw-grow rw-stack" style={{ gap: '4px' }}>
                  <View className="rw-row rw-row--between">
                    <Text className="index__name rw-line-clamp-1">
                      {part.vendor} {part.model}
                    </Text>
                    <Text className="index__price">{partPrice(part)}</Text>
                  </View>
                  <Text className="rw-caption rw-line-clamp-1">{partCategoryLabel(part)}</Text>
                  <View className="index__facts">
                    {facts.map((fact) => (
                      <Text className="index__fact" key={fact.key}>
                        {fact.label} {fact.value}
                      </Text>
                    ))}
                  </View>
                  <View className="rw-row rw-row--between">
                    <Text className="rw-caption">
                      {rating.count ? `★ ${rating.avg ?? '-'}（${rating.count}）` : '暂无评分'}
                    </Text>
                    {part.verified ? <Text className="rw-badge">已核对</Text> : null}
                  </View>
                </View>
              </View>
            )
          })}
        </View>
      ) : null}

      {!loading && !error && items.length > 0 ? (
        <View className="index__footer">
          {items.length < total ? (
            <Button className="rw-btn" disabled={loadingMore} onClick={loadMore}>
              {loadingMore ? '加载中…' : `加载更多（${items.length}/${total}）`}
            </Button>
          ) : (
            <Text className="rw-caption">已经到底了</Text>
          )}
        </View>
      ) : null}

      <View className="rw-safe-bottom" />
    </View>
  )
}
