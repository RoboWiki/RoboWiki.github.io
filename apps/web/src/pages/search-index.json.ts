import type { APIRoute } from 'astro'
import { getCollection } from 'astro:content'
import { categoryLabel, parts } from '@/lib/catalog'
import robotsData from '@/data/robots.json'
import materialsData from '@/data/materials.json'
import softwareData from '@/data/software.json'
import suppliersData from '@/data/suppliers.json'

/**
 * 全站搜索索引（构建期生成，静态 JSON）。
 *
 * 之前搜索只能进部件库，整机、材质、工具、渠道、教程、竞赛全都搜不到。
 * 这里把七类条目摊平成同一个数组，前端只做字符串匹配，不引入依赖。
 *
 * 字段刻意取短名（k/t/d/u/x）以压缩体积：
 *   k 类型 · t 标题 · d 副标题 · u 地址 · x 额外可搜文本
 */
export const GET: APIRoute = async () => {
  const base = import.meta.env.BASE_URL
  const entries: Array<{ k: string; t: string; d: string; u: string; x: string }> = []

  for (const part of parts) {
    entries.push({
      k: 'part',
      t: part.model,
      d: `${part.vendor} · ${categoryLabel(part.category)}`,
      u: `${base}parts/${part.category}/${part.slug}.html`,
      x: [part.vendor, categoryLabel(part.category), part.subtypeLabel ?? '', part.tier ? `${part.tier} 级` : '', part.verified ? '已核对' : ''].join(' '),
    })
  }

  for (const robot of (robotsData.robots as unknown as Array<Record<string, any>>)) {
    entries.push({
      k: 'build',
      t: robot.title,
      d: `${robot.vendor_cn || robot.vendor} · ${robot.subtype_label ?? '整机方案'}`,
      u: `${base}builds/${robot._slug}.html`,
      x: [robot.vendor_cn, robot.vendor, robot.model, robot.subtype_label, robot.dof ? `${robot.dof} 自由度` : ''].filter(Boolean).join(' '),
    })
  }

  const materials = [...(materialsData.materials as any[]), ...(materialsData.processes as any[])]
  for (const material of materials) {
    entries.push({
      k: 'material',
      t: material.name,
      d: `${material.category === 'process' ? '加工工艺' : '材料'} · ${material.group_label ?? ''}`,
      u: `${base}${String(material._href ?? '').replace(/^\//, '')}`,
      x: [material.name_en, material.model, (material.aliases ?? []).join(' '), material.family_label].filter(Boolean).join(' '),
    })
  }

  for (const tool of (softwareData.items as any[])) {
    entries.push({
      k: 'tool',
      t: tool.name,
      d: `${tool.vendor} · ${tool.group ?? '工具'}`,
      u: `${base}tools.html`,
      x: [tool.lang, tool.license, tool.what, tool.when, tool.repo].filter(Boolean).join(' '),
    })
  }

  for (const supplier of (suppliersData.suppliers as any[])) {
    entries.push({
      k: 'supplier',
      t: supplier.display_name || supplier.name,
      d: `${supplier.category ?? '渠道'} · ${supplier.kind ?? ''}`,
      u: `${base}suppliers.html`,
      x: [supplier.name, supplier.channel, supplier.grade, supplier.process].filter(Boolean).join(' '),
    })
  }

  const learn = await getCollection('learn')
  for (const doc of learn) {
    entries.push({
      k: 'doc',
      t: doc.data.title,
      d: '指南',
      u: `${base}learn/${doc.id}.html`,
      x: doc.data.description ?? '',
    })
  }

  const competitions = await getCollection('competitions')
  for (const doc of competitions) {
    entries.push({
      k: 'doc',
      t: doc.data.title,
      d: '竞赛资料',
      u: `${base}competitions/${doc.id}.html`,
      x: doc.data.description ?? '',
    })
  }

  const standing = [
    { t: '学习路径', d: '从零到跑通，按天给判据', u: `${base}start.html`, x: '入门 教程 路径 新手' },
    { t: '电控 14 天路径', d: '接线 → CAN → 闭环 → 四轮联动', u: `${base}paths/electrical-14d.html`, x: '电机 电调 CAN PID 闭环 底盘' },
    { t: '部件对比', d: '2–4 个部件并排比较', u: `${base}compare.html`, x: '对比 选型 差异' },
    { t: '开源索引', d: '带仓库与许可的机型、部件、工具', u: `${base}open.html`, x: '开源 仓库 许可 GPL MIT 复现' },
    { t: '工具链', d: '仿真、固件、上位机与部署', u: `${base}tools.html`, x: '软件 工具 IDE ROS' },
    { t: '参数口径', d: '字段含义、单位与可比性', u: `${base}semantics.html`, x: '口径 单位 含义 参数' },
    { t: '方法与来源', d: '数据怎么来的、怎么核对', u: `${base}method.html`, x: '方法 来源 核对 可信度' },
    { t: '来源清单', d: '每个数字的出处等级', u: `${base}sources.html`, x: '来源 A 级 B 级 C 级' },
  ]
  for (const page of standing) {
    entries.push({ k: 'page', t: page.t, d: page.d, u: page.u, x: page.x })
  }

  // 去重：同一地址只保留第一条（例如工具都指向 /tools.html）。
  const seen = new Set<string>()
  const unique = entries.filter(entry => {
    const key = `${entry.k}|${entry.u}|${entry.t}`
    if (seen.has(key)) return false
    seen.add(key)
    return true
  })

  return new Response(JSON.stringify({ generated: new Date().toISOString().slice(0, 10), entries: unique }), {
    headers: { 'Content-Type': 'application/json; charset=utf-8' },
  })
}
