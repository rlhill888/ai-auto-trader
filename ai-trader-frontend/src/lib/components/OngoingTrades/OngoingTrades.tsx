"use client";

import { useCallback, useEffect, useRef, useState } from "react";

import styles from "./OngoingTrades.module.css";
import LiveTradesRow from "./LiveTradesRow";
import { useAblyChannel } from "@/lib/useAblyChannel";
import { Trade } from "@/lib/types";
import { isForexMarketOpen } from "@/lib/forexMarketHours";

export default function OngoingTrades({ initialTrades }: { initialTrades: Trade[] }) {
  const [trades, setTrades] = useState(initialTrades);
  const [flashIds, setFlashIds] = useState<Set<string>>(new Set());
  const [marketOpen, setMarketOpen] = useState(() => isForexMarketOpen());
  const prevIdsRef = useRef<Set<string>>(new Set(initialTrades.map((t) => t.trade_id)));

  useEffect(() => {
    const id = setInterval(() => setMarketOpen(isForexMarketOpen()), 60000);
    return () => clearInterval(id);
  }, []);

  const refetch = useCallback(async () => {
    const res = await fetch("/api/trades?status=open");
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

  useAblyChannel("trading", "trade.opened", refetch);
  useAblyChannel("trading", "trade.closed", refetch);
  useAblyChannel("trading", "trade.exited_early", refetch);

  return (
    <section className={styles.container}>
      <div className={styles.titleRow}>
        <p className={`${styles.title}${!marketOpen ? ` ${styles.titleClosed}` : ""}`}>Ongoing Trades</p>
        {!marketOpen && <span className={styles.marketClosed}>Market Closed</span>}
      </div>
      {trades.length === 0 ? (
        <p className={styles.empty}>No active trades.</p>
      ) : (
        <LiveTradesRow trades={trades} flashIds={flashIds} />
      )}
    </section>
  );
}
