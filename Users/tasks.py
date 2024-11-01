import os

from celery import shared_task
from django.core.mail import EmailMessage


@shared_task(queue="email")
def send_email(subject, message, to_emails, from_email=None, cc=None, bcc=None):
    cc = cc or []
    bcc = bcc or []

    if from_email is None:
        from_email = os.getenv("EMAIL_ID")
        assert from_email is not None, "Make sure you set valid email"

    sender = EmailMessage(subject, message, from_email, to_emails, cc, bcc)
    sender.send()
