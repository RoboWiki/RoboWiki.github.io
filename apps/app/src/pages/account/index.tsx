import { useEffect, useState } from 'react'

import { Button, Input, Text, Textarea, View } from '@tarojs/components'
import Taro from '@tarojs/taro'
import type { AuthSession, Identity, Submission, User } from '@robowiki/core'

import { Avatar } from '@/components/Avatar'
import { SkeletonRows } from '@/components/Feedback'
import { ThemeToggle } from '@/components/ThemeToggle'
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
  updateAvatar,
  uploadImage,
  API_ORIGIN,
  type AppNotification,
} from '@/services/api'
import { matchPartLink, resolvePartId } from '@/services/parts'
import { openExternal } from '@/utils/nav'
import { useThemeMode } from '@/utils/theme'
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

const SUBMISSION_STATUS: Record<string, { label: string; tone: string }> = {
  pending: { label: '待审核', tone: 'rw-badge--warn' },
  accepted: { label: '已通过', tone: 'rw-badge--success' },
  rejected: { label: '已驳回', tone: 'rw-badge' },
}

const SUBMISSION_KIND: Record<string, string> = {
  part_patch: '部件纠错',
  part_new: '新部件',
}

const PROVIDERS: Array<{ id: string; label: string }> = [
  { id: 'github', label: 'GitHub' },
  { id: 'wechat_mini', label: '微信小程序' },
]

function goLogin() {
  Taro.navigateTo({ url: '/pages/login/index' })
}

function goSubmit() {
  Taro.navigateTo({ url: '/pages/submit/index' })
}

function providerLabel(id: string): string {
  return PROVIDERS.find((item) => item.id === id)?.label || id
}

function formatDate(iso: string | null | undefined): string {
  const value = String(iso || '')
  return value ? value.slice(0, 10) : ''
}

function submissionSummary(item: Submission): string {
  const payload = item.payload || {}
  const key = Object.keys(payload)[0]
  if (!key) return ''
  const raw = payload[key]
  const value = typeof raw === 'object' ? JSON.stringify(raw) : String(raw ?? '')
  return `${key}: ${value}`.slice(0, 60)
}


export default function AccountPage() {
  const theme = useThemeMode()
  const darkClass = theme === 'dark' ? 'dark' : ''
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

  const [avatarBusy, setAvatarBusy] = useState(false)
  const [exporting, setExporting] = useState(false)

  const [submissions, setSubmissions] = useState<Submission[]>([])
  const [submissionsLoaded, setSubmissionsLoaded] = useState(false)
  const [submissionsError, setSubmissionsError] = useState('')
  const [submissionsKey, setSubmissionsKey] = useState(0)

  const loadNotifications = async () => {
    try {
      const page = await listNotifications()
      setItems(page.items || [])
      setUnread(page.unread || 0)
    } catch {
      // 通知失败不影响账号页主体。
    }
  }

  /** /auth/me 没带聚合统计时，用公开资料补齐。 */
  const withStats = async (me: User): Promise<User> => {
    const keys: Array<keyof User> = [
      'reputation',
      'post_count',
      'comment_count',
      'rating_count',
      'submission_count',
      'accepted_count',
    ]
    if (keys.every((key) => typeof me[key] === 'number')) return me
    try {
      const fresh = await api.request<User>(`/users/${encodeURIComponent(me.handle)}`)
      const merged: User = {
        ...me,
        reputation: fresh.reputation ?? me.reputation,
        post_count: fresh.post_count ?? me.post_count,
        comment_count: fresh.comment_count ?? me.comment_count,
        rating_count: fresh.rating_count ?? me.rating_count,
        submission_count: fresh.submission_count ?? me.submission_count,
        accepted_count: fresh.accepted_count ?? me.accepted_count,
      }
      cacheUser(merged)
      return merged
    } catch {
      return me
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

  const loadSubmissions = async () => {
    setSubmissionsLoaded(false)
    setSubmissionsError('')
    try {
      const rows = await api.mySubmissions(8)
      setSubmissions(rows || [])
    } catch (err) {
      setSubmissionsError(errorMessage(err))
    } finally {
      setSubmissionsLoaded(true)
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
      // 统计可能不在 /auth/me 里：先渲染主体，再用公开资料补齐。
      withStats(me).then((next) => {
        if (alive) setUser(next)
      })
      await loadNotifications()
      if (!alive) return
      await Promise.all([loadSessions(), loadIdentities()])
    })
    return () => { alive = false }
  }, [])

  useEffect(() => {
    if (!user) return
    loadSubmissions()
  }, [user?.handle, submissionsKey])

  const reset = () => {
    setError('')
    setNotice('')
  }

  /** PATCH /auth/me 可能只回基础字段，合并时保住已有统计。 */
  const applyUser = (next: User) => {
    const merged: User = user
      ? {
          ...user,
          ...next,
          reputation: next.reputation ?? user.reputation,
          post_count: next.post_count ?? user.post_count,
          comment_count: next.comment_count ?? user.comment_count,
          rating_count: next.rating_count ?? user.rating_count,
          submission_count: next.submission_count ?? user.submission_count,
          accepted_count: next.accepted_count ?? user.accepted_count,
        }
      : next
    setUser(merged)
    cacheUser(merged)
  }

  const chooseAvatar = () => {
    if (!user || avatarBusy || busy) return
    reset()
    Taro.chooseImage({
      count: 1,
      sizeType: ['compressed'],
      sourceType: ['album', 'camera'],
    })
      .then(async (res) => {
        const path = res.tempFilePaths?.[0]
        if (!path) return
        setAvatarBusy(true)
        try {
          const media = await uploadImage(path)
          const next = await updateAvatar(media.url)
          applyUser(next)
          setNotice('头像已更新')
        } catch (err) {
          setError(errorMessage(err))
        } finally {
          setAvatarBusy(false)
        }
      })
      .catch((err: unknown) => {
        const message = String((err as { errMsg?: string })?.errMsg || '')
        if (/cancel/i.test(message)) return
        setError('选择图片失败，请重试')
      })
  }

  const exportAccount = async () => {
    if (!user || exporting) return
    reset()
    setExporting(true)
    try {
      const data = await api.exportAccount()
      const text = JSON.stringify(data, null, 2)
      if (IS_H5 && typeof document !== 'undefined') {
        const blob = new Blob([text], { type: 'application/json' })
        const href = URL.createObjectURL(blob)
        const link = document.createElement('a')
        link.href = href
        link.download = `robowiki-${user.handle}.json`
        document.body.appendChild(link)
        link.click()
        document.body.removeChild(link)
        setTimeout(() => URL.revokeObjectURL(href), 1000)
        setNotice('账号数据已导出为 JSON')
      } else {
        await Taro.setClipboardData({ data: text })
        Taro.showToast({ title: '账号数据已复制', icon: 'none' })
      }
    } catch (err) {
      setError(errorMessage(err))
    } finally {
      setExporting(false)
    }
  }

  const openAccountCenter = () => {
    openExternal(`${API_ORIGIN}/account.html`, '账号中心')
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
      applyUser(next)
      setDisplayName(next.display_name || name)
      setBio(typeof next.bio === 'string' ? next.bio : bio.trim())
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
      applyUser(next)
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
      const nextUser = applySession(pair)
      applyUser(nextUser)
      withStats(nextUser).then(applyUser)
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
      const nextUser = applySession(pair)
      applyUser(nextUser)
      withStats(nextUser).then(applyUser)
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
      <View className={`rw-page ${darkClass}`}>
        <View className="account__profile">
          <View className="rw-skeleton" style={{ width: '72px', height: '72px', borderRadius: '999px' }} />
          <View className="rw-grow rw-stack" style={{ gap: '8px' }}>
            <View className="rw-skeleton rw-skeleton--line" style={{ width: '48%' }} />
            <View className="rw-skeleton rw-skeleton--line" style={{ width: '30%' }} />
            <View className="rw-skeleton rw-skeleton--line" style={{ width: '62%' }} />
          </View>
        </View>
        <View className="account__stats">
          {Array.from({ length: 6 }).map((_, index) => (
            <View className="account__stat" key={index}>
              <View className="rw-skeleton rw-skeleton--line" style={{ width: '40%' }} />
              <View className="rw-skeleton rw-skeleton--line" style={{ width: '58%' }} />
            </View>
          ))}
        </View>
        <SkeletonRows rows={3} />
      </View>
    )
  }

  if (!user) {
    return (
      <View className={`rw-page ${darkClass}`}>
        <View className="rw-stack">
          <Text className="rw-title">还没有登录</Text>
          <Text className="rw-caption">登录后可以评分、评论，并在这里管理账号。</Text>
          <Button className="rw-btn rw-btn--primary" onClick={goLogin}>去登录</Button>
        </View>
        <View className="account__section">
          <ThemeToggle />
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

  const statRows: Array<{ label: string; value?: number }> = [
    { label: '帖子', value: user.post_count },
    { label: '评论', value: user.comment_count },
    { label: '评分', value: user.rating_count },
    { label: '投稿', value: user.submission_count },
    { label: '被采纳', value: user.accepted_count },
    { label: '声望', value: user.reputation },
  ]

  return (
    <View className={`rw-page ${darkClass}`}>
      <View className="account__profile">
        <View
          className={`account__avatar ${avatarBusy ? 'account__avatar--busy' : ''}`}
          onClick={chooseAvatar}
        >
          <Avatar user={user} size={72} />
          <Text className="account__avatar-action">
            {avatarBusy ? '上传中…' : '换头像'}
          </Text>
        </View>
        <View className="rw-grow account__identity">
          <Text className="rw-title">{user.display_name || user.handle}</Text>
          <Text className="rw-caption">
            @{user.handle}
            {user.is_staff ? ' · 站务' : ''}
          </Text>
          <Text className="rw-caption">
            {user.password_set ? '本站账号' : '第三方登录建号，还没有本站密码'}
          </Text>
        </View>
      </View>

      <View className="account__stats">
        {statRows.map((row) => (
          <View className="account__stat" key={row.label}>
            <Text className="account__stat-value">
              {typeof row.value === 'number' ? row.value : '—'}
            </Text>
            <Text className="rw-caption">{row.label}</Text>
          </View>
        ))}
      </View>

      {error ? <Text className="rw-error">{error}</Text> : null}
      {notice ? <Text className="rw-caption rw-success account__line">{notice}</Text> : null}

      <View className="account__section">
        <ThemeToggle />
      </View>

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

      <View className="account__section">
        <View className="account__section-head">
          <Text className="rw-subtitle">我的投稿</Text>
          <Text className="rw-link rw-link--tap" onClick={goSubmit}>
            去投稿 ›
          </Text>
        </View>

        <Text className="rw-caption account__line">
          审核通过不等于页面已更新；数据在下一个 data-v* 发布后生效。
        </Text>

        {!submissionsLoaded ? (
          <Text className="rw-caption">正在读取投稿…</Text>
        ) : submissionsError ? (
          <View className="account__inline-error">
            <Text className="rw-caption">{submissionsError}</Text>
            <Text className="rw-link rw-link--tap" onClick={() => setSubmissionsKey((key) => key + 1)}>
              重试
            </Text>
          </View>
        ) : submissions.length === 0 ? (
          <View className="account__empty">
            <Text className="rw-caption">还没有投稿。发现参数有误时，可以直接提交纠错。</Text>
            <Text className="rw-link rw-link--tap" onClick={goSubmit}>
              投稿纠错 ›
            </Text>
          </View>
        ) : (
          <View className="rw-list">
            {submissions.map((item) => {
              const status = SUBMISSION_STATUS[item.status] || {
                label: item.status,
                tone: 'rw-badge',
              }
              const summary = submissionSummary(item)
              return (
                <View key={item.id} className="rw-list__row account__submission">
                  <View className="rw-grow">
                    <View className="account__submission-head">
                      <Text className="rw-subtitle">
                        {SUBMISSION_KIND[item.kind] || item.kind} #{item.id}
                      </Text>
                      <Text className={`rw-badge ${status.tone}`}>{status.label}</Text>
                    </View>
                    <Text className="rw-caption account__line">
                      目标 {item.target_id || '—'} · {formatDate(item.created_at)}
                    </Text>
                    {summary ? (
                      <Text className="rw-caption account__line rw-line-clamp-1">{summary}</Text>
                    ) : null}
                  </View>
                </View>
              )
            })}
          </View>
        )}
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
            <Text className="rw-link rw-link--tap" onClick={sendVerifyMail}>发送验证邮件</Text>
          ) : null}
        </View>

        <View className="rw-list__row account__row">
          <View className="rw-grow">
            <Text className="rw-subtitle">邮件通知</Text>
            <Text className="rw-caption account__line">
              {user.email_notify ? '回复与审核结果会发到邮箱' : '当前只在站内通知'}
            </Text>
          </View>
          <Text className="rw-link rw-link--tap" onClick={toggleEmailNotify}>
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
            <Text className="rw-link rw-link--tap" onClick={() => { reset(); setEmailEditing(true) }}>
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
          <Text className="rw-link rw-link--tap rw-link--danger" onClick={logoutAll}>全部下线</Text>
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
                <Text className="rw-link rw-link--tap rw-link--danger" onClick={() => revokeSession(session)}>
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
                  <Text className="rw-link rw-link--tap rw-link--danger" onClick={() => unlinkIdentity(row.identity!)}>
                    解绑
                  </Text>
                ) : (
                  <Text className="rw-link rw-link--tap" onClick={openAccountCenter}>
                    去网页绑定 ›
                  </Text>
                )}
              </View>
            ))}
          </View>
        )}
        <Text className="rw-caption account__hint">
          OAuth 跳转只在网页账号中心提供：{IS_H5 ? '点击上方链接会在新窗口打开。' : '点击后复制链接，请在手机浏览器打开。'}
        </Text>
      </View>

      <View className="account__section">
        <View className="rw-row--between account__section-head">
          <Text className="rw-subtitle">通知{unread ? ` · ${unread} 条未读` : ''}</Text>
          {unread ? <Text className="rw-link rw-link--tap" onClick={readAll}>全部已读</Text> : null}
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

      <View className="account__section">
        <View className="account__section-head">
          <Text className="rw-subtitle">账号数据</Text>
        </View>
        <View className="rw-list">
          <View className="rw-list__row account__row">
            <View className="rw-grow">
              <Text className="rw-subtitle">导出账号数据</Text>
              <Text className="rw-caption account__line">
                {IS_H5 ? '下载 JSON，包含资料、会话与贡献记录。' : '复制 JSON 到剪贴板，可粘贴保存。'}
              </Text>
            </View>
            <Text className="rw-link rw-link--tap" onClick={exportAccount}>
              {exporting ? '导出中…' : '导出'}
            </Text>
          </View>
        </View>
      </View>

      {confirmLogout ? (
        <View className="account__confirm">
          <Text className="rw-caption">退出后需要重新登录才能评分和评论。</Text>
          <View className="account__confirm-actions">
            <Text className="rw-link rw-link--tap" onClick={() => setConfirmLogout(false)}>取消</Text>
            <Text className="rw-link rw-link--tap rw-link--danger" onClick={doLogout}>确认退出</Text>
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
