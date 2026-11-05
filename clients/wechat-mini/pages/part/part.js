const api = require('../../utils/api')
const auth = require('../../utils/auth')
const F = require('../../utils/format')
const L = require('../../utils/labels')
const { text } = require('../../utils/text')

/** 群里的分享链接可能被手工改坏（% 不完整）。decode 失败时按原文查，别直接崩页面。 */
function safeDecode(v) {
  try { return decodeURIComponent(v || '') } catch (e) { return String(v || '') }
}

/**
 * 讨论页标识与网页 PageComments 同规则：VitePress 路径，去前导斜杠与 .html。
 * /parts/actuator/cubemars-ak80-6.html → parts/actuator/cubemars-ak80-6
 * 换标题不会掉讨论；改路径才会，和网页端是同一串讨论。
 */
function pageIdOf(p) {
  const web = p && p.web_path ? String(p.web_path) : ''
  if (web) return web.replace(/^\/+|\/+$/g, '').replace(/\.html$/, '')
  const slug = String((p && p.id) || '').replace(/[^A-Za-z0-9]+/g, '-')
  return 'parts/' + ((p && p.category) || 'unknown') + '/' + slug
}

function authorName(a) {
  return (a && (a.display_name || a.handle)) || '匿名'
}

function hue(a) {
  const n = Number(a && a.avatar_hue)
  return isFinite(n) ? n : 160
}

Page({
  data: {
    part: null,
    rows: [],
    derived: [],
    reviews: [],
    offers: [],
    sources: [],
    image: '',
    webUrl: '',
    tierLabel: '',
    tierNote: '',
    tierColor: '',
    priceLabel: '',
    basis: '',
    keySpecs: [],
    version: '',
    loading: true,
    error: '',
    timelinePreview: false,

    // 登录
    loggedIn: false,
    me: null,
    loginBusy: false,
    authError: '',

    // 评分：1–5 分 + 是否装过机 + 200 字备注，改分幂等（后端一条唯一记录）
    rating: null,
    ratingMine: null,
    ratingError: '',
    ratingNotice: '',
    ratingBusy: false,
    scoreOptions: [1, 2, 3, 4, 5],
    score: 0,
    ownHardware: false,
    ratingNote: '',

    // 讨论：与网页共用 /wiki/comments，登录后可发；接口不可用时保持只读
    comments: [],
    commentsLoading: false,
    commentsReadonly: false,
    commentError: '',
    commentNotice: '',
    commentBusy: false,
    commentBody: '',
    replyTo: null,
  },

  onLoad(query) {
    this.id = safeDecode(query.id)
    this.page = ''
    this.setData({ timelinePreview: Number(query.scene) === 1154 })
    this.syncAuth(false)
    this.load()
  },

  onShow() {
    // 从别处登录 / 退出后回来，按钮与可写状态要跟着变。
    if (this.data.part) this.syncAuth(true)
  },

  onPullDownRefresh() {
    this.load().then(() => wx.stopPullDownRefresh(), () => wx.stopPullDownRefresh())
  },

  syncAuth(reload) {
    const loggedIn = auth.isLoggedIn()
    const changed = loggedIn !== this.data.loggedIn
    this.setData({ loggedIn, me: auth.user() })
    if (changed && reload && this.data.part) {
      this.loadRating()
      this.loadComments()
    }
  },

  async load() {
    this.setData({ loading: true, error: '' })
    try {
      const p = await api.get('/parts/' + encodeURIComponent(this.id), { posts_kind: 'review', posts_limit: 5 })
      const t = F.tier(p.source_tier)
      const specs = p.specs || {}
      const hidden = ['image_url', 'image_source', 'doc_url', 'doc_pdf',
        'repo_urls', 'repo_license', 'tags', 'coupon', 'fetched_at', 'category_cn']
      const rows = Object.keys(specs)
        .filter(k => !hidden.includes(k))
        .filter(k => specs[k] !== null && specs[k] !== undefined && specs[k] !== '')
        .slice(0, 80)
        .map(k => ({ key: k, label: L.partLabel(k), value: text(specs[k]) }))

      const derived = Object.keys(p.derived || {})
        .filter(k => p.derived[k] !== null && p.derived[k] !== undefined)
        .map(k => ({
          key: k,
          label: L.DERIVED[k] || L.humanize(k),
          value: text(p.derived[k]),
        }))

      const reviews = (p.posts || [])
        .filter(x => x.kind === 'review')
        .slice(0, 3)
        .map(x => ({
          id: x.id,
          title: x.title,
          body: F.short(x.body, 100),
          rating: x.rating,
          score: x.score,
          author: x.author && x.author.display_name,
        }))

      const sources = []
      if (p.url) sources.push({ label: '厂商 / 商品页', url: p.url })
      if (specs.doc_url) sources.push({ label: '官方资料', url: specs.doc_url })
      if (specs.doc_pdf) sources.push({ label: '官方手册 PDF', url: specs.doc_pdf })

      let basis = ''
      if (specs.tau_basis) basis += '扭矩口径：' + (specs.tau_basis === 'peak' ? '峰值' : specs.tau_basis === 'rated' ? '额定' : specs.tau_basis) + '；'
      if (specs.inertia_basis) basis += '惯量口径：' + (specs.inertia_basis === 'rotor' ? '转子侧' : specs.inertia_basis === 'output' ? '输出端' : specs.inertia_basis)

      this.page = pageIdOf(p)
      this.setData({
        part: p,
        rows,
        derived,
        reviews,
        offers: (p.offers || []).filter(o => o.url && o.kind !== 'sponsor').slice(0, 3),
        sources,
        image: F.imageUrl(p.image_url),
        webUrl: F.partUrl(p),
        tierLabel: t.label,
        tierNote: t.note,
        tierColor: t.color,
        priceLabel: F.price(p.price_cny),
        basis,
        keySpecs: (p.key_specs || []).map(x => `${x.label} ${x.value}`),
        // 详情响应自带 data_version；从分享链接直接进来的页面不该显示空版本。
        version: p.data_version || (getApp().globalData || {}).dataVersion || '',
        loading: false,
      })
      wx.setNavigationBarTitle({ title: p.model || p.title || '部件详情' })
      this.loadRating()
      this.loadComments()
    } catch (e) {
      this.setData({ loading: false, error: e.message })
    }
  },

  // ── 登录 ────────────────────────────────────────────────────────────────
  async login() {
    if (this.data.loginBusy) return
    this.setData({ loginBusy: true, authError: '' })
    try {
      const user = await auth.login()
      this.setData({ loggedIn: true, me: user || auth.user(), authError: '' })
      wx.showToast({ title: '已登录', icon: 'success' })
      this.loadRating()
      this.loadComments()
    } catch (e) {
      const msg = (e && e.message) || '登录失败，请重试'
      this.setData({ authError: msg })
      wx.showToast({ title: msg, icon: 'none' })
    } finally {
      this.setData({ loginBusy: false })
    }
  },

  logout() {
    wx.showModal({
      title: '退出登录',
      content: '退出后仍可浏览；评分与讨论需要重新登录。',
      success: res => { if (res.confirm) this.doLogout() },
    })
  },

  async doLogout() {
    try {
      await auth.logout()
    } finally {
      this.setData({
        loggedIn: false,
        me: null,
        ratingMine: null,
        ratingNotice: '',
        replyTo: null,
        commentNotice: '',
        score: 0,
        ownHardware: false,
        ratingNote: '',
      })
      this.loadRating()
      this.loadComments()
    }
  },

  /** 写操作前统一登录；失败时把原因留在页面上，不静默丢掉用户输入。 */
  async ensureLogin() {
    if (auth.isLoggedIn()) return true
    this.setData({ loginBusy: true, authError: '' })
    try {
      const user = await auth.login()
      this.setData({ loggedIn: true, me: user || auth.user() })
      return true
    } catch (e) {
      const msg = (e && e.message) || '登录失败，请重试'
      this.setData({ authError: msg })
      wx.showToast({ title: msg, icon: 'none' })
      return false
    } finally {
      this.setData({ loginBusy: false })
    }
  },

  // ── 评分 ────────────────────────────────────────────────────────────────
  applyRating(r) {
    const count = Number((r && r.count) || 0)
    const histogram = (r && r.histogram) || {}
    const bars = Object.keys(histogram)
      .map(k => ({ score: k, n: histogram[k] || 0 }))
      .sort((a, b) => Number(b.score) - Number(a.score))
    const mine = (r && r.mine) || null
    const patch = {
      rating: {
        count,
        avg: count ? Number(r.avg) : null,
        avgLabel: count ? String(Math.round(Number(r.avg) * 10) / 10) : '—',
        own_hardware_count: Number(r.own_hardware_count || 0),
        low_sample: !!r.low_sample || count < 5,
        bars,
      },
      ratingMine: mine,
    }
    if (mine) {
      patch.score = Number(mine.score) || this.data.score
      patch.ownHardware = !!mine.own_hardware
      patch.ratingNote = mine.note || ''
    }
    this.setData(patch)
  },

  async loadRating() {
    try {
      const r = await api.get('/ratings/' + encodeURIComponent(this.id))
      this.applyRating(r)
    } catch (e) {
      this.setData({ ratingError: e.message })
    }
  },

  pickScore(e) {
    const score = Number(e.currentTarget.dataset.score)
    if (score >= 1 && score <= 5) this.setData({ score })
  },

  toggleOwnHardware(e) {
    this.setData({ ownHardware: !!(e.detail && e.detail.value) })
  },

  onRatingNote(e) {
    this.setData({ ratingNote: (e.detail && e.detail.value) || '' })
  },

  async submitRating() {
    if (this.data.ratingBusy) return
    const score = Number(this.data.score)
    if (!(score >= 1 && score <= 5)) {
      wx.showToast({ title: '请选择 1–5 分', icon: 'none' })
      return
    }
    const note = String(this.data.ratingNote || '').trim()
    if (note.length > 200) {
      wx.showToast({ title: '备注最多 200 字', icon: 'none' })
      return
    }
    if (!(await this.ensureLogin())) return
    this.setData({ ratingBusy: true, ratingError: '', ratingNotice: '' })
    try {
      // 同一人同一件由后端唯一约束 + upsert 保证：再提交就是改分，不刷票。
      const r = await api.post('/ratings/' + encodeURIComponent(this.id), {
        score,
        own_hardware: !!this.data.ownHardware,
        note,
      })
      this.applyRating(r)
      const msg = r && r.created ? '评分已提交' : '评分已更新'
      this.setData({ ratingNotice: msg })
      wx.showToast({ title: msg, icon: 'success' })
    } catch (e) {
      const msg = (e && e.message) || '评分失败，请重试'
      // 401 已由 api 清会话；同步按钮状态，避免还显示「已登录」。
      this.setData({ ratingError: msg, loggedIn: auth.isLoggedIn(), me: auth.user() })
      wx.showToast({ title: msg, icon: 'none' })
    } finally {
      this.setData({ ratingBusy: false })
    }
  },

  // ── 讨论 ────────────────────────────────────────────────────────────────
  buildComments(rows) {
    const byId = {}
    ;(rows || []).forEach(c => {
      const deleted = !!c.deleted
      byId[c.id] = {
        id: c.id,
        body: deleted ? '该讨论已被删除' : c.body,
        deleted,
        pending: c.status === 'pending',
        canReply: !deleted,
        created_at: c.created_at,
        authorName: deleted ? '已删除' : authorName(c.author),
        hue: hue(c.author),
        parent_id: c.parent_id,
        children: [],
      }
    })
    const roots = []
    ;(rows || []).forEach(c => {
      const node = byId[c.id]
      if (!node) return
      const parent = c.parent_id != null ? byId[c.parent_id] : null
      if (parent) {
        node.parentName = parent.authorName
        parent.children.push(node)
      } else {
        roots.push(node)
      }
    })
    const flat = []
    const walk = (list, depth) => {
      list.forEach(n => {
        flat.push({
          id: n.id,
          body: n.body,
          deleted: n.deleted,
          pending: n.pending,
          canReply: n.canReply,
          date: F.date(n.created_at),
          authorName: n.authorName,
          hue: n.hue,
          depth,
          parentName: n.parentName || '',
        })
        // 后端支持多层回复；超过 3 层只收窄缩进，不能把内容丢掉。
        walk(n.children, Math.min(depth + 1, 3))
      })
    }
    walk(roots, 0)
    return flat
  },

  async loadComments() {
    if (!this.page) return
    this.setData({ commentsLoading: true, commentError: '' })
    try {
      const d = await api.get('/wiki/comments', { page: this.page, limit: 200 })
      this.setData({
        comments: this.buildComments((d && d.comments) || []),
        commentsLoading: false,
        commentsReadonly: false,
      })
    } catch (e) {
      // 讨论接口不可用不等于部件详情失败：保留只读降级，不弹错误页。
      this.setData({
        comments: [],
        commentsLoading: false,
        commentsReadonly: true,
        commentError: e.message || '讨论暂不可用，当前为只读',
      })
    }
  },

  startReply(e) {
    const id = Number(e.currentTarget.dataset.id)
    const name = e.currentTarget.dataset.name || ''
    if (!id) return
    this.setData({ replyTo: { id, name } })
  },

  cancelReply() {
    this.setData({ replyTo: null })
  },

  onCommentInput(e) {
    this.setData({ commentBody: (e.detail && e.detail.value) || '' })
  },

  async submitComment() {
    if (this.data.commentBusy || this.data.commentsReadonly) return
    const body = String(this.data.commentBody || '').trim()
    if (body.length < 2) {
      wx.showToast({ title: '至少写 2 个字', icon: 'none' })
      return
    }
    if (body.length > 4000) {
      wx.showToast({ title: '内容最多 4000 字', icon: 'none' })
      return
    }
    if (!(await this.ensureLogin())) return
    const parent = this.data.replyTo
    this.setData({ commentBusy: true, commentError: '', commentNotice: '' })
    try {
      await api.post('/wiki/comments', {
        page: this.page,
        body,
        parent_id: parent ? parent.id : null,
      })
      this.setData({ commentBody: '', replyTo: null, commentNotice: '已发表' })
      wx.showToast({ title: '已发表', icon: 'success' })
      this.loadComments()
    } catch (e) {
      // 401 已由 api 清会话；服务端内容安全拒绝会带 detail，原样展示便于修改。
      const msg = (e && e.message) || '发言失败，请稍后重试'
      this.setData({ commentError: msg, loggedIn: auth.isLoggedIn(), me: auth.user() })
      wx.showToast({ title: msg, icon: 'none' })
    } finally {
      this.setData({ commentBusy: false })
    }
  },

  // ── 分享 / 复制 / 错误态 ────────────────────────────────────────────────
  async copyLink() {
    // 静态分享 JSON 的 canonical_url 与网页 canonical/OG 同源；取不到再退回 API web_path。
    const p = this.data.part || {}
    let url = this.data.webUrl
    try {
      const json = F.sharePartUrl(p)
      if (json) {
        const share = await api.getUrl(json)
        if (share && share.canonical_url) url = share.canonical_url
      }
    } catch (e) {}
    F.copy(url, '网页链接已复制')
  },

  retry() { this.load() },

  goHome() {
    const pages = getCurrentPages()
    if (pages.length > 1) wx.navigateBack()
    else wx.reLaunch({ url: '/pages/index/index' })
  },

  copySource(e) {
    F.copy(e.currentTarget.dataset.url, '来源链接已复制')
  },

  copyOffer(e) {
    const url = e.currentTarget.dataset.url
    if (!url) {
      wx.showToast({ title: '该优惠没有可复制链接', icon: 'none' })
      return
    }
    F.copy(url, '优惠链接已复制')
  },

  onImageError() {
    this.setData({ image: '' })
  },

  shareBits() {
    const p = this.data.part || {}
    const bits = [p.model || p.title || '部件']
    if (p.source_tier) bits.push(p.source_tier + ' 级')
    if (this.data.keySpecs && this.data.keySpecs.length) bits.push(this.data.keySpecs[0])
    return bits
  },

  onShareAppMessage() {
    return {
      title: this.shareBits().join(' · '),
      path: `/pages/part/part?id=${encodeURIComponent(this.id)}`,
      imageUrl: this.data.image || undefined,
    }
  },

  onShareTimeline() {
    return {
      title: this.shareBits().join(' · '),
      query: `id=${encodeURIComponent(this.id)}`,
    }
  },
})
