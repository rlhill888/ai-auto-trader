import ssl
import logging
from datetime import date
from urllib.parse import urlparse

import pg8000

from config import DATABASE_URL

logger = logging.getLogger(__name__)

_conn = None


def get_connection():
    global _conn
    if _conn is None:
        try:
            url = urlparse(DATABASE_URL)
            ssl_context = ssl.create_default_context()
            ssl_context.check_hostname = False
            ssl_context.verify_mode = ssl.CERT_NONE
            _conn = pg8000.connect(
                host=url.hostname,
                port=url.port or 5432,
                database=url.path.lstrip("/"),
                user=url.username,
                password=url.password,
                ssl_context=ssl_context,
            )
            logger.info("Database connection established")
        except Exception as e:
            _conn = None
            logger.error("Failed to connect to database: %s", e)
            raise
    return _conn


def store_weekly_report(
    week_start: date,
    week_end: date,
    trade_count: int,
    synopsis: str,
    weekly_lesson: str,
    key_insights: str,
    biggest_mistakes: str,
    best_performing_themes: str,
    new_playbook_rules: str,
) -> None:
    global _conn
    sql = """
        INSERT INTO weekly_trading_reports
            (week_start, week_end, trade_count, synopsis, weekly_lesson,
             key_insights, biggest_mistakes, best_performing_themes, new_playbook_rules)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
    """
    for attempt in range(2):
        try:
            conn = get_connection()
            cursor = conn.cursor()
            try:
                cursor.execute(sql, (
                    week_start.isoformat(),
                    week_end.isoformat(),
                    trade_count,
                    synopsis,
                    weekly_lesson,
                    key_insights,
                    biggest_mistakes,
                    best_performing_themes,
                    new_playbook_rules,
                ))
                conn.commit()
                logger.info("Weekly report stored | week_start=%s | trade_count=%d", week_start, trade_count)
            finally:
                cursor.close()
            return
        except Exception as e:
            logger.error("DB error storing weekly report (attempt %d): %s", attempt + 1, e)
            _conn = None
            if attempt == 1:
                raise


def get_closed_trades_for_week(start_date: date, end_date: date) -> list[dict]:
    global _conn
    sql = """
        SELECT *
        FROM trade_decisions
        WHERE trade_status = 'closed'
          AND closed_at >= %s
          AND closed_at < %s
        ORDER BY closed_at ASC
    """
    for attempt in range(2):
        try:
            conn = get_connection()
            cursor = conn.cursor()
            try:
                cursor.execute(sql, (start_date.isoformat(), end_date.isoformat()))
                cols = [d[0] for d in cursor.description]
                rows = [dict(zip(cols, row)) for row in cursor.fetchall()]
                logger.info("Fetched %d closed trade(s) for week %s–%s", len(rows), start_date, end_date)
                return rows
            finally:
                cursor.close()
        except Exception as e:
            logger.error("DB error fetching closed trades for week (attempt %d): %s", attempt + 1, e)
            _conn = None
            if attempt == 1:
                raise
    return []
