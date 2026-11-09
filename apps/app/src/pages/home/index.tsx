import { useCallback, useEffect, useState } from 'react'

import { Button, Image, Input, ScrollView, Text, View } from 'virtual:taro/components'
import Taro, { useDidShow } from 'virtual:taro/api'
import { POSITIONING } from '@robowiki/content'
import type { PartList } from '@robowiki/core'

import { ErrorState, SkeletonRows } from '@/components/Feedback'
import { LayerBadge } from '@/components/LayerBadge'
import { api, errorMessage } from '@/services/api'
import {
  partCategoryLabel,
  partImage,
  partPrice,
  resolvePartId,
  type PartView,
} from '@/services/parts'
import { openTab, queueCatalogSearch, showToast } from '@/utils/nav'
import { readRecent } from '@/utils/recent'
import { useThemeMode } from '@/utils/theme'
import './index.css'

const HOT_QUERY = '/parts?sort=featured&compact=true&limit=6'

type QuickEntry = { key: string; label: string; desc: string; wide?: boolean; action: () => void }

export default function HomePage() {
  const theme = useThemeMode()
  const [search, setSearch] = useState('')
  const [hot, setHot] = useState<PartView[]>([])
  const [hotLoading, setHotLoading] = useState(true)
  const [hotError, setHotError] = useState('')
  const [hotKey, setHotKey] = useState(0)
  const [recent, setRecent] = useState<PartView[]>([])

  useEffect(() => {
    let alive = true
    setHotLoading(true)
    setHotError('')
    api
      .request<PartList>(HOT_QUERY)
      .then((res) => {
        if (alive) setHot((res.items || []) as PartView[])
      })
      .catch((err) => {
        if (alive) setHotError(errorMessage(err))
      })
      .finally(() => {
        if (alive) setHotLoading(false)
      })
    return () => {
      alive = false
    }
  }, [hotKey])

  const loadRecent = useCallback(() => {
    const ids = readRecent()
    if (!ids.length) {
      setRecent([])
      return
    }
    Promise.all(
      ids.map((id) =>
        api
          .getPart(id)
          .then((item) => item as PartView)
          .catch(() => null),
      ),
    )
      .then((list) => {
        setRecent(list.filter((item): item is PartView => Boolean(item)))
      })
      .catch(() => {
        setRecent([])
      })
  }, [])

  useDidShow(loadRecent)

  const openPart = (id: string) => {
    Taro.navigateTo({ url: `/pages/part/index?id=${encodeURIComponent(id)}` })
  }

  const submitSearch = () => {
    const keyword = search.trim()
    if (!keyword) {
      openTab('/pages/index/index')
      return
    }
    queueCatalogSearch(keyword)
  }

  const resolveScan = async (raw: string) => {
    const text = raw.trim()
    if (!text) return
    const looksLikeLink = /\/parts\/([^/?#]+)\/([^/?#]+)\.html/i.test(text)
    const looksLikeSlug = /^[a-z0-9][a-z0-9._-]{1,63}$/i.test(text)

    let id = ''
    Taro.showLoading({ title: '查找部件…', mask: true })
    try {
      if (looksLikeLink) {
        id = (await resolvePartId(text)) || ''
      } else if (looksLikeSlug) {
        try {
          const part = await api.getPart(text)
          id = String(part.id || '')
        } catch {
          id = ''
        }
      }
    } catch {
      id = ''
    } finally {
      Taro.hideLoading()
    }

    if (id) {
      openPart(id)
      return
    }
    setSearch(text)
    showToast('没有匹配部件，已填入搜索')
  }

  const handleScan = async () => {
    if (typeof Taro.scanCode !== 'function') {
      showToast('当前环境不支持扫码')
      return
    }
    let result = ''
    try {
      const res = await Taro.scanCode({ onlyFromCamera: false, scanType: ['qrCode', 'barCode'] })
      result = String(res.result || '').trim()
    } catch (err) {
      const msg = err instanceof Error ? err.message : String((err as { errMsg?: string })?.errMsg || '')
      if (!/cancel/i.test(msg)) showToast('扫码失败，请重试')
      return
    }
    if (!result) {
      showToast('没有识别到内容')
      return
    }
    await resolveScan(result)
  }

  const quickEntries: QuickEntry[] = [
    {
      key: 'layers',
      label: '能力地图',
      desc: '四层能力做骨架，系统集成做大脑',
      wide: true,
      action: () => Taro.navigateTo({ url: '/pages/layers/index' }),
    },
    {
      key: 'catalog',
      label: '部件库',
      desc: '参数带来源，缺失写 null',
      action: () => openTab('/pages/index/index'),
    },
    {
      key: 'builds',
      label: '方案库',
      desc: '可复现方案，含 BOM 与步骤',
      action: () => openTab('/pages/builds/index'),
    },
    {
      key: 'community',
      label: '社区',
      desc: '写实测，不写「好用」',
      action: () => openTab('/pages/community/index'),
    },
    {
      key: 'learn',
      label: '学习',
      desc: '从零到跑通，按天给判据',
      action: () => Taro.navigateTo({ url: '/pages/learn/index' }),
    },
  ]

  return (
    <View className={`rw-page home ${theme === 'dark' ? 'dark' : ''}`}>
      <View className="home__hero">
        <Text className="home__eyebrow">可追溯工程知识库</Text>
        <Text className="rw-title home__title">四层能力做骨架，系统集成做大脑</Text>
        <Text className="rw-caption">
          {POSITIONING.short}。{POSITIONING.tagline}
        </Text>

        <View className="rw-field home__search">
          <Input
            className="rw-input"
            value={search}
            placeholder="搜索型号 / 厂商 / 关键词"
            confirmType="search"
            onInput={(event) => setSearch(event.detail.value)}
            onConfirm={submitSearch}
          />
          <Text className="home__search-action" onClick={submitSearch}>
            搜索
          </Text>
        </View>

        <Button className="rw-btn home__scan" onClick={handleScan}>
          扫一扫 · 部件条码 / 二维码
        </Button>
      </View>

      <View className="home__quick">
        {quickEntries.map((entry) => (
          <View
            className={`home__quick-card ${entry.wide ? 'home__quick-card--wide' : ''}`}
            key={entry.key}
            onClick={entry.action}
          >
            <Text className="home__quick-label">{entry.label}</Text>
            <Text className="home__quick-desc">{entry.desc}</Text>
          </View>
        ))}
      </View>

      <View className="home__section">
        <View className="rw-row rw-row--between home__section-head">
          <Text className="rw-subtitle">热门部件</Text>
          <Text className="rw-link rw-link--tap" onClick={() => openTab('/pages/index/index')}>
            全部部件 ›
          </Text>
        </View>

        {hotLoading ? <SkeletonRows rows={3} /> : null}
        {!hotLoading && hotError ? (
          <ErrorState message={hotError} onRetry={() => setHotKey((key) => key + 1)} />
        ) : null}
        {!hotLoading && !hotError && hot.length === 0 ? (
          <Text className="rw-caption">暂时没有推荐部件。</Text>
        ) : null}

        {!hotLoading && !hotError && hot.length > 0 ? (
          <ScrollView scrollX className="home__hot" showScrollbar={false}>
            <View className="home__hot-row">
              {hot.map((part) => {
                const image = partImage(part)
                return (
                  <View
                    className="home__hot-card"
                    key={part.id}
                    onClick={() => openPart(String(part.id))}
                  >
                    {image ? (
                      <Image className="home__hot-image" src={image} mode="aspectFill" />
                    ) : (
                      <View className="home__hot-image home__hot-image--empty">
                        {String(part.model || '?').slice(0, 2)}
                      </View>
                    )}
                    <Text className="home__hot-name rw-line-clamp-1">
                      {part.vendor} {part.model}
                    </Text>
                    <View className="home__hot-meta-row">
                      <LayerBadge category={part.category} />
                      <Text className="home__hot-meta rw-line-clamp-1">
                        {partCategoryLabel(part)}
                      </Text>
                    </View>
                    <Text className="home__hot-price">{partPrice(part)}</Text>
                  </View>
                )
              })}
            </View>
          </ScrollView>
        ) : null}
      </View>

      <View className="home__section">
        <View className="rw-row rw-row--between home__section-head">
          <Text className="rw-subtitle">最近浏览</Text>
          {recent.length ? (
            <Text className="rw-caption">最多 5 个</Text>
          ) : (
            <Text className="rw-link rw-link--tap" onClick={() => openTab('/pages/index/index')}>
              去部件库 ›
            </Text>
          )}
        </View>

        {recent.length === 0 ? (
          <Text className="rw-caption">看过的部件会出现在这里，方便现场回来接着查。</Text>
        ) : (
          <View className="rw-list">
            {recent.map((part) => {
              const image = partImage(part)
              return (
                <View
                  className="rw-list__row rw-list__row--tap"
                  key={part.id}
                  onClick={() => openPart(String(part.id))}
                >
                  {image ? (
                    <Image className="home__recent-thumb" src={image} mode="aspectFill" />
                  ) : (
                    <View className="home__recent-thumb home__recent-thumb--empty">
                      {String(part.model || '?').slice(0, 2)}
                    </View>
                  )}
                  <View className="rw-grow">
                    <Text className="home__recent-name rw-line-clamp-1">
                      {part.vendor} {part.model}
                    </Text>
                    <View className="home__recent-meta">
                      <LayerBadge category={part.category} />
                      <Text className="rw-caption rw-line-clamp-1">
                        {partCategoryLabel(part)} · {partPrice(part)}
                      </Text>
                    </View>
                  </View>
                  <Text className="rw-caption">查看 ›</Text>
                </View>
              )
            })}
          </View>
        )}
      </View>

      <View className="rw-safe-bottom" />
    </View>
  )
}
