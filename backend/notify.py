"""站主推送：Server酱(SERVERCHAN_KEY) 或 SMTP 邮件(SMTP_HOST/USER/PASS/NOTIFY_TO)。
都没配就静默。main.py 与 sparky.py 共用；调用方自己决定要不要放进线程。"""
import os
import requests as _rq


def notify_owner(title: str, body: str) -> None:
    sc = (os.getenv("SERVERCHAN_KEY") or "").strip()
    if sc:
        try:
            _rq.post(f"https://sctapi.ftqq.com/{sc}.send",
                     data={"title": title[:32], "desp": body[:800]}, timeout=10)
            print(f"[NOTIFY] serverchan 已推送: {title}", flush=True)
        except Exception as e:
            print(f"[NOTIFY] serverchan 失败: {e}", flush=True)
    host = (os.getenv("SMTP_HOST") or "").strip()
    if host:
        try:
            import smtplib
            from email.mime.text import MIMEText
            from email.header import Header
            user_ = os.getenv("SMTP_USER", ""); pwd = os.getenv("SMTP_PASS", "")
            to = os.getenv("NOTIFY_TO", user_)
            msg = MIMEText(body, "plain", "utf-8")
            msg["Subject"] = Header(title, "utf-8")
            msg["From"] = user_; msg["To"] = to
            with smtplib.SMTP_SSL(host, int(os.getenv("SMTP_PORT", "465")), timeout=15) as sm:
                sm.login(user_, pwd)
                sm.sendmail(user_, [to], msg.as_string())
            print(f"[NOTIFY] 邮件已发 {to}: {title}", flush=True)
        except Exception as e:
            print(f"[NOTIFY] 邮件失败: {e}", flush=True)

