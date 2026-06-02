import logging
import os

import boto3

logger = logging.getLogger()
logger.setLevel(logging.INFO)

TABLE_NAME = os.environ.get("TABLE_NAME", "ai-trader-global-values")

dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table(TABLE_NAME)


def lambda_handler(event, context):
    logger.info("Resetting daily values in %s", TABLE_NAME)

    table.update_item(
        Key={"globalKey": "GLOBAL"},
        UpdateExpression="SET daily_money_made = :zero",
        ExpressionAttributeValues={":zero": 0},
    )

    logger.info("daily_money_made reset to 0")
    return {"statusCode": 200, "body": "Reset complete"}
