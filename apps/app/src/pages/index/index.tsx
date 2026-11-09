import { useCallback, useEffect, useMemo, useRef, useState } from 'react'

import { Button, Image, Input, ScrollView, Text, View } from 'virtual:taro/components'
import Taro, { useDidShow, useRouter } from 'virtual:taro/api'
import {
  LAYER_BY_ID,
  LAYER_OF_CATEGORY,
  SKELETON_LAYERS,
  type LayerId,
} from '@robowiki/content'
import type { User } from '@robowiki/core'

import { EmptyState, ErrorState, SkeletonRows } from '@/components/Feedback'
import { LayerBadge, LayerDot } from '@/components/LayerBadge'
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
import { MAX_COMPARE, readCompare, writeCompare } from '@/utils/compare'
import { takeCatalogSearch, openTab } from '@/utils/nav'
import { useThemeMode } from '@/utils/theme'
import './index.css'

const PAGE_SIZE = 20
// 能力层没有后端参数：按层内品类各取一小页再合并，明确不冒充全量分页。
const LAYER_FETCH_LIMIT = 8
const IS_H5 = process.env.TARO_ENV === 'h5'

function safeDecode(value: string | undefined): string {
  const raw = value || ''
  try {
    return decodeURIComponent(raw)
  } catch {
    return raw
  }
}

export default function IndexPage() {
  const router = useRouter()
  const theme = useThemeMode()
  const initialQuery = safeDecode(router.params?.q).trim()
  const initialLayer = SKELETON_LAYERS.find(
    (layer) => layer.id === safeDecode(router.params?.layer),
  )?.id
  const [searchInput, setSearchInput] = useState(initialQuery)
  const [query, setQuery] = useState(initialQuery)
  const [category, setCategory] = useState('')
  const [layer, setLayer] = useState<LayerId | ''>(initialLayer || '')
  const [categories, setCategories] = useState<CatalogFacet[]>([])
  const [items, setItems] = useState<PartView[]>([])
  const [total, setTotal] = useState(0)
  const [loading, setLoading] = useState(true)
  const [loadingMore, setLoadingMore] = useState(false)
  const [error, setError] = useState('')
  const [reloadKey, setReloadKey] = useState(0)
  const [user, setUser] = useState<User | null>(cachedUser())
  const [compare, setCompare] = useState<string[]>(readCompare)

  const offsetRef = useRef(0)
  const requestIdRef = useRef(0)

  const layerInfo = layer ? LAYER_BY_ID[layer] : undefined
  // API 不支持 layer 参数：按层内品类取首屏后再按 LAYER_OF_CATEGORY 复核，
  // 兜住接口返回异常品类，也不伪造全量分页。
  const visibleItems = useMemo(
    () =>
      layerInfo
        ? items.filter((part) => LAYER_OF_CATEGORY[part.category] === layerInfo.id)
        : items,
    [items, layerInfo],
  )

  // 能力层筛选时只展示该层覆盖的品类，避免选了层又切到不相干品类。
  const facetCategories = useMemo(
    () =>
      layerInfo
        ? categories.filter((item) => layerInfo.categories.includes(item.category))
        : categories,
    [categories, layerInfo],
  )

  useDidShow(() => {
    setUser(cachedUser())
    setCompare(readCompare())
    // 首页搜索优先用 q 深链；小程序 / 旧路由拿不到 query 时用 storage 交接。
    const pending = takeCatalogSearch()
    if (pending) {
      setSearchInput(pending)
      setQuery(pending)
    }
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
      let data: PartView[] = []
      let nextTotal = 0

      if (layerInfo) {
        const cats = layerInfo.categories.filter(
          (cat) => !category || cat === category,
        )
        const pages = await Promise.all(
          cats.map((cat) =>
            listPartCards({
              q: query || undefined,
              category: cat,
              limit: LAYER_FETCH_LIMIT,
              offset: 0,
            }),
          ),
        )
        if (requestId !== requestIdRef.current) return

        const seen = new Set<string>()
        pages.forEach((page) => {
          nextTotal += page.total || 0
          const rows = (page.items || []) as PartView[]
          rows.forEach((part) => {
            const key = String(part.id)
            if (seen.has(key)) return
            if (LAYER_OF_CATEGORY[part.category] !== layerInfo.id) return
            seen.add(key)
            data.push(part)
          })
        })
      } else {
        const res = await listPartCards({
          q: query || undefined,
          category: category || undefined,
          limit: PAGE_SIZE,
          offset: 0,
        })
        if (requestId !== requestIdRef.current) return
        data = (res.items || []) as PartView[]
        nextTotal = res.total || 0
      }

      offsetRef.current = layerInfo ? 0 : data.length
      setItems(data)
      setTotal(nextTotal)
    } catch (err) {
      if (requestId === requestIdRef.current) setError(errorMessage(err))
    } finally {
      if (requestId === requestIdRef.current) setLoading(false)
    }
  }, [query, category, layerInfo])

  useEffect(() => {
    loadFirst()
  }, [loadFirst, reloadKey])

  const loadMore = async () => {
    if (layer || loading || loadingMore || items.length >= total) return
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

  const openAccount = () => {
    openTab('/pages/account/index')
  }

  const toggleCompare = (id: string) => {
    const value = String(id)
    if (compare.includes(value)) {
      const next = compare.filter((item) => item !== value)
      setCompare(next)
      writeCompare(next)
      return
    }
    if (compare.length >= MAX_COMPARE) {
      Taro.showToast({ title: `最多对比 ${MAX_COMPARE} 个部件`, icon: 'none' })
      return
    }
    const next = [...compare, value]
    setCompare(next)
    writeCompare(next)
  }

  const clearCompare = () => {
    setCompare([])
    writeCompare([])
  }

  const goCompare = () => {
    if (!compare.length) return
    Taro.navigateTo({
      url: `/pages/compare/index?ids=${encodeURIComponent(compare.join(','))}`,
    })
  }

  const hasFilter = Boolean(query || category || layer)

  const clearLayer = () => setLayer('')

  const clearFilters = () => {
    setSearchInput('')
    setQuery('')
    setCategory('')
    setLayer('')
  }

  return (
    <View
      className={`rw-page index ${theme === 'dark' ? 'dark' : ''} ${
        compare.length ? 'index--with-bar' : ''
      }`}
    >
      <View className="index__head">
        <View className="rw-row rw-row--between">
          <Text className="rw-title">
            部件目录{layerInfo ? ` · ${layerInfo.name}` : ''}
          </Text>
          {user ? (
            <Text className="rw-link" onClick={openAccount}>
              {user.display_name || user.handle}
            </Text>
          ) : (
            <Text className="rw-link" onClick={openLogin}>
              登录
            </Text>
          )}
        </View>
        <Text className="rw-caption">
          {loading
            ? '正在加载目录…'
            : error
              ? '目录暂时无法加载'
              : layerInfo
                ? `匹配 ${total} 个 · 已加载 ${visibleItems.length} 个`
                : `共 ${total} 个部件`}
        </Text>

        {layerInfo ? (
          <View className="index__layer">
            <View className="index__layer-main">
              <LayerDot layer={layerInfo} />
              <Text className="index__layer-text">
                按能力层筛选 · 每品类前 {LAYER_FETCH_LIMIT} 个
              </Text>
            </View>
            <Text className="index__layer-clear" onClick={clearLayer}>
              清除
            </Text>
          </View>
        ) : null}

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
            {facetCategories.map((item) => (
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

      {!loading && !error && visibleItems.length === 0 ? (
        <EmptyState
          title={
            layerInfo
              ? '这一层暂时没有匹配的部件'
              : hasFilter
                ? '没有匹配的部件'
                : '目录暂时为空'
          }
          hint={
            layerInfo
              ? `能力层按品类各取前 ${LAYER_FETCH_LIMIT} 个，清除筛选可看完整目录`
              : hasFilter
                ? '换个关键词，或切回全部品类'
                : '稍后再来看看'
          }
          actionLabel={hasFilter ? '清除筛选' : undefined}
          onAction={hasFilter ? clearFilters : undefined}
        />
      ) : null}

      {!loading && !error && visibleItems.length > 0 ? (
        <View className="rw-list index__list">
          {visibleItems.map((part) => {
            const image = partImage(part)
            const facts = partFacts(part).slice(0, 4)
            const rating = partRating(part)
            const selected = compare.includes(String(part.id))
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
                  <View className="index__meta">
                    <LayerBadge category={part.category} />
                    <Text className="rw-caption rw-line-clamp-1 index__category">
                      {partCategoryLabel(part)}
                    </Text>
                  </View>
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
                  </View>
                </View>

                <View
                  className={`index__compare ${selected ? 'index__compare--on' : ''}`}
                  onClick={(event) => {
                    event.stopPropagation()
                    toggleCompare(String(part.id))
                  }}
                >
                  <Text className="index__compare-box">{selected ? '✓' : '+'}</Text>
                  <Text className="index__compare-text">对比</Text>
                </View>
              </View>
            )
          })}
        </View>
      ) : null}

      {!loading && !error && visibleItems.length > 0 ? (
        <View className="index__footer">
          {layerInfo ? (
            <Text className="rw-caption">
              能力层按品类各取前 {LAYER_FETCH_LIMIT} 个，不做全量分页；清除后可继续加载。
            </Text>
          ) : visibleItems.length < total ? (
            <Button className="rw-btn" disabled={loadingMore} onClick={loadMore}>
              {loadingMore ? '加载中…' : `加载更多（${visibleItems.length}/${total}）`}
            </Button>
          ) : (
            <Text className="rw-caption">已经到底了</Text>
          )}
        </View>
      ) : null}

      {compare.length ? (
        <View className={`index__compare-bar ${IS_H5 ? 'index__compare-bar--h5' : ''}`}>
          <View className="rw-grow">
            <Text className="rw-subtitle">对比 {compare.length}/{MAX_COMPARE}</Text>
            <Text className="rw-caption index__compare-tip">勾选部件后并排看参数</Text>
          </View>
          <Text className="index__compare-clear" onClick={clearCompare}>
            清空
          </Text>
          <Button className="rw-btn rw-btn--primary" onClick={goCompare}>
            对比（{compare.length}）
          </Button>
        </View>
      ) : null}

      <View className="rw-safe-bottom" />
    </View>
  )
}
