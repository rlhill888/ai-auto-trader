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


def article_already_traded(article_id: str) -> bool:
    global _conn
    sql = "SELECT 1 FROM trade_decisions WHERE article_id = %s AND trade_status = 'open' LIMIT 1"
    for attempt in range(2):
        try:
            conn = get_connection()
            cursor = conn.cursor()
            try:
                cursor.execute(sql, (article_id,))
                return cursor.fetchone() is not None
            finally:
                cursor.close()
        except Exception as e:
            print(f"Database error checking article (attempt {attempt + 1}): {e}")
            _conn = None
            if attempt == 1:
                raise
    return False


def get_open_trade_for_instrument(instrument: str) -> dict | None:
    global _conn
    sql = """
        SELECT trade_id, article_title, article_summary, direction, reasoning, confidence, oanda_trade_id
        FROM trade_decisions
        WHERE instrument = %s AND trade_status = 'open'
        ORDER BY timestamp DESC
        LIMIT 1
    """
    for attempt in range(2):
        try:
            conn = get_connection()
            cursor = conn.cursor()
            try:
                cursor.execute(sql, (instrument,))
                row = cursor.fetchone()
                if row is None:
                    return None
                return {
                    "trade_id": str(row[0]),
                    "article_title": row[1],
                    "article_summary": row[2],
                    "direction": row[3],
                    "reasoning": row[4],
                    "confidence": float(row[5]),
                    "oanda_trade_id": row[6],
                }
            finally:
                cursor.close()
        except Exception as e:
            print(f"Database error getting open trade (attempt {attempt + 1}): {e}")
            _conn = None
            if attempt == 1:
                raise
    return None


def mark_trade_exited_early(trade_id: str, reason: str, exit_price: float, profit_loss: float) -> None:
    global _conn
    sql = """
        UPDATE trade_decisions
        SET trade_status = 'closed',
            left_trade_early = TRUE,
            reason_for_leaving_trade_early = %s,
            exit_price = %s,
            profit_loss = %s,
            closed_at = NOW(),
            is_successful = %s
        WHERE trade_id = %s
    """
    is_successful = profit_loss > 0
    for attempt in range(2):
        try:
            conn = get_connection()
            cursor = conn.cursor()
            try:
                cursor.execute(sql, (reason, exit_price, profit_loss, is_successful, trade_id))
                conn.commit()
            finally:
                cursor.close()
            print(f"Marked trade as exited early | trade_id={trade_id}")
            return
        except Exception as e:
            print(f"Database error marking early exit (attempt {attempt + 1}): {e}")
            _conn = None
            if attempt == 1:
                raise


def store_trade_decision(article: dict, analysis: dict, units: int, oanda_order_id: str = None, oanda_trade_id: str = None, skipped_reason: str = None) -> None:
    global _conn

    sql = """
        INSERT INTO trade_decisions (
            trade_id, article_id, article_title, article_summary,
            is_good_trade, instrument, direction, units,
            reasoning, confidence, timestamp, oanda_order_id, oanda_trade_id, trade_status,
            confidence_duration, estimated_trade_timeframe, recheck_duration, estimated_latest_trade_end
        ) VALUES (
            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
        )
    """

    if oanda_order_id:
        trade_status = "open"
    elif skipped_reason:
        trade_status = skipped_reason
    else:
        trade_status = "skipped"

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
        oanda_trade_id or "",
        trade_status,
        analysis.get("confidence_duration"),
        analysis.get("estimated_trade_timeframe"),
        analysis.get("recheck_duration"),
        analysis.get("estimated_latest_trade_end"),
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
