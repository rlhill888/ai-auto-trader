import { NextResponse } from "next/server";

export async function GET() {
  const apiKey = process.env.OANDA_API_KEY;
  const accountId = process.env.OANDA_ACCOUNT_ID;
  const baseUrl = process.env.OANDA_BASE_URL;

  if (!apiKey || !accountId || !baseUrl) {
    return NextResponse.json({ error: "Missing OANDA credentials" }, { status: 500 });
  }

  const res = await fetch(`${baseUrl}/v3/accounts/${accountId}/summary`, {
    headers: { Authorization: `Bearer ${apiKey}` },
    cache: "no-store",
  });

  if (!res.ok) {
    return NextResponse.json({ error: "Failed to fetch from OANDA" }, { status: 502 });
  }

  const { account } = await res.json();

  return NextResponse.json({
    balance: parseFloat(account.balance),
    nav: parseFloat(account.NAV),
    unrealizedPl: parseFloat(account.unrealizedPL),
    currency: account.currency,
  });
}
