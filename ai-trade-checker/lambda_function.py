import json
import logging

from ably_publisher import publish_ably_event
from dynamodb import update_daily_money_made
from lesson import generate_lesson_learned
from oanda import get_trade_state
from storage import get_open_trades, update_trade_closed, update_trade_lesson_learned

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def lambda_handler(event, context):
    logger.info("ai-trade-checker starting")

    open_trades = get_open_trades()

    if not open_trades:
        logger.info("No open trades to check")
        return {"statusCode": 200, "body": json.dumps({"message": "No open trades"})}

    closed_count = 0

    for trade in open_trades:
        trade_id = trade["trade_id"]
        oanda_trade_id = trade["oanda_trade_id"]

        try:
            oanda_trade = get_trade_state(oanda_trade_id)
            state = oanda_trade.get("state")

            if state == "CLOSED":
                exit_price = float(oanda_trade.get("averageClosePrice", 0))
                profit_loss = float(oanda_trade.get("realizedPL", 0))
                closed_at = oanda_trade.get("closeTime")

                update_trade_closed(
                    trade_id=trade_id,
                    exit_price=exit_price,
                    profit_loss=profit_loss,
                    closed_at=closed_at,
                )
                publish_ably_event("trade.closed", {
                    "trade_id": str(trade_id),
                    "profit_loss": profit_loss,
                    "is_successful": profit_loss > 0,
                })

                logger.info(
                    "Trade marked closed | trade_id=%s | oanda_trade_id=%s | exit_price=%.5f | profit_loss=%.2f",
                    trade_id, oanda_trade_id, exit_price, profit_loss,
                )

                update_daily_money_made(profit_loss)
                publish_ably_event("stats.updated", {})

                try:
                    lesson = generate_lesson_learned(trade, exit_price, profit_loss)
                    update_trade_lesson_learned(trade_id=trade_id, lesson_learned=lesson)
                except Exception:
                    logger.exception("Failed to generate lesson learned | trade_id=%s", trade_id)

                closed_count += 1

            elif state == "OPEN":
                logger.info(
                    "Trade still open | trade_id=%s | oanda_trade_id=%s | unrealized_pl=%s",
                    trade_id, oanda_trade_id, oanda_trade.get("unrealizedPL", "N/A"),
                )

            else:
                logger.warning(
                    "Unexpected trade state | trade_id=%s | oanda_trade_id=%s | state=%s",
                    trade_id, oanda_trade_id, state,
                )

        except Exception:
            logger.exception("Error checking trade | trade_id=%s | oanda_trade_id=%s", trade_id, oanda_trade_id)

    logger.info("ai-trade-checker complete | checked=%d | closed=%d", len(open_trades), closed_count)
    return {
        "statusCode": 200,
        "body": json.dumps({"checked": len(open_trades), "closed": closed_count}),
    }
