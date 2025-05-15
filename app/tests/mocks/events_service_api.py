import uuid
from typing import Any

events_service_api_response: dict[str, Any] = {
    "id": uuid.uuid4(),
    "url": "http://example.com",
    "authorization": "Bearer token",
    "chains": [1, 2],
    "events": ["SEND_TOKEN_TRANSFERS", "SEND_CONFIRMATIONS"],
    "isActive": True,
}
