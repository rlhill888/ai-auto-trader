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
        is_successful = profit_loss > 0
        outcome_field = "daily_succeeded" if is_successful else "daily_failed"
        get_table().update_item(
            Key={"globalKey": "GLOBAL"},
            UpdateExpression=f"ADD daily_money_made :amount, {outcome_field} :one",
            ExpressionAttributeValues={
                ":amount": Decimal(str(round(profit_loss, 2))),
                ":one": 1,
            },
        )
        logger.info(
            "Daily stats updated | profit_loss=%.2f | is_successful=%s",
            profit_loss, is_successful,
        )
    except Exception:
        logger.exception("Failed to update daily stats | profit_loss=%.2f", profit_loss)
