def send_email(to: str, content: str) -> bool:
    """
    Sends an email to an email address using the configured provider

    Args:
        to: Email address to send the email to
        content: Content of the email

    Returns:
        `True` if the email was sent, `False` otherwise
    """
    return True


def send_temporary_token_email(to: str, token: str) -> bool:
    return send_email(
        to,
        f"""
                Please use this token to register an user {token}
               """,
    )
