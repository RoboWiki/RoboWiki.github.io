import { useEffect, useState } from 'react'
import ProfileIsland from './profile'

export default function ProfileRoute() {
  const [handle, setHandle] = useState<string | null>(null)
  useEffect(() => {
    setHandle(new URLSearchParams(location.search).get('handle') || '')
  }, [])
  if (handle === null) return <p className="text-sm text-slate-500">正在读取用户…</p>
  if (!handle) return <p className="text-sm text-amber-700">缺少用户名。</p>
  return <ProfileIsland handle={handle} />
}
