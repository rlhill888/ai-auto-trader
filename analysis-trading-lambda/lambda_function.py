import json


def lambda_handler(event, context):
    print(f"Event: {json.dumps(event)}")

    records = event.get("Records", [])
    print(f"Processing {len(records)} record(s)")

    for index, record in enumerate(records):
        body = json.loads(record["body"])
        article = body.get("article", {})
        print(f"Record {index}: {json.dumps(article)}")
        # TODO: add analysis logic here

    return {
        "statusCode": 200,
        "body": json.dumps({"message": "OK"}),
    }
