from datetime import date, datetime, timedelta


def resolve_date_range(event: dict) -> tuple[date, date]:
    raw = (event or {}).get("date")
    if raw:
        parsed = datetime.strptime(raw, "%m/%d/%Y").date()
        days_since_sunday = (parsed.weekday() + 1) % 7
        week_start = parsed - timedelta(days=days_since_sunday)
        return week_start, week_start + timedelta(days=7)
    today = date.today()
    days_since_sunday = (today.weekday() + 1) % 7  # 0 when today is Sunday
    week_start = today - timedelta(days=days_since_sunday)
    return week_start, today
