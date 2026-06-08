from datetime import date, datetime, timedelta


def resolve_week_start(event: dict) -> date:
    raw = (event or {}).get("date")
    if raw:
        parsed = datetime.strptime(raw, "%m/%d/%Y").date()
        days_since_sunday = (parsed.weekday() + 1) % 7
        return parsed - timedelta(days=days_since_sunday)
    today = date.today()
    # Find the most recently completed Sunday–Saturday week.
    # Go to the most recent Saturday on or before today, then back 6 days to that week's Sunday.
    days_to_last_saturday = (today.weekday() + 2) % 7
    last_saturday = today - timedelta(days=days_to_last_saturday)
    return last_saturday - timedelta(days=6)
