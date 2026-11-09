import { Image, Text, View } from 'virtual:taro/components'
import Taro from 'virtual:taro/api'
import type { Comment } from '@robowiki/core'

import { authorName, formatTime, parseCommentContent } from '@/utils/format'

type CommentItemProps = {
  comment: Comment
  depth?: number
  mineHandle?: string
  isStaff?: boolean
  onDelete: (comment: Comment) => void
  onReport: (comment: Comment) => void
}

export function CommentItem({
  comment,
  depth = 0,
  mineHandle,
  isStaff,
  onDelete,
  onReport,
}: CommentItemProps) {
  const content = parseCommentContent(comment.body)
  const author = comment.author
  const own = Boolean(mineHandle && author?.handle === mineHandle)
  const canDelete = own || Boolean(isStaff)
  const pending = comment.status === 'pending'

  const preview = (current: string) => {
    Taro.previewImage({ urls: content.images, current })
  }

  return (
    <View
      className="comment"
      style={depth > 0 ? { marginLeft: `${Math.min(depth, 2) * 16}px` } : undefined}
    >
      <View className="comment__head">
        <Text className="comment__author">{authorName(author)}</Text>
        {author?.is_staff ? <Text className="rw-badge">站务</Text> : null}
        {pending ? <Text className="rw-badge rw-badge--warn">待审核</Text> : null}
        <Text className="rw-caption comment__time">{formatTime(comment.created_at)}</Text>
      </View>

      {comment.deleted ? (
        <Text className="rw-muted">该讨论已删除</Text>
      ) : (
        <View className="comment__content">
          {content.text ? (
            <Text className="comment__body" selectable>
              {content.text}
            </Text>
          ) : null}
          {content.images.length ? (
            <View className="comment__images">
              {content.images.map((url) => (
                <Image
                  key={url}
                  className="comment__image"
                  src={url}
                  mode="widthFix"
                  lazyLoad
                  onClick={() => preview(url)}
                />
              ))}
            </View>
          ) : null}
        </View>
      )}

      {!comment.deleted ? (
        <View className="comment__actions">
          {canDelete ? (
            <Text className="comment__action comment__action--danger" onClick={() => onDelete(comment)}>
              删除
            </Text>
          ) : null}
          <Text className="comment__action" onClick={() => onReport(comment)}>
            举报
          </Text>
        </View>
      ) : null}
    </View>
  )
}
