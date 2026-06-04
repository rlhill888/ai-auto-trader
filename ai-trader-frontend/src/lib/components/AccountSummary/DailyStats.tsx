"use client";

import { useCallback, useState } from "react";
import { useAblyChannel } from "@/lib/useAblyChannel";
import { type DailyStats } from "@/lib/api";
import styles from "./AccountSummary.module.css";

export default function DailyStats({ initialStats }: { initialStats: DailyStats }) {
  const [stats, setStats] = useState(initialStats);

  const refetch = useCallback(async () => {
    const res = await fetch("/api/account/daily");
    if (res.ok) setStats(await res.json());
  }, []);

  useAblyChannel("trading", "stats.updated", refetch);

  if (stats.tradesCompleted === 0) return null;

  return (
    <div className={styles.dailyStats}>
      <span className={styles.statsTotal}>
        {stats.tradesCompleted} trade{stats.tradesCompleted !== 1 ? "s" : ""} today
      </span>
      <div className={styles.statsBreakdown}>
        <span className={styles.statsSucceeded}>{stats.succeeded} succeeded</span>
        <span className={styles.statsFailed}>{stats.failed} failed</span>
      </div>
    </div>
  );
}
