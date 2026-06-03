"use client";

import { useCallback, useState } from "react";
import styles from "./OngoingTrades.module.css";
import LiveTradesRow from "./LiveTradesRow";
import { useAblyChannel } from "@/lib/useAblyChannel";
import { Trade } from "@/lib/types";

export default function OngoingTrades({ initialTrades }: { initialTrades: Trade[] }) {
  const [trades, setTrades] = useState(initialTrades);

  const refetch = useCallback(async () => {
    const res = await fetch("/api/trades?status=open");
    if (res.ok) setTrades(await res.json());
  }, []);

  useAblyChannel("trading", "trade.opened", refetch);

  return (
    <section className={styles.container}>
      <p className={styles.title}>Ongoing Trades</p>
      {trades.length === 0 ? (
        <p className={styles.empty}>No active trades.</p>
      ) : (
        <LiveTradesRow trades={trades} />
      )}
    </section>
  );
}
