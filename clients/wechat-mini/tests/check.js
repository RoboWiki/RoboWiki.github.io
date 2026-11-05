// 小程序静态检查：JS 语法、JSON 可解析、WXML 标签闭合、AppID 形态。
// 不依赖 npm 包也不调用微信开发者工具，适合放进 PR 门禁。
const fs = require('fs')
const path = require('path')
const { execFileSync } = require('child_process')

const ROOT = path.resolve(__dirname, '..')

function walk(dir, out = []) {
  for (const name of fs.readdirSync(dir)) {
    if (name === 'node_modules' || name.startsWith('.')) continue
    const p = path.join(dir, name)
    const st = fs.statSync(p)
    if (st.isDirectory()) walk(p, out)
    else out.push(p)
  }
  return out
}

function checkJs(file) {
  execFileSync(process.execPath, ['--check', file], { stdio: 'pipe' })
}

function checkJson(file) {
  JSON.parse(fs.readFileSync(file, 'utf8'))
}

function checkWxml(file) {
  const src = fs.readFileSync(file, 'utf8').replace(/<!--[\s\S]*?-->/g, '')
  const tag = /<\/?([a-zA-Z][\w:-]*)((?:"[^"]*"|'[^']*'|[^>"'])*)>/g
  const stack = []
  let m
  while ((m = tag.exec(src)) !== null) {
    const [whole, name, attrs] = m
    const closing = whole.startsWith('</')
    const selfClosing = /\/\s*$/.test(attrs)
    if (closing) {
      const top = stack.pop()
      if (top !== name) {
        throw new Error(`${file}: </${name}> 与 <${top || '空'}> 不匹配`)
      }
    } else if (!selfClosing) {
      stack.push(name)
    }
  }
  if (stack.length) {
    throw new Error(`${file}: 有未闭合标签 ${stack.join(', ')}`)
  }
}

function main() {
  const files = walk(ROOT)
  let js = 0
  let json = 0
  let wxml = 0
  for (const file of files) {
    const ext = path.extname(file)
    if (ext === '.js') {
      checkJs(file)
      js += 1
    } else if (ext === '.json') {
      checkJson(file)
      json += 1
    } else if (ext === '.wxml') {
      checkWxml(file)
      wxml += 1
    }
  }

  const project = JSON.parse(fs.readFileSync(path.join(ROOT, 'project.config.json'), 'utf8'))
  if (!/^wx[0-9a-z]{16}$/.test(project.appid || '')) {
    throw new Error(`project.config.json 的 appid 形态不对：${project.appid}`)
  }

  checkConfigAndShare()
  checkNoSecrets(files)
  checkPartComments()

  return checkApiAuth().then(() => {
    console.log(`mini check ok: ${js} JS, ${json} JSON, ${wxml} WXML, appid ${project.appid}`)
  })
}

function assert(ok, message) {
  if (!ok) throw new Error(message)
}

/**
 * Bearer / refresh / 统一错误是写入路径的地基，不该只靠人工点。
 * 这里用假 wx 走真实 api.js：401 → 只刷新一次 → 重放一次；刷新失败清会话。
 */
function checkApiAuth() {
  const store = {}
  const calls = []
  let refreshMode = 'ok'
  global.wx = {
    getStorageSync(key) {
      return Object.prototype.hasOwnProperty.call(store, key) ? store[key] : ''
    },
    setStorageSync(key, value) { store[key] = value },
    removeStorageSync(key) { delete store[key] },
    getAccountInfoSync() { return { miniProgram: { envVersion: 'develop' } } },
    login(opts) { opts.success({ code: 'wx-code-1' }) },
    request(opts) {
      const auth = (opts.header && (opts.header.Authorization || opts.header.authorization)) || ''
      calls.push({ url: opts.url, method: opts.method, auth, data: opts.data })
      if (/\/auth\/wechat\/mini$/.test(opts.url)) {
        opts.success({
          statusCode: 200,
          data: {
            access_token: 'access-login',
            refresh_token: 'refresh-login',
            user: { handle: 'wx-1', display_name: '微信用户' },
          },
          header: {},
        })
        return
      }
      if (/\/auth\/logout$/.test(opts.url)) {
        opts.success({ statusCode: 200, data: { ok: true, revoked: 1 }, header: {} })
        return
      }
      if (/\/auth\/refresh$/.test(opts.url)) {
        if (refreshMode === 'fail') {
          opts.success({ statusCode: 401, data: { detail: '登录会话已失效' }, header: {} })
        } else {
          opts.success({
            statusCode: 200,
            data: {
              access_token: 'access-2',
              refresh_token: 'refresh-2',
              user: { handle: 'wx-mini', display_name: '微信用户' },
            },
            header: {},
          })
        }
        return
      }
      if (opts.method === 'POST' && /\/ratings\//.test(opts.url)) {
        opts.success({ statusCode: 201, data: { created: true }, header: {} })
      } else if (opts.method === 'DELETE') {
        opts.success({ statusCode: 204, data: '', header: {} })
      } else if (auth === 'Bearer access-2') {
        opts.success({ statusCode: 200, data: { ok: true }, header: {} })
      } else if (auth === 'Bearer access-1') {
        opts.success({ statusCode: 401, data: { detail: '过期' }, header: {} })
      } else {
        opts.success({ statusCode: 401, data: { detail: '未登录' }, header: {} })
      }
    },
  }

  const apiPath = path.join(ROOT, 'utils', 'api.js')
  delete require.cache[require.resolve(apiPath)]
  const api = require(apiPath)

  api.setSession({ access_token: 'access-1', refresh_token: 'refresh-1', user: { handle: 'wx-mini' } })
  return api.get('/parts/x')
    .then(got => {
      assert(got && got.ok, '401 后 refresh 重试没有成功')
      assert(calls.length === 3, `401 重试应发出 3 个请求，实际 ${calls.length}`)
      assert(calls[0].auth === 'Bearer access-1', '第一次请求没有带旧 Bearer')
      assert(!calls[1].auth, '/auth/refresh 不应带 Bearer')
      assert(calls[1].data.refresh_token === 'refresh-1', 'refresh 没有带轮换前的 token')
      assert(calls[2].auth === 'Bearer access-2', '重放请求没有换成新 Bearer')
      assert(api.getSession().access_token === 'access-2', '新 access 没有写入 Storage')
      assert(api.getSession().refresh_token === 'refresh-2', '轮换后的 refresh 没有写入 Storage')
      assert(api.getSession().user.handle === 'wx-mini', '用户资料没有保留')
      console.log('api: Bearer + 401 refresh 单次重试通过')

      calls.length = 0
      return api.post('/ratings/cubemars-ak80-6', { score: 5, own_hardware: true, note: '好' })
    })
    .then(posted => {
      assert(posted && posted.created === true, 'POST 响应没有透传')
      assert(calls[0].method === 'POST', 'POST 方法没有发出去')
      assert(calls[0].data.score === 5 && calls[0].data.own_hardware === true, 'POST body 不完整')
      calls.length = 0
      return api.del('/ratings/cubemars-ak80-6')
    })
    .then(() => {
      assert(calls[0].method === 'DELETE', 'DELETE 方法没有发出去')
      console.log('api: POST / DELETE 通过')

      // 并发 401 必须共用同一次 refresh：后端 refresh 是一次性轮换，
      // 各刷一次会触发复用检测、整条会话链被撤销。
      api.setSession({ access_token: 'access-old', refresh_token: 'refresh-old' })
      refreshMode = 'ok'
      calls.length = 0
      return Promise.all([api.get('/parts/a'), api.get('/parts/b')])
    })
    .then(() => {
      const refreshes = calls.filter(c => /\/auth\/refresh$/.test(c.url))
      assert(refreshes.length === 1, `并发 401 应只刷新一次，实际 ${refreshes.length}`)
      console.log('api: 并发 401 共用一次 refresh')

      api.setSession({ access_token: 'access-1', refresh_token: 'refresh-bad' })
      refreshMode = 'fail'
      return api.get('/parts/z').then(
        () => { throw new Error('refresh 失败时不应成功') },
        err => err,
      )
    })
    .then(err => {
      assert(err && err.status === 401, 'refresh 失败应返回 401')
      assert(/登录/.test(err.message), 'refresh 失败提示应说明需要重新登录')
      const s = api.getSession()
      assert(!s.access_token && !s.refresh_token, 'refresh 失败应清空本地会话')
      console.log('api: refresh 失败清理会话')
      return checkAuthLogin(store, calls, api)
    })
}

/** 登录只该写 access / refresh / user；不保存微信会话密钥或 openid 原文。 */
function checkAuthLogin(store, calls, api) {
  Object.keys(store).forEach(k => delete store[k])
  calls.length = 0
  const authPath = path.join(ROOT, 'utils', 'auth.js')
  delete require.cache[require.resolve(authPath)]
  const auth = require(authPath)

  return auth.login()
    .then(user => {
      assert(user && user.handle === 'wx-1', '登录后没有返回用户资料')
      assert(calls[0] && /\/auth\/wechat\/mini$/.test(calls[0].url), '没有调用 /auth/wechat/mini')
      assert(calls[0].data.code === 'wx-code-1', 'wx.login 的 code 没有带进请求')
      assert(!calls[0].auth, '登录请求不该带 Bearer')
      const s = api.getSession()
      assert(s.access_token === 'access-login', '登录后 access 没写入 Storage')
      assert(s.refresh_token === 'refresh-login', '登录后 refresh 没写入 Storage')
      const keys = Object.keys(store).sort()
      assert(keys.length === 3, `登录只应存 3 个键，实际 ${keys.join(',')}`)
      assert(!keys.some(k => /secret|session_key|openid/i.test(k)), 'Storage 出现不该保存的密钥字段')
      return auth.logout()
    })
    .then(() => {
      const logout = calls.find(c => /\/auth\/logout$/.test(c.url))
      assert(logout && logout.data.refresh_token === 'refresh-login', '退出没有撤销当前 refresh')
      const s = api.getSession()
      assert(!s.access_token && !s.refresh_token && !s.user, '退出后本地会话没有清空')
      console.log('auth: wx.login → /auth/wechat/mini，只存 3 键；退出撤销 refresh')
    })
}

/** 小程序包是公开的：任何应用密钥、微信会话密钥都不该出现在源码里。 */
function checkNoSecrets(files) {
  const bad = /(appsecret|app_secret|wechat_mp_secret|session_key)/i
  for (const file of files) {
    if (!/\.(js|json|wxml)$/i.test(file)) continue
    if (file.split(path.sep).includes('tests')) continue
    const src = fs.readFileSync(file, 'utf8')
    if (bad.test(src)) {
      throw new Error(`${file} 含有不该进客户端的密钥 / 会话字段`)
    }
  }
}

/**
 * 讨论配图分段与归属是纯逻辑：本站 /api/v1/media/<id> 切图片，
 * 外链保持文本；评论只按 handle 判定「是不是我」。用 Page() 捕获页面定义，
 * 不需要微信运行时。
 */
function checkPartComments() {
  const pagePath = path.join(ROOT, 'pages', 'part', 'part.js')
  let page = null
  global.Page = def => { page = def }
  try {
    delete require.cache[require.resolve(pagePath)]
    require(pagePath)
  } finally {
    delete global.Page
  }
  assert(page && typeof page.buildComments === 'function', 'part.js 没有 buildComments')

  const id = '0123456789abcdef0123456789abcdef'
  const rows = [
    {
      id: 1, body: '看图 /api/v1/media/' + id + ' 结束', status: 'visible',
      created_at: '2026-01-01T00:00:00Z',
      author: { handle: 'wx-1', display_name: '我' },
    },
    {
      id: 2, body: '外链 https://evil.example/api/v1/media/' + id, status: 'visible',
      created_at: '2026-01-01T00:00:00Z',
      author: { handle: 'wx-2', display_name: '别人' },
    },
  ]
  const out = page.buildComments(rows, 'wx-1')
  const mine = out.find(c => c.id === 1)
  const other = out.find(c => c.id === 2)
  assert(mine.segments.some(s => s.type === 'image'), '本站媒体 URL 没有切成图片')
  assert(mine.segments.some(s => s.type === 'text' && /结束/.test(s.text)), '图片前后的文本丢了')
  assert(mine.segments.some(s => s.type === 'image' && s.src === configApi() + '/media/' + id),
    '图片 src 没有指向当前 API')
  assert(!other.segments.some(s => s.type === 'image'), '外链媒体 URL 不应渲染成图片')
  assert(mine.canDelete === true && other.canDelete === false, '评论归属判断不对')
  console.log('comments: 本站配图分段 / 归属判断通过')
}

function configApi() {
  return require(path.join(ROOT, 'config.js')).API
}

/** 环境映射与分享 URL 是契约，不该只靠 README 口述。 */
function checkConfigAndShare() {
  const config = require(path.join(ROOT, 'config.js'))
  const want = [
    ['develop', config.LOCAL],
    ['trial', config.PROD],
    ['release', config.PROD],
  ]
  for (const [env, base] of want) {
    if (config.baseFor(env) !== base) {
      throw new Error(`config.baseFor(${env}) 应为 ${base}，实际 ${config.baseFor(env)}`)
    }
  }
  if (config.PROD !== 'https://robowiki.org.cn') {
    throw new Error(`正式版主域应为 https://robowiki.org.cn，实际 ${config.PROD}`)
  }
  if (!/^http:\/\/(127\.0\.0\.1|localhost):\d+$/.test(config.LOCAL)) {
    throw new Error(`开发版应连本机，实际 ${config.LOCAL}`)
  }

  const F = require(path.join(ROOT, 'utils', 'format.js'))
  const partJson = F.sharePartUrl({
    id: 'cubemars-ak80-6', category: 'actuator',
    web_path: '/parts/actuator/cubemars-ak80-6.html',
  })
  if (!/\/share\/parts\/actuator\/cubemars-ak80-6\.json$/.test(partJson)) {
    throw new Error(`部件分享 JSON 路径不对：${partJson}`)
  }
  const matJson = F.shareMaterialUrl({
    id: 'mat-alu-6061-t6', category: 'material',
    web_path: '/materials/alu-6061-t6.html',
  })
  if (!/\/share\/materials\/alu-6061-t6\.json$/.test(matJson)) {
    throw new Error(`材质分享 JSON 路径不对：${matJson}`)
  }
}

main().catch(err => {
  console.error('mini check failed:', err && err.message ? err.message : err)
  process.exit(1)
})
