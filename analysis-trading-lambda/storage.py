import ssl
import uuid
from datetime import datetime, timezone
from urllib.parse import urlparse

import pg8000

from config import DATABASE_URL

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
        except Exception as e:
            _conn = None
            print(f"Failed to connect to Supabase: {e}")
            raise
    return _conn


def store_trade_decision(article: dict, analysis: dict, units: int, oanda_order_id: str = None) -> None:
    global _conn

    sql = """
        INSERT INTO trade_decisions (
            trade_id, article_id, article_title, article_summary,
            is_good_trade, instrument, direction, units,
            reasoning, confidence, timestamp, oanda_order_id, trade_status
        ) VALUES (
            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
        )
    """

    values = (
        str(uuid.uuid4()),
        article.get("id", "unknown"),
        article.get("title", ""),
        article.get("summary", ""),
        analysis.get("is_good_trade", False),
        analysis.get("instrument", ""),
        analysis.get("direction", ""),
        units,
        analysis.get("reasoning", ""),
        analysis.get("confidence", 0),
        datetime.now(timezone.utc),
        oanda_order_id or "",
        "open" if oanda_order_id else "skipped",
    )

    for attempt in range(2):
        try:
            conn = get_connection()
            cursor = conn.cursor()
            try:
                cursor.execute(sql, values)
                conn.commit()
            finally:
                cursor.close()
            print(f"Stored trade decision — isGoodTrade={analysis.get('is_good_trade')} instrument={analysis.get('instrument')}")
            return
        except Exception as e:
            print(f"Database error (attempt {attempt + 1}): {e}")
            _conn = None
            if attempt == 1:
                raise
