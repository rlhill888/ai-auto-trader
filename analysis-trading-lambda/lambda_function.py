import json


def handler(event, context):
    print(f"Event: {json.dumps(event)}")
    #  analysis trading lambda
    return {
        "statusCode": 200,
        "body": json.dumps({"message": "OK"}),
    }
