import { useState } from 'react'

import { Button, Input, Text, View } from '@tarojs/components'
import Taro from '@tarojs/taro'
import { ApiError } from '@robowiki/core'

import { errorMessage, loginWithPassword, loginWithWechat } from '@/services/api'
import './index.css'

const IS_H5 = process.env.TARO_ENV === 'h5'

function backOrHome() {
  const pages = Taro.getCurrentPages()
  if (pages.length > 1) {
    Taro.navigateBack()
  } else {
    Taro.reLaunch({ url: '/pages/index/index' })
  }
}

export default function LoginPage() {
  const [account, setAccount] = useState('')
  const [password, setPassword] = useState('')
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')

  const finish = () => {
    Taro.showToast({ title: '登录成功', icon: 'success', duration: 1200 })
    setTimeout(backOrHome, 500)
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
    <View className="rw-page login">
      <View className="login__head">
        <Text className="rw-title">登录 RoboWiki</Text>
        <Text className="rw-caption">
          {IS_H5
            ? '一个账号同时用于网站、小程序和 App 的评分与讨论。'
            : '小程序内使用微信身份登录，无需另记密码。'}
        </Text>
      </View>

      {IS_H5 ? (
        <View className="login__form">
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
