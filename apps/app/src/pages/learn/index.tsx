import { useEffect, useState } from 'react'

import { Image, Text, View } from 'virtual:taro/components'
import { EMPTY } from '@robowiki/content'
import type { LearnArticle } from '@robowiki/core'

import { EmptyState, ErrorState, SkeletonRows } from '@/components/Feedback'
import { API_ORIGIN, absoluteUrl, api, errorMessage } from '@/services/api'
import { openExternal } from '@/utils/nav'
import { useThemeMode } from '@/utils/theme'
import './index.css'

export default function LearnPage() {
  const theme = useThemeMode()
  const [items, setItems] = useState<LearnArticle[]>([])
  const [updatedAt, setUpdatedAt] = useState('')
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [reloadKey, setReloadKey] = useState(0)

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
    const path = article.web_path || ''
    const url = /^https?:\/\//i.test(path) ? path : `${API_ORIGIN}${path}`
    openExternal(url, article.title)
  }

  return (
    <View className={`rw-page learn ${theme === 'dark' ? 'dark' : ''}`}>
      <View className="learn__head">
        <Text className="rw-title">教程库</Text>
        <Text className="rw-caption">
          {loading
            ? '正在加载教程…'
            : error
              ? '教程库暂时无法加载'
              : updatedAt
                ? `内容快照 ${updatedAt}`
                : `${items.length} 份资料`}
        </Text>
        <Text className="rw-caption">只收经典教程与资料；PDF 可在线阅读，导读回到本站。</Text>
      </View>

      {loading ? <SkeletonRows rows={4} /> : null}

      {!loading && error ? (
        <ErrorState message={error} onRetry={() => setReloadKey((key) => key + 1)} />
      ) : null}

      {!loading && !error && items.length === 0 ? (
        <EmptyState title={EMPTY.learn.title} hint={EMPTY.learn.hint} />
      ) : null}

      {!loading && !error && items.length > 0 ? (
        <View className="rw-list learn__list">
          {items.map((article) => {
            const cover = article.cover_url ? absoluteUrl(article.cover_url) : ''
            const kind = article.type === 'pdf' ? 'PDF' : article.type === 'link' ? '外链' : '本站笔记'
            const meta = [
              kind,
              article.source,
              article.year ? String(article.year) : '',
              article.pages ? `${article.pages} 页` : '',
              article.minutes ? `${article.minutes} 分钟` : '',
              article.level,
            ].filter(Boolean).join(' · ')
            return (
              <View
                className="rw-list__row rw-list__row--tap learn__row"
                key={article.slug}
                onClick={() => open(article)}
              >
                {cover ? (
                  <Image className="learn__thumb" src={cover} mode="aspectFill" />
                ) : (
                  <View className="learn__thumb learn__thumb--empty">{kind}</View>
                )}
                <View className="rw-grow rw-stack" style={{ gap: '6px' }}>
                  <View className="rw-row rw-row--between">
                    <Text className="learn__meta">{meta}</Text>
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
            )
          })}
        </View>
      ) : null}

      <View className="rw-safe-bottom" />
    </View>
  )
}
