// 主题：默认主题 + 每页底部的讨论串（主站自托管 / 静态镜像 giscus）。
// 参考 YunQianDoc 的 theme/index.ts（doc-before / layout-bottom 插槽用法），
// 这里只占 doc-after 一个插槽，把评论放在正文之后。
import { defineAsyncComponent, h } from 'vue'
import { useRoute, type Theme } from 'vitepress'
import DefaultTheme from 'vitepress/theme'
import PageComments from '../components/PageComments.vue'
import AuthPanel from '../components/AuthPanel.vue'
import NotificationList from '../components/NotificationList.vue'
import ContributorGrid from '../components/ContributorGrid.vue'
import ShareBox from '../components/ShareBox.vue'
import DataFix from '../components/DataFix.vue'
import './custom.css'
import './part.css'
import './explorer.css'
import './material.css'

export default {
  extends: DefaultTheme,
  Layout() {
    const route = useRoute()
    // 按路由重挂载：ShareBox / DataFix 在 onMounted 里按 pathname 取当前部件，
    // 不随 VitePress 的客户端路由切换更新；不 remount 会把上一页的数据带过去。
    // 注意 route.data（useData().page）没有 path 字段，必须用 route.path。
    return h(DefaultTheme.Layout, null, {
      'doc-after': () => h('div', { key: route.path }, [
        h(ShareBox), h(DataFix), h(PageComments),
      ]),
    })
  },
  enhanceApp({ app }) {
    app.component('PageComments', PageComments)
    app.component('AuthPanel', AuthPanel)
    app.component('NotificationList', NotificationList)
    app.component('PartExplorer', defineAsyncComponent(() => import('../components/PartExplorer.vue')))
    app.component('SupplierList', defineAsyncComponent(() => import('../components/SupplierList.vue')))
    app.component('ContributorGrid', ContributorGrid)
    app.component('RobotGrid', defineAsyncComponent(() => import('../components/RobotGrid.vue')))
app.component('SoftwareGrid', defineAsyncComponent(() => import('../components/SoftwareGrid.vue')))
    app.component('MaterialGrid', defineAsyncComponent(() => import('../components/MaterialGrid.vue')))
    app.component('MaterialLibGrid', defineAsyncComponent(() => import('../components/MaterialLibGrid.vue')))
    app.component('ExplorerShell', defineAsyncComponent(() => import('../components/ExplorerShell.vue')))
        app.component('PartRating', defineAsyncComponent(() => import('../components/PartRating.vue')))
    app.component('ShareBox', ShareBox)
    app.component('DataFix', DataFix)
  },
} satisfies Theme
