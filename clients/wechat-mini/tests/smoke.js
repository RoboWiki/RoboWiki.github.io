// 官方 miniprogram-automator：连接本机微信开发者工具，跑核心只读路径。
// 前置：开发者工具已登录，且「设置 → 安全设置 → 服务端口」已开启。
// 用法：cd clients/wechat-mini/tests && npm i && npm test
const path = require('path')
const automator = require('miniprogram-automator')

const CLI = process.env.WECHAT_CLI || 'D:/微信web开发者工具/cli.bat'
const PROJECT = process.env.MINI_PROJECT || path.resolve(__dirname, '..')
const WS = process.env.WECHAT_WS

function assert(ok, message) {
  if (!ok) throw new Error(message)
}

async function main() {
  let mini
  try {
    mini = WS
      ? await automator.connect({ wsEndpoint: WS })
      : await automator.launch({
        cliPath: CLI,
        projectPath: PROJECT,
        timeout: 90000,
      })

    console.log('connected')
    let page = await mini.reLaunch('/pages/index/index')
    console.log('reLaunch index')
    await page.waitFor(1800)
    let data = await page.data()
    assert(data.items && data.items.length > 0, '首页没有加载到部件')
    console.log(`index: ${data.items.length}/${data.total} 条，版本 ${data.version || '—'}`)

    const cats = await page.$$('.cat')
    assert(cats.length > 1, '首页没有品类筛选')
    await cats[1].tap()
    await page.waitFor(1200)
    data = await page.data()
    assert(data.category, '点击品类后 category 没有变化')
    assert(data.items.length > 0, `品类 ${data.category} 没有结果`)
    console.log(`filter: ${data.category} -> ${data.items.length} 条`)

    const input = await page.$('.search')
    await input.input('XT30')
    await page.waitFor(1500)
    data = await page.data()
    assert(data.items.length > 0, '搜索 XT30 没有结果')
    console.log(`search: XT30 -> ${data.items.length} 条`)

    const cards = await page.$$('.item')
    await cards[0].tap()
    await page.waitFor(1800)
    page = await mini.currentPage()
    assert(page.path === 'pages/part/part', `详情页路径不对：${page.path}`)
    const part = await page.data()
    assert(part.part && part.part.title, '部件详情没有加载')
    assert(part.rows && part.rows.length > 0, '部件详情没有参数行')
    const share = await page.callMethod('onShareAppMessage')
    assert(share && share.title, '部件详情分享标题为空')
    console.log(`part: ${part.part.title} · ${part.rows.length} 行参数 · 分享「${share.title}」`)

    // 材质库是首页里的 Tab，不再有独立 pages/materials 页。
    await page.callMethod('switchTab', {
      currentTarget: { dataset: { tab: 'materials' } },
    })
    await page.waitFor(1800)
    const mats = await page.data()
    assert(mats.items && mats.items.length > 0, '材质列表没有加载')
    console.log(`materials: ${mats.items.length}/${mats.total} 条`)

    const mcards = await page.$$('.item')
    await mcards[0].tap()
    await page.waitFor(1800)
    page = await mini.currentPage()
    assert(page.path === 'pages/material/material', `材质详情页路径不对：${page.path}`)
    const material = await page.data()
    assert(material.item && material.item.name, '材质详情没有加载')
    console.log(`material: ${material.item.name} · ${material.rows.length} 行参数`)

    await page.callMethod('copyLink')
    await page.waitFor(500)
    console.log('copy: 已触发网页链接复制')

    await mini.close()
    console.log('smoke ok')
  } finally {
    if (mini) {
      try { await mini.disconnect() } catch (e) {}
    }
  }
}

main().catch(err => {
  console.error('smoke failed:', err && err.message ? err.message : err)
  process.exit(1)
})
