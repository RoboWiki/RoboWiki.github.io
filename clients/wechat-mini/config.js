// 开发版连本机 Docker（微信开发者工具需在「详情 → 本地设置」关闭域名校验）；
// 体验版 / 正式版必须换成已备案、已在小程序后台配置的 HTTPS 域名。
// 真机预览开发版时，把 LOCAL 改成电脑的局域网地址，如 http://192.168.1.5:8080。
const PROD = 'https://robowiki.org'
const LOCAL = 'http://127.0.0.1:8080'

function envVersion() {
  try {
    return wx.getAccountInfoSync().miniProgram.envVersion
  } catch (e) {
    return 'release'
  }
}

const isDev = envVersion() === 'develop'
const base = isDev ? LOCAL : PROD

module.exports = {
  API: base + '/api/v1',
  SITE: base,
  IS_DEV: isDev,
}
