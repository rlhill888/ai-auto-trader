import hashlib
import json
import os
import boto3
import requests
import feedparser
from botocore.exceptions import ClientError


ARTICLE_TABLE_NAME = os.environ["ARTICLE_TABLE_NAME"]
QUEUE_URL = os.environ["ANALYSIS_QUEUE_URL"]
dynamodb = boto3.resource("dynamodb")
sqs = boto3.client("sqs")
table = dynamodb.Table(ARTICLE_TABLE_NAME)


def lambda_handler(event, context):
    RSS_URL = "https://investinglive.com/feed/"
    print(f"Event: {json.dumps(event)}")
    try:
        print(f"Fetching RSS feed from {RSS_URL}")
        response = requests.get(RSS_URL, timeout=10)
        print(f"Received response with status code {response.status_code}")
        response.raise_for_status()
        print("Parsing RSS feed")

        feed = feedparser.parse(response.text)

        for index, entry in enumerate(feed.entries):
            article = {
                "id": entry.get("id"),
                "title": entry.get("title"),
                "link": entry.get("link"),
                "published": entry.get("published"),
                "summary": entry.get("summary"),
                "tags": entry.get("tags")
            }

            try:
                table.put_item(
                    Item={
                        "article-id": entry["id"],
                        **article,
                    },
                    ConditionExpression="attribute_not_exists(#id)",
                    ExpressionAttributeNames={"#id": "article-id"},
                )

                print(f"Article {index}: {json.dumps(article)}")
                print(f"Saved article {index} to DynamoDB")

                sqs.send_message(
                    QueueUrl=QUEUE_URL,
                    MessageBody=json.dumps({"article": article}),
                    MessageGroupId="articles",
                    MessageDeduplicationId=hashlib.md5(entry["id"].encode()).hexdigest()
                )
                print(f"Sent article {index} to queue")

            except ClientError as e:
                if e.response["Error"]["Code"] == "ConditionalCheckFailedException":
                    print(f"Article {index} already exists, skipping")
                else:
                    raise

    except requests.RequestException as e:
        print(f"Error fetching RSS feed: {e}")
        return {
            "statusCode": 500,
            "body": json.dumps({"message": "Error fetching RSS feed"}),
        }
    
    # polling lambda
    return {
        "statusCode": 200,
        "body": json.dumps({"message": "OK"}),
    }
