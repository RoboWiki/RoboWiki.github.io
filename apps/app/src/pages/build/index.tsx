import { useEffect, useState } from 'react'

import { Button, Image, Text, View } from 'virtual:taro/components'
import Taro, { useRouter } from 'virtual:taro/api'
import type { BuildDetail } from '@robowiki/core'

import { ErrorState } from '@/components/Feedback'
import { api, errorMessage } from '@/services/api'
import {
  buildFacts,
  buildImage,
  buildPrice,
  buildSubtype,
  buildWebUrl,
  rawSpecs,
} from '@/services/builds'
import { openExternal } from '@/utils/nav'
import { useThemeMode } from '@/utils/theme'
import './index.css'

export default function BuildPage() {
  const router = useRouter()
  const theme = useThemeMode()
  const id = decodeURIComponent(router.params?.id || '')
  const [build, setBuild] = useState<BuildDetail | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [reloadKey, setReloadKey] = useState(0)

  useEffect(() => {
    if (!id) {
      setLoading(false)
      setError('缺少方案 id')
      return
    }
    let alive = true
    setLoading(true)
    setError('')
    api
      .getBuild(id)
      .then((data) => {
        if (alive) setBuild(data)
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
  }, [id, reloadKey])

  if (loading) {
    return (
      <View className={`rw-page build ${theme === 'dark' ? 'dark' : ''}`}>
        <View className="rw-stack">
          <View className="rw-skeleton" style={{ height: '180px' }} />
          <View className="rw-skeleton" style={{ height: '120px' }} />
          <View className="rw-skeleton" style={{ height: '160px' }} />
        </View>
      </View>
    )
  }

  if (error || !build) {
    return (
      <View className={`rw-page build ${theme === 'dark' ? 'dark' : ''}`}>
        <ErrorState
          message={error || '方案不存在'}
          onRetry={() => setReloadKey((key) => key + 1)}
        />
      </View>
    )
  }

  const image = buildImage(build)
  const facts = buildFacts(build)
  const specs = rawSpecs(build)
  const webUrl = buildWebUrl(build)
  const subtype = buildSubtype(build)

  return (
    <View className={`rw-page build ${theme === 'dark' ? 'dark' : ''}`}>
      {image ? (
        <Image
          className="build__hero"
          src={image}
          mode="aspectFill"
          onClick={() => Taro.previewImage({ urls: [image], current: image })}
        />
      ) : (
        <View className="build__hero build__hero--empty">
          {String(build.model || '?').slice(0, 4)}
        </View>
      )}

      <View className="build__head">
        <Text className="rw-title build__title">{build.title || build.model}</Text>
        <Text className="rw-caption">
          {build.vendor}
          {build.vendor_cn ? `（${build.vendor_cn}）` : ''} · {build.model}
        </Text>

        <View className="build__badges">
          {subtype ? <Text className="rw-badge">{subtype}</Text> : null}
          {build.last_checked ? (
            <Text className="rw-caption">核对于 {build.last_checked}</Text>
          ) : null}
        </View>

        <Text className="build__price">{buildPrice(build)}</Text>

        <View className="build__actions">
          {build.url ? (
            <Button
              className="rw-btn"
              onClick={() => openExternal(String(build.url), '方案链接')}
            >
              仓库 / 文档
            </Button>
          ) : null}
          {webUrl ? (
            <Button className="rw-btn rw-btn--primary" onClick={() => openExternal(webUrl, '网页方案')}>
              在网页查看完整方案
            </Button>
          ) : null}
        </View>
      </View>

      {build.notes ? (
        <View className="build__section">
          <Text className="rw-subtitle">说明</Text>
          <Text className="build__notes">{build.notes}</Text>
        </View>
      ) : null}

      <View className="build__section">
        <View className="rw-row rw-row--between">
          <Text className="rw-subtitle">关键参数</Text>
          <Text className="rw-caption">{facts.length ? `${facts.length} 项` : '暂无'}</Text>
        </View>
        {facts.length ? (
          <View className="build__specs">
            {facts.map((fact) => (
              <View className="build__spec" key={fact.key}>
                <Text className="build__spec-label">{fact.label}</Text>
                <Text className="build__spec-value">{fact.value}</Text>
              </View>
            ))}
          </View>
        ) : (
          <Text className="rw-caption">这套方案还没有结构化关键参数。</Text>
        )}
      </View>

      <View className="build__section">
        <View className="rw-row rw-row--between">
          <Text className="rw-subtitle">全部原始参数</Text>
          <Text className="rw-caption">{specs.length ? `${specs.length} 项` : '暂无'}</Text>
        </View>
        {specs.length ? (
          <View className="build__specs">
            {specs.map((spec) => (
              <View className="build__spec" key={spec.key}>
                <Text className="build__spec-label build__spec-label--raw">{spec.label}</Text>
                <Text className="build__spec-value">{spec.value}</Text>
              </View>
            ))}
          </View>
        ) : (
          <Text className="rw-caption">没有可展示的原始参数。</Text>
        )}
      </View>

      {build.origin ? (
        <View className="build__section">
          <Text className="rw-subtitle">来源说明</Text>
          <Text className="build__notes">{build.origin}</Text>
        </View>
      ) : null}

      <View className="rw-safe-bottom" />
    </View>
  )
}
