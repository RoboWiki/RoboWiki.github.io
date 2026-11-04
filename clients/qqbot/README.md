# QQ 群机器人（参考实现）

协议、重连、事件与鉴权交给 **NoneBot2 + nonebot-adapter-qq**；RoboWiki 只提供
`/api/v1/bot/answer`。机器人不自己实现 QQ 协议，也不读群文件或私聊。

## 行为

- 只在群内被 `@` 时回答；不做主动推送（QQ 群主动消息 4 条/月）。
- 回答固定格式：一句结论（型号 + 关键参数 + 来源等级）+ 链接 + `data_version`。
- 查不到就明确说没找到，给目录链接，不编参数。
- 不落群聊正文、不把聊天记录回传为语料；服务端只记录限流计数。

## 运行

```bash
cd clients/qqbot
python -m venv .venv && . .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env        # 填 QQ_BOTS 与 ROBOWIKI_BOT_TOKEN
python bot.py
```

后端需设置同一个令牌：

```bash
ROBOWIKI_BOT_TOKEN=<随机长串>
ROBOWIKI_SITE_URL=https://robowiki.org.cn
```

## 调用契约

```http
GET /api/v1/bot/answer?q=AK80-6
X-Bot-Token: <token>
```

```json
{
  "found": true,
  "answer": "CubeMars AK80-6 · 额定 6.0 N·m · 峰值 12.0 N·m · 48.0 V（来源 B）",
  "url": "https://robowiki.org.cn/parts/actuator/cubemars-ak80-6.html",
  "data_version": "data-v2026.11.2",
  "part": { "id": "cubemars-ak80-6", "model": "AK80-6" }
}
```

未配置 `ROBOWIKI_BOT_TOKEN` 时接口返回 503；令牌错误返回 401。
接口只读、按客户端 IP 限流（反代后取 X-Forwarded-For），不写库，也不依赖用户登录。

## 为什么不是自写协议

NoneBot2 已经处理登录、重连、事件分发与限流；自写一遍就是重复造轮子，且 QQ 侧
协议变更频繁。机器人只做“群消息 → 一次 API 查询 → 一条消息”。
