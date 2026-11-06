import { useEffect, useMemo, useState } from 'react'

import { ScrollView, Text, View } from '@tarojs/components'
import {
  EMPTY,
  LAYER_BY_ID,
  SKELETON_LAYERS,
  type LayerId,
} from '@robowiki/content'
import type { LearnArticle } from '@robowiki/core'

import { EmptyState, ErrorState, SkeletonRows } from '@/components/Feedback'
import { LayerDot } from '@/components/LayerBadge'
import { API_ORIGIN, api, errorMessage } from '@/services/api'
import { openExternal } from '@/utils/nav'
import { useThemeMode } from '@/utils/theme'
import './index.css'

export default function LearnPage() {
  const theme = useThemeMode()
  const [items, setItems] = useState<LearnArticle[]>([])
  const [updatedAt, setUpdatedAt] = useState('')
  const [activeLayer, setActiveLayer] = useState<LayerId | ''>('')
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [reloadKey, setReloadKey] = useState(0)

  // 只做客户端交集过滤：指南 slug 与 layer.guides 对齐，不发额外请求。
  const visibleItems = useMemo(() => {
    if (!activeLayer) return items
    const guides = LAYER_BY_ID[activeLayer].guides
    return items.filter((article) => guides.includes(article.slug))
  }, [items, activeLayer])

  useEffect(() => {
    let alive = true
    setLoading(true)
    setError('')
    api
      .listLearn()
      .then((data) => {
        if (!alive) return
        setItems(data.items || [])
        setUpdatedAt(data.updated_at || '')
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
  }, [reloadKey])

  const open = (article: LearnArticle) => {
    // 正文仍在网页（Markdown 渲染、代码高亮、SEO 只有一份），端内只做列表与导读。
    openExternal(`${API_ORIGIN}${article.web_path}`, article.title)
  }

  return (
    <View className={`rw-page learn ${theme === 'dark' ? 'dark' : ''}`}>
      <View className="learn__head">
        <Text className="rw-title">学习</Text>
        <Text className="rw-caption">
          {loading
            ? '正在加载指南…'
            : error
              ? '指南暂时无法加载'
              : activeLayer
                ? `能力层筛选 · ${visibleItems.length} 篇`
                : updatedAt
                  ? `内容快照 ${updatedAt}`
                  : `${items.length} 篇站内指南`}
        </Text>
        <Text className="rw-caption">先看思路，再回去选型；每篇都能回到对应的部件与来源。</Text>

        <View className="learn__layer-filter">
          <Text className="learn__layer-label">按能力层看</Text>
          <ScrollView scrollX className="rw-chips" showScrollbar={false}>
            <View className="learn__layer-chips">
              <View
                className={`rw-chip rw-chip--touch ${activeLayer ? '' : 'rw-chip--active'}`}
                onClick={() => setActiveLayer('')}
              >
                全部
              </View>
              {SKELETON_LAYERS.map((layer) => (
                <View
                  key={layer.id}
                  className={`rw-chip rw-chip--touch learn__layer-chip ${
                    activeLayer === layer.id ? 'rw-chip--active' : ''
                  }`}
                  onClick={() => setActiveLayer(layer.id)}
                >
                  <LayerDot layer={layer} />
                  <Text>{layer.name}</Text>
                </View>
              ))}
            </View>
          </ScrollView>
          {activeLayer ? (
            <Text className="rw-caption">
              只看「{LAYER_BY_ID[activeLayer].name}」相关指南，点「全部」取消。
            </Text>
          ) : null}
        </View>
      </View>

      {loading ? <SkeletonRows rows={4} /> : null}

      {!loading && error ? (
        <ErrorState message={error} onRetry={() => setReloadKey((key) => key + 1)} />
      ) : null}

      {!loading && !error && visibleItems.length === 0 ? (
        activeLayer ? (
          <EmptyState
            title="这个能力层还没有对应指南"
            hint="先看全部指南，或去能力地图了解四层分工"
            actionLabel="看全部指南"
            onAction={() => setActiveLayer('')}
          />
        ) : (
          <EmptyState title={EMPTY.learn.title} hint={EMPTY.learn.hint} />
        )
      ) : null}

      {!loading && !error && visibleItems.length > 0 ? (
        <View className="rw-list learn__list">
          {visibleItems.map((article) => (
            <View
              className="rw-list__row rw-list__row--tap learn__row"
              key={article.slug}
              onClick={() => open(article)}
            >
              <View className="rw-grow rw-stack" style={{ gap: '6px' }}>
                <View className="rw-row rw-row--between">
                  <Text className="learn__meta">
                    {article.level || '指南'} · {article.minutes || '—'} 分钟
                  </Text>
                  <Text className="rw-link">阅读 ›</Text>
                </View>
                <Text className="rw-subtitle learn__title">{article.title}</Text>
                {article.summary ? (
                  <Text className="rw-caption learn__summary">{article.summary}</Text>
                ) : null}
                {article.tags?.length ? (
                  <View className="learn__tags">
                    {article.tags.map((tag) => (
                      <Text className="rw-badge" key={tag}>
                        {tag}
                      </Text>
                    ))}
                  </View>
                ) : null}
              </View>
            </View>
          ))}
        </View>
      ) : null}

      <View className="rw-safe-bottom" />
    </View>
  )
}
