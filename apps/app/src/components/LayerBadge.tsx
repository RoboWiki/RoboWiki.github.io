import { Text, View } from 'virtual:taro/components'
import { layerOfCategory, type Layer } from '@robowiki/content'

type LayerDotProps = {
  layer: Layer
  className?: string
}

/** 能力层小圆点：只用作识别，不铺大面积底色。 */
export function LayerDot({ layer, className = '' }: LayerDotProps) {
  return <View className={`rw-layer-dot rw-layer-dot--${layer.id} ${className}`} />
}

type LayerBadgeProps = {
  category?: string
  layer?: Layer
  className?: string
}

/** 部件层徽标：品类不在四层映射里时静默不渲染。 */
export function LayerBadge({ category, layer, className = '' }: LayerBadgeProps) {
  const target = layer || (category ? layerOfCategory(category) : undefined)
  if (!target) return null

  return (
    <View className={`rw-layer-badge rw-layer-badge--${target.id} ${className}`}>
      <View className="rw-layer-badge__dot" />
      <Text className="rw-layer-badge__text">{target.name}</Text>
    </View>
  )
}
