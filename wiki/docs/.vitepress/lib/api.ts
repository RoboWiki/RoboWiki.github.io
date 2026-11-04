/**
 * 主站后端可用性探测。
 *
 * 本站**同一个构建**同时上两种部署：
 *   · robowiki.org.cn —— 有 FastAPI：评论、评分、纠错提交这些「写」的动作都在这里
 *   · robowiki.github.io —— 纯静态镜像：只有构建期生成的快照，没有任何 /api
 *
 * 因此动态功能一律先问一句「后端在不在」，不在就**降级隐藏**，
 * 而不是发起请求再显示一个 404 红字 —— 镜像端报错会被当成站点坏了。
 *
 * 探测走同源 `/api/v1/health`（不拼 base、不读环境变量）：
 *   · 静态站上是 404，捕获后返回 false
 *   · 主站上由反向代理转给 FastAPI，返回 {ok: true}
 *   · 本地 `npm run dev` 由 vite proxy 转到 127.0.0.1:8080（Docker API；
 *     直接跑 uvicorn 时用 ROBOWIKI_API_ORIGIN 覆盖）
 */

/** 有后端的主站；镜像端只做跳转，不做请求 */
export const PRIMARY_SITE = 'https://robowiki.org.cn'

/** 同源健康检查路由。不要改成 withBase(...)：API 挂在站点根，不在 /wiki/ 下 */
const HEALTH_PATH = '/api/v1/health'

/** 3s 够慢网探通；再慢就当没有，页面不能为了一个探测卡住 */
const PROBE_TIMEOUT_MS = 3000

/** 模块级缓存：一个页面里可能挂多个组件（评论 / 评分 / 纠错），只探一次 */
let probe: Promise<boolean> | null = null

async function probeOnce(): Promise<boolean> {
  try {
    const r = await fetch(HEALTH_PATH, {
      method: 'GET',
      headers: { Accept: 'application/json' },
      credentials: 'same-origin',
      cache: 'no-store',
      signal: AbortSignal.timeout(PROBE_TIMEOUT_MS),
    })
    return r.ok
  } catch {
    // 超时、断网、404、CORS、SW 拦截……一律视为「这里没有后端」
    return false
  }
}

/**
 * 后端是否可用。失败结果同样缓存 —— 镜像站永远没有后端，
 * 每次切换页面重探只会多出一串 404。
 */
export function apiAvailable(): Promise<boolean> {
  if (!probe) probe = probeOnce()
  return probe
}
