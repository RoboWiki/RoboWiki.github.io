#!/usr/bin/env node
/**
 * 构建产物自检：证明「同一份构建」在 github.io 上确实把 API 指向主域。
 *
 * 用法（需先 npm run build，产物在 docs/.vitepress/dist）：
 *   node scripts/check-api-base.mjs
 *
 * 做法不是读文档，而是把真实的 lib/api.ts 用 esbuild 打成 ESM，
 * 在模拟的 window.location.hostname 下执行 apiBase()/apiFetch()：
 *   · github.io          → https://robowiki.org.cn/api/v1
 *   · robowiki.org.cn    → /api/v1（同源）
 *   · localhost / dev    → /api/v1
 *   · 运行时注入 / 构建环境变量优先级
 * 再检查 dist：CSP meta、sw.js 的 NetworkOnly、bundle 里的主域常量。
 *
 * 只做静态/模拟检查，不启动服务、不发真实请求。
 */
import { build } from 'esbuild'
import { readFile, readdir } from 'node:fs/promises'
import { existsSync } from 'node:fs'
import path from 'node:path'
import { fileURLToPath } from 'node:url'

const here = path.dirname(fileURLToPath(import.meta.url))
const root = path.resolve(here, '..')
const apiEntry = path.join(root, 'docs/.vitepress/lib/api.ts')
const componentsDir = path.join(root, 'docs/.vitepress/components')
const distDir = path.join(root, 'docs/.vitepress/dist')

const PRIMARY_API = 'https://robowiki.org.cn/api/v1'
const MIRROR = 'robowiki.github.io'

const failures = []
const checks = []
function ok(name, extra = '') {
  checks.push(`  PASS  ${name}${extra ? `  ${extra}` : ''}`)
}
function fail(name, detail) {
  checks.push(`  FAIL  ${name}  ${detail}`)
  failures.push(`${name}: ${detail}`)
}

/* ── 浏览器环境桩 ──────────────────────────────────────────────────────── */

const store = new Map()
const windowStub = {
  location: {
    hostname: MIRROR,
    origin: `https://${MIRROR}`,
    hash: '',
    pathname: '/login',
    search: '',
  },
  history: { replaceState() {} },
}
globalThis.window = windowStub
globalThis.localStorage = {
  getItem: k => (store.has(k) ? store.get(k) : null),
  setItem: (k, v) => store.set(k, String(v)),
  removeItem: k => store.delete(k),
}

/* ── 用真实源码构建可执行模块 ──────────────────────────────────────────── */

async function loadApi(envValue) {
  const result = await build({
    entryPoints: [apiEntry],
    bundle: true,
    write: false,
    format: 'esm',
    platform: 'browser',
    target: 'es2022',
    define: {
      // 构建期变量：Vite 在 build 时把未设置的 VITE_* 替换成 undefined
      'import.meta.env.VITE_ROBOWIKI_API': envValue === undefined
        ? 'undefined'
        : JSON.stringify(envValue),
    },
  })
  const code = result.outputFiles[0].text
  const url = `data:text/javascript;base64,${Buffer.from(code).toString('base64')}`
  return import(url)
}

function setHost(hostname) {
  windowStub.location.hostname = hostname
  windowStub.location.origin = `https://${hostname}`
  windowStub.__ROBOWIKI_API__ = undefined
}

/* ── 1. base 解析 ──────────────────────────────────────────────────────── */

const api = await loadApi()

setHost(MIRROR)
const mirrorBase = api.apiBase()
mirrorBase === PRIMARY_API
  ? ok('github.io → 主域 API', mirrorBase)
  : fail('github.io → 主域 API', `得到 ${mirrorBase}，期望 ${PRIMARY_API}`)

setHost('robowiki.org.cn')
const mainBase = api.apiBase()
mainBase === '/api/v1'
  ? ok('robowiki.org.cn → 同源', mainBase)
  : fail('robowiki.org.cn → 同源', `得到 ${mainBase}`)

setHost('localhost')
const localBase = api.apiBase()
localBase === '/api/v1'
  ? ok('localhost → 同源（dev proxy）', localBase)
  : fail('localhost → 同源（dev proxy）', `得到 ${localBase}`)

setHost(MIRROR)
windowStub.__ROBOWIKI_API__ = 'https://staging.example.com/api/v9/'
const injected = api.apiBase()
injected === 'https://staging.example.com/api/v9'
  ? ok('window.__ROBOWIKI_API__ 优先级最高', injected)
  : fail('window.__ROBOWIKI_API__ 优先级最高', `得到 ${injected}`)
windowStub.__ROBOWIKI_API__ = undefined

/* ── 2. 构建期变量 ─────────────────────────────────────────────────────── */

const apiWithEnv = await loadApi('https://env.example.com/api/v2')
setHost(MIRROR)
const envBase = apiWithEnv.apiBase()
envBase === 'https://env.example.com/api/v2'
  ? ok('VITE_ROBOWIKI_API 覆盖 hostname 推导', envBase)
  : fail('VITE_ROBOWIKI_API 覆盖 hostname 推导', `得到 ${envBase}`)

/* ── 3. apiFetch：URL / Bearer / 401 清 token / 断网文案 ───────────────── */

setHost(MIRROR)
const realFetch = globalThis.fetch
let lastUrl = ''
let lastInit
globalThis.fetch = async (url, init) => {
  lastUrl = String(url)
  lastInit = init
  return new Response(JSON.stringify({ ok: true }), {
    status: 200,
    headers: { 'content-type': 'application/json' },
  })
}
localStorage.setItem('roboselect.token', 'tok-123')
await api.apiFetch('/auth/me')
lastUrl === `${PRIMARY_API}/auth/me`
  ? ok('apiFetch 在 github.io 上拼主域 URL', lastUrl)
  : fail('apiFetch 在 github.io 上拼主域 URL', `得到 ${lastUrl}`)
const authHeader = new Headers(lastInit?.headers).get('authorization')
authHeader === 'Bearer tok-123'
  ? ok('apiFetch 自动带 Bearer', authHeader)
  : fail('apiFetch 自动带 Bearer', `得到 ${authHeader}`)

globalThis.fetch = async () => new Response(
  JSON.stringify({ detail: 'Not authenticated' }),
  { status: 401, headers: { 'content-type': 'application/json' } },
)
let authErr
try { await api.apiFetch('/auth/me') } catch (e) { authErr = e }
authErr?.status === 401 && authErr?.message === api.MSG_AUTH
  ? ok('401 统一文案 + 清 token', `"${authErr.message}"`)
  : fail('401 统一文案 + 清 token', `status=${authErr?.status} msg=${authErr?.message}`)
localStorage.getItem('roboselect.token') === null
  ? ok('401 后 token 已清除')
  : fail('401 后 token 已清除', 'localStorage 仍有 roboselect.token')

// 登录接口的 401 带业务原因（中文），不能被统一文案吞掉
globalThis.fetch = async () => new Response(
  JSON.stringify({ detail: '账号或密码不对' }),
  { status: 401, headers: { 'content-type': 'application/json' } },
)
let loginErr
try { await api.apiFetch('/auth/login', { method: 'POST', body: '{}' }) } catch (e) { loginErr = e }
loginErr?.message === '账号或密码不对'
  ? ok('登录 401 保留后端业务文案', `"${loginErr.message}"`)
  : fail('登录 401 保留后端业务文案', `得到 "${loginErr?.message}"`)

globalThis.fetch = async () => { throw new TypeError('Failed to fetch') }
let netErr
try { await api.apiFetch('/wiki/comments') } catch (e) { netErr = e }
netErr?.kind === 'network' && /主站|网络/.test(netErr.message)
  ? ok('断网 → 统一网络文案（镜像提到快照）', `"${netErr.message}"`)
  : fail('断网 → 统一网络文案', `${netErr?.kind} ${netErr?.message}`)

/* ── 3b. 401 并发刷新：只发一次 refresh，且保留 JSON Content-Type ────────── */
localStorage.setItem('roboselect.token', 'old-access')
localStorage.setItem('roboselect.refresh', 'old-refresh')
let refreshCalls = 0
let retryContentType = ''
let retryAuth = ''
globalThis.fetch = async (url, init) => {
  const u = String(url)
  if (u.endsWith('/auth/refresh')) {
    refreshCalls++
    return new Response(JSON.stringify({
      access_token: 'new-access', refresh_token: 'new-refresh',
    }), { status: 200, headers: { 'content-type': 'application/json' } })
  }
  const h = new Headers(init?.headers)
  if (h.get('authorization') === 'Bearer old-access') {
    return new Response(JSON.stringify({ detail: 'expired' }), {
      status: 401, headers: { 'content-type': 'application/json' },
    })
  }
  retryAuth = h.get('authorization') || ''
  retryContentType = h.get('content-type') || ''
  return new Response(JSON.stringify({ ok: true }), {
    status: 200, headers: { 'content-type': 'application/json' },
  })
}
const parallel = await Promise.allSettled([
  api.apiFetch('/wiki/comments', { method: 'POST', body: JSON.stringify({ body: 'a' }) }),
  api.apiFetch('/wiki/comments', { method: 'POST', body: JSON.stringify({ body: 'b' }) }),
])
parallel.every(x => x.status === 'fulfilled')
  ? ok('并发 401 后两个请求都重试成功')
  : fail('并发 401 后重试', JSON.stringify(parallel))
refreshCalls === 1
  ? ok('并发 401 只刷新一次（避免 refresh 重放）')
  : fail('并发刷新次数', `${refreshCalls} 次`)
retryAuth === 'Bearer new-access'
  ? ok('重试使用新 access token')
  : fail('重试 Authorization', retryAuth)
retryContentType.includes('application/json')
  ? ok('重试保留 JSON Content-Type')
  : fail('重试 Content-Type', retryContentType || '缺失')
localStorage.getItem('roboselect.refresh') === 'new-refresh'
  ? ok('刷新后的 refresh token 已落盘')
  : fail('refresh token 落盘', String(localStorage.getItem('roboselect.refresh')))
localStorage.removeItem('roboselect.token')
localStorage.removeItem('roboselect.refresh')

// 刷新请求断网：不能把用户误登出，也不能丢 refresh。
localStorage.setItem('roboselect.token', 'old-access-2')
localStorage.setItem('roboselect.refresh', 'old-refresh-2')
globalThis.fetch = async (url) => {
  if (String(url).endsWith('/auth/refresh')) throw new TypeError('Failed to fetch')
  return new Response(JSON.stringify({ detail: 'expired' }), {
    status: 401, headers: { 'content-type': 'application/json' },
  })
}
let refreshNetErr
try { await api.apiFetch('/auth/me') } catch (e) { refreshNetErr = e }
refreshNetErr?.kind === 'network'
  && localStorage.getItem('roboselect.refresh') === 'old-refresh-2'
  ? ok('刷新遇到断网 → 网络错误且保留会话')
  : fail('刷新断网处理',
    `kind=${refreshNetErr?.kind} refresh=${localStorage.getItem('roboselect.refresh')}`)
localStorage.removeItem('roboselect.token')
localStorage.removeItem('roboselect.refresh')

globalThis.fetch = realFetch

/* ── 4. 探活打 base + /health ──────────────────────────────────────────── */

setHost(MIRROR)
api.resetApiProbe()
let healthUrl = ''
globalThis.fetch = async (url) => {
  healthUrl = String(url)
  return new Response('{"ok":true}', { status: 200, headers: { 'content-type': 'application/json' } })
}
const alive = await api.apiAvailable()
globalThis.fetch = realFetch
alive === true && healthUrl === `${PRIMARY_API}/health`
  ? ok('apiAvailable 探测主域 /health', healthUrl)
  : fail('apiAvailable 探测主域 /health', `${healthUrl} → ${alive}`)

/* ── 5. 源码：4 个组件不再散落 /api/v1 或自己拼 base ───────────────────── */

const components = ['AuthPanel.vue', 'PageComments.vue', 'PartRating.vue', 'DataFix.vue']
function stripComments(src) {
  return src
    .replace(/\/\*[\s\S]*?\*\//g, '')
    .replace(/<!--[\s\S]*?-->/g, '')
    .split('\n')
    .map(line => line.replace(/(^|[^:])\/\/.*$/, '$1'))
    .join('\n')
}
for (const name of components) {
  const src = stripComments(await readFile(path.join(componentsDir, name), 'utf8'))
  if (src.includes('/api/v1')) fail(`组件 ${name} 仍硬编码 /api/v1`, '应统一走 lib/api')
  else ok(`组件 ${name} 无硬编码 /api/v1`)
  if (/VITE_ROBOWIKI_API/.test(src)) fail(`组件 ${name} 自行读取 VITE_ROBOWIKI_API`, '应在 lib/api')
  else ok(`组件 ${name} 不自行解析 API base`)
}

/* ── 6. dist：CSP / SW / bundle 常量 ──────────────────────────────────── */

if (!existsSync(distDir)) {
  fail('dist 产物存在', `${distDir} 不存在，先 npm run build`)
} else {
  const indexHtml = await readFile(path.join(distDir, 'index.html'), 'utf8')
  if (/http-equiv="Content-Security-Policy"/i.test(indexHtml)
    && /connect-src[^"]*https:\/\/robowiki\.org\.cn/.test(indexHtml)) {
    ok('dist/index.html 注入 CSP，connect-src 含主域')
  } else {
    fail('dist/index.html 注入 CSP', '缺 http-equiv 或 connect-src 不含 https://robowiki.org.cn')
  }

  const sw = await readFile(path.join(distDir, 'sw.js'), 'utf8')
  const swOk = sw.includes('NetworkOnly')
    && sw.includes('https://robowiki.org.cn')
    && sw.includes('/auth/')
    // workbox 会把 urlPattern 函数原样序列化：闭包变量在 SW 里不存在，绝不能漏进去
    && !sw.includes('API_ORIGIN')
  if (swOk) {
    ok('dist/sw.js 对 API/auth 使用 NetworkOnly（主域已内联）')
  } else {
    fail('dist/sw.js 对 API/auth 使用 NetworkOnly',
      '未找到 NetworkOnly + 主域字面量 + /auth/，或残留闭包标识符 API_ORIGIN')
  }

  async function jsFiles(dir) {
    const out = []
    for (const entry of await readdir(dir, { withFileTypes: true })) {
      const full = path.join(dir, entry.name)
      if (entry.isDirectory()) out.push(...await jsFiles(full))
      else if (entry.name.endsWith('.js')) out.push(full)
    }
    return out
  }
  // 压缩器会把 PRIMARY_API 折成 `${PRIMARY_ORIGIN}/api/v1`，所以不要求整串连续。
  // 同一 chunk 里同时出现「主域」「/api/v1」「github.io」才算条件分支真的进了产物。
  const js = await jsFiles(path.join(distDir, 'assets'))
  let found = false
  for (const file of js) {
    const code = await readFile(file, 'utf8')
    if (code.includes('https://robowiki.org.cn')
      && code.includes('/api/v1')
      && code.includes('robowiki.github.io')) { found = true; break }
  }
  found
    ? ok('dist JS 内含主域 + /api/v1 + github.io 分支', PRIMARY_API)
    : fail('dist JS 内含主域 API 常量', `assets 下未找到 主域 + /api/v1 + github.io 同处一个 chunk`)
}

/* ── 报告 ──────────────────────────────────────────────────────────────── */

console.log('\nRoboWiki API base / 镜像一致性检查\n')
console.log(checks.join('\n'))
console.log(`\n${checks.filter(c => c.includes('PASS')).length} passed, ${failures.length} failed\n`)

if (failures.length) {
  console.error('失败项：\n' + failures.map(f => ` - ${f}`).join('\n'))
  process.exit(1)
}
