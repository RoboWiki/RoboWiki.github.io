"""SMTP 传输：465 隐式 SSL（阿里云 DirectMail）与 587 STARTTLS 二选一。"""
from __future__ import annotations


def test_smtp_ssl_uses_implicit_tls(monkeypatch):
    from app import mailer

    calls: dict[str, object] = {}

    class FakeSSL:
        def __init__(self, host, port, timeout=None, context=None):
            calls["tls"] = (host, port, context is not None)

        def ehlo(self):
            calls["ehlo"] = int(calls.get("ehlo", 0)) + 1

        def starttls(self, context=None):
            calls["starttls"] = True

        def login(self, user, password):
            calls["login"] = (user, password)

        def send_message(self, msg):
            calls["subject"] = msg["Subject"]

        def quit(self):
            pass

    def no_plain(*args, **kwargs):
        raise AssertionError("SMTP_SSL=true 时不应走明文 SMTP")

    monkeypatch.setattr(mailer.smtplib, "SMTP_SSL", FakeSSL)
    monkeypatch.setattr(mailer.smtplib, "SMTP", no_plain)
    for key, value in {
        "email_mode": "smtp",
        "smtp_host": "smtpdm.aliyun.com",
        "smtp_port": 465,
        "smtp_user": "no-reply@robowiki.org.cn",
        "smtp_password": "secret",
        "smtp_from": "RoboWiki <no-reply@robowiki.org.cn>",
        "smtp_ssl": True,
        "smtp_starttls": True,
    }.items():
        monkeypatch.setattr(mailer.settings, key, value)

    mailer.send_email("to@example.com", "测试主题", "正文")

    assert calls["tls"] == ("smtpdm.aliyun.com", 465, True)
    assert "starttls" not in calls
    assert calls["login"] == ("no-reply@robowiki.org.cn", "secret")
    assert calls["subject"] == "测试主题"
