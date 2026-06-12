import json
import logging
import re
from datetime import datetime, timezone, timedelta

import requests

from forex_market_hours import is_forex_market_open
from ably_publisher import publish_ably_event
from dynamodb import update_daily_money_made
from lesson import generate_lesson_learned
from oanda import get_trade_state, close_trade
from recheck import analyze_trade_recheck
from storage import (
    get_open_trades,
    get_early_exited_trades_needing_lesson,
    update_trade_cancelled,
    update_trade_closed,
    update_trade_lesson_learned,
    update_trade_last_checked,
)

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def parse_duration(s: str) -> timedelta:
    m = re.match(r'(\d+(?:\.\d+)?)\s*(minute|hour|day|week)s?', s.lower())
    if not m:
        logger.warning("Unrecognized recheck_duration format %r — defaulting to 2 hours", s)
        return timedelta(hours=2)
    v, unit = float(m.group(1)), m.group(2)
    return {'minute': timedelta(minutes=v), 'hour': timedelta(hours=v),
            'day': timedelta(days=v), 'week': timedelta(weeks=v)}.get(unit, timedelta(hours=2))



def lambda_handler(event, context):
    logger.info("ai-trade-checker starting")

    if not is_forex_market_open():
        logger.info("Forex market is closed — skipping run")
        return {"statusCode": 200, "body": json.dumps({"message": "Market closed"})}

    open_trades = get_open_trades()

    if not open_trades:
        logger.info("No open trades to check")
        return {"statusCode": 200, "body": json.dumps({"message": "No open trades"})}

    closed_count = 0
    closed_trade_ids = set()

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

                # Detect manual close: SL and TP orders both not filled
                sl_filled = oanda_trade.get("stopLossOrder", {}).get("state") == "FILLED"
                tp_filled = oanda_trade.get("takeProfitOrder", {}).get("state") == "FILLED"
                already_flagged = trade.get("left_trade_early") or False
                manual_exit = not sl_filled and not tp_filled and not already_flagged

                update_trade_closed(
                    trade_id=trade_id,
                    exit_price=exit_price,
                    profit_loss=profit_loss,
                    closed_at=closed_at,
                    left_trade_early=manual_exit,
                    reason_for_leaving_trade_early="User manually left trade" if manual_exit else None,
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
                    actual_left_early = trade.get("left_trade_early") or manual_exit
                    actual_reason = trade.get("reason_for_leaving_trade_early") or ("User manually left trade" if manual_exit else None)
                    lesson = generate_lesson_learned(trade, exit_price, profit_loss, left_trade_early=actual_left_early, early_exit_reason=actual_reason)
                    update_trade_lesson_learned(trade_id=trade_id, lesson_learned=lesson)
                except Exception:
                    logger.exception("Failed to generate lesson learned | trade_id=%s", trade_id)

                closed_trade_ids.add(trade_id)
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

        except requests.exceptions.HTTPError as e:
            if e.response is not None and e.response.status_code == 404:
                logger.warning(
                    "Trade not found on OANDA (404) — marking cancelled | trade_id=%s | oanda_trade_id=%s",
                    trade_id, oanda_trade_id,
                )
                update_trade_cancelled(trade_id=trade_id)
                closed_trade_ids.add(trade_id)
                closed_count += 1
            else:
                logger.exception("Error checking trade | trade_id=%s | oanda_trade_id=%s", trade_id, oanda_trade_id)
        except Exception:
            logger.exception("Error checking trade | trade_id=%s | oanda_trade_id=%s", trade_id, oanda_trade_id)

    early_exit_trades = get_early_exited_trades_needing_lesson()
    lesson_count = 0

    for trade in early_exit_trades:
        trade_id = trade["trade_id"]
        exit_price = float(trade.get("exit_price") or 0)
        profit_loss = float(trade.get("profit_loss") or 0)
        reason = trade.get("reason_for_leaving_trade_early")

        try:
            lesson = generate_lesson_learned(trade, exit_price, profit_loss, left_trade_early=True, early_exit_reason=reason)
            update_trade_lesson_learned(trade_id=trade_id, lesson_learned=lesson)
            lesson_count += 1
        except Exception:
            logger.exception("Failed to generate lesson learned for early exit | trade_id=%s", trade_id)

    # Step 3: AI recheck for still-open trades whose recheck interval has elapsed
    now = datetime.now(timezone.utc)
    recheck_count = 0

    for trade in open_trades:
        if trade["trade_id"] in closed_trade_ids:
            continue

        recheck_str = trade.get("recheck_duration")
        if not recheck_str:
            continue

        last_checked = trade.get("trade_last_checked")
        created_at = trade.get("timestamp")

        reference = last_checked if last_checked is not None else created_at
        if reference is None:
            continue

        if reference.tzinfo is None:
            reference = reference.replace(tzinfo=timezone.utc)

        elapsed = now - reference
        interval = parse_duration(recheck_str)

        if elapsed < interval:
            logger.info(
                "Trade recheck not yet due | trade_id=%s | elapsed=%s | interval=%s",
                trade["trade_id"], elapsed, interval,
            )
            continue

        logger.info(
            "Trade recheck interval elapsed — calling AI | trade_id=%s | elapsed=%s | interval=%s | last_checked=%s",
            trade["trade_id"], elapsed, interval, trade.get("trade_last_checked") or "never",
        )

        try:
            update_trade_last_checked(trade["trade_id"])

            oanda_trade = get_trade_state(trade["oanda_trade_id"])
            decision = analyze_trade_recheck(trade, oanda_trade)

            if not decision.get("should_stay"):
                reason = decision.get("reason", "AI recheck recommended exit")
                close_result = close_trade(trade["oanda_trade_id"])
                exit_price = close_result["exit_price"]
                profit_loss = close_result["profit_loss"]
                closed_at = datetime.now(timezone.utc).isoformat()
                update_trade_closed(
                    trade_id=trade["trade_id"],
                    exit_price=exit_price,
                    profit_loss=profit_loss,
                    closed_at=closed_at,
                    left_trade_early=True,
                    reason_for_leaving_trade_early=reason,
                )
                lesson = generate_lesson_learned(
                    trade, exit_price, profit_loss,
                    left_trade_early=True, early_exit_reason=reason,
                )
                update_trade_lesson_learned(trade_id=trade["trade_id"], lesson_learned=lesson)
                publish_ably_event("trade.closed", {
                    "trade_id": str(trade["trade_id"]),
                    "profit_loss": profit_loss,
                    "is_successful": profit_loss > 0,
                })
                update_daily_money_made(profit_loss)
                publish_ably_event("stats.updated", {})
                logger.info(
                    "AI recheck exited trade | trade_id=%s | pl=%.2f | reason=%s",
                    trade["trade_id"], profit_loss, reason[:80],
                )
            else:
                logger.info("AI recheck: staying in trade | trade_id=%s", trade["trade_id"])

            recheck_count += 1
        except requests.exceptions.HTTPError as e:
            if e.response is not None and e.response.status_code == 404:
                logger.warning(
                    "Trade not found on OANDA during recheck (404) — marking cancelled | trade_id=%s",
                    trade["trade_id"],
                )
                update_trade_cancelled(trade_id=trade["trade_id"])
            else:
                logger.exception("Error during AI recheck | trade_id=%s", trade["trade_id"])
        except Exception:
            logger.exception("Error during AI recheck | trade_id=%s", trade["trade_id"])

    logger.info(
        "ai-trade-checker complete | checked=%d | closed=%d | early_exit_lessons=%d | rechecked=%d",
        len(open_trades), closed_count, lesson_count, recheck_count,
    )
    return {
        "statusCode": 200,
        "body": json.dumps({
            "checked": len(open_trades),
            "closed": closed_count,
            "early_exit_lessons": lesson_count,
            "rechecked": recheck_count,
        }),
    }
