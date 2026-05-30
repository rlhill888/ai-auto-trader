import json

from analysis import analyze_article
from oanda import calculate_units, execute_trade, get_account_nav
from storage import store_trade_decision


def lambda_handler(event, context):
    print(f"Event: {json.dumps(event)}")

    records = event.get("Records", [])
    print(f"Processing {len(records)} record(s)")

    nav = get_account_nav()
    units = calculate_units(nav)
    print(f"Calculated trade units: {units} (1% of NAV {nav})")

    for index, record in enumerate(records):
        body = json.loads(record["body"])
        article = body.get("article", {})
        print(f"Record {index}: {json.dumps(article)}")

        try:
            analysis = analyze_article(article)

            if analysis.get("is_good_trade"):
                oanda_order_id = execute_trade(
                    instrument=analysis["instrument"],
                    direction=analysis["direction"],
                    units=units,
                )
                store_trade_decision(article, analysis, units=units, oanda_order_id=oanda_order_id)
                print(f"Record {index}: trade executed — {analysis['direction']} {units} {analysis['instrument']}")
            else:
                store_trade_decision(article, analysis, units=units)
                print(f"Record {index}: no trade — {analysis.get('reasoning', 'low confidence')}")

        except Exception as e:
            print(f"Record {index}: error processing article — {e}")
            raise

    return {
        "statusCode": 200,
        "body": json.dumps({"message": "OK"}),
    }
