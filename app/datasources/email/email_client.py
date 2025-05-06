import logging
import smtplib
from email.message import EmailMessage

from ...config import settings
from .templates.register import (
    get_register_html_mail_content,
    get_register_text_mail_content,
)
from .templates.reset_password import (
    get_reset_password_html_mail_content,
    get_reset_password_text_mail_content,
)

logger = logging.getLogger(__name__)


def send_email(to: str, subject: str, html_content: str, text_content: str) -> bool:
    """
    Sends an email to an email address using the configured provider

    Args:
        to: Email address to send the email to
        subject: Subject of the email
        html_content: HTML version of the email content
        text_content: Plain text fallback version of the email content

    Returns:
        `True` if the email was sent, `False` otherwise
    """
    msg = EmailMessage()
    msg.set_content(html_content, subtype="html")
    msg.add_alternative(text_content, subtype="plain")

    msg["Subject"] = subject
    msg["From"] = settings.SMTP_FROM_ADDRESS
    msg["To"] = to

    try:
        with smtplib.SMTP(settings.SMTP_SERVER, settings.SMTP_PORT) as smtp_client:
            if settings.SMTP_STARTTLS:
                smtp_client.starttls()
            if settings.SMTP_USERNAME:
                smtp_client.login(settings.SMTP_USERNAME, settings.SMTP_PASSWORD)
            smtp_client.send_message(msg)
            return True
    except (smtplib.SMTPException, IOError) as e:
        logger.exception("Problem while sending email", exc_info=e)
    return False


def send_register_temporary_token_email(to: str, token: str) -> bool:
    return send_email(
        to,
        "Verify Your Account - Safe Dashboard",
        get_register_html_mail_content(token),
        get_register_text_mail_content(token),
    )


def send_reset_password_temporary_token_email(to: str, token: str) -> bool:
    return send_email(
        to,
        "Recover Your Password - Safe Dashboard",
        get_reset_password_html_mail_content(token),
        get_reset_password_text_mail_content(token),
    )
