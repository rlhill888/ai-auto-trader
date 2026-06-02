import logging
import os
from decimal import Decimal

import boto3

logger = logging.getLogger(__name__)

TABLE_NAME = os.environ.get("GLOBAL_VALUES_TABLE", "ai-trader-global-values")

_table = None


def get_table():
    global _table
    if _table is None:
        _table = boto3.resource("dynamodb").Table(TABLE_NAME)
    return _table


def update_daily_money_made(profit_loss: float) -> None:
    try:
        get_table().update_item(
            Key={"globalKey": "GLOBAL"},
            UpdateExpression="ADD daily_money_made :amount",
            ExpressionAttributeValues={":amount": Decimal(str(round(profit_loss, 2)))},
        )
        logger.info("Daily money made updated | profit_loss=%.2f", profit_loss)
    except Exception:
        logger.exception("Failed to update daily money made | profit_loss=%.2f", profit_loss)
