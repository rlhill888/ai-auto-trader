"use client";

import { useCallback, useState } from "react";
import styles from "./ClosedTrades.module.css";
import TradeCard from "@/lib/components/TradeCard/TradeCard";
import { useAblyChannel } from "@/lib/useAblyChannel";
import { Trade } from "@/lib/types";

export default function ClosedTrades({ initialTrades }: { initialTrades: Trade[] }) {
  const [trades, setTrades] = useState(initialTrades);

  const refetch = useCallback(async () => {
    const res = await fetch("/api/trades?status=closed");
    if (res.ok) setTrades(await res.json());
  }, []);

  useAblyChannel("trading", "trade.closed", refetch);

  return (
    <section className={styles.container}>
      <p className={styles.title}>Past Closed Trades</p>
      {trades.length === 0 ? (
        <p className={styles.empty}>No closed trades yet.</p>
      ) : (
        <div className={styles.row}>
          {trades.map((trade) => (
            <TradeCard key={trade.trade_id} trade={trade} />
          ))}
        </div>
      )}
    </section>
  );
}
