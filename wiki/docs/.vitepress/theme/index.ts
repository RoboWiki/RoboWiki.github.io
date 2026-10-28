// 主题：默认主题 + 每页底部的讨论串（giscus）。
// 参考 YunQianDoc 的 theme/index.ts（doc-before / layout-bottom 插槽用法），
// 这里只占 doc-after 一个插槽，把评论放在正文之后。
import { h } from 'vue'
import type { Theme } from 'vitepress'
import DefaultTheme from 'vitepress/theme'
import PageComments from '../components/PageComments.vue'
import PartExplorer from '../components/PartExplorer.vue'
import SupplierList from '../components/SupplierList.vue'
import ContributorGrid from '../components/ContributorGrid.vue'
import PartRating from '../components/PartRating.vue'
import './custom.css'
import './part.css'

export default {
  extends: DefaultTheme,
  Layout() {
    return h(DefaultTheme.Layout, null, {
      'doc-after': () => h(PageComments),
    })
  },
  enhanceApp({ app }) {
    app.component('PageComments', PageComments)
    app.component('PartExplorer', PartExplorer)
    app.component('SupplierList', SupplierList)
    app.component('ContributorGrid', ContributorGrid)
    app.component('PartRating', PartRating)
  },
} satisfies Theme
