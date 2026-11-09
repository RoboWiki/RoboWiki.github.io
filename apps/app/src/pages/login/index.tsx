import { useState } from 'react'

import { Button, Input, Text, View } from 'virtual:taro/components'
import Taro from 'virtual:taro/api'
import { ApiError } from '@robowiki/core'

import {
  api,
  errorMessage,
  loginWithPassword,
  loginWithWechat,
  registerAccount,
  requestPasswordReset,
  resetPassword,
} from '@/services/api'
import { useThemeMode } from '@/utils/theme'
import './index.css'

const IS_H5 = process.env.TARO_ENV === 'h5'
const EMAIL_RE = /^[^\s@]+@[^\s@]+\.[^\s@]+$/

function backOrHome() {
  const pages = Taro.getCurrentPages()
  if (pages.length > 1) {
    Taro.navigateBack()
  } else {
    Taro.reLaunch({ url: '/pages/index/index' })
  }
}

export default function LoginPage() {
  const theme = useThemeMode()
  const [authTab, setAuthTab] = useState<'password' | 'wechat'>(IS_H5 ? 'password' : 'wechat')
  const [mode, setMode] = useState<'login' | 'register'>('login')
  const [forgot, setForgot] = useState(false)
  const [forgotStep, setForgotStep] = useState<'email' | 'token'>('email')
  const [account, setAccount] = useState('')
  const [password, setPassword] = useState('')
  const [handle, setHandle] = useState('')
  const [displayName, setDisplayName] = useState('')
  const [email, setEmail] = useState('')
  const [resetEmail, setResetEmail] = useState('')
  const [resetToken, setResetToken] = useState('')
  const [resetPasswordValue, setResetPasswordValue] = useState('')
  const [resetPasswordConfirm, setResetPasswordConfirm] = useState('')
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')

  const finish = (title = '登录成功') => {
    Taro.showToast({ title, icon: 'success', duration: 1200 })
    setTimeout(backOrHome, 500)
  }

  const switchMode = (next: 'login' | 'register') => {
    if (busy) return
    setMode(next)
    setError('')
  }

  const reset = () => {
    setError('')
  }

  const submitRegister = async () => {
    if (busy) return
    if (handle.trim().length < 2 || handle.trim().length > 24) {
      setError('用户名需 2–24 个字符')
      return
    }
    if (!displayName.trim()) {
      setError('请填写显示名')
      return
    }
    if (email.trim() && !EMAIL_RE.test(email.trim())) {
      setError('邮箱格式不对')
      return
    }
    if (password.length < 6) {
      setError('密码至少 6 位')
      return
    }
    setBusy(true)
    setError('')
    try {
      await registerAccount(handle, displayName, password, email)
      if (email.trim()) {
        // 注册后顺手发验证邮件；发信失败不阻断注册。
        api.request('/auth/email/verify/request', { method: 'POST' }).catch(() => {})
      }
      finish(email.trim() ? '注册成功，验证邮件已发送' : '注册成功')
    } catch (err) {
      if (err instanceof ApiError && err.status === 409) {
        setError('这个用户名已被占用')
      } else {
        setError(errorMessage(err))
      }
    } finally {
      setBusy(false)
    }
  }

  const submitPassword = async () => {
    if (busy) return
    if (!account.trim()) {
      setError('请输入邮箱或用户名')
      return
    }
    if (!password) {
      setError('请输入密码')
      return
    }
    setBusy(true)
    setError('')
    try {
      await loginWithPassword(account, password)
      finish()
    } catch (err) {
      if (err instanceof ApiError && err.status === 401) {
        setError('账号或密码不对')
      } else {
        setError(errorMessage(err))
      }
    } finally {
      setBusy(false)
    }
  }

  const submitWechat = async () => {
    if (busy) return
    setBusy(true)
    setError('')
    try {
      await loginWithWechat()
      finish()
    } catch (err) {
      if (err instanceof ApiError && err.status === 503) {
        setError('微信登录暂未开放（服务端未配置小程序 Secret）')
      } else if (err instanceof ApiError && err.status === 502) {
        setError('微信登录服务暂不可用，请稍后再试')
      } else {
        setError(errorMessage(err))
      }
    } finally {
      setBusy(false)
    }
  }

  const sendResetMail = async () => {
    if (busy) return
    const value = resetEmail.trim()
    if (!EMAIL_RE.test(value)) {
      setError('邮箱格式不对')
      return
    }
    setBusy(true)
    setError('')
    try {
      await requestPasswordReset(value)
      setForgotStep('token')
      Taro.showToast({ title: '重置邮件已发送', icon: 'success' })
    } catch (err) {
      setError(errorMessage(err))
    } finally {
      setBusy(false)
    }
  }

  const submitReset = async () => {
    if (busy) return
    if (resetToken.trim().length < 10) {
      setError('请输入邮件里的重置令牌')
      return
    }
    if (resetPasswordValue.length < 6) {
      setError('新密码至少 6 位')
      return
    }
    if (resetPasswordValue !== resetPasswordConfirm) {
      setError('两次输入的新密码不一致')
      return
    }
    setBusy(true)
    setError('')
    try {
      await resetPassword(resetToken, resetPasswordValue)
      setForgot(false)
      setForgotStep('email')
      setMode('login')
      setAccount(resetEmail.trim())
      setPassword('')
      setResetToken('')
      setResetPasswordValue('')
      setResetPasswordConfirm('')
      Taro.showToast({ title: '密码已重置，请登录', icon: 'success' })
    } catch (err) {
      setError(errorMessage(err))
    } finally {
      setBusy(false)
    }
  }

  const passwordForm = () => (
    <View className="login__form">
      <View className="login__tabs" role="tablist">
        <Text
          className={`login__tab ${mode === 'login' ? 'login__tab--active' : ''}`}
          onClick={() => switchMode('login')}
        >
          登录
        </Text>
        <Text
          className={`login__tab ${mode === 'register' ? 'login__tab--active' : ''}`}
          onClick={() => switchMode('register')}
        >
          注册
        </Text>
      </View>

      {mode === 'register' ? (
        <>
          <View className="rw-stack" style={{ gap: '8px' }}>
            <Text className="rw-caption">用户名</Text>
            <View className="rw-field">
              <Input
                className="rw-input"
                value={handle}
                name="handle"
                placeholder="2–24 个字符，登录时可用"
                onInput={(event) => setHandle(event.detail.value)}
              />
            </View>
          </View>

          <View className="rw-stack" style={{ gap: '8px' }}>
            <Text className="rw-caption">显示名</Text>
            <View className="rw-field">
              <Input
                className="rw-input"
                value={displayName}
                name="display_name"
                placeholder="公开显示的昵称"
                onInput={(event) => setDisplayName(event.detail.value)}
              />
            </View>
          </View>

          <View className="rw-stack" style={{ gap: '8px' }}>
            <Text className="rw-caption">邮箱（建议填写）</Text>
            <View className="rw-field">
              <Input
                className="rw-input"
                value={email}
                name="email"
                type="text"
                placeholder="用于找回密码和邮件通知"
                onInput={(event) => setEmail(event.detail.value)}
              />
            </View>
          </View>

          <View className="rw-stack" style={{ gap: '8px' }}>
            <Text className="rw-caption">密码</Text>
            <View className="rw-field">
              <Input
                className="rw-input"
                value={password}
                name="new-password"
                password
                placeholder="至少 6 位"
                confirmType="done"
                onInput={(event) => setPassword(event.detail.value)}
                onConfirm={submitRegister}
              />
            </View>
          </View>

          {error ? <Text className="rw-error">{error}</Text> : null}

          <Button className="rw-btn rw-btn--primary" disabled={busy} onClick={submitRegister}>
            {busy ? '注册中…' : '注册并登录'}
          </Button>

          <Text className="rw-caption login__note">
            注册即登录。填写邮箱后会自动发送验证邮件，验证后可在网页或其他设备用邮箱登录。
          </Text>
        </>
      ) : (
        <>
          <View className="rw-stack" style={{ gap: '8px' }}>
            <Text className="rw-caption">邮箱 / 用户名</Text>
            <View className="rw-field">
              <Input
                className="rw-input"
                value={account}
                name="username"
                placeholder="name@example.com 或用户名"
                onInput={(event) => setAccount(event.detail.value)}
              />
            </View>
          </View>

          <View className="rw-stack" style={{ gap: '8px' }}>
            <Text className="rw-caption">密码</Text>
            <View className="rw-field">
              <Input
                className="rw-input"
                value={password}
                name="password"
                password
                placeholder="至少 6 位"
                confirmType="done"
                onInput={(event) => setPassword(event.detail.value)}
                onConfirm={submitPassword}
              />
            </View>
          </View>

          {error ? <Text className="rw-error">{error}</Text> : null}

          <Button className="rw-btn rw-btn--primary" disabled={busy} onClick={submitPassword}>
            {busy ? '登录中…' : '登录'}
          </Button>

          <Text className="rw-link login__forgot" onClick={() => { reset(); setForgot(true); setForgotStep('email') }}>
            忘记密码？
          </Text>
          <Text className="rw-caption login__note">
            用户名和已验证邮箱都可以登录；微信创建的账号先设置邮箱和密码即可在网页登录。
          </Text>
        </>
      )}
    </View>
  )

  const forgotForm = () => (
    <View className="login__form">
      <Text className="rw-subtitle">找回密码</Text>
      <Text className="rw-caption login__note">
        {forgotStep === 'email'
          ? '输入注册邮箱，我们会发一封含重置令牌的邮件。'
          : `已发送到 ${resetEmail}；把邮件里的令牌和新密码填在下面。`}
      </Text>

      {forgotStep === 'email' ? (
        <>
          <View className="rw-stack" style={{ gap: '8px' }}>
            <Text className="rw-caption">注册邮箱</Text>
            <View className="rw-field">
              <Input
                className="rw-input"
                value={resetEmail}
                name="reset-email"
                type="text"
                placeholder="name@example.com"
                onInput={(event) => setResetEmail(event.detail.value)}
                onConfirm={sendResetMail}
              />
            </View>
          </View>
          {error ? <Text className="rw-error">{error}</Text> : null}
          <Button className="rw-btn rw-btn--primary" disabled={busy} onClick={sendResetMail}>
            {busy ? '发送中…' : '发送重置邮件'}
          </Button>
        </>
      ) : (
        <>
          <View className="rw-stack" style={{ gap: '8px' }}>
            <Text className="rw-caption">邮件里的令牌</Text>
            <View className="rw-field">
              <Input
                className="rw-input"
                value={resetToken}
                name="reset-token"
                placeholder="粘贴邮件中的令牌"
                onInput={(event) => setResetToken(event.detail.value)}
              />
            </View>
          </View>
          <View className="rw-stack" style={{ gap: '8px' }}>
            <Text className="rw-caption">新密码</Text>
            <View className="rw-field">
              <Input
                className="rw-input"
                value={resetPasswordValue}
                name="reset-password"
                password
                placeholder="至少 6 位"
                onInput={(event) => setResetPasswordValue(event.detail.value)}
              />
            </View>
          </View>
          <View className="rw-stack" style={{ gap: '8px' }}>
            <Text className="rw-caption">确认新密码</Text>
            <View className="rw-field">
              <Input
                className="rw-input"
                value={resetPasswordConfirm}
                name="reset-password-confirm"
                password
                placeholder="再输入一次"
                confirmType="done"
                onInput={(event) => setResetPasswordConfirm(event.detail.value)}
                onConfirm={submitReset}
              />
            </View>
          </View>
          {error ? <Text className="rw-error">{error}</Text> : null}
          <Button className="rw-btn rw-btn--primary" disabled={busy} onClick={submitReset}>
            {busy ? '提交中…' : '重置密码'}
          </Button>
          <Text className="rw-link login__forgot" onClick={sendResetMail}>
            没收到？重新发送
          </Text>
        </>
      )}

      <Text className="rw-link login__forgot" onClick={() => { reset(); setForgot(false) }}>
        返回登录
      </Text>
    </View>
  )

  return (
    <View className={`rw-page login ${theme === 'dark' ? 'dark' : ''}`}>
      <View className="login__head">
        <Text className="rw-title">
          {forgot ? '找回密码' : mode === 'register' ? '注册 RoboWiki' : '登录 RoboWiki'}
        </Text>
        <Text className="rw-caption">
          一个账号同时用于网站、小程序和 App 的评分与讨论。
        </Text>
      </View>

      {!forgot && !IS_H5 ? (
        <View className="login__tabs login__tabs--platform">
          <Text
            className={`login__tab ${authTab === 'wechat' ? 'login__tab--active' : ''}`}
            onClick={() => { reset(); setAuthTab('wechat') }}
          >
            微信登录
          </Text>
          <Text
            className={`login__tab ${authTab === 'password' ? 'login__tab--active' : ''}`}
            onClick={() => { reset(); setAuthTab('password') }}
          >
            账号密码
          </Text>
        </View>
      ) : null}

      {authTab === 'wechat' && !IS_H5 && !forgot ? (
        <View className="login__form">
          <Text className="rw-caption">
            点击后调用微信登录，服务端用 code 换取 openid 并签发与网页同一套令牌。
          </Text>
          {error ? <Text className="rw-error">{error}</Text> : null}
          <Button className="rw-btn rw-btn--primary" disabled={busy} onClick={submitWechat}>
            {busy ? '登录中…' : '微信一键登录'}
          </Button>
          <Text className="rw-caption login__note">
            微信账号可在「我的 → 账号」设置邮箱和密码，之后也能用邮箱登录。
          </Text>
        </View>
      ) : forgot ? (
        forgotForm()
      ) : (
        passwordForm()
      )}

      <View className="login__switch">
        <Text className="rw-caption">
          {IS_H5 ? '网页端使用账号密码或扫码登录。' : '小程序端支持微信一键登录，也可使用邮箱账号。'}
        </Text>
        <Text className="rw-link" onClick={backOrHome}>
          先随便看看
        </Text>
      </View>

      <View className="rw-safe-bottom" />
    </View>
  )
}
