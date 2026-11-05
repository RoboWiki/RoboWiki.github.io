import { Button, Text, View } from '@tarojs/components'

type SkeletonRowsProps = {
  rows?: number
}

/** 列表骨架：与真实行同样的高度节奏，避免加载完成时跳版。 */
export function SkeletonRows({ rows = 5 }: SkeletonRowsProps) {
  return (
    <View className="rw-list">
      {Array.from({ length: rows }).map((_, index) => (
        <View className="rw-list__row" key={index}>
          <View className="rw-skeleton rw-thumb" />
          <View className="rw-grow rw-stack" style={{ gap: '8px' }}>
            <View className="rw-skeleton rw-skeleton--line" style={{ width: '62%' }} />
            <View className="rw-skeleton rw-skeleton--line" style={{ width: '88%' }} />
            <View className="rw-skeleton rw-skeleton--line" style={{ width: '40%' }} />
          </View>
        </View>
      ))}
    </View>
  )
}

type EmptyStateProps = {
  title: string
  hint?: string
  actionLabel?: string
  onAction?: () => void
}

export function EmptyState({ title, hint, actionLabel, onAction }: EmptyStateProps) {
  return (
    <View className="rw-state">
      <Text className="rw-state__title">{title}</Text>
      {hint ? <Text className="rw-caption">{hint}</Text> : null}
      {actionLabel && onAction ? (
        <Button className="rw-btn" onClick={onAction}>
          {actionLabel}
        </Button>
      ) : null}
    </View>
  )
}

type ErrorStateProps = {
  message: string
  onRetry?: () => void
}

export function ErrorState({ message, onRetry }: ErrorStateProps) {
  return (
    <View className="rw-state">
      <Text className="rw-state__title">加载失败</Text>
      <Text className="rw-caption">{message}</Text>
      {onRetry ? (
        <Button className="rw-btn" onClick={onRetry}>
          重试
        </Button>
      ) : null}
    </View>
  )
}
