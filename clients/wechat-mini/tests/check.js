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

  console.log(`mini check ok: ${js} JS, ${json} JSON, ${wxml} WXML, appid ${project.appid}`)
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

main()
