import json
import os

import boto3


def get_secret(secret_name: str) -> dict:
    try:
        client = boto3.client("secretsmanager")
        response = client.get_secret_value(SecretId=secret_name)
        return json.loads(response["SecretString"])
    except Exception as e:
        print(f"Failed to retrieve secret '{secret_name}': {e}")
        raise


secret = get_secret(os.environ["SECRET_NAME"])
OPENAI_API_KEY = secret["OPENAI_API_KEY"]
OANDA_API_KEY = secret["OANDA_API_KEY"]
OANDA_ACCOUNT_ID = secret["OANDA_ACCOUNT_ID"]
DATABASE_URL = secret["DATABASE_URL"]

print(f"[DEBUG] OANDA_API_KEY first/last 4 chars: {OANDA_API_KEY[:4]}...{OANDA_API_KEY[-4:]!r} len={len(OANDA_API_KEY)}")
print(f"[DEBUG] OANDA_ACCOUNT_ID: {OANDA_ACCOUNT_ID!r}")

OANDA_ENVIRONMENT = os.environ.get("OANDA_ENVIRONMENT", "practice")
OANDA_BASE_URL = (
    "https://api-fxtrade.oanda.com"
    if OANDA_ENVIRONMENT == "live"
    else "https://api-fxpractice.oanda.com"
)
