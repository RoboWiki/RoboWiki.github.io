import { useEffect, useState } from 'react'
import PostDetail from './post-detail'

export default function PostRoute() {
  const [id, setId] = useState<number | null>(null)
  useEffect(() => {
    const raw = new URLSearchParams(location.search).get('id') || ''
    const parsed = Number(raw)
    setId(Number.isFinite(parsed) && parsed > 0 ? parsed : 0)
  }, [])
  if (id === null) return <p className="text-sm text-ink-3">正在读取帖子…</p>
  if (!id) return <p className="text-sm text-warning">缺少帖子 id，链接可能不完整。</p>
  return <PostDetail postId={id} />
}
