"""QQ 群 @ 机器人：把一次群消息转成一次只读查询。

协议、重连、事件、鉴权交给 NoneBot2 + nonebot-adapter-qq；
这里只做两件事：取消息文本、回一句话 + 链接。不做推送、不落群聊语料。
"""
from __future__ import annotations

import os

import httpx
from nonebot import on_message
from nonebot.adapters.qq import (Bot, GroupAtMessageCreateEvent, MessageEvent,
                                 MessageSegment)
from nonebot.rule import Rule

API = os.environ.get("ROBOWIKI_API", "https://robowiki.org.cn").rstrip("/")
TOKEN = os.environ["ROBOWIKI_BOT_TOKEN"]
TIMEOUT = float(os.environ.get("ROBOWIKI_BOT_TIMEOUT", "5"))


async def _in_group(event: MessageEvent) -> bool:
    return isinstance(event, GroupAtMessageCreateEvent)


matcher = on_message(rule=Rule(_in_group), priority=50, block=True)


@matcher.handle()
async def answer(bot: Bot, event: MessageEvent):
    q = event.get_plaintext().strip()
    if not q:
        await matcher.finish("发个型号给我，例如：@RoboWiki AK80-6")
    try:
        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            r = await client.get(f"{API}/api/v1/bot/answer", params={"q": q},
                                 headers={"X-Bot-Token": TOKEN})
            r.raise_for_status()
            d = r.json()
    except Exception:
        await matcher.finish("查询服务暂时不可用，稍后再试；站点："
                             f"{API.replace('api.', '')}")
    text = f"{d['answer']}\n{d['url']}\n数据 {d.get('data_version', '')}".strip()
    await matcher.finish(MessageSegment.text(text))
