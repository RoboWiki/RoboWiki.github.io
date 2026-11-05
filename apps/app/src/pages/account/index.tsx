import { useEffect, useState } from 'react'

import { Button, Text, View } from '@tarojs/components'
import Taro from '@tarojs/taro'
import type { User } from '@robowiki/core'

import {
  api,
  cacheUser,
  errorMessage,
  listNotifications,
  loadMe,
  logout,
  markNotificationsRead,
  type AppNotification,
} from '@/services/api'
import './index.css'

const IS_H5 = process.env.TARO_ENV === 'h5'

function goLogin() {
  Taro.navigateTo({ url: '/pages/login/index' })
}

export default function AccountPage() {
  const [user, setUser] = useState<User | null>(null)
  const [loading, setLoading] = useState(true)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')
  const [items, setItems] = useState<AppNotification[]>([])
  const [unread, setUnread] = useState(0)
  const [confirmLogout, setConfirmLogout] = useState(false)

  const loadNotifications = async () => {
    try {
      const page = await listNotifications()
      setItems(page.items || [])
      setUnread(page.unread || 0)
    } catch {
      // 通知失败不影响账号页主体。
    }
  }

  useEffect(() => {
    let alive = true
    loadMe().then(async (me) => {
      if (!alive) return
      setUser(me)
      setLoading(false)
      if (me) await loadNotifications()
    })
    return () => { alive = false }
  }, [])

  const toggleEmailNotify = async () => {
    if (!user || busy) return
    setBusy(true)
    setError('')
    try {
      const next = await api.request<User>('/auth/me', {
        method: 'PATCH',
        body: { email_notify: !user.email_notify },
      })
      setUser(next)
      cacheUser(next)
    } catch (err) {
      setError(errorMessage(err))
    } finally {
      setBusy(false)
    }
  }

  const sendVerifyMail = async () => {
    if (busy) return
    setBusy(true)
    setError('')
    try {
      await api.request('/auth/email/verify/request', { method: 'POST' })
      Taro.showToast({ title: '验证邮件已发送', icon: 'success' })
    } catch (err) {
      setError(errorMessage(err))
    } finally {
      setBusy(false)
    }
  }

  const readAll = async () => {
    if (busy || !unread) return
    setBusy(true)
    try {
      await markNotificationsRead()
      await loadNotifications()
    } catch (err) {
      setError(errorMessage(err))
    } finally {
      setBusy(false)
    }
  }

  const doLogout = async () => {
    setBusy(true)
    await logout()
    setUser(null)
    setItems([])
    setUnread(0)
    setConfirmLogout(false)
    setBusy(false)
    Taro.showToast({ title: '已退出', icon: 'none' })
  }

  if (loading) {
    return (
      <View className="rw-page">
        <Text className="rw-caption">正在读取账号…</Text>
      </View>
    )
  }

  if (!user) {
    return (
      <View className="rw-page">
        <View className="rw-stack">
          <Text className="rw-title">还没有登录</Text>
          <Text className="rw-caption">登录后可以评分、评论，并在这里管理账号。</Text>
          <Button className="rw-btn rw-btn--primary" onClick={goLogin}>去登录</Button>
        </View>
      </View>
    )
  }

  return (
    <View className="rw-page">
      <View className="account__head">
        <Text className="rw-title">{user.display_name || user.handle}</Text>
        <Text className="rw-caption">@{user.handle}</Text>
      </View>

      {error ? <Text className="rw-error">{error}</Text> : null}

      <View className="rw-list account__section">
        <View className="rw-list__row account__row">
          <View className="rw-grow">
            <Text className="rw-subtitle">邮箱</Text>
            {user.email ? (
              <Text className="rw-caption account__line">
                {user.email}
                {user.email_verified ? ' · 已验证' : ' · 未验证'}
              </Text>
            ) : (
              <Text className="rw-caption account__line">未填写邮箱</Text>
            )}
          </View>
          {user.email && !user.email_verified ? (
            <Text className="rw-link" onClick={sendVerifyMail}>发送验证邮件</Text>
          ) : null}
        </View>

        <View className="rw-list__row account__row">
          <View className="rw-grow">
            <Text className="rw-subtitle">邮件通知</Text>
            <Text className="rw-caption account__line">
              {user.email_notify ? '回复与审核结果会发到邮箱' : '当前只在站内通知'}
            </Text>
          </View>
          <Text className="rw-link" onClick={toggleEmailNotify}>
            {user.email_notify ? '关闭' : '开启'}
          </Text>
        </View>
      </View>

      <View className="account__section">
        <View className="rw-row--between account__section-head">
          <Text className="rw-subtitle">通知{unread ? ` · ${unread} 条未读` : ''}</Text>
          {unread ? <Text className="rw-link" onClick={readAll}>全部已读</Text> : null}
        </View>

        {items.length ? (
          <View className="rw-list">
            {items.map((item) => (
              <View key={item.id} className="rw-list__row account__notice">
                <View className="rw-grow">
                  <Text className="account__notice-title">
                    {item.read_at ? '' : '● '}{item.subject || '通知'}
                  </Text>
                  {item.body ? (
                    <Text className="rw-caption account__line">{item.body}</Text>
                  ) : null}
                  <Text className="rw-caption">{item.created_at.slice(0, 10)}</Text>
                </View>
              </View>
            ))}
          </View>
        ) : (
          <Text className="rw-caption">还没有通知。有人回复或审核有结果时会出现在这里。</Text>
        )}
      </View>

      {!IS_H5 ? (
        <Text className="rw-caption account__hint">小程序内账号由微信身份自动登录。</Text>
      ) : null}

      {confirmLogout ? (
        <View className="account__confirm">
          <Text className="rw-caption">退出后需要重新登录才能评分和评论。</Text>
          <View className="account__confirm-actions">
            <Text className="rw-link" onClick={() => setConfirmLogout(false)}>取消</Text>
            <Text className="rw-link rw-link--danger" onClick={doLogout}>确认退出</Text>
          </View>
        </View>
      ) : (
        <Button className="rw-btn rw-btn--ghost account__logout" onClick={() => setConfirmLogout(true)}>
          退出登录
        </Button>
      )}
      <View className="rw-safe-bottom" />
    </View>
  )
}
