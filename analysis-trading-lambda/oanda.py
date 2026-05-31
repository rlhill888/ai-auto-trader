import logging
import requests

from config import OANDA_API_KEY, OANDA_ACCOUNT_ID, OANDA_BASE_URL

logger = logging.getLogger(__name__)


def get_account_nav() -> float:
    url = f"{OANDA_BASE_URL}/v3/accounts/{OANDA_ACCOUNT_ID}/summary"
    headers = {"Authorization": f"Bearer {OANDA_API_KEY}"}
    logger.info("Fetching account NAV from OANDA | url=%s | account_id=%s", url, OANDA_ACCOUNT_ID)

    response = requests.get(url, headers=headers, timeout=10)
    logger.debug("GET %s -> HTTP %s", url, response.status_code)
    response.raise_for_status()

    body = response.json()
    logger.debug("Account summary response body: %s", body)

    nav = float(body["account"]["NAV"])
    logger.info("Account NAV retrieved | nav=%.2f", nav)
    return nav


def calculate_units(nav: float) -> int:
    """Trade 1% of NAV, rounded to nearest 1000, clamped between 1000 and 100000."""
    raw = int(nav * 0.01)
    rounded = max(1000, round(raw / 1000) * 1000)
    result = min(rounded, 100_000)
    logger.info(
        "Calculated trade units | nav=%.2f | 1pct_raw=%d | rounded=%d | clamped=%d",
        nav, raw, rounded, result,
    )
    return result


def execute_trade(instrument: str, direction: str, units: int) -> str:
    signed_units = units if direction == "buy" else -units
    payload = {
        "order": {
            "type": "MARKET",
            "instrument": instrument,
            "units": str(signed_units),
            "timeInForce": "FOK",
            "positionFill": "DEFAULT",
        }
    }
    headers = {
        "Authorization": f"Bearer {OANDA_API_KEY}",
        "Content-Type": "application/json",
    }
    url = f"{OANDA_BASE_URL}/v3/accounts/{OANDA_ACCOUNT_ID}/orders"

    logger.info(
        "Submitting %s order | instrument=%s | units=%d | signed_units=%d | url=%s",
        direction, instrument, units, signed_units, url,
    )
    logger.debug("Order payload: %s", payload)

    response = requests.post(url, json=payload, headers=headers, timeout=10)
    logger.debug("POST %s -> HTTP %s", url, response.status_code)
    response.raise_for_status()

    data = response.json()
    logger.debug("Order response body: %s", data)

    order_fill = data.get("orderFillTransaction", {})
    order_cancel = data.get("orderCancelTransaction", {})
    order_create = data.get("orderCreateTransaction", {})

    order_id = order_fill.get("id") or order_create.get("id", "unknown")
    fill_price = order_fill.get("price", "N/A")
    fill_pl = order_fill.get("pl", "N/A")
    cancel_reason = order_cancel.get("reason", None)

    if order_fill.get("id"):
        logger.info(
            "Order FILLED | transaction_id=%s | instrument=%s | direction=%s | units=%d | fill_price=%s | pl=%s",
            order_id, instrument, direction, units, fill_price, fill_pl,
        )
    elif cancel_reason:
        logger.warning(
            "Order CANCELLED | transaction_id=%s | instrument=%s | direction=%s | units=%d | reason=%s",
            order_id, instrument, direction, units, cancel_reason,
        )
    else:
        logger.info(
            "Order CREATED (pending fill) | transaction_id=%s | instrument=%s | direction=%s | units=%d",
            order_id, instrument, direction, units,
        )

    return order_id
