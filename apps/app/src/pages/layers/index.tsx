import { Text, View } from 'virtual:taro/components'
import {
  BRAIN_LAYER,
  POSITIONING,
  SKELETON_LAYERS,
  type Layer,
} from '@robowiki/content'

import { LayerDot } from '@/components/LayerBadge'
import { openCatalogLayer } from '@/utils/nav'
import { useThemeMode } from '@/utils/theme'
import './index.css'

const BRAIN_STEPS = ['需求', '接口', '预算', '联调']

function layerClass(prefix: string, layer: Layer): string {
  return `${prefix} ${prefix}--${layer.id}`
}

export default function LayersPage() {
  const theme = useThemeMode()
  const brain = BRAIN_LAYER

  return (
    <View className={`rw-page layers ${theme === 'dark' ? 'dark' : ''}`}>
      <View className="layers__hero">
        <Text className="layers__eyebrow">能力地图</Text>
        <Text className="rw-title layers__title">{POSITIONING.short}</Text>
        <Text className="layers__tagline">{POSITIONING.tagline}</Text>
        <Text className="rw-caption layers__lede">能力分层：机械 / 硬件 / 嵌入式 / 算法 + 集成。核心是部件库，选型台为试验版。</Text>
      </View>

      <View className="layers__section">
        <View className="rw-row rw-row--between layers__section-head">
          <Text className="rw-subtitle">四层能力骨架</Text>
          <Text className="rw-caption">点一层，查看对应部件</Text>
        </View>

        <View className="layers__cards">
          {SKELETON_LAYERS.map((layer) => (
            <View
              className={layerClass('layers__card', layer)}
              key={layer.id}
              onClick={() => openCatalogLayer(layer.id)}
            >
              <View className="layers__card-head">
                <View className={layerClass('layers__index', layer)}>
                  <Text className="layers__index-text">{layer.index}</Text>
                </View>
                <View className="rw-grow">
                  <View className="layers__name-row">
                    <LayerDot layer={layer} />
                    <Text className="layers__name">{layer.name}</Text>
                    <Text className="layers__en">{layer.en}</Text>
                  </View>
                  <Text className="layers__tagline">{layer.tagline}</Text>
                </View>
                <Text className={layerClass('layers__arrow', layer)}>›</Text>
              </View>

              <Text className="layers__desc">{layer.desc}</Text>

              <View className="layers__card-foot">
                <Text className="rw-caption layers__hint">{layer.hint}</Text>
                <Text className={layerClass('layers__go', layer)}>查看该层部件 ›</Text>
              </View>
            </View>
          ))}
        </View>
      </View>

      {brain ? (
        <View className="layers__brain">
          <View className="layers__brain-head">
            <View className="layers__brain-mark">
              <Text className="layers__brain-star">{brain.index}</Text>
            </View>
            <View className="rw-grow">
              <Text className="layers__brain-kicker">横贯四层 · 大脑</Text>
              <Text className="layers__brain-name">{brain.name}</Text>
            </View>
            <Text className="layers__brain-badge">系统集成</Text>
          </View>

          <Text className="layers__brain-desc">{brain.desc}</Text>

          <View className="layers__steps">
            {BRAIN_STEPS.map((step) => (
              <Text className="layers__step" key={step}>
                {step}
              </Text>
            ))}
          </View>

          <Text className="rw-caption layers__brain-hint">
            横贯四层：需求 / 接口 / 预算 / 联调 · {brain.hint}
          </Text>
        </View>
      ) : null}

      <Text className="rw-caption layers__note">
        系统集成不是第五层：它把四层选择装进同一台机器，负责接口、预算与联调收口。
      </Text>

      <View className="rw-safe-bottom" />
    </View>
  )
}
