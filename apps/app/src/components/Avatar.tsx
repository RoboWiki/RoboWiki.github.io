import { useEffect, useState } from 'react'

import { Image, Text, View } from 'virtual:taro/components'
import type { User } from '@robowiki/core'

import { absoluteUrl } from '@/services/api'

type AvatarProps = {
  user: Pick<User, 'avatar_url' | 'avatar_hue' | 'display_name' | 'handle'>
  size?: number
}

/**
 * 头像：有 avatar_url 用图片，否则用 avatar_hue 生成底色 + 首字母。
 * 图片加载失败也回退到首字母，避免出现破图。
 */
export function Avatar({ user, size = 48 }: AvatarProps) {
  const url = absoluteUrl(user.avatar_url)
  const [failed, setFailed] = useState(false)

  useEffect(() => {
    setFailed(false)
  }, [url])

  const initial = String(user.display_name || user.handle || '?').trim().charAt(0).toUpperCase() || '?'
  const hue = typeof user.avatar_hue === 'number' ? user.avatar_hue : 210
  const box = {
    width: `${size}px`,
    height: `${size}px`,
    flex: `0 0 ${size}px`,
    borderRadius: '999px',
  }

  if (url && !failed) {
    return (
      <Image
        className="rw-avatar"
        src={url}
        mode="aspectFill"
        style={box}
        onError={() => setFailed(true)}
      />
    )
  }

  return (
    <View
      className="rw-avatar rw-avatar--fallback"
      style={{ ...box, background: `hsl(${hue}, 58%, 42%)`, fontSize: `${Math.round(size * 0.4)}px` }}
    >
      <Text className="rw-avatar__initial">{initial}</Text>
    </View>
  )
}
