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


def get_current_playbook() -> str | None:
    try:
        response = get_table().get_item(Key={"globalKey": "GLOBAL"})
        return response.get("Item", {}).get("currentPlaybook")
    except Exception:
        logger.exception("Failed to fetch currentPlaybook from DynamoDB")
        return None


def update_daily_money_made(profit_loss: float) -> None:
    try:
        is_successful = profit_loss > 0
        outcome_field = "dailySucceeded" if is_successful else "dailyFailed"
        get_table().update_item(
            Key={"globalKey": "GLOBAL"},
            UpdateExpression=f"ADD dailyMoneyMade :amount, totalMoneyMade :amount, {outcome_field} :one",
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
