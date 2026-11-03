"""邮件发送：开发用日志，生产用 SMTP。不在 API 响应里泄露令牌。"""
from __future__ import annotations

import smtplib
from email.message import EmailMessage

from .core.config import settings


def send_email(to: str, subject: str, text: str) -> None:
    if settings.email_mode == "smtp":
        if not settings.smtp_host:
            raise RuntimeError("EMAIL_MODE=smtp 但未配置 SMTP_HOST")
        msg = EmailMessage()
        msg["From"] = settings.smtp_from
        msg["To"] = to
        msg["Subject"] = subject
        msg.set_content(text)
        with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=15) as s:
            if settings.smtp_starttls:
                s.starttls()
            if settings.smtp_user:
                s.login(settings.smtp_user, settings.smtp_password or "")
            s.send_message(msg)
        return

    # 开发模式：令牌只写服务端日志，不进 API 响应
    print(f"[email:dev] to={to} subject={subject}\n{text}")
