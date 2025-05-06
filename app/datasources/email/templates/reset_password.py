from app.config import settings

from .base import get_mail_base_html_template


def get_reset_password_html_mail_content(temporary_token: str) -> str:
    return get_mail_base_html_template(
        f"""
            <div>
                <h1>Password Recovery for Safe Dashboard</h1>
                <p>You have requested to reset your password. Please click the button below to proceed:</p>
                <a href="{settings.FRONTEND_BASE_URL}/reset-password?token={temporary_token}">Reset Password</a>
                <p>If you didn't request this, please ignore this email.</p>
            </div>
        """
    )


def get_reset_password_text_mail_content(temporary_token: str) -> str:
    return f"""
        Password Recovery for Safe Dashboard

        You have requested to reset your password. Please click the link below to proceed:

        {settings.FRONTEND_BASE_URL}/reset-password?token={temporary_token}

        If you didn't request this, please ignore this email.
    """
