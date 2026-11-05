"""邮件模板：纯文本 + 简洁 HTML。

模板只接受白名单字段；用户内容进 HTML 前统一 escape，避免把昵称/评论
直接拼进邮件造成 HTML 注入。事务类邮件不做退订，通知类由用户偏好控制。
"""
from __future__ import annotations

from html import escape

from .core.config import settings


def _base(title: str, body_html: str, link: str = "", link_label: str = "") -> str:
    site = escape(settings.site_url.rstrip("/"))
    button = (
        f'<p style="margin:24px 0"><a href="{escape(link)}" '
        f'style="background:#2563eb;color:#fff;padding:10px 18px;border-radius:8px;'
        f'text-decoration:none">{escape(link_label or "打开 RoboWiki")}</a></p>'
        if link else ""
    )
    return f"""<!doctype html>
<html lang="zh-CN"><body style="margin:0;background:#f5f7fb;font-family:-apple-system,
BlinkMacSystemFont,'Segoe UI',sans-serif;color:#0f172a">
<table role="presentation" width="100%" cellpadding="0" cellspacing="0"
 style="background:#f5f7fb;padding:28px 12px"><tr><td align="center">
<table role="presentation" width="100%" cellpadding="0" cellspacing="0"
 style="max-width:560px;background:#fff;border:1px solid #e2e8f0;border-radius:14px;
 padding:28px"><tr><td>
<div style="font-size:13px;letter-spacing:.08em;color:#2563eb;font-weight:700">
ROBOWIKI</div>
<h1 style="font-size:20px;margin:8px 0 14px">{escape(title)}</h1>
<div style="font-size:14px;line-height:1.8;color:#334155">{body_html}</div>
{button}
<p style="margin:22px 0 0;font-size:12px;color:#94a3b8">RoboWiki ·
<a href="{site}" style="color:#64748b">{site}</a></p>
</td></tr></table></td></tr></table></body></html>"""


def render_email(kind: str, **ctx: object) -> tuple[str, str, str]:
    """返回 (subject, text, html)。kind 是固定枚举，未知 kind 走通知模板。"""
    site = settings.site_url.rstrip("/")
    minutes = ctx.get("minutes") or settings.email_token_minutes
    token = str(ctx.get("token") or "")
    email = str(ctx.get("email") or "")
    title = str(ctx.get("title") or "RoboWiki 通知")
    body = str(ctx.get("body") or "")
    link = str(ctx.get("link") or "")
    label = str(ctx.get("link_label") or "打开 RoboWiki")
    if link.startswith("/"):
        link = site + link

    if kind == "verify":
        subject = "RoboWiki 邮箱验证"
        text = (f"你的邮箱验证令牌：{token}\n有效期 {minutes} 分钟。\n"
                "在站点登录后打开「验证邮箱」输入该令牌即可。")
        html = _base("验证你的邮箱", f"<p>你的邮箱验证令牌：</p>"
                     f"<p style='font-size:20px;font-weight:700;letter-spacing:2px'>{escape(token)}</p>"
                     f"<p>有效期 {escape(str(minutes))} 分钟。在站点登录后打开「验证邮箱」输入即可。</p>")
        return subject, text, html
    if kind == "reset":
        subject = "RoboWiki 重置密码"
        text = (f"你的密码重置令牌：{token}\n有效期 {minutes} 分钟。\n"
                "在登录框选择「找回密码」并输入该令牌与新密码。")
        html = _base("重置密码", f"<p>你的密码重置令牌：</p>"
                     f"<p style='font-size:20px;font-weight:700;letter-spacing:2px'>{escape(token)}</p>"
                     f"<p>有效期 {escape(str(minutes))} 分钟。若不是你本人操作，请忽略本邮件。</p>")
        return subject, text, html
    if kind == "change_email":
        subject = "RoboWiki 确认绑定新邮箱"
        text = (f"确认把 RoboWiki 账号绑定到 {email}。\n验证令牌：{token}\n"
                f"有效期 {minutes} 分钟。")
        html = _base("确认绑定新邮箱",
                     f"<p>确认把账号绑定到 <strong>{escape(email)}</strong>。</p>"
                     f"<p style='font-size:20px;font-weight:700;letter-spacing:2px'>{escape(token)}</p>"
                     f"<p>有效期 {escape(str(minutes))} 分钟。若不是你本人操作，请忽略本邮件。</p>")
        return subject, text, html
    if kind == "test":
        subject = "RoboWiki SMTP 测试"
        text = "这是一封 RoboWiki SMTP 测试邮件。能收到说明配置可用。"
        html = _base("SMTP 配置可用", "<p>这是一封测试邮件。能收到说明 SMTP 配置可用。</p>")
        return subject, text, html
    if kind == "security":
        subject = str(ctx.get("subject") or "RoboWiki 账号安全提醒")
        text = f"{body}\n\n如果不是你本人操作，请立即修改密码并退出全部设备。\n{site}/login"
        html = _base(title, f"<p>{escape(body)}</p>"
                     "<p>如果不是你本人操作，请立即修改密码并退出全部设备。</p>",
                     f"{site}/login", "打开账号中心")
        return subject, text, html

    subject = str(ctx.get("subject") or "RoboWiki 通知")
    text = f"{body}\n\n{link}\n\n可在账号中心关闭邮件提醒。"
    html = _base(title, f"<p>{escape(body)}</p>",
                 link, label)
    return subject, text, html
