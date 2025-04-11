import logging
import smtplib
from email.message import EmailMessage

from ...config import settings

logger = logging.getLogger(__name__)


class EmailClient:
    def send_email(self, to: str, content: str) -> bool:
        """
        Sends an email to an email address using the configured provider

        Args:
            to: Email address to send the email to
            content: Content of the email

        Returns:
            `True` if the email was sent, `False` otherwise
        """

        # TODO Add auth/ssl depending on the provider
        msg = EmailMessage()
        msg.set_content(content)
        msg["Subject"] = "Register token for Safe Auth Service"
        msg["From"] = settings.SMTP_FROM_ADDRESS
        msg["To"] = to
        try:
            with smtplib.SMTP(settings.SMTP_SERVER, settings.SMTP_PORT) as smtp:
                smtp.send_message(msg)
                return True
        except (smtplib.SMTPException, IOError) as e:
            logger.exception("Problem while sending email", exc_info=e)
            return False

    def send_temporary_token_email(self, to: str, token: str) -> bool:
        return self.send_email(
            to,
            f"""
                    Please use this token to register an user {token}
                   """,
        )
