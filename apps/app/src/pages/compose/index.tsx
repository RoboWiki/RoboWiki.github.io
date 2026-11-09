import { useEffect, useState } from 'react'

import { Button, Input, Text, Textarea, View } from 'virtual:taro/components'
import Taro, { useDidShow, useRouter } from 'virtual:taro/api'
import type { PostInput, PostSummary, User } from '@robowiki/core'

import { ErrorState } from '@/components/Feedback'
import { api, errorMessage, loadMe } from '@/services/api'
import { partCategoryLabel, type PartView } from '@/services/parts'
import { showToast } from '@/utils/nav'
import { useThemeMode } from '@/utils/theme'
import './index.css'

type Kind = 'discussion' | 'review' | 'build'

type PostExtra = PostSummary & {
  use_case?: string | null
  own_hardware?: boolean
  total_price_cny?: number | null
  price_scope?: string | null
  price_verified?: boolean
}

const KIND_OPTIONS: Array<{ value: Kind; label: string; hint: string }> = [
  { value: 'discussion', label: '讨论', hint: '提问、纠错或补充实测' },
  { value: 'review', label: '评价', hint: '给用过的部件打分' },
  { value: 'build', label: '方案', hint: '整机配置与报价' },
]

const KIND_LABEL: Record<string, string> = {
  discussion: '讨论',
  review: '评价',
  build: '方案',
}

const MAX_TAGS = 6

function parseTags(raw: string): string[] {
  const seen = new Set<string>()
  return raw
    .split(/[,，、\s]+/)
    .map((tag) => tag.trim())
    .filter((tag) => {
      if (!tag || seen.has(tag)) return false
      seen.add(tag)
      return true
    })
    .slice(0, MAX_TAGS)
}

export default function ComposePage() {
  const router = useRouter()
  const theme = useThemeMode()
  const darkClass = theme === 'dark' ? 'dark' : ''

  const editRaw = decodeURIComponent(router.params?.id || '')
  const editId = Number(editRaw)
  const editing = Number.isFinite(editId) && editId > 0

  const presetKindRaw = String(router.params?.kind || '')
  const presetKind: Kind = (['discussion', 'review', 'build'] as Kind[]).includes(presetKindRaw as Kind)
    ? (presetKindRaw as Kind)
    : 'discussion'
  const presetPartId = decodeURIComponent(router.params?.part_id || '')

  const [user, setUser] = useState<User | null>(null)
  const [userLoading, setUserLoading] = useState(true)

  const [kind, setKind] = useState<Kind>(presetKind)
  const [title, setTitle] = useState('')
  const [body, setBody] = useState('')
  const [tags, setTags] = useState('')
  const [rating, setRating] = useState(0)
  const [useCase, setUseCase] = useState('')
  const [ownHardware, setOwnHardware] = useState<boolean | null>(null)
  const [price, setPrice] = useState('')
  const [priceScope, setPriceScope] = useState('')
  const [priceVerified, setPriceVerified] = useState(false)

  const [partId, setPartId] = useState(presetPartId)
  const [part, setPart] = useState<PartView | null>(null)
  const [searchInput, setSearchInput] = useState('')
  const [query, setQuery] = useState('')
  const [results, setResults] = useState<PartView[]>([])
  const [searching, setSearching] = useState(false)

  const [pageLoading, setPageLoading] = useState(editing)
  const [loadError, setLoadError] = useState('')
  const [forbidden, setForbidden] = useState('')
  const [reloadKey, setReloadKey] = useState(0)

  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')

  const loadPart = (id: string) => {
    if (!id) {
      setPart(null)
      return
    }
    api
      .getPart(id)
      .then((data) => setPart(data as PartView))
      .catch(() => setPart(null))
  }

  useDidShow(() => {
    loadMe().then((me) => {
      setUser(me)
      setUserLoading(false)
    })
  })

  useEffect(() => {
    Taro.setNavigationBarTitle({ title: editing ? '编辑帖子' : '发帖' }).catch(() => {})
  }, [editing])

  useEffect(() => {
    if (presetPartId) loadPart(presetPartId)
  }, [presetPartId])

  useEffect(() => {
    if (!editing || !user) return
    let alive = true
    setPageLoading(true)
    setLoadError('')
    setForbidden('')
    api
      .getPost(editId)
      .then((data) => {
        if (!alive) return
        const post = data as PostExtra
        const allowed =
          Boolean(user.is_staff) ||
          post.author?.id === user.id ||
          Boolean(post.author?.handle && post.author.handle === user.handle)
        if (!allowed) {
          setForbidden('只能编辑自己发布的帖子')
          return
        }
        setKind((['discussion', 'review', 'build'] as Kind[]).includes(post.kind as Kind)
          ? (post.kind as Kind)
          : 'discussion')
        setTitle(post.title || '')
        setBody(post.body || '')
        setTags((post.tags || []).join(', '))
        setRating(typeof post.rating === 'number' ? post.rating : 0)
        setUseCase(post.use_case || '')
        setOwnHardware(typeof post.own_hardware === 'boolean' ? post.own_hardware : null)
        setPrice(post.total_price_cny == null ? '' : String(post.total_price_cny))
        setPriceScope(post.price_scope || '')
        setPriceVerified(Boolean(post.price_verified))
        const nextPartId = post.part_id || presetPartId || ''
        setPartId(nextPartId)
        if (nextPartId) loadPart(nextPartId)
      })
      .catch((err) => {
        if (alive) setLoadError(errorMessage(err))
      })
      .finally(() => {
        if (alive) setPageLoading(false)
      })
    return () => {
      alive = false
    }
  }, [editing, editId, user?.id, reloadKey])

  useEffect(() => {
    const timer = setTimeout(() => setQuery(searchInput.trim()), 350)
    return () => clearTimeout(timer)
  }, [searchInput])

  useEffect(() => {
    if (!query) {
      setResults([])
      return
    }
    let alive = true
    setSearching(true)
    api
      .listParts({ q: query, limit: 8, compact: true })
      .then((data) => {
        if (alive) setResults((data.items || []) as PartView[])
      })
      .catch(() => {
        if (alive) setResults([])
      })
      .finally(() => {
        if (alive) setSearching(false)
      })
    return () => {
      alive = false
    }
  }, [query])

  const pickPart = (item: PartView) => {
    setPart(item)
    setPartId(String(item.id))
    setResults([])
    setSearchInput('')
    setQuery('')
  }

  const clearPart = () => {
    setPart(null)
    setPartId('')
  }

  const openLogin = () => {
    Taro.navigateTo({ url: '/pages/login/index' })
  }

  const goBack = (postId?: number) => {
    const pages = Taro.getCurrentPages()
    if (pages.length > 1) {
      Taro.navigateBack()
      return
    }
    if (postId) {
      Taro.redirectTo({ url: `/pages/post/index?id=${encodeURIComponent(String(postId))}` })
      return
    }
    Taro.reLaunch({ url: '/pages/community/index' })
  }

  const validate = (): string => {
    const text = title.trim()
    if (text.length < 4) return '标题至少 4 个字'
    if (text.length > 120) return '标题最多 120 字'
    if (body.trim().length < 10) return '正文至少 10 个字，写清背景和已试过的方法'
    const tagList = parseTags(tags)
    if (tags.trim() && tagList.length === 0) return '标签格式不正确'
    if (tagList.some((tag) => tag.length > 16)) return '单个标签最多 16 个字'
    if (tagList.join(',').length > 80) return '标签总长最多 80 字，请精简一下'
    if (kind === 'review') {
      if (!partId) return '评价必须关联一个部件'
      if (!rating || rating < 1 || rating > 5) return '请选择 1–5 分'
      if (ownHardware === null) return '请选择是否自购设备'
      if (useCase.trim().length > 16) return '使用场景最多 16 字'
    }
    if (kind === 'build') {
      if (price.trim()) {
        if (!/^\d+(\.\d+)?$/.test(price.trim())) return '整机报价必须是非负数字（不要带 ¥ 或逗号）'
        if (Number(price.trim()) > 10_000_000) return '报价超出合理范围（≤ 1000 万）'
        if (!priceScope.trim()) return '填了整机报价，就要写清覆盖范围'
      }
      if (priceScope.trim().length > 80) return '覆盖范围最多 80 字'
    }
    return ''
  }

  const fail = (message: string) => {
    setError(message)
    Taro.pageScrollTo({ scrollTop: 0, duration: 200 }).catch(() => {})
  }

  const submit = async () => {
    if (busy || !user) return
    setError('')
    const message = validate()
    if (message) {
      fail(message)
      return
    }

    const payload: PostInput = {
      kind,
      title: title.trim(),
      body: body.trim(),
      tags: parseTags(tags).join(','),
      part_id: partId || null,
      rating: null,
      use_case: null,
      own_hardware: false,
      total_price_cny: null,
      price_scope: null,
    }
    if (kind === 'review') {
      payload.rating = rating
      payload.use_case = useCase.trim() || null
      payload.own_hardware = Boolean(ownHardware)
    }
    if (kind === 'build') {
      payload.total_price_cny = price.trim() ? Number(price.trim()) : null
      payload.price_scope = priceScope.trim() || null
      // 「已核实」是站务信任标记，普通作者传了也会被后端忽略；不传以免覆盖已有标记。
      if (user.is_staff) payload.price_verified = priceVerified
    }

    if (editing) {
      // PATCH /posts/{id} 不接受 kind / part_id，传了也会被忽略。
      delete payload.kind
      delete payload.part_id
    }

    setBusy(true)
    try {
      const saved = editing
        ? await api.updatePost(editId, payload)
        : await api.createPost(payload)
      showToast(editing ? '修改已保存' : '已发布')
      setTimeout(() => goBack(saved.id), 350)
    } catch (err) {
      fail(errorMessage(err))
      setBusy(false)
    }
  }

  if (userLoading) {
    return (
      <View className={`rw-page compose ${darkClass}`}>
        <View className="rw-stack" style={{ gap: '12px' }}>
          <View className="rw-skeleton rw-skeleton--line" style={{ width: '40%' }} />
          <View className="rw-skeleton" style={{ height: '44px' }} />
          <View className="rw-skeleton" style={{ height: '160px' }} />
          <View className="rw-skeleton" style={{ height: '44px' }} />
        </View>
      </View>
    )
  }

  if (!user) {
    return (
      <View className={`rw-page compose ${darkClass}`}>
        <View className="compose__gate">
          <Text className="rw-title">{editing ? '编辑帖子' : '发帖'}</Text>
          <Text className="rw-caption">登录后才能发布讨论、评价和方案。</Text>
          <Button className="rw-btn rw-btn--primary" onClick={openLogin}>
            去登录
          </Button>
          <Text className="rw-link rw-link--tap" onClick={() => goBack()}>
            先返回
          </Text>
        </View>
      </View>
    )
  }

  if (editing && pageLoading) {
    return (
      <View className={`rw-page compose ${darkClass}`}>
        <View className="rw-stack" style={{ gap: '12px' }}>
          <View className="rw-skeleton rw-skeleton--line" style={{ width: '40%' }} />
          <View className="rw-skeleton" style={{ height: '44px' }} />
          <View className="rw-skeleton" style={{ height: '160px' }} />
          <View className="rw-skeleton" style={{ height: '44px' }} />
        </View>
      </View>
    )
  }

  if (editing && (forbidden || loadError)) {
    return (
      <View className={`rw-page compose ${darkClass}`}>
        <ErrorState
          message={forbidden || loadError}
          onRetry={forbidden ? undefined : () => setReloadKey((key) => key + 1)}
        />
        <Button className="rw-btn" onClick={() => goBack(editId)}>
          返回帖子
        </Button>
      </View>
    )
  }

  return (
    <View className={`rw-page compose ${darkClass}`}>
      <View className="compose__head">
        <Text className="rw-title">{editing ? '编辑帖子' : '发帖'}</Text>
        <Text className="rw-caption">
          写清型号、场景和依据；只写用过的、量过的。发布后可在帖子页继续讨论。
        </Text>
      </View>

      {error ? <Text className="rw-error compose__error">{error}</Text> : null}

      <View className="compose__section">
        <Text className="rw-subtitle">类型</Text>
        <View className="compose__chips">
          {KIND_OPTIONS.map((item) => (
            <View
              key={item.value}
              className={`rw-chip rw-chip--touch ${kind === item.value ? 'rw-chip--active' : ''} ${editing ? 'compose__chip--fixed' : ''}`}
              onClick={() => {
                if (!editing) setKind(item.value)
              }}
            >
              {item.label}
            </View>
          ))}
        </View>
        <Text className="rw-caption">
          {editing
            ? `当前为${KIND_LABEL[kind]}，编辑时不能修改类型`
            : KIND_OPTIONS.find((item) => item.value === kind)?.hint}
        </Text>
      </View>

      <View className="compose__section">
        <View className="compose__label">
          <Text className="rw-subtitle">标题</Text>
          <Text className="rw-caption">{title.length}/120</Text>
        </View>
        <View className="rw-field">
          <Input
            className="rw-input"
            value={title}
            maxlength={120}
            placeholder="一句话说清问题或结论"
            onInput={(event) => setTitle(event.detail.value)}
          />
        </View>
      </View>

      <View className="compose__section">
        <View className="compose__label">
          <Text className="rw-subtitle">正文</Text>
          <Text className="rw-caption">{body.length}/20000</Text>
        </View>
        <View className="rw-field rw-field--textarea">
          <Textarea
            className="rw-textarea compose__body"
            value={body}
            maxlength={20000}
            placeholder={
              kind === 'discussion'
                ? '背景、现象、已试过的方法、希望得到的帮助…'
                : kind === 'review'
                  ? '实际使用时长、场景、优点与问题，尽量给可复核的细节…'
                  : '配置清单、装配步骤、踩过的坑与复现条件…'
            }
            onInput={(event) => setBody(event.detail.value)}
          />
        </View>
      </View>

      <View className="compose__section">
        <Text className="rw-subtitle">标签</Text>
        <View className="rw-field">
          <Input
            className="rw-input"
            value={tags}
            maxlength={80}
            placeholder="逗号分隔，最多 6 个，如 舵机, 树莓派"
            onInput={(event) => setTags(event.detail.value)}
          />
        </View>
        <Text className="rw-caption">用于筛选与关联，留空也可以。</Text>
      </View>

      <View className="compose__section">
        <Text className="rw-subtitle">关联部件</Text>
        {partId ? (
          <View className="rw-list">
            <View className="rw-list__row compose__part">
              <View className="rw-grow">
                <Text className="rw-strong">
                  {part ? `${part.vendor} ${part.model}` : partId}
                </Text>
                <Text className="rw-caption compose__line">
                  {part ? `${partCategoryLabel(part)} · ${part.web_path || part.id}` : '已关联部件'}
                </Text>
              </View>
              {editing ? null : (
                <Text className="rw-link rw-link--tap" onClick={clearPart}>
                  移除
                </Text>
              )}
            </View>
          </View>
        ) : editing ? (
          <Text className="rw-caption">这条帖子没有关联部件；编辑时不能新增。</Text>
        ) : (
          <>
            <View className="rw-field">
              <Input
                className="rw-input"
                value={searchInput}
                placeholder="搜索厂商 / 型号（可选）"
                confirmType="search"
                onInput={(event) => setSearchInput(event.detail.value)}
              />
            </View>
            {searching ? <Text className="rw-caption">正在搜索…</Text> : null}
            {results.length ? (
              <View className="rw-list">
                {results.map((item) => (
                  <View
                    key={item.id}
                    className="rw-list__row rw-list__row--tap compose__part"
                    onClick={() => pickPart(item)}
                  >
                    <View className="rw-grow">
                      <Text className="rw-strong">{item.vendor} {item.model}</Text>
                      <Text className="rw-caption compose__line">
                        {partCategoryLabel(item)} · {item.web_path || item.id}
                      </Text>
                    </View>
                  </View>
                ))}
              </View>
            ) : query && !searching ? (
              <Text className="rw-caption">没有匹配的部件，换个关键词试试。</Text>
            ) : null}
          </>
        )}
        {editing && partId ? (
          <Text className="rw-caption">编辑时不能更换关联部件。</Text>
        ) : null}
      </View>

      {kind === 'review' ? (
        <>
          <View className="compose__section">
            <Text className="rw-subtitle">评分</Text>
            <View className="compose__rating">
              {[1, 2, 3, 4, 5].map((value) => (
                <View
                  key={value}
                  className={`compose__star ${rating >= value ? 'compose__star--on' : ''}`}
                  onClick={() => setRating(value)}
                >
                  <Text className="compose__star-icon">★</Text>
                  <Text className="compose__star-label">{value}</Text>
                </View>
              ))}
            </View>
            <Text className="rw-caption">
              {rating ? `已选 ${rating} 分` : '1 分最差，5 分最好'}
            </Text>
          </View>

          <View className="compose__section">
            <Text className="rw-subtitle">使用场景</Text>
            <View className="rw-field">
              <Input
                className="rw-input"
                value={useCase}
                maxlength={16}
                placeholder="如 室内建图（最多 16 字）"
                onInput={(event) => setUseCase(event.detail.value)}
              />
            </View>
          </View>

          <View className="compose__section">
            <Text className="rw-subtitle">是否自购</Text>
            <View className="compose__chips">
              <View
                className={`rw-chip rw-chip--touch ${ownHardware === true ? 'rw-chip--active' : ''}`}
                onClick={() => setOwnHardware(true)}
              >
                自购设备
              </View>
              <View
                className={`rw-chip rw-chip--touch ${ownHardware === false ? 'rw-chip--active' : ''}`}
                onClick={() => setOwnHardware(false)}
              >
                借测 / 未持有
              </View>
            </View>
            <Text className="rw-caption">自购评分会单独统计，帮助区分真实长期使用。</Text>
          </View>
        </>
      ) : null}

      {kind === 'build' ? (
        <>
          <View className="compose__section">
            <Text className="rw-subtitle">整机报价</Text>
            <View className="rw-field">
              <Input
                className="rw-input"
                type="digit"
                value={price}
                placeholder="人民币，可留空，如 1299"
                onInput={(event) => setPrice(event.detail.value)}
              />
            </View>
            <Text className="rw-caption">只填整机总价，不含运费或按覆盖范围说明。</Text>
          </View>

          <View className="compose__section">
            <Text className="rw-subtitle">覆盖范围</Text>
            <View className="rw-field">
              <Input
                className="rw-input"
                value={priceScope}
                maxlength={80}
                placeholder="如 含电池与充电器，不含遥控器"
                onInput={(event) => setPriceScope(event.detail.value)}
              />
            </View>
          </View>

          <View className="compose__section">
            <Text className="rw-subtitle">报价状态</Text>
            {user.is_staff ? (
              <>
                <View className="compose__chips">
                  <View
                    className={`rw-chip rw-chip--touch ${priceVerified ? 'rw-chip--active' : ''}`}
                    onClick={() => setPriceVerified(true)}
                  >
                    已核对官方报价
                  </View>
                  <View
                    className={`rw-chip rw-chip--touch ${!priceVerified ? 'rw-chip--active' : ''}`}
                    onClick={() => setPriceVerified(false)}
                  >
                    经验估算
                  </View>
                </View>
                <Text className="rw-caption">「已核实」会展示给读者，只在核对官方渠道后开启。</Text>
              </>
            ) : (
              <Text className="rw-caption">「已核实」标记由站务核对后设置，作者提交后默认为经验估算。</Text>
            )}
          </View>
        </>
      ) : null}

      <Button className="rw-btn rw-btn--primary compose__submit" disabled={busy} onClick={submit}>
        {busy ? (editing ? '保存中…' : '发布中…') : editing ? '保存修改' : '发布'}
      </Button>
      <Text className="rw-caption compose__note">
        发布即公开；请勿填写个人联系方式或未公开的隐私信息。
      </Text>
      <View className="rw-safe-bottom" />
    </View>
  )
}
