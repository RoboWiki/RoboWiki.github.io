import { Text, View } from 'virtual:taro/components'

import { setTheme, useThemeMode } from '@/utils/theme'

/** 账号页外观开关：浅色 / 深色，选择结果写入 rw.app.theme。 */
export function ThemeToggle() {
  const mode = useThemeMode()

  return (
    <View className="rw-list">
      <View className="rw-list__row">
        <View className="rw-grow">
          <Text className="rw-subtitle">外观</Text>
          <Text className="rw-caption" style={{ display: 'block' }}>
            深色适合夜间现场调试
          </Text>
        </View>
        <View className="rw-row" style={{ gap: '8px' }}>
          <View
            className={`rw-chip rw-chip--touch ${mode === 'light' ? 'rw-chip--active' : ''}`}
            onClick={() => setTheme('light')}
          >
            浅色
          </View>
          <View
            className={`rw-chip rw-chip--touch ${mode === 'dark' ? 'rw-chip--active' : ''}`}
            onClick={() => setTheme('dark')}
          >
            深色
          </View>
        </View>
      </View>
    </View>
  )
}
