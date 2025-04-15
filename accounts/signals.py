import logging

from django.contrib.auth import get_user_model
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import send_mail
from django.db.models.signals import post_save
from django.dispatch.dispatcher import receiver
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode

from educ_backend import settings

logger = logging.getLogger(__name__)
User = get_user_model()

@receiver(post_save, sender=User)
def send_password_reset_email(sender, instance, created, **kwargs):
    if created:
        try:
            token = default_token_generator.make_token(instance)
            uid = urlsafe_base64_encode(force_bytes(instance.pk))
            full_url = f"http://127.0.0.1:3000/reset?uid={uid}&token={token}" # domain
            html_message = f"""
            <html>
                <body style="font-family: Arial, sans-serif; color: #333;">
                    <h2>Welcome, {instance.first_name}!</h2>
                    <p>Please set your password by clicking the button below:</p>
                    <a href="{full_url}" style="display: inline-block; padding: 10px 20px; background-color: #4F46E5; color: white; text-decoration: none; border-radius: 5px;">
                        Set Password
                    </a>
                    <p style="font-size: 12px; color: #666;">This link expires in 24 hours. If you didn’t request this, ignore this email.</p>
                </body>
            </html>
            """
            send_mail(
                subject="Set Your Account Password",
                message=f"Hi {instance.first_name},\n\nSet your password here: {full_url}",
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[instance.email],
                html_message=html_message,
                fail_silently=False,
            )
            logger.info(f"Password reset email sent to {instance.email}")
        except Exception as e:
            logger.error(f"Failed to send reset email to {instance.email}: {e}")