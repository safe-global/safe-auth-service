from app.config import settings

from .base import get_mail_base_html_template


def get_register_html_mail_content(temporary_token: str) -> str:
    return get_mail_base_html_template(
        f"""
            <div>
                <h1>Welcome to Safe Dashboard!</h1>
                <p>Thank you for signing up. Please verify your email address by clicking the button below:</p>
                <a href="{settings.FRONTEND_BASE_URL}/register?token={temporary_token}">Verify Email</a>
                <p>If you didn't request this, please ignore this email.</p>
            </div>
        """
    )


def get_register_text_mail_content(temporary_token: str) -> str:
    return f"""
        Welcome to Safe Dashboard!

        Thank you for signing up. Please verify your email address by clicking the link below:

        {settings.FRONTEND_BASE_URL}/register?token={temporary_token}

        If you didn't request this, please ignore this email.
    """
