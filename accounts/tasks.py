from celery import shared_task
from django.core.mail import send_mail
from celery import shared_task
from django.core.mail import EmailMessage
from django.template.loader import render_to_string
from .templates.otp_email_template import get_otp_email_html

@shared_task
def send_otp_email_task(email, otp, first_name, reset_password_url=None):
    html_content = get_otp_email_html(first_name, otp, reset_password_url)
    email_message = EmailMessage(
        subject="Your OTP for Password Reset",
        body=html_content,
        from_email=None,  # Uses DEFAULT_FROM_EMAIL
        to=[email],
    )
    email_message.content_subtype = "html"
    email_message.send(fail_silently=False)
    