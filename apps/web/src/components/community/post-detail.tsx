import 'antd/dist/reset.css'
import {
  App as AntApp, Button, Card, Empty, Input, Modal, Select, Skeleton, Space, Tag, Typography,
} from 'antd'
import { EyeOutlined, MessageOutlined } from '@ant-design/icons'
import { useQuery, useQueryClient } from '@tanstack/react-query'
import { useState } from 'react'
import { KIND_COLOR, KIND_LABEL, api, siteHref } from '@/lib/community-api'
import { CommunityHeader, IslandProvider, useAuth } from './providers'
import { CommentList, MarkdownBody, UserBadge, VoteButtons, ago } from './ui'

function Detail({ postId }: { postId: number }) {
  const qc = useQueryClient()
  const { message } = AntApp.useApp()
  const { user, openAuth } = useAuth()
  const [reportOpen, setReportOpen] = useState(false)
  const [reason, setReason] = useState('spam')
  const [detail, setDetail] = useState('')
  const [sending, setSending] = useState(false)

  const post = useQuery({
    queryKey: ['post', postId],
    queryFn: () => api.post(postId),
    retry: false,
  })

  const vote = async (v: number) => {
    if (!user) return openAuth()
    try {
      await api.vote('post', postId, v)
      qc.invalidateQueries({ queryKey: ['post', postId] })
    } catch (e) {
      message.error((e as Error).message)
    }
  }

  const submitReport = async () => {
    if (!user) return openAuth()
    setSending(true)
    try {
      await api.report({ target_kind: 'post', target_id: postId, reason, detail })
      message.success('已提交，站务会审核')
      setReportOpen(false)
      setDetail('')
    } catch (e) {
      message.error((e as Error).message)
    } finally {
      setSending(false)
    }
  }

  const p = post.data

  return (
    <div>
      <CommunityHeader current="community" />

      {post.isLoading ? <Skeleton active /> : !p ? (
        <Empty description={`帖子不存在或已被隐藏${post.error ? `：${(post.error as Error).message}` : ''}`}>
          <a href={siteHref('/community.html')}><Button type="primary">回社区</Button></a>
        </Empty>
      ) : (
        <div className="grid gap-5 lg:grid-cols-[minmax(0,1fr)_260px]">
          <div className="min-w-0">
            <Card>
              <div className="mb-2 flex flex-wrap items-center gap-1.5">
                <Tag color={KIND_COLOR[p.kind]}>{KIND_LABEL[p.kind]}</Tag>
                {p.part_title && <Tag>{p.part_title}</Tag>}
                {p.own_hardware && <Tag color="blue">实测</Tag>}
                {p.tags.map(t => <Tag key={t} variant="filled">#{t}</Tag>)}
              </div>
              <Typography.Title level={1} style={{ marginTop: 0, fontSize: 24 }}>{p.title}</Typography.Title>
              <div className="mb-4 flex flex-wrap items-center gap-3">
                {p.author ? (
                  <a href={siteHref(`/u.html?handle=${encodeURIComponent(p.author.handle)}`)}><UserBadge user={p.author} /></a>
                ) : <UserBadge user={null} />}
                <Typography.Text type="secondary">{new Date(p.created_at).toLocaleString('zh-CN')}</Typography.Text>
                <Typography.Text type="secondary"><EyeOutlined /> {p.view_count}</Typography.Text>
                <Button type="text" size="small" style={{ color: '#616161' }}
                  onClick={() => (user ? setReportOpen(true) : openAuth())}>
                  举报
                </Button>
              </div>

              <div className="flex gap-3">
                <VoteButtons score={p.score} myVote={p.my_vote} onVote={vote} />
                <div className="min-w-0 flex-1">
                  <MarkdownBody>{p.body}</MarkdownBody>
                </div>
              </div>
            </Card>

            <Card title={<span><MessageOutlined /> 评论（{p.comment_count}）</span>} className="mt-4">
              {user ? <CommentList postId={postId} />
                : <Button type="primary" onClick={openAuth}>登录后参与讨论</Button>}
            </Card>
          </div>

          <aside className="min-w-0 space-y-3">
            <Card size="small" title="关于这条内容">
              <Typography.Paragraph type="secondary" style={{ fontSize: 12.5, marginBottom: 8 }}>
                投票与评论都记在账号上；写实测数据比写“好用”有用。
              </Typography.Paragraph>
              <a href={siteHref('/community.html')} className="text-[12.5px] text-blue-600">← 回社区</a>
            </Card>
          </aside>
        </div>
      )}

      <Modal open={reportOpen} title="举报这条内容" onCancel={() => setReportOpen(false)}
        okText="提交举报" confirmLoading={sending} onOk={submitReport} destroyOnHidden>
        <Space orientation="vertical" size={10} style={{ width: '100%', paddingTop: 8 }}>
          <Select value={reason} onChange={setReason} style={{ width: '100%' }}
            options={[
              { value: 'spam', label: '垃圾广告' },
              { value: 'abuse', label: '攻击辱骂' },
              { value: 'misinfo', label: '虚假信息' },
              { value: 'other', label: '其他' },
            ]} />
          <Input.TextArea rows={3} value={detail} onChange={e => setDetail(e.target.value)}
            placeholder="补充说明（选填）" maxLength={500} />
          <Typography.Text type="secondary" style={{ fontSize: 12 }}>
            举报不会自动下架；站务核实后决定隐藏或驳回。
          </Typography.Text>
        </Space>
      </Modal>
    </div>
  )
}

export default function PostDetail({ postId }: { postId: number }) {
  return (
    <IslandProvider>
      <Detail postId={postId} />
    </IslandProvider>
  )
}
