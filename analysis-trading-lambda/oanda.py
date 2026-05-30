import requests

from config import OANDA_API_KEY, OANDA_ACCOUNT_ID, OANDA_BASE_URL


def get_account_nav() -> float:
    url = f"{OANDA_BASE_URL}/v3/accounts/{OANDA_ACCOUNT_ID}/summary"
    headers = {"Authorization": f"Bearer {OANDA_API_KEY}"}
    response = requests.get(url, headers=headers, timeout=10)
    response.raise_for_status()
    nav = float(response.json()["account"]["NAV"])
    print(f"Account NAV: {nav}")
    return nav


def calculate_units(nav: float) -> int:
    """Trade 1% of NAV, rounded to nearest 1000, clamped between 1000 and 100000."""
    raw = int(nav * 0.01)
    rounded = max(1000, round(raw / 1000) * 1000)
    return min(rounded, 100_000)


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

    print(f"Executing {direction} order for {units} units of {instrument}")
    response = requests.post(url, json=payload, headers=headers, timeout=10)
    response.raise_for_status()

    data = response.json()
    order_fill = data.get("orderFillTransaction", {})
    order_id = order_fill.get("id") or data.get("orderCreateTransaction", {}).get("id", "unknown")
    print(f"OANDA order submitted, transaction ID: {order_id}")
    return order_id
