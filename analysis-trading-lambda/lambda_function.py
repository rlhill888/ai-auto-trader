import json
import logging

from analysis import analyze_article
from oanda import calculate_units, execute_trade, get_account_nav
from storage import store_trade_decision

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def lambda_handler(event, context):
    records = event.get("Records", [])
    logger.info("Processing %d record(s)", len(records))

    nav = get_account_nav()
    units = calculate_units(nav)
    logger.info("Calculated trade units: %d (1%% of NAV %.2f)", units, nav)

    for index, record in enumerate(records):
        body = json.loads(record["body"])
        article = body.get("article", {})
        logger.info(
            "Record %d: title=%r id=%r",
            index, article.get("title", "N/A"), article.get("id", "N/A"),
        )

        try:
            analysis = analyze_article(article)
            logger.info(
                "Record %d: analysis complete | is_good_trade=%s | instrument=%s | direction=%s | confidence=%.2f",
                index,
                analysis.get("is_good_trade"),
                analysis.get("instrument"),
                analysis.get("direction"),
                analysis.get("confidence", 0),
            )

            if analysis.get("is_good_trade"):
                oanda_order_id, oanda_trade_id = execute_trade(
                    instrument=analysis["instrument"],
                    direction=analysis["direction"],
                    units=units,
                )
                store_trade_decision(article, analysis, units=units, oanda_order_id=oanda_order_id, oanda_trade_id=oanda_trade_id)
                logger.info(
                    "TRADE EXECUTED | record=%d | direction=%s | units=%d | instrument=%s | order_id=%s | trade_id=%s",
                    index, analysis["direction"], units, analysis["instrument"], oanda_order_id, oanda_trade_id,
                )
            else:
                store_trade_decision(article, analysis, units=units)
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
