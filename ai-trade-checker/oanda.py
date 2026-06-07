import logging
import requests

from config import OANDA_API_KEY, OANDA_ACCOUNT_ID, OANDA_BASE_URL

logger = logging.getLogger(__name__)

HEADERS = {
    "Authorization": f"Bearer {OANDA_API_KEY}",
    "Content-Type": "application/json",
}


def close_trade(oanda_trade_id: str) -> dict:
    url = f"{OANDA_BASE_URL}/v3/accounts/{OANDA_ACCOUNT_ID}/trades/{oanda_trade_id}/close"
    logger.info("Closing trade early | oanda_trade_id=%s", oanda_trade_id)
    response = requests.put(url, json={"units": "ALL"}, headers=HEADERS, timeout=10)
    if not response.ok:
        logger.error("OANDA close trade error: %s", response.text)
    response.raise_for_status()
    order_fill = response.json().get("orderFillTransaction", {})
    exit_price = float(order_fill.get("price", 0))
    profit_loss = float(order_fill.get("pl", 0))
    logger.info("Trade closed early | oanda_trade_id=%s | exit_price=%.5f | pl=%.2f", oanda_trade_id, exit_price, profit_loss)
    return {"exit_price": exit_price, "profit_loss": profit_loss}


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
