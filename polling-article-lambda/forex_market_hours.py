from datetime import datetime
from zoneinfo import ZoneInfo


def is_forex_market_open() -> bool:
    now_et = datetime.now(tz=ZoneInfo("America/New_York"))
    day = now_et.weekday()  # Mon=0 ... Sat=5, Sun=6
    minutes_of_day = now_et.hour * 60 + now_et.minute
    five_pm = 17 * 60

    if day == 5:                                 # Saturday
        return False
    if day == 6 and minutes_of_day < five_pm:   # Sunday before 17:00 ET
        return False
    if day == 4 and minutes_of_day >= five_pm:  # Friday at/after 17:00 ET
        return False
    return True
