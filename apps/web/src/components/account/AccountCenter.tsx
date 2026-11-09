import 'antd/dist/reset.css'
import {
  App as AntApp, Form, Input, Switch,
} from 'antd'
import {
  CheckCircleFilled, ExportOutlined, GithubOutlined, LockOutlined,
  MailOutlined, ReloadOutlined, SafetyCertificateOutlined, WechatOutlined,
} from '@ant-design/icons'
import { useQuery, useQueryClient } from '@tanstack/react-query'
import { useRef, useState, type KeyboardEvent, type ReactNode } from 'react'
import {
  API_BASE, ApiError, api, auth, siteHref, uploadMedia, v1Req,
  type Account, type AuthSession, type Identity, type Media, type Notification,
  type Submission, type TokenPair,
} from '@/lib/community-api'
import { AuthForm, IslandProvider, useAuth } from '@/components/community/providers'
import { Avatar, EmptyState } from '@/components/community/ui'

// ── 常量与文案 ────────────────────────────────────────────────────────────
type TabId = 'profile' | 'security' | 'notifications' | 'submissions' | 'identities'

const TABS: { id: TabId; label: string }[] = [
  { id: 'profile', label: '资料' },
  { id: 'security', label: '安全' },
  { id: 'notifications', label: '通知' },
  { id: 'submissions', label: '我的投稿' },
  { id: 'identities', label: '登录方式' },
]

const CLIENT_LABEL: Record<string, string> = {
  web: '网页',
  h5: '手机网页',
  mini: '微信小程序',
  weapp: '微信小程序',
  wechat_mini: '微信小程序',
  github: 'GitHub',
}

const PROVIDERS: { id: string; label: string; hint: string }[] = [
  { id: 'github', label: 'GitHub', hint: '用 GitHub 授权登录，适合在电脑上参与共建。' },
  { id: 'wechat_mini', label: '微信小程序', hint: '在小程序内登录后自动绑定，网页端暂不支持发起绑定。' },
]

const STATUS_META: Record<string, { label: string; tone: string }> = {
  pending: { label: '待审', tone: 'bg-warning-soft text-warning' },
  accepted: { label: '已通过', tone: 'bg-brand-soft text-brand' },
  pr_open: { label: 'PR 中', tone: 'bg-brand-soft text-brand' },
  merged: { label: '已合并', tone: 'bg-success-soft text-success' },
  released: { label: '已发布', tone: 'bg-success-soft text-success' },
  rejected: { label: '已驳回', tone: 'bg-danger-soft text-danger' },
}

const NOTIFICATION_LABEL: Record<string, string> = {
  reply: '回复',
  comment: '评论',
  accepted: '采纳',
  mention: '提及',
  report: '举报处理',
  submission: '投稿',
  system: '系统',
}

type Status = { kind: 'ok' | 'error'; text: string } | null

// ── 小工具 ────────────────────────────────────────────────────────────────
function errText(e: unknown): string {
  if (e instanceof ApiError) return e.message
  if (e instanceof Error && e.message) return e.message
  return '请求失败，请稍后重试'
}

function when(iso: string | null | undefined): string {
  if (!iso) return '—'
  const d = new Date(iso)
  if (!Number.isFinite(d.getTime())) return '—'
  return d.toLocaleString('zh-CN', {
    year: 'numeric', month: '2-digit', day: '2-digit',
    hour: '2-digit', minute: '2-digit',
  })
}

function day(iso: string | null | undefined): string {
  if (!iso) return '—'
  const d = new Date(iso)
  return Number.isFinite(d.getTime()) ? d.toLocaleDateString('zh-CN') : '—'
}

function clientLabel(client: string): string {
  return CLIENT_LABEL[client] || client || '未知设备'
}

/** 后端通知 link 是站内根路径；站外链接保持原样。 */
function notifyHref(link: string | null): string | null {
  if (!link) return null
  if (/^(https?:)?\/\//i.test(link)) return link
  return siteHref(link)
}

function StatusLine({ value }: { value: Status }) {
  if (!value) return null
  return (
    <div aria-live="polite" className="mb-3">
      <p role={value.kind === 'error' ? 'alert' : 'status'}
        className={`m-0 rounded-md border px-3 py-2 text-[13px] leading-5 ${
          value.kind === 'error'
            ? 'border-danger/35 bg-danger-soft text-danger'
            : 'border-success/35 bg-success-soft text-success'
        }`}>
        {value.text}
      </p>
    </div>
  )
}

function SectionHead({ title, hint, action }: {
  title: string; hint?: string; action?: ReactNode
}) {
  return (
    <header className="mb-3 flex flex-wrap items-start justify-between gap-2 border-b border-line pb-3">
      <div className="min-w-0">
        <h2 className="m-0 text-[16px] font-semibold text-ink">{title}</h2>
        {hint && <p className="m-0 mt-1 text-[12px] leading-5 text-ink-3">{hint}</p>}
      </div>
      {action}
    </header>
  )
}

function RowsSkeleton({ rows = 2 }: { rows?: number }) {
  return (
    <div className="space-y-2" aria-busy="true" aria-label="正在加载">
      {Array.from({ length: rows }, (_, i) => (
        <div key={i} className="card animate-pulse p-4" aria-hidden="true">
          <div className="h-3.5 w-1/3 rounded bg-surface-3" />
          <div className="mt-2 h-3 w-full rounded bg-surface-3" />
          <div className="mt-2 h-3 w-2/3 rounded bg-surface-3" />
        </div>
      ))}
    </div>
  )
}

const BTN_PRIMARY = 'inline-flex min-h-11 items-center justify-center gap-2 rounded-md bg-brand px-4 text-[13px] font-semibold text-brand-fg transition-colors hover:bg-brand-hover disabled:cursor-not-allowed disabled:opacity-60 sm:min-h-9'
const BTN_SECONDARY = 'inline-flex min-h-11 items-center justify-center gap-2 rounded-md border border-line bg-surface px-4 text-[13px] text-ink-2 transition-colors hover:border-line-strong hover:text-ink disabled:cursor-not-allowed disabled:opacity-60 sm:min-h-9'
const BTN_GHOST = 'inline-flex min-h-11 items-center justify-center rounded-md px-3 text-[13px] text-ink-3 transition-colors hover:bg-surface-3 hover:text-ink disabled:cursor-not-allowed disabled:opacity-50 sm:min-h-8'
const BTN_DANGER = 'inline-flex min-h-11 items-center justify-center rounded-md border border-danger/35 bg-surface px-4 text-[13px] font-medium text-danger transition-colors hover:bg-danger-soft disabled:cursor-not-allowed disabled:opacity-60 sm:min-h-8'

// ── 未登录 ────────────────────────────────────────────────────────────────
const GUEST_POINTS = [
  '保存资料与头像，在社区里被认出来',
  '写评价、发讨论，并接收回复通知',
  '设置本站密码，管理登录设备与第三方绑定',
  '查看投稿进度，导出自己的账号数据',
]

function LoggedOut() {
  return (
    <section className="card p-4 sm:p-6">
      <div className="grid gap-6 lg:grid-cols-[minmax(0,1fr)_360px]">
        <div className="min-w-0">
          <h2 className="m-0 text-[20px] font-bold tracking-tight text-ink">登录后能做什么</h2>
          <p className="mb-4 mt-2 max-w-prose text-[13px] leading-6 text-ink-2">
            网页端现在可以完成资料、密码、会话、通知和投稿管理，不需要再跳小程序。
            账号与社区、App 共用一套会话。
          </p>
          <ul className="m-0 list-none space-y-3 p-0">
            {GUEST_POINTS.map(point => (
              <li key={point} className="flex items-start gap-2 text-[13px] leading-6 text-ink-2">
                <CheckCircleFilled aria-hidden="true" className="mt-1 shrink-0 text-success" />
                <span>{point}</span>
              </li>
            ))}
          </ul>
          <div className="mt-6 flex flex-wrap items-center gap-3 border-t border-line pt-4">
            <a href={siteHref('/community.html')} className="text-[13px] text-ink-3 hover:text-brand">
              先去社区看看 →
            </a>
            <a href={siteHref('/submit.html')} className="text-[13px] text-ink-3 hover:text-brand">
              投稿说明
            </a>
          </div>
        </div>

        <div className="min-w-0 rounded-lg border border-line bg-surface-2 p-4">
          <AuthForm compact />
          <p className="m-0 mt-3 border-t border-line pt-3 text-[12px] leading-5 text-ink-3">
            从 App 或 GitHub 回跳？走
            <a href={siteHref('/login.html')} className="ml-1 text-brand hover:underline">登录桥</a>
            ，一次性凭证 60 秒内有效。
          </p>
        </div>
      </div>
    </section>
  )
}

// ── 资料 ──────────────────────────────────────────────────────────────────
type ProfileValues = { display_name: string; bio?: string }

function ProfilePanel({ account, onAccount }: {
  account: Account
  onAccount: (next: Account) => void
}) {
  const [form] = Form.useForm<ProfileValues>()
  const fileRef = useRef<HTMLInputElement>(null)
  const [avatarBusy, setAvatarBusy] = useState<'upload' | 'remove' | null>(null)
  const [notifyBusy, setNotifyBusy] = useState(false)
  const [saving, setSaving] = useState(false)
  const [avatarStatus, setAvatarStatus] = useState<Status>(null)
  const [profileStatus, setProfileStatus] = useState<Status>(null)
  const [notifyStatus, setNotifyStatus] = useState<Status>(null)

  const save = async (v: ProfileValues) => {
    if (saving) return
    setSaving(true)
    setProfileStatus(null)
    try {
      const next = await api.updateMe({
        display_name: v.display_name.trim(),
        bio: (v.bio || '').trim(),
      })
      onAccount(next)
      form.setFieldsValue({ display_name: next.display_name, bio: next.bio || '' })
      setProfileStatus({ kind: 'ok', text: '资料已保存' })
    } catch (e) {
      setProfileStatus({ kind: 'error', text: errText(e) })
    } finally {
      setSaving(false)
    }
  }

  const saveAvatar = async (media: Media): Promise<Account> => {
    try {
      return await api.updateMe({ avatar_url: media.url })
    } catch (e) {
      // 上传接口返回 `/api/v1/media/…`，资料接口只接受 `/media/…` 或 http(s)。
      // 两端口径不一致时退回后端认可的规范路径，避免头像上传整条链路失败。
      if (e instanceof ApiError && e.status === 422 && media.url.includes('/media/') && media.id) {
        return api.updateMe({ avatar_url: `/media/${media.id}` })
      }
      throw e
    }
  }

  const upload = async (file: File) => {
    if (!/^image\/(jpeg|png|webp)$/i.test(file.type)) {
      setAvatarStatus({ kind: 'error', text: '只支持 JPEG / PNG / WebP 图片' })
      return
    }
    if (file.size > 5 * 1024 * 1024) {
      setAvatarStatus({ kind: 'error', text: '图片不能超过 5 MB' })
      return
    }
    setAvatarBusy('upload')
    setAvatarStatus(null)
    try {
      const media = await uploadMedia(file)
      const next = await saveAvatar(media)
      onAccount(next)
      setAvatarStatus({ kind: 'ok', text: '头像已更新' })
    } catch (e) {
      setAvatarStatus({ kind: 'error', text: errText(e) })
    } finally {
      setAvatarBusy(null)
    }
  }

  const removeAvatar = async () => {
    if (avatarBusy) return
    setAvatarBusy('remove')
    setAvatarStatus(null)
    try {
      const next = await api.updateMe({ avatar_url: null })
      onAccount(next)
      setAvatarStatus({ kind: 'ok', text: '已恢复首字母头像' })
    } catch (e) {
      setAvatarStatus({ kind: 'error', text: errText(e) })
    } finally {
      setAvatarBusy(null)
    }
  }

  const toggleNotify = async (checked: boolean) => {
    if (notifyBusy) return
    setNotifyBusy(true)
    setNotifyStatus(null)
    try {
      const next = await api.updateMe({ email_notify: checked })
      onAccount(next)
      setNotifyStatus({ kind: 'ok', text: checked ? '已开启邮件通知' : '已关闭邮件通知' })
    } catch (e) {
      setNotifyStatus({ kind: 'error', text: errText(e) })
    } finally {
      setNotifyBusy(false)
    }
  }

  return (
    <div className="grid items-start gap-4 lg:grid-cols-[240px_minmax(0,1fr)]">
      <section className="card p-4">
        <SectionHead title="头像" hint="用于社区、评价与贡献榜" />
        <div className="flex flex-col items-center gap-3">
          <div className={avatarBusy ? 'opacity-60' : ''} aria-busy={!!avatarBusy}>
            <Avatar user={account} size={88} />
          </div>
          <input ref={fileRef} type="file" accept="image/jpeg,image/png,image/webp"
            className="sr-only" id="account-avatar-input"
            onChange={e => {
              const file = e.target.files?.[0]
              e.target.value = ''
              if (file) void upload(file)
            }} />
          <div className="flex w-full flex-col gap-2">
            <button type="button" className={BTN_SECONDARY}
              disabled={!!avatarBusy}
              onClick={() => fileRef.current?.click()}>
              {avatarBusy === 'upload' ? '上传中…' : account.avatar_url ? '更换头像' : '上传头像'}
            </button>
            {account.avatar_url && (
              <button type="button" className={BTN_GHOST} disabled={!!avatarBusy}
                onClick={removeAvatar}>
                {avatarBusy === 'remove' ? '移除中…' : '恢复首字母头像'}
              </button>
            )}
          </div>
          <p className="m-0 text-center text-[12px] leading-5 text-ink-3">
            JPEG / PNG / WebP，≤ 5 MB。没有头像时用名字首字母和账号底色。
          </p>
          <div className="w-full">
            <StatusLine value={avatarStatus} />
          </div>
        </div>

        <dl className="m-0 mt-4 space-y-2 border-t border-line pt-3 text-[12px]">
          <div className="flex items-baseline justify-between gap-2">
            <dt className="text-ink-3">账号</dt>
            <dd className="mono m-0 truncate text-ink-2">@{account.handle}</dd>
          </div>
          <div className="flex items-baseline justify-between gap-2">
            <dt className="text-ink-3">加入</dt>
            <dd className="mono tabular m-0 text-ink-2">{day(account.created_at)}</dd>
          </div>
        </dl>
      </section>

      <section className="card p-4 sm:p-6">
        <SectionHead title="公开资料" hint="显示名与简介会出现在帖子、评价和主页上" />

        <Form form={form} layout="vertical" requiredMark={false} onFinish={save} disabled={saving}
          initialValues={{ display_name: account.display_name, bio: account.bio || '' }}>
          <Form.Item name="display_name" label="显示名" className="mb-3"
            normalize={v => v || ''}
            rules={[
              { required: true, message: '请填写显示名' },
              { max: 32, message: '显示名最多 32 个字符' },
            ]}>
            <Input placeholder="别人看到的名字" maxLength={32} autoComplete="nickname" />
          </Form.Item>
          <Form.Item name="bio" label="简介" className="mb-3"
            rules={[{ max: 500, message: '简介最多 500 个字符' }]}>
            <Input.TextArea rows={4} maxLength={500} showCount
              placeholder="写清你在做什么：方向、常用平台、愿意回答哪些问题。" />
          </Form.Item>

          <StatusLine value={profileStatus} />

          <button type="submit" className={BTN_PRIMARY} disabled={saving}>
            {saving ? '保存中…' : '保存资料'}
          </button>
        </Form>

        <div className="mt-6 border-t border-line pt-4">
          <div className="flex flex-wrap items-start justify-between gap-3">
            <div className="min-w-0">
              <p className="m-0 flex items-center gap-2 text-[14px] font-medium text-ink">
                <MailOutlined aria-hidden="true" className="text-ink-3" />
                邮件通知
              </p>
              <p className="m-0 mt-1 max-w-prose text-[12px] leading-5 text-ink-3">
                有人回复、采纳你的内容或处理举报时，发一封邮件。站内通知不受影响。
              </p>
              <p className="m-0 mt-1 text-[12px] text-ink-3">
                {account.email
                  ? <>发送到 <span className="mono">{account.email}</span>{account.email_verified ? '（已验证）' : '（未验证）'}</>
                  : '还没有绑定邮箱，暂时收不到邮件。'}
              </p>
            </div>
            <div className="flex items-center gap-2">
              {notifyBusy && <span className="text-[12px] text-ink-3">保存中…</span>}
              <Switch checked={!!account.email_notify} loading={notifyBusy}
                disabled={!account.email}
                onChange={toggleNotify} aria-label="开启邮件通知" />
            </div>
          </div>
          <div className="mt-2">
            <StatusLine value={notifyStatus} />
          </div>
        </div>
      </section>
    </div>
  )
}

// ── 安全 ──────────────────────────────────────────────────────────────────
type PasswordValues = {
  current_password?: string
  new_password: string
  confirm_password: string
}

function SecurityPanel({ account, onAccount }: {
  account: Account
  onAccount: (next: Account) => void
}) {
  const qc = useQueryClient()
  const { modal } = AntApp.useApp()
  const [form] = Form.useForm<PasswordValues>()
  const [saving, setSaving] = useState(false)
  const [pwStatus, setPwStatus] = useState<Status>(null)
  const [sessionStatus, setSessionStatus] = useState<Status>(null)
  const [exportStatus, setExportStatus] = useState<Status>(null)
  const [exporting, setExporting] = useState(false)
  const [endingAll, setEndingAll] = useState(false)
  const [revoking, setRevoking] = useState<number | null>(null)
  const [emailToken, setEmailToken] = useState('')
  const [emailStatus, setEmailStatus] = useState<Status>(null)
  const [emailBusy, setEmailBusy] = useState(false)

  const sendVerifyMail = async () => {
    setEmailBusy(true)
    setEmailStatus(null)
    try {
      await v1Req('/auth/email/verify/request', { method: 'POST' })
      setEmailStatus({ kind: 'ok', text: '验证邮件已发送，把邮件里的令牌填在下面。' })
    } catch (e) {
      setEmailStatus({ kind: 'error', text: errText(e) })
    } finally {
      setEmailBusy(false)
    }
  }

  const verifyEmail = async () => {
    if (emailToken.trim().length < 10) {
      setEmailStatus({ kind: 'error', text: '请输入邮件里的验证令牌' })
      return
    }
    setEmailBusy(true)
    setEmailStatus(null)
    try {
      const next = await v1Req<Account>('/auth/email/verify', {
        method: 'POST',
        body: JSON.stringify({ token: emailToken.trim() }),
      })
      onAccount(next)
      setEmailToken('')
      setEmailStatus({ kind: 'ok', text: '邮箱已验证，可以接收邮件通知。' })
    } catch (e) {
      setEmailStatus({ kind: 'error', text: errText(e) })
    } finally {
      setEmailBusy(false)
    }
  }

  const sessions = useQuery({
    queryKey: ['account', 'sessions'],
    queryFn: () => api.sessions(),
  })

  const changePassword = async (v: PasswordValues) => {
    if (!account.password_set && !v.new_password) return
    setSaving(true)
    setPwStatus(null)
    try {
      const pair: TokenPair = account.password_set
        ? await api.changePassword(v.current_password || '', v.new_password)
        : await api.setPassword(v.new_password)
      auth.setTokens(pair.access_token, pair.refresh_token ?? null)
      onAccount(pair.user)
      form.resetFields()
      await qc.invalidateQueries({ queryKey: ['account', 'sessions'] })
      setPwStatus({
        kind: 'ok',
        text: account.password_set
          ? '密码已修改。其他设备上的会话已全部失效，本机已换用新凭证。'
          : '本站密码已设置。现在可以用账号密码登录。',
      })
    } catch (e) {
      setPwStatus({ kind: 'error', text: errText(e) })
    } finally {
      setSaving(false)
    }
  }

  const revoke = (session: AuthSession) => {
    modal.confirm({
      title: '结束这条会话？',
      content: `「${clientLabel(session.client)}」需要重新登录才能继续使用。`,
      okText: '结束会话',
      cancelText: '取消',
      okButtonProps: { danger: true },
      onOk: async () => {
        setRevoking(session.id)
        setSessionStatus(null)
        try {
          await api.revokeSession(session.id)
          await qc.invalidateQueries({ queryKey: ['account', 'sessions'] })
          setSessionStatus({ kind: 'ok', text: '会话已结束' })
        } catch (e) {
          setSessionStatus({ kind: 'error', text: errText(e) })
        } finally {
          setRevoking(null)
        }
      },
    })
  }

  const logoutAll = () => {
    modal.confirm({
      title: '所有设备下线？',
      content: '包括当前这台设备在内，所有会话都会失效，需要重新登录。',
      okText: '全部下线',
      cancelText: '取消',
      okButtonProps: { danger: true },
      onOk: async () => {
        setEndingAll(true)
        setSessionStatus(null)
        try {
          await api.logoutAll()
          auth.clear()
          qc.clear()
          window.location.reload()
        } catch (e) {
          setSessionStatus({ kind: 'error', text: errText(e) })
          setEndingAll(false)
        }
      },
    })
  }

  const exportData = async () => {
    if (exporting) return
    setExporting(true)
    setExportStatus(null)
    try {
      const data = await api.exportAccount()
      const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' })
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `robowiki-account-${new Date().toISOString().slice(0, 10)}.json`
      document.body.appendChild(a)
      a.click()
      a.remove()
      URL.revokeObjectURL(url)
      setExportStatus({ kind: 'ok', text: '已导出账号数据（JSON）' })
    } catch (e) {
      setExportStatus({ kind: 'error', text: errText(e) })
    } finally {
      setExporting(false)
    }
  }

  return (
    <div className="grid items-start gap-4 lg:grid-cols-[minmax(0,1fr)_minmax(0,1fr)]">
      <section className="card p-4 sm:p-6 lg:col-span-2">
        <SectionHead title="邮箱验证"
          hint={account.email
            ? (account.email_verified
              ? '邮箱已验证，可用于找回密码、接收回复与审核通知。'
              : '未验证的邮箱只能浏览；验证后才能评分、发帖、评论和接收通知。')
            : '还没有绑定邮箱。可在小程序「我的 → 账号」绑定，绑定后即可用邮箱登录。'} />
        <div className="flex flex-wrap items-center gap-3 text-[13px] text-ink-2">
          <MailOutlined />
          <span>{account.email || '未填写邮箱'}</span>
          {account.email && (
            <span className={account.email_verified ? 'text-success' : 'text-warning'}>
              {account.email_verified ? '已验证' : '未验证'}
            </span>
          )}
        </div>
        {account.email && !account.email_verified && (
          <div className="mt-3 flex flex-wrap items-center gap-2">
            <button type="button" onClick={sendVerifyMail} disabled={emailBusy}
              className="inline-flex h-9 items-center rounded-md border border-line bg-surface px-3 text-[13px] font-semibold text-ink transition-colors hover:border-line-strong hover:bg-surface-2 disabled:opacity-60">
              {emailBusy ? '发送中…' : '发送验证邮件'}
            </button>
            <Input value={emailToken} onChange={(e) => setEmailToken(e.target.value)}
              placeholder="粘贴邮件中的令牌" className="max-w-[220px]" />
            <button type="button" onClick={verifyEmail} disabled={emailBusy}
              className="inline-flex h-9 items-center rounded-md bg-brand px-3 text-[13px] font-semibold text-brand-fg transition-colors hover:bg-brand-hover disabled:opacity-60">
              验证邮箱
            </button>
          </div>
        )}
        {emailStatus && (
          <p className={'m-0 mt-2 text-[12.5px] ' + (emailStatus.kind === 'ok' ? 'text-success' : 'text-danger')}>
            {emailStatus.text}
          </p>
        )}
      </section>

      <section className="card p-4 sm:p-6">
        <SectionHead title={account.password_set ? '修改密码' : '设置本站密码'}
          hint={account.password_set
            ? '修改后其他设备会全部下线，本机会自动换用新凭证。'
            : '当前账号由第三方登录创建，还没有本站密码；设置后可用账号密码登录。'} />

        <Form form={form} layout="vertical" requiredMark={false} onFinish={changePassword} disabled={saving}>
          {account.password_set && (
            <Form.Item name="current_password" label="当前密码" className="mb-3"
              rules={[{ required: true, message: '请输入当前密码' }]}>
              <Input.Password autoComplete="current-password" placeholder="当前密码" />
            </Form.Item>
          )}
          <Form.Item name="new_password" label="新密码" className="mb-3"
            rules={[
              { required: true, message: '请输入新密码' },
              { min: 6, message: '密码至少 6 位' },
              { max: 128, message: '密码最多 128 位' },
            ]}>
            <Input.Password autoComplete="new-password" placeholder="至少 6 位" />
          </Form.Item>
          <Form.Item name="confirm_password" label="确认新密码" className="mb-3"
            dependencies={['new_password']}
            rules={[
              { required: true, message: '请再次输入新密码' },
              ({ getFieldValue }) => ({
                validator(_, value) {
                  if (!value || getFieldValue('new_password') === value) return Promise.resolve()
                  return Promise.reject(new Error('两次输入的新密码不一致'))
                },
              }),
            ]}>
            <Input.Password autoComplete="new-password" placeholder="再输入一次" />
          </Form.Item>

          <StatusLine value={pwStatus} />

          <button type="submit" className={BTN_PRIMARY} disabled={saving}>
            <LockOutlined aria-hidden="true" />
            {saving ? '提交中…' : account.password_set ? '修改密码' : '设置密码'}
          </button>
        </Form>

        <div className="mt-6 border-t border-line pt-4">
          <p className="m-0 flex items-center gap-2 text-[14px] font-medium text-ink">
            <ExportOutlined aria-hidden="true" className="text-ink-3" />
            导出账号数据
          </p>
          <p className="mb-3 mt-1 text-[12px] leading-5 text-ink-3">
            下载账号资料、帖子与评论的 JSON 副本，用于备份或迁移。
          </p>
          <button type="button" className={BTN_SECONDARY} onClick={exportData} disabled={exporting}>
            {exporting ? '准备中…' : '下载 JSON'}
          </button>
          <div className="mt-3">
            <StatusLine value={exportStatus} />
          </div>
        </div>
      </section>

      <section className="card p-4 sm:p-6">
        <SectionHead title="登录会话" hint="仍可用的设备。结束会话后，该设备需要重新登录。"
          action={
            <button type="button" className={BTN_DANGER} onClick={logoutAll} disabled={endingAll}>
              <SafetyCertificateOutlined aria-hidden="true" />
              {endingAll ? '处理中…' : '全部下线'}
            </button>
          } />

        <StatusLine value={sessionStatus} />

        {sessions.isLoading ? (
          <RowsSkeleton rows={2} />
        ) : sessions.isError ? (
          <div role="alert" className="rounded-md border border-danger/35 bg-danger-soft p-3 text-[13px] leading-5 text-danger">
            <p className="m-0">会话列表没能加载：{errText(sessions.error)}</p>
            <div className="mt-2 flex flex-wrap items-center gap-3">
              <button type="button" className="inline-flex items-center gap-1 font-semibold hover:underline"
                onClick={() => sessions.refetch()}>
                <ReloadOutlined aria-hidden="true" /> 重试
              </button>
              <a href={siteHref('/community.html')} className="font-medium hover:underline">回社区</a>
            </div>
          </div>
        ) : !sessions.data?.length ? (
          <p className="m-0 text-[13px] leading-6 text-ink-3">没有可用的会话。下次登录会重新出现。</p>
        ) : (
          <ul className="m-0 list-none divide-y divide-line p-0">
            {sessions.data.map(session => (
              <li key={session.id} className="flex flex-wrap items-start justify-between gap-2 py-3 first:pt-0 last:pb-0">
                <div className="min-w-0">
                  <p className="m-0 text-[13px] font-medium text-ink">{clientLabel(session.client)}</p>
                  <p className="m-0 mt-1 text-[12px] leading-5 text-ink-3">
                    登录 <time dateTime={session.created_at}>{when(session.created_at)}</time>
                    <br className="sm:hidden" />
                    <span className="hidden sm:inline"> · </span>
                    到期 <time dateTime={session.expires_at}>{when(session.expires_at)}</time>
                  </p>
                </div>
                <button type="button" className={BTN_GHOST} disabled={revoking === session.id}
                  onClick={() => revoke(session)}>
                  {revoking === session.id ? '结束中…' : '结束'}
                </button>
              </li>
            ))}
          </ul>
        )}
      </section>
    </div>
  )
}

// ── 通知 ──────────────────────────────────────────────────────────────────
function NotificationPanel() {
  const qc = useQueryClient()
  const [status, setStatus] = useState<Status>(null)
  const [busy, setBusy] = useState<'all' | number | null>(null)
  const feed = useQuery({
    queryKey: ['account', 'notifications'],
    queryFn: () => api.notifications({ limit: 50 }),
  })

  const unread = feed.data?.unread ?? 0

  const markOne = async (n: Notification) => {
    if (n.read_at || busy) return
    setBusy(n.id)
    setStatus(null)
    try {
      await api.readNotification(n.id)
      await qc.invalidateQueries({ queryKey: ['account', 'notifications'] })
    } catch (e) {
      setStatus({ kind: 'error', text: errText(e) })
    } finally {
      setBusy(null)
    }
  }

  const markAll = async () => {
    if (busy || !unread) return
    setBusy('all')
    setStatus(null)
    try {
      await api.readAllNotifications()
      await qc.invalidateQueries({ queryKey: ['account', 'notifications'] })
      setStatus({ kind: 'ok', text: '全部通知已标为已读' })
    } catch (e) {
      setStatus({ kind: 'error', text: errText(e) })
    } finally {
      setBusy(null)
    }
  }

  return (
    <section>
      <div className="mb-3 flex flex-wrap items-end justify-between gap-2 border-b border-line pb-3">
        <div className="min-w-0">
          <h2 className="m-0 text-[16px] font-semibold text-ink">通知</h2>
          <p className="m-0 mt-1 text-[12px] leading-5 text-ink-3">
            {unread > 0 ? `${unread} 条未读` : '没有未读通知'} · 回复、采纳与站务处理结果都会出现在这里
          </p>
        </div>
        <button type="button" className={BTN_SECONDARY} onClick={markAll}
          disabled={busy === 'all' || unread === 0}>
          {busy === 'all' ? '处理中…' : '全部已读'}
        </button>
      </div>

      <StatusLine value={status} />

      {feed.isLoading ? (
        <RowsSkeleton rows={3} />
      ) : feed.isError ? (
        <div role="alert" className="card p-4">
          <p className="m-0 text-[13px] font-semibold text-ink">通知加载失败</p>
          <p className="mb-3 mt-1 text-[13px] leading-5 text-ink-2">{errText(feed.error)}</p>
          <div className="flex flex-wrap items-center gap-2">
            <button type="button" className={BTN_SECONDARY} onClick={() => feed.refetch()}>
              <ReloadOutlined aria-hidden="true" /> 重试
            </button>
            <a href={siteHref('/community.html')} className={BTN_GHOST}>回社区</a>
          </div>
        </div>
      ) : !feed.data?.items.length ? (
        <EmptyState title="还没有通知"
          hint="有人回复、采纳你的内容，或站务处理了你的举报时，会出现在这里。"
          action={
            <a href={siteHref('/community.html')} className={BTN_SECONDARY}>
              去社区看看
            </a>
          } />
      ) : (
        <div className="card overflow-hidden">
          <ul className="m-0 list-none divide-y divide-line p-0">
            {feed.data.items.map(n => {
              const href = notifyHref(n.link)
              return (
                <li key={n.id} className={`flex flex-wrap items-start gap-3 p-4 ${n.read_at ? '' : 'bg-brand-soft/40'}`}>
                  <span aria-hidden="true"
                    className={`mt-2 h-2 w-2 shrink-0 rounded-full ${n.read_at ? 'bg-line-strong' : 'bg-brand'}`} />
                  <div className="min-w-0 flex-1">
                    <div className="flex flex-wrap items-baseline gap-x-2 gap-y-1">
                      <span className="rounded-full border border-line bg-surface-2 px-2 py-1 text-[12px] font-medium text-ink-3">
                        {NOTIFICATION_LABEL[n.type] || n.type}
                      </span>
                      {href ? (
                        <a href={href}
                          onClick={e => {
                            if (n.read_at || e.metaKey || e.ctrlKey || e.shiftKey) return
                            e.preventDefault()
                            void markOne(n).finally(() => window.location.assign(href))
                          }}
                          className={`text-[14px] font-semibold hover:text-brand ${n.read_at ? 'text-ink-2' : 'text-ink'}`}>
                          {n.subject || '查看详情'}
                        </a>
                      ) : (
                        <span className={`text-[14px] font-semibold ${n.read_at ? 'text-ink-2' : 'text-ink'}`}>
                          {n.subject || '通知'}
                        </span>
                      )}
                      {!n.read_at && <span className="sr-only">未读</span>}
                    </div>
                    {n.body && (
                      <p className="m-0 mt-1 line-clamp-2 text-[13px] leading-5 text-ink-2">{n.body}</p>
                    )}
                    <p className="m-0 mt-1 text-[12px] text-ink-3">
                      <time dateTime={n.created_at}>{when(n.created_at)}</time>
                    </p>
                  </div>
                  {!n.read_at && (
                    <button type="button" className={BTN_GHOST} disabled={busy === n.id}
                      onClick={() => void markOne(n)}>
                      {busy === n.id ? '处理中…' : '标为已读'}
                    </button>
                  )}
                </li>
              )
            })}
          </ul>
        </div>
      )}
    </section>
  )
}

// ── 我的投稿 ──────────────────────────────────────────────────────────────
function targetHref(target: string | null): string | null {
  if (!target) return null
  if (/^(https?:)?\/\//i.test(target)) return target
  if (target.includes('/')) return siteHref(`/parts/${target.replace(/^\/+/, '')}.html`)
  return null
}

function SubmissionPanel() {
  const submissions = useQuery({
    queryKey: ['account', 'submissions'],
    queryFn: () => api.mySubmissions(50),
  })

  return (
    <section>
      <SectionHead title="我的投稿" hint="参数纠错与数据提案的审核进度。合并并发布数据后，目录才会更新。" />

      <p className="m-0 mb-3 rounded-md border border-warning/35 bg-warning-soft px-3 py-2 text-[12px] leading-5 text-warning">
        审核通过不等于页面已更新；数据在下一个 <span className="mono">data-v*</span> 发布后生效。
      </p>

      {submissions.isLoading ? (
        <RowsSkeleton rows={3} />
      ) : submissions.isError ? (
        <div role="alert" className="card p-4">
          <p className="m-0 text-[13px] font-semibold text-ink">投稿记录加载失败</p>
          <p className="mb-3 mt-1 text-[13px] leading-5 text-ink-2">{errText(submissions.error)}</p>
          <div className="flex flex-wrap items-center gap-2">
            <button type="button" className={BTN_SECONDARY} onClick={() => submissions.refetch()}>
              <ReloadOutlined aria-hidden="true" /> 重试
            </button>
            <a href={siteHref('/submit.html')} className={BTN_GHOST}>去投稿</a>
          </div>
        </div>
      ) : !submissions.data?.length ? (
        <EmptyState title="还没有投稿记录"
          hint="发现参数不对、来源过期或缺字段，可以在站内提交一条带依据的纠错。"
          action={
            <a href={siteHref('/submit.html')} className={BTN_PRIMARY}>
              去投稿
            </a>
          } />
      ) : (
        <div className="card overflow-hidden">
          <ul className="m-0 list-none divide-y divide-line p-0">
            {submissions.data.map((sub: Submission) => {
              const meta = STATUS_META[sub.status] || { label: sub.status, tone: 'bg-surface-2 text-ink-2' }
              const href = targetHref(sub.target_id)
              const fields = Object.keys(sub.payload || {})
              const reject = [...(sub.reviews || [])].reverse()
                .find(r => r.decision === 'rejected')
              return (
                <li key={sub.id} className="flex flex-wrap items-start gap-3 p-4">
                  <div className="min-w-0 flex-1">
                    <div className="flex flex-wrap items-center gap-2">
                      <span className={`inline-flex items-center rounded-full border border-line px-2 py-1 text-[12px] font-medium ${meta.tone}`}>
                        {meta.label}
                      </span>
                      <span className="mono text-[12px] text-ink-3">#{sub.id}</span>
                      <span className="text-[12px] text-ink-3">
                        <time dateTime={sub.created_at}>{day(sub.created_at)}</time>
                      </span>
                    </div>
                    <p className="m-0 mt-2 break-words text-[14px] font-medium text-ink">
                      {href ? (
                        <a href={href} className="hover:text-brand">{sub.target_id}</a>
                      ) : (sub.target_id || '未指定目标')}
                    </p>
                    <p className="m-0 mt-1 break-words text-[12px] leading-5 text-ink-3">
                      {fields.length ? `涉及字段：${fields.join('、')}` : '没有字段变更'}
                      {sub.revision > 1 ? ` · 第 ${sub.revision} 版` : ''}
                    </p>
                    {reject && (
                      <p className="m-0 mt-2 rounded-md border border-danger/25 bg-danger-soft px-3 py-2 text-[12px] leading-5 text-danger">
                        驳回：{reject.note || reject.reason_code || '未写明原因'}
                      </p>
                    )}
                  </div>
                  <a href={siteHref('/submit.html')}
                    className="inline-flex min-h-11 items-center text-[12px] text-ink-3 transition-colors hover:text-brand sm:min-h-8">
                    再投一条 →
                  </a>
                </li>
              )
            })}
          </ul>
        </div>
      )}
    </section>
  )
}

// ── 登录方式 ──────────────────────────────────────────────────────────────
function providerIcon(id: string) {
  if (id === 'github') return <GithubOutlined aria-hidden="true" />
  if (id === 'wechat_mini') return <WechatOutlined aria-hidden="true" />
  return <LockOutlined aria-hidden="true" />
}

function IdentityPanel({ account, onGoSecurity }: {
  account: Account
  onGoSecurity: () => void
}) {
  const qc = useQueryClient()
  const { modal } = AntApp.useApp()
  const [status, setStatus] = useState<Status>(null)
  const [busy, setBusy] = useState<string | null>(null)
  const identities = useQuery({
    queryKey: ['account', 'identities'],
    queryFn: () => api.identities(),
  })

  const bound = (provider: string): Identity | undefined =>
    identities.data?.find(i => i.provider === provider)

  const connectGithub = () => {
    try {
      window.sessionStorage.setItem('rw-auth-return', '/account.html')
    } catch {
      // 隐私模式下 sessionStorage 可能不可写；授权后仍会回到登录桥。
    }
    const origin = window.location.origin
    window.location.href = `${API_BASE}/auth/github/login?return_to=${encodeURIComponent(origin)}`
  }

  const unbind = (identity: Identity) => {
    const label = PROVIDERS.find(p => p.id === identity.provider)?.label || identity.provider
    modal.confirm({
      title: `解绑 ${label}？`,
      content: '解绑后这个身份不能再登录本账号。请确认还有另一种可用的登录方式。',
      okText: '解绑',
      cancelText: '取消',
      okButtonProps: { danger: true },
      onOk: async () => {
        setBusy(identity.provider)
        setStatus(null)
        try {
          await api.unlinkIdentity(identity.provider)
          await Promise.all([
            qc.invalidateQueries({ queryKey: ['account', 'identities'] }),
            qc.invalidateQueries({ queryKey: ['account', 'me'] }),
          ])
          setStatus({ kind: 'ok', text: `已解绑 ${label}` })
        } catch (e) {
          setStatus({ kind: 'error', text: errText(e) })
        } finally {
          setBusy(null)
        }
      },
    })
  }

  return (
    <section className="grid items-start gap-4 lg:grid-cols-2">
      <div className="card p-4 sm:p-6">
        <SectionHead title="第三方登录" hint="绑定后可以用对应渠道直接登录这个账号" />

        {identities.isLoading ? (
          <RowsSkeleton rows={2} />
        ) : identities.isError ? (
          <div role="alert" className="rounded-md border border-danger/35 bg-danger-soft p-3 text-[13px] leading-5 text-danger">
            <p className="m-0">绑定状态没能加载：{errText(identities.error)}</p>
            <div className="mt-2 flex flex-wrap items-center gap-3">
              <button type="button" className="inline-flex items-center gap-1 font-semibold hover:underline"
                onClick={() => identities.refetch()}>
                <ReloadOutlined aria-hidden="true" /> 重试
              </button>
              <a href={siteHref('/community.html')} className="font-medium hover:underline">回社区</a>
            </div>
          </div>
        ) : (
          <ul className="m-0 list-none divide-y divide-line p-0">
            {PROVIDERS.map(provider => {
              const identity = bound(provider.id)
              return (
                <li key={provider.id} className="flex flex-wrap items-start justify-between gap-3 py-3 first:pt-0 last:pb-0">
                  <div className="min-w-0">
                    <p className="m-0 flex items-center gap-2 text-[14px] font-medium text-ink">
                      <span className="text-[16px] text-ink-2">{providerIcon(provider.id)}</span>
                      {provider.label}
                      <span className={`inline-flex items-center rounded-full border border-line px-2 py-1 text-[12px] font-medium ${
                        identity ? 'bg-success-soft text-success' : 'bg-surface-2 text-ink-3'
                      }`}>
                        {identity ? '已绑定' : '未绑定'}
                      </span>
                    </p>
                    <p className="m-0 mt-1 max-w-prose text-[12px] leading-5 text-ink-3">
                      {identity
                        ? `绑定于 ${day(identity.created_at)}${identity.email ? ` · ${identity.email}` : ''}`
                        : provider.hint}
                    </p>
                  </div>
                  {identity ? (
                    <button type="button" className={BTN_DANGER} disabled={busy === provider.id}
                      onClick={() => unbind(identity)}>
                      {busy === provider.id ? '解绑中…' : '解绑'}
                    </button>
                  ) : provider.id === 'github' ? (
                    <button type="button" className={BTN_PRIMARY} onClick={connectGithub}>
                      <GithubOutlined aria-hidden="true" />
                      绑定 GitHub
                    </button>
                  ) : (
                    <span className="text-[12px] text-ink-3">请在小程序内完成</span>
                  )}
                </li>
              )
            })}
          </ul>
        )}

        <StatusLine value={status} />
      </div>

      <div className="card p-4 sm:p-6">
        <SectionHead title="本站密码" hint="除第三方身份外的另一种登录方式" />
        <p className="m-0 flex flex-wrap items-center gap-2 text-[13px] text-ink-2">
          <LockOutlined aria-hidden="true" className="text-ink-3" />
          {account.password_set ? '已设置，可用账号密码登录。' : '未设置，目前只能通过第三方身份登录。'}
        </p>
        <p className="mb-3 mt-2 text-[12px] leading-5 text-ink-3">
          解绑第三方身份前，请确认至少保留一种能进来的方式；站务端会拒绝把账号锁死的解绑。
        </p>
        <button type="button" className={BTN_SECONDARY} onClick={onGoSecurity}>
          {account.password_set ? '去修改密码' : '去设置密码'}
        </button>
      </div>
    </section>
  )
}

// ── 已登录外壳 ────────────────────────────────────────────────────────────
function Center() {
  const { user, ready, setUser, logout } = useAuth()
  const qc = useQueryClient()
  const [tab, setTab] = useState<TabId>('profile')
  const tabRefs = useRef<Array<HTMLButtonElement | null>>([])

  const accountQ = useQuery({
    queryKey: ['account', 'me'],
    queryFn: () => api.me(),
    enabled: !!user,
    retry: 1,
  })

  const notificationsQ = useQuery({
    queryKey: ['account', 'notifications'],
    queryFn: () => api.notifications({ limit: 50 }),
    enabled: !!user,
    retry: 1,
  })

  const account = accountQ.data ?? (user as Account | null)

  const changeTab = (id: TabId) => setTab(id)

  const onKeyDown = (e: KeyboardEvent<HTMLDivElement>) => {
    const index = TABS.findIndex(t => t.id === tab)
    let next = index
    if (e.key === 'ArrowRight') next = (index + 1) % TABS.length
    else if (e.key === 'ArrowLeft') next = (index - 1 + TABS.length) % TABS.length
    else if (e.key === 'Home') next = 0
    else if (e.key === 'End') next = TABS.length - 1
    else return
    e.preventDefault()
    changeTab(TABS[next].id)
    tabRefs.current[next]?.focus()
  }

  const applyAccount = (next: Account) => {
    qc.setQueryData(['account', 'me'], next)
    setUser(next)
  }

  // 通知角标要随已读变化；预取一次，避免切 tab 才看到未读。
  const unread = notificationsQ.data?.unread ?? 0

  if (!ready) {
    return (
      <div className="mx-auto max-w-4xl" aria-busy="true">
        <div className="card animate-pulse p-6">
          <div className="h-10 w-10 rounded-full bg-surface-3" />
          <div className="mt-3 h-4 w-40 rounded bg-surface-3" />
          <div className="mt-2 h-3 w-64 rounded bg-surface-3" />
        </div>
        <div className="mt-4 flex gap-2" aria-hidden="true">
          {[0, 1, 2, 3].map(i => <div key={i} className="h-9 w-20 animate-pulse rounded-full bg-surface-3" />)}
        </div>
      </div>
    )
  }

  if (!user) {
    return (
      <div className="mx-auto max-w-4xl">
        <LoggedOut />
      </div>
    )
  }

  if (accountQ.isLoading) {
    return (
      <div className="mx-auto max-w-4xl space-y-4" aria-busy="true">
        <div className="card animate-pulse p-6" aria-hidden="true">
          <div className="flex items-center gap-3">
            <div className="h-11 w-11 rounded-full bg-surface-3" />
            <div className="space-y-2">
              <div className="h-4 w-32 rounded bg-surface-3" />
              <div className="h-3 w-24 rounded bg-surface-3" />
            </div>
          </div>
        </div>
        <RowsSkeleton rows={2} />
      </div>
    )
  }

  if (accountQ.isError || !account) {
    return (
      <div className="mx-auto max-w-4xl">
        <div role="alert" className="card p-6">
          <h2 className="m-0 text-[16px] font-semibold text-ink">账号信息没能加载</h2>
          <p className="mb-4 mt-2 text-[13px] leading-6 text-ink-2">
            {accountQ.error ? errText(accountQ.error) : '会话可能已过期。'}
            <br />
            可以先重试；如果一直失败，退出后重新登录。
          </p>
          <div className="flex flex-wrap gap-2">
            <button type="button" className={BTN_PRIMARY} onClick={() => accountQ.refetch()}>
              <ReloadOutlined aria-hidden="true" /> 重试
            </button>
            <button type="button" className={BTN_SECONDARY} onClick={logout}>退出登录</button>
            <a href={siteHref('/community.html')} className={BTN_GHOST}>回社区</a>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="mx-auto max-w-4xl">
      <section className="card mb-4 flex flex-wrap items-center gap-3 p-4">
        <Avatar user={account} size={44} />
        <div className="min-w-0 flex-1">
          <p className="m-0 truncate text-[14px] font-semibold text-ink">{account.display_name}</p>
          <p className="m-0 truncate text-[12px] text-ink-3">
            用户 ID：{account.handle} · 声望 <span className="mono tabular">{account.reputation}</span>
            {account.is_staff && <span className="ml-1 text-warning">· 站务</span>}
          </p>
        </div>
        <a href={siteHref(`/u.html?handle=${encodeURIComponent(account.handle)}`)}
          className="inline-flex min-h-11 items-center text-[12px] text-ink-3 transition-colors hover:text-brand sm:min-h-8">
          我的主页
        </a>
        <button type="button" className={BTN_GHOST} onClick={logout}>退出</button>
      </section>

      <div className="chip-row mb-4 border-b border-line pb-3" role="tablist"
        aria-label="账号设置" onKeyDown={onKeyDown}>
        {TABS.map((t, i) => {
          const active = tab === t.id
          return (
            <button key={t.id} type="button" role="tab"
              id={`account-tab-${t.id}`}
              aria-selected={active}
              aria-controls={active ? `account-panel-${t.id}` : undefined}
              tabIndex={active ? 0 : -1}
              ref={el => { tabRefs.current[i] = el }}
              onClick={() => changeTab(t.id)}
              className={`relative inline-flex min-h-11 items-center gap-2 rounded-t-md px-3 text-[14px] transition-colors sm:min-h-9 ${
                active ? 'font-semibold text-brand' : 'text-ink-2 hover:text-ink'
              }`}>
              {t.label}
              {t.id === 'notifications' && unread > 0 && (
                <span className="mono tabular rounded-full bg-brand px-2 text-[12px] font-semibold text-brand-fg">
                  {unread > 99 ? '99+' : unread}
                </span>
              )}
              {active && (
                <span aria-hidden="true" className="absolute inset-x-2 bottom-0 h-0.5 rounded-full bg-brand" />
              )}
            </button>
          )
        })}
      </div>

      <div id={`account-panel-${tab}`} role="tabpanel" tabIndex={0}
        aria-labelledby={`account-tab-${tab}`} className="min-w-0">
        {tab === 'profile' && <ProfilePanel account={account} onAccount={applyAccount} />}
        {tab === 'security' && <SecurityPanel account={account} onAccount={applyAccount} />}
        {tab === 'notifications' && <NotificationPanel />}
        {tab === 'submissions' && <SubmissionPanel />}
        {tab === 'identities' && (
          <IdentityPanel account={account} onGoSecurity={() => changeTab('security')} />
        )}
      </div>
    </div>
  )
}

export default function AccountCenter() {
  return (
    <IslandProvider>
      <Center />
    </IslandProvider>
  )
}
