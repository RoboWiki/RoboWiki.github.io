const config = require('../config')

function friendly(message) {
  if (/url not in domain list|not in domain list/i.test(message)) {
    return '请求域名未配置：开发时请在开发者工具关闭域名校验；上线前在小程序后台配置合法域名。'
  }
  if (/timeout/i.test(message)) return '请求超时，请检查网络后重试'
  return message || '网络不可用'
}

function absorbMeta(data) {
  // 所有公开响应都会带 site_url；拿到后立刻切换分享/图片域名，
  // 避免页面用构建时写死的域名去拼 canonical 链接。
  if (data && typeof data === 'object' && data.site_url) {
    config.setSite(data.site_url)
  }
}

function get(path, data) {
  return new Promise((resolve, reject) => {
    wx.request({
      url: config.API + path,
      data: data || {},
      method: 'GET',
      timeout: 10000,
      success(res) {
        const version = res.header && (res.header['X-RoboWiki-Data-Version'] || res.header['x-robowiki-data-version'])
        if (version) {
          try { getApp().globalData.dataVersion = version } catch (e) {}
        }
        if (res.statusCode >= 200 && res.statusCode < 300) {
          absorbMeta(res.data)
          resolve(res.data)
        } else {
          const detail = res.data && res.data.detail
          reject(new Error(typeof detail === 'string' ? detail : `HTTP ${res.statusCode}`))
        }
      },
      fail(err) {
        reject(new Error(friendly(err.errMsg)))
      },
    })
  })
}

function getUrl(url) {
  return new Promise((resolve, reject) => {
    wx.request({
      url,
      method: 'GET',
      timeout: 6000,
      success(res) {
        if (res.statusCode >= 200 && res.statusCode < 300) resolve(res.data)
        else reject(new Error(`HTTP ${res.statusCode}`))
      },
      fail(err) { reject(new Error(friendly(err.errMsg))) },
    })
  })
}

module.exports = { get, getUrl }
