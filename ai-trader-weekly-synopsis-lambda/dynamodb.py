import logging
import os

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


def store_current_playbook(playbook: str) -> None:
    try:
        get_table().update_item(
            Key={"globalKey": "GLOBAL"},
            UpdateExpression="SET currentPlaybook = :playbook",
            ExpressionAttributeValues={":playbook": playbook},
        )
        logger.info("currentPlaybook stored in DynamoDB")
    except Exception:
        logger.exception("Failed to store currentPlaybook in DynamoDB")
