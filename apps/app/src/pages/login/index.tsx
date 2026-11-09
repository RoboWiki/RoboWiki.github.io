import { useState } from 'react'

import { Button, Input, Text, View } from 'virtual:taro/components'
import Taro from 'virtual:taro/api'
import { ApiError } from '@robowiki/core'

import { errorMessage, loginWithPassword, loginWithWechat, registerAccount } from '@/services/api'
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
  const [mode, setMode] = useState<'login' | 'register'>('login')
  const [account, setAccount] = useState('')
  const [password, setPassword] = useState('')
  const [handle, setHandle] = useState('')
  const [displayName, setDisplayName] = useState('')
  const [email, setEmail] = useState('')
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
      finish('注册成功')
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

  return (
    <View className={`rw-page login ${theme === 'dark' ? 'dark' : ''}`}>
      <View className="login__head">
        <Text className="rw-title">{mode === 'register' ? '注册 RoboWiki' : '登录 RoboWiki'}</Text>
        <Text className="rw-caption">
          {IS_H5
            ? '一个账号同时用于网站、小程序和 App 的评分与讨论。'
            : '小程序内使用微信身份登录，无需另记密码。'}
        </Text>
      </View>

      {IS_H5 ? (
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
                <Text className="rw-caption">邮箱（选填）</Text>
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
                注册即登录。填写邮箱后可在账号页发送验证邮件，验证后才能接收邮件通知。
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

              <Text className="rw-caption login__note">
                账号密码登录走 /auth/login；用户名和已验证邮箱都可以登录。
              </Text>
            </>
          )}
        </View>
      ) : (
        <View className="login__form">
          <Text className="rw-caption">
            点击后调用微信登录，服务端用 code 换取 openid 并签发与网页同一套令牌。
          </Text>
          {error ? <Text className="rw-error">{error}</Text> : null}
          <Button className="rw-btn rw-btn--primary" disabled={busy} onClick={submitWechat}>
            {busy ? '登录中…' : '微信一键登录'}
          </Button>
          <Text className="rw-caption login__note">
            若服务端未配置微信小程序 Secret，登录会返回 503；这是配置问题，不是客户端错误。
          </Text>
        </View>
      )}

      <View className="login__switch">
        <Text className="rw-caption">
          {IS_H5 ? '小程序端会自动使用微信登录。' : '网页端使用账号密码登录。'}
        </Text>
        <Text className="rw-link" onClick={backOrHome}>
          先随便看看
        </Text>
      </View>

      <View className="rw-safe-bottom" />
    </View>
  )
}
