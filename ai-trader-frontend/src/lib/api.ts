import { Trade } from "./types";

function baseUrl() {
  if (process.env.VERCEL_URL) return `https://${process.env.VERCEL_URL}`;
  return "http://localhost:3000";
}

export async function getTrades(status?: Trade["trade_status"]): Promise<Trade[]> {
  const url = status
    ? `${baseUrl()}/api/trades?status=${status}`
    : `${baseUrl()}/api/trades`;
  const res = await fetch(url, { cache: "no-store" });
  if (!res.ok) return [];
  return res.json();
}

export async function getTrade(trade_id: string): Promise<Trade | null> {
  const res = await fetch(`${baseUrl()}/api/trades/${trade_id}`, { cache: "no-store" });
  if (!res.ok) return null;
  return res.json();
}
