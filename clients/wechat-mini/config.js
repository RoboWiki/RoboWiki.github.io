// 开发版 / 体验版默认连本机 Docker；真机预览时把 LOCAL 改成电脑局域网地址，
// 例如 http://192.168.1.5:8080（手机和电脑要在同一网段）。
// 正式版必须换成已备案、已在小程序后台配置的 HTTPS 域名。
const PROD = 'https://robowiki.org'
const LOCAL = 'http://127.0.0.1:8080'

function envVersion() {
  try {
    return wx.getAccountInfoSync().miniProgram.envVersion
  } catch (e) {
    return 'release'
  }
}

const env = envVersion()
// 体验版是本地预览/真机调试用的，不能直接打向可能还没上线的正式域名。
const isLocal = env === 'develop' || env === 'trial'
const base = isLocal ? LOCAL : PROD

module.exports = {
  API: base + '/api/v1',
  SITE: base,
  IS_LOCAL: isLocal,
  ENV: env,
  // /meta 返回 site_url 后调用；分享链接、图片、网页 URL 都跟随它。
  setSite(url) {
    if (url && /^https?:\/\//i.test(url)) {
      this.SITE = url.replace(/\/+$/, '')
    }
  },
}
