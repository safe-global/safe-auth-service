from typing import Optional

from pydantic import AnyUrl, HttpUrl

from ..models import SiweMessageRequest


class SiweMessageRequestFactory:
    @staticmethod
    def create(
        domain: str = "example.com",
        address: str = "0x32Be343B94f860124dC4fEe278FDCBD38C102D88",
        chain_id: int = 1,
        uri: AnyUrl = HttpUrl("https://valid-url.com"),
        statement: Optional[str] = "Test statement",
    ) -> SiweMessageRequest:
        return SiweMessageRequest(
            domain=domain,
            address=address,
            chain_id=chain_id,
            uri=uri,
            statement=statement,
        )
