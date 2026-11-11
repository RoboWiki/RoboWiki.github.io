/** 看板娘的页面提示、动作反应与 driver.js 小圆点规则。改文案只动这里。 */

export type PageTip = { text: string; href?: string; label?: string }
export type GuideRule = { selector: string; title: string; text: string }

type Page = { test: RegExp; tips: PageTip[]; guides?: GuideRule[] }

export const WELCOME = '我是鲸鲸娘，社区来的；点我换条提示。'

export function greetingFor(hour: number): string {
  if (hour < 6) return '这个点还在；参数核完早点睡。'
  if (hour < 11) return '早；查件还是看方案？'
  if (hour < 18) return '下午好；查件还是看方案？'
  return '晚上好；核完参数再下单。'
}

export const REACTIONS = {
  select: ['记下了；数量按实际改。', '选好一个；供电和总线别漏。'],
  empty: ['没搜到；换个词。', '这条没有；放宽筛选试试。'],
  cleared: ['清空了，重新筛。'],
  exportBom: ['导出前把询价项核一遍。'],
  hintsOn: ['小圆点，点开看。'],
  hintsOff: ['收起来了。'],
  noHints: ['这页没有可点的提示。'],
  restored: ['我回来了。'],
} as const

const DEFAULT_TIPS: PageTip[] = [
  { text: '先搜型号，或者按品类筛。', href: '/catalog.html', label: '去部件库' },
  { text: '选型台是试验版；最终以部件库为准。', href: '/selector.html', label: '看选型台' },
]

const PAGES: Page[] = [
  {
    test: /^\/$/,
    tips: [
      { text: '先看资料和评价，别急着下单。', href: '/catalog.html', label: '去部件库' },
      { text: '数都有出处；null 是没公布。', href: '/method.html', label: '看方法' },
      { text: '均分不算数，看具体差评。', href: '/community.html', label: '去社区' },
    ],
  },
  {
    test: /^\/catalog/,
    tips: [
      { text: '先筛品类，再看来源和核对日期。' },
      { text: '对比最多 4 个，差异会标出来。', href: '/compare.html', label: '去对比' },
      { text: '价格和参数都可能过期；点进详情看核对时间。' },
    ],
    guides: [
      { selector: '[data-guide="catalog-search"]', title: '搜索', text: '型号、厂商、用途都能搜。' },
      { selector: '[data-guide="catalog-cats"]', title: '品类', text: '品类可叠加；点「全部」回去。' },
    ],
  },
  {
    test: /^\/parts\//,
    tips: [
      { text: '实际用过就写一句；没用过想买先看看别人踩的坑' },
      { text: 'null 是没公布，不是 0。' },
    ],
    guides: [
      { selector: '[data-guide="part-badges"]', title: '分类与层级', text: '品类、能力层、子类都在这。' },
      { selector: '#specs', title: '公开参数', text: '每格都有口径；null 是没公布。' },
      { selector: '[data-compare-add]', title: '加入对比', text: '最多 4 个；差异行会标出来。' },
    ],
  },
  {
    test: /^\/compare/,
    tips: [
      { text: '差异行看颜色；口径不同的别硬比。' },
      { text: '首列固定，左右滑看全部列。' },
    ],
  },
  {
    test: /^\/selector/,
    tips: [
      { text: '先定构型，再谈功能。' },
      { text: '试验版；最后回部件库核参数。', href: '/catalog.html', label: '去部件库' },
    ],
    guides: [
      { selector: '[data-guide="selector-model"]', title: '参考机型', text: '先挑一个 URDF 校验过的机型。' },
      { selector: '[data-guide="selector-roles"]', title: '角色清单', text: '每个角色先给虚拟件；参考选项自己挑。' },
    ],
  },
  {
    test: /^\/(builds|robots)/,
    tips: [
      { text: '先看 BOM，再看生态。' },
      { text: '没 BOM 就只能参考。' },
    ],
    guides: [
      { selector: '[data-guide="builds-search"]', title: '搜方案', text: '按构型、自由度或厂商搜。' },
    ],
  },
  {
    test: /^\/learn/,
    tips: [
      { text: '必看经典教程，等级+1' },
      { text: '机械组先读传动和结构。' },
    ],
    guides: [
      { selector: '#learn-search', title: '搜教程', text: '标题、来源、关键词都能搜。' },
      { selector: '#learn-grid', title: '卡片', text: '先看封面、页数和难度。' },
    ],
  },
  {
    test: /^\/suppliers/,
    tips: [
      { text: '先问开票和交期。' },
      { text: '同名店先看主体。' },
    ],
    guides: [
      { selector: '[data-guide="suppliers-search"]', title: '搜渠道', text: '按工艺、材料或地区筛。' },
    ],
  },
  {
    test: /^\/equipment/,
    tips: [
      { text: '工具按加工方式选，别买用不上的。' },
    ],
  },
  {
    test: /^\/(method|semantics|sources)/,
    tips: [
      { text: '口径看 semantics；TOPS 别硬比。' },
      { text: '参数带来源和核对日期；没出处的别引用。' },
    ],
  },
  {
    test: /^\/404/,
    tips: [
      { text: '这页没东西，回部件库翻。', href: '/catalog.html', label: '去部件库' },
      { text: '型号可能改名了，搜一下。', href: '/search.html', label: '去搜索' },
    ],
  },
  {
    test: /^\/community/,
    tips: [
      { text: '写实测，别写「好用」。' },
      { text: '装过机和没装过机分开算。' },
    ],
    guides: [
      { selector: '[data-guide="community-post"]', title: '发帖', text: '选型求助、踩坑、报价都能写。' },
    ],
  },
]

export function tipsFor(pathname: string): PageTip[] {
  const path = pathname.replace(/\/index\.html$/, '/').replace(/\.html$/, '')
  return PAGES.find(page => page.test.test(path))?.tips ?? DEFAULT_TIPS
}

export function guideRulesFor(pathname: string): GuideRule[] {
  const path = pathname.replace(/\/index\.html$/, '/').replace(/\.html$/, '')
  return PAGES.find(page => page.test.test(path))?.guides ?? []
}
