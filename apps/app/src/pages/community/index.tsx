import { useCallback, useEffect, useRef, useState } from 'react'

import { Button, ScrollView, Text, View } from 'virtual:taro/components'
import Taro, { useDidShow } from 'virtual:taro/api'
import { EMPTY, PAGE_SIZE } from '@robowiki/content'
import type { PostSummary } from '@robowiki/core'

import { EmptyState, ErrorState, SkeletonRows } from '@/components/Feedback'
import { api, errorMessage } from '@/services/api'
import { authorName, formatTime } from '@/utils/format'
import { useThemeMode } from '@/utils/theme'
import './index.css'

const KINDS = [
  { value: '', label: '全部' },
  { value: 'discussion', label: '讨论' },
  { value: 'review', label: '评价' },
  { value: 'build', label: '方案' },
]

const SOLVED = [
  { value: '', label: '全部状态' },
  { value: 'false', label: '待解决' },
  { value: 'true', label: '已解决' },
]

const KIND_LABEL: Record<string, string> = {
  discussion: '讨论',
  review: '评价',
  build: '方案',
}

export default function CommunityPage() {
  const theme = useThemeMode()
  const [kind, setKind] = useState('')
  const [solved, setSolved] = useState('')
  const [items, setItems] = useState<PostSummary[]>([])
  const [total, setTotal] = useState(0)
  const [loading, setLoading] = useState(true)
  const [loadingMore, setLoadingMore] = useState(false)
  const [error, setError] = useState('')
  const [reloadKey, setReloadKey] = useState(0)

  const offsetRef = useRef(0)
  const requestIdRef = useRef(0)
  const firstShowRef = useRef(true)

  const loadFirst = useCallback(async () => {
    const requestId = ++requestIdRef.current
    setLoading(true)
    setError('')
    try {
      const res = await api.listPosts({
        sort: 'hot',
        kind: kind || undefined,
        solved: kind === 'discussion' && solved ? solved === 'true' : undefined,
        limit: PAGE_SIZE.community,
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
  }, [kind, solved])

  useEffect(() => {
    loadFirst()
  }, [loadFirst, reloadKey])

  // 发帖 / 编辑 / 删除后返回社区，刷新第一页。
  useDidShow(() => {
    if (firstShowRef.current) {
      firstShowRef.current = false
      return
    }
    setReloadKey((key) => key + 1)
  })

  const loadMore = async () => {
    if (loading || loadingMore || items.length >= total) return
    const requestId = requestIdRef.current
    setLoadingMore(true)
    try {
      const res = await api.listPosts({
        sort: 'hot',
        kind: kind || undefined,
        solved: kind === 'discussion' && solved ? solved === 'true' : undefined,
        limit: PAGE_SIZE.community,
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

  const openPost = (post: PostSummary) => {
    Taro.navigateTo({ url: `/pages/post/index?id=${encodeURIComponent(String(post.id))}` })
  }

  const openCompose = () => {
    Taro.navigateTo({ url: '/pages/compose/index' })
  }

  const pickSolved = (value: string) => {
    // 解决状态只对讨论生效：选待解决 / 已解决时自动切到讨论。
    if (value) setKind('discussion')
    setSolved(value)
  }

  return (
    <View className={`rw-page community ${theme === 'dark' ? 'dark' : ''}`}>
      <View className="community__head">
        <View className="rw-row rw-row--between">
          <Text className="rw-title">社区</Text>
          <Button className="rw-btn rw-btn--primary community__compose" onClick={openCompose}>
            发帖
          </Button>
        </View>
        <Text className="rw-caption">
          {loading ? '正在加载讨论…' : error ? '社区暂时无法加载' : `共 ${total} 条实测与讨论`}
        </Text>
        <ScrollView scrollX className="rw-chips" showScrollbar={false}>
          <View className="community__chips">
            {KINDS.map((item) => (
              <View
                key={item.value || 'all'}
                className={`rw-chip rw-chip--touch ${kind === item.value ? 'rw-chip--active' : ''}`}
                onClick={() => {
                  setKind(item.value)
                  if (item.value !== 'discussion') setSolved('')
                }}
              >
                {item.label}
              </View>
            ))}
          </View>
        </ScrollView>
        <ScrollView scrollX className="rw-chips" showScrollbar={false}>
          <View className="community__chips">
            {SOLVED.map((item) => (
              <View
                key={item.value || 'solved-all'}
                className={`rw-chip rw-chip--touch ${solved === item.value ? 'rw-chip--active' : ''}`}
                onClick={() => pickSolved(item.value)}
              >
                {item.label}
              </View>
            ))}
          </View>
        </ScrollView>
        <Text className="rw-caption">解决状态只对讨论生效，选择后会自动切到讨论。</Text>
      </View>

      {loading ? <SkeletonRows rows={5} /> : null}

      {!loading && error ? (
        <ErrorState message={error} onRetry={() => setReloadKey((key) => key + 1)} />
      ) : null}

      {!loading && !error && items.length === 0 ? (
        <EmptyState
          title={EMPTY.community.title}
          hint={EMPTY.community.hint}
          actionLabel={EMPTY.community.action}
          onAction={openCompose}
        />
      ) : null}

      {!loading && !error && items.length > 0 ? (
        <View className="community__list">
          {items.map((post) => {
            const accepted = Boolean(post.accepted_comment_id)
            const edited = Boolean(post.updated_at && post.updated_at !== post.created_at)
            return (
              <View
                className="community__card"
                key={post.id}
                onClick={() => openPost(post)}
              >
                <View className="community__card-head">
                  <Text className="rw-badge">{KIND_LABEL[post.kind] || post.kind}</Text>
                  {post.pinned ? <Text className="rw-badge rw-badge--warn">置顶</Text> : null}
                  {accepted ? <Text className="rw-badge rw-badge--success">已解决</Text> : null}
                  {post.rating ? (
                    <Text className="community__rating">★ {post.rating}</Text>
                  ) : null}
                  <Text className="rw-caption community__time">
                    {formatTime(post.created_at)}
                    {edited ? ' · 已编辑' : ''}
                  </Text>
                </View>

                <Text className="community__title rw-line-clamp-2">{post.title}</Text>
                {post.body ? (
                  <Text className="community__body rw-line-clamp-2">{post.body}</Text>
                ) : null}

                <View className="community__foot">
                  <Text className="community__author">
                    {authorName(post.author)}
                    {post.author?.is_staff ? ' · 站务' : ''}
                  </Text>
                  <View className="community__stats">
                    {post.part_title ? (
                      <Text className="community__stat rw-line-clamp-1">{post.part_title}</Text>
                    ) : null}
                    <Text className="community__stat">分 {post.score}</Text>
                    <Text className="community__stat">评 {post.comment_count}</Text>
                  </View>
                </View>
              </View>
            )
          })}
        </View>
      ) : null}

      {!loading && !error && items.length > 0 ? (
        <View className="community__footer">
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
