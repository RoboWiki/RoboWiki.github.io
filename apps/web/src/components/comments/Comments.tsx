import { useEffect, useState } from 'react'
import { api } from '@/lib/api'
import type { Comment, User } from '@robowiki/core'

type Props = { page: string }

const LOGIN_HREF = '/account.html'

function renderBody(body: string) {
  return body.split(/(!\[[^\]]*\]\(\/api\/v1\/media\/[^)]+\))/g).map((chunk, i) => {
    const m = chunk.match(/^!\[([^\]]*)\]\((\/api\/v1\/media\/[^)]+)\)$/)
    if (!m) return <span key={i}>{chunk}</span>
    return <img key={i} src={m[2]} alt={m[1] || '评论配图'} loading="lazy" className="my-2 max-h-72 rounded-lg border border-line" />
  })
}

export default function Comments({ page }: Props) {
  const [comments, setComments] = useState<Comment[]>([])
  const [me, setMe] = useState<User | null>(null)
  const [body, setBody] = useState('')
  const [replyTo, setReplyTo] = useState<number | null>(null)
  const [busy, setBusy] = useState(false)
  const [uploading, setUploading] = useState(false)
  const [error, setError] = useState('')

  const load = () => {
    api.listComments(page)
      .then(data => setComments(data.comments || []))
      .catch(() => setError('讨论暂时加载不到，稍后再试。'))
  }

  useEffect(() => {
    let alive = true
    api.listComments(page)
      .then(data => { if (alive) setComments(data.comments || []) })
      .catch(() => { if (alive) setError('讨论暂时加载不到，稍后再试。') })
    api.me().then(u => { if (alive) setMe(u) }).catch(() => {})
    return () => { alive = false }
  }, [page])

  const submit = async () => {
    const text = body.trim()
    if (!text || busy) return
    setBusy(true)
    setError('')
    try {
      await api.addComment(page, text, replyTo ?? undefined)
      setBody('')
      setReplyTo(null)
      load()
    } catch (err: any) {
      setError(err?.status === 401 ? '登录后才能发言。' : (err?.message || '发送失败，请稍后重试。'))
    } finally {
      setBusy(false)
    }
  }

  const upload = async (file: File) => {
    if (!file || uploading) return
    setUploading(true)
    setError('')
    try {
      const token = localStorage.getItem('roboselect.token') || ''
      const base = (import.meta.env.PUBLIC_API_BASE || 'https://robowiki.org.cn/api/v1').replace(/\/$/, '')
      const form = new FormData()
      form.append('file', file)
      const res = await fetch(`${base}/media`, {
        method: 'POST',
        headers: token ? { Authorization: `Bearer ${token}` } : undefined,
        body: form,
      })
      const data = await res.json().catch(() => ({}))
      if (!res.ok) throw new Error(data.detail || '图片上传失败')
      setBody(v => `${v}${v ? '\n' : ''}![图片](${data.url})`)
    } catch (err: any) {
      setError(err?.message || '图片上传失败')
    } finally {
      setUploading(false)
    }
  }

  const remove = async (id: number) => {
    if (!confirm('删除这条讨论？')) return
    try {
      await api.deleteComment(id)
      load()
    } catch {
      setError('删除失败，可能需要重新登录。')
    }
  }

  const report = async (id: number) => {
    const reason = prompt('举报原因（spam / abuse / misinfo / other）', 'spam')
    if (!reason) return
    try {
      await api.request('/reports', {
        method: 'POST',
        body: { target_kind: 'wiki_comment', target_id: id, reason, detail: '' },
      })
      alert('已提交举报，站务会处理。')
    } catch {
      setError('举报失败，请稍后再试。')
    }
  }

  return (
    <section className="rounded-lg border border-line bg-surface p-5" aria-label="页面讨论">
      <div className="flex items-center justify-between gap-3">
        <h2 className="text-lg font-bold text-ink">这一页的讨论</h2>
        <span className="text-xs text-ink-3">{comments.length} 条</span>
      </div>

      <div className="mt-4 space-y-2">
        {me ? (
          <>
            {replyTo !== null && (
              <p className="text-xs text-ink-3">
                回复 #{replyTo} · <button className="text-blue-700 hover:underline" onClick={() => setReplyTo(null)}>取消</button>
              </p>
            )}
            <textarea
              value={body}
              onChange={e => setBody(e.target.value)}
              rows={3}
              maxLength={4000}
              placeholder="写清楚工况、实测数据和结论。只写“好用/不好用”对下一个人没有价值。"
              className="w-full rounded-lg border border-line p-3 text-sm focus:border-brand focus:outline-none focus:ring-2 focus:ring-brand/20"
            />
            <div className="flex flex-wrap items-center gap-2">
              <button onClick={submit} disabled={busy || !body.trim()} className="inline-flex h-9 items-center rounded-lg bg-brand px-4 text-sm font-medium text-brand-fg disabled:opacity-50">
                {busy ? '发送中…' : '发表讨论'}
              </button>
              <label className="inline-flex h-9 cursor-pointer items-center rounded-lg border border-line px-3 text-xs text-ink-2 hover:bg-surface-3">
                {uploading ? '上传中…' : '插入图片'}
                <input type="file" accept="image/jpeg,image/png,image/webp" className="sr-only" onChange={e => { const f = e.target.files?.[0]; if (f) upload(f); e.currentTarget.value = '' }} />
              </label>
              <span className="text-xs text-ink-3">支持 JPEG / PNG / WebP，≤ 5 MB</span>
            </div>
          </>
        ) : (
          <div className="rounded-lg bg-surface-2 p-3 text-sm text-ink-2">
            <a href={LOGIN_HREF} className="font-medium text-blue-700 hover:underline">登录</a> 后可以发表讨论、上传配图。
          </div>
        )}
        {error && <p className="text-sm text-amber-700" role="alert">{error}</p>}
      </div>

      <ul className="mt-5 space-y-4">
        {comments.map(c => (
          <li
            key={c.id}
            id={`comment-${c.id}`}
            className={`scroll-mt-24 rounded-lg border border-line p-3 ${c.parent_id ? 'ml-6 bg-surface-2/60' : ''}`}
          >
            <div className="flex flex-wrap items-center gap-2 text-xs text-ink-3">
              <span className="font-medium text-ink-2">{c.author?.display_name || c.author?.handle || '已注销'}</span>
              <span>{String(c.created_at).slice(0, 10)}</span>
              {c.status === 'pending' && <span className="text-amber-700">待审核</span>}
              {c.deleted && <span className="text-ink-3">已删除</span>}
            </div>
            {!c.deleted && <p className="mt-1 whitespace-pre-wrap text-sm leading-7 text-ink-2">{renderBody(c.body)}</p>}
            {!c.deleted && (
              <div className="mt-2 flex gap-3 text-xs">
                {me && <button className="text-ink-3 hover:text-ink" onClick={() => setReplyTo(c.id)}>回复</button>}
                {me && me.handle === c.author?.handle && <button className="text-ink-3 hover:text-danger" onClick={() => remove(c.id)}>删除</button>}
                {me && me.handle !== c.author?.handle && <button className="text-ink-3 hover:text-ink-2" onClick={() => report(c.id)}>举报</button>}
              </div>
            )}
          </li>
        ))}
        {!comments.length && !error && <li className="text-sm text-ink-3">还没有讨论。成为第一个留下实测记录的人。</li>}
      </ul>
    </section>
  )
}
