import { useEffect, useState } from 'react'

import { Text, View } from '@tarojs/components'
import Taro, { useRouter } from '@tarojs/taro'

import { confirmQrLogin } from '@/services/api'
import { useThemeMode } from '@/utils/theme'
import './index.css'

type Phase = 'checking' | 'done' | 'error'

const IS_WEAPP = process.env.TARO_ENV === 'weapp'

/**
 * 网页扫码登录的「确认页」：用户从网页拿到小程序码，扫进来后这里只做一件事——
 * 把 scene 里的 ticket 和 wx.login 的 code 交给后端，然后退回微信。
 * 不在这里建号、不展示网页内容，身份确认与账号逻辑都在服务端。
 */
export default function LoginConfirmPage() {
  const theme = useThemeMode()
  const router = useRouter()
  const [phase, setPhase] = useState<Phase>('checking')
  const [message, setMessage] = useState('正在确认登录…')

  useEffect(() => {
    const params = (router.params || {}) as Record<string, string>
    const ticket = decodeURIComponent(params.scene || '')
    if (!IS_WEAPP) {
      setPhase('error')
      setMessage('请在微信小程序中打开这个页面确认登录')
      return
    }
    if (!ticket) {
      setPhase('error')
      setMessage('二维码无效，请回到网页重新扫码')
      return
    }
    let cancelled = false
    const run = async () => {
      try {
        const login = await Taro.login()
        if (!login.code) throw new Error('微信登录没有返回 code，请重试')
        await confirmQrLogin(ticket, login.code)
        if (cancelled) return
        setPhase('done')
        setMessage('登录成功，正在返回微信…')
        setTimeout(() => {
          // 支持 exitMiniProgram 的基础库直接退回微信；否则退回首页
          Taro.exitMiniProgram?.({ fail: () => Taro.reLaunch({ url: '/pages/home/index' }) })
        }, 1200)
      } catch (e) {
        if (cancelled) return
        setPhase('error')
        setMessage(e instanceof Error ? e.message : '登录失败，请回到网页重新扫码')
      }
    }
    void run()
    return () => {
      cancelled = true
    }
  }, [router.params])

  return (
    <View className={`confirm-page ${theme === 'dark' ? 'is-dark' : ''}`}>
      <View className="confirm-card">
        <Text className={`confirm-icon ${phase}`} aria-hidden="true">
          {phase === 'checking' ? '…' : phase === 'done' ? '✓' : '!'}
        </Text>
        <Text className="confirm-title">
          {phase === 'checking' ? '确认网页登录' : phase === 'done' ? '登录成功' : '登录失败'}
        </Text>
        <Text className="confirm-message">{message}</Text>
        {phase === 'error' && (
          <Text className="confirm-hint">回到网页刷新二维码后重新扫码即可</Text>
        )}
      </View>
    </View>
  )
}
