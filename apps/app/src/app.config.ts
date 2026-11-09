import { APP_TABS } from '@robowiki/content'

export default defineAppConfig({
  pages: [
    // 首页放在第一位：冷启动直接进现场助手，而不是目录。
    'pages/home/index',
    'pages/index/index',
    'pages/builds/index',
    'pages/community/index',
    'pages/account/index',
    // 非 tab 页面
    'pages/layers/index',
    'pages/part/index',
    'pages/build/index',
    'pages/post/index',
    'pages/compare/index',
    'pages/learn/index',
    'pages/login/index',
    'pages/login/confirm/index',
    'pages/submit/index',
    'pages/compose/index',
  ],
  tabBar: {
    color: '#667085',
    selectedColor: '#2563eb',
    backgroundColor: '#ffffff',
    borderStyle: 'white',
    // 不引入图标依赖：微信小程序 tabBar 的 iconPath 是可选项，纯文字即可构建。
    list: APP_TABS.map((tab) => ({
      pagePath: tab.pagePath,
      text: tab.label,
    })),
  },
  window: {
    backgroundTextStyle: 'dark',
    navigationBarBackgroundColor: '#ffffff',
    navigationBarTitleText: 'RoboWiki',
    navigationBarTextStyle: 'black',
    backgroundColor: '#f7f8fb',
  },
})
