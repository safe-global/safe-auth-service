import logging
import smtplib
from email.message import EmailMessage

from ...config import settings

logger = logging.getLogger(__name__)


def send_email(to: str, content: str, subject: str) -> bool:
    """
    Sends an email to an email address using the configured provider

    Args:
        to: Email address to send the email to
        content: Content of the email
        subject: Subject of the email

    Returns:
        `True` if the email was sent, `False` otherwise
    """
    msg = EmailMessage()
    msg.set_content(content)
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
        f"Please use this token to register an user {token}",
        "Register token for Safe Auth Service",
    )

def send_reset_password_temporary_token_email(to: str, token: str) -> bool:
    return send_email(
        to,
f"""
            Please follow the following link to reset the password:
            {settings.FORGOT_PASSWORD_URL}?token={token}
       """,
        "Reset password token for Safe Auth Service",
    )
