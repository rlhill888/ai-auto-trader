import logging
import requests

from config import OANDA_API_KEY, OANDA_ACCOUNT_ID, OANDA_BASE_URL

logger = logging.getLogger(__name__)

HEADERS = {
    "Authorization": f"Bearer {OANDA_API_KEY}",
    "Content-Type": "application/json",
}


def get_trade_state(oanda_trade_id: str) -> dict:
    url = f"{OANDA_BASE_URL}/v3/accounts/{OANDA_ACCOUNT_ID}/trades/{oanda_trade_id}"
    logger.info("Fetching trade state from OANDA | oanda_trade_id=%s", oanda_trade_id)

    response = requests.get(url, headers=HEADERS, timeout=10)
    logger.debug("GET %s -> HTTP %s", url, response.status_code)
    response.raise_for_status()

    trade = response.json().get("trade", {})
    logger.debug("OANDA trade response: %s", trade)

    state = trade.get("state", "UNKNOWN")
    logger.info("OANDA trade state | oanda_trade_id=%s | state=%s", oanda_trade_id, state)

    return trade
