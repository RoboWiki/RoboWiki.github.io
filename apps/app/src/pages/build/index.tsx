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
  const isFull = build.openness === 'full'
  const artifacts = build.artifacts || {}
  const ARTIFACTS: Array<{ key: string; label: string }> = [
    { key: 'urdf', label: 'URDF' },
    { key: 'cad', label: '机械 CAD' },
    { key: 'bom', label: 'BOM 表' },
    { key: 'hardware', label: '硬件 / PCB' },
    { key: 'firmware', label: '固件' },
    { key: 'assembly', label: '装配说明' },
    { key: 'docs', label: '文档' },
  ]
  const artifactLinks = ARTIFACTS
    .map((item) => ({ ...item, url: artifacts[item.key] }))
    .filter((item): item is { key: string; label: string; url: string } => Boolean(item.url))
  const bom = build.bom || []
  const origins = build.artifacts_origin || {}
  const artifactName = (key: string, label: string) => origins[key] === 'community' ? `${label}（社区）` : label
  const eco = build.ecosystem || null
  const ECO_ROLES = ['官方项目', '官方描述/资产', '官方 SDK', '仿真', '训练', '部署', '导航', '控制/MPC', '社区复刻', 'BOM/复现', '工具/资料']
  const ecoProjects = (eco?.projects || []).filter((p) => p && p.url) as Array<{
    name: string; url: string; role: string; desc?: string | null
  }>

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
          {build.openness ? (
            <Text className={`rw-badge ${isFull ? 'rw-badge--success' : ''}`}>
              {isFull ? '全开源' : '半开源'}
            </Text>
          ) : null}
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

      {build.openness_note ? (
        <View className="build__section build__note-warn">
          <Text className="rw-subtitle">开源边界</Text>
          <Text className="build__notes">{build.openness_note}</Text>
        </View>
      ) : null}

      {artifactLinks.length || bom.length ? (
        <View className="build__section">
          <View className="rw-row rw-row--between">
            <Text className="rw-subtitle">可复现资料</Text>
            <Text className="rw-caption">
              {bom.length ? `BOM ${bom.length} 项` : artifactLinks.length ? `${artifactLinks.length} 份` : ''}
            </Text>
          </View>
          <Text className="rw-caption">
            {build.openness
              ? isFull
                ? '全开源方案：下列资料来自官方仓库，缺哪项就不显示。'
                : '半开源方案：机械与硬件未公开，以下为已开放的资料入口。'
              : '资料入口来自官方仓库，缺哪项就不显示。'}
          </Text>
          <View className="build__links">
            {artifactLinks.map((item) => (
              <View
                className="build__link"
                key={item.key}
                onClick={() => openExternal(item.url, item.label)}
              >
                <Text className="build__link-label">{artifactName(item.key, item.label)}</Text>
                <Text className="build__link-arrow">↗</Text>
              </View>
            ))}
          </View>
        </View>
      ) : null}

      {ecoProjects.length ? (
        <View className="build__section">
          <View className="rw-row rw-row--between">
            <Text className="rw-subtitle">仓库与子项目</Text>
            <Text className="rw-caption">{ecoProjects.length} 个</Text>
          </View>
          <Text className="rw-caption">
            官方子仓、资料与社区复刻按角色分组；社区项目不代表官方支持。
          </Text>
          {ECO_ROLES.map((role) => {
            const list = ecoProjects.filter((p) => p.role === role)
            if (!list.length) return null
            return (
              <View className="build__eco-group" key={role}>
                <Text className="build__eco-role">{role}（{list.length}）</Text>
                <View className="build__links">
                  {list.map((p) => (
                    <View
                      className="build__link"
                      key={p.url}
                      onClick={() => openExternal(p.url, p.name)}
                    >
                      <Text className="build__link-label">{p.name}</Text>
                      <Text className="build__link-arrow">↗</Text>
                    </View>
                  ))}
                </View>
              </View>
            )
          })}
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
