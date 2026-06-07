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
DATABASE_URL = secret["DATABASE_URL"]
