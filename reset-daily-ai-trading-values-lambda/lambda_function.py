import logging
import os
from datetime import datetime, timedelta, timezone

import boto3

logger = logging.getLogger()
logger.setLevel(logging.INFO)

TABLE_NAME = os.environ.get("TABLE_NAME", "ai-trader-global-values")

dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table(TABLE_NAME)

EST = timezone(timedelta(hours=-5))


def lambda_handler(event, context):
    logger.info("Reading daily values before reset from %s", TABLE_NAME)

    response = table.get_item(Key={"globalKey": "GLOBAL"})
    item = response.get("Item", {})

    money_made = item.get("dailyMoneyMade", 0)
    successful = int(item.get("dailySucceeded", 0))
    unsuccessful = int(item.get("dailyFailed", 0))
    total_trades = successful + unsuccessful
    day_successful = successful > unsuccessful

    # Yesterday in EST (lambda runs at midnight EST)
    yesterday_est = (datetime.now(EST) - timedelta(days=1)).strftime("%Y-%m-%d")

    logger.info(
        "Saving daily summary for %s: moneyMade=%s, total=%s, succeeded=%s, failed=%s, successful=%s",
        yesterday_est, money_made, total_trades, successful, unsuccessful, day_successful,
    )

    table.put_item(
        Item={
            "globalKey": yesterday_est,
            "moneyMade": money_made,
            "totalTrades": total_trades,
            "successfulTrades": successful,
            "unsuccessfulTrades": unsuccessful,
            "daySuccessful": day_successful,
        }
    )

    table.update_item(
        Key={"globalKey": "GLOBAL"},
        UpdateExpression="SET dailyMoneyMade = :zero, dailySucceeded = :zero, dailyFailed = :zero",
        ExpressionAttributeValues={":zero": 0},
    )

    logger.info("Daily values reset to 0")
    return {"statusCode": 200, "body": "Reset complete"}
