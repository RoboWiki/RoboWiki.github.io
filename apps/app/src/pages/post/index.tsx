import { useEffect, useMemo, useRef, useState } from 'react'

import { Button, Text, Textarea, View } from 'virtual:taro/components'
import Taro, { useDidShow, useRouter } from 'virtual:taro/api'
import { DISCUSSION } from '@robowiki/content'
import type { PostComment, PostSummary, User } from '@robowiki/core'

import { EmptyState, ErrorState } from '@/components/Feedback'
import { api, errorMessage, loadMe } from '@/services/api'
import { authorName, formatTime } from '@/utils/format'
import { showToast } from '@/utils/nav'
import { useThemeMode } from '@/utils/theme'
import './index.css'

const KIND_LABEL: Record<string, string> = {
  discussion: '讨论',
  review: '评价',
  build: '方案',
}

type FlatComment = { comment: PostComment; depth: number }

function flattenComments(list: PostComment[]): FlatComment[] {
  const out: FlatComment[] = []
  const seen = new Set<number>()
  const walk = (rows: PostComment[], depth: number) => {
    rows.forEach((comment) => {
      if (!comment || seen.has(comment.id)) return
      seen.add(comment.id)
      out.push({ comment, depth: Math.min(depth, 2) })
      if (comment.replies?.length) walk(comment.replies, depth + 1)
    })
  }
  walk(list, 0)
  return out
}

type CommentViewProps = {
  item: FlatComment
  acceptedId?: number | null
  canManage: boolean
  acceptingId: number
  onAccept: (comment: PostComment) => void
}

function PostCommentView({ item, acceptedId, canManage, acceptingId, onAccept }: CommentViewProps) {
  const { comment, depth } = item
  const accepted = Boolean(comment.accepted) || acceptedId === comment.id
  return (
    <View
      className={`post-comment ${accepted ? 'post-comment--accepted' : ''}`}
      style={depth > 0 && !accepted ? { marginLeft: `${depth * 16}px` } : undefined}
    >
      <View className="post-comment__head">
        <Text className="post-comment__author">{authorName(comment.author)}</Text>
        {comment.author?.is_staff ? <Text className="rw-badge">站务</Text> : null}
        {accepted ? <Text className="rw-badge rw-badge--success">已采纳</Text> : null}
        <Text className="rw-caption post-comment__time">{formatTime(comment.created_at)}</Text>
      </View>
      <Text className="post-comment__body" selectable>
        {comment.body}
      </Text>
      <View className="post-comment__foot">
        <Text className="post-comment__score">分 {comment.score}</Text>
        {canManage ? (
          <Text
            className={`rw-link rw-link--tap ${accepted ? 'rw-link--danger' : ''}`}
            onClick={() => onAccept(comment)}
          >
            {acceptingId === comment.id ? '处理中…' : accepted ? '取消采纳' : '采纳'}
          </Text>
        ) : null}
      </View>
    </View>
  )
}

export default function PostPage() {
  const router = useRouter()
  const theme = useThemeMode()
  const idText = decodeURIComponent(router.params?.id || '')
  const postId = Number(idText)

  const [post, setPost] = useState<PostSummary | null>(null)
  const [user, setUser] = useState<User | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [reloadKey, setReloadKey] = useState(0)

  const [comments, setComments] = useState<PostComment[]>([])
  const [commentsLoading, setCommentsLoading] = useState(false)
  const [commentsError, setCommentsError] = useState('')
  const [commentsKey, setCommentsKey] = useState(0)

  const [commentText, setCommentText] = useState('')
  const [commentBusy, setCommentBusy] = useState(false)
  const [acceptingId, setAcceptingId] = useState(0)
  const [deleting, setDeleting] = useState(false)

  const firstShowRef = useRef(true)
  const validId = Number.isFinite(postId) && postId > 0

  useDidShow(() => {
    loadMe().then(setUser)
    // 从编辑页返回时重新拉帖子与评论；首次展示交给下面的 effect。
    if (firstShowRef.current) {
      firstShowRef.current = false
      return
    }
    setReloadKey((key) => key + 1)
    setCommentsKey((key) => key + 1)
  })

  useEffect(() => {
    if (!validId) {
      setLoading(false)
      setError('缺少帖子 id')
      return
    }
    let alive = true
    setLoading(true)
    setError('')
    api
      .getPost(postId)
      .then((data) => {
        if (alive) setPost(data)
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
  }, [validId, postId, reloadKey])

  useEffect(() => {
    if (!validId) return
    let alive = true
    setCommentsLoading(true)
    setCommentsError('')
    api
      .listPostComments(postId)
      .then((data) => {
        if (alive) setComments(data || [])
      })
      .catch((err) => {
        if (alive) setCommentsError(errorMessage(err))
      })
      .finally(() => {
        if (alive) setCommentsLoading(false)
      })
    return () => {
      alive = false
    }
  }, [validId, postId, commentsKey])

  const flatComments = useMemo(() => {
    const rows = flattenComments(comments)
    const acceptedId = post?.accepted_comment_id
    // 已采纳的评论置顶，其余保持原顺序（sort 稳定）。
    return rows.sort(
      (a, b) =>
        Number(Boolean(b.comment.accepted) || b.comment.id === acceptedId) -
        Number(Boolean(a.comment.accepted) || a.comment.id === acceptedId),
    )
  }, [comments, post?.accepted_comment_id])

  const canManage = Boolean(
    user &&
      post &&
      (user.is_staff ||
        post.author?.id === user.id ||
        Boolean(post.author?.handle && post.author.handle === user.handle)),
  )

  const openLogin = () => {
    Taro.navigateTo({ url: '/pages/login/index' })
  }

  const requireLogin = (): boolean => {
    if (user) return true
    Taro.showModal({
      title: '需要登录',
      content: '登录后可以投票和发表评论。',
      confirmText: '去登录',
    }).then((res) => {
      if (res.confirm) openLogin()
    })
    return false
  }

  const vote = async (value: 1 | -1) => {
    if (!post || !requireLogin()) return
    const next: -1 | 0 | 1 = post.my_vote === value ? 0 : value
    try {
      const res = await api.vote('post', post.id, next)
      setPost((prev) => (prev ? { ...prev, score: res.score, my_vote: res.my_vote } : prev))
    } catch (err) {
      showToast(errorMessage(err))
    }
  }

  const submitComment = async () => {
    if (!post || !requireLogin()) return
    const body = commentText.trim()
    if (!body) {
      showToast('写点什么再发表')
      return
    }
    setCommentBusy(true)
    try {
      await api.addPostComment(post.id, body)
      setCommentText('')
      setCommentsKey((key) => key + 1)
      setPost((prev) => (prev ? { ...prev, comment_count: prev.comment_count + 1 } : prev))
      showToast('评论已发表')
    } catch (err) {
      showToast(errorMessage(err))
    } finally {
      setCommentBusy(false)
    }
  }

  const editPost = () => {
    if (!post) return
    Taro.navigateTo({ url: `/pages/compose/index?id=${encodeURIComponent(String(post.id))}` })
  }

  const removePost = () => {
    if (!post || !canManage || deleting) return
    Taro.showModal({
      title: '删除帖子',
      content: '删除后无法恢复，评论也会一起移除。确认删除？',
      confirmText: '删除',
      confirmColor: '#b91c1c',
    }).then(async (res) => {
      if (!res.confirm) return
      setDeleting(true)
      try {
        await api.deletePost(post.id)
        showToast('帖子已删除')
        const pages = Taro.getCurrentPages()
        if (pages.length > 1) Taro.navigateBack()
        else Taro.reLaunch({ url: '/pages/community/index' })
      } catch (err) {
        showToast(errorMessage(err))
        setDeleting(false)
      }
    })
  }

  const toggleAccept = (comment: PostComment) => {
    if (!post || !canManage || acceptingId) return
    const accepted = Boolean(comment.accepted) || post.accepted_comment_id === comment.id
    Taro.showModal({
      title: accepted ? '取消采纳' : '采纳回答',
      content: accepted
        ? '取消后帖子会回到待解决，评论恢复普通排序。'
        : '采纳后这条评论会置顶，帖子标记为已解决。',
      confirmText: accepted ? '取消采纳' : '采纳',
    }).then(async (res) => {
      if (!res.confirm) return
      setAcceptingId(comment.id)
      try {
        if (accepted) {
          await api.unacceptComment(post.id)
          setPost((prev) => (prev ? { ...prev, accepted_comment_id: null } : prev))
          showToast('已取消采纳')
        } else {
          const next = await api.acceptComment(post.id, comment.id)
          setPost((prev) => (prev ? { ...prev, ...next } : next))
          showToast('已采纳')
        }
        setCommentsKey((key) => key + 1)
      } catch (err) {
        showToast(errorMessage(err))
      } finally {
        setAcceptingId(0)
      }
    })
  }

  if (loading) {
    return (
      <View className={`rw-page post ${theme === 'dark' ? 'dark' : ''}`}>
        <View className="rw-stack">
          <View className="rw-skeleton" style={{ height: '32px' }} />
          <View className="rw-skeleton" style={{ height: '140px' }} />
          <View className="rw-skeleton" style={{ height: '120px' }} />
        </View>
      </View>
    )
  }

  if (error || !post) {
    return (
      <View className={`rw-page post ${theme === 'dark' ? 'dark' : ''}`}>
        <ErrorState
          message={error || '帖子不存在'}
          onRetry={() => setReloadKey((key) => key + 1)}
        />
      </View>
    )
  }

  const edited = Boolean(post.updated_at && post.updated_at !== post.created_at)

  return (
    <View className={`rw-page post ${theme === 'dark' ? 'dark' : ''}`}>
      <View className="post__head">
        <View className="post__badges">
          <Text className="rw-badge">{KIND_LABEL[post.kind] || post.kind}</Text>
          {post.pinned ? <Text className="rw-badge rw-badge--warn">置顶</Text> : null}
          {post.accepted_comment_id ? <Text className="rw-badge rw-badge--success">已解决</Text> : null}
          {post.rating ? <Text className="post__rating">★ {post.rating}</Text> : null}
          <Text className="rw-caption post__time">
            {formatTime(post.created_at)}
            {edited ? ' · 已编辑' : ''}
          </Text>
        </View>

        <Text className="rw-title post__title">{post.title}</Text>

        <View className="post__meta">
          <Text className="post__author">{authorName(post.author)}</Text>
          {post.author?.is_staff ? <Text className="rw-badge">站务</Text> : null}
          <Text className="rw-caption">浏览 {post.view_count}</Text>
        </View>

        {canManage ? (
          <View className="post__manage">
            <Text className="rw-link rw-link--tap" onClick={editPost}>
              编辑
            </Text>
            <Text className="rw-link rw-link--tap rw-link--danger" onClick={removePost}>
              {deleting ? '删除中…' : '删除'}
            </Text>
          </View>
        ) : null}

        {post.tags?.length ? (
          <View className="post__tags">
            {post.tags.map((tag) => (
              <Text className="rw-chip" key={tag}>
                {tag}
              </Text>
            ))}
          </View>
        ) : null}
      </View>

      {post.part_id ? (
        <View
          className="post__part"
          onClick={() =>
            Taro.navigateTo({ url: `/pages/part/index?id=${encodeURIComponent(String(post.part_id))}` })
          }
        >
          <View className="rw-grow">
            <Text className="rw-caption">关联部件</Text>
            <Text className="post__part-title rw-line-clamp-1">
              {post.part_title || post.part_id}
            </Text>
          </View>
          <Text className="rw-link">查看 ›</Text>
        </View>
      ) : null}

      <Text className="post__body" selectable>
        {post.body}
      </Text>

      <View className="post__votes">
        <View
          className={`post__vote ${post.my_vote === 1 ? 'post__vote--on' : ''}`}
          onClick={() => vote(1)}
        >
          <Text className="post__vote-icon">▲</Text>
          <Text>赞同 {post.score}</Text>
        </View>
        <View
          className={`post__vote ${post.my_vote === -1 ? 'post__vote--down' : ''}`}
          onClick={() => vote(-1)}
        >
          <Text className="post__vote-icon">▼</Text>
          <Text>反对</Text>
        </View>
      </View>

      <View className="post__section">
        <View className="rw-row rw-row--between post__section-head">
          <Text className="rw-subtitle">
            {DISCUSSION.title}
            {post.comment_count ? `（${post.comment_count}）` : ''}
          </Text>
          <Text className="rw-caption rw-link--tap" onClick={() => setCommentsKey((key) => key + 1)}>
            刷新
          </Text>
        </View>

        {user ? (
          <View className="post__composer">
            <View className="rw-field rw-field--textarea">
              <Textarea
                className="rw-textarea"
                value={commentText}
                maxlength={4000}
                placeholder="写下你的实测、纠错或补充…"
                onInput={(event) => setCommentText(event.detail.value)}
              />
            </View>
            <View className="rw-row rw-row--between">
              <Text className="rw-caption">只写用过的、量过的</Text>
              <Button
                className="rw-btn rw-btn--primary"
                disabled={commentBusy}
                onClick={submitComment}
              >
                {commentBusy ? '发送中…' : '发表评论'}
              </Button>
            </View>
          </View>
        ) : (
          <View className="post__login-hint">
            <Text className="rw-caption">{DISCUSSION.loginHint}</Text>
            <Text className="rw-link rw-link--tap" onClick={openLogin}>
              去登录
            </Text>
          </View>
        )}

        {commentsLoading ? (
          <Text className="rw-caption">正在加载评论…</Text>
        ) : commentsError ? (
          <ErrorState message={commentsError} onRetry={() => setCommentsKey((key) => key + 1)} />
        ) : flatComments.length === 0 ? (
          <EmptyState title="还没有讨论" hint={DISCUSSION.empty} />
        ) : (
          <View className="post__comments">
            {flatComments.map((item) => (
              <PostCommentView
                key={item.comment.id}
                item={item}
                acceptedId={post.accepted_comment_id}
                canManage={canManage}
                acceptingId={acceptingId}
                onAccept={toggleAccept}
              />
            ))}
          </View>
        )}
      </View>

      <View className="rw-safe-bottom" />
    </View>
  )
}
