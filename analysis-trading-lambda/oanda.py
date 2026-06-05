import logging
import requests

from config import OANDA_API_KEY, OANDA_ACCOUNT_ID, OANDA_BASE_URL, RISK_PER_TRADE

logger = logging.getLogger(__name__)

REQUEST_TIMEOUT = 30


def get_account_nav() -> float:
    url = f"{OANDA_BASE_URL}/v3/accounts/{OANDA_ACCOUNT_ID}/summary"
    headers = {"Authorization": f"Bearer {OANDA_API_KEY}"}
    logger.info("Fetching account NAV from OANDA | url=%s | account_id=%s", url, OANDA_ACCOUNT_ID)

    response = requests.get(url, headers=headers, timeout=REQUEST_TIMEOUT)
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
    response = requests.get(url, headers=headers, timeout=REQUEST_TIMEOUT)
    response.raise_for_status()
    prices = response.json()["prices"][0]
    # use ask for buys (we pay the ask), bid for sells
    price = float(prices["asks"][0]["price"]) if direction == "buy" else float(prices["bids"][0]["price"])
    logger.info("Current price for %s (%s): %.5f", instrument, direction, price)
    return price


def calculate_stop_price(entry_price: float, direction: str, pip_size: float, stop_loss_pips: int) -> str:
    stop_distance = stop_loss_pips * pip_size
    stop = entry_price - stop_distance if direction == "buy" else entry_price + stop_distance
    decimal_places = 3 if pip_size == 0.01 else 5
    return f"{stop:.{decimal_places}f}"


def calculate_take_profit_price(entry_price: float, direction: str, pip_size: float, take_profit_pips: int) -> str:
    take_profit_distance = take_profit_pips * pip_size
    tp = entry_price + take_profit_distance if direction == "buy" else entry_price - take_profit_distance
    decimal_places = 3 if pip_size == 0.01 else 5
    return f"{tp:.{decimal_places}f}"


def calculate_units(nav: float, pip_size: float, stop_loss_pips: int) -> int:
    risk_amount = nav * RISK_PER_TRADE
    raw = int(risk_amount / (stop_loss_pips * pip_size))
    result = min(max(raw, 1000), 100_000)
    logger.info(
        "Calculated trade units | nav=%.2f | risk_amount=%.2f | stop_loss_pips=%d | raw=%d | clamped=%d",
        nav, risk_amount, stop_loss_pips, raw, result,
    )
    return result


def has_open_position(instrument: str) -> bool:
    url = f"{OANDA_BASE_URL}/v3/accounts/{OANDA_ACCOUNT_ID}/openPositions"
    headers = {"Authorization": f"Bearer {OANDA_API_KEY}"}
    response = requests.get(url, headers=headers, timeout=REQUEST_TIMEOUT)
    response.raise_for_status()
    positions = response.json().get("positions", [])
    return any(p["instrument"] == instrument for p in positions)


def close_trade(oanda_trade_id: str) -> dict:
    url = f"{OANDA_BASE_URL}/v3/accounts/{OANDA_ACCOUNT_ID}/trades/{oanda_trade_id}/close"
    headers = {
        "Authorization": f"Bearer {OANDA_API_KEY}",
        "Content-Type": "application/json",
    }
    logger.info("Closing trade early | trade_id=%s", oanda_trade_id)
    response = requests.put(url, json={"units": "ALL"}, headers=headers, timeout=REQUEST_TIMEOUT)
    if not response.ok:
        logger.error("OANDA close trade error: %s", response.text)
    response.raise_for_status()
    order_fill = response.json().get("orderFillTransaction", {})
    exit_price = float(order_fill.get("price", 0))
    profit_loss = float(order_fill.get("pl", 0))
    logger.info("Trade closed early | trade_id=%s | exit_price=%.5f | pl=%.2f", oanda_trade_id, exit_price, profit_loss)
    return {"exit_price": exit_price, "profit_loss": profit_loss}


def execute_trade(instrument: str, direction: str, units: int, stop_loss_price: str, take_profit_price: str) -> str:
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
            "takeProfitOnFill": {
                "price": take_profit_price,
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
        "Submitting %s order | instrument=%s | units=%d | stop=%s | tp=%s | url=%s",
        direction, instrument, units, stop_loss_price, take_profit_price, url,
    )
    logger.debug("Order payload: %s", payload)

    response = requests.post(url, json=payload, headers=headers, timeout=REQUEST_TIMEOUT)
    logger.debug("POST %s -> HTTP %s", url, response.status_code)
    if not response.ok:
        logger.error("OANDA error response: %s", response.text)
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
