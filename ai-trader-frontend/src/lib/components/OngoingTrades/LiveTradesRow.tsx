"use client";

import { useEffect, useState } from "react";
import styles from "./OngoingTrades.module.css";
import TradeCard from "@/lib/components/TradeCard/TradeCard";
import { Trade } from "@/lib/types";

const POLL_INTERVAL_MS = 5_000;

export default function LiveTradesRow({ trades }: { trades: Trade[] }) {
  const [liveData, setLiveData] = useState<Record<string, number>>({});

  useEffect(() => {
    async function fetchLive() {
      try {
        const res = await fetch("/api/trades/live");
        if (res.ok) setLiveData(await res.json());
      } catch {}
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
          unrealizedPl={liveData[trade.oanda_trade_id] ?? null}
        />
      ))}
    </div>
  );
}
