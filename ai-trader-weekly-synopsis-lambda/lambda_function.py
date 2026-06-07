import json
import logging

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def lambda_handler(event, context):
    logger.info("Weekly synopsis lambda invoked")

    try:
        # TODO: implement weekly synopsis logic

        return {
            "statusCode": 200,
            "body": json.dumps({"message": "Weekly synopsis complete"}),
        }
    except Exception:
        logger.exception("Error generating weekly synopsis")
        raise
