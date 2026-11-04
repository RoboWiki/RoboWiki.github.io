// 开发版连本机 Docker；真机调试时把 LOCAL 改成电脑局域网地址，
// 例如 http://192.168.1.5:8080（手机和电脑要在同一网段）。
// 体验版 / 正式版走已备案、已在小程序后台配置的 HTTPS 域名。
const PROD = 'https://robowiki.org.cn'
const LOCAL = 'http://127.0.0.1:8080'

function envVersion() {
  try {
    return wx.getAccountInfoSync().miniProgram.envVersion
  } catch (e) {
    return 'release'
  }
}

const env = envVersion()
// 只有开发版连本机；体验版和正式版必须能直接打向主域。
// 映射固定为：develop → LOCAL，trial / release → PROD。不要按「非正式版」判断，
// 否则体验版会打到 127.0.0.1，审核和真机预览都会失败。
function baseFor(version) {
  return version === 'develop' ? LOCAL : PROD
}
const isLocal = env === 'develop'
const base = baseFor(env)

module.exports = {
  API: base + '/api/v1',
  SITE: base,
  IS_LOCAL: isLocal,
  ENV: env,
  // 供 tests/check.js 直接核对环境映射，不需要启动开发者工具。
  baseFor,
  LOCAL,
  PROD,
  // /meta 返回 site_url 后调用；分享链接、图片、网页 URL 都跟随它。
  setSite(url) {
    if (url && /^https?:\/\//i.test(url)) {
      this.SITE = url.replace(/\/+$/, '')
    }
  },
}
