import { DynamoDBClient } from "@aws-sdk/client-dynamodb";
import { DynamoDBDocumentClient } from "@aws-sdk/lib-dynamodb";

export const dynamo = DynamoDBDocumentClient.from(
  new DynamoDBClient({ region: process.env.APP_AWS_REGION ?? "us-east-1" })
);
