import { NextResponse } from "next/server";

export async function GET() {
  const apiKey = process.env.OANDA_API_KEY;
  const accountId = process.env.OANDA_ACCOUNT_ID;
  const baseUrl = process.env.OANDA_BASE_URL;

  if (!apiKey || !accountId || !baseUrl) {
    return NextResponse.json({ error: "Missing OANDA credentials" }, { status: 500 });
  }

  const res = await fetch(`${baseUrl}/v3/accounts/${accountId}/trades?state=OPEN`, {
    headers: {
      Authorization: `Bearer ${apiKey}`,
      "Content-Type": "application/json",
    },
    cache: "no-store",
  });

  if (!res.ok) {
    return NextResponse.json({ error: "Failed to fetch from OANDA" }, { status: 502 });
  }

  const data = await res.json();
  const trades: Record<string, {
    unrealizedPl: number;
    entryPrice: number;
    tpPrice: number | null;
    slPrice: number | null;
  }> = {};

  for (const trade of data.trades ?? []) {
    trades[trade.id] = {
      unrealizedPl: parseFloat(trade.unrealizedPL ?? "0"),
      entryPrice: parseFloat(trade.price ?? "0"),
      tpPrice: trade.takeProfitOrder ? parseFloat(trade.takeProfitOrder.price) : null,
      slPrice: trade.stopLossOrder ? parseFloat(trade.stopLossOrder.price) : null,
    };
  }

  return NextResponse.json(trades);
}
