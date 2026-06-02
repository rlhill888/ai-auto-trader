import json
import logging

from analysis import analyze_article
from oanda import calculate_stop_price, calculate_take_profit_price, calculate_units, execute_trade, get_account_nav, get_current_price, get_pip_size
from storage import store_trade_decision

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def lambda_handler(event, context):
    records = event.get("Records", [])
    logger.info("Processing %d record(s)", len(records))

    nav = get_account_nav()

    for index, record in enumerate(records):
        body = json.loads(record["body"])
        article = body.get("article", {})
        logger.info(
            "Record %d: title=%r id=%r",
            index, article.get("title", "N/A"), article.get("id", "N/A"),
        )

        risk_amount = round(nav * 0.005, 2)

        try:
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
                pip_size = get_pip_size(instrument)
                units = calculate_units(nav, pip_size)
                entry_price = get_current_price(instrument, direction)
                stop_loss_price = calculate_stop_price(entry_price, direction, pip_size)
                take_profit_price = calculate_take_profit_price(entry_price, direction, pip_size)

                logger.info(
                    "Trade sizing | nav=%.2f | units=%d | entry=%.5f | stop=%s | tp=%s",
                    nav, units, entry_price, stop_loss_price, take_profit_price,
                )

                oanda_order_id, oanda_trade_id = execute_trade(
                    instrument=instrument,
                    direction=direction,
                    units=units,
                    stop_loss_price=stop_loss_price,
                    take_profit_price=take_profit_price,
                )
                store_trade_decision(article, analysis, units=units, oanda_order_id=oanda_order_id, oanda_trade_id=oanda_trade_id)
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
