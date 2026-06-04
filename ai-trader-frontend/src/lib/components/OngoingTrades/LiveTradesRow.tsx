"use client";

import { useEffect, useState } from "react";
import styles from "./OngoingTrades.module.css";
import TradeCard from "@/lib/components/TradeCard/TradeCard";
import { Trade, LiveTradeData } from "@/lib/types";

const POLL_INTERVAL_MS = 10_000;

export default function LiveTradesRow({ trades, flashIds }: { trades: Trade[]; flashIds: Set<string> }) {
  const [liveData, setLiveData] = useState<Record<string, LiveTradeData>>({});
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function fetchLive() {
      try {
        const res = await fetch("/api/trades/live");
        if (res.ok) setLiveData(await res.json());
      } catch {}
      setLoading(false);
    }

    fetchLive();
    const id = setInterval(fetchLive, POLL_INTERVAL_MS);
    return () => clearInterval(id);
  }, []);

  return (
    <div className={styles.row}>
      {trades.map((trade) => (
        <TradeCard
          key={trade.trade_id}
          trade={trade}
          live
          liveLoading={loading}
          liveData={liveData[trade.oanda_trade_id] ?? null}
          isNew={flashIds.has(trade.trade_id)}
        />
      ))}
    </div>
  );
}
