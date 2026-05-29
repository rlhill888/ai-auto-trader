import json


def handler(event, context):
    print(f"Event: {json.dumps(event)}")

    return {
        "statusCode": 200,
        "body": json.dumps({"message": "OK"}),
    }
