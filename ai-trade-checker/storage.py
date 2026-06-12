import ssl
import logging
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


def get_open_trades() -> list[dict]:
    global _conn
    sql = """
        SELECT *
        FROM trade_decisions
        WHERE trade_status = 'open'
        AND oanda_trade_id IS NOT NULL
        AND oanda_trade_id != ''
    """
    for attempt in range(2):
        try:
            conn = get_connection()
            cursor = conn.cursor()
            try:
                cursor.execute(sql)
                cols = [d[0] for d in cursor.description]
                rows = [dict(zip(cols, row)) for row in cursor.fetchall()]
                logger.info("Fetched %d open trade(s) from DB", len(rows))
                return rows
            finally:
                cursor.close()
        except Exception as e:
            logger.error("DB error fetching open trades (attempt %d): %s", attempt + 1, e)
            _conn = None
            if attempt == 1:
                raise
    return []


def get_early_exited_trades_needing_lesson() -> list[dict]:
    global _conn
    sql = """
        SELECT trade_id, oanda_trade_id, instrument, direction,
               reasoning, confidence, article_title, article_summary,
               left_trade_early, reason_for_leaving_trade_early,
               exit_price, profit_loss
        FROM trade_decisions
        WHERE trade_status = 'closed'
        AND left_trade_early = TRUE
        AND lesson_learned IS NULL
    """
    for attempt in range(2):
        try:
            conn = get_connection()
            cursor = conn.cursor()
            try:
                cursor.execute(sql)
                cols = [d[0] for d in cursor.description]
                rows = [dict(zip(cols, row)) for row in cursor.fetchall()]
                logger.info("Fetched %d early-exited trade(s) needing lesson", len(rows))
                return rows
            finally:
                cursor.close()
        except Exception as e:
            logger.error("DB error fetching early-exited trades (attempt %d): %s", attempt + 1, e)
            _conn = None
            if attempt == 1:
                raise
    return []


def update_trade_closed(
    trade_id: str,
    exit_price: float,
    profit_loss: float,
    closed_at: str,
    left_trade_early: bool = False,
    reason_for_leaving_trade_early: str = None,
) -> None:
    global _conn
    is_successful = profit_loss > 0
    sql = """
        UPDATE trade_decisions
        SET trade_status                  = 'closed',
            exit_price                    = %s,
            profit_loss                   = %s,
            closed_at                     = %s,
            is_successful                 = %s,
            left_trade_early              = %s,
            reason_for_leaving_trade_early = %s
        WHERE trade_id = %s
    """
    for attempt in range(2):
        try:
            conn = get_connection()
            cursor = conn.cursor()
            try:
                cursor.execute(sql, (exit_price, profit_loss, closed_at, is_successful, left_trade_early, reason_for_leaving_trade_early, trade_id))
                conn.commit()
                logger.info(
                    "Trade closed in DB | trade_id=%s | exit_price=%.5f | profit_loss=%.2f | is_successful=%s | left_early=%s",
                    trade_id, exit_price, profit_loss, is_successful, left_trade_early,
                )
            finally:
                cursor.close()
            return
        except Exception as e:
            logger.error("DB error updating trade (attempt %d): %s", attempt + 1, e)
            _conn = None
            if attempt == 1:
                raise


def update_trade_cancelled(trade_id: str) -> None:
    global _conn
    sql = "UPDATE trade_decisions SET trade_status = 'cancelled' WHERE trade_id = %s"
    for attempt in range(2):
        try:
            conn = get_connection()
            cursor = conn.cursor()
            try:
                cursor.execute(sql, (trade_id,))
                conn.commit()
                logger.info("Trade marked cancelled | trade_id=%s", trade_id)
            finally:
                cursor.close()
            return
        except Exception as e:
            logger.error("DB error cancelling trade (attempt %d): %s", attempt + 1, e)
            _conn = None
            if attempt == 1:
                raise


def update_trade_last_checked(trade_id: str) -> None:
    global _conn
    sql = "UPDATE trade_decisions SET trade_last_checked = NOW() WHERE trade_id = %s"
    for attempt in range(2):
        try:
            conn = get_connection()
            cursor = conn.cursor()
            try:
                cursor.execute(sql, (trade_id,))
                conn.commit()
                logger.info("trade_last_checked updated | trade_id=%s", trade_id)
            finally:
                cursor.close()
            return
        except Exception as e:
            logger.error("DB error updating trade_last_checked (attempt %d): %s", attempt + 1, e)
            _conn = None
            if attempt == 1:
                raise


def update_trade_lesson_learned(trade_id: str, lesson_learned: str) -> None:
    global _conn
    sql = """
        UPDATE trade_decisions
        SET lesson_learned = %s
        WHERE trade_id = %s
    """
    for attempt in range(2):
        try:
            conn = get_connection()
            cursor = conn.cursor()
            try:
                cursor.execute(sql, (lesson_learned, trade_id))
                conn.commit()
                logger.info("Lesson learned saved | trade_id=%s", trade_id)
            finally:
                cursor.close()
            return
        except Exception as e:
            logger.error("DB error saving lesson learned (attempt %d): %s", attempt + 1, e)
            _conn = None
            if attempt == 1:
                raise
