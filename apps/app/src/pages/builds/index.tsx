import { useCallback, useEffect, useRef, useState } from 'react'

import { Button, Image, Input, ScrollView, Text, View } from '@tarojs/components'
import Taro from '@tarojs/taro'
import { EMPTY, PAGE_SIZE } from '@robowiki/content'
import type { BuildSummary } from '@robowiki/core'

import { EmptyState, ErrorState, SkeletonRows } from '@/components/Feedback'
import { api, errorMessage } from '@/services/api'
import {
  buildFacts,
  buildImage,
  buildPrice,
  buildSubtype,
} from '@/services/builds'
import { useThemeMode } from '@/utils/theme'
import './index.css'

const SUBTYPES = [
  { value: '', label: '全部' },
  { value: 'quadruped', label: '四足' },
  { value: 'humanoid', label: '人形' },
  { value: 'biped', label: '双足' },
  { value: 'wheeled_quadruped', label: '四轮足' },
  { value: 'wheeled_quadruped_inward_knee', label: '四轮足 · 内膝肘' },
]

export default function BuildsPage() {
  const theme = useThemeMode()
  const [searchInput, setSearchInput] = useState('')
  const [query, setQuery] = useState('')
  const [subtype, setSubtype] = useState('')
  const [items, setItems] = useState<BuildSummary[]>([])
  const [total, setTotal] = useState(0)
  const [loading, setLoading] = useState(true)
  const [loadingMore, setLoadingMore] = useState(false)
  const [error, setError] = useState('')
  const [reloadKey, setReloadKey] = useState(0)

  const offsetRef = useRef(0)
  const requestIdRef = useRef(0)

  // 与部件页一致：停止输入 350ms 再请求。
  useEffect(() => {
    const timer = setTimeout(() => setQuery(searchInput.trim()), 350)
    return () => clearTimeout(timer)
  }, [searchInput])

  const loadFirst = useCallback(async () => {
    const requestId = ++requestIdRef.current
    setLoading(true)
    setError('')
    try {
      const res = await api.listBuilds({
        q: query || undefined,
        subtype: subtype || undefined,
        limit: PAGE_SIZE.builds,
        offset: 0,
      })
      if (requestId !== requestIdRef.current) return
      const data = res.items || []
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
      const res = await api.listBuilds({
        q: query || undefined,
        subtype: subtype || undefined,
        limit: PAGE_SIZE.builds,
        offset: offsetRef.current,
      })
      if (requestId !== requestIdRef.current) return
      const data = res.items || []
      offsetRef.current += data.length
      setItems((prev) => [...prev, ...data])
      setTotal(res.total || 0)
    } catch (err) {
      Taro.showToast({ title: errorMessage(err), icon: 'none' })
    } finally {
      setLoadingMore(false)
    }
  }

  const openBuild = (build: BuildSummary) => {
    Taro.navigateTo({ url: `/pages/build/index?id=${encodeURIComponent(String(build.id))}` })
  }

  const hasFilter = Boolean(query || subtype)

  return (
    <View className={`rw-page builds ${theme === 'dark' ? 'dark' : ''}`}>
      <View className="builds__head">
        <Text className="rw-title">方案库</Text>
        <Text className="rw-caption">
          {loading ? '正在加载方案…' : error ? '方案库暂时无法加载' : `共 ${total} 套可复现方案`}
        </Text>

        <View className="rw-field builds__search">
          <Input
            className="rw-input"
            value={searchInput}
            placeholder="搜索型号 / 厂商 / 方案名"
            confirmType="search"
            onInput={(event) => setSearchInput(event.detail.value)}
            onConfirm={() => setQuery(searchInput.trim())}
          />
          {searchInput ? (
            <Text className="builds__clear" onClick={() => setSearchInput('')}>
              清除
            </Text>
          ) : null}
        </View>

        <ScrollView scrollX className="rw-chips" showScrollbar={false}>
          <View className="builds__chips">
            {SUBTYPES.map((item) => (
              <View
                key={item.value || 'all'}
                className={`rw-chip rw-chip--touch ${subtype === item.value ? 'rw-chip--active' : ''}`}
                onClick={() => setSubtype(item.value)}
              >
                {item.label}
              </View>
            ))}
          </View>
        </ScrollView>
      </View>

      {loading ? <SkeletonRows rows={5} /> : null}

      {!loading && error ? (
        <ErrorState message={error} onRetry={() => setReloadKey((key) => key + 1)} />
      ) : null}

      {!loading && !error && items.length === 0 ? (
        <EmptyState
          title={EMPTY.builds.title}
          hint={EMPTY.builds.hint}
          actionLabel={hasFilter ? EMPTY.builds.action : undefined}
          onAction={
            hasFilter
              ? () => {
                  setSearchInput('')
                  setQuery('')
                  setSubtype('')
                }
              : undefined
          }
        />
      ) : null}

      {!loading && !error && items.length > 0 ? (
        <View className="rw-list builds__list">
          {items.map((build) => {
            const image = buildImage(build)
            const facts = buildFacts(build).slice(0, 3)
            return (
              <View
                className="rw-list__row rw-list__row--tap builds__row"
                key={build.id}
                onClick={() => openBuild(build)}
              >
                {image ? (
                  <Image className="builds__thumb" src={image} mode="aspectFill" lazyLoad />
                ) : (
                  <View className="builds__thumb builds__thumb--empty">
                    {String(build.model || '?').slice(0, 2)}
                  </View>
                )}

                <View className="rw-grow rw-stack" style={{ gap: '4px' }}>
                  <Text className="builds__title rw-line-clamp-2">
                    {build.title || `${build.vendor} ${build.model}`}
                  </Text>
                  <Text className="rw-caption rw-line-clamp-1">
                    {build.vendor}
                    {build.vendor_cn ? `（${build.vendor_cn}）` : ''} · {build.model}
                  </Text>

                  <View className="builds__badges">
                    {buildSubtype(build) ? (
                      <Text className="rw-badge">{buildSubtype(build)}</Text>
                    ) : null}
                  </View>

                  <View className="rw-row rw-row--between builds__foot">
                    <Text className="builds__fact rw-line-clamp-1">
                      {facts.length
                        ? facts.map((fact) => `${fact.label} ${fact.value}`).join(' · ')
                        : '参数以详情页为准'}
                    </Text>
                    <Text className="builds__price">{buildPrice(build)}</Text>
                  </View>
                </View>
              </View>
            )
          })}
        </View>
      ) : null}

      {!loading && !error && items.length > 0 ? (
        <View className="builds__footer">
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
