## sends emails (and google chat messages) for the celery jobs
## default is MailHog on localhost:1025, open http://localhost:8025 to see the emails
import os
import json
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from urllib import request as urlrequest

SMTP_HOST = os.environ.get("SMTP_HOST", "localhost")
SMTP_PORT = int(os.environ.get("SMTP_PORT", 1025))
SMTP_USER = os.environ.get("SMTP_USER")          ## only needed for a real mail server like gmail
SMTP_PASSWORD = os.environ.get("SMTP_PASSWORD")
SENDER = os.environ.get("MAIL_SENDER", "noreply@examportal.com")
GCHAT_WEBHOOK_URL = os.environ.get("GCHAT_WEBHOOK_URL")  ## optional google chat space webhook


def send_email(to, subject, html):
    message = MIMEMultipart()
    message["From"] = SENDER
    message["To"] = to
    message["Subject"] = subject
    message.attach(MIMEText(html, "html"))
    with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
        if SMTP_USER:
            server.starttls()
            server.login(SMTP_USER, SMTP_PASSWORD)
        server.send_message(message)


def send_gchat(text):
    if not GCHAT_WEBHOOK_URL:
        return
    body = json.dumps({"text": text}).encode("utf-8")
    req = urlrequest.Request(GCHAT_WEBHOOK_URL, data=body, headers={"Content-Type": "application/json; charset=UTF-8"})
    urlrequest.urlopen(req)
