import Taro from 'virtual:taro/api'

/** 首页 → 部件 tab 的搜索词。switchTab 不能带 query，这里用 storage 交接。 */
const PENDING_SEARCH_KEY = 'rw.app.search'

export function openTab(path: string): void {
  Taro.switchTab({ url: path }).catch(() => {
    Taro.reLaunch({ url: path })
  })
}

export function queueCatalogSearch(keyword: string): void {
  const value = keyword.trim()
  try {
    if (value) Taro.setStorageSync(PENDING_SEARCH_KEY, value)
    else Taro.removeStorageSync(PENDING_SEARCH_KEY)
  } catch {
    // 存储失败时仍会跳转，只是搜索词带不过去。
  }

  // 空搜索直接切 tab；有关键词时用 reLaunch 带 q 进入部件页，
  // 这样 H5 与小程序的 useRouter().params.q 都能拿到（switchTab 会丢 query）。
  if (!value) {
    openTab('/pages/index/index')
    return
  }
  const url = `/pages/index/index?q=${encodeURIComponent(value)}`
  Taro.reLaunch({ url }).catch(() => {
    // 极端情况下退回 storage 交接 + switchTab。
    openTab('/pages/index/index')
  })
}

/** 部件页取走一次搜索词，避免返回 tab 时反复覆盖用户输入。 */
export function takeCatalogSearch(): string {
  try {
    const value = Taro.getStorageSync(PENDING_SEARCH_KEY)
    if (typeof value === 'string' && value) {
      Taro.removeStorageSync(PENDING_SEARCH_KEY)
      return value
    }
  } catch {
    // 忽略。
  }
  return ''
}

/**
 * 能力地图 → 部件 tab：switchTab 会丢 query，用 reLaunch 把 layer 带进去。
 * 部件页读 useRouter().params.layer；清空筛选不跳页。
 */
export function openCatalogLayer(layerId: string): void {
  const value = layerId.trim()
  if (!value) {
    openTab('/pages/index/index')
    return
  }
  const url = `/pages/index/index?layer=${encodeURIComponent(value)}`
  Taro.reLaunch({ url }).catch(() => {
    openTab('/pages/index/index')
  })
}

/**
 * 打开站外 / 网页链接：H5 新窗口，小程序复制到剪贴板后提示去浏览器。
 * 小程序 web-view 需要业务域名备案，这里不假设可用。
 */
export async function openExternal(url: string, label = '链接'): Promise<void> {
  const value = String(url || '').trim()
  if (!value) return

  if (process.env.TARO_ENV === 'h5' && typeof window !== 'undefined') {
    window.open(value, '_blank', 'noopener,noreferrer')
    return
  }

  try {
    await Taro.setClipboardData({ data: value })
    Taro.showToast({ title: `${label}已复制，请在浏览器打开`, icon: 'none', duration: 2200 })
  } catch {
    Taro.showToast({ title: '复制链接失败，请重试', icon: 'none' })
  }
}

export function showToast(title: string): void {
  Taro.showToast({ title, icon: 'none', duration: 2200 })
}
