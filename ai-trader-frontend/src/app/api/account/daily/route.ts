import { NextResponse } from "next/server";
import { DynamoDBClient } from "@aws-sdk/client-dynamodb";
import { DynamoDBDocumentClient, GetCommand } from "@aws-sdk/lib-dynamodb";

const client = DynamoDBDocumentClient.from(new DynamoDBClient({
  region: process.env.APP_AWS_REGION ?? "us-east-1",
}));

export async function GET() {
  try {
    const result = await client.send(new GetCommand({
      TableName: "ai-trader-global-values",
      Key: { globalKey: "GLOBAL" },
    }));

    const dailyMoneyMade = result.Item?.daily_money_made ?? 0;
    return NextResponse.json({ dailyMoneyMade: Number(dailyMoneyMade) });
  } catch (err) {
    console.error("Failed to fetch daily money made:", err);
    return NextResponse.json({ dailyMoneyMade: 0 }, { status: 500 });
  }
}
