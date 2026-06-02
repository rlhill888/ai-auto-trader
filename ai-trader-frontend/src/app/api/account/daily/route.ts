import { NextResponse } from "next/server";
import { GetCommand } from "@aws-sdk/lib-dynamodb";
import { dynamo } from "@/lib/dynamo";

export async function GET() {
  try {
    const result = await dynamo.send(new GetCommand({
      TableName: "ai-trader-global-values",
      Key: { globalKey: "GLOBAL" },
    }));

    const item = result.Item ?? {};

    return NextResponse.json({
      dailyMoneyMade: Number(item.dailyMoneyMade ?? 0),
      tradesCompleted: Number(item.dailySucceeded ?? 0) + Number(item.dailyFailed ?? 0),
      succeeded: Number(item.dailySucceeded ?? 0),
      failed: Number(item.dailyFailed ?? 0),
    });
  } catch (err) {
    console.error("Failed to fetch daily stats:", err);
    return NextResponse.json(
      { dailyMoneyMade: 0, tradesCompleted: 0, succeeded: 0, failed: 0 },
      { status: 500 }
    );
  }
}
