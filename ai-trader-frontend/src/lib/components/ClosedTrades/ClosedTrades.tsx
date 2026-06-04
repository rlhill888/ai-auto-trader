"use client";

import { useCallback, useRef, useState } from "react";
import styles from "./ClosedTrades.module.css";
import TradeCard from "@/lib/components/TradeCard/TradeCard";
import { useAblyChannel } from "@/lib/useAblyChannel";
import { Trade } from "@/lib/types";

export default function ClosedTrades({ initialTrades }: { initialTrades: Trade[] }) {
  const [trades, setTrades] = useState(initialTrades);
  const [flashIds, setFlashIds] = useState<Set<string>>(new Set());
  const prevIdsRef = useRef<Set<string>>(new Set(initialTrades.map((t) => t.trade_id)));

  const refetch = useCallback(async () => {
    const res = await fetch("/api/trades?status=closed");
    if (!res.ok) return;
    const next: Trade[] = await res.json();
    const newIds = next.map((t) => t.trade_id).filter((id) => !prevIdsRef.current.has(id));
    if (newIds.length > 0) {
      setFlashIds(new Set(newIds));
      setTimeout(() => setFlashIds(new Set()), 1100);
    }
    prevIdsRef.current = new Set(next.map((t) => t.trade_id));
    setTrades(next);
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
            <TradeCard key={trade.trade_id} trade={trade} isNew={flashIds.has(trade.trade_id)} />
          ))}
        </div>
      )}
    </section>
  );
}
