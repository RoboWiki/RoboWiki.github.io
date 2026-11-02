# QQ 群机器人（参考实现）

推荐用 **NoneBot2**（Python）或 **Koishi**（Node）承接 QQ 协议与事件；RoboWiki 只提供
`/api/v1/bot/answer`，不自己实现 QQ 协议、不做 WebSocket 重连。

## 行为

- 只在被 `@` 时回答；不做主动推送（QQ 群主动消息 4 条/月）。
- 只答高置信问题；答不上来说“不知道，建议问人”，并给站内链接。
- 同一群 5 分钟内最多回 5 次；相同问题 30 分钟内不重复回答。
- 回答固定格式：**一句结论 + 链接 + data_version**。
- 不读取群文件、不读私聊、不把群聊内容回传为语料。

## 调用契约

```http
GET /api/v1/bot/answer?q=4310+配+C620
```

```json
{
  "answer": "4310 可用 48V，配 C620 需确认固件版本。",
  "url": "https://robowiki.org/parts/actuator/damiao-dm-j4310-2ec-v1-2",
  "data_version": "data-v2026.11.0",
  "confidence": "high"
}
```

`confidence=low` 时机器人只回“没查到，建议问人”，不编。

## 环境

```bash
ROBOWIKI_API=https://api.robowiki.org
QQ_BOT_APP_ID=
QQ_BOT_SECRET=
```

## 为什么不是自写协议

NoneBot2 / Koishi 已经处理登录、重连、事件、限流；自写一遍就是重复造轮子，而且
QQ 侧协议变更频繁。机器人只做“把群消息转成一次 API 查询 + 把结果转成一条消息”。
