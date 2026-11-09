import { useEffect, useMemo, useState } from 'react'

import { Button, Image, Input, Text, Textarea, View } from 'virtual:taro/components'
import Taro, { useDidShow, useRouter } from 'virtual:taro/api'
import type { Comment, RatingSummary, User } from '@robowiki/core'

import { CommentItem } from '@/components/CommentItem'
import { EmptyState, ErrorState } from '@/components/Feedback'
import { LayerBadge } from '@/components/LayerBadge'
import { RatingStars } from '@/components/RatingStars'
import {
  absoluteUrl,
  api,
  errorMessage,
  loadMe,
  reportComment,
  uploadImage,
} from '@/services/api'
import {
  partCategoryLabel,
  partFacts,
  partImage,
  partPageKey,
  partPrice,
  type PartView,
} from '@/services/parts'
import { formatTime } from '@/utils/format'
import { touchRecent } from '@/utils/recent'
import { useThemeMode } from '@/utils/theme'
import './index.css'

const REPORT_REASONS = [
  { label: '垃圾广告', value: 'spam' as const },
  { label: '辱骂或攻击', value: 'abuse' as const },
  { label: '信息不实', value: 'misinfo' as const },
  { label: '其他', value: 'other' as const },
]

function toast(title: string) {
  Taro.showToast({ title, icon: 'none', duration: 2200 })
}

export default function PartPage() {
  const router = useRouter()
  const theme = useThemeMode()
  const darkClass = theme === 'dark' ? 'dark' : ''
  const id = decodeURIComponent(router.params?.id || '')

  const [part, setPart] = useState<PartView | null>(null)
  const [user, setUser] = useState<User | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  const [rating, setRating] = useState<RatingSummary | null>(null)
  const [ratingError, setRatingError] = useState('')
  const [score, setScore] = useState(0)
  const [ownHardware, setOwnHardware] = useState(false)
  const [ratingBusy, setRatingBusy] = useState(false)
  const [ratingKey, setRatingKey] = useState(0)

  const [comments, setComments] = useState<Comment[]>([])
  const [commentsLoading, setCommentsLoading] = useState(false)
  const [commentsError, setCommentsError] = useState('')
  const [commentsKey, setCommentsKey] = useState(0)
  const [commentText, setCommentText] = useState('')
  const [imageUrl, setImageUrl] = useState('')
  const [uploading, setUploading] = useState(false)
  const [commentBusy, setCommentBusy] = useState(false)

  const pageKey = partPageKey(part)

  useDidShow(() => {
    loadMe().then(setUser)
  })

  useEffect(() => {
    if (!id) {
      setLoading(false)
      setError('缺少部件 id')
      return
    }
    let alive = true
    setLoading(true)
    setError('')
    api
      .getPart(id)
      .then((data) => {
        if (alive) {
          setPart(data as PartView)
          touchRecent(String(data.id || id))
        }
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
  }, [id])

  // 评分单独加载：评分接口失败不该让整个详情页变成错误态。
  useEffect(() => {
    if (!id) return
    let alive = true
    setRatingError('')
    api
      .getRating(id)
      .then((data) => {
        if (!alive) return
        setRating(data)
        setScore(data.mine?.score || 0)
        setOwnHardware(Boolean(data.mine?.own_hardware))
      })
      .catch((err) => {
        if (alive) setRatingError(errorMessage(err))
      })
    return () => {
      alive = false
    }
  }, [id, ratingKey])

  // 评论 page 键依赖详情里的 web_path，拿到部件后才请求。
  useEffect(() => {
    if (!pageKey) return
    let alive = true
    setCommentsLoading(true)
    setCommentsError('')
    api
      .listComments(pageKey)
      .then((data) => {
        if (alive) setComments(data.comments || [])
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
  }, [pageKey, commentsKey])

  const depths = useMemo(() => {
    const map = new Map<number, number>()
    comments.forEach((comment) => {
      const parentDepth = comment.parent_id ? map.get(comment.parent_id) ?? 0 : -1
      map.set(comment.id, Math.min(parentDepth + 1, 2))
    })
    return map
  }, [comments])

  const openLogin = () => {
    Taro.navigateTo({ url: '/pages/login/index' })
  }

  const requireLogin = (): boolean => {
    if (user) return true
    Taro.showModal({
      title: '需要登录',
      content: '登录后可以评分、发表评论和举报。',
      confirmText: '去登录',
    }).then((res) => {
      if (res.confirm) openLogin()
    })
    return false
  }

  const submitRating = async () => {
    if (!requireLogin()) return
    if (!score) {
      toast('先选择 1–5 星')
      return
    }
    setRatingBusy(true)
    try {
      const data = await api.putRating(id, { score, own_hardware: ownHardware })
      setRating(data)
      setScore(data.mine?.score || score)
      toast(data.created ? '评分已提交' : '评分已更新')
    } catch (err) {
      toast(errorMessage(err))
    } finally {
      setRatingBusy(false)
    }
  }

  const revokeRating = async () => {
    if (!requireLogin()) return
    setRatingBusy(true)
    try {
      await api.deleteRating(id)
      setScore(0)
      setOwnHardware(false)
      setRatingKey((key) => key + 1)
      toast('已撤销评分')
    } catch (err) {
      toast(errorMessage(err))
    } finally {
      setRatingBusy(false)
    }
  }

  const copyPartLink = (url: string) => {
    Taro.setClipboardData({ data: url })
      .then(() => Taro.showToast({ title: '链接已复制', icon: 'success' }))
      .catch(() => Taro.showToast({ title: '复制失败', icon: 'none' }))
  }

  const openFix = () => {
    if (!part) return
    Taro.navigateTo({ url: `/pages/submit/index?id=${encodeURIComponent(String(part.id))}` })
  }

  /** 评论配图：先传 /media 拿 URL，再把 URL 写进评论正文。 */
  const pickImage = async () => {
    if (uploading || commentBusy) return
    try {
      const res = await Taro.chooseImage({
        count: 1,
        sizeType: ['compressed'],
        sourceType: ['album', 'camera'],
      })
      const path = res.tempFilePaths?.[0]
      if (!path) return
      setUploading(true)
      const media = await uploadImage(path)
      setImageUrl(absoluteUrl(media.url))
      toast('图片已上传')
    } catch (err) {
      const msg = err instanceof Error ? err.message : String((err as { errMsg?: string })?.errMsg || '')
      if (!/cancel/i.test(msg)) toast(msg || '上传失败，请重试')
    } finally {
      setUploading(false)
    }
  }

  const submitComment = async () => {    if (!requireLogin()) return
    const text = commentText.trim()
    const image = imageUrl.trim()
    if (!text && !image) {
      toast('写点什么再发表')
      return
    }
    if (image && !/^https?:\/\//i.test(image)) {
      toast('图片链接需以 http(s) 开头')
      return
    }
    const body = [text, image].filter(Boolean).join('\n')
    setCommentBusy(true)
    try {
      await api.addComment(pageKey, body)
      setCommentText('')
      setImageUrl('')
      setCommentsKey((key) => key + 1)
      toast('评论已发表')
    } catch (err) {
      toast(errorMessage(err))
    } finally {
      setCommentBusy(false)
    }
  }

  const deleteComment = (comment: Comment) => {
    if (!requireLogin()) return
    Taro.showModal({
      title: '删除评论',
      content: '删除后这条评论会变成占位，确认继续？',
      confirmText: '删除',
      confirmColor: '#b91c1c',
    }).then(async (res) => {
      if (!res.confirm) return
      try {
        await api.deleteComment(comment.id)
        setCommentsKey((key) => key + 1)
        toast('已删除')
      } catch (err) {
        toast(errorMessage(err))
      }
    })
  }

  const report = (comment: Comment) => {
    if (!requireLogin()) return
    Taro.showActionSheet({ itemList: REPORT_REASONS.map((item) => item.label) })
      .then(async (res) => {
        const reason = REPORT_REASONS[res.tapIndex]?.value
        if (!reason) return
        try {
          await reportComment(comment.id, reason)
          toast('举报已提交，等待站务处理')
        } catch (err) {
          toast(errorMessage(err))
        }
      })
      .catch(() => {
        // 用户取消选择，不需要提示。
      })
  }

  if (loading) {
    return (
      <View className={`rw-page part ${darkClass}`}>
        <View className="rw-stack">
          <View className="rw-skeleton" style={{ height: '80px' }} />
          <View className="rw-skeleton" style={{ height: '120px' }} />
          <View className="rw-skeleton" style={{ height: '160px' }} />
        </View>
      </View>
    )
  }

  if (error || !part) {
    return (
      <View className={`rw-page ${darkClass}`}>
        <ErrorState message={error || '部件不存在'} onRetry={() => Taro.navigateBack()} />
      </View>
    )
  }

  const specRecord = ((part as unknown as { specs?: Record<string, unknown> } | null)?.specs) || {}
  const PART_LINK_KEYS = new Set(['doc_url', 'doc_pdf', 'repo_urls', 'urdf_urls', 'repo_license'])
  const facts = partFacts(part).filter((fact) => !PART_LINK_KEYS.has(fact.key))
  const partLinks: Array<{ kind: string; url: string }> = []
  const pushLink = (kind: string, raw: unknown) => {
    const url = String(raw ?? '').trim()
    if (!/^https?:\/\//i.test(url)) return
    if (partLinks.some((link) => link.url === url)) return
    partLinks.push({ kind, url })
  }
  pushLink('资料页', specRecord.doc_url)
  pushLink('数据表', specRecord.doc_pdf)
  for (const url of (specRecord.repo_urls as string[] | undefined) || []) pushLink('仓库', url)
  for (const url of (specRecord.urdf_urls as string[] | undefined) || []) pushLink('URDF', url)
  const image = partImage(part)
  const offers = (part.offers || []).filter(o => o && !o.demo)
  const copyOffer = (url?: string | null) => {
    if (!url || !/^https?:\/\//i.test(url)) return
    Taro.setClipboardData({ data: url }).then(() =>
      Taro.showToast({ title: '活动链接已复制', icon: 'none' }),
    )
  }
  const avg = rating?.avg
  const count = rating?.count || 0
  const histogram = rating?.histogram || {}

  return (
    <View className={`rw-page part ${darkClass}`}>
      <View className="part__head">
        {image ? (
          <Image
            className="part__hero"
            src={image}
            mode="aspectFit"
            onClick={() => Taro.previewImage({ urls: [image], current: image })}
          />
        ) : (
          <View className="part__hero part__hero--empty">
            {String(part.model || '?').slice(0, 2)}
          </View>
        )}
        <View className="rw-grow rw-stack" style={{ gap: '4px' }}>
          <Text className="rw-title part__title">
            {part.vendor} {part.model}
          </Text>
          <View className="part__meta">
            <LayerBadge category={part.category} />
            <Text className="rw-caption">
              {partCategoryLabel(part)}
            </Text>
          </View>
          <Text className="part__price">{partPrice(part)}</Text>
        </View>
      </View>

      {part.notes ? <Text className="part__notes">{part.notes}</Text> : null}

      {offers.length ? (
        <View className="part__section">
          <View className="rw-row rw-row--between part__section-head">
            <Text className="rw-subtitle">渠道优惠 / 活动价</Text>
            <Text className="rw-caption">{offers.length} 条</Text>
          </View>
          <View className="rw-list">
            {offers.map((offer) => (
              <View className="rw-list__row" key={String(offer.id ?? offer.title)}>
                <View className="rw-grow">
                  <Text className="rw-strong">{offer.title || '渠道活动'}</Text>
                  {offer.detail ? <Text className="rw-caption part__offer-detail">{offer.detail}</Text> : null}
                  <Text className="rw-caption">
                    {offer.vendor ? `${offer.vendor} · ` : ''}
                    {offer.expires_on ? `有效期至 ${offer.expires_on}` : '有效期未标注'}
                  </Text>
                </View>
                {offer.url && /^https?:\/\//i.test(offer.url) ? (
                  <Text className="rw-link" onClick={() => copyOffer(offer.url)}>复制链接</Text>
                ) : null}
              </View>
            ))}
          </View>
          <Text className="rw-caption part__offer-note">优惠以下单页面为准；本站不卖货、不收佣金。</Text>
        </View>
      ) : null}

      <View className="rw-row rw-row--between part__fix">
        <Text className="rw-caption">参数或价格不对？提交纠错，站务审核后更新目录。</Text>
        <Text className="rw-link" onClick={openFix}>纠错</Text>
      </View>

      {partLinks.length > 0 ? (
        <View className="part__section">
          <View className="rw-row rw-row--between part__section-head">
            <Text className="rw-subtitle">资料与仓库</Text>
            <Text className="rw-caption">{partLinks.length} 个 · 点击复制</Text>
          </View>
          <View className="part__link-list">
            {partLinks.map((link) => (
              <View className="part__link" key={link.url} onClick={() => copyPartLink(link.url)}>
                <Text className="part__link-kind">{link.kind}</Text>
                <Text className="part__link-url">{link.url.replace(/^https?:\/\/(www\.)?/, '')}</Text>
              </View>
            ))}
          </View>
        </View>
      ) : null}

      <View className="part__section">
        <View className="rw-row rw-row--between part__section-head">
          <Text className="rw-subtitle">关键参数</Text>
          <Text className="rw-caption">{facts.length ? `${facts.length} 项` : '暂无结构化参数'}</Text>
        </View>
        {facts.length ? (
          <View className="part__specs">
            {facts.map((fact) => (
              <View className="part__spec" key={fact.key}>
                <Text className="part__spec-label">{fact.label}</Text>
                <Text className="part__spec-value">{fact.value}</Text>
              </View>
            ))}
          </View>
        ) : null}
      </View>

      <View className="part__section">
        <View className="rw-row rw-row--between part__section-head">
          <Text className="rw-subtitle">评分</Text>
          <Text className="rw-caption">
            {count > 0 ? `${avg ?? '-'} 分 · ${count} 人` : '还没有人评分'}
          </Text>
        </View>

        {ratingError ? (
          <View className="rw-row rw-row--between">
            <Text className="rw-error">{ratingError}</Text>
            <Text className="rw-link" onClick={() => setRatingKey((key) => key + 1)}>
              重试
            </Text>
          </View>
        ) : null}

        {count > 0 ? (
          <View className="part__rating-summary">
            <Text className="part__avg">{avg ?? '-'}</Text>
            <View className="rw-stack" style={{ gap: '6px' }}>
              <RatingStars value={Math.round(avg || 0)} size="sm" disabled />
              <Text className="rw-caption">{count} 人评分</Text>
            </View>
          </View>
        ) : null}

        {count > 0 ? (
          <View className="part__histogram">
            {[5, 4, 3, 2, 1].map((star) => {
              const n = Number(histogram[String(star)] || 0)
              const width = count ? Math.round((n / count) * 100) : 0
              return (
                <View className="part__histogram-row" key={star}>
                  <Text className="part__histogram-label">{star} 星</Text>
                  <View className="part__histogram-track">
                    <View className="part__histogram-fill" style={{ width: `${width}%` }} />
                  </View>
                  <Text className="part__histogram-count">{n}</Text>
                </View>
              )
            })}
          </View>
        ) : null}

        <View className="part__rate-box">
          <View className="rw-row rw-row--between">
            <RatingStars value={score} onChange={setScore} />
            <View
              className={`rw-chip ${ownHardware ? 'rw-chip--active' : ''}`}
              onClick={() => setOwnHardware((value) => !value)}
            >
              我实际用过
            </View>
          </View>
          {rating?.mine ? (
            <Text className="rw-caption">
              你的评分：{rating.mine.score} 星 · {formatTime(rating.mine.updated_at)}
              {rating.mine.hidden ? ' · 评价帖审核中' : ''}
            </Text>
          ) : user ? (
            <Text className="rw-caption">点星选择 1–5 分，可随时修改或撤销。</Text>
          ) : (
            <View className="rw-row rw-row--between">
              <Text className="rw-caption">登录后可以评分</Text>
              <Text className="rw-link" onClick={openLogin}>
                去登录
              </Text>
            </View>
          )}
          <View className="rw-row" style={{ gap: '12px' }}>
            <Button
              className="rw-btn rw-btn--primary"
              disabled={ratingBusy}
              onClick={submitRating}
            >
              {rating?.mine ? '更新评分' : '提交评分'}
            </Button>
            {rating?.mine ? (
              <Button className="rw-btn rw-btn--danger" disabled={ratingBusy} onClick={revokeRating}>
                撤销
              </Button>
            ) : null}
          </View>
        </View>
      </View>

      <View className="part__section">
        <View className="rw-row rw-row--between part__section-head">
          <Text className="rw-subtitle">讨论{comments.length ? `（${comments.length}）` : ''}</Text>
          <Text className="rw-caption" onClick={() => setCommentsKey((key) => key + 1)}>
            刷新
          </Text>
        </View>

        {user ? (
          <View className="part__composer">
            <View className="rw-field rw-field--textarea">
              <Textarea
                className="rw-textarea"
                value={commentText}
                maxlength={4000}
                placeholder="说说这个件的实测体验…"
                onInput={(event) => setCommentText(event.detail.value)}
              />
            </View>
            <View className="part__upload">
              <View className="rw-row rw-row--between">
                <Text className="rw-caption">配图（可选）</Text>
                {imageUrl ? (
                  <Text className="rw-link" onClick={() => setImageUrl('')}>移除</Text>
                ) : null}
              </View>
              {imageUrl ? (
                <Image
                  className="part__upload-preview"
                  src={imageUrl}
                  mode="aspectFit"
                  onClick={() => Taro.previewImage({ urls: [imageUrl], current: imageUrl })}
                />
              ) : null}
              <View className="rw-row" style={{ gap: '12px' }}>
                <Button
                  className="rw-btn"
                  disabled={uploading || commentBusy}
                  onClick={pickImage}
                >
                  {uploading ? '上传中…' : imageUrl ? '重新上传' : '上传图片'}
                </Button>
                <Text className="rw-caption">JPEG / PNG / WebP，≤ 5 MB</Text>
              </View>
              <View className="rw-field">
                <Input
                  className="rw-input"
                  value={imageUrl}
                  placeholder="或粘贴图片链接（可选）"
                  onInput={(event) => setImageUrl(event.detail.value)}
                />
              </View>
            </View>
            <View className="rw-row rw-row--between">
              <Text className="rw-caption">正文与图片会一起保存</Text>
              <Button
                className="rw-btn rw-btn--primary"
                disabled={commentBusy}
                onClick={submitComment}
              >
                {commentBusy ? '发送中…' : '发表'}
              </Button>
            </View>
          </View>
        ) : (
          <View className="rw-row rw-row--between part__login-hint">
            <Text className="rw-caption">登录后可以发表评论</Text>
            <Text className="rw-link" onClick={openLogin}>
              去登录
            </Text>
          </View>
        )}

        {commentsLoading ? (
          <Text className="rw-caption">正在加载讨论…</Text>
        ) : commentsError ? (
          <ErrorState message={commentsError} onRetry={() => setCommentsKey((key) => key + 1)} />
        ) : comments.length === 0 ? (
          <EmptyState title="还没有讨论" hint="成为第一个留下实测记录的人" />
        ) : (
          <View className="part__comments">
            {comments.map((comment) => (
              <CommentItem
                key={comment.id}
                comment={comment}
                depth={depths.get(comment.id) || 0}
                mineHandle={user?.handle}
                isStaff={Boolean(user?.is_staff)}
                onDelete={deleteComment}
                onReport={report}
              />
            ))}
          </View>
        )}
      </View>

      <View className="rw-safe-bottom" />
    </View>
  )
}
