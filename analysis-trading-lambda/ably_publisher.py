import base64
import json
import logging

import requests

from config import ABLY_API_KEY

logger = logging.getLogger()


def publish_ably_event(event_name: str, data: dict) -> None:
    if not ABLY_API_KEY:
        return
    token = base64.b64encode(ABLY_API_KEY.encode()).decode()
    try:
        requests.post(
            "https://rest.ably.io/channels/trading/messages",
            headers={
                "Authorization": f"Basic {token}",
                "Content-Type": "application/json",
            },
            json={"name": event_name, "data": json.dumps(data)},
            timeout=3,
        )
    except Exception:
        logger.exception("Failed to publish Ably event: %s", event_name)
