from datetime import date, datetime, timedelta


def resolve_week_start(event: dict) -> date:
    raw = (event or {}).get("date")
    if raw:
        return datetime.strptime(raw, "%m/%d/%Y").date()
    today = date.today()
    # weekday(): Mon=0 … Sat=5, Sun=6 → days to subtract to land on Sunday
    days_since_sunday = (today.weekday() + 1) % 7
    return today - timedelta(days=days_since_sunday)
