const api = require('./api')

// 小程序登录只换 code，不碰用户资料：
//   wx.login() → POST /auth/wechat/mini { code }
// 服务端用应用密钥调 jscode2session，返回 access + refresh + user。
// 应用密钥与会话密钥只存在服务端；客户端和本仓库都不保存它们。
let loginInFlight = null

function wxLogin() {
  return new Promise((resolve, reject) => {
    if (typeof wx === 'undefined' || typeof wx.login !== 'function') {
      reject(new api.ApiError('当前环境不支持微信登录', 0, 'NO_WX'))
      return
    }
    wx.login({
      timeout: 8000,
      success(res) {
        if (res && res.code) resolve(res.code)
        else reject(new api.ApiError('微信登录没有返回 code，请重试', 0, 'NO_CODE'))
      },
      fail(err) {
        reject(new api.ApiError('微信登录失败，请检查网络后重试', 0, 'WX_LOGIN', err && err.errMsg))
      },
    })
  })
}

function mapLoginError(err) {
  if (!(err instanceof api.ApiError)) {
    return new api.ApiError('登录失败，请重试', 0, 'LOGIN_FAILED', err && err.message)
  }
  if (err.status === 503) {
    return new api.ApiError('小程序登录暂未开通，请稍后再试', 503, 'SERVICE_UNAVAILABLE', err.detail)
  }
  if (err.status === 502) {
    return new api.ApiError('微信登录服务暂不可用，请稍后再试', 502, 'UPSTREAM', err.detail)
  }
  if (err.status === 400) {
    return new api.ApiError(err.message || '微信登录失败，请重新进入小程序', 400, 'REJECTED', err.detail)
  }
  return err
}

function login() {
  if (loginInFlight) return loginInFlight
  const session = api.getSession()
  if (session.access_token || session.refresh_token) {
    return Promise.resolve(api.currentUser())
  }
  loginInFlight = wxLogin()
    .then(code => api.post('/auth/wechat/mini', { code }, { auth: false }))
    .then(out => {
      if (!out || !out.access_token) {
        throw new api.ApiError('登录响应缺少令牌，请重试', 0, 'BAD_RESPONSE')
      }
      api.setSession(out)
      return out.user || api.currentUser()
    })
    .catch(err => { throw mapLoginError(err) })
  const done = () => { loginInFlight = null }
  loginInFlight.then(done, done)
  return loginInFlight
}

function logout() {
  const session = api.getSession()
  // 没有 refresh 时不调 /auth/logout：后端把「不带 token」解释为撤销该账号
  // 全部会话，会把网页端一起登出。只清本机即可。
  if (!session.refresh_token) {
    api.clearSession()
    return Promise.resolve()
  }
  // 能连服务端就撤销这条 refresh 会话链；断网 / 已过期也必须清本地。
  return api.post('/auth/logout', { refresh_token: session.refresh_token })
    .catch(() => null)
    .then(() => { api.clearSession() })
}

function isLoggedIn() {
  const s = api.getSession()
  return !!(s.access_token || s.refresh_token)
}

function user() {
  return api.currentUser()
}

/** 写操作统一入口：已登录直接放行，否则先走 wx.login。 */
function ensureLogin() {
  if (isLoggedIn()) return Promise.resolve(user())
  return login()
}

module.exports = { login, logout, ensureLogin, isLoggedIn, user }
