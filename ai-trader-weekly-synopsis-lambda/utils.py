from datetime import date, datetime, timedelta


def resolve_week_start(event: dict) -> date:
    raw = (event or {}).get("date")
    if raw:
        return datetime.strptime(raw, "%m/%d/%Y").date()
    today = date.today()
    # weekday(): Mon=0 … Sat=5, Sun=6
    # Always resolve to the most recently *completed* Sunday–Saturday week.
    # If today is Sunday the modulo would return 0 (today), so treat it as 7
    # to land on the previous Sunday instead.
    days_since_sunday = (today.weekday() + 1) % 7 or 7
    return today - timedelta(days=days_since_sunday)
