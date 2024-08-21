class SiweMessageError(Exception):
    """Base class for exceptions in this module."""

    pass


class InvalidMessageFormatError(SiweMessageError):
    """Raised when the SIWE message format is invalid."""

    pass


class InvalidNonceError(SiweMessageError):
    """Raised when the nonce is invalid."""

    pass


class InvalidSignatureError(SiweMessageError):
    """Raised when the SIWE signature is invalid."""

    pass
