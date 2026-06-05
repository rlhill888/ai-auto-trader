import json
import logging

from ably_publisher import publish_ably_event
from analysis import analyze_article, analyze_early_exit
from dynamodb import update_daily_money_made
from oanda import calculate_stop_price, calculate_take_profit_price, calculate_units, close_trade, execute_trade, get_account_nav, get_current_price, get_pip_size, has_open_position
from storage import store_trade_decision, article_already_traded, get_open_trade_for_instrument, mark_trade_exited_early

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def lambda_handler(event, context):
    records = event.get("Records", [])
    logger.info("Processing %d record(s)", len(records))

    nav = get_account_nav()
    traded_this_batch = set()

    for index, record in enumerate(records):
        body = json.loads(record["body"])
        article = body.get("article", {})
        logger.info(
            "Record %d: title=%r id=%r",
            index, article.get("title", "N/A"), article.get("id", "N/A"),
        )

        risk_amount = round(nav * 0.005, 2)

        try:
            article_id = article.get("id", "")
            if article_already_traded(article_id):
                logger.info("Record %d: article already traded, skipping | article_id=%s", index, article_id)
                continue

            analysis = analyze_article(article, risk_amount)
            logger.info(
                "Record %d: analysis complete | is_good_trade=%s | instrument=%s | direction=%s | confidence=%.2f",
                index,
                analysis.get("is_good_trade"),
                analysis.get("instrument"),
                analysis.get("direction"),
                analysis.get("confidence", 0),
            )

            if analysis.get("is_good_trade"):
                instrument = analysis["instrument"]
                direction = analysis["direction"]

                if article_already_traded(article_id):
                    logger.info("Record %d: article already traded, skipping | article_id=%s", index, article_id)
                    store_trade_decision(article, analysis, units=0, skipped_reason="already_traded")
                    continue

                if instrument in traded_this_batch:
                    logger.info("Record %d: instrument already traded in this batch, skipping | instrument=%s", index, instrument)
                    store_trade_decision(article, analysis, units=0, skipped_reason="already_in_trade")
                    continue

                if has_open_position(instrument):
                    current_trade_db = get_open_trade_for_instrument(instrument)

                    if current_trade_db is None or current_trade_db["direction"] == direction:
                        logger.info("Record %d: open position already exists (same direction), skipping | instrument=%s", index, instrument)
                        store_trade_decision(article, analysis, units=0, skipped_reason="already_in_trade")
                        continue

                    logger.info(
                        "Record %d: open position exists in OPPOSITE direction, running early-exit analysis | instrument=%s | current=%s | new=%s",
                        index, instrument, current_trade_db["direction"], direction,
                    )
                    exit_decision = analyze_early_exit(current_trade_db, analysis, article)
                    logger.info(
                        "Record %d: early exit decision | should_exit=%s | reason=%s",
                        index, exit_decision.get("should_exit"), exit_decision.get("reason"),
                    )

                    if not exit_decision.get("should_exit"):
                        store_trade_decision(article, analysis, units=0, skipped_reason="already_in_trade")
                        continue

                    close_result = close_trade(current_trade_db["oanda_trade_id"])
                    mark_trade_exited_early(
                        current_trade_db["trade_id"],
                        exit_decision["reason"] + "\n\n" + article.get("id", ""),
                        close_result["exit_price"],
                        close_result["profit_loss"],
                    )
                    update_daily_money_made(close_result["profit_loss"])
                    publish_ably_event("trade.exited_early", {
                        "instrument": instrument,
                        "reason": exit_decision["reason"],
                        "profit_loss": close_result["profit_loss"],
                    })
                    publish_ably_event("stats.updated", {})
                    logger.info(
                        "Record %d: TRADE EXITED EARLY | instrument=%s | exit_price=%.5f | pl=%.2f | reason=%s",
                        index, instrument, close_result["exit_price"], close_result["profit_loss"], exit_decision["reason"],
                    )
                    # Fall through to open the new trade in the opposite direction

                stop_loss_pips = analysis["stop_loss_pips"]
                take_profit_pips = analysis["take_profit_pips"]
                pip_size = get_pip_size(instrument)
                units = calculate_units(nav, pip_size, stop_loss_pips)
                entry_price = get_current_price(instrument, direction)
                stop_loss_price = calculate_stop_price(entry_price, direction, pip_size, stop_loss_pips)
                take_profit_price = calculate_take_profit_price(entry_price, direction, pip_size, take_profit_pips)

                logger.info(
                    "Trade sizing | nav=%.2f | units=%d | entry=%.5f | stop=%s | tp=%s | sl_pips=%d | tp_pips=%d",
                    nav, units, entry_price, stop_loss_price, take_profit_price, stop_loss_pips, take_profit_pips,
                )

                oanda_order_id, oanda_trade_id = execute_trade(
                    instrument=instrument,
                    direction=direction,
                    units=units,
                    stop_loss_price=stop_loss_price,
                    take_profit_price=take_profit_price,
                )
                traded_this_batch.add(instrument)
                store_trade_decision(article, analysis, units=units, oanda_order_id=oanda_order_id, oanda_trade_id=oanda_trade_id)
                publish_ably_event("trade.opened", {
                    "instrument": instrument,
                    "direction": direction,
                    "units": units,
                })
                logger.info(
                    "TRADE EXECUTED | record=%d | direction=%s | units=%d | instrument=%s | stop=%s | order_id=%s | trade_id=%s",
                    index, direction, units, instrument, stop_loss_price, oanda_order_id, oanda_trade_id,
                )
            else:
                store_trade_decision(article, analysis, units=0)
                logger.info(
                    "Record %d: no trade | reasoning=%s",
                    index, analysis.get("reasoning", "low confidence"),
                )

        except Exception as e:
            logger.exception("Record %d: error processing article", index)
            raise

    return {
        "statusCode": 200,
        "body": json.dumps({"message": "OK"}),
    }
