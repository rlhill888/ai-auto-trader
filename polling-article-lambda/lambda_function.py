import json
import requests
import feedparser


def lambda_handler(event, context):
    RSS_URL = "https://investinglive.com/rss/"
    print(f"Event: {json.dumps(event)}")
    try:
        print(f"Fetching RSS feed from {RSS_URL}")
        response = requests.get(RSS_URL, timeout=10)
        print(f"Received response with status code {response.status_code}")
        response.raise_for_status()
        print("Parsing RSS feed")
        print(response)

        feed = feedparser.parse(response.text)
        print(response.text)

        for index, entry in enumerate(feed.entries):
            article = {
                "title": entry.get("title"),
                "link": entry.get("link"),
                "published": entry.get("published"),
                "summary": entry.get("summary"),
                "id": entry.get("id"),
            }
            print(f"Article {index}: {json.dumps(article)}")
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
