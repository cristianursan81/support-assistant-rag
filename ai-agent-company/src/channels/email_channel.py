"""Email channel — SMTP send."""
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart


def send_email(to_email: str, subject: str, body: str) -> bool:
    """
    Send an email via SMTP (Gmail by default).
    Returns True on success.
    """
    smtp_host = os.getenv("SMTP_HOST", "smtp.gmail.com")
    smtp_port = int(os.getenv("SMTP_PORT", "587"))
    smtp_user = os.getenv("SMTP_USER", "")
    smtp_password = os.getenv("SMTP_PASSWORD", "")
    from_name = os.getenv("SMTP_FROM_NAME", "GestorIA")

    if not smtp_user or not smtp_password:
        print("[Email] SMTP_USER or SMTP_PASSWORD not set — skipping send.")
        return False

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = f"{from_name} <{smtp_user}>"
    msg["To"] = to_email

    # Plain text part
    msg.attach(MIMEText(body, "plain", "utf-8"))

    # HTML part (simple wrap)
    html_body = body.replace("\n", "<br>")
    html = f"<html><body><p>{html_body}</p></body></html>"
    msg.attach(MIMEText(html, "html", "utf-8"))

    try:
        with smtplib.SMTP(smtp_host, smtp_port) as server:
            server.starttls()
            server.login(smtp_user, smtp_password)
            server.sendmail(smtp_user, to_email, msg.as_string())
        return True
    except Exception as e:
        print(f"[Email] send error: {e}")
        return False
