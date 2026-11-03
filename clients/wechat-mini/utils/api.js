const { API } = require('../config')

function get(path, data) {
  return new Promise((resolve, reject) => {
    wx.request({
      url: API + path,
      data: data || {},
      method: 'GET',
      timeout: 8000,
      success(res) {
        if (res.statusCode >= 200 && res.statusCode < 300) resolve(res.data)
        else reject(new Error((res.data && res.data.detail) || `HTTP ${res.statusCode}`))
      },
      fail(err) { reject(new Error(err.errMsg || '网络不可用')) },
    })
  })
}

module.exports = { get }
