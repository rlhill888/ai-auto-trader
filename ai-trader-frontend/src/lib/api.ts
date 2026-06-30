import { Trade, WeeklyReport } from "./types";

function baseUrl() {
  if (process.env.VERCEL_URL) return `https://${process.env.VERCEL_URL}`;
  return "http://localhost:3000";
}

export async function getTrades(
  status?: Trade["trade_status"],
  limit?: number,
  offset?: number
): Promise<Trade[]> {
  const params = new URLSearchParams();
  if (status) params.set("status", status);
  if (limit !== undefined) params.set("limit", String(limit));
  if (offset !== undefined) params.set("offset", String(offset));
  const qs = params.toString();
  const url = `${baseUrl()}/api/trades${qs ? `?${qs}` : ""}`;
  const res = await fetch(url, { cache: "no-store" });
  if (!res.ok) return [];
  return res.json();
}

export async function getTrade(trade_id: string): Promise<Trade | null> {
  const res = await fetch(`${baseUrl()}/api/trades/${trade_id}`, { cache: "no-store" });
  if (!res.ok) return null;
  return res.json();
}

export async function getAccountNav(): Promise<number> {
  const res = await fetch(`${baseUrl()}/api/account`, { cache: "no-store" });
  if (!res.ok) return 0;
  const data = await res.json();
  return data.nav ?? 0;
}

export type DailyStats = {
  dailyMoneyMade: number;
  tradesCompleted: number;
  succeeded: number;
  failed: number;
};

export async function getDailyStats(): Promise<DailyStats> {
  const res = await fetch(`${baseUrl()}/api/account/daily`, { cache: "no-store" });
  if (!res.ok) return { dailyMoneyMade: 0, tradesCompleted: 0, succeeded: 0, failed: 0 };
  return res.json();
}

export async function getLatestWeeklyAnalysis(): Promise<WeeklyReport | null> {
  const res = await fetch(`${baseUrl()}/api/analysis`, { cache: "no-store" });
  if (!res.ok) return null;
  return res.json();
}

export async function getWeeklyAnalysis(id: string): Promise<WeeklyReport | null> {
  const res = await fetch(`${baseUrl()}/api/analysis/${id}`, { cache: "no-store" });
  if (!res.ok) return null;
  return res.json();
}

export async function getWeeklyCharts(weekStart: string, weekEnd: string): Promise<string[]> {
  const params = new URLSearchParams({ week_start: weekStart, week_end: weekEnd });
  const res = await fetch(`${baseUrl()}/api/charts?${params}`, { cache: "no-store" });
  if (!res.ok) return [];
  const data = await res.json();
  return data.charts ?? [];
}
