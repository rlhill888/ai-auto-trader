import logging
import requests

from config import OANDA_API_KEY, OANDA_ACCOUNT_ID, OANDA_BASE_URL, STOP_LOSS_PIPS, RISK_PER_TRADE

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


def get_pip_size(instrument: str) -> float:
    return 0.01 if "JPY" in instrument else 0.0001


def get_current_price(instrument: str, direction: str) -> float:
    url = f"{OANDA_BASE_URL}/v3/accounts/{OANDA_ACCOUNT_ID}/pricing?instruments={instrument}"
    headers = {"Authorization": f"Bearer {OANDA_API_KEY}"}
    response = requests.get(url, headers=headers, timeout=10)
    response.raise_for_status()
    prices = response.json()["prices"][0]
    # use ask for buys (we pay the ask), bid for sells
    price = float(prices["asks"][0]["price"]) if direction == "buy" else float(prices["bids"][0]["price"])
    logger.info("Current price for %s (%s): %.5f", instrument, direction, price)
    return price


def calculate_stop_price(entry_price: float, direction: str, pip_size: float) -> str:
    stop_distance = STOP_LOSS_PIPS * pip_size
    stop = entry_price - stop_distance if direction == "buy" else entry_price + stop_distance
    decimal_places = 3 if pip_size == 0.01 else 5
    return f"{stop:.{decimal_places}f}"


def calculate_units(nav: float, pip_size: float) -> int:
    """Risk exactly 0.5% of NAV per trade based on stop loss distance."""
    risk_amount = nav * RISK_PER_TRADE
    pip_value_per_unit = pip_size
    raw = int(risk_amount / (STOP_LOSS_PIPS * pip_value_per_unit))
    result = min(max(raw, 1000), 100_000)
    logger.info(
        "Calculated trade units | nav=%.2f | risk_amount=%.2f | stop_loss_pips=%d | raw=%d | clamped=%d",
        nav, risk_amount, STOP_LOSS_PIPS, raw, result,
    )
    return result


def execute_trade(instrument: str, direction: str, units: int, stop_loss_price: str) -> str:
    signed_units = units if direction == "buy" else -units
    payload = {
        "order": {
            "type": "MARKET",
            "instrument": instrument,
            "units": str(signed_units),
            "timeInForce": "FOK",
            "positionFill": "DEFAULT",
            "stopLossOnFill": {
                "price": stop_loss_price,
                "timeInForce": "GTC",
            },
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
    trade_id = order_fill.get("tradeOpened", {}).get("tradeID")
    fill_price = order_fill.get("price", "N/A")
    fill_pl = order_fill.get("pl", "N/A")
    cancel_reason = order_cancel.get("reason", None)

    if order_fill.get("id"):
        logger.info(
            "Order FILLED | transaction_id=%s | trade_id=%s | instrument=%s | direction=%s | units=%d | fill_price=%s | pl=%s",
            order_id, trade_id, instrument, direction, units, fill_price, fill_pl,
        )
    elif cancel_reason:
        logger.warning(
            "Order CANCELLED | transaction_id=%s | instrument=%s | direction=%s | units=%d | reason=%s",
            order_id, instrument, direction, units, cancel_reason,
        )
    else:
        logger.info(
            "Order CREATED (pending fill) | transaction_id=%s | trade_id=%s | instrument=%s | direction=%s | units=%d",
            order_id, trade_id, instrument, direction, units,
        )

    return order_id, trade_id
