"""邮件发送：开发用日志，生产用 SMTP。不在 API 响应里泄露令牌。

失败策略：**不吞异常**。配置缺失、连不上、认证失败、被拒收都会抛
`MailError`，调用方（认证路由）据此决定回 503 还是只记日志；错误文本只
描述「哪个环节坏了」，不带口令、邮件正文或收件人地址。
"""
from __future__ import annotations

import logging
import smtplib
import ssl
from email.message import EmailMessage

from .core.config import settings

log = logging.getLogger("robowiki.mailer")

#: 连接/读写的总超时；邮件是交互链路，不能把请求拖到网关超时
_SMTP_TIMEOUT_S = 15.0

#: email_mode 只接受这两个值；写错时宁可显式失败，也不要静默当 log
_MODES = ("log", "smtp")


class MailError(RuntimeError):
    """发信失败：配置缺失 / SMTP 拒绝 / 网络不可达。"""


def send_email(to: str, subject: str, text: str, html: str | None = None) -> None:
    to = (to or "").strip()
    if not to:
        raise MailError("收件人为空，未发送邮件")

    mode = (settings.email_mode or "").strip().lower()
    if mode == "smtp":
        _send_smtp(to, subject, text, html)
        return
    if mode == "log":
        # 开发模式：令牌只写服务端日志，不进 API 响应
        print(f"[email:dev] to={to} subject={subject}\n{text}", flush=True)
        return
    raise MailError(
        f"EMAIL_MODE={settings.email_mode!r} 不支持；只能是 {' / '.join(_MODES)}")


def enqueue_email(db, *, to: str, subject: str, text: str, html: str | None = None,
                  kind: str = "notification", user_id: int | None = None,
                  dedupe_key: str | None = None):
    """把邮件写进 outbox，由 worker 发送。

    不 commit：调用方的主事务一起落库；邮件失败不能回滚业务通知。
    """
    from .models import EmailOutbox

    to = (to or "").strip()
    if not to:
        return None
    if dedupe_key:
        from sqlmodel import select
        exists = db.exec(select(EmailOutbox).where(
            EmailOutbox.dedupe_key == dedupe_key)).first()
        if exists is not None:
            return exists
    job = EmailOutbox(user_id=user_id, to_addr=to, subject=subject[:200],
                      text=text[:20000], html=(html or None),
                      kind=kind[:40], dedupe_key=dedupe_key)
    db.add(job)
    return job


def _send_smtp(to: str, subject: str, text: str, html: str | None = None) -> None:
    host = (settings.smtp_host or "").strip()
    if not host:
        raise MailError("EMAIL_MODE=smtp 但未配置 SMTP_HOST")
    port = int(settings.smtp_port or 0)
    if not 0 < port <= 65535:
        raise MailError(f"SMTP_PORT 不合法：{settings.smtp_port!r}")
    sender = (settings.smtp_from or "").strip()
    if not sender:
        raise MailError("EMAIL_MODE=smtp 但未配置 SMTP_FROM")
    user = (settings.smtp_user or "").strip()
    if user and not settings.smtp_password:
        raise MailError("配置了 SMTP_USER 但 SMTP_PASSWORD 为空")

    msg = EmailMessage()
    msg["From"] = sender
    msg["To"] = to
    msg["Subject"] = subject
    msg.set_content(text)
    if html:
        msg.add_alternative(html, subtype="html")

    server: smtplib.SMTP | None = None
    try:
        ctx = ssl.create_default_context()
        if settings.smtp_ssl or port == 465:
            # 465 是隐式 SSL（阿里云 DirectMail 推荐），连上就是 TLS，不再 STARTTLS
            server = smtplib.SMTP_SSL(host, port, timeout=_SMTP_TIMEOUT_S, context=ctx)
        else:
            server = smtplib.SMTP(host, port, timeout=_SMTP_TIMEOUT_S)
        server.ehlo()
        if not settings.smtp_ssl and port != 465 and settings.smtp_starttls:
            # 默认上下文会校验证书链；不要用无校验的 _create_unverified_context
            server.starttls(context=ctx)
            server.ehlo()
        if user:
            server.login(user, settings.smtp_password or "")
        server.send_message(msg)
    except MailError:
        raise
    except smtplib.SMTPAuthenticationError as exc:
        raise MailError(
            f"SMTP 认证失败（{host}:{port}）；检查 SMTP_USER / SMTP_PASSWORD"
        ) from exc
    except smtplib.SMTPRecipientsRefused as exc:
        raise MailError(f"SMTP 拒收收件人（{host}:{port}）；检查邮箱是否存在") from exc
    except smtplib.SMTPException as exc:
        raise MailError(
            f"SMTP 发送失败（{host}:{port}）：{type(exc).__name__}: {exc}"
        ) from exc
    except (OSError, ssl.SSLError) as exc:
        raise MailError(
            f"无法连接 SMTP（{host}:{port}）：{type(exc).__name__}: {exc}"
        ) from exc
    finally:
        # quit 失败（对方已断）不应盖掉真正的发送结果
        if server is not None:
            try:
                server.quit()
            except (smtplib.SMTPException, OSError):
                pass
    log.info("email sent to=%s subject=%s", to, subject)
