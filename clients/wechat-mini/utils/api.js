const config = require('../config')

// access 短寿命、refresh 每次轮换。两者都只放在本机 Storage：
// refresh 原文只从 /auth/refresh 的响应里拿一次，服务端只留哈希。
// 小程序不保存微信会话密钥、openid 或应用密钥 —— 那些是服务端的事。
const STORAGE_KEYS = {
  access: 'robowiki.access_token',
  refresh: 'robowiki.refresh_token',
  user: 'robowiki.user',
}

// Node 静态检查 / 单测没有 wx 时退回内存，页面运行时始终走 wx Storage。
const memory = {}

function wxApi() {
  return typeof wx !== 'undefined' ? wx : null
}

function storageGet(key) {
  const w = wxApi()
  try {
    if (w && typeof w.getStorageSync === 'function') {
      const v = w.getStorageSync(key)
      if (v !== '' && v !== undefined && v !== null) return v
    }
  } catch (e) {}
  return memory[key]
}

function storageSet(key, value) {
  memory[key] = value
  const w = wxApi()
  try {
    if (w && typeof w.setStorageSync === 'function') w.setStorageSync(key, value)
  } catch (e) {}
}

function storageRemove(key) {
  delete memory[key]
  const w = wxApi()
  try {
    if (w && typeof w.removeStorageSync === 'function') w.removeStorageSync(key)
    else if (w && typeof w.setStorageSync === 'function') w.setStorageSync(key, '')
  } catch (e) {}
}

class ApiError extends Error {
  constructor(message, status, code, detail) {
    super(message || '网络不可用')
    this.name = 'ApiError'
    this.status = Number(status) || 0
    this.code = code || 'ERROR'
    this.detail = detail === undefined ? null : detail
  }
}

function getSession() {
  return {
    access_token: String(storageGet(STORAGE_KEYS.access) || ''),
    refresh_token: String(storageGet(STORAGE_KEYS.refresh) || ''),
    user: storageGet(STORAGE_KEYS.user) || null,
  }
}

function setSession(payload) {
  const access = payload && payload.access_token
  if (!access) return getSession()
  storageSet(STORAGE_KEYS.access, access)
  if (payload.refresh_token) storageSet(STORAGE_KEYS.refresh, payload.refresh_token)
  if (payload.user) storageSet(STORAGE_KEYS.user, payload.user)
  return getSession()
}

function clearSession() {
  storageRemove(STORAGE_KEYS.access)
  storageRemove(STORAGE_KEYS.refresh)
  storageRemove(STORAGE_KEYS.user)
}

function currentUser() {
  return getSession().user
}

function loginExpired(detail) {
  return new ApiError('登录已过期，请重新登录', 401, 'UNAUTHENTICATED', detail || null)
}

function loginRequired() {
  return new ApiError('请先登录后再操作', 401, 'UNAUTHENTICATED')
}

function friendly(message) {
  const msg = String(message || '')
  if (/url not in domain list|not in domain list/i.test(msg)) {
    return '请求域名未配置：开发时请在开发者工具关闭域名校验；上线前在小程序后台配置合法域名。'
  }
  if (/timeout/i.test(msg)) return '请求超时，请检查网络后重试'
  if (/ssl|certificate|handshake/i.test(msg)) return 'HTTPS 证书校验失败，请检查域名与证书'
  return '网络不可用，请检查网络或域名白名单'
}

const FIELD_LABELS = {
  score: '评分',
  own_hardware: '是否装过机',
  note: '备注',
  code: '微信登录凭证',
  refresh_token: '登录状态',
  body: '内容',
  page: '页面',
  parent_id: '回复对象',
}

function detailMessage(data) {
  if (!data) return ''
  if (typeof data === 'string') return data
  const detail = data.detail
  if (typeof detail === 'string') return detail
  if (Array.isArray(detail)) {
    const first = detail[0] || {}
    const loc = Array.isArray(first.loc) ? first.loc.filter(x => x !== 'body' && x !== 'query' && x !== 'path') : []
    const field = loc.length ? (FIELD_LABELS[loc[loc.length - 1]] || String(loc[loc.length - 1])) : ''
    const msg = first.msg || first.message || '参数不合法'
    return field ? field + '：' + msg : msg
  }
  if (typeof data.message === 'string') return data.message
  return ''
}

function statusError(status, data) {
  const detail = detailMessage(data)
  if (status === 401) {
    return new ApiError(detail || '需要登录后再操作', 401, 'UNAUTHORIZED', data)
  }
  if (status === 403) {
    return new ApiError(detail || '没有权限执行这个操作', 403, 'FORBIDDEN', data)
  }
  if (status === 404) {
    return new ApiError(detail || '内容不存在或已删除', 404, 'NOT_FOUND', data)
  }
  if (status === 409) {
    return new ApiError(detail || '操作冲突，请刷新后重试', 409, 'CONFLICT', data)
  }
  if (status === 422) {
    return new ApiError(detail || '提交内容不符合要求，请检查后重试', 422, 'INVALID', data)
  }
  if (status === 429) {
    return new ApiError(detail || '操作太频繁，请稍后再试', 429, 'RATE_LIMITED', data)
  }
  if (status >= 500) {
    return new ApiError(detail || '服务器暂时不可用，请稍后再试', status, 'SERVER', data)
  }
  return new ApiError(detail || '请求失败（HTTP ' + status + '）', status, 'HTTP_ERROR', data)
}

function hostOf(url) {
  const m = /^https?:\/\/([^\/]+)/i.exec(String(url || ''))
  return m ? m[1].toLowerCase() : ''
}

function absorbMeta(data) {
  // 所有公开响应都会带 site_url；只有它和 API 同源时才切分享/图片域名。
  // 真机预览常把 API 指向局域网 IP，而 Docker 里 site_url 还是 localhost——
  // 无条件采用会让图片和复制链接继续指向本机。
  if (data && typeof data === 'object' && data.site_url) {
    const apiHost = hostOf(config.API)
    const siteHost = hostOf(data.site_url)
    if (!apiHost || !siteHost || apiHost === siteHost) {
      config.setSite(data.site_url)
    }
  }
}

function rawRequest(method, path, data, withAuth, timeout) {
  return new Promise((resolve, reject) => {
    const w = wxApi()
    if (!w || typeof w.request !== 'function') {
      reject(new ApiError('当前环境不支持网络请求', 0, 'NO_WX'))
      return
    }
    const header = {
      'content-type': 'application/json',
      // 服务端会话列表用它区分 mini / web / console。
      'X-Client': 'mini',
    }
    if (withAuth) {
      const token = getSession().access_token
      if (token) header.Authorization = 'Bearer ' + token
    }
    w.request({
      url: /^https?:\/\//i.test(path) ? path : config.API + path,
      method,
      data: data || {},
      header,
      timeout: timeout || 10000,
      success(res) {
        const version = res.header && (res.header['X-RoboWiki-Data-Version'] || res.header['x-robowiki-data-version'])
        if (version) {
          try { getApp().globalData.dataVersion = version } catch (e) {}
        }
        if (res.statusCode >= 200 && res.statusCode < 300) {
          absorbMeta(res.data)
          resolve(res.data)
        } else {
          reject(statusError(res.statusCode, res.data))
        }
      },
      fail(err) {
        reject(new ApiError(friendly(err && err.errMsg), 0, 'NETWORK', (err && err.errMsg) || null))
      },
    })
  })
}

let refreshInFlight = null

/**
 * 用 refresh 换一对新 token。并发 401 共用同一次刷新：
 * 后端 refresh 是一次性轮换，两个请求各刷一次会把整条会话链判为复用。
 */
function refreshSession() {
  if (refreshInFlight) return refreshInFlight
  const session = getSession()
  if (!session.refresh_token) {
    const hadAccess = !!session.access_token
    clearSession()
    return Promise.reject(hadAccess ? loginExpired() : loginRequired())
  }
  const p = rawRequest('POST', '/auth/refresh',
    { refresh_token: session.refresh_token }, false, 10000)
    .then(out => {
      setSession(out)
      return out
    })
    .catch(err => {
      // refresh 被撤销 / 过期 / 已复用：本地令牌已无意义，清掉并要求重登。
      // 断网等网络错误保留令牌，恢复网络后还能继续。
      if (err && err.status === 401) {
        clearSession()
        throw loginExpired(err.detail)
      }
      throw err
    })
  refreshInFlight = p
  const done = () => { if (refreshInFlight === p) refreshInFlight = null }
  p.then(done, done)
  return p
}

function request(method, path, data, options) {
  const opts = options || {}
  const withAuth = opts.auth !== false
  return rawRequest(method, path, data, withAuth, opts.timeout).catch(err => {
    if (!err || err.status !== 401 || !withAuth) throw err
    if (opts.retried) {
      clearSession()
      throw loginExpired(err.detail)
    }
    // 401 只重试一次；重试前先把 refresh 换掉。
    return refreshSession()
      .then(() => request(method, path, data,
        Object.assign({}, opts, { auth: true, retried: true })))
      .catch(e => {
        if (e && e.status === 401) {
          clearSession()
          throw loginExpired(e.detail)
        }
        throw e
      })
  })
}

function get(path, data, options) {
  return request('GET', path, data, options)
}

function post(path, data, options) {
  return request('POST', path, data, options)
}

function del(path, data, options) {
  return request('DELETE', path, data, options)
}

function getUrl(url) {
  return new Promise((resolve, reject) => {
    const w = wxApi()
    if (!w || typeof w.request !== 'function') {
      reject(new ApiError('当前环境不支持网络请求', 0, 'NO_WX'))
      return
    }
    w.request({
      url,
      method: 'GET',
      header: { 'X-Client': 'mini' },
      timeout: 6000,
      success(res) {
        if (res.statusCode >= 200 && res.statusCode < 300) resolve(res.data)
        else reject(new ApiError('HTTP ' + res.statusCode, res.statusCode, 'HTTP_ERROR', res.data))
      },
      fail(err) { reject(new ApiError(friendly(err && err.errMsg), 0, 'NETWORK', (err && err.errMsg) || null)) },
    })
  })
}

module.exports = {
  get, post, del, getUrl,
  request, refreshSession,
  getSession, setSession, clearSession, currentUser,
  ApiError, STORAGE_KEYS,
}
