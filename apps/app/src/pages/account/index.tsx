import { useEffect, useState } from 'react'

import { Button, Input, Text, Textarea, View } from '@tarojs/components'
import Taro from '@tarojs/taro'
import type { AuthSession, Identity, User } from '@robowiki/core'

import {
  api,
  applySession,
  cacheUser,
  errorMessage,
  listNotifications,
  loadMe,
  logout,
  markNotificationRead,
  markNotificationsRead,
  tokenStore,
  type AppNotification,
} from '@/services/api'
import { matchPartLink, resolvePartId } from '@/services/parts'
import './index.css'

const IS_H5 = process.env.TARO_ENV === 'h5'
const EMAIL_RE = /^[^\s@]+@[^\s@]+\.[^\s@]+$/

const CLIENT_LABEL: Record<string, string> = {
  web: '网页',
  h5: '手机网页',
  mini: '微信小程序',
  weapp: '微信小程序',
  wechat_mini: '微信小程序',
}

const PROVIDERS: Array<{ id: string; label: string }> = [
  { id: 'github', label: 'GitHub' },
  { id: 'wechat_mini', label: '微信小程序' },
]

function goLogin() {
  Taro.navigateTo({ url: '/pages/login/index' })
}

function providerLabel(id: string): string {
  return PROVIDERS.find((item) => item.id === id)?.label || id
}

function formatDate(iso: string | null | undefined): string {
  const value = String(iso || '')
  return value ? value.slice(0, 10) : ''
}

export default function AccountPage() {
  const [user, setUser] = useState<User | null>(null)
  const [loading, setLoading] = useState(true)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')
  const [notice, setNotice] = useState('')

  const [items, setItems] = useState<AppNotification[]>([])
  const [unread, setUnread] = useState(0)
  const [confirmLogout, setConfirmLogout] = useState(false)

  const [displayName, setDisplayName] = useState('')
  const [bio, setBio] = useState('')

  const [emailEditing, setEmailEditing] = useState(false)
  const [newEmail, setNewEmail] = useState('')
  const [emailPassword, setEmailPassword] = useState('')
  const [emailPending, setEmailPending] = useState(false)
  const [emailToken, setEmailToken] = useState('')

  const [currentPassword, setCurrentPassword] = useState('')
  const [newPassword, setNewPassword] = useState('')
  const [confirmPassword, setConfirmPassword] = useState('')

  const [sessions, setSessions] = useState<AuthSession[]>([])
  const [sessionsLoaded, setSessionsLoaded] = useState(false)
  const [identities, setIdentities] = useState<Identity[]>([])
  const [identitiesLoaded, setIdentitiesLoaded] = useState(false)

  const loadNotifications = async () => {
    try {
      const page = await listNotifications()
      setItems(page.items || [])
      setUnread(page.unread || 0)
    } catch {
      // 通知失败不影响账号页主体。
    }
  }

  const loadSessions = async () => {
    try {
      const rows = await api.listSessions()
      setSessions(rows || [])
    } catch (err) {
      setError(errorMessage(err))
    } finally {
      setSessionsLoaded(true)
    }
  }

  const loadIdentities = async () => {
    try {
      const rows = await api.listIdentities()
      setIdentities(rows || [])
    } catch (err) {
      setError(errorMessage(err))
    } finally {
      setIdentitiesLoaded(true)
    }
  }

  useEffect(() => {
    let alive = true
    loadMe().then(async (me) => {
      if (!alive) return
      setUser(me)
      setLoading(false)
      if (!me) return
      setDisplayName(me.display_name || '')
      setBio(me.bio || '')
      await loadNotifications()
      if (!alive) return
      await Promise.all([loadSessions(), loadIdentities()])
    })
    return () => { alive = false }
  }, [])

  const reset = () => {
    setError('')
    setNotice('')
  }

  const saveProfile = async () => {
    if (!user || busy) return
    reset()
    const name = displayName.trim()
    if (!name) {
      setError('显示名不能为空')
      return
    }
    if (bio.length > 500) {
      setError('简介最多 500 字')
      return
    }
    setBusy(true)
    try {
      const next = await api.updateMe({ display_name: name, bio: bio.trim() })
      setUser(next)
      setDisplayName(next.display_name || '')
      setBio(next.bio || '')
      cacheUser(next)
      setNotice('资料已保存')
    } catch (err) {
      setError(errorMessage(err))
    } finally {
      setBusy(false)
    }
  }

  const toggleEmailNotify = async () => {
    if (!user || busy) return
    reset()
    setBusy(true)
    try {
      const next = await api.updateMe({ email_notify: !user.email_notify })
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
    reset()
    setBusy(true)
    try {
      await api.request('/auth/email/verify/request', { method: 'POST' })
      Taro.showToast({ title: '验证邮件已发送', icon: 'success' })
    } catch (err) {
      setError(errorMessage(err))
    } finally {
      setBusy(false)
    }
  }

  const requestEmailChange = async () => {
    if (!user || busy) return
    reset()
    const email = newEmail.trim()
    if (!EMAIL_RE.test(email)) {
      setError('邮箱格式不正确')
      return
    }
    if (user.password_set && !emailPassword) {
      setError('请先输入当前密码')
      return
    }
    setBusy(true)
    try {
      await api.requestEmailChange(email, user.password_set ? emailPassword : undefined)
      setEmailPending(true)
      setEmailEditing(false)
      setNotice(`确认邮件已发送到 ${email}，请输入邮件里的令牌。`)
    } catch (err) {
      setError(errorMessage(err))
    } finally {
      setBusy(false)
    }
  }

  const confirmEmailChange = async () => {
    if (busy) return
    reset()
    const token = emailToken.trim()
    if (!token) {
      setError('请输入邮件里的令牌')
      return
    }
    setBusy(true)
    try {
      const pair = await api.confirmEmailChange(token)
      setUser(applySession(pair))
      setEmailPending(false)
      setEmailToken('')
      setEmailPassword('')
      setNotice('邮箱已更新并验证')
      await loadSessions()
    } catch (err) {
      setError(errorMessage(err))
    } finally {
      setBusy(false)
    }
  }

  const submitPassword = async () => {
    if (!user || busy) return
    reset()
    if (newPassword.length < 6) {
      setError('新密码至少 6 位')
      return
    }
    if (newPassword !== confirmPassword) {
      setError('两次输入的新密码不一致')
      return
    }
    setBusy(true)
    try {
      const pair = user.password_set
        ? await api.changePassword(currentPassword, newPassword)
        : await api.setPassword(newPassword)
      setUser(applySession(pair))
      setCurrentPassword('')
      setNewPassword('')
      setConfirmPassword('')
      setNotice(user.password_set ? '密码已修改，其他设备已下线' : '本站密码已设置')
      await loadSessions()
    } catch (err) {
      setError(errorMessage(err))
    } finally {
      setBusy(false)
    }
  }

  const revokeSession = (session: AuthSession) => {
    if (busy) return
    Taro.showModal({
      title: '结束会话',
      content: `确认结束「${CLIENT_LABEL[session.client] || session.client}」这条会话？`,
      confirmText: '结束',
      confirmColor: '#b91c1c',
    }).then(async (res) => {
      if (!res.confirm) return
      reset()
      setBusy(true)
      try {
        await api.revokeSession(session.id)
        setSessions((rows) => rows.filter((row) => row.id !== session.id))
        setNotice('会话已结束')
      } catch (err) {
        setError(errorMessage(err))
      } finally {
        setBusy(false)
      }
    })
  }

  const logoutAll = () => {
    if (busy) return
    Taro.showModal({
      title: '全部设备下线',
      content: '所有设备（包括这台）都需要重新登录，确认继续？',
      confirmText: '全部下线',
      confirmColor: '#b91c1c',
    }).then(async (res) => {
      if (!res.confirm) return
      reset()
      setBusy(true)
      try {
        await api.logoutAll()
        tokenStore.clear()
        setUser(null)
        setItems([])
        setUnread(0)
        setSessions([])
        setIdentities([])
        Taro.showToast({ title: '已全部下线', icon: 'none' })
      } catch (err) {
        setError(errorMessage(err))
      } finally {
        setBusy(false)
      }
    })
  }

  const unlinkIdentity = (identity: Identity) => {
    if (busy) return
    Taro.showModal({
      title: `解绑 ${providerLabel(identity.provider)}`,
      content: '解绑后这个身份不能再登录本账号，确认继续？',
      confirmText: '解绑',
      confirmColor: '#b91c1c',
    }).then(async (res) => {
      if (!res.confirm) return
      reset()
      setBusy(true)
      try {
        await api.unlinkIdentity(identity.provider)
        setIdentities((rows) => rows.filter((row) => row.provider !== identity.provider))
        setNotice(`已解绑 ${providerLabel(identity.provider)}`)
      } catch (err) {
        setError(errorMessage(err))
      } finally {
        setBusy(false)
      }
    })
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

  const openNotification = async (item: AppNotification) => {
    if (item.read_at) {
      // 已读也要能再次打开部件。
      await openLink(item.link)
      return
    }
    try {
      const updated = await markNotificationRead(item.id)
      setItems((rows) => rows.map((row) => (row.id === item.id ? { ...row, read_at: updated.read_at } : row)))
      setUnread((value) => Math.max(0, value - 1))
    } catch {
      // 标记失败不拦住看内容。
    }
    await openLink(item.link)
  }

  const openLink = async (link: string | null) => {
    if (!link) return
    if (!matchPartLink(link)) {
      // 其余链接（/console/post/…、/catalog）在 App 内没有对应页，只展示不跳转。
      return
    }
    Taro.showLoading({ title: '打开部件…' })
    try {
      const id = await resolvePartId(link)
      Taro.hideLoading()
      if (!id) {
        Taro.showToast({ title: '没有找到对应部件', icon: 'none' })
        return
      }
      Taro.navigateTo({ url: `/pages/part/index?id=${encodeURIComponent(id)}` })
    } catch {
      Taro.hideLoading()
      Taro.showToast({ title: '跳转失败，请稍后再试', icon: 'none' })
    }
  }

  const doLogout = async () => {
    setBusy(true)
    await logout()
    setUser(null)
    setItems([])
    setUnread(0)
    setSessions([])
    setIdentities([])
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

  const bound = new Map(identities.map((item) => [item.provider, item]))
  const providerRows = [
    ...PROVIDERS.map((item) => ({ ...item, identity: bound.get(item.id) || null })),
    ...identities
      .filter((item) => !PROVIDERS.some((known) => known.id === item.provider))
      .map((item) => ({ id: item.provider, label: providerLabel(item.provider), identity: item })),
  ]

  return (
    <View className="rw-page">
      <View className="account__head">
        <Text className="rw-title">{user.display_name || user.handle}</Text>
        <Text className="rw-caption">@{user.handle}</Text>
        {user.password_set ? null : (
          <Text className="rw-caption">第三方登录建号，还没有本站密码。</Text>
        )}
      </View>

      {error ? <Text className="rw-error">{error}</Text> : null}
      {notice ? <Text className="rw-caption rw-success account__line">{notice}</Text> : null}

      <View className="account__section">
        <View className="account__section-head">
          <Text className="rw-subtitle">个人资料</Text>
        </View>
        <View className="account__form">
          <View className="rw-stack" style={{ gap: '8px' }}>
            <Text className="rw-caption">显示名</Text>
            <View className="rw-field">
              <Input
                className="rw-input"
                value={displayName}
                maxlength={32}
                placeholder="公开显示的昵称"
                onInput={(event) => setDisplayName(event.detail.value)}
              />
            </View>
          </View>
          <View className="rw-stack" style={{ gap: '8px' }}>
            <Text className="rw-caption">简介</Text>
            <View className="rw-field rw-field--textarea">
              <Textarea
                className="rw-textarea"
                value={bio}
                maxlength={500}
                placeholder="一句话介绍自己（最多 500 字）"
                onInput={(event) => setBio(event.detail.value)}
              />
            </View>
          </View>
          <Button className="rw-btn rw-btn--primary" disabled={busy} onClick={saveProfile}>
            保存资料
          </Button>
        </View>
      </View>

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

        {emailEditing ? (
          <View className="rw-list__row account__form-row">
            <Text className="rw-caption">新邮箱</Text>
            <View className="rw-field">
              <Input
                className="rw-input"
                value={newEmail}
                placeholder="name@example.com"
                onInput={(event) => setNewEmail(event.detail.value)}
              />
            </View>
            {user.password_set ? (
              <View className="rw-field">
                <Input
                  className="rw-input"
                  value={emailPassword}
                  password
                  placeholder="当前密码"
                  onInput={(event) => setEmailPassword(event.detail.value)}
                />
              </View>
            ) : null}
            <View className="rw-row" style={{ gap: '12px' }}>
              <Button className="rw-btn rw-btn--primary" disabled={busy} onClick={requestEmailChange}>
                发送确认邮件
              </Button>
              <Button className="rw-btn" onClick={() => setEmailEditing(false)}>取消</Button>
            </View>
          </View>
        ) : (
          <View className="rw-list__row account__row">
            <Text className="rw-caption">换邮箱需要验证新地址，并会让旧会话全部失效。</Text>
            <Text className="rw-link" onClick={() => { reset(); setEmailEditing(true) }}>
              更换邮箱
            </Text>
          </View>
        )}

        {emailPending ? (
          <View className="rw-list__row account__form-row">
            <Text className="rw-caption">邮件里的确认令牌</Text>
            <View className="rw-field">
              <Input
                className="rw-input"
                value={emailToken}
                placeholder="粘贴邮件中的令牌"
                onInput={(event) => setEmailToken(event.detail.value)}
              />
            </View>
            <Button className="rw-btn rw-btn--primary" disabled={busy} onClick={confirmEmailChange}>
              确认换绑
            </Button>
          </View>
        ) : null}
      </View>

      <View className="account__section">
        <View className="account__section-head">
          <Text className="rw-subtitle">{user.password_set ? '修改密码' : '设置本站密码'}</Text>
        </View>
        <View className="account__form">
          {user.password_set ? (
            <View className="rw-field">
              <Input
                className="rw-input"
                value={currentPassword}
                password
                placeholder="当前密码"
                onInput={(event) => setCurrentPassword(event.detail.value)}
              />
            </View>
          ) : (
            <Text className="rw-caption">设置后可用用户名 + 密码登录，旧会话会全部失效。</Text>
          )}
          <View className="rw-field">
            <Input
              className="rw-input"
              value={newPassword}
              password
              placeholder="新密码（至少 6 位）"
              onInput={(event) => setNewPassword(event.detail.value)}
            />
          </View>
          <View className="rw-field">
            <Input
              className="rw-input"
              value={confirmPassword}
              password
              placeholder="再输入一次新密码"
              onInput={(event) => setConfirmPassword(event.detail.value)}
            />
          </View>
          <Button className="rw-btn rw-btn--primary" disabled={busy} onClick={submitPassword}>
            {user.password_set ? '修改密码' : '设置密码'}
          </Button>
        </View>
      </View>

      <View className="account__section">
        <View className="rw-row--between account__section-head">
          <Text className="rw-subtitle">登录会话</Text>
          <Text className="rw-link rw-link--danger" onClick={logoutAll}>全部下线</Text>
        </View>
        {!sessionsLoaded ? (
          <Text className="rw-caption">正在读取会话…</Text>
        ) : sessions.length === 0 ? (
          <Text className="rw-caption">没有其他可用会话。</Text>
        ) : (
          <View className="rw-list">
            {sessions.map((session) => (
              <View key={session.id} className="rw-list__row account__row">
                <View className="rw-grow">
                  <Text className="rw-subtitle">
                    {CLIENT_LABEL[session.client] || session.client}
                  </Text>
                  <Text className="rw-caption account__line">
                    自 {formatDate(session.created_at)} · 到期 {formatDate(session.expires_at)}
                  </Text>
                </View>
                <Text className="rw-link rw-link--danger" onClick={() => revokeSession(session)}>
                  结束
                </Text>
              </View>
            ))}
          </View>
        )}
      </View>

      <View className="account__section">
        <View className="account__section-head">
          <Text className="rw-subtitle">登录方式</Text>
        </View>
        {!identitiesLoaded ? (
          <Text className="rw-caption">正在读取绑定状态…</Text>
        ) : (
          <View className="rw-list">
            {providerRows.map((row) => (
              <View key={row.id} className="rw-list__row account__row">
                <View className="rw-grow">
                  <Text className="rw-subtitle">{row.label}</Text>
                  <Text className="rw-caption account__line">
                    {row.identity
                      ? `已绑定 · ${formatDate(row.identity.created_at)}`
                      : '未绑定'}
                  </Text>
                </View>
                {row.identity ? (
                  <Text className="rw-link rw-link--danger" onClick={() => unlinkIdentity(row.identity!)}>
                    解绑
                  </Text>
                ) : (
                  <Text className="rw-caption">需在网页完成绑定</Text>
                )}
              </View>
            ))}
          </View>
        )}
        <Text className="rw-caption account__hint">
          OAuth 跳转只在网页端提供；小程序内绑定请先到 robowiki.org.cn 登录。
        </Text>
      </View>

      <View className="account__section">
        <View className="rw-row--between account__section-head">
          <Text className="rw-subtitle">通知{unread ? ` · ${unread} 条未读` : ''}</Text>
          {unread ? <Text className="rw-link" onClick={readAll}>全部已读</Text> : null}
        </View>

        {items.length ? (
          <View className="rw-list">
            {items.map((item) => {
              const partLink = matchPartLink(item.link)
              return (
                <View
                  key={item.id}
                  className={`rw-list__row account__notice ${item.read_at ? '' : 'rw-list__row--tap'}`}
                  onClick={() => openNotification(item)}
                >
                  <Text className="account__notice-title">
                    {item.read_at ? '' : '● '}{item.subject || '通知'}
                  </Text>
                  {item.body ? (
                    <Text className="rw-caption account__line">{item.body}</Text>
                  ) : null}
                  {item.link ? (
                    <Text className={`rw-caption account__link ${partLink ? 'rw-link' : ''}`}>
                      {partLink ? '打开对应部件 ›' : item.link}
                    </Text>
                  ) : null}
                  <Text className="rw-caption">{formatDate(item.created_at)}</Text>
                </View>
              )
            })}
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
